---
phase: 3
title: "Read-path dedup + regression green"
status: pending
priority: P2
effort: "1h"
dependencies: [2]
---

# Phase 3: Read-path dedup + regression green

## Overview

Switch the index read path to dedup by `finding_fingerprint` (fallback `evidence_id`). This single change
propagates correctness to BOTH consumers (inherit + rollup) since they both read through `_index_rows`. Then prove
zero regression on the full suite.

## Requirements
- Functional: `_index_rows` dedups by `finding_fingerprint or evidence_id`, keeping latest `report_ts`;
  `build_descendant_rollup` blocker_count + `build_inherited_context` candidates reflect per-finding dedup.
- Non-functional: collected passing-case count unchanged vs Phase-1 baseline.

## Architecture

`_index_rows` is the single chokepoint — both `build_inherited_context` (`_inherited_candidates`) and
`build_descendant_rollup` iterate its output. Change the dedup KEY only; keep the latest-ts tiebreak.

```python
def _index_rows(root):
    best = {}
    for entry in critique_cache.load_index(root).values():
        eid = entry.get("evidence_id")
        if not eid:
            continue
        key = entry.get("finding_fingerprint") or eid          # fingerprint-first, eid fallback
        cur = best.get(key)
        if cur is None or str(entry.get("report_ts") or "") >= str(cur.get("report_ts") or ""):
            best[key] = entry
    return list(best.values())
```

- **Line-drift (criterion 1)**: two eids, same fingerprint → one bucket → one row → rollup counts once.
- **Granularity (criterion 2)**: different fingerprints → separate buckets → preserved.
- **Legacy/fallback (criteria 4,5)**: rows without fingerprint key by eid (today's behavior); mixed old+new during
  transition may briefly co-count until the legacy row ages out — documented, acceptable.
- `build_descendant_rollup` needs NO change: it already counts per row from `_index_rows`; fewer rows → correct count.
  Verify `blocker_counts` increments once per deduped row.

## Related Code Files
- Modify: `.claude/skills/product-spec-critique/scripts/critique_inherit.py` (`_index_rows`)
- Verify (likely no change): `build_descendant_rollup`, `build_inherited_context` / `_inherited_candidates`

## Implementation Steps
1. Update `_index_rows` dedup key to `finding_fingerprint or evidence_id`.
2. Run Phase-1 read-path tests (criteria 1,2,4,5) → green.
3. Confirm `build_descendant_rollup` blocker_count test (criterion 2) green; if it over/under-counts, inspect whether
   it dedups independently (it shouldn't) — fix only if a real double-path exists.
4. Run the FULL critique suite:
   `./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec-critique/scripts/tests -q`.
5. Re-collect count (`--co -q`) and compare to Phase-1 baseline; assert all prior cases still pass (new cases added,
   none removed).
6. Cross-skill sanity: run product-spec suite too if any shared import touched (resolver imports spec_graph read-only,
   so product-spec should be unaffected) —
   `./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec/scripts/tests -q`.

## Success Criteria
- [ ] `_index_rows` dedups by fingerprint with eid fallback.
- [ ] Criteria 1,2,4,5 tests green; criteria 3 (Phase 2) still green.
- [ ] Full critique suite green; collected passing count ≥ baseline (only additions).
- [ ] product-spec suite unaffected.

## Risk Assessment
- **Transition co-count**: legacy fingerprint-less rows + new fingerprinted rows for the same logical finding briefly
  co-exist until re-critique overwrites — bounded, self-healing, documented. No migration needed.
- **Hidden second dedup path**: if `build_descendant_rollup` or `_inherited_candidates` dedups by node/eid elsewhere,
  the fix could be bypassed — Step 3 explicitly verifies the single-chokepoint assumption holds.
