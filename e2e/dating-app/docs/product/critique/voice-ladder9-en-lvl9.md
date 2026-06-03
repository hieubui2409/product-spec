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
level: 9
register:
  dialect: bac
  gender: m
  profanity: strong
---
# Critique: all  ·  level 9  ·  lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 11 · minor 3

## Top 3: fix now

1. **[blocker][product] BRD-G2:57** — The vision swears off match-count as a vanity metric and sells the 7-day sustained conversation as the north-star (VISION:51-52), and then the one persona-engagement goal you wrote measures `weekly-match-rate`. So the whole build steers by the exact garbage metric the product was founded to escape. PRD-MATCH wires its success straight to it (PRD-MATCH:15,72). The north-star is owned by literally no goal. **Wrecked because:** teams build to the number on the wall, and this wall says "make more matches" — so you will faithfully reproduce the millions of dead matches you claimed to be better than, and ship the competitor you set out to beat. The one thing that makes this product not-Tinder is unmeasured and therefore unbuilt. **Rewrite it, do not make me say it twice:** add a BRD goal that measures the north-star directly (% of matches that become a 7+ day conversation), re-point PRD-MATCH / PRD-CHAT success metrics to it, and demote `weekly-match-rate` to a leading funnel indicator, not the persona-success goal. `DEC-worthy` -- this re-defines the headline engagement goal and contradicts the metric PRD-MATCH already optimizes to.

2. **[blocker][tech] PRD-CHAT-E1-S4:18** -- Two ACs that are pure fantasy: line 18 promises conversations "an toàn tuyệt đối" (absolutely safe) and line 19 promises the system will "bảo vệ người dùng hoàn toàn" (completely protect users). No threat model, no detection mechanism, no response plan, no SLA -- an unbounded safety guarantee crammed into a should/size:M story. This is not a requirement. It is a fucking prayer with a checkbox. **Wrecked because:** nobody can test, size, or accept this. Any build trivially "complies" (the system does *something* when something bad happens), the AC is vacuously true forever, and the day a real safety incident lands post-launch this empty promise is what blocks the release. **Rewrite it, do not make me say it twice:** split into discrete testable stories, one mechanism per dimension -- e.g. "Given A blocks B, when B sends a message, then the server rejects with 403 and stores nothing"; "Given a message is stored server-side, then the payload is encrypted and decryptable only with sender/receiver keys, verifiable via server-log inspection." Retire the current story.

3. **[blocker][market] BRD:22** -- BRD-G3 wants premium revenue to hit operational break-even by Year 2, and the BRD-G3 body is *empty*. No price tier, no conversion target, no ARPU floor. Run the actual numbers: Vietnam dating-services ARPU is ~USD 8.15/user/yr (Statista 2025), at 100k MAU and an industry 2-5% freemium conversion that is roughly USD 16k-40k/year -- which does not come close to paying for real-time messaging infra (PRD-CHAT) plus a human safety-review queue (PRD-SAFETY). **Wrecked because:** a break-even goal with no pricing model and no conversion target is a wish with a year attached. You cannot validate whether view-who-liked-me + boost will ever cover cost, so the entire investment case for PRD-PREMIUM rests on a blank line. **Rewrite it, do not make me say it twice:** add to BRD-G3 / PRD-PREMIUM a monthly VND price range anchored to the market (Tinder Gold ~149k-199k VND/mo), a 3-6% target conversion, and a derived annual-revenue estimate compared against Year-2 opex. If the math does not close, revisit the `horizon:later` tag or specify a second revenue stream. Source: https://www.statista.com/outlook/emo/dating-services/vietnam `DEC-worthy`

## By lens

### Product

- **[major][product+tech] PRD-MATCH-E1-S2:38 / :21** -- A must, core-value story that quietly carries next-cycle work. PRD-MATCH explicitly excludes AI recommendations and "why recommended" and defers them to PRD-AIREC (PRD-MATCH:64; PRD-AIREC:77), yet S2 demands a recommender that beats random by >=20% via A/B at p<0.05 (`:38`/`:21`) plus a "why recommended this person?" explanation (`:22`). Both lenses land on the same rot: the product lens says it smuggles deferred AIREC scope into a now/must; the tech lens says a p<0.05 A/B outcome takes weeks to months of live traffic and is not a sprint-acceptable AC, so the story is neither Independent nor Estimable and sits in limbo forever. **Wrecked because:** the team either over-builds an ML recommender to clear an A/B gate that cannot pass on a cold-start user base, or quietly drops the AC -- both blow the now-cycle scope and rot the spec's credibility. **Rewrite it, do not make me say it twice:** strip the recommendation-lift A/B criterion and the "why recommended" AC from S2; keep S2 to deterministic hard-filter quality (age/distance/intent, active-profile freshness); move model ranking + explanation to PRD-AIREC where they already live; if a quality gate is wanted pre-launch, use a staging proxy like precision@10 vs the distance-only baseline. `DEC-worthy` -- contradicts the approved PRD-MATCH scope exclusion.

