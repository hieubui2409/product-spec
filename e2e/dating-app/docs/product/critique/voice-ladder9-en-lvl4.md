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
level: 4
---
# Critique: all · level 4 · lenses: product, tech, market, craft

> Severity tally: blocker 3 · major 12 · minor 3

## Top 3: fix now

1. **[blocker][product] BRD-G2:57.** The vision sells sustained 7-day conversation and explicitly rejects match count as vanity (VISION:51-52), yet the only persona-engagement goal measures `weekly-match-rate`, raw match volume, and PRD-MATCH optimizes straight to it (PRD-MATCH:15,72). You wrote down the metric you swore to escape and wired the core build to it. **Broken because:** teams build to the metric they are graded on, and this one counts matches, so the product will chase swipe-to-match volume and rebuild the "millions of dead matches" the vision was founded to beat, while the 7-day north-star sits unowned by any BRD goal. **Fix now:** add or swap in a BRD goal that measures the north-star directly (e.g. % of matches reaching a sustained 7-day conversation), re-point PRD-MATCH and PRD-CHAT success metrics to it, and keep `weekly-match-rate` only as a leading funnel indicator. *(DEC-worthy)*

2. **[blocker][tech] PRD-CHAT-E1-S3:18.** Both ACs describe a feeling. Line 18 says the experience "must be smooth," line 19 says the UI "displays quickly and does not lag." Neither names a frame rate, a render time, or a jank threshold. There is no number any test could assert against. **Broken because:** the sprint can be neither accepted nor rejected on this story, it ships with the AC permanently "interpreted" by whoever demos it, and no engineer can size effort toward an undefined quality bar. **Fix now:** replace both with measurable Given-When-Then ACs, for example "when 100 consecutive frames render, fewer than 5% drop below 60 fps on a mid-range reference Android (Redmi Note)" and "first 50 messages reach time-to-interactive at or below 1.5s at p95 on 4G," and pin the test device and network profile into the story frontmatter.

3. **[blocker][market] BRD:22.** BRD-G3 targets premium revenue sufficient for Year-2 break-even, but its body is empty: no pricing tier, no conversion target, no ARPU floor. At Vietnam dating ARPU around USD 8.15/user/yr (Statista 2025), 100k MAU at 2-5% freemium conversion yields only around USD 16k-40k/yr, almost certainly short of running real-time chat (PRD-CHAT) plus a human-review safety queue (PRD-SAFETY). **Broken because:** with no pricing model or grounded conversion target, BRD-G3 is an aspiration with no path; the spec cannot verify whether premium features (view-who-liked-me, boost) earn enough to break even, leaving the Year-2 goal unverifiable and the PRD-PREMIUM investment case unsupported. **Fix now:** add a VND monthly price range anchored to the market (Tinder Gold runs roughly 149k-199k VND/mo), a target conversion band (3-6% of MAU), and a derived annual-revenue figure compared against projected Year-2 opex; if the math does not close, revisit PRD-PREMIUM's `horizon:later` tag or specify a secondary revenue stream. Source: https://www.statista.com/outlook/emo/dating-services/vietnam *(DEC-worthy)*

## By lens

### Product

- **[major] PRD-EVENTS-E1-S3:18.** A fully-authored story to organize and sell tickets to nationwide concerts: line-ups, multi-tier ticketing, QR check-in, genre filters. None of the three personas hired a dating app to buy concert tickets, and no BRD goal maps to running a ticketing business; the PRD itself labels it gold-plating (PRD-EVENTS-E1-S3:43). **Broken because:** a complete AC-bearing story signals a real build candidate, and this one is an entire separate business (artist ops, venue security, ticket fraud) with zero line to the north-star, splitting the team off a core loop that has not yet been proven. **Fix now:** delete the story or demote it to a one-line parking-lot idea; do not carry an out-of-scope, persona-less feature as a drafted AC-complete artifact.

