# Validation Rules Spec

The check catalog, the script-vs-LLM ownership split, severity levels, and the findings JSON schema scripts emit. Drives `--validate` and `--approve`.

## Script vs LLM — Non-Negotiable Split

| Layer | Owns |
|-------|------|
| **Script** | Anything answerable by parsing YAML, traversing a graph, counting fields, or matching against a closed enum. |
| **LLM** | Anything requiring reading prose, weighing meaning, or judging quality. |

If a check needs to *understand* the words, it's LLM. If it can be answered by walking edges or counting items, it's script. **No exceptions.** This rule is enforced by the script code review gate (Phase 5) — any heuristic in a script that judges quality must be removed.

## Check Catalog

| ID | Owner | Severity | Trigger | Message Template |
|----|-------|----------|---------|------------------|
| `orphan_story` | script | error | a story whose `epic` field references an unknown epic ID | "Story {id} references unknown epic {epic}." |
| `orphan_epic` | script | error | an epic whose `prd` field references an unknown PRD ID | "Epic {id} references unknown PRD {prd}." |
| `orphan_prd` | script | error | a PRD whose `brd_goals` is empty or all unknown | "PRD {id} has no resolved BRD goals." |
| `orphan_brd_goal` | script | warn | a BRD goal with no PRDs referencing it | "BRD goal {id} has no PRDs addressing it." |
| `dangling_link` | script | error | any frontmatter ID reference that doesn't resolve | "{file}: reference {ref} does not resolve." |
| `unaddressed_parent` | script | warn | a parent (epic/PRD/BRD goal) with zero inbound child edges of the expected type | "{id} has no {child_type} addressing it (gap-analysis input)." |
| `missing_ac` | script | error | a story with empty / missing `acceptance_criteria` | "Story {id} has no acceptance criteria." |
| `low_ac_count` | script | warn | a story with `len(acceptance_criteria) < 2` | "Story {id} has fewer than 2 acceptance criteria ({count})." |
| `dup_id` | script | error | two artifacts sharing the same `id` | "Duplicate ID {id} in {files}." |
| `invalid_id` | script | error | an `id` not matching the parent-scoped grammar | "ID {id} does not match expected pattern {pattern}." |
| `unknown_enum` | script | error | a closed-enum field with a value outside the allowed set | "{file}: field {field} value '{value}' not in {allowed}." |
| `parse_error` | script | error | YAML parse failure or missing required field | "{file}: parse error — {detail}." |
| `status_inconsistency` | script | warn | child `approved` under parent `draft`, or descendant approval newer than ancestor | "{id} status inconsistent with parent {parent_id}." |
| `version_inconsistency` | script | warn | child `version` higher than parent (rare; flag only) | "{id} version {v} exceeds parent {pid} version {pv}." |
| `invest_quality` | LLM | warn | a story failing INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable) | "Story {id}: INVEST concern — {dimension}: {explanation}." |
| `vagueness` | LLM | warn | a story or PRD requirement using vague language ("should", "easy", "fast") without quantification | "{id}: vague language — '{phrase}'. Suggest quantification." |
| `core_value_drift` | LLM | warn | an artifact's narrative drifts from PRODUCT.md's core-value sentence | "{id}: core-value alignment is {aligned\|weak\|off}: {rationale}." |
| `gold_plating` | LLM | warn | scope expansion beyond the stated PRD problem | "{id}: gold-plating — {addition} not motivated by stated problem." |
| `semantic_duplication` | LLM | warn | two artifacts express the same intent in different words | "{id1} ≈ {id2}: semantic duplication detected — {explanation}." |
| `contradiction` | LLM | error | a new claim contradicts an `approved` artifact | "{id} contradicts approved {other_id}: {contradiction}. SURFACE TO PO — never auto-flip." |

## `--strict` Gate Behavior

Default behavior (no `--strict`):
- All findings reported.
- The skill proceeds with whatever action was requested.

