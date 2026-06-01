---
phase: 4
title: "behavioral-memory-voice-flag"
status: completed
priority: P2
effort: "3h"
dependencies: []
---

# Phase 4: behavioral-memory-voice-flag

## Overview
Give the PO an explicit entry point to record voice (3D) — `--voice` — so a PO-stated preference is captured
deterministically instead of relying on the LLM noticing a correction. Writes through the existing `record_po_style`
(same shape-validate + lang-key + DRY guard). Complements (does not replace) the inline forcing-function.

## Requirements
- Functional:
  - `behavioral_memory.py --voice --lang <en|vi> [--register <s>] [--vocabulary a,b] [--recurring-asks ...] [--do ...] [--dont ...]`
    → calls `record_po_style(...)` (union-merge lists, latest `register` wins).
  - Reuses the existing DRY guard (`_assert_no_structural_copy` → `BehavioralError` on closed-enum copy).
  - Read path unchanged: `--dump po-style` (the read-only selector renamed earlier) still works.
  - At least one writable field required; empty invocation is a no-op with a clear message (not a crash).
- Non-functional: lang-keyed; deterministic merge; goes through `fs_guard` (write under docs/product/).

## Architecture
`behavioral_memory.main()` gains a `--voice` write branch parallel to the existing `--dump` read branch. The writer is
the already-present `record_po_style`; `--voice` is just a CLI surface over it. SKILL.md flag row + GUIDE UC come in P10.

## Related Code Files
- Modify: `scripts/behavioral_memory.py` (`--voice` CLI write branch)
- Modify: `scripts/tests/test_behavioral_memory.py` (voice CLI tests)
- Read for context: existing `record_po_style`, `_assert_no_structural_copy`, `main()` (`--dump`)

## Tests (write FIRST — TDD)
1. `test_voice_records_vocabulary` → `--voice --vocabulary shopper` → present in `po-style.yaml[en]`.
2. `test_voice_lang_keyed` → `--voice --lang vi` writes vi block only; en untouched.
3. `test_voice_dry_guard` → `--voice --vocabulary must` (closed-enum) → `BehavioralError`, nothing written.
4. `test_voice_union_merge` → two `--voice` calls accrue (dedup, order-preserving); `register` latest-wins.
5. `test_voice_empty_noop` → `--voice` with no field → clear message, exit non-crash, no write.
6. `test_dump_still_reads` → `--dump po-style` unaffected (regression).

## Implementation Steps
1. Write tests (red).
2. Implement `--voice` branch in `main()` (parse fields → `record_po_style`).
3. Tests green; full suite no regression.

## Success Criteria
- [ ] 6 tests pass; full suite green.
- [ ] `--voice` writes via `record_po_style` (no second writer home) and honors the DRY guard.
- [ ] `--dump` read path unchanged.

## Risk Assessment
- Scope creep: `--voice` is a thin CLI over `record_po_style` — do NOT add a parallel write/validate path (DRY).
- 3D is still nudge-only at the inline layer (P6); `--voice` is the explicit manual path, not an enforcement.
