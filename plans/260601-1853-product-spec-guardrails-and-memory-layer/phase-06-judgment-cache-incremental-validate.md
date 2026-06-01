---
phase: 6
title: "judgment-cache-incremental-validate"
status: done
priority: P1
effort: "9h"
dependencies: [1, 5, 8]
---

# Phase 6: judgment-cache-incremental-validate

## Overview
The leverage engine: a deterministic judgment cache (`judgments.json` + `judgment_cache.py`) that reuses LLM verdicts for unchanged nodes, turning whole-spec re-validation into O(Δ). Includes the **ruled-drift field** (PO accepted a drift → don't re-nag) and **verified-sticky**. Script owns key + staleness; LLM only produces verdicts. Depends on P1 (`body_hash` is the key) + P5 (validate-hub order).

## Requirements
- Functional:
  - `judgment_cache.py`: `--check` emits per-check stale/fresh node lists (computes key, compares cache); `--store --model-id <id>` writes a verdict; `--no-cache` bypass; `cache_version`+`model_id` stamp → mismatch = full miss.
  - **`model_id` is caller-supplied (red-team RT-4 fix — Script-vs-LLM):** the script NEVER self-detects the model (that would read non-deterministic session state). The orchestration/LLM layer passes `--model-id <id>` (it knows its own model); the script treats it as opaque data it stamps + compares. `workflow-validate.md` Step 2.9 MUST pass the current model id.
  - Key = `check | scope_key | hash(es) | lang | dep_hash`. Single-node: `scope_key=node_id`, hash=`body_hash`. `semantic_duplication`: sorted pair `(idA+idB | body_hashA+body_hashB)`. `core_value_drift`: `dep_hash=cv:<hash(PRODUCT.core_value)>`. **`contradiction`: never cached** (no entry).
  - **Ruled-drift (red-team RT-3 — CONFIRMED at validate gate):** a verdict entry carries `po_ruling_ref: DEC-n` — a **reference** (still a field in judgments.json, per the locked decision), NOT an independent `accepted` fact. `decisions.md` is the single authoritative home for the ruling. On a body change the cache entry invalidates (re-judge the content, correct) BUT the orchestration consults `decisions.md`, finds the active DEC, and **surfaces it** ("you accepted DEC-n for the prior wording — still applies?") instead of silently re-flagging. Honors DRY + no-silent-reversal; reuses the `decisions.md` plumbing P5 already wires into the Contradiction Protocol (→ dep [5]).
  - **Deletion eviction (red-team RT-cache-GC):** on `--check`/`--store`, garbage-collect entries whose keyed node id(s) are no longer in the current graph (set-difference vs graph node ids) → no dead pair-entries, no id-reuse collision.
  - **`last_validated` marker (red-team RT-5 — P6 OWNS the write):** the `--validate` flow (P6 owns the Step 2 validate-hub edit) writes `docs/product/.memory/last_validated.json` (validated snapshot filename + hash) **on `--validate` ONLY** (NOT on bare `--viz --snapshot`). P8's `--status` reads it. Write goes through P8's `fs_guard` (→ dep [8]).
  - Incremental `--validate`: orchestration consults cache BEFORE the LLM pass (judge only stale nodes), stores AFTER.
- Non-functional: deterministic key (script-only); cache is optimization, never authoritative; committed (per locked decision, monitor/evidence).

## Architecture
- `judgment_cache.py` reuses `spec_graph` nodes (`body_hash` from P1) + `PRODUCT.core_value` hash for dep. Mirrors the `*_anchors.py` script-half pattern (script emits structured staleness; LLM applies/produces verdict).
- `judgments.json` under `docs/product/.memory/`. Schema: `{cache_version, model_id, entries:{<key>:{verdict, po_ruling?, stored_at}}}`.
- `workflow-validate.md` Step 2 gains: 2.0 "ask judgment_cache `--check` for stale set per check" → LLM judges only stale → 2.9 "`--store` new verdicts". **Edits the validate hub AFTER P5** (DAG).
- Invalidate: `body_hash` or `dep_hash` change → miss; version/model mismatch → full miss.

## Related Code Files
- Create: `scripts/judgment_cache.py`, `scripts/tests/test_judgment_cache.py`
- Modify: `references/workflow-validate.md` (Step 2 incremental orchestration + verified-sticky/ruled-drift note — **last writer in the validate-hub chain after P5**)
- Read for context: `scripts/spec_graph.py` (`body_hash`), `scripts/time_realism_anchors.py` (anchor-script pattern), `references/validation-rules-spec.md` (check catalog)

## Tests (write FIRST — TDD)
1. `test_key_single_node` → key composition correct; fresh after store, stale after `body_hash` change.
2. `test_key_semantic_dup_pair_sorted` → `(idA,idB)` and `(idB,idA)` map to same key.
3. `test_core_value_drift_dep_invalidates` → changing PRODUCT.core_value → drift entries go stale.
4. `test_contradiction_never_cached` → contradiction check never reads/writes the cache.
5. `test_version_model_mismatch_full_miss` → a DIFFERENT `--model-id` on `--check` (and a bumped `cache_version`) → all stale (proves the caller-supplied model stamp actually fires).
6. `test_po_ruling_ref_surfaces_dec` → ruled-drift marker `po_ruling_ref: DEC-n` suppresses re-flag while body unchanged; on body change the entry invalidates AND the orchestration surfaces the active DEC (no silent re-flag). decisions.md is authoritative.
7. `test_no_cache_bypass` → `--no-cache` ignores cache.
8. `test_incremental_only_stale` → 1 of N nodes changed → `--check` returns only that node stale.
9. `test_deleted_node_evicted` → delete a node → its single-node + pair entries GC'd from the cache.
10. `test_last_validated_written_on_validate_only` → `--validate` writes `last_validated.json`; a bare `--viz --snapshot` does NOT.

## Implementation Steps
1. Write tests (red).
2. Implement `judgment_cache.py` (key, staleness, store, ruling, version/model stamp, `--no-cache`).
3. Wire `workflow-validate.md` Step 2 incremental orchestration (consult→judge-stale→store) + verified-sticky/ruled-drift; reconcile with P5's Contradiction wiring in the same file.
4. Tests green; full suite no regression; measure token-saving on a re-validate fixture.

## Success Criteria
- [ ] 8 tests pass; full suite green.
- [ ] Re-validate an unchanged spec → single-node checks issue 0 LLM calls (cache hit); `contradiction` still runs.
- [ ] Ruled-drift marker `po_ruling_ref: DEC-n` suppresses re-nag; on body change it surfaces the active DEC (decisions.md authoritative) rather than silently re-flagging.
- [ ] Version/model mismatch → full safe re-validate.

## Risk Assessment
- Stale verdict after model change → version/model stamp + `--no-cache` (tested).
- Validate-hub last-writer: must reconcile with P1 (Step 2.5) + P5 (Contradiction) edits — whole-file read before edit; DAG `dependencies: [1,5]`.
- `strict_gate.py` is structural-only (LLM-free) → CI never depends on cache (note, keep so).
