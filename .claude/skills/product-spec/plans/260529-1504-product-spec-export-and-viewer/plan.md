---
title: "product-spec: read-once Export + interactive Viewer (board/explorer)"
description: "Add F1 read-once Export (one md/html doc) + F2 interactive Viewer (--viz board/explorer) on a shared deterministic assembler."
status: done
priority: P2
branch: "master"
tags: [product-spec, export, visualization, html, viewer]
blockedBy: []
blocks: []
created: "2026-05-29T08:23:47.160Z"
createdBy: "ck:plan"
source: skill
---

# product-spec: read-once Export + interactive Viewer (board/explorer)

## Overview

Two **consume/read** capabilities on top of `cleanmatic:product-spec`, built on **one shared deterministic assembler** (DRY):

- **F1 — read-once Export**: assemble a spec slice (`--export <all|ID|list>` + `--layers`) into **one self-contained doc** (`md` or `html`), per-layer **full / compact**. For stakeholders / single-pass read / LLM feed.
- **F2 — interactive Viewer**: two new `--viz` views — **`board`** (kanban) + **`explorer`** (Tree / Flat-tabs / Table-tree toggle) — rendering actual artifact **bodies** (marked→DOMPurify), with client-side **search + facet filters** and **print-CSS** (Save-as-PDF).
- **Consistency**: unify **all** product-spec HTML (the existing 9 `--viz` views + board/explorer/export) under **one design system** — the `--viz explorer` UI (theme toggle, palette, typography, framing, print-CSS). DRY: one shared head, every shell includes it.

## Context

- Design (locked decisions D1–D11): `../reports/brainstorm-design-260529-1504-product-spec-export-and-viewer-report.md`
- Research (md-libs / print / vanilla-JS): `../reports/researcher-260529-1504-md-libs-print-css-vanilla-js-ui-patterns-report.md`
- Research (skill-creator conventions + 19 extension seams w/ file:line): `../reports/researcher-260529-1504-skill-creator-conventions-and-product-spec-extension-points-report.md`
- Preview-skill UI patterns mined: theme-toggle+localStorage · semantic palette · `.ve-card` depth tiers · `<details>/<summary>` · scroll-snap · stagger fade-in · print-CSS (skip preview's CDN Mermaid/Chart/Fonts — offline constraint).

## Locked stack

- Selection: `ID/all + --layers` combined. Compaction: `--compact-mode struct|llm` (struct=script deterministic; llm=LLM workflow step). Default `--depth context`.
- Render: **marked 18.0.4 (48.5KB) + DOMPurify 3.4.7 (13.7KB)**, vendored + inlined, **no CDN fallback** for these. Chokepoint: `DOMPurify.sanitize(marked.parse(md))`. "PDF" = `@media print`.
- Constraints (hard): self-contained HTML, no runtime network, Python stdlib+pyyaml only, writes only under `docs/product/`, each new file <200 LOC, board/explorer carry no Mermaid.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Foundation](./phase-01-foundation.md) | ✅ Done |
| 2 | [Vendor and HTML Body Render](./phase-02-vendor-and-html-body-render.md) | ✅ Done |
| 3 | [F1 Export](./phase-03-f1-export.md) | ✅ Done |
| 4 | [F2 Board](./phase-04-f2-board.md) | ✅ Done |
| 5 | [F2 Explorer](./phase-05-f2-explorer.md) | ✅ Done |
| 6 | [Unify existing --viz HTML to design system](./phase-06-unify-existing-viz-html-to-design-system.md) | ✅ Done |
| 7 | [Docs and Regression](./phase-07-docs-and-regression.md) | ✅ Done |

> **Implemented 2026-05-29.** Tests: product-spec **156** (was 92, +64) · claude-pack **77** + golden integration **1**, all green. Independent code-review: PASS (0 CRITICAL/HIGH; XSS neutralization proven in a live DOM). SKILL.md bumped to 1.1.0. Next: resume GOAL.md **Cycle 3** (new-feature diff = primary review surface + regression sweep).

## Dependencies

- P1 (assembler) and P2 (vendor + HTML body-render infra) are **independent** — can run in parallel.
- P3, P4, P5 each depend on **P1 + P2**.
- P6 (unify existing --viz HTML) depends on **P2 + P5** (shared design system + the explorer reference UI).
- P7 (docs + regression) depends on **P3 + P4 + P5 + P6**.
- Build order: F1 first (D1), then board, then explorer, then unify-legacy-HTML, then docs.