- **[major] PRD-MATCH-E1-S2:38.** Scope explicitly defers AI recommendations and "why recommended" to PRD-AIREC next cycle (PRD-MATCH:64; PRD-AIREC:77), yet this must/core-value story demands a recommender beating random by at or above 20% (p<0.05) and a "why recommended this person?" explanation, the deferred AIREC capability smuggled into a now/must story. Tech flags the same story at `:21` for the unsizeable A/B AC. **Broken because:** the team either over-builds an ML recommender to hit an A/B-lift gate that cannot pass on a cold-start user base, or quietly drops the AC; either way the spec's credibility rots and now-cycle scope blows. **Fix now:** strip the recommendation-lift and "why recommended" ACs from S2, keep it to deterministic hard-filter quality (age/distance/intent, active-profile freshness), and move model ranking and explanation back to PRD-AIREC where they already live. *(DEC-worthy)*

- **[major] PRD-PREMIUM-E1-S2:34.** A paid "boost" that buys 30 minutes of priority visibility. The value sold is quantity of exposure, the exact volume game the vision positions against; PRD-PREMIUM's own risk register flags that paid features erode the free experience, yet boost ships as a should-have. **Broken because:** boost monetizes the swipe-volume dynamic the product claims to reject, rewarding payers with reach instead of sustained conversation, lifting ARPU short-term while pulling the experience off the one differentiator the brand is built on. **Fix now:** reframe the premium gain around the core value (e.g. surface to verified-serious users, not raw reach) or record an explicit PO decision accepting the north-star tension; do not ship a reach-for-pay mechanic as an unexamined should. *(DEC-worthy)*

- **[minor] PRD-AIREC-E1-S1:30.** A "so that I create more matches per week" story for an AI ranking layer the PRD itself calls a me-too feature landing behind Tinder and Bumble (PRD-AIREC:41-45); its gates need at or above 20 swipes/user and sustained-message signals the product has no proven path to accumulate, and that riskiest assumption is named but unowned. **Broken because:** effort goes to a delighter the spec admits will be worse than incumbents on day one, whose data precondition may never materialize, while the real must-be (reliable chat producing 7-day conversations) carries the value. **Fix now:** keep it could/later but add a go/no-go gate. Do not start PRD-AIREC until PRD-CHAT shows measurable volume of sustained 7-day conversations to train on, and re-anchor the story's "so that" to sustained connection, not match count.

### Tech

- **[blocker] PRD-CHAT-E1-S4:18.** Two ACs are absolute guarantees with no mechanism: line 18 demands conversations be "absolutely safe," line 19 demands the system "completely protect" users, with no named threat, detection, response, or SLA, while the story is marked should/size M. **Broken because:** it cannot be tested, sized, or accepted; any build trivially claims compliance, the hidden scope (moderation? encryption? abuse detection?) stays invisible to estimators, and a post-launch incident will pin blame on a vacuously-true AC. **Fix now:** split into discrete one-mechanism stories, e.g. E2E encryption ("stored payload encrypted, decryptable only with sender/receiver keys, verifiable via server-log inspection") and abuse blocking ("when A blocks B, B's send is rejected 403, no message stored"); retire the current story.

- **[major] PRD-MATCH-E1-S2:21.** One AC requires a statistically significant A/B outcome (recommended-profile match rate at or above 20% above random control, p<0.05). A p<0.05 result needs weeks to months of live traffic and an analysis pipeline; it is not a sprint deliverable. Product flags the same story at `:38` for the scope leak. **Broken because:** done-ness cannot be judged at sprint review, the story's lifecycle couples to traffic volume and calendar time, and it fails INVEST on Independent and Estimable, leaving it permanently in limbo. **Fix now:** move the A/B outcome to a PRD success metric or a separate experiment epic owned by the data team, and replace the AC with a pre-launch proxy, e.g. "scored against a labeled staging batch, precision@10 is at or above X% above the distance-only baseline."

- **[major] PRD-SAFETY-E1-S1:18.** The face-verification story mandates liveness plus face-match at or above 90% confidence within 60s (lines 18, 20), yet neither the story, the epic PRD-SAFETY-E1, nor PRD-SAFETY declares a `depends_on` for a liveness/face-comparison service; PRD-SAFETY:71 defers only government-API verification. **Broken because:** the story silently assumes a face-matching pipeline exists, so the team discovers vendor selection, procurement, and integration mid-sprint (massive scope expansion) or stubs it and ships unverified, and the 90% threshold cannot be validated without a labeled test set that appears nowhere. **Fix now:** add `depends_on: [FACE-MATCH-SERVICE]` to the story and PRD-SAFETY frontmatter, add a vendor-selection spike, and add an NFR AC documenting precision/recall at the 90% threshold against a labeled face-pair test set; the story is unestimable until the spike lands.

