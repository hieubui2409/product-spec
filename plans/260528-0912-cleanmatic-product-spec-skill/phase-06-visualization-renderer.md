---
phase: 6
title: "Visualization Renderer"
status: completed
priority: P2
effort: "7h"
dependencies: [5]
---

# Phase 6: Visualization Renderer

## Overview
Build the in-skill, self-contained visualization renderer that turns the graph-JSON (from Phase 5 `spec_graph.py`) into the 9 views across **3 output formats** (ASCII, Mermaid, inline-vendored HTML). Format + view selected by flag. No cross-skill dependency; HTML is a single self-contained file with Mermaid JS vendored inline. **SVG/PNG dropped (validate gate).**

## Requirements
- Functional: render traceability tree, status heatmap, scope/value map, roadmap, persona×feature coverage, gap-analysis, MoSCoW quadrant, risk matrix, delta/diff — as ASCII (terminal), Mermaid (in-markdown blocks), and interactive HTML.
- Non-functional: single source of truth = the Phase 5 graph JSON; stdlib templating (no jinja2); HTML self-contained with **Mermaid JS vendored inline** (offline, no external binary/CDN); deterministic output for testability.

## Architecture
- **`visualize.py`** — entry: `visualize.py --view <name> --format <ascii|mermaid|html> --root <dir> [--lang en|vi] [--diff <snapshot>]`. Reads graph JSON (from stdin or by invoking spec_graph), dispatches to a renderer per format.
- **Renderers (modular, one concern each):**
  - `render_ascii.py` — text tree + simple tables (heatmap/quadrant/matrix as ASCII grids). Zero deps, always available.
  - `render_mermaid.py` — emit Mermaid `graph`/`flowchart`/`quadrantChart`/`timeline` blocks for embedding into docs (valid v11 text).
  - `render_html.py` — wrap Mermaid (+ minimal vanilla JS for collapse/zoom) into one self-contained `.html` with **Mermaid JS vendored inline**; outputs to `docs/product/visuals/`.
- **View builders** map graph JSON → view model: tree, heatmap (status×node), scope/value (scope-tag + moscow), roadmap (horizon now/next/later), persona×feature (personas[] × epics/features), gap-analysis (unaddressed parents from P5), MoSCoW quadrant, risk matrix (impact×likelihood from risk frontmatter), delta/diff (compare two graph snapshots via change-log/git refs).
- **HTML (validate gate — CONFIRMED):** Mermaid JS **vendored inline** into the `.html` (self-contained, offline). No CDN, no external binary.

## Red-Team Corrections
- **Formats (validate gate):** **ASCII + Mermaid + inline-HTML for all 9 views**. SVG/PNG **dropped** — no Mermaid-CLI/external binary, keeps skill self-contained.
- **Diff snapshots (H4):** delta/diff view compares two graph-snapshot JSONs from `docs/product/visuals/.snapshots/` (written on validate, Phase 5). NO `git show` archaeology. No baseline → render "no baseline yet".
- **`--root` (M5):** `visualize.py` takes `--root` like other scripts.
- **VENV (C1):** repo venv for run/test.

## Related Code Files
- Create: `scripts/visualize.py` (dispatcher)
- Create: `scripts/render_ascii.py`, `scripts/render_mermaid.py`, `scripts/render_html.py` (no render_svg.py — dropped)
- Create: `assets/templates/visual-html-shell.html` (self-contained scaffold w/ Mermaid JS vendored inline)
- Vendor: a pinned Mermaid JS file under `assets/vendor/` for inline embedding
- Create: `scripts/tests/test_visualize.py` (fixtures → expected ASCII/Mermaid text)
- Read for contract: Phase 2 `visualization-spec.md`; Phase 5 `spec_graph.py` JSON shape

## Implementation Steps
1. Define view-model builders from graph JSON (one function per view); unit-test against fixture spec.
2. `render_ascii.py` — tree + grid renderers; deterministic; tests assert exact text.
3. `render_mermaid.py` — valid Mermaid v11 blocks per view; tests assert structure.
4. `render_html.py` + `visual-html-shell.html` + vendored Mermaid JS — self-contained file; manual browser check (offline); assert file opens + contains expected node IDs.
5. `visualize.py` dispatcher + flag parsing; wire view×format matrix; `--lang` localizes labels only.
6. Tests green; verify HTML renders in a browser with network disabled (offline self-contained check).

## Success Criteria
- [ ] `visualize.py` renders all 9 views in ASCII + Mermaid + HTML; ASCII + Mermaid deterministic and unit-tested.
- [ ] Interactive HTML is a single self-contained file under `docs/product/visuals/`, opens without a server AND offline (Mermaid JS inline).
- [ ] Format/view chosen by flag; `--lang` localizes labels, not IDs.
- [ ] Renders consume only the Phase 5 graph JSON (single source of truth).
- [ ] `pytest` green; no jinja2; no external binary (no Mermaid-CLI).

## Risk Assessment
- **HTML file weight** (inline Mermaid JS ~MB) → accept: tradeoff for offline self-containment (validate-gate decision); one vendored pinned copy reused by all HTML outputs.
- **Delta/diff needs two snapshots** → mitigate: compare two snapshot JSONs from `.snapshots/`; if no prior snapshot, degrade to "no baseline yet" message.
- **Mermaid view-type limits** (e.g. quadrant/timeline support) → mitigate: fall back to ASCII grid for views Mermaid can't express cleanly.
