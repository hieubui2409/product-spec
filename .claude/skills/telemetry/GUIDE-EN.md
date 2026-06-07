# Using `cleanmatic:telemetry` (English)

A guide for **product owners**. Each use-case is a sample dialogue. The natural-language way (just ask) is preferred; the flag form is the equivalent.

> Vietnamese version: [`GUIDE-VI.md`](./GUIDE-VI.md).

---

## 1. What it is, and what it is NOT

`cleanmatic:telemetry` is a **read-only, honest read** of how your own skills and scripts are being used and whether they are healthy. It runs **eight lenses** over your local telemetry (skill invocations, sessions, script runs, subagent outcomes, memory tidiness) and narrates the results in plain Vietnamese (or English with `--lang en`).

It is **NOT**:
- A **market effectiveness** metric (E3). It sees *usage*, not *value*.
- An **editor** — it never touches specs, code, the catalog, or memory.
- **Billing-exact** — token counts and run times are directional estimates.
- A **CI gate** — it is opinion-free numbers for you to read; nothing blocks on it.
- A **crash-log analyzer** — it lacks rich `errors.jsonl` for now.

**It IS:** a diagnostic window into *whether your machinery runs* (usage ✓, health ✓, internal-quality ✓).

---

## 2. Core concepts — the mental model (read this once)

1. **Script gathers; LLM narrates.** The Python script (`analyze_telemetry.py`) reads append-only JSONL sinks (deterministic, stdlib-only) and produces JSON aggregates. The skill **narrates** those numbers in plain Vietnamese, following the narration contract (`references/narration-contract.md`).

2. **Eight lenses, one report.** The `--all` report shows all eight lenses (except forensics, which is a deep-dive separate from the dashboard). Each lens answers one question:
   - `usage` — which skills, how often, token weight, never-used?
   - `session` — how many sessions, duration, co-occurrence?
   - `health` — script errors, run times, subagent success?
   - `reliability` — subagent failure modes (timeout, api_error, etc.)?
   - `workflow` — actual skill chains vs. declared chains?
   - `validate` — did the spec validate pass (internal quality)?
   - `memory` — orphaned notes, dead links, staleness?
   - `forensics` — reconstruct one session in detail (skills, tools, tokens, files).

3. **Low-volume gate.** Below ~5 data points, a lens shows raw counts + **"chưa đủ dữ liệu" (insufficient data)** and suppresses recommendations. On a fresh repo, **most lenses are gated** — the report says so plainly.

4. **The honesty gate (mandatory).** Every report ends with **"Cái này KHÔNG đo được"** (This cannot be measured), naming:
   - E3 / market outcome — whether the product wins in the market.
   - Any gated lens — explicitly with "chưa đủ dữ liệu".
   - Approx disclaimers — tokens, ms, exit codes are ước lượng (estimates), not exact.

5. **Recommendations are suggestions, not orders.** Phrases like "Gợi ý" (suggestion) signal that the skill has no authority to delete skills, edit memory, or change scope — you decide.

---

## 3. Your learning path

- **First run:** `/cleanmatic:telemetry` at the default (all lenses, ascii, Vietnamese) and read the report. You'll see the shape: summary → usage → health → sessions → workflow → validate → memory → honesty gate.
- **Then focus:** Pick one or two lenses (`--lens usage`, `--lens health`) to drill into.
- **Try formats:** `--format md --top 5` for a concise markdown table, `--format mermaid` for charts, `--format json` to script further.
- **Deep dive:** `--session <id>` to reconstruct a single session's skill flow (needs the session ID from the session lens).
- **As you build:** run it weekly or before major decision; the data is cumulative, so patterns emerge over time.

---

## 4. Important caveats & gotchas

