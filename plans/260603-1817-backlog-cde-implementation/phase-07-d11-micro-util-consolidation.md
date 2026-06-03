---
phase: 7
title: "D11 _hashable consolidation (scoped down)"
status: done
priority: P3
effort: "0.25d"
dependencies: []
---

# Phase 7: D11 — consolidate `_hashable()` only (within product-spec)

> **Scoped down after red-team (2026-06-03).** The original "shared util module for `_now()` + `_hashable()`
> across 3 skills" was rejected: `_now()` formats are **intentionally divergent** and a cross-skill
> `common/` module is **not bundlable**. PO decision: consolidate ONLY `_hashable()`, same-skill, no shared module.

## Overview
Close D11 to its one honest residue: `_hashable()` is duplicated in TWO product-spec render files with
identical impl. Merge them into one tiny local helper **inside product-spec** — no cross-skill module,
no manifest change, no bundling risk.

## What was DROPPED and why (red-team)
- **`_now()` consolidation — DROPPED.** Not identical: `spec_graph._now` emits `Z`-suffix (`spec_graph.py:658`), others emit `+00:00` (`judgment_cache.py:123` carries a comment that the divergence is *intentional*). `behavioral_memory._now` (`:70`) is a documented test monkeypatch seam. Merging would flip snapshot timestamp format → silent determinism break. Leave all `_now()` copies as-is.
- **Cross-skill `common/`/`_shared/` module — DROPPED.** `selection.py:35-44` packs by skill-name allowlist; `pack.manifest.yaml:37` `follow_shared: false` → a `common/` module would not ship → `ModuleNotFoundError` on install. `_hashable` is product-spec-internal anyway (no cross-skill need).

## Scope (corrected counts)
- `_hashable()` real sites = **2, both in product-spec**: `render_ascii.py:188`, `render_ascii_board.py:44` (NOT `spec_graph.py`/`critique_common.py` as the original plan miscounted). Both type-coerce unhashable → str, identical.

## Requirements
- Functional: one `_hashable()` helper imported by both render files; behavior byte-identical.
- Non-functional: no new shared/cross-skill module; no `pack.manifest.yaml` change; YAGNI/DRY.

## Architecture
- Place the helper in an existing product-spec module both renderers already import, or a small
  `product-spec/scripts/render_common.py` (product-spec-internal — already inside the bundled skill tree,
  so no manifest work). Replace the 2 local defs with an import. Signature unchanged.

## Related Code Files
- Create/Modify: `product-spec/scripts/render_common.py` (or reuse an existing shared render module) — single `_hashable()`
- Modify: `render_ascii.py:188`, `render_ascii_board.py:44` — swap local def for import
- Explicitly NOT touched: any `_now()` site; `pack.manifest.yaml`; `critique_common.py`; `spec_graph.py`

## Implementation Steps
> **TDD:** behavior-preserving refactor — the existing suite is the spec. Run product-spec tests green first, swap each site, re-run after each.
1. Add the single `_hashable()` helper in a product-spec-internal module.
2. Replace `render_ascii.py:188` + `render_ascii_board.py:44` defs with the import.
3. Run product-spec tests; confirm ASCII/board render output unchanged.

## Success Criteria
- [ ] `_hashable()` defined once in product-spec; both render files import it; output unchanged.
- [ ] No `_now()` site touched; no shared/cross-skill module; no manifest change.
- [ ] product-spec test suite green (run via venv python).

## Risk Assessment
- Near-zero risk; same-skill, behavior-preserving, no packaging surface. If even this proves not worth it, closing D11 entirely is acceptable — the duplication is two trivial functions.
