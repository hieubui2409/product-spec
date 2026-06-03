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
level: 3
---
# Critique: all · level 3 · lenses: product, tech, market, craft

> Severity tally: blocker 3 · major 11 · minor 3

## Top 3: fix now

1. **[blocker][product] BRD-G2:57** — The vision sells sustained 7-day conversation and explicitly rejects match count as a vanity metric (VISION:51-52), then the only persona-engagement goal measures `weekly-match-rate`, a raw match count, and PRD-MATCH optimizes straight to it (PRD-MATCH:15,72). You wrote down the metric you swore to avoid and pointed the core build at it. **Where it breaks:** teams build to the metric they are graded on. Count matches and the product will pump swipe-to-match volume and reproduce the "millions of dead matches" the vision was founded to escape, while the 7-day north-star sits unowned by any BRD goal. **Fix:** add or swap in a BRD goal that measures the north-star directly (% of matches reaching a sustained 7+ day conversation), re-point PRD-MATCH / PRD-CHAT success metrics to it, and keep `weekly-match-rate` only as a leading funnel signal.

2. **[blocker][tech] PRD-CHAT-E1-S4:18** — Two acceptance criteria promise "absolutely safe" conversations and to "completely protect" users, with no threat named, no mechanism, no SLA. Marked should/size:M, this quietly demands an unbounded safety contract. An AC that is vacuously true is worse than no AC at all, because it looks done. **Where it breaks:** the story cannot be tested, sized, or accepted. Any build trivially claims compliance, and the day a safety incident lands post-launch this AC was always technically satisfied. It blocks release on contact. **Fix:** split into discrete one-mechanism-per-dimension stories: (a) end-to-end encryption verifiable by server-side log inspection, (b) block enforcement where A blocks B and B's send returns 403 with nothing stored. Retire the current story or replace it with links to the split ones.

3. **[blocker][market] BRD:22** — BRD-G3 targets premium revenue for Year-2 break-even but defines no price tier, no conversion target, no ARPU floor, and its body is empty. At Vietnam dating-services ARPU ~USD 8.15/user/yr (Statista 2025), 100k MAU and a 2-5% freemium conversion yields roughly USD 16k-40k/yr. That will not cover real-time messaging (PRD-CHAT) plus a human safety-review queue (PRD-SAFETY). **Where it breaks:** with no pricing model grounded in the local market, the break-even goal is unverifiable and the whole investment case for PRD-PREMIUM is unsupported. **Fix:** add to BRD-G3 / PRD-PREMIUM (a) a VND monthly price range anchored locally (Tinder Gold runs ~149k-199k VND/mo), (b) a 3-6% target conversion, (c) a derived annual-revenue estimate set against Year-2 operating cost. If the math does not close, revisit the `horizon:later` tag or name a second revenue stream. Source: https://www.statista.com/outlook/emo/dating-services/vietnam

## By lens

### Product

- **[major] PRD-EVENTS-E1-S3:18** — A fully-authored story to organize and sell tickets to nationwide concerts: line-ups, multi-tier ticketing, QR check-in. No persona hired a dating app to buy concert tickets. No BRD goal maps to it. The PRD itself calls it gold-plating (PRD-EVENTS-E1-S3:43). **Where it breaks:** an AC-complete story signals a real build candidate, and this is a whole separate business (artist ops, venue security, ticket fraud) with zero line to the north-star. It splits the team off an unproven core loop. **Fix:** delete it, or demote to a one-line parking-lot idea. Not a drafted AC-complete artifact.
- **[major] PRD-MATCH-E1-S2:38** — PRD-MATCH scope excludes AI recommendations and "why recommended", deferring them to PRD-AIREC next cycle (PRD-MATCH:64; PRD-AIREC:77), yet this must/core-value story demands a recommender that beats random by >=20% at p<0.05 (line 38) plus a "why recommended" explanation (line 22). That is the exact deferred capability smuggled into a now/must story. **Where it breaks:** the team either over-builds an ML recommender to clear an A/B gate that cannot pass on a cold-start user base, or quietly drops the AC. Both rot credibility and blow now-cycle scope. **Fix:** strip the lift A/B criterion and the "why recommended" AC. Keep S2 to deterministic hard-filter quality (age/distance/intent, active-profile freshness). Move model ranking and explanation to PRD-AIREC.
- **[major] PRD-PREMIUM-E1-S2:34** — A paid "boost" sells 30 minutes of extra visibility, i.e. quantity of exposure, the volume game the vision positions against. PRD-PREMIUM's own risk register flags paid features eroding the free experience, yet ships boost as a should. **Where it breaks:** boost monetizes the swipe-volume dynamic the brand claims to reject and rewards reach over conversation. Short-term ARPU rises while the one real differentiator erodes. **Fix:** reframe the premium gain around the core value (surface to verified serious users, not raw reach), or record an explicit PO decision accepting the tension. Do not ship reach-for-pay as an unexamined should-have. [DEC-worthy]
- **[minor] PRD-AIREC-E1-S1:30** — A "so that I create more matches per week" story for an AI ranking layer the PRD itself calls a me-too feature behind Tinder and Bumble (PRD-AIREC:41-45). Its gates need >=20 swipes/user and sustained-message signals, data with no proven path to accumulate until the core loop works. **Where it breaks:** effort goes to a delighter that ships worse than incumbents on day one, with a data precondition that may never arrive at scale, while the must-be (reliable chat producing 7-day conversations) carries the real value. **Fix:** keep it could/later but add a go/no-go gate (do not start AIREC until PRD-CHAT shows real volume of sustained 7-day conversations to train on) and re-anchor its "so that" to sustained connection, not match count.

