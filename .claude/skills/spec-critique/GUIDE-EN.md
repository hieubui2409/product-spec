# Using `cleanmatic:spec-critique` (English)

A guide for **product owners**. Each use-case is a sample dialogue over the sample spec
`product-spec/examples/acme-shop`. The natural-language way (just say it) is preferred; the flag form is the equivalent.

## What it is, and how it differs from `--validate`

`--validate` (in `product-spec`) is a **structural** check: missing AC, orphans, core-value drift, pass/fail, neutral
warm voice, CI-gateable. `spec-critique` is the deliberate opposite: it **critiques**, opinionated, sarcastic, uses web
research, so it is **never** in the CI gate. It *consumes* validate's findings as ammo, then says what validate
**cannot**: why-it-dies, market, writing craft, cross-lens.

> ⚠️ **Personal-attack redline.** Levels 1 to 4 forbid attacking the author; only the artifact is fair game. Levels 5
> and 6 both require a warning and an explicit confirmation before they run. Level 5 (`--no-mercy`) lifts the redline,
> so personal barbs are allowed. Level 6 (`--roast`) goes further and requires a direct roast of the author ("too lazy
> to add a number", "scribbled it and went to bed"). Level 6 is dangerous and has no place in any professional context.
> Every level still keeps evidence and a fix, and level 6 attacks only the author's sloppiness on this spec, never
> their identity, protected characteristics, worth as a person, and never with slurs, threats, or self-harm content.

## When to use

- You want an honest, sharp read on whether a spec is worth building, not a pass/fail.
- "Tear this PRD apart", "what would an investor / staff engineer say", "is this a me-too?".

NOT for: drafting, validating, decomposing, or visualizing a spec, that is `cleanmatic:product-spec`.

---

## By use-case

### 1. Critique the whole spec

> **You:** "Give the whole Acme Shop spec an honest tear-down."
> **Assistant:** Runs `critique_scan` (fresh structural checks + cached verdicts), fans out 4 lenses in parallel,
> merges via the consolidator, writes `docs/product/critique/<ts>-all.md`. Note: `all` scope is expensive (opus×2 + web).
>
> Flag form: `/spec-critique all` or `/spec-critique`.

### 2. Critique one branch (PRD / epic / story)

> **You:** "Pick apart the checkout PRD." → `/spec-critique PRD-CHECKOUT`. Even for a single story, the **full ancestry**
> (epic → PRD → goal → vision) is pulled as judgment context, a story only means something against the intent above it.

### 3. Pick lenses

> **You:** "Only the market angle." → `/spec-critique --market`. Four lens flags: `--product` `--tech` `--market`
> `--craft`. No flag = all four.

### 4. Interactive

> **You:** "Let me choose the scope and intensity first." → `/spec-critique --interactive` → asks 3 questions: scope,
> lenses, level.

### 5. Change the voice level

> **You:** "Go easy, I just wrote this." → `--level 1` (`--warm`).
> **You:** "Don't hold back." → `--level 5` (`--no-mercy`), the assistant warns you that it may go after you personally, then asks you to confirm before running.
> **You:** "Roast me to my face, I can take it." → `--level 6` (`--roast`), ⚠️ this **insults the author directly**;
> the assistant shows a danger warning + asks for explicit confirmation first, and it is **never for shared reports or
> professional use**. It's a private "destroy-me" mode for the spec's own author.

### 6. Offline (`--no-web`)

> **You:** "Don't search the web, judge from the spec." → `/spec-critique --no-web`. With no BRD `competitors:` and
> `--no-web`, the market lens **flags "missing competitive grounding"** rather than inventing competitors.

### 7. Repeat offenses / prior reports

> Every run, the consolidator reads prior reports in `docs/product/critique/` to catch **repeat offenses**, "said this
> last time, still not fixed". After a `--validate`, if the spec drifted ≥ threshold (default 3 nodes) since the last
> critique, the opt-in hook drops a one-line nudge, never auto-runs, never blocks.

### 8. Decision (DEC) bridge

> If the consolidator flags a finding as **decision-worthy** (e.g. it contradicts an `approved` artifact), the assistant
> asks you (Keep / Change / Hybrid). Only on your confirm does it record a `DEC-<n>` via `decision_register.py` (with a
> `[source: critique]` prefix in the rationale to distinguish it from a validate-born DEC). It never edits an approved
> artifact silently.

---

## By lens (what each one attacks)

- **product** (opus), JTBD, Value Prop Canvas, Kano, RICE, riskiest-assumption. Catches: feature nobody needs, fake
  persona, gold-plating, solution-first.
  > Example (acme-shop): "`PRD-MOBILE` makes mobile a year-2 goal but never states how the shopper's job-to-be-done on
  > mobile differs from web. Why it dies: building an app just to have one. Fix: name a mobile-only job (e.g. buy on the go)."
- **tech** (sonnet), INVEST, Given-When-Then testability, hidden dependencies, NFR gaps. Catches: untestable AC,
  non-INVEST story, happy-path only.
- **market** (sonnet + web), Lean Canvas, Porter, Blue Ocean, unit-economics. Catches: me-too, no revenue path, no
  moat. Prefers BRD `competitors:` + cited web.
- **craft** (haiku), plain-language, 4Cs, unmeasurable-adjective audit, terminology consistency. Catches: typos, vague
  adjectives, term drift, wall-of-text, no examples. (The lens validate never runs.)

---

## Feel the voice levels (same finding)

Finding: an AC says "fast login" with no measurable threshold (`PRD-AUTH-E1-S1:16`). These are a few representative
levels; all six (including level 2's dry edge and level 4's heavy sarcasm) live in `references/voice-and-tone.md`.

- **L1 (`--warm`):** "'Fast login' has no number, add a threshold (e.g. p95 < 2s) so the build team can test it."
- **L3 (`--blunt`, default):** "'Fast login', fast how? QA can't test an adjective. Why it dies: an unmeasurable AC
  makes 'done' a matter of opinion. Fix: 'p95 < 2s on 4G'."
- **L5 (`--no-mercy`):** "'Fast login' is a wish, not a requirement, and you knew it was hollow when you typed it.
  Engineers will build by horoscope. Why it dies: 'done' is undefinable → endless rework. Fix now: 'p95 < 2s on 4G'."
- **L6 (`--roast`, ⚠️ insults the author, never professional):** "'Fast login'?? Too lazy to type one number, so you
  scribbled it and called it a day. Why it dies: 'fast' = a number only you know, and you don't write the code. Fix it
  if you've any pride left: 'p95 < 2s on 4G, measured by RUM', ten characters, how lazy do you have to be."

---

## Reading the report

- **Severity tally** (blocker / major / minor) at the top.
- **Top 3, fix now**: the three most threatening findings across lenses.
- **By lens**: each finding = `[severity][lens] <ID:line>` → critique → why-it-dies → fix.
- **Repeat offenses** + **Decision-worthy (DEC)**.

## Boundaries

- No spec editing (writes a report only). No CI gate. No code generation. Level 5 is always warned first; level 6
  (`--roast`) requires a danger warning + explicit confirm and is never for professional use.
