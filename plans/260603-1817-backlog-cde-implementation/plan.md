---
title: "Backlog C/D/E implementation — close the PO pipeline"
description: ""
status: done
priority: P2
branch: "claude/agent-naming-conventions-cd70n"
tags: []
blockedBy: []
blocks: []
created: "2026-06-03T18:20:40.293Z"
createdBy: "ck:plan"
source: skill
---

# Backlog C/D/E implementation — close the PO pipeline

## Overview

Close the open edges of the `product-spec` → `product-spec-critique` pipeline and harden the shared
ecosystem, per backlog groups C/D/E (`BACKLOG.md`). Build order is **stabilize → close the loop →
governance/polish → widen → cleanup**: E5 (release identity) and D12 (CI gate) first so every later
feature lands on a gated, version-honest base; then E1 (the critique return-edge — biggest structural
gap); then C9/E4 (governance + brief); then E2 (discovery seed); then D11 cleanup.

Grounded by `plans/reports/research-260603-1758-backlog-cde-grounding-report.md` (codebase facts) and
`plans/reports/brainstorm-260603-1758-backlog-cde-approaches-report.md` (approaches + trade-offs).

**Excluded:** C10 (parked — awaits task-tracker choice), E3 (deferred — product not in market).

**Phase 8 (C11)** added 2026-06-03, **revised after its own red-team**: adapt the red-team *assumption
discipline* — but NOT as a new lens (that duplicates the existing product **Riskiest-assumption** + tech
**Hidden-deps** frameworks). Instead **strengthen those existing lens prompts** (require an explicit
"assumption → consequence" clause) + add the one missing deterministic check `goal_without_metric` to
`--validate`. No new lens/agent/flag. (All 4 ck-plan lenses now judged already-covered or out-of-scope.)

### Non-negotiable constraints (every phase)
- product-spec stays **non-technical-PO-facing** + **NO network at runtime**; **no code generation**.
- Never overwrite PO prose (`--update` flags + asks). Honor **GATE-NEVER-ASSUME** + **GATE-NO-SILENT-REVERSAL**.
- New flags must be **menu-discoverable** (no-flag menu) + plain-language. Viewers stay read-only.
- **No reduction in passing test cases** (anchor on collected cases via `pytest --co -q`, NOT "50 files" — red-team Scope F8). Run scripts via `.claude/skills/.venv/bin/python3`.
- YAGNI / KISS / DRY. Frontmatter is source-of-truth; scripts handle struct, LLM judges prose.

### TDD convention (all phases — regression-safe)
Each phase follows **tests-first**: (1) write the new/failing tests that encode the phase's success
criteria, (2) confirm they fail for the right reason, (3) implement until green, (4) re-run the FULL
existing suite to prove no regression (anchor = collected passing-case count, re-baselined in Phase 2).
Tests live in each skill's `scripts/tests/` and run via `.claude/skills/.venv/bin/python3 -m pytest`.
Phase 2 (D12 CI gate) lands first so every later phase's red/green cycle is also enforced in CI.

### Resolved decisions (PO, 2026-06-03 — post red-team)
- **E1 anchoring** (Phase 3): parse the structured **lens-cache JSON** (via `lens_findings_hash`), not prose; freshness via `body_hash` with `None`-handling; DEC writes atomic+resumable; injection-sanitized; read-fenced. (Supersedes the original A/B/C prose-anchor framing.)
- **Surface budget** (H8): E1 `--apply-critique` (new flag) · C9 `--viz audit` (view, not a new flag) · E4 `--summary --audience` (no new flag) · E2 `--discover` (new flag, kept separate from `--auto`).
- **E5**: keep both new CHANGELOGs (E5=standardize-hybrid locked); verifier reads nested `metadata.version`, shape+presence only.
- **D11**: scoped down to `_hashable()` only (same-skill), no shared module; `_now()` left divergent.
- **D12 matrix**: 1 OS × 2 Python; offline-enforced; `bug_class` marker registered in all 3 configs.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [E5 per-skill release identity](./phase-01-e5-per-skill-release-identity.md) | Done |
| 2 | [D12 cross-skill CI gate](./phase-02-d12-cross-skill-ci-gate.md) | Done |
| 3 | [E1 apply-critique loop](./phase-03-e1-apply-critique-loop.md) | Done |
| 4 | [C9 audit-trail view](./phase-04-c9-audit-trail-view.md) | Done |
| 5 | [E4 stakeholder brief mode](./phase-05-e4-stakeholder-brief-mode.md) | Done |
| 6 | [E2 discovery seed](./phase-06-e2-discovery-seed.md) | Done |
| 7 | [D11 micro-util consolidation](./phase-07-d11-micro-util-consolidation.md) | Done |
| 8 | [C11 assumption-rigor (strengthen lenses) + goal_without_metric](./phase-08-c11-red-team-adaptation.md) | Done |
| 9 | [9a — E2E (selectively extend /e2e/dating-app) + lv5 acme showcase](./phase-09-e2e-example-docs-changelogs.md) | Done |
| 10 | [9b — docs sweep + changelog backfill](./phase-10-docs-sweep-changelog-backfill.md) | Done |

