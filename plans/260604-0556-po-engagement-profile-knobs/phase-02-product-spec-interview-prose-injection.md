---
phase: 2
title: "Product-spec interview/prose injection"
status: done
priority: P1
effort: "2h"
dependencies: [1]
---

# Phase 2: Product-spec interview/prose injection

## Overview

Wire the 2 knobs into the product-spec interview/prose flow so they change AI behavior. Reference-doc edits placed
**adjacent to the existing `detail_level` preference section** (red-team K — NOT the Bilingual section). Knob values
come from Phase-1 `preferences.load()`; this is LLM-side guidance, not new script logic.

## Requirements

- Functional:
  - `interview_rigor` sizes claim-challenge + gap/edge/AC probing depth during interview.
  - `action_prompting` sizes density of suggested next-actions.
  - **Init-Flow ask, mirroring `detail_level`**: on first interview (or when unset), offer strict-first (deep/proactive)
    vs neutral; persist via Phase-1 `--set`; default `standard` + say-so if skipped; never re-ask once set (red-team Q).
    <!-- Updated: Validation Session 1 — COMBINE into the existing detail_level Init-Flow AskUserQuestion batch when the
    total stays ≤4 questions (max 1 batch = 4); otherwise a separate batch. -->
  - **`interview_rigor` applies at ALL interview levels** (vision/BRD/PRD/epic/story), not just story/epic.
    <!-- Updated: Validation Session 1 — rigor scope = all levels (consistency over selective application). -->
  - Orthogonality with `detail_level` documented: `detail_level` = verbosity (length); `interview_rigor` = rigor
    (depth). "Concise but deep" must be expressible.
- Non-functional: defaults neutral (`standard`) → no GATE-NEVER-ASSUME breach; one home per fact (DRY).

## Architecture

- In `workflow-interview.md`, **Detail-level preference section (`:25-61`)**: add a sibling **Engagement profile**
  subsection with a knob→behavior table (rigor: light/standard/deep; action_prompting: minimal/standard/proactive),
  the orthogonality callout, and the init-ask line (reuse the detail_level one-time-ask pattern at `:31-48`).
- The consume hook mirrors the `detail_level` read at `:51-61` (`preferences.load(root)[...]`).

## Related Code Files

- Modify: `.claude/skills/product-spec/references/workflow-interview.md`
- Modify (hook lines only, defer to workflow-interview.md home): `references/interview-story.md`,
  `references/interview-epic.md` (probing-depth pointer; no duplicated tables).

## Implementation Steps

1. Add the **Engagement profile** subsection adjacent to the Detail-level preference section (`:25-61`), with both
   knob→behavior tables + the `detail_level` orthogonality callout + a concise-but-deep example.
2. Add the Init-Flow one-time `AskUserQuestion` line (mirror `:31-48`): offer strict-first; persist via Phase-1
   `--set`; default `standard` + say-so; never re-ask.
3. Add pointer hook lines in `interview-story.md`/`interview-epic.md` that defer to the workflow-interview.md home.
4. Grounding test: a grep-based test asserting the new subsection cites the exact enum tokens from
   `preferences.ENUMS` (mirror `test_voice_examples_grounding.py`), guarding token drift. Disambiguate the bare token
   `deep` (also used by `critique_inherit_depth`) by matching `interview_rigor` + token together.

## Success Criteria

- [ ] `workflow-interview.md` documents reading both knobs at the consume point with concrete per-enum behavior.
- [ ] Init-Flow one-time ask documented (mirrors `detail_level`); default `standard`; never re-asked.
- [ ] Orthogonality with `detail_level` stated; "concise + deep" is a valid documented combo.
- [ ] No duplicated tables across interview references (DRY); grounding test green.

## Risk Assessment

- **Drift with `detail_level`**: reviewers may read rigor as "more verbose". Mitigate with the orthogonality callout.
- **Bare-token `deep` false grep match** (red-team unresolved Q2): grounding test matches knob+token pairs, not bare
  `deep`.
