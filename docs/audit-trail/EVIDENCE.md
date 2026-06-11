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

### Cycle 3 · P01–P03 landed (condensed; full before/after rolled off per the size cap)
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

### PS-14 · CORRECTNESS · HIGH · `product-spec/scripts/spec_graph.py` + `parse_critique_report.py`
- **Root cause:** the critique provenance/freshness fingerprint hashed only body bytes; an AC-only edit (AC
  lives in frontmatter) — or any BRD-goal edit, which had no node in the map at all — left it unchanged →
  the next critique reused a STALE fast-path result for an artifact the PO had changed.
- **Before:** edit only a story's `acceptance_criteria`, rebuild the graph → its provenance fingerprint is unchanged.
- **Fix:** a SEPARATE per-node `content_hash = sha256(body + canonical(acceptance_criteria))[:8]` (goals hash
  title/status/metrics/owner), used ONLY by provenance + apply-freshness; `body_hash` stays body-only so the
  wide judgment/drift/memory caches never churn. Every artifact + goal now has a node; `CHANGED_FIELDS` gained it.
- **After:** `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec -q` → green incl
  `test_ac_only_edit_changes_content_hash_only`, `test_every_node_carries_content_hash`,
  `test_goal_content_edit_changes_goal_content_hash`, `test_changed_fields_includes_content_hash`.
- **Note:** the frontmatter keeps wire-name `body_hash` (back-compat) now holding the content fingerprint → a one-time cache rebuild on the first post-upgrade run is expected, not a regression.

### PSC-2 · CORRECTNESS · HIGH · `product-spec-critique/scripts/critique_signals.py` + `critique_bundle.py`
- **Root cause:** `source_files` packed the WHOLE corpus into the bundle regardless of `--scope`, so a
  single-target critique shipped every off-target artifact to all four lenses in parallel.
- **Before:** a scoped bundle and a `--scope all` bundle pulled the SAME source set.
- **Fix:** `_source_files(include_ids)` filters to `target_ids ∪ ancestry ∪ digest ∪ BRD`; `_source_include_ids`
  computes it (None = whole corpus, only for scope=all).
- **After:** `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec-critique -q` → green incl
  `test_source_files_scoped_to_target_and_ancestry` (an off-target goal ABSENT from a scoped bundle) +
  `test_source_files_all_scope_keeps_whole_corpus`.
- **Note:** the "scope=all descendants → verbosity:struct" sub-optimization is deliberately deferred (YAGNI):
  all-scope critique legitimately needs every source, and struct risks under-informing the lenses.

### PSC-3 · CORRECTNESS · HIGH · `product-spec-critique/scripts/critique_persist.py` (new) + `parse_critique_report.py`
- **Root cause:** the lens-cache / findings-index / critique-state were three separate writes the consolidator
  had to remember; skipping one (usually the lens-cache) made the next apply-critique parse `findings: 0` and
  the state stick on an earlier pass.
- **Before:** a report written without the lens-cache step → apply-critique yields `findings: 0`.
- **Fix:** one `critique_scan.py --persist --input <envelope>` writes all three together; `parse_critique_report`
  gained a prose-fallback recovering `**[severity][lens] id:line**` markers when the cache is absent; `--doctor`
  reconciles critique-state vs the critique/ dir + lens-cache.
- **After:** the two product-spec trees run PER-TREE → green incl `test_persist_writes_lens_cache_index_and_state`,
  `test_prose_fallback_recovers_findings_when_cache_absent`,
  `test_prose_fallback_two_markers_on_one_line_keep_distinct_critiques`, `test_doctor_flags_missing_lens_cache_and_report`.
- **Note:** the persist envelope degrades to a clean `bad_input` record (never a crash; a non-int `level` is caught, not leaked).

### PS-13 · CORRECTNESS · HIGH · `product-spec/scripts/check_consistency_schema.py` + `migrate_metric_to_metrics.py` (new)
- **Root cause:** a BRD authored by an older skill carries the singular `metric:` goal key; the missing-metric
  check fired an ERROR per goal → `strict_gate` exit 2 blocked an approved artifact, and no migrator moved the
  value `metric:`→`metrics:` (an approved file the placeholder-only migrator must never touch).
- **Before:** `check_consistency.py` on a legacy `metric:` BRD → `goal_without_metric` ERROR ×N, exit 2.
- **Fix:** a goal with no plural `metrics:` but an intrinsic singular `metric:` key emits `legacy_metric_key`
  WARN (names the key, never blocks); a SEPARATE GATE-safe `migrate_metric_to_metrics.py` does the rename —
  dry-run writes 0 bytes, `--apply` demands BOTH `--confirmed-by` AND `--date` (the approved-artifact
  re-approval), wraps a scalar into a list, stamps `schema_version: 2`, backs up `.bak`. A truly metric-LESS
  goal still ERRORs (the gate is not loosened).
