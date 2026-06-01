# Memory-Write Enforcement — the operative model (single home)

The memory layer (`decisions.md`, `judgments.json`, `po-style.yaml`, `self-corrections.json`) only fills if a writer
actually runs at a workflow hook point. Left purely to discretion, writes are forgettable. This reference is the **one
authoritative home** for *how* the skill makes those writes reliable — the deterministic detector, the portable
forcing-functions, the opt-in hook, the install posture, and the honest ceiling. Other surfaces (`CLAUDE.md`,
`workflow-validate.md`, `workflow-interview.md`, `workflow-status.md`, `behavioral-memory.md`, the opt-in Stop hook, and
`--reflect`) **link here by reference** rather than restating the model — DRY, one home per fact.

> **The whole point in one line:** enforcement raises the **consideration-rate** (the LLM is reliably *prompted* to
> consider a write), never the **write-quality** (the LLM can still, honestly, decide "nothing to record"). Read the
> honest ceiling at the bottom before claiming any guarantee.

---

## The `memory_gap` signal catalogue (deterministic detection)

`scripts/memory_gap.py` is the SCRIPT half — it emits structured "this looks unrecorded" signals and makes **no**
flag/no-flag judgment (the Script-vs-LLM split). It reuses the existing detectors by import (`check_fence`, `spec_graph`,
`decision_register`, `judgment_cache`) — it never re-homes their logic. Always exits 0 (advisory); a malformed input
degrades to a `parse_error` signal, never a crash.

```bash
./.claude/skills/.venv/bin/python3 scripts/memory_gap.py --root <root>
# → {"signals": [ {type, severity, subject, evidence, suggested_writer}, … ]}
```

Each signal is `{type, severity, subject, evidence, suggested_writer}`. The four types:

| `type` | `severity` | Fires when | `suggested_writer` (what to run) |
|--------|-----------|------------|----------------------------------|
| `fence_breach` | `warn` | A working-tree change landed OUTSIDE `docs/product/` (reuses `check_fence.scan`). | `behavioral_memory.record_self_correction` (3E slip) |
| `validate_no_marker` | `info` | The live graph drifted from `.memory/last_validated.json`, or no marker exists at all (PERSISTED-STATE only — the script cannot know a `--validate` ran "this session"). | run `--validate` (writes the marker via `judgment_cache.write_last_validated`) |
| `approved_changed_no_dec` | `warn` | An `approved` artifact's `body_hash` changed vs the last validated snapshot but no new `DEC-<n>` exists. **Surfaced, never blocked** — a legit approved edit is a false positive by design. | record the ruling with `--decision` (`decision_register`), or silence the wording once with `memory_gap.py --ack-no-dec <id>` |
| `judged_not_stored` | `info` | The graph drifted but `judgments.json` did not grow vs the `.memory/last_judged.json` marker (the marker the cache batch-store writes on each store). Marker absent → signal skipped (degrade, never a false fire). | run `--validate` with the batch-store path (see `workflow-validate.md` Memory pass) |

**One-time ack (`--ack-no-dec`):** `memory_gap.py --root <root> --ack-no-dec <node-id>` records
`.memory/no-dec-acks.json` `{node_id: body_hash}`; `collect()` then suppresses `approved_changed_no_dec` for that node
while its current `body_hash` matches the ack. The LLM/PO marks "no DEC needed" ONCE and is not re-nudged for that
wording — a later body change re-arms the signal.

This catalogue is the SINGLE detection home. `--status` (`workflow-status.md`), the Tier-0 validate Memory pass
(`workflow-validate.md`), the Tier-1 hook, and `--reflect` all CONSUME these signals — none re-detect.

---

## Tier-0 — portable forcing-functions (no hook, always on)

The reliability core that works in any install, with no setup. These are **prompt-level "consideration" gates** the LLM
follows — not script gates. They do not block; they make the *consideration* deterministic.

- **Validate "Memory pass" (required).** Every `--validate` report MUST include a Memory-pass section that explicitly
  answers — even "none" for each — *contradiction → a `DEC-<n>`? · structural slip → a 3E self-correction? ·
  `memory_gap` candidates surfaced?* Operative steps + the batch-store wiring live in `workflow-validate.md` (its sole
  home); this reference only states *why* the pass exists.
- **Batch-store the cache (N → 1).** At the end of the validate LLM pass, emit ONE JSON payload of all new verdicts and
  call `judgment_cache.py --store-batch <file|->` once, instead of N separate `--store` calls — removing the
  "forgetting surface" where some verdicts get stored and others don't mid-loop. Atomic: a bad entry fails the whole
  batch, nothing written. Wiring in `workflow-validate.md`.
