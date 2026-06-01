---
phase: 7
title: "stop-hook-and-noop-guard"
status: completed
priority: P1
effort: "6h"
dependencies: [1, 2]
---

# Phase 7: stop-hook-and-noop-guard

## Overview
The opt-in Tier-1 enforcement: a Python/venv `Stop` hook that runs `memory_gap` at turn-end and, per-signal, either
persists (fence) or nudges-once (others) the LLM to record what's missing. Plus a cheap `PostToolUse` no-op guard so the
hook is effectively free on turns/projects that don't touch `docs/product/`. Built ONLY after P1 confirms CC mechanics.

> **Placement (locked by PO):** the hook handler ships at **top-level `.claude/hooks/memory_gap_hook.py`** (the
> `.claude/hooks/` convention), NOT under the skill `scripts/`. It is a NEW skill-owned file added ALONGSIDE the existing
> ck-managed `.claude/hooks/*.cjs` — those are NEVER edited. The handler resolves the skill scripts dir from
> `$CLAUDE_PROJECT_DIR/.claude/skills/product-spec/scripts` and `sys.path.insert`s it to `import memory_gap` (no logic
> copy — DRY reuse of P2). The pytest (`scripts/tests/test_memory_gap_hook.py`) loads the handler via `importlib` from
> the top-level path (with a fixture `CLAUDE_PROJECT_DIR`).

## Requirements
- Functional:
  - `memory_gap_hook.py` (run via `./.claude/skills/.venv/bin/python3`): reads `Stop` stdin → `stop_hook_active` short-
    circuit for nudge-once signals → no-op guard → `memory_gap.collect` → emit block JSON or exit 0.
  - **Per-signal policy:** `fence_breach` = **persist** (block while the gap remains, relying on the 8-cap backstop);
    `validate_no_marker` + `approved_changed_no_dec` = **nudge-once** (honor `stop_hook_active`: block once with a
    "re-judge X; write the DEC if warranted, else run `memory_gap.py --ack-no-dec <id>` then stop" reason → on the
    continuation's stop, allow). The ack (red-team R2) suppresses future-turn re-nudges for the same wording.
  - **No-op guard:** a `PostToolUse` matcher `Write|Edit` writes a per-session "touched docs/product" flag; the `Stop`
    hook runs the detector only when the flag is set AND `docs/product/` exists — else exit 0 immediately.
  - block `reason` text is actionable (names the writer command) and never claims a hard guarantee.
- Non-functional: deterministic; fast no-op path; honors the 8-cap; degrades to the P1-confirmed fallback if a CC field
  is absent. The hook itself NEVER writes memory (it only nudges the LLM, who writes via the existing writers).

## Architecture
Two small scripts: `memory_gap_hook.py` (Stop) + the touched-flag writer (a tiny `PostToolUse` handler — may live in the
same file behind a `--post-tool-use` mode, or a 3-line sibling). **touched-flag = EPHEMERAL, session-keyed in the system
temp dir** (validate V2): NOT under `docs/product/`, NOT committed, no git noise, no fence needed (it is transient
session state, like `.touched-<session_id>` in `$TMPDIR`). Contrast: `no-dec-acks.json` + `last_judged.json` ARE
committed `.memory/` state (persistent, like `judgments.json`). Reuses `memory_gap` (P2).

## Related Code Files
- Create: `.claude/hooks/memory_gap_hook.py` (top-level, skill-owned — Stop hook + PostToolUse touched-flag),
  `scripts/tests/test_memory_gap_hook.py`
- Read for context: P1 findings note, `scripts/memory_gap.py`, `scripts/fs_guard.py`, prior hook stdin shapes, an
  existing ck `.claude/hooks/*.cjs` (placement only — never edit them)

## Tests (write FIRST — TDD)
1. `test_noop_when_no_docs_product` → no `docs/product/` → exit 0, no detector run.
2. `test_noop_when_flag_unset` → docs/product exists but touched-flag unset → exit 0.
3. `test_fence_breach_blocks` → fence signal → block JSON (`ok:false`/reason names the fix).
4. `test_fence_persist_ignores_stop_hook_active` → fence + `stop_hook_active:true` → STILL blocks (persist).
5. `test_nudge_once_honors_stop_hook_active` → `approved_changed_no_dec` + `stop_hook_active:true` → exit 0 (allow).
6. `test_nudge_once_blocks_first_time` → `approved_changed_no_dec` + `stop_hook_active:false` → block once.
7. `test_clean_spec_allows_stop` → no signals → exit 0.
8. `test_post_tool_use_sets_flag` → PostToolUse Write under docs/product → flag set; outside → not set.
9. `test_hook_never_writes_memory` → run hook → no `.memory/` mutation (only the touched-flag).

## Implementation Steps
1. Read P1 findings; lock the exact stdin field names + block contract.
2. Write tests (red).
3. Implement `memory_gap_hook.py` (Stop policy + PostToolUse flag).
4. Tests green; full suite no regression; manual smoke against a real `Stop` turn.

## Success Criteria
- [ ] 9 tests pass; full suite green.
- [ ] fence-breach persists (8-cap backstop); other signals nudge once (allow on `stop_hook_active`).
- [ ] No-op path is taken on non-product-spec turns; hook never writes memory.

## Risk Assessment
- Loop: nudge-once honors `stop_hook_active`; fence persist relies on the 8-cap (P1-verified) — never an infinite loop.
- If P1 found `stop_hook_active` absent/different → adapt the nudge-once mechanism per P1 findings before coding.
- False positive (`approved_changed_no_dec`) costs exactly one re-judgment (nudge-once), not a loop.
