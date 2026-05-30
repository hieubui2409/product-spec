"""Phase 4 — COMPETITION dimension: the `competitive_drift` LLM check, SCRIPT half
(goal G-E3, design R2 / trade-off T2 / §0.1).

`competitive_drift` ("this PRD is losing its competitive edge") is an LLM-judgment
warn — a sensory call no enum-match makes. To stop the classic over-flag
hallucination, the design pins the LLM to STRUCTURED, SCRIPT-resolved parity
anchors and forbids it from inventing a competitor or a parity verdict. This module
is the RED spec for that script half — `competitive_drift_anchors.build_anchors(...)`
and its CLI:

  - the script RESOLVES the PRD's ID-keyed `competitive_parity` map against the
    BRD's DRY competitor identity home (`graph['competitors']`) into NAME-bearing
    rows and pre-computes `competitors_with_data` (real, non-`none` verdicts) and
    `all_behind_competitors` — the LLM NEVER counts or re-parses brd.md (F6).
  - `eligible = scope=='core-value' AND competitors_with_data>=2` is the anchored
    gate (design §0.1); a PRD failing it is emitted `eligible: false` so the LLM
    returns `missing_anchor` instead of flagging on a lone `behind`.
  - an eligible PRD with EVERY real parity `behind` (all_behind == data count) is
    surfaced WITH all anchors so the LLM can flag it citing data (true-positive).
  - an eligible PRD with any non-`behind` verdict still carries full anchors; the
    LLM returns `{finding: null}` (must-not-flag) — the SCRIPT never decides.

The flag/no-flag JUDGMENT itself is graded by the LLM evals (eval/evals.json ids
11-13); these tests assert only the deterministic script contract (G-B1 split).
Subprocess + direct-call style, mirroring test_time_realism.py.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
from competitive_drift_anchors import build_anchors  # noqa: E402


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


def _brd_md(*competitors: str) -> str:
    """A BRD with the given competitor YAML blocks (the DRY identity home)."""
    comp_block = ""
    if competitors:
        comp_block = "competitors:\n" + "".join(competitors)
    return f"""---
id: BRD
type: brd
status: draft
lang: en
goals:
  - id: BRD-G1
    title: g
    status: draft
    metrics: [m]
{comp_block}---
"""


_COMP_ACME = """  - id: COMP-ACME
    name: "Acme Commerce"
    url: "https://acme.example"
    threat: high
"""
_COMP_SHOPIFY = """  - id: COMP-SHOPIFY
    name: "Shopify"
    threat: high
"""
_COMP_NICHE = """  - id: COMP-NICHE
    name: "NicheCart"
    threat: low
