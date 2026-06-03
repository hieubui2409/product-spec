---
phase: 6
title: "E2 discovery seed"
status: pending
priority: P2
effort: "1.5d"
dependencies: [3]
---

# Phase 6: E2 discovery seed (`product-spec --discover`)

## Overview
A pre-stage that ingests raw inputs (interview transcripts, support-ticket dumps, competitor notes)
and proposes **candidate** personas / problems / JTBD to SEED the Vision/BRD interview — instead of a
cold start. Complements the interview (which assumes you already know your personas); never auto-commits.

## Requirements
- Functional: `--discover <path(s)>` reads local raw text → proposes candidate personas/problems/JTBD as a DRAFT the Vision interview then confirms field-by-field.
- Non-functional: NEVER auto-commit personas (GATE-NEVER-ASSUME — persona identity/count is never assumed); no network; local files only; scope TIGHT (text in → candidate bullets out).

## Key facts (from research)
- No `--discover` today; closest is `--auto` (decompose a brain-dump YOU wrote into the hierarchy).
- Vision interview V1–V7 (`interview-vision.md`) asks personas as an OPEN question (assumes known) → seeding is genuinely additive, not duplicative.
- Personas live in `PRODUCT.md` (`personas:[slug]` + one-liner; narrative in vision.md). Scout-first rule: resolve from spec before asking.

## Architecture
- Input: local text/md files the PO points at (no network). LLM synthesizes CANDIDATE personas/problems/JTBD; script handles file read + structural assembly of the draft.
- Output: a draft seed presented at interview start ("found these — confirm/edit/reject") feeding V1 (problem) / V2 (personas). PO confirms each before anything is written to PRODUCT.md/vision.md.
- **Distinct from `--auto`:** `--discover` synthesizes UPSTREAM raw inputs into interview seeds; `--auto` decomposes a finished brain-dump into the hierarchy. **Open decision:** ship as separate flag vs prototype inside `--auto` and split only if the distinction proves real (surface to PO).

## Related Code Files
- Modify: SKILL.md (flag + menu), CLAUDE.md pointer table
- Create: `.claude/skills/product-spec/references/workflow-discover.md` (ingest → candidate-synthesis → seed-handoff contract)
- Reuse: `interview-vision.md` (seed feeds V1/V2), `workflow-interview.md` scout-first, GATE-NEVER-ASSUME
- Possibly create: `scripts/ingest_raw_inputs.py` (file read + chunk + structural draft scaffold — keep deterministic parts in script, synthesis in LLM)

## Implementation Steps
> **TDD:** after step 1, write step 5's tests FIRST (ingest fixture transcripts → candidate draft scaffold; the GATE test asserting NO persona is committed without a confirm step), confirm they fail, then implement to green; re-run full suite. The no-auto-commit gate test is the critical lock.
1. **Surface the E2-vs-`--auto` decision** to PO before build.
2. Write `workflow-discover.md`: input handling (local files only), candidate synthesis rules, the confirm/edit/reject handoff into Vision interview, GATE-NEVER-ASSUME enforcement (no persona written without PO confirm).
3. Optional `ingest_raw_inputs.py` for deterministic file read/scaffold; synthesis stays LLM.
4. Register flag + menu + plain-language description.
5. Tests: ingest fixture transcripts → candidate draft scaffold; assert NO persona is committed without a confirm step (gate test).

## Success Criteria
- [ ] `--discover <files>` reads local raw inputs and proposes candidate personas/problems/JTBD as a draft.
- [ ] Draft seeds the Vision interview; PO confirms field-by-field; nothing written to PRODUCT.md/vision.md without confirmation (GATE-NEVER-ASSUME).
- [ ] Scope stays tight (no entity-extraction/clustering gold-plating); no network.
- [ ] Clear distinction from `--auto` documented (or merged per PO decision).
- [ ] Tests pass; 50 existing untouched.

## Risk Assessment
- Highest scope-creep risk in the plan → hard cap: text in → candidate bullets out → interview confirms.
- Risk: overlap with `--auto` → resolve via the open decision; merging is acceptable if cleaner.
- Do AFTER E1 so the closed loop is proven before widening the front door.
