# Using `cleanmatic:product-spec-critique` (English)

A guide for **product owners**. Each use-case is a sample dialogue over the sample spec
`product-spec/examples/acme-shop`. The natural-language way (just say it) is preferred; the flag form is the equivalent.

## What it is, and how it differs from `--validate`

`--validate` (in `product-spec`) is a **structural** check: missing AC, orphans, core-value drift, pass/fail, neutral
warm voice, CI-gateable. `product-spec-critique` is the deliberate opposite: it **critiques**, opinionated, sarcastic, uses web
research, so it is **never** in the CI gate. It *consumes* validate's findings as ammo, then says what validate
**cannot**: why-it-dies, market, writing craft, cross-lens.

> ⚠️ **Personal-attack redline.** Levels 1 to 4 forbid attacking the author; only the artifact is fair game. Level 5
> (`--no-mercy`) lifts the redline, so personal barbs are allowed, and it is the **default baseline** voice. Level 6 (`--roast`) requires a direct roast of the
> author ("too lazy to add a number", "scribbled it and went to bed"). **Levels 7 to 9 escalate further:** level 7 is
> cold contempt + a competence attack with zero profanity; level 8 adds a character attack with profanity on
> (work-targeted); level 9 is sustained work-targeted profanity with no internal restraint. (Vietnamese rides the
> `ông/tôi` → `mày/tao` pronoun ladder; English has no ladder, so 7-9 escalate by profanity-presence.) Levels 6-9 are
> dangerous and have no place in any professional context. **Level 5 is the default baseline and is ungated** (no
> warning). Levels 6-8 warn + confirm when ad-hoc (a standing preference just prints a one-line reminder); **level 9
> re-confirms on EVERY run regardless of source and downgrades to 8 on decline.**
>
> 🚧 **Universal-harm floor (holds at EVERY level, even 9, even with consent).** The TARGET of a line decides, not its
> strength. The tool will swear at and tear into the WORK, the effort, the competence on this spec, profanity aimed at
> an empty AC included. It will NEVER threaten real violence, never use protected-characteristic slurs (gender, region,
> ethnicity, religion, age, disability, sexuality, appearance), never aim profanity at your family (`đụ má`-style),
> never produce self-harm or sexual content. A defanged minced oath like `đậu xanh` is allowed (it dodges the literal
> vulgarity); only the literal family-target form is out. Every line still keeps evidence (`ID:line`) and a fix.

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
> Flag form: `/product-spec-critique all` or `/product-spec-critique`.

### 2. Critique one branch (PRD / epic / story)

> **You:** "Pick apart the checkout PRD." → `/product-spec-critique PRD-CHECKOUT`. Even for a single story, the **full ancestry**
> (epic → PRD → goal → vision) is pulled as judgment context, a story only means something against the intent above it.

### 3. Pick lenses

> **You:** "Only the market angle." → `/product-spec-critique --market`. Four lens flags: `--product` `--tech` `--market`
> `--craft`. No flag = all four.

### 4. Interactive

> **You:** "Let me choose the scope and intensity first." → `/product-spec-critique --interactive` → asks 3 questions: scope,
> lenses, level.

### 5. Change the voice level

> **You:** "Go easy, I just wrote this." → `--level 1` (`--warm`).
> **You:** "Don't hold back." → `--level 5` (`--no-mercy`). This is the default baseline: it may go after you personally but runs straight away, no warning or confirm (the gate starts at level 6).
> **You:** "Roast me to my face, I can take it." → `--level 6` (`--roast`), ⚠️ this **insults the author directly**;
> the assistant shows a danger warning + asks for explicit confirmation first, and it is **never for shared reports or
> professional use**. It's a private "destroy-me" mode for the spec's own author.
> **You:** "Harsher, get contemptuous." → `--level 7` (cold contempt + competence attack, no profanity) or `--level 8`
> (character attack, profanity on). No aliases for 7-9, type `--level 7/8`.
> **You:** "Full profanity, no holds barred." → `--level 9` (sustained work-targeted profanity, no restraint). Level 9
> **re-confirms on every run** and downgrades to 8 if you decline. The universal-harm floor above holds at 9 regardless.

### Register config for levels 7-9 (gender, dialect, profanity)

The three harshest levels read knobs from `preferences.yaml`. These pick the ADDRESS form, not extra permission, the
safety floor is identical whatever you set:

| Pref | Values | Default | Applies at | Surface form |
|------|--------|---------|-----------|--------------|
| `critique_address_gender` | `m` / `f` | `m` | level 7 | `ông/tôi` (m) ↔ `bà/tôi` (f), Vietnamese only |
| `critique_dialect` | `bac` / `trung` / `nam` | `bac` | level ≥ 8 | `mày/tao` ↔ `mi/tau` ↔ southern, Vietnamese only |
| `critique_profanity` | `off` / `abbrev` / `strong` | `strong` | level 9 | none ↔ `đm/vl` ↔ `đm/vl/vãi`, work-targeted |

In English the gender/dialect knobs are no-ops (no pronoun ladder); `critique_profanity` still sets profanity strength
and is what separates English level 7 (off) from 8 (on). Default is `strong` because level 9 re-confirms every run
anyway, so when it fires it runs at full power.

