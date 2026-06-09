# Workflow: `--decision` (the Decision Register)

View or record an explicit PO decision (`DEC-<n>`) in `docs/product/decisions.md`. The register
is the **authoritative home for ruled drift**: once a contradiction is ruled, downstream
artifacts point back with `po_ruling_ref: DEC-<n>` rather than re-litigating it.

## Two entry points

- `--decision list` — show the register (the ruled `DEC-<n>` entries, newest first).
- `--decision [ID]` — record a new ruling, or view one by ID.

## How decisions get opened

1. **Auto-opened** — a contradiction with an `approved` artifact surfaces via
   **GATE-NO-SILENT-REVERSAL** (Keep / Change+re-approve / Hybrid). The PO's choice is recorded
   as a `DEC-<n>` so it is never re-litigated.
2. **PO-direct** — `--decision` lets the PO record a ruling they've already made, without a
   triggering contradiction (e.g. "we settled the guest-checkout debate, log it").

## Rules

- Writes go through `decision_register.py --append` (one writer home; structural, deterministic).
- **GATE-NEVER-ASSUME:** never invent or record a `DEC` without explicit PO confirmation of the
  ruling text + rationale.
- **GATE-NO-SILENT-REVERSAL:** a decision that changes an `approved` artifact requires the PO to
  choose Change + re-approve (owner + date); the skill never auto-flips approved content.
- Read of `list` is side-effect-free.

Routing: an ambiguous "we decided X / put that on the record / I made the call" → `--decision`.
Distinct from `--reflect` (recover decisions you FORGOT to log, retroactively from git/.memory).
