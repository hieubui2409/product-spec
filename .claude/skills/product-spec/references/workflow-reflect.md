# Workflow — `--reflect` (retroactive memory harvest)

`--reflect` is the **Tier-2** catch-up for the memory layer: when the inline forcing-functions
were skipped (a long session, an old spec imported wholesale, a stretch of work with no
`--validate`), `--reflect` retroactively harvests the memory writes that were never made —
rulings (`DEC-<n>`), structural self-corrections (3E), and PO-style voice (3D) — from
**structurally-readable sources only** (git history + the on-disk `.memory/`/`decisions.md`
state), presents them for PO confirmation, and persists **only after the PO confirms**.

> **DRY:** the *why*, the placement, and the dedup contract for `--reflect` live in the single
> enforcement home — `references/memory-enforcement.md` (its "Tier-2 — `--reflect`" section).
> This reference owns only the **operative flow**; it does not restate the model.

It is **on-demand** (the PO asks for it, or accepts the soft `--status` suggestion — see
`workflow-status.md`'s `reflect_suggestion`). It is never auto-run: the harvest spends an
opus sub-agent's tokens, so it stays explicit and opt-in.

---

## Why a sub-agent (and why read-only)

The harvest is a focused, context-isolated read job: scan git + `.memory/`, reason about what
implies an unrecorded write, and propose candidates. Running it as a **dedicated sub-agent**
keeps that token cost off the main thread and the reasoning uncontaminated by the live session.

The harvester (`.claude/agents/memory-harvester.md`, `model: opus`) is **read-only at the tool
layer** — `tools: Glob, Grep, Read, Bash`, with **no `Write`/`Edit`/`NotebookEdit`/`Task`**. A
harvester that could write memory could silently record an unconfirmed ruling; removing the
write tools makes "persist only after PO confirm" a structural guarantee, not a promise. The
sub-agent **proposes**; the **main agent persists**.

The sub-agent also cannot see the live conversation — by design. A PO wording-correction made
in chat leaves no structural trace, so reflect harvests only git + file state. Conversational
3D nuance is the inline per-prose-turn forcing-function's job (see `behavioral-memory.md`), not
reflect's. This is the honest ceiling: reflect catches what is *written down*, not what was
*said*.

---

## The flow (five steps)

### 1. Scan — the deterministic anchors

Run the script half (emits JSON, exits 0, **git-degrade-safe** — never crashes):

```bash
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/reflect_scan.py --root <project-dir>
```

It returns `{git_available, commits_since_last, revert_fix_candidates, existing_memory,
parse_errors}`:

| Field | Meaning |
|-------|---------|
| `git_available` | `false` when `<root>` is not a git work tree → no commit candidates; the file-state harvest still runs. |
| `commits_since_last` | Spec-touching commits (`docs/product/`) AFTER the harvest cutoff — the most recent of `.memory/last_reflect.json` / `.memory/last_validated.json`; all history when neither exists. Each: `{sha, subject, files, is_revert_or_fix}`. |
| `revert_fix_candidates` | The subset whose subject reads as a revert/fix — 3E self-correction candidates. |
| `existing_memory` | The **dedup index** of what is ALREADY recorded (`decision_ids`, `decision_affects`, `self_correction_slips`, `po_style_keys`), reusing the same readers `memory_gap` uses — so the harvest never re-proposes a write on record. |
| `parse_errors` | Any artifact the graph could not parse (advisory — never blocks the harvest). |

`reflect_scan.py` is the **SCRIPT** half (Script-vs-LLM split, CLAUDE.md): it correlates
disk/git state and emits anchors, but makes **no** candidate judgment. The judgment is the
harvester's.

### 2. Spawn the harvester (Task)

The main agent spawns the read-only harvester with `Task(memory-harvester)`, passing the
project `<root>` and the anchors. The harvester reads the anchors, walks each candidate commit
with `git show`, dedups against `existing_memory`, and returns a **candidate report** — it
writes nothing.

### 3. Candidate report

Each candidate is a **proposal**, mapped to exactly one existing writer:

| Candidate kind | Persists via (step 5) |
|----------------|------------------------|
| Decision (`DEC-<n>`) | `decision_register.py --append` |
| 3E self-correction | `behavioral_memory.record_self_correction` |
| 3D PO-style voice | `behavioral_memory.py --voice` |

The report also lists what it **skipped** (already in `existing_memory`) and says plainly when
there is **nothing to record** — an empty harvest is a valid, honest result, never padded.

### 4. PO interview — accept / edit / reject

The main agent surfaces each candidate to the PO via `AskUserQuestion`: **accept** (record as
proposed), **edit** (record with PO-adjusted wording), or **reject** (drop it). Two GATEs apply
exactly as in any other turn — reflect does not relax them:

<GATE-NEVER-ASSUME>
Never persist a candidate the PO has not confirmed. A proposed `DEC` is not a ruling until the
PO accepts it; a proposed self-correction is not recorded until the PO agrees it was a slip.
The harvester's confidence score is a hint, never a licence to auto-write. "Silent" here means
*no extra ceremony AFTER the PO has approved* — it never means *write without asking*.
</GATE-NEVER-ASSUME>

<GATE-NO-SILENT-REVERSAL>
If a candidate would contradict an `approved` artifact (e.g. a diff that quietly changed an
approved scope), do NOT record it as a fait accompli. Surface the contradiction with
**Keep / Change / Hybrid** (see `workflow-validate.md`'s `--decision` flow); the resolved
ruling is what gets recorded as the `DEC`, not the raw diff.
</GATE-NO-SILENT-REVERSAL>

### 5. Persist — only after confirm, through the existing writers

For each **accepted** candidate, the main agent calls the **existing** writer — there is **no
new write home**, and every write goes through the soft fence (`fs_guard`), so it can never
escape `docs/product/`:

```bash
# Accepted ruling → the Decision Register (allocate, then append).
DEC=$(./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/decision_register.py --root <root> --alloc-id)
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/decision_register.py --root <root> \
  --append --id "$DEC" --title "<PO-confirmed title>" \
  --rationale "<the WHY>" [--affects <NODE-ID>]

# Accepted PO-style voice → the 3D writer (lang-keyed; union-merge).
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/behavioral_memory.py --root <root> --voice \
  --lang <en|vi> [--register …] [--vocabulary …] [--recurring-asks …] [--do …] [--dont …]
```

Accepted **3E self-corrections** are recorded via `behavioral_memory.record_self_correction`
(the `violated_rule` must cite one of the five operating principles — the writer enforces it).
None of these are new writers: they are the same homes the inline forcing-functions and the
`--decision`/`--voice` flows use. `--reflect` only changes *when* they run, never *where* the
fact lives.

After the harvest is processed, the main agent records the harvest point so the next
`--reflect` starts after it (the cutoff `reflect_scan` reads):

```jsonc
// docs/product/.memory/last_reflect.json  (written through the soft fence)
{ "reflected_at": "<ISO timestamp>" }
```

Write it only when a harvest actually ran (even one that recorded nothing) — it marks "the spec
was reflected up to here", the same way `last_validated.json` marks the validate timeline.

---

## Git-degrade path (no repo)

With no git work tree, `reflect_scan` returns `git_available: false`, empty
`commits_since_last`/`revert_fix_candidates`, and the file-state `existing_memory` index only.
The harvester then harvests from the on-disk `.memory/`/`decisions.md` state alone (what is
recorded vs what the current spec implies) and never errors. The flow is otherwise identical:
report → PO interview → persist-after-confirm. No git is a degraded harvest, not a failure.

---

## What `--reflect` does NOT do

- It does **not** write memory from the sub-agent — the sub-agent has no write tools; the main
  agent persists, and only after PO confirm.
- It does **not** create a new memory store — accepted candidates go to the existing
  `decisions.md` / `self-corrections.json` / `po-style.yaml` homes.
- It does **not** auto-run — it is on-demand plus the soft `--status` suggestion; the opus token
  cost is paid only when the PO asks.
- It does **not** recover conversational nuance — only what is written to git/`.memory/`. The
  inline 3D forcing-function owns chat-time capture.
