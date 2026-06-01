# Workflow — Validate / Approve / Summary

End-to-end workflow for the **--validate** (+ optional **--strict**), **--approve**, and **--summary** flags. Operationalizes the script-vs-LLM split: scripts produce JSON; the LLM layers judgment; the report is composed for a human PO.

## `--validate` Flow

### Step 1 — Run structural scripts (in order)

```bash
./.claude/skills/.venv/bin/python3 scripts/spec_graph.py --root <root> --snapshot
./.claude/skills/.venv/bin/python3 scripts/check_traceability.py --root <root>
./.claude/skills/.venv/bin/python3 scripts/check_consistency.py --root <root>
./.claude/skills/.venv/bin/python3 scripts/build_traceability_matrix.py --root <root> --write
```

Each script emits JSON to stdout. Collect the union of `findings[]` across the three checkers. `spec_graph --snapshot` writes a snapshot JSON to `docs/product/visuals/.snapshots/` for later delta viz.

The structural checkers above now also emit the TIME-dimension findings: `dep_cycle` + `dep_dangling` (errors, from `check_traceability`) and `dep_order` + `time_child_late` (warns, from `check_consistency`). These are pure date/graph comparisons — deterministic, in-gate (G-B1).

**Out-of-gate advisories (run separately, NEVER part of the `--strict` gate — they consume the wall clock or resolve external references):**

```bash
# overdue: target_date strictly before --today (default real today; pin for reproducibility)
./.claude/skills/.venv/bin/python3 scripts/time_advisory.py --root <root> [--today YYYY-MM-DD]
# time_realism anchors: per-epic {size, child_story_count, days_remaining, …} feeder for the LLM check
./.claude/skills/.venv/bin/python3 scripts/time_realism_anchors.py --root <root> [--today YYYY-MM-DD]
# competitive_drift anchors: per-PRD resolved parity map feeder for the LLM check (no --today)
./.claude/skills/.venv/bin/python3 scripts/competitive_drift_anchors.py --root <root>
```

All three exit 0 on a valid run regardless of how many overdue/anchor items they surface (advisories/anchors, not gates) — the calendar never blocks. They exit non-zero ONLY on a malformed CLI argument (e.g. a non-ISO `--today`), which is input validation, not a finding. Surface `overdue` to the PO as information; feed the `time_realism` and `competitive_drift` anchors to the LLM pass in Step 2. Keep these OUT of `strict_gate.py` so the structural gate stays byte-reproducible (G-A4).

For CI (no LLM in the loop), use the shell-runnable strict gate which exits non-zero on any error-severity finding:

```bash
./.claude/skills/.venv/bin/python3 scripts/strict_gate.py --root <root>
```

### Step 2 — Layer LLM judgment on the JSON

#### Step 2.0 — Consult the judgment cache FIRST (incremental: judge only stale nodes)

Before running any LLM pass below, ask the cache which nodes actually need re-judging. A re-validate of an unchanged spec must issue **zero** LLM calls on the single-node checks — the cache reuses the prior verdict for any node whose body (and core-value dependency) is unchanged. The cache is the SCRIPT half (deterministic key + staleness); the LLM only judges the stale set and produces the verdict (Script-vs-LLM split).

The cache key is `check | scope_key | hash(es) | lang | dep_hash`, computed by `scripts/judgment_cache.py` from the graph `body_hash`. Per-check consult, passing the **caller-supplied** model id:

```bash
# Per single-node check (invest_quality / vagueness / gold_plating / core_value_drift /
# time_realism / competitive_drift), one consult over its candidate node ids:
./.claude/skills/.venv/bin/python3 scripts/judgment_cache.py --root <root> \
  --check --check-name <check> --node-ids <ID> --model-id <current-model-id>
# semantic_duplication is a PAIR check: pass the two ids; the key is order-independent.
./.claude/skills/.venv/bin/python3 scripts/judgment_cache.py --root <root> \
  --check --check-name semantic_duplication --node-ids <IDA>,<IDB> --model-id <current-model-id>
```

