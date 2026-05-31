# Recommended Architecture: Claude "product-manager" Skill

**Date:** May 28, 2026  
**Status:** Architectural Recommendation (Pre-Implementation)  
**Target Audience:** Skill developers, product managers, stakeholders

---

## Executive Summary

Based on research of 8+ active tools, 6 open-source projects, and industry PM best practices, this document recommends a **4-phase conversational interview skill** with persistent context persistence and automatic scope validation.

**Core Recommendation:** Build a **lightweight, interview-driven skill** (not a form-filling tool) that targets non-technical product owners. The skill generates a single unified BRD+PRD markdown document with embedded traceability and validation, persists product context across sessions, and offers optional export to Notion/Jira/HTML.

---

## 1. Skill Definition

### Metadata

```yaml
name: product-manager
description: >
  Guided BRD/PRD/Epic/Story interview for non-technical product owners.
  Asks 12-15 structured questions across 4 phases (50-80 min), generates
  unified BRD+PRD+Traceability matrix markdown, and validates scope alignment.
  Persists product context across sessions via product.md metadata file.
entry_points:
  - "Generate a BRD and PRD for my product"
  - "Create a PRD from my product idea"
  - "I want to define my product requirements"
  - "Update our PRD with customer feedback"
file_formats: [markdown, .md files]
target_users: [Product Owners, Product Managers, Domain Experts]
prerequisites: None (non-technical friendly)
time_estimate: "50-80 minutes for full interview; 10-15 minutes for updates"
```

### Core Deliverables

1. **product.md** (persistent metadata)
   - Product name, vision, personas, features (MoSCoW), success metrics, constraints
   - Read on startup; updated after each session
   - Single source of truth for context across sessions

2. **BRD+PRD Document** (unified markdown)
   - Business context (goals, metrics, constraints)
   - Product vision & scope (personas, use cases, features)
   - Roadmap & rollout plan
   - Epics & stories with acceptance criteria
   - Risks & dependencies
   - Appendix: Traceability matrix, change log

3. **Validation Report** (after each phase)
   - INVEST compliance check (stories)
   - Traceability matrix (stories → epics → PRD → BRD → metrics)
   - Timeline conflict detection (effort vs. capacity)
   - Scope alignment warnings

4. **Export Options** (post-generation)
   - Markdown (primary; saved to ./docs/)
   - Notion (if API configured)
   - Jira (if API configured)
   - HTML (stakeholder-friendly view)

---

## 2. Interview Workflow (4 Phases)

### Phase 1: Discovery (15-20 min, 5 questions)

**Goal:** Understand the business problem, target users, and success definition.

**Questions:**
1. "What problem are you solving?"
   - Yields: Problem statement, market opportunity, why-now
   - Follow-up (5 Why): "Why is this important now vs. 6 months ago?"

2. "Who experiences this problem most acutely?"
   - Yields: Primary persona, severity of pain
   - Follow-up: "What keeps them up at night about this problem?"

3. "How do they solve it today?"
   - Yields: Competing solutions, incumbent behavior, switching barriers
   - Follow-up: "What's missing from today's solution?"

4. "What does success look like?"
   - Yields: Success metric definition, business outcome
   - Follow-up: "How will you measure it? (e.g., 10K users, 50% adoption, $100K ARR)"

5. "What's the timeline?"
   - Yields: Launch deadline, phase-in plan, resource constraints
   - Follow-up: "If you had to launch in half the time, what would you cut?"

**Output:** BRD skeleton (Problem, Goal, Success Metrics, Timeline)

**Validation Check:**
```
✓ Problem statement defined
✓ Primary persona identified
✓ Success metric quantified
⚠️ Timeline uncertain? (Follow-up offered)
```

---

### Phase 2: Scope Definition (15-20 min, 4 questions)

**Goal:** Lock MVP boundary and prevent scope creep.

**Questions:**
1. "If you could build ONE feature, what is it?"
   - Yields: Core value prop, absolute must-have
   - Follow-up: "Why is this the #1 priority?"

2. "What 3-5 things must users do in the first week?"
   - Yields: User flows, primary use cases, story map scaffold
   - Pattern: Story mapping (narrative flow)

3. "What should NOT be in v1.0?"
   - Yields: Explicit deferred scope, "won't-haves"
   - Validation: User forced to make priority call

