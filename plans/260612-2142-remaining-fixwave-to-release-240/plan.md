---
title: Remaining field-audit work (P10b+P11+#9) to release 2.4.0
description: >-
  Build 8 deferred units (P10b #6/#13/#14 + P11 #8/#11/#15 + #9 validation pack)
  TDD, then cut release 2.4.0 + push + GitHub release.
status: pending
priority: P2
branch: master
tags:
  - field-audit
  - product-spec
  - telemetry
  - release
  - tdd
blockedBy: []
blocks: []
created: '2026-06-12T14:59:48.660Z'
createdBy: 'ck:plan'
source: skill
mode: deep + --tdd + --validate
decision_owner: hieubt
source_brainstorm: >-
  plans/reports/from-brainstorm-to-plan-260612-2142-remaining-fixwave-pipeline-report.md
parent_plan: >-
  plans/260611-0050-po-field-audit-fix-waves/ (P1-P10a,P12 landed; this finishes
  P10b/P11/#9 + release)
---

# Remaining field-audit work (P10b+P11+#9) to release 2.4.0

## Overview

Finish the buildable remainder of the Cleanmatic-ERP field audit, then ship it as **release 2.4.0**.
Eight build-new units across product-spec + telemetry, each TDD (RED→GREEN on synthetic in-repo
fixtures), then a release phase (bump 4 skills, lock root CHANGELOG, push tag → CI release).

**LIB-9 stays deferred** — `UserPromptExpansion` 0-record is only diagnosable on a real-transcript
session, not synthetic. Out of scope; remains open in REVIEW.md + BACKLOG real-transcript bucket.

Owner decisions locked (AskUserQuestion 2026-06-12 — do NOT re-litigate): scope = P10b+P11+#9 (all
buildable); #14 = full snapshot/restore engine; #9 = all 3 (incl. id-backfill); release = Claude
pushes tag + release directly after Stage-5 sign-off; version = **2.4.0**; cadence = continuous,
stop only at 3 gates (validate Qs · post-review interview · release-notes sign-off).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [#9ab subsystem-horizon + persona-portrait rules](./phase-01-9ab-subsystem-horizon-persona-portrait-rules.md) | Completed |
| 2 | [#9c id-backfill migrator](./phase-02-9c-id-backfill-migrator.md) | Completed |
| 3 | [#13 decision index view](./phase-03-13-decision-index-view.md) | Completed |
| 4 | [#6 visuals latest + staleness retention](./phase-04-6-visuals-latest-staleness-retention.md) | Completed |
| 5 | [#14 snapshot-restore engine + VCS warn](./phase-05-14-snapshot-restore-engine-vcs-warn.md) | Completed |
| 6 | [#8 artifact-events sink + heat lens](./phase-06-8-artifact-events-sink-heat-lens.md) | Completed |
| 7 | [#11 usage-summary export + harvester](./phase-07-11-usage-summary-export-harvester.md) | Completed |
| 8 | [#15 change-log rotation + path check](./phase-08-15-change-log-rotation-path-check.md) | Completed |
| 9 | [Release 2.4.0 push + github release](./phase-09-release-2-4-0-push-github-release.md) | Pending |

## Architecture decision — modularization via sibling modules (NOT rule-engine refactor)

Scout finding (corrects the brainstorm assumption): the touched files **already** use a focused-sibling
pattern — `check_consistency.py` dispatches to `check_consistency_schema.py`/`_time.py`/`_risk.py`/
`_competition.py`/`session_staleness.py`; `render_html` already split (P12). So new logic lands in **new
sibling modules**, keeping each main file's growth near-zero. No risky base-class/rule-engine extraction
(KISS + matches convention). New siblings: `check_consistency_product.py` (P1), `decision_register_view.py`
(P3), `visuals_retention.py` (P4), `status_vcs.py` + new `snapshot.py` (P5), `lens_artifact_heat.py` +
`track_artifact_edits.py` hook (P6), `harvester.py` (P7).

## Real LOC (scout-measured, core+siblings) & budget posture (~250 exec-LOC rule)

`visualize.py` 500 · `check_consistency.py` 403 · `decision_register.py` 401 · `status.py` 321 ·
`migrate_metric_to_metrics.py` 283 (pattern). All over budget already → every unit adds to a **sibling**,
not the main file. Any main file that must still grow >~20 LOC records a one-line DEC exception in its phase.

## Global constraints (every phase obeys)

1. **TDD**: RED test reproducing the gap FIRST → GREEN. Synthetic in-repo fixtures only (PO real data
   lives in a SEPARATE Cleanmatic-ERP repo — never embed real PO numbers in runnable commands). Hard
   thresholds (byte/bool/count), never "<<1MB"/"safe". Every guard/migrate has a **negative test**
   (idempotent, no over-fix, hook-HEAD-not-clobbered, fresh-install-not-broken, path-only-no-content).
2. **GATE-NO-SILENT-REVERSAL / GATE-NEVER-ASSUME** live during cook: P2 id-backfill migrator is the ONLY
   approved-artifact-touching unit → dry-run→AskUserQuestion→re-approve owner+date. Any contradiction with
   an approved artifact → stop, surface Keep/Change/Hybrid, record DEC. Build-new units on fixtures ⇒ low risk.
3. **Naming hygiene**: test/function/commit names describe BEHAVIOR. CI lint blocks `^def test_(ps|lib|psc|pack)\d+`;
   commit-msg hook blocks finding-codes. Finding IDs (POX-F02 etc.) allowed in phase-file PROSE as description only.
4. **Evidence**: build-new units record `DEC-<n>` + `EVIDENCE.md` before/after (runnable). POX-mapped rows
   (POX-F02/F06/F04/F10/F11) tick `docs/audit-trail/REVIEW.md` when their unit lands.
5. **Privacy/boundary**: #8 path+op only (test asserts no diff content); #11 harvester read-only + opt-in
   (test asserts NO write to skill/template — boundary A9). `.claude/telemetry/` gitignore already landed (P8).
6. **Verify gate per phase**: `CONTRIBUTING.md:69` suite = `.venv/bin/python3 -m pytest .claude/skills/telemetry
   .claude/hooks .claude/skills/_shared -q` + the touched skill's own suite. Broaden when a `_shared`/shared
   contract changes.

## File ownership (single-writer within this round) — CORRECTED post red-team

Red-team found the original "P1-P8 fully parallel-safe" claim FALSE: **P6 and P7 both edit
`telemetry_render.py` (`_T` label dict) AND `analyze_telemetry.py`** (P6 registers a lens, P7 adds CLI
flags). So P7 is serialized behind P6 (`blockedBy: [6]`). All other main files are touched by exactly one
phase. The cook must NOT parallelize P6 and P7.

| File(s) | Phase | Note |
|---|---|---|
| `check_consistency.py` (+ new `check_consistency_product.py`) | P1 | pre-edit: grep dispatch tail, confirm before adding 2 calls |
| `migrate_backfill_ids.py` (new) + PRODUCT.md template | P2 | build+test ONLY; never `--apply` a real approved artifact in cook |
| `decision_register.py` (+ new `decision_register_view.py`) | P3 | append-only data model unchanged |
| `visualize.py` / `render_html.py` (+ new `visuals_retention.py`) | P4 | render_html already split (P12) |
| `status.py` (+ new `status_vcs.py`, `snapshot.py`) | P5 | snapshot OPT-IN only (no migrator auto-hook → no P2 collision); re-read build_status first |
| `register_telemetry_hooks.py` + hook + `lens_artifact_heat.py` + `telemetry_render.py` + `analyze_telemetry.py` | **P6** | **shares render+analyze with P7 → P6 runs FIRST** |
| `harvester.py` (new) + `telemetry_render.py` + `analyze_telemetry.py` | **P7 (blockedBy P6)** | re-read both shared files after P6 lands |
| `assemble_audit_trail.py` + `generate_templates.py` (new append+rotate helper) + 4 workflow ref docs | P8 | full rotation (owner chose (b)); re-read P12 ascii first |

P9 (release) is `blockedBy: [1..8]` **plus** the controller's Stage-4 review + Stage-5 sign-off (Gate C).

## Execution order — CORRECTED

```
P1 ─┐
P2 ─┤  (build+test ONLY — no real-artifact --apply in cook)
P3 ─┤
P4 ─┼─► (Stage-4 code-review) ─► (Stage-5 interview + release-notes sign-off, Gate C) ─► P9 release
P5 ─┤   (snapshot opt-in; no migrator auto-hook)
P6 ─┤
P7 ─┘  (blockedBy P6 — shares telemetry_render.py + analyze_telemetry.py)
P8 ─┘  (full rotation: writer helper + 4 ref docs)
```

Parallel-safe set for cook: {P1, P2, P3, P4, P5, P6, P8}. P7 waits for P6.

## Acceptance criteria (whole plan)

- [ ] 8/8 units RED→GREEN on synthetic fixtures; each has ≥1 negative test; hard thresholds only.
- [ ] `CONTRIBUTING.md:69` suite + each touched skill suite green; `verify_skill_versions.py` green.
- [ ] POX-F02/F06/F04/F10/F11 ledger rows ticked in REVIEW.md; build-new DECs + EVIDENCE recorded.
- [ ] Boundary A9 held (harvester suggests, never writes skill/template — test-asserted); #8 path-only (test-asserted).
- [ ] No GATE violation: id-backfill migrator confirm-gated; **no real artifact mutated during cook** (P2 build+test-only).
- [ ] Pre-push gates green (clean tree · on master · P1-P8 committed · `--extract 2.4.0` non-empty · `test_version_sync` green · suite green on release commit).
- [ ] Release 2.4.0: 4 skills version==changelog-top; root `[2.4.0]`==manifest; tag pushed; GitHub release live with tarball+sha256.

## Risk register (incl. red-team resolutions)

| Risk | Phase | Mitigation |
|---|---|---|
| **[C1] P6/P7 concurrent edits to `telemetry_render.py`+`analyze_telemetry.py` clobber** | P6,P7 | P7 `blockedBy: [6]`; cook must serialize; P7 re-reads both files after P6 |
| **[H1] autonomous cook self-applies id-backfill to a real approved artifact** | P2 | P2 is build+test ONLY; tests use synthetic fixtures with explicit `--confirmed-by`/`--date`; acceptance "no real artifact mutated in cook"; real backfill = PO-side post-upgrade step |
| **[H2] P5 auto-snapshot edits P2 migrator files (collision + undeclared dep)** | P5 | snapshot is OPT-IN (`--snapshot`/`--restore`) only for 2.4.0; auto-before-migrate hook deferred → no P2/P5 file overlap |
| **[C3/H4] autonomous tag-push publishes from dirty/unverified tree** | P9 | hard pre-push gates: `git status --porcelain` empty · on `master` · P1-P8 committed · `release.py --extract 2.4.0` non-empty · `test_version_sync` green · full suite green on release commit · run CI's exact verify cmd locally |
| visuals content-hash reuse deletes a needed render / wrong latest target | P4 | hash compare before write; `--clean` keeps `*-latest` + newest-per-view; negative test "twice-same → 0 new file, latest still resolves" |
| snapshot/restore clobbers live tree or restores wrong ts | P5 | timestamped dirs, never overwrite; restore staging→swap; negative test "restore wrong-ts → error, tree intact" |
| **[H3] #8 sink leaks content / weak privacy test** | P6 | extract `tool_input.path` only, drop rest; test asserts record key-set EXACTLY {ts,artifact_path,op,session} + feeds payload containing `tool_response`/`new_string` to prove stripping |
| **[H3] harvester self-edits skill/template (boundary A9) / weak test** | P7 | read-only by construction; test monkeypatches `open` to raise on any write-mode outside report path (not mtime diff); opt-in flag |
| **[C2] #15 full rotation touches PO-facing prose (4 ref docs) in autonomous run** | P8 | owner chose (b); writer helper in `generate_templates.py` is kit code (not PO artifact); ref-doc edits are kit references; back-compat read of legacy `change-log.md` preserved; idempotent rotation test |
| release CI absent/fails → no GitHub release | P9 | verify remote + `.github/workflows/release.yml` exists pre-push; fallback manual `gh release create` with built tarball+sha256 |
| wrong skill semver bump fails A4 gate | P9 | bump SKILL.md + per-skill CHANGELOG together; `verify_skill_versions.py` + `test_version_sync.py` before push |

## Cook directive — mechanical re-read (replaces "vibes" re-read)

Before editing any 300+ LOC main file (`check_consistency.py` P1, `decision_register.py` P3, `status.py`
P5, `assemble_audit_trail.py`/`generate_templates.py` P8, `telemetry_render.py`/`analyze_telemetry.py` P6→P7),
the cook agent MUST first `grep` the specific insertion anchor and confirm current state in the report —
not edit from the plan's description alone. P7 specifically re-reads `telemetry_render.py` + `analyze_telemetry.py`
AFTER P6 has landed.

## Unresolved (carried as deferred, by owner decision)

- **LIB-9** — needs real-transcript e2e (matcher-fix vs `UserPromptSubmit` fallback vs remove). Stays open.
