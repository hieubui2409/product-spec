---
phase: 8
title: "C11 assumption-rigor (strengthen lenses) + goal_without_metric"
status: done
priority: P2
effort: "0.75d"
dependencies: []
---

# Phase 8: C11 — assumption-rigor via existing lenses + `goal_without_metric`

> **Revised after Phase-8 red-team (2026-06-03).** The original "add a 5th Assumption-Destroyer lens" was
> CUT: it duplicates the existing product **Riskiest-assumption** + tech **Hidden-dependencies/assume-success**
> frameworks (gold-plating — the same DRY test that cut Scope/Security/Failure). Intent ("adapt the red-team
> assumption discipline") is met by **strengthening the existing lens prompts** — a prompt edit, zero new
> agent, no +25% cost, no consolidator/manifest rewrite. Half B (`goal_without_metric`) survives, with fixes.

## Overview
Two small, justified changes — no new lens, no new sub-agent:
- **Half A (prompt edit):** sharpen the EXISTING product/tech lens framework rows so every named assumption carries an explicit "if this is wrong → consequence" clause (the red-team assumption discipline, inside lenses that already own it).
- **Half B (deterministic check):** add `goal_without_metric` to `--validate` — the one real gap the inventory left.

## Half A — strengthen existing lenses (NO new lens)
The assumption angle is already owned (`lens-frameworks.md:16` product Riskiest-assumption; `:29,33` tech
Hidden-deps / assume-success). Edit those rows to **require an explicit failure-consequence clause**:
- Product Riskiest-assumption: finding MUST state *"unproven belief X → if wrong, Y happens"* (not just name the assumption).
- Tech Hidden-dependencies / assume-success: finding MUST name the silently-assumed system/story AND the failure when it's absent.
- This is a prompt/reference edit only. **NOT touched:** `.claude/agents/` roster, `pack.manifest.yaml`, packaging test, consolidator (N<4 stays), `--product/tech/market/craft` flag set, lens count in docs. No E1 coupling (lens-cache is lens-agnostic — A5) → `dependencies: []`.

## Half B — `goal_without_metric` (corrected)
A BRD goal whose `metrics` is empty or missing.
- **Verified gap:** spec says goal `metrics` "required, ≥1 metric slug" (`frontmatter-and-id-spec.md:84`) but nothing enforces it (`metrics` at `check_consistency.py:88` is an artifact-level `LIST_FIELDS` *type* check only). No catalog row exists.
- **Correct code anchor (A4):** goal `metrics` are populated by `spec_graph._node_from_goal:176` onto `type: goal` nodes. Implement by iterating `graph["nodes"]` for `n["type"]=="goal"` with empty/missing `metrics` — NOT beside the `LIST_FIELDS` type loop.
- **Severity `error`** (mirrors `missing_ac`) — PO decision. Because `error` would turn the shipped `broken-spec` fixture + its eval RED, this phase MUST also (B1):
  - give `broken-spec`'s goals real `metrics` (both are `metrics:[]` today, `brd.md:11-18`) so the fixture only triggers its intended findings;
  - seed a **dedicated new fixture** with a metric-less goal + its own eval entry asserting `goal_without_metric`;
  - update `evals.json` expected-findings sets accordingly (the broken-spec eval at `:30-31` asserts "exactly those issues").

## Requirements
- Functional: existing product/tech lens prompts require an explicit assumption-consequence clause; `--validate` gains `goal_without_metric` (error) over goal nodes.
- Non-functional: NO new lens/agent/flag; validate half script-only + reproducible + in `strict_gate.py`; no network.

## Related Code Files
- Modify: `product-spec-critique/references/lens-frameworks.md` (sharpen Riskiest-assumption + Hidden-deps rows)
- Modify: `product-spec/scripts/check_consistency.py` (add `goal_without_metric` over `type:goal` nodes), `product-spec/references/validation-rules-spec.md` (catalog row)
- Modify: `product-spec/scripts/tests/fixtures/broken-spec/docs/product/brd.md` (give goals real metrics)
- Create: a new metric-less-goal fixture + `product-spec/eval/evals.json` entry; update broken-spec expected set
- Explicitly NOT touched: `.claude/agents/*`, `pack.manifest.yaml`, packaging tests, consolidator, lens flags/docs

## Implementation Steps
> **TDD:** write Half-B tests FIRST (incl. the new fixture + eval), confirm fail, implement to green, re-run full suite.
1. Half A: edit the two `lens-frameworks.md` rows to require the consequence clause; no other lens surface touched.
2. Half B: implement `goal_without_metric` in `check_consistency.py` iterating `type:goal` nodes (missing/empty `metrics` → error); add the catalog row.
3. Fix fixtures/evals: real metrics on broken-spec goals; new metric-less fixture + eval; update broken-spec expected set.
4. Confirm `strict_gate.py` exits 2 on the metric-less fixture; confirm broken-spec eval passes unchanged otherwise.

## Success Criteria
- [ ] product/tech lens prompts require an explicit "assumption → consequence" clause; NO new lens/agent/flag added.
- [ ] `goal_without_metric` (error) fires on a `type:goal` node with empty/missing metrics, silent on goals with ≥1 metric, reproducible, enforced by `strict_gate.py`.
- [ ] broken-spec fixture given real metrics; new metric-less fixture + eval added; `evals.json` expected sets updated; **full suite + evals green** (no false reds from the new error).
- [ ] No `.claude/agents`/manifest/consolidator/flag/doc changes (blast radius zero beyond the listed files).

## Risk Assessment
- Risk: `error` severity breaking fixtures/evals → addressed head-on by step 3 (the whole point of B1).
- Risk: prompt edit (Half A) drifts lens voice → keep it to the consequence-clause requirement; no scope change to the lens.
- Half A duplication risk is eliminated by NOT adding a lens; the rigor lives where assumptions already belong.