"""


def _scaffold(tmp_path: Path, *competitors: str) -> Path:
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(_PRODUCT_MD)
    (prod / "brd.md").write_text(_brd_md(*competitors))
    return proj


def _write_prd(proj: Path, name: str, prd_id: str, *, scope=None,
               parity: dict | None = None) -> None:
    fm = [f"id: {prd_id}", "type: prd", "brd_goals: [BRD-G1]",
          "status: draft", "lang: en", "horizon: now"]
    if scope is not None:
        fm.append(f"scope: {scope}")
    if parity is not None:
        fm.append("competitive_parity:")
        for cid, val in parity.items():
            fm.append(f"  {cid}: {val}")
    body = "---\n" + "\n".join(fm) + "\n---\n"
    (proj / "docs" / "product" / "prds" / name).write_text(body)


def _anchor_for(proj: Path, prd_id: str):
    g = build_graph(proj)
    anchors = build_anchors(g)
    match = [a for a in anchors if a["artifact_id"] == prd_id]
    assert match, f"no anchor for {prd_id}; got {[a['artifact_id'] for a in anchors]}"
    return match[0]


# ── true-positive: eligible core-value PRD, every real parity behind ─────────
# Rule (§0.1): flag only if scope==core-value AND competitors_with_data>=2 AND
# every real (non-none) parity == behind.

def test_anchor_true_positive_eligible_and_all_behind(tmp_path):
    """core-value PRD, 2 verdicts both `behind` → eligible, all_behind lists BOTH
    resolved NAMES, so the LLM can flag and cite data (no parity invented)."""
    proj = _scaffold(tmp_path, _COMP_ACME, _COMP_SHOPIFY)
    _write_prd(proj, "checkout.md", "PRD-CHECKOUT", scope="core-value",
               parity={"COMP-ACME": "behind", "COMP-SHOPIFY": "behind"})
    a = _anchor_for(proj, "PRD-CHECKOUT")
    assert a["eligible"] is True, f"core-value + 2 verdicts must be eligible: {a}"
    assert a["scope"] == "core-value"
    assert a["competitors_with_data"] == 2, f"two real verdicts: {a}"
    # Resolved NAMES come from the BRD identity home — the LLM does not re-parse.
    assert a["all_behind_competitors"] == ["Acme Commerce", "Shopify"], a
    # The flag rule: all real verdicts are behind iff len(all_behind)==data count.
    assert len(a["all_behind_competitors"]) == a["competitors_with_data"]


# ── must-not-flag: eligible but one verdict at parity (LLM returns finding:null) ─

def test_anchor_borderline_one_parity_not_all_behind(tmp_path):
    """core-value PRD, 2 verdicts but one is `parity`: still eligible with FULL
    anchors, but all_behind != data count — the LLM must return finding:null. The
    script does NOT decide; it only reports the numbers."""
    proj = _scaffold(tmp_path, _COMP_ACME, _COMP_SHOPIFY)
    _write_prd(proj, "search.md", "PRD-SEARCH", scope="core-value",
               parity={"COMP-ACME": "behind", "COMP-SHOPIFY": "parity"})
    a = _anchor_for(proj, "PRD-SEARCH")
    assert a["eligible"] is True
    assert a["competitors_with_data"] == 2
    assert a["all_behind_competitors"] == ["Acme Commerce"], a
    # Not every real verdict is behind → the LLM scaffold returns no finding.
    assert len(a["all_behind_competitors"]) != a["competitors_with_data"]


# ── missing-anchor: not core-value → eligible False, LLM returns missing_anchor ─

def test_anchor_non_core_value_is_ineligible(tmp_path):
    """A PRD that is not scope:core-value cannot drift-flag; marked eligible:false
    so the LLM returns missing_anchor (never flags on a lone behind)."""
    proj = _scaffold(tmp_path, _COMP_ACME, _COMP_SHOPIFY)
    _write_prd(proj, "reports.md", "PRD-REPORTS", scope="in",
               parity={"COMP-ACME": "behind", "COMP-SHOPIFY": "behind"})
    a = _anchor_for(proj, "PRD-REPORTS")
    assert a["eligible"] is False, f"scope:in must be ineligible: {a}"
    assert a["scope"] == "in"
    # Counting still happens (it is data, not judgment) — only the gate is closed.
    assert a["competitors_with_data"] == 2


def test_anchor_fewer_than_two_data_points_is_ineligible(tmp_path):
    """The other half of the gate: a core-value PRD with <2 REAL verdicts is
    ineligible. `none` parity is tracked-but-no-verdict — NOT a data point."""
    proj = _scaffold(tmp_path, _COMP_ACME, _COMP_NICHE)
    _write_prd(proj, "p.md", "PRD-P", scope="core-value",
               parity={"COMP-ACME": "behind", "COMP-NICHE": "none"})
    a = _anchor_for(proj, "PRD-P")
    assert a["eligible"] is False, f"<2 real verdicts must be ineligible: {a}"
    # COMP-NICHE 'none' is excluded from the data count and from all_behind.
    assert a["competitors_with_data"] == 1, f"none is not a data point: {a}"
    assert a["all_behind_competitors"] == ["Acme Commerce"]


def test_unresolved_parity_key_dropped_from_block(tmp_path):
    """A parity key that does not resolve to a BRD competitor is dropped from the
    resolved block (its `unknown_ref` is the consistency check's job) so the LLM
    never sees a phantom competitor."""
    proj = _scaffold(tmp_path, _COMP_ACME)
    _write_prd(proj, "p.md", "PRD-P", scope="core-value",
               parity={"COMP-ACME": "behind", "COMP-GHOST": "behind"})
    a = _anchor_for(proj, "PRD-P")
    ids = {r["competitor_id"] for r in a["competitive_parity"]}
    assert ids == {"COMP-ACME"}, f"phantom COMP-GHOST must be dropped: {a}"
    # With only the one resolved verdict it falls below the >=2 gate → ineligible.
    assert a["competitors_with_data"] == 1
    assert a["eligible"] is False


# ── only PRDs with a parity map are anchored ─────────────────────────────────

def test_prd_without_parity_map_is_not_anchored(tmp_path):
    """A v1 PRD (no competitive_parity) is not a drift unit — skipped, not emitted
    as an ineligible anchor (mirrors time anchors skipping non-epics)."""
    proj = _scaffold(tmp_path, _COMP_ACME, _COMP_SHOPIFY)
    _write_prd(proj, "withparity.md", "PRD-A", scope="core-value",
               parity={"COMP-ACME": "behind", "COMP-SHOPIFY": "behind"})
    _write_prd(proj, "noparity.md", "PRD-B", scope="core-value", parity=None)
    g = build_graph(proj)
    ids = {a["artifact_id"] for a in build_anchors(g)}
    assert "PRD-B" not in ids, f"a PRD with no parity map must not be anchored: {ids}"
    assert "PRD-A" in ids


def test_only_prds_anchored_not_epics(tmp_path):
    """The drift rule is defined on PRDs (scope + parity). Epics have no parity
    map and must not be emitted."""
    proj = _scaffold(tmp_path, _COMP_ACME, _COMP_SHOPIFY)
    _write_prd(proj, "p.md", "PRD-P", scope="core-value",
               parity={"COMP-ACME": "behind", "COMP-SHOPIFY": "behind"})
    (proj / "docs" / "product" / "epics" / "e.md").write_text("""---
id: PRD-P-E1
type: epic
prd: PRD-P
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    g = build_graph(proj)
    anchors = build_anchors(g)
    types = {a["type"] for a in anchors}
    assert types == {"prd"}, f"only PRDs anchored: {[(a['artifact_id'], a['type']) for a in anchors]}"


# ── determinism: resolved anchors are byte-stable across runs (G-A4) ──────────

def test_anchors_deterministic_and_sorted(tmp_path):
    proj = _scaffold(tmp_path, _COMP_ACME, _COMP_SHOPIFY)
    _write_prd(proj, "b.md", "PRD-B", scope="core-value",
               parity={"COMP-SHOPIFY": "behind", "COMP-ACME": "behind"})
    _write_prd(proj, "a.md", "PRD-A", scope="core-value",
               parity={"COMP-ACME": "behind", "COMP-SHOPIFY": "behind"})
    g = build_graph(proj)
    first = build_anchors(g)
    second = build_anchors(g)
    assert first == second, "anchors must be reproducible (G-A4)"
    # Sorted by artifact_id (A before B) regardless of file read order, and the
    # resolved parity rows are sorted by competitor_id (stable cited_data).
    assert [a["artifact_id"] for a in first] == ["PRD-A", "PRD-B"]
    for a in first:
        cids = [r["competitor_id"] for r in a["competitive_parity"]]
        assert cids == sorted(cids), f"parity rows must be sorted: {a}"


# ── back-compat: a v1 spec (no competitors / no parity) → empty anchors ───────

def test_backcompat_no_competitors_empty_anchors(tmp_path):
    """A v1 spec with no BRD competitors and no parity map yields no anchors and
    does not crash (G-A2)."""
    proj = _scaffold(tmp_path)  # no competitors
    _write_prd(proj, "p.md", "PRD-P", scope="core-value", parity=None)
    g = build_graph(proj)
    assert build_anchors(g) == [], "v1 spec must yield no drift anchors"


# ── CLI: advisory feeder always exits 0 ──────────────────────────────────────

def _run_cli(proj: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "competitive_drift_anchors.py"),
         "--root", str(proj)],
        capture_output=True, text=True,
    )


