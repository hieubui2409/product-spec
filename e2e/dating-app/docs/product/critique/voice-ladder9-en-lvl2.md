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
level: 2
---
# Critique: all · level 2 · lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 8 · minor 3

## Top 3: fix now

1. **[blocker][product] BRD-G2:57** — The vision sells sustained 7-day conversations and explicitly rejects match count as vanity (VISION:51-52), yet the only persona-engagement goal, BRD-G2, measures `weekly-match-rate` (>=1 match/week for 20% of actives), a raw match-count metric. PRD-MATCH optimizes straight to it (PRD-MATCH:15,72). The headline goal counts the thing the product says it is not about. **The problem:** teams build to the metric they are graded on. The product will end up optimizing swipe-to-match volume and recreate the "millions of dead matches" the vision was founded to escape, while the 7-day-conversation north-star sits unowned by any BRD goal. **A fix:** add or replace a BRD goal that measures the north-star directly (e.g., % of matches that reach a 7+ day conversation), re-point PRD-MATCH and PRD-CHAT success metrics to it, and keep weekly-match-rate only as a leading funnel indicator. *(DEC-worthy: this changes the binding persona-success metric.)*

2. **[blocker][tech] PRD-CHAT-E1-S3:18** — Both acceptance criteria describe sensations only. Line 18 says the experience "must be smooth," line 19 says the UI "displays quickly and does not lag." Neither carries a number any test can assert against. **The problem:** the story cannot be accepted, rejected, or estimated. It ships with the AC permanently interpreted by whoever happens to demo it, and no engineer can size effort toward an undefined quality bar. **A fix:** rewrite both as measurable Given-When-Then, e.g. "when 100 consecutive frames render, fewer than 5% drop below 60 fps on a mid-range Android (Redmi Note)" and "the first 50 messages reach time-to-interactive <= 1.5s at p95 on 4G." Add the test device and network profile to the story frontmatter.

3. **[blocker][market] BRD:22** — BRD-G3 targets premium revenue sufficient for Year-2 break-even, but neither BRD-G3 nor PRD-PREMIUM defines a price tier, conversion-rate target, or ARPU floor. The BRD-G3 body is empty. Vietnam dating-services ARPU is about USD 8.15/user/year (Statista 2025). At 100k MAU and a 2-5% freemium conversion, that is roughly USD 16k-40k/year, likely short of running real-time messaging (PRD-CHAT) plus a human safety-review queue (PRD-SAFETY). **The problem:** without a pricing model grounded in the Vietnam market, BRD-G3 is an aspiration with no path, and the investment case for PRD-PREMIUM cannot be checked. **A fix:** add a monthly VND price range anchored to the local market (Tinder Gold ~149k-199k VND/mo), a target conversion of 3-6% of MAU, and a derived annual-revenue figure compared against projected Year-2 operating cost. If the math does not close, revisit the `horizon:later` tag or specify a second revenue stream. Source: https://www.statista.com/outlook/emo/dating-services/vietnam *(DEC-worthy.)*

## By lens

### Product

- **[major][product+tech] PRD-MATCH-E1-S2:38 (also :21)** — PRD-MATCH's scope explicitly defers AI recommendations and "why recommended" to PRD-AIREC next cycle (PRD-MATCH:64; PRD-AIREC:77), yet this must / core-value story requires a recommender that beats random by >=20% via A/B at p<0.05 (lines 38, 21) plus a "why recommended this person?" explanation (line 22), the exact capability the spec said it would not build yet. Tech adds that an A/B p<0.05 outcome needs weeks to months of live traffic, so the AC is sprint-unacceptable, not Independent, not Estimable. **The problem:** a core must story silently carries a could/later capability the spec deferred, and ties its done-ness to traffic volume and calendar time. The team either over-builds an ML recommender that cannot survive cold-start, or quietly drops the AC. **A fix:** strip the A/B-lift criterion and the "why recommended" AC from S2. Keep S2 to deterministic hard-filter quality (age, distance, intent, active-profile freshness). Move model ranking and explanation to PRD-AIREC. If a pre-launch proxy is wanted, use precision@10 vs. the distance-only baseline on a labeled staging set, and run the holdout experiment as a data-team task, not a story AC.
- **[major][product] PRD-EVENTS-E1-S3:18** — This story fully specs organizing and selling tickets to nationwide concerts: line-ups, multi-tier ticketing, QR check-in, genre filters. None of the three personas is hiring a dating app to buy concert tickets, and the PRD itself labels it gold-plating (PRD-EVENTS-E1-S3:43). **The problem:** a fully-authored, AC-complete story reads as a real build candidate. It is also an entire separate business (artist ops, venue security, ticket fraud) with no line to the 7-day-conversation north-star. **A fix:** delete the story, or demote it to a one-line parking-lot idea. Do not carry an out-of-scope, persona-less feature as a drafted AC-complete artifact.
- **[major][product] PRD-PREMIUM-E1-S2:34** — A paid "boost" prioritizes a profile for 30 minutes of extra visibility. The value sold is quantity of exposure, the volume game the vision positions against. PRD-PREMIUM's own risk register flags that paid features can erode the free experience, yet ships boost as a should. **The problem:** boost monetizes the swipe-volume dynamic the product claims to reject. It rewards paying users with raw reach rather than sustained conversation, lifting short-term ARPU while pulling directly away from the one differentiator. **A fix:** reframe the premium gain around the core value (e.g., surface-to-verified-serious-users, not raw reach), or explicitly record a PO decision accepting the tension. Do not ship a reach-for-pay mechanic as an unexamined should. *(DEC-worthy if the PO keeps boost as-is.)*
- **[minor][product] PRD-AIREC-E1-S1:30** — A "so that I create more matches per week" story for an AI ranking layer the PRD itself calls a me-too feature behind Tinder and Bumble (PRD-AIREC:41-45), whose gates need >=20 swipes of interaction data per user, data with no proven path until the core loop works. **The problem:** effort goes to a delighter the spec admits will be worse than incumbents on day one, with a data precondition that may never materialize at scale. **A fix:** keep it could/later (already done) but add a go/no-go gate. Do not start PRD-AIREC until PRD-CHAT shows real sustained 7-day conversations to train on, and re-anchor the "so that" to sustained connection, not match count.

