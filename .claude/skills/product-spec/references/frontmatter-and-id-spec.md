# Frontmatter & ID Spec

Canonical YAML schema for every artifact under `docs/product/`, plus the parent-scoped ID grammar. **Frontmatter is the source-of-truth.** Scripts parse YAML; the LLM never infers structure from headings.

## ID Grammar

Parent-scoped — globally unique by construction, lineage readable, no central allocator needed.

| Artifact | Pattern | Example | Notes |
|----------|---------|---------|-------|
| BRD goal | `BRD-G<n>` | `BRD-G1`, `BRD-G2` | `<n>` = next free integer in BRD. |
| PRD | `PRD-<SLUG>` | `PRD-AUTH`, `PRD-BILLING` | `<SLUG>` = uppercase, ≤16 chars, derived from feature-area. |
| Epic | `PRD-<SLUG>-E<n>` | `PRD-AUTH-E1`, `PRD-AUTH-E2` | `<n>` = next free integer within that PRD. |
| Story | `PRD-<SLUG>-E<n>-S<n>` | `PRD-AUTH-E1-S1` | `<n>` = next free integer within that epic. |

**Slug rules:** uppercase ASCII letters and digits only; hyphen permitted but prefer flat (e.g., `AUTH`, `BILLING`, `ONBOARDING`). No spaces, no diacritics. The slug is permanent — renaming a PRD does not update existing epic/story IDs (they keep the original lineage).

**Next-`<n>`-within-parent rule:** `generate_templates.py` scans existing siblings (by ID prefix) and assigns `max(siblings) + 1`. On a single `--auto` brain-dump batch the orchestration layer drives a sequence of calls and passes each pre-allocated ID via `--id` (override). The script also accepts an in-process `session_used` list of already-issued IDs in a single batch so it never re-uses one before files are written.

## Universal Fields (every artifact)

| Field | Type | Required | Allowed values | Purpose |
|-------|------|----------|----------------|---------|
| `id` | string | yes | parent-scoped per table above | unique identifier |
| `type` | enum | yes | `vision`, `product`, `brd`, `prd`, `epic`, `story`, `goal`, `exec_summary` | artifact kind |
| `status` | enum | yes | `draft`, `review`, `approved` | lifecycle state |
| `lang` | enum | yes | `en`, `vi` | content language (frontmatter keys stay English) |
| `owner` | string | no | free text | who is accountable |
| `created` | ISO 8601 | yes | e.g. `2026-05-28` | creation date |
| `updated` | ISO 8601 | yes | e.g. `2026-05-28` | last update date |
| `version` | semver-lite | yes | e.g. `0.1.0`, `1.0.0` | major.minor.patch (lean) |

## Parent-Link Fields

Stories, epics, PRDs, and BRD goals carry explicit parent references in frontmatter.

| Artifact | Field name | References | Required |
|----------|------------|------------|----------|
| story | `epic` | epic ID, e.g. `PRD-AUTH-E1` | yes |
| epic | `prd` | PRD ID, e.g. `PRD-AUTH` | yes |
| PRD | `brd_goals` | list of BRD goal IDs, e.g. `[BRD-G1, BRD-G3]` | yes (≥1) |

BRD goals do not carry an explicit `parent` field — BRD is a singleton container and goals attach to PRODUCT directly in the rendered tree.

Resolved by `spec_graph.py` to build the directed graph `story → epic → prd → brd_goal → vision`. A missing referent = `dangling_link` finding. A node with no inbound expected child = `unaddressed_parent` (gap-analysis input — structural only).

## Domain Fields

### `personas`
List of persona **labels** (English keys). Free-text labels chosen by the PO, capped 2–4 by default (soft guidance, not hard limit).

```yaml
personas: [shopper, store-admin]
```

