---
phase: 1
title: "Workflow Orchestration Harness"
status: completed
priority: P1
effort: "0.5d"
dependencies: []
---

# Phase 1: Workflow Orchestration Harness

## Overview

Build the **execution harness** that runs content phases 2–7 through one fixed pipeline and gates ship on `goal.md`. This is the "optimize for the Workflow tool" deliverable: a single self-contained Workflow script that encodes the user's pipeline — **plan → validate → red-team → scope-driven TDD → implement → phase-review → cross-phase-review → checkpoint**, then a global tail **overall-review → multi-wave-review (looped vs `goal.md`) → fix → ship**.

No product code in this phase. Output = `goal.md` (done) + the orchestrator script (below, canonical) + the scope→test map + a harness smoke check.

## Requirements

- **Functional:** the orchestrator drives phases 2–7 sequentially (later phases depend on earlier schema); per phase runs the 8-step inner pipeline; the tail loops goal-gate verification until 2 consecutive clean waves, then ships.
- **Non-functional:** deterministic ordering; sequential file-mutating steps (no parallel write conflicts); read-only verification may parallelize; bounded wave count (anti-infinite-loop); honors all `goal.md` Category A/B deal-breakers.
- **Opt-in:** the Workflow tool spawns many agents → run ONLY during `/ck:cook` with explicit user opt-in. The plan documents the script; it is not executed at plan time.

## Architecture

### Pipeline → stage mapping (user-defined)

| # | User stage | Orchestrator implementation |
|---|-----------|------------------------------|
| 1 | plan | agent reads `phase-0N.md` + design report, restates intent |
| 2 | validate | agent checks preconditions/AC-testability → `{ready, gaps}` |
| 3 | redteam | agent attacks the APPROACH (failure modes, deal-breaker violations) → `{risks, blockers}` |
| 4 | test (scope-driven) | TDD **RED** — write failing pytest for the phase's touched files → `{test_files, cases, red_confirmed}` |
| 5 | implement | TDD **GREEN** — implement to pass → `{files_changed, tests_green}` |
| 6 | phase review | review diff vs phase spec + that phase's goal gates → `{verdict, findings}` |
| 7 | cross-phase review | consistency vs already-completed phases (stale terms, renamed fields, schema drift) → `{verdict, findings}` |
| 8 | checkpoint | run full pytest → conventional `git commit` (commits only when green) |
| 9 | overall review | after all phases, whole-skill review |
| 10 | multi-wave review | loop: verify EVERY `goal.md` gate; FAILs → fix wave → re-verify; exit at 2 clean waves |
| 11 | fix | sequential fixes for failed gates (mutating → no parallel conflict) |
| 12 | ship | bump `2.0.0`, full pytest + evals, prepare release |

**Sequential phases, sequential fixes, parallel verification.** Phases 2–7 are dependent → `for` loop with `await`. Gate verification is read-only → `parallel()`. Fixes mutate files → sequential.

### Scope-driven test map (input to stage 4)

| Phase | Touched files (scope) | Test files (write/extend) |
|-------|----------------------|---------------------------|
| P2 risk | `assets/templates/prd.md`, `epic.md`; `check_consistency.py`; `spec_graph.py`; `render_html.py` | `tests/test_check_consistency.py`, `tests/test_risk_complete.py` (new) |
| P3 time | `prd.md`/`epic.md`; `spec_graph.py`; `check_traceability.py`; `check_consistency.py`; new `time_advisory.py`; `render_mermaid.py`/`render_html.py`; `i18n_labels.py` | `tests/test_dep_cycle.py` (new), `tests/test_check_traceability.py`, `tests/test_time_advisory.py` (new) |
| P4 competition | `brd.md`/`prd.md`; `spec_graph.py`; `check_consistency.py`; `frontmatter_parser.py`; `render_html.py`; `i18n_labels.py` | `tests/test_check_consistency.py`, `tests/test_competition.py` (new) |
| P5 impact+migration | `references/workflow-*.md`; `change-log` schema; new migration script | `tests/test_migration.py` (new), eval `impact-pass` |
| P6 ascii | `render_ascii.py`; `visualize.py`; `render_board.py`/`render_explorer.py`; `test_visualize.py` | `tests/test_visualize.py` (rewrite graph-art asserts, keep tree-text) |
| P7 docs/release | `SKILL.md`, `CLAUDE.md`, `references/*`, `examples/acme-shop/*`, `eval/evals.json` | eval runner, version grep |

