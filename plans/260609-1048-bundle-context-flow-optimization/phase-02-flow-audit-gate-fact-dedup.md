---
phase: 2
title: "Routing-eval authoring + reasoning-proof protocol"
status: completed
priority: P1
effort: "1d"
dependencies: [1]
---

# Phase 2: Routing-eval authoring + reasoning-proof protocol

## Overview

Repurposed after the red-team (BLOCKER-1): the original "flow audit + GATE dedup" is DROPPED (BLOCKER-2 —
deduping a GATE to a non-co-loaded ref silently deletes it; the harness co-presence check in Phase 1 now
guards that mechanically). This phase instead builds the **missing reasoning gate** that makes Phase 3's
SKILL.md compaction safe to verify: routing/flag-selection eval scenarios (none exist today — every
current scenario names its flag) + a written reasoning-proof protocol.

## Requirements

- Functional:
  - **Routing-selection eval scenarios** (the reasoning gate Phase 3 needs): a small set of `llm_advisory`
    scenarios per core skill where the prompt is an AMBIGUOUS PO ask (NOT naming a flag) and the assertion
    judges that the correct flag/mode was chosen + the right ref loaded. Add to `eval/evals.json` with a
    `golden` artifact where needed (so `llm_eval.py` can judge them). Cover the flags Phase 3 will compact.
  - **Baseline the new scenarios GREEN before any compaction** — if a routing scenario fails on the
    CURRENT (verbose) SKILL.md, fix the scenario, not the skill; there must be a real green to preserve.
  - **Reasoning-proof protocol (PO-resolved: sub-agent, NO API key, best-of-3):** proof (b) = **spawn a
    sub-agent** (a Claude instance = the LLM judge) that (i) generates the eval materials / goldens for the
    routing + affected advisory scenarios, then (ii) judges them **before vs after** each compaction —
    reading both SKILL.md versions — as a **best-of-3 / majority vote** (3 independent judgements, majority
    wins; ties → fail-safe = revert). Recorded per commit. Offline pytest proves STRUCTURE only; the
    sub-agent majority is the REASONING proof. `llm_eval.py` HTTP path optional, NOT required.
- Non-functional: scenarios are real reasoning probes (ambiguous → correct routing), not "names the flag"
  restatements; the deterministic structural half stays gating; the reasoning half is judged by the
  spawned sub-agent.

## Architecture

```
author routing scenarios (ambiguous ask → expected flag/ref) ──► eval/evals.json (+ golden)
sub-agent generates goldens + runs/judges on CURRENT skill ──► GREEN baseline (reasoning to preserve)
proof-(b) per Phase-3 commit: sub-agent judges before vs after → held? keep : revert
```

## Related Code Files

- Modify: `.claude/skills/product-spec/eval/evals.json` (+ routing scenarios, golden if needed)
- Modify: `.claude/skills/product-spec-critique/eval/evals.json` (+ routing scenarios)
- Read: `_shared/lib/run_evals.py`, `_shared/lib/llm_eval.py` (how advisory scenarios are judged)
- Create: a short reasoning-proof-protocol note in the plan EVIDENCE

## Implementation Steps

1. Inventory the flags Phase 3 will compact; for each, draft an ambiguous-ask routing scenario.
2. Add scenarios to `evals.json`; supply goldens where `llm_eval.py` needs them.
3. Run them on the CURRENT skill → must be green (fix the scenario, never the skill, to reach green).
4. Define the sub-agent proof recipe (the prompt + what materials it generates + the before/after judging
   contract) so Phase 3 can invoke it identically per commit.
5. Write the proof-(b) protocol into the plan EVIDENCE; Phase 3 follows it per commit.

## Success Criteria

- [ ] Routing-selection scenarios exist for every flag Phase 3 will touch (both core skills).
- [ ] Scenarios are GREEN on the current (pre-compaction) skill (sub-agent judged) = reasoning baseline.
- [ ] Sub-agent proof-(b) recipe written (generate goldens + before/after judge), reproducible per commit.
- [ ] No SKILL.md content edited in this phase (it only adds the gate that makes Phase 3 safe).

## Risk Assessment

- **Routing scenarios are weak (still implicitly name the flag)** → review each for genuine ambiguity; a
  scenario the verbose SKILL.md ALREADY fails is a scenario bug, not a skill bug.
- **Sub-agent judge is non-deterministic** → mitigated by **best-of-3 majority vote** (PO-chosen) + a tight
  rubric (did it pick flag X? yes/no); a majority "after worse" or a tie → revert that commit (fail-safe).
- **Scope creep into a full eval framework** → keep to the handful of flags Phase 3 compacts; reuse the
  existing `evals.json` shape, do not rebuild the harness.