- **`--model-id` is caller-supplied — pass the CURRENT model id.** The script NEVER self-detects the running model (that is non-deterministic session state, Script-vs-LLM split). The orchestration layer knows its own model and passes it; the script stamps + compares it as opaque data. A **different `--model-id`** — or a bumped `cache_version` — is a **full miss** (every entry stale → safe full re-validate): a model change can shift every judgment.
- **`fresh`** (cache hit) → reuse the stored verdict verbatim; **do NOT call the LLM** for that node. **`stale`** → the LLM judges it in the matching pass below.
- **`contradiction` is NEVER cached** — skip the consult for it entirely; it always runs (Step 2's `contradiction` bullet). The script refuses a contradiction key (defensive).
- **`--no-cache`** → bypass the cache entirely (every node stale); use when a verdict policy changed and a clean full re-judge is wanted.
- **Ruled-drift (`po_ruling_ref`):** a fresh hit may carry `po_ruling_ref: DEC-n` (a REFERENCE — `decisions.md` is authoritative; see § Decision Register wiring). Surface the prior ruling instead of re-nagging. On a **stale** entry the consult returns `prior_po_ruling_ref: DEC-n` when the same node+check was previously ruled under different wording — the body changed, so re-judge the content, BUT consult `decisions.md` for the active DEC and **surface it** ("you accepted DEC-n for the prior wording — still applies?") rather than silently re-flagging (no-silent-reversal, G-A3; reuses the `decisions.md` plumbing wired below).

For each check in `validation-rules-spec.md` whose **owner = LLM**, run a separate pass **over its stale set only**:

- **invest_quality** — for every story: check Independent · Negotiable · Valuable · Estimable · Small · Testable. If any dimension fails, emit a finding (warn).
- **vagueness** — scan story AC and PRD MoSCoW lists for vague terms (`should`, `easy`, `fast`, `intuitive`, `robust`); if found, emit a finding suggesting a quantified rewrite.
- **core_value_drift** — for each PRD/epic/story, score alignment with `PRODUCT.md.core_value` as `aligned | weak | off` + a 1-line rationale. Emit a finding (warn) when `weak` or `off`.
- **gold_plating** — scan PRD scope: does any new requirement go beyond the stated problem? Emit finding (warn).
- **semantic_duplication** — compare every pair of PRDs/epics within the same product for intent overlap. Emit finding (warn) on suspected duplicates.
- **time_realism** — for each epic, read the SCRIPT-precomputed anchor from `time_realism_anchors.py` (`size`, `child_story_count`, `days_remaining`, …) and apply the FIXED rule in `validation-rules-spec.md → time_realism LLM Scaffold`: flag (warn) ONLY when `eligible` AND `size=="L"` AND `child_story_count>=6` AND `days_remaining<21`; missing anchor → `missing_anchor` (no flag); otherwise no flag. The finding MUST carry `context.cited_data` (verbatim from the anchor). **Do NO date arithmetic** — the script already computed `days_remaining`.
- **competitive_drift** — for each eligible PRD, read the SCRIPT-resolved anchor from `competitive_drift_anchors.py` and apply the FIXED rule in `validation-rules-spec.md → competitive_drift LLM Scaffold`: flag (warn) ONLY when `eligible` (scope `core-value` AND `competitors_with_data >= 2`) AND every real (non-`none`) parity is `behind`; missing anchor / ineligible / any non-`behind` → no flag. The finding MUST carry `context.cited_data` (verbatim from the anchor). **Never invent a competitor or parity verdict** — use only what the script resolved.
- **contradiction** — compare every new artifact against `approved`-status artifacts. If contradicted → emit `error`-severity finding + surface to PO via the contradiction protocol (see below). **Never auto-flip.**

#### Step 2.9 — Store the new verdicts + GC the cache (after the LLM pass)

Once the LLM has judged the **stale** set, persist each new verdict so the next re-validate reuses it. Store under the key the consult returned (`--store` is a no-op under `--no-cache`):

```bash
./.claude/skills/.venv/bin/python3 scripts/judgment_cache.py --root <root> \
  --store --key "<key-from-consult>" --verdict '<verdict-json>' --model-id <current-model-id> \
  [--po-ruling-ref DEC-n]
```

- Store the SAME caller-supplied `--model-id` used for the consult — a stamp mismatch resets the cache, so consult and store must agree on the model.
- `--po-ruling-ref DEC-n` attaches the active ruling reference to the verdict when the PO confirmed a drift (the reference points at `decisions.md`; never copy the rationale — DRY). On the next clean re-validate the fresh hit surfaces `po_ruling_ref` so the drift is not re-nagged.
- **`contradiction` is never stored** (the script refuses a contradiction key).
- **Garbage-collect deleted nodes.** A node removed from the spec must not leave a dead single-node or pair entry behind (and a reused id must not collide with a stale verdict). Evict by set-difference vs the current graph node ids — run once per `--validate`:

  ```bash
  ./.claude/skills/.venv/bin/python3 scripts/judgment_cache.py --root <root> --gc
  ```

The cache is an OPTIMIZATION, never authoritative: a miss is always safe (re-judge). `strict_gate.py` is structural-only (LLM-free) and never consults the cache, so CI reproducibility never depends on it.

### Step 2.5 — Impact-pass (per-change propagation; runs on `--validate` too)

The impact-pass is the per-CHANGE propagation surface — `downstream()` + an LLM `{dim_touched, one_liner, action}` per affected node — and it runs on `--validate` as well as `--update` (it is per-CHANGE, distinct from the per-ARTIFACT catalog checks above). On `--update` there is one explicit `changed_id`; on a whole-spec `--validate` there is none, so **derive the change-set from the snapshot delta**:

1. **Get the change-set from the snapshot delta.** Step 1 already wrote a fresh snapshot to `docs/product/visuals/.snapshots/`. Compare it to the **previous** snapshot (the second-most-recent — the freshly-written one is the current state, not a baseline). Derive the change-set by comparing the two snapshot node dicts directly:
   - **Added IDs:** `spec_graph.diff_graphs(current, previous)` returns `{added, removed, product_changes}` — `added` carries the new node IDs.
   - **Changed IDs:** `spec_graph.changed_nodes(current, previous)` returns the IDs of nodes present in BOTH snapshots whose any tracked field differs. The tracked-field set is the single shared home `spec_graph.CHANGED_FIELDS` (`status`/`scope`/`moscow`/`horizon`/`size` + `body_hash`) — the SAME rule the `--viz delta` surface uses, so a body-only edit (frontmatter unchanged, `body_hash` differs) is caught here too. **Do NOT re-implement the field comparison inline** — call `changed_nodes` so the rule stays in one place.
   - **Baseline-missing-`body_hash` (no first-validate flood):** `changed_nodes` counts a field only when it is PRESENT on both sides AND differs. A `body_hash` ABSENT on the previous snapshot (an old pre-upgrade snapshot taken before this field existed) is UNKNOWN → not a body change, so the first post-upgrade `--validate` flags only nodes with a real frontmatter diff (it does not mark the whole spec as changed).

   The union (added ∪ changed) is the change-set. (`removed` nodes have no downstream to propagate to, so they are not change-set roots.) Note: `render_ascii.delta` returns a formatted display string, not a list of IDs — do not call it here; it consumes the very same `changed_nodes` rule for its display.
   - **First run / no previous snapshot** → there is no baseline, so **nothing changed** → skip the impact-pass entirely (do NOT crash; do NOT treat every node as "changed"). This reuses the same no-baseline rule as `--viz delta` (DRY).
2. **Run `downstream()` per changed ID** (deterministic) → union the affected sets.
3. **Annotate** each affected node with the impact-pass LLM scaffold (`validation-rules-spec.md → Impact-Pass LLM Scaffold`): `{node, dim_touched, one_liner, action}`.
4. **Approved + contradicted** → an affected node that is `status: approved` AND contradicted by the change runs the **Contradiction Protocol** (`validation-rules-spec.md` § Contradiction Protocol; keep/change/hybrid). The engine NEVER auto-flips (G-A3).
5. **Write the impact report** → `docs/product/impact/<ts>.md` (skeleton `assets/templates/impact-report.md`; `trigger: --validate`, `changed_set:` the delta IDs, `dims:` the dimension union, one table row per affected node). This is a body document the LLM composes directly — not a `generate_templates.render` scalar fill.

The impact-pass is deterministic in its graph half (snapshot-delta + `downstream()`) and LLM-only in its interpretation (G-B1/G-B2). When the change-set is empty (a clean re-validate of an unchanged spec), no impact report is written.

#### Self-correction write (behavioral memory 3E)

Run the advisory fence scan and feed any structural slip into the self-correction store so the next pre-flight catches it:

```bash
# advisory: lists working-tree changes OUTSIDE docs/product/ (always exits 0; never gates)
./.claude/skills/.venv/bin/python3 scripts/check_fence.py --root <root>
```

If `check_fence.py` reports a `fence_breach` (a write that escaped the spec boundary), or the Contradiction Protocol
below catches an attempted auto-flip, record the slip via `behavioral_memory.record_self_correction(root, slip=…,
violated_rule=…, reminder=…)` — `violated_rule` MUST cite one of the five operating principles (a `fence_breach` is
typically `dry`/`frontmatter_source_of_truth`; an auto-flip is `no_silent_reversal`). A repeat of the same slip
increments its frequency rather than duplicating the row. This guards the skill's BEHAVIOR (read it as a pre-flight
self-check before at-risk ops), distinct from 3D which shapes the PO's OUTPUT wording. **Honesty:** the fence scan is
advisory and the write is LLM-discretionary — this REDUCES recurrence, it is not a hard block, and the store is not
guaranteed to accrue every turn. Full spec + privacy posture in `references/behavioral-memory.md`.

