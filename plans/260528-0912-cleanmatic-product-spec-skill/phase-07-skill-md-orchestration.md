---
phase: 7
title: "SKILL.md Orchestration"
status: completed
priority: P1
effort: "8h"
dependencies: [3, 4, 5, 6]
---

# Phase 7: SKILL.md Orchestration

## Overview
Write the LLM-facing prose that ties everything together: the workflows SKILL.md (+ a few orchestration references) follow to run the PO interview, generate artifacts, validate (script JSON → LLM judgment → human report), auto-decompose brain-dumps, delta-update, sign-off, summarize, and present the no-flag menu. This is where the script-vs-LLM split is enforced operationally.

## Requirements
- Functional: every flag has a documented workflow; the LLM knows when to call which script, how to layer judgment on JSON findings, and how to drive AskUserQuestion from the banks; bilingual handling per `lang`.
- Non-functional: SKILL.md stays < 300 lines (deep workflows in `references/`); workflows cite reference specs by filename; no plan/finding-code references in the prose.

## Architecture
- **Detect-state menu (no flag):** no PRODUCT.md → init; else AskUserQuestion menu (new BRD? new PRD? add stories? validate? update? visualize? approve? summary?).
- **Init flow:** scaffold PRODUCT.md template → guided init interview (vision bank) → write context → proceed to requested action.
- **Interview engine (H3 — resume defined):** phased + resumable via `docs/product/.session.md` (committed) using the Phase 2 session schema (`phase`, `lang`, `answers{}`, `pending[]`, `updated`). Resume = read schema → continue at first `pending` question of saved `phase`. Adaptive: skip questions answered by PRODUCT.md; 5-Why on vague; MoSCoW gate; story-mapping. Compose AskUserQuestion from Phase 3 banks in active `lang`. Stale detection = diff `answers` vs current PRODUCT.md → offer resume/discard.
- **Generation flows (`--brd/--prd/--epic/--story`):** interview → `generate_templates.py` → fill prose → assign IDs/links → write to `docs/product/...`. Multi-PRD: accept target arg, else menu of existing PRDs.
- **Validation flow (`--validate`):** run `check_traceability.py` + `check_consistency.py` + `build_traceability_matrix.py` → parse JSON → **LLM layers judgment** (INVEST quality, AC testability, core-value scoring aligned|weak|off, gold-plating, semantic dup, contradiction) → compose human report. `--strict`: errors block, warns don't. Detect prose/frontmatter drift; never overwrite manual prose.
- **Core-value scoring:** LLM scores each PRD/epic/story vs PRODUCT.md core-value sentence; PO confirms `scope` tag; script only checks tag exists + links resolve.
- **`--auto` brain-dump:** chunk large input → decompose into BRD goals/PRDs/epics/stories → propose split → AskUserQuestion **confirm-batch** on ambiguous items → write with traceability.
- **Delta-update (H2 — affected-set defined):** load existing → ask only what changed → call `spec_graph.downstream(changed_id)` to compute the **affected set** = downstream nodes whose *frontmatter* references the changed field → **flag those for PO review / re-interview; NEVER auto-rewrite prose** (resolves the regenerate-vs-never-overwrite collision) → append change-log. **Contradiction with approved decision → surface verbatim + ask keep/change/hybrid; never auto-flip.**
- **`--approve`:** run validation first → warn (not block) on open issues → record owner+date → flip `status: approved`.
- **`--summary`:** generate 1-page exec summary (markdown + optional HTML).
- **Visualization:** invoke Phase 6 `visualize.py` per flag.

## Related Code Files
- Modify: `.claude/skills/product-spec/SKILL.md` (fill workflows, keep < 300 lines)
- Create: `references/workflow-interview.md`, `references/workflow-validate.md`, `references/workflow-auto-and-update.md` (deep prose offloaded from SKILL.md)
- Read for input: all Phase 2 specs, Phase 3 banks, Phase 5/6 script CLIs

## Implementation Steps
1. Finalize SKILL.md: flags table, detect-state menu, Mermaid workflow map, reference-loading pointers, Resources. Keep terse.
2. `workflow-interview.md`: init + phased/resumable interview + adaptivity + bilingual + `.session.md` lifecycle + multi-PRD targeting.
3. `workflow-validate.md`: script-call sequence, JSON→judgment layering, core-value scoring protocol, strict-gate, drift detection, human-report format, exec-summary.
4. `workflow-auto-and-update.md`: brain-dump chunk→decompose→confirm-batch; delta-update + change-log + contradiction-surfacing; `--approve` sign-off.
5. Wire visualization invocations into validate/menu.
6. Consistency sweep: every workflow cites the right reference/script; no orphaned flag; SKILL.md < 300 lines.

## Success Criteria
- [ ] Every flag (+ no-flag menu) has an end-to-end documented workflow.
- [ ] Validate workflow calls scripts, then explicitly layers each LLM-judgment check on the JSON; strict-gate behavior specified.
- [ ] Contradiction-on-approved surfaces + asks, never auto-flips (matches no-silent-reversal rule).
- [ ] `--auto` chunking + confirm-batch documented; delta-update appends change-log.
- [ ] SKILL.md < 300 lines; deep prose in references; no plan/finding-code refs.

## Risk Assessment
- **SKILL.md overflow** (>300 lines) → mitigate: push all step-by-step prose to `workflow-*.md`; SKILL.md = routing + pointers only.
- **LLM skipping scripts** and judging structurally → mitigate: workflows state "MUST run script X first; do not infer the graph by reading files."
- **Judgment/structural boundary blur** in prose → mitigate: each validate step labels owner (script vs LLM) explicitly, mirroring Phase 2 catalog.
