---
phase: 1
title: "Foundation"
status: done
priority: P1
effort: "0.5d"
dependencies: []
---

# Phase 1: Foundation — shared assembler + `ancestors()`

## Overview

The deterministic, script-owned core both features reuse: a graph `ancestors()` edge-walk + an `assemble_digest` module that turns (selection + layer-filter + depth) into an ordered **digest model**. No HTML, no LLM. Tests-first. **Re-founded after red-team C1**: Vision and BRD are **not graph nodes** (verified: `build_nodes` `spec_graph.py:64-81` nodifies only goals for a BRD; vision is an isolated node, no edges), so they cannot be reached by ancestor traversal — they are loaded as **singletons** and prepended.

## Requirements

- **Functional**
  - `spec_graph.ancestors(graph, node_id) -> Set[str]` — reverse edge walk (child→parent over `{from,to}`), the inverse of `downstream()` (`spec_graph.py:192-205`). Returns the **goals + PRD/epic chain only** (e.g. `ancestors("PRD-AUTH-E1-S1") == {"PRD-AUTH-E1","PRD-AUTH","BRD-G1"}`). It **does not and cannot** return Vision or a BRD container — they are not nodes. Do **not** add phantom Vision/BRD edges (would break `test_mermaid_tree_has_no_phantom_brd_node` + `test_mermaid_tree_skips_vision_node`).
  - `assemble_digest.build_digest(graph, artifacts, select, layers, depth)` → ordered list:
    - **Vision + BRD context = singletons.** Load `vision.md` + `brd.md` via `load_artifacts()` (they ARE parsed, just not nodified) and **prepend** them as `role=ancestor` entries whenever the selection has descendants and `--layers` includes their type. This is a documented assembler step, separate from `ancestors()`.
    - goals/PRD/epic/story chain from `ancestors()` + `downstream()`.
    - `select`: `"all"` | single ID | comma-list. `layers`: subset of `{vision,brd,prd,epic,story}` (default all). `depth`: `context`(default)|`full`|`brief`.
    - **Emit as a canonical SORTED list** (hierarchy order then ID), independent of `nodes[]`/set iteration order — `downstream()`/`ancestors()` return sets, so sort before emit (determinism, red-team M6).
  - **struct compaction** (deterministic): frontmatter + title + key fields (`ac` stories, `metrics` goals, goals list for BRD); drop long narrative.
  - **`--layers` precedence (D2, locked) + warning**: `select` chooses the subtree; `--layers` filters which *types* appear; an excluded type is dropped — **even the selected root's own type**. When `--layers` drops the selected root's type (e.g. `--export PRD-AUTH --layers story`), the assembler emits a **provenance warning** entry ("`--layers` excluded the PRD/epic context for PRD-AUTH") so the read-once doc isn't silently context-less (red-team H5). Precedence itself is **not changed** (owner-locked).
- **Non-functional**: stdlib+pyyaml; **deterministic**; reuse `load_artifacts()` + `downstream()`; file <200 LOC.

## Architecture

Digest element: `{id, type, role: ancestor|target|descendant, verbosity: full|struct, frontmatter, title, body, ac|None}`.
Algorithm: (1) resolve target set from `select` (`all` = every artifact: vision+brd+all goals+PRDs+epics+stories); (2) `ancestors()` for goal/PRD/epic context; (3) **prepend Vision+BRD singletons**; (4) depth→verbosity (`context`: ancestors/singletons `struct`, target+desc `full`; `full`: all full; `brief`: all struct); (5) `--layers` filter (+ warning if root type dropped); (6) emit canonical sorted list. `ancestors()` mirrors `downstream()`'s child-map, inverted to a parent-map.

## Related Code Files

- Create: `scripts/assemble_digest.py`
- Create: `scripts/tests/test_assemble_digest.py` (+ fixture **with `vision.md` AND `brd.md`** — the existing `valid-spec` fixture has no vision.md, red-team C1b)
- Modify: `scripts/spec_graph.py` (add `ancestors()` after `downstream()` ~L205, before `write_snapshot()` ~L208)

## Implementation Steps

1. Tests first: assert `ancestors()` == goals+PRD chain (NOT vision/brd); assert Vision+BRD **singletons appear** in a `--depth context` PRD digest with `role=ancestor, verbosity=struct`; assert `--layers story` drops context **and emits the warning**; assert digest is a sorted list **independent of shuffled `nodes[]` order**; assert determinism (call twice → equal).
2. Add `ancestors(graph, id)` (invert `downstream()`'s map).
3. Implement `build_digest(...)` incl. Vision/BRD singleton prepend + `_struct_compact()`.
4. Run pytest to green.

## Success Criteria

- [ ] `ancestors()` returns goals+PRD/epic chain; never vision/BRD; no phantom edges (existing 2 tests still pass).
- [ ] Vision + BRD render in the digest via singleton prepend (fixture has vision.md + asserts it).
- [ ] Digest is a canonical sorted list; deterministic + shuffle-independent.
- [ ] `--layers` precedence preserved + warning emitted when root type dropped.
- [ ] New tests green; existing 92 untouched/green.

## Risk Assessment

- **C1 (vision/BRD not graph-reachable)** → singleton prepend; `ancestors()` stays pure edge walk; documented.
- **C1b fixture gap** → fixture MUST include vision.md + assert it in digest.
- **M6 set-order leak** (`downstream`/`ancestors` return sets) → sort before emit + shuffle-independence test.
- **>200 LOC** → split selection-resolver / `_struct_compact` helpers.
