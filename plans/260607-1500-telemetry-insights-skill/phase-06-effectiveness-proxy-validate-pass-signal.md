---
phase: 6
title: "Effectiveness proxy: validate-pass signal"
status: complete
priority: P3
effort: "4h"
dependencies: [3]
---

# Phase 6: Effectiveness proxy: validate-pass signal

## Overview

The one genuine "effectiveness" signal the PO opted into: **after a `product-spec` run, did `validate` pass?** An INTERNAL-QUALITY proxy (spec well-formed) — explicitly NOT E3 market-outcome (deferred, untouched). Step 1 finds the cleanest source; only then aggregate. Lowest priority (P3) — a shrink point if the Full scope runs long.

## Requirements
- Functional:
  - Determine a deterministic validate-outcome source (decision tree below).
  - Aggregate `validate_pass_rate` over a window + last status; apply the low-volume gate.
  - Label it an internal-quality proxy with an explicit "does NOT measure market/user outcome (E3)" line.
- Non-functional: read-only; no runtime network; fail-soft.

## Architecture — source decision (Step 1)
1. **Best (VERIFIED available, 2026-06-07):** product-spec validate persists `docs/product/.memory/last_validated.json` via `judgment_cache.write_last_validated` (confirmed in `status.py:11-12`). Read this marker for the validate outcome — exact, not inferred. **Use this as the primary source.**
2. **Fallback (only if marker absent for a spec):** correlate `hook-telemetry.jsonl` — a validate-path script `exit==0` in a session that also invoked `product-spec`. Coarse (carry "approx").
3. **If neither trustworthy:** do NOT fabricate. Degrade to "not available on current data"; surface Keep/Change to the PO.
- Aggregation in `_shared/lib/lens_validate_proxy.py`; reuse the gate.

## Related Code Files
- Create: `.claude/skills/_shared/lib/lens_validate_proxy.py`
- Modify: `.claude/skills/_shared/scripts/analyze_telemetry.py` (include proxy in `--lens all`/`--overview`)
- Create test: `test_lens_validate_proxy.py`
- Read for context: product-spec validate workflow + `scripts/status.py` (does it persist a result?), `.memory/`, `docs/product/`

## Implementation Steps (TDD)
1. Confirm the `last_validated.json` schema (read one real marker under `docs/product/.memory/`) — source #1 is verified present; just pin the field names for the parser.
2. **Test first** with fixtures of the chosen source → assert pass-rate + last-status + below-gate suppression. Red.
3. Implement to green.
4. Thread into renderers (a small labelled section).

## Success Criteria
- [ ] Source chosen from real evidence (cited), not assumed.
- [ ] `validate_pass_rate` + last status correct; below-gate suppressed.
- [ ] Output labels it internal-quality + NOT E3.
- [ ] No trustworthy source → honest degrade + PO consulted (no fabricated metric).

## Risk Assessment
- **Re-opening E3 (PO-warned).** Mitigation: internal-quality only; E3 row untouched; Phase 8 records the distinction.
- **No clean source / coarse exit.** Mitigation: decision tree + honest degrade.
- **Sparse data.** Mitigation: gate applies here too.