- **Never-used external skills are not flagged.** Skills you don't own (e.g., `ck:code-review`, `com:mcp-builder`) are normal to not use — only **never-used cleanmatic skills** (`cleanmatic:*`) are highlighted.
- **Token weight is approximate.** Derived from transcript length + a rough per-skill coefficient; labeled "ước lượng", never exact.
- **The validate proxy is internal quality only** — "spec is well-formed", not "users adopted it" (that is E3).
- **Low-volume data is reported honestly.** On a fresh repo, many lenses will say "chưa đủ dữ liệu" — that's the truth, not a shortcoming.
- **No `--apply` flag.** This skill is diagnostic only. Findings stay as suggestions; you decide what to do.

---

## When to use

- You want an honest read on how your skills are being used, not a pass/fail.
- "Which scripts are erroring?", "Are subagents reliable?", "Is memory tidy?".
- "Is the spec validate passing?" (as an internal-quality snapshot).

NOT for: editing the spec, writing code, deleting skills, or fixing memory — that is other skills (`product-spec`, code-review, etc.).

---

## 5. Use cases — grouped by tier

---

## Tier A — Run your first telemetry read

### A1. Snapshot the whole stack

> **You:** "Show me how my skills are being used and whether they're healthy."
> **Assistant:** Runs all eight lenses, narrates in Vietnamese, ends with the honesty gate. Report shows: top invoked skills + token weight → never-used → script errors → subagent reliability → memory state → validate proxy → "Cái này KHÔNG đo được" (E3, any gated lens, token disclaimers).
>
> Flag form: `/cleanmatic:telemetry` or `/cleanmatic:telemetry --lens all --format ascii`.

### A2. Reading the report (structure)

- **Tóm tắt (Summary)** — 2–3 lines: overall usage level, any health issues, data sufficiency.
- **Mức dùng (Usage)** — top skills by invocation count + approx token weight + never-used cleanmatic skills.
- **Sức khỏe (Health)** — scripts that error or run slow; subagent success/failure breakdown.
- **Phiên (Sessions)** — session count, avg/median duration, co-occurrence (skills used together).
- **Workflow chains** — actual vs. declared skill chains; deviations flagged.
- **Validate proxy** — last validate pass/fail + pass-rate (internal quality snapshot, tagged "không phải E3").
- **Memory** — orphaned notes, broken `[[links]]`, staleness.
- **Cái này KHÔNG đo được** — honesty section: E3 + gated lenses + approx disclaimers.

---

## Tier B — Focus & drill deeper

### B1. Usage only: which skills are cold?

> **You:** "I want to know which of my skills nobody is using."
> **Assistant:** Runs `--lens usage` → shows invocation counts, token weight, never-used cleanmatic skills. One-line per skill. Only your owned skills are listed (external skills are not flagged).
>
> Flag form: `/cleanmatic:telemetry --lens usage`.

### B2. Health: spot the broken scripts

> **You:** "Which scripts are failing or running slow?"
> **Assistant:** Runs `--lens health` → shows per-script run count, error rate, avg ms (approx). Any script with >0 errors is highlighted. Slow runs are estimated (ước lượng).
>
> Flag form: `/cleanmatic:telemetry --lens health`.

### B3. Reliability: are my subagents trustworthy?

> **You:** "Tell me the subagent success breakdown."
> **Assistant:** Runs `--lens reliability` → shows per-subagent-type: success, api_error, timeout, blocked, unknown. Helps you spot patterns (e.g., "researcher times out often").
>
> Flag form: `/cleanmatic:telemetry --lens reliability`.

### B4. Sessions: how long do people spend?

> **You:** "How many sessions have we had, and how long do they take?"
> **Assistant:** Runs `--lens session` → shows session count, avg/median duration (in minutes), file/tool co-occurrence, skill co-occurrence. Co-occurrence shows which skills are used together (workflow patterns).
>
> Flag form: `/cleanmatic:telemetry --lens session`.

### B5. Validate proxy: is the spec well-formed?

> **You:** "Did the last spec validate pass?"
> **Assistant:** Runs `--lens validate` → shows last validate result (pass/fail) + pass-rate over N runs. Explicitly tagged "không phải E3" (not market outcome, internal quality only).
>
> Flag form: `/cleanmatic:telemetry --lens validate`.

### B6. Memory: is the decision log tidy?

