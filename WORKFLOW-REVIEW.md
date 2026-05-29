# WORKFLOW-REVIEW.md — Hardcore Multi-Cycle Skill Review Protocol

The stable protocol for the max-recall, multi-cycle review of `cleanmatic:product-spec` and
`cleanmatic:claude-pack`. Companion to **`GOAL.md`** — this file is the **fixed process**;
`GOAL.md` is the **mutable progress + findings log**. Both are committed (durable); per-cycle
reports under `plans/reports/` are gitignored, so condense each cycle into `GOAL.md`.

> Conversational language with the owner is Vietnamese; this file is English to match the repo docs.

---

## 1. Goal & termination

- **Max-recall:** catch every real bug. Recall > precision — a missed bug ships, a false positive is cheap to drop.
- Run as up to **10 cycles** (C1 → C10).
- **Converge-then-stop:** stop after **2 consecutive cycles with ZERO new findings**. Hard cap **C10**.
- **Fix-before-next (non-negotiable):** every finding in a cycle is resolved (fixed, or owner-decided) **before** the next cycle begins. A cycle never starts with unfixed findings from the prior one.
- **Fix autonomy:** auto-fix safe findings; **interview the owner** only on risky/ambiguous items or anything touching a *locked decision* (safety filter · determinism · scope · a value the owner already confirmed). Never silently reverse a locked or owner-confirmed decision.

## 2. Scope

- **Whole skill:** every script, reference, template, `SKILL.md`, tests, `install.sh`, vendored assets.
- **C3+ Expanded Scope:** the newest feature diff is the **PRIMARY** surface; regression on all prior changes is **secondary**.
- Scope is itself a cost lever (see §5): one **full** pass, then **narrow** convergence passes.

## 3. Per-cycle workflow — 3 waves

Each cycle = ONE Workflow run with three waves. Dedup/consolidation happens between waves in
orchestration JS (no agent cost).

**Wave 1 — FIND (parallel finders).**
- N independent finder angles (§4) run concurrently, each reading live files + `git diff`.
- **NO cap on candidates.** Each finder surfaces *every* real defect it sees — no padding, no artificial ceiling. Recall first; cost is controlled downstream, not by truncating finders.

**Consolidate (orchestration, no agent).**
- **Distinct/dedup** raw candidates: collapse same `file:line` (keep the most concrete failure scenario), merge same-mechanism duplicates across angles.
- **Group by file** for batched verification.

**Wave 2 — VERIFY (batched, per-file).**
- **One verifier per FILE**, not per candidate — it sees all candidates in that file at once and returns a 3-state verdict per candidate, each with a quoted proof line:
  - **CONFIRMED** — names triggering inputs/state → wrong output/crash.
  - **PLAUSIBLE** — real mechanism, trigger depends on timing/env/config.
  - **REFUTED** — factually wrong or guarded elsewhere (quote the proof).
- Keep CONFIRMED + PLAUSIBLE; drop REFUTED. Recall mode: a single non-REFUTED vote carries the finding.
- A candidate that re-flags a *locked decision* (§7) without proving a NEW regression → REFUTED.

**Wave 3 — SWEEP (gap finder) → consolidate → verify.**
- One fresh reviewer holding the verified list; surfaces ONLY defects not already listed (moved/extracted code that dropped a guard, second-tier footguns, setup/teardown asymmetry, flag-default flips, doc/version drift).
- Consolidate, then batched-verify the same way.

**Output:** findings ranked (correctness > cleanup; then severity). Owner triages → fix → commit → next cycle.

## 4. Finder angles (9)

- **Correctness (5):** A line-by-line diff scan · B removed-behavior auditor · C cross-file tracer (callers/callees, contract shapes) · D language-pitfall specialist · E wrapper/template/sanitize correctness.
- **Cleanup (3):** Reuse (dup of existing helper) · Simplification (needless complexity/dead code) · Efficiency (wasted I/O, redundant compute, O(n²)).
- **Altitude (1):** right depth, not a fragile bandaid; generalize shared mechanism over special-casing.

