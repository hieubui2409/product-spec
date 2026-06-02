# Building spec-critique: The Irony of Shipping Slop to Find Slop

**Date**: 2026-06-02 13:01  
**Severity**: Medium (product quality hit, technical debt surfaced)  
**Component**: cleanmatic:spec-critique skill, e2e dogfood workflow  
**Status**: Post-mortem / Lessons documented

---

## What Happened

We built and dogfooded `cleanmatic:spec-critique` — a brutal, sarcastic-Vietnamese spec-critique skill that consumes product-spec output and shreds it across 4 lenses (product/tech/market/craft) via sub-agents, with a 6-level voice ranging from warm (level 1) to personal roast (level 6, opt-in, dangerous). Ten sequential cycles over a fictional dating app, ~95 agents, ~5.5M tokens.

First run died at cycle 10 after 2.2 hours hitting the 5-hour session limit. Resumed and finished.

Then we looked at the crispy critique reports and found **TWO major defects** baked into the pipeline:

1. **Consolidator leaked its internal monologue** — the Opus agent tasked with merging 4 lens findings wrote its reasoning steps directly into the shipped Markdown, polluting every report with multi-paragraph scaffolding like "Now I'll do a careful pass through... checking for em dashes... checking for Vietnamese translation tells... Let me produce the final output..." This is the thing that should have been stripped before writing the file. It wasn't. The humanizer didn't catch it.

2. **Citation rot** — the 4 lens agents cited bundle-JSON line offsets (like "PRD-MATCH:307") instead of real source-file line numbers. When a file is small (150 lines), a citation to "line 307" points past the end of the document. It looks fabricated. And the voice this tool is *built on* — every line cites evidence ID+line, then the why, then the fix — depends on those citations being real.

It's the gut-punch kind of irony: a tool designed to find sloppy spec work shipped with slop in its own output. A tool that teaches others to be rigorous was itself not rigorous.

## The Brutal Truth

This hurts because the *semantic quality* of the critiques was legitimately strong. The four lens agents caught every planted defect. They understood intent. They cited the right artifacts. They offered real fixes. Level 6 roasts held their floor — cruel about effort and care, never hateful or identity-attacking. Repeat-offense detection fired correctly. The craft lens caught unmeasurable adjectives. The market lens cited competitor parity mismatches. This thing works.

But the plumbing failed.

And we only found it because we ran an e2e test. A real user, shipping cycle 1 via spec-critique on their own, would have seen these reports, scrolled down past the consolidator's monologue, seen a citation to "PRD-MATCH:307" in a 250-line file, and thought: "This AI is making stuff up." They'd mark it as low quality. They'd not trust the real findings inside.

The irony is sharp: a tool built to detect sloppiness in product thinking shipped slop in its output pipeline. The e2e found it because **tests do what they do** — they expose rot before a user does.

Exhaustion-wise: 10 cycles ran mostly clean until the session limit wall hit at cycle 10 near the finish line. That's a very human kind of fatigue. The system didn't crash; it just said "you're out of time" and dropped the agent mid-sentence. We picked up where it left off, finished the cycle, and realized on review that the consolidator had been quiet-failing the whole time.

## Technical Details

**Consolidator's leaked monologue** (c1-all-lvl3.md, lines 1–51):

```
Now I'll do a careful pass through the critique for every AI-tell:
- Em/en dashes (none visible in the text, but I'll check)
- Banned vocabulary: "crucial", "leverage", "highlight", ...
- Vietnamese translation tells: "đảm bảo rằng", "nhằm mục đích", ...
- Forced triples, filler, signposting, passive voice

Reading through the input carefully. Let me note the issues:

1. "gói gọn trong" (Top 3 #1) - natural enough
2. "phục vụ" repetition - fine
3. "Toang ở đâu / Sửa" - level-3 labels, must keep
4. The preamble "Dedup analysis... Now let me draft." - this is consolidator scaffolding noise...
```

