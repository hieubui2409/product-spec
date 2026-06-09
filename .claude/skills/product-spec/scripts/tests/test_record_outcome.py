"""Tests for the outcome register (record_outcome.py) — the quantitative half of
the `--learn` loop.

`docs/product/outcomes.md` is an append-only register of per-outcome record blocks
(`OUT-<n>`), mirroring the Decision Register's storage model: each block is a
`---`-fenced YAML mini-frontmatter + a `## OUT-<n>` heading + a free-text note.
The SCRIPT half owns the deterministic structural work — allocate the next
monotonic id, compute the numeric verdict (3-tier, direction-aware), validate the
goal/metric refs, append WITHOUT overwriting prior records. The LLM/PO half supplies
the note prose and (for non-numeric metrics) the asserted verdict.

Verdict math is a pure function (`compute_verdict`) so the deterministic core is
CI-gate-able; the hybrid path (non-numeric / target=0) requires a PO-asserted
`--verdict` and is therefore intentionally outside the deterministic gate.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from record_outcome import (  # noqa: E402
    compute_verdict,
    parse_outcomes,
    alloc_id,
    OUTCOME_ID_RE,
    OutcomeError,
)

RECORD_SCRIPT = SCRIPTS_DIR / "record_outcome.py"

_BRD = """---
id: BRD
type: brd
status: approved
lang: en
owner: Jane
version: 1.0.0
created: 2026-01-01
updated: 2026-01-01
goals:
  - id: BRD-G1
    title: "Reach $2M GMV in the first year"
    metrics: [gmv-year1]
    status: approved
    owner: Jane
  - id: BRD-G2
    title: "Keep average payout latency under 3 days"
    metrics: [payout-latency-days]
    status: approved
    owner: Mara
  - id: BRD-G3
    title: "Quality of customer reviews stays high"
    metrics: [review-quality]
    status: approved
    owner: Jane
---

