# humanizer-and-anti-ai-tells — write so it does not read like a machine

Adapted from the `blader/humanizer` skill (v2.7.0, MIT), itself based on Wikipedia's "Signs of AI writing". This is the
single rulebook both humanizer gates use: the consolidator applies it while drafting (Gate 1), and the
`critique-humanizer` agent re-checks the finished draft against it (Gate 2). Read it in full, every run.

---

## How this applies to product-spec-critique (read this first)

This is a critique skill, not an encyclopedia. Three carve-outs change how you apply the rules below:

1. **Keep the teeth.** The sarcasm, the strong opinions, and the bite are the intended voice (see `voice-and-tone.md`).
   At level 5 the jab at the author stays; at level 6 the direct roast of the author stays in full. The PERSONALITY AND
   SOUL section below is not optional decoration here, it is the whole point. You are removing robot-stiffness and
   translationese, never the venom. A line can be cruel and still read like a person wrote it.
2. **Never touch the grounding or the structure.** Every finding, every evidence `ID:line`, and every fix survives.
   Keep the headings, the severity tally, the top-3, the per-lens sections, the repeat-offense and DEC sections. Keep
   all IDs, frontmatter keys (`moscow`, `scope`, `competitive_parity`), framework names (INVEST, JTBD, Lean Canvas),
   and verbatim quotes from the source spec exactly as they are. Those are not AI tells; they are the citation.
3. **Vietnamese: kill the word-for-word translation tells** (the table just below). This is the most common way the
   output reads machine-made in Vietnamese.
4. **Check FOR the human-voice layer, not just against AI-tells.** A report can be free of banned vocabulary and still
   read like a report engine: every finding the same long even cadence, abstract where it could be concrete, the
   verdict buried under qualifiers. Per `voice-and-tone.md` ("the human-voice layer"), nudge it the other way: a
   physical image the PO can see, a short blunt sentence before the long one, the verdict stated flat then backed.
   And the FIRST-PERSON rule: at levels 1 to 2 the critic stays out of it (no "tôi đọc mà…"); from level 3 up the
   critic MAY name a genuine reaction to reading the spec, escalating with the level. That first-person reaction is
   the critic's, NOT an attack on the author, and it is a separate axis from the level-5/6 personal-attack redline. If
   a level-3+ report reads correct but bloodless, give it that human pulse; if a level-1/2 report has crept into
   first-person reaction, pull it back to artifact-focused. Never add first-person reaction below level 3.

### Vietnamese translation tells (đừng dịch sống)

| Đừng viết | Viết thế này |
|---|---|
| làm tươi, quét tươi, dữ liệu tươi | quét lại từ đầu, kiểm tra ngay tại chỗ, số liệu mới nhất |
| đường gốc, trải nghiệm gốc | ứng dụng di động riêng, trải nghiệm trên ứng dụng |
| đảm bảo rằng / đảm bảo là | để chắc chắn, cho chắc |
| nhằm mục đích / với mục đích | để |
| một cách + tính từ ("một cách rõ ràng") | bỏ "một cách", viết thẳng "rõ ràng" |
| điều này cho phép / việc này giúp | nhờ đó, như vậy |
| nó đóng vai trò như / nó hoạt động như | nó là, nó làm |
| tận dụng, tối ưu hóa, mạnh mẽ, liền mạch, toàn diện | dùng từ cụ thể đúng nghĩa, đừng sáo rỗng |
| việc + động từ hóa lê thê ("việc đăng nhập của người dùng") | rút gọn ("người dùng đăng nhập") |

When Vietnamese is the output language, the PERSONALITY AND SOUL voice still applies: vary rhythm, have an opinion,
sound like a sharp person, not a textbook.

---

The rest of this file is the humanizer ruleset, applied to whatever language the report is written in.

## Your task

1. Identify AI patterns. Scan for the patterns listed below.
2. Rewrite, do not delete. Replace AI-isms with natural alternatives and cover everything the original covers.
3. Preserve meaning. Keep the core message (here: every finding and fix) intact.
4. Match the voice. Fit the requested level and language. Here, that voice is sarcastic and opinionated by design.

## PERSONALITY AND SOUL

Avoiding AI patterns is only half the job. Sterile, voiceless writing is just as obvious as slop. Good writing has a
human behind it. For a critique, that means a real opinion with a real edge.

Signs of soulless writing, even when technically clean: every sentence the same length and structure; no opinions, just
neutral reporting; no humor, no edge; reads like a press release.

How to add voice: have opinions and react to them, do not just report. Vary the rhythm, short punchy sentences then
longer ones that take their time. Let some mess in; perfect structure feels algorithmic.

## Content patterns

1. Undue emphasis on significance/legacy. Cut: "stands as", "is a testament", "a pivotal/crucial/key role/moment",
   "underscores its importance", "marks a shift", "evolving landscape", "indelible mark", "deeply rooted".