- **After:** `.../python3 -m pytest .claude/skills/product-spec -q` → 678 green incl
  `test_singular_metric_key_warns_not_errors_on_legacy`, `test_draft_missing_metric_still_errors`,
  `test_migrate_dry_run_writes_zero_bytes`, `test_migrate_apply_requires_confirmed_by_and_date`.
- **Note:** the migrator rename is scoped per goal entry — an entry already on plural `metrics:` is skipped
  (no duplicate key) and a trailing inline comment on a scalar `metric:` is preserved (stays valid YAML):
  `test_migrate_skips_goal_already_on_plural_metrics`, `test_migrate_preserves_inline_comment_on_scalar_metric`.

### PS-17 · CORRECTNESS · MED · `product-spec/scripts/check_consistency_schema.py` + `spec_graph.py`
- **Root cause:** a goal missing the spec-required `status` was caught by no check, and a goal's `moscow` was
  silently dropped from the graph node.
- **Before:** a goal with no `status:` passed `check_consistency.py` clean; `moscow` absent from the node.
- **Fix:** `goal_without_status` keyed on the BRD `schema_version` marker — WARN when the artifact predates the
  marker (legacy lenience), ERROR at `schema_version >= 2` (a migrated/fresh spec must comply); `moscow` +
  `unknown_goal_keys` now ride the goal node (an unknown key → `unknown_goal_key` WARN).
- **After:** green incl `test_goal_without_status_warns_on_legacy_errors_on_schema_v2`, `test_moscow_preserved_in_graph_node`.
- **Note:** `moscow` is deliberately NOT folded into the provenance `content_hash` (it would re-churn the prior
  wave's caches); it rides `CHANGED_FIELDS` instead.

### PS-18 · CONSISTENCY · MED · `product-spec/scripts/check_consistency_schema.py` + `spec_graph.py`
- **Root cause:** an LLM-authored artifact could carry parent-only fields (a story holding `prd`/`brd_goals`,
  whose parent is an epic) and a non-semver `version`, and the validator stayed silent.
- **Before:** a story with `prd:`/`brd_goals:` and `version: "0.3"` validated clean.
- **Fix:** `misplaced_parent_field` WARN (a story carrying `prd`/non-empty `brd_goals`) + `bad_version_format`
  WARN (a `version` not matching semver-lite `MAJOR.MINOR.PATCH`); `parse_semver` consolidated to a single
  home in `spec_graph.py` (consumed by both the parent/child compare and this lint).
- **After:** green incl `test_misplaced_parent_field_and_bad_version_flagged`.
- **Note (deferred, by design):** a generic per-type frontmatter whitelist + a derived-`title`-in-frontmatter
  flag are NOT shipped — both would false-positive on legit `created`/`updated`/`version`; scope is held to the
  two node-derivable signals. Recorded here (no kit-level DEC registry; `decisions.md` is for PO rulings).

### PS-21 · CONSISTENCY · MED · `product-spec/SKILL.md` + `references/frontmatter-and-id-spec.md`
- **Root cause:** `migrate_multidim_fields.py` was orphaned from all routing (0 SKILL.md/reference hits) → a v1
  spec hitting post-upgrade warn-noise had no signposted path to migration.
- **Fix:** a trimmed "schema migration" callout in SKILL.md routes BOTH migrators (empty-shape vs the
  value-moving `metric→metrics`); the frontmatter reference gained `schema_version`, the `moscow` goal field,
  and a version-format warn note. (SKILL.md + ref grew → footprint baseline regenerated in the same change.)
- **After:** `grep -c migrate_metric_to_metrics product-spec/SKILL.md` ≥ 1; the footprint regression guard is green.

### PS-23 · CORRECTNESS · LOW · `product-spec/scripts/encoding_utils.py` + `check_consistency.py` + `spec_graph.py`
- **Root cause:** piping a large JSON emitter into `head` closed the pipe early → a `BrokenPipeError` traceback
  + exit 1, violating the "analytical script always exits 0" contract.
- **Before:** `check_consistency.py ... | head -c 16` → traceback, returncode 1.
- **Fix:** a single-home `emit_json()` helper writes/flushes and swallows `BrokenPipeError` (redirecting the fd
  to devnull), wired into both script mains.
- **After:** `test_check_consistency_survives_broken_pipe` (400 stories piped to `head -c 16`) → returncode 0, no traceback.

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
