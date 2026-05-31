---
phase: 3
title: "Bilingual Question Banks"
status: completed
priority: P2
effort: "5h"
dependencies: [2]
---

# Phase 3: Bilingual Question Banks

## Overview
Author the phase-by-phase PO interview question banks in **both English and Vietnamese**, plus the elicitation-framework prompt sets (5-Why, MoSCoW, Story-Mapping). These drive the AskUserQuestion interview the skill runs against the product owner. Structured so each question maps to the artifact field it fills.

## Requirements
- Functional: cover Vision → BRD → PRD → Epic → Story phases; each question pre-fills sensible AskUserQuestion option defaults; questions tagged with the target frontmatter field / doc section they populate.
- Non-functional: EN + VI authored in parallel, same IDs/structure; Vietnamese fully diacritic-correct; PO-friendly language (no jargon, no eng terms like story points).

## Architecture
- **One bank per phase**, each with EN + VI variants keyed by `lang`. Question record: `{id, phase, target_field, en: {q, options[]}, vi: {q, options[]}, follow_up: 5why?}`.
- **Framework prompts** woven in: MoSCoW scope-gate ("if X delays launch, still must-have?"), Story-Mapping ("walk me through a user's day"), 5-Why drill for vague answers.
- **Adaptivity rules** (consumed by P7): skip questions already answered by PRODUCT.md; trigger 5-Why when an answer is vague; cap personas at 2–4.
- Format: markdown reference files (LLM reads + adapts) — NOT executable; the skill composes AskUserQuestion calls from them. Keeps logic in the LLM layer, banks as content.

## Related Code Files
- Create: `references/interview-vision.md` (EN+VI)
- Create: `references/interview-brd.md` (EN+VI)
- Create: `references/interview-prd.md` (EN+VI)
- Create: `references/interview-epic-story.md` (EN+VI)
- Create: `references/interview-frameworks.md` (5-Why / MoSCoW / story-mapping prompts, EN+VI)
- Read for input: research tools-report §4,§7 (frameworks, phased interview); brainstorm §6

## Implementation Steps
1. Vision bank: problem narrative, personas (co-create, cap 2–4), value prop, north-star, horizon — EN+VI; tag each → vision.md section / PRODUCT.md label.
2. BRD bank: business goals, success metrics, stakeholders, constraints, market — map to BRD goal IDs + goal→metric table.
3. PRD bank: per feature-area — overview/problem, use cases, functional reqs (MoSCoW), NFRs, scope in/out, dependencies, open questions.
4. Epic/Story bank: epic goal + links; story As-a/I-want/so-that + AC + size(S/M/L) + personas.
5. Frameworks bank: MoSCoW gate, story-mapping walkthrough, 5-Why templates; adaptivity rules block.
6. VI pass: translate every question/option with correct diacritics; keep IDs/field tags identical.

## Success Criteria
- [ ] Five interview reference files exist, each EN + VI, structurally identical.
- [ ] Every question tagged with the frontmatter field or doc section it fills.
- [ ] MoSCoW, story-mapping, 5-Why prompts present and PO-friendly (no eng jargon).
- [ ] Persona cap (2–4) and skip-if-known adaptivity rules documented.
- [ ] Vietnamese text fully diacritic-correct (spot-review).

## Risk Assessment
- **Bank bloat / decision fatigue** → mitigate: keep core questions tight (research: ~12–15 per full run); mark optional deep-dive questions separate.
- **VI translation quality** (unresolved: who reviews) → mitigate: flag for native review in P8; ship EN-verified, VI best-effort with review note.
