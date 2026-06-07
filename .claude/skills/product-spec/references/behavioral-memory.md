# Behavioral Memory — PO-style (3D) + LLM-self-correction (3E)

Two behavioral stores that extend the memory layer. They are **behavioral**, not structural: the structural memory
(`decisions.md`, `preferences.yaml`, `judgments.json`) records *facts and verdicts*; these two record *how the skill
talks* and *how the skill behaves*. Both live under `docs/product/.memory/` and are committed.

> **The one-line distinction:** **3D shapes OUTPUT wording. 3E guards BEHAVIOR.** PO-style tunes the prose the PO
> reads; self-correction tunes the skill's own conduct before it acts. They never overlap — 3E is never user-facing
> voice, 3D never gates an operation.

Helper: `scripts/behavioral_memory.py` (the SCRIPT half — read / write / shape-validate / lang-key / frequency / the
DRY guard). The LLM half observes the PO's voice and decides what to write. Standard Script-vs-LLM split.

---

## 3D — PO-style (`po-style.yaml`)

### Purpose

Capture the product owner's own **voice** so generated prose sounds like *their* product, not a generic template. It
shapes — never dictates — the wording of:

- the vision narrative,
- story descriptions and acceptance phrasing,
- `AskUserQuestion` text and options.

It is a phrasing layer. It changes *how* something is said, never *what is true*.

### File & format (lang-keyed)

`docs/product/.memory/po-style.yaml` — committed, PO-authored intent. **Lang-keyed** (`en` / `vi`): the PO's wording in
one language must never leak into prose generated in the other.

```yaml
version: 1
voice:
  en:
    register: "warm but concise"            # the scalar tone; latest observation wins
    vocabulary: ["shopper", "store admin"]  # the PO's OWN terms (use these, not synonyms)
    recurring_asks: ["always include a one-line summary"]
    do: ["use 'shopper' not 'customer'"]
    dont: ["no jargon like 'churn' or 'funnel'"]
  vi:
    register: "thân thiện nhưng ngắn gọn"
    vocabulary: ["người mua"]
    recurring_asks: []
    do: []
    dont: []
```

- The four list fields (`vocabulary` / `recurring_asks` / `do` / `dont`) are **union-merged** on each observation
  (deduped, order-preserving) — repeated observations accrue without churn. `register` is the one scalar and the latest
  observation overwrites it.
- A missing file, a missing lang block, or a corrupt YAML all degrade to an EMPTY voice block on read — `load_po_style`
  never raises (absence is benign; it just seeds phrasing).

### Read trigger

At **prose-generation** time. Before composing the vision narrative, a story description, or an `AskUserQuestion`,
read `load_po_style(root, lang)` for the **active session lang** and let the PO's vocabulary / register / do-don't
shape the wording. The read hook-line lives in `references/workflow-interview.md` (§ Bilingual Handling).

### Write trigger (keeps the store from staying empty — but soft, not guaranteed)

Two entry points, both writing through `record_po_style` (one writer home — no parallel write path):

- **Per-prose-turn forcing-function (the portable Tier-0 reminder).** On every prose-bearing turn the interview flow
  asks one deterministic question — *did the PO correct my wording this turn?* — and records the do/dont/vocabulary if
  so. The forcing-function line + its placement live in `references/workflow-interview.md` (§ PO-style read → Per-prose-turn
  forcing-function); the whole enforcement model (why it is a forcing-function, the honest ceiling) is in
  `references/memory-enforcement.md`. This raises the *consideration*-rate, not the write-quality.
- **Explicit `--voice` (the deterministic PO entry point).** `behavioral_memory.py --voice --lang <en|vi>
  [--register <s>] [--vocabulary a,b] [--recurring-asks …] [--do …] [--dont …]` lets the PO state a preference directly
  instead of relying on the LLM noticing a correction. It is a thin CLI over `record_po_style` (union-merge lists,
  latest `register` wins) and honors the same DRY guard. At least one writable field is required; an empty `--voice` is
  a no-op with a clear message, not a crash. The read path (`--dump po-style`) is unchanged.
