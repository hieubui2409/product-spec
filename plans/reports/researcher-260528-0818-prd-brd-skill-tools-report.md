# Research Report: AI-Assisted PRD/BRD Generation Tools & Skill Design

**Date:** May 28, 2026  
**Scope:** Existing tools, document hierarchies, elicitation frameworks, scope validation, context persistence  
**Target:** Inform design of Claude Code "product-manager" skill for product owners

---

## 1. Existing AI PRD Tools Landscape

### Active Market Leaders (2026)

| Tool | Positioning | Key Feature | Strength | Weakness |
|------|-------------|-------------|----------|----------|
| **ChatPRD** | "AI Copilot for PMs" | Multi-template generation, user story mapping | 100K+ users, established flow | Generic output, limited scope validation |
| **PRDKit** | "AI-Powered PRD Platform" | Notion/Confluence integration, Bolt/Loveable export | Live tool integration | Pricing model, limited context depth |
| **Productboard Spark** | "AI-first PM assistant" | Live data connectors (Amplitude, Linear), change highlighting | Enterprise features, governance | AI only with Pulse add-on (paid) |
| **Notion AI PM Templates** | Self-serve templates | Epic Summary, Structured AI PRD | Cost-effective (free), Notion native | No interactive interview, static templates |
| **Jira AI Requirements** | Jira native plugin | Generate PRDs from Jira issues | Native integration | Limited to Jira ecosystem |

### Interview/Intake Patterns

- **ChatPRD**: Template-driven. Select template → fill form fields → AI enhances/expands
- **PRDKit**: Conversational AI. "Tell me about your idea" → Clarifying questions → Multi-document output
- **Productboard Spark**: Live editing. Attach context docs → Ask questions → AI edits in-place with diff highlights
- **Notion templates**: Manual. User fills form; no AI guidance loop
- **CLaude PM Skills** (emerging): Structured 30-90 min interview → Adaptive Q&A → Synthesis into BRD/PRD/Epic/Story artifacts

**Key Insight:** Active tools pivot away from "dumb form filling" toward **conversational discovery with adaptive questioning** and **multi-artifact synthesis** in single session.

---

## 2. Open-Source GitHub Projects (Star Counts as of May 2026)

### Core Projects

