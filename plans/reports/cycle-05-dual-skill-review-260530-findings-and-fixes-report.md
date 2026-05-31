# Cycle 5 — Hardcore Dual-Skill Review: Findings & Fixes

Full thorough pass (config per `WORKFLOW-REVIEW.md` §6, C5 row). Workflow: 9 finders → batched per-file verify → 2 sweepers → sweep-verify. This report is the per-cycle detail; the durable condensed record is in `GOAL.md` (this file is gitignored).

## Workflow run

- **Wave 1 (Find):** 9 angle finders → 30 raw candidates, 13 files.
- **Wave 2 (Verify):** one verifier per file → 28 kept (CONFIRMED+PLAUSIBLE), 0 refuted.
- **Wave 3 (Sweep):** first run both sweepers failed StructuredOutput (returned prose) → `sweep=0` was a FALSE negative. Re-ran via `resumeFromRunId` with a forced-tool-call prompt (finders+verifiers cached, 0 extra cost) → **11 new sweep findings, all CONFIRMED**.
- **Total: 39 findings** — 11 MED · 28 LOW · 0 CRITICAL/HIGH · 38 CONFIRMED + 1 PLAUSIBLE · 0 REFUTED. 19 correctness · 3 altitude · 17 cleanup. claude-pack: 3 (all cleanup/efficiency/doc).
- Cost: ~24 agents / ~2.0M tok (run 1) + ~7 agents (sweep re-run).

## Owner decisions (locked 2026-05-30)

- **Q1** = fail-loud `--layers` on **both** surfaces (export `all` + viewers).
- **Q2** = **multi-parent** explorer (HTML matches the ASCII tree).
- **Q3** = qualify the CLAUDE.md "no runtime network" claim to match the already-shipped CDN graph-view fallback (no behavior change).
- **Q4** = **fix all 39**, no defer (incl. the 2 pre-existing behavioral items).

## Findings → fixes (all applied + verified)

### Correctness (19)
- **F1 (MED)** HTML explorer client lacked the cyclic-edge guard → self/cyclic parent hung the tab. Fix: `spec_graph.parents_of` drops self-edges (server), and the client `visibleSet`/`renderTree` got `seen`/path guards. `explorer-shell.html`, `spec_graph.py`.
- **F2 (MED)** `--export all --layers X` wrote an empty doc + exit 0 when `--layers` stripped pre-existing content. Fix: narrow the `all`-exemption — fail loud when `entries` non-empty but `kept` empty. `assemble_digest.py`.
- **F3 (MED)** ASCII explorer (`--layers`) dropped a child of a deferred parent; HTML reparented it. Fix: `explorer()` keep-set via `select_cards`. `render_ascii.py`.
- **F4 (MED)** ASCII explorer (no `--layers`) dropped a kept child of a deferred parent under `--filter-wont` (bypassed `_orphan_forest`). Fix: route through orphan-forest when `layers OR filter_wont`. `render_ascii.py`.
- **F5 (MED)** Export `.md` frontmatter f-string interpolation of `product_name` → `:`/`#`/newline broke/truncated YAML + broke the HTML strip. Fix: `_yaml_scalar()` double-quoted scalar. `render_export.py`.
- **F6 (MED)** Bodyless story with AC rendered AC twice at `--depth full`. Fix: render the raw body directly; struct fallback only when no body AND no AC. `render_export.py`.
- **F7 (MED)** Viewer `--layers` empty-after-filter was not fail-loud (board rendered empty, exit 0). Fix: guard at `_dispatch_body_view` → exit 2 (Q1). `visualize.py`.
- **F8 (LOW)** `--export VISION/PRODUCT` self-contradictory "unresolved" error when the file omits `id:`. Fix: match the literal token like `BRD`. `assemble_digest.py`.
- **F9 (LOW)** `--layers` warning falsely claimed a childless excluded goal "appears via sub-layers". Fix: partition excluded ids into surfaced (has included descendant) vs absent. `assemble_digest.py`.
- **F10 (LOW)** HTML explorer dropped multi-goal PRD coverage the ASCII tree shows. Fix: multi-parent payload (`parents` list) + client renders a node under each parent (Q2). `render_explorer.py`, `explorer-shell.html`.
- **F11 (LOW)** Docstring overclaimed a "stable filename" (name embeds a wall-clock ts). Fix: scope idempotency to the hash. `render_export.py`.
- **F12 (LOW/PLAUSIBLE)** `--compact-mode llm` body containing `-->` closed the COMPACT region early for a comment-aware consumer. Fix: neutralize `-->` with a U+200B (defensive; documented LLM consumer unaffected). `render_export.py`.
- **F13 (LOW)** `--compact-mode llm` dropped a body-present struct story's AC. Fix: append the AC list inside the COMPACT region. `render_export.py`.
- **F14 (LOW)** Export HTML `<title>/<h1>` "Spec Export" hardcoded English under `--lang vi`. Fix: i18n key `export`. `render_export.py`, `i18n_labels.py`.
- **F15 (LOW)** Board `--group-by horizon` had no horizon facet (pre-existing). Fix: add `horizon` to `psFacetGroups` + both shells' facet state (Q4). `render_html.py`, `board-shell.html`, `explorer-shell.html`.
- **F16 (LOW)** persona view dropped `--filter-wont` in mermaid/html (pre-existing). Fix: thread `filter_wont` into `render_mermaid.persona` + the unified dispatch (Q4). `render_mermaid.py`, `visualize.py`.
- **F17 (LOW)** Doc promised a `--color` ASCII flag no script implements. Fix: removed the clause. `visualization-spec.md`.
- **F18 (LOW)** Doc claimed stdin input; no script reads stdin. Fix: removed the clause. `visualization-spec.md`.
- **F19 (LOW)** CLAUDE.md "No runtime external network calls" contradicted the Mermaid graph-view CDN fallback. Fix: qualified to "when assets are vendored" + named the degraded-install fallback (Q3, doc-only). `CLAUDE.md`.

