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
level: 7
register:
  dialect: bac
  gender: m
  profanity: strong
---
# Critique: all · level 7 · lenses: product, tech, market, craft

> Severity tally: blocker 4 · major 12 · minor 4

## Top 3: fix now

1. **[blocker][product] BRD-G2:57** -- You wrote a vision that swears off match count as a vanity metric (VISION:51-52), then made the one persona-engagement goal `weekly-match-rate`, a raw match-count number, and pointed PRD-MATCH straight at it (PRD-MATCH:15,72). I will be blunt: whoever owns this spec does not yet think through what a metric does to a team. Teams build to the number they are graded on. The headline goal counts matches, so the build will optimize swipe-to-match volume and reproduce the "millions of dead matches" the vision was founded to escape, while the 7-day-conversation north-star is owned by no goal at all. You will ship the competitor you set out to beat. Fix it: add or replace a BRD goal that measures the north-star directly (% of matches that become a sustained 7+ day conversation), re-point PRD-MATCH / PRD-CHAT success metrics to it, and keep `weekly-match-rate` only as a leading funnel indicator. **[DEC-worthy]**

2. **[blocker][tech] PRD-CHAT-E1-S4:18** -- Two ACs that promise the world and define nothing: line 18 says conversations must be "absolutely safe" and line 19 says the system must "completely protect" users, on a story tagged `should` / size:M. No threat, no detection, no response, no SLA. Naming an unbounded guarantee is not the same as engineering one, and a product person should know the difference. The story cannot be tested, sized, or accepted. Any build trivially claims compliance, and the day a safety incident lands post-launch, the vacuously-true AC becomes the thing that blocks release. Fix it: split into discrete testable stories, one mechanism per dimension, e.g. "Given A blocks B, when B sends a message, then the server rejects it with 403 and stores nothing", and an encryption AC verifiable by server-side log inspection. Retire the current story.

3. **[blocker][market] BRD:22** -- BRD-G3 wants premium revenue to hit operational break-even by Year 2, and the goal body is empty. No price tier, no conversion target, no ARPU floor. Vietnam dating-services ARPU is roughly USD 8.15/user/year (Statista 2025); at 100k MAU and a 2-5% freemium conversion, that is USD 16k-40k a year, which does not credibly cover real-time messaging (PRD-CHAT) plus a human safety-review queue (PRD-SAFETY). A break-even goal with no math behind it is a wish wearing a target's clothes. Nobody can validate whether view-who-liked-me and boost generate enough to break even, so the Year 2 goal is unverifiable and the investment case for PRD-PREMIUM is unsupported. Fix it: add to BRD-G3 / PRD-PREMIUM a VND monthly price anchored to the market (Tinder Gold ~149k-199k VND/mo), a 3-6% conversion target, and a derived annual-revenue figure compared against projected Year 2 opex. If the math does not close, revisit `horizon:later` on PRD-PREMIUM or specify a secondary revenue stream. Source: https://www.statista.com/outlook/emo/dating-services/vietnam **[DEC-worthy]**

## By lens

### Product

- **[blocker] BRD-G2:57** -- see Top 3 #1. The north-star goal is unowned; the persona-success goal counts matches. **[DEC-worthy]**

- **[major] PRD-EVENTS-E1-S3:18** -- A fully drafted story to organize and sell tickets to nationwide concerts, line-ups, multi-tier ticketing, QR check-in, genre filters, inside a dating app. None of the three personas hired you to sell concert tickets, no BRD goal maps to it, and the PRD itself labels it gold-plating (PRD-EVENTS-E1-S3:43). A product owner who fully specs an entire second business with acceptance criteria is not setting priorities. An AC-complete story reads as a real build candidate; it is a separate business (artist ops, venue security, ticket fraud) with zero line to the north-star, and chasing it splits the team off a core loop that is not yet proven. Fix it: delete the story, or demote it to a one-line idea in a parking-lot doc, not an authored AC-complete artifact.