4. "If you hit timeline crunch, what's negotiable?"
   - Yields: MoSCoW informal ranking (must-have vs. should-have priority)
   - Follow-up: "Top 5 must-haves; rest are should-haves?"

**Output:** MVP feature list (MoSCoW), story map scaffold, roadmap (v1.0 vs. v1.1)

**Validation Check:**
```
✓ MVP scope locked (N features identified)
✓ Timeline realism check: effort estimate vs. capacity
⚠️ Scope creep risk: If >15 must-haves for 4-week timeline, warn on effort
✓ Deferred scope explicit (v1.1, backlog)
```

---

### Phase 3: User Understanding (15-20 min, 3 questions)

**Goal:** Build persona definitions and use cases; validate story completeness.

**Questions:**
1. "Walk me through a typical day for [Persona A]. What do they do first?"
   - Yields: Use cases, workflows, pain points, context
   - Pattern: Story mapping (narrative flow) → generates stories inline

2. "What's the biggest risk they face [using your product]?"
   - Yields: Edge cases, error handling, success criteria, quality requirements
   - Follow-up: "How will users know if they're successful?"

3. [For each secondary persona] "Do [Persona B] and [Persona C] have different workflows?"
   - Yields: Additional epics/stories for non-primary personas
   - Follow-up: "Is Persona B in scope for v1.0?"

**Output:** Detailed personas, use cases, story list with acceptance criteria

**Validation Check:**
```
✓ All personas defined for stories
✓ All stories have defined personas (no orphaned generic stories)
✓ Acceptance criteria present for each story (objective, testable)
⚠️ INVEST compliance: Flag stories >13 points or too vague
⚠️ Missing use case? (Edge cases, error flows, support scenarios)
```

---

### Phase 4: Synthesis & Validation (5-10 min, 3 questions)

**Goal:** Confirm understanding, identify gaps, generate final artifacts.

**Questions:**
1. "Let me summarize what I heard. [Read back BRD + PRD outline in plain language]"
   - Yields: User confirmation, catch misunderstandings early

2. "What did I miss? What's most important I got wrong?"
   - Yields: Corrections, unstated assumptions

3. "Ready for me to generate the full documents?"
   - Yields: Explicit sign-off before synthesis

**Output:** 
- Final BRD+PRD markdown
- Traceability matrix
- Validation report (INVEST, timeline, alignment)
- All artifacts saved to ./docs/

**Validation Check:**
```
✓ Traceability complete (Story → Epic → PRD → BRD → Metric)
✓ Timeline conflict detected (if capacity > effort, green; else warn)
✓ INVEST compliance (if >20% non-compliant, warn; else green)
✓ Scope alignment (if >15% stories orphaned, warn; else green)
```

---

## 3. Context Persistence Model

### product.md File

**Location:** `./product.md` or `./docs/product-metadata.md` (user choice on first run)

**Read:** On skill startup (context injection into system prompt)

**Write:** After each interview phase completes

**Format:** Plain markdown (editable by non-technical users if needed)

```markdown
# Product Context: [Product Name]

**Last Updated:** 2026-05-28  
**Version:** 1.0 | **Status:** Draft | **Owner:** [PM name]

## Business Context
- Problem: [1-2 sentences]
- Market opportunity: [size, growth rate if known]
- Success metric: [quantified outcome, e.g., "10K users by Q4"]
- Timeline: [launch date/quarter]
- Constraints: [timeline, budget, team size, technical, compliance]

## Product Vision
- Vision statement: [one sentence value prop]

## Personas (v1.0)
- **Persona A:** [Name, Role, 1-2 paragraph background]
  - Primary pain: [what frustrates them]
  - Success goal: [what they want to achieve]
  
- **Persona B:** [similar structure]

## In-Scope (v1.0)
- Feature A: [one-liner + estimated effort]
- Feature B: [one-liner + estimated effort]

## Out-of-Scope (v1.0, deferred to v1.1+)
- Feature X: [reason deferred]
- Feature Y: [reason deferred]

## Success Metrics
- Adoption: [target]
- Engagement: [target]
- Quality: [target]

## Related Artifacts
- BRD+PRD: [path to generated doc]
- Epics: [path to epics list or Jira board]
- Stories: [path to stories or Linear/Jira link]
```

