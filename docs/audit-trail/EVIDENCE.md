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
- **Root cause:** the declared-chains source lived in two `.claude/rules/*.md` routing docs that a
  context-flow optimization deleted; the lens read them by hardcoded path and silently returned `[]`
  when they vanished, while a test asserted ≥1 chain → a red test on the default branch.
- **Before:** `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/telemetry -q -k declared_chains`
  → `test_declared_chains_parsed_from_routing_docs FAILED` (`assert 0 >= 1`).
- **Fix:** moved declared chains into an on-demand, in-skill `data/skill-chains.yaml` (read only when the
  lens runs → zero always-on token cost); `declared_chains()` reads it and raises `FileNotFoundError`
  when missing — and `ValueError` on malformed data (non-list `chains`, a string/scalar entry, a null
  step) — instead of silently returning `[]` or char-splitting a string into a fake chain. The SKILL.md
  source-cell label grew +2 tokens; the committed footprint baseline was regenerated in the same change.
- **After:** `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q`
  → `202 passed` (was `1 failed`); new tests `test_declared_chains_loaded_from_data_file`,
  `test_declared_chains_raises_when_data_file_missing`, `..._null_key_is_empty_not_crash`,
  `..._raises_on_malformed_data` all green.
- **Note:** the `data/` dir ships with the skill via the recursive `skills:` walk — no manifest edit.

### LIB-6 · CONSISTENCY · HIGH · `.github/workflows/`
- **Root cause:** 26 tracked test files (telemetry 18, hooks 4, _shared 4) had no workflow;
  `product-spec-ci.yml` path filter omitted `_shared/**` though its eval gate runs
  `_shared/lib/run_evals.py`; CONTRIBUTING's "all tests must pass" was unenforced — LIB-5 was exhibit A.
- **Before:** `grep -l telemetry .github/workflows/*.yml` → no workflow ran the telemetry/hooks/_shared suite.
- **Fix:** added `.github/workflows/internal-test-suite.yml` running the exact CONTRIBUTING.md command on
  telemetry+hooks+_shared; added `_shared/**` to `product-spec-ci.yml` paths; added a guard test asserting
  the workflow and CONTRIBUTING document the same canonical pytest targets.
- **After:** the `_shared` leg of the suite now includes `test_internal_ci_runs_canonical_suite.py`
  (3 tests) → `202 passed`, `0 failed`.
- **Note:** drift guard is a path-presence + co-presence check (workflow ⇄ CONTRIBUTING share the same
  pytest targets); it intentionally does not lock the interpreter, since CI runs system `python` while
  CONTRIBUTING documents the venv path.

### LIB-4 · CORRECTNESS · HIGH · `hooks/emit_session_summary.py`
- **Root cause:** `first_timestamp()` read only the literal first transcript line; that record is often a
  meta line with no `ts`, so duration computed as 0; early `Skill` invocations clustered in the head were
  missed by the recent-activity tail → empty `skills[]`.
- **Before:** on a real transcript whose first record has no `ts`, `sessions.jsonl` got `duration_s:0` and `skills:[]`.
- **Fix:** `scan_head()` scans the bounded head to the first record that HAS a `ts` (→ real duration) and
  collects head `Skill` invocations, merged with the tail (dedup, order-preserving).
- **After:** `.claude/skills/.venv/bin/python3 -m pytest .claude/hooks -q` → green incl
  `test_duration_nonzero_when_first_record_has_no_timestamp`, `test_scan_head_returns_first_ts_and_early_skills`.

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
- **Root cause:** `gather_all` was a list-comprehension with no isolation — one lens raising (e.g. the
  workflow lens fail-loud when `data/skill-chains.yaml` is absent on a recipient) crashed the entire
  `--lens all` overview (all seven lenses dark).
- **Fix:** wrap each lens → a VISIBLE `{lens, error}` entry (never a silent drop); the per-lens `gather()`
  still raises at the function level (loud for unit tests). The renderers surface the error in md, ascii AND
  mermaid — the `error` check precedes lens-name dispatch, so a registry-name vs lens-name mismatch can't
  swallow it.
- **After:** `test_overview_isolates_a_failing_lens` (six lenses survive + a visible error entry),
  `test_error_entry_surfaced_in_md` / `_ascii` / `_mermaid`.

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