- **[minor] PRD-EVENTS-E1-S2:18.** The seat-reservation story specifies decrement-on-book (line 18) and increment-on-cancel (line 21) but has no AC for concurrent booking: two users tapping "Giữ chỗ" on the last seat can both read a positive count and both decrement, causing an oversell. **Broken because:** absent a concurrency AC the build defaults to a naive lock-free decrement, the oversell surfaces only in load testing or at a live event, and the post-launch fix (schema change or advisory lock) is far more expensive; the story also fails INVEST-Testable on the edge path. **Fix now:** add an AC: "when two users contend for the last seat, exactly one is confirmed and the other gets seat-unavailable, final count 0, no negative capacity," and note the implementation must use an atomic decrement or row-level lock.

### Market

- **[major] BRD:42.** The BRD rates COMP-FIKA threat: low, but Fika already runs mandatory manual ID verification (around 40% rejection), a 16-personality matching layer, values-based dealbreakers, and IRL events in Vietnam as free-tier core, and Fika is absent from PRD-SAFETY's competitive_parity table entirely. The spec's "authentic connection, not match count" differentiator is also Fika's stated positioning. **Broken because:** if Fika is underweighted, the safety-first verification moat and authentic-connection positioning are far more contested than the BRD admits, and a later entrant with similar positioning but without Fika's verification rigor faces a harder acquisition story, especially for P-URBAN women who are Fika's core audience. **Fix now:** raise COMP-FIKA to med/high for PRD-SAFETY, add it to the competitive_parity table with an honest parity/behind read on manual verification, and foreground the real differentiator Fika lacks (national scope for P-PROVINCE and P-RETURNEE) in the BRD market context. Source: https://vietcetera.com/en/fika-asias-first-female-focused-ai-social-and-dating-app-raises-16m-in-seed-funding

- **[major] BRD:56.** BRD-G1 targets 100k MAU in Year 1 on a swipe mechanic functionally identical to Tinder/Bumble, with no JTBD-competition analysis for P-PROVINCE, whose real alternative is not Tinder but Facebook groups, Zalo, or natural introduction; the thin-pool risk is acknowledged but the spec never explains why a province user stays active long enough to reach a first match on near-empty swipe stacks. **Broken because:** without a credible cold-start strategy the 100k MAU goal implicitly leans on P-URBAN density in Hanoi/HCM where Tinder is already the top dating app, the national positioning collapses to a Hanoi/HCM-only Tinder clone with no moat, and the north-star is unreachable if users churn before a first match. **Fix now:** add a JTBD-competition section naming the do-nothing and Zalo/Facebook-groups alternatives for P-PROVINCE, specify a cold-start tactic (geographic seeding, invite incentives, or a minimum-viable-pool threshold below which the product surfaces an interest-signal/waiting-list flow instead of an empty stack), and tie BRD-G1's 100k MAU to per-persona acquisition assumptions so the figure is falsifiable. Source: https://www.similarweb.com/top-apps/google/vietnam/dating/

- **[minor] PRD-EVENTS:44.** PRD-EVENTS is correctly scoped out, but it frames offline events purely as internal gold-plating without noting that COMP-FIKA (rated threat: low) already runs IRL events as core positioning; Fika's App Store title is literally "Fika: Matchmaker & IRL Events." **Broken because:** dismissing events as gold-plating while a competitor uses them as a retention and acquisition hook leaves a strategic blind spot with no re-evaluation trigger if IRL events prove meaningful in Vietnam. **Fix now:** add a competitive note to PRD-EVENTS' risk section flagging Fika's events positioning, keep scope:out but add a trigger ("if Fika's events show measurable retention lift in public signals within 12 months, escalate events from later to next"), and reconsider COMP-FIKA's BRD threat rating. Source: https://apps.apple.com/us/app/fika-matchmaker-irl-events/id1528449006

