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

For each check in `validation-rules-spec.md` whose **owner = LLM**, run a separate pass:

- **invest_quality** — for every story: check Independent · Negotiable · Valuable · Estimable · Small · Testable. If any dimension fails, emit a finding (warn).
- **vagueness** — scan story AC and PRD MoSCoW lists for vague terms (`should`, `easy`, `fast`, `intuitive`, `robust`); if found, emit a finding suggesting a quantified rewrite.
- **core_value_drift** — for each PRD/epic/story, score alignment with `PRODUCT.md.core_value` as `aligned | weak | off` + a 1-line rationale. Emit a finding (warn) when `weak` or `off`.
- **gold_plating** — scan PRD scope: does any new requirement go beyond the stated problem? Emit finding (warn).
- **semantic_duplication** — compare every pair of PRDs/epics within the same product for intent overlap. Emit finding (warn) on suspected duplicates.
- **time_realism** — for each epic, read the SCRIPT-precomputed anchor from `time_realism_anchors.py` (`size`, `child_story_count`, `days_remaining`, …) and apply the FIXED rule in `validation-rules-spec.md → time_realism LLM Scaffold`: flag (warn) ONLY when `eligible` AND `size=="L"` AND `child_story_count>=6` AND `days_remaining<21`; missing anchor → `missing_anchor` (no flag); otherwise no flag. The finding MUST carry `context.cited_data` (verbatim from the anchor). **Do NO date arithmetic** — the script already computed `days_remaining`.
- **competitive_drift** — for each eligible PRD, read the SCRIPT-resolved anchor from `competitive_drift_anchors.py` and apply the FIXED rule in `validation-rules-spec.md → competitive_drift LLM Scaffold`: flag (warn) ONLY when `eligible` (scope `core-value` AND `competitors_with_data >= 2`) AND every real (non-`none`) parity is `behind`; missing anchor / ineligible / any non-`behind` → no flag. The finding MUST carry `context.cited_data` (verbatim from the anchor). **Never invent a competitor or parity verdict** — use only what the script resolved.
- **contradiction** — compare every new artifact against `approved`-status artifacts. If contradicted → emit `error`-severity finding + surface to PO via the contradiction protocol (see below). **Never auto-flip.**

### Step 2.5 — Impact-pass (per-change propagation; runs on `--validate` too)

The impact-pass is the per-CHANGE propagation surface — `downstream()` + an LLM `{dim_touched, one_liner, action}` per affected node — and it runs on `--validate` as well as `--update` (it is per-CHANGE, distinct from the per-ARTIFACT catalog checks above). On `--update` there is one explicit `changed_id`; on a whole-spec `--validate` there is none, so **derive the change-set from the snapshot delta**:

1. **Get the change-set from the snapshot delta.** Step 1 already wrote a fresh snapshot to `docs/product/visuals/.snapshots/`. Compare it to the **previous** snapshot (the second-most-recent — the freshly-written one is the current state, not a baseline). Derive the change-set by comparing the two snapshot node dicts directly: `spec_graph.diff_graphs(current, previous)` returns `{added, removed, product_changes}` — `added` carries the new node IDs. Then compare the per-node `status`/`scope`/`moscow`/`horizon`/`size` fields between the two snapshots' node dicts to identify **changed** node IDs (nodes present in both where any of those fields differ). The union (added ∪ changed) is the change-set. (`removed` nodes have no downstream to propagate to, so they are not change-set roots.) Note: `render_ascii.delta` returns a formatted display string, not a list of IDs — do not call it here.
   - **First run / no previous snapshot** → there is no baseline, so **nothing changed** → skip the impact-pass entirely (do NOT crash; do NOT treat every node as "changed"). This reuses the same no-baseline rule as `--viz delta` (DRY).
2. **Run `downstream()` per changed ID** (deterministic) → union the affected sets.
3. **Annotate** each affected node with the impact-pass LLM scaffold (`validation-rules-spec.md → Impact-Pass LLM Scaffold`): `{node, dim_touched, one_liner, action}`.
4. **Approved + contradicted** → an affected node that is `status: approved` AND contradicted by the change runs the **Contradiction Protocol** below (keep/change/hybrid). The engine NEVER auto-flips (G-A3).
5. **Write the impact report** → `docs/product/impact/<ts>.md` (skeleton `assets/templates/impact-report.md`; `trigger: --validate`, `changed_set:` the delta IDs, `dims:` the dimension union, one table row per affected node). This is a body document the LLM composes directly — not a `generate_templates.render` scalar fill.

The impact-pass is deterministic in its graph half (snapshot-delta + `downstream()`) and LLM-only in its interpretation (G-B1/G-B2). When the change-set is empty (a clean re-validate of an unchanged spec), no impact report is written.

### Step 3 — Compose the human report

Format per `validation-rules-spec.md → Human Report Format`:

```
# Validation Report — <date>
## Summary  (counts of artifacts, errors, warns, strict on/off)
## Errors   (each: artifact_id, file, detail)
## Warnings (grouped by check)
## Suggested Next Steps  (1 bullet per top-priority remediation)
```

Write the report to stdout (and optionally to `docs/product/validation-report-<ts>.md` if the PO asks).

### Step 4 — Strict-Gate Behavior

- Without `--strict`: report all findings, do nothing else (advisory).
- With `--strict`: if **any** finding has `severity: error`, stop. Print: "Strict mode blocked on errors above. Resolve and re-run."
- `severity: warn` never blocks.

## Contradiction Protocol (critical — never auto-flip)

When `--validate` detects a `contradiction` finding against an `approved` artifact, before composing the report:

1. Stop and present the contradiction to the PO via `AskUserQuestion`:
   - **Keep approved** — the new claim is rejected; the LLM offers to revise the new artifact.
   - **Change** — the approved artifact is reopened (`status: draft`), the new claim is recorded; a follow-up `--approve` is required.
   - **Hybrid** — record both; PO defines a follow-up to reconcile.
2. **Never silently rewrite** an `approved` artifact. Surface, ask, defer.

This applies even if `--strict` is OFF.

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

## Cross-Flag Notes

- The LLM **must run scripts first**; it must not infer the graph by reading files directly.
- All script invocations use the repo venv: `./.claude/skills/.venv/bin/python3`.
- Every flag closes by appending a change-log entry (action = `validated` / `approved` / `summarized`). When the `--validate` impact-pass (Step 2.5) found a non-empty change-set, that entry also carries `affected_set` + `dims` (mirroring the impact report), alongside the `docs/product/impact/<ts>.md` file.
