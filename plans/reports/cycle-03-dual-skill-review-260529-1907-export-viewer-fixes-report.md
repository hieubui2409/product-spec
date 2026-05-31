# Cycle 3 — Fixes Applied (export + viewer findings)

**Date:** 2026-05-29 19:07 · **Status:** fixes DONE · **29/30 fully fixed + verified · F15 partial (documented).**
**Skill:** `cleanmatic:product-spec` (claude-pack untouched — 0 findings, regression-clean).
**Tests (green):** product-spec **173** (was 156 at review start; +17 net) · claude-pack **77**.
**Owner decisions (interview, locked this cycle):** A=viewer artifact-type vocab · B=emit-once+dedup+guard · C=hard-reject llm+html · F10=escape-all-`<`.

> Diagnosis was the Cycle-3 review report (`cycle-03-...-findings-report.md`) — each finding had file:line + root + fix. This cycle = apply + verify. No new findings surfaced during fixing.

---

## What changed (by cluster)

### A — viewer `goal→brd` vocab collision (F1,F2,F9,F13) ✅
- `render_ascii._filter_by_layers` now filters by **artifact type** (`n.get("type")`), not the export bucket `LAYER_FOR_TYPE` (single source for ASCII board + HTML board/explorer).
- `render_board`/`render_explorer` card/item `layer` field = the artifact **type** (was `LAYER_FOR_TYPE.get(type)`); `LAYER_FOR_TYPE` import dropped from all three viewers.
- i18n labels added: `goal/prd/epic/story` (en+vi) for facet/tab localization; added to both viewers' `_UI_KEYS`.
- CLI help (`visualize.py --layers`) already advertised `goal,prd,epic,story` → now honored (F9). Export `--layers` keeps doc-layer vocab `vision,brd,…` — surfaces intentionally differ, each self-consistent with its own help.
- **Verified e2e:** `--viz board --layers goal` shows `BRD-G1/BRD-G2` (was empty). Explorer `goal` in `layer_order`, items `layer=="goal"` → Flat-tabs goal tab fills.

### B — export selection guards / silent-empty / dedup (F3,F4,F6,F8,F12) ✅
- New `_resolve_selection` → `(spec_targets, singleton_types, unresolved)`. Vision/BRD/PRODUCT split OUT of the edge-walk target set (context singletons).
- `build_digest` **raises ValueError** on unresolved IDs (lists bad + valid) and on empty/whitespace selection; `--export all` allowed-empty. `render_export.main` catches → stderr + **exit 2**.
- F4: PRODUCT kept via `_in_layers` (layer-agnostic context); no bogus `--layers` warning when none passed. `TYPE_RANK` gains `product:0` (sorts first).
- F8: VISION emitted **once** (dedup by id in singleton append) — no duplicate `<a id="vision">`/TOC.
- F12: `--layers` warning collapses to **one per excluded TYPE** (was one per node) → `--export all --layers prd` = 3 warnings, not N.
- **Verified e2e:** `--export VISION` → 1 anchor; `--export PRODUCT` → product present, 0 warnings; `--export PRD-TYPO` → exit 2 with valid-ID list; `--export all` still OK.

### C — `--compact-mode llm` + `--format html` (F5) ✅
- `write_export` rejects the combo with a clear ValueError (DOMPurify strips `<!-- COMPACT -->`; no `.md` for step-2). md+llm and html+struct remain valid. **Verified:** combo → exit 2.

### D — viewer layers/depth (F7,F11) ✅
- F7: `render_ascii.explorer` forwards `--layers` (filters nodes+edges via `_filter_by_layers`, then renders tree). Was silently ignored.
- F11: explorer `build_payload` recomputes per-item `depth` from the **reconciled parent chain** over `present_ids` (not static `_DEPTH_BY_TYPE`) → after a layer filter, a story whose epic is pruned becomes `parent="" depth=0`, so Tree-root and Table-indent agree.

### E — `embed_spec_data` `<!--` render-break (F10) ✅ (+ R2 gap closed)
- `embed_spec_data` now escapes **every `<` → `<`** (was only `</`→`<\/`). Neutralizes `</script>` + `<script` + the `<!--` primer at once; `<` round-trips via `JSON.parse`. (Report suggested `&#x3c;` — that is WRONG for a `<script>` data island, which is not entity-decoded; `<` is the correct JSON escape satisfying the round-trip requirement.)
- **R2 settlement:** rather than a browser test, added a **structural invariant** test — no raw `<` survives in the island body (so the WHATWG script-data states are unreachable by construction, for ALL conformant parsers — stronger than one browser render) + a `JSON.parse` round-trip test + the `<!--`+`<script` primer test. Updated 4 tests that asserted the old `<\/script>` form.

