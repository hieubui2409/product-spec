# Brainstorm Design — product-spec: read-once Export + interactive Viewer

Date: 2026-05-29 · Skill: `cleanmatic:product-spec` · Status: **design approved by owner; ready for /ck:plan --hard**
Input to: implementation plan (this is the brainstorm deliverable; planner + researchers consume it).

> EN to match repo docs/references; owner converses in VI.

---

## 1. Problem statement

Two new **consume/read** capabilities on top of the existing author/validate/visualize-structure skill:

- **F1 — read-once Export**: assemble a chosen slice of the spec (one/many/all of Vision/BRD/PRD/Epic/Story) into **one self-contained doc** (md or html) so a stakeholder reads the whole context in a single pass, or it is fed to an LLM. Each layer at **full** or **compacted** verbosity.
- **F2 — interactive Viewer**: self-contained **HTML** to browse the spec as a **board** (kanban) and an **explorer** (tree / flat-tabs / table-tree), showing actual artifact **content** (not just a node-graph).

Neither exists today. Closest existing: `--summary` (LLM 1-pager, high-level — different artifact) and `--viz tree --format html` (Mermaid **structure** graph, no bodies).

## 2. Locked decisions (owner interview)

| # | Decision | Value |
|---|----------|-------|
| D1 | Scope this round | **Both F1 + F2**, on **one shared assembler** (F1 first as the base, F2 on top). |
| D2 | Selection model | **ID/all + `--layers` combined.** Root by ID or `all`, then filter by artifact type (vision/brd/prd/epic/story; 1\|many\|all). e.g. `--export PRD-AUTH --layers epic,story`. |
| D3 | "compacted" meaning | **Both modes via flag** `--compact-mode struct\|llm`. `struct` = deterministic skeleton (script). `llm` = LLM summary (workflow step, not script). |
| D4 | Default depth | `--depth context` = ancestors compacted, target + descendants full. (`full` / `brief` available.) |
| D5 | F2 home | **Two new `--viz` views: `board` + `explorer`** (reuse dispatcher; do NOT replace `tree`). |
| D6 | Explorer v1 layouts | **All three modes in one view, in-page toggle**: Tree (collapse/expand nav + content pane) · Flat-tabs · **Table-tree** (treegrid: expandable rows, metadata columns, expand-row→body inline). |
| D7 | Board grouping | `--group-by status\|horizon\|moscow` (default `status`); cards = artifacts. |
| D8 | HTML body rendering | **marked.js + DOMPurify**, both vendored + inlined. Pipeline: `marked(md)` → `DOMPurify.sanitize(html)` → inject. (Owner chose this over zero-dep; it is the industry-standard sanitize combo.) |
| D9 | Search/filter (viewer) | **Text search + facet filters** (status/moscow/persona/layer), client-side JS, no server. board + explorer. |
| D10 | "PDF" | **Print-CSS** (`@media print`) → browser **Save-as-PDF**. No PDF binary, no JS PDF lib (honors stdlib+pyyaml + no-network constraint). |
| D11 | Threat model | Exports are **shared with team** + specs often hold **pasted external text** → cross-user stored-XSS is real → sanitize (D8) is justified, but no CSP/sandbox gymnastics (YAGNI). |

## 3. Architecture — one assembler, multiple front-ends (DRY)

```
                         spec_graph.build_graph (existing)
                                   │  + new ancestors(id)  + downstream(id) [existing]
                                   ▼
                 assemble_digest.py  ──►  DIGEST MODEL (ordered)
                 (select + --layers + depth)   [{node, role: ancestor|target|descendant,
                  deterministic full/struct      verbosity: full|struct, frontmatter, body}]
                                   │
            ┌──────────────────────┼───────────────────────┐
            ▼                      ▼                       ▼
   render_export.py        render_board.py         render_explorer.py
   (F1: md / html doc)     (F2: --viz board)       (F2: --viz explorer, 3 modes)
            │                      └───────────┬───────────┘
            │                                  ▼
            └────────────► shared HTML body render (render_html.py):
                           marked + DOMPurify inline · print-CSS · search/filter JS
```

