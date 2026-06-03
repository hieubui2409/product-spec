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
level: 8
register:
  dialect: bac
  gender: m
  profanity: strong
---
# Critique: all  ·  level 8  ·  lenses: product, tech, market, craft

> Severity tally: blocker 3 · major 11 · minor 3

## Top 3: fix now

1. **[blocker][product] BRD-G2:57** The vision swears off match-count as a vanity metric (VISION:51-52), then the only persona-engagement goal measures `weekly-match-rate`, raw match count, and PRD-MATCH wires its success straight to it (PRD-MATCH:15,72). This whole spec pulls the same stunt every time: it writes a north-star at the top, then forgets it three files down. Teams build to the number they are graded on. **Trashed because:** grade the team on match count and they will optimize swipe-to-match volume and rebuild the exact "millions of dead matches" graveyard the vision was founded to escape, while the 7-day-conversation north-star sits in no goal, owned by nobody. **Rewrite it now:** add or replace a BRD goal that measures the north-star directly (% of matches that become a sustained 7+ day conversation), re-point PRD-MATCH and PRD-CHAT success to it, and keep `weekly-match-rate` as a leading funnel indicator only, never the persona-success goal.

2. **[blocker][tech] PRD-CHAT-E1-S4:18** Two acceptance criteria promise the moon and name no mechanism: line 18 says conversations are "absolutely safe," line 19 says the system "completely protects" users. No threat model, no detection, no response, no SLA, on a story tagged `should`/`M`. It is bullshit to write an unbounded safety guarantee and call it an acceptance criterion. **Trashed because:** this story cannot be tested, sized, or accepted in a sprint, and any build will trivially claim compliance because the AC is vacuously true. Worse, after a real safety incident post-launch, the AC blocks release because "completely protect" was never something you could actually verify. **Rewrite it now:** split into discrete one-mechanism stories, each testable. E2E encryption: "Given a message is sent, when it is stored server-side, then the stored payload is encrypted and decryptable only with sender/receiver keys." Abuse block: "Given A blocks B, when B sends, then the server returns 403 and stores nothing." Retire the current story or replace it with links to the split set.

3. **[blocker][market] BRD:22** BRD-G3 targets break-even on premium revenue by Year 2 and its body is empty: no price tier, no conversion target, no ARPU floor. Vietnam dating-services ARPU runs ~USD 8.15/user/year (Statista 2025); at 100k MAU and a 2-5% freemium conversion that is USD 16k-40k/year, which does not cover real-time chat infra (PRD-CHAT) plus a human safety-review queue (PRD-SAFETY). A revenue goal with no math is just a feeling typed into a frontmatter field. **Trashed because:** with no pricing model or grounded conversion target, BRD-G3 is an aspiration with no path, the premium feature set cannot be validated against break-even, and the entire Year-2 investment case is unsupported. **Rewrite it now:** add to BRD-G3 or PRD-PREMIUM a monthly VND price range anchored to market (Tinder Gold ~149k-199k VND/mo), a target conversion of 3-6% MAU, and a derived annual-revenue figure compared against projected Year-2 opex. If the math does not close, revisit the `horizon:later` tag or specify a second revenue stream. Source: https://www.statista.com/outlook/emo/dating-services/vietnam

## By lens

### Product

- **[major] PRD-EVENTS-E1-S3:18** A fully drafted story to organize and sell tickets to nationwide concerts, lineups, multi-tier ticketing, QR check-in, inside a dating app. None of the three personas hired this app to buy concert tickets, no BRD goal or vision pain maps to it, and the PRD itself labels it gold-plating (PRD-EVENTS-E1-S3:43). Whoever wrote this got bored of the dating app and started speccing a Ticketmaster clone. **Trashed because:** an AC-complete story reads as a real build candidate, and it is a whole separate business (artist ops, venue security, ticket fraud) with zero line to the north-star, pulling the team off a core loop that is not even proven yet. **Rewrite it now:** delete the story or demote it to a one-line idea in a parking-lot doc; never carry an out-of-scope, persona-less feature as a drafted AC-complete artifact.