- **[major][product] PRD-EVENTS-E1-S3:18** -- A fully drafted, AC-complete story for organizing and *selling tickets* to nationwide concerts inside a dating app: line-ups, multi-tier ticketing, QR check-in, genre filters. None of the three personas hired this app to buy concert tickets, no BRD goal maps to running a ticketing business, and the PRD itself labels it gold-plating and solution-first (`:43`). It is genuinely baffling this got AC. **Where it dies:** a fully-specified story reads as a real build candidate, and this one is an entire separate business -- artist ops, venue security, ticket fraud -- with zero line to the 7-day north-star, pulling the team off a core loop that is not even proven yet. **Rewrite it, do not make me say it twice:** delete the story, or demote it to a one-line idea in a parking-lot doc. Do not carry a persona-less, out-of-scope feature as a drafted AC artifact.

- **[major][product] PRD-PREMIUM-E1-S2:34** -- Paid "boost" sells 30 minutes of extra visibility. The value prop is raw exposure -- the volume game the vision explicitly positions *against*. PRD-PREMIUM's own risk register flags that paid features can erode the free experience, and then ships boost as a should anyway. **Where it dies:** boost monetizes the exact swipe-volume dynamic the brand claims to reject and rewards payers with reach instead of sustained conversation; it can bump ARPU short-term while dragging the experience off the one differentiator the product is built on. **Rewrite it, do not make me say it twice:** reframe the premium gain around the core value (surface-to-verified-serious-users, not raw reach) or record an explicit PO decision accepting the north-star tension. Do not ship a reach-for-pay mechanic as an unexamined should. `DEC-worthy`

- **[minor][product] PRD-AIREC-E1-S1:30** -- A "so that I create more matches per week" story for an AI ranking layer the PRD itself calls a me-too that lands behind Tinder and Bumble (PRD-AIREC:41-45). Its gates need >=20 swipes of interaction data per user and sustained-message signals -- data with no proven path to exist until the core loop works. The riskiest assumption is named but unowned. **Where it dies:** effort flows to a delighter that is worse than incumbents on day one and whose data precondition may never materialize at scale, while the must-be (reliable chat that yields 7-day conversations) carries the real value. **Rewrite it, do not make me say it twice:** keep it could/later, add a go/no-go gate (do not start PRD-AIREC until PRD-CHAT shows real volume of sustained 7-day conversations to train on), and re-anchor the "so that" to sustained connection, not match count.

### Tech

- **[blocker][tech] PRD-CHAT-E1-S3:18** -- Both ACs are pure vibes: line 18 says the experience "must be smooth" (mượt mà), line 19 says the UI "displays quickly and does not lag." Not one number. No frame rate, no render time, no jank threshold. There is nothing here a test author can assert against -- this AC is fucking useless on a bench. **Where it breaks:** the sprint can be neither accepted nor rejected on this story, so it ships with the bar "interpreted" by whoever happens to demo it, and no engineer can size effort toward an undefined quality. **Rewrite it, do not make me say it twice:** make both measurable Given-When-Then -- e.g. "Given scrolling the message list, when 100 consecutive frames render, then <5% drop below 60fps on a mid-range Android (e.g. Redmi Note)"; "Given the conversation opens, when the first 50 messages load, then time-to-interactive <= 1.5s at p95 on 4G." Pin the test device + network profile in story frontmatter as a fixture.

- **[major][tech] PRD-SAFETY-E1-S1:18** -- A must-have face-verification story demanding liveness + face-match at >=90% confidence (lines 18, 20) within 60s, with no `depends_on` for a face-comparison or liveness service anywhere -- not the story, not PRD-SAFETY-E1, not PRD-SAFETY. Line 71 defers only the government-API piece; the liveness face-match is left hanging with no vendor, SDK, or in-house service named. **Wrecked because:** the story silently assumes a face-matching pipeline that does not exist, so the team either discovers mid-sprint that vendor selection, procurement, and integration are a whole project (scope explosion), or stubs it and ships unverified. The 90% threshold also cannot be validated without a labeled test set, mentioned nowhere. **Rewrite it, do not make me say it twice:** add `depends_on: [FACE-MATCH-SERVICE]` to the story + PRD-SAFETY frontmatter, add a spike ("evaluate + select a liveness/face-comparison vendor, define integration contract + SLA"), and add an NFR AC requiring documented precision/recall at the 90% threshold against a labeled test set before the story is estimable.

