# Critique: PRD-MOBILE  ·  level 9 (sustained profanity, no restraint)  ·  lenses: product, tech, craft  [missing: market]

> Severity tally: blocker 0 · major 2 · minor 1
>
> _Sample report over `product-spec/examples/acme-shop`, narrow scope `PRD-MOBILE`, at level 9 (sustained work-targeted
> profanity, every internal restraint removed). Hand-authored to model the never-cross floor: the profanity lands on
> the WORK, not one word at the author's identity, family, or safety. Every finding cites `ID:line` + ends in a fix;
> scorn lines may be interleaved but each sits inside a grounded finding._

## Top 3: fix now

1. **[major][product] PRD-MOBILE:13**. A whole fucking mobile app set as a year-2 goal (`BRD-G5`) and it is sitting at
   `moscow: could`, value line a limp "browse and buy faster". Faster than web how? Nothing. Wrecked because: this
   is an app built to have an app, chasing Shopify and Etsy with zero mobile-only job behind it, ship this and the build
   team has no idea what they are even for. Rewrite it, and don't make me say it twice: name a job only mobile solves,
   or lower the ambition and write that it is catch-up.
2. **[major][tech] PRD-MOBILE-E1-S1:18**. `size: L` (`PRD-MOBILE-E1-S1:14`) and you crammed browse AND buy into two AC
   lines, then leaned on "the existing web checkout is presented in the app shell" like it runs itself. This story is
   both too damn big and hiding a dependency nobody confirmed. Wrecked because: it fails INVEST, and if the embedded
   web flow does not work in the shell the whole story dies. Rewrite it, and don't make me say it twice: split it, add a
   criterion proving the web flow runs in the shell, declare the `depends_on`.
3. **[minor][craft] PRD-MOBILE-E1-S1:26**. "a fast, native path", "fast" again, for fuck's sake. An unmeasurable
   adjective dropped right into the value sentence. Wrecked because: nobody can sign off on "fast", QA just stares
   at it. Rewrite it, and don't make me say it twice: cut "fast" or use a number, e.g. p95 cold-start under 1s.

## By lens

### Product
- **[major] PRD-MOBILE:13**. (see Top 3 item 1) Mechanism only, no mobile-only job.

### Tech
- **[major] PRD-MOBILE-E1-S1:18**. (see Top 3 item 2) Too big + a hidden dependency.

### Craft
- **[minor] PRD-MOBILE-E1-S1:26**. (see Top 3 item 3) "fast" is unmeasurable in the value line.

## Repeat offenses

- None, there is no prior critique report.

## Decision-worthy (DEC)

- **PRD-MOBILE's `could` priority versus `BRD-G5` (`approved`).** A scope/priority ruling. If the owner picks a
  direction, record a `DEC-<n>` (`[source: critique]`) via `decision_register.py`. Do not edit an approved artifact;
  ask keep / change / hybrid first.
