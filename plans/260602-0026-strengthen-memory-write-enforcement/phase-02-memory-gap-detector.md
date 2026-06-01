---
phase: 2
title: "memory-gap-detector"
status: completed
priority: P1
effort: "6h"
dependencies: []
---

# Phase 2: memory-gap-detector

## Overview
The deterministic detector + single DRY home for "memory that looks unrecorded". `memory_gap.py` emits structured
signals consumed by `--status` (P5), the validate forcing-function (P6), the Stop hook (P7), and `--reflect` dedup (P9).
Script-only (no judgment); reuses existing detectors — never re-homes their logic.

## Requirements
- Functional — emit JSON `{signals: [...]}` (always exit 0) for these signal types:
  - `fence_breach` — a write landed outside `docs/product/` (reuse `check_fence` logic; do NOT duplicate it).
  - `validate_no_marker` — the current graph has drifted from (or has no) `.memory/last_validated.json` marker
    (PERSISTED-STATE only: the script CANNOT know a `--validate` ran "this session" — it compares the live graph snapshot
    vs the marker; reframed per red-team R1).
  - `approved_changed_no_dec` — an `approved` artifact's `body_hash` changed (vs last validated snapshot) but no new
    `DEC-<n>` exists in `decisions.md` (resolve via `spec_graph` diff + `decision_register` parse).
  - `judged_not_stored` — `judgments.json` did not grow vs the `last_judged` marker despite graph drift.
    **Resolved (red-team R1):** P3 batch-store persists `.memory/last_judged.json` (verdict count + snapshot hash);
    `memory_gap` reads it. Marker absent → signal skipped (degrade), never a false fire.
  - Each signal: `{type, severity, subject (id/path), evidence, suggested_writer}`.
  - **`--ack-no-dec <node-id>` (red-team R2):** record `.memory/no-dec-acks.json` `{node_id: body_hash}`. `collect()`
    SUPPRESSES `approved_changed_no_dec` for a node whose CURRENT `body_hash` matches its ack → the LLM/PO marks
    "no DEC needed" ONCE and is not re-nudged for that wording (a later body change re-arms the signal).
- Non-functional: deterministic (same input → same output); reuses `check_fence`, `spec_graph`, `decision_register`,
  `judgment_cache` — imports, never copies. Git-independent (works on file/graph state, not commits — that's P9).

## Architecture
`memory_gap.py` builds the graph (`spec_graph`), reads last-validated marker (`judgment_cache._last_validated_path`),
parses `decisions.md` (`decision_register.parse_decisions`), runs the fence scan (`check_fence`), and the cache index;
correlates to emit signals. Mirrors the `*_anchors.py` script-half pattern (structured output, no flag/no-flag judgment).

## Related Code Files
- Create: `scripts/memory_gap.py`, `scripts/tests/test_memory_gap.py`
- Read for context: `scripts/check_fence.py`, `scripts/spec_graph.py` (`body_hash`, `changed_nodes`), `scripts/decision_register.py` (`parse_decisions`), `scripts/judgment_cache.py` (`_last_validated_path`), `scripts/status.py` (snapshot diff helpers)

## Tests (write FIRST — TDD)
1. `test_no_signals_clean_spec` → a fully-recorded spec → `signals: []`.
2. `test_fence_breach_detected` → a file outside docs/product → `fence_breach` (matches `check_fence`).
3. `test_validate_no_marker` → graph changed after last marker / no marker → `validate_no_marker`.
4. `test_approved_changed_no_dec` → flip an approved body_hash, no DEC → `approved_changed_no_dec`; add the DEC → clears.
5. `test_judged_not_stored` → drift + judgments unchanged vs `last_judged` marker → signal; grows → clears; marker absent → skipped.
6. `test_ack_no_dec_suppresses` → `--ack-no-dec <id>` then `collect()` → `approved_changed_no_dec` suppressed while body_hash matches; a later body change re-arms it.
7. `test_deterministic` → same input twice → identical JSON.
8. `test_exit_zero_always` → even on malformed inputs, exit 0 (advisory) + a `parse_error` signal, never crash.
9. `test_reuses_check_fence` → fence detection matches `check_fence` output (no logic drift).

## Implementation Steps
1. Write tests (red).
2. Implement `memory_gap.py` (import + correlate the four signals; structured JSON; exit 0).
3. Tests green; full suite no regression.

## Success Criteria
- [ ] 8 tests pass; full suite green.
- [ ] Each of the 4 signal types fires on its trigger and clears on remedy.
- [ ] No copied logic from `check_fence`/`spec_graph` (imports only) — grep proves single home.

## Risk Assessment
- `approved_changed_no_dec` false positives (legit approved edits) → it is **surfaced**, never auto-blocked here; the
  hook (P7) treats it nudge-once. Document the false-positive nature in the signal `evidence`.