- **[minor][tech] PRD-EVENTS-E1-S2:18** -- Seat-reservation specifies decrement-by-1 on booking (line 18) and increment-by-1 on cancel (line 21) but has no AC for the concurrent case: two users both hit "Giữ chỗ" (hold seat) on the last seat, both read a positive remaining-count, both decrement, oversell. Happy-path AC never distinguishes optimistic-read from post-commit. **Where it breaks:** with no concurrency AC the build defaults to a naive lock-free decrement, oversell surfaces only in load testing or at a live event, and the post-launch fix needs a schema change or advisory lock -- much more expensive. **Rewrite it, do not make me say it twice:** add "Given two users simultaneously book the last seat, when both are processed, then exactly one is confirmed and the other gets seat-unavailable; final count is 0, negative capacity impossible," plus a note that the implementation must use an atomic decrement or row-level lock (SELECT FOR UPDATE / compare-and-swap).

### Market

- **[major][market] BRD:42** -- The BRD rates COMP-FIKA threat: low. Fika already runs mandatory manual identity verification (~40% rejection), 16-personality-type matching, values dealbreakers, and IRL events in Vietnam as core *free-tier* features, and its stated positioning -- authentic connection over match count -- is literally yours. PRD-SAFETY claims competitive_parity ahead of COMP-HEN on verification yet omits Fika from the parity table entirely. **Where it dies:** if Fika is underweighted, your safety-first verification moat and "authentic connection" positioning are far more contested than the BRD admits, and a later entrant with the same pitch but without Fika's head-start in verification rigor faces a harder acquisition story for the exact P-URBAN women Fika already owns. **Rewrite it, do not make me say it twice:** re-rate COMP-FIKA to med/high for PRD-SAFETY, add it to the competitive_parity table with an honest behind/parity assessment, and foreground the thing Fika actually lacks -- national scope for P-PROVINCE and P-RETURNEE -- as the differentiator instead of verification. Source: https://vietcetera.com/en/fika-asias-first-female-focused-ai-social-and-dating-app-raises-16m-in-seed-funding

- **[major][market] BRD:56** -- BRD-G1 targets 100k MAU in Year 1 on a swipe mechanic (PRD-MATCH) functionally identical to Tinder/Bumble, with no JTBD-competition analysis for P-PROVINCE. The real alternative for thin-pool province users is not Tinder -- it is Facebook groups, Zalo, or natural introduction. The BRD admits the thin-pool risk but never says why a P-PROVINCE user installs and stays long enough to reach a first match when the swipe stack is near-empty at launch. **Where it dies:** with no cold-start strategy for the provinces, 100k MAU silently rides on P-URBAN density in Hanoi/HCM where Tinder is already the #1 dating app on Google Play Vietnam -- if P-PROVINCE never activates, the national positioning collapses into a HN/HCM-only app fighting Tinder head-on with no moat, and the 7-day north-star is unreachable if users churn before a first match. **Rewrite it, do not make me say it twice:** add a JTBD-competition section naming the do-nothing / Zalo / Facebook-groups alternatives for P-PROVINCE and a cold-start tactic (geographic seeding, invite incentives, or a minimum-viable-pool threshold that surfaces an interest-signal/waitlist flow instead of an empty stack), and tie BRD-G1 to per-persona acquisition assumptions so the number is falsifiable. Source: https://www.similarweb.com/top-apps/google/vietnam/dating/

