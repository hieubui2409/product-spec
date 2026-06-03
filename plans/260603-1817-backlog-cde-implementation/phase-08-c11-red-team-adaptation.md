---
phase: 8
title: "C11 red-team adaptation (assumption lens + deterministic gaps)"
status: pending
priority: P2
effort: "1.5d"
dependencies: [3]
---

# Phase 8: C11 — adapt ck-plan red-team into the spec ecosystem (split: judgment → critique, structural → validate)

> Added 2026-06-03 per PO. Brings the ck-plan red-team *discipline* into product-spec, **split by determinism**
> so `--validate` stays a reproducible CI gate and the hostile judgment lives where non-determinism already lives.

## Overview
ck-plan red-team spawns hostile reviewer lenses + an evidence-required adjudication. We adapt it **split**:
- **Half A (non-deterministic judgment) → `product-spec-critique`:** add ONE new lens — **Assumption-Destroyer** — to the existing 4 (product/tech/market/craft). It is the only ck-plan lens critique lacks.
- **Half B (deterministic structural risk) → `product-spec --validate`:** add only the genuinely-missing script-able checks (the catalog already covers most). Keep the script-vs-LLM split sacred.

## Why only the Assumption-Destroyer lens (not all 4 ck-plan lenses)
| ck-plan lens | Adapt? | Reason |
|---|---|---|
| **Assumption Destroyer** | ✅ add to critique | critique has no "which unstated assumption kills this" lens — genuine gap |
| Scope & Complexity Critic | ❌ skip | **gold-plating: `product-critic` already catches "features nobody needs / gold-plating / fake personas"; `market-critic` catches "me-too / no moat."** A Scope lens duplicates them — the very YAGNI violation it would flag. |
| Security Adversary | ❌ skip | code/impl-level; the spec tool generates no code |
| Failure Mode Analyst | ❌ skip | runtime/race-level; out of a product-spec's scope |

## Half B = exactly ONE net-new deterministic check: `goal_without_metric`
The validate catalog already owns most structural-risk checks — `orphan_*`, `missing_ac`, `low_ac_count`,
`risk_blindspot`, `gold_plating` (LLM), `vagueness` (LLM — "should/easy/fast"), `invest_quality`,
`semantic_duplication`, `contradiction`. The inventory leaves **one real gap**, and Half B builds it:

**`goal_without_metric`** — a BRD goal whose `metrics` list is empty or missing.
- **Verified gap:** `frontmatter-and-id-spec.md:87` declares goal `metrics` **"required, ≥1 metric slug"**, but no script enforces it. `metrics` appears only in `check_consistency.py:88` `LIST_FIELDS` (a *type* check) — an empty/missing list passes validate today. A goal with no measurable target is exactly the "unstated assumption" a red-team catches; here it is fully deterministic.
- **This check WILL be built** (not conditional). It is the sole Half-B deliverable.
- **DRY boundary (not a hedge):** do NOT re-implement weasel-word / gold-plating / INVEST — those are already owned. Half B adds `goal_without_metric` and nothing else.

## Requirements
- Functional: critique gains an Assumption-Destroyer lens (read-only sub-agent, same evidence `ID:line` + voice discipline as the other 4); validate gains the `goal_without_metric` deterministic check.
- Non-functional: critique half stays OUT of the CI gate (non-deterministic); validate half stays script-only + reproducible. No network in validate.

## Architecture
- **Half A (critique):** new `assumption-critic` sub-agent mirroring the existing 4 critics' contract (reads the `critique_scan` bundle, emits `{lens:"assumption", evidence:ID:line, critique, why_it_dies, fix, severity}`), consumed by the existing consolidator + humanizer + voice levels. Lens question: *"what must be true for this to work that the spec never states — and what happens when it isn't?"* (riskiest-assumption framing). No new orchestration — reuse the bundle + consolidator.
- **Half B (validate):** add `goal_without_metric` to the `validation-rules-spec.md` catalog + implement in `check_consistency.py` (where goal `metrics`/`LIST_FIELDS` already live) as a **script** finding: trigger = a `type: goal` node whose `metrics` is missing or an empty list; message = "BRD goal {id} declares no metric." **Severity `error`** (mirrors `missing_ac` — a parent with zero measurable target is a hard gap; the spec marks `metrics` required). Flows through the existing `strict_gate.py` (exit 2 on error). Closed-field/graph only — no prose judgment.
- **Coupling with Phase 3 (E1):** the apply-critique parser reads the lens-cache JSON keyed by lens; it MUST tolerate the new `assumption` lens. Hence `dependencies: [3]` — land E1's parser first (or update it here).

## Related Code Files
- Create: `.claude/skills/product-spec-critique/` — assumption-critic sub-agent definition + reference (mirror an existing lens critic, e.g. `product-critic`)
- Modify: critique `SKILL.md` (register 5th lens), consolidator prompt (accept 5 lenses, tolerate N<5 already supported)
- Modify (Half B): `product-spec/references/validation-rules-spec.md` (add `goal_without_metric` catalog row) + `product-spec/scripts/check_consistency.py` (implement the check next to the existing `metrics` handling at `:88`)
- Modify: E1 `parse_critique_report.py` (Phase 3) — accept `assumption` lens key
- Reference: `.claude/skills/ck-plan/references/red-team-personas.md` (evidence-discipline pattern to mirror)

## Implementation Steps
> **TDD:** write the lens-output + new-rule tests FIRST, confirm fail, implement to green, re-run full suite.
1. Half A: author `assumption-critic` mirroring `product-critic`'s contract; register as 5th lens; confirm consolidator tolerates 5 (and still N<5).
2. Half B: implement `goal_without_metric` in `check_consistency.py` (missing/empty `metrics` on a `type: goal` node → error finding); add the catalog row to `validation-rules-spec.md`; confirm it surfaces via `strict_gate.py` (exit 2).
3. Update E1 parser (Phase 3) to accept the `assumption` lens key (or note it as a Phase-3 acceptance item if 3 not yet built).
4. Tests: assumption-critic emits valid findings on a fixture spec (EN/VI); consolidator renders 5 lenses; `goal_without_metric` fires on a metric-less goal, stays silent on a goal with ≥1 metric, and is reproducible (deterministic ordering); `strict_gate.py` exits 2 when a goal lacks a metric; E1 parses an assumption-lens finding.

## Success Criteria
- [ ] critique runs a 5th **Assumption-Destroyer** lens via the existing sub-agent/consolidator/voice pipeline; stays out of CI.
- [ ] NO Scope/Security/Failure lens added (justified as duplicative/out-of-scope).
- [ ] Half B ships `goal_without_metric` (missing/empty goal `metrics` → error), reproducible + enforced by `strict_gate.py`; nothing already-covered (vagueness/gold_plating/INVEST) re-added.
- [ ] E1 parser tolerates the new lens key.
- [ ] New tests pass; full existing suite green.

## Risk Assessment
- Risk: Half B scope-creep re-implementing `vagueness`/`gold_plating` → the DRY boundary is explicit: Half B = `goal_without_metric` only.
- Risk: `goal_without_metric` as `error` fails existing specs that omit goal metrics → acceptable (the spec already marks metrics required); if it breaks real in-flight specs, downgrade to `warn` is a one-line change, but default is `error`.
- Risk: 5th lens dilutes critique's voice/cost → it reuses the same consolidator/humanizer, marginal cost; gate behind the existing lens-selection if critique supports per-lens opt-in.
- Coupling with Phase 3: if E1 ships first, this only adds a lens key; if this ships first, E1 must include `assumption` from day one.
