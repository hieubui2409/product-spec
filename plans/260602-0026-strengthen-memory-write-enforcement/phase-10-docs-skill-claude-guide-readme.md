---
phase: 10
title: "docs-skill-claude-guide-readme"
status: completed
priority: P1
effort: "5h"
dependencies: [2, 3, 4, 5, 6, 7, 8, 9]
---

# Phase 10: docs-skill-claude-guide-readme

## Overview
Document the new surfaces under the hard doc-placement principle: `CLAUDE.md` ref-only (terse, loads per turn),
`references/*` detail (done in P6/P9), `GUIDE-EN/VI` full use-cases, `README` overview. Sole owner of CLAUDE.md +
SKILL.md + GUIDEs + README → no cross-phase doc conflict. Keep the claude-pack marker block byte-unchanged.

## Requirements
- Functional:
  - `CLAUDE.md` (ABOVE the `cleanmatic:claude-pack` BEGIN marker, byte-unchanged below): add **1-line** Workflow-Pointers
    rows for `--reflect` (→ `workflow-reflect.md`) and the memory-hook / enforcement (→ `memory-enforcement.md`); add
    `memory_gap.py` + `reflect_scan.py` to the Scripts list (one line each) and note the opt-in Stop hook handler ships at
    top-level `.claude/hooks/memory_gap_hook.py` (one line); add ONE always-on "Memory hygiene" line. NO long prose
    (token-optimized).
  - `SKILL.md`: flag rows for `--voice` and `--reflect`; install note for `--memory-hook`; keep ≤ the lean budget.
  - `GUIDE-EN.md` + `GUIDE-VI.md`: full bilingual use-case sections for `--reflect`, `--memory-hook` (opt-in enforcement),
    and the validate "Memory pass" (mirror the existing per-priority UC structure; EN/VI parity).
  - `README.md` (product-spec): 1–2 line overview (new flags + opt-in hook install note).
- Non-functional: DRY (CLAUDE.md points, GUIDE details — no duplicated prose); EN/VI parity; no §5 leaks; CLAUDE.md
  stays terse.

## Architecture
Pure docs. CLAUDE.md = pointers only; the operative detail already lives in references (P6/P9). GUIDEs carry the worked
conversations. Enforced separation = the doc-placement matrix in the locked decisions.

## Related Code Files
- Modify: `CLAUDE.md` (pointers + scripts list + hygiene line — above the frozen marker)
- Modify: `SKILL.md` (flag rows + install note)
- Modify: `GUIDE-EN.md`, `GUIDE-VI.md` (full UC, EN/VI parity)
- Modify: `README.md` (overview)
- Read for context: the final behavior from P2–P9; existing CLAUDE.md/SKILL.md structure + the GUIDE per-priority format

## Verification (structural)
- CLAUDE.md: claude-pack marker block byte-identical to pre-edit (awk-extract + diff); new content is 1-line pointers only.
- Cross-ref: every CLAUDE.md/SKILL.md pointer resolves to a real reference/flag/script.
- GUIDE EN/VI parity: `--reflect`/`--memory-hook`/Memory-pass UC present in BOTH; section counts match.
- §5: no plan-phase/finding-code leaks.

## Implementation Steps
1. Edit CLAUDE.md (terse pointers + scripts list + hygiene line) — verify marker block byte-unchanged.
2. Edit SKILL.md (flag rows + install note).
3. Add GUIDE-EN + GUIDE-VI UC sections (parity).
4. Edit README overview.
5. Run structural checks (byte-invariant, cross-ref, parity, §5).

## Success Criteria
- [ ] CLAUDE.md gains only terse pointers; claude-pack marker block byte-unchanged.
- [ ] GUIDE-EN/VI have parity UC for `--reflect` + `--memory-hook` + Memory-pass.
- [ ] All cross-refs resolve; no §5 leaks; SKILL.md stays lean.

## Risk Assessment
- CLAUDE.md bloat (loads per turn) → enforce 1-line pointers; detail goes to references/GUIDE (doc-placement matrix).
- Byte-invariant of the claude-pack block is mandatory (verified in P12 too).
