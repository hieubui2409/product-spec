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
level: 1
---
# Critique: all · level 1 · lenses: product, tech, market, craft

> Severity tally: blocker 3 · major 13 · minor 3

## Top 3: fix now

1. **[blocker][product] BRD-G2:57.** The vision sets sustained 7-day conversations as the north-star and explicitly rejects match count as vanity (VISION:51-52), yet BRD-G2, the only persona-engagement goal, measures `weekly-match-rate` (20% of active users create >=1 match/week), and PRD-MATCH points its success straight at it (PRD-MATCH:15,72). The build is steered one layer below the connection you say you sell. Worth a look: teams build to the metric they are measured on, so a match-count headline goal reproduces the "millions of dead matches" the product was founded to escape, while the 7-day north-star sits unowned by any BRD goal. Maybe try: add or replace a BRD goal that measures the north-star directly (% of matches that become a sustained 7+ day conversation), re-point PRD-MATCH/PRD-CHAT success metrics to it, and keep weekly-match-rate only as a leading funnel indicator.

2. **[blocker][tech] PRD-CHAT-E1-S3:18.** Both ACs describe sensations only: line 18 says the experience "must be smooth," line 19 says the UI "displays quickly and does not lag." Neither carries a numeric observable, so there is nothing that produces a binary pass or fail. Worth a look: a test author has no threshold to assert against and an engineer cannot size an undefined quality bar, so the story ships permanently "interpreted" by whoever demos it. Maybe try: rewrite both as measurable Given-When-Then ACs, e.g. "when 100 consecutive frames render, fewer than 5% drop below 60fps on a mid-range Android (Redmi Note)" and "first 50 messages load with time-to-interactive <=1.5s at p95 on 4G," and add the test device and network profile to the story frontmatter.

3. **[blocker][market] BRD:22.** BRD-G3 targets premium revenue sufficient for Year-2 break-even, but neither it nor PRD-PREMIUM defines a price tier, conversion rate, or ARPU floor, and the BRD-G3 body is empty. At Vietnam dating-services ARPU of ~USD 8.15/user/year (Statista 2025), 100k MAU and a 2-5% freemium conversion lands at ~USD 16k-40k/year, likely short of running real-time messaging (PRD-CHAT) plus a human-review safety queue (PRD-SAFETY). Worth a look: without a pricing model and a Vietnam-grounded conversion target, the Year-2 break-even goal is unverifiable and the PRD-PREMIUM investment case is unsupported. Maybe try: add to BRD-G3 or PRD-PREMIUM a monthly price range in VND (compare Tinder Gold ~149k-199k VND/mo), a 3-6% target conversion, and a derived annual-revenue estimate set against Year-2 operating cost; if the math does not close, revisit the `horizon:later` tag or name a secondary revenue stream. Source: https://www.statista.com/outlook/emo/dating-services/vietnam

## By lens

### Product

- **[major] PRD-EVENTS-E1-S3:18.** This story specs organizing and selling tickets to nationwide concerts inside the app (line-ups, multi-tier ticketing, QR check-in), and none of the three personas is hiring a dating app to buy concert tickets; the PRD itself labels it gold-plating (PRD-EVENTS-E1-S3:43). A fully-specced, AC-complete story signals a real build candidate, and this is a whole separate business (artist ops, venue security, ticket fraud) with no line to the north-star. Delete the story or demote it to a one-line parking-lot idea, not an authored story with acceptance criteria.

- **[major] PRD-MATCH-E1-S2:38 (also tech, PRD-MATCH-E1-S2:21).** PRD-MATCH scopes out AI recommendations and "why recommended" explanations, deferring them to PRD-AIREC next cycle (PRD-MATCH:64; PRD-AIREC:77), yet this must/core-value story requires a recommender beating random by >=20% via A/B test at p<0.05 (line 38/21) and a "why recommended this person?" explanation (line 22), exactly the deferred AIREC capability. A p<0.05 A/B outcome needs weeks to months of live traffic, so the story is neither Independent nor Estimable and sits permanently in limbo at sprint review. Worth a look: the team either over-builds an ML recommender to hit an A/B gate that cannot pass on a cold-start base, or quietly drops the AC; both rot the spec and blow now-cycle scope. Maybe try: strip the recommendation-lift A/B criterion and the "why recommended" AC from S2, keep S2 to deterministic hard-filter quality (age/distance/intent, active-profile freshness), move model ranking and explanation to PRD-AIREC, and re-express any lift target as a PRD success metric or a separate experiment epic with a staging proxy (precision@10 vs the distance-only baseline).