### Canonical orchestrator (run via the Workflow tool at cook time)

```javascript
export const meta = {
  name: 'product-spec-v2-orchestrator',
  description: 'Build product-spec v2.0.0 (risk/time/competition + impact engine + ASCII downgrade) via TDD pipeline gated by goal.md',
  phases: [
    { title: 'Build',          detail: 'per content-phase: validate->redteam->TDD red->green->phase-review->cross-phase-review->checkpoint' },
    { title: 'Overall Review', detail: 'whole-skill review after all phases land' },
    { title: 'Multi-Wave',     detail: 'verify every goal.md gate; fix; loop until 2 clean waves' },
    { title: 'Ship',           detail: 'bump 2.0.0, full pytest + evals, prepare release' },
  ],
}

const ROOT   = '/home/hieubt/Documents/cleanmatic-skills'
const PLAN   = `${ROOT}/plans/260530-0503-product-spec-multidim-impact-v2`
const SKILL  = `${ROOT}/.claude/skills/product-spec`
const REPORT = `${ROOT}/plans/reports/brainstorm-design-260530-0309-product-spec-multidim-impact-uc3-report.md`
const GOAL   = `${PLAN}/goal.md`
const PYTEST = `${ROOT}/.claude/skills/.venv/bin/python3 -m pytest ${SKILL}/scripts/tests`

// content phases — dependent, run in order. gates = goal.md IDs this phase must satisfy.
const PHASES = [
  { id: 2, file: 'phase-02-risk-hardening.md',                gates: ['G-C1','G-C2','G-C3','G-C4'] },
  { id: 3, file: 'phase-03-time-and-dependencies.md',         gates: ['G-D1','G-D2','G-D3','G-D4','G-D5','G-D6','G-G2'] },  // G-G2: new time views keep a text path
  { id: 4, file: 'phase-04-competition.md',                   gates: ['G-E1','G-E2','G-E3','G-E4','G-G2'] },              // G-G2: new comp views keep a text path
  { id: 5, file: 'phase-05-impact-engine-and-migration.md',   gates: ['G-F1','G-F2','G-F3','G-A3'] },                     // G-A3 acute here (approved edits) + also global
  { id: 6, file: 'phase-06-ascii-downgrade-to-html-native.md',gates: ['G-G1','G-G2','G-G3'] },
  { id: 7, file: 'phase-07-docs-and-2-0-0-release.md',        gates: ['G-H1','G-H2','G-H3','G-H4'] },
]
// always-on deal-breaker gates re-checked every wave; per-phase reviews also honor G-A*/G-B* via the `base` preamble
const GLOBAL_GATES = ['G-A1','G-A2','G-A3','G-A4','G-B1','G-B2','G-H5']

const VALIDATE  = { type:'object', required:['ready','gaps'], properties:{ ready:{type:'boolean'}, gaps:{type:'array',items:{type:'string'}} } }
const REDTEAM   = { type:'object', required:['blockers','risks'], properties:{ blockers:{type:'array',items:{type:'string'}}, risks:{type:'array',items:{type:'object'}} } }
const TEST      = { type:'object', required:['test_files','red_confirmed'], properties:{ test_files:{type:'array',items:{type:'string'}}, cases:{type:'array',items:{type:'string'}}, red_confirmed:{type:'boolean'} } }
const IMPLEMENT = { type:'object', required:['files_changed','tests_green'], properties:{ files_changed:{type:'array',items:{type:'string'}}, tests_green:{type:'boolean'}, notes:{type:'string'} } }
const REVIEW    = { type:'object', required:['verdict','findings'], properties:{ verdict:{enum:['pass','fail']}, findings:{type:'array',items:{type:'object'}} } }
const GATE      = { type:'object', required:['gate_id','status','evidence'], properties:{ gate_id:{type:'string'}, status:{enum:['pass','fail']}, evidence:{type:'string'} } }
const SHIP      = { type:'object', required:['ready','blockers'], properties:{ ready:{type:'boolean'}, blockers:{type:'array',items:{type:'string'}} } }
const REREVIEW  = { type:'object', required:['phase_verdict','xphase_verdict','tests_green'], properties:{ phase_verdict:{enum:['pass','fail']}, xphase_verdict:{enum:['pass','fail']}, tests_green:{type:'boolean'}, findings:{type:'array',items:{type:'object'}} } }

const done = []   // completed phase ids (for cross-phase review context)

// ---------- per-phase inner pipeline (steps 1-8) ----------
phase('Build')                                  // one Build group spanning all content phases
for (const p of PHASES) {
  log(`Phase ${p.id}: ${p.file}`)
  const base = `Repo ${ROOT}. Skill at ${SKILL}. Phase spec: ${PLAN}/${p.file}. Design report (authoritative §0): ${REPORT}. Acceptance: ${GOAL}. Honor deal-breakers G-A*/G-B* (traceability, back-compat, no-auto-edit-approved, determinism, Script-vs-LLM split).`

  await agent(`${base}\nSTAGE plan (1): read the phase spec + design report §0; restate intent, deliverables, acceptance in your own words; surface any ambiguity before the pipeline proceeds.`, { label:`p${p.id}:plan` })
  const v = await agent(`${base}\nSTAGE validate (2): read the phase spec; confirm preconditions met, AC testable, files identified. List gaps.`, { label:`p${p.id}:validate`, schema: VALIDATE })
  if (!v.ready) log(`  validate gaps: ${v.gaps.join('; ')}`)

  const rt = await agent(`${base}\nSTAGE redteam: attack the APPROACH only (not the code yet). Find failure modes, missing edge cases, and any deal-breaker violation. List blockers that must be resolved before implementing.`, { label:`p${p.id}:redteam`, schema: REDTEAM })
  if (rt.blockers.length) log(`  redteam blockers: ${rt.blockers.join('; ')}`)

  const t = await agent(`${base}\nSTAGE test (TDD RED): write the failing pytest cases listed in the phase spec for its touched files. Run ${PYTEST} and CONFIRM they fail for the intended reason (not import/syntax error). Return the test files + whether red is confirmed.`, { label:`p${p.id}:test`, schema: TEST })

  const impl = await agent(`${base}\nSTAGE implement (TDD GREEN): implement the phase to make ${t.test_files.join(', ')} pass. Keep scripts structural-only and LLM checks judgment-only. Run ${PYTEST} until green. Return files changed + tests_green.`, { label:`p${p.id}:impl`, schema: IMPLEMENT })

  const pr = await agent(`${base}\nSTAGE phase-review: review the implemented diff vs the phase spec AND its goal gates [${p.gates.join(', ')}]. verdict=fail if any gate unmet or any deal-breaker violated.`, { label:`p${p.id}:review`, schema: REVIEW })

  const cpr = await agent(`${base}\nSTAGE cross-phase-review: completed phases = [${done.join(', ') || 'none'}]. Check phase ${p.id} for contradictions vs them: stale terms, renamed fields/APIs, schema drift, duplicated contracts. verdict=fail on any unreconciled contradiction.`, { label:`p${p.id}:xphase`, schema: REVIEW })

  // per-phase fix loop (bounded) so checkpoint only commits green + clean
  let tries = 0
  while ((!impl.tests_green || pr.verdict === 'fail' || cpr.verdict === 'fail') && tries < 2) {
    tries++
    const findings = [...(pr.findings||[]), ...(cpr.findings||[])]
    await agent(`${base}\nSTAGE fix (phase ${p.id}, attempt ${tries}): resolve these findings then re-run ${PYTEST} to green: ${JSON.stringify(findings)}`, { label:`p${p.id}:fix${tries}` })
    // re-review keeps phase + cross-phase verdicts SEPARATE (a fix can resolve one yet break the other)
    const re = await agent(`${base}\nSTAGE re-review phase ${p.id}: re-run ${PYTEST}; re-check gates [${p.gates.join(', ')}] AND cross-phase consistency vs [${done.join(', ') || 'none'}] SEPARATELY. Return phase_verdict, xphase_verdict, tests_green.`, { label:`p${p.id}:rereview`, schema: REREVIEW })
    pr.verdict = re.phase_verdict; cpr.verdict = re.xphase_verdict; impl.tests_green = re.tests_green
  }

  // hard gate: NEVER checkpoint a non-converged phase (abort, leave worktree for triage)
  if (!impl.tests_green || pr.verdict === 'fail' || cpr.verdict === 'fail') {
    log(`Phase ${p.id}: fix loop exhausted with open failures — skipping checkpoint, ABORTING. Worktree left dirty for human triage (git stash to inspect).`)
    return { error: `Phase ${p.id} did not converge`, phasesBuilt: done }
  }
  await agent(`${base}\nSTAGE checkpoint (8): run ${PYTEST} (must be green), then git add the phase ${p.id} files and commit with a conventional message describing the CHANGE (no plan/finding refs in the message). Do NOT push.`, { label:`p${p.id}:checkpoint` })
  done.push(p.id)
}

// ---------- step 9: overall review ----------
phase('Overall Review')
const overall = await agent(`Repo ${ROOT}. All content phases landed. Review the WHOLE product-spec v2 skill end-to-end vs ${GOAL}: coherence, DRY (one home per fact), Script-vs-LLM split, back-compat. Run ${PYTEST}. List any systemic issues.`, { label:'overall', phase:'Overall Review', schema: REVIEW })

// ---------- steps 10+11: multi-wave review driven by goal.md ----------
phase('Multi-Wave')
const ALL_GATES = [...new Set([...PHASES.flatMap(p => p.gates), ...GLOBAL_GATES])].sort()
let clean = 0, wave = 0, lastFails = []     // lastFails hoisted so the Ship stage can see it
while (clean < 2 && wave < 8) {            // bounded — anti-infinite-loop
  wave++
  const results = await parallel(ALL_GATES.map(g => () =>      // verification is read-only -> parallel
    agent(`Repo ${ROOT}. Verify goal gate ${g} from ${GOAL}: run its stated verify method (pytest/eval/grep/manual). Return pass|fail + evidence (command output or file:line).`, { label:`w${wave}:${g}`, phase:'Multi-Wave', schema: GATE })))
  const nulls = results.filter(r => r === null).length    // a crashed verification is NOT a pass
  lastFails = results.filter(Boolean).filter(r => r.status === 'fail')
  if (nulls === 0 && !lastFails.length) { clean++; log(`Wave ${wave}: CLEAN (${clean}/2)`); continue }
  clean = 0                                 // any fail OR any null resets the clean streak
  if (nulls) log(`Wave ${wave}: ${nulls} gate verification(s) returned null — not counted clean; will re-verify`)
  log(`Wave ${wave}: ${lastFails.length} fail(s): ${lastFails.map(f => f.gate_id).join(', ')}`)
  for (const f of lastFails) {              // fixes mutate files -> sequential (no write conflict)
    await agent(`Repo ${ROOT}. Fix goal gate ${f.gate_id}: ${f.evidence}. Make its verify method pass; re-run it. Respect deal-breakers — surface (don't auto-flip) any approved-artifact contradiction.`, { label:`w${wave}:fix:${f.gate_id}`, phase:'Multi-Wave' })
  }
}

