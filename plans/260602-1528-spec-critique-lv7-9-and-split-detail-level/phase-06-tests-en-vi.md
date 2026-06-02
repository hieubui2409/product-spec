---
phase: 6
title: "Tests EN+VI"
status: pending
effort: ""
---

# Phase 6: Tests EN+VI

## Overview

The "test kỹ" requirement: cover BOTH requirements (split detail + levels 7-9) in BOTH languages. Two tiers:
deterministic unit/guard tests (Python/pytest) + an LLM-judged behavioral e2e (voice-ladder extended to 1..9, vi+en).

## Requirements
- Functional: schema, floor, register, grounding, gate, detail-split all verified; vi AND en.
- Non-functional: the safety floor has a DETERMINISTIC guard (not only LLM judgment), runnable in CI.

## Architecture

### Tier 1 — deterministic (pytest, no LLM)
- `test_preferences.py` (extend): defaults for all keys; `critique_level` 1..9 accept (9 IS valid), 0/10 → 3,
  save-invalid raises; each new enum accept/fallback/save-raise; `critique_profanity` only `off·abbrev·strong` (no
  family/sexual token representable); `detail_level` ⟂ `critique_detail_level` independence. (The level-9 per-run
  re-confirm + downgrade-to-8 is a workflow behavior, not a schema test.)
- `critique_scan` / nudge regression: bundle still v2, source_files keyed by id, drift unaffected (no schema break).
- **Grounding guard (the one deterministic safety-adjacent test):** every finding block in an lv7/8/9 example has an
  `ID:line` that resolves in the spec + a fix label present. lv9 may interleave pure-scorn lines, but enforce the
  ratio rule (scorn lines must sit in a grounded finding block; scorn-count must not exceed finding-count).
- **NO floor_guard / denylist** (dropped by PO): a keyword scanner cannot catch compositional harm or spelling dodges
  and would give false assurance. The harm-floor is judged by reading meaning (Tier 2), not token-matched.

### Decouple "test the render" from "test the gate" (the level-9 testability problem)

Level 9 re-confirms via AskUserQuestion in the MAIN agent every run — but a workflow/subagent cannot answer an
AskUserQuestion. So the two concerns are tested separately:

- **The GATE** (confirm-every-run + downgrade-to-8) is main-agent interactive guidance, NOT code/a hook → it is NOT
  unit-testable. Verify by (a) a doc/marker assertion that `workflow-critique.md` states the rule, and (b) one manual
  interactive smoke check (a human runs `/spec-critique --level 9` and observes the confirm + a decline → level 8).
- **The RENDER** (does consolidate/humanize PRODUCE correct, floor-compliant lv9 text) is decoupled from the gate and
  tested via a **harness pre-confirm**: the e2e workflow passes `danger_confirmed: true` into the consolidate/humanize
  prompts, standing in for the PO's consent — exactly as the current `regen-voice-ladder-workflow.js` already does for
  lv5/6 (`dangerConfirmed=true`). No human is needed to test the OUTPUT; the test author IS the standing consent.

### Tier 2 — behavioral e2e (LLM-judged, reuse the voice-ladder harness)
- Extend `regen-voice-ladder-workflow.js` to render lv1..9 in BOTH `lang: vi` and `lang: en` over the e2e dating-app
  spec (lenses once; consolidate+humanize per level×lang), passing `danger_confirmed: true` for levels 5-9 (harness
  pre-confirm, per above). Vary register prefs across runs (gender f, dialect trung, profanity strong) to exercise the
  matrix.
- Per-report judge asserts (reading whole-sentence meaning against the IN/OUT table): register/profanity correct per
  level+prefs; **floor held** (no real violence threat / protected-trait slur / self-harm / sexual / family-target
  profanity, however harsh); grounding + ratio kept; first-person scaling; 0 leak / 0 em-dash; EN 7≠8 (profanity-presence).
- Gate behavior (guidance-level checks, the gate is LLM-driven not a hook): the workflow doc specifies that a resolved
  level 9 (from `critique_level: 9` pref OR `--level 9` flag) re-confirms every run and downgrades to 8 on decline —
  verified by a doc/marker assertion, not a runtime hook.

## Related Code Files
- Modify: `.claude/skills/product-spec/scripts/tests/test_preferences.py`
- Create: a grounding/ratio guard test (in spec-critique tests) over the committed lv7/8/9 examples — structural only
  (resolves `ID:line`, fix present, scorn-ratio bound). NO floor_guard / denylist script (dropped by PO).
- Modify: `plans/260602-0814-e2e-dating-app-cycles/regen-voice-ladder-workflow.js` (extend to 1..9 × vi/en × register
  matrix) — or a new `regen-voice-ladder-9-workflow.js`
- Reuse: existing `test_critique_scan.py`, `test_spec_critique_nudge_hook.py` (regression must stay green)

## Implementation Steps
1. Extend `test_preferences.py` with the new-key cases (incl. `critique_level: 9` → default; profanity enum) + the
   detail-split independence test.
2. Add the grounding/ratio guard test over the lv7/8/9 examples (ID:line resolves, fix present, scorn ≤ findings).
3. Extend the voice-ladder workflow to 1..9 × {vi,en} × register matrix; add judge assertions incl. the floor read
   (meaning-based, against the IN/OUT table) — no token scan.
4. Run all suites separately (product-spec / spec-critique / claude-pack) — keep them green.

## Success Criteria
- [ ] All deterministic suites pass (product-spec preferences + spec-critique critique_scan/nudge/grounding-guard).
- [ ] `critique_level: 9` is accepted as a preference; `critique_level: 10` falls back to default; `save({10})` raises.
- [ ] `critique_profanity` has no family/sexual value representable (`off·abbrev·strong` only).
- [ ] Grounding/ratio guard passes on the committed lv9 example (profanity present, every finding grounded, scorn-ratio ok).
- [ ] e2e voice-ladder renders lv1..9 in vi AND en; judge: register/profanity correct, floor held (meaning-read),
      grounding kept, 0 leak, 0 em-dash, EN 7≠8.
- [ ] detail-split independence verified.
- [ ] lv1-6 behavior unchanged (regression).

## Risk Assessment
- No deterministic guarantee on live harm-floor (PO dropped the denylist, understanding its limits). The floor rests on
  the IN/OUT instruction + humanizer override + LLM judge + native review of committed examples. This is a reading-level
  defense, honestly labelled as such — not a mechanical guarantee.
- e2e cost (1..9 × 2 langs ≈ 18 renders + lenses) is high; run as a gated/manual workflow, not every CI push (mirror
  the existing weekly/manual integration pattern).