- **Per-prose-turn 3D forcing-function (interview).** On every prose-bearing turn, the LLM considers one question: *did
  the PO correct my wording this turn?* If yes → record it via `record_po_style` (or the explicit `--voice` flag). The
  forcing-function line lives in `workflow-interview.md`; the 3D write-trigger model lives in `behavioral-memory.md`.
- **End-of-interview validate nudge.** When a session closes after changing N items since the last validate, nudge:
  "you changed N items since last validate — run `--validate`?" In `workflow-interview.md`.
- **Explicit voice entry (`--voice`).** `behavioral_memory.py --voice --lang <en|vi> [--register …] [--vocabulary …]
  [--recurring-asks …] [--do …] [--dont …]` lets the PO record voice deterministically instead of relying on the LLM
  noticing a correction. It is a thin CLI over `record_po_style` (no second writer home). Full flag spec in
  `behavioral-memory.md`.
- **`--status unrecorded_signals` + soft `--reflect` hint.** The read-only `--status` nudge surfaces the `memory_gap`
  signals and, on high drift-since-last-validate, suggests a retroactive `--reflect` harvest. Read-only — it never
  writes the memory layer. In `workflow-status.md`.

---

## Tier-1 — opt-in Stop hook (capability, never auto-registered)

Beyond the portable core, a project may opt in to a **Stop hook** that runs `memory_gap` at conversation end and turns
its signals into a deterministic at-end reminder (or, for the one persist signal, a block-until-fixed). The hook is
Python via the shared venv and reuses `memory_gap.py` — it adds no new detection.

**Install posture — recommend-and-ask, never silent.** The hook is **opt-in only** and **never auto-registered**: the
capability ships (the hook script + the `--memory-hook` installer flag), and the recipient opts in. Auto-modifying a
user's `settings.local.json` is a trust violation, so the installer merges the hook registration only on explicit
opt-in, idempotently. A passive recommend-nudge appears at most once per day and an explicit "never" silences it
permanently. (Installer mechanics are owned by the installer + its docs; this reference states only the *posture*.)

**Per-signal persistence policy** — not every signal blocks; only the one that is never a false positive does:

| Signal | Hook policy | Why |
|--------|-------------|-----|
| `fence_breach` | **persist** (block-until-fixed, small re-fire cap) | A write outside `docs/product/` is an unambiguous boundary breach — worth stopping for. |
| `validate_no_marker` | **nudge-once** (honors `stop_hook_active`) | Drift is normal mid-work; a one-shot reminder, not a wall. |
| `approved_changed_no_dec` | **nudge-once** (honors `stop_hook_active`) | A legit approved edit is a false positive — block-once would cost at most one re-judgment, so nudge instead. |

"Nudge-once" means the hook respects the harness `stop_hook_active` flag so a single reminder does not loop. The persist
signal re-fires only up to a small cap to avoid a stuck session.

---

## Tier-2 — `--reflect` (retroactive harvest)

When forcing-functions were skipped (a long session, an old spec), `--reflect` retroactively harvests candidate memory
writes — rulings and observations that were never recorded — from the spec/`.memory/` state and (when available) git
history, presents them for PO confirmation, and persists only after confirm. It is **on-demand** plus the soft
`--status` suggestion above, and is **git-degrade-safe**: with no git it harvests `.memory/`/`decisions.md` diff state
only, never crashing. It reuses `memory_gap`'s dedup so it never re-proposes an already-recorded write. (Full flow in
its own workflow reference; this home owns the placement and the dedup contract.)

---

## Honest ceiling (do NOT over-claim)

This model makes the *trigger* reliable; it cannot make the *judgment* reliable. State this plainly:

- **Decision (`DEC`), 3E self-corrections, and the `fence_breach` path get materially stronger** — the deterministic
  detector + the required Memory pass + (opt-in) the persist hook raise how reliably a write is *considered*.
- **3D stays nudge-only.** A PO wording-correction is conversational — there is no structural signal to key on — so 3D
  is forcing-function + `--voice` + retroactive `--reflect`, never a hard capture.
- **The cache is via batch-write** — an optimization, never authoritative. A miss is always safe (re-judge); a content
  change self-heals through the `body_hash` key; a PO override in chat goes to the Decision Register, not the cache.
- **Enforcement raises the consideration-rate, never the write-quality.** The LLM can still honestly rubber-stamp
  "none" on the Memory pass. There is no way around the judgment limit — do not claim "the stores fill themselves" or
  "every slip is recorded". The right claim is *reduced recurrence / reliably prompted*, not *guaranteed*.