- **Assembler** is deterministic for `full` + `struct` (testable). `llm` compaction = the orchestrating LLM post-processes the full digest per `workflow-export.md` (keeps Script-vs-LLM split clean).
- Ancestors walked via edges (`from→to`); descendants via existing `downstream()`; bodies via existing `load_artifacts()`.

## 4. F1 — Export spec

- **CLI (skill flag):** `--export <select>` where `<select>` = `all` | `<ID>` | comma-list. Modifiers: `--layers <types>` · `--depth context|full|brief` (default `context`) · `--compact-mode struct|llm` (default `struct`) · `--format md|html` (default `md`).
- **Script entry:** `render_export.py` has its own `main()` (it is not a `--viz` view).
- **Output:** `docs/product/exports/<select>-<ts>.md|html` — TOC + provenance frontmatter + layers in hierarchy order (Vision→BRD→PRD→Epic→Story, AC included on stories).
- **md** = deterministic. **html** = marked+DOMPurify render + `@media print` for Save-as-PDF.

## 5. F2 — Viewer (two new `--viz` views)

- `--viz board [--group-by status|horizon|moscow] [--layers …]` — columns = group values, cards = artifacts (ID + title + key fields), click card → sanitized body. ascii fallback = grouped lists.
- `--viz explorer [--layers …]` — single self-contained page, in-page mode switch:
  - **Tree**: collapsible nav + content pane.
  - **Flat-tabs**: tabs (per layer or per node) + content pane.
  - **Table-tree**: treegrid; rows indented by hierarchy, expand/collapse rows, columns = status/moscow/horizon/owner/AC-count; expand row → body inline.
  - ascii fallback = existing `tree`.
- Both: client-side **search box + facet filters** over an embedded JSON dataset; **no Mermaid** (smaller files); print-CSS.

## 6. Touchpoints

**Create**
| File | Role |
|------|------|
| `scripts/assemble_digest.py` | shared assembler (select + `--layers` + depth → digest model; deterministic full/struct) |
| `scripts/render_export.py` | F1 → one md/html doc (+ `main()` CLI for `--export`) |
| `scripts/render_board.py` | F2 `--viz board` HTML (+ascii) |
| `scripts/render_explorer.py` | F2 `--viz explorer` HTML, 3 modes (+ascii fallback) |
| `assets/templates/board-shell.html`, `explorer-shell.html`, `export-shell.html` | self-contained shells (print-CSS, search/filter JS slots) |
| `assets/vendor/marked.min.js`, `assets/vendor/purify.min.js` | vendored render+sanitize libs |
| `assets/install-vendor-markdown.sh` | one-time vendor step (mirror `install-vendor-mermaid.sh`) |
| `references/workflow-export.md` | F1 workflow incl `--compact-mode llm` LLM step |
| `scripts/tests/test_assemble_digest.py`, `test_render_export.py`, `test_render_viewer.py` | new tests |

**Modify**
| File | Change |
|------|--------|
| `scripts/spec_graph.py` | add `ancestors(graph, id)` helper (DRY; only `downstream` exists) |
| `scripts/visualize.py` | `VIEWS += ("board","explorer")`; dispatch; add `--layers`, `--group-by` args |
| `scripts/render_ascii.py` | board ascii (grouped lists); explorer ascii fallback (= tree) |
| `scripts/render_html.py` | marked+DOMPurify inline path; shared body-render helper; print-CSS; search/filter JS injection; include md-libs only for body views (skip Mermaid) |
| `SKILL.md` + repo `CLAUDE.md` | +flags (`--export`,`--layers`), +views (board/explorer), +output `exports/` |
| `references/visualization-spec.md` | +2 views in matrix, +layer-filter, +search/filter, +print-CSS |
| `install.sh` | call `install-vendor-markdown.sh` |
| `scripts/tests/test_visualize.py` | +board/explorer tests |

