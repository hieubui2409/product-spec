---
name: cleanmatic:spec-critique
description: "Brutal, sarcastic-but-grounded critique of a product spec (Vision/BRD/PRD/Epic/Story) across 4 lenses (product/tech/market/craft) via dedicated read-only sub-agents + an opus consolidator. Consumes cleanmatic:product-spec output; reuses its --validate findings as ammo, then adds the why-it-dies / market / craft judgment validate deliberately omits. Non-deterministic by design (opinion + web + voice), kept OUT of the reproducible --validate CI gate. Never edits artifacts; writes one critique report."
user-invocable: true
when_to_use: "Invoke when a product owner wants an honest, opinionated critique of an existing spec, 'tear this apart', 'is this any good', 'what would a skeptic say', across product value, feasibility, market, and writing craft. NOT for drafting/validating a spec (that is cleanmatic:product-spec); this only critiques what already exists."
category: product
keywords: [ critique, review, product-spec, brutal, sarcasm, prd, brd, epic, story, market, feasibility, craft ]
argument-hint: "[scope] [--product|--tech|--market|--craft] [--interactive] [--lang vi|en] [--no-web] [--level 1..6]"
metadata:
  author: cleanmatic
  version: "1.0.0"
---

# cleanmatic:spec-critique

A **consumer** skill that critiques the spec produced by `cleanmatic:product-spec`. It reads the spec's
structure + `--validate` verdicts as *ammunition*, then fans out four read-only lens critics
(product/tech/market/craft) in parallel and merges them with an opus consolidator into ONE markdown
critique, in a fixed sarcastic-but-grounded Vietnamese (or English) voice. Every line carries an
evidence `ID:line`, a why-it-dies, and a fix. It **never edits the spec** and **never gates CI**.

> 📘 **PO guide:** [`GUIDE-VI.md`](./GUIDE-VI.md) (Tiếng Việt) / [`GUIDE-EN.md`](./GUIDE-EN.md), every flag,
> every lens, every use-case as a sample dialogue over the `acme-shop` example. Point the PO there first.

## When to Use

- A PO wants an honest, opinionated read on whether a spec is worth building, not a structural pass/fail.
- "Tear this PRD apart", "what would a skeptic / investor / staff engineer say", "is this me-too?".
- Pre-review gut-check before taking a spec to stakeholders.

**NOT for:** drafting, validating, decomposing, or visualizing a spec, that is `cleanmatic:product-spec`.
This skill only critiques what `product-spec` already wrote under `docs/product/`.

## How it differs from `product-spec --validate`

| | `--validate` (product-spec) | `/spec-critique` (this skill) |
|---|---|---|
| Output | pass/fail findings, reproducible | opinionated critique, non-deterministic |
| Voice | warm, PO-facing, neutral | sarcastic, brutal-but-grounded, 6 levels |
| CI gate | yes (deterministic) | **never** (opinion + web + voice) |
| Web research | no | yes (market lens, opt-out `--no-web`) |
| Judges | structure + core-value drift | + why-it-dies, market, craft, cross-lens |
| Edits the spec | no | no (writes a report only) |

It **reuses** validate's findings (run fresh) + cached LLM verdicts as ammo, but a critique line must say
what validate *cannot*: the product/market/craft consequence + a fix. (See **Anti-overlap** below.)

## Flags