### Step 2.6 — Record the validate marker (`--validate` ONLY)

Write `docs/product/.memory/last_validated.json` recording the validated snapshot (the one Step 1 wrote) — its filename + content hash + the validation time. This marker is the `--validate` signal the `--status` command reads ("last validated against snapshot X at time T"):

```bash
./.claude/skills/.venv/bin/python3 -c "import sys; sys.path.insert(0,'scripts'); \
  import judgment_cache as jc; jc.write_last_validated('<root>', '<snapshot-path>')"
```

- Write it **only on `--validate`** — a bare `--viz --snapshot` writes the snapshot but NOT this marker, so the snapshot timeline and the validate timeline stay distinct (the marker is "I validated", not "I snapshotted").
- The write goes through the shared soft fence (`fs_guard`) — it can never escape `docs/product/`. The marker lives under `.memory/` (committed, per the locked folder-split decision).

### Step 3 — Compose the human report

Format per `validation-rules-spec.md` § Human Report Format (single authoritative home for the report skeleton: Summary / Errors / Warnings / Suggested Next Steps).

Write the report to stdout (and optionally to `docs/product/validation-report-<ts>.md` if the PO asks).

### Step 4 — Strict-Gate Behavior

- Without `--strict`: report all findings, do nothing else (advisory).
- With `--strict`: if **any** finding has `severity: error`, stop. Print: "Strict mode blocked on errors above. Resolve and re-run."
- `severity: warn` never blocks.

