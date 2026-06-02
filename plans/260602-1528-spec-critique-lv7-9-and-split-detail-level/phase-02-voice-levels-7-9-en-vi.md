---
phase: 2
title: "Voice levels 7-9 EN+VI"
status: pending
effort: ""
---

# Phase 2: Voice levels 7-9 EN+VI

## Overview

Define levels 7-9 in `voice-and-tone.md` (the single voice home): the pronoun-ladder escalation, the register config
surface, the universal-harm floor, and EN+VI sample lines. This is the heart of the change.

## Requirements
- Functional: 7-9 escalate harshness via register (pronoun/profanity), each level distinct; floor explicit; EN+VI both.
- Non-functional: keep the "defaults not straitjacket" tone guidance; keep grounding mandatory.

## Architecture

**The level ladder (extend the table to 9 rows):**

| Lvl | Register (VI) | Profanity | Personal attack | cite+fix |
|-----|---------------|-----------|-----------------|----------|
| 1-4 | bạn/tôi | none | forbidden | yes |
| 5 | bạn/tôi | none | barb allowed | yes |
| 6 | bạn/tôi | none | required (effort/care) | yes |
| **7** | **ông/tôi** (gender: bà/tôi) | none | competence + effort | yes |
| **8** | **mày/tao** (dialect: mi/tau…) | none | competence + character | yes |
| **9** | mày/tao | **on, work-targeted** (`đm/vl`…) | no internal restraint | findings grounded; scorn lines allowed (ratio-bounded) |

No aliases for 7-9 — `--level 7/8/9` only (decided).

**Register config → surface form (reads the Phase-1 prefs):**
- gender `m|f` → lv7 `ông/tôi` | `bà/tôi`.
- dialect `bac|trung|nam` → lv8+ `mày/tao` | `mi/tau` | nam. The PO's OWN voice (self-configured), not a region they
  are othering.
- profanity `off|abbrev|strong` → lv9 none | `đm/vl` | `đm/vl/vãi` (all aimed at the WORK; no family/sexual-target).

**Universal-harm floor — the TARGET decides (new dedicated section, applies to ALL levels incl. 9).** The authoritative
artifact is an **IN/OUT adjudication table** (15-20 native-reviewed borderline lines). The rule:

- **IN:** profanity aimed at the WORK (`cái AC này rỗng vl`, `đm cái scope`); effort/attitude (`mày lười`); competence
  (`làm sản phẩm không tới`); authoritative scolding idioms (`đừng để tao nhắc lại` = "don't make me repeat myself",
  NOT a violence threat); harsh in the PO's own dialect (`mi/tau`).
- **OUT (never, even with consent):** real threats of violence (`tao đánh/giết mày`, `biết nhà mày ở đâu`); slurs on
  protected characteristics (gender/region/ethnicity/religion/age/disability/sexuality/appearance); profanity taking the
  author/family as object (`đụ má mày`); self-harm; sexual-act content. Plus: mocking the author FOR being from a
  region (vs being harsh in one's own regional voice).

lv9 "removes restraints" = removes the polite-pronoun / no-profanity / effort-only INTERNAL rules, NOT this floor.

**EN mapping (profanity-presence is the hard boundary, since EN has no pronoun ladder):**
- lv7 = cold contemptuous "you" + competence jab, **zero profanity**.
- lv8 = blunt character attack ("whoever wrote this"), **profanity required** (work-targeted), no slur-adjacent terms.
- lv9 = sustained profanity + no internal restraint + scorn lines.
Same floor. `critique_address_gender`/`critique_dialect` are VI-only no-ops in EN; `critique_profanity` maps to EN
profanity strength (and is what mechanically separates EN 7 from 8).

## Related Code Files
- Modify: `.claude/skills/spec-critique/references/voice-and-tone.md`
  - extend the levels table + the why/fix label table (propose labels for 7-9, vi+en)
  - new "register config" subsection + the VN forms table
  - new "universal-harm floor" section (distinct from the existing personal-attack redline)
  - EN+VI escalating sample lines for 7/8/9 (one finding, floor-compliant: attack the work/competence, never harm cats)
  - first-person scaling note already covers 3-6; extend to "7-9 fuse first-person with the harsher register"

## Implementation Steps
1. Extend the six-levels table → nine; columns = register / profanity (work-targeted) / personal-attack / cite+fix.
   No aliases for 7-9.
2. Add why/fix label rows for 7-9 (vi+en), monotonic intensity (PO-ranked 2026-06-02:
   `toang≈hỏng < chết ở chỗ < vì sao đi đời < banh nóc < nát bét < banh xác`, banh xác is the apex). Final couples: L7
   "Banh nóc vì / Gõ lại cho tử tế", L8 "Nát bét vì / Gõ lại ngay", L9 "Banh xác vì / Gõ lại, đừng để tao nhắc lại"
   (and the L4-L6 why-labels shift up: L4 Hỏng vì, L5 Chết ở chỗ, L6 Vì sao đi đời). Keep "defaults not straitjacket".
   NB: `đừng để tao nhắc lại` is an authoritative scolding idiom (IN), not a violence threat.
3. **Author the IN/OUT adjudication table** (15-20 native-reviewed borderline VI lines, target-based: see the IN/OUT
   lists above). This is the authoritative floor spec referenced by the agents + humanizer + e2e judge.
4. Write the register-config subsection + the VN surface-form table (gender/dialect/profanity → exact strings;
   profanity is work-targeted only, no `đụ má`/`đậu xanh`).
5. Write EN + VI escalating samples for the SAME finding across lv7/8/9 (model floor-compliance: profanity + mày/tao
   aimed at sloppy WORK, zero protected-characteristic/threat/self-harm/sexual/family-target content).
6. Write the EN-mapping note (no pronoun ladder; profanity-presence is the hard lv7→8 boundary; gender/dialect VI-only).

## Success Criteria
- [ ] Levels table has 9 rows; 7-9 specify register, work-targeted profanity, attack scope, cite+fix.
- [ ] IN/OUT adjudication table exists (target-based), states it holds at lv9 even with consent, native-reviewed.
- [ ] lv7/8/9 sample lines exist in BOTH vi and en, each floor-compliant + grounded (ID:line + fix).
- [ ] Register config maps gender/dialect/profanity to concrete WORK-TARGETED surface strings (no family/sexual tokens).
- [ ] EN 7 vs 8 are mechanically distinct (profanity off at 7, on at 8).
- [ ] No em/en dashes introduced; prose natural VN/EN.

## Risk Assessment
- **Highest-risk phase** (this is where harmful output could originate). Mitigation: the IN/OUT table is the explicit,
  native-reviewed floor spec; samples model compliance; floor is enforced downstream by the humanizer override (Phase 3)
  + the LLM judge (Phase 6). There is NO token-denylist (dropped by PO — it cannot catch compositional harm). Every
  committed lv7-9 sample + the IN/OUT table get native human review before merge; if any line reads like it crosses the
  floor, it is rewritten or cut.