- **[major] PRD-PREMIUM-E1-S2:34.** The paid "boost" sells 30 minutes of extra visibility, i.e. quantity of exposure, which is the volume game the vision positions against; PRD-PREMIUM's own risk register flags that paid features can erode the free experience yet ships boost as a should. Worth a look: boost monetizes the same swipe-volume dynamic the brand claims to reject and rewards reach over sustained conversation, lifting ARPU short-term while pulling away from the one differentiator. Maybe try: reframe the premium gain around the core value (surface-to-verified-serious-users, not raw reach) or explicitly record a PO decision accepting the north-star tension; do not ship a reach-for-pay mechanic as an unexamined should.

- **[minor] PRD-AIREC-E1-S1:30.** This "so that I create more matches per week" story drives an AI ranking layer the PRD itself calls a me-too feature behind Tinder and Bumble (PRD-AIREC:41-45), and its gates need >=20 swipes of interaction data per user plus sustained-message signals the product has no proven path to accumulate. Worth a look: effort goes to a delighter that is worse than incumbents on day one and whose data precondition may never materialize, while the must-be (reliable chat producing 7-day conversations) carries the real value. Maybe try: keep it could/later (already done) but add a go/no-go gate, do not start PRD-AIREC until PRD-CHAT shows a measurable volume of sustained 7-day conversations to train on, and re-anchor the story's "so that" to sustained connection, not match count.

### Tech

- **[blocker] PRD-CHAT-E1-S4:18.** Two ACs are absolute guarantees with no mechanism: line 18 demands conversations be "absolutely safe," line 19 demands the system "completely protect" users, with no threat, detection, response, or SLA named, yet the story is moscow:should, size:M. Worth a look: the story cannot be tested, sized, or accepted; any implementation trivially claims compliance, and it will block release after a safety incident because the AC was always vacuously true. Maybe try: split into discrete testable stories, one mechanism per dimension, e.g. "(a) message stored server-side is encrypted and only decryptable with sender/receiver keys, verified by log inspection; (b) when A blocks B, B's send is rejected 403 and no message is stored."

- **[major] PRD-SAFETY-E1-S1:18.** The face-verification story mandates liveness + face-match at >=90% confidence within 60s (lines 18, 20), yet no `depends_on` for a face-comparison/liveness service exists in the story, the epic, or PRD-SAFETY; line 71 defers only government-API verification. Worth a look: without a named service the team discovers mid-sprint that vendor selection, procurement, and integration are required (scope blowout), or stubs it and ships unverified, and the 90% threshold cannot be validated without a labeled test set that appears nowhere. Maybe try: add `depends_on: [FACE-MATCH-SERVICE]` to the story and PRD-SAFETY frontmatter, add a vendor-selection spike defining the integration contract and SLA, and add an NFR AC documenting precision/recall at the 90% threshold against a labeled test set, accepted by the PO.

- **[minor] PRD-EVENTS-E1-S2:18.** The seat-reservation story specs decrement-on-book (line 18) and increment-on-cancel (line 21) but has no AC for concurrent booking, so two users hitting the last seat can both read positive remaining-count and both decrement (oversell). Worth a look: the implementation defaults to a naive unlocked decrement, oversell surfaces only in load testing or at a live event, and a post-launch fix needs a schema change or advisory lock. Maybe try: add an AC, "when two users simultaneously book the last seat, exactly one gets confirmation, the other a seat-unavailable error, final remaining count 0, no negative capacity," and note the implementation must use an atomic decrement or row-level lock.

### Market

- **[major] BRD:42.** The BRD rates COMP-FIKA threat:low, but Fika already runs mandatory manual identity verification (~40% rejection), a 16-personality matching layer, values dealbreakers, and IRL events in Vietnam as core free-tier features, and is absent from PRD-SAFETY's competitive_parity table; Fika's stated positioning is also your "authentic connection, not match count." Worth a look: if Fika is underweighted, the safety-first verification moat and the authentic-connection positioning are more contested than the BRD admits, and a later entrant without Fika's head-start faces a harder acquisition story for the same P-URBAN women. Maybe try: re-rate COMP-FIKA to med/high for PRD-SAFETY, add it to competitive_parity with an honest verification assessment, and foreground what Fika lacks, national scope for P-PROVINCE and P-RETURNEE, as the real differentiator instead of identity verification. Source: https://vietcetera.com/en/fika-asias-first-female-focused-ai-social-and-dating-app-raises-16m-in-seed-funding

- **[major] BRD:56.** BRD-G1 targets 100k MAU in Year 1 on a swipe mechanic functionally identical to Tinder/Bumble, and the spec never addresses JTBD-competition for P-PROVINCE (thin local pools), whose real alternative is Facebook groups, Zalo, or natural introduction, not Tinder; the thin-pool risk is acknowledged but the activation question is not. Worth a look: without a cold-start strategy for the provinces, 100k MAU rides implicitly on P-URBAN density in Hanoi/HCM where Tinder is already top-ranked, and the national positioning collapses into a Hanoi/HCM-only Tinder clone with no moat. Maybe try: add a JTBD-competition section to BRD or PRD-MATCH naming the do-nothing and Zalo/Facebook alternatives, specify a cold-start tactic (geographic seeding, invite incentives, or a minimum-viable-pool threshold that surfaces an interest-signal/waiting-list flow instead of an empty swipe stack), and tie BRD-G1 to per-persona acquisition assumptions so it is falsifiable. Source: https://www.similarweb.com/top-apps/google/vietnam/dating/

