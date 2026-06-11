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