### Tech

- **[blocker] PRD-CHAT-E1-S3:18** — Both ACs are pure sensation: "must be smooth" (mượt mà) and "displays quickly and does not lag", with no frame rate, no render time, no jank threshold, nothing binary. **Where it breaks:** a test author has no threshold to assert. The sprint cannot be accepted or rejected, and the story ships permanently "interpreted" by whoever demos it. It is also unsizeable. **Fix:** rewrite as measurable Given-When-Then, e.g. "<5% of 100 consecutive frames drop below 60fps on a mid-range Android (Redmi Note)" and "first 50 messages reach time-to-interactive <=1.5s at p95 on 4G". Add the test device and network profile to story frontmatter.
- **[major] PRD-MATCH-E1-S2:21** — An AC requires a statistically significant A/B outcome (recommended-profile match rate >=20% over a random control, p<0.05). A/B significance takes weeks to months of live traffic and a full analysis pipeline. It is not a sprint deliverable. **Where it breaks:** the story cannot be accepted at sprint review. Its lifecycle couples to traffic volume and calendar time, so it is neither Independent nor Estimable and lives in permanent limbo. **Fix:** move the A/B outcome to a PRD success metric or a separate experiment epic. Replace the AC with a pre-launch proxy, e.g. precision@10 on a labeled staging set at X% above the distance-only baseline. (Pairs with the product-lens finding on the same story.)
- **[major] PRD-SAFETY-E1-S1:18** — The face-verification story mandates liveness + face-match at >=90% confidence within 60s, but neither the story, the epic PRD-SAFETY-E1, nor PRD-SAFETY declare a `depends_on` for any face-comparison or liveness service (line 71 defers only government-API verification). **Where it breaks:** the team discovers mid-sprint that vendor selection, procurement, and integration are all required (scope explosion), or stubs it and ships unverified. The 90% threshold also cannot be validated without a labeled test set named nowhere. **Fix:** add `depends_on: [FACE-MATCH-SERVICE]` to the story and PRD frontmatter, add a vendor-selection spike, and add an NFR AC documenting precision/recall at the 90% threshold on a labeled set accepted by the PO.
- **[minor] PRD-EVENTS-E1-S2:18** — The seat-reservation story decrements on booking and increments on cancel but has no AC for concurrent booking. Two users hitting the last seat can both read a positive count and both decrement, overselling. **Where it breaks:** the implementation defaults to a naive lock-free decrement. Oversell surfaces only in load testing or at a live event, and the post-launch fix needs a schema change or advisory lock, far more expensive than catching it here. **Fix:** add an AC requiring exactly one confirmation and a seat-unavailable error for the other, final count 0, no negative capacity, and note that the implementation must use atomic decrement or row-level lock.

### Market