## Contradiction Protocol (critical — never auto-flip)

→ `validation-rules-spec.md` § Contradiction Protocol (single authoritative home for the keep/change/hybrid steps).

This protocol runs on a `contradiction` finding against an `approved` artifact before the report is composed, and applies even if `--strict` is OFF.

### Decision Register wiring (kill re-litigation)

The Decision Register (`docs/product/decisions.md`, managed by `scripts/decision_register.py`) is the authoritative, append-only home for explicit PO rulings (`DEC-<n>`). It bookends the keep/change/hybrid flow above: **read it FIRST, write it on resolve.**

**Before surfacing the keep/change/hybrid options — read the register first.** A contradiction the PO has *already ruled on* must not be re-asked:

```bash
./.claude/skills/.venv/bin/python3 scripts/decision_register.py --root <root> --list
```

The script returns the **active** decisions (status `active`) as JSON — deterministic parse, no judgment (Script-vs-LLM split). The LLM then judges whether any active `DEC-<n>` already covers *this* contradiction (same artifacts, same tension). If a matching active DEC exists, **surface it instead of re-asking**:

> "You already decided this in **DEC-n** ("…title…", because …rationale…). Keep that ruling, or supersede it with a new decision?"

- **Keep the prior ruling** → no new contradiction is raised; note the `DEC-n` reference and move on (re-litigation avoided).
- **Supersede** → proceed to the keep/change/hybrid options below, then auto-append a NEW decision carrying `supersedes: DEC-n` (the script flips the old record to `status: superseded` and appends the new one — append-only lineage, no id reuse).

If no active DEC matches, run the keep/change/hybrid options as normal.

**On resolve (Keep / Change / Hybrid) — auto-append a `DEC`.** Every resolution of a contradiction is a binding PO ruling, so record it so the same tension cannot resurface unflagged. Allocate the next id, then append (the LLM supplies the title + rationale prose; the script owns the id grammar + append-only write through the soft fence):

```bash
# 1. allocate the next monotonic DEC id
./.claude/skills/.venv/bin/python3 scripts/decision_register.py --root <root> --alloc-id
# 2. append the ruling (rationale is the LLM's prose; affects = the approved artifact id;
#    supersedes only when superseding a prior DEC)
./.claude/skills/.venv/bin/python3 scripts/decision_register.py --root <root> --append \
  --id <DEC-n> --title "<short ruling>" --rationale "<why the PO chose Keep/Change/Hybrid>" \
  --affects <approved-artifact-id> [--supersedes <DEC-m>]
```

