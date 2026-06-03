---
title: "Backlog C/D/E implementation — close the PO pipeline"
description: ""
status: pending
priority: P2
branch: "claude/agent-naming-conventions-cd70n"
tags: []
blockedBy: []
blocks: []
created: "2026-06-03T18:20:40.293Z"
createdBy: "ck:plan"
source: skill
---

# Backlog C/D/E implementation — close the PO pipeline

## Overview

Close the open edges of the `product-spec` → `product-spec-critique` pipeline and harden the shared
ecosystem, per backlog groups C/D/E (`BACKLOG.md`). Build order is **stabilize → close the loop →
governance/polish → widen → cleanup**: E5 (release identity) and D12 (CI gate) first so every later
feature lands on a gated, version-honest base; then E1 (the critique return-edge — biggest structural
gap); then C9/E4 (governance + brief); then E2 (discovery seed); then D11 cleanup.

Grounded by `plans/reports/research-260603-1758-backlog-cde-grounding-report.md` (codebase facts) and
`plans/reports/brainstorm-260603-1758-backlog-cde-approaches-report.md` (approaches + trade-offs).

**Excluded:** C10 (parked — awaits task-tracker choice), E3 (deferred — product not in market).

### Non-negotiable constraints (every phase)
- product-spec stays **non-technical-PO-facing** + **NO network at runtime**; **no code generation**.
- Never overwrite PO prose (`--update` flags + asks). Honor **GATE-NEVER-ASSUME** + **GATE-NO-SILENT-REVERSAL**.
- New flags must be **menu-discoverable** (no-flag menu) + plain-language. Viewers stay read-only.
- Preserve the **50 existing pytest tests** (do not break). Run scripts via `.claude/skills/.venv/bin/python3`.
- YAGNI / KISS / DRY. Frontmatter is source-of-truth; scripts handle struct, LLM judges prose.

### TDD convention (all phases — regression-safe)
Each phase follows **tests-first**: (1) write the new/failing tests that encode the phase's success
criteria, (2) confirm they fail for the right reason, (3) implement until green, (4) re-run the FULL
existing suite (50 tests) to prove no regression. Tests live in each skill's `scripts/tests/` and run
via `.claude/skills/.venv/bin/python3 -m pytest`. Phase 2 (D12 CI gate) lands first so every later
phase's red/green cycle is also enforced in CI.

### Open decisions (surface in-phase, do not block planning)
- **E1 anchoring** (Phase 3): A (artifact-id + freshness warning) default + C (manual) fallback — recommended; vs stricter B (hash-gate). **Final pick needed before Phase 3 build.**
- **E2 vs `--auto`** (Phase 6): separate flag vs prototype inside `--auto`.
- **D12 matrix** (Phase 2): 1 OS × 2 Python (recommended) vs claude-pack's 3×3.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [E5 per-skill release identity](./phase-01-e5-per-skill-release-identity.md) | Pending |
| 2 | [D12 cross-skill CI gate](./phase-02-d12-cross-skill-ci-gate.md) | Pending |
| 3 | [E1 apply-critique loop](./phase-03-e1-apply-critique-loop.md) | Pending |
| 4 | [C9 audit-trail view](./phase-04-c9-audit-trail-view.md) | Pending |
| 5 | [E4 stakeholder brief mode](./phase-05-e4-stakeholder-brief-mode.md) | Pending |
| 6 | [E2 discovery seed](./phase-06-e2-discovery-seed.md) | Pending |
| 7 | [D11 micro-util consolidation](./phase-07-d11-micro-util-consolidation.md) | Pending |

## Dependencies

**Intra-plan ordering** (soft — phases are independently shippable, ordered by risk-reduction):
- Phase 2 (D12 CI gate) SHOULD precede Phases 3–7 so new code lands on an automated gate.
- Phase 5 (E4 release-notes flavor) depends on Phase 4 (C9 trail) only for that flavor; exec one-pager can ship without it.
- All other phases are independent.

**Cross-plan:** none. Prior plans (`260528-…product-spec-skill`, `260602-…spec-critique-*`, `260529-…claude-pack-skill`, etc.) are shipped features this plan extends; no blocking relationship.