**Benefit:** PM returns weeks later, loads product.md context, skill immediately knows: "Ah, you're building a [problem] product for [personas], MVP is [features], deadline is [date]. What changed?"

---

## 4. Validation Architecture

### Three-Layer Validation

#### Layer 1: Phase Validation (After each phase)
- Is the phase complete? (All required questions answered)
- Are there any red flags? (Undefined persona, missing metric, timeline conflict)
- Output: Validation report (see Phase 1-4 specs above)

#### Layer 2: Story Validation (After story generation)
- **INVEST Check:** Independent? Negotiable? Valuable? Estimable? Small? Testable?
- **Acceptance Criteria Check:** 3-5 per story, objective, testable conditions
- **Persona Check:** Story has defined persona, not generic
- Output: Flagged stories for rework

#### Layer 3: Scope Validation (Before final export)
- **Traceability:** Every story traces → epic → PRD → BRD goal → success metric (unbroken chain)
- **Timeline Check:** Sum(story effort) / team velocity ≤ timeline weeks (warn if >1.2x)
- **Alignment Check:** % of stories without goal link ≤ 15% (warn if higher)
- Output: Traceability matrix, warnings for PM decision

### Validation Rules (Implementable in Python or Claude logic)

```python
def validate_invest(story):
    """Check INVEST compliance"""
    issues = []
    if not story.persona: issues.append("Persona undefined")
    if story.effort > 13: issues.append("Story too large (>13 points)")
    if not story.acceptance_criteria or len(story.acceptance_criteria) < 2:
        issues.append("Missing acceptance criteria")
    if story.dependencies: issues.append("Story not independent")
    return issues

def validate_traceability(stories, epics, prd, brd):
    """Check all stories link to BRD goals"""
    orphaned = []
    for story in stories:
        if not story.epic_id:
            orphaned.append((story.id, "No epic parent"))
        elif not get_epic(story.epic_id).brd_goal:
            orphaned.append((story.id, "Epic has no BRD goal"))
    return orphaned

def detect_timeline_conflict(stories, capacity_per_week, timeline_weeks):
    """Warn if scope exceeds capacity"""
    total_effort = sum(s.estimate for s in stories)
    available_capacity = capacity_per_week * timeline_weeks
    if total_effort > available_capacity * 1.2:
        overrun = total_effort - available_capacity
        return f"⚠️ Scope exceeds capacity by {overrun} points ({total_effort} vs {available_capacity} available)"
    return None
```

---

## 5. Document Generation (Output Templates)

### Unified BRD+PRD Markdown Template

**File:** `docs/product-{name}-brd-prd.md`

