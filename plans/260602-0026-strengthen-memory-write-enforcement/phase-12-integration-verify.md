---
phase: 12
title: "integration-verify"
status: completed
priority: P1
effort: "3h"
dependencies: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
---

# Phase 12: integration-verify

## Overview
Final gate: prove the whole change is green + side-effect-free. Full pytest suite, claude-pack tests, the byte-invariant
of the claude-pack marker block in CLAUDE.md, a pack dry-run confirming the agent bundles, and a `check_fence` clean
sweep. No new feature code — verification + remediation only.

## Requirements
- Functional:
  - `pytest` product-spec suite green (prior 477 + all new tests from P2/3/4/5/7/9) — no regression.
  - claude-pack pytest green (docstring/manifest changes don't break it).
  - CLAUDE.md `cleanmatic:claude-pack` BEGIN/END block **byte-unchanged** vs the pre-plan baseline (awk-extract + diff).
  - `python -m pack --dry-run` lists `.claude/agents/memory-harvester.md` AND `.claude/hooks/memory_gap_hook.py`; bundle
    still deterministic.
  - `check_fence` over the working tree: no unexpected writes outside `docs/product/`.
  - Cross-ref sweep: every new flag/script/agent referenced in CLAUDE.md/SKILL.md/GUIDE/refs resolves.
  - Doc-placement honored: CLAUDE.md only gained terse pointers (size delta sane).
  - **OUTCOME validation (validate V1):** add 1–2 scenarios to the existing `eval/` harness exercising the new mechanism
    end-to-end (e.g. a surfaced contradiction → DEC recorded; a fence breach → 3E slip recorded; a re-validate of an
    unchanged spec → 0 re-judges). Plus a short **dogfood checklist** (run product-spec on `examples/acme-shop`: trigger
    each forcing-function + the hook nudge + `--reflect`). HONEST: write-rate is LLM-behavioral — eval + dogfood validate
    the outcome; pytest only validates the mechanism.
- Non-functional: deterministic; reproducible.

## Architecture
Verification harness (pytest + grep/awk + pack dry-run). Mirrors the prior plan's verify phase + the byte-invariant
check used in the review round.

## Related Code Files
- Read/verify only: all files touched by P2–P11; `CLAUDE.md` marker block; `pack.manifest.yaml`
- Create (optional): `plans/260602-0026-strengthen-memory-write-enforcement/reports/integration-verify-report.md`

## Implementation Steps
1. Run product-spec pytest + claude-pack pytest; fix any regression (route back to the owning phase).
2. Byte-invariant: awk-extract the claude-pack block from HEAD vs working CLAUDE.md → `diff -q` → identical.
3. `python -m pack --dry-run` → confirm harvester agent in the file set; confirm determinism.
4. `check_fence` clean; cross-ref sweep resolves; CLAUDE.md size delta is pointers-only.
5. Whole-plan consistency: re-read plan + phases, reconcile any drift before declaring done.

## Success Criteria
- [ ] product-spec + claude-pack suites green; no regression.
- [ ] claude-pack marker block byte-unchanged in CLAUDE.md.
- [ ] pack dry-run includes `memory-harvester.md`; bundle deterministic.
- [ ] `check_fence` clean; all cross-refs resolve; CLAUDE.md stayed terse.

## Risk Assessment
- A regression here routes back to the OWNING phase (file-ownership matrix) — never patch outside ownership.
- Byte-invariant failure → revert the offending CLAUDE.md edit (must be above the marker only).
