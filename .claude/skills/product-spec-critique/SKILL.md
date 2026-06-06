---
name: cleanmatic:product-spec-critique
description: "Brutal, sarcastic-but-grounded critique of a product spec (Vision/BRD/PRD/Epic/Story) across 4 lenses (product/tech/market/craft) via dedicated read-only sub-agents + an opus consolidator. Consumes cleanmatic:product-spec output; reuses its --validate findings as ammo, then adds the why-it-dies / market / craft judgment validate deliberately omits. Non-deterministic by design (opinion + web + voice), kept OUT of the reproducible --validate CI gate. Never edits artifacts; writes one critique report."
user-invocable: true
when_to_use: "Invoke when a product owner wants an honest, opinionated critique of an existing spec, 'tear this apart', 'is this any good', 'what would a skeptic say', across product value, feasibility, market, and writing craft. NOT for drafting/validating a spec (that is cleanmatic:product-spec); this only critiques what already exists."
category: product
keywords: [ critique, review, product-spec, brutal, sarcasm, prd, brd, epic, story, market, feasibility, craft ]
argument-hint: "[scope] [--product|--tech|--market|--craft] [--interactive] [--lang vi|en] [--no-web] [--level 1..9]"
metadata:
  author: cleanmatic
  version: "1.2.0"
---

# cleanmatic:product-spec-critique

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

