---
phase: 1
title: Failing tests (TDD red)
status: completed
priority: P2
effort: 2h
dependencies: []
---

# Phase 1: Failing tests (TDD red)

## Overview

Write the tests that encode all 6 acceptance criteria FIRST, confirm they fail for the right reason
(helper/field not yet present), and capture the regression baseline. No production code this phase.

## Requirements
- Functional: tests cover fingerprint compute (pure), line resolver, write-path persistence, read-path dedup,
  tolerant read, graceful fallback.
- Non-functional: tests deterministic, use `make_proj` real fixture for end-to-end line resolution; no wall-clock.

## Architecture

Split tests by surface so identity is testable without depending on fixture line layout:
- **Pure helper tests** (no I/O): `compute_finding_fingerprint(node, severity, line_text)` — stable, order/whitespace
  normalized, severity-sensitive.
- **Resolver tests** (real fixture): `_resolve_line_text(root, graph, evidence_id)` → exact line text; out-of-range /
  unknown node → `None`.
- **Write-path test** (real fixture, end-to-end): `index_report_findings` attaches `finding_fingerprint`; persisted +
  reloaded via `load_index`; index `version == 2`.
- **Read-path tests** (hand-built rows carrying fingerprints): `_index_rows` dedups by fingerprint;
  `build_descendant_rollup` blocker_count reflects dedup; `build_inherited_context` dedups.

## Related Code Files
- Modify: `.claude/skills/product-spec-critique/scripts/tests/test_critique_cache.py`
- Modify: `.claude/skills/product-spec-critique/scripts/tests/test_critique_inherit.py`
- Read for fixture API: `.claude/skills/product-spec-critique/scripts/tests/critique_test_support.py`

## Implementation Steps

1. **Baseline**: record collected count —
   `./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec-critique/scripts/tests --co -q | tail -1`.
   Note the number in the phase report; this is the no-regression anchor for Phase 3.
2. **test_critique_inherit.py — pure fingerprint** (`test_fingerprint_*`), via `_finding_fingerprint` or a hashing
   sub-helper:
   - same `(node, severity, normalized line_text)` → identical hash; whitespace/case variants → identical hash
     (light normalize: trim, collapse internal ws, lowercase, strip leading markdown bullet/heading markers).
   - different `severity` → different hash (3b); different `line_text` → different hash; different `node` → different.
   - **B1 empty-normalize**: a cited line that is all-punctuation/structural (`---`, `2026-05-28`, `1. 2. 3.`)
     normalizes to `""` → `_finding_fingerprint` returns **None** (NOT a hash of "") → two such findings on the same
     node+severity do NOT merge (they fall back to distinct eids). This is the primary collision-regression guard.
3. **Resolver** (`test_resolve_line_text_*`, uses `make_proj`):
   - build graph via `spec_graph.build_graph(proj)`; pick a known node+line from the fixture; assert resolved text
     equals that file's line.
   - line out of range → `None`; evidence node not in graph → `None`; malformed evidence (no `:line`) → `None`.
4. **Criterion 1 (line-drift dedup)** (`test_index_rows_dedup_line_drift`): hand-insert two index rows for the SAME
   node+severity+identical fingerprint but different `evidence_id` line + different ts → `_index_rows` returns ONE
   (latest ts, latest eid for citation).
5. **Criterion 2 (granularity)** (`test_index_rows_distinct_findings`): two rows, same node, DIFFERENT fingerprints →
   `_index_rows` returns TWO; `build_descendant_rollup` blocker_count for that child == 2.
6. **Criterion 3 (spec edit → new fp)** (`test_fingerprint_changes_on_spec_edit`): resolver on same evidence line but
   mutated file text → different fingerprint.
7. **Criterion 4 (tolerant read)** (`test_index_rows_legacy_no_fingerprint`): rows WITHOUT `finding_fingerprint`
   (legacy v1) → `_index_rows` falls back to `evidence_id` keying; no KeyError; behaves as today.
8. **Criterion 5 (graceful fallback)** (`test_index_report_findings_unresolvable_fallback`): `index_report_findings`
   on a finding whose node/line is unresolvable → row persisted with `finding_fingerprint = None`; no crash.
9. **Write-path persistence** (`test_index_report_findings_writes_fingerprint`, `make_proj`): index a real finding
   citing a real content line → `load_index` row has non-null `finding_fingerprint`. Do NOT assert on `version` (M3:
   no consumer reads it — a version assertion is a phantom test).
9b. **B2 goal node** (`test_goal_node_eid_fallback`, `make_proj`): a `BRD-G<n>:<line>` finding whose cited line is
   structural (e.g. `:1` = `---`) → `finding_fingerprint` is None → row keys by eid; no crash. (Goal nodes have
   `file=brd.md`, content in frontmatter — accepted eid-fallback.)
10. Run the new tests; confirm each FAILS for the right reason (missing helper / missing field), NOT import errors.

## Success Criteria
- [ ] Baseline collected count recorded.
- [ ] All new tests written across the 6 criteria + helper/resolver/write/read surfaces + B1 (empty-normalize
      collision) + B2 (goal-node eid-fallback).
- [ ] No `version`-read phantom assertion (M3).
- [ ] New tests fail for the right reason (feature absent), existing tests still pass.
- [ ] No production code changed this phase.

## Risk Assessment
- **Fixture line coupling**: resolver tests reference fixture line numbers that may shift if fixture changes →
  mitigate by reading the expected line via the same file read in-test (compare resolver vs direct read), not a
  hard-coded string.
- **Hand-built rows drifting from real schema**: keep row dicts aligned with `_INDEX_FIELDS` + new field.
