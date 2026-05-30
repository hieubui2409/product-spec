"""Phase 3 — TIME dimension: the `time_realism` LLM check, SCRIPT half (goal G-D6,
design R2 / trade-off T2).

`time_realism` ("this deadline is unrealistic for this scope") is an LLM-judgment
warn — a sensory call no regex makes. To stop the classic over-flag hallucination,
the design pins the LLM to STRUCTURED, SCRIPT-precomputed anchors and forbids it
from doing any date math. This module is the RED spec for that script half —
`time_realism_anchors.build_anchors(...)` and its `--today` CLI:

  - the script pre-computes `days_remaining = (target_date - today).days` and
    `child_story_count` (a graph count) — the LLM NEVER computes a date.
  - `today_date` comes from a pinnable `--today <ISO>` so the anchor (and thus the
    gate's reproducibility) is deterministic (design F3 / G-A4).
  - an eligible epic (size + target_date present) crossing the rule's numbers is
    surfaced WITH all anchors so the LLM can flag it citing data (true-positive).
  - a below-threshold epic still carries full anchors; the LLM returns
    `{finding: null}` (must-not-flag) — the SCRIPT never decides flag/no-flag.
  - an epic missing `target_date` or `size` is marked `eligible: false` so the LLM
    returns `missing_anchor` instead of fabricating a date.

The flag/no-flag JUDGMENT itself is graded by the LLM evals (eval/evals.json ids
8-10); these tests assert only the deterministic script contract (G-B1 split).
Subprocess + direct-call style, mirroring test_time_advisory.py.
"""

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
from time_realism_anchors import build_anchors  # noqa: E402


_PRODUCT_MD = """---
id: PRODUCT
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [s]
---
"""

_BRD_MD = """---
id: BRD
type: brd
status: draft
lang: en
goals:
  - id: BRD-G1
    title: g
    status: draft
    metrics: [m]
---
"""


