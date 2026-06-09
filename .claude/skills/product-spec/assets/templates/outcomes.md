<!--
TEMPLATE: outcomes.md — one record block appended to
docs/product/outcomes.md by record_outcome.py on every `--learn` measurement
(the quantitative half of the learning loop).

The register is APPEND-ONLY: each measurement adds a new OUT-<n> block; prior
records stay byte-unchanged. IDs are parent-free, globally monotonic
(`OUT-<n>`, allocated max+1 — never reused), mirroring the Decision Register.

DRY GUARD — what an outcome record holds, and what it must NEVER hold:
  HOLDS  : one measurement-in-time of a BRD goal metric — target (as captured at
           measure time), actual, unit, direction, measured_on, source label,
           the computed/asserted verdict, and a free-text note. It POINTS at the
           goal by ID (`goal: BRD-G<n>`).
  NEVER  : the goal DEFINITION (title/owner/status — those live in brd.md). An
           outcome is the actual; the goal is the spec. They stay decoupled so the
           BRD schema is untouched and a goal can be measured many times.

`source` is a human LABEL ("monthly-benefit-report 2026-05"), NOT a fetchable
path — this skill is offline; the PO exports analytics to a value, the register
records it. `verdict`: numeric metrics → computed by record_outcome.py
(deterministic); non-numeric → PO-asserted (Hybrid B3).

Bilingual: the note prose localizes per the session `lang`; frontmatter keys and
the `OUT-<n>` id stay English.
-->

---
id: {{id}}
goal: {{goal}}
metric: {{metric}}
target: {{target}}
actual: {{actual}}
unit: {{unit}}
direction: {{direction}}
measured_on: {{measured_on}}
source: {{source}}
verdict: {{verdict}}
---

## {{id}} — {{metric}} @ {{measured_on}}

{{note}}
