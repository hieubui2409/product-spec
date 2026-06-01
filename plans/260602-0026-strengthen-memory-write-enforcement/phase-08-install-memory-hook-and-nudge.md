---
phase: 8
title: "install-memory-hook-and-nudge"
status: completed
priority: P2
effort: "4h"
dependencies: [7]
---

# Phase 8: install-memory-hook-and-nudge

## Overview
The opt-in install surface for the Tier-1 hook: `install.sh --memory-hook` (+ `.ps1` twin) idempotently merges the hook
entries into `.claude/settings.local.json`, and a passive ≤1/day recommend-nudge with an explicit "never". **Never
auto-registers** — capability + opt-in only.

## Requirements
- Functional:
  - `install.sh --memory-hook` / `install.ps1 -MemoryHook`: parse-JSON → check if the hook (by command+matcher) is
    already present → add `Stop` + `PostToolUse(Write|Edit)` entries only if absent → write back (idempotent; never
    string-replace; never touch the user's other hooks). Target `.claude/settings.local.json` (gitignored) by default;
    `--memory-hook-shared` opt-in for `.claude/settings.json`.
  - Recommend-nudge (SessionStart self-check OR a tiny `--check-memory-hook` the skill calls): if hook absent AND not
    opted out AND `hook-prompted-last` != today → emit ONE passive line recommending `install.sh --memory-hook`; stamp
    `hook-prompted-last=<date>`. An explicit user "stop asking" sets `hook-optout`.
  - Decline / not installed → degrade to Tier-0 (skill fully functional); one-line "enforcement off" note; no nag.
- Non-functional: idempotent; safe JSON merge (parse+reconstruct); cross-platform (.sh + .ps1); reversible (documents
  how to remove the entry).

## Architecture
A new `--memory-hook` branch in product-spec `install.sh`/`install.ps1` doing the settings merge. The nudge markers
(`hook-prompted-last`, `hook-optout`) live under `docs/product/.memory/` (project-scoped). The hook command path uses
`$CLAUDE_PROJECT_DIR` + the venv python + the top-level **`.claude/hooks/memory_gap_hook.py`** (per the locked
placement), e.g. `"$CLAUDE_PROJECT_DIR"/.claude/skills/.venv/bin/python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/memory_gap_hook.py`.

## Related Code Files
- Modify: `install.sh`, `install.ps1` (product-spec) — `--memory-hook` merge + `--check-memory-hook` nudge
- Read for context: existing `install.sh` arg parsing (`--dev`), `.claude/settings*.json` shape, P1 settings-merge findings

## Verification (script behavior — shell test or manual)
- Idempotency: run `--memory-hook` twice → settings.local.json has exactly ONE Stop + one PostToolUse entry.
- Non-destructive: a pre-existing unrelated hook in settings.local.json survives untouched.
- Default scope: writes `settings.local.json`, NOT `settings.json` (unless `--memory-hook-shared`).
- Nudge cadence: second same-day check → silent; new day → one line; after optout → silent forever.
- Degrade: with no hook registered, all Tier-0 paths still work.

## Implementation Steps
1. Add `--memory-hook` JSON-merge to `install.sh` (parse via python/venv for safe JSON), mirror in `install.ps1`.
2. Add the `--check-memory-hook` passive nudge + markers.
3. Verify idempotency + non-destructive merge + scope + cadence + degrade.

## Success Criteria
- [ ] `--memory-hook` is idempotent + non-destructive + defaults to settings.local.json.
- [ ] Nudge is ≤1/day with an explicit never; decline degrades cleanly to Tier-0.
- [ ] Hook is NEVER registered without the explicit `--memory-hook` invocation.

## Risk Assessment
- Settings corruption → parse+reconstruct JSON (never string-replace); back up before write; idempotent guard.
- Trust: NO silent/auto registration (locked). The bundled recipient installer does NOT pass `--memory-hook` (P11/INSTALL).
