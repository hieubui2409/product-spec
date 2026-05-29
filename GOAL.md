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
| 3 | ✅ DONE (fixes applied 2026-05-29) | **30 findings** (5 HIGH · 11 MED · 14 LOW · 0 CRITICAL) + 2 refuted, all in export+viewer (`6009c50`). **29/30 fully fixed + verified; F15 partial** (detail-panel hoisted; facet/search engine deferred — no DOM-test harness). Owner decisions locked: A=viewer artifact-type vocab · B=emit-once+dedup+guard · C=reject llm+html · F10=escape-all-`<`. claude-pack: 0 findings. |
| 4 → 10 | ⏸️ PENDING (unblocked) | Cycle-3 fixes landed → Cycle 4 may start. Workflow **re-scaled** to cut the ~42-agent / ~3M-token Cycle-3 cost (config locked in `WORKFLOW-REVIEW.md`). |

**Convergence:** NOT converged. Cycle 3 was not clean (30 findings) → counter at 0. Fixes now applied; next = Cycle 4 (the single thorough full-skill pass). Stop after 2 consecutive zero-finding cycles; hard cap 10.

**Test state (green):** `claude-pack` **77** · `product-spec` **173** (was 156 at Cycle-3 review start; +17 from the fix regression tests).
Run: `PYTHONPATH=.claude/skills/<skill>/scripts ./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/<skill>/scripts/tests -q`

**Report paths (local, gitignored — may be absent on fresh clone):**
- Cycle 1: `.claude/skills/claude-pack/plans/reports/cycle-01-dual-skill-review-260529-0940-findings-and-fixes-report.md`
- Cycle 2: `plans/reports/cycle-02-dual-skill-review-260529-findings-fixes-and-pending-report.md`
- Cycle 3: `plans/reports/cycle-03-dual-skill-review-260529-1816-export-viewer-findings-report.md` (ALL 30 + 2 refuted; review-only, no fixes)

### Cycle 4/5 workflow config (LOCKED 2026-05-29)

Full protocol in **`WORKFLOW-REVIEW.md`** (repo root, committed). Each cycle = one Workflow, 3 waves: **Find → consolidate/dedup → batched Verify → Sweep**. Main cost lever vs Cycle 3 (~42 agents / ~3M tok): **batched verify — one verifier per FILE, not per candidate** → the ~32 per-candidate verify agents collapse to ~6–8.