| Flag | Purpose |
|------|---------|
| `[scope]` | The artifact to critique by ID (`PRD-AUTH`, `PRD-AUTH-E1`, `PRD-AUTH-E1-S1`) or `all` (default). The full **ancestry** is always pulled as judgment context, even for one story. `all` is the whole tree, expensive (note shown). |
| `--product` / `--tech` / `--market` / `--craft` | Run only the named lens(es). Default = all four. |
| `--interactive` | AskUserQuestion to pick scope + lenses + level before running. |
| `--lang vi\|en` | Critique language. Default `vi`. IDs + frontmatter keys stay English. |
| `--no-web` | Disable the market lens's WebSearch/WebFetch. With no BRD `competitors:` it then **flags missing competitive grounding** rather than fabricating. |
| `--level 1..6` | Voice intensity. Default = the `critique_level` preference (itself `3` if unset); the flag overrides it. Aliases: `--warm`(1) `--gentle`(2) `--blunt`(3) `--savage`(4) `--no-mercy`(5) `--roast`(6). A PO who wants a standing harsh voice sets `critique_level: 6` in `preferences.yaml` once. Levels 1 to 4 forbid personal attack (artifact only). **Levels 5 and 6 both require a warning + an explicit AskUserQuestion confirmation before running:** level 5 lifts the redline (personal barbs allowed); **level 6 (`--roast`) ENFORCES a personal attack, a DANGEROUS roast that insults the PO as the lazy/careless author of a bad spec, FORBIDDEN in professional contexts.** Every level keeps evidence + a fix per line. |

## Output contract

- **Report:** `docs/product/critique/<ts>-<scope>.md` (markdown only, v1). Written by the main agent through
  the soft fence (`fs_guard`). The lens agents, the consolidator, and the humanizer are all read-only: they propose, the main agent writes.
- **Marker:** `docs/product/.memory/last_critique.json` (per-node `body_hash` snapshot), refreshed after each run;
  powers the drift nudge.
- **Never** edits a spec artifact. **Never** gates CI. **Never** auto-writes memory, a PO-confirmed big finding
  may bridge to a Decision (`DEC-<n>`) via product-spec's `decision_register.py`, only on explicit confirm.

## Workflow

```mermaid
flowchart TD
    A[parse flags / --interactive pick] --> G{docs/product exists & non-empty?}
    G -->|no| Z[friendly 'chưa có spec để chửi', spawn NO agents]
    G -->|yes| B[critique_scan.py: structural FRESH + cached verdicts + ancestry + digest + competitors + prior reports]
    B --> C{cache empty/stale?}
    C -->|yes| C1[suggest 'chạy --validate trước', proceed anyway]
    C -->|no| D
    C1 --> D[fan-out selected lens agents in parallel - read-only]
    D --> E[spec-critique-consolidate opus: dedup · severity · top-3 · repeat-offense · DEC-worthy · voice + humanizer Gate 1]
    E --> E2[spec-critique-humanize sonnet: Gate 2 - strip AI/translation tells, keep the bite + findings]
    E2 --> F[main agent WRITES docs/product/critique/<ts>-<scope>.md + --snapshot]
    F --> H{DEC-worthy flagged?}
    H -->|yes| I[AskUserQuestion per item → on confirm: decision_register.py --append, rationale [nguồn: critique]]
    H -->|no| J[done]
```

The executable orchestration lives in **`references/workflow-critique.md`**, load it whenever this skill runs.

## Anti-overlap with `--validate` (mechanical + advisory)

A critique line must NOT merely restate a structural finding. Enforced two ways (the consolidator owns both):
1. **MECHANICAL floor:** a finding line must not be byte-identical to a structural-finding `detail` string, AND
   every finding MUST carry a non-empty `why_it_dies` + `fix`. A finding failing either is dropped.
2. **ADVISORY:** "merely rephrases the validator" beyond the mechanical floor stays a judgment call, keep a
   finding when it adds a real why/fix; drop it when its only content is the validator's label.

## The bundle contract (what the lens agents consume)

`critique_scan.py --root <proj> --scope <id|all> --lang <vi|en>` emits ONE JSON bundle. Top-level keys:
`bundle_version (=2), scope, lang, target_ids, ancestry{vision,brd_goals[],prd,epic}, digest[], source_files{},
structural_findings[], cached_verdicts[], competitors[], prior_reports[], drift_threshold, parse_errors[]`.

- `digest` is a **LIST** of entries `{id,type,role,verbosity,title,frontmatter,body,ac}` (target/ancestor/descendant
  + vision/PRODUCT/BRD singletons), not an object.
