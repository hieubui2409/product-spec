# Phase 07 — Red-team adversarial review

**Prio:** — · **Effort:** S · **Status:** completed · **Depends:** 01–05 landed (green)

## Context links
- `review-audit-self-decision.md` (verified-decision stickiness; counter-arg alone ≠ reversal)
- Record findings in `docs/audit-trail/EVIDENCE.md` (Phase 02)

## Overview
Once Phases 01–05 are green, run a dedicated adversarial pass that *tries to break* each invariant the phases claim. This is not a re-review of style — it is an attempt to produce a concrete exploit / false-state for each guarantee. Anything that breaks → fix → re-test → log.

## Method
- Prefer delegating to `code-reviewer` (scout-based edge detection) and/or a `Workflow` adversarial-verify pass per invariant. Each finding must be a **reproducible** break (command + observed bad state), not a worry.
- Apply the verified-decision rule: a finding only forces a change if it shows a NEW failure the phase's tests missed. State *why* the prior test missed it.

## Invariants to attack (one verdict each)
1. **Telemetry never enters tarball (A1).** Build a bundle with telemetry sinks present + a symlinked sink; grep the tar. Expect: absent.
2. **Telemetry fail-open (A1).** Make the sink unwritable / path hostile mid-op; expect observed op unaffected, no throw, no partial-corrupt line.
3. **JSONL non-forgery (A1).** Skill/script names with newlines/quotes; expect one record per event, no injected records.
4. **Audit-trail no-secret / no-plan-ref (A2).** Grep ledgers for secret-shaped strings + plan/finding-code refs. Expect: none.
5. **Eval harness no false-green (A3).** Script exits 0 producing nothing; unknown `check:`; mis-tagged `llm`. Expect: FAIL / loud-skip, never silent pass.
6. **Version gate no false state (A4).** `## [Unreleased]` top; pre-release heading; missing CHANGELOG; PR touching only SKILL.md. Expect: correct red/green, runs on PR.
7. **Phase-05 litmus (critical).** Attempt to make repeat-count influence the flagged set: inject count into a lens prompt → litmus test must go RED; delete index → flagged set unchanged. Expect: boundary holds, reproducibility intact.
8. **Determinism of critique unchanged.** Run a critique twice on identical inputs/index → byte-identical findings set (annotation aside).

## Implementation steps
1. For each invariant, write/execute the breaking attempt; capture command + output.
2. Classify: PASS (held) / BROKEN (reproduced) / N/A.
3. For BROKEN → root-cause → fix in the owning phase → re-run that phase's tests + this attack → green.
4. Log every BROKEN+fix as an `EVIDENCE.md` entry (before/after commands).
5. Prune any plan risk rows that the red-team verified as non-issues (cite the check).

## Todo
- [x] 8 invariants attacked, each with a verdict + evidence (REVIEW.md red-team block, all `[N/A]`/held)
- [x] all BROKEN findings fixed + re-tested green (zero BROKEN this pass; LIB-1 from A3 wiring logged retroactively)
- [x] EVIDENCE.md entries for each fix (LIB-1 + pre-existing PSC-1)
- [x] litmus boundary verified by *temporary* injection → red → revert (INV7; no marker left)
- [x] determinism double-run diff = empty (INV8; script-side surface byte-identical)

## Outcome
8/8 invariants held under reproducible attack (command + observed state each). No new BROKEN findings,
so no new fixes; verdicts recorded in `docs/audit-trail/REVIEW.md`. One retroactive EVIDENCE entry
(LIB-1, run_evals `--root` depth) for a defect found+fixed during A3 wiring. Litmus proven catchable
(RED under injected `repeat_count`, GREEN after revert). All suites green after the inject/revert cycle:
critique 27, claude-pack 49, product-spec 43, _shared-lib 7 (py) + 22 (node).

## Success criteria
- Every invariant has a reproducible PASS verdict (or a logged fix that converts BROKEN→PASS).
- No invariant left "assumed safe" without an executed attack.
- The litmus boundary (Phase 05) is proven catchable, not just asserted.

## Risk
- **Theater** (reviewing without actually attacking) → each invariant requires a *command + observed state*, not prose.
- **Scope creep into A9** → repeat-offense attacks target the boundary only; do not add learning-loop machinery to "fix" anything.

## Next steps
- Feeds Phase 06 (STANDARDIZE.md records the *verified* final state + divergences).
- Update BACKLOG.md: HA-adoption A1–A4 + polish marked done; A5–A9 status noted.