// ---------- step 12: ship (BLOCKED if the wave loop never converged) ----------
phase('Ship')
const exhausted = clean < 2                 // hit the wave cap with gates still failing
const ship = exhausted
  ? await agent(`Repo ${ROOT}. DO NOT SHIP. Multi-wave loop exhausted after ${wave} waves with gates still failing: ${lastFails.map(f => f.gate_id).join(', ') || '(verification nulls)'}. Do NOT bump version, do NOT commit. Summarize each open blocker for human triage. Return ready:false + blockers.`, { label:'ship', phase:'Ship', schema: SHIP })
  : await agent(`Repo ${ROOT}. Ship product-spec 2.0.0: bump version in SKILL.md + CLAUDE.md + references (G-H2), run ${PYTEST} + all evals (G-H5), confirm examples/acme-shop --validate green (G-H4). Prepare a conventional commit + 1-paragraph release note. Do NOT push. Return ready + blockers.`, { label:'ship', phase:'Ship', schema: SHIP })

return { phasesBuilt: done, overallVerdict: overall.verdict, waves: wave, cleanWaves: clean, converged: !exhausted, shipReady: ship.ready, blockers: ship.blockers }
```

### Fallback (no Workflow opt-in)

Same pipeline run manually, phase by phase: `/ck:cook phase-0N` (plan: restate intent) → `/ck:test` (TDD red→green) → `/ck:code-review` (phase + cross-phase) → commit (checkpoint) → repeat; then `/ck:code-review` whole-skill (**overall review**) → manual `goal.md` gate walk (**multi-wave**) → fix → `/ck:ship`. The script automates this loop; the loop is the contract.

## Related Code Files

- Create: `plans/260530-0503-product-spec-multidim-impact-v2/goal.md` (DONE) — review oracle.
- Create (at cook time, by extraction): the orchestrator script above, passed inline to the Workflow tool.
- Read for context: design report `§0`, all `phase-0N.md`, `.claude/skills/product-spec/scripts/tests/` (existing pytest conventions).

## Implementation Steps

1. **(DONE)** Author `goal.md` with verifiable gates (Categories A–H) + wave exit condition.
2. Freeze the canonical orchestrator script (above) as the cook-time Workflow input.
3. Fill the scope→test map (above) — confirm each touched-file set against the live tree before cook.
4. Harness smoke (TDD): a 10-line check asserting `meta.phases` length == 4, `PHASES` covers plan phases 2–7, and every `goal.md` gate ID appears in some phase's `gates[]` or `GLOBAL_GATES` (no orphan gate). Keep as a checklist, not product code.
5. Document the opt-in + fallback (above) so cook knows the Workflow run needs explicit user consent.

## Tests First (TDD)

- **RED:** harness-smoke asserts every `goal.md` gate is referenced by the orchestrator; initially fails (gates list not yet wired).
- **GREEN:** wire `PHASES[].gates` + `GLOBAL_GATES` so the union equals the `goal.md` gate set.
- This phase ships no Python; its "test" is the gate-coverage check + a dry parse of the script (valid JS, `meta` is a pure literal).

## Success Criteria

- [ ] `goal.md` exists; every gate has a concrete verify method.
- [ ] Orchestrator script parses (valid JS, `meta` pure literal, phases titles match `meta.phases`).
- [ ] Gate-coverage check passes: union of `PHASES[].gates` + `GLOBAL_GATES` == `goal.md` gate set (no orphan, no dangling gate ID).
- [ ] Scope→test map references only files that exist (or are explicitly "new").
- [ ] Opt-in + fallback documented.

## Risk Assessment

- **Workflow non-opt-in / unavailable** → fallback manual loop documented; same gates, slower. LOW.
- **Multi-wave never converges** → bounded `wave < 8`; on exhaustion, ship returns `ready:false` with blockers for human triage. LOW.
- **Parallel fix file-conflict** → fixes are sequential by design; only read-only verification parallelizes. LOW.
- **Partial write on mid-phase crash** → phases are sequential (no parallel mutation) → `isolation:'worktree'` intentionally NOT used (avoids per-agent cost); the checkpoint abort-guard stops on non-convergence and leaves the worktree dirty for human triage (`git stash`/`reset` to recover). LOW.
- **Null gate verification miscounted as clean** → wave loop counts `null` results and resets the clean streak; never increments clean on a crashed verification. LOW.
- **Wave exhaustion ships broken state** → Ship stage is gated on `exhausted = clean < 2`; on exhaustion it returns `ready:false` + blockers and does NOT bump/commit. LOW.
- **Gate drift** (goal.md edited, orchestrator stale) → harness-smoke gate-coverage check catches orphan/dangling gate IDs. LOW.

## Goal Gates Covered

Meta-phase: wires ALL gates. Directly owns the wave loop + ship that enforce `G-A*`/`G-B*`/`G-H5`.