- **Observation mid-composition.** When the LLM has observed enough of the PO's voice to register a term or a recurring
  ask (even without an explicit correction), it may call `record_po_style` directly.

> **Honesty caveat (do NOT over-claim):** even with the forcing-function and `--voice`, these triggers are
> **LLM-discretionary prose** (except `--voice`, which the PO drives deterministically). 3D stays **nudge-only** — a
> wording correction is conversational, with no structural signal to key on, so there is no opt-in hook for it. The
> store *reduces* the chance the same wording correction is needed twice and is also recoverable retroactively via
> `--reflect`; it does NOT *always accrue* on every turn. "Reduced recurrence", never "the store actually fills itself".

### DRY guard (the Script-vs-LLM split, made concrete)

Behavioral memory shapes **phrasing only** — it must NEVER re-home a structural fact that already has an authoritative
home in frontmatter. The guard is split into a script half and an LLM half along the closed-enum / open-text line:

| Copy attempt | Decidable by | Where enforced |
|--------------|--------------|----------------|
| A **closed-enum structural value** copied into vocabulary/do/dont — `scope` (`in`/`out`/`core-value`), `moscow` (`must`/`should`/`could`/`wont`), `horizon` (`now`/`next`/`later`) | **Script** — exact match against a fixed enum set | `behavioral_memory.py` → `_assert_no_structural_copy` raises `BehavioralError`. **Asserted in pytest.** |
| A **persona label** copied into vocabulary (re-homing the persona list that lives in `PRODUCT.md`) | **LLM** — persona labels are open PO free-text, not a closed enum, and `PRODUCT.md` is not passed into the pure validator | LLM-side judgment at write time (this section). **NOT asserted in pytest.** |

- **Script half:** the comparison is case-insensitive on the trimmed token, so `Must` and `must` are both caught. A
  natural phrase that merely *contains* an enum word as a substring (`core shopper journey`) is **not** a copy and
  passes — the guard rejects exact closed-enum copies, never the PO's natural language.
- **LLM half (persona labels):** before writing a `vocabulary` term, check it against the persona labels in
  `PRODUCT.md`. If the PO's "term" is actually a persona label, do **not** copy it into `po-style.yaml` — the persona
  list is DRY-homed in `PRODUCT.md` (full narrative in `vision.md`). Reference the persona by its label there; the
  voice store records *how the PO phrases things*, not *who the personas are*. This is judgment (open free-text, needs
  `PRODUCT.md`), so it is the LLM's job — exactly the Script-vs-LLM split.

---

## 3E — LLM-self-correction (`self-corrections.json`)

### Purpose

A short, growing memory of the skill's own **recurring slips** so it can run a pre-flight self-check before an at-risk
operation and not repeat the same mistake. It guards **behavior**, never output voice. It is never shown to the PO as
prose.

### File & format

`docs/product/.memory/self-corrections.json` — committed now (privacy toggle flagged below).

```json
{
  "schema_version": "1",
  "corrections": [
    {
      "slip": "wrote code into a story body",
      "violated_rule": "script_vs_llm_split",
      "frequency": 2,
      "last_seen": "2026-06-01T18:53:00+00:00",
      "reminder": "redirect code asks to stories + acceptance criteria"
    }
  ]
}
```

- **`violated_rule` is required and closed** to the five operating principles (`CLAUDE.md` § Five Operating Principles).
  An un-anchored slip has no corrective lesson, so the citation is mandatory:

  | `violated_rule` value | Operating principle |
  |-----------------------|---------------------|
  | `frontmatter_source_of_truth` | 1 — frontmatter is the structural truth |
  | `dry` | 2 — one authoritative home per fact |
  | `script_vs_llm_split` | 3 — scripts do structure; the LLM does judgment |
  | `no_silent_reversal` | 4 — never auto-flip an `approved` decision |
  | `never_overwrite_prose` | 5 — never overwrite the PO's own words |