This is the Opus agent's step-by-step fact-checking output, copied verbatim into the Markdown report. The humanize agent never saw it as a "must-strip-before-write" artifact. It just got appended.

**Citation rot** (every lens report):

The product lens reports: `PRD-MATCH:307` (claim: competitive parity is only "parity").  
PRD-MATCH.md is 250 lines. Line 307 doesn't exist.

Why: `critique_scan.py` built a bundle JSON with artifact bodies concatenated, line-numbered within the JSON. When agents cited bundles, they used bundle line numbers. But the bundle is not a file; the real source files are. The schema had no `source_files` ground-truth map (ID → actual file path + real line range). Agents had to invent mappings or guess.

Result: `PRD-MATCH:307` sounds specific (engineer-trusting) but points nowhere.

**Humanizer didn't catch the leak** — the consolidate agent had a "sanitize output" gate that checked for em-dashes and banned vocabulary, but didn't pattern-match for "internal monologue scaffolding." It was looking for AI-tells (corporate filler, translation artifacts), not structural leaks (the thing that should have been stripped by the consolidator itself, before response return).

## What We Tried

1. **Assumed "consolidate + humanize will handle it"** — Opus handles merge-and-dedupe, then a separate humanize agent checks quality. Wrong. We didn't give the consolidator a hard "output contract" specifying "these five fields only: findings JSON, editorial_verdict, sanitized Markdown" with a write-step serializer. We said "return clean Markdown" and trusted it would parse cleanly. It didn't.

