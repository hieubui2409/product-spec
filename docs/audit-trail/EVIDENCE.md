# EVIDENCE — fixes + proof

One entry per landed fix. Format (copy the block):

```
### <ID> · <CATEGORY> · <SEVERITY> · `file:line`
- **Root cause:** <one sentence — the invariant/race/contract that broke>
- **Before:** <command> → <observed bad state>
- **Fix:** <one sentence — what changed and why it holds>
- **After:** <command> → <observed good state>
- **Note:** <optional — DEC-<n> ref, residual risk, by-design caveat>
```

Rules: before/after are runnable commands (scrub secrets); no plan/finding-code refs
(explain the *why*, not the origin); ID per the README grammar. Size cap ≤200 lines —
roll the oldest cycle into `## Archive` when exceeded.

---

## Cycle 3 — 2026-06-11 (PO field-audit fixes)

### Cycle 3 · P01–P05 landed (condensed; full before/after rolled off per the size cap)
- LIB-5 · CORRECTNESS · HIGH · `telemetry/.../lens_workflow_chains.py` — declared-chains read a deleted
  routing-doc path → silent `[]` vs a ≥1 assertion. Fix: chains → on-demand `data/skill-chains.yaml`,
  `declared_chains()` fail-loud. (`test_declared_chains_loaded_from_data_file` +3)
- LIB-6 · CONSISTENCY · HIGH · `.github/workflows/` — 26 tracked tests had no workflow; the eval gate ran
  `_shared/lib/run_evals.py` off the path filter. Fix: `internal-test-suite.yml` mirrors the CONTRIBUTING
  command + a drift-guard test ties workflow⇄CONTRIBUTING; `_shared/**` path-filtered. (`test_internal_ci_runs_canonical_suite`)
- LIB-4 · CORRECTNESS · HIGH · `hooks/emit_session_summary.py` — `first_timestamp()` read a ts-less meta
  line → `duration_s:0`/empty skills. Fix: `scan_head()` to the first ts'd record + early head Skill calls.
  (`test_duration_nonzero_when_first_record_has_no_timestamp`; subagent-outcome classify deferred to real-transcript.)
- LIB-7 · CORRECTNESS · MED · `hooks/hook_runtime.py` (SCRIPT_RE) — a bare-substring matcher counted a
  grep/ls/cat of a script path as a run + inflated validate pass-rate. Fix: require exec position (command
  boundary / interpreter prefix, incl. abs & `$VAR`). (`test_reference_only_command_is_not_counted_as_run` +2)
- LIB-8 · CORRECTNESS · MED · `hooks/track_script_execution.py` — `session` join key computed, never written
  → script runs un-joinable to the other 3 sinks. Fix: emit `"session"`. (`test_script_record_carries_session_join_key`)
- carry-in · ROBUSTNESS · MED · `telemetry/.../analyze_telemetry.py` — one lens raising crashed the whole
  `--lens all` overview. Fix: per-lens isolation → a visible `{lens,error}` entry, surfaced in md/ascii/mermaid.
- LIB-10 · CONSISTENCY · MED · `CLAUDE.md` + `references/workflow-status.md` — routing said "three skills",
  hiding `telemetry`. Fix: "four" + a telemetry row + a `--status` pointer (footprint baseline regenerated).
- LIB-12 · CLEANUP(i18n) · LOW · `telemetry/.../lens_validate_proxy.py` — an English `reason` leaked under
  `--lang vi`. Fix: a language-neutral `reason_code` localized by the renderer. (`..._no_english_leak_in_vi`)
- LIB-13/14 · CONSISTENCY+CLEANUP · LOW · audit/readback docs + fixtures — added crash-audit + per-hook
  config-gate sections (verified vs `hook_runtime`); re-attributed the memory-gap hook to `product-spec`;
  fixtures dropped the stale `claude-pack` id.
- LIB-3 · CORRECTNESS · HIGH · `release/.../install.sh.template` + `hooks/memory_gap_hook.py` + `hook_runtime.py`
  — an upgrade kept a pre-config-gate hook → exit-2 blocking switched on for a non-opted-in PO. Fix: the
  installer force-replaces an un-gated enforcement hook (`.bak`, `[CONFLICT]` on a PO-edited copy) +
  `memory_gap_mode()` advisory default (warn exit 0; blocking opt-in; missing key = disabled) + a read-only
  product_memory lens. (`test_upgrade_replaces_pre_config_gate_enforcement_hook` +5; baseline regenerated.)
- PS-14 · CORRECTNESS · HIGH · `spec_graph.py` + `parse_critique_report.py` — provenance fingerprint hashed
  only body → an AC-only / BRD-goal edit reused a STALE critique. Fix: a separate per-node `content_hash`
  (body + canonical AC; goals hash title/status/metrics/owner), provenance/apply-only; `body_hash` stays
  AC-blind so the wide caches never churn. (`test_ac_only_edit_changes_content_hash_only` +3)
- PSC-2 · CORRECTNESS · HIGH · `critique_signals.py` + `critique_bundle.py` — `source_files` shipped the WHOLE
  corpus regardless of `--scope`. Fix: filter to `target_ids ∪ ancestry ∪ digest ∪ BRD`. (`test_source_files_scoped_to_target_and_ancestry`)