### Tech

- **[blocker][tech] PRD-CHAT-E1-S4:18** — Two ACs are absolute guarantees with no mechanism. Line 18 asserts conversations must be "absolutely safe," line 19 that the system "completely protects" users from bad behavior. No threat, detection, response, or SLA is named. The story is marked should / size:M while demanding an unbounded safety contract. **The problem:** it cannot be tested, sized, or accepted. Any implementation can trivially claim compliance, and post-launch it becomes a release blocker because the AC was always vacuously true. **A fix:** split into discrete testable stories, one mechanism per dimension, e.g. (a) E2E encryption verifiable via server-side log inspection, (b) block enforcement "when B messages a user who blocked them, the server rejects with 403 and stores nothing." Retire the current story or point it at the split set.
- **[major][tech] PRD-SAFETY-E1-S1:18** — Face-verification mandates liveness + face-match at >=90% confidence within 60s (lines 18, 20), but no `depends_on` for a face-comparison or liveness service exists in the story, parent epic, or PRD-SAFETY frontmatter. PRD-SAFETY:71 defers only the government-API path. **The problem:** the story silently assumes a face-matching pipeline exists. The team discovers mid-sprint that vendor selection, procurement, and integration are required, or stubs it and ships unverified. The 90% threshold cannot be validated without a labeled test set named nowhere. **A fix:** add `depends_on: [FACE-MATCH-SERVICE]` to the story and PRD frontmatter, add a vendor-selection spike with an integration contract and SLA, and add an NFR AC documenting precision/recall at the 90% threshold against a labeled face-pair set accepted by the PO.
- **[minor][tech] PRD-EVENTS-E1-S2:18** — Seat reservation specs decrement-by-1 on booking (line 18) and increment-by-1 on cancel (line 21), but there is no concurrent-booking AC. Two users hitting the last seat can both read a positive count and both decrement, causing oversell. **The problem:** without a concurrency AC the implementation defaults to a naive unlocked decrement, and oversell only surfaces in load testing or at a live event where the fix needs a schema change or advisory lock. **A fix:** add "given two users simultaneously book the last seat, exactly one is confirmed, the other gets seat-unavailable, final count is 0, no negative capacity," and note the implementation must use an atomic decrement or row-level lock (the choice stays with the team).

### Market

- **[major][market] BRD:42** — The BRD rates COMP-FIKA threat: low, but Fika already runs mandatory manual identity verification (~40% rejection rate), a 16-personality matching layer, values dealbreakers, and IRL events in Vietnam as core free-tier features. It is absent from PRD-SAFETY's competitive_parity table entirely. Fika's stated positioning, authentic connection over match count, is also this spec's primary differentiator. **The problem:** if Fika is underweighted, the safety-first verification moat and the "authentic connection" positioning are more contested than the BRD admits. A later entrant with similar positioning but without Fika's verification head-start faces a harder acquisition story, especially for P-URBAN women, who are Fika's core audience. **A fix:** re-rate COMP-FIKA to med/high for PRD-SAFETY and positioning, add it to the competitive_parity table with an honest verification assessment, and foreground what Ghep Doi Viet does that Fika does not (national scope for P-PROVINCE and P-RETURNEE) in the BRD market context. Source: https://vietcetera.com/en/fika-asias-first-female-focused-ai-social-and-dating-app-raises-16m-in-seed-funding *(DEC-worthy: contradicts an approved competitive rating.)*
- **[major][market] BRD:56** — BRD-G1 targets 100k MAU in Year 1 on a swipe mechanic functionally identical to Tinder/Bumble, without addressing JTBD-competition for P-PROVINCE (thin local pools). The real alternative for that persona is Facebook groups, Zalo, or in-person introduction, not Tinder. The spec names the thin-pool risk but never says why a P-PROVINCE user stays active long enough for a first match when the swipe stack is near-empty at launch. **The problem:** with no credible cold-start strategy, the 100k MAU goal leans implicitly on P-URBAN density in Hanoi/HCM, where Tinder already ranks top on Google Play Vietnam. If P-PROVINCE fails to activate, the national positioning collapses into a Hanoi/HCM-only app with no moat, and the 7-day north-star is unreachable if users churn before a first match. **A fix:** add a JTBD-competition section to the BRD or PRD-MATCH naming the do-nothing and Zalo/Facebook alternatives for P-PROVINCE, specify a cold-start tactic (geographic seeding, invite incentives, or a minimum-pool threshold that surfaces an interest-signal/waiting-list flow instead of an empty stack), and tie BRD-G1's 100k to per-persona acquisition assumptions so the figure is falsifiable. Source: https://www.similarweb.com/top-apps/google/vietnam/dating/
- **[minor][market] PRD-EVENTS:44** — PRD-EVENTS is correctly scoped out, but it frames offline events purely as internal gold-plating without noting that COMP-FIKA (rated threat: low) runs IRL events as core positioning. Fika's App Store title is "Fika: Matchmaker & IRL Events." **The problem:** dismissing events as gold-plating with no nod to a competitor using them as a retention and acquisition hook leaves a strategic blind spot and no re-evaluation trigger if IRL events prove a real retention mechanism in Vietnam. **A fix:** add a competitive note to the PRD-EVENTS risk section, keep scope:out for now but add a trigger: if Fika's events show measurable retention lift in public signals within 12 months, escalate the events horizon later to next and reconsider COMP-FIKA's threat rating. Source: https://apps.apple.com/us/app/fika-matchmaker-irl-events/id1528449006