| | `--validate` (product-spec) | `/product-spec-critique` (this skill) |
|---|---|---|
| Output | pass/fail findings, reproducible | opinionated critique, non-deterministic |
| Voice | warm, PO-facing, neutral | sarcastic, brutal-but-grounded, 9 levels |
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
| `--fresh` / `--force` | Bypass ALL reuse: force a full fresh run (`provenance.reuse = none`), re-running every lens even when nothing changed. Use after a fix you want re-judged from scratch. |
| `--refresh-web` | Force the market lens to re-fetch URLs (ignore the 14-day web-cache) and re-store. `--no-web` still wins (no fetch at all). |
| `--no-inherit` | Disable the parent→child **inherited_context** (the parent's prior blockers surfaced as the child's risk). Beats `--inherit deep` (off wins over depth). Default ON. |
| `--no-rollup` | Disable the child→parent **descendant_rollup** (critiqued children's verdicts aggregated onto the parent). Default ON. |
| `--inherit nearest\|deep` | Inherit depth (implies inherit ON): `nearest` (default) = nearest critiqued ancestor per branch + the latest `scope=all` critique; `deep` = every critiqued ancestor in the chain. |
| `--level 1..9` | Voice intensity. Default = the `critique_level` preference (itself `5`, no-mercy, if unset; the last level before a mandated roast, so a flagless run is level 5 + the standing-consent reminder); the flag overrides it. Aliases (1-6 only): `--warm`(1) `--gentle`(2) `--blunt`(3) `--savage`(4) `--no-mercy`(5) `--roast`(6). **Levels 7-9 have NO aliases** — use `--level 7/8/9`. A PO who wants a standing harsh voice sets `critique_level` once. Levels 1 to 4 forbid personal attack (artifact only). Level 5 (`--no-mercy`) lifts the redline (personal barbs allowed) and is the **default baseline**, so it is **ungated** (no warning, no reminder). **Levels 6 to 9 carry a danger gate** (warning + AskUserQuestion when ad-hoc; standing-preference reminder for 6-8): 6 (`--roast`) ENFORCES a personal roast (lazy/careless author); 7 attacks competence in the confrontational `ông/tôi` register; 8 attacks character in the street `mày/tao` register; **9 adds work-targeted profanity (`đm/vl`) and removes every internal restraint, so it RE-CONFIRMS via AskUserQuestion on EVERY run regardless of source and downgrades to 8 on decline.** Register at 7-9 reads `critique_address_gender` / `critique_dialect` / `critique_profanity` from preferences. **Universal-harm floor (all levels, even 9, even with consent):** the TARGET decides, profanity at the WORK is fine, but never real violence threats, protected-characteristic slurs, self-harm, sexual, or family-target profanity (`đụ má`-style). Every level keeps evidence + a fix per line. See `references/voice-and-tone.md` for the IN/OUT floor table. |

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
    D --> E[critique-consolidator opus: dedup · severity · top-3 · repeat-offense · DEC-worthy · voice + humanizer Gate 1]
    E --> E2[critique-humanizer sonnet: Gate 2 - strip AI/translation tells, keep the bite + findings]
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

`critique_scan.py --root <proj> --scope <id|all> --lang <vi|en> [--level N] [--fresh] [--no-inherit] [--no-rollup]
[--inherit nearest|deep]` emits ONE JSON bundle. Top-level keys:
`bundle_version (=2), scope, lang, target_ids, ancestry{vision,brd_goals[],prd,epic}, digest[], source_files{},
structural_findings[], cached_verdicts[], competitors[], prior_reports[], drift_threshold, provenance{},
inherited_context[], descendant_rollup{}, parse_errors[]`.

- `provenance` = `{reuse: none|full|consolidate_only|relens, ...}` — the lifecycle reuse verdict. `full` →
  report already current; `consolidate_only` → reuse the lens-cache array, re-render at the new level (carries
  `lens_findings_hash`); `relens` → some node changed (`changed_ids`); `none` → fresh run. ECONOMIC gate, not a safety
  gate; `--fresh` forces `none`. The orchestrator branches on it (see the provenance-branch step in `workflow-critique.md`).
- `inherited_context` (parent→child) + `descendant_rollup` (child→parent) — cross-critique context, consumed by
  the **consolidator ONLY** (lenses stay blind, anti-anchoring). Inherited items render in a separate section and are
  NEVER added to the severity tally. Both empty on run 1 / when `--no-inherit` / `--no-rollup`.

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

- `scripts/critique_scan.py`, the CLI entrypoint + back-compat facade. Deterministic, reuse-first (no LLM): assembles
  the bundle, writes/reads the `last_critique.json` snapshot (`--snapshot`), counts drift (`--drift [--vs-validated]`),
  and emits the provenance/inherit/rollup keys. The implementation is split into focused modules:
  `critique_common` (graph helpers), `critique_bundle` + `critique_signals` (bundle assembly), `critique_provenance`
  (frontmatter + reuse decision), `critique_drift` (snapshot/drift), `critique_inherit` (inherit + rollup),
  `critique_cache` + `critique_cache_io` + `critique_blob_cache` (the 5 cache/state stores). Reuses product-spec's
  `spec_graph`/`assemble_digest`/`judgment_cache`/`preferences`/`fs_guard` via a cross-dir import; runs
  `check_traceability`/`check_consistency` as a subprocess. Always exits 0.
- **Cache/state stores** (`docs/product/.memory/`, committed): `critique-findings-index.json` (lossy evidence-ID query
  cache → inherit/repeat-offense), `critique-lens-cache/<hash>.json` (FULL lens arrays → `consolidate_only`),
  `critique-state.json` (per-scope provenance fast-path marker), `web-cache/<url-hash>.json` (market URL + 14-day TTL),
  `humanized-cache.json` (reuse humanized output when consolidated text is unchanged).
- Reused (read-only) from `product-spec/scripts/`: `decision_register.py` (the DEC bridge), `preferences.py` (the
  `critique_drift_threshold` default 3; `critique_level` 1..9 default 5; the level-7-9 register knobs
  `critique_address_gender` m/f, `critique_dialect` bac/trung/nam, `critique_profanity` off/abbrev/strong (default
  strong, since level 9 re-confirms every run); `critique_detail_level` concise/standard/verbose sizing the report;
  and the cross-critique knobs `critique_inherit` on/off, `critique_rollup` on/off, `critique_inherit_depth`
  nearest/deep, all default on / nearest — registered in product-spec's `preferences.py`).

> ⚙️ **Venv bootstrap (first run):** before invoking any script, check the shared interpreter exists
> (`./.claude/skills/.venv/bin/python3` on POSIX, `.claude\skills\.venv\Scripts\python.exe` on Windows). If it is
> **missing**, do NOT silently fail or fall back to system Python, ask the user via **AskUserQuestion** to confirm
> running an installer (`product-spec/install.sh` or `product-spec-critique/install.sh`, both idempotent, both reuse the
> SAME shared venv). Run only on approval, then retry. product-spec-critique adds no new runtime dependency.

> 🪝 **Opt-in drift nudge hook:** `product-spec-critique/install.sh --critique-hook` registers the advisory Stop hook
> `product_spec_critique_nudge.py` into `.claude/settings.local.json` (gitignored; `--critique-hook-shared` → committed
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