- PSC-3 · CORRECTNESS · HIGH · `critique_persist.py` (new) + `parse_critique_report.py` — lens-cache/index/state
  were 3 separate writes; skipping one → apply-critique parsed `findings: 0`. Fix: one `--persist` writes all
  three + a prose-fallback marker recovery + `--doctor` reconcile. (`test_persist_writes_lens_cache_index_and_state` +3)
- PS-13 · CORRECTNESS · HIGH · `check_consistency_schema.py` + `migrate_metric_to_metrics.py` (new) — legacy
  singular `metric:` goal key ERROR-blocked an approved BRD + no value-mover. Fix: `legacy_metric_key` WARN +
  a SEPARATE GATE-safe migrator (dry-run 0-byte; `--apply` demands `--confirmed-by`+`--date`; entry-scoped,
  comment-safe rename; stamps `schema_version:2`). A metric-LESS goal still ERRORs. (+6 tests)
- PS-17 · CORRECTNESS · MED · `check_consistency_schema.py` + `spec_graph.py` — goal missing `status` uncaught;
  `moscow` dropped from the node. Fix: `goal_without_status` (WARN legacy / ERROR at `schema_version≥2`); `moscow`
  + `unknown_goal_keys` ride the node. (moscow on CHANGED_FIELDS, NOT content_hash — no cache re-churn.)
- PS-18 · CONSISTENCY · MED · `check_consistency_schema.py` + `spec_graph.py` — a story holding parent-only
  `prd`/`brd_goals` + a non-semver `version` stayed silent. Fix: `misplaced_parent_field` + `bad_version_format`
  WARN; `parse_semver` single-home. (Generic per-type whitelist deferred — would false-positive on `created`/`updated`.)
- PS-21 · CONSISTENCY · MED · `SKILL.md` + `references/frontmatter-and-id-spec.md` — `migrate_multidim_fields.py`
  orphaned from routing. Fix: a "schema migration" callout routes BOTH migrators; frontmatter ref gained
  `schema_version`/`moscow`/version-note. (footprint baseline regenerated.)
- PS-23 · CORRECTNESS · LOW · `encoding_utils.py` + `check_consistency.py` + `spec_graph.py` — piping a JSON
  emitter to `head` → `BrokenPipeError` exit 1, breaking the always-exit-0 contract. Fix: single-home
  `emit_json()` swallows `BrokenPipeError` → exit 0. (`test_check_consistency_survives_broken_pipe`)

### PS-15 · CORRECTNESS · HIGH · `product-spec/scripts/check_fence.py` + `memory_gap.py`
- **Root cause:** the advisory fence scan listed EVERY changed path outside `docs/product/` — including the
  kit's own `.claude/` tree, which a fresh install dirties wholesale → ~2258 warnings / ~1MB `--status` JSON,
  contradicting the "never an over-report" contract.
- **Before:** `--status` on a freshly-installed tree embeds thousands of `.claude/...` fence breaches.
- **Fix:** `check_fence` skips `.claude/` (kit infra, never PO spec content; every other out-of-fence path —
  e.g. `src/` — still surfaces); `_fence_signals` caps the enumerated breaches at 10 and collapses any overflow
  into ONE aggregate signal carrying the full total count.
- **After:** green incl `test_fence_scan_excludes_kit_tree`, `test_fence_signals_cap_with_total`.

### PS-16 · CORRECTNESS · MED · `product-spec/scripts/spec_graph.py` + `check_consistency.py` + `critique_common.py`
- **Root cause:** an artifact with no `id:` was indexed under the internal `<missing-id>` sentinel and (a) was
  never flagged for product/vision (no id pattern), (b) leaked the sentinel into PO-facing findings
  (`artifact_id` + interpolated detail prose) and into the critique bundle's `target_ids`/`source_files`.
- **Before:** an id-less `PRODUCT.md` validated clean; an id-less node with >4 personas emitted a
  `persona_cap_exceeded` finding reading `<missing-id> declares 6 personas…`.
- **Fix:** `^PRODUCT$`/`^VISION$` added to `ID_PATTERN_BY_TYPE`; a sentinel id → `missing_id`/`malformed_id`
  naming the FILE; `make_finding` (the single finding-record home) nulls a sentinel `artifact_id` AND rewrites
  the sentinel to the file path in ANY detail, so no checker can leak it; `_resolve_targets` filters the
  sentinels out of the critique target set.
- **After:** green incl `test_missing_id_names_file_no_sentinel_leak`, `test_sentinel_not_leaked_via_other_checks`,
  `test_product_wrong_id_flagged_invalid`, `test_resolve_targets_all_scope_drops_id_sentinels`.
- **Note:** the `id: PRODUCT` template backfill migrator for legacy id-less specs is deferred to the proposals
  stage (no in-tree spec needs it; the dogfood already carries ids) — the artifact is now flagged, which is the defect.

