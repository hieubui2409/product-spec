---
phase: 3
title: "F1 Export"
status: done
priority: P1
effort: "1d"
dependencies: [1, 2]
---

# Phase 3: F1 — read-once Export (md + html)

## Overview

Assemble a digest (Phase 1) into **one self-contained doc**: deterministic markdown, or print-ready HTML via the Phase-2 substrate. Own CLI (`--export`), output under `docs/product/exports/`, plus the `workflow-export.md` reference that defines the `--compact-mode llm` LLM step.

## Requirements

- **Functional** — `scripts/render_export.py` with `main()`:
  - Args: `--root` `--export <all|ID|list>` `--layers <types>` `--depth context|full|brief` (default `context`) `--compact-mode struct|llm` (default `struct`) `--format md|html` (default `md`) `--lang en|vi`.
  - **md**: deterministic string assembly — provenance frontmatter (product, select, depth, generated_at) + TOC (anchors from IDs) + sections in hierarchy order; story sections include AC; struct sections render the compacted skeleton. Vision + BRD arrive via the **Phase-1 singleton prepend** (not graph traversal). When `--layers` drops the selected root's own type, render the assembler's provenance **warning** in the doc header (red-team H5).
  - **html**: render the same md through Phase-2 body-render into `export-shell.html` (print-CSS, embedded JSON, sanitize chokepoint).
  - Output path: `docs/product/exports/<stem>-<ts>-<hash8>.md|html` — `<stem>` = `all` | sanitized single ID | for a list: sorted IDs joined `_`, length-capped with a hashed tail; `<hash8>` = 8-char content hash (reuse the collision-free snapshot pattern, `spec_graph.py:223-226`) so same-second re-exports don't collide and identical content stays stable (red-team L11). `all` = the full spec (vision+brd+all goals+PRDs+epics+stories). Create `exports/` if absent; writes only under `docs/product/`.
  - `--compact-mode llm`: script emits the **full** digest + explicit `<!-- COMPACT:<id> -->` section markers; the LLM summarizes those sections per `references/workflow-export.md`. **Script never summarizes** (Script-vs-LLM split). <!-- Updated: Validation Session 1 --> Runs as **2 steps in one skill invocation**: skill runs the script (full+markers) then the LLM fills the COMPACT sections → one finished file. `--format html` is a **linear print-friendly doc** (TOC, no interactive nav/search — distinct from explorer); doc headings localize per `--lang` (`i18n_labels.py`).
- **Non-functional**: md+ascii deterministic (testable); file <200 LOC (split md-assembler vs html-wrapper if needed).

## Architecture

`render_export` consumes `assemble_digest.build_digest(...)`. md path = pure functions (no I/O beyond final write). html path = reuse `render_html` helpers (Phase 2) + `export-shell.html`. TOC + intra-doc anchors keyed on artifact IDs.

## Related Code Files

- Create: `scripts/render_export.py`
- Create: `assets/templates/export-shell.html`
- Create: `references/workflow-export.md` (selection model, depth presets, `--compact-mode llm` workflow, examples — incl. the `--layers`-drops-root-type warning example, H5)
- Create/extend: `scripts/tests/test_render_export.py`

## Implementation Steps

1. Tests first: fixture spec; `--export <PRD> --format md` → assert exact deterministic doc (TOC + ordered sections + AC); `--layers story` → only story sections; `--depth full` vs `context` differ as specified; html output sanitized + self-contained.
2. Implement md assembler (frontmatter + TOC + sections + struct skeleton).
3. Add `export-shell.html` + html path (reuse Phase 2).
4. Implement `main()` + argparse; output dir handling.
5. Write `workflow-export.md` (incl. the LLM-compact step + `<!-- COMPACT -->` marker contract).
6. Run pytest to green.

## Success Criteria

- [ ] `--export <ID> --format md` deterministic; matches expected (TOC, order, AC).
- [ ] `--layers` + `--depth` behave per spec; `all` works.
- [ ] html opens offline, body sanitized, print-CSS present.
- [ ] `exports/` created; nothing written outside `docs/product/`.
- [ ] `--compact-mode llm` emits markers only (no script summarization).
- [ ] Tests green.

## Risk Assessment

- **LLM-compact purity** → script only emits full + markers; tested by asserting no summarization in `struct`/`llm` script output.
- **Relative links in bodies** (`[x](./foo.md)`) → v1 renders inert/as-text; documented (researcher-A Q3).
- **ID→anchor collisions** → derive anchors from unique IDs; test.
- **Filename collisions / determinism (L11)** → content-hash suffix (snapshot pattern `spec_graph.py:223-226`); sorted-IDs stem for lists, length-capped + hashed tail.
- **H5 context-less export** → `--layers` dropping the root type is owner-locked behavior; mitigate with the header warning + a `workflow-export.md` example (do NOT change precedence without owner).
