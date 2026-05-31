---
phase: 5
title: "Core Scripts"
status: completed
priority: P1
effort: "8h"
dependencies: [2, 4]
---

# Phase 5: Core Scripts

## Overview
Build the Python scripts that do **deterministic, structural work only** (zero judgment): parse frontmatter, build the traceability graph, flag structural orphans/dangling links, count AC presence, check ID integrity/duplicates, render the traceability matrix, and instantiate templates. All emit JSON to stdout for the LLM layer to interpret.

## Requirements
- Functional: scripts parse `docs/product/**` per Phase 2 schema, emit findings JSON per the validation spec's schema; `generate_templates.py` instantiates Phase 4 templates with token substitution.
- Non-functional: stdlib + pyyaml + markdown only (no jinja2); cross-platform; `tests/` pytest with sample fixture docs; each script single-responsibility, < 200 lines where feasible.

## Architecture
- **Shared lib:**
  - `frontmatter_parser.py` — read a doc → `{frontmatter: dict, body: str, sections: dict}` (pyyaml).
  - `spec_graph.py` — load all artifacts under `docs/product/`, build the directed graph (story→epic→prd→brd-goal→vision) from explicit frontmatter links; expose nodes/edges + the **graph-JSON** shape reused by P6.
  - `encoding_utils.py` — copy skill-creator's UTF-8 console helper.
- **Structural checkers (JSON out, structural ONLY):**
  - `check_traceability.py` — orphans (no parent), dangling links (parent ID missing), unaddressed parents (gap-analysis inverse), nodes with no upstream goal. NO value judgment.
  - `check_consistency.py` — AC field present + non-empty + count; ID integrity; duplicate IDs; broken cross-refs. NO INVEST/vagueness (that's LLM).
  - `build_traceability_matrix.py` — render story→epic→PRD→BRD-goal→metric matrix table (markdown) + artifact/ID/status index; reuse spec_graph JSON.
- **Generator:**
  - `generate_templates.py` — given artifact type + token values, copy template from `assets/templates/`, substitute `{{tokens}}`, drop unmarked optional sections, write to correct `docs/product/...` path with next free ID.
- **CLI contract:** each script takes `--root <project-dir>` (default CWD — **M5**, no implicit-CWD scatter) + `--help`; output `{"findings": [...], "graph": {...}}` JSON; exit 0 always (findings carry severity; `--strict` gating happens in LLM/orchestration, not the script).

## Red-Team Corrections
- **VENV (C1):** run/test via repo venv `./.claude/skills/.venv/bin/python3`; install via `./.claude/skills/install.sh`.
- **ID allocator (C2):** `generate_templates.py` allocates parent-scoped IDs (per Phase 2 grammar); for `--auto` batch, allocate from one in-memory counter for the whole run and write each ID once. Test: 2 stories under 2 different PRDs → unique IDs.
- **`downstream()` query (H2):** `spec_graph.py` exposes `downstream(node_id)` (graph reachability) so delta-update can compute the "affected set". Script computes the set; it does NOT rewrite prose.
- **Snapshot emit (H4):** on validate, `spec_graph.py`/matrix writes a graph-snapshot JSON to `docs/product/visuals/.snapshots/<timestamp>.json` for diff viz.
- **Gap-analysis structural-only (H1):** `check_traceability.py` "unaddressed parent" = zero inbound edges of expected child type. No sufficiency judgment.
- **Drop unused dep (L3):** include `markdown` in requirements ONLY if a renderer/parser actually needs it; frontmatter parsing is pyyaml-only. Default: omit `markdown`.
- **Section anchors stable (L1):** scripts key off frontmatter + stable English anchors only, never localized headers.

## Related Code Files
- Create: `scripts/frontmatter_parser.py`, `scripts/spec_graph.py`, `scripts/encoding_utils.py`
- Create: `scripts/check_traceability.py`, `scripts/check_consistency.py`, `scripts/build_traceability_matrix.py`, `scripts/generate_templates.py`
- Create: `scripts/requirements.txt` (pyyaml, pytest, pytest-cov; add `markdown` only if a parser actually needs it — L3)
- Create: `scripts/tests/` (fixtures: a valid mini spec + a broken one w/ orphan+missing-AC+dup-ID)
- Read for contract: Phase 2 `frontmatter-and-id-spec.md`, `validation-rules-spec.md`; Phase 4 templates

## Implementation Steps
1. `frontmatter_parser.py` + unit tests (valid/malformed frontmatter, section extraction).
2. `spec_graph.py` — graph build + JSON serialization; tests on fixture spec (correct edges, orphan isolated).
3. `check_traceability.py` — orphan/dangling/unaddressed-parent/no-goal detection → findings JSON; tests assert exact findings on broken fixture.
4. `check_consistency.py` — AC presence count, ID integrity, dup-ID, broken-ref → findings JSON; tests.
5. `build_traceability_matrix.py` — matrix markdown + index from graph JSON; tests on fixture.
6. `generate_templates.py` — template instantiation + token substitution + optional-section drop + ID assignment; tests (generated doc parses + validates).
7. `requirements.txt`; run `install.sh` to install into shared venv; `pytest scripts/tests` all green.

## Success Criteria
- [ ] All scripts run via `~/.claude/skills/.venv/bin/python3` and emit valid JSON.
- [ ] `check_traceability`/`check_consistency` flag EXACTLY the seeded issues on the broken fixture, nothing semantic.
- [ ] `build_traceability_matrix` renders correct matrix from fixture.
- [ ] `generate_templates` produces schema-valid artifacts with correct next IDs + optional-section handling.
- [ ] `pytest scripts/tests` passes; no jinja2 dependency.

## Risk Assessment
- **Judgment leaking into scripts** (violates the split) → mitigate: code review gate — any heuristic about quality/meaning must be removed; scripts only resolve links + count + check IDs.
- **Markdown parsing brittleness** (PO hand-edits) → mitigate: tolerant parser; on parse failure emit a structured `parse_error` finding rather than crashing (frontmatter=source-of-truth, report drift not abort).
- **ID collision on concurrent generation** → mitigate: generator scans existing IDs before assigning; document single-session assumption.
