---
phase: 4
title: "detail_level split wiring"
status: pending
effort: ""
---

# Phase 4: detail_level split wiring

## Overview

Turn the two detail levels from dormant into functional, INDEPENDENTLY: `detail_level` sizes product-spec output;
`critique_detail_level` sizes spec-critique reports. Each gets a PO interview question + a real consumer.

## Requirements
- Functional: product-spec interview captures `detail_level`; product-spec generation honors it. spec-critique honors
  `critique_detail_level`. The two never bleed into each other.
- Non-functional: concise/standard/verbose semantics consistent across both; defaults = standard.

## Architecture

**Semantics (shared vocabulary, separate application):**
| Level | product-spec (`detail_level`) | spec-critique (`critique_detail_level`) |
|-------|-------------------------------|------------------------------------------|
| concise | terse AC/prose, minimal narrative, fewer interview follow-ups | top-3 + one-line-per-lens, no extended pre-mortems |
| standard (default) | current behavior | current behavior (full per-lens) |
| verbose | fuller narrative, more examples, richer rationale | full per-lens + extended why-it-dies + more sources |

**product-spec wiring:**
- `workflow-interview.md`: add ONE preference-seeding question (AskUserQuestion) for detail_level early in the flow;
  persist via `preferences.save`. Honor `GATE-NEVER-ASSUME` (offer the 3 options; default standard if skipped).
- Consumer: the interview/generation guidance reads `preferences.load(root)["detail_level"]` and adjusts prose length.
  (LLM-side guidance, not a script knob — consistent with how `lang` is used.)

**spec-critique wiring:** done in Phase 3 (consolidate reads `critique_detail_level`). Phase 4 only documents the
PO-facing side (how to set it; that it is SEPARATE from product-spec's).

## Related Code Files
- Modify: `.claude/skills/product-spec/references/workflow-interview.md` (capture + consume `detail_level`)
- Modify: `.claude/skills/product-spec/CLAUDE.md` operating-guide section (note detail_level is now live) — only if
  there is a natural home; else skip (avoid bloat).
- Cross-ref: `.claude/skills/spec-critique/references/workflow-critique.md` already reads `critique_detail_level`
  (Phase 3) — Phase 4 adds the PO-facing doc note in GUIDE (Phase 5 owns GUIDE edits; coordinate).

## Implementation Steps
1. workflow-interview.md: add the detail_level seeding question + persistence; document the consumer behavior (how
   concise/verbose change product-spec prose length).
2. Confirm spec-critique's `critique_detail_level` consumer (Phase 3) is independent — no shared variable.
3. Add a short note where preferences are documented that the two keys are separate (so a PO knows verbose specs +
   concise critiques is a valid combo).

## Success Criteria
- [ ] product-spec interview offers a detail_level choice; the chosen value persists to preferences.yaml.
- [ ] Setting `detail_level: concise` changes product-spec prose length; it does NOT change critique report size.
- [ ] Setting `critique_detail_level: verbose` changes critique report size; it does NOT change product-spec output.
- [ ] Both default to standard when unset.

## Risk Assessment
- Low-moderate. Main risk = the two keys being conflated in prose/consumer. Mitigation: Phase 6 has an explicit
  independence test (set one, assert the other's behavior unchanged). Keep the consumer guidance pointing at the
  correctly-named key in each skill.
