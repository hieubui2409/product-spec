---
name: cleanmatic:telemetry
description: "Plain-Vietnamese read on how the PO's skills are actually used + whether their scripts/subagents are healthy + a thin internal-quality proxy (did validate pass). Runs read-only lenses over local telemetry (invocations, sessions, script runs, subagent outcomes, memory) and narrates them honestly — usage & health, NOT market effectiveness. Outputs ascii/markdown/mermaid/json."
user-invocable: true
when_to_use: "When the (non-technical) product owner asks how their skills are being used, which scripts error or run slow, whether subagents succeed, whether memory is tidy, or whether the last spec validate passed — and wants it explained in plain Vietnamese, not raw logs."
category: observability
keywords: [telemetry, usage, health, skills, tokens, sessions, reliability, subagents, memory, validate, vietnamese, dashboard, analytics]
argument-hint: "[--lens usage|session|health|reliability|workflow|validate|memory|forensics|all] [--format ascii|md|mermaid|json] [--days N] [--top N]"
metadata:
  author: cleanmatic
  version: "1.0.0"
---

# cleanmatic:telemetry — Usage & Health (Mức dùng & Sức khỏe)

A **read-only** skill that tells the product owner, **in plain Vietnamese**, three things about their own tooling:

1. **Mức dùng (Usage)** — which skills get used (and how often), token weight per skill, and which skills are never touched.
2. **Sức khỏe (Health)** — which scripts error or run slow (approx), whether subagents succeed/fail, whether memory is tidy.
3. **Một tín hiệu chất lượng nội bộ (a thin internal-quality proxy)** — after a `product-spec` run, did `validate` pass.

**Honest framing — this is "mức dùng & sức khỏe", NOT "hiệu quả".** It measures *whether the machinery runs*, never *whether the product wins in the market* (that is E3, deliberately deferred). The narration MUST keep that line bright (see the honesty gate below).

## What this is NOT

- **Not** a market/user-outcome metric (E3). The validate proxy = "spec is well-formed", not "users adopted it".
- **Not** a writer — it never edits specs, code, the catalog, or memory. No `--apply`, no fixes.
- **Not** billing-exact — token attribution and `ms` durations are **directional/approx**.
- **Not** a CI gate — opinion-free numbers for the PO to read, nothing blocks on it.

## How it runs (deterministic gather → LLM narrates)

The split both repos follow: a **script gathers** (deterministic, never judges), the **skill narrates** (judges, in VI). The skill NEVER recomputes a number — it narrates the script's dict.

```bash
./.claude/skills/.venv/bin/python3 ./.claude/skills/_shared/scripts/analyze_telemetry.py \
  --lens all --format ascii [--days 30] [--top 10]
```

Default behaviour when the PO invokes `/cleanmatic:telemetry`:
1. Run `analyze_telemetry.py --lens all --format ascii`.
2. Read the aggregates; **narrate in Vietnamese** (use `--en` / "in English" to switch).
3. Lead with the honesty gate; recommendations are **gợi ý (suggestions)** only.

Pass-through flags: `--lens <name>`, `--format md|mermaid|json`, `--days N`, `--top N`, `--session <id>` / `--all-sessions` (forensics). The venv interpreter is mandatory.

## Lenses

| `--lens`     | Reads (sink)                          | Surfaces |
|--------------|---------------------------------------|----------|
| `usage`      | `invocations.jsonl` + transcripts     | invocation counts, per-skill tokens (approx), never-used catalog |
| `session`    | `sessions.jsonl`                      | session count, avg/median duration, files, subagents, skill co-occurrence |
| `health`     | `hook-telemetry.jsonl`                | per-script runs/errors/error-rate + avg `ms` (approx) |
| `reliability`| `subagent-outcomes.jsonl`             | subagent success / api_error / timeout / blocked / unknown per type |
| `workflow`   | `invocations.jsonl` + routing docs    | actual skill chains vs declared chains; deviations |
| `validate`   | `last_validated.json` + `hook-telemetry` | validate-pass proxy (internal quality, NOT E3) |
| `memory`     | `~/.claude/projects/<root>/memory/`   | orphans, dead index entries, broken `[[links]]`, staleness (read-only) |
| `forensics`  | session transcript JSONL              | one session reconstructed (skills/tools/tokens/files/duration) |
| `all`        | the above (minus forensics)           | the dashboard-lite the PO reads first |

## Low-volume gate (chưa đủ dữ liệu)

Below ~5 data points a lens shows raw counts + **"chưa đủ dữ liệu"** and **suppresses recommendations**. On a thin/new repo most lenses WILL be gated — say so plainly; do not invent trends.

## Narration & honesty gate (mandatory)

Detailed rubric: `references/narration-contract.md`. The non-negotiable parts:

- **Separate MEASURED from NOT-MEASURED.** Every report MUST end with a section **"Cái này KHÔNG đo được"** naming at minimum: market/user outcome (E3); plus any lens that is empty/gated on current data → call it "chưa đủ dữ liệu", never spin it.
- **Approx is approx.** Token weight, `ms`, and `exit` are inferred/directional — say "ước lượng", never present them as exact.
- **Suggestions, not verdicts.** Phrase any action as a gợi ý the PO may ignore; the skill has no authority to prune skills, edit memory, or change scope.
- **VI is native-quality** — correct diacritics, natural register for a non-technical owner; numbers stay numbers, skill ids stay ascii.

## Boundaries

- **Read-only.** No edits to spec/code/catalog/memory; no network; venv-run.
- **GATE-NEVER-ASSUME / GATE-NO-SILENT-REVERSAL:** not applicable in the usual sense (nothing is written/approved), but the skill still never fabricates a metric — an absent signal is reported as absent.
- **Deferred capabilities** (NOT in this skill): rich crash-log `errors.jsonl` (can't instrument shipped scripts), HTML output, and E3 market-outcome. See `BACKLOG.md`.

## CHANGELOG

See `CHANGELOG.md`.
