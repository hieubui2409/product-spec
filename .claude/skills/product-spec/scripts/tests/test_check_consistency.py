"""Phase 3 — TIME/DEPENDENCIES consistency checks (goal G-D1, G-D4, plus
dep_order + the depends_on type-guard).

All checks here are PURE structural / date comparisons — no wall clock, no LLM
(G-A4 determinism + G-B1 split). The wall-clock `overdue` advisory is a separate
script (test_time_advisory.py), deliberately OUTSIDE this gate.

RED spec for:
  - G-D1  `target_date` (ISO) parses onto PRD + Epic graph nodes; optional.
  - G-D4  `time_child_late` (warn) when a child's target_date is AFTER its
          parent's (an epic due after its PRD is incoherent).
  - dep_order (warn) when A depends_on B but A.target_date < B.target_date
          (you can't finish A before its prerequisite B).
  - type-guard: a NON-EMPTY `depends_on` on a story (wrong artifact type;
          depends_on is PRD+Epic only) reuses the EXISTING `invalid_type`
          finding — NOT a new check id (design-report build-order 3b / F7).

Fixture + finding-set assertion style of test_scripts.py / test_risk_complete.py.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
from check_consistency import check as check_cons, _enrich_with_ac  # noqa: E402


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
    return proj


def _checks(proj: Path):
    g = build_graph(proj)
    _enrich_with_ac(g, proj)
    return g, check_cons(g)


def _node(graph, node_id):
    return next((n for n in graph["nodes"] if n["id"] == node_id), None)


# ---------------------------------------------------------------------------
# G-D1 — target_date parses onto PRD + Epic nodes; optional.
# ---------------------------------------------------------------------------


def test_target_date_parses_on_prd_and_epic(tmp_path):
    proj = _scaffold(tmp_path)
    (proj / "docs" / "product" / "prds" / "a.md").write_text("""---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
target_date: 2026-09-30
---
""")
    (proj / "docs" / "product" / "epics" / "a-e1.md").write_text("""---
