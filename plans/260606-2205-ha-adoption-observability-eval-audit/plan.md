# HA Adoption — Observability + Audit-trail + Eval/CI hardening

**Created:** 2026-06-06 · **Branch:** master · **Mode:** `--tdd --redteam` · **Scope:** P0+P1 (A1–A4) + repeat-offense surfacing polish + reverse STANDARDIZE doc

## Methodology — TDD + Red-team

**TDD (red → green → refactor)** governs every code/test-bearing phase (01, 03, 04, 05; 02 partial):
1. **RED** — write the failing test(s) first (assert the intended behavior; run, confirm they fail for the *right* reason).
2. **GREEN** — minimal implementation to pass.
3. **REFACTOR** — clean up under green; keep tests passing.
- Doc-only work (Phase 02 ledgers, Phase 06) has no unit test → substitute a *checklist gate* (structure/size/convention asserted by a reviewer or a tiny lint), noted per phase.
- Each phase's Todo leads with its failing-test step. No implementation step is marked done until its test is green.

**Red-team (adversarial gate)** runs as a dedicated pass (Phase 07) AND inline per phase:
- Every code-bearing phase carries a **"Red-team angles"** subsection — the attack/abuse/edge vectors its tests MUST cover (not optional).
- Phase 07 is an adversarial review of the *landed* implementation: try to break each invariant (telemetry leak into tarball, audit-trail secret leak, eval false-green, version-gate bypass, and above all the Phase-05 litmus boundary). Findings → fix → re-test → record in `docs/audit-trail/EVIDENCE.md`.
- Red-team findings on a *verified* decision follow `review-audit-self-decision.md`: a counter-argument alone does not reverse; it must surface a NEW issue the tests missed.

## Source

- Comparative-learning: `plans/reports/comparative-learning-260606-1720-human-analyzer-patterns-report.md`
- Implementation blueprint: `plans/reports/ha-implementation-blueprint-260606-1720-four-lens-deepdive-report.md`
- Origin: learn-back from `human-analyzer` (HA); CM is the source repo, HA built observability/audit/eval layers on top — we adopt those, filtered to a 3-skill repo (YAGNI).

## PO decisions (interview 2026-06-06)

- **Scope:** P0+P1 + repeat-offense polish (NOT A9 learning loop).
- **A2 audit-trail location:** `docs/audit-trail/` (dev-facing, durable, git-tracked) — NOT `docs/product/` (PO-owned) nor `plans/reports/` (ephemeral).
- **A1 telemetry safety:** gitignore + CI-assert that the tarball excludes `.claude/telemetry/`.
- **Reverse doc:** yes, one light `STANDARDIZE.md` (HA-source → pattern → CM application).
- **A9 (instinct-store learning loop):** deferred. The valuable slice (repeat-offense *surfacing*) already exists (N1 + findings-index) and is made louder in Phase 5 — presentation only, bound by the litmus test below.

## Litmus test (governs Phase 5 — keeps critique reproducible)

> If the findings-index were deleted, would the *set of flagged findings* change?
> **Must be NO.** Count → presentation = safe. Count → judgment input = A9 = forbidden.
> Lenses judge the current spec blind to repeat-counts; consolidator attaches the count *after* as annotation.

## Phases

**Status: ALL PHASES COMPLETE (2026-06-07).** Reverse ledger `STANDARDIZE.md` (repo root); fixes/verdicts in `docs/audit-trail/{EVIDENCE,REVIEW}.md`. Suites green: critique 27 · claude-pack 49 · product-spec 43 · _shared-lib 7 py + 22 node. Commit held (CLAUDE.md: commit only when asked).

| # | Phase | Item | Prio | Effort | Status |
|---|-------|------|------|--------|--------|
| 01 | Telemetry sink (skill-invocation + script-exec + session-summary JSONL) | A1 | P0 | S | ✅ completed |
| 02 | Cycle audit-trail ledger (`docs/audit-trail/{EVIDENCE,REVIEW}.md`) | A2 | P0 | S | ✅ completed |
| 03 | `run_evals.py` harness (reuse `_gating` structural subset; reshape claude-pack too) | A3 | P1 | **L** | ✅ completed (LLM-gen of missing ps/critique fixtures deferred — needs API key + separate review) |
| 04 | Version-sync CI gate (SKILL.md ↔ CHANGELOG, on PR) | A4 | P1 | S | ✅ completed |
| 05 | Repeat-offense surfacing polish (template/voice only) | — | P1 | S | ✅ completed |
| 06 | Reverse `STANDARDIZE.md` (light, doc-only) | — | — | XS | ✅ completed |
| 07 | Red-team adversarial review (break every invariant) | — | — | S | ✅ completed (8/8 held, 0 BROKEN) |

