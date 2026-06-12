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
  "overdue": [ { "check": "overdue", "artifact_id": "...", "..." } ],
  "unrecorded_signals": [ { "type": "validate_no_marker", "severity": "info", "subject": null, "evidence": "...", "suggested_writer": "..." } ],
  "reflect_suggestion": "...",
  "bundle_age": { "bundle_version": "2.3.1", "built_at": "<ISO>", "age_days": 30 }
}
```

`bundle_age` is `null` whenever there is no readable `.claude/MANIFEST.json` (a dev tree, a hand-copied spec, or a corrupt/old-format MANIFEST) — the key is always present so the contract is stable.

| Field | Meaning | How it is computed |
|-------|---------|--------------------|
| `baseline` | Was there a last-validated marker at all? | `last_validated.json` present + parseable + its snapshot file still readable. |
| `unvalidated` | Node ids changed since the baseline snapshot — work the last validate never saw. | `spec_graph.changed_nodes` (field/body delta) **∪** `added` **∪** `removed`. |
| `added` / `removed` | The set-diff halves vs the baseline snapshot. | `spec_graph.diff_graphs`. |
| `drafts` | Node ids still in `status: draft`. | scan current graph. |
| `stale_approvals` | **Approved** node ids that ALSO changed since the baseline — the approval predates the new wording. | `approved` ∩ `unvalidated`. |
| `overdue` | Artifacts whose `target_date` is before `--today`. | **reuses** `time_advisory.check_overdue` (one home for the date math; pin `--today` to reproduce). |
| `unrecorded_signals` | What looks unrecorded in the memory layer (fence breach / drift-since-validate / approved-changed-no-DEC / judged-not-stored). | **reuses** `memory_gap.collect` (the SINGLE detection home — `references/memory-enforcement.md` § signal catalogue; status never re-detects). |
| `open_questions` | PO-facing hanging parameters (`cần PO xác định` / `TBD` / `Vẫn còn mở`) riding inside artifacts that look done. | **reuses** `open_questions.scan` (the SINGLE marker home; the `--approve` gate consults the same module per-file). |
| `reflect_suggestion` | A soft one-line `--reflect` hint, present only when drift-since-last-validate is high. | derived advisory string — points at a retroactive `--reflect` harvest of rulings/observations never recorded. |
| `bundle_age` | How old the **installed bundle** is — `bundle_version` + `built_at` + `age_days` (days since it was packed), or `null`. | reads `<root>/.claude/MANIFEST.json` (the installer's version stamp). **Build-age**, not install-age: it catches a freshly-installed but already-old release. No network — fail-silent on any absent/unreadable MANIFEST. |

## How the LLM composes the nudge

1. Run `status.py`. If `baseline: false`, lead with **"no validation baseline yet — run `--validate` to establish one."** Do **not** present the spec as "all unvalidated" — a never-validated (or marker-lost) spec has no comparison point, so `unvalidated` is empty by design. You may still surface `drafts` and `overdue` (those need no baseline).
2. If `baseline: true`, summarize in PO language:
   - **Changed since last validate** (`unvalidated`): "N items changed since you last validated. Re-run `--validate` to re-check them." Name the ids.
   - **Stale approvals** (`stale_approvals`): surface each verbatim — "**`PRD-AUTH`** is approved but its wording changed since approval. Keep / re-validate / revisit?" **Never silently re-flip** an approved decision (no-silent-reversal).
   - **Drafts** (`drafts`): "still in draft" — a gentle progress reminder, not a blocker.
   - **Overdue** (`overdue`): the calendar reminder, framed as information ("`PRD-X` was due `<date>`"), never a gate.
   - **Unrecorded signals** (`unrecorded_signals`): surface what looks unrecorded in plain language — a stray file
     outside `docs/product/`, drift since the last validate, an approved artifact whose wording changed without a
     `DEC-<n>`, or verdicts that drifted without re-judging. Each signal already carries its `suggested_writer` (the
     fix); point at it, never block. These are advisory and may be false positives (an `approved_changed_no_dec` on a
     legitimate edit is expected) — frame them as "worth a look", not "you did something wrong". The detector is the
     single home (`memory_gap` → `references/memory-enforcement.md`); `--status` only reports it.
   - **Open questions** (`open_questions`): surface each hanging parameter in plain language — "**`PRD-AUTH-E1-S1`** (line {n}) still says `cần PO xác định` — that decision has no home yet." Point at the file+line; these block nothing, but a `must` carrying one is not approvable silently (the `--approve` gate re-checks).
   - **Reflect hint** (`reflect_suggestion`): when present (high drift-since-validate), pass it through as a soft
     one-liner — "a lot has changed unrecorded; `--reflect` can retroactively harvest any rulings/observations that
     were never recorded." A suggestion only; `--status` never runs it.
   - **Telemetry pointer** (optional, read-only): if the PO also wants the *usage/health* picture — how often each
     skill runs, which scripts error or run slow, whether validate has been passing as a trend — point them at the
     `telemetry` skill (`/cleanmatic:telemetry --lens all`). `--status` reports THIS spec's drift; `telemetry` reads
     usage & health across all skills. A pointer only; `--status` never runs it.
   - **Build-age beacon** (`bundle_age`): when present, add ONE soft line so the PO knows how stale their installed
     copy is and that a newer release may exist — e.g. *"Bạn đang dùng bản **{bundle_version}**, đóng gói **{age_days}**
     ngày trước — hỏi người phát hành xem có bản mới hơn không."* (EN: *"You're on **{bundle_version}**, packed
     **{age_days}** days ago — ask the publisher whether a newer release exists."*). It is **build-age**, not the date
     the PO installed; phrase it as "đóng gói/packed", not "cài/installed". A heads-up only — never a gate, and absent
     (`null`) in a dev tree, so simply omit the line then. `--status` does NOT check the network for newer versions.
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
