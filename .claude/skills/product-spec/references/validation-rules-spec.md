# Validation Rules Spec

The check catalog, the script-vs-LLM ownership split, severity levels, and the findings JSON schema scripts emit. Drives `--validate` and `--approve`.

## Script vs LLM — Non-Negotiable Split

| Layer | Owns |
|-------|------|
| **Script** | Anything answerable by parsing YAML, traversing a graph, counting fields, or matching against a closed enum. |
| **LLM** | Anything requiring reading prose, weighing meaning, or judging quality. |

If a check needs to *understand* the words, it's LLM. If it can be answered by walking edges or counting items, it's script. **No exceptions.** This rule is enforced by the script code review gate — any heuristic in a script that judges quality must be removed.

## Check Catalog

| ID | Owner | Severity | Trigger | Message Template |
|----|-------|----------|---------|------------------|
| `orphan_story` | script | error | a story with a missing or empty `epic` field (no parent reference at all) | "Story {id} has no epic reference." |
| `orphan_epic` | script | error | an epic with a missing or empty `prd` field (no parent reference at all) | "Epic {id} has no PRD reference." |
| `orphan_prd` | script | error | a PRD whose `brd_goals` is empty or missing (not declared). Unresolved IDs in a non-empty `brd_goals` list surface as `dangling_link` instead | "PRD {id} has no BRD goals declared." |
| `orphan_brd_goal` | script | warn | a BRD goal with no PRDs referencing it | "BRD goal {id} has no PRDs addressing it." |
| `dangling_link` | script | error | any frontmatter ID reference that doesn't resolve | "{file}: reference {ref} does not resolve." |
| `unaddressed_parent` | script | warn | a parent (epic/PRD) with zero inbound child edges of the expected type (BRD goals with zero PRDs use `orphan_brd_goal` instead) | "{id} has no {child_type} addressing it (gap-analysis input)." |
| `missing_ac` | script | error | a story with empty / missing `acceptance_criteria` | "Story {id} has no acceptance criteria." |
| `low_ac_count` | script | warn | a story with `len(acceptance_criteria) < 2` | "Story {id} has fewer than 2 acceptance criteria ({count})." |
| `goal_without_metric` | script | error | a BRD goal (`type: goal`) whose `metrics` is empty or missing (frontmatter-and-id-spec requires ≥1 metric slug) | "BRD goal {id} has no success metric; at least one metric slug is required." |
| `dup_id` | script | error | two artifacts sharing the same `id` | "Duplicate ID {id} in {files}." |
| `invalid_id` | script | error | an `id` not matching the parent-scoped grammar | "ID {id} does not match expected pattern {pattern}." |
| `unknown_enum` | script | error | a closed-enum field with a value outside the allowed set (incl. a `risks[]` entry's `impact`/`likelihood` ∈ {low,med,high} or `status` ∈ {open,mitigated,accepted}) | "{file}: field {field} value '{value}' not in {allowed}." |
| `unknown_ref` | script | error | a `competitive_parity` key that does not resolve to any competitor ID declared in the BRD's `competitors:` list — emitted by `check_consistency._check_competitive_parity` | "{id}: competitive_parity key '{ref}' does not resolve to any BRD competitor." |
| `parse_error` | script | error | YAML parse failure or missing required field | "{file}: parse error — {detail}." |
| `status_inconsistency` | script | warn | child `approved` under parent `draft`, or descendant approval newer than ancestor | "{id} status inconsistent with parent {parent_id}." |
| `version_inconsistency` | script | warn | child semver `version` greater than parent's | "{id} version {v} exceeds parent {pid} version {pv}." |
| `self_reference` | script | error | an artifact whose `epic`, `prd`, or `brd_goals` reference points at its own ID | "{id} references itself via `{field}`." |
| `invalid_type` | script | error | a list-typed field that is not a list, a wrong-shape field (e.g. a `risks[]` entry that is not a mapping, a `competitive_parity` that is not a dict), or a closed-enum sub-field (dates, `depends_on` type) with an invalid value (reuse — no separate `invalid_shape`). The artifact `type` field is **directory-derived and trusted** — `check_consistency` does NOT validate it against an enum | "{file}: field {field} value '{value}' is not a valid {expected}." |
| `persona_cap_exceeded` | script | warn | `personas` list with > soft-cap entries (sanity check against spec drift) | "{id}: personas list ({count}) exceeds soft cap ({cap})." |
| `risk_high_ratio` | script | warn | more than `RISK_HIGH_RATIO` (default 0.5) of an artifact's risks are `impact: high` (deterministic ratio) | "{id} has {high}/{total} risks at impact=high (>{pct}%)." |
| `risk_blindspot` | script | warn | an epic with ≥ `RISK_BLINDSPOT_MIN_STORIES` (default 5) child stories and zero declared risks — child-story count is a deterministic graph traversal, NOT an LLM judgment | "{id} has {story_count} child stories but no declared risks." |
| `dep_cycle` | script | error | a circular `depends_on` chain (A→B→…→A) detected by an iterative 3-color DFS (no `RecursionError` on long chains); `context.cycle` carries the closed path | "Circular depends_on chain: {a → b → a}." |
| `dep_dangling` | script | error | a `depends_on` target that does not resolve to a real artifact — same dangling family as `dangling_link` (lives in `check_traceability`) | "{id} depends_on unknown artifact {ref}." |
| `dep_order` | script | warn | A `depends_on` B but A's `target_date` is BEFORE B's — A is due before the prerequisite it waits on (deterministic; fires only when BOTH dates parse) | "{id} target_date {a} is before its prerequisite {b} target_date {b_date}." |
| `time_child_late` | script | warn | a child's `target_date` is AFTER its parent's (an epic due after its PRD finishes) — deterministic date compare, fires only when BOTH dates parse | "{id} target_date {c} is after parent {pid} target_date {p}." |
| `overdue` | script (`time_advisory.py --today`, OUTSIDE the `--validate` gate) | advisory | an artifact whose `target_date` is strictly before `--today` (default real today; pinnable for reproducibility) — consumes the wall clock so it is deliberately NOT a structural gate (keeps the gate byte-reproducible) | "{id} target_date {td} is before today {today} (overdue by {n} days)." |
| `session_md_gitignored` | script | warn | `docs/product/.session.md` matched by a `.gitignore` rule — session state is meant to be committed (resumable across PO sessions) | "docs/product/.session.md is gitignored; session state must be committed." |
| `session_stale` | script (`session_staleness.py`) | warn | `.session.md` `updated` predates the newest artifact `updated` — the session (an authorised assume-source) may assert facts the spec has moved past | "docs/product/.session.md updated {d} predates the newest artifact edit ({id} updated {d2}); re-read before assuming from it." |
| `session_superseded` | script (`session_staleness.py`) | warn | one or more active `DEC-<n>` are dated AFTER `.session.md` `updated` — decisions ruled after the snapshot the session cannot reflect; `decisions.md` is authoritative (Q5), the session is never auto-rewritten | "docs/product/.session.md predates {n} decision(s) [{ids}]; decisions.md is authoritative — verify the session does not contradict them." |
| `invest_quality` | LLM | warn | a story failing INVEST (Independent, Negotiable, Valuable, Estimable, Small, Testable) | "Story {id}: INVEST concern — {dimension}: {explanation}." |
| `vagueness` | LLM | warn | a story or PRD requirement using vague language ("should", "easy", "fast") without quantification | "{id}: vague language — '{phrase}'. Suggest quantification." |
| `core_value_drift` | LLM | warn | an artifact's narrative drifts from PRODUCT.md's core-value sentence | "{id}: core-value alignment is {aligned\|weak\|off}: {rationale}." |
| `gold_plating` | LLM | warn | scope expansion beyond the stated PRD problem | "{id}: gold-plating — {addition} not motivated by stated problem." |
| `semantic_duplication` | LLM | warn | two artifacts express the same intent in different words | "{id1} ≈ {id2}: semantic duplication detected — {explanation}." |
| `time_realism` | LLM (anchored to SCRIPT-precomputed numbers — see scaffold below) | warn | an epic's deadline is unrealistic for its scope — flag ONLY when all anchors present AND `size=='L'` AND `child_story_count>=6` AND `days_remaining<21`; uncertain/missing anchor → no-flag | "{id}: deadline likely unrealistic — size {size}, {child_story_count} stories, {days_remaining} days to {target_date}." |
| `competitive_drift` | LLM (anchored to SCRIPT-resolved parity — see scaffold below) | warn | a core-value PRD is losing its competitive edge — flag ONLY when `eligible` (scope=='core-value' AND `competitors_with_data>=2`) AND EVERY real (non-`none`) parity is `behind`; wrong scope / <2 data / any non-`behind` → no-flag | "{id}: competitive drift — behind on every tracked competitor ({all_behind_competitors}); scope core-value." |
| `contradiction` | LLM | error | a new claim contradicts an `approved` artifact | "{id} contradicts approved {other_id}: {contradiction}. SURFACE TO PO — never auto-flip." |

## `--strict` Gate Behavior

Default behavior (no `--strict`):
- All findings reported.
- The skill proceeds with whatever action was requested.

With `--strict`:
- Any finding with `severity: error` blocks the action.
- The skill stops and presents the errors; the PO must resolve before proceeding.
- `severity: warn` never blocks.

The gate is enforced in the **LLM/orchestration layer** (workflow-validate.md), not in the scripts. The analytical findings-emitters (`check_traceability`, `check_consistency`, `build_traceability_matrix`, `spec_graph`) always exit 0 with JSON on stdout; the LLM reads severities and decides. (`visualize` and `generate_templates` are a renderer and a generator, not findings-emitters: they exit non-zero on a user CLI error — e.g. an empty-after-`--layers` filter or an unresolved template token — by design.) The sole exception in the gate path is `strict_gate.py`, a CI-side wrapper that re-runs the analytical scripts, applies the gate, and exits `2` on `error` findings — usable from shell pipelines without an LLM.

## Severity Definitions

- **error** — the spec is structurally broken (orphan, dangling link, missing AC, dup ID, dependency cycle, dangling dependency) or contradicts an approved decision. With `--strict`, blocks.
- **warn** — the spec is structurally OK but may have a quality issue (low AC count, vague language, status inconsistency, unaddressed parent, child due after parent, dependency-order conflict). Never blocks; advisory.
- **advisory** — emitted ONLY by the out-of-gate `time_advisory.py` (`overdue`). It consumes the wall clock, so it is never part of the reproducible `--validate` gate; the script always exits 0. Informational only.

## Core-Value Scoring (LLM)

For every PRD/epic/story, the LLM scores against `PRODUCT.md`'s `core_value` sentence:

| Score | Meaning |
|-------|---------|
| `aligned` | clearly serves the core value |
| `weak` | tangentially serves; could be cut without harm to core |
| `off` | does not serve the core value |

Score + 1-line rationale included in the finding. The PO confirms the `scope: core-value` tag (or chooses `scope: in` / `scope: out`); the script only validates that the tag is one of the allowed enum values.

## `time_realism` LLM Scaffold (anchored — never date-math by the LLM)

`time_realism` is an LLM-judgment warn ("this deadline is unrealistic for this scope"), but it is **pinned to structured, script-precomputed numbers** so the LLM cannot hallucinate (the classic over-flag). The split:

- **Script half** — `scripts/time_realism_anchors.py --root <root> [--today YYYY-MM-DD]` pre-computes, per **epic**, the anchor record:

  ```json
  {"artifact_id": "PRD-X-E1", "file": "epics/PRD-X-E1.md", "type": "epic",
   "size": "L", "horizon": "now",
   "target_date": "2026-06-15", "today_date": "2026-06-01",
   "days_remaining": 14, "child_story_count": 6, "incomplete": true,
   "eligible": true}
  ```

  `days_remaining = (target_date − today).days` and `child_story_count` (a graph traversal) are computed **here, by the script** — the LLM does NO date arithmetic. `today_date` comes from the pinnable `--today` (default real today; **evals/tests PIN it** so the anchor — and the gate — is reproducible). When `target_date` or `size` is absent the anchor is still emitted with that field null and `eligible: false`.

- **LLM half** — apply this FIXED rule to each anchor (no prose, no velocity speculation):

  | Anchor state | LLM output |
  |--------------|------------|
  | `eligible == false` (any required anchor null) | `{finding: null, reason: "missing_anchor"}` |
  | `size == "L"` AND `child_story_count >= 6` AND `days_remaining < 21` | a `time_realism` **warn** (see below) |
  | otherwise (eligible but rule not met) | `{finding: null, reason: "below_threshold"}` |

  The conservative default is **no-flag**: if uncertain, or any anchor is missing, do not flag.

- **The finding REQUIRES cited data.** A `time_realism` warn MUST carry `context.cited_data` = `{size, child_story_count, days_remaining, target_date, horizon}` (verbatim from the anchor) plus `context.threshold_crossed` (which conditions tripped). A finding without `cited_data` is invalid (this is what the hallucination evals — `eval/evals.json` ids 8-10 — gate).

This mirrors the Script-vs-LLM split (CLAUDE.md): the structural numbers are deterministic Python; only the "is this realistic" judgment is the LLM's, and even that is reduced to a fixed threshold over script-supplied numbers.

## `competitive_drift` LLM Scaffold (anchored — never parity-guessed by the LLM)

`competitive_drift` is an LLM-judgment warn ("this PRD is losing its competitive edge"), the COMPETITION sibling of `time_realism`. "Mất lợi thế" is the classic over-flag, so the LLM is **pinned to structured, script-resolved parity anchors** and forbidden from inventing a competitor or a parity verdict. The split:

- **Script half** — `scripts/competitive_drift_anchors.py --root <root>` resolves each PRD's ID-keyed `competitive_parity` map against the BRD's DRY competitor identity home (`graph['competitors']`) and pre-computes, per **PRD**, the anchor record:

  ```json
  {"artifact_id": "PRD-CHECKOUT", "type": "prd", "scope": "core-value",
   "competitive_parity": [{"competitor_id": "COMP-ACME", "competitor": "Acme Commerce", "parity": "behind"},
                          {"competitor_id": "COMP-SHOPIFY", "competitor": "Shopify", "parity": "behind"}],
   "competitors_with_data": 2, "all_behind_competitors": ["Acme Commerce", "Shopify"],
   "incomplete": true, "eligible": true}
  ```

  `competitors_with_data` (the count of parity entries whose value is NOT `none`), the resolved competitor NAMES, and `all_behind_competitors` are computed **here, by the script** — the LLM does NO counting and never re-parses `brd.md`. `none` parity means "tracked, no verdict yet" and is **not** a data point. A parity KEY that does not resolve to a BRD competitor is dropped from the resolved block (its `unknown_ref` error is the consistency check's job) so the LLM never sees a phantom competitor. `eligible = (scope == "core-value" AND competitors_with_data >= 2)` — the anchored gate. PRDs with no `competitive_parity` map are not emitted (a v1 PRD is not a drift unit). Output is sorted by `artifact_id` → deterministic. The script NEVER decides flag/no-flag.

- **LLM half** — apply this FIXED rule to each anchor (no prose, no market speculation):

  | Anchor state | LLM output |
  |--------------|------------|
  | `eligible == false` (scope ≠ core-value, OR `competitors_with_data < 2`) | `{finding: null, reason: "missing_anchor"}` |
  | `eligible == true` AND EVERY real (non-`none`) parity is `behind` (i.e. `len(all_behind_competitors) == competitors_with_data`) | a `competitive_drift` **warn** (see below) |
  | otherwise (eligible but at least one real parity is `ahead`/`parity`) | `{finding: null, reason: "below_threshold"}` |

  The conservative default is **no-flag**: if uncertain, scope is not core-value, there are fewer than 2 real verdicts, or any tracked competitor is NOT `behind`, do not flag.

- **The finding REQUIRES cited data.** A `competitive_drift` warn MUST carry `context.cited_data` = `{scope, competitors_with_data, all_behind_competitors, competitive_parity}` (verbatim from the anchor) plus `context.threshold_crossed` (which conditions tripped). A finding without `cited_data` is invalid (this is what the hallucination evals — `eval/evals.json` ids 11-13 — gate).

This mirrors `time_realism` exactly: the structural resolution + counting is deterministic Python; only the "is this drift" judgment is the LLM's, and even that is a fixed rule over script-supplied parity anchors.

## Impact-Pass LLM Scaffold (per-change propagation — distinct from the catalog checks)

The **impact-pass** answers "I changed X — what downstream is affected, and how?" It runs on `--update` (one explicit `changed_id`) AND on `--validate` (change-set derived from the snapshot delta — `workflow-validate.md → Step 2.5`). It is **per-CHANGE propagation**, NOT a per-ARTIFACT quality check — keep it separate from `risk_blindspot`/`time_realism`/`competitive_drift` so neither bloats the other. The split:

- **Script half (deterministic)** — `spec_graph.downstream(graph, changed_id)` returns the transitive child closure (iterative, cycle-safe). On `--validate` the change-set itself is deterministic: the `delta` view's added ∪ changed nodes between the two most-recent `.snapshots/` (`spec_graph.diff_graphs` for added/removed + `spec_graph.changed_nodes` for the per-node field diff — the single home for the tracked-field set `spec_graph.CHANGED_FIELDS`, the same rule `render_ascii.delta` displays); no previous snapshot → empty change-set → no impact-pass. The script NEVER interprets.

- **LLM half (judgment)** — for each affected node, emit one annotation record:

  ```json
  {"node": "PRD-AUTH-E1-S1", "dim_touched": "ac",
   "one_liner": "AC still references the pre-change scope wording.",
   "action": "review AC"}
  ```

  - `dim_touched` ∈ a **closed enum** — `{scope, risk, time, competition, ac, traceability}` — so the annotation stays bounded (an open-vocabulary tag would drift). Pick the single most-affected dimension.
  - `one_liner` — ONE sentence on HOW the change reaches this node; grounded in the node's actual content, never speculative.
  - `action` — a concrete suggestion: `review` / `review AC` / `re-estimate` / `split` / `re-approve` / `no-op`.
  - **Conservative default:** a node reachable but plausibly unaffected → `action: no-op` with a one-liner saying so; do not invent downstream damage.

- **Approved + contradicted** → if an affected node is `status: approved` AND the change contradicts its content, run the **Contradiction Protocol** below (keep/change/hybrid). The impact-pass NEVER auto-flips an approved artifact — this is the deal-breaker the `impact-pass` eval's approved branch gates.

- **Output** — the annotation records become the rows of `docs/product/impact/<ts>.md` (skeleton `assets/templates/impact-report.md`) and the `dims` (the union of `dim_touched`) + `affected_set` of the change-log entry.

This mirrors the Script-vs-LLM split exactly: `downstream()` + the snapshot delta are deterministic Python; only the dimension/interpretation/action is the LLM's.

## Contradiction Protocol (CRITICAL — never auto-flip)

When the LLM detects a contradiction with an `approved` artifact:

1. Emit a finding with `severity: error` and `check: contradiction`.
2. The orchestration layer presents three options to the PO via AskUserQuestion:
   - **Keep** the approved version, reject the new claim.
   - **Change** to the new claim — requires re-approval of the affected artifact(s).
   - **Hybrid** — record both, define a follow-up to reconcile.
3. The skill **never** auto-edits the approved artifact based on the contradiction. The PO decides.

This mirrors the global "No silent reversals" rule in CLAUDE.md.

## Findings JSON Schema (script output)

→ `frontmatter-and-id-spec.md` § Findings JSON Schema (single authoritative home for the script-output JSON shape).

## Human Report Format (LLM layer)

After scripts run and LLM judgment layers on:

```
# Validation Report — <date>

## Summary
- 23 artifacts checked
- 0 errors · 3 warnings
- Strict gate: OFF (no errors block; warns advisory)

## Errors (0)
(none)

## Warnings (3)

### PRD-AUTH-E1-S2 — low_ac_count (warn)
File: stories/PRD-AUTH-E1-S2.md
Detail: Story has 1 acceptance criterion. Suggest ≥2.

### PRD-BILLING — core_value_drift (warn — LLM)
File: prds/billing.md
Detail: Core-value alignment is "weak": billing flow is tangential to "help boutique
brands sell directly". Consider whether this PRD belongs in the next horizon.

### BRD-G3 — orphan_brd_goal (warn)
File: brd.md
Detail: No PRDs address this goal. Either drop, defer, or write a PRD.

## Suggested Next Steps
1. Add 1 more AC to PRD-AUTH-E1-S2.
2. PRD-BILLING: discuss core-value alignment with stakeholders.
3. BRD-G3: decide between drop / defer / new PRD.
```

## What This Spec Does NOT Define

- The exact prose template for the human report — that's the LLM's job.
- The order of script invocations — that's `workflow-validate.md`.
- The interactive flow on `contradiction` — that's `workflow-validate.md`.
- The change-set derivation + report-write steps of the impact-pass — those are `workflow-validate.md → Step 2.5` (`--validate`) and `workflow-update.md → Steps 2/3/6` (`--update`); this spec defines only the LLM annotation rule.
- Eval rubric for the LLM judgment checks — that's `eval/evals.json`.