### Craft

- **[major][craft] PRD-CHAT:70** — The NFR says "Do tre gui tin nhan thap" (low message delay) with no number. "Thap" is an unmeasurable comparative. **The problem:** the team cannot verify "low" objectively (is 500ms low? 1s? 2s?), so acceptance turns subjective and PO/dev expectations drift apart. **A fix:** set a concrete SLA, e.g. "toi da duoi 2 giay tren ket noi 3G tieu chuan Viet Nam, goi ~50KB," or a percentile target like p95 < 1.5s.
- **[major][craft] PRD-AIREC:37-38,39,50** — The PRD leans on "phu hop hon" (more suitable) and "thong minh hon" (smarter) with no metric (lines 37, 39). **The problem:** the team cannot pin "more fitting" or "smarter" into an AC, so the feature is unmeasurable and success becomes opinion. **A fix:** rewrite with an explicit metric, e.g. "ho so co kha nang cao dan toi match chuyen thanh nhan tin duy tri (match to 7-day-conversation >= 15%)" and "thu tu goi y toi uu theo ti le match-to-sustained-chat, khong theo so match tho."
- **[major][craft] PRD-PREMIUM:50-51,85** — Line 85 requires the free tier be "du rong" (sufficiently broad) to keep the core usable unpaid, a vague comparative (10 likes/day? 20? how long?). **The problem:** with no floor the team guesses. A tight limit churns users before they feel core value (a BRD anti-goal); a loose one fails to push conversion. **A fix:** specify the floor, e.g. "toi thieu 20 luot thich/ngay, kham pha khong gioi han, ghep doi + nhan tin mien phi khi da match, 48 gio thu premium cho nguoi moi," and measure "du rong" by a retention/conversion target.
- **[major][craft] PRD-SAFETY-E1-S1:20,36** — The ACs use the English term "liveness" (lines 20, 36) in a Vietnamese spec with no translation or definition. **The problem:** a reader unfamiliar with biometrics may read "liveness" as "being live/online." The spec is bilingual by accident, forcing readers to guess. **A fix:** define once in parent PRD-SAFETY ("Liveness = xac minh nguoi song, phat hien video/anh gia qua nhan dang dong tac selfie"), then use the Vietnamese term, or pair "liveness (xac minh nguoi song)" on first mention per artifact.
- **[major][craft] PRD-CHAT:33,54** — "realtime" appears in Latin script (line 33) and as "theo thoi gian thuc" (line 54) within the same artifact, with no consistent choice. **The problem:** terminology drift across languages adds friction for localization QA and cross-language readers, and makes the spec read as hastily stitched rather than deliberately bilingual. **A fix:** pick one: either "theo thoi gian thuc" throughout, or a bilingual convention ("theo thoi gian thuc (realtime)" on first mention, then Vietnamese only), and record the choice in a glossary at the top of VISION or PRODUCT.

## Repeat offenders

None. No prior critique reports for this scope.

## Worth recording as a decision (DEC-worthy)

- **BRD-G2:57** — replacing or re-pointing the binding persona-success metric (match-rate to sustained-conversation) is a positioning ruling the PO should record.
- **BRD:22** — committing a premium pricing model and conversion target for Year-2 break-even is a binding business decision.
- **BRD:42** — re-rating COMP-FIKA above threat:low touches the competitive assessment. If that rating is on an approved artifact, surface Keep / Change+re-approve / Hybrid rather than flipping it.
- **PRD-PREMIUM-E1-S2:34** — if the PO chooses to keep paid "boost" despite the north-star tension, record the accepted trade-off.
