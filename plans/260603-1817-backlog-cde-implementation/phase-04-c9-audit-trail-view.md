---
phase: 4
title: "C9 audit-trail view"
status: pending
priority: P2
effort: "1d"
dependencies: []
---

# Phase 4: C9 audit-trail view (`--audit` / `--viz audit`)

## Overview
A read-only governance view that joins the audit data the skill ALREADY captures (change-log,
approval metadata, stale approvals, decision register) into one chronological table:
*when · artifact · action · who-approved · what-drifted · DEC*. Mostly assembly, not new capture.

## Requirements
- Functional: a read-only view rendering a chronological audit trail; ASCII + markdown output; bilingual via session `lang`.
- Non-functional: viewer is read-only (edits only via interview flags); deterministic struct from script; no network.

## Key facts (from research)
- `.snapshots/` (`spec_graph.py:519` write, hash-named) + `diff_graphs()`/`changed_nodes()` (`:469`,`:492`); `CHANGED_FIELDS=(status,scope,moscow,horizon,size,body_hash)`.
- `change-log.md` (append-only, newest-top) from template `change-log-entry.md` (has `date/action/author/affected_set/dims`).
- Approval metadata: frontmatter `approval:{approved_by,approved_at,approved_version}` (`frontmatter-and-id-spec.md:171`).
- `status.py:207` `stale_approvals` (approved but changed since baseline).
- DEC register parseable via `decision_register.py --list` (JSON).
- Web best-practice: audit trail = chronological, who/what/when/why, version metadata, exportable.

## Architecture
- New deterministic assembler reads: `change-log.md` entries + every artifact's `approval:` block + `status.py` stale_approvals + `decision_register.py --list`. Emits a normalized event list sorted by date.
- Render to ASCII + md (reuse existing render patterns; bilingual labels per `lang`). HTML deferred (YAGNI; add later only if asked — must reuse `_escape`/DOMPurify chokepoint if so).
- Wire as a `--viz audit` view (preferred — reuses visualization plumbing) OR a standalone `--audit`; pick `--viz audit` to avoid a new top-level flag (KISS, fewer CLI-surface additions).

## Related Code Files
- Modify: `.claude/skills/product-spec/scripts/visualize.py` (register `audit` view) and/or a new `scripts/assemble_audit_trail.py` (deterministic event join)
- Reuse: `change-log.md`, `decision_register.py --list`, `status.py` stale_approvals, snapshot diff
- Modify: `.claude/skills/product-spec/references/visualization-spec.md` (document the view), SKILL.md view list, CLAUDE.md viz pointer row

## Implementation Steps
> **TDD:** write step 4's tests FIRST (event-join from a fixture spec w/ approvals+DEC+change-log, bilingual labels, empty-state), confirm they fail, then implement the assembler + renderers to green; re-run full suite.
1. Write `assemble_audit_trail.py`: collect events {date, artifact, action, who_approved, what_drifted, dec_ref}; sort chronologically; emit JSON. Handle empty/missing gracefully (fail-soft).
2. Add `audit` to the `--viz` view registry; ASCII + md renderers (bilingual labels).
3. Document in visualization-spec.md + add to the view count (mind the C8 "14 views" security-regression watch — if HTML added later, escape discipline applies).
4. Tests: event join from a fixture spec with approvals + DEC + change-log; bilingual label render; empty-state.

## Success Criteria
- [ ] `--viz audit` renders a chronological table (when·artifact·action·who-approved·what-drifted·DEC) in ASCII + md.
- [ ] Pulls real data from change-log + approval frontmatter + stale_approvals + DEC register (no new capture layer).
- [ ] Bilingual (EN/VI) labels; read-only; no network.
- [ ] Tests pass; 50 existing untouched.

## Risk Assessment
- Risk: data sources sparse on young specs → fail-soft + clear empty-state, no crash.
- Risk: adding a 15th view reopens the XSS watch IF HTML is added → keep this phase ASCII+md only; HTML is a separate later decision under escape discipline.
- Sets up E3 (deferred) later — outcome tracking would read the same trail.
