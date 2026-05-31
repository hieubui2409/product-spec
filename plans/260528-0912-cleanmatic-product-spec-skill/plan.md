---
title: "cleanmatic:product-spec skill"
description: "PO-facing skill: interview-driven BRD/PRD/Epic/Story spec hierarchy with traceability, validation, visualization"
status: completed
priority: P2
branch: "master"
tags: [skill, product-management, prd, brd]
blockedBy: []
blocks: []
created: "2026-05-28T02:22:42.985Z"
createdBy: "ck:plan"
source: skill
---

# cleanmatic:product-spec skill

## Overview

Build `cleanmatic:product-spec` — a user-invocable Claude skill for **non-technical product owners** (no code, product-centric). It interviews the PO via AskUserQuestion to produce + maintain a strictly-traceable spec hierarchy (Vision → 1 BRD → many PRDs → Epics → Stories), persists a thin product context file, validates scope/consistency (scripts = structural truth, LLM = judgment), and visualizes the tree (ASCII/Mermaid/HTML/SVG).

**Authoritative decisions:** `plans/reports/brainstorm-decisions-260528-0818-cleanmatic-product-spec-skill-report.md` (sticky; 18 rounds). Domain research: `plans/reports/researcher-260528-0818-prd-brd-skill-*.md` (5 files).

**Build target:** `.claude/skills/product-spec/` (this repo). Namespace `cleanmatic:product-spec` (user-confirmed, non-standard vs repo `ck:`). Python scripts via shared `~/.claude/skills/.venv`; **no jinja2** (stdlib templating, KISS). v1 = full scope (user chose everything).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Scaffold & Skeleton](./phase-01-scaffold-skeleton.md) | Completed |
| 2 | [Reference Specs](./phase-02-reference-specs.md) | Completed |
| 3 | [Bilingual Question Banks](./phase-03-bilingual-question-banks.md) | Completed |
| 4 | [Artifact Templates](./phase-04-artifact-templates.md) | Completed |
| 5 | [Core Scripts](./phase-05-core-scripts.md) | Completed |
| 6 | [Visualization Renderer](./phase-06-visualization-renderer.md) | Completed |
| 7 | [SKILL.md Orchestration](./phase-07-skill-md-orchestration.md) | Completed |
| 8 | [Eval Tests & Packaging](./phase-08-eval-tests-packaging.md) | Completed |

## Key Decisions (from brainstorm — sticky)

- **Hierarchy:** Vision(strategy) + thin PRODUCT.md(facts) → 1 BRD → many PRDs (per feature-area) → Epics → Stories(+AC). Strict traceability. DRY: one authoritative home per fact.
- **Storage:** typed subfolders under `docs/product/`; separate files per artifact; rich YAML frontmatter is source-of-truth; IDs `BRD-G1/PRD-AUTH/E1/S1`.
- **Validation:** scripts structural-only (parse/graph/orphan/AC-presence/ID-integrity/matrix → JSON); LLM all judgment (INVEST, vagueness, core-value drift, gold-plating, dup, contradiction). Default warn, `--strict` blocks.
- **Interview:** PO-facing, phased + resumable (`.session.md`, committed), adaptive + 5-Why + MoSCoW + story-mapping, AskUserQuestion batches, bilingual (`lang: en|vi`, EN+VI banks).
- **Flags:** `--product --brd --prd --epic --story --auto(braindump→decompose) --validate --summary --strict` + viz (tree/mermaid/html/svg). No-flag → detect-state menu.
- **Extras:** delta-update + change-log, contradiction surfaced never auto-flipped, `--approve` sign-off (warn not block), exec summary, 9 viz views, roadmap `now/next/later`.

## Global Constraints (red-team corrections — apply across all phases)

- **VENV (C1):** for dev/test/install **in this repo**, use the repo-local venv `./.claude/skills/.venv/bin/python3` and run `./.claude/skills/install.sh` (NOT `~/.claude/skills/.venv`). The home venv applies only to *installed* skills. All phase commands cite the repo venv. State this once; downstream cites it.
- **IDs (C2 — CONFIRMED):** **parent-scoped IDs** (`BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1`, `PRD-AUTH-E1-S1`) — globally unique by construction, readable lineage. (validate gate)
- **Script CWD (M5):** every script takes `--root <project-dir>` (default CWD); orchestration always passes the detected project root. No implicit CWD file scatter.
- **Boundary (H1):** "gap-analysis / unaddressed parent" script output = strictly *nodes with zero inbound edges of the expected child type*. Any sufficiency/quality assessment = LLM layer. No judgment in scripts.
- **Sequencing (M3/M4):** build order **1→2→4→5→6→(3 ∥ 7)→8**. P3 (bilingual banks) runs LATE/parallel — off critical path, after schema/scripts stabilize so field-tags are final.
- **Viz formats (validate gate — CONFIRMED):** **3 formats** = ASCII + Mermaid-in-markdown + **inline-vendored Mermaid HTML** (self-contained, offline). **SVG/PNG DROPPED** (user reversed earlier "4 formats" — avoids external Mermaid-CLI binary). 9 views × 3 formats.
- **VI banks (validate gate):** author EN+VI now; ship VI **best-effort + "pending native review"** note; off critical path.

## Dependencies

Revised order: **1→2→4→5→6→(3 ∥ 7)→8**. P4 (templates) + P5 (scripts) depend on P2 schema. P6 depends on P5 graph JSON. P3 (banks) depends on P2 but blocks only P7 — author late/parallel. P7 (orchestration) depends on P2–P6 + P3. P8 exercises whole skill. No cross-plan dependencies.
