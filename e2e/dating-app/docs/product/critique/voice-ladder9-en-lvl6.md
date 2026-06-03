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
level: 6
---
# Critique: all · level 6 · lenses: product, tech, market, craft

> Severity tally: blocker 3 · major 11 · minor 3

Twenty-one findings across four lenses, three of them sharing the same heartbeat: this spec keeps measuring matches while claiming it sells conversation. Whoever wrote it clearly read their own vision once, nodded approvingly, and then wrote the exact opposite into every goal and metric. Buckle up.

## Top 3: fix now

1. **[blocker][product] BRD-G2:57.** The vision plants its flag on sustained 7-day conversations and openly spits on match count as a vanity metric (VISION:51-52). Then the only persona-engagement goal, BRD-G2, measures `weekly-match-rate` -- raw match count -- and PRD-MATCH wires its success straight to it (PRD-MATCH:15,72). You wrote the anti-goal as the headline goal and didn't even flinch. The north-star you bragged about is owned by exactly nobody. **Why it's done for:** teams build to the metric on the scoreboard. Measure matches and the team ships swipe volume, which rebuilds the "millions of dead matches" graveyard the product was founded to escape. You will ship the competitor you set out to beat. **Just retype it:** add or swap in a BRD goal that measures the north-star directly (% of matches reaching a sustained 7+ day conversation), re-point PRD-MATCH / PRD-CHAT success to it, and demote `weekly-match-rate` to a leading funnel indicator, not the persona-success goal.

2. **[blocker][tech] PRD-CHAT-E1-S3:18 + PRD-CHAT-E1-S4:18.** Two safety/perf stories built entirely out of feelings. S3 says the experience "must be smooth" and "displays quickly and does not lag" -- zero numbers. S4 promises conversations are "absolutely safe" and the system "completely protects" users -- no threat named, no mechanism, no SLA, on a `should`/size-M story. This is what a spec looks like when someone wanted the warm glow of having written it without doing any of the thinking. **Why it's done for:** a test author has nothing to assert against. The sprint can never be accepted or rejected; "done" becomes whatever whoever runs the demo decides, and the vacuously-true safety AC turns into a liability the day a real incident lands. **Just retype it:** replace S3 with measurable Given-When-Then (e.g., "<5% of 100 consecutive frames drop below 60fps on a mid-range Android"; "first 50 messages reach time-to-interactive <=1.5s at p95 on 4G", plus a reference device in frontmatter). Split S4 into one-mechanism-per-dimension stories (encryption AC, block-enforcement AC with a 403), and retire the absolute-guarantee wording.

3. **[blocker][market] BRD:22.** BRD-G3 wants premium revenue at operational break-even by Year 2, and the BRD-G3 body is literally empty -- no price tier, no conversion target, no ARPU floor. Run the actual numbers: Vietnam dating-services ARPU ~USD 8.15/user/yr (Statista 2025), 100k MAU, 2-5% freemium conversion, that's ~USD 16k-40k/yr, which does not cover real-time messaging plus a human safety-review queue. You set a break-even goal and forgot to check whether it breaks even. **Why it's done for:** with no pricing model or grounded conversion target, BRD-G3 is a wish, and the whole investment case for PRD-PREMIUM (view-who-liked-me, boost) sits on air -- unverifiable by design. **Just retype it:** add a VND subscription range anchored to the market (Tinder Gold ~149k-199k VND/mo), a target conversion band (3-6% of MAU), and a derived annual-revenue figure compared against Year-2 opex. If the math doesn't close, revisit PRD-PREMIUM's horizon or specify a second revenue stream. Source: https://www.statista.com/outlook/emo/dating-services/vietnam

## By lens

### Product

- **[major] PRD-EVENTS-E1-S3:18.** A fully-authored, AC-complete story for organizing and ticketing nationwide concerts (line-ups, multi-tier tickets, QR check-in) inside a dating app. None of the three personas hired you to sell concert tickets, and the PRD itself labels it gold-plating (PRD-EVENTS-E1-S3:43) -- so you knew, and you wrote the whole thing out anyway. **Why it's done for:** a fully-specified story signals a real build candidate; this is an entire separate business (artist ops, venue security, ticket fraud) with no line to the north-star, and it pulls the team off the unproven core loop. **Just retype it:** delete the story or demote it to a one-line parking-lot idea. Never carry an out-of-scope, persona-less feature as a drafted AC-complete artifact.