- **[major] PRD-MATCH-E1-S2:38** -- PRD-MATCH's scope explicitly excludes AI recommendations and "why recommended", deferring them to PRD-AIREC next cycle (PRD-MATCH:64; PRD-AIREC:77). Then this must / core-value story smuggles both back in: a recommender that beats random by >=20% at p<0.05 (line 38) and a "why recommended this person?" explanation (line 22). You cannot defer a capability in one breath and require it in the next; that is not scope discipline, it is wishful drafting. The team either over-builds an ML recommender to clear an A/B gate that cannot pass on a cold-start base, or quietly drops the AC. Both rot the spec's credibility and blow now-cycle scope. Fix it: strip the lift A/B criterion and the "why recommended" AC; keep S2 to deterministic hard-filter quality (age/distance/intent, active-profile freshness). Move ranking and explanation to PRD-AIREC where they already live. **[DEC-worthy]**

- **[major] PRD-PREMIUM-E1-S2:34** -- A paid "boost" that buys 30 minutes of extra visibility. The thing being sold is raw exposure, the volume game the vision positions against, and PRD-PREMIUM's own risk register flags that paid features erode the free experience, yet it ships boost as a `should` anyway. Selling the exact dynamic your brand rejects is a thinking gap, not a revenue strategy. Boost rewards paying users with reach instead of sustained conversation; it can lift ARPU short-term while pulling the product off the one differentiator it was built on. Fix it: reframe the premium gain around the core value (surface-to-verified-serious-users, not raw reach), or record an explicit PO decision accepting the north-star tension. Do not ship a reach-for-pay mechanic as an unexamined `should`. **[DEC-worthy]**

- **[minor] PRD-AIREC-E1-S1:30** -- A "so that I create more matches per week" story for an AI ranking layer the PRD itself calls a me-too feature that lands behind Tinder and Bumble (PRD-AIREC:41-45). Its gates need >=20 swipes/user and sustained-message signals, data the product has no proven path to until the core loop works. Effort goes to a delighter that is worse than incumbents on day one and whose data precondition may never arrive, while the must-be (reliable chat that produces 7-day conversations) carries the real value. Fix it: keep it `could`/later, add an explicit go/no-go gate (do not start PRD-AIREC until PRD-CHAT shows measurable 7-day conversations to train on), and re-anchor the "so that" to sustained connection, not match count.

### Tech

- **[blocker] PRD-CHAT-E1-S4:18** -- see Top 3 #2. Unbounded "absolutely safe" / "completely protect" guarantees with no mechanism, untestable and unsizeable.

- **[blocker] PRD-CHAT-E1-S3:18** -- Both ACs are pure sensation: line 18 says it "must be smooth", line 19 says the UI "displays quickly and does not lag". Not one numeric observable, frame rate, render time, jank threshold, nothing that produces a binary pass/fail. A spec author who hands QA a feeling and calls it acceptance has not done the job. A test author has nothing to assert against; the story ships with its AC permanently "interpreted" by whoever runs the demo, and an engineer cannot size an undefined quality bar. Fix it: measurable Given-When-Then, e.g. "when 100 consecutive frames render, fewer than 5% drop below 60 fps on a mid-range Android (Redmi Note)" and "when the first 50 messages load, time-to-interactive <= 1.5s at p95 on 4G". Add the test device and network profile to the story frontmatter.

- **[major] PRD-MATCH-E1-S2:21** -- One AC requires a statistically significant A/B outcome: recommended-profile match-rate >=20% above a random control at p<0.05. A/B significance takes weeks to months of live traffic and an analysis pipeline; it is not a sprint-deliverable. (Same underlying defect as the product-lens smuggled-recommender finding; both lenses flagged PRD-MATCH-E1-S2.) The story cannot be accepted at sprint review, it is neither Independent (depends on traffic) nor Estimable ("reach significance" is unsizeable), so it sits in limbo. Fix it: move the A/B outcome to a PRD success metric or a separate experiment epic with its own lifecycle; replace the AC with a pre-launch proxy, e.g. "on a staging dataset with known labels, precision@10 is at least X% above the distance-only baseline".

- **[major] PRD-SAFETY-E1-S1:18** -- A must-have face-verification story mandating liveness + face-match at >=90% confidence within 60s, with no `depends_on` for a face-comparison or liveness service anywhere in the story, the epic, or PRD-SAFETY. PRD-SAFETY:71 defers only government-API verification; the liveness face-match has no vendor, SDK, or in-house service named. The team discovers mid-sprint that vendor selection, procurement, and integration are needed (scope explosion) or stubs it and ships unverified, and the 90% threshold cannot be validated without a labeled test set that is mentioned nowhere. Fix it: add `depends_on: [FACE-MATCH-SERVICE]` to the story and PRD frontmatter, add a vendor-selection spike with an integration contract and SLA, and an NFR AC documenting precision/recall at the 90% threshold on a labeled set, PO-accepted. Until the spike is done, this story cannot be estimated.

