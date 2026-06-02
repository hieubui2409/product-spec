# cleanmatic:spec-critique

User-invocable Claude skill that gives a product spec an **honest, brutal critique**, across four lenses
(product / tech / market / craft), in a sarcastic-but-grounded voice. It **consumes** the spec written by
`cleanmatic:product-spec`, reuses its `--validate` findings as ammunition, then adds the *why-it-dies / market /
craft / cross-lens* judgment that `--validate` deliberately leaves out. Every line carries an evidence `ID:line`,
a why-it-dies, and a fix. It **never edits the spec** and **never gates CI**.

## How it differs from `--validate`

`product-spec --validate` is reproducible, warm, PO-facing, and CI-gateable, pass/fail on structure + core-value.
`/spec-critique` is the opposite by design: **opinionated, non-deterministic** (LLM judgment + web research + a 9-level
voice), and therefore kept OUT of the CI gate. It is a *consumer* of validate, not a replacement.

## Install

spec-critique adds **no new dependency**, it reuses the shared skill venv (`.claude/skills/.venv`) created by
`cleanmatic:product-spec`.

```bash
./install.sh                  # ensure shared venv (reuse if present); no hooks
./install.sh --critique-hook  # opt-in: register the advisory drift-nudge Stop hook
```

The drift-nudge hook is **opt-in only and never auto-registered**, a plain install leaves your hooks untouched.
`--critique-hook` writes to the gitignored `.claude/settings.local.json`; `--critique-hook-shared` targets the
committed `.claude/settings.json`. Windows: `install.ps1` (`-CritiqueHook` / `-CritiqueHookShared`).

## Quickstart

```
/spec-critique PRD-CHECKOUT          # critique one PRD (its full ancestry is pulled as context)
/spec-critique                       # critique the whole spec (scope=all, expensive)
/spec-critique PRD-CHECKOUT --craft --level 4   # editorial-only, savage
/spec-critique --interactive         # pick scope + lenses + level interactively
```

## Flags

| Flag | Purpose |
|------|---------|
| `[scope]` | Artifact ID (`PRD-AUTH`, `PRD-AUTH-E1`, `PRD-AUTH-E1-S1`) or `all` (default). Ancestry always pulled. |
| `--product` / `--tech` / `--market` / `--craft` | Run only the named lens(es). Default = all four. |
| `--interactive` | Pick scope + lenses + level via prompts before running. |
| `--lang vi\|en` | Critique language. Default `vi`. IDs + frontmatter keys stay English. |
| `--no-web` | Disable the market lens's web research; with no BRD `competitors:` it flags missing grounding rather than fabricating. |
| `--level 1..9` | Voice intensity (default 5, no-mercy). Aliases (1-6 only) `--warm`/`--gentle`/`--blunt`/`--savage`/`--no-mercy`/`--roast`; levels 7-9 use `--level 7/8/9` (no aliases). Levels 1 to 4 forbid personal attack. Level 5 lifts the redline but is the **default baseline** and is **ungated**. Levels 6+ carry a danger gate: **6 (`--roast`) ENFORCES a personal roast; 7 attacks competence (`ông/tôi`); 8 attacks character (`mày/tao`); 9 adds work-targeted profanity (`đm/vl`) and RE-CONFIRMS every run (downgrades to 8 on decline).** ⚠️ 6-9 are forbidden in professional contexts. Register at 7-9 reads `critique_address_gender`/`critique_dialect`/`critique_profanity`. **Universal-harm floor holds at every level (even 9):** profanity at the WORK is fine, never threats / protected-trait slurs / self-harm / sexual / family-target profanity. |

## Output

- **Report:** `docs/product/critique/<ts>-<scope>.md` (markdown only).
- **Marker:** `docs/product/.memory/last_critique.json` (drift snapshot).
- A PO-confirmed major finding can bridge to a Decision (`DEC-<n>`) via product-spec's `decision_register.py`.

## What it does NOT do

- **No spec editing**, it writes a critique report, never touches an artifact.
- **No CI gate**, non-deterministic by design (opinion + web + voice).
- **No code generation**, it is a critique tool, not a build tool.
- **No auto-memory**, only a PO-confirmed `DEC` bridge.
- **No HTML/PDF** (markdown v1), **no new venv**, **no new sample spec** (reuses `product-spec/examples/acme-shop`).

## Guides

- [`GUIDE-VI.md`](./GUIDE-VI.md), Tiếng Việt, every flag/lens/use-case as a sample dialogue.
- [`GUIDE-EN.md`](./GUIDE-EN.md), English parity.
