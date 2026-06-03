---
body_hash:
  PRD-AIREC: c258d8fd
  PRD-AIREC-E1: a2c8a061
  PRD-AIREC-E1-S1: 917f7bc9
  PRD-CHAT: 1cfc4161
  PRD-CHAT-E1: eb20b520
  PRD-CHAT-E1-S1: 8943eb03
  PRD-CHAT-E1-S2: 8c751c9f
  PRD-CHAT-E1-S3: 0e54d9bf
  PRD-CHAT-E1-S4: 628c183c
  PRD-EVENTS: 1733e335
  PRD-EVENTS-E1: e3aabc84
  PRD-EVENTS-E1-S1: 40cb8605
  PRD-EVENTS-E1-S2: a8852e0b
  PRD-EVENTS-E1-S3: 3b04bb23
  PRD-MATCH: 6ef8ad25
  PRD-MATCH-E1: 982249bd
  PRD-MATCH-E1-S1: 0ebcb5e1
  PRD-MATCH-E1-S2: cfc87b23
  PRD-PREMIUM: 26b9a8eb
  PRD-PREMIUM-E1: 019f8b55
  PRD-PREMIUM-E1-S1: e5f44b06
  PRD-PREMIUM-E1-S2: 82cd5b3b
  PRD-SAFETY: 1b1dc2cb
  PRD-SAFETY-E1: afee85f3
  PRD-SAFETY-E1-S1: 1c73ea43
  PRD-SAFETY-E1-S2: 169b4b79
  PRODUCT: 12f8eb81
  VISION: 44634e30
bundle_version: 2
critique_scope: all
lang: en
lens_findings_hash: 22e9b7fd857a9d8e
level: 5
---
# Critique: all · level 5 · lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 13 · minor 3

## Top 3: fix now

1. **[blocker][product] BRD-G2:57.** The vision sells sustained 7-day conversation and openly calls match count a vanity metric (VISION:51-52), yet the only persona-engagement goal, BRD-G2, measures `weekly-match-rate`, and PRD-MATCH points its success straight at it (PRD-MATCH:15,72). You wrote down the metric one floor below the thing you claim to sell, and that is the floor the team will build to. Where it dies: teams build to the number they are graded on. Grade them on match count and they optimize swipe-to-match volume, reproduce the "millions of dead matches" the vision was founded to escape, and ship the competitor you set out to beat, while the 7-day north-star sits unowned by any goal. Fix it properly: add or replace a BRD goal that measures the north-star directly (e.g. % of matches that become a sustained 7+ day conversation), re-point PRD-MATCH / PRD-CHAT success to it, and keep weekly-match-rate as a leading funnel indicator only. _(DEC-worthy: this re-points the headline persona goal.)_

2. **[blocker][tech] PRD-CHAT-E1-S4:18.** Two acceptance criteria are absolute guarantees with no mechanism: line 18 demands conversations be "absolutely safe", line 19 demands the system "completely protect" users, and yet the story is a `should`, sized `M`, with no threat named, no detection named, no response named, no SLA named. A medium should-have with an unbounded safety contract is a blank check. Where it dies: the story cannot be tested, sized, or accepted. Any build trivially claims compliance because the system does *something* when bad behavior occurs, and the AC stays vacuously true right up until a real safety incident blocks release. Fix it properly: split into discrete testable stories, one mechanism each, e.g. "Given A blocks B, when B sends, then the server rejects with 403 and stores nothing", and an encryption story with server-side log verification. Retire the catch-all.

3. **[blocker][market] BRD:22.** BRD-G3 targets premium revenue enough for Year-2 break-even, but the goal body is empty: no pricing tier, no conversion target, no ARPU floor. At Vietnam dating-services ARPU ~USD 8.15/user/yr (Statista 2025), 100k MAU, and a 2-5% freemium conversion rate, you land at roughly USD 16k-40k/yr, which will not cover real-time messaging plus a human safety-review queue. A break-even goal with the math left blank is a wish with a deadline. Where it dies: with no pricing model grounded in Vietnam, the Year-2 break-even is unverifiable and the whole investment case for PRD-PREMIUM is unsupported. Fix it properly: add to BRD-G3/PRD-PREMIUM a monthly price range in VND (Tinder Gold ~149k-199k VND/mo), a 3-6% conversion target, and a derived annual-revenue estimate set against Year-2 operating cost. If the math does not close, revisit the `later` horizon on PRD-PREMIUM or specify a second revenue stream. Source: https://www.statista.com/outlook/emo/dating-services/vietnam _(DEC-worthy.)_

