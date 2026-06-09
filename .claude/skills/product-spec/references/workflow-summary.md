# Workflow: `--summary` (audience brief FROM the spec)

Generate a **1-page audience brief** rendered from the existing spec — never a new source of
truth, always a projection of `docs/product/`. One flag, two audiences via `--audience`:

| `--audience` | Produces | Source |
|--------------|----------|--------|
| `exec` (default) | The exec one-pager (`exec-summary.md`) — vision, core value, the BRD goals + metrics, PRD/epic shape, status roll-up. | the live spec graph |
| `release-notes` | "What changed since the last approved snapshot" — the delta narrative. | the governance audit trail (change-log · approvals · decisions) |

- **Same source-of-truth + same render path, different audience** — `release-notes` is NOT a new
  top-level flag, just the other `--audience` value. Keep them on one code path.
- `exec` is the unchanged default (a flagless `--summary` = the exec one-pager).
- `release-notes` reads the audit trail (`assemble_audit_trail.py`), so it only has content once
  there is at least one approved snapshot to diff against; otherwise say so plainly, don't fabricate.
- Read-only: `--summary` renders a brief; it never edits a spec artifact.
- Renders `md` (default) / `html`; HTML escapes every dynamic field server-side (shared design system).

Routing: an ambiguous "give me a one-pager / brief for my sponsor / what changed for release"
ask → `--summary` (pick `--audience` by whether they want the current state vs the delta).
Distinct from `--viz` (a picture) and `--export` (a full self-contained slice, not a 1-pager).
