---
phase: 3
title: "Time and Dependencies"
status: pending
priority: P1
effort: "2d"
dependencies: [2]
---

# Phase 3: Time and Dependencies

## Overview

Add the TIME dimension: `target_date` (ISO) on PRD+Epic, a new `depends_on: [ID]` graph edge, deterministic ordering warnings, an out-of-gate overdue advisory, and time views (roadmap+deadline / Mermaid gantt). **Trade-off T1:** `depends_on` permits cycles → a `dep_cycle` detector + cycle-safe renderers are a HARD PREREQUISITE, built and tested BEFORE the edge is parsed into the graph.

## Key Insights (grounded — from researcher reports)

- **Cycle detection (R1):** 3-color DFS chosen over Kahn — returns the cycle PATH in one pass, stdlib-only, deterministic with sorted iteration. `find_dep_cycles(adj: dict[str,list[str]]) -> list[list[str]]` lives in `check_traceability.py` (owns all graph-walk checks). Cycle path includes the repeated closing node (`["A","B","A"]`). Edit surface is tiny: `spec_graph.py` +1 line, `check_traceability.py` +3 funcs, `check_consistency.py` +1 func.
- `spec_graph._closure()` (lines 226-237) ALREADY guards `downstream()` with a visited-set — so existing traversal won't hang; only NEW renderers walking `depends_on` need the same guard (`if node in visited: continue`).
- **Determinism vs today:** structural checks (`dep_cycle`, `dep_order`, `time_child_late`) are PURE (no `today`) → fully deterministic, safe to gate. Anything consuming `today` (`overdue`, `time_realism`) is **advisory/LLM only, never a structural gate** — preserves G-A4.
- **time_realism (R2):** the SCRIPT pre-computes `days_remaining = (target_date - today).days` + `child_story_count`; the LLM never does date math. AND-logic: flag only if `size==L AND child_story_count>=6 AND days_remaining<21`; else `{finding:null}`; `cited_data` required.

## Requirements

- **Functional:** `target_date` parse + ordering checks; `depends_on` edge in graph; `dep_cycle` (error) + `dep_dangling` (error) + `dep_order` (warn) + `time_child_late` (warn); `time_advisory.py --today` overdue; `time_realism` LLM warn; roadmap+deadline + gantt views.
- **Non-functional:** new renderers cycle-safe (terminate — no hang/RecursionError — on a cyclic graph); structural layer deterministic; `depends_on` allowed on PRD+Epic only.

## Architecture

```yaml
# PRD + Epic frontmatter — add:
target_date: 2026-09-30      # ISO, optional
depends_on: [PRD-BILLING]    # list of IDs, new edge; PRD+Epic only
```

**Build order (T1-safe):**

1. **3a — cycle safety FIRST (no edge yet):** add `find_dep_cycles` + `_check_dep_cycles` (`dep_cycle` error) to `check_traceability.py`; add the visited-set guard helper for renderers. Test against synthetic adjacency dicts.
2. **3b — wire the edge:** `spec_graph._node_from_artifact` += `"depends_on": fm.get("depends_on") or []` (sorted; uniform empty default on ALL node types is harmless — UQ2); `dep_dangling` in **`check_traceability.py`** (the dangling family home, beside `dangling_link`/`dep_cycle` — reconciles R1↔RT1 F2); type-guard: a NON-EMPTY `depends_on` on a story/goal → reuse existing **`invalid_type`** (F7 + UQ2), not a new ID.
3. **3c — time fields + ordering:** `target_date` parse; `time_child_late` (child date > parent) + `dep_order` (A depends_on B but A.date < B.date) — both deterministic, in-check.
4. **3d — advisory + views:** new `time_advisory.py --today <ISO>` (overdue, outside gate); `render_mermaid.py` gantt (Q47); `render_html.py` roadmap+deadline column + cycle-safe `depends_on` arrows; `i18n_labels.py` VI labels; `time_realism` LLM check (R2 scaffold).

### `find_dep_cycles` (R1, **iterative** 3-color DFS — F4: no RecursionError on long chains)

```python
def find_dep_cycles(adj):                       # adj: dict[str, list[str]]; iterative (no recursion)
    WHITE, GRAY, BLACK = 0, 1, 2
    color, cycles = {}, []
    for root in sorted(adj):                    # sorted → determinism
        if color.get(root, WHITE) != WHITE:
            continue
        color[root] = GRAY; path = [root]
        stack = [(root, iter(sorted(adj.get(root, []))))]   # explicit stack, not call stack
        while stack:
            node, it = stack[-1]
            advanced = False
            for nbr in it:
                if nbr not in adj:              # dangling → dep_dangling owns it
                    continue
                c = color.get(nbr, WHITE)
                if c == GRAY:                   # back-edge → cycle
                    cycles.append(path[path.index(nbr):] + [nbr])
                elif c == WHITE:
                    color[nbr] = GRAY; path.append(nbr)
                    stack.append((nbr, iter(sorted(adj.get(nbr, [])))))
                    advanced = True
                    break
            if not advanced:                    # node exhausted → backtrack
                color[node] = BLACK; path.pop(); stack.pop()
    return cycles
```

### Cycle-safe renderer guard (R1)

```python
seen, stack = set(), [root]
while stack:
    node = stack.pop()
    if node in seen:        # ← same guard as _closure() lines 231-233
        continue
    seen.add(node)
    stack.extend(sorted(dep_adj.get(node, [])))
```

### `time_realism` LLM input (R2 — script pre-computes)

