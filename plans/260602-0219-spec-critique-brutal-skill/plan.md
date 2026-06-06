---
title: "cleanmatic:spec-critique — brutal product-spec critique skill"
description: "Separate consumer skill that critiques a product-spec (Vision/BRD/PRD/Epic/Story) from 4 lenses (product/tech/market/craft) via dedicated read-only sub-agents + an opus consolidator, in a fixed sarcastic Vietnamese voice (5-level), grounded in --validate findings + ancestry context + web competitor research. Output to docs/product/critique/. Opt-in post-validate drift nudge hook. Reuse-first: no re-analysis."
status: completed
priority: P2
branch: "feat/product-spec-guardrails-and-memory-layer"
tags: [skill, product-spec, critique, agents, hook, vietnamese]
blockedBy: []
blocks: []
created: "2026-06-01T19:27:44.134Z"
createdBy: "ck:plan"
source: skill
---

# cleanmatic:spec-critique — brutal product-spec critique skill

## Overview

A **separate** skill (`cleanmatic:spec-critique`) that consumes the shipped `cleanmatic:product-spec` output and **critiques** it — brutal, sarcastic Vietnamese voice — across 4 lenses, each a dedicated read-only sub-agent, fanned out in parallel and merged by an opus consolidator. It is **non-deterministic by design** (opinion + web research + voice) and therefore kept OUT of the reproducible `--validate` CI gate. It never edits artifacts; it only writes a critique report.

**Why separate (not a product-spec flag):** `--validate` must stay reproducible/gate-able and warm/PO-facing. A critique (web research + sarcasm) would poison both contracts. spec-critique is a *consumer*: it reuses product-spec's venv + structural scripts + `--validate` verdicts as ammo, adds the LLM critique layer + websearch + craft/editorial critique that validate deliberately omits.

**Design source:** `plans/reports/from-brainstorm-to-plan-260602-0152-spec-critique-skill-design-report.md`
**Research:** `plans/reports/researcher-260602-0152-product-spec-critique-value-lenses-report.md` (4-lens frameworks), `researcher-260602-0224-spec-critique-skill-scripts-conventions-report.md` (script APIs), `researcher-260602-0219-spec-critique-agents-hook-conventions-report.md` (agent/hook patterns).

## Core flow

```
/spec-critique [scope] [--product|--tech|--market|--craft] [--interactive] [--lang vi|en] [--no-web] [--level 1..5]
  1. critique_scan runs structural checks FRESH (check_traceability/check_consistency, cheap)
     + reads cached LLM verdicts from judgments.json (may be empty if PO never validated).
     NO forced --validate. If cache empty/stale → skill SUGGESTS "run --validate first", never forces.
     (Lens agents are the judgment layer; validate verdicts are supplementary ammo.)
  2. critique_scan.py: resolve scope · TRACE ANCESTRY up to root (story→epic→PRD→BRD→vision) =
     context frame; critique target = scope node(+descendants) · gather validate findings +
     judgment_cache verdicts · assemble_digest bundle (+singletons) · read BRD competitors:
     · read prior critique/ reports (repeat-offense) · emit ONE JSON bundle
  3. FAN-OUT 4 lens agents in parallel (Task, read-only): product/tech/market(+web)/craft
  4. spec-critique-consolidate (opus): dedup/merge cross-lens · severity · top-3 · repeat-offense
     · flag DEC-worthy · final voice per --lang/--level → returns markdown
  5. main agent WRITES docs/product/critique/<ts>-<scope>.md (via fs_guard) +
     updates .memory/last_critique.json (body_hash snapshot)
  6. (optional) DEC-flagged finding PO confirms → decision_register.py --append
```

## Key locked decisions (from brainstorm)

- **5 agents:** product=opus, tech=sonnet, market=sonnet+WebSearch/WebFetch, craft=haiku, consolidate=opus. All read-only by tool (no Write/Edit/Task) — agents propose, main agent writes.
- **Voice:** fixed "chửi + mỉa mai", thang 5 mức `--level 1..5` default 3; mức 1–4 cấm công kích cá nhân, chỉ mức 5 tháo. 5 "phũ-có-căn-cứ" principles apply at all levels (every line = evidence ID+line → mỉa → why-it-dies → fix).
- **Anti-overlap with --validate:** critique consumes structural findings (fresh) + cached `judgments.json` verdicts as ammo but must say what validate CANNOT (prose why-it-dies, market/web, craft, cross-lens). Enforced mechanically: a finding line must not be byte-identical to a structural `detail` string AND must carry non-empty why-it-dies+fix; the semantic "adds value" stays advisory.
- **No forced --validate (refined D8):** critique never auto-runs a full validate; structural checks run fresh, LLM verdicts read from cache (suggest validate when cache empty/stale). Lens agents judge independently.
- **Ancestry always loaded:** even a single story pulls its full ancestor chain as judgment context.
- **Output:** `docs/product/critique/<ts>-<scope>.md` (markdown only v1). Marker `docs/product/.memory/last_critique.json`.
- **Hook:** opt-in `spec_critique_nudge.py`, fires after `--validate`/Stop, nudges when body_hash drift ≥ `critique_drift_threshold` (preferences.yaml, default 3); never auto-runs; honors `stop_hook_active`.
- **Memory:** read-only w.r.t. product-spec `.memory`; PO-confirmed big findings bridge to a `DEC` via existing `decision_register.py`.
- **Reuse-first:** reuse `spec_graph`, `assemble_digest`, `check_traceability`, `check_consistency`, `judgment_cache`, `decision_register`, `preferences`, `fs_guard`. Only NEW analysis script = thin `critique_scan.py`.
- **Docs surface (in scope v1):** README + GUIDE-VI + GUIDE-EN + examples/ (sample critique over `product-spec/examples/acme-shop`) + eval/evals.json.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Scripts & preferences](./phase-01-scripts-preferences.md) | Completed |
| 2 | [Critique agents](./phase-02-critique-agents.md) | Completed |
| 3 | [Drift nudge hook](./phase-03-drift-nudge-hook.md) | Completed |
| 4 | [Skill & references](./phase-04-skill-references.md) | Completed |
| 5 | [Installer wiring](./phase-05-installer-wiring.md) | Completed |
| 6 | [Docs examples evals](./phase-06-docs-examples-evals.md) | Completed |

**Dependency order:** P1 → (P2, P3) ; P4 needs P1+P2 ; P5 needs P3 ; P6 needs P4. P1 first (defines the JSON bundle schema all agents consume + the last_critique.json marker the hook reads).

## Dependencies

No cross-plan blockers — `cleanmatic:product-spec` is already shipped (plan `260528-0912` completed; v2 memory layer `260601-1853`/`260602-0026` done). spec-critique only READS its scripts/output. `blockedBy: []`.

## Non-goals (v1)

No HTML/PDF report · no edit-from-report · no auto memory writes (only PO-confirmed DEC bridge) · no NLP assumption-detection (product agent infers via judgment) · no new sample spec (reuse acme-shop) · no separate venv.
