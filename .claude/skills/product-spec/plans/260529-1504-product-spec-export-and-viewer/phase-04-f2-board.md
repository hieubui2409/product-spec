---
phase: 4
title: "F2 Board"
status: done
priority: P2
effort: "1d"
dependencies: [1, 2]
---

# Phase 4: F2 — `--viz board` (kanban)

## Overview

A new `--viz board` view: a self-contained kanban HTML — columns grouped by `status|horizon|moscow`, cards = artifacts, click → sanitized body, plus client-side search + facet filters. ASCII fallback = grouped lists.

## Requirements

- **Functional**
  - `visualize.py`: `VIEWS += ("board",)`; add args `--group-by status|horizon|moscow` (default `status`) and `--layers`. **Dispatch must special-case board BEFORE the existing mermaid/`<pre>` html branch** (board is not Mermaid — it owns its html writer). **`--format mermaid`**: board has no Mermaid renderer → guard `_render_mermaid`/`_render_ascii` (`visualize.py:58` uses `getattr`, would `AttributeError`) to **fall back to the ascii board** with a one-line "mermaid not supported; showing ascii" note (board carries no Mermaid by design — red-team M8).
  - Card metadata placed into HTML attributes (`data-status`, `aria-label`, `id`) goes through `_escape()`; any `href` through the allowlist (red-team H3).
  - <!-- Updated: Validation Session 1 --> **Default `--format` = `html`** for `--viz board` (ascii = explicit fallback). UI chrome (search, filter labels, group-column headers, "unassigned") localizes per `--lang` via `i18n_labels.py`.
  - `scripts/render_board.py`: build columns from the chosen group field; card = ID + title + key fields (status/moscow/persona badges); embed bodies as JSON (Phase 2); click card → render+sanitize body into a panel. Search box + facet filters (status/moscow/persona/layer), client-side, instant (debounce for many nodes).
  - `render_ascii.board(graph, group_by, ...)`: deterministic grouped lists; `_filter_by_layers()` shared helper for `--layers`.
- **Non-functional**: self-contained, no Mermaid, print-CSS; reuse Phase-2 design system (`.ve-card` grid, palette for column/badge colors, stagger); file <200 LOC.

## Architecture

`.ve-card` grid; columns via CSS (`grid-auto-flow: column` or flex). One embedded `spec-data` JSON; vanilla `Array.filter()` + `classList.toggle()` for search/facets. Reuse `assemble_digest` (for `--layers` + bodies) and `render_html` (Phase 2 substrate) + a new `board-shell.html`.

## Related Code Files

- Create: `scripts/render_board.py`
- Create: `assets/templates/board-shell.html`
- Modify: `scripts/visualize.py` (`VIEWS` ~L32; argparse ~L125; dispatch ~L135–158 — add board branch before mermaid/pre)
- Modify: `scripts/render_ascii.py` (add `board()` + `_filter_by_layers()` helper, after existing views ~L280)
- Create/extend: `scripts/tests/test_render_viewer.py`; add board ASCII cases to `scripts/tests/test_visualize.py`

## Implementation Steps

1. Tests first: ascii board grouping deterministic per `--group-by`; html contains expected columns + cards; body sanitized; `--layers` filters cards.
2. `render_ascii.board()` + `_filter_by_layers()`.
3. `board-shell.html` + `render_board.py` (columns, cards, panel, search/facets JS).
4. Wire `visualize.py` (view + args + dispatch special-case).
5. Run pytest to green.

## Success Criteria

- [ ] `--viz board` ascii → deterministic grouped lists.
- [ ] `--viz board --format html` → offline self-contained; columns by group; card click → sanitized body; search + facets work.
- [ ] `--group-by horizon|moscow` regroup; missing field → "unassigned" column.
- [ ] `--layers` filters cards; body **and** attribute XSS payloads neutralized.
- [ ] `--viz board --format mermaid` → ascii fallback (no `AttributeError`); all 3 formats × board tested.
- [ ] Tests green; existing views unaffected.

## Risk Assessment

- **Dispatch regression**: current html branch routes non-mermaid → `<pre>` (`visualize.py:153-158`). Board must intercept **before** that or it renders as `<pre>`. Add explicit branch + test that board html is NOT a `<pre>` dump.
- **Null group field** (e.g. `horizon` unset) → bucket into "unassigned"; test.
- **Search perf** for hundreds of nodes → debounce.
