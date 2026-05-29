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
| 4 | ✅ DONE (fixes applied 2026-05-29) | **29 findings** (2 HIGH · 4 MED · 23 LOW; 0 CRITICAL) — 26 CONFIRMED + 3 PLAUSIBLE, ~all in product-spec (claude-pack regression-clean). Dedup → **22 distinct fixes, ALL applied + verified** (owner: "fix all, no defer"). Workflow re-scaled worked: **26 agents / ~2.1M tok** (vs C3's 42/~3M). Owner decisions: Q1=fail-loud `--layers` (validate token + empty-result guard) · Q2=ASCII explorer orphan-root · Q3=hoist facet/search engine into `_BODY_RENDER_JS` (incl. the deferred F15). |
| 5 | ✅ DONE (fixes applied 2026-05-30) | **39 findings** (11 MED · 28 LOW; 0 CRITICAL/HIGH) — 38 CONFIRMED + 1 PLAUSIBLE, 0 REFUTED. 19 correctness · 3 altitude · 17 cleanup; claude-pack 3 (cleanup/doc). **ALL 39 fixed + verified** (owner: "fix all, no defer"). Sweep wave was productive (+11 findings) — first sweep run hit a StructuredOutput false-negative, re-run via resume recovered it. Owner decisions: Q1=fail-loud `--layers` **both** surfaces · Q2=**multi-parent** explorer (HTML matches ASCII) · Q3=qualify CLAUDE.md network claim (doc-only) · Q4=fix all incl. pre-existing. |
| 6 | ✅ DONE (fixes applied 2026-05-30) | FULL thorough pass (owner override). **28 findings** (1 HIGH · 3 MED · 24 LOW; 28 CONFIRMED, 0 REFUTED). **The full pass earned its keep: caught 3 regressions the C5 fixes introduced** (HIGH hook-matcher divergence + llm-AC-double + horizon-label-missing). ALL fixed + verified (3 micro-perf items accepted-documented per YAGNI). primary surface = C5 fix diff. |
| 7 → 10 | ⏸️ PENDING (unblocked) | Cycle-6 fixes landed → Cycle 7 may start. Per convergence rule (stop after 2 consecutive zero-finding cycles; hard cap C10). Config = owner's call (full again vs narrow correctness-only per WORKFLOW-REVIEW §4). |

**Convergence:** NOT converged. Cycle 6 was not clean (28 findings) → counter at 0. Fixes now applied; next = Cycle 7. **Note: the C5 fixes introduced the C6 regressions (1 HIGH + 2 MED) — each full pass keeps surfacing fixes-induced defects + cleanup, so convergence is not near.** Stop after 2 consecutive zero-finding cycles; hard cap 10.

**Test state (green):** `claude-pack` **78** (was 77; +1 H1 path-pin) · `product-spec` **215** (was 211 at Cycle-6 start; +4 C6 regression tests).
Run: `PYTHONPATH=.claude/skills/<skill>/scripts ./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/<skill>/scripts/tests -q`

**Report paths (local, gitignored — may be absent on fresh clone):**
- Cycle 1: `.claude/skills/claude-pack/plans/reports/cycle-01-dual-skill-review-260529-0940-findings-and-fixes-report.md`
- Cycle 2: `plans/reports/cycle-02-dual-skill-review-260529-findings-fixes-and-pending-report.md`
- Cycle 3: `plans/reports/cycle-03-dual-skill-review-260529-1816-export-viewer-findings-report.md` (ALL 30 + 2 refuted; review-only, no fixes)
- Cycle 4: condensed into this file (§"Cycle 4" below). Raw 29-finding workflow output was ephemeral (`/tmp`); the durable record is the condensed block here.
- Cycle 5: `plans/reports/cycle-05-dual-skill-review-260530-findings-and-fixes-report.md` (39 findings + fixes + verification) + condensed in §"Cycle 5" below.
- Cycle 6: `plans/reports/cycle-06-dual-skill-review-260530-findings-and-fixes-report.md` (28 findings + fixes + verification) + condensed in §"Cycle 6" below.

### Cycle 4/5 workflow config (LOCKED 2026-05-29)

Full protocol in **`WORKFLOW-REVIEW.md`** (repo root, committed). Each cycle = one Workflow, 3 waves: **Find → consolidate/dedup → batched Verify → Sweep**. Main cost lever vs Cycle 3 (~42 agents / ~3M tok): **batched verify — one verifier per FILE, not per candidate** → the ~32 per-candidate verify agents collapse to ~6–8.

- **Order:** fix **all** Cycle-3 findings → commit + push → run Cycle 4. Never start a cycle with unfixed findings from the prior one.
- **Finders: NO cap.** Each finder surfaces every real defect (no padding, no ceiling); **consolidate/distinct happens in orchestration before** the verify (wave 2) and sweep (wave 3) waves, so cost is controlled by batching, not by truncating finders.
- **Cycle 4** (the single thorough pass, after Cycle-3 fixes land): scope = **full whole-skill** (both skills); **all 9 angles incl. cleanup**; per-file batched verify; sweep included. ✅ DONE — actual cost **26 agents / ~2.1M tok** (within estimate).
- **Cycle 5** (the second full thorough pass): ✅ DONE — full whole-skill, all 9 angles, batched per-file verify, sweep. Actual **39 findings / ~31 agents (incl. sweep re-run) / ~2.0M tok**. Sweep wave proved its worth (+11 findings). One workflow lesson: a finder/sweeper that concludes "nothing new" can end with prose and skip the StructuredOutput call → false-negative; the sweep prompt now MANDATES the tool call (even for `{candidates: []}`).
- **Cycle 6/7+** (convergence checks — two full passes C4+C5 now done, all cleanup fixed): scope = **narrow regression** (files touched by fixes + immediate callers); **correctness-only** (cleanup is cataloged + fixed in the thorough passes; re-running cleanup angles never converges to zero and would block the 2-clean-cycle stop); lean batched verify; sweep only if a finding lands. Est ~8 agents / ~0.6M tok.
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
- **I:** F18 ✅ panel CSS → `_viewer-head.html` (explorer divergence fixed); F19 ✅ docstring/CLAUDE.md/workflow-export narrowed; F23 ✅ dead `_safe_href`/`psSafeHref` removed; F25 ✅ singleton double-gate dropped; F26 ✅ `_body_or_struct`. **F15 ◐ PARTIAL** — detail-panel trio hoisted to `_BODY_RENDER_JS` (body-view-only, preserves H4 gating); facet/search engine left per-shell (no DOM-test harness to verify a parameterized refactor — deferred to a DOM-tested pass; **completed in Cycle 4 — see Q3 below**).

### Cycle 4 (29 findings — FIXED 2026-05-29; 22 distinct fixes, all applied)

Owner: **"fix all, no defer."** All in product-spec; claude-pack regression-clean. By cluster:

- **Q1 fail-loud `--layers` (2 findings, HIGH) ✅** `build_digest` now raises on (a) an unknown `--layers` token (validated vs `ALL_LAYERS`) and (b) a non-`all` selection filtered to empty (e.g. `--export VISION --layers prd` — the asymmetry where PRODUCT was protected but VISION/BRD silently dropped). `visualize.py` validates viewer tokens vs `goal,prd,epic,story` → exit 2. Closes the silent-empty-doc class the C3 fix only half-closed.
- **Q2 ASCII explorer orphan-root (1, MED) ✅** new `render_ascii._orphan_forest` reparents nodes whose parent was filtered out as roots (cyclic-edge guard included); `explorer()` delegates to `tree()` when no `--layers` (preserves `explorer==tree`), else forest. Was: empty `PRODUCT:` header for any goal-excluding subset.
- **HTML export frontmatter leak (1, MED ×3 angles) ✅** `_strip_frontmatter` drops the `.md` YAML block from the HTML body island (was rendering as a stray `<hr>`+setext `<h2>`); `render_html_doc(graph,…)` now reuses `chrome_values`.
- **Q3 facet/search hoist (1, LOW altitude — the C3-deferred F15) ✅** engine (`psFacetGroups/psDistinct/psSelfMatch/psBadge/psBuildFacets`) hoisted into `render_html._BODY_RENDER_JS`; both shells call it. Verified by **executing** the assembled JS under a DOM stub (node) — facets build, render emits nodes, click/search re-render without throwing — plus `node --check`. `psBuildFacets` also **localizes the Layer facet** (`L[v]`) — fixes the vi-facet-not-localized finding.
- **DRY ✅** `render_ascii.select_cards` (board/explorer/ascii-board); `render_html.file_timestamp` (4 writers); `spec_graph._now` imported into the 3 analytical scripts (`dt` removed); board column key uses `_hashable` (parity with ASCII board on malformed enums).
- **Cleanup ✅** dead `_SINGLETON_TYPES` removed; stale detail-panel comments (both shells); stale `assemble_digest` module docstring ("vision NOT a node"); `install.sh` header (marked+DOMPurify step); leaf-type (story) `--layers` warning wording; `<missing-id>` sentinel filtered from the unresolved-ID error; `visualize.py` reuses `_written_json` + `_unfence` (no double ASCII render on html mermaid-fallback); i18n `explorer` label.
- **H4 (1, PLAUSIBLE/LOW) ✅** the mermaid graph-view bundles Mermaid's OWN DOMPurify (third-party SVG sanitizer) — the H4 contract is "no SKILL body-sanitizer (`psRenderMarkdown`)", which holds. Test made precise (asserts `psRenderMarkdown` absent on ascii AND mermaid paths) + wording clarified (Mermaid bundle exempt).
- **Verification:** 189 product-spec (173→189, +16 new regression tests) + 77 claude-pack green; e2e on a temp fixture (all Q1 exit-2 cases, Q2 orphan-root, frontmatter-strip, valid exports); DOM-stub execution of both viewers' hoisted JS.

### Cycle 5 (39 findings — FIXED 2026-05-30; all applied)

Owner: **"fix all, no defer."** 0 CRITICAL/HIGH. Mostly product-spec; claude-pack 3 (cleanup/doc). Full report: `plans/reports/cycle-05-...-findings-and-fixes-report.md` (gitignored). By cluster:

- **Q1 fail-loud `--layers` BOTH surfaces (F2,F7) ✅** export `all`-branch no longer exempt unconditionally — raises (exit 2) when `--layers` strips PRE-EXISTING content (`all` on a genuinely empty spec stays allowed-empty); viewers (`board`/`explorer`) now raise (exit 2) on empty-after-filter at the `_dispatch_body_view` chokepoint. Closes the asymmetry the C3/C4 "fail-loud" only half-covered.
- **Q2 multi-parent explorer (F10,F1,F33,F34) ✅** explorer payload carries `parents` (list, all in-set parents) not a single `parent`; the HTML Tree renders a multi-goal PRD under EACH goal (matches the ASCII tree) with a per-path cycle guard; `visibleSet` walks all parents with a `seen` guard (F1 — a self/cyclic parent no longer hangs the tab; `spec_graph.parents_of` drops self-edges server-side). Depth = shortest-to-root. `_DEPTH_BY_TYPE` derived from `_LAYER_ORDER`.
- **ASCII/HTML/mermaid explorer parity (F3,F4) ✅** `explorer()` routes through the orphan-forest whenever `layers OR filter_wont` (was: only `layers`), using `select_cards` for the keep-set — so a kept child of a deferred OR layer-pruned parent reparents as a root on every format. Root determination tests ANY parent (multi-goal-aware).
- **Export correctness (F5,F6,F11,F12,F13,F14) ✅** YAML-safe frontmatter scalars (`:`/`#`/newline no longer break/truncate the `.md` or the HTML strip); bodyless story renders AC once at `--depth full`; `--compact-mode llm` includes a body-present story's AC + neutralizes a body `-->`; stable-filename docstring corrected to scope idempotency to the hash; export HTML title localized (`--lang vi`).
- **Resolution + warning truth (F8,F9) ✅** `--export VISION/PRODUCT` resolves by literal token (no self-contradictory "unresolved" when `id:` omitted); the `--layers` exclusion warning partitions excluded goals/prds into surfaced-via-sub-layer vs absent-entirely (no longer claims a childless goal is surfaced).
- **DRY helpers hoisted to `spec_graph` (F24,F25,F33,F37,F22) ✅** `CHILD_TYPE_FOR_PARENT` + `matching_child_counts` (gap rule, was triplicated across render_ascii/render_mermaid/check_traceability), `diff_graphs` (delta set-math + product-diff, was duplicated), `parents_of` (tree-parent index, was 2 homes w/ divergent coercion); dead `PARENT_FIELD_BY_TYPE` deleted; `ancestors()` kept-with-note.
- **Viewer/dispatch cleanup (F15,F16,F23,F29,F30,F31,F35,F36,F38,F39) ✅** board `--group-by horizon` facet added; persona honors `--filter-wont` in mermaid/html via a unified `_VIEW_KWARGS`/`_dispatch_view` (replaces the duplicated ascii/mermaid arity ladders); explorer renders only the active mode per keystroke (+ lazy repaint) and reuses cached vis on tab-click; board buckets-once; dead `all` label dropped; unused `List` import dropped; detail-panel body memoized; `visualize.py` docstring corrected (11 views).
- **claude-pack (F26,F27,F28) ✅** hook resolution indexes the tree once (was O(H·F) rescan per name); `is_dropped` hoists `_PATTERNS_LOWER` (no per-call re-lowercase); SKILL.md flags table gains the `--hooks` row.
- **Docs drift (F17,F18,F19,F20) ✅** removed the non-existent `--color` flag + the false stdin-input claim from visualization-spec; qualified CLAUDE.md "no runtime network calls" to match the shipped Mermaid graph-view CDN fallback (Q3, doc-only); documented `--filter-wont` (was in ZERO markdown) in SKILL.md + visualization-spec.
- **Verification:** product-spec **190 → 211** (+21 regression tests) + claude-pack **77** green; node DOM-stub of both viewers (multi-parent renders PRD under both goals, cyclic chains terminate, horizon facet, mode/tab/search clean); e2e on a temp fixture (export md/html/vi/layers/depth, board/explorer html/ascii/vi/filter-wont/group-by, persona-mermaid-filter-wont, gap, delta, strict_gate 0-errors; fail-loud exit-2 confirmed for unknown tokens + empty-after-filter export).

### Cycle 6 (28 findings — FIXED 2026-05-30; all applied)

Third full thorough pass (owner override: full, not narrow). Primary surface = the C5 fix diff. 0 CRITICAL. **The full pass caught 3 regressions the C5 fixes introduced.** Full report: `plans/reports/cycle-06-...-findings-and-fixes-report.md` (gitignored). By cluster:

- **H1 (HIGH, claude-pack) ✅** the C5 basename-only hook index (F26) **diverged** from `validate()`'s `rglob` → a path-qualified/glob hook name passed validation but was silently dropped from the tarball (exit 0), breaking the E074 "pin a unique path" remedy. Fix: ONE shared `manifest_loader.match_hooks()` (rglob) used by both `validate()` and `selection.resolve_selection` (drops C5's index — perf was negligible; also closes the un-mirrored validate twin). +regression test.
- **M1 (correctness) ✅** bodyless story rendered AC twice under `--compact-mode llm` (C5 F6 fixed only the full branch). Fix: shared `_content_with_ac` body-first helper used by both branches (can't diverge); dead `_body_or_struct` removed.
- **M3 + DRY (cleanup) ✅** C5 added `parents_of` but no mirror → forward children-adjacency re-typed in 4 sites + the closure walk in 3. Fix: add `spec_graph.children_of` + `_closure`; `downstream`/`ancestors`/`assemble_digest` consume them. Plus `is_visible` (ascii+mermaid tree), `_write_visual` (3 writers), `psMetaBadges`/`psWireSearch`/`appendHeader` (board+explorer client), agents+rules fold, dead `_orphan_forest` filter_wont param + vestigial goal `parent:"BRD"` removed, `--layers` warning reuses memoized child-reach.
- **Horizon facet label (C5 F15 added the facet, not its label) ✅** add `horizon` to i18n (en/vi) + both `_UI_KEYS`; `psBuildFacets` localizes chip values for all groups (`L[v]||v`, was layer-only); visualization-spec lists the horizon facet. (Fixes the bare lowercase `horizon:` header + raw chip values under `--lang vi`.)
- **render_export i18n/robustness ✅** body H1 localizes via `label('export',lang)` (matched the chrome title; .md+.html now agree under vi) + CR/LF in the product name collapse (a newline+`---` no longer garbles the H1).
- **defensive ✅** `render_explorer._depth` memoizes only at top level (no order-dependent depth on a malformed cyclic spec); `render_html` facet engine `state.facets[g]||{}` guards (group LIST is the single source of truth); `render_mermaid.delta` docstring notes its field-level limitation.
- **Doc ✅** `workflow-export.md` documents the `--export all --layers X` fail-loud case.
- **Accepted (YAGNI, no fix):** Flat-tabs bar rebuild on filter-change · `_dispatch_body_view` empty-guard recompute · `selection` redundant sorted-pick (finders concurred on the latter two).
- **Verification:** product-spec **211 → 215** (+4) + claude-pack **77 → 78** (+1) green; DOM-stub of both viewers re-run after the client refactors; e2e (vi H1 "Xuất đặc tả", board-vi "Mốc thời gian" horizon label, all flows exit 0, strict_gate clean).

---

## How to resume (Cycle 3+)

1. Confirm the new product-spec feature has landed; get its diff (`git diff` of the feature commits).
2. Re-read this file + (if present) the Cycle-1/2 reports for carried context.
3. Run the review (finders → verify → sweep) over the cycle's surface. **Cycle 4+ uses a re-scaled, leaner workflow** (Cycle 3's ~42-agent/~3M-token full pipeline was too costly for the owner's plan — config decided by interview, recorded in the Cycle-3 chat / report).
4. Fix all findings this cycle before starting the next (auto-fix safe; interview on risky/locked-decision items). **Cycle 3 + Cycle 4 fixes are DONE** (2026-05-29) — Cycle 5 may start.
5. Keep both test suites green; add tests for new behavior.
6. Write a cycle report to `plans/reports/` and update **this file's** Progress + Convergence.
7. Stop when 2 consecutive cycles produce zero new findings, or at Cycle 10.

## Open questions
**Cycle 3 owner decisions — LOCKED & applied (2026-05-29):** A=viewer artifact-type vocab · B=emit-once+dedup, unresolved→error · C=`llm`+`html` hard-reject · F10=escape-all-`<`.

**Cycle 4 owner decisions — LOCKED & applied (2026-05-29):** Q1=fail-loud `--layers` (validate token vs the surface vocab + raise on empty-after-filter) · Q2=ASCII explorer orphan-root (reparent filtered orphans, parity with HTML) · Q3=hoist the facet/search engine into `_BODY_RENDER_JS` (closes the C3-deferred F15). Owner directive: **"fix all, no defer"** — all 22 distinct fixes applied. H4 contract clarified: "no SKILL body-sanitizer (`psRenderMarkdown`)" — Mermaid's bundled DOMPurify is third-party/exempt.

**Cycle 5 owner decisions — LOCKED & applied (2026-05-30):** Q1=fail-loud `--layers` on **both** surfaces — export `all`-branch raises on layers-stripped-content (not just named selections), viewers raise on empty-after-filter (extends the C4 decision, which only covered token validation on viewers + the empty guard on export). Q2=**multi-parent** explorer — HTML Tree renders a multi-goal PRD under each goal, matching the ASCII tree (payload changed `parent`→`parents`). Q3=qualify the CLAUDE.md "no runtime external network calls" claim to match the already-shipped Mermaid graph-view CDN fallback (doc-only; body views still fail-closed). Q4=**fix all 39, no defer** incl. the 2 pre-existing behavioral items (board horizon facet, persona `--filter-wont` in mermaid/html). New locked decision: **viewer explorer is multi-parent** (was implicitly single-parent first-edge-wins).

**Cycle 6 — DONE (2026-05-30), no owner decisions needed** (all 28 findings were clear auto-fixes; 0 locked-decision conflict). Owner ran it as a FULL pass (override of the narrow default). The full pass caught 3 regressions the C5 fixes had introduced (HIGH hook-matcher + 2 MED).

**Next:** Cycle 7 — config is the owner's call. Per WORKFLOW-REVIEW §4 the eventual narrow correctness-only pass starts after a cleanup-clean cycle; cleanup is still surfacing (C6 had 17), and C5→C6 showed fixes can introduce regressions, so another FULL pass is defensible. **Watch for regressions from the C6 fixes:** the shared `manifest_loader.match_hooks` (claude-pack validate+selection), `spec_graph.children_of`/`_closure` (consumed by downstream/ancestors/assemble_digest), `render_export._content_with_ac` + body-H1 localization, the horizon i18n/`_UI_KEYS`/`psBuildFacets` chip-value change, `render_html._write_visual` + `psMetaBadges`/`psWireSearch`/`appendHeader` client refactor, `render_ascii.is_visible` + the slimmed `_orphan_forest`. Config in `WORKFLOW-REVIEW.md`. **Watch for regressions from the C5 fixes:** the explorer multi-parent payload (`parents` list) + the rewritten `explorer-shell.html` client (multi-parent Tree, cyclic guards, lazy active-mode render, tab-cache); `render_ascii.explorer`/`_orphan_forest` routing through `select_cards` + `parents_of`; the shared `spec_graph` helpers (`parents_of`/`matching_child_counts`/`diff_graphs`) consumed by render_ascii/render_mermaid/check_traceability; `assemble_digest` `all`-empty guard + the partitioned `--layers` warning + literal VISION/PRODUCT resolution; the `_yaml_scalar` frontmatter quoting; `visualize._VIEW_KWARGS`/`_dispatch_view`. Owner may opt for another full pass instead. Config in `WORKFLOW-REVIEW.md`.

**New product-spec feature — ✅ IMPLEMENTED (2026-05-29)**: read-once **Export** (`--export`) + interactive **Viewer** (`--viz board`/`explorer`) + unified ALL `--viz` HTML under one design system (marked+DOMPurify vendored + inlined, print-CSS, theme/palette).
- Design doc: `.claude/skills/product-spec/plans/reports/brainstorm-design-260529-1504-product-spec-export-and-viewer-report.md`
- Plan (7 phases; red-teamed + validated; Failed:0): `.claude/skills/product-spec/plans/260529-1504-product-spec-export-and-viewer/plan.md`
- Red-team report: `.claude/skills/product-spec/plans/reports/red-team-260529-1504-product-spec-export-and-viewer-plan-review-report.md`
- **Landed via `/ck:cook`.** SKILL.md bumped 1.0.0 → 1.1.0. New scripts: `assemble_digest.py`, `render_export.py`, `render_board.py`, `render_explorer.py`, `install-vendor-markdown.sh`; new templates: `_viewer-head.html`, `export-shell.html`, `board-shell.html`, `explorer-shell.html`; committed vendored libs `assets/vendor/{marked,purify}.min.js` (~68 KB). Modified: `render_html.py` (single-pass `substitute()` + body-render substrate), `render_ascii.py`, `visualize.py`, `i18n_labels.py`, `visual-html-shell.html`, `install.sh`, `SKILL.md`, repo-root `CLAUDE.md`, `references/visualization-spec.md` (+ new `references/workflow-export.md`), `eval/evals.json`. Fixture: added `vision.md` to `valid-spec`. `.claude/.ckignore`: allow the vendor dir.
- Tests (green): product-spec **92 → 156** (+64) · claude-pack **77** + golden integration **1**. Independent code-review PASS (0 CRITICAL/HIGH; XSS neutralization proven in a live DOM; 1 MED `assemble_digest.py` 220 LOC accepted-with-note, 2 LOW fixed).
- **Cycle 3 DONE — reviewed (18:16) + FIXED (19:07), 2026-05-29.** 30 findings; **29 fully fixed + verified, F15 partial** (facet/search hoist deferred). Reports (gitignored): `cycle-03-...-1816-...-findings-report.md` (review) + `cycle-03-...-1907-...-fixes-report.md` (fixes). product-spec 156→**173** tests · claude-pack **77**. **Next: run the re-scaled Cycle 4** (full thorough pass). Plan dir + per-cycle reports are gitignored (under `plans/`); this GOAL.md + the committed skill code are the durable record.
