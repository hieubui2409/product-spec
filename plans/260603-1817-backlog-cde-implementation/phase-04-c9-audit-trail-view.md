---
phase: 4
title: "C9 audit-trail view (--viz audit)"
status: pending
priority: P2
effort: "1d"
dependencies: []
---

# Phase 4: C9 audit-trail view (`--viz audit`)

> **Confirmed after red-team (2026-06-03).** Kept as a `--viz` **view** (not rerouted to `--status`) so the
> visual rendering capability is preserved (H8 / PO). Adds the H7 unreconciled-row rule + reuses `status.py`
> data loaders for DRY.

## Overview
A read-only governance view joining data the skill ALREADY captures — change-log, approval metadata,
stale approvals, decision register — into one chronological table: *when · artifact · action ·
who-approved · what-drifted · DEC*. `--viz audit` is a new **value** of the existing `--viz` flag
(like `board`/`explorer`), NOT a new top-level flag.

## Requirements
- Functional: `--viz audit` renders a chronological audit trail; ASCII + markdown; bilingual via session `lang`.
- Non-functional: read-only viewer; deterministic struct from script; no network. **ASCII+md only — no HTML this phase** (keeps the view registry off the XSS-watch reopen).

## Key facts (from research)
- `.snapshots/` + `diff_graphs()`/`changed_nodes()` (`spec_graph.py:466,469,492,519`); `CHANGED_FIELDS=(status,scope,moscow,horizon,size,body_hash)`.
- `change-log.md` (append-only, newest-top) from `change-log-entry.md` (`date/action/author/affected_set/dims`).
- Approval metadata: frontmatter `approval:{approved_by,approved_at,approved_version}` (`frontmatter-and-id-spec.md:~176`).
- `status.py` already loads `stale_approvals` (`:211`) + baseline snapshots (`:100`) + `unrecorded_signals` (`:51`) — **reuse these loaders** (DRY) rather than re-reading sources.
- DEC register parseable via `decision_register.py --list` (JSON).

## Architecture
- New deterministic assembler `assemble_audit_trail.py` reuses `status.py`'s governance-data loaders, then joins: change-log entries + each artifact's `approval:` block + stale_approvals + `decision_register --list`. Emits a normalized event list sorted by date → JSON.
- **H7 — source-disagreement rule (not just empty-state):** the 4 sources have no referential integrity. When an approval/stale flag has NO corroborating change-log entry or DEC, the trail MUST render it as an explicit **`unreconciled`** row (never silently drop it). An audit view that hides an inconsistency is worse than none.
- Render to ASCII + md (reuse existing render patterns; bilingual labels per `lang`). Register `audit` in the `--viz` view registry.
- **HTML deferred + gated:** if HTML is ever added later, every dynamic field (who_approved, DEC rationale, change-log text) MUST route through `render_html._escape` (`render_html.py:129`) and the test gets the `bug_class` marker. This phase asserts (test) that NO HTML emitter is wired.

## Related Code Files
- Create: `.claude/skills/product-spec/scripts/assemble_audit_trail.py` (reuse status.py loaders; emit events + unreconciled rows)
- Modify: `scripts/visualize.py` (register `audit` view), `references/visualization-spec.md`, SKILL.md view list, CLAUDE.md viz pointer
- Reuse: `status.py` loaders, `change-log.md`, `decision_register.py --list`, snapshot diff

## Implementation Steps
> **TDD:** write step 4 tests FIRST (incl. the orphaned-approval fixture), confirm fail, implement to green, re-run full suite.
1. `assemble_audit_trail.py`: reuse status.py loaders; collect events {date, artifact, action, who_approved, what_drifted, dec_ref}; emit `unreconciled` rows for orphaned approvals/stale flags; sort chronologically; fail-soft on sparse data.
2. Register `audit` in the `--viz` registry; ASCII + md renderers (bilingual labels).
3. Document in visualization-spec.md; assert (test) no HTML emitter is wired (XSS-watch guard).
4. Tests: event join from a fixture with approvals + DEC + change-log; **orphaned-approval fixture → renders an `unreconciled` row (not dropped)**; bilingual labels; empty-state; no-HTML assertion.

## Success Criteria
- [ ] `--viz audit` renders a chronological table (when·artifact·action·who-approved·what-drifted·DEC) in ASCII + md.
- [ ] Reuses status.py loaders (DRY); pulls real change-log + approval + stale_approvals + DEC data.
- [ ] Source disagreement (orphaned approval/stale) renders an explicit `unreconciled` row, never dropped.
- [ ] Bilingual; read-only; ASCII+md only (no-HTML asserted). Tests pass; full suite green.

## Risk Assessment
- Risk: sparse data on young specs → fail-soft + clear empty-state.
- Risk: a 15th view reopening XSS watch IF HTML added → this phase stays ASCII+md + asserts no HTML emitter.
- Sets up E3 (deferred) later — outcome tracking would read the same trail.