## Dependencies

**Hard (declared in phase frontmatter — reconciled with red-team F8):**
- Phase 1 → Phase 2 (`[1]`): CI gate verifies the E5 version verifier.
- Phase 2 → Phase 3 (`[2]`): E1 lands on the CI gate.
- Phase 3 → Phase 6 (`[3]`): E2 reuses E1's read-fence pattern. (Phase 8 no longer depends on Phase 3 — the lens-cache is lens-agnostic and no new lens is added.)
- Phase 4 → Phase 5 **release-notes flavor only** (`[4]`): the `--summary --audience release-notes` delta needs the C9 trail. **`--audience exec` is independent and carries Phase 5** — so Phase 5 frontmatter is `dependencies: []` with this conditional noted (avoids the F8 "soft prose vs hard frontmatter" contradiction).

**Independent:** Phase 7 (D11 cleanup).

**Phase 9 (9a)** `dependencies: [1..8]` — selectively extend the already-committed `/e2e/dating-app/` run (keep valid artifacts, recreate only what new features touch) + add a lv5 acme showcase (lv7-9 safety fixtures kept untouched). The committed `/e2e/dating-app/` critique reports (frontmatter-bearing) serve as **Phase 3's E1 freshness fixture** — resolving the ordering inversion (closes red-team H2). **Phase 10 (9b)** `dependencies: [9]` — docs sweep + changelog backfill (Phase 1 scaffolds the CHANGELOGs; 9b backfills them by commit-subject-scope + `--follow`, NOT raw path log — red-team H5).

**Cross-plan:** none. Prior plans (`260528-…product-spec-skill`, `260602-…spec-critique-*`, `260529-…claude-pack-skill`, etc.) are shipped features this plan extends; no blocking relationship.

## Red Team Review

### Session — 2026-06-03
4 hostile reviewers (Security · Failure-Mode · Assumption-Destroyer · Scope). 31 raw → 15 deduped findings, all `file:line`-evidenced. Full report: `reports/from-code-reviewer-to-planner-red-team-cde-plan-review-report.md`. PO adjudicated one-by-one.

**Severity:** 5 Critical · 6 High · 4 Medium. **Disposition:** all accepted/applied except the E5 CHANGELOG-cut (rejected — reverses locked decision E5=standardize-hybrid).

| # | Finding | Sev | Applied to |
|---|---------|-----|-----------|
| C1 | `_now()` formats intentionally divergent — not consolidatable | Critical | Phase 7 (scoped to `_hashable` only) |
| C2 | `common/` module unbundlable → split-brain install | Critical | Phase 7 (no shared module) |
| C3 | DEC-register injection via untrusted rationale | Critical | Phase 3 (sanitize `^---`/`^## DEC-`) |
| C4 | Non-atomic DEC alloc + no resume → dup/dropped DEC | Critical | Phase 3 (`--append-alloc` + resume markers) |
| C5 | GATE re-approval forgeable (LLM-honor-only) | Critical | Phase 3 (deterministic bypass test) |
| H1 | Parse lens-cache JSON, not humanized prose | High | Phase 3 |
| H2 | Freshness untestable on shipped fixtures (`body_hash:None`) | High | Phase 3 |
| H3 | Missing read-side path fence (`fs_guard` write-only) | High | Phase 3 + Phase 6 |
| H4 | D11 site counts wrong | High | Phase 7 (corrected) |
| H5 | `bug_class` marker breaks `--strict-markers`; 2/3 skills no config | High | Phase 2 |
| H6 | venv/sys.path misdiagnosed → per-skill-dir scoping | High | Phase 2 |
| H7 | Audit join has no source-disagreement rule | High | Phase 4 (`unreconciled` rows) |
| H8 | CLI surface bloat vs non-tech-PO | High | reroute: C9 view, E4→--summary, E2 kept, E1 new |
| M1 | `generate_templates.render()` is token-sub, not assembler | Med | Phase 5 (reuse value path) |
| M2 | `version` nested `metadata.version`; "consistency" undefined | Med | Phase 1 (shape+presence only) |
| — | Test anchor imprecise (files≠cases) | Med | plan + Phase 2 (re-baseline) |
| — | Dep frontmatter vs "soft" prose contradiction | Med | reconciled above |

**Whole-plan consistency sweep:** flag-surface decisions (H8) propagated to Phases 4/5/6 + Dependencies; test-anchor reworded plan-wide; D11 title/scope + E1 effort (S→3d) + D12 effort (S-M→1.5d) updated. No unresolved contradictions.

### Session — 2026-06-03 (Phase 8 / C11)
2 reviewers (Scope, Assumption-Destroyer). 3 Critical · 3 High · 1 Medium. Report: `reports/from-code-reviewer-to-planner-red-team-phase8-c11-review-report.md`.