## By lens

### Product

- **[major] PRD-EVENTS-E1-S3:18.** A fully-authored, AC-complete story to organize and sell tickets to nationwide concerts (line-ups, multi-tier ticketing, QR check-in). None of the three personas is hiring a dating app to buy concert tickets, and the PRD itself labels this gold-plating and solution-first (PRD-EVENTS-E1-S3:43). The spec admits it is junk and ships it anyway. Where it dies: a fully-specified story reads as a real build candidate. It describes a separate business (artist ops, venue security, ticket fraud) with no line to the north-star, and chasing it splits the team off a core loop that is not yet proven. Fix it properly: delete the story, or demote it to a one-line parking-lot idea. Do not carry an out-of-scope, persona-less feature as a drafted, AC-complete artifact.

- **[major] PRD-MATCH-E1-S2:38.** PRD-MATCH scope explicitly excludes AI recommendations and "why recommended", deferring them to PRD-AIREC next cycle (PRD-MATCH:64; PRD-AIREC:77), but the core-value must story S2 demands a recommender that beats random by >=20% (A/B, p<0.05) plus a "why recommended this person?" line. That is exactly the deferred capability smuggled into a now/must story. Where it dies: the team either over-builds an ML recommender to clear an A/B gate that cannot pass on a cold-start user base, or quietly drops the AC. Both rot credibility and blow the now-cycle scope. Fix it properly: strip the lift A/B criterion and the "why recommended" AC from S2; keep S2 to deterministic hard-filter quality (age/distance/intent, profile freshness). Move model ranking and explanation to PRD-AIREC where they already live. _(DEC-worthy: contradicts the stated PRD-MATCH scope exclusion.)_

- **[major] PRD-PREMIUM-E1-S2:34.** A paid "boost" that buys 30 minutes of extra visibility. The value sold is raw exposure, which is precisely the volume game the vision positions against, and PRD-PREMIUM's own risk register warns paid features can erode the free experience, yet boost ships as a revenue should anyway. Where it dies: boost monetizes the same swipe-volume dynamic the brand claims to reject and rewards payers with reach instead of sustained conversation. It can lift ARPU short-term while pulling the product off its one differentiator. Fix it properly: either reframe the gain around the core value (surface-to-verified-serious-users, not raw reach) or record an explicit PO decision accepting the tension. Do not ship a reach-for-pay mechanic as an unexamined should. _(DEC-worthy.)_

- **[minor] PRD-AIREC-E1-S1:30.** A "so that I create more matches per week" story for an AI ranking layer the PRD itself calls a me-too that lands behind Tinder and Bumble (PRD-AIREC:41-45), gated on >=20 swipes of interaction data per user, data the product has no proven path to accumulate until the core loop works. The riskiest assumption is named but unowned. Where it dies: effort goes to a delighter that the spec admits is worse than incumbents on day one, on a data precondition that may never materialize, while the real value (reliable chat producing 7-day conversations) waits. Fix it properly: keep it could/later, but add a go/no-go gate. Do not start PRD-AIREC until PRD-CHAT shows real volume of sustained 7-day conversations to train on, and re-anchor the "so that" to sustained connection, not match count.

### Tech

- **[blocker] PRD-CHAT-E1-S3:18.** Both ACs are pure sensation: line 18 says the experience "must be smooth", line 19 says the UI "displays quickly and does not lag". No frame rate, no render time, no jank threshold, nothing binary to pass or fail. Where it dies: the test author has no threshold to assert against. The story ships with its AC permanently "interpreted" by whoever runs the demo, and it is unsizeable as written. Fix it properly: replace both with measurable Given-When-Then, e.g. "when 100 consecutive frames render, fewer than 5% drop below 60 fps on a mid-range Android (Redmi Note)" and "first 50 messages load with time-to-interactive <= 1.5s at p95 on 4G". Add the test device and network profile to the story frontmatter as a fixture.

- **[major] PRD-MATCH-E1-S2:21.** One AC requires a statistically significant A/B outcome: swipe-right-to-match on recommended profiles >=20% above a random control, p<0.05. That takes weeks to months of live traffic plus an analysis pipeline. It is not a sprint-deliverable acceptance condition. Where it dies: the story cannot be accepted at sprint review, its done-ness is coupled to traffic volume and calendar time, and it is neither Independent nor Estimable, so it lives in permanent limbo. Fix it properly: move the A/B outcome to a PRD success metric or a separate experiment epic with its own lifecycle. Replace the AC with a pre-launch proxy, e.g. "scored on a labeled staging batch, precision@10 >= X% above the distance-only baseline", and own the holdout experiment as a data-team task, not a story AC.