| Repo | Stars | Focus | Interview Approach | Context Persistence |
|------|-------|-------|------------------|-------------------|
| [GTPlanner](https://github.com/OpenSQZ/GTPlanner) | ~500 | Agent PRD for Vibe/AI coding | Multi-stage planning workflow (short_planning → tool_recommend → design) | CLI session + workspace/output/ directory |
| [Vibe Coding Prompt Template](https://github.com/KhazP/vibe-coding-prompt-template) | ~300 | MVP + Tech Design hierarchy | Interactive Q&A (~15-20 min) | Saved docs/PRD-[AppName]-MVP.md |
| [Ralph](https://github.com/snarktank/ralph) | ~180 | Autonomous agent loop for PRD completion | Implicit (agent-driven iteration) | Loop state maintained until all items complete |
| [PRD Creator](https://github.com/AungMyoKyaw/prd-creator) | ~120 | Gemini-powered PRD generator | Simple prompt → Generated PRD | Single artifact output |
| [Agentic PRD Generation](https://github.com/SeeknnDestroy/agentic-prd-generation) | ~90 | FastAPI + Streamlit, SSE streaming | Agentic workflow with state streaming | Streamlit session state (ephemeral) |
| [PRPs-Agentic-Eng](https://github.com/Wirasm/PRPs-agentic-eng) | ~150 | Prompts + workflows for agent eng | Not primarily interview-focused | Repo as knowledge base |

### Recurring Patterns in OSS

1. **No persistent context store** — Each generation is fresh; no "product source of truth" across sessions
2. **Limited scope validation** — Most generate docs; few validate against earlier decisions
3. **Artifact-centric, not process-centric** — Output is PRD/story; intake is simplified
4. **AI-forward** — Assume Claude/Gemini/ChatGPT; not a framework for non-technical users to interact with
5. **Markdown-first** — All save to `.md` files for version control + diffs

---

## 3. Document Hierarchy Conventions

### Canonical Stack (Vision → Story)

```
┌─ VISION / BUSINESS CONTEXT ──────────────────────────────
│  Strategic rationale, market opportunity, success definition
│
├─ BRD (Business Requirements Document) ─────────────────
│  • Business goals & objectives
│  • Stakeholders, constraints, success metrics
│  • High-level scope & non-functional requirements
│  • Market size, competitive context, business model
│  • NOT: detailed features, UI, technical decisions
│
├─ PRD (Product Requirements Document) ──────────────────
│  • Features & functional requirements
│  • User personas & use cases
│  • Detailed workflows & interactions
│  • Success metrics (tied to BRD goals)
│  • Non-functional requirements (perf, security, scale)
│  • Design considerations, APIs, integrations
│
├─ EPIC ───────────────────────────────────────────────────
│  • Large body of work (1-3 quarters)
│  • Related group of user stories
│  • Epic goal, business context, acceptance criteria
│  • [Size: 3-12 stories; Timeline: 2-4 sprints minimum]
│
└─ USER STORY ──────────────────────────────────────────────
   Format: "As a [role] I want [action] so that [benefit]"
   • Acceptance criteria (3-5 per story)
   • Effort estimate (points or t-shirt size)
   • Dependencies, design notes, test scenarios
   • [Size: Completable in 1-2 sprints; Effort: 2-13 points]
```

### Typical Document Fields by Level

#### BRD
- Problem statement / Market opportunity
- Desired business outcomes
- Success metrics (financial, adoption, market share)
- Constraints & assumptions
- Stakeholder list
- Competitive landscape
- Phase-in plan (timeline, dependencies)

#### PRD
- Product vision / Problem statement
- Target users & personas
- Use cases (primary, secondary)
- Feature list (must-have, should-have, could-have via MoSCoW)
- Functional requirements
- Non-functional requirements (perf SLAs, security, accessibility)
- Success metrics (KPIs tied to BRD goals)
- Rollout & deployment plan
- Risks & mitigation
- Dependencies (third-party, internal)

#### Epic
- Epic name & goal
- Business context (links to PRD section + BRD goal)
- Estimated scope (stories, effort)
- Success criteria (how we know it's done)
- Acceptance criteria (testable conditions)
- Timeline & dependencies
- Risks

#### Story (INVEST-compliant)
- **I**ndependent — No hard dependencies on other stories
- **N**egotiable — Details can evolve in conversation
- **V**aluable — Clear user value, not just technical task
- **E**stimable — Team can forecast effort (2-13 points typical)
- **S**mall — Completable in 1-2 sprints
- **T**estable — Clear acceptance criteria, objective validation
- Acceptance criteria (3-5 per story)
- Effort estimate, acceptance tests, design notes

### Key Distinctions

| Aspect | BRD | PRD |
|--------|-----|-----|
| **Audience** | Executives, business stakeholders | Product, design, engineering teams |
| **Scope** | Why build it | What to build |
| **Detail** | High-level business rationale | Detailed features & workflows |
| **Timeline** | Often 1-2 year horizon | Current release + 2-3 cycles ahead |
| **Ownership** | Product + business leadership | Product manager |

---

## 4. Requirements Elicitation Frameworks

### Best-Suited Techniques for Guided Interview

#### Primary (High Signal for PM Context)

1. **Jobs-to-be-Done (JTBD)**
   - Core question: "What job is the user hiring this product to do?"
   - Yields: Emotional + functional motivation, success metrics, competing solutions
   - Interview depth: 45-60 min deep-dive → 10-15 min structured Q&A
   - Output: User jobs, constraints, context

2. **5 Whys** (Root Cause Intent)
   - Q: "Why is [goal] important?" → Iterate 5x
   - Yields: Real underlying motivation vs. stated feature request
   - Lightweight, integrates well into conversational flow
   - Output: Core business intent, prevents scope creep

3. **Story Mapping** (Scope Visualization)
   - Arrange stories in narrative flow (discovery → purchase → use → support)
   - Yields: Natural scope boundaries, priority ordering, dependencies
   - Interview trigger: "Walk me through a typical day a user has with this"
   - Output: Story sequence, gaps, out-of-scope items

4. **MoSCoW Prioritization** (Scope Control)
   - Must-haves (critical to 1.0), Should-haves, Could-haves, Won't-haves
   - Yields: Clear scope boundary, defensible "no" to creep
   - Interview: "If you could only ship ONE thing, what is it?" → Iterate backwards
   - Output: Structured scope, version planning

#### Secondary (Context + Prioritization)

5. **Kano Model** (Satisfaction Drivers)
   - Basic needs (absence = dissatisfaction), Performance needs (linear), Excitement needs (delightful)
   - Yields: Feature prioritization by emotional impact + effort
   - Lighter weight than JTBD; use when scope is clear but priorities are fuzzy
   - Output: Feature tiers by customer satisfaction curve

6. **Design Thinking / How Might We** (Innovation Framing)
   - Reframe constraints as opportunities: "How might we [goal] despite [constraint]?"
   - Yields: Creative solutions, edge case awareness, risk mitigation ideas
   - Use when scope is locked but implementation approach is open
   - Output: Solution hypotheses, design directions

---

## 5. Scope & Consistency Validation Heuristics

### Detection Mechanisms (Non-ML, Rule-Based)

#### Scope Creep Detection

1. **Traceability Matrix**
   - Every story must trace back to ≥1 epic
   - Every epic must trace back to ≥1 PRD requirement
   - Every PRD requirement must trace back to ≥1 BRD goal
   - **Heuristic:** Items without upstream traceability = scope creep or orphaned work

2. **Story Orphaning**
   - "This story doesn't mention the user problem or success metric"
   - **Heuristic:** Any story lacking clear user value = technical task, not story; flag for reclassification

3. **Timeline Sanity Check**
   - Sum story effort estimates → compare vs. available capacity
   - If BRD phase is "4 weeks" but stories total "200 points" + team is "10 points/week" → **2 weeks vs. 20 weeks = scope blown**
   - **Heuristic:** (Total effort / team velocity) ÷ timeline > 1.5x = scope creep warning

4. **Feature Creep Pattern**
   - Compare proposed features vs. original BRD success metrics
   - If feature doesn't contribute to ≥1 metric, ask: "Is this in-scope for v1.0?"
   - **Heuristic:** >15% of stories don't map to success metrics = scope drift

#### Consistency Checks

1. **Persona Alignment**
   - Every story is "As a [defined persona]"
   - If story uses undefined persona, create it or reject story
   - **Heuristic:** >10% of stories use undefined personas = persona definition incomplete

2. **Acceptance Criteria Completeness**
   - Each story has 3-5 objective, testable ACs
   - AC without clear "done" condition = incomplete story
   - **Heuristic:** Stories with <2 ACs or vague ACs (e.g., "should be intuitive") = likely incomplete

3. **INVEST Compliance Scan**
   - Flag stories that:
     - Hard-depend on other stories (not Independent)
     - Span 2+ team skill areas (not Small)
     - Lack clear definition of "done" (not Testable)
     - Can't be completed in 1 sprint (not Small)
   - **Heuristic:** >20% of stories fail INVEST = backlog not ready for eng

4. **Goal Alignment**
   - All success metrics in PRD must trace to ≥1 BRD goal
   - All epics must explicitly state which BRD goal(s) they serve
   - **Heuristic:** Epics without goal linkage = misalignment, ask PM to clarify

#### Output: Validation Report

```markdown
## Scope & Consistency Validation

### Issues Found (Warn if >0)
- 3 orphaned stories (no epic parent)
- 2 stories without defined persona
- Timeline overage: 220 points vs. 80-point capacity in 4 weeks

### Recommendations
1. Reassign [Story X] to backlog (defer to v1.1)
2. Add missing personas: [list]
3. Split [Story Y] into 2 stories (currently 13 points, exceeds 8-point threshold)

### Traceability (Green if complete)
- All 12 stories → 3 epics ✓
- All 3 epics → 2 BRD goals ✓
- BRD goals → success metrics ✓
- Status: READY FOR ENGINEERING
```

---

## 6. Product Context Persistence Patterns

### Problem Statement

Most PRD generators treat each document generation as **stateless**. When a PM wants to:
- Update feature list for v1.1
- Cross-check a new feature against v1.0 constraints
- Regenerate user stories with updated personas
- Validate scope creep in a new request

...they start from scratch. No "product source of truth" carries context forward.

### Existing Patterns

#### ChatPRD / PRDKit
- Templates are reusable; user refills form each session
- No persistent product metadata
- Multi-document project view (Notion/Confluence integration) but no unified source

#### GTPlanner
- Workspace directory (`workspace/output/`) persists generated docs
- Next session reads them for context ("what did we decide last time?")
- No metadata file; implicit from doc filenames

#### Productboard Spark
- "Live data connectors" link to external tools (Amplitude, Linear, Notion)
- Pulls fresh data each session for validation
- No internal product context store; external systems are source of truth

#### Notion PM Templates
- Database properties (status, priority, owner) create implicit context
- Related items linked via relations
- No explicit "product metadata" file; context implicit in DB structure

### Recommended Pattern for Claude Skill

**Single persistent product-metadata file** (non-negotiable for a non-technical PM):

```markdown
# Product Context (product.md)

**Product Name:** [name]
**Current Version:** [v1.0, v1.1, etc.]
**Last Updated:** [ISO date]

## Business Context
- Market opportunity: [1-2 sentences]
- Success metric: [5-10 key metrics that matter]
- Timeline: [quarters/dates]
- Team: [size, roles]

## Product Vision
- Problem: [What pain point do we solve?]
- Solution: [One-liner value prop]

## Personas (v1.0)
- [Persona A]: [1 paragraph, goals, frustrations]
- [Persona B]: ...

## In-Scope (v1.0)
- Feature A: [one-liner + link to epic or story]
- Feature B: ...

## Out-of-Scope (v1.0, for v1.1)
- Feature X (deferred)
- Feature Y (customer request, not core MVP)

## Success Metrics
- Adoption: [target]
- Engagement: [target]
- Quality: [target]

## Rollout Plan
- Launch: [date/quarter]
- Phases: [if applicable]

## Known Constraints
- Technical: [what limits design?]
- Business: [budget, timeline, resources]
- External: [API limits, compliance, third-party deps]

## Traceability (links to living docs)
- BRD: [path to BRD]
- PRD: [path to PRD]
- Epics: [path/link to epic backlog]
```

**Benefits:**
- Single reference point for PM across all Claude sessions
- Skill can read on startup → provide context-aware guidance
- Prevents "I forgot we decided X" scenario
- Diff-friendly (track evolution in git)
- Non-technical PM can maintain manually in plain text

---

## 7. Interview & Elicitation Best Practices

### Guided Interview Structure (No Overwhelming User)

**Constraint:** Product owner is non-technical, may be domain expert but not PM-trained. Goal: elicit BRD/PRD in 45-90 minutes without analysis paralysis.

#### Phase 1: Discovery (15-20 min)
**Goal:** Understand the "why"

```
1. "What problem are you solving?" 
   → Yields: Problem statement, pain point clarity

2. "Who experiences this problem most acutely?" 
   → Yields: Primary persona, frustration level

3. "How do they solve it today?" 
   → Yields: Competing solutions, incumbent behavior

4. "What would success look like?" 
   → Yields: Success metric, outcome definition
```

**Pattern:** Ask one at a time. Wait for full answer. Ask "Why?" 1-2 times to dig deeper. Synthesize after each answer.

#### Phase 2: Scope Definition (15-20 min)
**Goal:** Lock MVP boundary

```
5. "If you could build ONE feature, what is it?" 
   → Yields: Core value prop, must-have

6. "What 3-5 things would your first users need to do?" 
   → Yields: User stories in narrative flow (story map)

7. "What should NOT be in v1.0?" 
   → Yields: Deferred scope, clearer MVP boundary

8. "What constraints do you have?" 
   (Timeline, budget, tech, team size)
   → Yields: Realistic scope, integration needs
```

**Pattern:** Scope creep control. Use MoSCoW lightweight: "If [Feature X] means you miss launch date by 2 months, is it must-have?" → Forces prioritization.

#### Phase 3: User Understanding (15-20 min)
**Goal:** Build persona + use case clarity

```
9. "Walk me through a day in the life of your ideal user using this." 
   → Yields: Use cases, workflow, pain points, context

10. "What's the biggest risk they face?" / "What could go wrong?" 
    → Yields: Edge cases, error handling needs, success criteria

11. "How will we know if they're happy?" 
    → Yields: User-centric success metrics
```

**Pattern:** Story mapping → Narrative. Low-friction, natural flow.

#### Phase 4: Synthesis & Validation (5-10 min)
**Goal:** Confirm understanding, identify gaps

```
12. "Let me summarize what I heard..." 
    → Read back BRD + PRD outline in plain language

13. "What did I miss?" / "What's most important I got wrong?" 
    → Catch blind spots, course-correct

14. "Ready for me to generate the full documents?" 
    → Get explicit sign-off before synthesis
```

**Total Time: 50-80 min.** Shorter if PM is pre-aligned; longer if domain is complex.

### Interview Adaptivity

- **If PM keeps mentioning "nice-to-haves":** Ask "Will this be in v1.0 or v2.0?" after each one. Lock MVP.
- **If PM is vague on success metric:** Ask "How much would you pay for a 10% improvement in [metric]?" (JTBD leverage).
- **If scope is unclear:** Use MoSCoW immediately. "Rank these 5 features: must, should, could, won't."
- **If timeline pressure is implied:** "If you ship in [date], what's the minimum viable set?" (Forces prioritization).

---

## 8. Design Implications for Claude Skill

### Architecture (MD-first, persistent context)

1. **Skill Metadata**
   ```
   name: product-manager
   description: Guided BRD/PRD/Epic/Story interview for non-technical product owners
   ```

2. **Persistent State**
   - Read `product.md` on startup → provide context-aware guidance
   - Generate new `product.md` or update existing one after each interview
   - Store interview transcript + synthesis in `plans/reports/product-manager-{date}-{slug}.md`

3. **Document Artifacts**
   - **BRD**: `docs/brd-{product-name}.md`
   - **PRD**: `docs/prd-{product-name}.md`
   - **Epics**: `docs/epics-{product-name}.md` (list) or `docs/epics/{epic-name}.md` (per-epic files)
   - **Stories**: `docs/stories-{product-name}.md` or backlog tool export

4. **Interview Phases** (implement as skill flow)
   - Phase 1: Discovery Q&A (5-question intake)
   - Phase 2: Scope Definition (MoSCoW, story mapping, timeline)
   - Phase 3: User Understanding (persona building, use cases)
   - Phase 4: Synthesis + Validation (read back, confirm, generate docs)

### Interaction Pattern

```
User asks: "Generate a BRD for my new product"
or
User asks: "Update the PRD with new feature feedback"

Skill checks: Does product.md exist?
├─ NO → Start discovery interview (Phase 1)
├─ YES → Load context, ask "What are we working on today?"
    ├─ "First time, start from scratch" → Discovery
    ├─ "Update existing BRD with [feedback]" → Load BRD, ask clarifying Qs, generate delta
    └─ "Generate epics & stories from PRD" → Load PRD, ask persona q's, run story mapping, output stories
```

### Q&A Engine (Non-Overwhelming)

- **Default:** 1 question at a time, wait for answer, synthesize
- **If answer is vague:** Probe with "5 Why" before moving on
- **If answer contradicts earlier input:** Highlight & ask for clarification
- **Progress bar:** "We're 30% through Discovery phase; 6 of 12 questions answered"
- **Early exit:** "You can skip questions and come back later; ready to draft BRD?"

### Validation Output (Always Present)

After each phase, output a validation report:

```markdown
## Interview Progress: Discovery Phase

### Answers Collected
✓ Problem statement
✓ Primary persona
✓ Competing solutions
✗ Success metric (deferred)

### Detected Issues
- Warning: Success metric undefined (needed for PRD validation)
- Question: You mentioned "[constraint]" — is this a hard blocker for v1.0?

### Next Steps
- [Continue to Phase 2] or [Review answers] or [Export current state]
```

### Scope Creep Guard

- After Phase 2, automatically run scope validation
- Show traceability matrix (what stories support which BRD goals)
- Highlight timeline overage if effort > capacity
- Recommend story cuts or defer-to-v1.1 moves

### Context Propagation

- All generated documents reference `product.md` via inline links
- Stories link to parent epic + parent PRD requirement
- Epics link to BRD goal
- Every artifact includes "last updated" + "context as of [date]"

### Export Options

- **Markdown** (for git + version control)
- **Notion** (if Notion integration available)
- **Jira/Linear** (if backlog tool integration available)
- **HTML** (for sharing with stakeholders, non-technical view)

---

## 9. Scope & Consistency Validation Rules (Implementable)

### Validation Modes

1. **After each phase** (incremental)
   - Phase 1: Warn if success metric undefined
   - Phase 2: Warn if scope timeline conflict detected
   - Phase 3: Warn if personas undefined for stories
   - Phase 4: Full validation before export

2. **On-demand** (user can request)
   - "Validate scope against BRD goals"
   - "Check INVEST compliance for stories"
   - "Show traceability matrix"

### Checkpoints

| Checkpoint | Rule | Action if Fail |
|------------|------|----------------|
| **BRD Complete** | ≥1 success metric defined | Warn + ask user to add |
| **PRD Complete** | All personas in PRD are defined; ≥1 use case per persona | Flag undefined personas + use cases |
| **Epic Created** | Links to ≥1 BRD goal; ≥1 story assigned | Warn + ask user to add goal link |
| **Story Created** | INVEST: Independent, Negotiable, Valuable, Estimable, Small, Testable | Flag failing stories; suggest split/merge |
| **Traceability** | Story → Epic → PRD → BRD → Success Metric (unbroken chain) | Show missing links |
| **Timeline** | Sum(effort) / team_velocity ≤ timeline_weeks | Warn if overage; suggest cuts |
| **Scope Alignment** | >85% of stories trace to success metrics | Warn if >15% orphaned |

---

## 10. Recommended Document Structure (BRD + PRD Combined)

### Single Markdown File (Skill Output)

For non-technical PM ease, generate a **unified BRD-PRD document** with clear section headers:

```markdown
# Product: [Name]
**Version:** 1.0 | **Status:** Draft | **Date:** [date] | **Owner:** [PM name]

---

## I. BUSINESS CONTEXT (BRD Section)

### Problem & Opportunity
[Market opportunity, why now, competitive landscape]

### Business Goals & Success Metrics
- Goal 1: [quantified outcome]
- Goal 2: [quantified outcome]
- ...

### Constraints
- Timeline: [launch date/quarter]
- Budget/Resources: [team size, tools]
- Technical: [existing systems, integrations]
- Compliance: [regulatory, security]

---

## II. PRODUCT VISION & SCOPE (PRD Section)

### Vision Statement
[One sentence value prop + target users]

### Target Personas
- **Persona A:** [name, role, 1-2 paragraph background]
- **Persona B:** ...

### Use Cases & User Journeys
1. **[Persona A] Primary Flow:** [narrative]
   - Goal: [what they want to accomplish]
   - Current pain: [what makes it hard today]
   - With our product: [how we solve it]
   
2. **[Persona B] Flow:** ...

### Features (MoSCoW)

**Must-Have (v1.0)**
- Feature A: [description + business impact]
- Feature B: ...

**Should-Have (v1.0 stretch or v1.1)**
- Feature C: ...

**Could-Have (v2.0+)**
- Feature X: ...

**Won't-Have (out of scope)**
- Feature Z: [reason deferred]

### Non-Functional Requirements
- Performance: [SLAs, scale targets]
- Security: [auth, data, compliance]
- Accessibility: [WCAG level, languages]
- Integrations: [third-party APIs]

### Success Metrics
- **Adoption:** [target %]
- **Engagement:** [target usage pattern]
- **Quality:** [error rate, CSAT]

---

## III. ROADMAP & ROLLOUT

### Phasing
- **Phase 1 (MVP, [date]):** [features A, B]
- **Phase 2 (v1.1, [date]):** [features C, D]
- ...

### Launch Plan
- Beta: [date/target], target users: [persona X]
- GA: [date/target]
- Success criteria for launch readiness: [acceptance criteria]

---

## IV. EPICS & STORIES

### Epic: [Epic Name]
**Goal:** [What user outcome does this epic enable?]  
**Business Context:** Supports BRD goal "[goal name]" & success metric "[metric]"  
**Scope:** [X stories, estimated Y points]  
**Timeline:** [target sprint/quarter]  
**Success Criteria:**
- [AC1: testable outcome]
- [AC2]

**Stories:**
1. As a [Persona], I want [action] so that [benefit]
   - Acceptance Criteria:
     - [AC1]
     - [AC2]
   - Estimate: [points]
   - Design notes: [any UI/UX consideration]

2. As a [Persona], ...

...

---

## V. RISKS & DEPENDENCIES

### Risks
- [Risk A]: Impact [high/med], Likelihood [high/med], Mitigation: [plan]
- [Risk B]: ...

### Dependencies
- Third-party: [API X, service Y]
- Internal: [data from system Z]
- External: [regulatory approval]

---

## VI. APPENDIX

### Assumptions & Constraints
[Explicit list]

### Traceability Matrix
| Story | Epic | PRD Requirement | BRD Goal | Success Metric |
|-------|------|-----------------|----------|----------------|
| S1    | E1   | Feature A       | Growth   | Adoption       |
| S2    | E1   | Feature B       | Growth   | Adoption       |
| ...   | ...  | ...             | ...      | ...            |

### Change Log
- v1.0 (Draft) [date]: Initial document
- v1.0 (Review) [date]: Integrated feedback from [stakeholders]

### Sign-Off
- Product Manager: [name, date]
- Stakeholder: [name, date]
```

---

## 11. Unresolved Questions

1. **Interview Depth Control:** How to adapt question count/depth based on PM expertise level? (Novice PM = more questions; expert = faster)?
2. **Integration with Live Backlog:** Should the skill auto-push stories to Linear/Jira/Asana, or is markdown export sufficient?
3. **Persona Quantity Sweet Spot:** How many personas is "enough" for MVP? (Research suggests 2-4, but some teams use 8+.)
4. **Success Metric Quantification:** Should the skill help PM define metrics (e.g., suggest cohort sizes, benchmarks), or just collect their answers?
5. **Document Ownership & Access Control:** Who can edit `product.md`? Just the PM, or team-editable? Version control implications?
6. **Scope Validation Severity:** When timeline conflict is detected, should the skill block doc generation or just warn?
7. **Language/Domain Portability:** Is the skill optimized for web/SaaS products, or should it adapt questions for hardware/AI/B2B differently?
8. **Stakeholder Alignment Loop:** Should the skill auto-generate a stakeholder summary (1-page exec summary for sign-off)?
9. **Feedback Loops:** How does the skill handle "update story feedback" → "regenerate PRD" workflows without losing prior context?
10. **Complexity Scoring:** Should the skill estimate product complexity (simple CRUD vs. complex state machine) and adjust interview depth?

---

## Sources

### Tools & Platforms
- [ChatPRD](https://www.chatprd.ai/)
- [PRDKit](https://dynamicbusiness.com/ai-tools/prdkit-ai-powered-prd-generation-tool.html)
- [Productboard Spark](https://support.productboard.com/hc/en-us/articles/44571897288723-Beta-Productboard-Spark)
- [Jira AI Requirements](https://marketplace.atlassian.com/apps/1230496/ai-generated-product-requirements-for-jira)
- [Notion PM Templates](https://www.notion.com/templates/ai-prd-product-manager)

### Open-Source Projects
- [GTPlanner](https://github.com/OpenSQZ/GTPlanner)
- [Vibe Coding Prompt Template](https://github.com/KhazP/vibe-coding-prompt-template)
- [Ralph](https://github.com/snarktank/ralph)
- [PRD Creator](https://github.com/AungMyoKyaw/prd-creator)
- [Agentic PRD Generation](https://github.com/SeeknnDestroy/agentic-prd-generation)
- [PRPs-Agentic-Eng](https://github.com/Wirasm/PRPs-agentic-eng)

### Documentation & Best Practices
- [Reforge: PRD Templates](https://www.reforge.com/blog/product-requirement-document-prd-templates)
- [Atlassian: Product Requirements](https://www.atlassian.com/agile/product-management/requirements)
- [Aha: Requirements Management](https://www.aha.io/roadmapping/guide/requirements-management/what-is-a-good-product-requirements-document-template)
- [INVEST Criteria](https://platinumedge.com/the-invest-criteria-creating-powerful-user-stories)
- [Requirements Elicitation](https://re-magazine.ireb.org/articles/requirements-elicitation-in-modern-product-discovery)
- [MoSCoW Prioritization](https://www.altexsoft.com/blog/most-popular-prioritization-techniques-and-methods-moscow-rice-kano-model-walking-skeleton-and-others/)
- [Kano Model](https://www.businessanalystlearnings.com/blog/2013/8/22/applying-the-kano-analysis-model-to-requirements-identification-prioritization)
- [Jobs to Be Done](https://medium.com/tkww-design/reinvigorating-the-kano-model-with-jobs-to-be-done-theory-90dcb962d0e4)
- [Scope Creep Prevention](https://www.prodpad.com/glossary/scope-creep/)
- [Traceability Matrix](https://definedlogicllc.medium.com/traceability-keeps-project-scope-requirements-in-sync-1ab255bc4888)
- [Claude PM Skills Framework](https://github.com/deanpeters/Product-Manager-Skills)

---

**Report End**