- **Keep** → the new DEC records "kept the approved version, rejected the new claim" + the why.
- **Change** → the DEC records the switch; the affected artifact is then **re-approved** via `--approve` (the engine still never auto-flips — the DEC is the audit trail, the re-approval is the explicit promotion).
- **Hybrid** → the DEC records both positions + the follow-up to reconcile.

This is the SAME register the `--decision` flag writes (it lets the PO log a standalone ruling), and the SAME register `judgments.json` points at via `po_ruling_ref: DEC-<n>` for ruled drift — `decisions.md` is the authoritative home for the ruling; other surfaces link to it by id, never copy the rationale (DRY).

**DRY guard:** a `DEC` record holds the ruling + its rationale + ID links (`affects:`/`supersedes:`) ONLY. It NEVER copies a structural fact that already has a home (a persona narrative in `vision.md`, a goal in `brd.md`, a scope/AC in the PRD/story). Point at those by ID; do not duplicate them.

## Drift Detection (frontmatter ↔ prose)

When generating reports or summaries:

- If the LLM notices a heading-text in the body that conflicts with a frontmatter value (e.g., body says "MUST" but frontmatter says `moscow: should`), emit an advisory note. **Frontmatter wins by rule** (`CLAUDE.md → Frontmatter is source-of-truth`).
- Never auto-overwrite frontmatter from prose, and vice versa.

## `--approve` Flow

1. Run `--validate` (without `--strict`). Collect findings.
2. If errors exist → tell the PO: "Open issues: {n_errors}. Approval will record these as outstanding. Continue?" Warn-not-block per brainstorm decisions.
3. If contradictions exist → run the contradiction protocol first; abort approval until resolved.
4. Ask: "Approve which artifact? (default: the most recently edited)"
5. Ask: "Who is approving (owner)? Stakeholders to record?"
6. Update the artifact:
   - Frontmatter: set `status: approved`, add `approval: {approved_by, approved_at, approved_version}`, bump `version` minor.
   - Body: append the `sign-off.md` fragment with the answers.
7. Append a change-log entry (action = `approved`).

## `--summary` Flow

1. Run `spec_graph.py` (no snapshot needed unless the PO asks).
2. Compose the exec-summary inputs:
   - Product name + core-value (from PRODUCT.md).
   - BRD goals (titles + status).
   - PRDs (id + title + horizon).
   - Roadmap groupings (now/next/later via the `roadmap` view).
   - Persona list.
   - Top 3 risks (highest impact × likelihood).
3. Call `generate_templates.py --type exec_summary --values <json> --write` to render `docs/product/exec-summary.md`.
4. Optionally render an HTML version: `visualize.py --view tree --format html --root <root>` and bundle.

## `--decision` Flow

`--decision` is the PO's manual entry point into the Decision Register — the same register the Contradiction Protocol auto-writes (above). Use it to log a standalone ruling that did not arise from a contradiction (e.g. "we will NOT support multi-currency in v1"), so the choice is recorded once and never re-debated.

- **`--decision list`** → show the active rulings:

  ```bash
  ./.claude/skills/.venv/bin/python3 scripts/decision_register.py --root <root> --list
  ```

- **`--decision`** (no arg) or **`--decision <DEC-n>`** (to supersede an existing one) → record a new ruling. Ask the PO (via AskUserQuestion) for the ruling and the why, then:

  ```bash
  # allocate, then append (LLM supplies title + rationale prose)
  ./.claude/skills/.venv/bin/python3 scripts/decision_register.py --root <root> --alloc-id
  ./.claude/skills/.venv/bin/python3 scripts/decision_register.py --root <root> --append \
    --id <DEC-n> --title "<short ruling>" --rationale "<why>" \
    [--affects <artifact-id>] [--supersedes <DEC-m>]
  ```

Same Script-vs-LLM split as the contradiction wiring: the script owns the `^DEC-\d+$` grammar, the monotonic id allocation, and the append-only write through the soft fence; the LLM owns the rationale prose. Same DRY guard: the record links to artifacts by ID (`affects:`), it never copies their structural facts.

## Cross-Flag Notes

- The LLM **must run scripts first**; it must not infer the graph by reading files directly.
- All script invocations use the repo venv: `./.claude/skills/.venv/bin/python3`.
- Every flag closes by appending a change-log entry (action = `validated` / `approved` / `summarized`). When the `--validate` impact-pass (Step 2.5) found a non-empty change-set, that entry also carries `affected_set` + `dims` (mirroring the impact report), alongside the `docs/product/impact/<ts>.md` file.
