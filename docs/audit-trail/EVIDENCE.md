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

### LIB-5 · CORRECTNESS · HIGH · `telemetry/scripts/lens_workflow_chains.py`
- The declared-chains source lived in two routing docs a context-flow change deleted; the lens read them
  by hardcoded path and silently returned `[]` while a test asserted ≥1 chain → a red test on the default
  branch. Fix: chains moved to an on-demand in-skill `data/skill-chains.yaml` (zero always-on cost),
  `declared_chains()` fail-loud (`FileNotFoundError` missing / `ValueError` malformed) instead of `[]`.
  (`test_declared_chains_loaded_from_data_file` + 3 siblings; 202 passed.)

### LIB-6 · CONSISTENCY · HIGH · `.github/workflows/`
- 26 tracked test files (telemetry/hooks/_shared) had no workflow; `product-spec-ci.yml` omitted
  `_shared/**` though its eval gate runs `_shared/lib/run_evals.py`. Fix: `internal-test-suite.yml` runs
  the exact CONTRIBUTING pytest command + a drift-guard test ties workflow ⇄ CONTRIBUTING targets;
  `_shared/**` added to the path filter. (`test_internal_ci_runs_canonical_suite.py`; 202 passed.)

### LIB-4 · CORRECTNESS · HIGH · `hooks/emit_session_summary.py`
- `first_timestamp()` read only the literal first transcript line (often a ts-less meta line) →
  `duration_s:0` and empty `skills[]`. Fix: `scan_head()` scans the bounded head to the first record WITH
  a `ts` (real duration) + collects early head `Skill` invocations, merged with the tail.
  (`test_duration_nonzero_when_first_record_has_no_timestamp`, `test_scan_head_returns_first_ts_and_early_skills`.)
  Subagent-outcome classification deferred to a real-transcript pass.

### LIB-7 · CORRECTNESS · MED · `hooks/hook_runtime.py` (SCRIPT_RE)
- **Root cause:** the skill-script matcher was a bare substring — `grep/ls/cat` of a script path counted as
  a "script run", and (via the validate-proxy reading those records) a `grep check_*.py` exit 0 inflated the
  validate pass-rate.
- **Before:** `SCRIPT_RE.search("grep -n x .claude/skills/product-spec/scripts/check_consistency.py")` → matched.
- **Fix:** require execution position — the path must sit at a command boundary or after an interpreter
  (`python[3]`/`bash`/`sh`, incl. a venv/abs/`$VAR` dir prefix). `(?:\S*/)?` admits absolute and
  `$CLAUDE_PROJECT_DIR` exec paths without reopening the substring hole (it cannot bridge the space at an
  argument position, so a grep/ls/cat of the path — even an absolute one — stays rejected).
- **After:** grep/ls/cat → no match; direct / `python3 <path>` / venv-python / `cd && python3` / env-prefixed /
  absolute / `$VAR`-prefixed exec → match, group(1) = `<skill>/scripts/<file>`.
  (`test_reference_only_command_is_not_counted_as_run`, `test_direct_and_compound_execution_are_counted`,
  `test_absolute_and_var_prefixed_execution_are_counted`)
- **Note:** the matcher deliberately under-counts the safe direction — an exotic `python3 -W ignore <path>`
  (a flag that takes a space-separated argument) is missed; no documented invocation uses that form, and the
  alternative (a wider flag rule) would mis-eat `python3 -u <path>`.

### LIB-8 · CORRECTNESS · MED · `hooks/track_script_execution.py`
- **Root cause:** the `session` join key was computed but never written to the record, so the workflow and
  health lenses could not join a script run to the other three sinks (all of which record `session`).
- **Fix:** add `"session"` to the emitted record dict.
- **After:** `test_script_record_carries_session_join_key` asserts the record carries the session id.

### carry-in · ROBUSTNESS · MED · `telemetry/scripts/analyze_telemetry.py` (gather_all) + `telemetry_render.py`
- `gather_all` had no isolation — one lens raising (e.g. the workflow lens fail-loud on a recipient missing
  `data/skill-chains.yaml`) crashed the entire `--lens all` overview. Fix: wrap each lens → a VISIBLE
  `{lens, error}` entry (never a silent drop); renderers surface it in md/ascii/mermaid before lens dispatch.
  (`test_overview_isolates_a_failing_lens`, `test_error_entry_surfaced_in_md`/`_ascii`/`_mermaid`.)

### LIB-10 · CONSISTENCY · MED · `CLAUDE.md` + `product-spec/references/workflow-status.md`
- **Root cause:** the always-on routing layer said "three PO-facing skills" with a 3-row table → the
  `telemetry` skill was invisible, so the model never routed to it.
