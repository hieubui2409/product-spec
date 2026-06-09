# workflow-learn — learn from reality (`--learn`)

Loaded for `--learn`. The post-launch learning loop: once the product is in front of real users,
the PO has real signal (a monthly benefit report, analytics, order data, customer reviews). `--learn`
is the **umbrella** that turns that signal back into the spec. It owns **two distinct loops** behind
**one PO-facing door**, routed by a single question so a non-technical PO never has to pick a flag:

```
--learn ──► AskUserQuestion: "Số liệu (outcomes) hay Phản hồi (feedback)?" / "Metrics or feedback?"
   ├─ outcomes ─► Path A — quantitative loop (this file §A)
   └─ feedback ─► Path B — qualitative discover-back loop (this file §B)
```

The two paths are SEPARATE code paths under a thin router — each is tested on its own. The router
itself only asks the question and dispatches; it judges nothing.

> **`--learn` vs `--discover`:** `--discover` seeds a COLD Vision/BRD from raw upstream material
> (pre-launch, → new Vision). `--learn` feedback feeds the EXISTING spec via `--update` (post-launch,
> → delta on a live spec). Different lifecycle stage, different destination — same ingest script (DRY).

---

## §A — Outcomes (quantitative loop)

Records what a BRD goal metric ACTUALLY did vs its target, and computes a deterministic verdict.

### A1. Pick goals to measure
For each `BRD-G<n>` that is `approved` or `review` (skip `draft` — not yet committed), offer it for
measurement. A goal the PO has no number for is simply skipped — it shows up later as a **blind spot**
(grey cell) on the `scorecard`, which is itself useful signal ("you never measured this").

### A2. Capture the measurement (GATE-NEVER-ASSUME)
Per goal, collect: `target`, `actual`, `unit`, `direction` (higher-is-better default; `lower` for
latency/defects), `measured_on`, `source` (a human label like "monthly-benefit-report 2026-05" — NOT
a path; this skill is offline, the PO exports analytics to a value).

- **Target suggestion (assist, not assume):** the goal `title` often embeds the target in prose
  ("Onboard **100** boutique brands", "Reach **$2M** GMV"). The LLM may *suggest* that number as the
  target for the PO to confirm or correct. It is a SUGGESTION — never written without the PO's
  explicit OK (GATE-NEVER-ASSUME). The target is captured per measurement (it can move between
  periods); the title stays prose.
- Never invent `actual`. No number → ask, or skip the goal. Never guess a verdict.

### A3. Record → verdict (deterministic / Hybrid)
Call:
```
record_outcome.py --root <root> --append-alloc \
  --goal BRD-G<n> --metric <slug> --target <T> --actual <A> \
  --unit <u> --direction higher|lower --measured-on <ISO> --source "<label>" [--note "..."]
```
- **Numeric metric** → the script computes a **3-tier** verdict: `higher` → ratio = actual/target;
  `lower` → ratio = target/actual; `ratio ≥ hit_floor` → 🟢hit, `partial_floor ≤ ratio < hit_floor`
  → 🟡partial, else 🔴miss. Floors default `0.9 / 0.5`, configurable via `preferences.py`
  (`outcome_hit_floor` / `outcome_partial_floor`). Deterministic — same input → same verdict.
- **Non-numeric metric** (e.g. "review quality") or a `target` of 0/blank → **Hybrid B3**: the script
  cannot divide, so the PO asserts `--verdict hit|partial|miss`. Intentionally outside the
  deterministic gate — captured honestly as a PO judgement.
- `actual: 0` is a REAL measurement (a 🔴miss for higher-is-better), not "unmeasured" — it is always
  recorded as a normal `OUT-<n>` row.
- A `--metric` slug not in the goal's `metrics:` is **blocked** (a typo fragments the scorecard/trend);
  fix the slug, or pass `--force` to record anyway with a warning.

The write only touches `outcomes.md`. It NEVER edits `brd.md` — the goal definition is untouched.

### A4. A miss on an approved goal — surface, never silently flip (GATE-NO-SILENT-REVERSAL)
A `miss` (or `partial`) on an `approved` goal is a learning signal, NOT a license to edit the spec.
Surface it and offer three branches — never auto-pick:
- **Keep** — the goal stands; the miss is recorded, the target unchanged. (Reality missed the goal;
  the goal was right.)
- **Change** — the goal itself was wrong/outdated → route to `--update`, which re-flags downstream and
  requires explicit **re-approval (owner + date)**. Status never flips silently.
- **DEC** — open a `DEC-<n>` ruling (via `decision_register.py --append-alloc`) recording the PO's call
  so it is not re-litigated next period.

### A5. Cadence nudge (soft)
A `outcome-trend` only has meaning with **≥2 measurements** of the same goal+metric over time. After a
first measurement, gently suggest a re-measure cadence (monthly/quarterly) so the trend becomes
readable — a suggestion the PO can ignore, never an enforced schedule.

---

## §B — Feedback (qualitative discover-back loop)

Turns free-text real-world feedback (customer reviews, support notes, "this confused users") into
**candidate** new problems/personas/risks that feed the EXISTING spec via `--update`.

### B1. Read-fence + filter (deterministic — mandatory, reused)
Run `ingest_raw_inputs.py --root <root> --path <p> [--path <p> …] --scaffold` — the SAME read-fenced
ingest `--discover` uses, with **zero changes to its core** (DRY): project-root containment,
`.md`/`.txt` allow-list, dotfile exclusion, bounded directory recursion, per-file size cap.

### B2. Echo accepted/rejected for PO confirm (safety net)
Show the PO the `accepted` list (and `rejected` with reasons) **before reading content**. Proceed only
on PO OK. For directory inputs that fan out, this is the safety net.

### B3. Synthesize candidates (LLM) — nothing committed
With `--scaffold` the script returns raw text + EMPTY candidate buckets. The LLM proposes candidate
problems/personas/risks from the text. Keep scope TIGHT: **text in → candidate bullets out. No
clustering / theme-extraction / NLP gold-plating.**

### B4. Feed `--update` (confirm each → DEC)
Present candidates against the live spec and route confirmed ones through `--update` (delta on the
existing BRD/PRD — NOT a cold Vision seed). **GATE-NEVER-ASSUME**: nothing is written to
`docs/product/` until the PO confirms each candidate; each accepted change records one `DEC-<n>`.

---

## GATEs (both paths)
- **GATE-NEVER-ASSUME** — never write a target, verdict, persona, or problem the PO has not confirmed.
  Suggestions are offered; commits wait for the PO.
- **GATE-NO-SILENT-REVERSAL** — a miss/feedback that contradicts an `approved` goal is surfaced
  (Keep/Change/DEC); changing an approved goal requires re-approval (owner + date).
- **No network** — local files only; `source` is a label, never a fetch.

## What this loop does NOT do (YAGNI / OUT scope)
Live connectors (firebase/DB), parsing raw CSV/JSON analytics, BI dashboards, impact×effort quadrants,
feedback clustering/NLP, migrating the BRD goal schema, auto-fetching insight. Light verdict +
candidate bullets only.
