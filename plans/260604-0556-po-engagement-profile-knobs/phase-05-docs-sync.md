---
phase: 5
title: "Docs sync"
status: done
priority: P3
effort: "1.5h"
dependencies: [1, 2, 4]
---

<!-- Updated: Validation Session 1 — critique dropped from v1; removed product-spec-critique SKILL.md edit + the
     action_prompting critique-clamp doc line. Dependency on Phase 3 removed. -->


# Phase 5: Docs sync

## Overview

Keep the doc/source-of-truth surfaces consistent with the **2** new knobs. Doc-heavy repo → stale preference tables
are a real DRY hazard. One home per fact; cross-reference, don't restate.

## Requirements

- Functional: every place enumerating preferences/flags lists the 2 new keys (defaults `standard`, which skill reads).
- Non-functional: no duplicated knob→behavior tables (those live in `workflow-interview.md` / `workflow-critique.md`).

## Architecture

- `preferences.py` module docstring (canonical key catalogue) — add the 2 keys with the same rigor as `detail_level`,
  noting SEPARATE-from-`detail_level` (verbosity vs rigor). (No critique clamp note — critique deferred.)
- `CLAUDE.md` (product-spec section): note the engagement knobs + which reference owns them; add `--set` to any CLI
  mention.
- `behavioral-memory.md`: short cross-ref clarifying these are PREFERENCES (PO-confirmed), distinct from 3D voice /
  3E conduct — so future readers don't conflate them with a new behavioral store.
- product-spec `SKILL.md`: flag/CLI list += `preferences.py --set`. (product-spec-critique `SKILL.md` unchanged —
  critique deferred.)
- `GUIDE-VI.md`: brief VI note.

## Related Code Files

- Modify: `.claude/skills/product-spec/scripts/preferences.py` (docstring catalogue)
- Modify: `.claude/skills/product-spec/references/behavioral-memory.md`
- Modify: `CLAUDE.md`
- Modify: `.claude/skills/product-spec/SKILL.md`
- Modify: `.claude/skills/product-spec/GUIDE-VI.md`

## Implementation Steps

1. Update `preferences.py` docstring with the 2 keys (defaults, enums, which skill, SEPARATE-from-`detail_level`).
2. Add the cross-ref in `behavioral-memory.md` (prefs vs 3D/3E).
3. Update `CLAUDE.md` preferences/flag mention.
4. Update product-spec `SKILL.md` CLI list (`--set`).
5. Add the VI note in `GUIDE-VI.md`.
6. Grep sweep per new key name across `.claude/skills/product-spec*` — every mention consistent; no duplicated tables;
   no leftover reference to `standing_reminders` or `--reflect engagement-profile` (both cut).

## Success Criteria

- [ ] `preferences.py` docstring is the complete, accurate key catalogue (incl. the 2 new keys).
- [ ] `CLAUDE.md`, both `SKILL.md`, `behavioral-memory.md`, `GUIDE-VI.md` reference the knobs consistently.
- [ ] No duplicated knob→behavior tables; no orphan mentions of dropped features.

## Risk Assessment

- **Doc drift**: final grep for each new key name across `.claude/skills/product-spec*` to confirm consistency and
  zero orphan references to the cut features.
