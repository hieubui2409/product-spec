# Dual-Skill Hardcore Review — Cycle 2/10 (progress snapshot pre-compact)

Date: 2026-05-29 · Targets: `cleanmatic:product-spec` + `cleanmatic:claude-pack` · Mode: whole-skill, max-recall, converge-to-stop, auto-fix-safe/ask-on-risky.

## Report paths (keep)
- Cycle 1: `.claude/skills/claude-pack/plans/reports/cycle-01-dual-skill-review-260529-0940-findings-and-fixes-report.md`
- Cycle 2: `plans/reports/cycle-02-dual-skill-review-260529-findings-fixes-and-pending-report.md` (this file)

## Test state
- Baseline (start of project): claude-pack 61 · product-spec 76.
- After Cycle 1: claude-pack 73 · product-spec 88.
- After Cycle 2 (current): **claude-pack 77 pass · product-spec 92 pass** (all green).
  (product-spec 89→92: +3 tests for the F3 'other' column and F4 grid-alignment fixes below.)

## Cycle-2 decisions (interview, locked)
1. Top-level `.claude/scripts` + `.claude/schemas` → **opt-in** (flip global default to False; they are CK-framework internals, not skill content). Reverses the earlier "default-ship" locked decision on NEW evidence.
2. Commit ALL CK files (`.claude/{agents,scripts,schemas}`) — `.gitignore` re-includes them — BUT remove `agents:` from the seed manifest.
3. Bundle hygiene: drop only `plans/` (keep eval/ + tests/).
4. F6 follow_shared granularity: **keep dir-granular** + document (not file-granular). User-confirmed.
5. (Cycle-1 carryover) case-insensitive safety, follow_shared auto-include, full SemVer-2.0 installer, opt-in recipient hooks.

## Cycle-2 findings (23) + status

### Regressions introduced by Cycle-1 fixes (all FIXED)
- 2A-F1 (HIGH): `defaults.max_size_bytes: false` passed E042 (bool ⊂ int) → bricked every build. FIXED (reject bool explicitly) + test.
- 2D-F1 (HIGH): mermaid HTML double-escaped `&` (`_safe_label` + `_render_view_body` both) → "R&D"→"R&amp;D". FIXED (HTML layer escapes only `<`/`>`, never `&`) + composition test.
- 2D-F2 (MED test-gap): no `&` composition test. FIXED (added `test_mermaid_html_single_encodes_ampersand`).

### Packaging (FIXED)
- GIT-2C-F1 (CRITICAL): seed manifest `agents:` + default-ship scripts/schemas were untracked (`/.claude/*` gitignore) → fresh-clone pack abort E071. FIXED: `.gitignore` re-includes `.claude/{agents,scripts,schemas}`; seed manifest `agents: []`; scripts/schemas default flipped to opt-in.
- 2C-F2 (HIGH): default-ship pulled 18 untracked CK files → non-reproducible. FIXED by the opt-in flip (`apply_defaults` default False; `--include-scripts/--include-schemas` flags added; merge_cli honors them).
- 2C-F3 (MED): internal `plans/` review reports leaked into bundles. FIXED (`plans` added to `ALWAYS_DROP_DIRS`) + test.

### Core edges (FIXED)
- 2A-F2 (HIGH): non-deterministic hook pick (rglob order). FIXED (selection sorts; validate errors on >1 match → new code MANIFEST_E074) + test.
- 2A-F3 (MED): hook validate lacked `is_file()`. FIXED.
- 2A-F6 (MED): follow_shared over-include — KEPT dir-granular per decision; documented.
- 2A-F7 (LOW): `--max-size` negative accepted. FIXED (`_nonneg_int`).
- 2A-F8 (LOW): atomic_replace double-fault swallowed restore error. FIXED (annotate with backup path).
- 2A-F9 (LOW): `_include_shared` string iterated chars. FIXED (normalize in selection).
- 2A-F5 (LOW): follow_shared no transitive discovery. DEFERRED (YAGNI — `_shared` dirs have no SKILL.md; documented).