### The two "detail" levels are independent (spec vs critique)

- `detail_level` (set in `cleanmatic:product-spec`) sizes the SPEC you write (`concise`/`standard`/`verbose`).
- `critique_detail_level` (for `product-spec-critique`) sizes the CRITIQUE report (`concise` = top-3 + one line per lens;
  `verbose` = full per-lens + longer why-it-dies).

Setting one never affects the other. "Verbose specs + concise critiques" is valid. Both default to `standard`.

### 6. Offline (`--no-web`)

> **You:** "Don't search the web, judge from the spec." → `/product-spec-critique --no-web`. With no BRD `competitors:` and
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

### 9. Re-runs: reuse & parent/child context

From the second critique of a scope onward, prior work is **reused** — token savings only, never weaker quality.

> **You:** "Critique `PRD-CHECKOUT` again, but harsher — level 7."
>
> *(Spec unchanged, only the level changed.)* The assistant does NOT re-run the four lenses — it **only re-renders the
> voice** at level 7 from the saved analysis (much cheaper). Natural phrasing like "make it harsher without re-analysing"
> works too; the flag equivalent is just bumping `--level`.

> **You:** "I edited that story — re-critique it from scratch to be safe."
>
> Because the body changed, it re-critiques that branch (re-lens). To force a fully fresh run even with no edit: `--fresh`.

> **You:** "Critique this story."  *(after the parent PRD was critiqued and had a blocker)*
>
> The story report adds an **"Inherited from parent"** section: the parent's blocker shows up as the child's risk
> (cited as `<parent-id>@<ts>`), and is **not added to the story's severity tally**. Hide it with `--no-inherit`.

> **You:** "Critique this epic."  *(after ≥2 of its child stories were critiqued)*
>
> The epic report carries a rollup line like "3/5 critiqued children carry blockers → delivery risk at this parent".
> Turn it off with `--no-rollup`.

> **You:** "Refresh the competitor research."
>
> The market lens reuses pages fetched within the last 14 days by default. Add `--refresh-web` to force a re-fetch.

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
levels; all nine (including level 2's dry edge, level 4's heavy sarcasm, and the level-7-8 escalation) live in
`references/voice-and-tone.md`.

- **L1 (`--warm`):** "'Fast login' has no number, add a threshold (e.g. p95 < 2s) so the build team can test it."
- **L3 (`--blunt`):** "'Fast login', fast how? QA can't test an adjective. Why it dies: an unmeasurable AC
  makes 'done' a matter of opinion. Fix: 'p95 < 2s on 4G'."
- **L5 (`--no-mercy`, default):** "'Fast login' is a wish, not a requirement, and you knew it was hollow when you typed it.
  Engineers will build by horoscope. Why it dies: 'done' is undefinable → endless rework. Fix now: 'p95 < 2s on 4G'."
- **L6 (`--roast`, ⚠️ insults the author, never professional):** "'Fast login'?? Too lazy to type one number, so you
  scribbled it and called it a day. Why it dies: 'fast' = a number only you know, and you don't write the code. Fix it
  if you've any pride left: 'p95 < 2s on 4G, measured by RUM', ten characters, how lazy do you have to be."
- **L7 (⚠️ cold contempt + competence, zero profanity):** "'Fast login', and not one number behind it. Let me be blunt:
  whoever owns this spec does not yet think like a product person. Blown apart because: undefined 'done' hands the build team
  a guessing game. Rewrite it properly: 'p95 < 2s on 4G, measured by RUM'."
- **L8 (⚠️ character attack + profanity on, work-targeted):** "'Fast' again. This whole spec is half-assed the same way
  every time. The AC is so empty there isn't one number to test, and it's bullshit to ship something this lazy and call
  it a requirement. Trashed because: nothing to measure means endless rework. Rewrite it now: 'p95 < 2s on 4G'."
- **L9 (⚠️⚠️ sustained profanity, re-confirms every run):** "'Fast login'? This AC is fucking empty. Too lazy to type
  one number and you still call it a spec, that's pathetic. Wrecked because: 'fast' is a number only you know, and
  you don't write the code. Rewrite it, and don't make me say it twice: 'p95 < 2s on 4G, measured by RUM'."

---

## Reading the report

- **Severity tally** (blocker / major / minor) at the top.
- **Top 3, fix now**: the three most threatening findings across lenses.
- **By lens**: each finding = `[severity][lens] <ID:line>` → critique → why-it-dies → fix.
- **Repeat offenses** + **Decision-worthy (DEC)**.

## Boundaries

- No spec editing (writes a report only). No CI gate. No code generation. Level 5 is the ungated default baseline;
  levels 6-8 require a danger warning + explicit confirm when ad-hoc (a standing preference prints a one-line reminder
  instead) and are never for professional use; **level 9 re-confirms on every run and downgrades to 8 on decline.** The universal-harm
  floor (no threats / protected-trait slurs / family-target profanity / self-harm / sexual content) holds at every level
  including 9, even with consent.
