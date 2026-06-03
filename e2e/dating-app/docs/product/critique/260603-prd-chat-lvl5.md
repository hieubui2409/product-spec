---
body_hash:
  PRD-CHAT: 1cfc4161
  PRD-CHAT-E1: eb20b520
  PRD-CHAT-E1-S1: 8943eb03
  PRD-CHAT-E1-S2: 8c751c9f
  PRD-CHAT-E1-S3: 0e54d9bf
  PRD-CHAT-E1-S4: 628c183c
bundle_version: 2
critique_scope: PRD-CHAT
lang: en
lens_findings_hash: d4ec0301275ffe2f
level: 5
---
# Critique: PRD-CHAT · level 5 · lenses: product, tech, market, craft

> Severity tally: blocker 2 · major 2 · minor 1
> Scoped critique of the PRD-CHAT subtree. Full ancestry (VISION → BRD → PRD-CHAT) pulled as judgment context.

## Top 2: fix now

1. **[blocker][product] PRD-CHAT:15.** PRD-CHAT is `scope: core-value` + `moscow: must`, but its only success metric is `mau-monthly` (PRD-CHAT:15) — raw monthly actives, the volume number the vision (VISION:51-52) explicitly disowns. The PRD you call the heart of the product is graded on signups, not on the sustained 7-day conversation it exists to produce. Where it dies: teams build to the metric they are graded on; grade chat on MAU and the team ships notification spam and re-engagement loops that lift logins while the conversation-retention north-star stays unowned — the exact vanity-volume trap the product was founded to escape. Fix it properly: add a sustained-conversation metric (e.g. `sustained-7day-conversation-rate`) to PRD-CHAT success and demote `mau-monthly` to a leading funnel indicator. _(DEC-worthy: this is the build-side of DEC-1.)_

2. **[blocker][tech] PRD-CHAT-E1-S4:18.** Two ACs are absolute guarantees with no mechanism: line 18 demands chat be "an toàn tuyệt đối" (absolutely safe), line 19 demands the system "bảo vệ người dùng hoàn toàn" (completely protect) — yet the story is a `should`, sized `M`, naming no threat, no detection, no response, no SLA. Where it dies: an unbounded safety contract on a medium should-have is a blank check; any build trivially claims compliance because the system does *something*, the AC stays vacuously true until a real incident blocks release, and it can never be sized or accepted. Fix it properly: split into discrete testable stories, one mechanism each (block → server rejects with 403 and stores nothing; report → queued to a review SLA; encryption → server-side log verification). Retire the catch-all.

## By lens

### Product

- **[blocker] PRD-CHAT:15.** (see Top 2 #1) — north-star metric absent from the core-value PRD; graded on `mau-monthly`. _(DEC-worthy.)_

### Tech

- **[blocker] PRD-CHAT-E1-S4:18.** (see Top 2 #2) — absolute-safety AC, no mechanism, unsizeable.
- **[major] PRD-CHAT-E1-S3:18.** ACs are pure sensation: line 18 says the experience must be "mượt mà" (smooth), line 19 "hiển thị nhanh và không giật lag" (fast, no jank). No frame rate, no render budget, nothing binary. Where it dies: the test author has no threshold to assert against; the story ships with its AC permanently interpreted by whoever runs the demo, and is unsizeable. Fix it properly: replace with measurable Given-When-Then — "100 consecutive frames render, <5% drop below 60fps on a mid-range Android" and "first 50 messages reach time-to-interactive ≤1.5s p95 on 4G" — and pin the device + network profile in frontmatter.

### Craft

- **[major] PRD-CHAT-E1-S4:22.** The story title itself — "Nhắn tin an toàn tuyệt đối" (absolutely-safe messaging, PRD-CHAT-E1-S4:22) — bakes an unmeasurable absolute into the artifact's name, not just its AC. Where it dies: a title that asserts an absolute sets a reader expectation the body can never satisfy and primes every downstream reviewer to wave the story through on vibes; the unmeasurability is now structural, top to bottom. Fix it properly: rename to a concrete mechanism ("Block + report + encrypt in 1:1 chat") so the title states what is built, not an outcome that cannot be tested.

### Market

- **[minor] PRD-CHAT:22.** PRD-CHAT claims `competitive_parity: parity` with both COMP-TINDER and COMP-BUMBLE on messaging (PRD-CHAT:22-24), but messaging is table-stakes — every dating app has it. Where it dies: parity on a commodity is not a reason to switch; the product's one claimed differentiator (sustained connection) has to live IN the chat experience or the parity rating is an admission of me-too. Fix it properly: either name what the chat does that Tinder/Bumble do not (conversation-sustaining nudges, 7-day streak signals) and rate it ahead there, or record that chat is intentionally at parity and the moat lives elsewhere.