- **[major] PRD-SAFETY-E1-S1:18.** The face-verification story mandates liveness + face-match at >=90% confidence within 60s, but neither the story, the epic PRD-SAFETY-E1, nor PRD-SAFETY declares a `depends_on` for a face-comparison or liveness service. Line 71 defers only government-API verification. A must-have leaning on a pipeline nobody has named or procured. Where it dies: the team discovers mid-sprint that vendor selection, procurement, and integration are required (scope explodes), or stubs it and ships unverified. The 90% threshold also cannot be validated without a labeled test set that appears nowhere. Fix it properly: add `depends_on: [FACE-MATCH-SERVICE]` to the story and PRD frontmatter, add a vendor-selection spike defining the integration contract and SLA, and add an NFR AC documenting precision/recall at the 90% threshold on a labeled set. Until the spike lands and the vendor is named, this story cannot be estimated.

- **[minor] PRD-EVENTS-E1-S2:18.** The seat-reservation story specs decrement-on-book and increment-on-cancel but has no AC for the concurrent case: two users hitting "Giu cho" on the last seat can both read a positive count and both decrement, oversell. Where it dies: without a concurrency AC, the build defaults to a naive lockless decrement, oversell surfaces only in load testing or at a live event, and the post-launch fix needs a schema change or advisory lock, far more expensive. Fix it properly: add "Given two users simultaneously book the last seat, when both are processed, then exactly one is confirmed and the other gets seat-unavailable, final count is 0, no negative capacity", and note that the implementation must use an atomic decrement or row-level lock.

### Tech / product overlap

The recommendation defect at **PRD-MATCH-E1-S2** is flagged by both product (scope smuggling, line 38) and tech (unsizeable A/B AC, line 21). Same story, two distinct failures, both stand. See each entry above.

### Market

- **[major] BRD:42.** BRD rates COMP-FIKA threat: low, but Fika already runs mandatory manual ID verification (~40% rejection rate), a 16-type personality matching layer, values dealbreakers, and IRL events as core free-tier features. Fika is absent from PRD-SAFETY's competitive_parity table entirely. Fika's stated positioning, "authentic connection over match count", is also your headline differentiator. Where it dies: underweighting Fika means the safety-first verification moat and the "authentic connection" positioning are more contested than the BRD admits. A later entrant with the same positioning but without Fika's verification head-start faces a harder acquisition story for the same users, especially P-URBAN women who are Fika's core audience. Fix it properly: re-rate COMP-FIKA to med/high for PRD-SAFETY and the positioning, add it to the competitive_parity table with an honest behind/parity call on verification strictness, and foreground what you do that Fika does not: national scope for P-PROVINCE and P-RETURNEE. Source: https://vietcetera.com/en/fika-asias-first-female-focused-ai-social-and-dating-app-raises-16m-in-seed-funding

- **[major] BRD:56.** BRD-G1 targets 100k MAU Year 1 on a swipe mechanic (PRD-MATCH) functionally identical to Tinder/Bumble, with no JTBD-competition analysis for P-PROVINCE, whose real alternative is not Tinder but Facebook groups, Zalo, or natural introductions. The thin-pool risk is acknowledged but never answered: why would a province user stay active to a first match when the swipe stack is near-empty at launch? Where it dies: with no cold-start strategy for the provinces, 100k MAU implicitly rides on Hanoi/HCM density, where Tinder is already the top dating app on Google Play VN. If P-PROVINCE fails to activate, the national positioning collapses into a Hanoi/HCM-only Tinder clone with no moat, and the 7-day north-star is unreachable if users churn before a first match. Fix it properly: add a JTBD-competition section naming the do-nothing and Zalo/Facebook alternative for P-PROVINCE, specify a cold-start tactic (geographic seeding, invite incentives, a minimum-pool threshold below which you surface an interest-signal or waiting-list flow instead of an empty stack), and tie 100k MAU to a per-persona acquisition assumption so the figure is falsifiable. Source: https://www.similarweb.com/top-apps/google/vietnam/dating/