### F — `--filter-wont` help (F14) ✅ — now lists board/explorer.

### G — duplicate parse / perf (F16,F17,F27,F28) ✅
- `spec_graph.build_graph_with_artifacts(root) → (graph, artifacts)` (extracted shared `_assemble_graph`); used by `render_export.write_export` + `visualize._dispatch_body_view` → docs/product parsed **once** (was 2×).
- F27: `build_digest` builds parents/children adjacency **once** (`_adjacency`/`_reach`) instead of `ancestors()`/`downstream()` per target → O(N+edges).
- F28: export markdown rendered **once** with the real timestamp; hash computed over the timestamp-stripped doc (stable filename preserved).

### H — viewer-renderer DRY (F20,F21,F22,F24,F29,F30) ✅
- F20: `render_export._now_iso` removed → `spec_graph._now` reused; `render_html.assemble` uses `_now` too.
- F21/F29: single shared `spec_graph.index_artifacts(artifacts)` (id→artifact); board/explorer/digest build their maps on it (raw ok-filter loop no longer triplicated).
- F22/F24/F30: `render_html.product_name()` + `chrome_values()` + `assemble_body_shell()` collapse the `read→values→update({lang_attr,title,product_name,generated_at})→substitute` preamble shared by board/explorer.

### I — simplification (F18,F15,F19,F23,F25,F26)
- F18 ✅: detail-panel CSS (`.ps-detail*` incl. `:first-child` margin reset) moved into `_viewer-head.html`; board-shell drops its copy; explorer-shell drops inline styles + uses the `.ps-detail-body` class (fixes the explorer-only top-margin divergence) + shared print-hide.
- **F15 ◐ PARTIAL:** the verbatim detail-panel interaction (`psOpenDetail`/`psCloseDetail`/Escape) hoisted into `render_html._BODY_RENDER_JS` (body-view-only — keeps the 9 legacy graph views free of any sanitizer reference per **H4 symmetric gating**; shells call `psRegisterDetail(byId)`). The facet/search engine (`buildFacets`/`distinct`/`facetActive`/search-wiring, ~40 lines) is **left per-shell**: it closes over shell-specific data shapes + render callbacks, and there is **no DOM/Playwright harness** to prove a parameterized refactor side-effect-free (HARD-GATE-NO-SIDE-EFFECTS). The Cycle-3 report itself flagged F15 as "the riskiest cleanup … dedicated refactor pass." Deferred to a DOM-tested pass.
- F19 ✅: `assemble_digest` docstring + `CLAUDE.md` + `workflow-export.md` narrowed — `build_digest` powers `--export` ONLY; viewers build their own payloads.
- F23 ✅: dead `_safe_href`/`_SAFE_HREF_SCHEMES` (render_html) + `psSafeHref` (_viewer-head) removed; H3 sink comment + test comment corrected; `test_safe_href_*` removed.
- F25 ✅: vision/brd singleton inline layer-guards dropped (the final `kept` filter is the single gate — byte-identical).
- F26 ✅: `_section_body` empty-body fallback extracted to `_body_or_struct` (AC append preserved for story `full`).

### Refuted
- R1 (goals→unassigned) — sound, no action.
- R2 — the F10 escape-all-`<` fix closes both F10 and the test gap; settled with the structural-invariant + round-trip + primer tests (see E).

---

## Verification

- **Unit:** product-spec 173 / claude-pack 77 — all green. New tests: selection guards (unresolved/empty/typo), VISION-once, PRODUCT-keep, per-type warning, viewer `--layers goal`, explorer depth-parity, ASCII-explorer layers, llm+html reject, `<!--` primer + round-trip.
- **E2E (temp fixture copy):** `--viz board --layers goal` (goals shown) · `--export VISION` (1 anchor) · `--export PRODUCT` (present, 0 warnings) · `--export PRD-TYPO` (exit 2) · `--compact-mode llm --format html` (exit 2) · `--export all` + board/explorer/legacy html render OK.
- **Locked decisions respected:** H4 symmetric gating preserved (legacy views inline no sanitizer code; verified by `test_shared_head_has_no_sanitizer_code` + `test_legacy_html_...`). Cycle-2 `&`-escape, determinism, safety filter untouched. claude-pack regression-clean.

## Open items
- **F15 facet/search hoist** — deferred to a DOM-tested refactor pass (KISS + no-regression gate). Detail-panel portion done.
- Edge: `--export VISION --layers prd` (contradictory flags) yields an empty doc with no warning — pre-existing behavior, not a regression; candidate minor follow-up if owner wants a post-filter-empty guard.
