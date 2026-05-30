"""Phase 3 — TIME/DEPENDENCIES, trade-off T1 (cycle safety FIRST).

The `depends_on: [ID]` edge permits a circular dependency (A->B->C->A), which is
meaningless for a product spec. Per design-report §0.1 (T1) and goal G-D3, a
`dep_cycle` detector plus cycle-safe renderers are a HARD PREREQUISITE built and
tested BEFORE the edge is parsed into the graph.

This module is the RED spec for:
  - `check_traceability.find_dep_cycles(adj)` — iterative 3-color DFS over an
    adjacency map. Returns the cycle PATH including the repeated closing node
    (`["A","B","A"]`). Sorted iteration -> deterministic output (G-A4).
  - the `dep_cycle` finding (error) emitted by `check_traceability.check()` with
    `context.cycle` carrying the path.
  - every NEW renderer that walks `depends_on` terminating on a cyclic graph
    (visited-set guard) — NO hang, NO RecursionError (G-D3).

All checks here are deterministic Python — no LLM, no judgment (G-B1).
Mirrors the fixture-build + finding-set assertion style of test_scripts.py.
"""

import signal
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
from check_traceability import check as check_trace  # noqa: E402


# ---------------------------------------------------------------------------
# Hard wall-clock watchdog. pytest-timeout is intentionally NOT a dependency of
# this skill (stdlib-only test layer), so a renderer that hangs on a cyclic
# graph would otherwise stall the whole suite forever. A POSIX SIGALRM watchdog
# converts "hangs" into a deterministic test FAILURE (the intended RED reason is
# "function absent", but this guarantees the suite can never wedge on a cycle).
# ---------------------------------------------------------------------------

@contextmanager
def _hard_timeout(seconds: int = 5):
    if not hasattr(signal, "SIGALRM"):  # non-POSIX: best-effort, just run it
        yield
        return

    def _raise(signum, frame):
        raise TimeoutError(f"operation did not terminate within {seconds}s (cycle hang?)")

    prev = signal.signal(signal.SIGALRM, _raise)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, prev)


# ---------------------------------------------------------------------------
# find_dep_cycles — pure adjacency-map cases (no spec on disk).
# ---------------------------------------------------------------------------


def test_no_cycle_returns_empty():
    from check_traceability import find_dep_cycles
    assert find_dep_cycles({"A": ["B"], "B": ["C"], "C": []}) == []


def test_self_loop_single_node():
    from check_traceability import find_dep_cycles
    assert find_dep_cycles({"A": ["A"]}) == [["A", "A"]]


def test_two_node_mutual():
    from check_traceability import find_dep_cycles
    cycles = find_dep_cycles({"A": ["B"], "B": ["A"]})
    assert len(cycles) == 1, f"expected exactly one cycle, got {cycles}"
    assert set(cycles[0]) == {"A", "B"}, f"cycle must contain both nodes: {cycles[0]}"
    # Path closes on the node it started from (3-color back-edge convention).
    assert cycles[0][0] == cycles[0][-1], f"path must close on its start node: {cycles[0]}"


def test_three_node_chain_cycle():
    from check_traceability import find_dep_cycles
    cycles = find_dep_cycles({"A": ["B"], "B": ["C"], "C": ["A"]})
    assert len(cycles) == 1, f"expected one cycle, got {cycles}"
    # 3 distinct nodes + the repeated closing node = a 4-element path.
    assert len(cycles[0]) == 4, f"expected a 4-element closed path, got {cycles[0]}"
    assert set(cycles[0]) == {"A", "B", "C"}
    assert cycles[0][0] == cycles[0][-1]


def test_cycle_plus_valid_dangling():
    """A dangling target (X, absent from adj) is skipped by the cycle walk —
    dep_dangling owns the missing-ID report, not find_dep_cycles. Only the A<->B
    cycle is returned."""
    from check_traceability import find_dep_cycles
    cycles = find_dep_cycles({"A": ["B", "X"], "B": ["A"]})  # X not a key
    assert len(cycles) == 1, f"X must not produce a cycle; got {cycles}"
    assert set(cycles[0]) == {"A", "B"}, f"only A<->B expected: {cycles[0]}"