> **You:** "Are there any orphaned decisions or broken links in my memory?"
> **Assistant:** Runs `--lens memory` → shows orphaned notes, dead index entries, broken `[[links]]`, staleness (notes not updated in 30+ days). Read-only; no `--apply` (this is diagnostic, not auto-fix).
>
> Flag form: `/cleanmatic:telemetry --lens memory`.

### B7. Workflow: do skill chains match the docs?

> **You:** "Are my actual skill invocation chains matching what the routing docs say?"
> **Assistant:** Runs `--lens workflow` → compares actual chains (from invocation logs) vs. declared chains (from `.claude/rules/skill-workflow-routing.md`). Deviations are flagged (e.g., "we said planner → cook, but you're doing planner → debug directly").
>
> Flag form: `/cleanmatic:telemetry --lens workflow`.

---

## Tier C — Output formats & fine-tuning

### C1. Markdown table (top-N, copy-paste friendly)

> **You:** "Give me the usage lens in markdown, top 5 only."
> **Assistant:** Runs `--lens usage --format md --top 5` → markdown table: skill name, invocation count, approx tokens, never-used flag. Copy-paste friendly; shorter than ascii.
>
> Flag form: `/cleanmatic:telemetry --lens usage --format md --top 5`.

### C2. Mermaid charts (no network)

> **You:** "Show me the subagent success breakdown as a pie chart."
> **Assistant:** Runs `--lens reliability --format mermaid` → fenced mermaid pie/bar chart. Works in markdown viewers; requires no network or JS.
>
> Flag form: `/cleanmatic:telemetry --lens reliability --format mermaid`.

### C3. JSON (for scripting)

> **You:** "Give me the raw aggregates as JSON so I can process them."
> **Assistant:** Runs `--lens all --format json` → prints JSON dict of all aggregates. Useful for building dashboards or alerts.
>
> Flag form: `/cleanmatic:telemetry --lens all --format json`.

### C4. English mode

> **You:** "Give me the report in English, not Vietnamese."
> **Assistant:** Runs `--lang en` → fixed labels (headings, column headers, gate note) localize to English; LLM narrates in English too.
>
> Flag form: `/cleanmatic:telemetry --lang en`.

### C5. Custom lookback (days)

> **You:** "Show me the last 7 days only."
> **Assistant:** Runs `--days 7` → same lenses, filtered to last week. Default is 30 days.
>
> Flag form: `/cleanmatic:telemetry --days 7`.

---

## Tier D — Forensics: reconstruct a session

### D1. List all sessions

> **You:** "Which sessions do I have on record?"
> **Assistant:** Runs `--all-sessions` → prints a table of all session IDs, timestamps, skill count, file count, duration. Pick one for deep-dive.
>
> Flag form: `/cleanmatic:telemetry --all-sessions`.

### D2. Reconstruct one session

> **You:** "Show me what happened in session abc123def."
> **Assistant:** Runs `--session abc123def --format md` → reconstructs: entry point skill → all sub-calls (skills, tools, LLM calls, etc.) → tokens used → files touched → duration. Full call tree.
>
> Flag form: `/cleanmatic:telemetry --session <id> --format md`.

---

## 6. Mixing flags — common recipes

| Want | Command |
|------|---------|
| Weekly health check | `/cleanmatic:telemetry --days 7` |
| Top 10 invoked skills + tokens | `/cleanmatic:telemetry --lens usage --format md --top 10` |
| Spot script errors | `/cleanmatic:telemetry --lens health` |
| Subagent reliability pie chart | `/cleanmatic:telemetry --lens reliability --format mermaid` |
| Memory tidy check | `/cleanmatic:telemetry --lens memory` |
| Full snapshot, english, markdown | `/cleanmatic:telemetry --lang en --format md` |
| Last 14 days, usage only | `/cleanmatic:telemetry --days 14 --lens usage` |
| Reconstruct a session | `/cleanmatic:telemetry --session <id>` |
| Raw JSON for scripting | `/cleanmatic:telemetry --format json` |

---

## 7. Core concepts (deeper dive)

### The data model

