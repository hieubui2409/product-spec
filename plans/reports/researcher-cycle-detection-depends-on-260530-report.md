# Cycle Detection for `depends_on` Edges — Plan-Ready Spec

**Date:** 2026-05-30 | **Target skill:** `cleanmatic:product-spec`

---

## 0. Grounding Observations

From reading the three source files:

- **`_f()` helper** is identical in both checker scripts (fields: `check`, `severity`, `artifact_id`, `file`, `detail`, `context`). Use the same signature.
- **`_closure()` in `spec_graph.py`** (lines 226-237) uses a visited-set; the `parents_of()` already drops self-edges (`if par != child`). These ONLY guard the existing hierarchy edges. A new `depends_on` adjacency is separate; same guard pattern must be replicated.
- **`check_traceability.check()`** iterates `graph["nodes"]` and emits `_f(...)` findings — natural home for dep_cycle.
- **`check_consistency.check()`** handles shape/enum checks — natural home for `dep_dangling` (depends_on → non-existent ID) but NOT cycle detection.
- Graph nodes **do not carry `depends_on`** today; it must be read from frontmatter separately or added to `_node_from_artifact`.

---

## 1. Algorithm: DFS 3-color

**Pick: DFS 3-color (white/gray/black).**

Rationale over Kahn's topo-sort:
- **Reports the cycle path**, not just its existence. Kahn's detects cycle presence (nodes not reached) but extracting the path requires additional backtracking work.
- **Stdlib-only**: both are stdlib; DFS needs only a dict + list.
- **Determinism**: sorted node iteration + sorted neighbor iteration → identical output ordering every run.
- **All cycles**: the loop over `sorted(adj)` ensures every strongly-connected component is found, not just the first.
- Kahn would be preferable if "count nodes in each SCC" were needed — it isn't.

### Function body sketch (~20 lines)

```python
def find_dep_cycles(adj: dict[str, list[str]]) -> list[list[str]]:
    """
    DFS 3-color over depends_on adjacency.
    adj: {node_id: [dep_id, ...]} — only IDs present as keys matter.
    Returns list of cycle paths, each a list of IDs forming the loop.
    Deterministic: sorted node + neighbor iteration.
    """
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n: WHITE for n in adj}
    path: list[str] = []
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in sorted(adj.get(node, [])):
            if neighbor not in color:
                continue  # dangling ref — dep_dangling handles it
            if color[neighbor] == GRAY:
                # found back-edge: extract cycle from path
                idx = path.index(neighbor)
                cycles.append(path[idx:] + [neighbor])
            elif color[neighbor] == WHITE:
                dfs(neighbor)
        path.pop()
        color[node] = BLACK

    for node in sorted(adj):
        if color[node] == WHITE:
            dfs(node)
    return cycles
```

**Recursion depth note**: `depends_on` spans PRDs/Epics only (not the full story hierarchy). Real-world graphs rarely exceed 20-30 nodes here. Recursion depth is not a concern; no need for an iterative rewrite unless the spec explicitly allows cross-type depends_on graphs of 1000+ nodes.

**"Report all cycles"**: yes, the above reports all cycles. Rationale: a 3-node ring A→B→C→A is one finding per back-edge found, which is meaningful (each back-edge = one actionable fix for the PO).

---

## 2. Ownership: `check_traceability.py`

**Owner: `check_traceability.check()`** — not `check_consistency`.

Reasoning:
- Cycle detection is a **graph reachability** check (traversal), not a shape/enum check. `check_traceability` already owns `dangling_link`, `orphan_*`, `unaddressed_parent` — all graph-walk checks.
- `check_consistency` owns closed-enum + shape checks. `dep_dangling` (depends_on → non-existent ID) belongs in `check_consistency` since it mirrors the existing `dangling_link` shape check pattern.

### Integration points in `check_traceability.py`

