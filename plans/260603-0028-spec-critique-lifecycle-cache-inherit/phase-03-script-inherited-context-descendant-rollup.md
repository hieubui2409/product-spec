---
phase: 3
title: "Script: inherited_context + descendant rollup"
status: completed
priority: P1
effort: "1.5d"
dependencies: [1, 2]
---

# Phase 3: Script — inherited_context + descendant rollup

## Overview

The two cross-critique directions, both as deterministic bundle keys the consolidator (P4) consumes. New module `critique_inherit.py`: classify each prior finding (from the P1 findings-index) against the current scope X by graph-relation, emit `inherited_context` (parent→child) + `descendant_rollup` (child→parent). Reuses `spec_graph.ancestors()`/`downstream()`. Lens NEVER sees these keys.

## Requirements

- Functional:
  - **Evidence-ID classification** (brainstorm table) — for each indexed finding with evidence-ID `E` vs current scope `X`:
    | relation of `E` to `X` | bucket |
    |---|---|
    | `E == X` or `E` is a descendant of `X` | repeat-offense (handled by existing consolidator plumbing; tag only) |
    | `E` is an ancestor of `X` | **inherited_context** |
    | unrelated | drop |
    Use `spec_graph.ancestors(graph, X)` (set) for the ancestor test and `downstream(graph, X)` for descendants. **Must use the `ancestors()` SET, not the single `prd`/`epic` frontmatter fields** (brainstorm warns these are intentionally single and wrong for this).
  - **`build_inherited_context(root, graph, scope, depth, fresh_only=True)`** → list of `{source: "<parent-id>@<ts>", evidence_id, severity, why, fix, dec_worthy}`, **blockers + DEC-worthy only, full text** (index already extracted these → near-free). Fresh-only: drop a finding whose evidence-ID no longer resolves in the live graph (stale parent).
    - `depth="nearest"` (default): nearest ancestor-with-fresh-critique per branch + the most recent `scope=all` critique. Stop there.
    - `depth="deep"` (`--inherit=deep`): every critiqued ancestor in the chain.
  - **`build_descendant_rollup(root, graph, scope, fresh_only=True)`** → `{critiqued_child_count, total_child_count, blocker_children: [{id, blocker_count}], verdict_line}` — bounded counts + child blockers, fresh-only. No-op (empty) when no children critiqued. Direction is UP (children → this parent).
  - **emit_bundle wiring:** add `bundle["inherited_context"]` + `bundle["descendant_rollup"]`. Both **omitted/empty when** `--no-inherit` / `--no-rollup` or preference off, and **self-no-op** when the index has nothing relevant (ON costs nothing without context — brainstorm rationale for opt-out-not-opt-in).
  - **Preferences (P-level opt-out) — REQUIRES a cross-skill registration (R2/B2):** `preferences.load()` iterates `for key in DEFAULTS:` and DROPS any key not registered, so the 3 new keys are unreadable until added to **`product-spec/scripts/preferences.py`** `DEFAULTS` + `ENUMS`:
    - `critique_inherit` → enum `{on, off}`, default `on`
    - `critique_rollup` → enum `{on, off}`, default `on`
    - `critique_inherit_depth` → enum `{nearest, deep}`, default `nearest`
    The `on/off` keys MUST be ENUM-registered (mirroring `critique_profanity`) so the existing YAML `on/off→bool` coercion (`{False:"off", True:"on"}`) maps `critique_inherit: off` back to the `"off"` token instead of leaving a bare Python `False`. This is a **product-spec** (shared) script edit — flag it in the CHANGELOG (P6) as a product-spec touch.
    Flags `--no-inherit`/`--no-rollup`/`--inherit=deep` override per-run. **Precedence:** `--no-inherit` beats `--inherit=deep` (off wins over depth); same for `--no-rollup`.
  - **Findings-index write hook:** expose `index_report_findings(root, report_ts, scope, findings)` (thin wrapper over P1 `upsert_findings`) that P4's step-6 write path calls so each new report feeds the index. Extracts evidence-ID/severity/why/fix/dec_worthy per finding.
- Non-functional:
  - `critique_inherit.py` < 200 LOC; classification is one pass over the index, O(index × graph-lookup).
  - Pure/deterministic; time injected for any ts comparison.
  - Lens-blind enforced structurally: `inherited_context`/`descendant_rollup` are top-level bundle keys; the lens-agent prompt contract (P4) explicitly says ignore them — but ALSO the bundle the lenses receive is the same object, so document that the consolidator is the only consumer (no separate lens bundle needed; the keys just exist and lenses are told to skip — matches how register prefs are consolidator-only).

## Architecture

```
critique_inherit.py (new, ~190 LOC)
├── _classify(evidence_id, scope, ancestors_set, descendants_set) -> "inherited"|"repeat"|"drop"
├── build_inherited_context(root, graph, scope, depth, fresh_only)
├── build_descendant_rollup(root, graph, scope, fresh_only)
└── index_report_findings(root, ts, scope, findings)   # write-time wrapper over critique_cache.upsert_findings

critique_scan.py (modify)
└── emit_bundle: + inherited_context, + descendant_rollup (gated by flags/prefs)
   argparse: --no-inherit / --no-rollup / --inherit {nearest,deep}
```

