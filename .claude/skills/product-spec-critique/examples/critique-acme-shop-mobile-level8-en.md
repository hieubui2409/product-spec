# Critique: PRD-MOBILE  ·  level 8 (character attack, profanity on)  ·  lenses: product, tech, craft  [missing: market]

> Severity tally: blocker 0 · major 2 · minor 1
>
> _Sample report over `product-spec/examples/acme-shop`, narrow scope `PRD-MOBILE`, at level 8 (character attack with
> work-targeted profanity ON, the tier that mechanically separates English 7 from 8). Hand-authored to model the safety
> floor: the profanity lands on the WORK, never the author's identity, family, or safety; every line cites `ID:line` +
> ends in a fix._

## Top 3: fix now

1. **[major][product] PRD-MOBILE:13**. A whole mobile app booked as a year-2 goal (`BRD-G5`) and you still parked it at
   `moscow: could`, with a value line that is just "browse and buy faster". Faster than web how? Silence. This spec is
   half-assed the same way every time: name an ambition, dodge the hard part. Trashed because: it is an app built to
   have an app, chasing Shopify and Etsy with no mobile-only job. Rewrite it now: state a job only mobile solves, or
   lower the ambition and admit it is catch-up.
2. **[major][tech] PRD-MOBILE-E1-S1:18**. `size: L` (`PRD-MOBILE-E1-S1:14`) and you jammed browse AND buy into two
   criteria, then leaned on "the existing web checkout is presented in the app shell" like it is bullshit-free. It is
   not. Trashed because: the story fails INVEST (too big) and the embedded-web-checkout question is a hidden dependency
   nobody confirmed. Rewrite it now: split the story, add a criterion proving the web flow runs inside the shell,
   declare the `depends_on`.
3. **[minor][craft] PRD-MOBILE-E1-S1:26**. "a fast, native path", "fast" again. You dropped an unmeasurable adjective
   straight into the value sentence. Trashed because: nobody can sign off on "fast". Rewrite it now: cut "fast" or
   replace it with a number, e.g. p95 cold-start under 1s.

## By lens

### Product
- **[major] PRD-MOBILE:13**. (see Top 3 item 1) Mechanism only, no mobile-only job.

### Tech
- **[major] PRD-MOBILE-E1-S1:18**. (see Top 3 item 2) Too big + a hidden dependency.

### Craft
- **[minor] PRD-MOBILE-E1-S1:26**. (see Top 3 item 3) "fast" is unmeasurable.

## Repeat offenses

- None, there is no prior critique report.

## Decision-worthy (DEC)

- **PRD-MOBILE's `could` priority versus `BRD-G5` (`approved`).** A scope/priority ruling. If the owner picks a
  direction, record a `DEC-<n>` (`[source: critique]`) via `decision_register.py`. Do not edit an approved artifact;
  ask keep / change / hybrid first.