### Craft

- **[major] PRD-CHAT:70.** The NFR says "Độ trễ gửi tin nhắn thấp" (low message delay) with no number. "Thấp" is an unmeasurable comparative. **Broken because:** the team cannot verify "low" objectively (is 500ms low? 1s? 2s?), so acceptance turns subjective and PO/dev expectations diverge. **Fix now:** set a concrete SLA, e.g. "độ trễ gửi tin nhắn tối đa < 2 giây trên 3G tiêu chuẩn Việt Nam với gói ~50KB," or a percentile target (p95 < 1.5s).

- **[major] PRD-SAFETY-E1-S1:20,36.** The ACs use the English term "liveness" in a Vietnamese spec with no translation or definition. **Broken because:** readers unfamiliar with biometric jargon may read "liveness" as "being live/online," and the spec is bilingual by accident, forcing readers to guess. **Fix now:** define it once in parent PRD-SAFETY ("Liveness = xác minh người sống, phát hiện video/ảnh giả qua nhận dạng động tác selfie"), then use the Vietnamese term, or pair "liveness (xác minh người sống)" on first mention per artifact.

- **[major] PRD-AIREC:37-38,39,50.** The PRD leans on "phù hợp hơn" (more suitable) and "thông minh hơn" (smarter) with no metric, subjective quality claims with no measurement basis. **Broken because:** the team cannot put "more fitting" or "smarter" into acceptance criteria, so the feature is unmeasurable and success becomes opinion. **Fix now:** rewrite with explicit metrics, e.g. "hồ sơ có khả năng cao dẫn tới match chuyển thành nhắn tin duy trì (match to 7-day-conversation at or above 15%)" and "thứ tự gợi ý tối ưu theo tỉ lệ match-to-sustained-chat, không theo số match thô."

- **[major] PRD-CHAT:33,54.** "realtime" appears inconsistently, once in Latin script, once as "theo thời gian thực," within the same artifact, with no convention. **Broken because:** terminology drift across the spec creates friction for translation and localization QA and makes the spec read as hastily stitched together rather than deliberately bilingual. **Fix now:** pick one. Either "theo thời gian thực" throughout PRD-CHAT and children, or a bilingual convention ("theo thời gian thực (realtime)" on first mention then Vietnamese only), and record the choice in a glossary at the top of VISION or PRODUCT.

- **[major] PRD-PREMIUM:50-51,85.** NFR line 85 says the free tier must be "đủ rộng" (sufficiently broad) to keep the core experience usable without paying, a vague comparative with no floor: 10 likes/day? 20? for how long? **Broken because:** with no floor the team guesses. A tight limit churns users before they feel core value (a BRD anti-goal); a loose one fails to push conversion; and the constraint's enforcement is left to interpretation. **Fix now:** specify the floor, e.g. "tối thiểu 20 lượt thích/ngày, khám phá không giới hạn, ghép đôi và nhắn tin miễn phí khi đã match, 48 giờ dùng thử premium cho người mới," and tie "đủ rộng" to a retention metric.

## Repeat offenders

None. No prior critique reports for this scope.

## Worth recording as a decision (DEC-worthy)

- **BRD-G2:57** — the persona-success metric (`weekly-match-rate`) directly contradicts the vision's stated north-star (VISION:51-52, sustained 7-day conversation over match count). This is a binding metric-ownership ruling and touches approved positioning; record it via `--decision` before the build steers to the wrong number.
- **PRD-MATCH-E1-S2:38** — a now/must core-value story carries a capability the spec deferred to PRD-AIREC next cycle. The scope ruling (build the recommender now vs. honor the deferral) is the PO's to record.
- **PRD-PREMIUM-E1-S2:34** — paid "boost" (reach-for-pay) runs against the quality-over-quantity north-star. Either reframe or record an explicit PO decision accepting the tension; do not let it ship as an unexamined should.
- **BRD:22** — accepting the Year-2 break-even goal without a pricing model is a financial-viability ruling; the chosen pricing band and conversion target (or a decision to revisit PRD-PREMIUM's horizon) belongs in the Decision Register.
