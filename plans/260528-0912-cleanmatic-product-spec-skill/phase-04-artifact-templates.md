---
phase: 4
title: "Artifact Templates"
status: completed
priority: P2
effort: "4h"
dependencies: [2]
---

# Phase 4: Artifact Templates

## Overview
Create the markdown templates the skill instantiates for every artifact (PRODUCT.md, vision, BRD, PRD, epic, story) plus the exec-summary, sign-off block, and change-log fragments. Each template carries full frontmatter (per Phase 2 schema) and section skeletons with explicit **REQUIRED vs OPTIONAL** markers so simple products stay lean.

## Requirements
- Functional: templates are valid against the Phase 2 frontmatter schema; placeholders use a stdlib-friendly token (e.g. `{{field}}`) substitutable without jinja2; bilingual section headers (EN/VI selectable by `lang`).
- Non-functional: stored as assets (not loaded into LLM context wholesale); each template self-documents required vs optional sections.

## Architecture
- **assets/templates/** holds one file per artifact. Templates are *data*, not code — `generate_templates.py` (Phase 5) copies + token-substitutes them.
- **Required/optional markers:** each optional section wrapped with an HTML-comment marker (e.g. `<!-- OPTIONAL: dependencies -->`) the generator/LLM can drop for lean products.
- **Section content per brainstorm §14:**
  - PRODUCT.md: thin labels only (name, 1-line desc, current-impl, deployment, roadmap one-liner, core-value sentence, persona labels, `lang`).
  - vision.md: problem narrative, full personas, value prop, north-star, 1–3yr direction; OPTIONAL principles/non-goals, differentiation.
  - brd.md: problem/opportunity, goals+metrics, stakeholders, constraints, market; OPTIONAL assumptions&risks, goal→metric table.
  - prd.md: overview/problem, personas, use cases/flows, functional reqs (MoSCoW), NFRs, success metrics→BRD goals; OPTIONAL scope in/out, deps&risks, open-questions.
  - epic.md: RICH — goal, business-context(→PRD req+BRD goal), success criteria, scope, risks.
  - story.md: RICH — As-a/I-want/so-that, AC list, size, personas, notes.
- **Fragments:** exec-summary template, sign-off block (owner/stakeholder/date in frontmatter+body), change-log entry format.

## Related Code Files
- Create: `assets/templates/product.md`, `vision.md`, `brd.md`, `prd.md`, `epic.md`, `story.md`
- Create: `assets/templates/exec-summary.md`, `sign-off.md`, `change-log-entry.md`
- Read for input: Phase 2 `frontmatter-and-id-spec.md`, `document-model-and-hierarchy.md`; research report §10 (BRD/PRD/epic/story field lists)

## Implementation Steps
1. Define the token-substitution convention (`{{token}}`) + optional-section marker convention; document in a short header comment block reused across templates.
2. Author each artifact template with full frontmatter (all schema fields, sample values) + section skeleton + required/optional markers + bilingual headers.
3. Author exec-summary, sign-off, change-log fragments.
4. Hand-validate: a filled sample of each template parses under the Phase 2 schema (manual check now; automated in P5/P8).

## Success Criteria
- [ ] Nine template/fragment files exist with schema-complete frontmatter.
- [ ] Required vs optional sections explicitly marked in every template.
- [ ] Placeholder + optional-marker conventions consistent and jinja2-free.
- [ ] A filled sample of each validates against the Phase 2 frontmatter schema.
- [ ] Bilingual headers present (EN/VI).

## Risk Assessment
- **Template/schema mismatch** → mitigate: generate templates' frontmatter directly from the Phase 2 field list; P8 test parses every template.
- **Over-heavy defaults** contradicting lean-PO goal → mitigate: aggressive optional-marking; PRODUCT.md stays strictly one-liners.