- **[major] PRD-MATCH-E1-S2:38** (product + tech, merged) PRD-MATCH explicitly excludes AI recommendations and "why recommended" and defers them to PRD-AIREC next cycle (PRD-MATCH:64; PRD-AIREC:77), yet this `must`/core-value story demands a recommender that beats random by >=20% via A/B test at p<0.05 (line 38/21) plus a "why recommended" explanation (line 22), the exact deferred capability smuggled into a now-story. And p<0.05 is weeks-to-months of live traffic, not a sprint deliverable. The same half-assed pattern shows up twice: defer a thing on one line, require it on another. **Trashed because:** the build team either over-builds an ML recommender to hit an A/B gate that cannot pass on a cold-start user base, or quietly drops the AC; either way the story is not Independent (depends on traffic) and not Estimable, so it lives in permanent sprint-review limbo. **Rewrite it now:** strip the lift A/B criterion and the "why recommended" AC from S2, keep S2 to deterministic hard-filter quality (age/distance/intent/active-profile freshness), move model ranking and explanation to PRD-AIREC where they already live, and re-home the holdout experiment as a data-team task with a pre-launch proxy AC (precision@10 above the distance-only baseline on a labeled staging set).

- **[major] PRD-PREMIUM-E1-S2:34** A paid "boost" sells 30 minutes of extra visibility, quantity of exposure, the exact volume game the vision positions against in favor of quality. PRD-PREMIUM's own risk register flags paid features eroding the free experience, then ships boost as a `should` revenue feature anyway. Flag the risk, walk straight into it. This half-measure runs through the whole spec. **Trashed because:** boost monetizes the swipe-volume dynamic the product claims to reject and rewards payers with reach instead of sustained conversation, lifting ARPU short-term while pulling the experience off the one differentiator the brand is built on. **Rewrite it now:** reframe the premium gain around the core value (surface-to-verified-serious-users, not raw reach), or record an explicit PO decision accepting the north-star tension; do not ship a reach-for-pay mechanic as an unexamined `should`.

- **[minor] PRD-AIREC-E1-S1:30** A "so that I create more matches per week" story for an AI ranking layer the PRD itself calls a me-too feature landing behind Tinder and Bumble (PRD-AIREC:41-45). Its gates need >=20 swipes/user and sustained-message signals, data the product has no proven path to until the core loop works, and that riskiest assumption is named but owned by no one. **Trashed because:** effort goes to a delighter that by the spec's own admission starts worse than incumbents and whose data precondition may never arrive, while the real must-have, reliable chat that produces 7-day conversations, carries the value. **Rewrite it now:** keep it `could`/later (already done) but add a go/no-go gate: do not start PRD-AIREC until PRD-CHAT shows measurable sustained 7-day conversations to train on, and re-anchor the "so that" to sustained connection, not match count.

### Tech

- **[blocker] PRD-CHAT-E1-S3:18** Both ACs are pure feeling: line 18 says the experience "must be smooth," line 19 says the UI "displays quickly and does not lag." Not one frame rate, render time, or jank threshold, nothing that produces a binary pass/fail. A test author has literally nothing to assert against, and it is lazy to ship a quality bar with no number under it. **Trashed because:** the sprint can never be accepted or rejected on this story; it ships with the AC "interpreted" by whoever demos it, and it is unsizeable because no engineer can estimate toward an undefined bar. **Rewrite it now:** AC1: "Given the user scrolls the message list, when 100 consecutive frames render, then fewer than 5% drop below 60fps on the reference device (mid-range Android, e.g. Redmi Note)." AC2: "Given the conversation is opened, when the first 50 messages load, then time-to-interactive is <=1.5s at p95 on 4G." Add the test device and network profile to the story frontmatter as a testability fixture.

- **[major] PRD-SAFETY-E1-S1:18** The face-verification story mandates liveness + face-match at >=90% confidence within 60s, yet neither the story, the parent epic, nor PRD-SAFETY declares a `depends_on` for a face-comparison/liveness service (PRD-SAFETY:71 defers only the government-API piece). The story quietly assumes a face-matching pipeline already exists, the same wishful corner-cutting on display elsewhere. **Trashed because:** with no named dependency the team discovers mid-sprint that vendor selection, procurement, and integration are required (scope explodes) or stubs it and ships unverified, and the 90% threshold cannot be validated without a labeled test set that appears nowhere in the spec. **Rewrite it now:** add `depends_on: [FACE-MATCH-SERVICE]` to the story and PRD-SAFETY frontmatter, add a spike "evaluate and select a liveness + face-comparison vendor/SDK, define integration contract and SLA," and add an NFR AC: "Given a labeled set of N face pairs with known ground truth, when the service is evaluated, then precision/recall at the 90% threshold are documented and PO-accepted."