- **[major] PRD-MATCH-E1-S2:38 (also flagged by tech, PRD-MATCH-E1-S2:21).** A `must` / core-value story that smuggles in the explicitly-deferred AIREC capability: a recommendation engine beating random control by >=20% via A/B test at p<0.05, plus a "why recommended this person?" explanation -- exactly what PRD-MATCH:64 and PRD-AIREC:77 said you would NOT build this cycle. Tech adds: p<0.05 takes weeks to months of live traffic, so the story is neither Independent nor Estimable and lives in permanent limbo. **Why it's done for:** the team either over-builds an ML recommender to clear an A/B gate that can't pass on a cold-start userbase, or quietly drops the AC. Both rot the spec and blow now-cycle scope. **Just retype it:** strip the A/B-lift criterion and the "why recommended" AC from S2; keep S2 to deterministic hard-filter quality (age/distance/intent/freshness). Move model ranking and explanation to PRD-AIREC where they already live, and relocate any A/B outcome to a PRD success metric or a separate experiment epic.

- **[major] PRD-PREMIUM-E1-S2:34.** Paid "boost" sells 30 minutes of extra visibility -- quantity of exposure, the exact volume game the vision positions against. PRD-PREMIUM's own risk register warns paid features erode the free experience, and you shipped it as a `should` revenue feature regardless. **Why it's done for:** boost monetizes the swipe-volume dynamic the brand claims to reject and rewards paying for reach instead of sustained conversation; it can bump ARPU while dragging the product off its one differentiator. **Just retype it:** reframe the premium gain around the core value (surface-to-verified-serious-users, not raw reach), or record an explicit PO decision accepting the north-star tension. Do not ship reach-for-pay as an unexamined `should`.

- **[minor] PRD-AIREC-E1-S1:30.** A "so that I create more matches per week" story for an AI ranking layer the PRD itself calls a me-too feature landing behind Tinder and Bumble (PRD-AIREC:41-45). Its gates need >=20 swipes/user and sustained-message data the product has no proven path to accumulate, and that riskiest assumption is named but unowned. **Why it's done for:** effort flows to a delighter that's worse than incumbents on day one and whose data precondition may never arrive, while the real must-be -- reliable chat producing 7-day conversations -- carries the actual value. **Just retype it:** keep it could/later and add a go/no-go gate: don't start PRD-AIREC until PRD-CHAT shows real volume of sustained 7-day conversations to train on, and re-anchor the story's "so that" to sustained connection, not match count.

### Tech

- **[major] PRD-SAFETY-E1-S1:18.** Face-verification mandates liveness + face-match at >=90% confidence in 60s, yet no `depends_on` for a face-comparison or liveness service exists in the story, the epic, or PRD-SAFETY (which defers only government-API verification at line 71). A `must` resting on a pipeline nobody admitted needs building. **Why it's done for:** the team discovers mid-sprint that vendor selection, procurement, and integration are all required (scope explosion), or stubs it and ships unverified -- and the 90% threshold can't be validated without a labeled test set that appears nowhere. **Just retype it:** add `depends_on: [FACE-MATCH-SERVICE]` to the story and PRD frontmatter, add a vendor-selection spike defining contract and SLA, and add an NFR AC documenting precision/recall at the 90% threshold against a labeled set, accepted by the PO.

- **[minor] PRD-EVENTS-E1-S2:18.** Seat reservation specifies decrement-on-book and increment-on-cancel but has no concurrency AC: two users hitting "Giu cho" on the last seat can both read positive stock and both decrement -- oversell. **Why it's done for:** with no concurrency AC the implementation defaults to a naive lock-free decrement; oversell only surfaces in load testing or at a live event, and the post-launch fix (schema change or advisory lock) costs far more. **Just retype it:** add an AC: "Given two users simultaneously book the last seat, when both are processed, then exactly one is confirmed and the other gets seat-unavailable; final count is 0, never negative" -- and note the implementation must use atomic decrement or row-level lock.

### Market

