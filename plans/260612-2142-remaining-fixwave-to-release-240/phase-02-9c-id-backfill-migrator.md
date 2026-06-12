---
phase: 2
title: '#9c id-backfill migrator'
status: completed
priority: P2
effort: 0.75d
dependencies: []
---

# Phase 2: #9c id-backfill migrator (BUILD+TEST ONLY in cook)

> **Red-team H1:** the migrator's gate is flag-presence only (`--apply`+`--confirmed-by`+`--date` → writes),
> so an autonomous cook *could* self-supply those flags. Therefore this phase is **build-and-test ONLY**:
> all `--apply` runs in cook target **synthetic fixtures** with test-supplied flags. The cook NEVER runs
> `--apply` against a real approved artifact. The PO's real artifacts live in a separate Cleanmatic-ERP repo;
> backfilling them is a **PO-side post-upgrade action** (dry-run → human re-approve), not part of this run.

## Overview
Add `id: PRODUCT` to the PRODUCT.md template, plus a separate GATE-safe migrator that backfills a missing
`id:` into existing artifacts. Mirrors `migrate_metric_to_metrics.py` exactly: dry-run 0-byte default,
`--apply` requires `--confirmed-by`+`--date`, entry-scoped, idempotent, GATE re-approve. The migrator is the
mechanism; running it against real approved artifacts is deferred to a human-driven step.

## Requirements
- Functional: new `migrate_backfill_ids.py`. Dry-run (default): report artifacts missing `id:` + the value it
  would insert (derived from artifact type/filename canonical id, e.g. PRODUCT.md → `id: PRODUCT`). `--apply` +
  `--confirmed-by` + `--date`: insert `id:` into frontmatter, entry-scoped, `.bak`-once, idempotency guard,
  `schema_version` stamp only if changed. Approved artifacts → `confirm_required` list, never silent.
- Template: PRODUCT.md template gains `id: PRODUCT`.
- Non-functional: never touch an artifact that already has `id:`. BOM/comment preserving. GATE-NEVER-ASSUME:
  cook runs dry-run → AskUserQuestion → re-approve owner+date before `--apply` on any approved artifact.

## Architecture
Replicate `migrate_metric_to_metrics.py` contract verbatim (scout-confirmed):
- Dry-run returns `{applied:False, would_insert:[...], confirm_required:[...], error:None}`, writes 0 bytes.
- `--apply` alone → error `confirmation_required: --apply must be accompanied by BOTH --confirmed-by AND --date`.
- Per-artifact guard: skip if frontmatter already has `id:` (idempotent — original returned untouched, no marker write).
- `.bak` created once (`name + ".bak"`, never overwrite).
- `schema_version` stamp inserted only when something changed AND no marker present.
- Approved artifact (`status: approved`) → added to `confirm_required`, requires explicit `--confirmed-by`+`--date`.

## Related Code Files
- Create: `.claude/skills/product-spec/scripts/migrate_backfill_ids.py`
- Modify: PRODUCT.md template (find under `.claude/skills/product-spec/` templates/assets — add `id: PRODUCT`)
- Create: `.claude/skills/product-spec/scripts/tests/test_migrate_backfill_ids.py`
- Modify: REVIEW.md (relevant proposal #9 row), EVIDENCE.md, decisions.md (DEC for build-new + GATE pattern)

## TDD — tests first
1. `test_dry_run_reports_missing_id_zero_bytes` — artifact missing id → would_insert lists it; file byte-identical after.
2. `test_apply_requires_confirmed_by_and_date` — `--apply` alone → error, no write; both → writes.
3. `test_already_has_id_untouched` (negative/no-over-fix) — artifact with `id:` present → not in would_insert, byte-identical.
4. `test_apply_idempotent` — run `--apply` twice → second run 0 changes, single `.bak`, original preserved.
5. `test_approved_artifact_lands_in_confirm_required` (GATE) — approved artifact missing id → confirm_required, not auto-written.
6. `test_bom_and_comment_preserved` — frontmatter with BOM/comments → preserved on insert.
Synthetic BRD/PRODUCT fixtures (no real PO data), mirroring `test_migrate_metric_to_metrics.py`.

## Implementation Steps
1. Write 6 RED tests.
2. Implement `migrate_backfill_ids.py` cloning the metric→metrics structure (plan→transform→migrate contract).
3. Add `id: PRODUCT` to PRODUCT.md template.
4. GREEN; run product-spec suite + CONTRIBUTING:69.
5. **No real-artifact apply in cook**: all `--apply` runs in this phase are on synthetic fixtures with
   test-supplied flags. Do NOT run `--apply` against any real approved artifact during the autonomous run.
6. DEC + EVIDENCE; tick proposal #9 migrator row.

## Success Criteria
- [x] 6 tests green incl. idempotency + already-has-id negative + approved→confirm_required GATE.
- [x] Dry-run writes 0 bytes; `--apply` refuses without both flags.
- [x] PRODUCT.md template carries `id: PRODUCT`.
- [x] **No real artifact mutated during cook** (build+test-only; synthetic fixtures only).
- [x] product-spec suite + CONTRIBUTING:69 green; DEC + EVIDENCE recorded.

## Risk Assessment
- Silent rewrite of approved artifact → confirm_required gate + GATE-NEVER-ASSUME interview in cook; idempotency test.
- Wrong id derived → id derivation table per artifact type, tested; dry-run shows value before any write.

## Decisions

### DEC-P2-1 — build-new migrator with mirrored GATE contract (not shared helper extraction)
- **Decision:** implement `migrate_backfill_ids.py` as a self-contained sibling mirroring
  `migrate_metric_to_metrics.py`'s GATE contract in its own module, rather than extracting
  a shared helper from the existing migrator.
- **Rationale:** no shared helper exists in the codebase (DRY scan confirmed). The two migrators
  have structurally similar GATEs but different transformation domains (key rename vs id insertion).
  Extracting a shared helper would couple unrelated migration concerns and risk breaking the locked
  invariants of `migrate_metric_to_metrics.py`. KISS + YAGNI: mirror the contract, keep each
  migrator self-contained and independently evolvable.
- **Owner:** hieubt · **Date:** 2026-06-12
