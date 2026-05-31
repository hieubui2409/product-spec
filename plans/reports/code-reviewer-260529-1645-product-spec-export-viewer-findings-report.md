# Code Review — product-spec F1 Export + F2 Viewers + unified HTML design system

Reviewer: code-reviewer · Date: 2026-05-29 · Scope: read-only (skill-dev repo)
Plan: `.claude/skills/product-spec/plans/260529-1504-product-spec-export-and-viewer/`

## Verdict: PASS — ship-ready

All 5 hard-gate-no-side-effects items verified. No CRITICAL/HIGH findings. 3 LOW + 1 MED (all non-blocking, cosmetic/maintainability). Tests green; XSS neutralization empirically proven against the real vendored libs in a live DOM.

### Test counts (final clean re-run, no tree pollution — all renders used mktemp dirs)
- product-spec: **156 passed** (assemble_digest 15, html_sanitize 14, render_export 12, render_viewer 18, scripts 29, visualize 68)
- claude-pack: **77 passed**
- golden integration (`-m integration`): **1 passed**

All match expected.

---

## Gate-by-gate verification

### Gate 1 — Acceptance criteria met: PASS
Walked every phase success-criterion against live behavior on the fixture (`scripts/tests/fixtures/valid-spec`, which now includes `vision.md` — C1b satisfied):
- **P1**: `ancestors()` returns goals+PRD chain only (`spec_graph.py:208`), never vision/BRD. Vision+BRD prepend as singletons. Digest is canonical-sorted + **shuffle-independent** (verified: shuffled nodes/edges → identical id order `['VISION','BRD','BRD-G1','BRD-G2','PRD-AUTH','PRD-AUTH-E1','PRD-AUTH-E1-S1']`). `--layers story` on a PRD root drops PRD + emits the provenance `_warning` (sorts first).
- **P3 export**: md deterministic (byte-equal x2), TOC + ordered sections + AC, content-hash stem (`render_export.py:158-168`), `--compact-mode llm` emits `<!-- COMPACT:id -->` markers only (no script summarization), `exports/` created under `docs/product/`.
- **P4 board / P5 explorer**: default `--format html`; `--format mermaid` → ascii fallback + stderr note; ascii board deterministic; explorer ascii == tree; 3 mode roots + toggle + search present; missing group field → `unassigned`.
- **P6 unify**: all 9 legacy views render with the shared head + theme toggle (`psToggleTheme` present in every view's HTML).
- **P7 docs/eval**: SKILL.md/CLAUDE.md/visualization-spec.md modified; eval scenarios [4]export [5]board [6]explorer [7]legacy-design-system present.

### Gate 2 — No regression to 9 views / scripts: PASS
- All 9 legacy views (`tree heatmap scope roadmap persona gap moscow risk delta`) render in ascii AND html.
- `render_ascii` imports `assemble_digest.LAYER_FOR_TYPE` and exposes `_filter_by_layers`/`_BOARD_*`/`_is_deferred`/`_hashable`/`_mark`/`tree` for board/explorer — all resolve.
- `visualize.py` dispatch: body views intercepted **before** the mermaid/`<pre>` branch (`visualize.py:191`) — board/explorer html is NOT a `<pre>` dump (asserted by `test_board_html_has_columns_cards_and_no_pre_or_mermaid`).
- Single-pass `substitute()` (`render_html.py:264`) is a strict improvement; round-trip tests lock the no-bleed/no-inject behavior for legacy views too.
- `--diff` CLI alias still routes to `args.snapshot` (back-compat intact).

### Gate 3 — No breaking public-contract changes: PASS
- `assemble(view, view_format, view_text, graph, lang='en')` — **unchanged** signature; token set EXTENDED only (added `viewer_head`); RAW-`footer_note` invariant preserved (`render_html.py:236-239`).
- Graph JSON shape unchanged: top-level `['edges','generated_at','nodes','parse_errors','product','risks','root_path','version']`; node/edge keys unchanged.
- `spec_graph` API additive (`ancestors()` new, mirrors `downstream()`); `downstream()` untouched.
- `visualize.py` CLI additive (`--group-by`, `--layers`, new views/formats defaults); no removed flags.

### Gate 4 — No new lint/type/syntax errors: PASS
- All 10 scripts import + `py_compile` clean.
- Every new script runs end-to-end against the fixture.

### Gate 5 — Determinism + XSS neutralization: PASS (empirically proven)
- **Determinism**: md/ascii exact-repeatable; HTML body-content deterministic modulo timestamp; digest shuffle-independent.
- **XSS (live-DOM proof via vendored libs in jsdom/bun)**: ran 8 payload classes through the actual `DOMPurify.sanitize(marked.parse(...))` chokepoint — `<script>`, `<img onerror>`, `[x](javascript:)`, `<svg onload>`, `<iframe src=js>`, `<a href=js>`, `<details ontoggle>`, `</script><script>` breakout — **0 failures**, legitimate markdown still renders. Fail-closed path (libs absent) confirmed to escape + banner, no CDN.
- **JSON-island breakout (live-DOM proof)**: a body of `</script><script>window.PWNED=1</script>` parsed in a real DOM left `window.PWNED === undefined`; the island stayed `application/json` (inert); `JSON.parse(el.textContent)` round-tripped the body verbatim.
- **Attribute sinks**: a persona named `"><script>…` reaches the client ONLY inside the inert JSON island (escaped `<\/script>`), never in a server-rendered attribute. All card metadata built client-side via `textContent`/`dataset` (board-shell.html, explorer-shell.html); the sole `innerHTML` sinks are bodies through `psRenderMarkdown`.
- **H4 symmetric gating**: legacy Mermaid views inline 0× our `psRenderMarkdown` / `marked v18` (the `DOMPurify` strings present there are Mermaid's OWN bundled copy — correctly disambiguated by keying detection on `marked v18`/`psRenderMarkdown`, exactly as the locked decision prescribes). Body views inline 0× Mermaid (no mermaid CDN, no `<div class="mermaid">`).

---

## Findings

### MED-1 — `assemble_digest.py` exceeds the plan's own <200 LOC constraint
`scripts/assemble_digest.py` is **231 lines total (181 code)**. plan.md:36 and phase-01:60 both set "each new file <200 LOC" as a hard constraint and phase-01 Risk Assessment explicitly prescribed the remedy: "**>200 LOC** → split selection-resolver / `_struct_compact` helpers." The split wasn't done. Not a functional defect — purely the file-size discipline the plan committed to. Other new files comply (render_export 193, render_board 108, render_explorer 115). Optional: extract `_resolve_targets`/`_index_artifacts`/`_find_by_type` into a small `digest_selection.py`, or accept with a note. (Repo CLAUDE.md exempts non-new modified files, so `render_html.py` at 292 and `render_ascii.py` at 394 are out of scope here.)

### LOW-1 — dead variable `dropped_target_types`
`scripts/assemble_digest.py:186` computes `dropped_target_types = sorted({...})` which is never read (the warning loop at :189 re-derives the same set inline). Remove the assignment.

### LOW-2 — misleading comment in `export-shell.html`
`assets/templates/export-shell.html:23` says `psRenderMarkdown` is "defined in the shared head". It is NOT — the shared `_viewer-head.html` deliberately omits the sanitizer (H4); `psRenderMarkdown` arrives via the `{{markdown_libs}}` block at line 19. Code is correct; the comment misstates the source and could mislead a future maintainer into thinking the head carries sanitizer code. (board-shell.html:154 and explorer-shell have accurate comments.) Fix the comment to "defined in the markdown-libs block".

### LOW-3 — plan/code naming drift: `_struct_compact` → `compact_fields`
phase-01:44 references a `_struct_compact()` helper; the implementation named it `compact_fields()` + `_struct_lines()`. Harmless (code names are clean and self-documenting); noting only so the plan isn't mistaken for a missing-function gap.

---

## Positive observations
- Security architecture is textbook: single client-side sanitize chokepoint, inert JSON data island, all metadata via DOM APIs, server-side `_escape()` + `_safe_href()` allowlist as defense-in-depth. The two enumerated sinks (JSON body channel, attribute context) are both genuinely closed — verified in a live DOM, not just by substring asserts.
- Single-pass `substitute()` is the right fix and also closes a latent pre-existing bug for the 9 legacy views; the round-trip test (`{{mermaid_js}}`/`{{footer_note}}` in content survives verbatim) is exactly the right lock.
- Symmetric payload gating keeps body views Mermaid-free and legacy views sanitizer-free — confirmed both directions, with correct handling of Mermaid's self-bundled DOMPurify.
- Determinism is real: shuffle-independence test + content-hash filename + sorted JSON island. A non-technical PO re-exporting the same spec gets a stable filename.
- Fail-closed (no CDN sanitizer) honored; offline self-containment confirmed (0 external src/href in all three body-view HTMLs).
- Test suites assert the success criteria directly (not just smoke): 3-mode toggle, not-a-`<pre>`-dump, mermaid fallback, attribute inertness, body breakout, AC presence.

---

## Unresolved questions
None blocking. One optional decision for the owner/lead:
- **MED-1**: split `assemble_digest.py` to honor the plan's <200-LOC constraint, or accept the 231-line file with a documented exception? (No functional impact either way.)
