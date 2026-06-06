---
phase: 2
title: "Critique agents"
status: completed
priority: P1
effort: "1d"
dependencies: [1]
---

# Phase 2: Critique agents

## Overview

Author the 5 read-only sub-agents under `.claude/agents/`: 4 lens critics (product/tech/market/craft) fanned out in parallel, + 1 opus consolidator. Each consumes the Phase-1 bundle JSON, applies its lens's framework checklist, and returns findings in the fixed sarcastic-Vietnamese voice with evidence+fix. Agents NEVER write files (mirror `memory-harvester`): they propose, the main agent persists.

## Requirements

- **Functional:** each lens agent reads the bundle (path passed by main agent; structural findings use the real shape `{check,severity,artifact_id,file,detail,context}`), critiques ONLY the `target` node(s) but judges them against `ancestry` (upstream intent), pattern-matches against its framework signatures, returns a **compact structured** findings list (bounded — top-N per severity, not unbounded prose): `{lens, evidence: "<artifact_id>:<line>", critique, why_it_dies, fix, severity}`. Consolidator merges all 4, dedups cross-lens, assigns final severity, picks top-3, flags repeat-offense (vs `prior_reports`) + DEC-worthy items, renders the final markdown in voice per `--lang`/`--level`. **Partial-failure tolerant:** if a lens returns nothing/garbage, consolidator proceeds with N<4 and names the missing lens in the report header.
- **Non-functional:** read-only by tool. Models: product=opus, tech=sonnet, market=sonnet, craft=haiku, consolidate=opus. Market lens additionally has WebSearch+WebFetch. Frontmatter schema matches `memory-harvester.md`.

## Architecture

- **Template:** copy `.claude/agents/memory-harvester.md` structure — frontmatter (`name`, `description`, `model`, `tools`) + body (hard read-only boundary → role → inputs → output contract).
- **Tools per agent:**
  - product/tech/craft/consolidate: `Glob, Grep, Read, Bash` (Bash only to read the bundle / prior reports; NO Write/Edit/Task).
  - market: `Glob, Grep, Read, Bash, WebSearch, WebFetch`.
- **Lens framework banks** (from `researcher-260602-0152-...value-lenses-report.md`):
  - **product** (opus): JTBD, Value Prop Canvas, Kano, RICE-integrity, riskiest-assumption, opportunity-solution-tree. Catches: feature nobody needs, fake persona (vs BRD buyer), gold-plating, solution-first.
  - **tech** (sonnet): INVEST, Given-When-Then testability, hidden dependencies, complexity-vs-value, NFR gaps. Catches: untestable AC, non-INVEST story, assume-success.
  - **market** (sonnet+web): Lean Canvas, Porter (light), Blue Ocean, unit-economics, JTBD-competition. Uses bundle `competitors:` + WebSearch; if both absent + `--no-web` → flag "thiếu căn cứ cạnh tranh" (do NOT fabricate). Catches: me-too, no revenue path, no moat.
  - **craft** (haiku): plain-language, CSI-4Cs, unmeasurable-adjective audit, terminology consistency, show-don't-tell. Catches: typos, vague adjectives, term drift, wall-of-text, no examples. (The lens validate never runs.)
- **Voice contract (every agent):** each finding line MUST carry evidence `ID:line` + a fix; the sarcasm rides on top, never replaces grounding. Reference `references/voice-and-tone.md` (Phase 4) for the 5 levels — agents receive the active `--level` + `--lang` from the main agent.
- **Anti-overlap rule (every agent):** do NOT restate a `structural_findings`/`cached_verdicts` label verbatim — go beyond (why-it-dies / market / craft / cross-lens). **Operationalized two ways:** (a) MECHANICAL floor — a finding line must NOT be byte-identical to a structural-finding `detail` string (checkable in eval); (b) REQUIRED-VALUE — every finding MUST carry non-empty `why_it_dies` + `fix` (the value validate cannot provide); a finding lacking both is dropped. The semantic "merely restates" judgment stays advisory (honest: not mechanically decidable). Consolidator enforces (a)+(b).
- **Consolidator output:** a single markdown doc body (header with scope/level/lenses/severity tally → per-lens sections → repeat-offense callout → top-3 → DEC-worthy list). Returns text; main agent writes the file (Phase 4).

## Related Code Files

- Create: `.claude/agents/spec-critique-product.md` (opus)
- Create: `.claude/agents/spec-critique-tech.md` (sonnet)
- Create: `.claude/agents/spec-critique-market.md` (sonnet + WebSearch/WebFetch)
- Create: `.claude/agents/spec-critique-craft.md` (haiku)
- Create: `.claude/agents/spec-critique-consolidate.md` (opus)

## Implementation Steps

1. Read `memory-harvester.md` as the structural template (frontmatter + read-only boundary + inputs/output contract).
2. Write the 4 lens agents: each states its lens, its framework checklist (concrete diagnostic questions + failure signatures), the bundle input contract (`target` vs `ancestry`), the per-finding output schema, the evidence+fix rule, the anti-overlap rule, and the voice grounding.
3. Write `spec-critique-consolidate.md`: inputs = the 4 lens reports + `prior_reports`; dedup/merge rules, severity weighting (blocker/major/minor; structural findings ≥ major), top-3 selection, repeat-offense detection, DEC-worthy flagging, final markdown render in voice. Explicitly read-only — returns markdown, never writes.
4. Cross-check each agent's `description` is specific enough for correct routing and notes "belongs to cleanmatic:spec-critique; spawned by its workflow; cannot see live chat".
5. Verify tool lists are exactly read-only (+web only for market). No Write/Edit/Task anywhere.

## Success Criteria

- [ ] 5 agent files exist with correct frontmatter (name/description/model/tools) matching the locked model+tool table.
- [ ] No agent has `Write`/`Edit`/`NotebookEdit`/`Task`; only market has web tools.
- [ ] Each lens agent encodes its framework bank + evidence+fix + anti-overlap rule.
- [ ] Consolidator encodes dedup + severity + top-3 + repeat-offense + DEC-worthy + voice render, read-only.
- [ ] Agents reference the bundle contract from Phase 1 and the voice spec from Phase 4 (forward ref noted).

## Risk Assessment

- **Lens overlap → duplicate findings:** consolidator dedup + the per-agent anti-overlap rule. Test in Phase 6 eval (report must not duplicate a validate label).
- **Market fabrication:** explicit "no fabrication; flag missing grounding" rule + prefer BRD competitors + cited web. 
- **Voice drift into abuse:** the evidence+fix-per-line rule is mandatory; level 1–4 forbid personal attack. Encoded in every agent + enforced by consolidator.
- **Model cost (opus×2 + web):** acceptable — opt-in skill, scope-aware (story scope skips/thins market). Documented in skill.