## Verification (every phase)

```bash
PYTHONPATH=.claude/skills/product-spec/scripts \
  .claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec/scripts/tests -q
```

- md + ascii outputs **deterministic** (assert exact text). HTML may carry a timestamp but sanitized body deterministic.
- XSS: `<script>`, `<img onerror>`, `javascript:` payloads neutralized in every HTML output.
- Gate: product-spec **92 + new** green; claude-pack **77** unbroken.

## Red-team revisions (applied)

A `--hard` adversarial pass (`../reports/red-team-260529-1504-product-spec-export-and-viewer-plan-review-report.md`) verified every seam against live code. 2 CRITICAL + HIGH/MED applied:

- **C1** (P1): Vision/BRD are NOT graph nodes (`build_nodes` nodifies only goals; vision isolated). `ancestors()` = pure edge walk (goals+PRD chain); Vision/BRD **prepended as singletons** from `load_artifacts()`. Fixture must include `vision.md`.
- **C2** (P2): `assemble()` multi-pass `str.replace` is an injection/bleed sink → **single-pass `re.sub`** (also fixes a latent bug for the 9 legacy views).
- **H3** (P2/4/5): enumerate **attribute-context** sinks (`data-*`/`aria-label`/`href`) + escape; XSS tests for attribute payloads, not only bodies.
- **H4** (P6): `test_visualize.py` is substring-based → retrofit low-risk; real bite = the `<10_000` ascii-page bound vs the new shared head; legacy views inline no marked/DOMPurify.
- **L11** (P3): export filenames use a content-hash suffix (snapshot pattern) — collision-free + deterministic.
- **L12** (P2): marked/DOMPurify **fail closed** (no CDN fallback for the sanitizer).
- **M7**: vendored libs are **committed** (`.gitignore` un-ignores `assets/**`); claude-pack packs them (+62 KB, deterministic).
- **M8** (P4/5): `board|explorer --format mermaid` → **ascii fallback** (guarded; no `AttributeError`).
- **M9** (P7): cross-skill impact bounded (substring golden, sorted-walk determinism, exports not packed); golden via `-m integration`.

Decisions on the 4 owner-facing questions (none reverse a locked decision): (1) Vision/BRD **singleton prepend** — delivers the intended "whole spec in one doc"; (2) keep `--layers` precedence (D2) **+ warning note**; (3) keep Table-tree (D6); Tree+Flat-tabs must-ship, treegrid ship-if-time; (4) mermaid-format on board/explorer → ascii fallback.

## Validation Log

### Validation Session 1 (2026-05-29)

Verification Pass **skipped** per validate-workflow guard — `## Red-team revisions` already carries live-code verification (red-team ran 38 tool-uses against source; Failed findings applied). No `[UNVERIFIED]` tags remain. Failed: 0 → eligible to implement.

Critical-question decisions (4):
1. **board/explorer default `--format` = `html`** (the other 9 `--viz` views keep `ascii` default). `--viz board`/`explorer` with no `--format` → html; ascii is an explicit fallback. → P4, P5.
2. **`--compact-mode llm` = 2 steps in ONE skill invocation**: script emits full digest + `<!-- COMPACT -->` markers → the LLM summarizes those sections in the same call → one finished file. → P3 + workflow-export.md.
3. **`--lang vi` localizes everything**: viewer UI chrome (search, filter labels, mode buttons, column headers, "unassigned") + export headings + content (best-effort VI). IDs/frontmatter keys stay EN. → P2 (labels passed localized via `i18n_labels.py`), P3, P4, P5.
4. **`--export --format html` = linear print-friendly doc** (TOC, no interactive nav/search) — distinct from explorer's interactive chrome; F1/F2 roles stay separate. → P3.

### Whole-Plan Consistency Sweep
Re-read plan.md + 7 phases after propagation. Consistent across files: Vision/BRD singleton prepend, single-pass token engine, committed vendored libs, mermaid→ascii fallback, fail-closed sanitizer; the 4 validation decisions propagated to P3/P4/P5 (markers). **Zero unresolved contradictions. Eligible to implement.**

## Ties to GOAL.md

This is the "new product-spec feature" the 10-cycle review (`/GOAL.md`) paused for. After it lands, resume at **Cycle 3** — new-feature diff = primary review surface + regression sweep.