id: PRD-A-E1
type: epic
prd: PRD-A
status: draft
lang: en
target_date: 2026-08-15
---
""")
    g, _ = _checks(proj)
    prd = _node(g, "PRD-A")
    epic = _node(g, "PRD-A-E1")
    assert prd is not None and epic is not None
    # Stored as ISO date — accept either a date object or an ISO string; the
    # contract is "the date is preserved on the node", not its python type.
    assert str(prd.get("target_date")) == "2026-09-30", f"PRD target_date not on node: {prd.get('target_date')!r}"
    assert str(epic.get("target_date")) == "2026-08-15", f"Epic target_date not on node: {epic.get('target_date')!r}"


def test_target_date_optional_absence_is_clean(tmp_path):
    """G-D1 / G-A2: a PRD with no target_date validates with no error and the
    node's target_date is falsy (None/absent)."""
    proj = _scaffold(tmp_path)
    (proj / "docs" / "product" / "prds" / "a.md").write_text("""---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    g, findings = _checks(proj)
    assert not _node(g, "PRD-A").get("target_date"), "absent target_date must be falsy"
    assert [f for f in findings if f["severity"] == "error"] == [], (
        f"missing target_date must not error; got: {findings}"
    )


# ---------------------------------------------------------------------------
# G-D4 — time_child_late (warn): child target_date AFTER parent target_date.
# ---------------------------------------------------------------------------


def test_time_child_late(tmp_path):
    """Epic due 2026-10-01 under a PRD due 2026-09-30 → the child finishes after
    its parent. Deterministic warn."""
    proj = _scaffold(tmp_path)
    (proj / "docs" / "product" / "prds" / "a.md").write_text("""---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
target_date: 2026-09-30
---
""")
    (proj / "docs" / "product" / "epics" / "a-e1.md").write_text("""---
id: PRD-A-E1
type: epic
prd: PRD-A
status: draft
lang: en
target_date: 2026-10-01
---
""")
    g, findings = _checks(proj)
    late = [f for f in findings if f["check"] == "time_child_late"]
    assert late, f"expected time_child_late; got: {[f['check'] for f in findings]}"
    assert late[0]["severity"] == "warn", f"time_child_late must be warn: {late[0]}"
    assert late[0]["artifact_id"] == "PRD-A-E1"


def test_time_child_late_silent_when_child_earlier(tmp_path):
    """Child due before parent (the coherent case) → no warn."""
    proj = _scaffold(tmp_path)
    (proj / "docs" / "product" / "prds" / "a.md").write_text("""---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
target_date: 2026-09-30
---
""")
    (proj / "docs" / "product" / "epics" / "a-e1.md").write_text("""---
id: PRD-A-E1
type: epic
prd: PRD-A
status: draft
lang: en
target_date: 2026-08-15
---
""")
    g, findings = _checks(proj)
    assert not any(f["check"] == "time_child_late" for f in findings), (
        f"child earlier than parent must not warn; got: {findings}"
    )


# ---------------------------------------------------------------------------
# dep_order (warn): A depends_on B but A.target_date < B.target_date.
# ---------------------------------------------------------------------------


def test_dep_order(tmp_path):
    """PRD-A depends_on PRD-B, but A is due 2026-08-01 (earlier) while its
    prerequisite B is due 2026-09-01 — A cannot complete before B. Warn."""
    proj = _scaffold(tmp_path)
    (proj / "docs" / "product" / "prds" / "a.md").write_text("""---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
target_date: 2026-08-01
depends_on: [PRD-B]
---
""")
    (proj / "docs" / "product" / "prds" / "b.md").write_text("""---
id: PRD-B
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
target_date: 2026-09-01
---
""")
    g, findings = _checks(proj)
    order = [f for f in findings if f["check"] == "dep_order"]
    assert order, f"expected dep_order; got: {[f['check'] for f in findings]}"
    assert order[0]["severity"] == "warn", f"dep_order must be warn: {order[0]}"
    assert order[0]["artifact_id"] == "PRD-A"


def test_dep_order_silent_when_ordering_consistent(tmp_path):
    """A depends_on B with A due AFTER B (the consistent case) → no warn."""
    proj = _scaffold(tmp_path)
    (proj / "docs" / "product" / "prds" / "a.md").write_text("""---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
target_date: 2026-10-01
depends_on: [PRD-B]
---
""")
    (proj / "docs" / "product" / "prds" / "b.md").write_text("""---
id: PRD-B
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
target_date: 2026-09-01
---
""")
    g, findings = _checks(proj)
    assert not any(f["check"] == "dep_order" for f in findings), (
        f"consistent ordering must not warn; got: {findings}"
    )


# ---------------------------------------------------------------------------
# Type-guard: depends_on on a story (wrong type; PRD+Epic only) → invalid_type.
# ---------------------------------------------------------------------------


def test_depends_on_on_story_reuses_invalid_type(tmp_path):
    """`depends_on` is allowed on PRD + Epic ONLY. A non-empty depends_on on a
    story reuses the EXISTING `invalid_type` finding (no new check id)."""
    proj = _scaffold(tmp_path)
    (proj / "docs" / "product" / "prds" / "a.md").write_text("""---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    (proj / "docs" / "product" / "epics" / "a-e1.md").write_text("""---
id: PRD-A-E1
type: epic
prd: PRD-A
status: draft
lang: en
---
""")
    (proj / "docs" / "product" / "stories" / "a-e1-s1.md").write_text("""---
id: PRD-A-E1-S1
type: story
epic: PRD-A-E1
status: draft
lang: en
depends_on: [PRD-A]
acceptance_criteria:
  - "given x when y then z"
  - "another criterion"
---
""")
    g, findings = _checks(proj)
    bad = [f for f in findings
           if f["check"] == "invalid_type" and f["artifact_id"] == "PRD-A-E1-S1"]
    assert bad, (
        f"expected invalid_type for depends_on on a story; got: "
        f"{[(f['check'], f['artifact_id']) for f in findings]}"
    )
    # And NOT a fabricated new check id.
    assert not any(f["check"] in ("invalid_depends_on", "dep_invalid_type") for f in findings), (
        "must reuse invalid_type, not invent a new check id"
    )


def test_depends_on_on_prd_is_allowed(tmp_path):
    """The supported case: depends_on on a PRD does NOT trip invalid_type."""
    proj = _scaffold(tmp_path)
    (proj / "docs" / "product" / "prds" / "a.md").write_text("""---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
depends_on: [PRD-B]
---
""")
    (proj / "docs" / "product" / "prds" / "b.md").write_text("""---
id: PRD-B
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    g, findings = _checks(proj)
    assert not any(
        f["check"] == "invalid_type" and f["artifact_id"] == "PRD-A" for f in findings
    ), f"depends_on on a PRD must be allowed; got: {findings}"