- **[minor] PRD-EVENTS:44.** PRD-EVENTS is correctly scoped out, but it frames offline events as purely internal gold-plating and misses that COMP-FIKA (rated threat: low) runs IRL events as a core positioning feature. The App Store listing is literally "Fika: Matchmaker & IRL Events" (2025-2026). Where it dies: dismissing events as gold-plating without noting that a competitor uses them as a retention and acquisition hook leaves a strategic blind spot with no re-evaluation trigger if IRL events prove to drive retention in Vietnam. Fix it properly: keep scope: out, but add a competitive note plus a re-evaluation trigger. If Fika's events show measurable retention lift in public signals within 12 months, escalate the events horizon from later to next, and reconsider COMP-FIKA's threat rating. Source: https://apps.apple.com/us/app/fika-matchmaker-irl-events/id1528449006

### Craft

- **[major] PRD-CHAT:70.** The NFR says "Do tre gui tin nhan thap" (low message delay) with no number. "Thap" is an unmeasurable comparative. Is 500ms low? 1s? 2s? Where it dies: the team cannot verify "low" objectively, so acceptance turns subjective and the PO/dev expectation gap surfaces at the worst time. Fix it properly: state a concrete SLA, e.g. "Do tre gui tin nhan toi da duoi 2 giay tren 3G tieu chuan VN" or a percentile target such as p95 < 1.5s.

- **[major] PRD-SAFETY-E1-S1:20,36.** The ACs drop the English word "liveness" into a Vietnamese spec with no translation or definition. A Vietnamese reader gets no equivalent and may read it as "being live/online". Where it dies: anyone unfamiliar with biometrics misreads the term; the spec is bilingual by accident, not design, forcing readers to guess. Fix it properly: define once in PRD-SAFETY, "Liveness = xac minh nguoi song (phat hien video/hinh anh gia) qua nhan dang dong tac selfie", then use the Vietnamese term throughout, or pair "liveness (xac minh nguoi song)" on first mention per artifact.

- **[major] PRD-AIREC:37-38,39,50.** The PRD leans on "phu hop hon" (more suitable) and "thong minh hon" (smarter) with no metric behind either. Where it dies: the team cannot put "more fitting" or "smarter" into acceptance criteria; the feature becomes unmeasurable and success collapses into opinion. Fix it properly: rewrite with explicit metrics, e.g. "ho so co kha nang cao dan toi match chuyen thanh nhan tin duy tri (match to 7-day-conversation >= 15%)" and "thu tu goi y toi uu hoa theo match-to-sustained-chat, khong theo so match tho".

- **[major] PRD-CHAT:33,54.** "realtime" is used inconsistently inside one artifact: once in Latin script, once as "theo thoi gian thuc", with no convention declared. Where it dies: terminology drift across the spec creates friction for translation and localization QA and makes the spec read hastily stitched rather than deliberately bilingual. Fix it properly: pick one. Either "theo thoi gian thuc" throughout PRD-CHAT and its children, or a bilingual convention ("theo thoi gian thuc (realtime)" on first mention, then Vietnamese), and record the choice in a glossary at the top of VISION or PRODUCT.

- **[major] PRD-PREMIUM:50-51,85.** The NFR (line 85) says the free tier "phai du rong" (sufficiently broad) with no floor. Broad how? 10 likes/day? 20? For how long? Where it dies: with no floor the team guesses. A tight limit churns users before they feel core value (a BRD anti-goal); a loose one fails to push conversion. The constraint is asserted but its enforcement is left to interpretation. Fix it properly: specify the floor, e.g. "toi thieu 20 luot thich/ngay, kham pha khong gioi han, ghep doi + nhan tin mien phi khi da match, nguoi dung moi nhan 48 gio thu premium", and tie "du rong" to a retention/conversion metric.

## Repeat offenders

None. No prior reports.

## Worth recording as a decision (DEC-worthy)

- **BRD-G2:57** — re-pointing the headline persona goal off `weekly-match-rate` onto a sustained-conversation north-star changes what the whole build optimizes for. PO ruling worth recording.
- **PRD-MATCH-E1-S2:38** — the must story contradicts the stated PRD-MATCH scope exclusion of AI recommendations. Stripping it (or accepting the contradiction) is a binding scope ruling, it touches an approved-scope boundary, so it runs through Keep / Change+re-approve / Hybrid, not a silent edit.
- **PRD-PREMIUM-E1-S2:34** — shipping a reach-for-pay boost against the stated quality-over-quantity positioning is a trade-off the PO should record either way.
- **BRD:22 / BRD-G3** — committing a pricing tier and conversion target (or deferring PRD-PREMIUM's horizon) is a revenue-model decision worth a DEC entry.