- A **repeat of the same (`slip`, `violated_rule`)** increments `frequency` and refreshes `last_seen` — no duplicate
  row. A new slip appends a fresh row at `frequency: 1`.
- A missing / corrupt store degrades to empty on read — `load_self_corrections` never raises.

### Read trigger (pre-flight self-check)

Before an **at-risk operation** — most importantly before a `Write`, before regenerating downstream prose, or before
resolving a contradiction — read `load_self_corrections(root)` and re-check the operation against the recorded
reminders. A high-`frequency` slip is the strongest nudge.

### Write trigger (soft fence + Contradiction Protocol feed it — soft, not guaranteed)

- **`check_fence.py`** surfaces a `fence_breach` (a write that landed outside `docs/product/`) → record the structural
  slip (`violated_rule: dry` or `frontmatter_source_of_truth` as appropriate) so the next pre-flight catches it. The
  same breach is also the `fence_breach` signal `memory_gap.collect` emits — surfaced in the required validate **Memory
  pass** and, in an opted-in install, **persisted** (block-until-fixed) by the Tier-1 Stop hook, the one signal strong
  enough to stop for. Detector + hook policy: `references/memory-enforcement.md`.
- **The Contradiction Protocol** (`validation-rules-spec.md`) catching an attempted auto-flip → record
  `violated_rule: no_silent_reversal`.
- The **PO** catching a slip directly → record it with the principle it violated.

The write hook-line lives in `references/workflow-validate.md` (§ Step 2.5, after the impact-pass); the required Memory
pass (§ Step 2.7) makes "structural slip → 3E?" one of the three questions every validate report MUST answer.

> **Honesty caveat (the soft-fence reality):** 3E is a **soft** mechanism — `check_fence.py` is advisory (always exits
> 0, never blocks), and the LLM writes the entry at its discretion. The required Memory pass and the opt-in persist-hook
> raise how reliably the slip is *considered*, never that the write is *made*. The store **reduces recurrence**; it is
> **not a hard block** and does **not** guarantee a slip is recorded every time. Do not claim "stores actually accrue" —
> that is reduced-recurrence, not an invariant.

### Privacy posture

`self-corrections.json` is committed **now** (per the locked folder-split decision: `decisions.md` visible + `.memory/`
hidden, all committed). But a `slip` or `reminder` can **echo PO wording** verbatim. So:

- **Privacy toggle flagged for later** — the same always-drop posture `release`'s safety filter applies to session
  state. When the toggle ships, an opted-out project keeps the store local (gitignored), not committed.
- **Mirror the agent-memory drop posture:** treat the slip text as potentially sensitive; keep it terse and structural
  ("wrote code into a story body"), not a transcript of the PO's words.

---

## Why two stores, not one

3D and 3E are deliberately separate files with separate shapes because they answer different questions and have
different lifecycles:

- **3D is PO-authored intent** — the PO owns their voice; it is read on every prose generation and shapes user-facing
  output. It is bilingual (lang-keyed) because voice is language-specific.
- **3E is session-derived** — the *skill* owns its conduct memory; it is read before at-risk ops and never surfaces as
  voice. It is lang-agnostic (a slip is a behavior, not a phrasing).

Collapsing them would force user-facing voice and internal conduct into one schema and one privacy posture — exactly
the conflation this split avoids.

## Not to be confused with: the engagement-profile PREFERENCES

The `interview_rigor` / `action_prompting` **engagement knobs** (`preferences.yaml`, wired in
`workflow-interview.md` → *Engagement profile*) are **closed-enum PREFERENCES, not a third behavioral store**.
They are PO-confirmed session defaults (like `detail_level` / `lang`): the only writers are the PO-typed
`preferences.py --set` or the PO-confirmed end-of-session forcing-function — never LLM-discretionary, never
session-derived. Don't read them as 3D voice (they shape *how hard the interview probes / how many next-actions
it offers*, not the PO's wording) nor as 3E conduct (they're user-set knobs, not the skill's self-corrections).
DRY home for their behaviour table: `workflow-interview.md`; schema home: `scripts/preferences.py`.