```markdown
# Product: [Name]
**Version:** 1.0 | **Status:** Ready for Review | **Date:** [ISO date] | **Owner:** [PM name]

---

## I. BUSINESS CONTEXT (BRD)

### Problem & Opportunity
[Market opportunity, problem statement, why-now, competitive landscape]

### Business Goals
- Goal 1: [quantified business outcome]
- Goal 2: [quantified business outcome]

### Success Metrics
- Adoption: [target]
- Engagement: [target]
- Quality: [target]

### Constraints
- Timeline: [launch date/quarter]
- Budget/Resources: [team size, tools]
- Technical: [existing systems, integrations]
- Compliance: [regulatory, security]

---

## II. PRODUCT VISION & SCOPE (PRD)

### Vision Statement
[One-sentence value prop + target users]

### Target Personas
- **[Persona A]:** [Name, Role, 1-2 paragraph background]
  - Primary pain: [what frustrates them]
  - Success goal: [what they want to achieve]

- **[Persona B]:** [similar]

### Use Cases & User Journeys
1. **[Persona A] Primary Flow:** [narrative]
   - Goal: [what they want]
   - Current pain: [what makes it hard today]
   - With our product: [how we solve it]

2. **[Persona B] Flow:** [narrative]

### Features (MoSCoW)

**Must-Have (v1.0)**
- Feature A: [description + business impact]
- Feature B: [description + business impact]

**Should-Have (v1.0 stretch or v1.1)**
- Feature C: [description + business impact]

**Could-Have (v2.0+)**
- Feature X: [description + business impact]

**Won't-Have (out of scope)**
- Feature Z: [reason deferred]

### Non-Functional Requirements
- Performance: [SLAs, latency targets]
- Security: [auth, data protection, compliance]
- Accessibility: [WCAG level, languages]
- Integrations: [third-party APIs, data sources]

---

## III. ROADMAP & ROLLOUT

### Phasing
- **v1.0 (MVP, [date]):** [must-have features A, B, C]
- **v1.1 ([date]):** [should-have features D, E]
- **v2.0 ([date]):** [could-have features X, Y]

### Launch Plan
- Beta: [date/quarter], target users: [persona A]
- GA: [date/quarter]
- Success criteria for launch readiness: [acceptance criteria]

---

## IV. EPICS & STORIES

### Epic: [Epic Name]
**Goal:** [What user outcome does this epic enable?]  
**Business Context:** Supports BRD goal "[goal name]" & success metric "[metric]"  
**Scope:** [N stories, estimated M points]  
**Timeline:** [target sprint/quarter]  
**Acceptance Criteria:**
- [AC1: testable outcome]
- [AC2: testable outcome]

#### Stories in This Epic

1. **S[N]** — As a [Persona], I want [action] so that [benefit]
   - Acceptance Criteria:
     - [AC1: testable condition]
     - [AC2: testable condition]
     - [AC3: testable condition]
   - Estimate: [effort points]
   - Design notes: [any UI/UX consideration or technical note]

2. **S[N+1]** — As a [Persona], I want [action] so that [benefit]
   - [Similar structure]

### Epic: [Epic 2 Name]
[Repeat structure]

---

## V. RISKS & DEPENDENCIES

### Risks
- [Risk A]: Impact [High/Med], Likelihood [High/Med], Mitigation: [plan to reduce]
- [Risk B]: Impact [High/Med], Likelihood [High/Med], Mitigation: [plan to reduce]

### Dependencies
- Third-party: [API X, service Y, cost/timeline impact]
- Internal: [data from system Z, permissions, legacy integration]
- External: [regulatory approval, compliance review timeline]

---

## VI. APPENDIX

### Traceability Matrix
[Table showing Story → Epic → PRD Req → BRD Goal → Success Metric]

### Assumptions & Constraints
[Explicit list of things assumed true; constraints on design, timeline, scope]

### Change Log
- v1.0 (Draft) [date]: Initial document
- v1.0 (Review) [date]: Integrated feedback from [stakeholders]

### Sign-Off
- Product Manager: _________________ Date: _______
- Stakeholder: _________________ Date: _______
```

### Traceability Matrix Template

```markdown
## Traceability Matrix

| Story ID | Story Title | Epic | PRD Req | BRD Goal | Success Metric |
|----------|-------------|------|---------|----------|----------------|
| S1 | As a user I want to sign up | E1-Auth | Feature: Account creation | Growth | Adoption |
| S2 | As a user I want to reset password | E1-Auth | Feature: Account mgmt | Retention | Support tickets -20% |
| S3 | As admin I want to see usage dashboard | E2-Analytics | Feature: Admin panel | Engagement | DAU |
| ORPHAN | As a user I want dark mode | ❌ UNLINKED | ❌ NOT IN PRD | ❌ NO GOAL | ⚠️ DEFERRED |

**Legend:**
- ✓ = linked to parent
- ❌ = missing link (scope creep risk)
- ⚠️ = deferred to later version

**Summary:**
- Total Stories: 12
- Orphaned (no goal link): 1 (8%) — below 15% threshold, acceptable
- Timeline Conflict: None detected (48 points < 60-point capacity in 6 weeks)
- INVEST Compliance: 11/12 stories pass (92%) — 1 story flagged for rework
```

---

## 6. Export Options (Phase 2+)

### Primary (Built-in)
- **Markdown** → `./docs/product-{name}-brd-prd.md`

### Optional (Phase 2+, requires API setup)
- **Notion** → Create/update page in workspace
- **Jira** → Create epics + stories in backlog
- **Linear** → Create issues from stories
- **HTML** → Self-contained stakeholder view (opens in browser)

---

## 7. Incremental Update Workflow

**Use Case:** PM returns with "Update PRD with customer feedback"

