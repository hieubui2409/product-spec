# Document Model & Hierarchy

The artifact roles, the DRY "one home per fact" rule, and the BRD(1) ↔ PRD(many) relationship. This is the **content-ownership** contract that prevents drift between PRD narrative and story decomposition.

## Hierarchy

```
                    Vision (vision.md)
                       │
                       ▼
                 PRODUCT.md  ◄─── thin labels, source-of-truth facts
                       │
                       ▼
                  BRD (brd.md, singular)
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
            BRD-G1   BRD-G2   BRD-G3   ◄─── goals
              ▲        ▲
              │        │
          ┌───┴───┐    └──────────┐
          ▼       ▼               ▼
       PRD-AUTH  PRD-BILLING   PRD-ONBOARDING
          │
       ┌──┴──┐
       ▼     ▼
   E1    E2
       │
   ┌───┴───┐
   ▼       ▼
  S1      S2
```

- **Vision** (`vision.md`) — strategic narrative; 1-3 year direction; personas; value prop; north-star metric.
- **PRODUCT.md** — *thin* labels-only context file; the DRY home for product facts.
- **BRD** (`brd.md`) — **one BRD per product**; business goals + metrics + stakeholders + constraints + market.
- **PRD** (`prds/<slug>.md`) — **one PRD per feature-area**; many per BRD. Each PRD links to ≥1 BRD goal.
- **Epic** (`epics/<id>.md`) — decomposes a PRD into shipping-sized chunks; carries business context.
- **Story** (`stories/<id>.md`) — single user-facing slice; carries AC.

## Content Ownership (the DRY contract)

| Fact                                                                                       | Lives in                                                      | Why                                                                                                                                        |
|--------------------------------------------------------------------------------------------|---------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| Product name, one-liner, current state, deployment, roadmap one-liner, core-value sentence | `PRODUCT.md`                                                  | thin labels, referenced from every other artifact                                                                                          |
| Persona definitions (narrative)                                                            | `vision.md`                                                   | one place to define; labels-only elsewhere                                                                                                 |
| Persona labels                                                                             | `PRODUCT.md` + each artifact that scopes to specific personas | labels propagate; definitions don't                                                                                                        |
| Business goals + success metrics                                                           | `brd.md`                                                      | single source for goal IDs (`BRD-G<n>`)                                                                                                    |
| Stakeholders, market, constraints                                                          | `brd.md`                                                      | top-of-funnel context                                                                                                                      |
| Competitor identity (`id`/`name`/`url`/`threat`)                                           | `brd.md` `competitors:`                                       | single DRY home for competitor IDs (`COMP-<SLUG>`); a PRD's `competitive_parity` only references these IDs, never re-declares a competitor |
| Feature-area narrative (problem, use cases, NFRs, scope-in/out, deps, risks)               | the PRD                                                       | the PRD is the home of feature-level scope                                                                                                 |
| Functional requirements (MoSCoW list)                                                      | the PRD                                                       | reqs carry the MoSCoW tag, not the stories                                                                                                 |
| Epic goal + business-context links (→ PRD req + BRD goal)                                  | the epic                                                      | epics scope a slice of a PRD                                                                                                               |
| Story narrative (As-a/I-want/so-that) + AC + size + personas                               | the story                                                     | only stories carry AC                                                                                                                      |

## What Lives Where vs Not

**PRD owns:** narrative, scope (in/out), NFRs, success metrics → BRD goals, personas (labels), MoSCoW list of functional requirements, dependencies, open questions.

**PRD does NOT own:** story AC. PRD does NOT enumerate every story — that's the epic/story layer.

**Story owns:** As-a/I-want/so-that statement, AC list, size, persona labels.

