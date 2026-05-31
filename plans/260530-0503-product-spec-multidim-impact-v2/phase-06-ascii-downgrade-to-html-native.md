---
phase: 6
title: "ASCII Downgrade to HTML-native"
status: pending
priority: P2
effort: "1d"
dependencies: [5]
---

# Phase 6: ASCII Downgrade to HTML-native

# (PO decision §0.2 — DOWNGRADE, not removal)

## Overview

Make **HTML-native the new default** for the rich multi-dimensional + matrix views, add the HTML-only multi-dim **dashboard**, and **simplify** (not delete) the heavy ASCII graph-art into a **minimal text-summary tree** that keeps the zero-dependency terminal/CI path alive. This reverses the earlier "remove all ASCII" idea (report §0.2): no large breaking change, ASCII value preserved → risk LOW.

## Key Insights (grounded)

- `visualize.py:219` currently defaults graph views to `ascii`; body views (`board`/`explorer`) default `html`.
- `render_ascii.py` is 20.8K — much of it is heavy graph-art that Mermaid/HTML render better. We **gut the heavy art**, keep a compact text-summary tree (node/finding counts + indented structure) for terminal/CI.
- `test_visualize.py` asserts exact ASCII text — we **keep the tree-text asserts** (G-G2 / determinism) and rewrite only the asserts tied to the removed heavy art.
- Matrix/heatmap/risk-grid don't express cleanly in Mermaid (grounded #10 + Q44) → those are HTML-native tables already targeted in Phases 2/4.

## Requirements

- **Functional:** HTML-native = default for `risk` grid, `competition` matrix/heatmap, and the new `dashboard` (HTML-only, Q65); ASCII retained as a minimal text-summary tree for `tree`/`roadmap`/CI; `board`/`explorer` keep a text-summary fallback (NOT removed — §0.2 reverses Q45).
- **Non-functional:** zero-dep terminal path still works; determinism preserved on the retained text-summary; no CDN reached for body views (fail-closed unchanged).

## Architecture

```
spec_graph JSON → visualize.py dispatcher
  ├── HTML-native (default): risk-grid, parity matrix, threat heatmap, dashboard (multi-dim)
  ├── Mermaid: tree, roadmap, gantt, gap, delta (unchanged)
  └── ASCII (text-summary, retained): compact structure + counts for terminal/CI
```

- **Dashboard (new, HTML-only):** one page combining risk grid + roadmap/deadline + parity matrix + threat heatmap, sharing the single `_viewer-head.html` design system.
- **Default shift:** `visualize.py` default format for the multi-dim/matrix views → `html`; `tree`/`roadmap` keep `ascii` default (text-summary) so terminal users lose nothing.

### Text-summary tree format (fixed grammar so TDD RED can assert exact text — F10)

Deterministic, no art: one line per node, 2-space indent per depth, `[<type>:<id>] <title> · <status>`, sorted by ID at each level, plus a counts footer. Example:

```text
PRODUCT: Acme Shop
  [goal:BRD-G1] Increase conversion · approved
    [prd:PRD-AUTH] Authentication · review
      [epic:PRD-AUTH-E1] Login · draft
        [story:PRD-AUTH-E1-S1] Email login · draft
— 5 nodes · 1 goal · 1 prd · 1 epic · 2 stories · 0 findings
```

Sorted-by-ID → byte-deterministic; the RED test asserts this exact string. This is the contract `test_tree_text_summary_retained` locks.

## Related Code Files

- Modify: `scripts/render_ascii.py` (gut heavy graph-art; keep compact text-summary tree renderer).
- Modify: `scripts/visualize.py` (per-view default format; route `dashboard`; ensure `board`/`explorer` text-summary fallback retained).
- Modify: `scripts/render_html.py` (multi-dim `dashboard` HTML-only, reusing existing matrix/grid/heatmap builders from P2/P4).
- Modify: `scripts/render_board.py`, `scripts/render_explorer.py` (keep text-summary fallback on `--format mermaid`/no-HTML; do NOT remove).
- Modify: `scripts/tests/test_visualize.py` (keep tree-text asserts; rewrite removed-art asserts; add text-summary + dashboard asserts).
- Modify: `references/visualization-spec.md` (default-format matrix; dashboard view; "ASCII = text-summary, retained" note), `SKILL.md` + `CLAUDE.md` (viz contract wording: ASCII downgraded not removed).

## Tests First (TDD)

| Test | Scenario | Expect |
|------|----------|--------|
| `test_tree_text_summary_retained` | `--viz tree --format ascii` | compact text-summary tree (structure visible), deterministic |
| `test_html_default_for_matrix` | `--viz competition` no `--format` | defaults to HTML |
| `test_dashboard_html_only` | `--viz dashboard` | HTML; `--format mermaid` → falls back w/ note |
| `test_board_textsummary_fallback` | `--viz board --format mermaid` | text-summary (NOT removed) |
| `test_visualize_determinism` | run twice | byte-identical text-summary |
| `test_no_cdn_in_body_views` | render board HTML | inline marked/DOMPurify; fail-closed; no CDN |

## Implementation Steps

1. **RED:** rewrite `test_visualize.py` — keep tree-text asserts; add text-summary + HTML-default + dashboard + fallback-retained asserts (fail initially).
2. Slim `render_ascii.py`: replace heavy graph-art with compact text-summary tree renderer (counts + indented structure).
3. `visualize.py`: per-view default format (HTML for multi-dim/matrix/dashboard; ASCII text-summary for tree/roadmap); route `dashboard`.
4. `render_html.py`: assemble multi-dim `dashboard` (HTML-only) from existing P2/P4 builders.
5. Confirm `board`/`explorer` keep text-summary fallback.
6. Update `visualization-spec.md`, `SKILL.md`, `CLAUDE.md` wording (downgrade, not removal).
7. GREEN; determinism + no-CDN checks pass.

## Success Criteria

- [ ] G-G1 per-dim views (`time`, `competition`) + HTML-only `dashboard` render.
- [ ] G-G2 ASCII retained as minimal text-summary tree; zero-dep terminal path works; `test_visualize` tree-text asserts retained.
- [ ] G-G3 matrix/heatmap/risk-grid render HTML-native.
- [ ] G-A4 determinism on the retained text-summary; body views fail-closed (no CDN).

## Risk Assessment

- **Over-gutting render_ascii loses structural readability** → keep an explicit text-summary tree (Q46); test asserts it shows structure. LOW (was CAO before §0.2 downgrade).
- **Default-format shift surprises CLI users** → only multi-dim/matrix views shift to HTML; `tree`/`roadmap` keep ASCII default. LOW.
- **board/explorer fallback accidentally dropped** → dedicated `test_board_textsummary_fallback`. LOW.

## Goal Gates Covered

G-G1, G-G2, G-G3 (+ G-A4).