- **Order:** fix **all** Cycle-3 findings → commit + push → run Cycle 4. Never start a cycle with unfixed findings from the prior one.
- **Finders: NO cap.** Each finder surfaces every real defect (no padding, no ceiling); **consolidate/distinct happens in orchestration before** the verify (wave 2) and sweep (wave 3) waves, so cost is controlled by batching, not by truncating finders.
- **Cycle 4** (the single thorough pass, after Cycle-3 fixes land): scope = **full whole-skill** (both skills); **all 9 angles incl. cleanup** (so the cleanup fixes get verified too); per-file batched verify; sweep included. Est ~16–20 agents / ~1.5–2M tok.
- **Cycle 5+** (convergence checks): scope = **narrow regression** (files touched by fixes + immediate callers); **correctness-only** (cleanup dropped — already cataloged, and cleanup nits never converge to zero so they'd block the stop condition); lean single/few batched verifier; sweep only if a finding lands. Est ~8 agents / ~0.6M tok.
- **Convergence unchanged:** stop after 2 consecutive cycles with **zero new findings**; hard cap Cycle 10.

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

### Cycle 3 (30 findings — FIXED 2026-05-29; 29 full + F15 partial)

All in product-spec, export+viewer feature (`6009c50`). 0 CRITICAL. Fix report: `plans/reports/cycle-03-...-1907-export-viewer-fixes-report.md` (gitignored). By cluster:

- **A (F1,F2,F9,F13) ✅** viewer `--layers`/facet/Flat-tabs now use **artifact type** (`goal,…`): `_filter_by_layers` filters by `n.type`; board/explorer card `layer`=type; `LAYER_FOR_TYPE` import dropped from viewers; i18n labels added. Export keeps doc-layer vocab (`vision,brd,…`) — surfaces intentionally differ.
- **B (F3,F4,F6,F8,F12) ✅** `_resolve_selection` splits VISION/BRD/PRODUCT out as singletons; `build_digest` **raises** on unresolved/empty (CLI exit 2); PRODUCT kept (`_in_layers`); VISION emit-once (dedup); `--layers` warning = one-per-excluded-**type**.
- **C (F5) ✅** `write_export` hard-rejects `--compact-mode llm`+`--format html` (exit 2).
- **D (F7,F11) ✅** ASCII explorer forwards `--layers`; explorer depth recomputed from reconciled parent chain (Tree/Table agree post-filter).
- **E (F10) ✅** `embed_spec_data` escapes **every `<` → `<`** (not `&#x3c;` — wrong for a script island; `<` round-trips via JSON.parse). Closes F10 + the R2 gap (structural-invariant + round-trip + `<!--` primer tests). R1 sound (no action).
- **F (F14) ✅** help lists board/explorer.
- **G (F16,F17,F27,F28) ✅** `build_graph_with_artifacts` (parse once); adjacency built once; markdown rendered once (timestamp-stripped hash).
- **H (F20,F21,F22,F24,F29,F30) ✅** shared `spec_graph._now`/`index_artifacts` + `render_html.product_name/chrome_values/assemble_body_shell`.
- **I:** F18 ✅ panel CSS → `_viewer-head.html` (explorer divergence fixed); F19 ✅ docstring/CLAUDE.md/workflow-export narrowed; F23 ✅ dead `_safe_href`/`psSafeHref` removed; F25 ✅ singleton double-gate dropped; F26 ✅ `_body_or_struct`. **F15 ◐ PARTIAL** — detail-panel trio hoisted to `_BODY_RENDER_JS` (body-view-only, preserves H4 gating); facet/search engine left per-shell (no DOM-test harness to verify a parameterized refactor — deferred to a DOM-tested pass, as the review report itself flagged).

---

## How to resume (Cycle 3+)

1. Confirm the new product-spec feature has landed; get its diff (`git diff` of the feature commits).
2. Re-read this file + (if present) the Cycle-1/2 reports for carried context.
3. Run the review (finders → verify → sweep) over the cycle's surface. **Cycle 4+ uses a re-scaled, leaner workflow** (Cycle 3's ~42-agent/~3M-token full pipeline was too costly for the owner's plan — config decided by interview, recorded in the Cycle-3 chat / report).
4. Fix all findings this cycle before starting the next (auto-fix safe; interview on risky/locked-decision items). **Cycle 3 fixes are DONE** (2026-05-29) — Cycle 4 may start.
5. Keep both test suites green; add tests for new behavior.
6. Write a cycle report to `plans/reports/` and update **this file's** Progress + Convergence.
7. Stop when 2 consecutive cycles produce zero new findings, or at Cycle 10.

## Open questions
**Cycle 3 owner decisions — LOCKED & applied (2026-05-29):** A=viewer uses artifact-type vocab · B=`--export VISION`/`PRODUCT` emit-once+dedup, unresolved→error · C=`llm`+`html` hard-reject · F10=escape-all-`<` (+ structural-invariant test, no browser harness needed). Cleanup H done; **I done except F15 facet/search hoist (deferred — needs a DOM test harness)**.

**Next:** Cycle 4 — the single thorough full-skill pass (both skills, all 9 angles incl. cleanup so the fixes get verified; per-file batched verify; sweep). Watch for regressions from the Cycle-3 fixes (esp. viewer vocab change, `build_digest` selection guards, `embed_spec_data` escape change, the `build_graph_with_artifacts`/`index_artifacts`/`assemble_body_shell` refactors). Config in `WORKFLOW-REVIEW.md`.

**New product-spec feature — ✅ IMPLEMENTED (2026-05-29)**: read-once **Export** (`--export`) + interactive **Viewer** (`--viz board`/`explorer`) + unified ALL `--viz` HTML under one design system (marked+DOMPurify vendored + inlined, print-CSS, theme/palette).
- Design doc: `.claude/skills/product-spec/plans/reports/brainstorm-design-260529-1504-product-spec-export-and-viewer-report.md`
- Plan (7 phases; red-teamed + validated; Failed:0): `.claude/skills/product-spec/plans/260529-1504-product-spec-export-and-viewer/plan.md`
- Red-team report: `.claude/skills/product-spec/plans/reports/red-team-260529-1504-product-spec-export-and-viewer-plan-review-report.md`
- **Landed via `/ck:cook`.** SKILL.md bumped 1.0.0 → 1.1.0. New scripts: `assemble_digest.py`, `render_export.py`, `render_board.py`, `render_explorer.py`, `install-vendor-markdown.sh`; new templates: `_viewer-head.html`, `export-shell.html`, `board-shell.html`, `explorer-shell.html`; committed vendored libs `assets/vendor/{marked,purify}.min.js` (~68 KB). Modified: `render_html.py` (single-pass `substitute()` + body-render substrate), `render_ascii.py`, `visualize.py`, `i18n_labels.py`, `visual-html-shell.html`, `install.sh`, `SKILL.md`, repo-root `CLAUDE.md`, `references/visualization-spec.md` (+ new `references/workflow-export.md`), `eval/evals.json`. Fixture: added `vision.md` to `valid-spec`. `.claude/.ckignore`: allow the vendor dir.
- Tests (green): product-spec **92 → 156** (+64) · claude-pack **77** + golden integration **1**. Independent code-review PASS (0 CRITICAL/HIGH; XSS neutralization proven in a live DOM; 1 MED `assemble_digest.py` 220 LOC accepted-with-note, 2 LOW fixed).
- **Cycle 3 DONE — reviewed (18:16) + FIXED (19:07), 2026-05-29.** 30 findings; **29 fully fixed + verified, F15 partial** (facet/search hoist deferred). Reports (gitignored): `cycle-03-...-1816-...-findings-report.md` (review) + `cycle-03-...-1907-...-fixes-report.md` (fixes). product-spec 156→**173** tests · claude-pack **77**. **Next: run the re-scaled Cycle 4** (full thorough pass). Plan dir + per-cycle reports are gitignored (under `plans/`); this GOAL.md + the committed skill code are the durable record.