Five append-only JSONL sinks under `.claude/telemetry/` (gitignored):

- **`invocations.jsonl`** — every time you invoke a skill. Fields: skill name, timestamp, tokens (approx), transcript hash.
- **`sessions.jsonl`** — end-of-session summary. Fields: session ID, timestamp, duration, file list, subagent list, skill co-occurrence.
- **`hook-telemetry.jsonl`** — script execution logs. Fields: script name, timestamp, exit code, ms, error message (if any).
- **`subagent-outcomes.jsonl`** — subagent completion. Fields: subagent type, outcome (success / api_error / timeout / blocked / unknown), duration, error.
- **`last_validated.json`** — validate result snapshot. Fields: pass/fail, timestamp, pass-rate (from exit history).

All five sinks are written by fail-open hooks (auto-registered on install; opt out: `register_telemetry_hooks.py --remove`). On recipients, hooks write to their own `.claude/telemetry/` under their project root.

### Script → aggregates (what analyze_telemetry.py does)

1. Read all sinks into memory.
2. Group by metric (e.g., skill invocations grouped by skill name).
3. Compute counts, rates, averages, medians.
4. Check against low-volume gate (~5 points).
5. Emit JSON dict with all aggregates.

Script is deterministic, never judges. **The LLM judges** (narrates in VI, applies the honesty gate).

### Never-used (external vs. owned)

A skill in the catalog (from `.claude/rules/skill-workflow-routing.md`) that has zero invocations in the lookback period is "never-used".

- If it is a **cleanmatic skill** (`cleanmatic:*`), it is flagged as a candidate to review (maybe it is no longer needed?).
- If it is an **external skill** (`ck:*`, `com:*`, etc.), it is **not flagged** — the PO doesn't own it and may have no use for it. Only the count of never-used external skills is mentioned, not the list.

### Token weight (ước lượng)

Token counts are **directional**, not exact. Derived from transcript length + a per-skill coefficient (learned from a sample of runs). Always labeled "ước lượng" (estimate).

### Validate proxy (internal quality ≠ E3)

The `validate` lens shows whether `product-spec --validate` passed on the last run + the pass-rate. This is **internal quality** (spec is well-formed, no orphans, no core-value drift). It is **not** E3 (market effectiveness, user adoption, revenue). The report explicitly tags it "không phải E3".

---

## 8. Troubleshooting

### "Chưa đủ dữ liệu" on many lenses

**Normal on a fresh repo.** Telemetry accumulates over time. Once you have ~5+ data points per lens, recommendations appear.

**What to do:** Keep using the skills, and run `/cleanmatic:telemetry` again in a week.

### "Script X always errors"

**Check the error message** in the `health` lens. Run the script manually and see what fails. The skill is diagnostic; it doesn't fix.

**What to do:** Check the script's logs, look at the stack trace, file a bug or fix it directly.

### Session forensics shows 0 tokens

**Tokens are approximate.** If a session has few or no LLM calls, tokens may be 0. Check the session details (skills, tools) to see what actually happened.

### Memory shows "staleness" on my notes

**Notes older than 30 days are flagged.** This is normal if notes are stable; archive or update them if they are truly stale.

**What to do:** Review old notes, delete irrelevant ones, or update timestamps for notes you still use.

---

## 9. Asking the skill in natural language

You don't need flags. Just ask:

- "Show me which skills are cold."
- "Are subagents reliable?"
- "Did validate pass?"
- "Reconstruct session abc123."
- "Top 5 skills by invocation."
- "Workflow deviations."
- "Memory cleanup suggestions."

The skill will translate your intent into flags and run the right lenses.

---

## 10. Deep links & references

- **Narration contract** (rules for honest language): `references/narration-contract.md`
- **Full operating contract**: `SKILL.md`
- **Vietnamese guide**: `GUIDE-VI.md`
- **Lens modules**: `.claude/skills/telemetry/scripts/lens_*.py`
- **Script source**: `.claude/skills/telemetry/scripts/analyze_telemetry.py`
- **Changelog**: `CHANGELOG.md`
