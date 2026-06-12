---
phase: 9
title: "Upgrade-một-lệnh + legacy-sweep — implementation report"
date: 2026-06-12
status: completed
---

# Phase 09 Implementation Report

## Files Created

| File | Lines | Notes |
|------|-------|-------|
| `.claude/skills/release/scripts/upgrade_planner.py` | 278 | Pure planner, no disk writes; PlanItem dataclass; NOOP/REMOVE/PROMPT/UNLINK_ONLY actions; CLI with --dry-run\|--apply (mutually exclusive) + --json; assert→ValueError for dir pristine_sha type |
| `.claude/skills/release/scripts/upgrade_apply.py` | 271 | Mutator only; atomic all-or-nothing; timestamped backup dir; rollback-manifest.json; rollback(); faithful symlink round-trip (backup sidecar + symlink_target in manifest + os.symlink restore) |
| `.claude/skills/release/assets/templates/upgrade.sh.template` | 150 | bash 3.2-safe; set -euo pipefail + trap ERR auto-rollback; dry-run default; --apply; --rollback (find\|sort\|tail, no process substitution); gitignore backup dirs; migrate dry-run only |
| `.claude/skills/release/assets/templates/upgrade.ps1.template` | 148 | PowerShell parity; -Apply/-Rollback; try/catch auto-rollback around Steps 2+3; gitignore backup dirs; migrate dry-run only |
| `.claude/skills/release/scripts/tests/test_upgrade_planner.py` | 304 | 13 unit tests |
| `.claude/skills/release/scripts/tests/test_upgrade_apply.py` | 333 | 13 unit tests (+2: symlink round-trip + atomic mid-apply symlink restore) |
| `.claude/skills/release/scripts/tests/test_upgrade_e2e.py` | 631 | 12 tests (+2: shell --rollback e2e + Step-2-failure auto-rollback; bundle-embed test strengthened with byte-integrity + sha256 checks) |

## Files Modified

| File | Change |
|------|--------|
| `.claude/skills/release/scripts/pack/selection.py` | `render_embedded()` now embeds upgrade.sh/ps1 + _upgrade/*.py + legacy-map.json |
| `.claude/skills/release/scripts/pack/pipeline.py` | Two-phase MANIFEST build: preliminary tokens → render_embedded → final manifest with extra_embedded sha256s |
| `.claude/skills/release/scripts/pack/manifest_io.py` | `build_manifest_json()` + optional `extra_embedded` param; extracted `_collect_file_entries()` helper; stays ≤198 LOC |
| `.claude/skills/release/assets/templates/INSTALL.md.template` | Added bilingual "Upgrading / Nâng cấp" section |
| `.claude/skills/release/scripts/tests/test_golden_synthetic.py` | EXPECTED_FILES updated (+5 upgrade entries) |

## 7 Required Behaviors — Test Status

| # | Test name | Status |
|---|-----------|--------|
| 1 | `test_dry_run_lists_plan_and_writes_nothing` | PASS (test_upgrade_e2e.py + test_upgrade_planner.py::test_plan_writes_nothing_to_disk) |
| 2 | `test_apply_produces_clean_install` | PASS (e2e, real bundle) |
| 3 | `test_po_edited_legacy_file_prompts_not_deleted` | PASS |
| 4 | `test_symlink_target_not_followed_on_delete` | PASS |
| 5 | `test_rerun_keeps_original_backup` | PASS |
| 6 | `test_failure_mid_upgrade_rolls_back` | PASS |
| 7 | `test_upgrade_runs_migrate_dry_run_only` | PASS (static + e2e) |
| + | `test_upgrade_sh_bash32_syntax` | PASS (docker bash:3.2) |
| + | `test_bundle_embeds_upgrade_payload` | PASS (real bundle + MANIFEST entries) |

## pytest Result

```
276 passed, 19 skipped in ~25s
```

Baseline was 272 passed / 19 skipped (post-phase-09 original). After fold: +4 new tests (2 apply + 2 e2e).
0 failures.

## Docker bash:3.2 Result

`bash:3.2 -n upgrade.sh` → PASS (0 exit code, no syntax errors)

## Architecture Notes

- **Circular MANIFEST dependency resolved via two-phase build**: preliminary manifest_json (from selection only) feeds token rendering; post-render, final manifest_json is rebuilt with extra_embedded (all non-MANIFEST rendered files) so install.sh/upgrade.sh/_upgrade/*.py carry sha256 integrity entries.
- **upgrade.sh is bash 3.2 safe**: no `declare -A`, no process substitution; `--rollback` newest-backup discovery uses plain `find | sort | tail -n1` pipeline; loop uses `for arg in "$@"` case-match.
- **Sweep is atomic + auto-recovered**: `trap ERR` (bash) / try-catch (PowerShell) auto-rolls-back the legacy sweep via `upgrade_apply.py --rollback` if a post-sweep step (force-install or migrate) fails; re-running `--apply` is safe because force-install is idempotent.
- **Symlink round-trip is faithful**: `_copy_to_backup` stores the `readlink` target in the manifest entry; `_restore_from_backup` uses `os.symlink` to recreate the link — never `shutil.copy2` from the sidecar file.
- **migrate: dry-run only** in upgrade.sh — grep confirms no `--apply`/`--confirmed-by` on migrate invocation lines.

## Unresolved Questions

None.