2. Undue emphasis on notability/coverage. List a specific source, not vague "media outlets".
3. Superficial "-ing" analyses. Replace "symbolizing X, reflecting Y, contributing to Z" with direct statements.
4. Promotional language. Cut: "boasts", "vibrant", "rich", "nestled", "in the heart of", "renowned", "breathtaking",
   "stunning", "groundbreaking".
5. Vague attributions / weasel words. Replace "experts argue", "observers have cited" with a named source and date.
6. Formulaic "Challenges and Future Prospects" sections. Use concrete facts instead.
7. Overused AI vocabulary. Avoid: actually, additionally, align with, crucial, delve, emphasize, enduring, enhance,
   foster, garner, highlight (verb), interplay, intricate, key (adj), landscape (abstract), leverage, pivotal,
   showcase, tapestry, testament, underscore, valuable, vibrant.
8. Copula avoidance. Use "is"/"has", not "serves as", "stands as", "boasts", "features".
9. Negative parallelisms and tailing negations. Cut "not only X but also Y", "it's not just X, it's Y", and clipped
   "no guessing" fragments. State the point as a real clause.
10. Rule of three overuse. Do not force ideas into groups of three to look comprehensive.
11. Elegant variation (synonym cycling). Pick one term and repeat it; do not cycle "protagonist / main character /
    central figure / hero".
12. False ranges. Drop "from X to Y" when X and Y are not on a real scale.
13. Passive voice and subjectless fragments. Name the actor: "You do not need a config file", not "No config needed".

## Style patterns

14. Em and en dashes: cut them all. The final text contains no `, ` and no `, `. Replace each with a period, comma,
    colon, parentheses, or a restructure. Also catch spaced em dashes and double hyphens used the same way. Scan the
    final output for `, ` and `, `; any hit means it is not done.
15. Overuse of boldface. Remove mechanical emphasis, especially around acronyms.
16. Inline-header vertical lists ("- **Thing:** sentence"). Merge into flowing prose where it reads better.
17. Title Case headings. Use sentence case.
18. Emojis. Remove from headings and lists. (The deliberate ⚠️ danger marker in `voice-and-tone.md` and the SKILL flag
    table is a fixed safety signal, not decorative; leave that one alone.)
19. Curly quotation marks. Use straight quotes.

## Communication patterns

20. Collaborative artifacts. Cut "I hope this helps", "Of course!", "Let me know", "Would you like".
21. Knowledge-cutoff disclaimers and speculative gap-filling. State what is known with a source, or cut the sentence.
    Do not invent "maintains a low profile" filler.
22. Sycophantic tone. Cut "Great question!", "You're absolutely right!".

## Filler and hedging

23. Filler phrases. "In order to" becomes "to". "Due to the fact that" becomes "because". "At this point in time"
    becomes "now". "Has the ability to" becomes "can".
24. Excessive hedging. "Could potentially possibly be argued" becomes "may be".
25. Generic positive conclusions. Replace "the future looks bright" with a specific fact or next step.
26. Hyphenated word-pair overuse. Keep the hyphen attributively ("a high-quality report"), drop it in the predicate
    ("the report is high quality").
27. Persuasive authority tropes. Cut "the real question is", "at its core", "what really matters", "fundamentally".
28. Signposting. Cut "let's dive in", "here's what you need to know", "without further ado". Just say the thing.
29. Fragmented headers. Do not follow a heading with a one-line sentence that just restates the heading.
30. Diff-anchored writing. Describe the thing as it is, not as what changed (unless the doc is a changelog).

## Detection guidance: what NOT to flag

A clean human can hit several patterns with no AI involvement. Do not gut legitimate prose. On their own, these are not
tells: perfect grammar; mixed casual and formal registers; plain or dry prose without the specific tells; formal
vocabulary that is not on the overused-AI-vocabulary list; a single transition word; curly quotes alone; one em dash alone; unsourced
claims. Look for clusters, not isolated hits. For product-spec-critique specifically, do not "fix" the sarcasm, the verbatim
spec quotes, the IDs, or the frontmatter keys.

## Signs of human writing (preserve these)

Specific, hard-to-fabricate detail. Mixed feelings and unresolved tension. First-person editorial choices the writer
can defend. Variety in sentence length. Genuine asides and self-corrections. When you see these, lean toward leaving
the prose alone; over-editing destroys what makes it sound human.

## Process and output (run both passes)

1. Read the input and mark every instance of the patterns above.
2. Write a draft rewrite. Check that it reads naturally aloud, varies sentence length, prefers concrete detail and
   simple "is/has" constructions, and keeps the requested level and language.
3. Ask once: "what here still reads obviously AI or obviously translated?" Answer with the remaining tells (a banned
   word, an em dash, a calqued Vietnamese phrase, a robotic rhythm, a forced triple).
4. Produce the final rewrite that fixes them and contains no em or en dashes.

For product-spec-critique, the output of this process is the critique report itself: same findings, same grounding, same
structure, same bite, only the machine-stiffness removed.

## Source

Based on the `blader/humanizer` skill (MIT) and [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