### P07 · CORRECTNESS · HIGH · `product-spec/scripts/session_staleness.py` + `open_questions.py` (both new) + `spec_graph.py` + `check_consistency.py` + `status.py`
- **Root cause:** `.session.md` is an authorised assume-source, yet a session frozen at date D keeps asserting
  facts that artifacts edited after D — or decisions ruled after D — have moved past; no check flagged this, so a
  new session assuming from a stale session could silently reverse an approved fact. Separately, hanging
  parameters (`cần PO xác định` / `TBD` / `Vẫn còn mở`) rode inside artifacts that look done, with no home: they
  did not block `--validate` and were easy to seal `approved` over.
- **Before:** `--validate` on a spec whose `.session.md` `updated` predates the newest artifact edit (or predates
  an active `DEC-<n>`) reported nothing; `--status` had no open-questions surface; `--approve` could seal an
  artifact carrying an unresolved marker silently.
- **Fix:** `session_staleness.py` reconciles `.session.md` `updated` against `max(artifact updated)` and the
  Decision Register — emitting `session_stale` / `session_superseded` WARN findings on the gate and a `sweep`
  CLI; `decisions.md` is named authoritative (Q5) and the session is NEVER auto-rewritten. `open_questions.py`
  is the single marker-scan home (whole spec tree, skips visuals/snapshots/memory) wired into `--status` and the
  `--approve` open-questions gate. `spec_graph` now carries each artifact's `updated` (NOT in `CHANGED_FIELDS`,
  so no `--status` delta churn; per-node `content_hash` unaffected).
- **After:** `.../python3 -m pytest .claude/skills/product-spec -q` → 697 green incl
  `test_session_stale_when_predates_artifact_edit`, `test_superseding_decisions_listed_decisions_authoritative`,
  `test_staleness_findings_emit_warn_no_sentinel`, `test_marker_in_body_not_just_ac`, `test_status_surfaces_open_questions`.
- **Note:** the supersede-sweep lists DEC candidates by DATE (deterministic); judging whether a session line
  actually contradicts a ruling is the LLM/PO's job (Script-vs-LLM split) — so "decisions win" is realized as
  surfaced-divergence + authority designation, not an automated prose resolver. The whole-tree marker scan
  (vs a `must`-AC-only scan) is intentional: the defect spanned BOTH a story `must` AND free business questions
  in the session notes, which an AC-only scan would miss. Reviewer M1 (docs asserted "must"-only) folded by
  broadening the doc/prompt wording to match the broad scan; the broad contract is locked by a body-line test.

### P08 · PACKAGING · HIGH · `release/assets/templates/install.{sh,ps1}.template` + `pack.manifest.yaml` + `pack/{selection,cli}.py` + `manifest_validator.py`
- **Root cause:** the installer + bundle were authored for the dev kit, not the recipient — `declare -A`
  (bash-4) aborts on macOS's stock bash 3.2 (PACK-3); a hard-coded `claude-pack` brand + a dead
  `/cleanmatic:claude-pack` hint shipped despite an available `{{BUNDLE_NAME}}` token (PACK-4); the bundle shipped
  the dev-repo README/CLAUDE.md and dev rules that invoke `/ck:` skills the recipient never receives (PACK-5);
  nothing gitignored the telemetry JSONL the install writes into the PO's tree (PACK-6).
