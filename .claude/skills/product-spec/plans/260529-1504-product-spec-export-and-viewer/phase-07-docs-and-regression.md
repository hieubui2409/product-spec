---
phase: 7
title: "Docs and Regression"
status: done
priority: P1
effort: "0.5d"
dependencies: [3, 4, 5, 6]
---

# Phase 7: Docs sync + eval + full regression

## Overview

Make docs match the new behavior (skill-creator conventions), document the **unified HTML design system**, add eval scenarios, and run the full verification gate (determinism + XSS + both suites green). Version bump to 1.1.0.

## Requirements

- **Functional**
  - `SKILL.md`: flags table (+`--export`, `--layers`, `--group-by`), views list (+`board`, `explorer`), Output Contract (+`docs/product/exports/`), load-on-demand (+`references/workflow-export.md`), "What this skill does NOT do" (+ no live-reload/server, no edit-from-viewer, no real PDF binary — print-CSS only), note **all HTML shares one design system**, `metadata.version: "1.1.0"`.
  - repo-root `CLAUDE.md` product-spec guide: note `--export`/viewer flags, `exports/` output, board/explorer views, unified HTML look.
  - `references/visualization-spec.md`: add `board` + `explorer` rows to views + view×format matrices; document `--layers`, `--group-by`, search/facets, print-CSS, marked+DOMPurify self-containment; add an **"HTML Design System"** note (one shared head across all `--viz` html + board/explorer/export: theme toggle, palette, typography, print).
  - `eval/evals.json`: scenarios — export (md determinism), board (html columns + sanitize), explorer (3-mode + sanitize), and a legacy view (e.g. `tree`) html-consistency check.
- **Non-functional**: zero doc drift; skill-creator Part-A checklist satisfied.

## Architecture

Docs + eval + verification only. Cross-check every behavior from P1–P6 against its doc home.

## Related Code Files

- Modify: `.claude/skills/product-spec/SKILL.md`
- Modify: `/CLAUDE.md` (repo-root product-spec guide section)
- Modify: `.claude/skills/product-spec/references/visualization-spec.md`
- Modify: `.claude/skills/product-spec/eval/evals.json`

## Implementation Steps

1. Update `SKILL.md` (flags, views, output, refs, NOT-do, design-system note, version 1.1.0).
2. Update repo-root `CLAUDE.md` product-spec section.
3. Update `visualization-spec.md` (matrices + new flags + self-containment + HTML Design System note).
4. Add eval scenarios.
5. Full regression:
   ```bash
   PYTHONPATH=.claude/skills/product-spec/scripts .claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec/scripts/tests -q
   PYTHONPATH=.claude/skills/claude-pack/scripts   .claude/skills/.venv/bin/python3 -m pytest .claude/skills/claude-pack/scripts/tests -q
   # golden is @pytest.mark.integration — skipped by default; run explicitly:
   PYTHONPATH=.claude/skills/claude-pack/scripts   .claude/skills/.venv/bin/python3 -m pytest .claude/skills/claude-pack/scripts/tests -m integration -q
   ```
6. Golden render: run `--export`, `--viz board`, `--viz explorer`, and 2–3 legacy views (`tree`, `heatmap`) × html against `examples/`; confirm offline open + sanitized + consistent design + deterministic md/ascii.

## Success Criteria

- [ ] All four docs reflect actual behavior; no stale NOT-do or flag/view gaps; design-system documented.
- [ ] `SKILL.md` version = 1.1.0; skill-creator checklist satisfied.
- [ ] eval scenarios pass.
- [ ] product-spec **92 + new** green; claude-pack **77** green.
- [ ] Determinism + XSS assertions present and passing.

## Risk Assessment

- **Doc drift** (repo-root `CLAUDE.md` product-spec section forgotten) → step 2 explicit.
- **claude-pack collateral (red-team M9, bounded)**: product-spec is packed via sorted `rglob` (`pack/selection.py`) → new `scripts/*.py`, `assets/templates/*-shell.html`, and the **committed** `assets/vendor/{marked,purify}.min.js` (~62 KB) ride along deterministically; golden test is **substring-based** (no file-count/set assertion) so additions don't break it; `docs/product/exports/` lives in the PO project, **never packed**. Note the ~62 KB pack growth. Run the golden with `-m integration` (it's `@pytest.mark.integration`, skipped by default).
- **eval fixture gaps** → reuse `examples/` worked spec.
