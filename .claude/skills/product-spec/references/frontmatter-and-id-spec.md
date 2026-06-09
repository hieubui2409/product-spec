# Frontmatter & ID Spec

Canonical YAML schema for every artifact under `docs/product/`, plus the parent-scoped ID grammar. **Frontmatter is the source-of-truth.** Scripts parse YAML; the LLM never infers structure from headings.

## ID Grammar

Parent-scoped — globally unique by construction, lineage readable, no central allocator needed.

| Artifact   | Pattern                | Example                          | Notes                                                                                      |
|------------|------------------------|----------------------------------|--------------------------------------------------------------------------------------------|
| BRD goal   | `BRD-G<n>`             | `BRD-G1`, `BRD-G2`               | `<n>` = next free integer in BRD.                                                          |
| PRD        | `PRD-<SLUG>`           | `PRD-AUTH`, `PRD-BILLING`        | `<SLUG>` = uppercase, ≤16 chars, derived from feature-area.                                |
| Epic       | `PRD-<SLUG>-E<n>`      | `PRD-AUTH-E1`, `PRD-AUTH-E2`     | `<n>` = next free integer within that PRD.                                                 |
| Story      | `PRD-<SLUG>-E<n>-S<n>` | `PRD-AUTH-E1-S1`                 | `<n>` = next free integer within that epic.                                                |
| Competitor | `COMP-<SLUG>`          | `COMP-SHOPIFY`, `COMP-BIGCARTEL` | Declared in the BRD's `competitors:` list (the DRY identity home). Same slug rules as PRD. |
| Decision   | `DEC-<n>`              | `DEC-1`, `DEC-2`                 | Parent-free, globally monotonic. Allocated `max+1` in `docs/product/decisions.md`. Never reused. |
| Outcome    | `OUT-<n>`              | `OUT-1`, `OUT-2`                 | Parent-free, globally monotonic. Allocated `max+1` in `docs/product/outcomes.md`. Never reused. |

**Slug rules:** must begin with an uppercase ASCII letter; remaining characters may be uppercase ASCII letters, digits, or hyphens; ≤16 characters total (enforced regex: `^[A-Z][A-Z0-9-]{0,15}$`). Prefer flat slugs (e.g., `AUTH`, `BILLING`, `ONBOARDING`). No spaces, no diacritics. The slug is permanent — renaming a PRD does not update existing epic/story IDs (they keep the original lineage).

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

### Multi-dimensional impact fields (RISK / TIME / COMPETITION)

These optional fields carry the multi-dimensional impact data. All are optional, so a spec that omits them parses and
validates exactly as before (back-compat). **COST is deliberately NOT a field** — it is approximated by the existing
`size: S|M|L` proxy on stories; the skill stores no money/effort figure.

#### `risks` (epic / PRD only)

Optional list, each item:
`{description: str, impact: low|med|high, likelihood: low|med|high, status: open|mitigated|accepted, mitigation: str}`.
`description` is the only required key; `impact`/`likelihood`/`status` are validated against their closed enums (a
risk's `status` is `open|mitigated|accepted`, distinct from an artifact's `draft|review|approved`). Drives the
risk-matrix viz; a top-heavy register (>50% `impact: high`) warns, and a sizeable epic with no risks warns (blind spot).

```yaml
risks:
  - description: "Stripe onboarding/KYC delays a brand's first payout, blocking launch."
    impact: high
    likelihood: med
    status: open
    mitigation: "Pre-collect KYC docs during onboarding, before checkout goes live."
```

#### `target_date` (PRD / epic) and `depends_on` (PRD / epic)

- `target_date` — a single ISO calendar date (`YYYY-MM-DD`). A child due after its parent, or before a prerequisite,
  warns. Only the SHAPE is structural; overdue-vs-today is advisory (a separate `time_advisory.py`, outside the validate
  gate, so `--validate` stays reproducible).
- `depends_on` — a list of artifact IDs this artifact waits on (PRD + Epic only). An unresolved target is `dep_dangling`
  (error); a circular chain is `dep_cycle` (error).

```yaml
target_date: 2026-09-30
depends_on: [ PRD-CHECKOUT-E1 ]
```

#### `competitors` (BRD only) and `competitive_parity` (PRD)

Competitor IDENTITY lives ONCE in the BRD's `competitors:` list (the DRY home). A PRD references those competitors by ID
via the ID-keyed `competitive_parity` map.

- `competitors` — list, each item: `{id: COMP-<SLUG>, name: str, url: str, threat: low|med|high}`. A `url` beginning
  `private:` is dropped before it reaches the graph/render (OpSec chokepoint).
- `competitive_parity` — mapping `{COMP-ID: ahead|parity|behind|none}`. Each key must resolve to a BRD competitor id
  (else `unknown_ref` error); each value is a parity enum.