- **Before:** `bash install.sh` on macOS → `declare: -A: invalid option`; the rendered installer still carried
  `claude-pack`; the bundle's top-level docs were the dev-kit copies; a fresh install left `.claude/telemetry/`
  un-ignored (committable to the PO's GitHub).
- **Fix:** bash-3.2-safe parallel arrays (`SKILL_VERDICT_SLUGS`/`_VALUES` + `_set`/`_get_skill_verdict`) replace
  `declare -A`; brand literals route through `{{BUNDLE_NAME}}`; a new `top_level.source` ships recipient-variant
  README/CLAUDE.md from `assets/recipient/` (repo-root fallback for back-compat) and `rules: []` drops the dev
  rules — backed by a release-check guard (`check_rule_skill_refs`, wired into `pack/cli._load_and_validate`)
  that fails the build if any shipped rule invokes a skill absent from the bundle; the installer appends
  `.claude/telemetry/` to `.gitignore` idempotently, inserting a separator when the file's last line lacks a
  trailing newline so the entry never joins onto the prior line. `top_level.source` is path-safety-checked at
  validate-time (no absolute / `..`).
- **After:** `.../python3 -m pytest .claude/skills/release/scripts/tests -q` → 237 passed / 19 skipped incl
  `test_pack_build_aborts_on_dangling_rule_skill_ref`, `test_install_sh_gitignore_real_block_runtime` (incl the
  no-trailing-newline case), `test_install_sh_skill_verdict_helpers_roundtrip`; `docker run bash:3.2 bash -n` on
  the rendered installer OK + the gitignore/verdict blocks execute correctly under bash 3.2.
- **Note:** DEC-P08-1 — the guard runs at PACK-build time (recipient-bundle composition), not publish-time; it
  is a no-op while `rules: []`, a forward safety net. DEC-P08-2 — the install.ps1 newline-guard is
  correct-by-construction (no PowerShell runtime in CI); the bash leg is the runtime-proven one. DEC-P08-4 (PO
  ruling) — CONTRIBUTING.md dropped from the bundle (dev-kit content; only LICENSE travels per AGPL);
  `test_contributing_md_not_in_bundle` guards it.

### P09 · UPGRADE-PATH (build-new #1; DRY-F02/ARC-F02/CVR-F11/POX-F09) · `release/scripts/upgrade_{planner,apply}.py` + `assets/templates/upgrade.{sh,ps1}.template` + `assets/upgrade/legacy-map.json` + `pack/{selection,pipeline,manifest_io}.py`
- **Root cause:** no 1.x→2.x upgrade path — the installer only ADD/OVERWRITEs and SKIPs existing, so a PO on
  claude-pack 1.x who re-installs gets a Frankenstein tree (two critique skills, two packers, doubled agents,
  a stale CLAUDE.md routing the old skill). Skills/agents/hooks were renamed; nothing sweeps the legacy.
- **Before:** a recipient had no one-command way to migrate; the only options were a manual `rm -rf` (data-loss
  risk, symlink-follow risk) or living with the doubled install.
- **Fix:** `upgrade.sh`/`upgrade.ps1` (dry-run default · `--apply` · `--rollback`) drive a pure deterministic
  `upgrade_planner.plan()` (no disk writes; signature-gated rule removal so a dev repo's own rules are never
  swept; hash-diff against pristine keeps PO-edited files as PROMPT, never blind-delete; symlinks → UNLINK_ONLY,
  never followed) + `upgrade_apply.apply()` (the only mutator: timestamped backup BEFORE every delete,
  all-or-nothing self-rollback on any mid-loop failure, faithful symlink round-trip — sidecar + `symlink_target`
  in the manifest + `os.symlink` recreate on rollback). The Python is EMBEDDED verbatim into the bundle under
  `_upgrade/` (recipient bundle drops the `release` skill per P08); a two-phase MANIFEST build renders the
  embedded files then rebuilds the manifest with their sha256 so install.sh/upgrade.sh/`_upgrade/*` carry
  integrity entries. `trap ERR`/try-catch auto-rolls-back the sweep if a post-sweep install/migrate step fails;
  the upgrade runs `migrate_metric_to_metrics` DRY-RUN ONLY (bash/pwsh cannot drive the approval GATE).
- **After:** `.../python3 -m pytest .claude/skills/release/scripts/tests -q` → 276 passed / 19 skipped (+38 over
  the 238 baseline) incl `test_rollback_recreates_symlink_faithfully`, `test_failure_after_unlink_restores_symlink`,
  `test_shell_rollback_restores_legacy_artifact`, `test_step2_failure_auto_rolls_back_sweep`, and a strengthened
  `test_bundle_embeds_upgrade_payload` (byte-identity of embedded `_upgrade/*` + MANIFEST sha256, MANIFEST not
  self-listed); `docker run bash:3.2 bash -n` on the rendered `upgrade.sh` OK. 3-wave review + critique-challenge
  folded 14 findings (symlink-rollback false-success [HIGH], end-to-end auto-rollback [HIGH], embed-integrity
  test, dropped duplicate planner `--rollback`, mutually-exclusive `--dry-run`/`--apply`, assert→ValueError,
  redundant mkdir, process-substitution removed from `--rollback`, gitignore backups, lazy backup dir, µs ts).
- **Note:** DEC-P09-1..6 (phase-09 file). Bounded atomicity (DEC-P09-2): the destructive sweep is atomic +
  auto-recovered; a full staging-dir+atomic-swap of the install was deliberately NOT built (the plan's own
  highest-risk item; install.sh is force-overwrite/idempotent so re-running `--apply` recovers — no data loss).
  ps1 has no runtime syntax test (no PowerShell in the dev/CI env; DEC-P09-5) — it mirrors the bash:3.2-proven
  logic and shares the same Python planner/apply, so the symlink + atomicity fixes apply to both.

### P12 · DOCS/CLEANUP (PS-19/20/22/24/25 + LIB-11/15/16) · `product-spec/scripts/render_html*.py` + `assemble_audit_trail.py` + `*/GUIDE-*.md` + `*/CHANGELOG.md` + `_shared/lib/context_footprint_baseline.json`
- **Root cause / fixes:** PS-19 changelog claimed a non-reproducible `6090→5371`; PS-20 GUIDEs omitted real flags;
  PS-22 per-run state/cache was committed; PS-24 ascii audit overflowed terminals; PS-25 `render_html.py` was
  ~4× the modularization guideline; LIB-11/15/16 doc-drift.
- **Fix:** PS-19 → `5758→5371 (−6.7%)` + `3820→3677 (−3.7%)`, **reproducible** from tags v2.2.2→v2.3.0 via
  `token_proxy = ceil(len/4)` (`test_changelog_token_proxy` pins it + README convention). PS-20 → `--voice`/
  `--compact-mode` + critique `--gentle/--blunt/--savage` documented; `test_guide_flag_inventory` guards SKILL↔GUIDE
  (every GUIDE flag verified to exist in the skill — no phantom flags). PS-22 → `git rm --cached` 8 state/cache
  paths + gitignore (prose artifacts stay tracked; `test_dogfood_state_untracked`). PS-24 → per-column cap +
  proportional widest-first shrink to ≤120; markdown keeps full text. PS-25 → orchestrator 834→327 lines split
  into 5 modules (assets/risk_grid/count_grid/competition/tooltip/governance), each ≤214 exec-LOC, public API
  re-exported, render byte-identical. LIB-11 = DEC (tracked intentionally — schema loaded by validator, agents
  shipped via manifest). LIB-15 → telemetry GUIDE dead-ref `.claude/rules/skill-workflow-routing.md` → `data/skill-chains.yaml`
  (×2 lines × 2 langs). LIB-16 → SKILL.md memory-hook desc → `product-spec-hooks.json` flag (verified install.sh).
- **Review folds:** split mislabelled a **security regression** as "pre-existing" — `fail_closed_when_libs_absent`
  PASSES at HEAD, FAILS post-split (the lib-existence check moved into `render_html_assets`; the test patched the
  `render_html.*` facade copy → no-op → the inert-when-absent guarantee silently broke). Fixed by patching the real
  home + deleting the dead facade re-export (DEC-P12-1). The XSS `_escape` chokepoint, duplicated 5× by the split
  and **already drifted** into 2 variants, was consolidated into one leaf module `render_html_escape.py` (DEC-P12-2).
- **After:** product-spec 708/708 · critique 188/188 · telemetry 124/124 · `_shared` footprint 43/43 (run in
  separate processes), 0 fail. The `_shared` footprint regression-guard was **already RED at HEAD** (refs grown by
  P03–P07 without a baseline refresh, +668 total; not caused by P12) → baseline regenerated per the gate's own
  documented protocol; the other 3 skills are Δ0 (DEC-P12-4). Finding-code leak-scan CLEAN.
- **Note:** DEC-P12-1..4 (phase-12 file).

### P1-9ab · BUILD-NEW · subsystem-horizon drift + persona portrait gap · `check_consistency_product.py` (new)
- **Root cause:** PRODUCT.md subsystem tables can declare a `horizon` that silently drifts from the matching
  PRD's frontmatter `horizon`; and a persona listed in VISION/BRD frontmatter may have no body portrait section
  — both defects were undetected by the validate gate (no rule existed for either).
- **Before:** `python3 -m pytest .claude/skills/product-spec/scripts/tests/test_check_consistency_product.py -q`
  → `ERROR: ModuleNotFoundError: No module named 'check_consistency_product'` (all 6 tests collection-fail).
- **Fix:** new sibling `check_consistency_product.py` with `check_product_subsystems` (table parser keyed by ID,
  fail-soft on missing/garbled table) + `check_persona_portraits` (heading scan, conservative — heading-absent
  only); wired as 2 dispatch lines at the tail of `check_consistency.check()`. Severity WARN (advisory).
- **After:** `python3 -m pytest .claude/skills/product-spec/scripts/tests/test_check_consistency_product.py -q`
  → `6 passed`. Full suite: `python3 -m pytest .claude/skills/product-spec --tb=no -q` → `728 passed, 1 failed`
  (the 1 failure is `test_dogfood_state_untracked` — pre-existing at HEAD before this phase, confirmed by
  `git stash` baseline run). CONTRIBUTING.md:69 gate: `python3 -m pytest .claude/skills/telemetry .claude/hooks
  .claude/skills/_shared -q` → `219 passed`.

### P2-9c · BUILD-NEW · id-backfill migrator + PRODUCT template id stamp · `migrate_backfill_ids.py` (new)
- **Root cause:** spec artifacts generated or hand-authored before the `id:` requirement was added could
  reach production without a frontmatter `id:` key; `spec_graph` then assigned them the `<missing-id>`
  sentinel, which leaked into PO-facing findings and critique bundles. No migration tool existed to
  repair existing artifacts in a GATE-safe way.
- **Before:** `python3 -m pytest .claude/skills/product-spec/scripts/tests/test_migrate_backfill_ids.py -q`
  → `ERROR: ModuleNotFoundError: No module named 'migrate_backfill_ids'` (5 tests collection-fail, 2 pass
  vacuously). Full suite: 728 passed, 1 failed (pre-existing dogfood-state).
- **Fix:** new `migrate_backfill_ids.py` mirroring `migrate_metric_to_metrics.py` GATE contract exactly:
  dry-run default (0 bytes written), `--apply` gated on BOTH `--confirmed-by` + `--date` (non-zero exit
  if either absent), per-artifact idempotent (.bak-once, schema_version stamp, approved→confirm_required,
  underivable paths skipped + reported). ID derived from filename/subdir per `spec_graph.ID_PATTERN_BY_TYPE`.
  All 7 tests (synthetic fixtures, no real PO data; no `--apply` against any real artifact in cook).
- **After:** `python3 -m pytest .claude/skills/product-spec/scripts/tests/test_migrate_backfill_ids.py -q`
  → `7 passed`. Full suite: `python3 -m pytest .claude/skills/product-spec --tb=no` → `735 passed, 1 failed`
  (1 failure = pre-existing `test_dogfood_state_untracked`, unchanged). CONTRIBUTING.md:69 gate:
  `python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q` → `219 passed`.
- **Note:** DEC-P2-1 (phase-02 file). Build+test only — no real artifact `--apply`'d in cook.
  Real backfill is a deferred PO-side step (dry-run → human re-approve).

### P4-6 · visuals latest-alias + staleness banner + content-hash reuse + --clean retention
- **Root cause:** every viz render wrote a new timestamped file; no stable `-latest` pointer for external
  links; no way to detect content-identical re-renders; no pruning → unbounded HTML accumulation.
- **Before:** `python3 -m pytest .claude/skills/product-spec/scripts/tests/test_visuals_retention.py -q`
  → `ERROR: ModuleNotFoundError: No module named 'visuals_retention'` (6 tests collection-fail).
  Full suite: 741 passed, 1 failed (pre-existing dogfood-state).
- **Fix:** new `visuals_retention.py` sibling (≤130 exec-LOC, stays under 250-LOC module budget): `latest_alias`
  (copy-based alias, symlink-unsupported-FS portable), `staleness_banner` (symmetric diff of sorted node-id lists
  stored in `.signatures/<view>.json` sidecar), `content_hash` + `reuse_if_unchanged` (sha256 hex, sidecar in
  `.hashes/<view>.json`), `clean_old_renders` (keep=5 hard integer, `-latest` files never deleted).
  Wired into `render_html.write` (~8 lines): reuse check → skip write if identical; after fresh write → alias
  refresh + hash record + signature record. `visualize.py` gains `--clean` flag (~8 lines): dispatches to
  `clean_old_renders`, prints JSON list of deleted paths, exits 0. keep=5 is the single authoritative constant
  (`RETENTION_KEEP` in the sibling — DEC-2 records the choice).
- **After:** `python3 -m pytest .claude/skills/product-spec/scripts/tests/test_visuals_retention.py -q`
  → `6 passed`. Full suite: `python3 -m pytest .claude/skills/product-spec --tb=no` → `747 passed, 1 failed`
  (1 failure = pre-existing `test_dogfood_state_untracked`, unchanged). CONTRIBUTING.md:69 gate:
  `python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q` → `219 passed`.
- **Note:** DEC-2 (this file's decisions.md). Alias is copy-based (not symlink) for filesystem portability;
  missing sidecar → treated as changed (safe: forces re-render, never silently reuses stale output).

### P5-14 · snapshot/restore engine + VCS-warn · `snapshot.py` (new) + `status_vcs.py` (new) + `status.py` (wiring only)
- **Root cause:** PO used manual `cp` backups that leaked 88 tracked `*.bak-*` files to GitHub (PS-22 context);
  no structured snapshot/restore mechanism existed; `--status` had no VCS-state visibility (untracked spec tree,
  large uncommitted diff) to help the PO understand backup/commit posture.
- **Before:** `python3 -m pytest .claude/skills/product-spec/scripts/tests/test_snapshot.py -q`
  → `FAILED ×7: ModuleNotFoundError: No module named 'snapshot'` /  `...No module named 'status_vcs'`.
  Full suite: `754 passed, 1 failed` (pre-existing dogfood-state, UNCHANGED; this is taken AFTER P1–P4 landed).
- **Fix:** new `snapshot.py` sibling — `make_snapshot(spec_root, snapshots_home, ts)` (injectable ts for
  deterministic tests; copies spec tree + writes a README; dirs_exist_ok for re-runs), `restore_snapshot`
  (staging-dir + atomic rename swap; refuses `RestoreDirtyError` when git tree is dirty and `confirm=False`),
  `list_snapshots`/`latest_snapshot` (fail-soft empty). New `status_vcs.py` sibling — `vcs_warnings(spec_root)`
  with two checks: `spec_tree_untracked` (outside git, via `git rev-parse --is-inside-work-tree`) and
  `large_uncommitted_diff` (≥ `LARGE_DIFF_FILE_COUNT=5` uncommitted files via `git status --porcelain`;
  threshold is a hard integer constant). `status.py` gains 1 import + 1 `"vcs_warnings"` key in both return
  branches + opt-in CLI dispatch for `--snapshot`/`--restore`/`--list-snapshots` (no auto-hook in any migrator —
  GATE H2 held). `.product-spec-snapshots/` added to `.gitignore`.
- **After:** `python3 -m pytest .claude/skills/product-spec/scripts/tests/test_snapshot.py -q` → `7 passed`.
  Full suite: `python3 -m pytest .claude/skills/product-spec --tb=no` → `754 passed, 1 failed`
  (1 failure = pre-existing `test_dogfood_state_untracked`, unchanged). CONTRIBUTING.md:69 gate:
  `python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q` → `219 passed`.
- **Note:** DEC-3 (decisions.md). Snapshot is OPT-IN ONLY — no migrator auto-hook (deferred per plan H2).
  Restore staging → atomic rename so the live tree is never left partially restored. VCS thresholds are concrete
  integers (LARGE_DIFF_FILE_COUNT=5) in the sibling module — single authoritative source.

### P6-8 · BUILD-NEW · artifact-events sink + heat lens · `track_artifact_edits.py` (new) + `lens_artifact_heat.py` (new)
- **Root cause:** no telemetry existed for which spec artifacts were being edited most frequently; PO had
  no visibility into artifact churn ("which PRD is edited most?"). The PostToolUse hook slot was available
  but unused for Edit/Write/MultiEdit on spec paths.
- **Before:** `python3 -m pytest .claude/hooks/__tests__/test_track_artifact_edits.py .claude/skills/telemetry/scripts/tests/test_lens_artifact_heat.py -q`
  → `13 failed, 0 passed` (ModuleNotFoundError for both modules).
- **Fix:** new `track_artifact_edits.py` hook — `_build_record` WHITELISTS exactly `{ts, artifact_path, op, session}`
  (never reads new_string/old_string/tool_response); `_is_spec_artifact` filters to `docs/product/` prefix;
  registered in `register_telemetry_hooks.py` on `PostToolUse:Edit|Write|MultiEdit` (appended to existing group's
  commands, no clobber). New `lens_artifact_heat.py` — `gather(days)` tallies edits per path, returns rows sorted
  by edit count descending with `last_edit` timestamp; registered in `analyze_telemetry.py` LENSES dict +
  OVERVIEW_ORDER (append-only). VI/EN labels (`heat_h/total/cols/none/a_heat`) appended to `telemetry_render.py`
  `_T` dict; `_md_artifact_heat` renderer added to `_MD` dispatch; ascii status line added. Fail-open via
  `hook_runtime.run_telemetry_hook`; disabled under pytest (PYTEST_CURRENT_TEST + CK_TELEMETRY_DISABLED).
- **After:** `python3 -m pytest .claude/hooks/__tests__/test_track_artifact_edits.py .claude/skills/telemetry/scripts/tests/test_lens_artifact_heat.py -q`
  → `13 passed`. CONTRIBUTING.md:69 gate: `python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q`
  → `232 passed`. Product-spec regression: `python3 -m pytest .claude/skills/product-spec --tb=no` → `754 passed, 1 failed`
  (1 failure = pre-existing `test_dogfood_state_untracked`, unchanged).
- **Note:** DEC-4 (decisions.md). Privacy by construction (GATE H3): `_build_record` is a pure-function whitelist —
  it builds the record dict from exactly the 4 allowed values; it never receives content fields. The H3 test feeds a
  payload containing `new_string`, `old_string`, `tool_response.content` and asserts `set(record.keys()) == {ts,
  artifact_path, op, session}` AND that all content strings are absent from the serialized record. `telemetry_render.py`
  and `analyze_telemetry.py` edits are append-only (import + LENSES key + OVERVIEW_ORDER entry + _T label keys +
  _md_* fn + _MD entry + ascii elif) — P7 can re-read both files clean.

### P7-11 · BUILD-NEW · usage-summary export + read-only harvester · `harvester.py` (new) + `analyze_telemetry.py` (2 flags) + `telemetry_render.py` (2 label keys)
- **Root cause:** no mechanism existed to emit an aggregate usage report for PO review, and no read-only
  feedback-loop surface existed to surface self-correction patterns or churn hot-spots to the dev team.
  Boundary A9 required the harvester to be provably read-only (never write to any skill/template).
- **Before:** `python3 -m pytest .claude/skills/telemetry/scripts/tests/test_harvester.py -q`
  → `4 failed, 1 passed` (missing `--export-summary` flag; `ModuleNotFoundError: No module named 'harvester'`).
  `analyze_telemetry.py --export-summary /tmp/out.md` → `argparse error: unrecognized arguments`.
- **Fix:** new `harvester.py` sibling — `harvest_suggestions(days, corrections_path)` reads
  `docs/product/.memory/self-corrections.json` (category/artifact tallies) and `artifact-events.jsonl`
  (repeat-edit heat, threshold=3); returns `{"suggestions":[{category,artifact,count,why},...]}`.
  Opens files only in read mode by construction — no write-mode open call anywhere in the module.
  `analyze_telemetry.py` gains `--export-summary PATH` (default `.claude/telemetry/usage-summary.md`,
  writes rendered markdown; empty telemetry → valid markdown + exit 0) and `--auto-suggest` (store_true,
  opt-in; absent flag → no suggestions section at all). `_write_export_summary` + `_harvester_section`
  helpers added (append-only to the existing `main()`). VI/EN labels `suggest_h`/`suggest_none` appended
  to `telemetry_render.py` `_T` dict (P6's `heat_h/heat_none/a_heat` lines byte-identical).
- **After:** `python3 -m pytest .claude/skills/telemetry/scripts/tests/test_harvester.py -q`
  → `5 passed`. CONTRIBUTING.md:69 gate: `python3 -m pytest .claude/skills/telemetry .claude/hooks
  .claude/skills/_shared -q` → `237 passed`. Product-spec regression: `python3 -m pytest
  .claude/skills/product-spec --tb=no` → `1 failed` (pre-existing `test_dogfood_state_untracked`, unchanged).
- **Note:** DEC-5 (decisions.md). Boundary A9 test (`test_harvester_never_writes_anything`) monkeypatches
  builtin `open` to raise on any write-mode (`w`,`a`,`x`,`w+`,`wb`,`ab`,`xb`) AND `Path.write_text` /
  `Path.write_bytes` to raise — harvester completes and returns suggestions without triggering any write.
  Opt-in gate (`test_auto_suggest_absent_produces_no_suggestions_section`): without `--auto-suggest`,
  stdout contains neither "## Suggestions" nor "## Gợi ý". PO reviews the exported summary before sending —
  no auto-send, no skill self-edit.

---

## Archive

### Cycle 0 — 2026-06 (condensed; full before/after rolled off per the size cap)
- PSC-1 · CORRECTNESS · HIGH · `product-spec-critique/scripts/critique_inherit.py:59` — fingerprint
  normalizer stripped leading list numbers, merging distinct numbered-sibling findings → undercount.
  Fix: `_MARKER_RE` keeps list numbers as content. (`test_critique_inherit.py`)
- LIB-1 · CORRECTNESS · MED · `_shared/lib/run_evals.py:245` — `--root` default walked `parents[3]`
  (→ `.claude/`, not repo root) → every scenario FATAL'd. Fix: `parents[4]`.
- LIB-2 · CORRECTNESS · MED · `_shared/lib/llm_eval.py` — 35 `llm_advisory` assertions had no runnable
  path (always SKIP). Fix: golden-fixture judge via injectable LLM client (PASS/FAIL/MISSING/ERROR,
  never fabricates); local-on-demand, not CI. (`test_llm_eval.py`, 16 passed)

### Cycle 1 — 2026-06 (release-skill rename + bundle restructure; condensed)
- PACK-2 · CORRECTNESS · HIGH · `release/scripts/release.py:26` — repo-root resolution: the migration plan
  guessed `parents[3]` (→ `.claude/`), which would make every release read/write the WRONG CHANGELOG +
  manifest. Fix: `parents[4]`, established by running the resolution (not trusting the plan); a unit test
  asserts `REPO/.claude/pack.manifest.yaml` + `REPO/CHANGELOG.md` exist. Bundle-A4 (root CHANGELOG top ==
  manifest) stays RED until the owner-time `release.py --release 2.0.0 --apply`.

### Cycle 2 — 2026-06-09 (learning loop `--learn`; condensed)
- PS-1 · CONSISTENCY · LOW · `assemble_audit_trail.py` — a comment claimed the learning-map "filters" the
  outcome rows; it KEEPS them as source nodes. Fix: reworded (comment-only).
- PS-2 · CLEANUP · LOW · `record_outcome.py`/`render_outcomes.py` — both >200 exec-LOC, each fusing two
  concerns. Fix: extracted `outcome_verdict.py` (verdict core) + `render_learning.py` (callers unbroken). 649 passed.
- PS-3 · CORRECTNESS · LOW · `outcome_verdict.py` `_num` — `inf`/`nan` parsed → junk ratio. Fix: return the
  value only when `math.isfinite`, else `None` → routes to the PO-asserted Hybrid path.
- PS-4 · CLEANUP · LOW · `load_outcomes.py` — a bare `except Exception` around `load_goals` swallowed real
  bugs. Fix: narrow to `except OutcomeError` (the only exception a missing/broken BRD raises).
- PS-5 · CORRECTNESS · MED · `preferences.py` (`--set` float) — a bad float saved + exited 0, failing only
  later in another module. Fix: reject non-numeric / out-of-`[0,1]` at write time, exit 2, nothing written.
- PS-6/8/9 · CLEANUP+CONSISTENCY · LOW · product-spec scripts — removed unused imports; refreshed the stale
  `visualize.py` docstring; corrected comments naming the renamed `outcome_verdict.load_floors`. pyflakes clean.
- PS-7 · DRY · MED · `record_outcome.py` ↔ `decision_register.py` — byte-identical fenced-register machinery
  twinned. Fix: extracted `register_store.py` (`RECORD_RE`, `escape_injection`, `register_lock`,
  `scan_record_ids`); pure de-dup, decision_register retested.
- PS-10 · CORRECTNESS · MINOR · `record_outcome.py` `append_alloc` — `--measured-on` accepted any string; the
  field is an ISO date. Fix: validate via `date.fromisoformat`.
- PS-11 · CLEANUP(test-gap) · LOW · learning views — added a direct `render_learning.learning_map_ascii` test
  + a dispatcher test driving all 5 `--learn` views through `visualize.py`.

### P3-13 · BUILD-NEW · decision-register view · `decision_register_view.py`
- **Root cause:** `decision_register.py` at 401 LOC (over 250-LOC budget); no presentation layer existed for filtering DECs by affected artifact or resolving supersede chains.
- **Before:** `python3 decision_register.py --root . --list --affects PRD-AUTH` → unrecognized argument / no filter; supersede chains not navigable.
- **Fix:** new `decision_register_view.py` sibling (`filter_by_affects`, `render_supersede_chain` with visited-set cycle guard + dangling-ref fail-soft, `render_dashboard_row`, `render_dashboard_summary`); `--list --affects` dispatch wired in 6 LOC into `decision_register.py`; single DEC loader `parse_decisions()` reused (DRY).
- **After:** `python3 decision_register.py --root . --list --affects PRD-AUTH` → `{"affects": "PRD-AUTH", "rows": [...]}` with chain; cyclic / dangling supersede refs render with `[cycle]`/`[missing]` markers, no crash.
- **Note:** DEC-1 recorded. 6 new tests (6/6 pass). Suite 741 passed / 1 pre-existing dogfood-state failure.