### Installer (2B)
- 2B-F1 (HIGH): ps1 `Read-SkillVersion` regex unanchored (matched `min_version:`). FIXED (anchored `(?m)^\s+version:`, mirrors sh; also fixes top-level-version divergence).
- 2B-F2 (MED): sh `semver_compare` locale-sensitive pre-release compare. FIXED in Cycle-2 partial (LC_ALL=C in function) — VERIFY.
- 2B-F3 (MED): unparseable version + FORCE → overwrite. FIXED both: sh `install.sh:183-196` (UNKNOWN VERSION → SKIP); ps1 `install.ps1:165-178` (was a REAL gap — fell to ADD → FORCE overwrote; now mirrors sh).
- 2B-F4 (LOW): "Stale kept" summary wrong under FORCE. FIXED both: sh summary printed phantom `$STALE` (never set) — now prints real `$STALE_KEPT`/`$STALE_WROTE` (`install.sh:297-302`); ps1 had one `$Stale` mislabeled under FORCE — split into `$StaleKept`/`$StaleWrote` with FORCE-aware message (`install.ps1:142-152, 270-275`).

### Product-spec ascii (2D) — FIXED (user opted to fix the deferred cosmetics)
- 2D-F3 (LOW): heatmap dropped non-canonical status from display. FIXED — non-canonical statuses now sum into an 'other' column (shown only when present) so no node is silently dropped (`render_ascii.py:heatmap`). +test.
- 2D-F4 (LOW): ASCII table separators sized from header → overlong label misaligned. FIXED — new shared `_grid()` helper computes per-column width from `max(label across header+rows)`; heatmap/scope/persona/risk all route through it (`render_ascii.py:_grid`). +alignment test.
- 2D-F5 (LOW): delta baseline picked by filename not mtime on same-second. FIXED (sort by st_mtime).

## Repo-level edits (by orchestrator, not agents)
- `.gitignore`: re-include `.claude/{agents,scripts,schemas}` (+ re-ignore their caches); (Cycle-1) claude-pack/assets exception.
- `.claude/pack.manifest.yaml`: `agents: []`.

## PENDING — ALL CLOSED (Cycle 2 wrap)
1. **Docs sync for the opt-in flip + E074** — DONE: `manifest-spec.md` (include_scripts/_schemas default `true`→`false`; apply_defaults note; ambiguous→E071/E072/E074), `flag-reference.md` (+`--include-scripts/--include-schemas`), `safety-rules.md` (`plans` added to Layer-2), `error-catalog.md` (+E074 ambiguous-hook, +E042/E043 which were undocumented), `SKILL.md` (+2 flags). Repo `CLAUDE.md` verified clean (no stale "default-ship scripts/schemas" text).
2. **2B-F4** stale summary — DONE both: sh prints real `$STALE_KEPT`/`$STALE_WROTE`; ps1 split counters + FORCE-aware message.
3. **2B-F2/F3** — DONE: F2 OK both (sh `LC_ALL=C`; ps1 ordinal). F3 was a REAL ps1 gap (fell to ADD → FORCE overwrote unparseable-version skill); now mirrors sh `UNKNOWN VERSION → SKIP`.
4. **Golden re-verify** — DONE: real build of seed manifest = 127 entries; `plans/` leak 0, top-level `.claude/scripts|schemas` 0, secrets/.env/pyc 0, product-spec 71 + claude-pack 42 skill files present, root has INSTALL.md/MANIFEST.json/install.{sh,ps1}/README/CLAUDE; gzip_mtime_zero true.

Also fixed in this wrap (user opted "fix all"): **2D-F3** heatmap 'other' column, **2D-F4** shared `_grid()` alignment helper (heatmap/scope/persona/risk). +3 product-spec tests.

## Convergence
Cycle 2 CLOSED: 23 findings + 3 late-found (2B-F3 ps1 gap, 2B-F4 sh+ps1) all fixed; 2 stale notes corrected (2B-F1, 2C-F2 were already done). Tests: claude-pack 77 · product-spec 92. **NOT yet converged** (need 2 clean cycles). Review PAUSED here per user request to update product-spec requirements. **Cycle 3** (when resumed) = regression sweep on all Cycle-2 changes (opt-in flip, hook resolver, ps1 regex+UNKNOWN-VERSION, escaping, `_grid`) + installer parity re-check + first convergence test.

## Unresolved questions
None blocking. All scope decisions confirmed by user.
