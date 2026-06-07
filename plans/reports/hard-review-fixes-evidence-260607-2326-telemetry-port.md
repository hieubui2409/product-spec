# Hard-review FIXES + evidence — telemetry usage-&-health port

**Date:** 2026-06-07 · **Scope:** uncommitted telemetry port (`cleanmatic:telemetry`, CM-local, NOT bundled).
**Source review:** `from-code-reviewer-to-cook-hard-review-260607-2326-telemetry-port-correctness-dry.md` (code-reviewer, opus).
Verdict there: **MERGE-READY, 0 blocking** — 1 MEDIUM + 5 LOW. This file records what was applied + evidence.

## Findings → action

| ID | Sev | Finding | Decision | Fix (file:line) | Evidence |
|----|-----|---------|----------|-----------------|----------|
| F1 | MED | `telemetry/SKILL.md` `argument-hint` listed `[--en]` among CLI pass-through flags, but CLI has no `--en` → argparse exit 2 if forwarded. `--en` is an LLM narration toggle, not a CLI flag. | **FIX** | `telemetry/SKILL.md:8` — dropped `[--en]` from `argument-hint`. `--en` stays documented as a narration directive (SKILL.md:42); it is correctly absent from the "Pass-through flags" list (45). | `--en` no longer advertised as a CLI flag; LLM won't forward it. CLI still exits 2 on `--en` (expected — it's not a CLI arg). |
| F2 | LOW | `lens_usage_tokens.py` pre-cutoff records skipped wholesale → a Skill span opened just before the window edge under-attributes its in-window tail. | **ACCEPT + document** | `lens_usage_tokens.py:79` — added comment: directional metric, chronological records, small boundary effect, not corrected. | No behavior change; intent now explicit in code. |
| F3 | LOW | `_md_memory` omitted `invalid_frontmatter` (counts toward `issue_count`) + `stale` → a RED driven by invalid frontmatter showed a headline with no detail. | **FIX** | `telemetry_render.py:141-149` — added `_sec("Invalid frontmatter", …)` (issue-bearing) + `_sec("Stale (informational)", …)` (not in issue_count). | `--lens memory --format md` now emits both sections (verified: "Invalid frontmatter: 0", "Stale (informational): 0"). |
| F4 | LOW | `--top` silently ignored in ascii (only `render_md` threads it); undocumented no-op. | **FIX (doc)** | `analyze_telemetry.py:80` — help now reads "limit usage table to top N skills (md format only)". | json returns raw aggregates (no truncation), ascii usage is headline-only → `--top` is genuinely md-only; now stated. |
| F5 | LOW | bash-timer helpers take an unused `session` param (key = sha1(command)). | **ACCEPT (no change)** | — | Documented L2 conscious-accept from round-2 red-team; reviewer said "no change required". Dropping would churn signature + tests for zero behavior gain. |
| F6 | LOW | `telemetry_render.py:14` re-exported `json_output` but nothing imports it from there (CLI imports it from `formatters` directly) → dead re-export. | **FIX** | `telemetry_render.py:14` — import narrowed to `from formatters import markdown_table`. | grep: no module imports `json_output` from `telemetry_render` (NONE). |

## Shipped-boundary re-confirmation (the one risky shipped change)
- Only SHIPPED file touched: `release/scripts/verify_skill_versions.py` (inside the bundled `release` skill). It now adds CM-local `"telemetry"` to `DEFAULT_SKILLS` + skips a missing DEFAULT skill dir.
- Reviewer empirically confirmed: a **present-but-broken** telemetry dir (SKILL.md missing `metadata.version`) still **FAILS exit 1**; only a genuinely-absent dir is `[skip]`-ed → skip never masks a real failure. Leaking the name is documented + deliberate (semver-checked locally, exempt from changelog-pin in `test_version_sync`).

## Test / CLI evidence (post-fix)
- `pytest .claude/skills/_shared .claude/hooks -q` → **155 passed**.
- `pytest .claude/skills/release/scripts/tests -q` → all pass (incl. real tarball build excludes telemetry skill+hooks+sinks).
- `pytest .claude/skills/product-spec -q` → pass (no regression). `pytest .claude/skills/product-spec-critique -q` → pass.
- CLI `--lens all --format ascii` / `--lens memory --format json|md` → exit 0, no traceback.

## Plan coverage
All 8 phases of `plans/260607-1500-telemetry-insights-skill/` confirmed covered by the code-reviewer's per-phase matrix (impl + tests). Documented deviations (bash-timer command-hash key, `verify_skill_versions` bundle-portability skip) confirmed documented in-code + tested — not re-litigated.

## Unresolved questions
- None blocking. F1's only residual: if any future automation literally forwards `--en` to the CLI it would exit 2 — mitigated by removing it from `argument-hint` and keeping it out of the pass-through list.
