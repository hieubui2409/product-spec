---
phase: 5
title: "status-unrecorded-signals"
status: completed
priority: P2
effort: "3h"
dependencies: [2]
---

# Phase 5: status-unrecorded-signals

## Overview
Surface `memory_gap` signals + a soft `--reflect` suggestion in the read-only `--status` nudge, so a PO/dev sees what
looks unrecorded without any blocking. Reuses P2's detector (no second detection home).

## Requirements
- Functional:
  - `status.py` imports `memory_gap` and adds an `unrecorded_signals` section to its JSON/report.
  - When drift-since-last-validate is high (existing `--status` drift metric), add a soft one-line `--reflect` suggestion.
  - Stays read-only (never writes memory/marker) — the locked `--status` invariant.
- Non-functional: deterministic; degrades to empty signals if `memory_gap` finds nothing; never crashes on absent `.memory/`.

## Architecture
`status.py` calls `memory_gap.collect(root)` and merges its signals into the existing report payload; the reflect
suggestion is a derived advisory string. No new detection logic in status.py (DRY → P2 is the home).

## Related Code Files
- Modify: `scripts/status.py` (import `memory_gap`; add `unrecorded_signals` + reflect suggestion)
- Modify: `scripts/tests/test_status.py` (additions)
- Read for context: `scripts/memory_gap.py` (P2 API), existing `status.py` drift/unvalidated logic

## Tests (write FIRST — TDD)
1. `test_status_includes_unrecorded_signals` → a seeded gap → appears in `unrecorded_signals`.
2. `test_status_clean_empty_signals` → recorded spec → `unrecorded_signals: []`.
3. `test_status_reflect_suggestion_on_high_drift` → high drift → reflect suggestion present; low drift → absent.
4. `test_status_still_readonly` → running `--status` writes NOTHING under `.memory/` (regression of the invariant).
5. `test_status_no_memory_dir_graceful` → absent `.memory/` → no crash, empty signals.

## Implementation Steps
1. Write tests (red).
2. Wire `memory_gap` into `status.py`; add `unrecorded_signals` + reflect suggestion.
3. Tests green; full suite no regression.

## Success Criteria
- [ ] 5 tests pass; full suite green.
- [ ] `--status` shows `memory_gap` signals + a soft reflect hint, and writes nothing.
- [ ] Detection logic lives only in `memory_gap.py` (status imports it).

## Risk Assessment
- Read-only invariant is sacred — `test_status_still_readonly` guards it; never call any writer from status.
