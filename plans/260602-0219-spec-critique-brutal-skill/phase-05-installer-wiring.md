---
phase: 5
title: "Installer wiring"
status: pending
priority: P2
effort: "0.5d"
dependencies: [3]
---

# Phase 5: Installer wiring

## Overview

Make spec-critique installable: reuse the shared venv `.claude/skills/.venv` (do NOT create a new one) and add an opt-in `--critique-hook` flag that idempotently registers `spec_critique_nudge.py` into `.claude/settings.local.json` (gitignored) — with `--critique-hook-shared` targeting the committed `settings.json`. Never auto-register. Mirror product-spec's `--memory-hook` registration exactly.

## Requirements

- **Functional:** an installer for spec-critique (`install.sh` POSIX / `install.ps1` Windows) that ensures the shared venv + deps exist (reuse product-spec's bootstrap if present, else create the same shared venv), and on `--critique-hook` merges a Stop-hook entry for `spec_critique_nudge.py` into `settings.local.json` via JSON parse+merge (idempotent, basename-anchored). `--critique-hook-shared` → `settings.json`. Plain install touches no hooks.
- **Non-functional:** idempotent, cross-platform, uses literal `"$CLAUDE_PROJECT_DIR"` in the command string, recommend-and-ask posture (never silent registration). Exits non-zero only on real failure.

## Architecture

- **Decide:** standalone `spec-critique/install.{sh,ps1}` vs extending product-spec's installer with `--critique-hook`. Recommended: a thin standalone installer that **reuses** the shared venv created by product-spec (the venv is shared across skills under `.claude/skills/.venv`), so spec-critique can be packaged independently by claude-pack. If the shared venv is absent, create it identically (same Python + same `requirements.txt` deps: stdlib + pyyaml — spec-critique adds no new runtime dep).
- **Hook registration:** copy the JSON-merge block from `product-spec/install.sh` `--memory-hook` path. Anchor on the hook command basename (`spec_critique_nudge.py`) for idempotency. Settings shape:
  ```jsonc
  { "hooks": { "Stop": [ { "hooks": [ { "type": "command",
      "command": "<venv-python> \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/spec_critique_nudge.py" } ] } ] } }
  ```
- **Passive recommend (optional v1):** a `--check-critique-hook` flag for a ≤1/day nudge to opt in (mirror memory_gap_hook's recommend cadence) — keep minimal or defer.
- **claude-pack:** ensure the new skill dir + 5 agents + hook are packable (manifest opt-in). Coordinate with `pack.manifest.yaml` so the bundle ships spec-critique artifacts (test already exists: `test_bundle_ships_memory_artifacts.py` is the pattern). Add/extend a ships-test if needed.

## Related Code Files

- Create: `.claude/skills/spec-critique/install.sh`
- Create: `.claude/skills/spec-critique/install.ps1`
- Modify (if extending bundle): `.claude/pack.manifest.yaml` (add spec-critique skill + agents + hook to opt-in inputs)
- Create/Modify (optional): a claude-pack ships-test mirroring `test_bundle_ships_memory_artifacts.py`

## Implementation Steps

1. Read the `--memory-hook` / `--memory-hook-shared` blocks in `product-spec/install.sh` + `install.ps1`; extract the venv-detect + JSON-merge logic.
2. Write `spec-critique/install.sh`: venv ensure (reuse shared) → on `--critique-hook[-shared]`, merge the Stop-hook entry idempotently → print what was registered.
3. Port to `install.ps1` (Windows venv path `.claude\skills\.venv\Scripts\python.exe`).
4. Verify idempotency: running twice does not duplicate the hook entry.
5. Verify plain `./install.sh` registers NO hook.
6. Update `pack.manifest.yaml` so claude-pack can bundle spec-critique; run/extend the ships-test.

## Success Criteria

- [ ] Plain install ensures shared venv, registers no hook.
- [ ] `--critique-hook` idempotently adds `spec_critique_nudge.py` to `settings.local.json`; `--critique-hook-shared` → `settings.json`.
- [ ] Running the installer twice produces no duplicate hook entry.
- [ ] Windows `install.ps1` parity.
- [ ] claude-pack bundles spec-critique skill + 5 agents + hook (ships-test green).
- [ ] No new runtime dependency beyond stdlib + pyyaml.

## Risk Assessment

- **Venv divergence:** must reuse the exact shared venv path; never a per-skill venv. Mitigation: detect-and-reuse, create only if absent with identical deps.
- **settings merge corrupting JSON:** use Python stdlib JSON parse+merge (never string-replace), basename-anchored idempotency. Mirror the proven product-spec block.
- **Bundle drift:** the ships-test guards that claude-pack actually includes the new artifacts.