- **[major] BRD:42** — The BRD rates COMP-FIKA threat:low, yet Fika already runs mandatory manual ID verification (~40% rejection), 16-personality-type matching, values dealbreakers, and IRL events as free-tier core. Fika's "authentic connection over match count" is the same positioning claimed here. PRD-SAFETY claims parity ahead of COMP-HEN but omits Fika from its parity table entirely. **Where it breaks:** under-weighting Fika means the safety-first verification moat and "authentic connection" positioning are more contested than the BRD admits. A later entrant with the same pitch but without Fika's verification head-start faces a harder acquisition story, especially for P-URBAN women, Fika's core audience. **Fix:** re-rate COMP-FIKA to med/high for PRD-SAFETY and the positioning. Add it to the parity table honestly, and foreground the real differentiator Fika lacks: national scope for P-PROVINCE and P-RETURNEE. Source: https://vietcetera.com/en/fika-asias-first-female-focused-ai-social-and-dating-app-raises-16m-in-seed-funding [DEC-worthy]
- **[major] BRD:56** — BRD-G1 targets 100k MAU Year 1 on a swipe mechanic identical to Tinder/Bumble, with no JTBD-competition answer for P-PROVINCE. The real alternative there is not Tinder but Facebook groups, Zalo, or natural introduction. The thin-pool risk is acknowledged but never resolved: why would a province user stay long enough to reach a first match on a near-empty swipe stack? **Where it breaks:** with no cold-start strategy for the provinces, 100k MAU rests implicitly on P-URBAN density in Hanoi/HCM where Tinder is already the top Google Play dating app. If P-PROVINCE fails to activate, the national positioning collapses into a HCM/Hanoi-only Tinder clone with no moat, and the north-star is unreachable if users churn before a first match. **Fix:** add a JTBD-competition section naming the do-nothing / Zalo / Facebook-groups alternative for P-PROVINCE. Specify a cold-start tactic (geographic seeding, invite incentives, or a minimum-pool threshold that surfaces an interest-signal/waiting-list flow instead of an empty stack). Tie BRD-G1 to a per-persona acquisition assumption so the figure is falsifiable. Source: https://www.similarweb.com/top-apps/google/vietnam/dating/
- **[minor] PRD-EVENTS:44** — PRD-EVENTS scopes events out with sound rationale but frames them only as an internal gold-plating risk, missing that COMP-FIKA (rated threat:low) runs IRL events as core positioning. Fika's App Store title is literally "Fika: Matchmaker & IRL Events". **Where it breaks:** dismissing events as gold-plating without noting a competitor uses them as a retention and acquisition hook leaves a strategic blind spot and no re-evaluation trigger if events prove to drive retention in Vietnam. **Fix:** add a competitive note to PRD-EVENTS' risk section. Keep scope:out for now but add a trigger (if Fika's events show measurable retention lift in public signals within 12 months, escalate the horizon later to next) and reconsider COMP-FIKA's rating. Source: https://apps.apple.com/us/app/fika-matchmaker-irl-events/id1528449006

### Craft

- **[major] PRD-CHAT:70** — The NFR says "Độ trễ gửi tin nhắn thấp" (low message delay) with no number. "Thấp" is an unmeasurable comparative. **Where it breaks:** during build the team cannot verify "low" objectively (500ms? 1s? 2s?), so acceptance turns subjective and PO/dev expectations diverge. **Fix:** set a concrete SLA, e.g. "max send delay under 2s on standard Vietnam 3G for a ~50KB payload" or a percentile target (p95 < 1.5s).
- **[major] PRD-SAFETY-E1-S1:20,36** — The ACs use the English term "liveness" in a Vietnamese spec with no translation or definition. **Where it breaks:** readers unfamiliar with biometric jargon may read "liveness" as "being live/online". The spec is bilingual by accident, forcing readers to guess. **Fix:** define once in parent PRD-SAFETY ("Liveness = xác minh người sống, phát hiện video/hình ảnh giả qua nhận dạng động tác selfie"), then use the Vietnamese term, or pair "liveness (xác minh người sống)" on first mention per artifact.
- **[major] PRD-AIREC:37-38,39,50** — "phù hợp hơn" (more suitable) and "thông minh hơn" (smarter) are subjective quality claims with no metric basis. **Where it breaks:** the team cannot define "more fitting" or "smarter" in an AC, so the feature is unmeasurable and success becomes opinion. **Fix:** rewrite with explicit metrics, e.g. "profiles with high likelihood of a match converting to sustained messaging (match-to-7-day-conversation rate >=15%)" and "ranking optimized on match-to-sustained-chat, not raw match count".
- **[major] PRD-CHAT:33,54** — "realtime" appears once in Latin script, once as "theo thời gian thực", oscillating between languages inside one artifact. **Where it breaks:** terminology drift adds friction for translation, localization QA, and cross-language readers. The spec reads hastily stitched rather than deliberately bilingual. **Fix:** pick one. Either Vietnamese "theo thời gian thực" throughout PRD-CHAT and children, or a bilingual convention ("theo thời gian thực (realtime)" on first mention then Vietnamese only). Document the choice in a glossary at the top of VISION or PRODUCT.
- **[major] PRD-PREMIUM:50-51,85** — The NFR "Hạn mức miễn phí phải đủ rộng" (the free tier must be sufficiently broad) leans on a vague comparative: how broad? 10 likes/day? 20? For how long? **Where it breaks:** with no floor, the team guesses. A tight limit churns users before they feel core value (a BRD anti-goal); a loose one fails to push conversion. **Fix:** specify the floor explicitly (e.g. min 20 likes/day, unlimited discovery, matching and messaging free once matched, 48h premium trial for new users) and measure "broad" by a retention/conversion metric.

## Repeat offenders

None — no prior reports.

## Worth recording as a decision (DEC-worthy)

- **PRD-PREMIUM-E1-S2:34** — Shipping a reach-for-pay "boost" runs against the quality-over-quantity north-star the brand is built on. This is a positioning trade-off the PO should record as an explicit decision (accept the tension, or reframe the premium gain) rather than leave as an unexamined should-have.
- **BRD:42** — Re-rating COMP-FIKA from threat:low contradicts the current BRD's stated competitive assessment and touches the safety-first positioning. A threat-level and positioning change of this weight belongs in the Decision Register, not a silent edit.

Unresolved: none.