def test_find_cycles_long_chain():
    """~2000-node linear chain must NOT raise RecursionError — the detector is
    iterative (explicit stack), not recursive (G-D3 / design-report F4)."""
    from check_traceability import find_dep_cycles
    n = 2000
    adj = {f"N{i}": [f"N{i+1}"] for i in range(n)}
    adj[f"N{n}"] = []
    with _hard_timeout(5):
        assert find_dep_cycles(adj) == []


def test_find_cycles_deterministic():
    """Sorted iteration -> identical output across runs (G-A4 determinism)."""
    from check_traceability import find_dep_cycles
    adj = {"B": ["C"], "A": ["B"], "C": ["A"]}
    first = find_dep_cycles(adj)
    second = find_dep_cycles(adj)
    assert first == second, f"non-deterministic cycle output: {first!r} vs {second!r}"


# ---------------------------------------------------------------------------
# Shared minimal spec scaffold (PRODUCT + BRD) so the graph builds clean; the
# test layers the cyclic PRDs on top. Same style as test_risk_complete._scaffold.
# ---------------------------------------------------------------------------

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


def _write_cyclic_prds(proj: Path) -> None:
    """Two PRDs that depend on each other -> A<->B dep cycle."""
    prds = proj / "docs" / "product" / "prds"
    prds.joinpath("a.md").write_text("""---
id: PRD-A
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
depends_on: [PRD-B]
---
""")
    prds.joinpath("b.md").write_text("""---
id: PRD-B
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
depends_on: [PRD-A]
---
""")


# ---------------------------------------------------------------------------
# dep_cycle finding shape — via the full check_traceability.check().
# ---------------------------------------------------------------------------


def test_dep_cycle_finding_shape(tmp_path):
    """A cyclic depends_on spec produces a `dep_cycle` error finding whose
    `context.cycle` carries the offending path."""
    proj = _scaffold(tmp_path)
    _write_cyclic_prds(proj)
    g = build_graph(proj)
    findings = check_trace(g)
    cyc = [f for f in findings if f["check"] == "dep_cycle"]
    assert cyc, f"expected a dep_cycle finding; got checks: {[f['check'] for f in findings]}"
    assert cyc[0]["severity"] == "error", f"dep_cycle must be error severity: {cyc[0]}"
    ctx = cyc[0].get("context") or {}
    assert "cycle" in ctx, f"dep_cycle finding must carry context.cycle: {cyc[0]}"
    assert {"PRD-A", "PRD-B"} <= set(ctx["cycle"]), f"cycle path must name both PRDs: {ctx['cycle']}"


# ---------------------------------------------------------------------------
# Cycle-safe renderer — every NEW renderer walking depends_on must terminate on
# a cyclic graph (visited-set guard). RED: the time view / depends_on-arrow
# renderer does not exist yet, so this fails on AttributeError (intended), not a
# hang. The SIGALRM watchdog backstops the "hang" failure mode either way.
# ---------------------------------------------------------------------------


def test_renderer_terminates_on_cycle(tmp_path):
    """Render the HTML `time` view on a graph with a depends_on cycle; it must
    return a string and NOT hang / RecursionError (G-D3, trade-off T1)."""
    import render_html

    proj = _scaffold(tmp_path)
    _write_cyclic_prds(proj)
    g = build_graph(proj)

    with _hard_timeout(5):
        out = render_html.write(proj, "time", "mermaid", "", g, lang="en")
    assert out.exists(), "time-view HTML must be written even on a cyclic graph"
    html = out.read_text(encoding="utf-8")
    assert "PRD-A" in html and "PRD-B" in html, "cyclic nodes must still render"
