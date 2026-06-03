---
title: "Backlog C/D/E implementation — close the PO pipeline"
description: ""
status: pending
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

**Phase 8 (C11)** added 2026-06-03: adapt the ck-plan red-team *discipline* into the spec ecosystem,
**split by determinism** — an Assumption-Destroyer lens into `product-spec-critique` (non-deterministic
home) + only genuinely-missing deterministic checks into `--validate` (which already covers most). The
other 3 ck-plan lenses are deliberately NOT adapted (Scope = duplicates critique's product/market lens;
Security/Failure = code/runtime-level, out of a spec's scope).

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
| 1 | [E5 per-skill release identity](./phase-01-e5-per-skill-release-identity.md) | Pending |
| 2 | [D12 cross-skill CI gate](./phase-02-d12-cross-skill-ci-gate.md) | Pending |
| 3 | [E1 apply-critique loop](./phase-03-e1-apply-critique-loop.md) | Pending |
| 4 | [C9 audit-trail view](./phase-04-c9-audit-trail-view.md) | Pending |
| 5 | [E4 stakeholder brief mode](./phase-05-e4-stakeholder-brief-mode.md) | Pending |
| 6 | [E2 discovery seed](./phase-06-e2-discovery-seed.md) | Pending |
| 7 | [D11 micro-util consolidation](./phase-07-d11-micro-util-consolidation.md) | Pending |
| 8 | [C11 red-team adaptation (assumption lens + deterministic gaps)](./phase-08-c11-red-team-adaptation.md) | Pending |

## Dependencies

**Hard (declared in phase frontmatter — reconciled with red-team F8):**
- Phase 1 → Phase 2 (`[1]`): CI gate verifies the E5 version verifier.
- Phase 2 → Phase 3 (`[2]`): E1 lands on the CI gate.
- Phase 3 → Phase 6, Phase 8 (`[3]`): E2 reuses E1's read-fence pattern; C11's assumption-lens key must be in E1's parser.
- Phase 4 → Phase 5 **release-notes flavor only** (`[4]`): the `--summary --audience release-notes` delta needs the C9 trail. **`--audience exec` is independent and carries Phase 5** — so Phase 5 frontmatter is `dependencies: []` with this conditional noted (avoids the F8 "soft prose vs hard frontmatter" contradiction).

**Independent:** Phase 7 (D11 cleanup).

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
