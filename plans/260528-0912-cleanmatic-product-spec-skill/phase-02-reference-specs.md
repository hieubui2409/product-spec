---
phase: 2
title: "Reference Specs"
status: completed
priority: P1
effort: "5h"
dependencies: [1]
---

# Phase 2: Reference Specs

## Overview
Author the authoritative `references/*` specs that every downstream artifact obeys: the frontmatter+ID schema, the document model/hierarchy + traceability semantics, the validation rules catalog (script-vs-LLM split + JSON finding schema), and the visualization spec. These are the *contract* — scripts (P5), templates (P4), viz (P6), and orchestration (P7) all cite them. Build this before code so there is one source of truth.

## Requirements
- Functional: each spec is self-contained, unambiguous, and machine-followable; defines exact field names, ID grammar, link semantics, severities, and the JSON schema scripts emit.
- Non-functional: each reference file < 300 lines; no plan-artifact references in content (stable, self-contained); bilingual-neutral (specs in English; keys/IDs English-only).

## Architecture
- **frontmatter-and-id-spec.md** — canonical YAML schema per artifact. Fields: `id`, `type` (vision|brd|prd|epic|story|goal), parent links (`parent`, `brd_goal`, `prd`, `epic`), `status` (draft|review|approved), `moscow` (must|should|could|wont), `scope` (in|out|core-value), `size` (S|M|L), `horizon` (now|next|later), `owner`, `created`, `updated`, `version` (semver-lite), `personas` (labels[]), `metrics` (refs[]). ID grammar: `BRD-G<n>` (goal), `PRD-<SLUG>`, `E<n>`, `S<n>`. Link resolution rules.
- **document-model-and-hierarchy.md** — Vision/PRODUCT.md/BRD/PRD/Epic/Story roles, the DRY "one home per fact" rule, BRD(1)↔PRD(many) relationship, what content lives where (avoid PRD↔story overlap: PRD owns narrative/scope/NFR/metrics, stories own decomposition+AC).
- **validation-rules-spec.md** — the check catalog as a table: each check → owner (script|LLM) → severity (error|warn) → message template. Embeds the **script-vs-LLM split** verbatim (structural-only scripts; LLM judgment). Defines findings **JSON schema** scripts emit (`{check, severity, artifact_id, file, detail}`), and the `--strict` gate (errors block, warns don't).
- **visualization-spec.md** — the 9 views (traceability tree, status heatmap, scope/value map, roadmap, persona×feature, gap-analysis, MoSCoW quadrant, risk matrix, delta/diff) × **3 formats (ASCII, Mermaid, inline-vendored HTML)** — SVG/PNG dropped (validate gate); the graph-JSON input shape (shared with P5 matrix); flag→view/format mapping.
- **roadmap + lang conventions** — `now/next/later` horizon vocabulary; `lang: en|vi` localizes prose/interview only, keys/IDs stay English.

## Red-Team Corrections (decide HERE — schema phase)
- **ID allocation (C2 — CONFIRMED parent-scoped):** IDs are **parent-scoped**: `BRD-G<n>`, `PRD-<SLUG>`, `PRD-<SLUG>-E<n>`, `PRD-<SLUG>-E<n>-S<n>`. Globally unique by construction; no batch allocator needed. Specify grammar + next-`<n>`-within-parent rule precisely.
- **`.session.md` schema (H3):** define it here. YAML frontmatter: `phase`, `lang`, `answers: {question_id: value}`, `pending: [question_ids]`, `updated`. Phase 7 resume + §17 stale-detection key off this.
- **Snapshot JSON (H4):** define a graph-snapshot JSON shape persisted under `docs/product/visuals/.snapshots/` (written on `--validate`); delta/diff viz compares two snapshots (no git archaeology).
- **Gap-analysis is structural-only (H1):** spec output = nodes with zero inbound edges of the expected child type. Sufficiency/quality = LLM layer, label it so.

## Related Code Files
- Create: `references/frontmatter-and-id-spec.md`
- Create: `references/document-model-and-hierarchy.md`
- Create: `references/validation-rules-spec.md`
- Create: `references/visualization-spec.md`
- Read for input: brainstorm decisions report §2,§4,§8,§11; research recommended-architecture report

## Implementation Steps
1. Write `frontmatter-and-id-spec.md`: full field table (name/type/required?/allowed-values/purpose), ID grammar + examples, link-resolution + dangling rules. This is the schema scripts parse.
2. Write `document-model-and-hierarchy.md`: artifact roles, DRY rule, hierarchy diagram, content-ownership table (kills PRD/story overlap).
3. Write `validation-rules-spec.md`: check catalog table (12+ checks w/ owner+severity), findings JSON schema, strict-gate behavior, core-value scoring protocol (LLM scores aligned|weak|off + rationale).
4. Write `visualization-spec.md`: views×formats matrix, graph-JSON shape, flag mapping.
5. Cross-link the four specs; verify each < 300 lines (split if needed).

## Success Criteria
- [ ] Four reference specs exist, each < 300 lines, internally consistent.
- [ ] Frontmatter schema enumerates every field with allowed values; ID grammar unambiguous.
- [ ] Validation spec's script-vs-LLM split matches brainstorm decisions exactly; findings JSON schema defined.
- [ ] Viz spec defines all 9 views × 3 formats (ASCII, Mermaid, inline-HTML — SVG/PNG dropped per validate gate) + graph-JSON shape reused by P5/P6.
- [ ] No plan/finding-code references inside spec content.

## Risk Assessment
- **Spec/code drift** later → mitigate: scripts + templates must cite section anchors; P8 tests assert sample docs validate against the schema.
- **Over-specification** (YAGNI) → mitigate: keep allowed-value lists closed and small; mark optional fields clearly.