- **Fix:** "three"→"four" + a telemetry routing row + a voice note (CLAUDE.md is not token-measured by the
  footprint guard); added a read-only telemetry pointer to the `--status` reference (an on-demand ref; the
  committed baseline was regenerated for the +107-token ref growth).
- **After:** the footprint regression guard is green; `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec -q` green.

### LIB-12 · CLEANUP(i18n) · LOW · `telemetry/scripts/lens_validate_proxy.py` + `telemetry_render.py`
- **Root cause:** the validate lens baked an English `reason` string into the gathered dict; under
  `--lang vi` that English prose leaked into Vietnamese output (and into the json path).
- **Fix:** the lens emits a language-neutral `reason_code`; the renderer localizes it via
  `_reason_label`/`_REASON_KEYS` (the `val_na_reason` label is defined in both `en` and `vi`).
- **After:** `test_unavailable_emits_language_neutral_reason_code` (asserts `"reason" not in d`) +
  `test_unavailable_reason_localized_no_english_leak_in_vi` (English absent from VI render).

### LIB-13/14 · CONSISTENCY+CLEANUP · LOW · audit/readback docs + test fixtures
- **Fix:** `telemetry-readback.md` gained the crash-audit sink (`.claude/hooks/.logs/hook-crashes.log`) +
  the per-hook config-gate (`product-spec-hooks.json`) sections, each claim verified against `hook_runtime`;
  `README.md` (EN+VI) re-attributed the memory-gap hook to `product-spec` (it had been scoped under
  `product-spec-critique`); test fixtures dropped the stale `claude-pack` id for a neutral `sample-skill`.
- **After:** `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/telemetry .claude/hooks -q` green;
  doc claims cross-checked against `hook_runtime.py` + the product-spec / critique installers.

### LIB-3 · CORRECTNESS · HIGH · `release/.../install.sh.template` + `hooks/memory_gap_hook.py` + `hooks/hook_runtime.py`
- **Root cause:** the installer copied `.claude/hooks/*.py` via generic skip-existing, so an upgrade KEPT a
  pre-config-gate `memory_gap_hook.py` (an old copy that blocks turn-end unconditionally with no
  `hook_enabled` check); the registrar then wired it → exit-2 blocking switched on for a PO who never opted
  in. Separately, the hook had only a single blocking mode, so any future auto-enable would impose blocking.
- **Before:** install over a tree whose `memory_gap_hook.py` lacks a `hook_enabled` call → the old unsafe
  copy survives (generic `[SKIP]`), and once wired it blocks Stop unconditionally.
- **Fix (3 parts):**
  1. **Upgrade safety** — the installer treats the two enforcement hooks as kit code: a copy with no
     `hook_enabled` call is force-replaced with the gated bundle copy + `.bak.<ts>`; a gate-aware copy the PO
     edited is KEPT and flagged `[CONFLICT]` (never blind-overwritten; `FORCE_OVERWRITE=1` takes the bundle).
  2. **Advisory mode** — `memory_gap_mode()` (default `advisory`) gates the block decision: advisory warns on
     stderr at exit 0; `blocking` (opt-in) keeps the exit-2 contract. The shipped config auto-enables the
     hook in advisory mode. A missing key is still DISABLED, and a non-`blocking` mode value falls to the safe
     advisory default — auto-enable can never silently impose blocking.
  3. **product-memory lens** — read-only `lens_product_memory.gather()` narrates `docs/product/.memory`
     health (last-validated age, missing state files, critique-cache size) under `--lens product_memory|all`.
- **After:** `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/release/scripts/tests/test_installer_e2e.py
  .claude/skills/product-spec/scripts/tests/test_memory_gap_hook.py .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q`
  → green incl. `test_upgrade_replaces_pre_config_gate_enforcement_hook`,
  `test_upgrade_preserves_po_edited_gate_aware_hook`, `test_auto_enable_defaults_to_advisory_warn_exit_zero`,
  `test_opted_in_blocking_is_not_downgraded`, `test_memory_gap_mode_defaults_to_advisory_and_honors_blocking`,
  `test_absent_store_is_flagged`. The telemetry SKILL.md grew +41 tokens (new lens row) → footprint baseline regenerated.
- **Note:** advisory is the new shipped default but the runtime "missing enforcement key ⇒ disabled" invariant
  is unchanged; blocking remains opt-in (`memory_gap_mode: "blocking"`). Recorded in the config `_README` +
  `telemetry-readback.md` (no kit-level DEC-<n> registry exists; product `decisions.md` is for PO rulings).

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
