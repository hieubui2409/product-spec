# Dual-Skill Hardcore Review — Cycle 1/10

Date: 2026-05-29 · Targets: `cleanmatic:product-spec` + `cleanmatic:claude-pack` · Mode: whole-skill, max-recall, converge-to-stop, auto-fix-safe/ask-on-risky.

Baseline (pre-cycle): claude-pack 61 pass · product-spec 76 pass.
Post-cycle: **claude-pack 73 pass · product-spec 88 pass** · +1 .gitignore fix · 2 CRITICALs independently probed.

## Locked decisions (interview)
1. safety_check matching → **case-insensitive (all layers)**.
2. `follow_shared` → **implement auto-include** (`_shared/<ref>` bundled when true).
3. installer version compare → **full SemVer 2.0** identical in sh + ps1.
4. recipient per-skill hooks → **opt-in** (`RUN_HOOKS=1` / `-RunHooks`) + INSTALL.md review warning.

## Findings (31 = 30 finder + 1 verification-gate). All addressed.

### CRITICAL
- SAFETY-1 secret leak: `is_dropped()` case-sensitive → `deploy.PEM`/`.ENV`/`ID_RSA`/`.GIT/` slipped on case-insensitive FS (and `.PEM` on Linux). FIXED (lowercased all 3 layers) + probed.
- VIZ-1 stored XSS: `gap`/`roadmap`/`delta` mermaid views interpolated raw ids/labels (no `_safe_label`). FIXED (routed through `_safe_label`).
- VIZ-2 stored XSS: `_render_view_body` mermaid branch unescaped + `_safe_label` missed `&` (entity-encoded bypass). FIXED (HTML-escape DSL body; `&`→`&amp;` first; mermaid reads textContent so syntax preserved) + probed.
- GIT-1 packaging: `.gitignore:105 assets/` ignored **claude-pack/assets/** (3 installer templates + manifest.example) → committed skill non-functional on fresh clone; product-spec had an exception, claude-pack did not. FIXED (added claude-pack assets exception). **Finders missed it (content-only review).**

### HIGH
- VIZ-3: `_safe_id` only mapped `-`/`:`, leaked `<>"]` into mermaid identifier. FIXED (whitelist `[A-Za-z0-9_]`).
- CORE-1: `follow_shared` dead (validated, ignored) — docs promised auto-include. FIXED (cli populates `_include_shared`; --strict passes).
- CORE-2: `MANIFEST.json`/counts followed symlinks the tarball drops → leaked external-secret size+sha256, broke recipient verify. FIXED (skip symlinks in build_manifest_json + filter_findings).
- SAFETY-2: INSTALL.md hardcoded `sha256sum` (absent on macOS) → Mac users skip integrity check. FIXED (document `sha256sum` + `shasum -a 256`).
- SAFETY-3: installer NEWER-guard only on SKILL.md → other files overwritten older under FORCE = split-brain skill. FIXED (per-skill-dir verdict applied to all files).
- GRAPH-1: bare-string `brd_goals` iterated per-char → phantom dangling_link in check_traceability + matrix (only check_consistency guarded). FIXED (replicated isinstance(list) guard).
- DOCS-1: SKILL.md said `python -m pack --discover` (no such flag) → broken no-flag entry. FIXED (`python -m build_manifest --discover`).
- DOCS-2: `eval/fixtures/dirty-claude/` referenced but `.env*` gitignored → uncommittable/missing → eval un-runnable. FIXED (scenario generates dirty tree at runtime).

### MEDIUM
- CORE-3 `--max-size 0` falsy-ignored → explicit None check. CORE-4 `defaults.max_size_bytes` unvalidated (string→TypeError crash) → type-check E042/E043. GRAPH-2 PRD slug `AUTH-E1` collides with epic grammar → reject. GRAPH-3 malformed `{{my-key}}` token shipped raw → raise on residual. DOCS-3 flag-reference listed unsupported `defaults.source_date_epoch` → "(CLI only)". SAFETY-4 sh `sort -V` ≠ ps1 `[version]` → unified SemVer 2.0. SAFETY-5 recipient hooks auto-ran → opt-in + warning. All FIXED.

### LOW (all fixed)
CORE-5 force+replace-fail lost output (restore backup). CORE-6 `a:b` falsely rejected as drive. SAFETY-6 installer `find|sort` locale → `LC_ALL=C`; STALE+FORCE double-count. SAFETY-7 fixed tmp name → PID+rand suffix. SAFETY-8 atomic_replace exists() followed symlink → is_symlink() or exists(). GRAPH-4 snapshot same-second overwrite → content-hash suffix. GRAPH-5 nested OPTIONAL leak → post-strip. GRAPH-6 extract_sections docstring vs behavior → corrected. VIZ-5 footer_note raw → invariant comment. VIZ-4 subsumed by VIZ-2.

## Verification
- Full suites re-run with ALL changes present: claude-pack 73/73, product-spec 88/88.
- C+D parallel collision on `test_visualize.py::test_w3_l5` reconciled — XSS tests + snapshot-hash fix coexist (59 tests in file).
- Independent probes: secret case-insensitive drop ✓; `_safe_label`/`_safe_id` markup-clean ✓.
- `.gitignore` fix verified: `claude-pack/assets/` now `??` (trackable), only cache/dist ignored.

## Carry-forward to Cycle 2 (gaps + risk areas)
- **Add packaging/distribution-completeness angle** (finders missed GIT-1): any other needed-but-untracked files? actually build a real tarball and inspect contents + run install.sh end-to-end.
- **Scrutinize new installer logic** (highest risk, NOT pytest-covered): bash `semver_compare` + PowerShell `Compare-Semver` correctness across edge cases; per-skill verdict loop; `RUN_HOOKS` opt-in; sh/ps1 parity.
- **Regression sweep** on Cycle-1 code changes: follow_shared inclusion path, symlink skip, atomic_replace restore path, snapshot filename change.
- Re-check product-spec viz: other injection sinks? did escaping change any deterministic output?

## Unresolved questions
None blocking. Cycle 1 converged on fixes; proceeding to Cycle 2.