Module rule: each new file < 200 LOC (repo rule); split renderer vs assembler.
Skill-creator conventions to honor: SKILL.md flag table + load-on-demand references + `assets/vendor` + install.sh vendor step + `eval/` + tests.

## 7. Out-of-scope v1

- ❌ **Permanent**: live-reload / server / file-watch; **edit-from-viewer** (read-only).
- Deferred / not done: real PDF binary (use print-CSS); SVG/PNG (already dropped); transitive `_shared` discovery; multi-product in one export; viewer beyond search/filter+toggle.
- `--compact-mode llm` summarization is an **LLM workflow step**, never a script summarizer.
- board/explorer do **not** replace existing `tree` view.

## 8. Evaluated alternatives (rejected, with reason)

- **Zero-dep md→HTML converter** (my initial rec) — rejected by owner in favor of marked+DOMPurify (richer, standard sanitizer). Accepted.
- **Separate `--explore` CLI flag** for F2 — rejected; reuse `--viz` dispatcher (less CLI surface).
- **Three separate `--viz` views** (tree/tabs/table) — rejected; fold into one `explorer` with in-page toggle (DRY, less surface).
- **marked alone (no sanitizer)** — rejected; passes raw HTML → XSS. DOMPurify required.
- **JS PDF lib / PDF binary** — rejected; print-CSS keeps zero-dep + offline constraint.
- **LLM compaction inside the script** — rejected; violates Script-vs-LLM split + determinism/testability.

## 9. Risks + mitigations

| Risk | Mitigation |
|------|-----------|
| Stored-XSS in shared HTML (skill had 3 in Cycle 1) | marked→DOMPurify.sanitize before inject; tests with `<script>`/`onerror` payloads; sanitize is the single chokepoint. |
| Regression in existing tested files (`spec_graph`,`visualize`,`render_html`,`render_ascii`) | TDD: lock current behavior first; keep 92 tests green; add per-change tests. |
| Vendored lib size / offline | inline both libs only for body views; CDN fallback + visible warning if vendor missing (mirror Mermaid path). |
| `--layers` + ID interaction ambiguity | define precedence: ID selects subtree, `--layers` filters which types of that subtree appear; document + test. |
| Determinism (snapshots/tests) | md + ascii deterministic; html may carry timestamp but sanitized body deterministic; assert text in tests. |
| Treegrid/board complexity creep | v1 = vanilla JS only; no framework; search/filter + toggle + collapse only. |

## 10. Success criteria / acceptance

- `--export PRD-AUTH --format md` → one `.md` under `docs/product/exports/`: Vision(struct)+BRD(struct)+PRD-AUTH(full)+its epics(full)+stories(full,with AC), TOC + provenance; **deterministic** (testable).
- `--export all --depth full` → every artifact verbatim, one doc. `--layers story` → only stories.
- `--compact-mode llm` → same structure, compacted layers summarized by LLM (workflow).
- `--viz board --format html` → self-contained HTML; columns by status; cards click → sanitized body; search+facets; no network.
- `--viz explorer` → self-contained HTML; Tree/Flat-tabs/Table-tree toggle; collapse/expand; expand-row→body; search+facets; print-CSS → Save-as-PDF.
- All HTML XSS-safe (payloads neutralized). Both test suites green (claude-pack 77, product-spec 92 + new). Determinism asserted.

## 11. Next steps

1. `/ck:plan --hard` → research (md-libs vendoring/sanitize/print-CSS + skill-creator conventions/extension points) → planner → red-team → phases.
2. Implement (F1 first: assembler + export; then F2: board, explorer; then vendor + docs + tests).
3. **Ties to GOAL.md**: this is the "new product-spec feature" Cycle 3 was waiting for. After it lands, resume the 10-cycle review at Cycle 3 (new feature = primary review surface + regression sweep).

## Open questions
None blocking. All forks resolved in interview (D1–D11).