- `source_files` is the **citation ground-truth**, keyed by ARTIFACT ID: a map `{<artifact_id>: "<n>: <text>\n..."}`
  giving each artifact's file as line-numbered text. A lens agent's `evidence` is `<artifact_id>:<line>`, and the
  `<line>` MUST be a real number read from `source_files[<that artifact_id>]`, NEVER a bundle-JSON offset, a bare file
  path, or a guessed number. Keying by ID (the citation prefix itself) is what makes every `ID:line` resolve in the
  PO's actual file. Artifacts sharing a file (the BRD goals) each get their own ID key; the BRD container is `BRD`.
- `target_ids` = the scope node + descendants; for `scope=all` it includes the PRODUCT/VISION singletons (they are
  graph nodes). Lens agents critique the targets and judge them against `ancestry`.
- On any failure `critique_scan` emits `{error,scope}` instead (always exit 0), handle both shapes.

## Scripts

- `scripts/critique_scan.py`, the ONLY new analysis script. Deterministic, reuse-first (no LLM): assembles the
  bundle, writes/reads the `last_critique.json` snapshot (`--snapshot`), counts drift (`--drift [--vs-validated]`).
  Reuses product-spec's `spec_graph`, `assemble_digest`, `judgment_cache`, `preferences`, `fs_guard` via a cross-dir
  import, and runs `check_traceability`/`check_consistency` as a subprocess. Always exits 0.
- Reused (read-only) from `product-spec/scripts/`: `decision_register.py` (the DEC bridge), `preferences.py` (the
  `critique_drift_threshold` key, default 3).

> ⚙️ **Venv bootstrap (first run):** before invoking any script, check the shared interpreter exists
> (`./.claude/skills/.venv/bin/python3` on POSIX, `.claude\skills\.venv\Scripts\python.exe` on Windows). If it is
> **missing**, do NOT silently fail or fall back to system Python, ask the user via **AskUserQuestion** to confirm
> running an installer (`product-spec/install.sh` or `spec-critique/install.sh`, both idempotent, both reuse the
> SAME shared venv). Run only on approval, then retry. spec-critique adds no new runtime dependency.

> 🪝 **Opt-in drift nudge hook:** `spec-critique/install.sh --critique-hook` registers the advisory Stop hook
> `spec_critique_nudge.py` into `.claude/settings.local.json` (gitignored; `--critique-hook-shared` → committed
> `settings.json`). After a `--validate`, if the spec drifted ≥ `critique_drift_threshold` nodes since the last
> critique, it nudges (once per session), never auto-runs, never blocks. Opt-in only; never auto-registered.

## Loads `references/*` on demand

| When | Reference |
|------|-----------|
| every run (the orchestration) | `references/workflow-critique.md` |
| rendering the voice at `--level` | `references/voice-and-tone.md` |
| a lens's framework checklist | `references/lens-frameworks.md` |
| writing prose that reads human (both humanizer gates) | `references/humanizer-and-anti-ai-tells.md` |

## Two GATEs (always on)

- **GATE-NEVER-ASSUME:** never assume scope, lenses, or level when ambiguous, ask (or honor the flags). Never write
  a `DEC` or touch any spec artifact without explicit PO confirmation.
- **GATE-NO-SILENT-REVERSAL:** if a critique finding contradicts an `approved` artifact, do NOT edit it. Surface the
  DEC-worthy item to the PO (Keep / Change+re-approve / Hybrid) and only record via `decision_register.py` on confirm.

## What this skill does NOT do

- No code generation. No spec editing (critique writes a report, never an artifact).
- No CI gate (non-deterministic by design, opinion + web + voice).
- No auto-memory writes (only a PO-confirmed `DEC` bridge).
- No HTML/PDF report (markdown only, v1). No new venv. No new sample spec (reuses `product-spec/examples/acme-shop`).