### `scope`
Enum: `in` (this artifact is in-scope for the current release), `out` (explicitly out-of-scope), `core-value` (this artifact is part of the product's stated core value proposition).

`core-value` is the PO's claim; `--validate` asks the LLM to score `aligned | weak | off` against `PRODUCT.md`'s core-value sentence.

### `moscow`
Enum: `must`, `should`, `could`, `wont`. Applied to PRD functional requirements and stories. PRD-level may carry an aggregate; story-level is per-story.

### `horizon`
Enum: `now`, `next`, `later`. Roadmap classification. Roadmap viz groups by this.

### `size` (stories only)
Enum: `S`, `M`, `L`. Coarse PO-level effort indicator (not story points). No engineering-units estimation.

### `metrics`
List of metric references (free-text identifiers). PRDs reference BRD-goal metrics; stories may reference PRD metrics.

```yaml
metrics: [conversion-rate, time-to-checkout]
```

### BRD `goals` (under `brd.md` `goals:` key)

`goals:` is **list-of-dicts**, not a list of bare IDs. Each goal entry MUST carry the following keys; `spec_graph.py` expands them into `type: goal` nodes (`BRD-G<n>`) that PRDs reference via `brd_goals: [BRD-G<n>, …]`. Flat ID strings cause `dangling_link` findings at validate time.

```yaml
# inside brd.md frontmatter
goals:
  - id: BRD-G1                                  # parent-scoped ID, required
    title: "Onboard 100 boutique brands in 12 months"  # required, prose
    metrics: [brands-onboarded]                 # required, ≥1 metric slug
    status: draft                               # required, closed enum
    owner: Jane Doe                             # optional, accountable person; LLM should ask if missing
  - id: BRD-G2
    title: "Achieve 80% 90-day repeat-purchase rate"
    metrics: [repeat-rate-90d]
    status: draft
```

The BRD template (`assets/templates/brd.md`) carries a YAML comment block above `goals:` repeating this shape so a PO opening a freshly generated `brd.md` sees the contract inline.

### `acceptance_criteria` (stories only)
List of strings, each a single AC. Scripts count and presence-check; LLM evaluates testability.

```yaml
acceptance_criteria:
  - "Given a registered user, when they sign in with correct credentials, then they reach the home page."
  - "Given five failed sign-ins, when the user tries again, then the account is rate-limited for 15 minutes."
```

### `risks` (epic / PRD only)
Optional list, each item: `{description: str, impact: low|med|high, likelihood: low|med|high}`. Drives the risk-matrix viz.

### `assumptions`, `dependencies`, `out_of_scope` (PRD)
Optional lists of free-text bullets. Documented in the PRD's frontmatter when surfaced during interview; otherwise omitted.

## Approval Block (when `status: approved`)

When approved, the following sub-block is added:

```yaml
approval:
  approved_by: "Jane Doe"
  approved_at: "2026-05-28"
  approved_version: "1.0.0"
```

`--approve` writes this block, flips `status: approved`, and bumps `version` minor if not already done. Re-approval after a change updates `approved_at` and `approved_version`.

## Session Schema (`.session.md`)

The interview state file. Lives at `docs/product/.session.md`, committed.

```yaml
---
phase: vision | brd | prd | epic | story | done
lang: en | vi
target: <artifact-id-or-slug-being-edited>
answers:
  <question_id>: <value>
pending: [<question_id>, ...]
created: <ISO 8601>
updated: <ISO 8601>
---

# (optional notes body)
```

Resume rule: read `phase` + first `pending` question, resume there.
Stale rule: if `updated > 30 days` OR `answers` reference IDs no longer in the spec → on resume, ask "**Resume from saved state** / **Discard and restart**".

## Snapshot Schema (graph-snapshot JSON)

Persisted on `--validate` under `docs/product/visuals/.snapshots/<ISO>.json`. Used by the delta/diff viz.

```json
{
  "snapshot_at": "2026-05-28T10:00:00Z",
  "nodes": [
    {"id": "BRD-G1", "type": "goal", "status": "approved", "scope": "in", "moscow": "must", "horizon": "now"}
  ],
  "edges": [
    {"from": "PRD-AUTH-E1-S1", "to": "PRD-AUTH-E1", "kind": "epic"}
  ],
  "personas": ["shopper", "store-admin"]
}
```

## Findings Schema (script output)

Every structural checker emits a JSON document with this shape:

```json
{
  "schema_version": "1.0",
  "root": "<absolute project root>",
  "checked_at": "<ISO 8601>",
  "findings": [
    {
      "check": "<check_id, e.g. orphan_story>",
      "severity": "error" | "warn",
      "artifact_id": "<id-or-null>",
      "file": "<path-relative-to-root-or-null>",
      "detail": "<short message>"
    }
  ],
  "graph": { /* graph JSON shape — see snapshot above */ }
}
```

Scripts ALWAYS exit 0. The LLM (orchestration layer) decides what to do with severities; `--strict` gating is the LLM's job, not the script's.

## Frontmatter Examples

### PRODUCT.md

```yaml
---
id: PRODUCT
type: product
status: approved
lang: en
owner: Jane Doe
version: 1.0.0
created: 2026-05-28
updated: 2026-05-28
name: "Acme Shop"
one_line_description: "A web storefront for boutique fashion brands."
current_implementation: "early-stage prototype"
deployment: "single-region Vercel + Postgres on Supabase"
roadmap_one_liner: "Launch checkout flow in Q3; expand to mobile Q4."
core_value: "Help boutique brands sell directly to fans without payment middlemen."
personas: [shopper, store-admin]
---
```

### Story

```yaml
---
id: PRD-AUTH-E1-S1
type: story
epic: PRD-AUTH-E1
status: draft
lang: en
owner: Jane Doe
version: 0.1.0
created: 2026-05-28
updated: 2026-05-28
personas: [shopper]
scope: in
moscow: must
size: S
horizon: now
metrics: [signup-conversion]
acceptance_criteria:
  - "Given a new visitor, when they enter a valid email + password, then a verification email is sent and a placeholder account is created."
  - "Given a visitor with a duplicate email, when they submit, then they see a clear duplicate-email message."
---
```

## What This Spec Does NOT Carry

- Engineering estimates (no story points).
- Implementation notes (no code, no architecture decisions).
- Cross-PRD links other than via shared BRD goals.
- Free-form custom fields — adding a new key requires updating this spec first.
