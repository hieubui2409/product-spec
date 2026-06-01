<!--
TEMPLATE: decision-record.md — one record block appended to
docs/product/decisions.md by decision_register.py (--append) on every explicit
PO ruling: a standalone --decision, or a Keep/Change/Hybrid resolve of a
contradiction against an approved artifact.

The register is APPEND-ONLY: a new ruling is added; an obsolete one is marked
`status: superseded` and the new record carries `supersedes: DEC-<n>`. IDs are
parent-free, globally monotonic (`DEC-<n>`, allocated max+1 — never reused).

DRY GUARD — what a decision record holds, and what it must NEVER hold:
  HOLDS  : the PO ruling + its one-paragraph RATIONALE + ID links
           (`affects: PRD-AUTH-E1`, `supersedes: DEC-3`). Links, not copies.
  NEVER  : structural facts that already have an authoritative home — a persona
           narrative (lives in vision.md), a business goal (brd.md), a feature
           scope or AC (the PRD/story). A decision POINTS at those by ID; it does
           not duplicate them. Copying a fact here creates a second source of
           truth that drifts. Reference `affects:` by ID and stop.

Bilingual: the prose (title + rationale) localizes per the session `lang`; the
frontmatter keys and the `DEC-<n>` id stay English (CLAUDE.md → Bilingual
Conventions).
-->

---
id: {{id}}
status: {{status}}
date: {{date}}
affects: {{affects}}
supersedes: {{supersedes}}
---

## {{id}} — {{title}}

{{rationale}}