- **[minor] PRD-EVENTS-E1-S2:18** -- The seat-reservation story specs decrement-on-book and increment-on-cancel but has no AC for concurrent booking: two users hitting "Giu cho" on the last seat can both read a positive count and both decrement, oversell. With no concurrency AC the build defaults to a naive unlocked decrement, the oversell surfaces in load testing or at a live event, and the post-launch fix (schema change or advisory lock) is far more expensive. Fix it: add "Given two users simultaneously book the last seat, exactly one gets a confirmation, the other a seat-unavailable error, final count 0, no negative capacity", and a note that the implementation must use an atomic decrement or row-level lock.

### Market

- **[blocker] BRD:22** -- see Top 3 #3. BRD-G3 break-even goal with empty body, no price, conversion, or ARPU floor; market math does not close. Source: https://www.statista.com/outlook/emo/dating-services/vietnam **[DEC-worthy]**

- **[major] BRD:42** -- The BRD rates COMP-FIKA threat:low. Fika already runs mandatory manual identity verification (~40% rejection), a 16-personality-type matching layer, values dealbreakers, and IRL events in Vietnam as core free-tier features, and its stated positioning, "authentic connection", is your stated primary differentiator. Fika is absent from PRD-SAFETY's competitive_parity table entirely. Calling your closest positioning rival "low" is not a competitive assessment, it is hoping it goes away. If Fika is underweighted, your safety-first verification moat and "authentic connection" positioning are more contested than the BRD admits, and a later entrant with the same positioning but without Fika's head-start faces a harder acquisition story, especially for P-URBAN women who are Fika's core audience. Fix it: re-rate COMP-FIKA to med/high for PRD-SAFETY and the positioning, add it to the competitive_parity table with an honest "parity or behind on manual-verification rigor", and foreground what Fika lacks, national scope for P-PROVINCE and P-RETURNEE, as the real differentiator. Source: https://vietcetera.com/en/fika-asias-first-female-focused-ai-social-and-dating-app-raises-16m-in-seed-funding **[DEC-worthy]**

- **[major] BRD:56** -- BRD-G1 targets 100k MAU in Year 1 on a swipe-discovery mechanic functionally identical to Tinder/Bumble, with no JTBD-competition for P-PROVINCE (thin local pools), whose real alternative is Facebook groups, Zalo, or natural introduction, not Tinder. The spec acknowledges the thin-pool risk but never says why a province user installs and stays through a nearly empty swipe stack. With no cold-start strategy the 100k goal silently leans on P-URBAN density in Hanoi/HCM, where Tinder already ranks #1 on Google Play Vietnam; if P-PROVINCE fails to activate, the national positioning collapses into a HN/HCM-only app fighting Tinder with no moat, and the 7-day north-star is unreachable if users churn before a first match. Fix it: add a JTBD-competition section naming the do-nothing and Zalo/Facebook-groups alternatives, specify a cold-start tactic (geographic seeding, invite incentives, or a minimum-viable-pool threshold that surfaces an interest-signal/waiting-list flow instead of an empty stack), and tie 100k MAU to per-persona acquisition assumptions so the figure is falsifiable. Source: https://www.similarweb.com/top-apps/google/vietnam/dating/

