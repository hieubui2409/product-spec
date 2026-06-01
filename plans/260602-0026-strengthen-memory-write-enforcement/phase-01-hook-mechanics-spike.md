---
phase: 1
title: "hook-mechanics-spike"
status: completed
priority: P1
effort: "2h"
dependencies: []
---

# Phase 1: hook-mechanics-spike

## Overview
Verify Claude Code hook mechanics on the TARGET CC version BEFORE building the Tier-1 hook (P7). No shipped code — a
findings note that confirms or corrects the design's hook assumptions. De-risks the only part of the plan built on
external (CC) behavior.

## Requirements
- Functional: confirm, on the installed CC version, that
  - `Stop`, `PostToolUse`, `SessionStart` events exist and fire as documented;
  - a `Stop` hook can force continuation (JSON `{"ok":false,"reason":...}` or exit-2 / `{"decision":"block"}`) and the
    `reason` reaches the model;
  - `stop_hook_active` appears in the `Stop` hook stdin on a continuation (the nudge-once escape);
  - the consecutive-block cap (default 8; `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) behaves as a backstop;
  - `Stop` stdin carries `transcript_path` + `cwd`; `PostToolUse` stdin carries `tool_name`/`tool_input`/`tool_output`
    and a matcher (`Write|Edit`) works;
  - settings hook shape + merge precedence (`settings.local.json` vs `settings.json`).
- Non-functional: zero side effects on the repo; findings captured for P7/P8 to consume.

## Architecture
A throwaway local hook registered in a scratch `settings.local.json` (NOT committed) that logs its stdin to a temp file
on `Stop`/`PostToolUse`/`SessionStart`; trigger a turn, inspect the logged JSON. Cross-check against current CC docs via
the `claude-code-guide` agent / official docs.

## Related Code Files
- Create: `plans/260602-0026-strengthen-memory-write-enforcement/reports/hook-mechanics-findings.md` (findings note)
- Read for context: existing `.claude/settings*.json` (shape), prior brainstorm report §2/§9

## Implementation Steps
1. Enumerate CC version + read current hooks docs (claude-code-guide / official).
2. Register a scratch logging hook (`Stop` + `PostToolUse` matcher `Write|Edit` + `SessionStart`) in a temp settings.
3. Trigger one turn that writes a file; capture each hook's stdin JSON.
4. Confirm `Stop` block→continue + `stop_hook_active` on the second stop; confirm the 8-cap env.
5. Write findings; flag ANY deviation from the design (esp. if `stop_hook_active` / block-once behaves differently →
   P7 per-signal policy must adapt). Remove the scratch hook.

## Success Criteria
- [ ] Findings note records: events present, `Stop` block+`stop_hook_active` behavior, 8-cap, stdin fields, settings merge.
- [ ] Any deviation from the report's assumptions is called out with the required P7 adaptation.
- [ ] No scratch hook / temp settings left in the repo.

## Risk Assessment
- CC version lacks an assumed event/field → P7 falls back (e.g., nudge-only via `additionalContext`, or `PostToolUse`
  `decision:block`); spike MUST surface this before P7 starts. Gate: P7 `dependencies: [1]`.
