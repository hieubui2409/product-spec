---
title: "spec-critique levels 7-9 (ông-tôi / mày-tao / chửi thề) + split detail_level"
description: ""
status: complete
priority: P2
branch: "feat/product-spec-guardrails-and-memory-layer"
tags: []
blockedBy: []
blocks: []
created: "2026-06-02T08:34:53.199Z"
createdBy: "ck:plan"
source: skill
---

# spec-critique levels 7-9 (ông-tôi / mày-tao / chửi thề) + split detail_level

## Overview

Increment on the shipped `cleanmatic:spec-critique` skill (built in `plans/260602-0219-spec-critique-brutal-skill`,
research in `plans/reports/research-260602-1516-spec-critique-lv6-harsher-register-report.md`). Two requirements:

1. **Split `detail_level` into two independent prefs** — product-spec output verbosity AND spec-critique report
   verbosity, each 3 levels (concise / standard / verbose), wired with a PO interview question + a real consumer (today
   `detail_level` is declared-but-dormant: no interview sets it, no consumer reads it).
2. **Three new voice levels 7-9** above the current 1-6, escalating harshness via the Vietnamese pronoun ladder, in
   BOTH `vi` and `en`:
   - **lv7** — formal-confrontational, address `ông/tôi` (gendered: `bà/tôi`). No profanity. Attacks competence, not
     just effort. cite+fix kept.
   - **lv8** — street register, address `mày/tao` (regional: `mi/tau`…). Harsher. cite+fix kept.
   - **lv9** — `mày/tao` + **work-targeted profanity** (`đm/vl` abbrev default · `đm/vl/vãi` strong; NO family/sexual
     tokens like `đụ má`/`đậu xanh`). Removes every spec-critique INTERNAL restraint; allows pure-scorn lines, but each
     finding still grounds on a real `ID:line` + fix.

### Register config (preferences, new)

The harsh levels read register knobs from `preferences.yaml`: gender (`ông/tôi` ↔ `bà/tôi`), dialect
(`mày/tao` ↔ `mi/tau` ↔ nam — the PO's OWN voice, self-configured), profanity strength (off ↔ `đm/vl` abbrev ↔
`đm/vl/vãi` strong, **aimed at the work**). **Defaults: `ông/tôi` · `mày/tao` · `strong` (`đm/vl/vãi`).** (Profanity
default is `strong` because level 9 re-confirms with the PO on every run anyway, so when it fires it runs at full power.
Updated PO 2026-06-02, supersedes the original `abbrev` default.)

### Safety floor — TARGET decides (NON-NEGOTIABLE, locked with PO 2026-06-02)

lv9 removes spec-critique's INTERNAL restraints (polite pronoun, no-profanity, attack-effort-only). A universal-harm
floor holds at every level incl. 9, even with confirmation. The rule is **the TARGET of the line, not its strength**:

**IN (allowed, even at lv9):** profanity aimed at the WORK (`cái AC này rỗng vl`, `đm cái scope mâu thuẫn`); attacking
effort/attitude (`mày lười, viết cho xong`); attacking competence (`làm sản phẩm không tới, tư duy non`); authoritative
scolding idioms (`đừng để tao nhắc lại` — this is "don't make me repeat myself", NOT a violence threat).

**OUT (never, regardless of consent):** real **threats of violence** (`tao đánh/giết mày`, `tao biết nhà mày ở đâu`);
**slurs on protected characteristics** (gender, region, ethnicity, religion, age, disability, sexuality, appearance);
profanity that grammatically takes the **author or their family** as object (`đụ má mày` — names a sexual act against
the mother, so it is dropped from the profanity ladder); **self-harm** content; **sexual-act** content.

> **Updated PO 2026-06-02 — `đậu xanh` is IN, supersedes the original "đậu xanh dropped" ruling.** `đậu xanh` is a
> deliberately defanged minced oath / nói-lái dodge for `đm` — it does NOT literally name a sexual act or take the
> author's family as object, so it is an accepted work-aimed euphemism (IN). Only the LITERAL family-target form
> (`đụ má mày` / `đụ mẹ mày` / `...nhà mày` constructions) stays OUT.

The authoritative spec is the IN/OUT adjudication table (15-20 native-reviewed borderline lines, Phase 2) — it defines
the floor by target, and is the shared source for the agents, the humanizer override, and the floor-guard scan.

- **Grounding kept even at lv9:** every finding cites a real `ID:line` + ends in a fix; pure-scorn lines may be
  interleaved but each finding stays grounded. (This guards against the e2e finding that ungrounded/loosely-cited
  output reads as fabricated and worthless — same lesson as the citation-discipline fix, not a separate "empty-rage"
  claim.)

### Captured decisions (PO interview, locked)

- lv9 = max harshness within the universal floor; floor defined by TARGET (IN/OUT table).
- `critique_profanity` is **work-targeted only**; the LITERAL family-target `đụ má mày` (sexual-semantic) dropped; keep
  strong `đm/vl/vãi` aimed at the spec. **`đậu xanh` (minced-oath dodge) is IN** — updated 2026-06-02, see the floor
  note above. Default strength = `strong` (level 9 re-confirms every run anyway).
