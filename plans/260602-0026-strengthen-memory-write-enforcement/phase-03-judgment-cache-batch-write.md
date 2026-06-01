---
phase: 3
title: "judgment-cache-batch-write"
status: completed
priority: P2
effort: "4h"
dependencies: []
---

# Phase 3: judgment-cache-batch-write

## Overview
Collapse the per-verdict `--store` calls (N → 1) into a single batch write driven by one structured payload, removing
the "forgetting surface" where the LLM stores some verdicts and forgets others mid-loop. Stays validate-gated; the cache
stays an optimization, never authoritative.

## Requirements
- Functional:
  - Add `--store-batch` (reads a JSON list of `{key, verdict, po_ruling_ref?}` from a file or stdin) → one read-modify-write.
  - Preserves all existing single-`--store` semantics: stamp validate, `NEVER_CACHED` (contradiction) refused per entry,
    stamp/version reset on model mismatch, `po_ruling_ref` passthrough, GC of deleted-node entries.
  - Per-entry validation: a bad entry (e.g. a `contradiction` key) fails the WHOLE batch atomically (validate-before-write,
    mirroring the `decision_register` ordering fix) — no partial write.
  - Backward compatible: single `--store` keeps working (no removal).
  - **Persist `.memory/last_judged.json` (red-team R1, for P2's `judged_not_stored`):** on a batch store, record the
    verdict count + the current snapshot hash so `memory_gap` can detect "drift since judged but judgments didn't grow".
    Written through `fs_guard`; absent → P2 skips that signal (degrade).
- Non-functional: deterministic; atomic write (no partial cache on a bad entry); reuses `_now()` (already module-level).

## Architecture
`judgment_cache.py` gains `store_batch(root, entries, model_id, no_cache)` that validates all entries first, then writes
once. CLI `--store-batch <file|->`. The validate orchestration (P6) emits the batch payload at end of Step 2 and calls
`--store-batch` instead of N× `--store`.

## Related Code Files
- Modify: `scripts/judgment_cache.py` (add batch path; reuse existing helpers)
- Modify: `scripts/tests/test_judgment_cache.py` (batch tests)
- Read for context: existing `store()` + `_write_cache()` + `_stamp_valid()`

## Tests (write FIRST — TDD)
1. `test_store_batch_writes_all` → N entries → all present after one write.
2. `test_store_batch_atomic_on_bad_entry` → one `contradiction` key in the batch → ValueError, NOTHING written (no partial).
3. `test_store_batch_model_mismatch_resets` → batch under a new model id → cache reset then stored.
4. `test_store_batch_po_ruling_passthrough` → `po_ruling_ref` survives the batch.
5. `test_single_store_still_works` → legacy `--store` unaffected (regression).
6. `test_store_batch_gc` → deleted-node entries GC'd during the batch write.
7. `test_store_batch_writes_last_judged` → batch store writes `.memory/last_judged.json` (count + snapshot hash) for P2.

## Implementation Steps
1. Write tests (red).
2. Implement `store_batch` + `--store-batch` (validate-all-then-write-once).
3. Tests green; full suite no regression; measure call-count reduction on a multi-verdict fixture.

## Success Criteria
- [ ] 6 tests pass; full suite green.
- [ ] A multi-verdict validate path can persist all verdicts in ONE script call.
- [ ] A bad entry leaves the cache byte-unchanged (atomic).

## Risk Assessment
- Atomicity: validate the entire batch before any write (read-modify-write once) — tested by `test_store_batch_atomic_on_bad_entry`.
- Do NOT add a chat-time write path (locked: cache never authoritative; content change self-heals via `body_hash`).
