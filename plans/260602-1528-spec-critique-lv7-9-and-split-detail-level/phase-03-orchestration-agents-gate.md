---
phase: 3
title: "Orchestration + agents + gate"
status: pending
effort: ""
---

# Phase 3: Orchestration + agents + gate

## Overview

Wire the orchestration + agents to levels 1..9: level resolution, the escalating danger gate for 7/8/9, and the
consolidate/humanize agents reading the register/profanity/critique_detail_level prefs.

## Requirements
- Functional: `--level 7/8/9` + preference resolution; gate warns+confirms for 7/8/9 (lv9 strongest); render honors
  gender/dialect/profanity + critique_detail_level; floor enforced in agent instructions.
- Non-functional: keep the standing-consent semantics already built for 5/6; DRY (floor text single-homed in
  voice-and-tone, agents reference it).

## Architecture

**Level resolution (workflow-critique step 1):** unchanged shape — flag > `critique_level` pref > 3 — but now spans
1..9 (`critique_level: 9` is a valid standing default; level 9 always re-confirms per run, see gate). No new aliases — `--level N` only.

**Danger gate (workflow-critique step 1):** extend the 5/6 gate to 7/8/9, escalating, with lv9 special-cased per B5:
- lv7/8: warn (harsher than 6: confrontational/street register, attacks competence/character) + AskUserQuestion confirm
  on an ad-hoc flag. A STANDING `critique_level` of 7 or 8 is deliberate consent → don't re-ask every run, print the
  one-line danger reminder each run (mirrors 5/6).
- **lv9 always re-confirms, regardless of source.** `critique_level: 9` IS a valid standing default, AND `--level 9`
  forces it — but whenever the resolved level is 9, the workflow shows the strongest warning + an AskUserQuestion confirm
  **every run** (never a silent reminder). The warning names exactly what it removes (polite pronoun, no-profanity,
  effort-only) AND what the floor still forbids (real violence threats / protected-trait slurs / self-harm / sexual /
  family-target profanity). **On decline, downgrade to 8** (not 6). Never inferred; vague phrasing is never consent.
- Fallback on "no": lv9→8, lv8→7, lv7→6 (then 6's own gate applies if reached ad-hoc).

**Agents:**
- `spec-critique-consolidate` + `-humanize`: read `critique_address_gender` / `critique_dialect` / `critique_profanity`
  (passed by the main agent) and render the lv7-9 surface form; read `critique_detail_level` to size the report
  (concise = top-3 + terse per-lens; verbose = full per-lens + extended pre-mortems). Both reaffirm the universal-harm
  floor + grounding (findings cite+fix; lv9 scorn-lines allowed) by pointing at voice-and-tone (DRY, no copy).
- Lens agents (product/tech/market/craft): essentially unchanged — they emit grounded findings; the voice/register is
  applied downstream at consolidate. Only tweak: their `--level` note now says "1..9; voice rendered by consolidate".
- The main agent passes the resolved level + register prefs + detail level into the consolidate/humanize prompts.

## Related Code Files
- Modify: `.claude/skills/spec-critique/references/workflow-critique.md` (level resolution 1..9; gate 7/8/9; pass
  register + detail prefs to agents; consumer note for critique_detail_level)
- Modify: `.claude/skills/spec-critique/SKILL.md` (flags table: `--level 1..9`, NO new aliases; floor note; pref list)
- Modify: `.claude/agents/spec-critique-consolidate.md` (render register/profanity/detail; floor; grounding)
- Modify: `.claude/agents/spec-critique-humanize.md` (preserve register/profanity; floor OVERRIDES preserve; size per detail)
- Modify (light): the four lens agents' `--level` line (1..9 note)

## Implementation Steps
1. workflow-critique step 1: extend resolution to 1..9 (no new aliases); rewrite the gate block for 5/6/7/8/9 with the
   escalation + lv7/8-standing-reminder + **lv9 always-re-confirm (pref OR flag) + downgrade-to-8 on decline** + fallback above.
2. **M4 — pref load/pass:** specify the exact step-5/5b change: the main agent calls `preferences.load(root)`, extracts
   `critique_address_gender`, `critique_dialect`, `critique_profanity`, `critique_detail_level`, and INJECTS them into
   both the consolidate and humanize spawn prompts (today step 5/5b pass only scope/lang/level). Without this the agents
   render defaults regardless of the PO's config.
3. consolidate agent: add register/profanity rendering rules (cite the voice-and-tone surface table; profanity is
   work-targeted) + `critique_detail_level` sizing + reaffirm floor/grounding (reference the IN/OUT table, don't copy).
   Same level-label rendering discipline as before.
4. **M3 — humanize agent:** PRESERVE register/profanity (do not soften mày/tao or strip work-profanity at lv9) while
   killing AI-tells + em-dashes; BUT make the floor clause **level-agnostic** (it is currently scoped to "level 6") and
   make it **override** the preserve instruction: "if preserving venom would cross the floor (violence threat /
   protected-trait slur / self-harm / sexual / family-target profanity), DROP the line — do not soften-and-keep."
5. SKILL.md flags table + levels note + the lv9-not-standing + floor one-liners.
6. lens agents: one-line `--level 1..9` update.

## Success Criteria
- [ ] Resolved level 9 (from `critique_level: 9` pref OR `--level 9` flag) re-confirms EVERY run; decline → downgrades to 8.
- [ ] lv7/8 standing-consent prints the reminder without re-asking; lv9 never runs without a per-run confirm.
- [ ] consolidate renders `ông/tôi` vs `bà/tôi` (gender), `mày/tao` vs `mi/tau` (dialect), work-targeted profanity per
      `critique_profanity`; `critique_detail_level` changes report size.
- [ ] M4: a gender=f / dialect=trung PREFERENCE (not a flag) actually changes the rendered surface form.
- [ ] humanize keeps the harsh register + work-profanity intact, still 0 em-dash / 0 leak; floor clause is
      level-agnostic AND overrides preserve.
- [ ] Floor + grounding text single-homed (IN/OUT table + voice-and-tone); agents reference, don't duplicate.
- [ ] lv5/6 behavior unchanged (regression).

## Risk Assessment
- Gate-bypass risk: addressed by behavior — level 9 always re-confirms per run (whether from the `critique_level: 9`
  pref or the flag) and downgrades to 8 on decline, so it can never run silently even as a standing default.
- Humanizer softening risk: Gate-2 might neutralize mày/tao/profanity as an "AI-tell". Mitigation: explicit "preserve
  register/work-profanity" rule, with the floor override on top; Phase-6 e2e checks lv9 output retains the configured
  register AND the judge confirms the floor held.
- Humanizer softening risk: Gate-2 might neutralize mày/tao/profanity as "AI-tell". Mitigation: explicit "preserve
  register/profanity" rule in the humanize agent + a Phase-6 check that lv9 output retains the configured register.