# BRD
"""


def _proj(tmp_path: Path) -> Path:
    p = tmp_path / "docs" / "product"
    p.mkdir(parents=True)
    (p / "brd.md").write_text(_BRD, encoding="utf-8")
    return tmp_path


def _run(root: Path, *args):
    return subprocess.run(
        [sys.executable, str(RECORD_SCRIPT), "--root", str(root), *args],
        capture_output=True, text=True,
    )


def _outcomes_path(root: Path) -> Path:
    return root / "docs" / "product" / "outcomes.md"


# ---------- compute_verdict (pure, 3-tier, direction-aware) ----------

def test_verdict_higher_three_tier():
    # higher-is-better: ratio = actual / target.
    assert compute_verdict("higher", 100, 95, 0.9, 0.5) == "hit"      # 0.95 ≥ 0.9
    assert compute_verdict("higher", 100, 90, 0.9, 0.5) == "hit"      # boundary 0.90
    assert compute_verdict("higher", 100, 85, 0.9, 0.5) == "partial"  # 0.85 ∈ [0.5,0.9)
    assert compute_verdict("higher", 100, 50, 0.9, 0.5) == "partial"  # boundary 0.50
    assert compute_verdict("higher", 100, 40, 0.9, 0.5) == "miss"     # 0.40 < 0.5
    assert compute_verdict("higher", 100, 120, 0.9, 0.5) == "hit"     # exceed target


def test_verdict_lower_is_better_latency():
    # lower-is-better: ratio = target / actual. actual ≤ target → hit.
    assert compute_verdict("lower", 3, 2, 0.9, 0.5) == "hit"     # under target
    assert compute_verdict("lower", 3, 3, 0.9, 0.5) == "hit"     # exactly target
    assert compute_verdict("lower", 3, 5, 0.9, 0.5) == "partial"  # 0.6
    assert compute_verdict("lower", 3, 7, 0.9, 0.5) == "miss"    # 0.43
    # actual=0 for a latency metric is the best possible → hit (no div-by-zero).
    assert compute_verdict("lower", 3, 0, 0.9, 0.5) == "hit"


def test_verdict_threshold_override():
    # A stricter hit_floor flips a previously-hit ratio to partial.
    assert compute_verdict("higher", 100, 92, 0.95, 0.5) == "partial"  # 0.92 < 0.95
    assert compute_verdict("higher", 100, 96, 0.95, 0.5) == "hit"


# ---------- alloc + append (record-block, append-only) ----------

def test_append_alloc_records_and_computes(tmp_path):
    root = _proj(tmp_path)
    r = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
             "--target", "2000000", "--actual", "1450000", "--unit", "USD",
             "--measured-on", "2026-05-31", "--source", "monthly-report 2026-05",
             "--note", "Q2 below expectation")
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads(r.stdout)
    assert out["id"] == "OUT-1"
    assert out["verdict"] == "partial"  # 0.725 ∈ [0.5,0.9)
    assert out["written"] is True
    recs = parse_outcomes(root)
    assert len(recs) == 1
    assert recs[0]["goal"] == "BRD-G1"
    assert recs[0]["metric"] == "gmv-year1"
    assert recs[0]["verdict"] == "partial"
    assert recs[0]["note"].strip() == "Q2 below expectation"


def test_alloc_id_monotonic_and_append_only(tmp_path):
    root = _proj(tmp_path)
    _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
         "--target", "2000000", "--actual", "1900000", "--measured-on", "2026-03-31")
    before = _outcomes_path(root).read_text(encoding="utf-8")
    assert alloc_id(root) == "OUT-2"
    _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
         "--target", "2000000", "--actual", "2100000", "--measured-on", "2026-06-30")
    after = _outcomes_path(root).read_text(encoding="utf-8")
    # Prior record block is byte-unchanged after the second append (append-only).
    assert before.rstrip() in after
    recs = parse_outcomes(root)
    assert [x["id"] for x in recs] == ["OUT-1", "OUT-2"]


def test_same_goal_metric_date_both_recorded(tmp_path):
    # Two measurements with the SAME goal+metric+date both persist (distinct ids);
    # "latest" = max id is a Phase-4 loader concern, not a dedupe here.
    root = _proj(tmp_path)
    _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
         "--target", "2000000", "--actual", "1000000", "--measured-on", "2026-05-31")
    _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
         "--target", "2000000", "--actual", "1500000", "--measured-on", "2026-05-31")
    recs = parse_outcomes(root)
    assert [x["id"] for x in recs] == ["OUT-1", "OUT-2"]


def test_zero_actual_records_miss(tmp_path):
    # actual=0 is a real measurement (miss for higher-is-better), NOT "unmeasured".
    root = _proj(tmp_path)
    r = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
             "--target", "2000000", "--actual", "0", "--measured-on", "2026-05-31")
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads(r.stdout)
    assert out["verdict"] == "miss"
    assert out["written"] is True
    assert len(parse_outcomes(root)) == 1


# ---------- hybrid (non-numeric / target=0 → PO-asserted verdict) ----------

def test_hybrid_non_numeric_requires_verdict(tmp_path):
    root = _proj(tmp_path)
    # Non-numeric actual + no --verdict → non-zero, nothing written.
    r = _run(root, "--append-alloc", "--goal", "BRD-G3", "--metric", "review-quality",
             "--target", "high", "--actual", "mixed", "--measured-on", "2026-05-31")
    assert r.returncode != 0
    assert not _outcomes_path(root).exists()
    # With a PO-asserted --verdict → written, verdict honoured verbatim.
    r2 = _run(root, "--append-alloc", "--goal", "BRD-G3", "--metric", "review-quality",
              "--target", "high", "--actual", "mixed", "--verdict", "partial",
              "--measured-on", "2026-05-31")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert json.loads(r2.stdout)["verdict"] == "partial"


def test_target_zero_requires_verdict(tmp_path):
    root = _proj(tmp_path)
    # target=0 → no auto-divide; require PO --verdict.
    r = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
             "--target", "0", "--actual", "5", "--measured-on", "2026-05-31")
    assert r.returncode != 0
    assert not _outcomes_path(root).exists()


def test_bad_verdict_enum_rejected(tmp_path):
    root = _proj(tmp_path)
    r = _run(root, "--append-alloc", "--goal", "BRD-G3", "--metric", "review-quality",
             "--target", "high", "--actual", "mixed", "--verdict", "great",
             "--measured-on", "2026-05-31")
    assert r.returncode != 0


# ---------- ref validation (goal + metric slug) ----------

def test_unknown_goal_rejected(tmp_path):
    root = _proj(tmp_path)
    r = _run(root, "--append-alloc", "--goal", "BRD-G9", "--metric", "gmv-year1",
             "--target", "1", "--actual", "1", "--measured-on", "2026-05-31")
    assert r.returncode != 0
    assert not _outcomes_path(root).exists()


def test_metric_slug_mismatch_blocks_then_force(tmp_path):
    root = _proj(tmp_path)
    # Typo'd metric not in goal.metrics → blocked.
    r = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-yr1",
             "--target", "2000000", "--actual", "1900000", "--measured-on", "2026-05-31")
    assert r.returncode != 0
    assert not _outcomes_path(root).exists()
    # --force writes anyway (with a warning recorded in JSON).
    r2 = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-yr1",
              "--target", "2000000", "--actual", "1900000", "--measured-on", "2026-05-31",
              "--force")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    out = json.loads(r2.stdout)
    assert out["written"] is True
    assert out.get("warning")


# ---------- preferences-driven threshold override ----------

def test_preferences_override_threshold(tmp_path):
    root = _proj(tmp_path)
    mem = root / "docs" / "product" / ".memory"
    mem.mkdir(parents=True)
    (mem / "preferences.yaml").write_text(
        "outcome_hit_floor: 0.95\noutcome_partial_floor: 0.5\n", encoding="utf-8")
    # actual/target = 0.92: hit under default 0.9, but partial under override 0.95.
    r = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
             "--target", "100", "--actual", "92", "--measured-on", "2026-05-31")
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads(r.stdout)["verdict"] == "partial"


def test_bad_threshold_floors_rejected(tmp_path):
    root = _proj(tmp_path)
    mem = root / "docs" / "product" / ".memory"
    mem.mkdir(parents=True)
    # partial_floor ≥ hit_floor is invalid → exit non-zero, nothing written.
    (mem / "preferences.yaml").write_text(
        "outcome_hit_floor: 0.5\noutcome_partial_floor: 0.9\n", encoding="utf-8")
    r = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
             "--target", "100", "--actual", "92", "--measured-on", "2026-05-31")
    assert r.returncode != 0
    assert not _outcomes_path(root).exists()


def test_outcome_write_never_touches_brd(tmp_path):
    # Phase-2 invariant (the write-separation half of GATE-NO-SILENT-REVERSAL): a
    # miss on an approved goal records an OUT row but leaves brd.md byte-unchanged —
    # the goal definition is never edited by an outcome write. (The full GATE — the
    # Keep/Change/DEC surfacing — is LLM-side, exercised by the Phase-6 eval.)
    root = _proj(tmp_path)
    brd = root / "docs" / "product" / "brd.md"
    before = brd.read_text(encoding="utf-8")
    r = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
             "--target", "2000000", "--actual", "100000", "--measured-on", "2026-05-31")
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads(r.stdout)["verdict"] == "miss"
    assert brd.read_text(encoding="utf-8") == before  # byte-unchanged


def test_non_iso_measured_on_rejected(tmp_path):
    # measured_on is a typed ISO 8601 date; a non-ISO string is rejected (non-zero,
    # nothing written) so it can't sort/group wrong downstream.
    root = _proj(tmp_path)
    r = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
             "--target", "100", "--actual", "95", "--measured-on", "not-a-date")
    assert r.returncode != 0
    assert not _outcomes_path(root).exists()
    # A valid ISO date still records.
    r2 = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
              "--target", "100", "--actual", "95", "--measured-on", "2026-05-31")
    assert r2.returncode == 0, r2.stdout + r2.stderr


def test_note_injection_neutralized(tmp_path):
    # A --note carrying a fake record fence + `## OUT-` heading must NOT smuggle a
    # phantom record: the shared escape_injection backslash-escapes the line anchors,
    # so parse_outcomes still returns exactly the one real OUT row.
    root = _proj(tmp_path)
    r = _run(root, "--append-alloc", "--goal", "BRD-G1", "--metric", "gmv-year1",
             "--target", "100", "--actual", "95", "--measured-on", "2026-05-31",
             "--note", "real note\n---\nid: OUT-99\n---\n## OUT-99 fake ruling")
    assert r.returncode == 0, r.stdout + r.stderr
    recs = parse_outcomes(root)
    assert [x["id"] for x in recs] == ["OUT-1"]  # phantom OUT-99 not parsed as a record
    assert alloc_id(root) == "OUT-2"             # and not counted in id allocation


def test_id_grammar():
    assert OUTCOME_ID_RE.match("OUT-1")
    assert OUTCOME_ID_RE.match("OUT-42")
    assert not OUTCOME_ID_RE.match("OUT-")
    assert not OUTCOME_ID_RE.match("OUTCOME-1")