- **[minor] PRD-EVENTS:44.** PRD-EVENTS is correctly scoped out, but it frames offline events purely as internal gold-plating while COMP-FIKA (rated threat:low) runs IRL events as core positioning; Fika's App Store title is literally "Fika: Matchmaker & IRL Events." Worth a look: dismissing events without noting a competitor uses them as a retention/acquisition hook leaves a strategic blind spot with no re-evaluation trigger. Maybe try: add a competitive note to the PRD-EVENTS risk section, keep scope:out for now, and add a trigger, if Fika's events show measurable retention lift in public signals within 12 months, escalate the events horizon from later to next and reconsider COMP-FIKA's rating. Source: https://apps.apple.com/us/app/fika-matchmaker-irl-events/id1528449006

### Craft

- **[major] PRD-CHAT:70.** The NFR says "Do tre gui tin nhan thap" (low message delay) with no number; "thap" is an unmeasurable comparative. Worth a look: the team cannot verify "low" objectively (is 500ms low? 1s? 2s?), so acceptance becomes subjective and expectations drift between PO and dev. Maybe try: set a concrete SLA, e.g. "do tre gui tin nhan toi da duoi 2 giay tren 3G tieu chuan Viet Nam" or a percentile target p95 < 1.5s.

- **[major] PRD-SAFETY-E1-S1:20,36.** The ACs use the English term "liveness" in a Vietnamese spec with no translation or definition. Worth a look: readers unfamiliar with biometric jargon may misread "liveness" as "being live/online," and the spec ends up bilingual by accident, forcing a guess. Maybe try: define once in PRD-SAFETY ("Liveness = xac minh nguoi song, phat hien video/hinh anh gia qua nhan dang dong tac selfie") then use the Vietnamese term, or pair "liveness (xac minh nguoi song)" on first mention per artifact.

- **[major] PRD-AIREC:37-38,39,50.** The PRD uses "phu hop hon" (more suitable) and "thong minh hon" (smarter) with no metric, e.g. "uu tien nhung ho so co kha nang dan toi ket noi phu hop hon" and "mot thu tu goi y thong minh hon." Worth a look: the team cannot put "more fitting" or "smarter" into an AC, so the feature is unmeasurable and success becomes opinion. Maybe try: rewrite with explicit metrics, e.g. "ho so co kha nang cao dan toi match chuyen thanh nhan tin duy tri (match->7-day-conversation >= 15%)" and "thu tu toi uu theo ti le match-to-sustained-chat, khong theo so match tho."

- **[major] PRD-CHAT:33,54.** "Realtime" appears inconsistently in one artifact, once as "realtime" (Latin) and once as "theo thoi gian thuc," with no convention set. Worth a look: terminology drift adds friction for localization QA and cross-language readers and makes the spec read hastily stitched rather than deliberately bilingual. Maybe try: pick one, either Vietnamese "theo thoi gian thuc" throughout, or a bilingual convention ("theo thoi gian thuc (realtime)" on first mention, then Vietnamese), and record the choice in a glossary at the top of VISION or PRODUCT.

- **[major] PRD-PREMIUM:50-51,85.** The NFR says the free tier must be "du rong" (sufficiently broad) to keep the core experience usable unpaid; "du rong" is a vague comparative (10 likes/day? 20? for how long?). Worth a look: without a floor the team guesses, a tight limit churns users before they feel core value (a BRD anti-goal), a loose one fails to push conversion. Maybe try: specify the floor, e.g. "toi thieu 20 luot thich/ngay, kham pha khong gioi han, ghep doi + nhan tin mien phi khi da match, 48 gio thu premium cho nguoi moi," then bind "du rong" to a retention metric.

## Repeat offenders

None -- no prior reports supplied.

## Worth recording as a decision (DEC-worthy)

- **BRD-G2:57 (north-star metric)** -- re-pointing the persona-success goal away from `weekly-match-rate` is a binding metric/priority ruling and contradicts the metric PRD-MATCH already optimizes to; record the chosen north-star metric via `--decision`.
- **PRD-PREMIUM-E1-S2:34 (boost vs north-star)** -- shipping a reach-for-pay mechanic against the stated quality-over-quantity positioning is a positioning trade-off the PO should record (accept the tension or reframe the gain).
- **PRD-MATCH-E1-S2 (deferred AIREC smuggled into a now/must story)** -- pulling the recommender and "why recommended" back to PRD-AIREC is a scope ruling that contradicts the now-cycle must designation; record the scope boundary.