With `--strict`:
- Any finding with `severity: error` blocks the action.
- The skill stops and presents the errors; the PO must resolve before proceeding.
- `severity: warn` never blocks.

The gate is enforced in the **LLM/orchestration layer** (workflow-validate.md), not in the scripts. Scripts always exit 0; the LLM reads severities and decides.

## Severity Definitions

- **error** — the spec is structurally broken (orphan, dangling link, missing AC, dup ID) or contradicts an approved decision. With `--strict`, blocks.
- **warn** — the spec is structurally OK but may have a quality issue (low AC count, vague language, status inconsistency, unaddressed parent). Never blocks; advisory.

## Core-Value Scoring (LLM)

For every PRD/epic/story, the LLM scores against `PRODUCT.md`'s `core_value` sentence:

| Score | Meaning |
|-------|---------|
| `aligned` | clearly serves the core value |
| `weak` | tangentially serves; could be cut without harm to core |
| `off` | does not serve the core value |

Score + 1-line rationale included in the finding. The PO confirms the `scope: core-value` tag (or chooses `scope: in` / `scope: out`); the script only validates that the tag is one of the allowed enum values.

## Contradiction Protocol (CRITICAL — never auto-flip)

When the LLM detects a contradiction with an `approved` artifact:

1. Emit a finding with `severity: error` and `check: contradiction`.
2. The orchestration layer presents three options to the PO via AskUserQuestion:
   - **Keep** the approved version, reject the new claim.
   - **Change** to the new claim — requires re-approval of the affected artifact(s).
   - **Hybrid** — record both, define a follow-up to reconcile.
3. The skill **never** auto-edits the approved artifact based on the contradiction. The PO decides.

This mirrors the global "No silent reversals" rule in CLAUDE.md.

## Findings JSON Schema (script output)

```json
{
  "schema_version": "1.0",
  "root": "<absolute project root>",
  "checked_at": "<ISO 8601>",
  "findings": [
    {
      "check": "<check_id>",
      "severity": "error" | "warn",
      "artifact_id": "<id-or-null>",
      "file": "<path-relative-to-root-or-null>",
      "detail": "<short message>",
      "context": { /* optional structured detail (e.g. {ref, expected, found}) */ }
    }
  ],
  "graph": { /* see frontmatter-and-id-spec.md → Snapshot Schema */ }
}
```

Multiple scripts run during `--validate`. The orchestrator merges findings (preserves order: traceability → consistency → matrix).

## Human Report Format (LLM layer)

After scripts run and LLM judgment layers on:

```
# Validation Report — <date>

## Summary
- 23 artifacts checked
- 0 errors · 3 warnings
- Strict gate: OFF (no errors block; warns advisory)

## Errors (0)
(none)

## Warnings (3)

### PRD-AUTH-E1-S2 — low_ac_count (warn)
File: stories/PRD-AUTH-E1-S2.md
Detail: Story has 1 acceptance criterion. Suggest ≥2.

### PRD-BILLING — core_value_drift (warn — LLM)
File: prds/billing.md
Detail: Core-value alignment is "weak": billing flow is tangential to "help boutique
brands sell directly". Consider whether this PRD belongs in the next horizon.

### BRD-G3 — orphan_brd_goal (warn)
File: brd.md
Detail: No PRDs address this goal. Either drop, defer, or write a PRD.

## Suggested Next Steps
1. Add 1 more AC to PRD-AUTH-E1-S2.
2. PRD-BILLING: discuss core-value alignment with stakeholders.
3. BRD-G3: decide between drop / defer / new PRD.
```

## What This Spec Does NOT Define

- The exact prose template for the human report — that's the LLM's job.
- The order of script invocations — that's `workflow-validate.md` (Phase 7).
- The interactive flow on `contradiction` — that's `workflow-validate.md`.
- Eval rubric for the LLM judgment checks — that's `eval/evals.json` (Phase 8).
