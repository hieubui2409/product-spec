# Phase 06 — Reverse STANDARDIZE.md (light, doc-only)

**Item:** PO-requested (close the 2-way learning loop) · **Prio:** — · **Effort:** XS · **Status:** completed · **Depends:** 01–05 land (documents what shipped)

## Context links
- HA's own `human-analyzer/STANDARDIZE.md` (the forward direction: CM → HA) is the format to mirror.
- The two source reports (comparative-learning + blueprint) already hold the analysis; this is a thin pointer/index, not a re-derivation.

## Overview
HA documented "17 patterns mined from cleanmatic". This closes the loop: a light `STANDARDIZE.md` at CM root recording the **reverse** — patterns CM adopted *from* HA, each as `HA-source → pattern → CM application`.

## Key insights
- **Keep it thin** — doc-sprawl is a flagged anti-pattern. One table, one entry per adopted pattern (A1, A2, A3, A4, repeat-offense-polish). Link to the two reports for depth; don't duplicate them.
- Note explicitly where **CM stayed ahead / diverged**: A4 version-sync is a CM-original (HA lacks it); repeat-offense kept on the safe side of the boundary (HA's instinct-store crossed it).

## Requirements
- One file `STANDARDIZE.md` (repo root, mirroring HA's placement).
- Table columns: `Pattern | HA source | What CM adopted | Divergence / why`.
- ≤ ~60 lines. Links to the 2 reports + relevant phases.

## Related code files
**Create**
- `STANDARDIZE.md` (repo root).

**Modify**
- Optional: one-line pointer in `README.md` or `BACKLOG.md` referencing it.

## Implementation steps
1. After Phases 1–5 land, fill one row per adopted pattern with the final file locations.
2. Add divergence notes (A4 CM-original; repeat-offense boundary; A9 deferred-on-purpose).
3. Link the two 260606-1720 reports as the depth source.

## Todo
- [x] `STANDARDIZE.md` table (5 rows) — A1/A2/A3/A4/repeat-offense polish
- [x] divergence notes (A4 CM-original; repeat-offense safe-side-of-boundary; A9 deferred-on-purpose)
- [x] links to reports + phases (both 260606-1720 reports linked)
- [x] ≤60 lines check (25 lines)

## Success criteria
- A reader sees, at a glance, what CM took from HA, where it lives now, and where CM deliberately did NOT follow HA.

## Risk
- **Becoming a second backlog** → it is a *retrospective ledger of adopted patterns*, not a TODO list. Keep BACKLOG.md as the TODO home.

## Next steps
- Update BACKLOG.md "NEW" section: mark this HA-adoption work, retire N1 from the ungroomed list (already shipped).
