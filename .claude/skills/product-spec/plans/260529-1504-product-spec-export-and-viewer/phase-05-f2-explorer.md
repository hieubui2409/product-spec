---
phase: 5
title: "F2 Explorer"
status: done
priority: P2
effort: "1.5d"
dependencies: [1, 2]
---

# Phase 5: F2 — `--viz explorer` (Tree / Flat-tabs / Table-tree)

## Overview

A new `--viz explorer` view: one self-contained HTML page with an **in-page mode toggle** across three layouts — **Tree** (collapsible nav + content pane), **Flat-tabs**, **Table-tree** (treegrid: expandable rows, metadata columns, expand-row→body inline) — sharing search + facet filters. ASCII fallback = the existing `tree` render.

## Requirements

- **Functional**
  - `visualize.py`: `VIEWS += ("explorer",)`; dispatch special-cases explorer **before** the mermaid/`<pre>` branch (own html writer); honors `--layers`. **`--format mermaid`** → ascii fallback (= tree) with a note, guarded like board (red-team M8). Attribute-context values (`data-*`, `aria-label`, `id`, `href`) escaped per H3.
  - <!-- Updated: Validation Session 1 --> **Default `--format` = `html`** for `--viz explorer` (ascii = explicit fallback). Mode-button / search / filter / column labels localize per `--lang` via `i18n_labels.py`.
  - `scripts/render_explorer.py` + `assets/templates/explorer-shell.html`:
    - **Tree**: `<details>/<summary>` nav (zero-JS collapse/expand) + content pane; click → sanitized body.
    - **Flat-tabs**: tabs (per layer type, or per node) + pane; optional scroll-snap.
    - **Table-tree**: semantic `<table>` treegrid; rows indented by depth; expand/collapse rows (`aria-expanded`); columns = status/moscow/horizon/owner/AC-count; expand row → inline detail row with sanitized body.
    - Mode switch buttons; **Tree is the default mode**; persist last mode to `localStorage`.
    - **Ship priority (red-team L10):** Tree + Flat-tabs are **must-ship**; Table-tree **ships if Phase-5 effort holds** (graceful degrade). Table-tree is owner-locked (D6) — do NOT cut without owner sign-off; only stage it if the phase slips.
    - Shared search box + facet filters (status/moscow/persona/layer).
  - `render_ascii.explorer(graph, ...)`: delegate to existing `tree` renderer (fallback).
- **Non-functional**: self-contained, no Mermaid, print-CSS; reuse Phase-2 design system; keep `.py` lean — push CSS/JS into `explorer-shell.html`; file <200 LOC.

## Architecture

Single page, three mode-containers toggled by buttons; one embedded `spec-data` JSON; shared render+sanitize (Phase 2). Tree = native `<details>`; tabs = buttons + panes (+scroll-snap from preview); treegrid = `<table>` + depth-padded rows + inline detail row. Reuse preview theme/stagger/overflow patterns.

## Related Code Files

- Create: `scripts/render_explorer.py`
- Create: `assets/templates/explorer-shell.html`
- Modify: `scripts/visualize.py` (`VIEWS`; dispatch explorer branch before mermaid/pre)
- Modify: `scripts/render_ascii.py` (`explorer()` → delegate to `tree()`)
- Extend: `scripts/tests/test_render_viewer.py`; explorer ASCII case in `scripts/tests/test_visualize.py`

## Implementation Steps

1. Tests first: explorer html contains all 3 mode roots + toggle controls + search; body sanitized; ascii explorer == tree output.
2. `render_ascii.explorer()` (delegate to tree).
3. `explorer-shell.html` (3 mode markup + CSS + toggle/search JS) + `render_explorer.py`.
4. Wire `visualize.py` (view + dispatch special-case).
5. Run pytest to green.

## Success Criteria

- [ ] `--viz explorer --format html` → offline self-contained.
- [ ] Toggle switches Tree / Flat-tabs / Table-tree; default Tree; persists.
- [ ] Tree collapse/expand; tabs switch; treegrid expand-row → inline sanitized body.
- [ ] Search + facets filter across modes; XSS neutralized; print-CSS present.
- [ ] `--viz explorer` ascii == tree; tests green.

## Risk Assessment

- **Dispatch regression** (same as board): explorer must intercept before `<pre>` path (`visualize.py:153-158`); test it's not a `<pre>` dump.
- **Treegrid ARIA weakness** (researcher-A Q4, W3C APG caveat) → Tree is the primary/default accessible mode; treegrid is secondary.
- **`.py` >200 LOC** → keep markup/CSS/JS in the shell template; Python only assembles tokens + JSON.
- **localStorage absent** → default to Tree, no crash.
