---
phase: 5
title: "Impact Engine and Migration"
status: pending
priority: P2
effort: "1.5d"
dependencies: [4]
---

# Phase 5: Impact Engine and Migration

## Overview

Two workstreams. **(A) Impact-engine:** a per-change propagation pass that runs on both `--update` and `--validate`, uses the existing `downstream(id)` closure to find affected nodes, and (LLM layer) annotates each with which dimension is touched + a 1-line interpretation + an action suggestion — writing an impact report and extending the change-log. **(B) Migration:** a script that brings existing v1 specs up to the v2 schema with empty placeholders, backups, and `approved`-artifact confirm-per-item (never auto-edits an approved file).

## Key Insights (grounded)

- `spec_graph.downstream(id)` (line 251) already returns the transitive child closure — the propagation engine exists; this phase ADDS interpretation + output, not graph traversal.
- Script-vs-LLM split (Q37): `downstream()` + report-file write + change-log append = deterministic; per-node dimension/interpretation/contradiction = LLM.
- No-auto-edit-approved (Q22/Q59 → G-A3): a contradiction with an `approved` artifact → contradiction protocol (keep/change/hybrid) via AskUserQuestion; the engine NEVER auto-flips.

## Requirements

- **Impact:** trigger on `--update` AND `--validate` (Q23); per affected node emit `{node, dim_touched, one_liner, action}`; write `docs/product/impact/<ts>.md`; append change-log entry with `dims` (Q62; `affected_set` already exists — extend, don't re-add); approved + contradiction → protocol.
- **Migration:** add v2 fields as empty placeholders to v1 specs; back up originals; `approved` files deferred to a confirm list (PO confirms per item); idempotent; deterministic.

## Architecture

### Impact-pass flow (report §5.2)

```
--update | --validate
  → spec_graph.downstream(changed_id)        [script, deterministic]
  → for each node: LLM tags dim + 1-liner + action
  → node approved & contradicts change? → contradiction protocol (keep/change/hybrid)   [G-A3]
  → write docs/product/impact/<ts>.md         [templated]
  → append change-log: + dims (affected_set already exists)  [structured]
```

- **Changed set on `--validate`** (UQ1 — there is no single `changed_id` on a whole-spec run): derive it from the **snapshot delta** — `.snapshots/` is already written every `--validate`; compare to the previous snapshot → the added/changed node IDs become the change set, then run `downstream()` on each. First run / no baseline → no impact-pass (nothing changed). Reuses the existing delta infra (DRY).
- **Impact ≠ validation-catalog:** the impact-pass is per-CHANGE propagation; the catalog checks (`risk_blindspot`/`time_realism`/`competitive_drift`) are per-ARTIFACT quality. Both LLM-layer, independent (report §5.4) — keep them separate so neither bloats the other.

### change-log entry (extended)

```yaml
- ts: 2026-05-30T10:00:00
  changed: PRD-AUTH
  affected_set: [PRD-AUTH-E1, PRD-AUTH-E1-S1]   # ALREADY EXISTS in change-log-entry.md — do NOT re-add (F13)
  dims: [risk, time]                              # NEW — the only field this phase adds
  note: "..."
```

### Migration (Q57/Q60)

`migrate_multidim_fields.py --root <dir> [--apply]`:
- Dry-run default: report which files lack which v2 fields.
- `--apply`: write empty placeholders (`risks: []`, `target_date: null`, `depends_on: []`, `competitive_parity: {}`, BRD `competitors: []`); copy original → `*.bak` first.
- `status: approved` files → NOT written; emitted in a `confirm_required` list for the PO to approve per item (LLM drives AskUserQuestion). Placeholder presence reduces Q25 "warn-if-missing" noise.

## Related Code Files

- Modify: `references/workflow-auto-and-update.md` (impact-pass on `--update`), `references/workflow-validate.md` (impact-pass on `--validate`).
- Create: impact report template (under `assets/templates/`) + `docs/product/impact/` output dir convention.
- Modify: change-log schema + writer (`assets/templates/change-log-entry.md` or generator) → add `dims` ONLY (`affected_set` already present — F13).
- Create: `scripts/migrate_multidim_fields.py` + `scripts/tests/test_migration.py`.
- Note: `docs/product/impact/` must be added to the SKILL.md output layout (done in Phase 7 — G-H3 / F11).
- Modify: `eval/evals.json` + fixtures (`impact-pass`).

## Tests First (TDD)

| Test | Scenario | Expect |
|------|----------|--------|
| `test_migration_adds_placeholders` | v1 PRD missing v2 fields | `--apply` adds empty placeholders + `.bak` |
| `test_migration_skips_approved` | approved artifact | NOT edited; in `confirm_required` list |
| `test_migration_idempotent` | run twice | second run = no-op (fields present) |
| `test_changelog_schema` | append entry | `affected_set` + `dims` present |
| eval `impact-pass` | change PRD-AUTH, approved epic downstream | impact report lists nodes+dims+action; approved → contradiction protocol surfaced |
| `test_impact_pass_triggers` | both `--update` + `--validate` | impact report written both times |

## Implementation Steps

1. **RED:** `test_migration.py` (placeholders/approved-skip/idempotent) + `test_changelog_schema` + eval `impact-pass`.
2. Build `migrate_multidim_fields.py` (dry-run, `--apply`, backup, approved confirm list) → GREEN.
3. Extend change-log schema + writer (`affected_set`, `dims`).
4. Wire impact-pass into `--update` + `--validate` workflows (downstream() + LLM annotation + report file).
5. Contradiction protocol on approved nodes (reuse existing keep/change/hybrid; do NOT duplicate logic — G-A3).
6. Full pytest + eval green.

## Success Criteria

- [ ] G-F1 impact-pass runs on `--update` AND `--validate`; uses `downstream()` + LLM 1-liner + action.
- [ ] G-F2 `docs/product/impact/<ts>.md` written; change-log gains `dims` (`affected_set` already present).
- [ ] G-F3 migration: placeholders + backup; approved confirm-per-item; idempotent.
- [ ] G-A3 no-auto-edit-approved: contradiction surfaced, never auto-flipped.
- [ ] G-B1/B2: downstream()+write deterministic; interpretation LLM-only.

## Risk Assessment

- **Impact-pass duplicates catalog logic** → keep per-change vs per-artifact separate (report §5.4); cross-phase review checks for overlap. TB.
- **Migration corrupts an approved file** → approved never written (deferred to confirm list) + `.bak` for everything; idempotent. Tested. LOW.
- **Impact report noise on large downstream sets** → 1-liner per node, grouped by dim; `--update` scopes to the changed subtree. LOW.

## Goal Gates Covered

G-F1, G-F2, G-F3, G-A3.