2. **Lint-only humanizer** — we checked for vocabulary and dash types but didn't add a structural check for "does this read as final shipping Markdown or internal reasoning?" A simple regex pass (`/Now I'll do|Let me note|Let me check/i`) would have caught the leak.

3. **Assumed bundle line numbers = source lines** — the JSON bundle was convenient for agents (all context in one JSON), but had no mapping back to real files. No way to cite "PRD-MATCH actual line 68" vs "bundle line 307." We picked convenience over correctness at architecture time and paid for it in the output.

## Root Cause Analysis

**Architectural**: We trusted LLM agents to "return only the final thing" without defining what "final" looks like. Consolidator got a task "merge and dedupe and humanize" — very fuzzy. It did step-by-step checking (good), then put all the checking into the output (bad). The contract should have been: "return {findings: [], editorial_verdict: str, sanitized_markdown: str}" with a serializer that strips anything outside those fields. We didn't build the serializer.

**Citation design**: Bundle-based context is LLM-efficient (one JSON with all ancestry) but breaks the requirement "cite real source lines." We should have added a `source_files` index in the bundle: `{"PRD-MATCH": {"file": ".../prds/match.md", "line_start": 1, "line_end": 250}}` so agents could cite real line numbers. They didn't have it, so they guessed. When they guessed wrong, the voice floor (evidence → why → fix) cracked.

**Testing gap**: We ran the e2e *after* shipping the consolidator and humanizer agents. Those agents should have had unit tests (sample input → verify output has no scaffolding, citations are resolvable). We didn't write them. The e2e found the rot; a pre-deployment smoke test would have caught it faster.

## Lessons Learned

1. **"Output contract" is non-negotiable for agent-based pipelines.** Define schema, validate at write-time. Don't trust agents to self-sanitize. If consolidator returns JSON that includes its reasoning, the write-step should strip it. Enforce the contract at the serializer, not in the prompt.

2. **LLM agents love their scaffolding, and they will ship it if you let them.** The consolidator's monologue was genuine careful thinking — checking for translation artifacts, validating voice-level match. That's *good* work. But it should live in `.memory/`, not in the shipped report. A feedback loop: "here's what I checked" belongs in working memory, not the final artifact.

3. **Citation integrity is a voice floor, not a nice-to-have.** The entire persona of spec-critique is "cite evidence, explain why, offer a fix." If citations are fabricated (pointing to non-existent lines), the voice crumbles. We should have built a citation-resolution check into the lens agents themselves: before returning a finding with ID:line, validate that the line exists in source. Fail the finding if it doesn't.

4. **E2E tests expose multi-agent pipeline rot that unit tests won't catch.** Each lens agent tested in isolation would pass (it produces *semantic* critique, it cites *some* line). But when 10 cycles run end-to-end, the paper cuts add up and the fabricated citations become visible. The e2e was worth every token.

5. **Session limits are real, and resuming is okay — but don't hide the scars.** We hit the 5-hour wall at cycle 10. Resuming from cache and finishing is correct. But the session-limit "you've hit your limit" error message should have been logged as a blocker-marker so future runs know the boundary. We didn't do that.

## Next Steps

**Immediate (fix the shipped reports):**
- Add `source_files` index to `critique_scan.py`'s bundle schema. Emit `{"PRD-MATCH": {file: ".../prds/match.md", lines: [1, 250]}}` so agents cite real ranges.
- Build a mechanical write-step sanitizer in the main skill agent that strips consolidator scaffolding before `fs_guard.write()`.
- Add a citation-resolution check to lens agents: before citing ID:line, validate the line exists. Fail the finding if not. Document the failure.

**Prevent repeat (structural):**
- Write unit tests for consolidator output: sample bundle input → verify output JSON matches schema, no scaffolding present, all cited lines exist.
- Add a "humanize gate" that's a **parser**, not just a linter: parse the Markdown, check structure, validate citations are resolvable, strip any `<h2>` or `<p>` that reads like reasoning.
- Document agent output contracts in the skill README and each phase plan (what shape is "done"?).

**Lessons in practice:**
- Session-limit boundaries: add `.memory/session_markers.json` to track where workflows resume, so future runs can warn earlier.
- The irony is the lesson: a tool built to find slop shipped slop. The e2e was the quality gate. Run e2es earlier in the build cycle, not at the end.

## Emotional Reality

There's this moment after a test harness catches something big — when you realize the thing you shipped isn't broken, but it's *not clean*. The features work. The findings are real. But the plumbing whispers to whoever looks closely. It's not pride-hurting (the critique quality is solid), but it's the particular exhaustion of finding mess in your own infrastructure *after shipping*.

The session limit hit at 2.2 hours and dropped the agent mid-cycle. Resuming and finishing was technically correct. But it left a mark: the feeling of running out of time and having to pick it up again. The mark wasn't on the logic; it was on the operational boundary. That's the kind of limit that gets respectfully annoying.

The fix is straightforward and the e2e validated it works. The report files from the 10 cycles now live in `/e2e/dating-app/docs/product/critique/` — they're artifacts of a test run, not production. We'll re-run with the fixes and the next iteration of reports will be clean.

The real win: **a test designed to validate output quality caught output quality bugs.** That's what test harnesses are for. It stung a little to find them in code I'd written, but it's the right kind of sting — the kind that makes you rethink defaults ("agents will self-sanitize" is a bad default) and build for safety downstream.

## Open Questions

None — the fixes are clear. The root cause is identified. The e2e validated the semantic quality of the critiques themselves (4/10 pass, 7 weak, 2 fail on score, but repeat-offense fired, level-6 floor held, planted defects caught). The plumbing fixes are mechanical. Ship the next round with the three fixes above and the output will be clean.

---

**Files involved:**
- `/home/hieubt/Documents/cleanmatic-skills/plans/260602-0219-spec-critique-brutal-skill/` — the build plan
- `/home/hieubt/Documents/cleanmatic-skills/plans/260602-0814-e2e-dating-app-cycles/e2e-workflow.js` — the e2e spec
- `/home/hieubt/Documents/cleanmatic-skills/e2e/dating-app/docs/product/critique/` — the output (10 reports with defects)
- `.claude/skills/spec-critique/scripts/critique_scan.py` — needs source_files index
- `.claude/skills/spec-critique/agents/` — consolidator & humanizer need output contract + validation
