# GOAL — Hardcore Dual-Skill Review (10 cycles)

Durable resume anchor for an in-progress, multi-cycle hardcore review of two Claude Code skills.
The per-cycle reports live under `plans/reports/` which is **gitignored** (`.gitignore:61`), so this file
is the authoritative, self-contained state — written so the review can continue even if the local reports are lost.

> Conversational language with the owner is Vietnamese; this file is English to match the repo's docs (references/SKILL.md/CLAUDE.md).

---

## Mission

Max-recall, whole-skill review of **`cleanmatic:product-spec`** and **`cleanmatic:claude-pack`**, run as up to **10 cycles**.
Each cycle re-runs the same hardcore review, carrying forward the prior cycles' findings as context, and **must finish all fixes before the next cycle begins**.

### Locked operating parameters (do NOT re-ask)
- **Scope:** whole skill — every script, reference, template, `SKILL.md`, tests, `install.sh`.
- **Termination:** converge-then-stop — stop after **2 consecutive cycles with zero new findings**, hard cap **10**.
- **Fix autonomy:** auto-fix safe findings; **interview only** on risky/ambiguous items or anything touching a locked decision (safety pattern / determinism / scope).

### Locked design decisions (carry across all cycles — never silently reverse)
1. **scripts/schemas opt-in.** Top-level `.claude/scripts` + `.claude/schemas` are CK-framework internals; NOT shipped by default. Enable via `--include-scripts` / `--include-schemas` or `defaults.include_scripts/_schemas: true`.
2. **Commit CK files, drop `agents:` from seed manifest.** `.claude/{agents,scripts,schemas}` are tracked (`.gitignore` re-includes them) so the repo self-packs reproducibly; the seed `.claude/pack.manifest.yaml` carries `agents: []`.
3. **Bundle hygiene:** drop only `plans/` from bundles (keep `eval/` + `tests/`). `plans` is in `ALWAYS_DROP_DIRS`.
4. **`follow_shared` granularity:** keep dir-granular (segment-0), not file-granular. Not a bug — documented.
5. **Safety filter:** case-insensitive across all 3 layers (exact/dirs/patterns); basename + full-arcname matching.
6. **Installer:** full SemVer-2.0 precedence; recipient per-skill hooks are opt-in (`RUN_HOOKS=1` / `-RunHooks`).

---

## EXPANDED SCOPE for Cycles 3 → 10

The owner is implementing a **new product-spec feature (a product-spec update)** before Cycle 3 resumes.
From **Cycle 3 through Cycle 10**, the review scope **expands** to cover, in addition to the two existing skills:

- the **new product-spec feature/update** (review for correctness + fix), AND
- **regression** introduced by that new feature into existing product-spec behavior, AND
- continued regression sweep on all Cycle-2 changes (below).

Cycle 3 therefore begins **only after** the new product-spec feature lands. Treat the new feature's diff as primary review surface, with the rest of both skills as secondary.

---

## Progress

| Cycle | Status | Result |
|-------|--------|--------|
| 1 | ✅ DONE | 31 findings, all fixed |
| 2 | ✅ DONE (CLOSED) | 23 findings + 3 late-found, all fixed; 2 stale notes corrected; deferred cosmetics later fixed on owner request |
| 3 → 10 | ⏸️ PENDING | Paused for the new product-spec feature; resume per Expanded Scope |

**Convergence:** NOT converged (need 2 consecutive clean cycles). Review is **paused**, not finished.

**Test state (green):** `claude-pack` **77** · `product-spec` **92**.
Run: `PYTHONPATH=.claude/skills/<skill>/scripts ./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/<skill>/scripts/tests -q`

**Report paths (local, gitignored — may be absent on fresh clone):**
- Cycle 1: `.claude/skills/claude-pack/plans/reports/cycle-01-dual-skill-review-260529-0940-findings-and-fixes-report.md`
- Cycle 2: `plans/reports/cycle-02-dual-skill-review-260529-findings-fixes-and-pending-report.md`

---

## Bugs fixed (condensed — survives loss of reports)

### Cycle 1 (31) — highlights
- **CRITICAL** secret leak via case-sensitivity → safety filter made case-insensitive (`.ENV`/`ID_RSA`/`.GIT`/`DEPLOY.PEM` all drop).
- **CRITICAL** 3× stored-XSS in self-contained HTML viz → `_safe_label`/`_safe_id` markup-clean; `<`/`>` escaped in HTML layer.
- **CRITICAL** `.gitignore` excluded `claude-pack/assets/` (3 installer templates + manifest example) → skill non-functional on fresh clone; fixed.
- `follow_shared` dead code; MANIFEST.json followed symlinks (hash leak); installer missing macOS `shasum`; installer downgrade split-brain; `brd_goals` iterated per-char; SKILL.md `--discover` wrong; eval fixture gaps; +18 MED/LOW.

### Cycle 2 (all fixed)
- **Regressions from Cycle-1:** `max_size_bytes: false` bricked builds (bool ⊂ int) → reject bool; mermaid HTML double-escaped `&` (`R&D`→`R&amp;amp;D`) → HTML layer escapes only `<`/`>`; +composition test.
- **Packaging CRITICAL:** seed manifest + default-ship scripts/schemas were untracked → fresh-clone pack abort (E071). Fixed via the opt-in flip + committing CK files + `agents: []`.
- **Bundle leak:** internal `plans/` shipped into bundles → added to `ALWAYS_DROP_DIRS`.
- **Non-deterministic hook pick** (rglob order) → sorted + ambiguous-hook error `MANIFEST_E074`.
- **Installer (sh+ps1):** version regex matched `min_version:` → anchored `^…version:`; locale-sensitive semver compare → `LC_ALL=C` (sh) / ordinal (ps1); unparseable-version + FORCE overwrote → `UNKNOWN VERSION → SKIP` (was a real ps1 gap); wrong "Stale kept" summary → split `STALE_KEPT`/`STALE_WROTE` counters with FORCE-aware message.
- **product-spec ASCII (owner opted to fix deferred cosmetics):** heatmap dropped non-canonical status → `other` column; table separators sized from header → shared `_grid()` computes width from `max(label across header+rows)` (heatmap/scope/persona/risk).
- **Misc:** `_nonneg_int` for `--max-size`; atomic-replace double-fault annotates restore failure + backup path; `_include_shared` string normalized; delta baseline by mtime not filename; +E042/E043 documented in error-catalog.
- **Docs synced** to all behavior changes (manifest-spec, flag-reference, safety-rules, error-catalog, SKILL.md).

---

## How to resume (Cycle 3+)

1. Confirm the new product-spec feature has landed; get its diff (`git diff` of the feature commits).
2. Re-read this file + (if present) the Cycle-1/2 reports for carried context.
3. Run the hardcore review (max-recall finders → verify → sweep) over: **new feature diff (primary)** + both skills + the Cycle-2 change surface (opt-in flip, hook resolver, installer version logic, HTML escaping, `_grid`).
4. Fix all findings this cycle before starting the next (auto-fix safe; interview on risky/locked-decision items).
5. Keep both test suites green; add tests for new behavior.
6. Write a cycle report to `plans/reports/` and update **this file's** Progress + Convergence.
7. Stop when 2 consecutive cycles produce zero new findings, or at Cycle 10.

## Open questions
None blocking. All scope decisions confirmed by owner. New product-spec feature requirements: TBD by owner before Cycle 3.