- **[minor][market] PRD-EVENTS:44** -- PRD-EVENTS is correctly scoped out, but frames offline events purely as internal gold-plating risk and misses that COMP-FIKA (rated threat: low) already runs IRL events as core positioning -- its App Store title is literally "Fika: Matchmaker & IRL Events" (2025-2026). Events are a competitive battleground, not just an internal scope worry. **Where it dies:** dismissing events as gold-plating with no awareness that a competitor uses them as a retention/acquisition hook leaves a strategic blind spot and no re-evaluation trigger if IRL events prove to drive retention in Vietnam. **Rewrite it, do not make me say it twice:** keep scope:out, but add a competitive note that COMP-FIKA competes on IRL events, add a re-evaluation trigger (if Fika's events show measurable retention lift in public signals within 12 months, escalate events from later to next), and reconsider COMP-FIKA's threat rating. Source: https://apps.apple.com/us/app/fika-matchmaker-irl-events/id1528449006

### Craft

This is the part that genuinely pisses me off: five separate "fill in a number later" placeholders dressed up as a finished spec. Every one of them is the same lazy shorthand, and not one of you typed the number.

- **[major][craft] PRD-CHAT:70** -- NFR says "Độ trễ gửi tin nhắn thấp" (low message delay) with no number. "Thấp" (low) is an unmeasurable comparative -- this NFR is empty as hell. **Wrecked because:** the team cannot verify "low" objectively (is 500ms low? 1s? 2s?), so acceptance becomes subjective and you ship straight into an unmet-expectations fight between PO and dev. **Rewrite it, do not make me say it twice:** concrete SLA -- "Độ trễ gửi tin nhắn tối đa dưới 2 giây trên kết nối 3G tiêu chuẩn Việt Nam" or a percentile target (p95 < 1.5s).

- **[major][craft] PRD-PREMIUM:50-51,85** -- Line 85: "Hạn mức miễn phí phải đủ rộng để trải nghiệm lõi còn dùng được mà không trả phí." "Đủ rộng" (sufficiently broad) is a vague comparative -- broad how? 10 likes/day? 20? for how long? **Wrecked because:** with no floor the team guesses; a tight limit churns users before they feel core value (a BRD anti-goal), a loose one never pushes conversion, and the spec asserts a constraint while outsourcing its enforcement to a coin flip. **Rewrite it, do not make me say it twice:** specify the floor -- e.g. "Hạn mức miễn phí tối thiểu: 20 lượt thích/ngày, khám phá không giới hạn, ghép đôi + nhắn tin miễn phí khi đã match," and measure "đủ rộng" by a retention metric.

- **[major][craft] PRD-AIREC:37-38,39,50** -- "phù hợp hơn" (more suitable) and "thông minh hơn" (smarter) with no metric (lines 37, 39). Subjective quality claims, nothing behind them. **Wrecked because:** the team cannot put "more fitting" or "smarter" into an AC -- fitting by what measure? smarter how? -- so the feature is unmeasurable and success becomes opinion. **Rewrite it, do not make me say it twice:** explicit metric -- "hồ sơ có khả năng cao dẫn tới match chuyển thành nhắn tin duy trì (tỉ lệ match->7-day-conversation >= 15%)" and rank by match-to-sustained-chat, not raw match count.

- **[major][craft] PRD-SAFETY-E1-S1:20,36** -- Uses the English term "liveness" (lines 20, 36) in a Vietnamese spec with no translation or definition. **Wrecked because:** anyone unfamiliar with biometrics may read "liveness" as "being live/online"; the spec is bilingual by accident, not design, forcing readers to guess. **Rewrite it, do not make me say it twice:** define once in parent PRD-SAFETY -- "Liveness = xác minh người sống (phát hiện video/hình ảnh giả) qua nhận dạng động tác selfie" -- then use the Vietnamese term, or pair "liveness (xác minh người sống)" on first mention per artifact.

- **[major][craft] PRD-CHAT:33,54** -- "realtime" used inconsistently: once as "realtime" (line 33), once as "theo thời gian thực" (line 54), switching languages in one artifact with no convention. **Wrecked because:** terminology drift creates friction for translation, localization QA, and cross-language readers; the spec reads hastily stitched rather than deliberately bilingual. **Rewrite it, do not make me say it twice:** pick one -- Vietnamese "theo thời gian thực" throughout, or "theo thời gian thực (realtime)" on first mention then Vietnamese only -- and document the choice in a glossary at the top of VISION or PRODUCT.

## Repeat offenders

none (no prior reports).

## Worth recording as a decision (DEC-worthy)

- **BRD-G2:57** -- redefining the headline persona-engagement goal from `weekly-match-rate` to a north-star conversation metric, and re-pointing PRD-MATCH / PRD-CHAT success to it. Contradicts the metric PRD-MATCH currently optimizes to, record via `--decision`.
- **PRD-MATCH-E1-S2:38 / :21** -- stripping the AI recommendation-lift + "why recommended" scope out of a must story and back to PRD-AIREC. Contradicts the approved PRD-MATCH scope exclusion, record via `--decision`.
- **PRD-PREMIUM-E1-S2:34** -- either reframe boost away from reach-for-pay or formally accept the north-star tension. A binding positioning ruling, record via `--decision`.
- **BRD:22** -- committing PRD-PREMIUM to a concrete pricing tier + conversion target, or revisiting its `horizon:later`. Binding revenue/scope ruling, record via `--decision`.