| # | Finding | Sev | Disposition |
|---|---------|-----|-------------|
| A1 | Assumption-lens duplicates product Riskiest-assumption + tech Hidden-deps | Critical | **Accept** — lens CUT; strengthen existing lens prompts instead |
| A2 | Lens agents live in `.claude/agents/`+manifest+test, not skill subtree | Critical | Moot (lens cut) |
| A3 | Consolidator hardcodes 4 lenses; "N<5" false (N<4) | Critical | Moot (lens cut) |
| B1 | `goal_without_metric: error` reds broken-spec fixture + eval | Critical | **Accept** — PO chose `error` + mandatory fixture/eval updates |
| A4 | Wrong code anchor (`check_consistency:88` vs `spec_graph._node_from_goal:176`) | High | **Accept** — re-anchored to goal nodes |
| A5 | E1 coupling overstated (lens-cache is lens-agnostic) | High | **Accept** — Phase 8 `dependencies: []` |
| A6 | 5th-lens edit surfaces undercounted | High | Moot (lens cut) |
| A7 | Citation `:87`→`:84`; evidence-mirror is no-op | Medium | **Accept** — corrected/dropped |

PO rulings: cut new lens + strengthen existing lenses; `goal_without_metric` = `error` with fixture/eval updates; keep Phase 8 (retitled). Phase 8 effort M→0.75d after lens cut.

## Validation Log

### Session — 2026-06-03
Verification pass SKIPPED per validate-workflow guard (`## Red Team Review` already present with `file:line` evidence from 2 rounds; no `[UNVERIFIED]` tags). 4 critical questions on genuine remaining decision points.

| Q | Decision | Effect |
|---|----------|--------|
| MVP scope | **Build all 8 phases** this round (no MVP cut) | No change |
| `goal_without_metric` severity | **`error`** — PO confirms no real in-flight specs with metric-less goals are affected | Phase 8 unchanged (error stays) |
| `--discover` input | **Files AND directories** (bounded recursion); fences retained — *rolled back from files-only same session per PO* | Phase 6: dir input walked with depth/count cap, every file still fenced |
| E1 sequencing | **One full phase** (hardening not split off) | Phase 3 unchanged |

**Phase propagation:** Phase 6 updated (`<!-- Updated: Validation Session 1 - accept files + directories (bounded recursion), fences retained -->`).

### Whole-Plan Consistency Sweep
Re-read plan.md + all 8 phases. Only Phase 6 changed (accepts files + bounded-recursion dirs, all security fences retained); no other phase references `--discover` input shape. Phase 6 "path(s)" wording consistent. No stale terms, no contradictory claims, no superseded decisions left. **Zero unresolved contradictions.**

## Red Team Review (cont.)

### Session — 2026-06-03 (Phase 9 capstone)
2 reviewers (Failure-Mode, Assumption-Destroyer). 2 Critical · 5 High · 2 Medium. Report: `reports/from-code-reviewer-to-planner-red-team-phase9-capstone-review-report.md`. Pivoted the phase.

| # | Finding | Sev | Disposition |
|---|---------|-----|-------------|
| C1/C2 | Wholesale-delete reds committed tests incl. a SAFETY harm-floor grounding contract | Critical | **Accept** — PO: keep lv7-9 safety fixtures+test untouched; acme showcase = additive lv5; no wholesale delete |
| H1 | `/e2e/dating-app/` already committed (full run + caches) — unreconciled | High | **Accept** — PO: selectively extend it (keep/recreate), don't redo |
| H2 | Phase-3 freshness fixture ordering inversion (circular) | High | **Accept** — dating-app critique reports (frontmatter) = Phase 3 fixture |
| H3 | inherit/rollup OFF by default + never exercised | High | **Accept** — explicit prefs-on + parent→child→parent named nodes |
| H4 | 2 driving workflow refs net-new (apply-critique/discover) | High | **Accept** — `[1..8]` gate mandatory; ref grouping fixed |
| H5 | Changelog backfill mis-attributable (contaminated path history) | High | **Accept** — 9b: subject-scope + `--follow`, not raw path log |
| M1 | Committed caches: timestamps + abs paths + web-scraped text | Med | **Accept** — scrub ts/paths, exclude web-cache; "leak NONE" corrected |
| M2 | Bilingual two-run vs freeze-pair body_hash contradiction | Med | **Accept** — one canonical-lang fixture (default vi) |
| M3 | "Repeatable script smoke" needs LLM artifacts → vacuous | Med | **Accept** — reframed as fixture-replay asserting real values |

PO rulings: keep acme lv7-9 safety fixtures untouched + add lv5 acme showcase; selectively extend `/e2e/dating-app`; **split Phase 9 → 9a (E2E+examples, phase 9) + 9b (docs+changelog, phase 10)**. Test impact minimized (safety grounding untouched; golden re-baseline only if files added).

### Whole-Plan Consistency Sweep (Phase 9)
Re-read all 10 phases. Phase 9 split into 9/10; Phase 3 freshness-fixture source now points at `/e2e/dating-app/` (inversion resolved); plan table + dependencies updated. No phase still claims "wholesale delete" or "lv7-9 regenerate". **Zero unresolved contradictions.**