**TDD applicability:** 01 ✅ · 02 partial (checklist gate) · 03 ✅ · 04 ✅ · 05 ✅ (litmus test) · 06 doc-only (checklist) · 07 is itself the adversarial test pass.

## Build order & dependencies

```
01 (A1 telemetry) ──┬──► 03 (A3 run_evals, reuses A1 exit-helper pattern)
                    │
02 (A2 audit-trail) │   04 (A4 version-sync) ── independent
05 (repeat-offense) │   06 (STANDARDIZE) ── after 01–05 land (documents them)
        └─ independent of 01–04 (touches critique template/agents only)
07 (red-team) ── after 01–05 land; gates before 06 finalizes
```

Recommended sequence: **01 → 02 → 04 → 03 → 05 → 07 (red-team) → 06**. (04 before 03 — A4 is S & independent; A3 carries a design gate. 07 red-team runs once the implementation has landed, before STANDARDIZE.md records the final state.)

## Key cross-cutting constraints

- **claude-pack safety:** `.claude/telemetry/` must never enter the tarball. Manifest is whitelist-based (safe by default) + add CI assert (Phase 1).
- **Fail-open telemetry:** a telemetry write must NEVER break the hook/op it observes. Silent on any error.
- **No new network at runtime** (product-spec / critique promise). Harness (A3) runs no-API-key, deterministic subset only.
- **bug_class marker** is the cross-skill invariant channel — A4 rides it.
- **Determinism of critique** preserved (Phase 5 litmus test).

## Red-team gates (from `plans/reports/from-code-reviewer-to-planner-red-team-plan-review-260606-2257-ha-adoption.md`, all verified against real files)

**Two hard gates before code + one PO contradiction:**

- **C1 (Phase 01) — `PreToolUse:Skill` is a phantom matcher.** Verified: `settings.json` has NO `Skill` matcher; CM uses SessionStart/UserPromptSubmit/PreToolUse(Write·Bash|Glob…)/PostToolUse(Edit|Write·Task…)/SubagentStart/SubagentStop(Plan)/Stop. HA's event names are NOT authoritative for CM. **Gate:** empirical hook-event spike (step-0 of Phase 01) — does a hook fire on Skill-tool use vs slash-command `UserPromptExpansion`? Re-target the invocation hook to whatever actually fires. Same spike resolves H2 (does `PostToolUse:Bash` expose `tool_response.exit_code`, or use the distinct `PostToolUseFailure` event, instead of stderr-regex).
- **C2 (Phase 03) — reuse `_gating`, do NOT invent `kind`.** Verified: product-spec (41 structural/13 llm_advisory) + critique evals ALREADY tag every assertion `_gating: structural|llm_advisory`. **claude-pack has 0 tags** + bare-string assertions → its harness path = real reshape, not tagging. **PO decision (2026-06-06): reshape claude-pack too** — build harness on ps/critique `structural` first (settle contract), THEN add `_gating` + machine mapping to claude-pack. All 3 wired to CI. Phase 03 effort **L** (claude-pack reshape is heaviest sub-task).
- **H1 (Phase 04) — claude-pack breaks A4's equality on a clean repo.** Verified: product-spec 2.2.0==2.2.0 ✅, critique 1.2.0==1.2.0 ✅, **claude-pack CHANGELOG top 1.4.0 ≠ SKILL.md 0.2.0** (bundle-versioned changelog vs skill version, per E5 decoupling). A4's `SKILL.md == CHANGELOG top` would be RED on a correct tree → **must exclude/special-case claude-pack**. PO confirm needed (Q2 below).

## Open questions / PO decisions (resolve before the owning phase)

1. **C1/H2 spike (Phase 01):** confirm the real skill-invocation + bash-failure hook events in *this* Claude Code version (empirical, not doc-guess). Owner: implementer, step-0.
2. **H1 (Phase 04): RESOLVED 2026-06-06** — claude-pack CHANGELOG is intentionally bundle-versioned (E5). A4 **excludes claude-pack**; checks product-spec + critique only.
3. **C2 (Phase 03): RESOLVED 2026-06-06** — **reshape claude-pack too** (not defer): ps/critique `structural` first, then claude-pack `_gating` + machine mapping; all 3 in CI.
4. **Reports landing:** Phase reports → `plans/260606-2205-.../reports/`.
