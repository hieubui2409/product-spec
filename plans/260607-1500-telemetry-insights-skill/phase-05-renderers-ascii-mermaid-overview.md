---
phase: 5
title: "Renderers: ascii + mermaid + overview"
status: complete
priority: P2
effort: "3h"
dependencies: [3]
---

# Phase 5: Renderers: ascii + mermaid + overview

## Overview

The genuine NEW gap over `com:skill-analytics` (which already does md/json/html): **ascii** (terminal one-glance) + **mermaid** (fenced charts) renderers, plus a slim **overview** that composes the key lenses into one dashboard-like view. md/json come free from the ported `formatters.py`. **No HTML** (D4 — avoids the vendored-asset / shipped-render coupling).

## Requirements
- Functional:
  - `--format ascii` — compact traffic-light-ish text tables across lenses (usage top/never-used, health error-rate, reliability, session shape). Terminal-friendly, no deps.
  - `--format mermaid` — fenced ```mermaid blocks: pie of skill usage, bar of script error-rate, bar of subagent reliability. Escaped labels; below-gate → note not chart.
  - `--format md|json` — already available via `formatters.py`; ensure every lens renders in all formats consistently.
  - `--lens all` / `--overview` — compose the lenses into one ordered report (the "dashboard-lite" the PO reads first).
- Non-functional: snapshot-testable (stable ordering); ascii/mermaid pure text, NO network, NO inlined JS, NO asset reads; <200 LOC.

## Architecture
- `telemetry_render.py`: `render_ascii(aggregate)`, `render_mermaid(aggregate)` + a thin `render_overview(aggregates)` ordering helper. md/json delegate to `formatters.py`. `analyze_telemetry.py` dispatches `--format`.
- Mermaid label-escape = tiny local function (do NOT import product-spec's, keeps F1 dead).

## Related Code Files
- Create: `.claude/skills/_shared/lib/telemetry_render.py`
- Modify: `.claude/skills/_shared/scripts/analyze_telemetry.py` (format + overview dispatch)
- Create tests: `test_render_ascii.py`, `test_render_mermaid.py`, `test_render_overview.py`
- Read for context: HA `build-unified-dashboard.py` (overview composition idea, md/json), `scan-skill-usage-and-tokens.py` `render_md`

## Implementation Steps (TDD)
1. **Test first:** ascii snapshot (above + below gate) → red; implement → green.
2. **Test:** mermaid snapshot — valid fenced syntax, escaped labels, below-gate note, NO `http(s)://`/JS (asserted) → red; implement → green.
3. **Test:** overview composes lenses in a stable order, all formats → red; implement → green.
4. Confirm md/json parity across every lens.

## Success Criteria
- [ ] ascii + mermaid + md + json all deterministic snapshots for both gate states.
- [ ] mermaid syntactically valid + escaped; output has NO network/JS/asset reads (asserted).
- [ ] `--overview` produces one ordered multi-lens report.
- [ ] No re-vendored libs; no product-spec import.

## Risk Assessment
- **Mermaid breakage** on odd skill names. Mitigation: escape + a tricky-label snapshot test.
- **Overview sprawl.** Mitigation: fixed lens order, cap per-lens rows, gate-aware.
- Resist re-adding HTML (reintroduces F1) — a future separate plan only.
