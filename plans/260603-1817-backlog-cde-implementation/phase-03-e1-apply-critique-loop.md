---
phase: 3
title: "E1 apply-critique loop"
status: pending
priority: P1
effort: "2d"
dependencies: [2]
---

# Phase 3: E1 apply-critique loop (`product-spec --apply-critique <report>`)

## Overview
The critique return-edge: consume a `product-spec-critique` report, walk each finding with the PO
(**Keep / Change+re-approve / Defer**), and record each ruling in the Decision Register (`DEC-<n>`).
Critique stays report-only; product-spec owns the spec and the rulings. Biggest structural gap in the pipeline.

## Requirements
- Functional: new `--apply-critique <report-path>` flag on product-spec; per finding offer Keep / Change+re-approve / Defer; write a `DEC-<n>` per resolved finding via `decision_register.py`; honor GATE-NO-SILENT-REVERSAL on approved artifacts; reuse `--update` impact-pass (never auto-rewrite prose).
- Non-functional: menu-discoverable + plain-language; no network; deterministic struct handled by script, prose judgment by LLM.

## Key facts (from research)
- Critique report: `docs/product/critique/<ts>-<scope>.md`; each finding has `lens / evidence(ID:line) / why_it_dies / fix / severity` but **NO stable finding ID** (transient). `source_files` in the bundle is citation ground-truth.
- DEC register: `decision_register.py` (`--alloc-id`, `--append --id --title --rationale --affects --supersedes`), `docs/product/decisions.md`, grammar `^DEC-\d+$`, append-only.
- GATE-NO-SILENT-REVERSAL: `guardrails-and-boundaries.md:102` — Keep/Change/Hybrid, never auto-flip; only PO Change+re-approve (owner+date) edits approved content.
- `--update` flow (`workflow-update.md`): detect change → `spec_graph.py --downstream` → flag (never auto-rewrite) → contradiction protocol → consistency sweep → impact report + change-log entry.
- Snapshots carry `body_hash` per node → usable for freshness.

## Architecture — anchoring (the one real unknown)
**Recommended: Option A default + Option C fallback.** (B documented, NOT built.)
- **A — anchor by artifact-id + freshness:** map each finding to its artifact via the `ID` in `evidence ID:line` (drop the line number for matching). Compare the artifact's current `body_hash` vs the critique's `body_hash`/bundle; if changed, tag the finding **"⚠ may be stale — spec changed since critique"** before asking Keep/Change/Defer. Survives line drift (the common case), reuses existing `body_hash`, degrades gracefully.
- **C — manual fallback:** when one artifact carries multiple findings, present them together and let the PO disambiguate/confirm which still apply.
- **B — hash-gate (documented alternative, not built):** require freshest critique; drift forces re-critique. Correct but high friction → kills adoption; reserve its hash-check as A's informational warning only.
- **DECISION REQUIRED before build:** confirm A+C vs B with PO.

### Flow
1. Parse report → list of findings `{lens, artifact_id, line, severity, critique, why_it_dies, fix}` (script: deterministic parse of the report markdown/frontmatter).
2. For each finding: resolve artifact_id, compute freshness (A), present to PO via interview: **Keep** (reject finding) / **Change** (apply fix → if artifact `approved`, run GATE re-approval with owner+date; never auto-rewrite prose — flag + ask per `--update`) / **Defer** (record, no change).
3. Allocate + append `DEC-<n>` per resolved finding: `--rationale "[source: critique <report>] ..."`, `--affects <artifact_id>`. Keep = DEC records rejection; Change = DEC records switch + re-approval; Defer = DEC records deferral + follow-up.
4. Run consistency sweep (reuse `--update` gate); write impact report + change-log entry.

## Related Code Files
- Modify: `.claude/skills/product-spec/SKILL.md` (register `--apply-critique` flag + menu entry)
- Create: `.claude/skills/product-spec/references/workflow-apply-critique.md` (the interview/flow contract)
- Create: `.claude/skills/product-spec/scripts/parse_critique_report.py` (deterministic finding extractor + freshness check using `body_hash`)
- Reuse: `scripts/decision_register.py`, `scripts/spec_graph.py` (`--downstream`, snapshots/body_hash), `references/workflow-update.md`, `references/guardrails-and-boundaries.md`
- Modify: `CLAUDE.md` workflow-pointers table (add the flag → reference row)

## Implementation Steps
> **TDD:** after step 1, write step 5's tests FIRST (parser on multi-finding/missing/stale fixtures, DEC-write integration, GATE re-approval path, Defer follow-up), confirm they fail, then implement parser + workflow to green; re-run full suite. The GATE path test is the critical regression lock.
1. **Confirm anchoring decision (A+C vs B)** with PO.
2. Write `parse_critique_report.py`: read report, emit findings JSON; compute per-artifact freshness by comparing critique-time body_hash vs current snapshot. <120 LOC, pytest-covered.
3. Write `workflow-apply-critique.md`: the per-finding Keep/Change/Defer interview, GATE wiring, DEC-write calls, freshness-warning UX (bilingual).
4. Register flag in SKILL.md + no-flag menu + CLAUDE.md pointer table.
5. Tests: parser (multi-finding artifact, missing artifact, stale detection), DEC-write integration, GATE path on an approved artifact (Change requires re-approval), Defer records follow-up.

## Success Criteria
- [ ] `--apply-critique <report>` parses a real critique report and walks findings.
- [ ] Each resolution writes a correct `DEC-<n>` (Keep/Change/Defer captured; `--affects` set; rationale cites the report).
- [ ] Change on an `approved` artifact triggers GATE-NO-SILENT-REVERSAL (re-approval owner+date); prose never auto-rewritten.
- [ ] Stale findings flagged (A) when artifact body changed since critique; multi-finding artifacts handled (C).
- [ ] Flag is menu-discoverable + plain-language; no network. New tests pass; 50 existing untouched.

## Risk Assessment
- Risk: line-drift mis-mapping → mitigated by A (id-anchor + freshness), never silent.
- Risk: scope-creep into auto-applying fixes → forbidden; prose changes always PO-driven via `--update` discipline.
- Risk: critique report format variance across levels/langs → parser must tolerate level 1–9 + EN/VI; test both. `check_report_language` test in critique skill is a reference.