def test_cli_emits_anchors_and_exits_zero(tmp_path):
    """The CLI is an advisory feeder (never a gate) → always exits 0."""
    proj = _scaffold(tmp_path, _COMP_ACME, _COMP_SHOPIFY)
    _write_prd(proj, "p.md", "PRD-CHECKOUT", scope="core-value",
               parity={"COMP-ACME": "behind", "COMP-SHOPIFY": "behind"})
    r = _run_cli(proj)
    assert r.returncode == 0, f"anchors CLI must exit 0: {r.stderr}"
    payload = json.loads(r.stdout)
    anchors = payload["anchors"]
    assert any(a["artifact_id"] == "PRD-CHECKOUT" and a["eligible"] is True
               and a["all_behind_competitors"] == ["Acme Commerce", "Shopify"]
               for a in anchors), f"CLI must emit resolved anchors: {anchors}"


def test_none_parity_not_counted_as_data(tmp_path):
    """An unset `COMP-X:` parses to Python None ("tracked, no verdict") and must
    NOT count toward competitors_with_data — only real verdicts do."""
    proj = _scaffold(tmp_path, _COMP_ACME, _COMP_SHOPIFY, _COMP_NICHE)
    _write_prd(proj, "c.md", "PRD-C", scope="core-value",
               parity={"COMP-ACME": "", "COMP-SHOPIFY": "behind", "COMP-NICHE": "behind"})
    a = _anchor_for(proj, "PRD-C")
    assert a["competitors_with_data"] == 2, f"None parity must be excluded: {a}"
    assert "Acme Commerce" not in a["all_behind_competitors"]
