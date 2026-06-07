# Hard Review — Telemetry "Usage & Health" Port (uncommitted)

Reviewer: code-reviewer · Date: 2026-06-07 23:29 · Scope: uncommitted telemetry feature
Surface: 11 new lib modules + 1 CLI + 2 new hooks + 4 modified hooks/scripts + new `telemetry` skill + tests + gitignore/docs.

## Verdict

**MERGE-READY. Blocking issues: 0.** All 155 tests pass; CLI runs clean (ascii+json, exit 0); all 4 hooks fail-open on garbage/empty stdin; bundle-exclusion + version-sync tests green; the critical shipped-file scrutiny (`verify_skill_versions.py`) is empirically safe. Findings below are 1 MEDIUM (doc/flag consistency) + several LOW (cosmetic / directional-metric). None block.

The single most important verification — does the new skip-missing logic in the SHIPPED `verify_skill_versions.py` mask a real failure? — **NO**. Confirmed empirically: a present-but-broken telemetry dir (SKILL.md without `metadata.version`) still FAILS exit 1; only a genuinely-absent dir is skipped (exit 0). Leaking the CM-local name `telemetry` into `DEFAULT_SKILLS` is consistent and documented (semver-checked, exempt from changelog-pin via `VERSION_SYNCED_SKILLS`).

## Findings

