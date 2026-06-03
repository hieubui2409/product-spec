---
phase: 7
title: "D11 micro-util consolidation"
status: pending
priority: P3
effort: "0.5d"
dependencies: []
---

# Phase 7: D11 micro-util consolidation

## Overview
Close the "shared common base" backlog item to its only honest residue. Research REFUTED the premise
(actual duplication ≈ 0 — determinism only in claude-pack, HTML/escaping only in product-spec, critique
+ claude-pack generate NO HTML). Consolidate ONLY the genuine micro-duplication; drop the rest.

## Requirements
- Functional: `_now()` (×4) and `_hashable()` (×3) live in ONE tiny shared util module the 3 skills import; behavior byte-identical to today.
- Non-functional: the shared module must be bundled by claude-pack (verify in manifest/golden test); YAGNI — no determinism/safety/design-system extraction.

## Key facts (from research)
- `_now()`: product-spec `spec_graph.py:658`, `behavioral_memory.py:70`, `judgment_cache.py:123`; critique `critique_cache_io.py:43`. Identical ISO8601 UTC.
- `_hashable()`: product-spec `spec_graph.py`, `render_ascii.py`; critique `critique_common.py`. Type-coerce unhashable → str.
- Existing shared dirs `.claude/skills/common/` (API-key helpers) + `_shared/` are NOT used by the 3 skills.
- claude-pack golden tests (`test_golden_product_spec`, `test_bundle_ships_*`) assert bundled arcnames → must include the new module.

## Architecture
- Add one small module (e.g. `.claude/skills/common/spec_utils.py` or a per-skill-shared location that claude-pack already packs) exposing `now_iso()` + `hashable()`. Decide home by what claude-pack's manifest already includes (avoid creating an unbundled import → split-brain on install).
- Replace the 7 copy sites with imports. Keep function signatures identical.

## Related Code Files
- Create: shared util module (home TBD by manifest coverage — verify before choosing)
- Modify: `spec_graph.py`, `behavioral_memory.py`, `judgment_cache.py`, `render_ascii.py` (product-spec); `critique_cache_io.py`, `critique_common.py` (critique) — swap local defs for import
- Modify: `pack.manifest.yaml` if the module's path isn't already covered
- Verify: claude-pack golden/bundle tests still assert the module ships

## Implementation Steps
> **TDD:** this is a behavior-preserving refactor — the EXISTING 50 tests are the spec. Run them green before touching anything, swap each copy site, re-run after each swap; add one tiny test asserting the bundle ships the module (step 4). No behavior change ⇒ no new behavioral tests beyond the bundling assertion.
1. Confirm the module home is inside claude-pack's bundled tree (check `pack.manifest.yaml` selection + golden tests). If not, add it to the manifest.
2. Create the module with `now_iso()` + `hashable()` (copy current impls verbatim).
3. Replace the 7 sites with imports; run each skill's tests.
4. Build a pack (dry-run) + confirm the module is in the bundle (golden test or `--dry-run` file list).
5. Drop D11's broader scope from BACKLOG (mark resolved).

## Success Criteria
- [ ] `now_iso()` + `hashable()` exist once; 7 copy sites import them; behavior unchanged.
- [ ] claude-pack bundles the module (golden/dry-run verified) — no split-brain on install.
- [ ] determinism/safety/design-system extraction explicitly NOT done (documented as closed).
- [ ] All 50 tests pass (run via venv python).

## Risk Assessment
- Risk: shared module not bundled → recipient install breaks the import. Mitigate by step 1 + step 4 verification (the whole point).
- Marginal value by design; do last, don't gold-plate. If bundling proves awkward, leaving the 7 copies is an acceptable no-op (the duplication is trivial).