- **[minor] PRD-EVENTS:44** -- PRD-EVENTS scopes out offline events with good rationale but frames them purely as internal gold-plating, missing that COMP-FIKA (rated threat:low) already runs IRL events as core positioning, its App Store title is literally "Fika: Matchmaker & IRL Events". Events are a competitive battleground, not just an internal scope concern. Dismissing events without noting a competitor uses them as a retention and acquisition hook leaves a strategic blind spot with no re-evaluation trigger if IRL events prove to drive retention in Vietnam. Fix it: keep `scope:out` for now but add a competitive note and a re-evaluation trigger (if Fika's events show measurable retention lift in public signals within 12 months, escalate the events horizon later to next), and reconsider COMP-FIKA's threat rating. Source: https://apps.apple.com/us/app/fika-matchmaker-irl-events/id1528449006

### Craft

- **[major] PRD-CHAT:70** -- The NFR "Do tre gui tin nhan thap" (low message delay) ships "thap" with no number. "Low" is an unmeasurable comparative; the team cannot tell 500ms from 2s. With no number, acceptance is subjective and the PO and dev team build a mismatch of expectations into the release. Fix it: a concrete SLA, "do tre gui tin nhan toi da duoi 2 giay tren 3G tieu chuan Viet Nam, goi ~50KB", or a percentile target (p95 < 1.5s).

- **[major] PRD-SAFETY-E1-S1:20,36** -- The ACs drop the English term "liveness" into a Vietnamese spec with no translation or definition. A Vietnamese reader gets "gia mao liveness" and no Vietnamese equivalent. Readers unfamiliar with the biometric term may read it as "being live/online", and the spec is bilingual by accident, forcing a context-switch or a guess. Fix it: define once in parent PRD-SAFETY, "liveness = xac minh nguoi song (phat hien video/hinh anh gia) qua nhan dang dong tac selfie", then use the Vietnamese term, or pair "liveness (xac minh nguoi song)" on first mention per artifact.

- **[major] PRD-AIREC:37-38,39,50** -- "phu hop hon" (more suitable) and "thong minh hon" (smarter) used as quality claims with no metric, e.g. "uu tien nhung ho so co kha nang dan toi ket noi phu hop hon" (line 37), "mot thu tu goi y thong minh hon" (line 39). Subjective comparatives are not acceptance criteria. The team cannot define "more fitting" or "smarter" in an AC, so success becomes opinion. Fix it: explicit metrics, "ho so co kha nang cao dan toi match chuyen thanh nhan tin duy tri (ti le match->7-day-conversation >= 15%)" and "thu tu goi y toi uu hoa theo ti le match-to-sustained-chat, khong theo so match tho".

- **[major] PRD-CHAT:33,54** -- "realtime" used inconsistently in one artifact: once as "realtime" (Latin), once as "theo thoi gian thuc" (Vietnamese), no convention, no explanation. Terminology drift across the spec creates friction for translation, localization QA, and cross-language readers, and the spec reads hastily stitched rather than deliberately bilingual. Fix it: pick one, either "theo thoi gian thuc" throughout PRD-CHAT and child stories, or "theo thoi gian thuc (realtime)" on first mention then Vietnamese only, and document the choice in a spec glossary at the top of VISION or PRODUCT.

- **[major] PRD-PREMIUM:50-51,85** -- NFR line 85: "Han muc mien phi phai du rong de trai nghiem loi con dung duoc ma khong tra phi." "Du rong" (sufficiently broad) is a vague comparative, 10 likes/day, 20, for how long? With no floor the team guesses; a tight limit churns users before they feel core value (a BRD anti-goal), a loose one fails to push conversion, and the constraint's enforcement is left to interpretation. Fix it: specify the floor, "han muc mien phi toi thieu: 20 luot thich/ngay, kham pha khong gioi han, ghep doi + nhan tin mien phi khi da match; nguoi dung moi nhan 48 gio thu premium", and measure "du rong" by a retention metric.

## Repeat offenders

None -- no prior critique reports for this scope.

## Worth recording as a decision (DEC-worthy)

- **BRD-G2:57** -- the persona-success goal (`weekly-match-rate`) contradicts the vision's stated north-star (VISION:51-52, sustained 7-day conversation over match count). This is a binding metric-ownership ruling the PO should record: which goal owns the north-star, and whether match-rate stays only as a funnel indicator. Touches the `approved` vision positioning, so it needs Keep / Change+re-approve / Hybrid, not a silent edit.
- **BRD:22** -- recording the premium pricing model, conversion target, and Year-2 break-even math is a binding business decision (pricing, scope-horizon for PRD-PREMIUM); fits the Decision Register.
- **BRD:42** -- the COMP-FIKA threat re-rating and the safety-first positioning call (is "authentic connection" still defensible against Fika's head-start) is a positioning ruling worth recording.
- **PRD-MATCH-E1-S2:38** -- the scope ruling on whether the recommender and "why recommended" stays deferred to PRD-AIREC or moves into the now-cycle directly contradicts PRD-MATCH:64 / PRD-AIREC:77; record which side holds.
- **PRD-PREMIUM-E1-S2:34** -- if the PO chooses to ship reach-for-pay boost despite the north-star tension, that acceptance should be an explicit recorded decision, not an unexamined `should`.