def _scaffold(tmp_path: Path) -> Path:
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(_PRODUCT_MD)
    (prod / "brd.md").write_text(_BRD_MD)
    # One parent PRD so the epics attach to a clean graph.
    (prod / "prds" / "p.md").write_text("""---
id: PRD-P
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    return proj


def _write_epic(proj: Path, name: str, epic_id: str, *, size=None,
                target_date=None, horizon="now") -> None:
    fm = [f"id: {epic_id}", "type: epic", "prd: PRD-P",
          "brd_goals: [BRD-G1]", "status: draft", "lang: en",
          f"horizon: {horizon}"]
    if size is not None:
        fm.append(f"size: {size}")
    if target_date is not None:
        fm.append(f"target_date: {target_date}")
    body = "---\n" + "\n".join(fm) + "\n---\n"
    (proj / "docs" / "product" / "epics" / name).write_text(body)


def _write_stories(proj: Path, epic_id: str, count: int) -> None:
    sdir = proj / "docs" / "product" / "stories"
    for i in range(1, count + 1):
        sid = f"{epic_id}-S{i}"
        sdir.joinpath(f"{sid}.md").write_text(f"""---
id: {sid}
type: story
epic: {epic_id}
status: draft
lang: en
acceptance_criteria: [a, b]
---
""")


def _anchor_for(proj: Path, epic_id: str, today: str):
    g = build_graph(proj)
    anchors = build_anchors(g, dt.date.fromisoformat(today))
    match = [a for a in anchors if a["artifact_id"] == epic_id]
    assert match, f"no anchor for {epic_id}; got {[a['artifact_id'] for a in anchors]}"
    return match[0]


# ── true-positive: eligible epic that crosses the design rule's numbers ──────
# Rule (R2): flag only if size==L AND child_story_count>=6 AND days_remaining<21.

def test_anchor_true_positive_eligible_and_over_threshold(tmp_path):
    """L epic, 6 stories, target 14 days out → eligible, days_remaining computed
    by the SCRIPT (not the LLM), all rule anchors present so the LLM can flag and
    cite data."""
    proj = _scaffold(tmp_path)
    _write_epic(proj, "big.md", "PRD-P-E1", size="L",
                target_date="2026-06-15", horizon="now")
    _write_stories(proj, "PRD-P-E1", 6)
    a = _anchor_for(proj, "PRD-P-E1", "2026-06-01")
    assert a["eligible"] is True, f"L epic with size+target_date must be eligible: {a}"
    assert a["size"] == "L"
    assert a["child_story_count"] == 6, f"expected 6 stories: {a}"
    # SCRIPT computed the date delta — (2026-06-15 - 2026-06-01) = 14 days.
    assert a["days_remaining"] == 14, f"days_remaining must be SCRIPT-computed: {a}"
    assert a["days_remaining"] < 21, "this fixture is the over-threshold (flag) case"


# ── must-not-flag: eligible but below threshold (LLM returns finding:null) ───

def test_anchor_below_threshold_still_full_anchors(tmp_path):
    """Small epic, far-future date: still eligible with FULL anchors, but the
    numbers are below the rule — the LLM must return finding:null. The script does
    NOT decide; it only reports the numbers."""
    proj = _scaffold(tmp_path)
    _write_epic(proj, "small.md", "PRD-P-E2", size="S",
                target_date="2026-12-31", horizon="later")
    _write_stories(proj, "PRD-P-E2", 2)
    a = _anchor_for(proj, "PRD-P-E2", "2026-06-01")
    assert a["eligible"] is True
    assert a["size"] == "S"
    assert a["child_story_count"] == 2
    assert a["days_remaining"] == 213, f"days_remaining must be computed: {a}"
    # Below-threshold on every dimension → the LLM scaffold returns no finding.
    assert not (a["size"] == "L" and a["child_story_count"] >= 6
                and a["days_remaining"] < 21)


# ── missing-anchor: no target_date → eligible False, LLM returns missing_anchor ─

def test_anchor_missing_target_date_is_ineligible(tmp_path):
    """An epic with no target_date cannot have days_remaining; it is marked
    eligible:false so the LLM returns missing_anchor (never guesses a date)."""
    proj = _scaffold(tmp_path)
    _write_epic(proj, "nodate.md", "PRD-P-E3", size="L", target_date=None)
    _write_stories(proj, "PRD-P-E3", 8)
    a = _anchor_for(proj, "PRD-P-E3", "2026-06-01")
    assert a["eligible"] is False, f"no target_date must be ineligible: {a}"
    assert a["target_date"] is None
    assert a["days_remaining"] is None, "no date math possible without a target_date"
    # child_story_count is still known (a graph count, not date-dependent).
    assert a["child_story_count"] == 8


def test_anchor_missing_size_is_ineligible(tmp_path):
    """size is the other required rule anchor; absent → eligible:false."""
    proj = _scaffold(tmp_path)
    _write_epic(proj, "nosize.md", "PRD-P-E4", size=None, target_date="2026-06-10")
    a = _anchor_for(proj, "PRD-P-E4", "2026-06-01")
    assert a["eligible"] is False, f"no size must be ineligible: {a}"
    assert a["size"] is None
    # days_remaining is still computed (target_date present) — only the rule is gated.
    assert a["days_remaining"] == 9


# ── only epics are anchored; a PRD has no size and is not the realism unit ───

def test_prd_is_not_anchored(tmp_path):
    """The realism rule is defined on epics (size + story count). A PRD has no
    size and must be skipped, not emitted as an ineligible anchor."""
    proj = _scaffold(tmp_path)
    _write_epic(proj, "e.md", "PRD-P-E1", size="M", target_date="2026-07-01")
    g = build_graph(proj)
    anchors = build_anchors(g, dt.date(2026, 6, 1))
    ids = {a["artifact_id"] for a in anchors}
    assert "PRD-P" not in ids, f"PRD must not be anchored: {ids}"
    assert "PRD-P-E1" in ids


# ── determinism: pinned --today → byte-identical output across runs (G-A4) ───

def test_anchors_deterministic_for_pinned_today(tmp_path):
    proj = _scaffold(tmp_path)
    _write_epic(proj, "a.md", "PRD-P-E2", size="L", target_date="2026-06-20")
    _write_epic(proj, "b.md", "PRD-P-E1", size="S", target_date="2026-06-10")
    g = build_graph(proj)
    first = build_anchors(g, dt.date(2026, 6, 1))
    second = build_anchors(g, dt.date(2026, 6, 1))
    assert first == second, "anchors must be reproducible for a pinned --today"
    # Sorted by artifact_id (E1 before E2) regardless of file read order.
    assert [a["artifact_id"] for a in first] == ["PRD-P-E1", "PRD-P-E2"]


def _run_cli(proj: Path, today: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "time_realism_anchors.py"),
         "--root", str(proj), "--today", today],
        capture_output=True, text=True,
    )


def test_cli_emits_anchors_and_exits_zero(tmp_path):
    """The CLI is an advisory feeder (never a gate) → always exits 0."""
    proj = _scaffold(tmp_path)
    _write_epic(proj, "e.md", "PRD-P-E1", size="L", target_date="2026-06-15")
    _write_stories(proj, "PRD-P-E1", 6)
    r = _run_cli(proj, "2026-06-01")
    assert r.returncode == 0, f"anchors CLI must exit 0: {r.stderr}"
    payload = json.loads(r.stdout)
    assert payload["today"] == "2026-06-01"
    anchors = payload["anchors"]
    assert any(a["artifact_id"] == "PRD-P-E1" and a["days_remaining"] == 14
               for a in anchors), f"CLI must emit computed anchors: {anchors}"


def test_cli_rejects_malformed_today(tmp_path):
    """A malformed --today is the one user error worth a non-zero exit."""
    proj = _scaffold(tmp_path)
    r = _run_cli(proj, "not-a-date")
    assert r.returncode == 1, f"malformed --today must exit 1: {r.stdout} / {r.stderr}"
