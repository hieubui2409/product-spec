# Critique: PRD-MOBILE  ·  level 7 (cold contempt)  ·  lenses: product, tech, craft  [missing: market]

> Severity tally: blocker 0 · major 2 · minor 1
>
> _Sample report over `product-spec/examples/acme-shop`, narrow scope `PRD-MOBILE`, at level 7 (cold contemptuous
> register, competence attack, ZERO profanity, English has no pronoun ladder so 7 is the no-profanity tier). Hand-authored
> to model the output contract + the safety floor: every line cites `ID:line` + ends in a fix; the attack hits the work
> and the competence, never the person._

## Top 3: fix now

1. **[major][product] PRD-MOBILE:13**. A whole mobile app is set as a year-2 goal (`BRD-G5`) yet sits at `moscow: could`,
   and the value line is just "browse and buy faster". Faster than the web how? No answer. Blown apart because: this is
   building an app to have an app, chasing competitors with no mobile-only job to justify it. Whoever owns this does not
   yet think like a product person. Rewrite it properly: name a job only mobile solves (drop push notifications,
   buy-on-the-go), or lower the ambition and say plainly this is catch-up.
2. **[major][tech] PRD-MOBILE-E1-S1:18**. The story is `size: L` (`PRD-MOBILE-E1-S1:14`) yet crams browse AND buy into
   two criteria and leans on "the existing web checkout is presented in the app shell" as if that were free. Blown
   apart because: it fails INVEST (too big), and the embedded-web-checkout-in-a-native-shell question is a hidden dependency
   nobody has confirmed. Rewrite it properly: split into two stories, add a criterion that proves the web flow renders
   and completes inside the shell, or declare a `depends_on`.
3. **[minor][craft] PRD-MOBILE-E1-S1:26**. The value sentence "a fast, native path" carries "fast", an unmeasurable
   adjective, in the most important spot. Blown apart because: fast means something different to everyone, so there is
   nothing to test. Rewrite it properly: drop "fast" from the value line, or move it to a numbered NFR, e.g. p95 app
   cold-start under 1s.

## By lens

### Product
- **[major] PRD-MOBILE:13**. (see Top 3 item 1) No mobile-only job stated, only mechanism.

### Tech
- **[major] PRD-MOBILE-E1-S1:18**. (see Top 3 item 2) Fails INVEST + a hidden dependency.

### Craft
- **[minor] PRD-MOBILE-E1-S1:26**. (see Top 3 item 3) "fast" is unmeasurable in the value line.

## Repeat offenses

- None, there is no prior critique report.

## Decision-worthy (DEC)

- **PRD-MOBILE's `could` priority versus the year-2 goal `BRD-G5`.** A scope/priority ruling, and `BRD` is `approved`.
  If the owner picks a direction, record a `DEC-<n>` (rationale led by `[source: critique]`) via `decision_register.py`.
  Do not edit an approved artifact; ask keep / change / hybrid first.
