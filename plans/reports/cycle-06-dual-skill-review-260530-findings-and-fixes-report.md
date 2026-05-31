# Cycle 6 — Hardcore Dual-Skill Review: Findings & Fixes

Third full thorough pass (owner override: full, not the narrow convergence pass). Primary surface = the Cycle-5 fix diff (`d430fcb..HEAD`). Workflow: 9 finders → batched per-file verify → 2 sweepers → sweep-verify. Durable condensed record in `GOAL.md` (this file is gitignored).

## Workflow run
- Wave 1: 28 raw candidates / 14 files. Wave 2: 24 kept, 0 refuted. Wave 3 sweep: +4 (forced-StructuredOutput prompt held — no false-negative this time). **Total 28 findings** — 1 HIGH · 3 MED · 24 LOW · 0 CRITICAL · 28 CONFIRMED · 0 REFUTED. 6 correctness · 5 altitude · 17 cleanup. ~29 agents / ~2.6M tok / ~25 min.
- **The full pass earned its keep:** it caught 3 real regressions the C5 fixes introduced (the HIGH hook-matcher + the llm-AC-double + the horizon-label-missing), which a narrow correctness-only pass might also have caught but the cleanup angles found the rest.

## Findings → fixes (all applied + verified; 3 YAGNI items accepted-documented)

### HIGH (1) — C5 regression
- **H1 (claude-pack)** `selection.py`'s C5 basename-only hook index diverged from `validate()`'s `rglob` matcher → a path-qualified (`a/foo.cjs`) or glob (`*.sh`) hook name passed validation but was **silently dropped from the tarball** (exit 0), breaking the documented E074 "pin a unique path" remedy. **Fix:** one shared `manifest_loader.match_hooks()` (rglob) used by BOTH `validate()` and `selection.resolve_selection` → they can no longer disagree (also closes the un-mirrored L4 twin). Drops C5's index (its perf win was negligible; correctness wins). +regression test (pin `a/shared.cjs` → validates AND bundles).

### MED (3)
- **M1** `render_export.py` llm branch: a bodyless story rendered AC twice under `--compact-mode llm` (C5 F6 fixed only the full branch). **Fix:** extract `_content_with_ac` shared by both branches (body-first; struct skeleton only when no body AND no AC) → the two can't diverge. Dead `_body_or_struct` removed. +test.
- **M2** `workflow-export.md` L25 under-stated C5 fail-loud (no mention of `--export all --layers X` exiting non-zero). **Fix:** doc updated to match `build_digest`.
- **M3** `spec_graph.py`: forward children-adjacency re-typed in 4 sites; C5 added `parents_of` but no mirror. **Fix:** add `children_of` + `_closure`; rewrite `downstream`/`ancestors` to use them; `assemble_digest._adjacency/_reach` consume them.

### LOW (24) — by cluster
- **Horizon facet (C5 F15 added the facet, not its label):** add `horizon` to i18n (en `Horizon` / vi `Mốc thời gian`) + both `_UI_KEYS`; `psBuildFacets` localizes chip VALUES for all groups (`L[v]||v`, was layer-only); visualization-spec facet enumeration lists horizon. (4 dup findings → these fixes.)
- **render_export:** body H1 localizes via `label('export',lang)` (was hardcoded English while the chrome title localized) + CR/LF in the name collapse to a space (a newline+`---` no longer garbles the H1 into a setext rule).
- **render_explorer:** `_depth` memoizes only at the top level (empty stack) → no order-dependent depth on a malformed cyclic spec.
- **render_mermaid.delta:** docstring notes field-level edits appear only in the ascii/html delta (pre-existing; not a regression).
- **render_html facet engine:** `state.facets[g]||{}` guards so the group LIST is the single source of truth (a shell needn't lockstep-declare every bucket); `psBuildFacets` seeds the bucket per rendered group.
- **DRY (C5-adjacent):** `is_visible` shared predicate (render_ascii tree + render_mermaid tree); `_orphan_forest` dead `filter_wont` param + `_visible` removed (select_cards already filters); vestigial `parent:"BRD"` dropped from goal nodes; `_write_visual` (render_html / board / explorer writers); `psMetaBadges` + `psWireSearch` + `appendHeader` shared client helpers (board + explorer); agents+rules resolution folded into one loop; `--layers` warning reuses a memoized child-reach.

### Accepted-documented (no fix — negligible per YAGNI; finders concurred on 2)
- Flat-tabs bar rebuilds on filter change (a handful of buttons; tab-click path already optimized).
- `_dispatch_body_view` empty-guard recomputes `select_cards` (O(nodes) on a tiny in-memory graph; finder said YAGNI).
- `selection` basename `sorted(...)[0]` pick now redundant under the shared matcher (finder said keep as a guard for unvalidated callers).

## Verification
- Tests: product-spec **211 → 215** (+4) · claude-pack **77 → 78** (+1, the H1 path-pin). Both green.
- DOM-stub (node): both viewers re-verified after the client refactors (psMetaBadges/psWireSearch/appendHeader/facet-guard) — multi-parent PRD under both goals, cyclic chains terminate, horizon facet present, mode/tab/search clean.
- E2e (CLI): export md/html/vi, board (`--group-by horizon --lang vi`) / explorer (`--filter-wont`), delta mermaid, strict_gate (0 errors); vi body H1 = "Xuất đặc tả — Acme Shop"; board vi payload carries the localized "Mốc thời gian" horizon label.

## Open questions / observations
- **C5 fixes introduced C6 regressions** (1 HIGH + 2 MED). Each full pass surfaces fewer correctness but cleanup keeps appearing; convergence (2 consecutive zero-finding cycles) is not near. Recommend the eventual switch to the narrow correctness-only pass once a cleanup-clean cycle lands, per WORKFLOW-REVIEW §4 — owner has been choosing full passes.
