# Workflow — Auto-Decompose & Delta-Update

End-to-end workflow for the **--auto** (brain-dump → spec hierarchy) and **--update** (delta — flag affected nodes, never auto-rewrite prose) flags.

The **impact-pass** (`downstream()` + LLM `{dim_touched, one_liner, action}` per affected node → impact report + change-log `dims`) runs on `--update` (here) AND on `--validate` (`workflow-validate.md`). Its annotation rule lives once in `validation-rules-spec.md → Impact-Pass LLM Scaffold`; both flows reference it. The impact-pass is per-CHANGE propagation — keep it distinct from the per-ARTIFACT validation-catalog checks (`risk_blindspot`/`time_realism`/`competitive_drift`).

## `--auto` Flow (brain-dump decomposition)

The PO pastes (or refers to) a large free-form text dump. The skill chunks it, proposes a decomposition into BRD goals / PRDs / epics / stories, asks for confirmation on ambiguous splits, then writes the artifacts with full traceability.

### Step 1 — Capture the brain-dump

- Ask: "Paste the brain-dump, or give a path to a file."
- Load into memory as `dump_text`.
- Chunk if `len(dump_text) > 4000 chars`: split on blank lines or section headings, max ~3000 chars per chunk. Process chunks in order; the LLM keeps a running tally of identified candidates.

### Step 2 — First-pass extraction (LLM)

For each chunk, the LLM extracts candidates:

- **Goal candidates** — sentences expressing a business outcome ("Reach $1M ARR", "Achieve 80% repeat-purchase").
- **PRD candidates** — multi-sentence descriptions of a feature-area ("user authentication", "billing").
- **Epic candidates** — bounded chunks within a feature-area ("sign-in epic", "password recovery epic").
- **Story candidates** — single user-facing slices ("as a shopper, I want to reset my password").

Each candidate is recorded as: `{type, title, source_excerpt, suggested_parent}`.

### Step 3 — Propose decomposition

Present the proposed tree to the PO in one batch:

```
Proposed decomposition:
- BRD-G1 (new): "Reach $1M ARR in 12 months"
- BRD-G2 (new): "Achieve 80% repeat-purchase rate"
- PRD-AUTH (new): "User authentication"
  - PRD-AUTH-E1: "Sign-in flow"
    - PRD-AUTH-E1-S1: "Email + password sign-in"
    - PRD-AUTH-E1-S2: "OAuth Google sign-in"
  - PRD-AUTH-E2: "Password recovery"
    ...
- PRD-BILLING (new): "Billing & subscriptions"
  ...

Ambiguous items needing your call:
- "Allow user to upload an avatar" — looks like a story but no clear epic. Attach to PRD-AUTH or new PRD-PROFILE?
- "Send weekly newsletter" — likely a separate PRD-NOTIFICATIONS. Confirm?
```

### Step 4 — Confirm-batch on ambiguous items

For each ambiguous item, present an `AskUserQuestion` with 2–4 concrete options. **Do not silently classify** ambiguous items. Defer to PO.

### Step 5 — Write artifacts

Once decomposition is confirmed, generate the files in dependency order:

1. BRD (one file; multiple goals as `goals[]`).
2. PRDs.
3. Epics.
4. Stories.

Use a **single in-memory ID counter** so that batch-allocated parent-scoped IDs are unique even before any file is written. Pass `--id` explicitly to `generate_templates.py` so the counter is the source of truth.

Each file is generated with `keep-optional` set to the minimum that captures the PO's brain-dump content.

### Step 6 — Append change-log

One change-log entry per artifact created (action = `created_via_auto`, reason = "decomposed from brain-dump").

## `--update` Flow (delta — never auto-rewrite prose)

Triggered when the PO has changed a fact and the downstream artifacts need attention.

### Step 1 — Identify the changed artifact

Ask: "Which artifact has changed? (default: the most recently edited)"

- If PO names a file/ID, use it.
- If PO describes a change ("the core-value sentence changed"), ask which artifact carries it.

