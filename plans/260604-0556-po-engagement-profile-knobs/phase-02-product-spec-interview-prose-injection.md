---
phase: 2
title: "Product-spec interview/prose injection"
status: pending
priority: P1
effort: "3h"
dependencies: [1]
---

# Phase 2: Product-spec interview/prose injection

## Overview

Wire the 3 knobs into the product-spec interview + prose flow so they actually change AI behavior. Mostly
reference-doc (markdown) edits at the EXACT points where `detail_level` is already read. Knob VALUES come from the
Phase-1 `preferences.load()` (already unit-tested); this phase is LLM-side guidance, not new script logic.

## Requirements

- Functional:
  - `interview_rigor` sizes claim-challenge + gap/edge/AC probing depth during interview.
  - `action_prompting` sizes density of suggested next-actions.
  - `standing_reminders` injected as always-checks during interview + prose, with `dismissed_reminders` overriding.
  - Orthogonality documented: `detail_level` = verbosity (length); `interview_rigor` = rigor (depth). "Concise but deep" must be expressible.
- Non-functional: no contradiction with existing `detail_level` table; GATE-NEVER-ASSUME respected (defaults are
  quality-posture, not PO judgment).

## Architecture

Read points mirror the existing `detail_level` read (`workflow-interview.md` §Bilingual/prose, ~line 52):
- Add an **Engagement profile** subsection: a knob→behavior table (rigor: light/standard/deep;
  action_prompting: minimal/standard/proactive) parallel to the `detail_level` table.
- Init flow: extend the one-time `AskUserQuestion` (or add a sibling) so a brand-new project can set these once;
  default-and-say-so when unset. Never re-ask once set.
- `standing_reminders` read alongside; precedence rule: a reminder also in `dismissed_reminders` is suppressed.

## Related Code Files

- Modify: `.claude/skills/product-spec/references/workflow-interview.md`
- Modify (if a story/AC probing list lives there): `.claude/skills/product-spec/references/interview-story.md`,
  `interview-epic.md` (only the probing-depth hook lines; keep DRY — point back to workflow-interview.md).
- Read for context: `references/interview-frameworks.md`.

## Implementation Steps

1. Add the **Engagement profile** read subsection in `workflow-interview.md` with the two knob→behavior tables +
   the `standing_reminders`/`dismissed_reminders` precedence note + the orthogonality-vs-`detail_level` callout.
2. Add the init-flow capture line (read current `preferences.load()`; if unset, ask once, persist via Phase-1 CLI).
3. Add hook lines in `interview-story.md`/`interview-epic.md` that defer to the workflow-interview.md home (no
   duplication of the tables).
4. Grounding check: grep that the new subsection cites real keys/enums matching Phase-1 schema.

## Success Criteria

- [ ] `workflow-interview.md` documents reading all 3 knobs at the prose/question-gen point, with concrete
      behavior per enum value.
- [ ] Orthogonality with `detail_level` stated; "concise + deep" is a documented valid combination.
- [ ] `dismissed_reminders` precedence over `standing_reminders` documented.
- [ ] No duplicated tables across interview references (DRY — one home).

## Risk Assessment

- **Drift with `detail_level`**: reviewers may read rigor as "more verbose". Mitigate with the explicit
  orthogonality callout + a concise-but-deep example.
- **Markdown-only = no unit test**: add a tiny grounding test (grep-based) that the doc references the exact enum
  tokens from `preferences.ENUMS` to prevent token drift (mirror `test_voice_examples_grounding.py` pattern).
