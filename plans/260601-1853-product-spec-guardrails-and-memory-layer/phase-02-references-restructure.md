---
phase: 2
title: "references-restructure"
status: done
priority: P1
effort: "4h"
dependencies: [1]
---

# Phase 2: references-restructure

## Overview
Split 2 bundled reference files (load-only-when-needed / progressive disclosure) and fix 3 cross-file DRY duplications (one authoritative home + link). Prose/structural phase — no script logic; verify by structural checks. Depends on P1 only because it co-edits `workflow-validate.md` (serialize behind P1).

## Requirements
- Functional: `--epic` loads epic-only guidance, `--story` story-only; `--auto` vs `--update` load separately; each of 3 duplicated blocks has exactly one home; all pointer tables + cross-refs updated, zero broken links.
- Non-functional: no semantic content loss in splits (verbatim move); DRY-dup home choice respects Principle 2.

## Architecture
**Splits (progressive disclosure):**
- `interview-epic-story.md` → `interview-epic.md` (E1–E6) + `interview-story.md` (Story Block + S1–S5 + shared Adaptivity). Delete original.
- `workflow-auto-and-update.md` → `workflow-auto.md` (`--auto` flow) + `workflow-update.md` (`--update` flow + Cross-Flag Anti-Patterns). Delete original.

**DRY-dup single-home (one authoritative + link):**
| Block | Authoritative home | Linker (replace body w/ link) |
|-------|--------------------|-------------------------------|
| Contradiction Protocol | `validation-rules-spec.md` (the rule spec) | `workflow-validate.md` → "see validation-rules-spec.md → Contradiction Protocol" |
| Human Report Format | `validation-rules-spec.md` | `workflow-validate.md` |
| Findings (JSON) Schema | `frontmatter-and-id-spec.md` (schema aggregator) | `validation-rules-spec.md` → link |

**Pointer updates:** repo-root `CLAUDE.md → Workflow Pointers` table is owned by **P3** (P3 depends on P2) — P2 supplies the final filenames; P2 itself updates the **SKILL.md** references list + any references-internal cross-links.

## Related Code Files
- Create: `references/interview-epic.md`, `references/interview-story.md`, `references/workflow-auto.md`, `references/workflow-update.md`
- Delete: `references/interview-epic-story.md`, `references/workflow-auto-and-update.md`
- Modify: `references/validation-rules-spec.md` (becomes home for Contradiction Protocol + Human Report Format), `references/frontmatter-and-id-spec.md` (home for Findings Schema), `references/workflow-validate.md` (replace 2 dup blocks with links — **after P1**), `SKILL.md` (references list)
- Read for context: `CLAUDE.md` (Workflow Pointers — edited by P3)

## Verification (structural — no pytest)
1. `grep -rn` the 4 new filenames are referenced by SKILL.md + (P3) CLAUDE.md; old 2 filenames have **zero** remaining references repo-wide.
2. **(red-team RT-10 — content-signature, not heading)** First reconcile the two heading names (`Findings Schema` vs `Findings JSON Schema` → one canonical title). Then grep a distinctive CONTENT line of each dup block (e.g. the schema's `severity` enum row; a verbatim sentence of the Contradiction Protocol) → assert it appears in exactly ONE file; the other file contains only a `→ <file> §<section>` link line. A heading-count grep alone false-passes on synonym titles — do NOT rely on it.
3. No orphaned cross-ref: every `→ <file> §<section>` resolves to an existing heading.
4. Split files: union of headings == original headings (no content dropped).
5. **(coordination from P1)** Update `validation-rules-spec.md:148` prose so the changed-field description references `spec_graph.changed_nodes` (the new single home), not an inline 5-field list.

## Implementation Steps
1. Create the 4 split files (verbatim move of sections + each file's own Adaptivity/anti-pattern tail).
2. Delete the 2 originals.
3. Move Contradiction Protocol + Human Report Format bodies to `validation-rules-spec.md`; move Findings Schema to `frontmatter-and-id-spec.md`; replace vacated copies with one-line links.
4. Update `SKILL.md` references list (rename pointers).
5. Run the 4 structural checks; hand final filenames to P3 for the CLAUDE.md pointer table.

## Success Criteria
- [ ] 4 new ref files created, 2 deleted; heading union preserved.
- [ ] 3 DRY-dups each single-home + link; grep proves no duplicate.
- [ ] Zero broken cross-refs / dangling pointers (grep clean).
- [ ] SKILL.md references list updated.

## Risk Assessment
- Broken cross-ref after rename → mitigated by structural grep gate (#1, #3).
- Shared `workflow-validate.md` with P1/P5/P6 → serialized via `dependencies: [1]` + DAG.
- Content loss in split → heading-union check (#4).