- **[major] BRD:42.** COMP-FIKA is rated threat: low, but Fika already runs mandatory manual ID verification (~40% rejection), 16-personality-type matching, values dealbreakers, and IRL events as free-tier core -- and its "authentic connection" positioning is your differentiator, almost word for word. Fika is absent from PRD-SAFETY's competitive_parity table entirely. **Why it's done for:** underweighting Fika means the safety-first verification moat and "authentic connection" positioning are far more contested than the BRD admits; arriving after Fika without its head-start makes acquiring the same users (especially P-URBAN women, Fika's core audience) much harder. **Just retype it:** raise COMP-FIKA to med/high for PRD-SAFETY and the positioning, add it to the competitive_parity table with an honest parity/behind call, and foreground what Ghep Doi Viet actually does that Fika doesn't -- national scope for P-PROVINCE and P-RETURNEE. Source: https://vietcetera.com/en/fika-asias-first-female-focused-ai-social-and-dating-app-raises-16m-in-seed-funding

- **[major] BRD:56.** BRD-G1 targets 100k MAU on a swipe mechanic functionally identical to Tinder/Bumble, with no JTBD-competition analysis for P-PROVINCE, whose real alternative is Facebook groups, Zalo, or do-nothing -- not Tinder. The thin-pool risk is acknowledged but the cold-start swipe-stack-empty problem is never answered. **Why it's done for:** with no cold-start strategy for the provinces, 100k MAU implicitly leans on Hanoi/HCM density where Tinder is already the top dating app on Google Play VN; if P-PROVINCE doesn't activate, the national positioning collapses into a HN/HCM-only Tinder clone with no moat, and the 7-day north-star is unreachable if users churn before a first match. **Just retype it:** add a JTBD-competition section naming the do-nothing and Zalo/FB-groups alternative for P-PROVINCE, specify a cold-start tactic (geographic seeding, invite incentives, or a minimum-pool threshold that surfaces an interest-signal/waiting-list flow instead of an empty stack), and tie BRD-G1's 100k to per-persona acquisition assumptions so it's falsifiable. Source: https://www.similarweb.com/top-apps/google/vietnam/dating/

- **[minor] PRD-EVENTS:44.** PRD-EVENTS is correctly scoped out, but frames offline events purely as internal gold-plating, missing that COMP-FIKA (rated low) runs IRL events as core positioning -- its App Store title is literally "Fika: Matchmaker & IRL Events". **Why it's done for:** dismissing events as gold-plating with no competitive note leaves a blind spot; if IRL events prove a retention mechanism in Vietnam, the spec has no re-evaluation trigger. **Just retype it:** add a competitive note to PRD-EVENTS' risk section, keep scope: out for now but add a trigger -- if Fika's events show measurable retention lift in public signals within 12 months, escalate the events horizon later to next, and reconsider COMP-FIKA's threat rating. Source: https://apps.apple.com/us/app/fika-matchmaker-irl-events/id1528449006

### Craft

- **[major] PRD-CHAT:70.** The NFR says "Do tre gui tin nhan thap" (low message delay) with no number. "Thap" is a comparative adjective, not a threshold. **Why it's done for:** the team can't verify "low" objectively -- is 500ms low? 1s? 2s? -- so acceptance turns subjective and the PO/dev expectation gap bites at delivery. **Just retype it:** give it an SLA, e.g. "max message latency under 2s on standard Vietnam 3G with ~50KB payload" or a percentile target (p95 < 1.5s).

- **[major] PRD-AIREC:37-38,39,50.** "phu hop hon" (more suitable) and "thong minh hon" (smarter) used as success claims with no metric. **Why it's done for:** nobody can write an AC for "more fitting" or "smarter"; the feature becomes unmeasurable and success collapses into opinion. **Just retype it:** rewrite with explicit metrics, e.g. "profiles with high likelihood of match to sustained-messaging (match to 7-day-conversation rate >=15%)" and "ranking optimized for match-to-sustained-chat rate, not raw match count".

- **[major] PRD-SAFETY-E1-S1:20,36.** English "liveness" dropped into a Vietnamese spec with no translation or definition. **Why it's done for:** non-technical or non-English readers may read it as "being live/online"; the spec is bilingual by accident, forcing readers to guess. **Just retype it:** define it once in PRD-SAFETY -- "Liveness = xac minh nguoi song (phat hien video/hinh anh gia) qua nhan dang dong tac selfie" -- then use the Vietnamese term, or pair "liveness (xac minh nguoi song)" on first mention per artifact.

- **[major] PRD-CHAT:33,54.** "realtime" appears in Latin script once and as "theo thoi gian thuc" once, in the same artifact, with no convention. **Why it's done for:** terminology drift adds friction for localization QA and cross-language readers; the spec reads hastily stitched rather than deliberately bilingual. **Just retype it:** pick one -- Vietnamese throughout, or "theo thoi gian thuc (realtime)" on first mention then Vietnamese -- and record the choice in a glossary at the top of VISION or PRODUCT.

- **[major] PRD-PREMIUM:50-51,85.** The free-tier NFR says the limit must be "du rong" (sufficiently broad) -- how broad? 10 likes/day? 20? For how long? **Why it's done for:** with no floor the team guesses; a tight limit churns users before they feel core value (a BRD anti-goal), a loose one fails to push conversion. **Just retype it:** specify the floor, e.g. "minimum 20 likes/day, unlimited discovery, free match and messaging once matched, 48h premium trial for new users", and measure "du rong" by a retention/conversion target.

## Repeat offenders

None -- no prior critique reports for this scope.

## Worth recording as a decision (DEC-worthy)

- **BRD-G2:57 (Top-3 #1) -- metric vs north-star.** Re-pointing the headline persona goal away from `weekly-match-rate` to a sustained-conversation metric is a binding scope/measurement ruling and contradicts the steering of an authored core-value PRD. The PO should record it via `--decision`.
- **PRD-PREMIUM-E1-S2:34 -- boost vs positioning.** Either reframing the boost mechanic or formally accepting the north-star tension is a positioning decision the PO should record, not leave implicit.
- **PRD-MATCH-E1-S2:38 -- deferred AIREC in a `must` story.** Pulling the recommendation-lift / "why recommended" capability back out to PRD-AIREC re-draws now-cycle scope against what the spec said it would build; worth recording as a scope ruling.