- **`critique_level` may be 9** (enum 1..9). But a resolved level of 9, whether from the standing preference OR a
  `--level 9` flag, **re-confirms via AskUserQuestion EVERY run** (never silent); on decline it **downgrades to 8**.
  lv7/8 may be standing with just the one-line reminder (no re-ask). So 9 is never silent, but it is settable + forceable.
- lv9 keeps grounding, allows interleaved pure-scorn lines (ratio-bounded, Phase 6).
- Dialect config KEPT — it is the PO's own self-configured voice, not regional mockery; a light "self-dialect" note in
  the IN/OUT table separates "harsh in my Trung voice" (IN) from "mocking the author for being Trung" (OUT).
- `detail_level` SPLIT: separate product-spec (`detail_level`) vs spec-critique (`critique_detail_level`) prefs.
- Both `vi` and `en`. EN has no pronoun ladder → escalation by **profanity-presence** (lv7 none, lv8 profanity on, lv9
  sustained + no restraint) + contempt; same floor.
- No new aliases for 7-9 — use `--level 7/8/9`.
- Humanizer: the floor **overrides** the preserve-venom instruction; floor clause is level-agnostic.
- **No denylist / token-filter** (dropped by PO after understanding it only matches known tokens and misses
  compositional harm / spelling dodges). Floor enforcement = three reading-level layers: **(1) IN/OUT table** (instructs
  the agents), **(2) humanizer pull-back** (floor overrides preserve), **(3) LLM judge** in the e2e (reads whole-sentence
  meaning). Grounding (every finding has `ID:line` + fix) IS structurally checkable and stays a deterministic test.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Preferences schema](./phase-01-preferences-schema.md) | Complete |
| 2 | [Voice levels 7-9 EN+VI](./phase-02-voice-levels-7-9-en-vi.md) | Complete |
| 3 | [Orchestration + agents + gate](./phase-03-orchestration-agents-gate.md) | Complete |
| 4 | [detail_level split wiring](./phase-04-detail-level-split-wiring.md) | Complete |
| 5 | [Docs examples evals](./phase-05-docs-examples-evals.md) | Complete |
| 6 | [Tests EN+VI](./phase-06-tests-en-vi.md) | Complete |

## Post-build PO decisions (locked 2026-06-02, during /cook)

- **`đậu xanh` is IN** (minced-oath dodge); only literal family-target `đụ má mày` is OUT. Supersedes the original
  "đậu xanh dropped" ruling.
- **`critique_profanity` default = `strong`** (lv9 re-confirms every run anyway, so it runs at full power).
- **`critique_level` default = `5`** (no-mercy), the last level before a mandated personal roast (6+).
- **Level 5 is the ungated default baseline** — no warning / confirm / reminder. The danger gate now applies to
  **levels 6-9** only (6/7/8 ad-hoc warn+confirm or standing reminder; 9 always re-confirms + downgrades to 8).
- **Why-label ladder reordered monotonic**, apex `banh xác` moved to L9: toang≈hỏng < chết ở chỗ < vì sao đi đời <
  banh nóc < nát bét < banh xác.
- **Register interview seed added** — one AskUserQuestion batch (gender/dialect/profanity) on first level-≥7 use,
  persisted + marked `critique_register_seeded` so it asks once.

## Dependencies

- Builds on (completed in practice) `plans/260602-0219-spec-critique-brutal-skill` — the shipped 6-level skill.
- Research input: `plans/reports/research-260602-1516-spec-critique-lv6-harsher-register-report.md` (VN register ladder,
  options, floor). No fresh researcher spawn needed (`--hard` research satisfied by this report).
- No open plan conflicts: the predecessor is shipped; this is a clean additive increment. `blockedBy: []`.

## Touchpoints (blast radius)

- `.claude/skills/product-spec/scripts/preferences.py` — extend `critique_level` enum to 1..9 (9 valid; the per-run
  re-confirm for level 9 is enforced in the workflow, not the schema); add
  `critique_detail_level`, `critique_address_gender`, `critique_dialect`, `critique_profanity`; keep `detail_level`.
- `.claude/skills/product-spec/scripts/tests/test_preferences.py` — new-key coverage.
- `.claude/skills/spec-critique/references/voice-and-tone.md` — levels 7-9, register config, floor, EN+VI samples.
- `.claude/skills/spec-critique/references/workflow-critique.md` — level resolution 1..9, gate for 7/8/9, register +
  detail consumers.
- `.claude/skills/spec-critique/SKILL.md` — flags table, levels, floor note.
- `.claude/agents/spec-critique-consolidate.md` + `-humanize.md` — render register/dialect/profanity + detail level;
  lens agents largely unchanged (they emit grounded findings; voice is applied at consolidate).
- `.claude/skills/product-spec/references/workflow-interview.md` — capture `detail_level` (Phase 4).
- `.claude/skills/spec-critique/{README,GUIDE-VI,GUIDE-EN}.md`, `examples/`, `eval/evals.json` — docs + evals.
- (No denylist/floor_guard script — dropped by PO.) A deterministic GROUNDING test (every finding has `ID:line` + fix)
  + the LLM-judge floor check in the e2e.
