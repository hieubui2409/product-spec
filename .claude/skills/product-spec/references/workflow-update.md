# Workflow — Delta-Update

End-to-end workflow for the **--update** flag (delta — flag affected nodes, never auto-rewrite prose). The **--auto** brain-dump flow lives separately in `workflow-auto.md`.

The **impact-pass** (`downstream()` + LLM `{dim_touched, one_liner, action}` per affected node → impact report + change-log `dims`) runs on `--update` (here) AND on `--validate` (`workflow-validate.md`). Its annotation rule lives once in `validation-rules-spec.md → Impact-Pass LLM Scaffold`; both flows reference it. The impact-pass is per-CHANGE propagation — keep it distinct from the per-ARTIFACT validation-catalog checks (`risk_blindspot`/`time_realism`/`competitive_drift`).

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

The script returns the set of node IDs whose frontmatter transitively references `changed_id` — the iterative `downstream()` closure (cycle-safe via its visited-set; see `spec_graph.downstream`). Example: changing `PRD-AUTH` returns `{PRD-AUTH-E1, PRD-AUTH-E1-S1, ...}`. This is the **deterministic** half of the impact-pass: graph traversal only, no judgment.

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

If a downstream artifact is `approved` AND the change would contradict its content, run the **contradiction protocol** (`validation-rules-spec.md → Contradiction Protocol`). The PO chooses keep / change / hybrid.

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

### Step 7 — Consistency-sweep gate (block "done" on unresolved contradictions)

An `--update` touches one artifact, but a fact can ripple into cross-references the impact-pass closure does not surface (a persona label changed in `PRODUCT.md` that a PRD problem statement still quotes the old way; a core-value sentence a story AC contradicts). Before declaring the update **done**, run a whole-tree consistency sweep and **block completion until zero contradictions remain unresolved**.

This is an LLM step — re-read, reconcile, block — anchored to a deterministic change-set so it never sweeps the whole tree blindly:

1. **Build the deterministic change-set.** Compare the two most-recent snapshots under `docs/product/visuals/.snapshots/` with `spec_graph.diff_graphs` (added/removed nodes) + `spec_graph.changed_nodes` (per-node field diff over the tracked field set `spec_graph.CHANGED_FIELDS`). Union that with the `downstream()` closure of the changed artifact. No previous snapshot → run `--validate` first to create one; do not crash.
2. **Re-read each node in the change-set and its cross-references.** For each, ask: does any prose still assert something the change now contradicts — a stale persona label, an out-of-date core-value quote, an AC that names the old scope, a `scope_intent` lock the new content exceeds?
3. **Reconcile or block.** Every contradiction found must be resolved before "done":
   - a non-approved artifact → flag it for PO review (Step 3 checklist) and either the PO edits it or explicitly marks it stale;
   - an **approved** artifact → run the contradiction protocol (Step 5 / `validation-rules-spec.md → Contradiction Protocol`); never auto-flip;
   - a **PO-confirmed** answer (in `.session.md` Validation Log) → run **No Silent Reversal** (below).
4. **Gate.** Do **not** report the update as complete while any contradiction is unresolved. List the open contradictions verbatim and tell the PO completion is blocked on them. A clean sweep (zero contradictions) closes the update.

The sweep reuses existing mechanisms (snapshot delta + `downstream()`); it adds no new script. It is the LLM-judgment layer on top of the deterministic change-set — the Script-vs-LLM split holds (the script enumerates; the LLM judges contradiction).

## No Silent Reversal — protect PO-confirmed answers, not just approved artifacts

The global "No silent reversals" rule (CLAUDE.md) protects `approved` artifacts. This flow extends the same protection to **any answer the PO has confirmed** and recorded in the `.session.md` **Validation Log** (`workflow-interview.md → Validation Log`) — a locked `scope_intent`, a persona decision, a chosen threshold, a MoSCoW call — **even when the artifact carrying it is still `draft`**. A confirmed decision is a decision; draft status does not make it free to overwrite silently.

Before regenerating or editing anything that would reverse a PO-confirmed answer (whether triggered by `--update`, the consistency sweep, or `--auto`):

1. **Detect the reversal.** Read the Validation Log; if the new content would change a recorded answer, treat it as a reversal — do not apply it.
2. **Surface it to the PO**, with all four parts:
   - the **verbatim original** answer (quoted from the Validation Log),
   - the **reason** the new content wants to change it,
   - the **trade-off** (what the change costs vs. keeps),
   - the three options: **Keep** (reject the new claim), **Change** (apply it — and re-record the new decision in the Validation Log; re-approve any `approved` artifact it touches), **Hybrid** (record both, plan a follow-up).
3. **Never auto-flip.** The skill applies nothing until the PO chooses. On **Change**, append the new decision to the Validation Log so the trail stays complete.

This is the draft-aware sibling of the approved-artifact contradiction protocol (Step 5): same surface-and-choose shape, broader trigger (any confirmed answer, not only `approved` status). The MoSCoW gate's "MUST set exceeds the locked `scope_intent`" check is one common trigger — surface it, do not silently widen the lock.

## Cross-Flag Anti-Patterns

- **Do not** silently classify ambiguous items in `--auto`. Always confirm-batch.
- **Do not** auto-rewrite an existing artifact's body in `--update`. Flag only.
- **Do not** advance an `approved` artifact's `status` backwards (to `draft`) without surfacing the contradiction to the PO first.
- **Do not** overwrite a PO-confirmed answer (Validation Log) just because the artifact carrying it is still `draft`. Run No Silent Reversal first.
- **Do not** report an `--update` as done while the consistency sweep still has an unresolved contradiction.
- **Do not** allocate global IDs by scanning the disk twice. Use one in-memory counter per run.