```yaml
# brd.md
competitors:
  - id: COMP-SHOPIFY
    name: "Shopify"
    url: "https://www.shopify.com"
    threat: high
# prds/checkout.md
competitive_parity:
  COMP-SHOPIFY: behind
```

### `assumptions`, `dependencies`, `out_of_scope` (PRD)

Optional free-text content. These are PRD **body sections** (rendered as optional `<!-- OPTIONAL -->` blocks in the
`prd.md` template), not frontmatter fields. No script reads them from frontmatter. Surfaced during the PRD interview as
narrative prose; for structured ordering dependencies use the frontmatter `depends_on` field instead.

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

Persisted on `--validate` under `docs/product/visuals/.snapshots/<ISO-second>-<content-hash8>.json` (separators stripped from the ISO timestamp; hash is the first 8 hex digits of the SHA-256 of the JSON body). Used by the delta/diff viz.

```json
{
  "snapshot_at": "2026-05-28T10:00:00Z",
  "version": "1.0",
  "generated_at": "2026-05-28T10:00:00Z",
  "product": {
    "name": "Acme Shop",
    "core_value": "Help boutique brands sell directly to fans.",
    "personas": ["shopper", "store-admin"]
  },
  "nodes": [
    {"id": "BRD-G1", "type": "goal", "status": "approved", "scope": "in", "moscow": "must", "horizon": "now"}
  ],
  "edges": [
    {"from": "PRD-AUTH-E1-S1", "to": "PRD-AUTH-E1", "kind": "epic"}
  ],
  "risks": [],
  "competitors": []
}
```

## Findings JSON Schema (script output)

Every structural checker emits a JSON document with this shape (the single authoritative schema home — `validation-rules-spec.md` links here):

```json
{
  "schema_version": "1.0",
  "root": "<absolute project root>",
  "checked_at": "<ISO 8601>",
  "findings": [
    {
      "check": "<check_id, e.g. orphan_story>",
      "severity": "error" | "warn" | "advisory",
      "artifact_id": "<id-or-null>",
      "file": "<path-relative-to-root-or-null>",
      "detail": "<short message>",
      "context": { /* optional structured detail (e.g. {ref, expected, found}) */ }
    }
  ],
  "graph": { /* graph JSON shape — see Snapshot Schema above */ }
}
```

`advisory` severity is emitted ONLY by the out-of-gate `time_advisory.py` (`overdue`); the in-gate checkers emit `error`/`warn` only. Multiple scripts run during `--validate`; the orchestrator merges findings preserving order (traceability → consistency → matrix).

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

## Outcome records (under `outcomes.md` record blocks)

`docs/product/outcomes.md` is an append-only register written by `record_outcome.py`
(the quantitative half of `--learn`). Each measurement is one `---`-fenced YAML block +
a `## OUT-<n>` heading + a free-text note — the SAME storage model as the Decision
Register (text-append, prior records byte-unchanged), NOT a frontmatter list-of-dicts.

An outcome is a measurement-in-time of a BRD goal metric; it POINTS at the goal by ID and
NEVER duplicates the goal definition (title/owner live in `brd.md`). Per-block fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `OUT-<n>` | yes | monotonic, max+1, never reused |
| `goal` | BRD goal ID | yes | must exist in `brd.md` `goals:` (else rejected) |
| `metric` | slug | yes | must be in the referenced goal's `metrics:` (else rejected unless `--force`) |
| `target` | number \| string | yes | captured AT measure time; a non-numeric/0 target → Hybrid (PO asserts verdict) |
| `actual` | number \| string | yes | `actual: 0` is a real measurement (≠ unmeasured), recorded as a normal row |
| `unit` | string | no | e.g. `USD`, `days`, `%` |
| `direction` | `higher` \| `lower` | yes | default `higher`; `lower` = lower-is-better (latency/defects) |
| `measured_on` | ISO 8601 date | yes | the measurement date |
| `source` | string | no | a human LABEL, NEVER a fetchable path (offline) |
| `verdict` | `hit` \| `partial` \| `miss` | yes | numeric → computed (3-tier); non-numeric → PO-asserted |

**Verdict math (deterministic, 3-tier):** `higher` → `ratio = actual/target`; `lower` →
`ratio = target/actual` (`actual=0` → best → hit). `ratio ≥ hit_floor` → hit ·
`partial_floor ≤ ratio < hit_floor` → partial · else miss. Floors default `0.9 / 0.5`,
overridable via `preferences.py` (`outcome_hit_floor` / `outcome_partial_floor`, floats in
`[0,1]` with `partial_floor < hit_floor`; a bad pair is a hard error).

## What This Spec Does NOT Carry

- Engineering estimates (no story points).
- Implementation notes (no code, no architecture decisions).
- Cross-PRD links other than via shared BRD goals.
- Free-form custom fields — adding a new key requires updating this spec first.