Script assembles per-epic: `{artifact_id, size, horizon, target_date, today_date, days_remaining, child_story_count, incomplete}`. **`today_date` is injected via an optional `--today` flag** on the validate path (default = real today; evals/tests PIN it so the gate is reproducible — F3). Prompt: flag only if `size=="L" AND child_story_count>=6 AND days_remaining<21`; any anchor null → `{finding:null, reason:"missing_anchor"}`; else `{finding:null, reason:"below_threshold"}`. Finding REQUIRES `context.cited_data` (size, child_story_count, days_remaining, target_date, horizon) + `threshold_crossed`. No date math by the LLM. No prose, no velocity speculation.

## Related Code Files

- Modify: `assets/templates/prd.md`, `assets/templates/epic.md` (+`target_date`, +`depends_on`).
- Modify: `scripts/spec_graph.py` (`_node_from_artifact` +`depends_on` sorted; snapshot += `target_date`/`depends_on`).
- Modify: `scripts/check_traceability.py` (+`_build_dep_adj`, `find_dep_cycles` [iterative], `_check_dep_cycles` → `dep_cycle`; **`dep_dangling` here too** — same dangling family as `dangling_link`; call-sites in `check()`).
- Modify: `scripts/check_consistency.py` (`target_date` ISO-shape check; `time_child_late`; `dep_order`; type-guard for `depends_on` on wrong artifact types → existing `invalid_type`).
- Create: `scripts/time_advisory.py` (`--today <ISO>` → `overdue` advisory JSON; never in `--validate` gate).
- Modify: `scripts/render_mermaid.py` (gantt), `scripts/render_html.py` (roadmap+deadline col, cycle-safe dep arrows), `scripts/visualize.py` (route `time` view), `scripts/i18n_labels.py` (VI).
- Modify: `--summary` generator — add a TIME line (F9 / Q35: horizon spread + nearest `target_date`), parallel to the competition line in Phase 4.
- Modify: `references/validation-rules-spec.md` (rows: `dep_cycle`, `dep_dangling`, `dep_order`, `time_child_late`, `overdue`, `time_realism`).
- Create: `scripts/tests/test_dep_cycle.py`, `scripts/tests/test_time_advisory.py`; extend `test_check_traceability.py`, `test_check_consistency.py`.

## Tests First (TDD)

| Test | Scenario | Expect |
|------|----------|--------|
| `test_no_cycle_returns_empty` | `{A:[B],B:[C]}` | `[]` |
| `test_self_loop_single_node` | `{A:[A]}` | `[["A","A"]]` |
| `test_two_node_mutual` | `{A:[B],B:[A]}` | one cycle, both IDs |
| `test_three_node_chain_cycle` | `{A:[B],B:[C],C:[A]}` | 4-element path |
| `test_cycle_plus_valid_dangling` | `{A:[B,X],B:[A]}`, X absent | only A↔B; X skipped |
| `test_find_cycles_long_chain` | ~2000-node linear chain | `[]`, no `RecursionError` (iterative) |
| `test_dep_cycle_finding_shape` | cyclic spec | `dep_cycle` error, `context.cycle` set |
| `test_renderer_terminates_on_cycle` | HTML render of cyclic graph | terminates (pytest-timeout), no hang/RecursionError |
| `test_dep_dangling` | `depends_on:[PRD-GHOST]` | `dep_dangling` error |
| `test_time_child_late` | epic date > prd date | `time_child_late` warn |
| `test_dep_order` | A dep B, A.date<B.date | `dep_order` warn |
| `test_time_advisory_overdue` | `--today 2026-12-01`, target 2026-09 | overdue (separate script) |
| eval `time-realism` TP/borderline/missing-anchor | R2 fixtures | flag / no-flag / `missing_anchor` |

## Implementation Steps

1. **RED:** author `test_dep_cycle.py` (5 R1 cases) + cycle-safe renderer test — all fail (functions absent).
2. Implement `find_dep_cycles` + `_check_dep_cycles` + renderer guard helper → GREEN (no edge wired yet).
3. **RED:** dep_dangling / target_date / time_child_late / dep_order tests.
4. Wire `depends_on` passthrough + the consistency checks → GREEN.
5. Build `time_advisory.py` + its test (overdue, `--today`).
6. Views: gantt + roadmap-deadline + cycle-safe HTML arrows + VI labels.
7. `time_realism` LLM check (script pre-computes anchors; document scaffold in validation-rules-spec) + 3 evals.
8. Full pytest + evals green; refactor.

## Success Criteria

- [ ] G-D1 `target_date` parses on PRD+Epic; optional.
- [ ] G-D2 `depends_on` edge in graph; `dep_dangling` error on ghost ID.
- [ ] G-D3 (T1) `dep_cycle` error on self/2/3-node cycles; iterative (no `RecursionError` on long chains); every new renderer terminates on a cyclic graph (pytest-timeout, not a wall-clock SLA).
- [ ] G-D4 `time_child_late` deterministic warn.
- [ ] G-D5 `overdue` advisory via `time_advisory.py --today` (NOT in gate).
- [ ] G-D6 (T2) `time_realism` flags only with all anchors + cites data; missing anchor → no-finding; borderline → no-finding.
- [ ] G-A4 structural layer deterministic (sorted); G-B1/B2 split intact.

## Risk Assessment

- **(T1) cycle hangs a renderer** → guard helper reused everywhere walking `depends_on`; explicit terminate-on-cycle test. CAO→mitigated.
- **depends_on on unsupported type** → type-guard → existing `invalid_type`; scoped to PRD+Epic. TB.
- **time_realism non-determinism via today** → today-consuming checks are advisory/LLM only, never gate; evals pin `today_date`. TB.
- **R1 open Q (variable-length cycle context)** → consumers read `detail` string; `context.cycle` is informational. LOW.

## Goal Gates Covered

G-D1..G-D6 (+ G-A4, G-B1/B2).