**Story does NOT own:** business rationale (that's the epic), feature-level scope (that's the PRD), or product-wide context (that's PRODUCT.md/vision).

**Epic owns:** epic goal, links to (1) the PRD functional requirement it implements and (2) the BRD goal it advances, success criteria for the epic, risks specific to the epic.

## BRD(1) ↔ PRD(many)

One BRD per product. Many PRDs per BRD. The PRD lists which BRD goals it advances (via `brd_goals: [BRD-G1, BRD-G3]`). One BRD goal can be addressed by multiple PRDs — that's expected. Validation flags BRD goals with **zero** PRDs as `orphan_brd_goal` (warn — structural; sufficiency is a separate LLM judgment).

## Impact-Pass vs Catalog (don't conflate)

Two distinct ways "what's affected" is computed — keep them separate:

- **Impact-pass** — the per-CHANGE propagation surface used on `--validate` and `--update`. It runs
  `spec_graph.downstream(<changed-id>)` over the **live** graph for the IDs that actually changed (snapshot-delta), then
  layers a one-line LLM annotation (`dim_touched · one_liner · action`) per affected node and flags it for PO review.
  It is dynamic (depends on *what changed*), partially LLM-graded, and never auto-rewrites prose. Reports to
  `docs/product/impact/<ts>.md` and appends to the existing `affected_set:` change-log field.
- **Catalog** — a *static* enumeration of the whole spec: every node/edge as it exists right now, independent of any
  change. The traceability matrix, the `tree`/`explorer` views, and the snapshot JSON are catalogs. Deterministic,
  no LLM, no notion of "what changed".

Rule of thumb: a **catalog** answers "what exists?"; the **impact-pass** answers "given THIS change, what now needs a
look?". The graph (`spec_graph.py`) is the single source for both, but only the impact-pass consumes the snapshot delta.

## DRY Rule — Why It Matters

If a fact moves (e.g., the core-value sentence is rephrased in PRODUCT.md), every artifact that depends on it should be **flagged for review** (delta-update). The skill does NOT auto-rewrite prose; the PO decides which downstream nodes to refresh.

If a fact is duplicated (e.g., a persona definition copied into vision.md AND a PRD), validation flags it as `duplicate_fact` (LLM judgment, not structural). Default: warn; the PO chooses to consolidate.

## Vision vs PRODUCT.md — Why Both

- **`vision.md`** = narrative, prose, the *story* of the product.
- **`PRODUCT.md`** = labels, one-liners, the *facts* of the product.

The split exists because:
1. **Vision is long-form** and read once by humans; **PRODUCT.md is short-form** and read every interview cycle by the skill (to skip already-answered questions).
2. **Vision changes slowly**; PRODUCT.md changes per release (current implementation, deployment state, roadmap one-liner).
3. The interview adaptivity rule "**skip questions already answered by PRODUCT.md**" needs a compact lookup file.

If the product is tiny, PRODUCT.md may be the only file; vision.md becomes optional. Default = both.

## Status Lifecycle

```
draft → review → approved
            ↑        │
            └────────┘  (re-edit after change)
```

- `draft` — being authored or edited. Default for new artifacts.
- `review` — sent for stakeholder review (no behavior change in the skill; just a flag).
- `approved` — `--approve` sets this with `approval` block. Contradictions are surfaced, not auto-flipped.

The skill never auto-flips `approved` → `draft`. A contradiction is surfaced and the PO chooses keep / change / hybrid (see CLAUDE.md "No silent reversals").

## Cross-Artifact References

References are always by **ID** (frontmatter), never by file path or by prose. Examples:

- `PRD-AUTH.brd_goals: [BRD-G1]` — PRD references BRD goal.
- `PRD-AUTH-E1.prd: PRD-AUTH` — epic references PRD.
- `PRD-AUTH-E1-S1.epic: PRD-AUTH-E1` — story references epic.

Prose may *mention* IDs (`"This story addresses BRD-G1..."`) but those are advisory; the script graph only follows frontmatter.

## When the Hierarchy Bends

Some products won't have all five levels:

| Product size | Hierarchy |
|--------------|-----------|
| Tiny solo project | `PRODUCT.md` + a few stories. |
| Single-feature MVP | `PRODUCT.md` + vision + 1 PRD + stories (skip BRD if no business goals are formal). |
| Standard | full hierarchy. |
| Multi-team | full hierarchy; multiple PRDs per BRD goal. |

The skill never requires upper layers — if BRD is skipped, PRDs simply have an empty `brd_goals` list (validation warns once, then accepts). Default flow encourages the full hierarchy, but supports gradual fill-in.
