---
phase: 7
title: "cleanmatic-telemetry skill (usage and health) + VI narration"
status: complete
priority: P2
effort: "4h"
dependencies: [5, 6]
---

# Phase 7: cleanmatic-telemetry skill (usage and health) + VI narration

## Overview

The non-tech face — the other half of the real gap over `com:skill-analytics` (which is dev-facing English). A new skill `cleanmatic:telemetry` the PO invokes to get a plain-Vietnamese read on usage + health + reliability + the validate proxy. The skill runs `analyze_telemetry.py`, reads the aggregates, and NARRATES + JUDGES honestly.

## Requirements
- Functional:
  - `SKILL.md` metadata (`name: cleanmatic:telemetry`, `version: 1.0.0`, description) + body.
  - Default: run `--overview --format ascii`, narrate in Vietnamese (default; `lang`/`--en` knob). Pass-through: `--lens …`, `--format md|mermaid|json`, `--days/--since/--top/--out`.
  - Narration: usage (top / never-used, above gate only), health hotspots + perf (approx caveat), reliability, session shape, validate proxy (internal-quality, not market). Recommendations = SUGGESTIONS only.
  - **Honesty gate (F4):** mandatory "Cái này KHÔNG đo được" section — market/user outcome (E3); + any lens that's empty on current data → "chưa đủ dữ liệu".
- Non-functional: read-only (no edits to spec/code/catalog/memory); no network; venv-run; GATEs N/A (read-only) — stated.

## Architecture
- Skill dir `.claude/skills/telemetry/`: `SKILL.md` + `CHANGELOG.md` + optional `references/narration-contract.md` (move the detailed rubric there if SKILL.md grows).
- Mirror `com:skill-analytics` SKILL.md structure (when-to-use, subcommand table, determinism split, anti-patterns) but: VI-first narration, 3-flat-skill scope, the honesty gate, no `--apply`/write lenses.
- Invocation name: **`/cleanmatic:telemetry`** (PO-confirmed at validate; matches the cleanmatic: convention shared by product-spec/critique/release).
- Skill never recomputes numbers — narrates the script's dict only.

## Related Code Files
- Create: `.claude/skills/telemetry/SKILL.md`, `CHANGELOG.md`
- Create (optional): `.claude/skills/telemetry/references/narration-contract.md`
- Read for context: HA `com-skill-analytics/SKILL.md` + `GUIDE-VI.md` (structure + VI voice), cleanmatic `release/SKILL.md`, `product-spec/SKILL.md`

## Implementation Steps
1. Write `SKILL.md` metadata + body (when-to-use, CLI contract per lens, VI narration rules, honesty gate, read-only boundary, deferred-capabilities pointer).
2. Write `CHANGELOG.md` `[1.0.0]`.
3. Dry-run against real local sinks (thin → MUST hit low-volume path) AND Phase-1 fixtures (rich → full narration). Confirm the honesty gate fires + VI reads naturally.
4. (Packaging is Phase 8 — only create the dir here.)

## Success Criteria
- [ ] `SKILL.md` valid frontmatter + semver; reads naturally for a non-tech VI PO.
- [ ] Narration separates MEASURED (usage/tokens/health/reliability/validate-proxy) from NOT-MEASURED (market outcome).
- [ ] On current thin data, leads with "chưa đủ dữ liệu" (dry-run proof).
- [ ] Zero file edits by the skill; invocation name is `/cleanmatic:telemetry`.

## Risk Assessment
- **Over-claiming effectiveness** (the core F4 trap). Mitigation: honesty gate hard-required, verified by dry-run + review.
- **SKILL.md bloat** (8 lenses). Mitigation: push the rubric to a reference; keep SKILL.md a lean index.
- **Naming mismatch** → undiscoverable. Mitigation: verify in Step 1.
