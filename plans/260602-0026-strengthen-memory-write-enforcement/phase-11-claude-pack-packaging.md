---
phase: 11
title: "claude-pack-packaging"
status: completed
priority: P2
effort: "2h"
dependencies: [9]
---

# Phase 11: claude-pack-packaging

## Overview
Make the bundle ship the new harvester agent + the top-level hook handler + document the opt-in hook step. The skills +
new scripts + references auto-ship already (slug rglob); the top-level agent needs a manifest `agents:` entry, the
top-level hook handler needs a manifest `hooks:` entry, and the INSTALL doc needs the opt-in note. **NO sub-agent / NO
auto-registered hook for claude-pack itself.** The hook handler SHIPS (capability) but is NEVER auto-registered in
settings (opt-in via `install.sh --memory-hook`).

## Requirements
- Functional:
  - `pack.manifest.yaml`: `agents:` += `memory-harvester.md` (top-level agent def) AND `hooks:` += `memory_gap_hook.py`
    (top-level hook handler) — use the exact name form the `manifest_loader.match_hooks` resolver expects (read it first).
    Bump `version` per the release process (tag-CI owns the actual build — do NOT hand-build).
  - `INSTALL.md.template`: add ONE line — optional post-install step
    `bash .claude/skills/product-spec/install.sh --memory-hook` to enable the opt-in memory hook.
  - Confirm `install.sh.template` / `install.ps1.template` need NO logic change (per-skill hooks under `RUN_HOOKS=1` +
    `.claude/agents/...` paths are handled generically) — verify, don't edit unless a gap is found.
  - `include_settings` stays `false` → the bundle never ships a settings hook registration (consistent with opt-in).
- Non-functional: bundle stays deterministic; safety filter unchanged; the harvester ships read-only.

## Architecture
A 1-line manifest edit + a 1-line INSTALL.md.template edit. The bundle's generic `.claude/...` installer already places
`.claude/agents/memory-harvester.md`. Verified by a `python -m pack` dry-run in P12.

## Related Code Files
- Modify: `.claude/pack.manifest.yaml` (`agents:` += memory-harvester.md; `hooks:` += memory_gap_hook.py)
- Modify: `.claude/skills/claude-pack/assets/templates/INSTALL.md.template` (+1 opt-in line)
- Read for context: `.claude/skills/claude-pack/scripts/pack/selection.py` (agent + hook inclusion loop, `match_hooks`),
  `manifest_loader.match_hooks` (exact name form), `install.sh.template` (generic `.claude/` install)

## Verification (structural + dry-run)
- `python -m pack --dry-run` (or build) lists BOTH `.claude/agents/memory-harvester.md` AND
  `.claude/hooks/memory_gap_hook.py` in the bundle file set.
- `install.sh.template` confirmed to install `.claude/agents/...` and `.claude/hooks/...` generically (no edit needed) —
  or edit if a gap.
- `include_settings: false` unchanged; no settings hook REGISTRATION in the bundle (the handler ships, but is not wired
  into settings — opt-in only).
- NO new claude-pack-self sub-agent; the only bundled hook is the skill's opt-in handler (not auto-registered).

## Implementation Steps
1. Add `memory-harvester.md` to manifest `agents:`.
2. Add the opt-in `--memory-hook` line to `INSTALL.md.template`.
3. Verify the generic installer handles the agent path (dry-run in P12); edit template only if a real gap is found.

## Success Criteria
- [ ] Manifest `agents:` includes `memory-harvester.md` AND `hooks:` includes `memory_gap_hook.py`; bundle dry-run shows
      BOTH packed.
- [ ] INSTALL.md.template documents the opt-in `--memory-hook` step.
- [ ] No settings registration bundled; no claude-pack-self sub-agent; the bundled hook handler is opt-in (not wired).

## Risk Assessment
- Version bump + build are release-process (tag-CI) — do NOT hand-build/publish here (locked release process).
- If the generic installer does NOT place `.claude/agents/*` → minimal template fix; flagged in P12 dry-run.