- **[minor] PRD-EVENTS-E1-S2:18** The seat-reservation story specifies decrement-by-1 on booking (line 18) and increment-by-1 on cancel (line 21), and has no AC for the concurrent case: two users hitting "Giữ chỗ" on the last seat both read a positive count and both decrement, producing oversell. The happy path does not distinguish optimistic-read from post-commit state. **Trashed because:** without a concurrency AC the build defaults to a naive lockless decrement, the oversell only surfaces in load testing or at a live event, and the post-launch fix needs a schema change or advisory lock that costs far more. **Rewrite it now:** add "Given two users simultaneously book the last seat, when both requests process, then exactly one gets a confirmation and the other a seat-unavailable error, final count is 0, negative capacity impossible," and annotate that the implementation must use an atomic decrement or row-level lock (SELECT FOR UPDATE / compare-and-swap), leaving the mechanism choice with the team.

### Market

- **[major] BRD:42** The BRD rates COMP-FIKA threat:low, but Fika already runs mandatory manual ID verification (~40% rejection), a 16-personality matching layer, values dealbreakers, and IRL events in Vietnam as core free-tier features, and its stated positioning, "authentic connection over match count," is this product's headline differentiator. PRD-SAFETY claims parity ahead of COMP-HEN but leaves COMP-FIKA out of the parity table entirely. Underrating the one competitor who already occupies your exact position is not analysis; it is wishful thinking. **Trashed because:** if Fika is logged as threat:low, the safety-first verification moat and the "authentic connection" positioning are far more contested than the BRD admits, and a late entrant with the same pitch but without Fika's head start faces a much harder acquisition story, especially for P-URBAN women, Fika's primary audience. **Rewrite it now:** re-rate COMP-FIKA to med/high for PRD-SAFETY and the positioning, add it to the parity table with an honest behind/parity call on manual-verification strictness, and foreground what Fika lacks, national scope for P-PROVINCE and P-RETURNEE, instead of competing on verification where Fika already leads. Source: https://vietcetera.com/en/fika-asias-first-female-focused-ai-social-and-dating-app-raises-16m-in-seed-funding

- **[major] BRD:56** BRD-G1 targets 100k MAU in Year 1 on a swipe mechanic functionally identical to Tinder/Bumble, and never addresses JTBD-competition for P-PROVINCE, whose real alternative is not Tinder but Facebook groups, Zalo, or a natural introduction. The thin-pool risk is acknowledged but the spec never says why a province user installs and stays active long enough to reach a first match when the swipe stack is near-empty at launch. **Trashed because:** with no cold-start strategy the 100k MAU goal silently depends on P-URBAN density in Hanoi/HCM, where Tinder is already the top dating app on Google Play Vietnam; if P-PROVINCE fails to activate, the national positioning collapses into a HN/HCM-only Tinder clone with no moat, and the 7-day north-star is unreachable if users churn before a first match. **Rewrite it now:** add a JTBD-competition section to the BRD or PRD-MATCH naming the do-nothing and Zalo/Facebook-groups alternative for P-PROVINCE, specify a cold-start tactic (geographic seeding, invite incentives, or a minimum-viable-pool threshold below which the app surfaces an interest-signal/waiting-list flow instead of an empty stack), and tie 100k MAU to a per-persona acquisition assumption so the number is falsifiable. Source: https://www.similarweb.com/top-apps/google/vietnam/dating/

- **[minor] PRD-EVENTS:44** PRD-EVENTS is correctly scoped out with sound rationale, but frames offline events solely as internal gold-plating while COMP-FIKA, rated threat:low, already runs IRL events as core positioning, App Store title "Fika: Matchmaker & IRL Events" (2025-2026). **Trashed because:** dismissing events as gold-plating without noting a competitor uses them as a retention and acquisition hook leaves a strategic blind spot with no re-evaluation trigger if IRL events prove to be a real retention mechanism in Vietnam. **Rewrite it now:** add a competitive note to the PRD-EVENTS risk section flagging Fika's events positioning, keep `scope:out` for now but add a trigger: if Fika's events show measurable retention lift in public signals within 12 months, escalate the events horizon from later to next, and reconsider COMP-FIKA's threat rating. Source: https://apps.apple.com/us/app/fika-matchmaker-irl-events/id1528449006

### Craft