```python
# 1. New helper — add after existing _f() def, before check()
def _build_dep_adj(graph: Dict[str, Any]) -> Dict[str, List[str]]:
    """Build depends_on adjacency from graph nodes.
    Only includes nodes that have a non-empty depends_on list."""
    adj: Dict[str, List[str]] = {}
    for n in graph["nodes"]:
        deps = n.get("depends_on") or []
        if isinstance(deps, list) and deps:
            adj[n["id"]] = [str(d) for d in deps]
    return adj

# 2. Call site — inside check(), after existing loop, before parse_error block:
dep_adj = _build_dep_adj(graph)
if dep_adj:
    findings.extend(_check_dep_cycles(dep_adj, node_ids, graph))

# 3. New function:
def _check_dep_cycles(
    adj: Dict[str, List[str]],
    node_ids: Set[str],
    graph: Dict[str, Any],
) -> List[Dict[str, Any]]:
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    cycles = find_dep_cycles(adj)
    findings = []
    for cycle in cycles:
        # Representative node = first ID in cycle path (sorted for determinism)
        rep_id = cycle[0]
        node = nodes_by_id.get(rep_id, {"id": rep_id, "file": None})
        findings.append(_f(
            "dep_cycle",
            "error",
            node,
            f"Circular dependency detected: {' -> '.join(cycle)}.",
            cycle=cycle,
        ))
    return findings
```

**`depends_on` must be added to `_node_from_artifact`** in `spec_graph.py`:

```python
# In _node_from_artifact(), add one line:
"depends_on": fm.get("depends_on") or [],
```

This is the only edit to `spec_graph.py`. All else is additive in the checker scripts.

---

## 3. Finding JSON Shape

Exact field names verified against `_f()` in both checker scripts:

```json
{
  "check": "dep_cycle",
  "severity": "error",
  "artifact_id": "PRD-AUTH",
  "file": "prds/auth.md",
  "detail": "Circular dependency detected: PRD-AUTH -> PRD-BILLING -> PRD-AUTH.",
  "context": {
    "cycle": ["PRD-AUTH", "PRD-BILLING", "PRD-AUTH"]
  }
}
```

Notes:
- `artifact_id` = first node in the cycle path (representative; deterministic via sorted iteration).
- `context.cycle` = full path including the repeated closing node, so readers can render `A → B → A` without post-processing.
- Self-loop example: `{"cycle": ["PRD-AUTH", "PRD-AUTH"]}` — path length 2, both entries same ID.
- `context` is `None` when empty (per existing `_f()` pattern: `context or None`); here it's always non-None since cycle is always present.

---

## 4. Cycle-Safe Render Pattern

Any new renderer traversing `depends_on` edges (Gantt, timeline, dependency view) must guard against cycles:

```python
def walk_deps(start_id: str, depends_on_adj: dict[str, list[str]]) -> list[str]:
    """Cycle-safe BFS/DFS over depends_on. Returns reachable IDs (excluding start)."""
    visited: set[str] = set()
    stack = list(depends_on_adj.get(start_id, []))
    while stack:
        node = stack.pop()
        if node in visited:
            continue          # visited-set guard — same pattern as _closure()
        visited.add(node)
        stack.extend(depends_on_adj.get(node, []))
    return sorted(visited)
```

Key points:
- `if node in visited: continue` — identical to `_closure()` lines 231-233; no new pattern, same proven guard.
- Guard must be checked **before** `stack.extend`, not after (the current `_closure()` does this correctly).
- Do NOT inline `adj.get(node, [])` without the guard — that's how renderers hang on cycles.

---

## 5. Pytest Test Cases

File: `.claude/skills/product-spec/scripts/tests/test_dep_cycle.py`

```
test_no_cycle_returns_empty
  Scenario: adj = {A: [B], B: [C]} — no cycle; find_dep_cycles returns [].

test_self_loop_single_node
  Scenario: adj = {A: [A]} — self-loop; returns one cycle path ["A", "A"].

test_two_node_mutual
  Scenario: adj = {A: [B], B: [A]} — A→B→A; returns one cycle containing both IDs.

test_three_node_chain_cycle
  Scenario: adj = {A: [B], B: [C], C: [A]} — 3-node ring; returns cycle path with 4 elements ["A","B","C","A"] (or equivalent starting point).

test_cycle_plus_valid_dangling
  Scenario: adj = {A: [B, X], B: [A]} — A↔B cycle plus dangling ref X (not in adj);
  find_dep_cycles returns only the A→B cycle; X is silently skipped (dangling = dep_dangling's job).
```

Test structure note: `find_dep_cycles` takes only the adjacency dict — it's pure stdlib, no graph object needed. Tests should import it directly from `check_traceability` (or a shared module if extracted). This keeps tests fast and isolated from file I/O.