### Altitude (3)
- **F20 (MED)** `--filter-wont` (a real output-changing flag) was documented in ZERO markdown. Fix: SKILL.md flags row + `visualization-spec.md`.
- **F21 (LOW)** `_orphan_forest` docstring/test comment wrongly claimed the (flat) ASCII board "reparents orphans". Fix: corrected. `render_ascii.py`, `test_render_viewer.py`.
- **F22 (LOW)** `ancestors()` has no production caller (tests only). Fix: keep-with-note docstring (deliberate public API). `spec_graph.py`.

### Cleanup (17)
- **F23 (MED)** Explorer rebuilt all 3 mode DOMs per keystroke. Fix: render only the active mode + lazy dirty repaint. `explorer-shell.html`.
- **F24 (MED)** `gap()` unaddressed-parent rule triplicated. Fix: shared `spec_graph.CHILD_TYPE_FOR_PARENT` + `matching_child_counts()`. `spec_graph.py`, `render_ascii.py`, `render_mermaid.py`, `check_traceability.py`.
- **F25 (MED)** `delta()` set-math + product-diff duplicated. Fix: shared `spec_graph.diff_graphs()`. `render_ascii.py`, `render_mermaid.py`.
- **F26 (LOW)** Hook resolution re-walked the hooks tree per name (O(H·F)). Fix: single basename→paths index. `pack/selection.py`.
- **F27 (LOW)** `is_dropped` re-lowercased the invariant patterns per call. Fix: hoisted `_PATTERNS_LOWER`. `safety_check.py`.
- **F28 (LOW)** claude-pack SKILL.md flags table omitted `--hooks`. Fix: added the row.
- **F29 (LOW)** Board `render()` re-walked `visible[]` per column (O(col·N)). Fix: bucket once. `board-shell.html`.
- **F30 (LOW)** Tab-click recomputed `visibleSet` + rebuilt the whole bar. Fix: reuse cached vis, swap only the active list pane. `explorer-shell.html`.
- **F31 (LOW)** Dead label key `all` shipped in every viewer payload. Fix: dropped from `i18n_labels` + both `_UI_KEYS`.
- **F32 (LOW)** `(no PRODUCT.md)` fallback inlined twice. Fix: `_ascii_product_name()`. `render_ascii.py`.
- **F33 (LOW)** `parent_of` "first-parent-wins" index re-inlined in 2 homes (divergent coercion). Fix: shared `spec_graph.parents_of()`. `render_explorer.py`, `render_ascii.py`.
- **F34 (LOW)** `_DEPTH_BY_TYPE` duplicated `_LAYER_ORDER`. Fix: derived from it. `render_explorer.py`.
- **F35 (LOW)** Unused `List` import. Fix: dropped. `render_html.py`.
- **F36 (LOW)** Detail panel re-parsed the body on every open. Fix: `psDetailCache` memo. `render_html.py`.
- **F37 (LOW)** Dead constant `PARENT_FIELD_BY_TYPE` (already drifted). Fix: deleted. `spec_graph.py`.
- **F38 (LOW)** `_render_ascii`/`_render_mermaid` duplicated the arity dispatch ladder. Fix: `_VIEW_KWARGS` map + `_dispatch_view`. `visualize.py`.
- **F39 (LOW)** `visualize.py` docstring said "9 views" (actual 11) + omitted flags. Fix: updated. `visualize.py`.

## Verification

- **Tests:** product-spec **190 → 211** (+21 regression tests in `test_layers_parity_and_export_guards.py` + 3 viewer-payload tests updated for the multi-parent shape); claude-pack **77**. Both green.
- **DOM-stub (node):** assembled explorer + board client JS executed against a crafted payload (multi-goal PRD + self-cycle + 2-cycle): PRD renders under BOTH goals (F10), cyclic chains terminate without hang (F1), horizon facet present (F15), mode switch (F23) + tab click (F30) + search re-render run clean.
- **E2e (CLI on the valid-spec fixture):** export md/html (incl `--lang vi`, `--layers`, `--depth full`), board/explorer html (incl `--group-by horizon`, `--filter-wont`, `--lang vi`), ascii explorer with `--layers`, persona mermaid honoring `--filter-wont`, gap, delta, `strict_gate` (0 errors) — all exit 0 + write output. Fail-loud paths verified exit 2: unknown `--layers` token (export + viewer), and empty-after-filter export (vision.md removed).

## Open questions

None. All 4 owner decisions locked + applied; all 39 findings fixed + verified.