```
User: "Update PRD with feedback from customer interviews"

Skill: [Reads product.md]
       Loaded product context: [Product Name], v1.0, targeting [Personas]

Skill: "What changed? New features? Different timeline? New personas?
       Tell me what's different, and I'll update the docs."

User: "Customers asked for dark mode and bulk export. Timeline is now 6 weeks instead of 4."

Skill: [Asks clarifying Qs on delta only, not full re-interview]
       - "Is dark mode must-have or should-have?"
       - "Bulk export as in 'export all reports at once'? For what use case?"
       - "6 weeks total, or 6 additional weeks?"

[Skill integrates feedback, regenerates docs]

Skill: "Updated! Changes:
       + 2 new stories (Dark Mode S13, Bulk Export S14)
       + Timeline extended: 6 weeks (vs 4)
       - Capacity: 80 points (vs 60 points in 4 weeks), still within budget ✓
       
       Full docs: ./docs/product-[name]-brd-prd.md
       Git diff shows what changed: [new stories, updated timeline, no scope cut needed]"
```

---

## 8. Recommended Implementation Approach

### Phase 1 (MVP Skill)
- Implement 4-phase interview (all 12-15 questions)
- Generate unified BRD+PRD markdown
- Save product.md context file
- Validation rules (traceability, timeline, INVEST) — Python scripts or Claude logic
- Export to Markdown (primary)

**Time Estimate:** 4-6 weeks (experienced Claude skill developer)

### Phase 2 (Polish + Extensions)
- Export to Notion / Jira / Linear APIs
- Incremental update workflow (load product.md, only re-interview delta)
- HTML stakeholder view
- Prompt optimization (reduce token count, improve UX)

**Time Estimate:** 2-4 weeks

### Phase 3 (Advanced)
- Integration with customer interview platforms (Dovetail, UserTesting APIs)
- Automatic persona synthesis from interview data
- Competitive analysis integration (Craft, similar tools)
- AI-assisted story writing refinement

**Time Estimate:** 3-6 weeks (depends on API availability)

---

## 9. Success Criteria for Skill Launch

**Functional:**
- [ ] 4-phase interview completes in 50-80 min (timed with real PMs)
- [ ] Generated BRD+PRD is coherent, readable (non-technical PM can share directly)
- [ ] Traceability matrix auto-generated and correct
- [ ] Validation rules flag >70% of real scope issues (timeline, orphaned stories, INVEST violations)
- [ ] product.md persists across sessions and loads context correctly

**Usability:**
- [ ] Non-technical PM (no prior PM training) can complete full interview without help
- [ ] Progress bar shows phase completion (reduces anxiety)
- [ ] Validation warnings are actionable (explain issue + suggest fix, not just flag)
- [ ] Output documents are immediately shareable (readable, no AI jargon)

**Adoption:**
- [ ] Skill used for ≥3 products in first month
- [ ] Feedback: "Saved me [X hours] vs. writing PRD from scratch"
- [ ] Reuse rate: >50% of users update product.md for v1.1 vs. starting fresh

---

## 10. Known Limitations (Honest Assessment)

1. **Persona Synthesis:** Skill asks user to define personas; doesn't synthesize from interview data (Phase 3+ feature)
2. **Competitive Analysis:** Doesn't integrate competitive research; relies on user input
3. **Quantification:** Success metrics depend on user providing numbers (can't auto-benchmark)
4. **Backlog Tool Integration:** Jira/Linear integration is Phase 2+ (MVP is Markdown export)
5. **Interview Customization:** Same 12-15 questions for all products (not yet adaptive to domain — e.g., SaaS vs. hardware)
6. **Assumption Validation:** Doesn't probe user assumptions with real data (relies on user expertise)

**Mitigation:** Start with MVP (Markdown, basic validation). Phase 2 adds integrations. Phase 3+ adds advanced features.

---

## Conclusion

This architecture delivers a **lightweight, interview-driven skill** that addresses the core gap in existing tools: **guided discovery without form-filling friction, persistent context across sessions, and automatic scope validation visible to non-technical PMs.**

Recommended start: **Build Phase 1 (MVP skill) with focus on interview UX + document generation quality.** Validation rules and export options are secondary; the core value is a 50-80 min conversational interview that produces a coherent BRD+PRD artifact with traceability.

---

**End of Architectural Recommendation**
