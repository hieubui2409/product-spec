---
phase: 1
title: "body-hash-foundation"
status: done
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: body-hash-foundation

## Overview
Add a per-node `body_hash` to the spec graph (the missing cache key the whole memory layer depends on) and fix the latent impact-pass gap where body-only edits go undetected. One change, two wins. **Blocker for P6.**

## Requirements
- Functional: every artifact node carries `body_hash = sha256(body)[:8]`; snapshot persists it; `--validate` impact-pass (Step 2.5) detects a node whose body changed even when frontmatter is unchanged.
- Non-functional: deterministic (same body → same hash); back-compatible (old snapshots without `body_hash` → node treated as "changed" once, safe re-validate; never crash).

## Architecture
- `spec_graph._node_from_artifact` already receives `body`. Add `"body_hash": hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]` to the returned node dict (`spec_graph.py:116`). Goals (`_node_from_goal`) have no standalone body → `body_hash: None` — keep `None` for back-compat, document.
- Snapshot already serializes the full node dict → `body_hash` rides along automatically (no `write_snapshot` change).
- **DRY home for the changed-field rule (red-team RT-1/RT-2 fix):** the "which fields make a node changed" tuple is currently DUPLICATED in 3 places — `render_ascii.delta()` (`render_ascii.py:682`), `validation-rules-spec.md:148` (prose), and the impact-pass prose (`workflow-validate.md:56`). Hoist it into ONE home in spec_graph: a module constant `CHANGED_FIELDS = ("status","scope","moscow","horizon","size","body_hash")` **plus** a function `changed_nodes(current, previous) -> list[str]` (node ids whose any `CHANGED_FIELDS` value differs between two snapshot node-dicts). `render_ascii.delta()` is refactored to import/use it; the impact-pass prose points to it. P1 owns `render_ascii.py:682` (update the tuple → import the constant).
- **Baseline-missing-body_hash rule (red-team RT-11 fix — avoid first-validate flood):** in `changed_nodes`, a node is "changed" only when a field is **present on both sides AND differs**. A `body_hash` ABSENT on the baseline (old pre-upgrade snapshot) is treated as **unknown → not a body change** (so the first post-upgrade `--validate` does NOT mark every node as impact-changed). Test 4 covers the once-changed re-validate path; new Test 6 covers the no-flood guarantee.
- `validation-rules-spec.md:148` prose is **P2-owned** → P1 hands P2 a coordination note to update that line to reference `spec_graph.changed_nodes` (keeps the 3 homes collapsed to 1).

## Related Code Files
- Modify: `.claude/skills/product-spec/scripts/spec_graph.py` (`_node_from_artifact` ~line 116 + `_node_from_goal` `None` case + NEW `CHANGED_FIELDS` constant + `changed_nodes()` function)
- Modify: `.claude/skills/product-spec/scripts/render_ascii.py` (line ~682: `delta()` field tuple → import `CHANGED_FIELDS`/use `changed_nodes`)
- Modify: `.claude/skills/product-spec/references/workflow-validate.md` (Step 2.5: point changed-node derivation at `spec_graph.changed_nodes`) — **P1 sole owner of this file in W1/W2**
- Create/Modify: `.claude/skills/product-spec/scripts/tests/test_spec_graph_body_hash.py` (new) + existing snapshot/delta test fixtures
- Coordination note to P2: update `validation-rules-spec.md:148` prose to reference `spec_graph.changed_nodes` (P2 owns that file)

## Tests (write FIRST — TDD)
1. `test_node_carries_body_hash` — build_graph on a fixture artifact → node has `body_hash` == sha256(body)[:8]; deterministic across two builds.
2. `test_body_hash_changes_with_body` — edit body only (frontmatter identical) → `body_hash` differs.
3. `test_goal_node_body_hash_none` — goal node has `body_hash: None`, no crash.
4. `test_old_snapshot_without_body_hash` — `changed_nodes` vs a snapshot lacking `body_hash` → node NOT marked changed by body (unknown baseline), no KeyError.
5. `test_changed_nodes_detects_body_only_change` — **targets the NEW `spec_graph.changed_nodes(current, previous)`** (the real callable that replaces the un-writable LLM-prose test): two snapshots differing only in one node's body → returned id list includes that node. Also assert a frontmatter-only change is still caught (regression on the 5 legacy fields).
6. `test_first_validate_no_flood` — baseline snapshot missing `body_hash` on EVERY node → `changed_nodes` returns only nodes with a real frontmatter diff (NOT the whole spec) → no impact flood.
7. `test_delta_uses_body_hash` — `render_ascii.delta()` renders a body-only edit as a changed line (proves the single shared field-tuple reaches the `--viz delta` surface too).
- Run existing `scripts/tests/` first to capture green baseline before any edit (regression lock).

## Implementation Steps
1. Capture baseline: run full `scripts/tests/` suite → all green (record).
2. Write the 7 tests above (red).
3. Add `body_hash` to `_node_from_artifact`; `None` on `_node_from_goal`; add `CHANGED_FIELDS` constant + `changed_nodes()` to spec_graph.
4. Refactor `render_ascii.delta()` to use the shared field tuple (`render_ascii.py:682`).
5. Update `workflow-validate.md` Step 2.5 to derive the changed set via `spec_graph.changed_nodes` (+ baseline-missing-body_hash rule); hand P2 the `validation-rules-spec.md:148` coordination note.
6. Run tests → green. Run full suite → no regression.

## Success Criteria
- [ ] All 7 new tests pass; full existing suite still green.
- [ ] `body_hash` present on every artifact node + in snapshots.
- [ ] ONE shared changed-field home (`spec_graph.CHANGED_FIELDS`/`changed_nodes`); `delta` + impact-pass both consume it (no 3-way drift).
- [ ] Body-only edit detected by BOTH impact-pass and `--viz delta`.
- [ ] First post-upgrade `--validate` does NOT flood the impact report (no-flood test passes).
- [ ] No date/graph behavior change beyond the added field + shared function.

## Risk Assessment
- Snapshot format churn → mitigated: additive field; old snapshots degrade to "changed once" (tested).
- Goal `None` hashing inconsistency → documented + tested.
- File ownership: **P1 solely owns `workflow-validate.md` in early waves**; P2/P5/P6 edits to it are serialized behind P1 (DAG).
