---
phase: 6
title: "Unify existing --viz HTML to design system"
status: done
priority: P2
effort: "1d"
dependencies: [2, 5]
---

# Phase 6: Unify ALL product-spec HTML under one design system

## Overview

Retrofit the existing 9 `--viz` views' HTML (`tree, heatmap, scope, roadmap, persona, gap, moscow, risk, delta`) to the **shared design system** (Phase 2), using **`--viz explorer` as the reference UI**. Goal: every product-spec HTML output — the 9 legacy views + board + explorer + export — shares **one** look + UX (theme toggle, palette, typography, framing, print-CSS). **Skin only — no change to view content / graph semantics.**

## Requirements

- **Functional**
  - Extract the Phase-2 design-system head into **one shared partial** (a `render_html.py` constant or `assets/templates/_viewer-head.html`) consumed by `visual-html-shell.html` **and** the export/board/explorer shells (single source — DRY).
  - Refit `assets/templates/visual-html-shell.html` to include it: theme toggle (sun/moon + localStorage), palette tokens, typography scale, container/`.ve-card` framing, footer, `@media print`.
  - **Mermaid views**: keep the `<div class="mermaid">` + add Mermaid CSS theme-var overrides (`.mermaid .nodeLabel/.edgeLabel { color/background: var(--…) }`) so diagram text follows light/dark theme.
  - **ASCII-fallback views** (`<pre>`): apply consistent typography + card framing; keep content verbatim.
  - **Preserve the existing token contract** (`lang, title, generated_at, product_name, view, view_body, mermaid_js, footer_note`) and the RAW-`footer_note` INVARIANT in `render_html.py`; only **extend** with design-system tokens.
  - `mermaid_js` payload stays gated to Mermaid views only (don't bloat ascii-fallback views) — preserve `render_html.py:153` behavior.
- **Non-functional**: 9 views still render correct graph content; determinism preserved (Mermaid DSL + ascii body unchanged; only the timestamp varies, as today); offline; no new network.

## Architecture

One design-system partial → 4 shells (`visual-html-shell.html` + board/explorer/export). Changing the look in one place updates all (DRY). Explorer's UI is the canonical reference the legacy shell is brought up to.

## Related Code Files

- Modify: `assets/templates/visual-html-shell.html` (adopt shared head + theme toggle + print-CSS + Mermaid theme overrides)
- Modify: `scripts/render_html.py` (`assemble()` token set; include shared design-system partial for ALL views, not only body views)
- Modify: `scripts/tests/test_visualize.py` — its HTML tests are **substring/content** checks, not exact-markup (red-team H4), so changes are small; **keep** graph/body content assertions; add a "theme-toggle present" assertion. The one that bites: `test_html_ascii_fallback_view_skips_mermaid_js` asserts `len(body) < 10_000` (`test_visualize.py:259`) — the new shared head inflates every page, so keep the head lean OR raise that bound with justification.
- Possibly create: `assets/templates/_viewer-head.html` (shared head partial)

## Implementation Steps

1. Factor the Phase-2 design-system head into the shared partial.
2. Refit `visual-html-shell.html` (shared head + toggle + print + Mermaid theme-var overrides).
3. Point board/explorer/export shells at the same partial (replace any duplicated CSS).
4. Update `test_visualize.py` HTML-shell expectations (new markup) while preserving each view's graph/body content checks; add theme-toggle assertion.
5. Render all 9 views × `--format html` against `examples/`; confirm consistent look, themed diagram text, offline open.
6. `pytest` green.

## Success Criteria

- [ ] 9 legacy views + board + explorer + export share one design system (toggle, palette, typography, print-CSS).
- [ ] Mermaid diagram text follows theme (dark mode legible).
- [ ] Graph/body content of the 9 views **unchanged** (content assertions still pass).
- [ ] Determinism preserved; `mermaid_js` still gated to Mermaid views; legacy views inline NO marked/DOMPurify; ascii-fallback page within its size bound.
- [ ] `test_visualize.py` updated + green; existing non-HTML tests untouched.

## Risk Assessment

- **Test breakage is SMALL, not big (red-team H4)**: `test_visualize.py` HTML tests are substring/content-based, not exact-shell. Real bite = the `len(body) < 10_000` ascii-fallback bound (`test_visualize.py:259`) vs the new shared head → keep head lean or raise the bound deliberately.
- **Payload gating (symmetric)**: legacy graph views inline NEITHER Mermaid (unless `--format mermaid`) NOR marked/DOMPurify (never — no bodies). Add a test.
- **Mermaid hardcoded colors in dark mode** → theme-var override CSS (preview pattern).
- **Over-skinning `<pre>` views** → keep minimal, content verbatim.
- **Token-contract drift** → extend only; never remove tokens; preserve RAW-`footer_note` invariant + `_escape` discipline; the single-pass substitution (Phase 2 C2) must already be in place.
- **Scope**: skin only — NOT changing what each view computes.
