---
phase: 7
title: "Docs and 2.0.0 Release"
status: pending
priority: P2
effort: "1d"
dependencies: [6]
---

# Phase 7: Docs and 2.0.0 Release

## Overview

Land the documentation, migrate the worked example, finalize bilingual labels, and bump the skill to **2.0.0** (major — breaking frontmatter schema additions: `risks` enums, `target_date`, `depends_on`, `competitors`, `competitive_parity`). This phase makes the v2 schema authoritative across every reference and verifies the whole skill end-to-end.

## Key Insights (grounded)

- Skill is `v1.1.0` (`SKILL.md:11`); deal-breaker = back-compat (G-A2), so 2.0.0 adds fields as optional — v1 specs still parse. Major bump signals the schema growth, not a hard break.
- `examples/acme-shop` is the worked sample — migrate it via `migrate_multidim_fields.py` (Phase 5) so docs show v2 in action (Q42).
- Bilingual VI ships best-effort with a native-review-pending note (existing convention) — extend to new enums/labels (Q39).

## Requirements

- **Functional:** all references updated to v2; `SKILL.md` flags + version 2.0.0; `CLAUDE.md` version; acme-shop migrated + `--validate` green; full eval suite present + green; VI labels for all new enums/views.
- **Non-functional:** version string `2.0.0` consistent everywhere (G-H2); docs DRY (one home per fact); no plan/finding refs in any doc or commit (project rule).

## Architecture / Doc Surface

| Doc | Update |
|-----|--------|
| `references/frontmatter-and-id-spec.md` | new fields (`risks` enums, `target_date`, `depends_on`, `competitors`, `competitive_parity`), COMP-ID grammar, "what this carries / does NOT carry" (cost still excluded) |
| `references/validation-rules-spec.md` | all new check rows (script: `dep_cycle`,`dep_dangling`,`dep_order`,`time_child_late`,`risk_high_ratio`,`risk_blindspot`,`unknown_ref`,`overdue`; LLM: `time_realism`,`competitive_drift`) + findings schema (`context.cited_data`) |
| `references/document-model-and-hierarchy.md` | competitor identity = BRD home (DRY); impact-pass vs catalog distinction |
| `references/visualization-spec.md` | `time`/`competition`/`dashboard` views; HTML-native default for matrix; ASCII=text-summary retained |
| `references/interview-*.md` | new bilingual question banks: risk (mitigation/status), time (target_date/depends_on), competition (competitors/parity) |
| `SKILL.md` | flags (`--viz time|competition|dashboard`, `time_advisory`), version `2.0.0`, output contract (`docs/product/impact/`) |
| `CLAUDE.md` (repo root) | version + any new operating notes |
| `examples/acme-shop/*` | migrated to v2 with realistic risk/time/competition data |
| `eval/evals.json` + fixtures | all dimension + impact + migration + backcompat scenarios |

## Tests First (TDD)

| Test | Scenario | Expect |
|------|----------|--------|
| `test_version_consistency` | grep version across SKILL.md/CLAUDE.md/refs | all `2.0.0` |
| eval `backcompat-v1-spec` | a pre-v2 spec (no new fields) | parses + validates + visualizes, NO error |
| `test_acme_shop_validate` | migrated example | `--validate` → 0 structural errors |
| `test_i18n_new_labels` | `--lang vi` on new views/enums | localized labels + native-review note |
| full eval suite | all scenarios | green |

## Implementation Steps

1. **RED:** `test_version_consistency`, `backcompat-v1-spec` eval, `test_acme_shop_validate`, `test_i18n_new_labels` — fail initially.
2. Update each reference doc (table above) to v2 schema + check catalog.
3. Bump version → `2.0.0` in `SKILL.md` frontmatter + `CLAUDE.md` + any version string in refs.
4. Migrate `examples/acme-shop` (run Phase-5 migration, then add realistic v2 data) → `--validate` green.
5. Finalize `i18n_labels.py` VI for new enums/views + native-review-pending note.
6. Author new bilingual interview-bank questions.
7. Ensure `eval/evals.json` covers every dimension + impact + migration + back-compat; run full suite GREEN.
8. Final whole-skill `--validate` + `pytest` + eval pass.

## Success Criteria

- [ ] G-H1 VI labels for all new enums/views (+ native-review note).
- [ ] G-H2 version `2.0.0` consistent across SKILL.md / CLAUDE.md / references.
- [ ] G-H3 all references updated (frontmatter-id, validation-rules, document-model, visualization, interview banks).
- [ ] G-H4 acme-shop migrated + `--validate` green.
- [ ] G-H5 full pytest + all evals green.
- [ ] G-A2 back-compat eval green (v1 spec still works).

## Risk Assessment

- **Version drift (string in many places)** → `test_version_consistency` greps all; single source where possible. LOW.
- **acme-shop migration leaves placeholders that warn** → add realistic data after migration so the example is exemplary, not just valid. LOW.
- **Docs reference plan artifacts** → project rule forbids; review pass strips any finding/phase refs from docs + commits. LOW.

## Goal Gates Covered

G-H1, G-H2, G-H3, G-H4, G-H5 (+ G-A2). Final phase also satisfies the orchestrator's Ship stage.