## Related Code Files

- Create: `.claude/skills/spec-critique/scripts/critique_inherit.py`
- Create: `.claude/skills/spec-critique/scripts/tests/test_critique_inherit.py`
- Modify: `.claude/skills/spec-critique/scripts/critique_scan.py` (emit_bundle keys + 3 flags)
- Modify: `.claude/skills/spec-critique/scripts/tests/test_critique_scan.py` (bundle-key presence/gating)
- **Modify (cross-skill, R2): `.claude/skills/product-spec/scripts/preferences.py`** — register the 3 keys in `DEFAULTS` + `ENUMS`
- Modify: `.claude/skills/product-spec/scripts/tests/` — add/extend a `preferences.load` round-trip test for the 3 new keys (incl. `on/off`→token coercion)
- Read for context: P1 `critique_cache.py` (`load_index`/`upsert_findings`), `.../product-spec/scripts/spec_graph.py` (`ancestors`, `downstream`, `build_graph`)

## Implementation Steps (TDD — tests first)

1. **Tests first** (red), `test_critique_inherit.py` using `make_proj` (valid BRD-G1/G2 ← PRD-AUTH ← E1 ← S1 chain):
   - classify: ancestor-of-X → inherited; X itself / descendant → repeat; unrelated → drop. Assert it uses the ancestor SET (seed a finding on a grandparent goal, critique the story, expect inherited).
   - inherited_context: seed index with a PRD blocker + a PRD minor; critique the child epic → only the **blocker** (and any DEC-worthy) inherited, minor dropped; `source` == `PRD-…@<ts>`.
   - fresh-only: seed an index finding whose evidence-ID was deleted from the spec → dropped.
   - depth: nearest stops at nearest critiqued ancestor + `all`; deep pulls the whole chain. Distinct expected sets.
   - descendant_rollup: seed 2 of 3 child stories with blockers in the index; critique the parent epic → `critiqued_child_count=2`, `blocker_children` lists both, no-op when zero children indexed.
   - gating: `--no-inherit` → key empty/absent; `--no-rollup` → empty; preference off mirrors flags; ON with empty index → empty (no error); `--no-inherit --inherit=deep` → off wins (precedence).
   - preferences round-trip (in product-spec test dir): write `critique_inherit: off` to `preferences.yaml`, `load()` returns the `"off"` token (NOT bare `False`, NOT dropped); unset → default `"on"`; `critique_inherit_depth: deep` round-trips.
2. **Register the 3 keys in `product-spec/preferences.py` (R2) FIRST** (DEFAULTS+ENUMS) — the inherit/rollup gating tests depend on it. Then implement `critique_inherit.py`; wire `emit_bundle` + 3 flags + preference reads.
3. Run `test_critique_inherit.py` + `test_critique_scan.py` + the product-spec `preferences` test + full module → green.

## Success Criteria

- [ ] Classification uses `spec_graph.ancestors()` SET (not single `prd`/`epic` fields) — asserted by a grandparent-inherit test.
- [ ] `inherited_context` = blockers + DEC-worthy only, full text, fresh-only, with `<parent-id>@<ts>` source.
- [ ] `descendant_rollup` = bounded child counts + blocker children, fresh-only, no-op when empty.
- [ ] The 3 preferences are registered in `product-spec/preferences.py` (DEFAULTS+ENUMS) and `load()` round-trips them (incl. `on/off`→token); without this they are silently unreadable (R2).
- [ ] `--no-inherit`/`--no-rollup`/`--inherit=deep` + matching preferences all behave; `--no-inherit` beats `--inherit=deep`; ON-with-empty-index is a clean no-op.
- [ ] `index_report_findings` upserts each finding to the P1 index (verified via a round-trip test).
- [ ] Both spec-critique modules < 200 LOC; all green; no regression in product-spec preferences tests.

## Risk Assessment

- **Risk: lens accidentally reads inherited_context (anti-anchoring breach).** Mitigation: structural — keys exist in the bundle but the P4 lens-prompt contract says ignore; add an eval (P5) that the lens findings carry no evidence-ID outside the scope subtree. The 5-reason rationale is copied into P4's reference, not here.
- **Risk: double-count — inherited finding inflating the severity tally.** Mitigation: inherited items render in a SEPARATE "Kế thừa từ cha" section with `source`, never added to `blocker/major/minor` tally. Enforced in P4 consolidator contract + P5 eval.
- **Risk: index grows unbounded.** Mitigation: last-write-wins per `(evidence_id, report_ts)`; a future prune is YAGNI. Fresh-only at read time already drops dead evidence-IDs from the OUTPUT even if the index row lingers.
- **Risk: "nhiều cha" via PRD↔goal m:n edge.** Mitigation: brainstorm confirms goal/epic rarely critiqued alone → in practice {1 PRD parent} + {1 `scope=all` prior}; `ancestors()` returns the full set so multi-parent is handled, just usually small.
