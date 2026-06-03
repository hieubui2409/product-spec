---
phase: 3
title: "E1 apply-critique loop"
status: pending
priority: P1
effort: "3d"
dependencies: [2]
---

# Phase 3: E1 apply-critique loop (`product-spec --apply-critique <report>`)

> **Revised after red-team (2026-06-03).** Folds C3, C4, C5, H1, H2, H3. The naive "parse prose + per-finding alloc+append" design was rejected as injection-prone, non-atomic, and untestable.

## Overview
The critique return-edge: consume a `product-spec-critique` report, walk each finding with the PO
(**Keep / Change+re-approve / Defer**), record each ruling in the Decision Register (`DEC-<n>`).
Critique stays report-only; product-spec owns the spec and the rulings. Biggest structural gap.
**The one justified new flag** (other items route through existing surfaces — see plan surface budget).

## Requirements
- Functional: `--apply-critique <report-path>`; per finding Keep / Change+re-approve / Defer; one `DEC-<n>` per resolved finding; honor GATE-NO-SILENT-REVERSAL; reuse `--update` impact-pass (never auto-rewrite prose).
- Non-functional: menu-discoverable + plain-language; NO network; deterministic struct in script, prose judgment by LLM; **atomic + resumable + injection-safe** DEC writes.

## Architecture — corrected per red-team

### Parse source: structured lens-cache JSON, NOT humanized prose (H1)
The report prose repeats each finding ID 2-3× (Top-3 + per-lens + DEC sections), is bilingual, and
uses localized severity tokens — regex over prose is unreliable. Instead resolve findings from the
**structured cache** the report frontmatter points at: `lens_findings_hash` →
`docs/product/.memory/critique-lens-cache/<hash>.json` (structured `{lens,evidence,critique,why_it_dies,fix,severity}`).
Fall back to manual prose walk (PO reads the report) ONLY when the cache is absent.
- Emit a **deterministic per-finding fingerprint** = `sha8(lens + artifact_id + normalized_critique_text)` — the stable key for dedup, resume, and DEC cross-reference (findings have no native stable ID).

### Read-side path fence (H3)
`fs_guard` is **write-only**. Before reading `<report-path>`: resolve + assert it is contained under
`<root>/docs/product/critique/` (reuse `_is_within`); reject traversal/symlink-escape with a friendly
error. No raw read of arbitrary paths.

### DEC writes: atomic + resumable + injection-safe (C3, C4)
- **Atomic alloc+append:** add a single `decision_register.py --append-alloc` mode that allocates the next id AND appends in ONE process under a file lock — closes the TOCTOU window. The loop never holds an allocated id across a PO-interaction gap.
- **Parse `written` field:** the loop MUST read the JSON `written` result and abort/retry on `false` (dup-id guard returns `written:false` on exit 0 — never silently drop a ruling).
- **Resume markers:** write a per-finding progress marker keyed by the fingerprint → `DEC-n` (under `docs/product/.memory/apply-critique/<report-hash>.json`). A re-run skips already-resolved findings (preserves the anti-re-litigation contract).
- **Rationale sanitization:** reject or escape any rationale line matching `^---\s*$` or `^##\s+DEC-`; store rationale as a YAML literal block-scalar inside the fenced frontmatter. Prevents phantom-DEC smuggling. Add an injection test fixture.

### Freshness (A) with `None`-handling (H2)
Anchor a finding to its artifact by the `ID` in `evidence ID:line`. Compare the artifact's current
`body_hash` vs the critique-time per-node `body_hash` in the report frontmatter. If the report has no
frontmatter / `body_hash: None` (e.g. the hand-authored examples), tell the PO **"this report predates
freshness tracking — re-critique or proceed without staleness check"** rather than silently skipping.
Multi-finding-per-artifact (Option C): present them together (disambiguated by fingerprint) for PO confirm.

### Change → re-approval, deterministically gated (C5)
A Change on an `approved` artifact MUST go through GATE-NO-SILENT-REVERSAL: explicit PO turn → fresh
`approval.approved_at >= DEC.date` + non-placeholder `approved_by`. Pass `--supersedes <prior-DEC>`
when a Change overturns a prior Keep on the same fingerprint, so exactly one active ruling remains
(prevents two contradictory active DECs). Prose is never auto-rewritten — flag + ask per `--update`.

## Related Code Files
- Modify: `.claude/skills/product-spec/SKILL.md` (register `--apply-critique` + menu), `CLAUDE.md` pointer table
- Create: `.claude/skills/product-spec/references/workflow-apply-critique.md` (interview/flow contract)
- Create: `.claude/skills/product-spec/scripts/parse_critique_report.py` (resolve cache-JSON via `lens_findings_hash`, fingerprint, freshness, read-fence)
- Modify: `.claude/skills/product-spec/scripts/decision_register.py` (add atomic `--append-alloc` + file lock; rationale sanitization)
- Reuse: `spec_graph.py` (snapshots/body_hash), `references/workflow-update.md`, `references/guardrails-and-boundaries.md` (Keep/Change/Hybrid at lines ~105-108)

## Implementation Steps
> **TDD:** write the tests in step 6 FIRST (they encode every red-team fix), confirm they fail, implement to green, re-run full suite.
1. **Confirm open decisions** with PO: atomic `--append-alloc` mode (yes), cache-JSON parse source (yes).
2. `parse_critique_report.py`: read-fence the path; resolve findings from `lens_findings_hash` cache (fallback prose); emit fingerprints + per-artifact freshness (handle `body_hash:None`).
3. `decision_register.py`: add `--append-alloc` (lock + alloc + append in one process); add rationale sanitization (reject `^---`/`^## DEC-` lines / literal-block).
4. `workflow-apply-critique.md`: per-finding Keep/Change/Defer interview; resume-marker read/write; GATE re-approval with `--supersedes`; freshness-warning UX (bilingual).
5. Register flag + no-flag menu + CLAUDE.md pointer.
6. Tests: read-fence (traversal/symlink rejected); injection fixture (finding text with `---` fence → no phantom DEC); atomic alloc (no dup id under simulated concurrent/looped alloc); resume (interrupt → re-run skips resolved, no dup DEC); GATE re-approval **bypass test** (Change without fresh owner+date FAILS); `--supersedes` flips prior DEC to superseded; `body_hash:None` warns; cache-JSON parse on a real frontmatter'd fixture generated via the actual critique path; bilingual report.

## Success Criteria
- [ ] Findings resolved from the lens-cache JSON (fingerprinted); prose fallback only when cache absent.
- [ ] `<report-path>` read-fenced to `docs/product/critique/`; traversal/symlink rejected.
- [ ] DEC writes atomic (`--append-alloc`, no dup id), loop parses `written`, resumable (interrupt → no dup/no re-litigation).
- [ ] Rationale injection (`---`/`## DEC-`) neutralized; phantom-DEC test passes.
- [ ] Change on approved triggers GATE (fresh owner+date, `--supersedes`); **bypass test proves the gate cannot be forged**; prose never auto-rewritten.
- [ ] `body_hash:None` reports warn, not silently skip. Menu-discoverable; no network. New tests pass; full suite green.

## Risk Assessment
- Effort raised S→3d after red-team (atomicity, resume, injection, read-fence, deterministic gate are not optional).
- Residual: cache absent on old reports → prose fallback path is weaker; document it as best-effort + recommend `--fresh` re-critique.
