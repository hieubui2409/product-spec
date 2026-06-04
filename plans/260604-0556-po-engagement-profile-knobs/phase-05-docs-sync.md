---
phase: 5
title: "Docs sync"
status: pending
priority: P3
effort: "2h"
dependencies: [1, 2, 3, 4]
---

# Phase 5: Docs sync

## Overview

Keep the docs/source-of-truth surfaces consistent with the new knobs. This repo is doc-heavy; stale preference
tables are a real DRY hazard. One home per fact — cross-reference, don't restate.

## Requirements

- Functional: every place that enumerates preferences/flags lists the 3 new keys with defaults + which skill reads
  them.
- Non-functional: no duplicated knob→behavior tables (those live in `workflow-interview.md` / `workflow-critique.md`
  from Phases 2-3); docs here link to those homes.

## Architecture

- `preferences.py` module docstring (the canonical key catalogue) already lists keys — add the 3 with the same
  rigor as `detail_level` (this is the doc source-of-truth for keys).
- `CLAUDE.md` (product-spec operating guide): note the engagement-profile knobs exist + which workflow reference
  owns them.
- `behavioral-memory.md`: add a short cross-ref clarifying these knobs are PREFERENCES (PO-confirmed), distinct
  from 3D voice / 3E conduct — so future readers don't conflate them with a new behavioral store.
- `SKILL.md` (both skills): flag/CLI list += `--set` / `--add-reminder` / `--remove-reminder`.
- `GUIDE-VI.md`: brief VI note for the PO-facing audience.

## Related Code Files

- Modify: `.claude/skills/product-spec/scripts/preferences.py` (docstring catalogue)
- Modify: `.claude/skills/product-spec/references/behavioral-memory.md`
- Modify: `CLAUDE.md` (root product-spec section)
- Modify: `.claude/skills/product-spec/SKILL.md`, `.claude/skills/product-spec-critique/SKILL.md`
- Modify: `.claude/skills/product-spec/GUIDE-VI.md`

## Implementation Steps

1. Update `preferences.py` docstring with the 3 keys (defaults, enums, which skill, SEPARATE-from-`detail_level`).
2. Add the cross-ref in `behavioral-memory.md` (prefs vs 3D/3E distinction).
3. Update `CLAUDE.md` workflow-pointer / preferences mention.
4. Update both `SKILL.md` CLI/flag lists.
5. Add the VI note in `GUIDE-VI.md`.
6. Grep sweep: no contradictory/stale knob description; no duplicated behavior tables.

## Success Criteria

- [ ] `preferences.py` docstring is the complete, accurate key catalogue (incl. new 3).
- [ ] `CLAUDE.md`, both `SKILL.md`, `behavioral-memory.md`, `GUIDE-VI.md` reference the knobs consistently.
- [ ] No duplicated knob→behavior tables (single home preserved).

## Risk Assessment

- **Doc drift**: easy to forget one surface. Mitigate with a final grep for each new key name across
  `.claude/skills/product-spec*` to confirm every mention is consistent.