**Integration test** (1 additional, for `_check_dep_cycles` with full graph shape):
```
test_dep_cycle_finding_shape
  Scenario: minimal graph dict with two nodes having depends_on cycle;
  verify emitted finding has check="dep_cycle", severity="error", context.cycle is list.
```

---

## 6. Determinism

Three levers, all required:

| Point | Rule |
|---|---|
| `find_dep_cycles` node iteration | `for node in sorted(adj):` — alphabetical DFS entry order |
| neighbor iteration | `for neighbor in sorted(adj.get(node, [])):` — identical tie-breaking |
| `_check_dep_cycles` output order | findings appended in DFS discovery order; since DFS entry is sorted, output is stable |

**No `set` iteration**: `adj` keys are iterated via `sorted()`, not set enumeration. This is the same pattern `spec_graph.py` uses in `load_artifacts` (`for path in sorted(product_dir.glob(...))`).

**Test compatibility**: existing test files (`test_scripts.py`, `test_visualize.py`) assert exact JSON text. The `find_dep_cycles` output will be deterministic as long as the adj dict is built from sorted node lists — which `_build_dep_adj` must ensure via `sorted()` on the `depends_on` YAML list values.

---

## 7. `dep_dangling` ownership (bonus: check_consistency.py)

For completeness — the companion check for `depends_on` pointing to a non-existent ID:

**Owner: `check_consistency.check()`** — not `check_traceability`.

Rationale: mirrors the shape of existing `self_reference` check (lines 193-223). It's a field-value-vs-known-IDs check, not a graph traversal.

```python
# In check_consistency.check(), after _self_reference() call:
findings.extend(_dep_dangling(graph))

def _dep_dangling(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    node_ids = {n["id"] for n in graph["nodes"]}
    findings = []
    for n in graph["nodes"]:
        deps = n.get("depends_on") or []
        if not isinstance(deps, list):
            continue  # invalid_type catches this already
        for ref in deps:
            if str(ref) not in node_ids:
                findings.append(_f(
                    "dep_dangling", "error", n,
                    f"{n['id']} depends_on unknown ID {ref!r}.",
                    ref=ref,
                ))
    return findings
```

Finding shape:
```json
{
  "check": "dep_dangling",
  "severity": "error",
  "artifact_id": "PRD-AUTH",
  "file": "prds/auth.md",
  "detail": "PRD-AUTH depends_on unknown ID 'PRD-NONEXISTENT'.",
  "context": {"ref": "PRD-NONEXISTENT"}
}
```

---

## 8. Summary: Minimal Edit Surface

| File | Change |
|---|---|
| `spec_graph.py` | `_node_from_artifact`: add `"depends_on": fm.get("depends_on") or []` (1 line) |
| `check_traceability.py` | Add `find_dep_cycles()` + `_build_dep_adj()` + `_check_dep_cycles()` + call site in `check()` |
| `check_consistency.py` | Add `_dep_dangling()` + call site in `check()` |
| `scripts/tests/test_dep_cycle.py` | New file — 5+ test functions (pure unit, no I/O) |

No changes to `build_edges`, `build_graph`, `_closure`, or any renderer. The `depends_on` adjacency is a separate graph layer, not wired into the existing hierarchy edges.

---

**Status:** DONE

**Summary:** Picked DFS 3-color over Kahn's for cycle-path extraction; assigned `dep_cycle` to `check_traceability`, `dep_dangling` to `check_consistency`; all field shapes verified against live `_f()` helper; 5 test cases specified covering self-loop, 2-node, 3-node, and dangling-with-cycle combinations.

**Unresolved questions:**

1. **`depends_on` allowed types**: Should it be scoped to `prd`/`epic` only, or also `story`/`goal`? The shape check in `check_consistency` can add a `_dep_type_guard` if cross-type depends_on should be an error.
2. **Max cycle path length in finding**: If a 10-node ring exists, the `context.cycle` list has 11 entries. Fine for JSON; confirm the strict-gate / LLM summary layer can handle variable-length context arrays.
3. **Renderer integration scope**: This report does not cover how a Gantt/timeline view builds its layout from `depends_on`; only the cycle-safe traversal guard is specified here. That view's full spec is out of scope.