| ID | Sev | file:line | Finding | Recommended fix |
|----|-----|-----------|---------|-----------------|
| F1 | MEDIUM | `.claude/skills/telemetry/SKILL.md:8` | `argument-hint` advertises `[--en]` mixed with genuine CLI pass-through flags (`--days N`, `--top N`), but `analyze_telemetry.py` has NO `--en` arg → passing it to the CLI is a hard argparse error (exit 2: `unrecognized arguments: --en`). `--en` is an LLM-narration toggle (line 42), correctly absent from the "Pass-through flags" list (line 45), but `argument-hint` conflates the two. Real failure mode: an agent reads the hint, appends `--en` to the bash invocation, CLI aborts. | Move `--en` out of `argument-hint`'s CLI-flag cluster, or annotate it as narration-only, e.g. `… [--top N]` and separately `(say "in English" / --en to narrate in EN)`. One-line doc edit. |
| F2 | LOW | `lens_usage_tokens.py:78-90` | Token attribution: a pre-cutoff `Skill` tool_use record is `continue`-skipped, so `current` is not advanced to that skill; subsequent in-window usage stays attributed to the prior in-window skill or `None`. Under-attributes a span that opened just before the window edge. Directional metric (docstring says so), records are chronological so the skipped region is the file head only → small, realistic effect. | Accept as documented directional behavior, OR resolve `current` from a Skill open even when its ts < cutoff (don't `continue` before scanning for a Skill block). Not blocking. |
| F3 | LOW | `telemetry_render.py:129-142` | `_md_memory` renders orphans/dead/broken/duplicates but omits `stale` and `invalid_frontmatter`, which `lens_memory_health.gather()` does populate and which DO count toward `issue_count`/status. A RED memory status driven purely by stale/invalid items shows the headline count but no detail section in md. | Add `_sec("Stale", …)` and `_sec("Invalid frontmatter", …)` to `_md_memory`, or document the omission as intentional (ascii already only shows headline). |
| F4 | LOW | `telemetry_render.py:200-247` (`render_ascii`) | `--top` is silently ignored in ascii format (only `render_md` threads `top`). `--top 1` on `--format ascii` shows the full headline regardless. Harmless (ascii is headline-only) but the flag's no-op is undocumented. | Either honor `top` in the ascii usage row table (none rendered today, so likely no-op is fine) or note in SKILL.md that `--top` affects md/json only. |
| F5 | LOW | `telemetry_paths.py:159` (`_bash_timer_path`) | `session` param accepted but unused (key = sha1(command) only). This is the DOCUMENTED L2 accept (back-to-back identical concurrent commands collide → at worst a dropped `ms`, never a misattribution since key is command-scoped and `read_and_clear` unlinks on read). Kept in signature "for call-site clarity." Confirmed not a correctness bug; flagging only so it isn't mistaken for a live param. | No change required (conscious accept, prior-report L2). Optionally drop the unused `session` param to silence the dead-arg smell. |
| F6 | LOW | `telemetry_render.py:14` | `from formatters import markdown_table, json_output  # noqa: F401 (json_output re-exported)` — `json_output` imported only to re-export; the CLI imports `json_output` directly from `formatters` (analyze_telemetry.py:26), so the re-export is unused. | Drop `json_output` from this import (keep `markdown_table`), or keep if a documented public re-export of the render module. Cosmetic. |

## DRY / Cleanup audit (clean)

- `sessions_dir()` / `memory_dir()` / `TELEMETRY` / `project_dir()` / `low_volume_gate` centralized in `telemetry_paths.py`. `emit_session_summary.py` correctly dropped its private `_sessions_dir()` and now calls the shared `sessions_dir()` (diff verified) — DRY win, no duplicate path logic left in hooks/lenses.
- `formatters.py` is the verbatim HA port; no divergence, no dead code beyond the standard `print_*`/`eprint`/`summary_block`/`severity_badge` helpers (these are part of the ported public surface, harmless).
- `SCRIPT_RE` is intentionally duplicated between `mark_bash_start.py:31` and `track_script_execution.py` with an explicit comment justifying the no-cross-import between two fail-open hooks — acceptable KISS tradeoff, not a DRY violation.
- `telemetry_render.py` is 13KB / 305 LOC > the 200-LOC guideline, but it is 8 small per-lens renderers + 3 format dispatchers with near-zero branching depth; splitting would scatter the render contract. Borderline; not flagged as a fix.
- No leftover debug prints, no TODO/FIXME, no `any`-widening (Python), no lint suppressions beyond justified `# noqa: E402` (sys.path insert before import) and the F1-flagged F401.

## Consistency audit (clean)

- Fail-open + pytest-silent contract holds across ALL new/modified hooks: `mark_bash_start`, `track_subagent_outcome`, `track_script_execution`, `emit_session_summary` each emit `{"continue": true}` and never raise (verified by garbage + empty stdin injection, exit 0 every time). `disabled()` gates on `PYTEST_CURRENT_TEST` and `CK_TELEMETRY_DISABLED`.
- `CK_*_DIR` override pattern uniform: `CK_TELEMETRY_DIR`, `CK_SESSIONS_DIR`, `CK_MEMORY_DIR`, `CK_SKILLS_DIR` all env-checked-first in their resolvers.
- Lens `gather()` all return a dict with a `lens` key; render dispatch keys match (`_MD` map + ascii/mermaid branches). No shape drift.
- Outcome enum (`track_subagent_outcome.py:38,127-134`): explicit-field path validated against `OUTCOMES`, transcript fallback never returns `success` unless a clean `end_turn`/`stop_sequence` with no pending tool_use; default `unknown`. Never fabricates success — meets Phase-2 criterion.
- `validate_pass_rate` is `None` (not `0`) when `runs==0` (`lens_validate_proxy.py:90`), rendered as "n/a (no validate runs in window)" — correct None-vs-0 distinction.
- `low_volume_gate(==threshold)` returns False (not gated); confirmed by `test_low_volume_gate.py` + `test_gate_not_triggered_at_five_invocations`.
- Memory frontmatter parser reads nested `metadata.type` (`lens_memory_health.py:87`) AND top-level `type`, falling back correctly.

## Plan coverage matrix

| Phase | Acceptance criteria | Covered? | Evidence |
|-------|---------------------|----------|----------|
| 01 Foundations | formatters ported + VI width; sessions_dir/memory_dir/TELEMETRY env-overridable; emit_session uses shared resolver; fixtures w/ asserted counts | YES | `formatters.py` _disp_width NFC+EAW; `telemetry_paths.py:62-80,46-50`; emit_session diff drops `_sessions_dir`; `test_telemetry_paths_helpers.py`, fixtures present |
| 02 New sinks | subagent-outcomes enum correct + malformed fail-open; `ms` on Pre/Post pair, degrades; hooks pytest-silent + {"continue":true}; register idempotent; no shipped import | YES | `track_subagent_outcome.py`; `test_bash_duration_pairing.py` (pair→ms, missing-pre→no-ms, different-cmd no-pair); fault-injection exit 0; `register_telemetry_hooks.py` diff; `test_no_shipped_script_imports_a_telemetry_module` |
| 03 Core lenses | usage+tokens parity, flat slugs, never-used, gate; session-shape+health; ms degrades; pure/no-raise | YES | `test_lens_usage_tokens.py` (slug collapse=3, tokens 450/150, gate@5); `lens_session_shape.py`, `lens_health.py` (avg_ms None when no pair) |
| 04 Extended lenses | 4 lenses correct on fixtures; memory read-only even w/ --fix; reliability+workflow gated; forensics reconstructs; no-raise | YES | `lens_forensics/memory_health/workflow_chains/reliability.py`; `memory_health` has no write path (`fix_preview` dry-run only, `read_only:True`); per-lens tests present |
| 05 Renderers | ascii+mermaid+md+json deterministic both gate states; mermaid escaped, no network/JS/asset; --overview ordered; no re-vendor/product-spec import | YES | `telemetry_render.py` `_mermaid_escape`; CLI ascii+json ran clean; `OVERVIEW_ORDER`; `test_telemetry_render.py` |
| 06 Validate proxy | source from real evidence; pass_rate+last status; below-gate suppressed; labels internal-quality NOT E3; honest degrade no fabrication | YES | `lens_validate_proxy.py` decision tree (marker→runs→available:False); `not_e3:True`; pass_rate None-not-0; `test_lens_validate_proxy.py` |
| 07 Telemetry skill | valid frontmatter+semver; MEASURED vs NOT-MEASURED narration; thin-data "chưa đủ dữ liệu"; zero edits; name /cleanmatic:telemetry | YES (1 doc nit F1) | SKILL.md frontmatter v1.0.0 semver-OK; `narration-contract.md`; `_GATE_NOTE` "chưa đủ dữ liệu"; name `cleanmatic:telemetry` |
| 08 Packaging guards | skill+2 hooks+sinks git-tracked yet absent from tarball; DEFAULT_SKILLS incl telemetry, VERSION_SYNCED excl; no-shipped-import grep; CI gates green; readback+BACKLOG; 2nd red-team applied | YES | `test_bundle_excludes_telemetry.py` (4 tests pass, real-tarball + by-construction + exempt + no-import); `verify_skill_versions.py` exit 0; gitignore re-include verified (`git add -n` succeeds, check-ignore shows negation); readback+BACKLOG diffs present |

Documented deviations (NOT re-litigated, confirmed documented): bash-timer command-hash key (`telemetry_paths.py:143-155` comment + prior L2); `verify_skill_versions` bundle-portability skip (`:107-111` comment + `test_telemetry_exempt_from_version_sync_assertion`).

## Test / CLI run evidence

- `pytest .claude/skills/_shared .claude/hooks -q` → **155 passed in 0.22s**.
- `analyze_telemetry.py --lens all --format ascii` → exit 0, all 8 lenses render, no traceback.
- `analyze_telemetry.py --lens all --format json` → exit 0, valid JSON array.
- Fault injection (garbage `not json{{{` + empty stdin) on all 4 new/modified hooks → each prints `{"continue": true}`, exit 0.
- `test_bundle_excludes_telemetry.py` → **4 passed** (incl. real `python -m pack` build, non-empty assert, no telemetry member).
- `test_version_sync.py` → **9 passed**.
- `verify_skill_versions.py` (local, 4 dirs present) → exit 0, all OK.
- Synthesized broken telemetry SKILL.md (no metadata.version, dir present) → **exit 1 FAIL** (skip-missing does NOT mask broken-present). Removed dir → exit 0 `[skip]`.

## Unresolved questions

1. F1: is `--en` ever programmatically forwarded to the CLI by the skill's run instructions, or is it purely a natural-language narration directive the LLM consumes? If the latter (likely, per SKILL.md:42/45), F1 is a pure doc-hygiene fix; if any automation passes it through, F1 is a real exit-2 break. Recommend the one-line `argument-hint` clarification regardless.
