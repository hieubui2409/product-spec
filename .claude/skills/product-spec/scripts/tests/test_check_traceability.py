"""TIME/DEPENDENCIES traceability checks.

The new `depends_on: [ID]` edge joins the dangling family already owned by
check_traceability (beside `dangling_link`): a `depends_on` pointing at a
non-existent ID is `dep_dangling` (error). Same home as the cycle detector
(`find_dep_cycles` / `dep_cycle`) so the whole graph-walk dependency family
lives in one module.

RED spec for:
  - `dep_dangling` (error) when `depends_on` names an absent ID.
  - no `dep_dangling` when every `depends_on` target resolves.
  - back-compat: a v1 spec with no `depends_on` produces no dep findings.

Deterministic Python, no LLM. Fixture + finding-set style of test_scripts.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
from check_traceability import check as check_trace  # noqa: E402


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


def _write_prd(proj: Path, name: str, body: str) -> None:
    (proj / "docs" / "product" / "prds" / name).write_text(body)


def test_dep_dangling(tmp_path):
    """A PRD depending on a ghost ID (PRD-GHOST, never declared) trips
    `dep_dangling` (error)."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, "a.md", """---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
depends_on: [PRD-GHOST]
---
""")
    g = build_graph(proj)
    findings = check_trace(g)
    dangling = [f for f in findings if f["check"] == "dep_dangling"]
    assert dangling, f"expected dep_dangling for PRD-GHOST; got: {[f['check'] for f in findings]}"
    assert dangling[0]["severity"] == "error", f"dep_dangling must be error: {dangling[0]}"
    assert dangling[0]["artifact_id"] == "PRD-A"


def test_dep_dangling_silent_when_target_resolves(tmp_path):
    """A `depends_on` whose target exists produces no dep_dangling."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, "a.md", """---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
depends_on: [PRD-B]
---
""")
    _write_prd(proj, "b.md", """---
id: PRD-B
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    g = build_graph(proj)
    findings = check_trace(g)
    assert not any(f["check"] == "dep_dangling" for f in findings), (
        f"resolvable depends_on must not flag dep_dangling; got: {findings}"
    )


def test_v1_spec_no_depends_on_produces_no_dep_findings(tmp_path):
    """Back-compat: a v1 PRD with no depends_on field at all yields no
    dep_dangling / dep_cycle findings — the new edge is optional, absence is a
    clean empty default."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, "a.md", """---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    g = build_graph(proj)
    findings = check_trace(g)
    dep_checks = {f["check"] for f in findings if f["check"] in ("dep_dangling", "dep_cycle")}
    assert dep_checks == set(), f"v1 spec must produce no dep findings; got: {dep_checks}"
