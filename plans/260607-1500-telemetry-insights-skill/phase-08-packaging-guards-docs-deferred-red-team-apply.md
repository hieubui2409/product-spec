---
phase: 8
title: "Packaging guards + docs + deferred + red-team apply"
status: complete
priority: P1
effort: "4h"
dependencies: [7]
---

# Phase 8: Packaging guards + docs + deferred + red-team apply

## Overview

Wire the new skill + new hooks into the packaging contract (git-tracked, never bundled, CI green), close out docs, record deferred decisions, and run a SECOND red-team on the now-much-larger ported plan (the first ran on the pre-port shape). P1 — highest CI-break risk.

## Requirements
- **Packaging (D8 / R3):**
  - Add `telemetry` to `DEFAULT_SKILLS` (semver check); NOT to `VERSION_SYNCED_SKILLS` (exemption asserted by test).
  - Confirm `pack.manifest.yaml` `skills:` omits `telemetry` AND `hooks:` omits the 2 new hooks → exclusion by construction.
  - gitignore: the new skill dir needs `!/.claude/skills/telemetry/**`; new hooks are `*.py` → already tracked via the existing `!*.py` re-include (verify with `git check-ignore -v`). `git add -f` first skill file.
  - Bundle-exclusion test (extend `test_bundle_excludes_telemetry.py`): assert the telemetry SKILL + the 2 new hooks + the new sinks are absent from a real `python -m pack` tarball.
- **Docs + decisions:**
  - `docs/audit-trail/telemetry-readback.md`: add the new sinks (`subagent-outcomes.jsonl`, `ms` field) + the lens/CLI surface + `/cleanmatic:telemetry`; keep jq fallback.
  - BACKLOG: record SHIPPED (port + lenses + 2 sinks + proxy), DEFERRED (rich errors.jsonl crash-log, HTML, E3 outcome) with rationale; cross-ref E3 (no status flip).
- Non-functional: deterministic build sha for shipped content unchanged; all pre-existing CI gates green.

## Architecture
- The grep-assert "no shipped script imports a telemetry module" (the D5 guarantee) lives here as a test.
- Second red-team: re-challenge the EXPANDED scope — is Full justified vs the original SHRINK verdict? does the 2-hook cost pay off? is reliability/forensics real value for 3 skills or gold-plating? Triage accept/reject/defer.

## Related Code Files
- Modify: `verify_skill_versions.py` (`DEFAULT_SKILLS` += telemetry), `.gitignore`, `test_bundle_excludes_telemetry.py` (+ skill + 2 hooks + sinks; + VERSION_SYNCED exemption assertion)
- Verify-only: `pack.manifest.yaml`, `test_version_sync.py`
- Modify: `docs/audit-trail/telemetry-readback.md`, `BACKLOG.md`
- Create: `plans/reports/from-code-reviewer-to-planner-red-team-260607-1528-telemetry-port-full-scope-report.md`
- Read: `pack/selection.py`, round-1 red-team report

## Implementation Steps (TDD)
1. **Test first:** extend bundle-exclusion (telemetry skill + 2 hooks + new sinks absent from real tarball) + VERSION_SYNCED exemption + "no shipped script imports telemetry module" grep-assert. Run → red.
2. Confirm manifest omissions; add telemetry to `DEFAULT_SKILLS`; gitignore re-include + `git add -f` + `git check-ignore -v`. Make tests green.
3. Full gate sweep: `verify_skill_versions.py`, pytest (3 skills + telemetry + release + new hooks), node tests, deterministic build sha stable.
4. Update `telemetry-readback.md` + BACKLOG (shipped/deferred + E3 cross-ref).
5. **Second red-team** on the full ported plan; triage findings (accept/reject/defer + reason); apply accepted; whole-plan consistency sweep.

## Success Criteria
- [ ] telemetry skill + 2 hooks + new sinks git-tracked yet absent from tarball (asserted vs real build).
- [ ] `DEFAULT_SKILLS` includes telemetry; `VERSION_SYNCED_SKILLS` excludes it (asserted).
- [ ] "No shipped script imports a telemetry module" grep-assert green (the D5/F1 guarantee).
- [ ] All pre-existing CI gates green; deterministic build sha unchanged for shipped content.
- [ ] Read-back doc + BACKLOG updated; E3 status NOT changed.
- [ ] Second red-team report exists; findings triaged + accepted ones applied; zero unresolved plan contradictions.

## Risk Assessment
- **gitignore gotcha (hit in v2.0.0):** new skill dir ignored by `/.claude/skills/*`. Mitigation: explicit re-include + `git add -f` + `git check-ignore -v`.
- **New hooks leaking into bundle.** Mitigation: real-tarball regression test names them explicitly.
- **Second red-team may still say SHRINK.** Acceptable — surface to PO; the per-phase shrink points (P3 proxy, independent lenses) make partial landing easy.
