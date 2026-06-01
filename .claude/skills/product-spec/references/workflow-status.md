# Workflow — `--status` (spec-health nudge)

A **read-only** pull nudge: the PO asks "where does my spec stand?", and the skill reports its health **against the last time it was validated** — without touching a single artifact. It is the gentle counterpart to `--validate`: validate *runs* the gate; `--status` *reminds* the PO what has drifted since they last ran it.

`--status` **never edits, never approves, never writes the memory layer**. In particular it only **reads** `docs/product/.memory/last_validated.json` (the marker the `--validate` hub writes via `judgment_cache.write_last_validated`); it never creates or mutates that marker. The validate timeline stays owned by `--validate`.

Run via the repo venv:

```bash
./.claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/status.py \
  --root <project-dir> [--today YYYY-MM-DD]
```

## Script-vs-LLM split

`status.py` is the **SCRIPT** half — it emits the deterministic structural facts as JSON. The **LLM** composes the human-facing nudge from that JSON (localized per `--lang`). The script does no judgment; the LLM does no date math or graph traversal.

The feeder JSON shape:

```json
{
  "schema_version": "1.0",
  "root": "<abs path>",
  "baseline": true,
  "checked_at": "<ISO>Z",
  "today": "YYYY-MM-DD",
  "unvalidated": ["PRD-AUTH-E1-S1", "..."],
  "added": ["..."],
  "removed": ["..."],
  "drafts": ["PRD-AUTH-E1", "..."],
  "stale_approvals": ["PRD-AUTH"],
  "overdue": [ { "check": "overdue", "artifact_id": "...", "..." } ]
}
```

| Field | Meaning | How it is computed |
|-------|---------|--------------------|
| `baseline` | Was there a last-validated marker at all? | `last_validated.json` present + parseable + its snapshot file still readable. |
| `unvalidated` | Node ids changed since the baseline snapshot — work the last validate never saw. | `spec_graph.changed_nodes` (field/body delta) **∪** `added` **∪** `removed`. |
| `added` / `removed` | The set-diff halves vs the baseline snapshot. | `spec_graph.diff_graphs`. |
| `drafts` | Node ids still in `status: draft`. | scan current graph. |
| `stale_approvals` | **Approved** node ids that ALSO changed since the baseline — the approval predates the new wording. | `approved` ∩ `unvalidated`. |
| `overdue` | Artifacts whose `target_date` is before `--today`. | **reuses** `time_advisory.check_overdue` (one home for the date math; pin `--today` to reproduce). |

## How the LLM composes the nudge

1. Run `status.py`. If `baseline: false`, lead with **"no validation baseline yet — run `--validate` to establish one."** Do **not** present the spec as "all unvalidated" — a never-validated (or marker-lost) spec has no comparison point, so `unvalidated` is empty by design. You may still surface `drafts` and `overdue` (those need no baseline).
2. If `baseline: true`, summarize in PO language:
   - **Changed since last validate** (`unvalidated`): "N items changed since you last validated. Re-run `--validate` to re-check them." Name the ids.
   - **Stale approvals** (`stale_approvals`): surface each verbatim — "**`PRD-AUTH`** is approved but its wording changed since approval. Keep / re-validate / revisit?" **Never silently re-flip** an approved decision (no-silent-reversal).
   - **Drafts** (`drafts`): "still in draft" — a gentle progress reminder, not a blocker.
   - **Overdue** (`overdue`): the calendar reminder, framed as information ("`PRD-X` was due `<date>`"), never a gate.
3. Always close with the **soft-fence reminder** (below) when anything is unvalidated.

## Honesty caveat — this is a NUDGE, not a guard

`--status` is **advisory and read-only**. It reports drift; it does not prevent it.

- It does **not** block a raw LLM `Write`, nor an LLM composing a body directly to disk (e.g. the impact report). Those are governed by the prose boundary rule + the advisory `check_fence.py` scan + the script-path `fs_guard` assert — **not** by `--status`.
- A `baseline: false` result means "I cannot tell what drifted" — it is **not** an all-clear and **not** an everything-is-broken. State that honestly.
- `--status` never auto-fixes, auto-approves, or re-runs the gate. It points; the PO decides whether to run `--validate` / `--approve` / `--update`.

## Soft-fence reminder

When `unvalidated` is non-empty, remind the PO: *"the spec has drifted since your last `--validate` — these changes were never structurally checked. Run `--validate` to re-gate, and remember the skill only ever writes under `docs/product/` (run `check_fence.py` if you suspect a stray file landed elsewhere)."*

## Exit behavior

`status.py` exits **0** on every valid run regardless of how many items it surfaces (it is a nudge, never a gate). The single exception is a **malformed `--today`** (a non-ISO date) → exit **1**, mirroring `time_advisory.py`: that is input validation, not a finding.