### Step 2 — Compute the affected downstream set (impact-pass, part 1: deterministic)

```bash
./.claude/skills/.venv/bin/python3 scripts/spec_graph.py --root <root> --downstream <changed_id>
```

The script returns the set of node IDs whose frontmatter transitively references `changed_id` — the iterative `downstream()` closure (cycle-safe via its visited-set; see `spec_graph.downstream`). Example: changing `PRD-AUTH` returns `{PRD-AUTH-E1, PRD-AUTH-E1-S1, ...}`. This is the **deterministic** half of the impact-pass (G-B1): graph traversal only, no judgment.

### Step 3 — Annotate + flag for PO review (impact-pass, part 2: LLM)

For each affected node, layer the **impact-pass LLM annotation** (the per-CHANGE interpretation, distinct from the per-ARTIFACT validation-catalog checks — see `validation-rules-spec.md → Impact-Pass LLM Scaffold`): tag `{dim_touched, one_liner, action}`. Present the annotated set as a checklist:

```
Changed: PRD-AUTH
Affected downstream (4 items):
- [ ] PRD-AUTH-E1   [scope] Sign-in epic — scope wording changed upstream; check the epic goal still matches. → review
- [ ] PRD-AUTH-E1-S1 [ac] Email + password sign-in — AC may reference the old scope. → review AC
- [ ] PRD-AUTH-E1-S2 [time] OAuth Google sign-in — target_date now tighter than parent. → re-estimate
- [ ] PRD-AUTH-E2   [scope] Password recovery — unaffected on inspection. → no-op
```

For each item, the PO chooses:
- **Review now** — open the file, walk through what may need updating; let the PO edit.
- **Skip** — leave as-is.
- **Mark stale** — set `status: draft` on the artifact (was `review`; for `approved` see Step 5) to flag it for later attention.

The `{node, dim_touched, one_liner, action}` records are also written to the impact report in Step 6.

### Step 4 — NEVER auto-rewrite prose

Under no circumstances does the skill regenerate the prose of an existing artifact during `--update`. If the PO wants a rewrite, they invoke the matching flag explicitly (`--prd`, `--epic`, `--story`) which goes through the interview engine.

### Step 5 — Contradiction protocol on approved artifacts

If a downstream artifact is `approved` AND the change would contradict its content, run the **contradiction protocol** (`workflow-validate.md → Contradiction Protocol`). The PO chooses keep / change / hybrid.

### Step 6 — Write the impact report + append change-log

Two artifacts close every `--update`:

1. **Impact report** → `docs/product/impact/<ts>.md` (skeleton: `assets/templates/impact-report.md`). `<ts>` is an ISO-second UTC stamp, matching the `.snapshots/` convention. Fill:
   - `trigger: --update`, `changed_set: [<changed_id>]`, `dims:` the union of `dim_touched` across affected nodes.
   - One **Affected downstream** table row per node from Step 3 (`Node | Dim touched | Interpretation | Suggested action`).
   - The **Contradictions** section ONLY when Step 5 surfaced one (otherwise drop the optional block).
   - This is a body document the LLM composes directly (like the human validation report) — it does NOT go through `generate_templates.render` (that path is for single-line frontmatter scalars).
2. **Change-log entry** (one per invocation) via `generate_templates.py --type change_log_entry`, carrying:
   - `affected_set:` the downstream IDs (already a template field — do NOT re-add),
   - `dims:` the same dimension union written to the report (the field this phase added),
   - `po_decision:` the PO's per-item decisions.

The impact report is the human-readable per-change surface; the change-log `dims`/`affected_set` is the structured, append-only record. Same union of dimensions in both.

## Cross-Flag Anti-Patterns

- **Do not** silently classify ambiguous items in `--auto`. Always confirm-batch.
- **Do not** auto-rewrite an existing artifact's body in `--update`. Flag only.
- **Do not** advance an `approved` artifact's `status` backwards (to `draft`) without surfacing the contradiction to the PO first.
- **Do not** allocate global IDs by scanning the disk twice. Use one in-memory counter per run.
