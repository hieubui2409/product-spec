# Product-Spec Critique: 4-Lens Framework & Diagnostic Questions

## LENS 1: PRODUCT (Value/Desirability)

### Framework: Jobs-to-Be-Done (JTBD)
**Diagnostic Questions:**
1. "What did users hire BEFORE this?" (what are we displacing?) — reveals if feature solves a real job or invents one.
2. "What will users STOP doing once they use this?" (switching jobs) — exposes if scope is truly valuable or tangential.
3. Is the job functional, social, OR emotional? (or all 3?) — vague specs often miss emotional job entirely.

**Failure Signature:** Feature described without context of what it replaces; no mention of switching friction or existing solutions.

**Sources:** [JTBD Framework](https://www.christenseninstitute.org/theory/jobs-to-be-done/), [Tony Ulwick JTBD](https://strategyn.com/jobs-to-be-done/)

---

### Framework: Value Proposition Canvas
**Diagnostic Questions:**
1. Does the feature address customer PAINS? (define pain: costs, time, effort, frustration) — specs often skip this.
2. Does it create GAINS the customer explicitly wants? (savings, quality, status?) — or is it assumed?
3. Are products/features mapped to specific jobs? (not just "cool features") — missing link reveals scope creep.

**Failure Signature:** Feature list without pain-gain mapping; abstract benefits ("more efficient") without customer evidence.

**Sources:** [Value Proposition Canvas](https://university.hygger.io/en/articles/1818952-questions-for-value-proposition-canvas), [Strategyzer](https://www.strategyzer.com/library/roadmap-to-test-your-value-proposition)

---

### Framework: Kano Model (Feature Satisfaction Categories)
**Diagnostic Questions:**
1. Is this a MUST-HAVE (basic expectation) or a DELIGHTER (differentiator)?
2. Will its absence cause dissatisfaction? Will its presence cause satisfaction?
3. What features are PERFORMANCE drivers (actively compared by users)?

**Failure Signature:** Entire roadmap of delighters with no basics; features that satisfy neither pain nor ambition.

**Sources:** [Kano Model](https://lemonlearning.com/blog/kano-model)

---

### Framework: RICE/ICE Prioritization Score Integrity Test
**Diagnostic Questions:**
1. Are REACH estimates cherry-picked (best-case window only)? Or realistic?
2. Is EFFORT sandbagged (underestimated)? — check every contributor's time, not just dev.
3. What's the confidence level in IMPACT? Is it speculative or validated?

**Failure Signature:** Low-effort estimates cluster unrealistically; reach claims without supporting data; high-impact claims on unvalidated assumptions.

**Sources:** [RICE Prioritization](https://www.koji.so/docs/rice-prioritization-framework), [Score Integrity Test](https://www.saasfunnellab.com/essay/rice-scoring-prioritization-framework/)

---

### Framework: Riskiest Assumption Hunt
**Diagnostic Questions:**
1. What's the single assumption that, if false, kills this feature?
2. Is that assumption validated or stated as fact?
3. What would it take to invalidate it? (Spec should name the test.)

**Failure Signature:** Features designed around unexamined assumptions; no mention of validation plan.

**Sources:** [Risk-Driven Design](https://producttalk.org/2022/09/identifying-riskiest-assumptions/)

---

### Framework: Opportunity-Solution Tree
**Diagnostic Questions:**
1. What's the customer problem statement? (Or are we jumping straight to solution?)
2. Are alternative solutions considered? Or only one path?
3. Does the spec justify why THIS solution over alternatives?

**Failure Signature:** Solution-first spec (feature list without problem context); no exploration of trade-offs.

---

## LENS 2: TECHNICAL (Feasibility/Clarity)

### Framework: INVEST User Story Criteria
**Diagnostic Questions:**
1. **Independent:** Does this story depend on other stories not yet done? (Or is it waiting on integration?)
2. **Negotiable:** Is scope fixed or can it flex during implementation?
3. **Valuable:** Does it ship user value, or just infrastructure? (Can it be demoed alone?)
4. **Estimable:** Is it detailed enough for team to estimate? (Or do devs have questions?)
5. **Small:** Can it complete in one sprint? (Or is it really an epic?)
6. **Testable:** Can we write acceptance criteria today? (If not, story is unfinished.)

**Failure Signature:** Epic-sized stories; stories with no AC; stories awaiting dependency clarity; infrastructure-only stories (no user value).

**Sources:** [INVEST Criteria](https://agilealliance.org/glossary/invest/), [LogRocket Guide](https://blog.logrocket.com/product-management/writing-meaningful-user-stories-invest-principle/)

---

### Framework: Given-When-Then (BDD Spec by Example)
**Diagnostic Questions:**
1. Can every AC be written in Given-When-Then format? (If not, AC is vague.)
2. Does each AC test ONE behavior, not multiple requirements?
3. Can QA automate the Then clause? (Or is it subjective: "should feel fast"?)
4. Are preconditions in Given? Triggers in When? Outcomes in Then? (Or are they mixed?)

**Failure Signature:** AC without examples; subjective outcomes ("user happy"); multiple scenarios in one AC; unmeasurable Then clauses.

**Sources:** [BDD Anti-Patterns](https://www.linkedin.com/pulse/bdd-anti-patterns-ravi-kumar-g), [Thoughtworks BDD](https://www.thoughtworks.com/en-us/insights/blog/applying-bdd-acceptance-criteria-in-user-stories), [Martin Fowler GWT](https://martinfowler.com/bliki/GivenWhenThen.html)

---

### Framework: Hidden Dependency & Complexity Audit
**Diagnostic Questions:**
1. What data, services, or systems does this story touch?
2. Are those dependencies documented? (Or hidden in the "how"?)
3. What's the failure mode if a dependency is slow or unavailable?
4. Does the story assume success? (Or does it handle edge cases: timeouts, retries, missing data?)

**Failure Signature:** Stories that gloss over integrations; no mention of error handling; assumptions about data availability.

---

### Framework: NFR (Non-Functional Requirement) Visibility
**Diagnostic Questions:**
1. What's the latency requirement? (Or is "fast" the spec?)
2. What's the failure recovery strategy? (Or does it assume nothing fails?)
3. Is compliance/security/scalability mentioned? (Or deferred as "future work"?)
4. Are these NFRs testable? (Or just aspirational?)

**Failure Signature:** Spec with zero NFRs; NFRs listed but not quantified; security/compliance mentioned in passing.

---

## LENS 3: MARKET (Competition/Business/Profit)

### Framework: Lean Canvas Business Model
**Diagnostic Questions:**
1. **Problem:** Is it real? (Evidence or just assumption?)
2. **Customer Segment:** Who exactly? (Or "everyone"?)
3. **Unique Value Proposition:** What makes this different? (Or is it me-too?)
4. **Revenue Streams & Cost Structure:** Is the math viable? (Or hopeful?)
5. **Unfair Advantage:** What can't competitors copy? (Or is it easily replicated?)

**Failure Signature:** Vague target audience; no revenue model; value prop that describes features, not differentiation; no defensibility.

**Sources:** [Lean Canvas Diagnostic](https://gustdebacker.com/lean-canvas/), [LEANSpark 7-Dimension Check](https://leanstack.com/articles/the-lean-canvas-diagnostic-part-2-of-7---structure)

---

### Framework: Porter's Five Forces (Lightweight)
**Diagnostic Questions:**
1. **Competitive Rivalry:** How many direct competitors? (Are we crowding an existing market?)
2. **Threat of Substitutes:** What do users hire instead? (Is our solution truly differentiated?)
3. **Bargaining Power of Buyers:** How price-sensitive is the market? (Is margin viable?)
4. **Bargaining Power of Suppliers:** Who controls key inputs? (Are we dependent on a single vendor?)
5. **Threat of New Entry:** How easy is it for competitors to enter? (What's our moat?)

**Failure Signature:** No mention of competitors; threat of substitutes ignored; moat undefined or easily replicated.

**Sources:** [Porter's Five Forces](https://www.isc.hbs.edu/strategy/business-strategy/Pages/the-five-forces.aspx), [HBR Strategic Guide](https://hbr.org/2008/01/the-five-competitive-forces-that-shape-strategy)

---

### Framework: Blue Ocean Strategy (Value Innovation)
**Diagnostic Questions:**
1. Are we playing Red Ocean (compete on existing factors) or Blue Ocean (create new demand)?
2. What factors should we **Eliminate** (industry standard but not valued)?
3. What factors should we **Reduce** (below industry norm)?
4. What factors should we **Raise** (above industry standard)?
5. What factors should we **Create** (industry never offered)?

**Failure Signature:** Roadmap copies competitor features; no discussion of what NOT to build; competing on price alone.

**Sources:** [Blue Ocean Strategy Canvas](https://umbrex.com/resources/frameworks/strategy-frameworks/blue-ocean-strategy-canvas/), [Four Actions Framework](https://www.blueoceanstrategy.com/tools/four-actions-framework/)

---

### Framework: Unit Economics & Willingness-to-Pay
**Diagnostic Questions:**
1. What's the revenue per user? (Or is monetization vague?)
2. What's the cost to acquire one customer? (CAC)
3. What's the lifetime value? (LTV / CAC ratio; should be 3:1+)
4. Have we validated willingness-to-pay? (Or is pricing aspirational?)

**Failure Signature:** No revenue model; monetization deferred; no pricing research; "users will pay when we ask."

---

## LENS 4: CRAFT (Clarity/Polish/Communication)

### Framework: Plain Language & Clarity Heuristics
**Diagnostic Questions:**
1. Does the spec use everyday words? (Or industry jargon without explanation?)
2. Are sentences short (15-20 words avg)? (Or dense paragraphs?)
3. Are technical terms defined on first use? (Or assumed knowledge?)
4. Is subject-verb pair close? (Or does the sentence meander?)

**Failure Signature:** Wall-of-text paragraphs; undefined jargon; passive voice dominating; long, complex sentences.

**Sources:** [Plain Language Technical Writing](https://clickhelp.com/clickhelp-technical-writing-blog/basics-of-plain-language-in-technical-documentation/), [National Archives Plain Writing](https://www.archives.gov/open/plain-writing/10-principles.html)

---

### Framework: CSI 4Cs of Specification Quality
**Diagnostic Questions:**
1. **Clear:** Is every statement unambiguous? (Or are readers guessing intent?)
2. **Concise:** Is every word necessary? (Or is there filler?)
3. **Correct:** Is the spec factually accurate? (Or does it contradict itself?)
4. **Complete:** Are all dependencies, edge cases, and NFRs addressed? (Or is scope fuzzy?)

**Failure Signature:** Contradictions between sections; redundant prose; factual errors; missing edge cases.

**Sources:** [CSI 4Cs + Spec Quality](https://www.timelytext.com/technical-specification-document-2/), [Specification Anti-Patterns](https://www.oreilly.com/radar/how-to-write-a-good-spec-for-ai-agents/)

---

### Framework: Unmeasurable Adjectives Audit
**Diagnostic Questions:**
1. Count instances of: "flexible," "robust," "efficient," "fast," "intuitive," "seamless," "elegant."
2. For each, ask: Can I test this? (If not, replace with metric.)
3. Are acceptance criteria objective or subjective?
4. Could a different team interpret this differently?

**Failure Signature:** "High-quality," "industry-standard," "best-in-class" without definition; subjective AC ("feels smooth").

**Sources:** [Requirements Clarity](https://specinnovations.com/blog/how-to-ensure-requirements-are-clear-and-unambiguous/), [Unmeasurable Language](https://fullclarity.co.uk/insights/information-architecture-design-in-ux-complete-guide-2025/)

---

### Framework: Terminology Consistency & Traceability
**Diagnostic Questions:**
1. Is "customer" used the same way everywhere? (Or does it mean different things in different sections?)
2. Are persona names used consistently? (Or mixed with role names, user types?)
3. Are feature names stable? (Or do they shift across docs?)
4. Can you trace a requirement from BRD → PRD → Epic → Story? (Or are connections lost?)

**Failure Signature:** Term redefinition mid-spec; persona names inconsistent; feature IDs missing; broken cross-references.

---

### Framework: "Show, Don't Tell" & Concrete Examples
**Diagnostic Questions:**
1. For each feature, is there at least one user flow or screenshot mockup?
2. For each AC, is there a worked example? (User does X, system shows Y.)
3. Are edge cases illustrated? (Not just listed.)
4. Is the tone descriptive or prescriptive? (Does it explain the why?)

**Failure Signature:** Spec with zero mockups, examples, or workflows; abstract feature descriptions; no user journey.

---

## CRITIQUE METHODOLOGY: Brutal But Credible

### 5 Principles for Constructive Brutality

**1. Tie Every Harsh Claim to Evidence**
- ❌ "This persona is fake."
- ✅ "This persona (40-yo accountant) has no buying power per your BRD. Actual buyer is 55+ CTO. Recommend re-interview or re-scope."

**2. Name the Failure Mode, Not the Person**
- ❌ "Your spec is vague."
- ✅ "Spec says 'users should feel the app is responsive.' Dev will ship when p50 latency < 500ms; PM expects < 200ms. Quantify it or expect rework."

**3. Separate Observation from Opinion**
- Observation: "This feature appears in no JTBD interview quote."
- Opinion: "Therefore it's gold-plating."
- **Bridge:** "No JTBD evidence + high build cost (3 weeks) + unclear revenue. Recommend validation sprint before committing dev time."

**4. Pre-Mortem > Devil's Advocate**
- Instead of: "What if nobody wants this?" (generic challenge)
- Use: "This spec assumes X. If X is false, what happens? How do we test it?"

**5. Always Offer a Fix Path**
- ❌ "Revenue model is missing."
- ✅ "Revenue model is missing. Recommend: (a) Pricing research with 5 customers, (b) Unit economics template filled by PM, (c) willingness-to-pay validation before dev."

**Sources:** [Pre-Mortem Method](https://www.psychologytoday.com/us/blog/seeing-what-others-dont/202101/the-pre-mortem-method), [Constructive Feedback Frameworks](https://matterapp.com/blog/constructive-feedback), [Red Teaming](https://www.redteamthinking.com/rtt-tools-and-techniques)

---

## Implementation Notes for Agent Prompts

Each sub-agent (product, tech, market, craft) should:

1. **Load framework checklist** (3-6 frameworks per lens)
2. **Ask diagnostic questions** in order; capture evidence for each
3. **Identify failure signatures** by pattern-matching against provided list
4. **Tie findings to fix** (e.g., "AC is untestable → rewrite Given-When-Then → provide template")
5. **Assign severity** (blocker / major / minor)
6. **Cite sources** (framework name + URL)

---

## Unresolved Questions

1. **Scope of "spec hierarchy":** Does the roast cover Vision → BRD → PRD → Epic → Story, or start at PRD? (JTBD, Lean Canvas apply to BRD; INVEST to Story; where do lenses overlap?)
2. **Competitive intelligence baseline:** For Porter's Five Forces / Blue Ocean, should agent assume competitor research exists? Or flag missing research as blocker?
3. **Severity weighting:** How should blockers (untestable AC) vs. concerns (missing NFR) vs. refinements (unclear terminology) be weighted for final roast report?
4. **Riskiest assumption tooling:** Should roast identify assumptions automatically (via NLP) or ask PM to list them first?

---

## Sources Cited (Inline Above)

- [JTBD Christensen Institute](https://www.christenseninstitute.org/theory/jobs-to-be-done/)
- [Value Proposition Canvas](https://university.hygger.io/en/articles/1818952-questions-for-value-proposition-canvas)
- [Kano Model](https://lemonlearning.com/blog/kano-model)
- [RICE Prioritization](https://www.koji.so/docs/rice-prioritization-framework)
- [INVEST Criteria](https://agilealliance.org/glossary/invest/)
- [BDD Anti-Patterns](https://www.linkedin.com/pulse/bdd-anti-patterns-ravi-kumar-g)
- [Lean Canvas](https://gustdebacker.com/lean-canvas/)
- [Porter's Five Forces](https://www.isc.hbs.edu/strategy/business-strategy/Pages/the-five-forces.aspx)
- [Blue Ocean Strategy](https://umbrex.com/resources/frameworks/strategy-frameworks/blue-ocean-strategy-canvas/)
- [Plain Language Writing](https://clickhelp.com/clickhelp-technical-writing-blog/basics-of-plain-language-in-technical-documentation/)
- [CSI 4Cs](https://www.timelytext.com/technical-specification-document-2/)
- [Pre-Mortem Method](https://www.psychologytoday.com/us/blog/seeing-what-others-dont/202101/the-pre-mortem-method)
- [Constructive Feedback](https://matterapp.com/blog/constructive-feedback)
