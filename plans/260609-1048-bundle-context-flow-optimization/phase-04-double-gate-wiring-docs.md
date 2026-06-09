---
phase: 4
title: "Double-gate wiring + docs"
status: completed
priority: P2
effort: "0.5d"
dependencies: [1, 2, 3]
---

# Phase 4: Double-gate wiring + docs

## Overview

Close the loop: make the gate (harness Δ + co-presence + the Phase-2 reasoning protocol) a repeatable
check, record the before/after savings, and update docs/version. The deliverable is a reproducible "did
we cut SKILL.md tokens without hurting routing/reasoning?" guard plus an honest savings report.
(SKILL.md compaction is the only edited surface this round.)

## Requirements

- Functional:
  - Wire `context_footprint.py --compare baseline.json --gate` (incl. the **co-presence check**) into the
    repo's check surface (a make target / a line in the test/CI doc) so a future edit that regrows
    SKILL.md or orphans a GATE is caught.
  - Refresh the **baseline JSON** to the post-optimization state and record the per-skill SKILL.md
    before/after deltas (Δtokens, Δ%) + which reasoning-proof path (ii/ii′) was used, in the plan's
    `EVIDENCE`/report.
  - `BACKLOG.md`: note the flow-optimization round done; cross-reference the brainstorm.
  - **Version:** bump `product-spec` (+ `product-spec-critique` if its SKILL.md/refs changed)
    `metadata.version` + each CHANGELOG (keepachangelog); `verify_skill_versions.py` passes.
- Non-functional: the final state passes BOTH gates one last time (harness reduction + full pytest 658 +
  eval green); CHANGELOG matches SKILL.md version.

## Architecture

```
context_footprint.py --compare baseline.json --gate  ──► CI/check surface (regression guard)
record Δ per skill ──► plan EVIDENCE/report
bump SKILL.md version + CHANGELOG (per changed skill) ──► verify_skill_versions.py green
final: harness Δ + pytest 658 + eval green
```

## Related Code Files

- Modify: the test/CI doc or a make target (wire the `--gate` check)
- Modify: `.claude/skills/product-spec/SKILL.md` + `CHANGELOG.md` (version)
- Modify (if changed in 2-4): `.claude/skills/product-spec-critique/SKILL.md` + `CHANGELOG.md`
- Modify: `BACKLOG.md` (round noted)
- Update: the committed baseline JSON (post-optimization reference)

## Implementation Steps

1. Re-run the harness on the final tree → refresh baseline JSON; compute per-skill Δ.
2. Wire `--compare --gate` into the check surface (regression guard for future edits).
3. Record Δ + the two-proof summary in the plan EVIDENCE/report.
4. Bump version(s) + CHANGELOG for each skill whose SKILL.md/refs changed; run
   `verify_skill_versions.py`.
5. Final double-gate: harness reduction confirmed + full pytest 658 + eval green.

## Success Criteria

- [ ] `--gate` regression guard wired into the check surface.
- [ ] Per-skill before/after Δ recorded; net reduction shown for product-spec + critique.
- [ ] Version + CHANGELOG bumped for changed skills; `verify_skill_versions.py` green.
- [ ] Final: harness Δ + pytest 658 + eval all green (the NON-NEGOTIABLE proof).
- [ ] BACKLOG notes the round.

## Risk Assessment

- **Version drift fails CI** → bump SKILL.md + CHANGELOG together; verify before commit.
- **Gate too strict (blocks legit future growth)** → `--gate` compares against the committed baseline;
  a deliberate growth updates the baseline in the same change (documented).
- **Savings smaller than hoped** → report honestly; the flow-audit dedup + SKILL.md compaction are wins
  even if absolute token Δ is modest (PO set no hard %).