Angle selection per cycle:
- **Thorough passes (C4 and C5):** all 9 angles. (Plan change 2026-05-29: C5 repeats the full thorough pass rather than narrowing — C4 surfaced 23 cleanup findings, so one more full sweep is wanted before convergence.)
- **Convergence passes (C6/7+, after a cleanup-clean cycle):** **correctness-only** — cleanup nits never converge to zero, so re-running them every cycle would block the 2-clean-cycle stop condition. Cleanup is cataloged in the thorough passes and fixed there.

## 5. Quality vs token strategy (cost levers)

Baseline: **Cycle 3 ≈ 42 agents / ~3M output tokens / ~834s** (per-candidate verify · all 9 angles · full scope). Levers to cut cost **without** losing recall:

| Lever | Effect | Recall impact |
|---|---|---|
| **Batched verify (one agent per FILE)** | ~32 per-candidate verifiers → ~6–8 | none — same evidence, grouped |
| **No finder cap + consolidate before waves** | full recall; dedup removes waste, not signal | ↑ recall |
| **Scope: full once → narrow after** | C4 full whole-skill; C5+ only fixed-code + immediate callers | none once coverage is established |
| **Cleanup angles only in the thorough pass** | C5+ correctness-only | cleanup already cataloged |
| **Resume-from-runId cache** | re-run post-processing (e.g. emit all findings vs top-N) at **0 agent cost** | n/a — reporting only |
| **Converge-then-stop** | end as soon as 2 clean cycles | n/a |

Cost tiers (choose per cycle):
- **Full** (~16–20 agents · ~1.5–2M tok): full scope + all 9 angles + batched per-file verify + sweep. Use for the single thorough pass.
- **Lean** (~8 agents · ~0.6M tok): narrow scope + correctness-only + single/few batched verifier + no sweep. Use for convergence passes.

## 6. Per-cycle plan (this engagement)

| Cycle | Scope | Angles | Verify | Cap | Status |
|---|---|---|---|---|---|
| C1 | whole-skill | all | per-finding | — | ✅ 31 found, fixed |
| C2 | whole-skill | all | per-finding | — | ✅ 26 found, fixed |
| C3 | feature (primary) + regression | all 9 | per-candidate (42 agents) | 8 | ✅ 30 found, fixed |
| C4 | FULL whole-skill (both skills) | all 9 (incl. cleanup) | batched per-file | NONE | ✅ 29 found (26 agents / ~2.1M tok), fixed |
| **C5** | **FULL whole-skill** (same as C4) | **all 9 (incl. cleanup)** | **batched per-file** | **NONE** | ✅ 39 found (~31 agents incl. sweep re-run / ~2.0M tok), all fixed |
| C6 | FULL whole-skill (owner override) | all 9 | batched per-file | NONE | ✅ 28 found (~29 agents / ~2.6M tok), all fixed — caught 3 C5-fix-induced regressions (1 HIGH) |
| **C7+** | owner's call: full again, or **narrow correctness-only** | per choice | lean/batched | none | pending — narrow per §4 once a cleanup-clean cycle lands; full still defensible (fixes keep inducing regressions) |
| … C10 | per convergence rule | — | — | — | hard cap |

## 7. Locked decisions (carry across all cycles — never silently reverse)

See `GOAL.md` → "Locked design decisions" for the authoritative list. Summary: claude-pack scripts/schemas opt-in · CK files committed + `agents: []` seed · bundles drop only `plans/` · `follow_shared` dir-granular · safety filter case-insensitive (3 layers) · installer full SemVer-2.0 + opt-in hooks · product-spec HTML body views **fail closed** to escaped text (no CDN) · HTML layer escapes only `<`/`>` (not `&`) · read-only viewers (no edit/server/SVG/PNG/real-PDF) · determinism (HTML carries only a timestamp). A finding re-flagging any of these is REFUTED unless it proves a NEW regression.

## 8. Durable record practice

- **`GOAL.md`** (committed): live progress table + convergence state + condensed per-cycle findings. Survives loss of the gitignored reports.
- **`WORKFLOW-REVIEW.md`** (this file, committed): the stable protocol.
- **`plans/reports/cycle-NN-*.md`** (gitignored): full per-cycle detail; condense into `GOAL.md` each cycle.
- The committed skill code + these two files are the only guaranteed-durable artifacts.
