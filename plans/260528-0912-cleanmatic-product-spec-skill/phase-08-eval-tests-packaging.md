---
phase: 8
title: "Eval Tests & Packaging"
status: completed
priority: P2
effort: "5h"
dependencies: [7]
---

# Phase 8: Eval Tests & Packaging

## Overview
Validate the whole skill end-to-end: ship scenario evals (structural assertions + LLM rubric), finalize README + walkthrough + worked example, install Python deps, and package/validate the skill. This is the quality gate before the skill is usable.

## Requirements
- Functional: 4 eval scenarios run with grading; a worked example product spec demonstrates the full hierarchy + viz; install + package validation pass.
- Non-functional: evals follow skill-creator's `evals.json` schema + grader agent; structural assertions deterministic; rubric for prose quality.

## Architecture
- **Eval suite (`eval/evals.json`)** — 4 scenarios (per brainstorm §16):
  1. init-from-scratch → scaffold + guided init → valid PRODUCT.md.
  2. brain-dump decompose (`--auto`) → correct BRD/PRD/epic/story split + resolved links.
  3. validate-catches-issues → seeded orphan + missing-AC + off-core-value → flags exactly those (structural via script, semantic via LLM).
  4. delta-update + viz → change regenerates affected artifacts, change-log appends, traceability viz renders.
- **Grading = BOTH:** structural assertions (files created, frontmatter valid, expected JSON findings present) + LLM rubric (prose quality 0–100, pass above threshold). Use skill-creator `agents/grader.md`.
- **Headless eval inputs (L2):** the interview is interactive (AskUserQuestion) — evals can't drive Q&A live. Supply PO answers non-interactively: each scenario ships a **pre-baked answer transcript** + seeded files (e.g. a ready PRODUCT.md / braindump fixture) so the run is deterministic. Structural assertions gate; rubric advisory.
- **VENV (C1):** install via `./.claude/skills/install.sh`; test via repo venv.
- **Docs:** README (quickstart + full flag reference), step-by-step walkthrough, `examples/` worked sample product (small product taken through vision→stories→validate→visualize), finalize in-skill CLAUDE.md.
- **Packaging:** add `scripts/requirements.txt` deps to install; `package_skill.py` + `quick_validate.py` clean.

## Related Code Files
- Create: `eval/evals.json` (+ any fixture inputs)
- Create: `examples/` (worked sample product spec tree + a rendered visual)
- Modify: `README.md` (finalize), `CLAUDE.md` (finalize)
- Use: `~/.claude/skills/skill-creator/agents/grader.md`, `scripts/run_eval.py`, `scripts/aggregate_benchmark.py`, `scripts/package_skill.py`, `scripts/quick_validate.py`
- Read for format: Phase 2 specs (assertions reference real field names)

## Implementation Steps
1. Author `eval/evals.json`: 4 scenarios, each with prompt + structural assertions (text form) + expected outputs.
2. Build the `examples/` worked sample: run the skill manually on a small product, commit the resulting `docs/product/**` tree + one rendered HTML/Mermaid visual.
3. Run evals: spawn with-skill + without-skill in parallel; grade via grader agent; `aggregate_benchmark.py`; review deltas.
4. Fix any scenario failures (loop back to owning phase per recommendations; do not fake-pass).
5. Finalize README (quickstart, every flag, output layout, bilingual note) + walkthrough + CLAUDE.md.
6. `install.sh` to install deps into shared venv; `quick_validate.py` + `package_skill.py` clean; full `pytest` green.

## Success Criteria
- [ ] 4 eval scenarios defined and run; structural assertions pass; rubric ≥ threshold.
- [ ] Worked `examples/` spec demonstrates full hierarchy + a rendered visual.
- [ ] README + walkthrough + CLAUDE.md complete and accurate to shipped behavior.
- [ ] `quick_validate.py` + `package_skill.py` pass; all `pytest` green.
- [ ] VI translation flagged for native review (note in README) — known open item.

## Risk Assessment
- **Eval flakiness** (LLM rubric variance) → mitigate: lean on deterministic structural assertions for gating; rubric advisory.
- **Scope = "everything"** may overrun → mitigate: phases are independently shippable; if time-boxed, structural core (P1–P5,P7) + validate is the usable MVP, viz richness (P6 SVG, `--rich` HTML) and some evals can trail.
- **VI quality** unresolved → mitigate: ship EN-verified; mark VI review as a follow-up.

## Resolved by validate gate
- IDs = **parent-scoped** (`PRD-AUTH-E1-S1`). HTML = **Mermaid vendored inline**. **SVG/PNG dropped** (9 views × 3 formats). VI = **ship best-effort + pending-review note**.

## Unresolved Questions (whole-plan — minor)
- Persona cap 2–4: hard cap or soft guidance? (default: soft guidance unless told otherwise)
- Folder name final form (`product-spec` expected from init_skill.py — verified; confirm in Phase 1 spike).
- `markdown` lib actually needed (L3) — confirm during Phase 5 or drop (default: drop).
- VI native-speaker reviewer identity (post-v1).
