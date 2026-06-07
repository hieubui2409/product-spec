# Phase 02 — Cycle audit-trail ledger (A2)

**Item:** A2 · **Prio:** P0 · **Effort:** S · **Status:** pending · **Depends:** none

## Context links
- Blueprint Lens C: `…ha-implementation-blueprint…` (§LENS C)
- Existing rule this satisfies: `.claude/rules/review-audit-self-decision.md` (rule exists; the *artifact* to record into is missing)
- Decision Register: `docs/product/decisions.md` (`DEC-<n>`)

## Overview
We have the *rule* "prove root cause before fix" + a Decision Register, but **no ledger** recording what was fixed and the evidence. Add two durable, git-tracked files capturing fixes per review cycle.

## Key insights
- PO decision: location = `docs/audit-trail/` (dev-facing, durable) — NOT `docs/product/` (PO-owned spec space; mixing engineering fixes there violates DRY one-home) nor `plans/reports/` (ephemeral).
- **Keep small**: HA's EVIDENCE.md hit 50K, REVIEW.md 80K — anti-pattern. CM target: EVIDENCE ≤200 lines, REVIEW ≤300 lines.
- Before/after must be **runnable command output**, not prose.
- Tie to Decision Register: when a fix resolves a ruled conflict, EVIDENCE entry cites `DEC-<n>`. decisions.md = "what we decided", EVIDENCE.md = "what changed + proof".

## Requirements
**Functional**
- `docs/audit-trail/EVIDENCE.md` — one entry per fix: `{ID, category, severity, file:line, root-cause, evidence-before (cmd+output), fix, evidence-after (cmd+output), note}`.
- `docs/audit-trail/REVIEW.md` — finding tracker per cycle: `[ ]/[x]/[~]/[N/A]` per finding with id·cat·sev·file:line·symptom·fix-sketch.
- ID grammar: `PS-` / `PSC-` / `PACK-` / `LIB-` + `<n>` (skill-scoped). Category: CORRECTNESS/DRY/CONSISTENCY/CLEANUP/ENV/YAGNI. Severity HIGH/MED/LOW.

**Non-functional**
- Manual, not CI-driven. Cadence: quarterly / post-major-feature.
- No plan-artifact references inside (per `review-audit-self-decision.md` §5 — explain the *why*, not the origin).

## Architecture
Two markdown files + a short header template. No script orchestrator (HA also has none — driven by `/code-review` skill manually). This phase is **template + seed + convention doc**, not code.

## Related code files
**Create**
- `docs/audit-trail/EVIDENCE.md` — header + format spec + (optional) seed entry from a recent real fix (e.g. the N1 index-empty bug `critique_inherit.py:188`).
- `docs/audit-trail/REVIEW.md` — header + cycle-0 skeleton.
- `docs/audit-trail/README.md` (≤30 lines) — what these are, ID grammar, size caps, DEC tie-in, when to write.

**Modify**
- None (new top-level docs dir).

## Implementation steps
1. Create `docs/audit-trail/` with the two ledgers + README convention.
2. Define ID grammar + category/severity enums in README.
3. Seed EVIDENCE.md with 1 real recent fix (N1 `evidence_id` bug) as a worked example — proves the before/after-command discipline.
4. Cross-link: add a one-line pointer from `review-audit-self-decision.md` (or its rule doc) → "record fixes in `docs/audit-trail/EVIDENCE.md`". (Confirm before editing a rule file — it is committed guidance.)
5. Size guard note in README (≤200 / ≤300 lines; roll old cycles to an archive section if exceeded).

## Todo
- [ ] `docs/audit-trail/EVIDENCE.md` (header + format + 1 seed entry)
- [ ] `docs/audit-trail/REVIEW.md` (header + cycle-0)
- [ ] `docs/audit-trail/README.md` (convention, ≤30 lines)
- [ ] DEC tie-in documented
- [ ] one-line pointer from review rule (confirm first)

## TDD discipline (doc-only → checklist gate)
No unit test (markdown). Substitute a **checklist gate** asserted at review:
- [ ] Both ledgers parse as valid markdown; headers match the README-defined schema.
- [ ] ID grammar regex (`^(PS|PSC|PACK|LIB)-\d+$`) matches every entry ID (a 5-line lint script MAY enforce this — optional, KISS).
- [ ] Size: EVIDENCE ≤200 lines, REVIEW ≤300 lines (CI-cheap `wc -l` check optional).
- [ ] Seed entry's before/after blocks are runnable commands (copy-paste reproducible).

## Red-team angles
- **Secret leak:** seed/evidence command output could paste a token/path → README mandates scrubbing; reviewer greps the seed for secret-shaped strings before commit.
- **Plan-ref leak:** ensure no `F1`/`phase-0X`/finding-code references inside (violates `review-audit-self-decision.md` §5) — grep for `phase-\|finding\|§`.
- **Sprawl regression:** size cap is the guard; archive-roll documented.

## Success criteria
- A new fix can be recorded in <5 min following the template.
- Seed entry has real, reproducible before/after command output.
- No plan/phase/finding-code references leak into the ledger.

## Risk
- **Sprawl** → size caps + archive-roll documented; this is the main HA anti-pattern to avoid.
- **Overlap with decisions.md** → clarified split (decided-what vs changed-what+proof).

## Security
- No secrets in command output (scrub before pasting evidence). Note this in README.

## Next steps
- Becomes the home for fixes discovered during Phases 1/3/4 implementation.
