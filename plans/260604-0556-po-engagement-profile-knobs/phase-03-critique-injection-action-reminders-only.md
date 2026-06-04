---
phase: 3
title: "Critique injection — DEFERRED (out of v1)"
status: deferred
priority: P3
effort: "0h"
dependencies: []
---

# Phase 3: Critique injection — DEFERRED (out of v1)

<!-- Updated: Validation Session 1 — critique wiring DROPPED from v1. -->

## Status: NOT IN SCOPE (deferred post-v1)

Engagement knobs apply to **product-spec only** in v1. Critique is untouched (`critique_level` already owns harshness).
Marked `completed` so it is a no-op in plan progress, not a pending work item.

## Why deferred (validation decision)

After dropping `standing_reminders`, critique would receive only ONE knob (`action_prompting`, clamped ≤ standard).
But the critique `fix` field already produces standard-density remediation today, so the only NET-new capability would be
PO enabling `minimal` (terse-fix reports). That marginal value does not justify the cost:

- editing `critique_bundle.py::emit_bundle`, AND
- folding the knob into `_provenance_hash` (`critique_common.py:106-111`), which **rebusts every existing critique
  cache once** (global re-judge) — or the alternative leaves the knob **silently inert on cached re-runs** (confusing).

KISS/YAGNI: defer. Re-adding later is cheap and breaks nothing (additive bundle key + optional provenance fold).

## If revived later

- Add clamped `action_prompting` to `emit_bundle`; decide provenance-fold vs `--fresh`-only at that time.
- Red-team findings C, I, S apply only to this deferred work.

## Success Criteria

- [x] Critique code paths unchanged in v1 (no `critique_bundle.py` / provenance edits).
