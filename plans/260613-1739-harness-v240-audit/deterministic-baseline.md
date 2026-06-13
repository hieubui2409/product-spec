# Deterministic Baseline — independent grep cross-check (controller-run)

Scoped strictly to the 4 bundle skills. Use to validate/supplement agent findings during consolidation.

## CONFIRMED (controller-verified)

### BASE-1 [high] Telemetry lens family has no injectable clock → time-coupled, boundary untested
- **Files (9 sites):** `telemetry/scripts/lens_reliability.py:31`, `lens_artifact_heat.py:46`,
  `lens_usage_tokens.py:38,65`, `lens_validate_proxy.py:57`, `lens_memory_health.py:68`,
  `lens_product_memory.py:37`, `lens_workflow_chains.py:50`, `harvester.py:58`.
- All compute `cutoff = datetime.now(timezone.utc) - timedelta(days=days)`; `gather()` signatures
  (`def gather(days=30, ...)`) accept **no** `now`/`today` injection.
- Contrast: product-spec injects a clock everywhere (`time_advisory.py:76`, `time_realism_anchors.py:108`
  `args.today or date.today()`; `status.build_status(..., today=)`; `record_outcome` `--measured-on`),
  and `release/upgrade_apply.py:127` even comments *"NEVER call datetime.now() here — caller injects for determinism."*
- **Consequence:** the days-window boundary is untestable deterministically. Other lens tests dodge it with
  `gather(days=BIG_DAYS)` (so boundary logic is effectively **uncovered**); `test_lens_artifact_heat`'s
  `test_heat_lens_respects_days_window` is the lone boundary test and it pins `2026-06-12` against real
  `now()` → **currently FAILS on 2026-06-13** and will keep rotting.
- **Fix:** add `now: datetime | None = None` to each `gather()` (default `datetime.now(timezone.utc)`),
  thread into the cutoff; tests inject a fixed `now`. Matches product-spec's existing pattern (DRY).

### BASE-2 [confirmed FAILING test] test_lens_artifact_heat::test_heat_lens_respects_days_window
- One concrete instance of BASE-1. `assert 'docs/product/NEW.md' in []` once wall-clock > event+days.

## CHECKED → NOT a defect (don't let agents over-report these)
- `release/build_manifest_writer.py:94` `except Exception:` → does `tmp.unlink(missing_ok=True); raise`
  (atomic-write cleanup + **re-raise**). Correct. NOT swallowed.
- In-scope broad `except` in `assemble_audit_trail.py:149`, `snapshot.py:247/253`, `telemetry_paths.py:120/190/213/239`
  are all **deliberate fail-open/fail-soft** with rationale comments. Judge case-by-case but default = intended.
- `render_html_tooltip.py:130` `r.exec(txt)` = JavaScript regex inside an HTML template string, NOT Python exec.
- No mutable-default args in scope. `subprocess` uses are list-form, no `shell=True`, fail-soft on git.
- Most telemetry lens tests use `days=BIG` to avoid date rot (defensive) — only artifact_heat tests the boundary.

## Out-of-scope (other skills in .claude/skills, NOT the product-spec bundle)
- `ai-multimodal/.../media_optimizer.py:107 eval(...)`, `cti-expert/...shell=True`, `_shared/lib/run_evals.py`
  `skill-creator`, `document-skills` — ignore; not part of the 4 audited skills.