- **[major] PRD-CHAT:70** The NFR says "Độ trễ gửi tin nhắn thấp" with no number. "Thấp" is an unmeasurable comparative, the team cannot verify it, and shipping a latency requirement with no threshold is the same lazy reflex as the smoothness ACs. **Trashed because:** is 500ms low? 1s? 2s? Without a number, acceptance is subjective and the gap between PO and dev expectation only surfaces after build. **Rewrite it now:** "Độ trễ gửi tin nhắn tối đa dưới 2 giây trên kết nối 3G tiêu chuẩn Việt Nam (gói ~50KB)" or a percentile target (p95 < 1.5s).

- **[major] PRD-SAFETY-E1-S1:20,36** The ACs use the English term "liveness" in a Vietnamese spec with no translation or definition. Bilingual by accident, not design. **Trashed because:** readers unfamiliar with biometric jargon may read "liveness" as "being live/online" and build the wrong thing. **Rewrite it now:** define once in parent PRD-SAFETY: "Liveness = xác minh người sống (phát hiện video/hình ảnh giả) qua nhận dạng động tác selfie," then use the Vietnamese term in stories or pair "liveness (xác minh người sống)" on first mention per artifact.

- **[major] PRD-AIREC:37-38,39,50** The PRD leans on "phù hợp hơn" and "thông minh hơn" with no metric: "ưu tiên những hồ sơ có khả năng dẫn tới kết nối phù hợp hơn" (line 37) and "một thứ tự gợi ý thông minh hơn" (line 39). Subjective quality claims with nothing to measure against. **Trashed because:** the team cannot put "more fitting" or "smarter" into an AC, so the feature is unmeasurable and success becomes opinion. **Rewrite it now:** "hồ sơ có khả năng cao dẫn tới match chuyển thành nhắn tin duy trì (tỉ lệ match→7-day-conversation >= 15%)" and "thứ tự gợi ý tối ưu hóa theo tỉ lệ match-to-sustained-chat, không theo số match thô."

- **[major] PRD-CHAT:33,54** "realtime" appears twice in one artifact, once as English "realtime" (line 33), once as "theo thời gian thực" (line 54), with no convention. **Trashed because:** terminology drift across languages creates friction for localization QA and cross-language readers; the spec reads hastily stitched rather than deliberately bilingual. **Rewrite it now:** pick one: either "theo thời gian thực" throughout PRD-CHAT and child stories, or "theo thời gian thực (realtime)" on first mention then Vietnamese only, and record the choice in a glossary at the top of VISION or PRODUCT.

- **[major] PRD-PREMIUM:50-51,85** NFR line 85 says "Hạn mức miễn phí phải đủ rộng để trải nghiệm lõi còn dùng được mà không trả phí." "Đủ rộng" is a vague comparative: 10 likes/day? 20? For how long? **Trashed because:** without a floor the team guesses; a tight limit churns users before they feel core value (a BRD anti-goal), a loose one fails to push conversion, and the spec asserts a constraint while leaving enforcement to interpretation. **Rewrite it now:** "Hạn mức miễn phí tối thiểu: 20 lượt thích/ngày, khám phá không giới hạn, ghép đôi + nhắn tin miễn phí khi đã match. Người dùng mới nhận 48 giờ thử premium miễn phí," then measure "đủ rộng" by retention: "Người dùng miễn phí không quá 7 ngày trong 30 ngày đầu vẫn >= 40% chuyển đổi sang premium."

## Repeat offenders

None, no prior reports.

## Worth recording as a decision (DEC-worthy)

- **BRD-G2:57 (north-star vs `weekly-match-rate`)** Re-pointing the persona-success goal off raw match count contradicts the metric PRD-MATCH/PRD-CHAT already optimize to. If any of these is `approved`, this is a no-silent-reversal point: record the PO ruling (Keep / Change+re-approve / Hybrid) as a `DEC`.
- **PRD-PREMIUM-E1-S2:34 (boost vs north-star)** Shipping a reach-for-pay mechanic against the stated quality-over-quantity positioning is a binding positioning ruling; record the PO's accept/reframe decision as a `DEC` rather than leaving it as an unexamined `should`.
- **PRD-MATCH-E1-S2:38 (deferred AIREC capability in a now/must story)** Pulling AI ranking and "why recommended" out of a core-value cycle story contradicts the PRD's own deferral to PRD-AIREC; record the scope ruling as a `DEC`.
