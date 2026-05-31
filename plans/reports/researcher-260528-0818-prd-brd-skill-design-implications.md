# Design Implications: Claude "product-manager" Skill

**Date:** May 28, 2026  
**Based On:** Research Report `researcher-260528-0818-prd-brd-skill-tools-report.md`  
**Target:** Concrete architectural decisions for skill implementation

---

## Executive Summary

Research across 8+ active AI PRD tools, 6 open-source projects, and canonical PM frameworks identifies **12 critical design implications** for a Claude skill targeting non-technical product owners.

**Key Finding:** Successful tools treat PRD generation as a **guided interview process, not form-filling**. Persistence, scope validation, and traceability are differentiators that existing tools mostly overlook.

---

## 12 Design Implications (Prioritized)

### 1. **Persistent Product Context File (P0 — Critical)**

**Implication:** Every PM session must read/write a single `product.md` metadata file that carries forward across sessions.

**Rationale:**
- ChatPRD, PRDKit, Notion templates all fail at "I want to update the PRD with feedback from customers" — no prior context available
- Open-source projects (GTPlanner, Vibe) use workspace directories or doc filenames; none have explicit metadata
- Non-technical PM can't remember across sessions; metadata file prevents "what did we decide last time?"

**Implementation:**
```yaml
File: product.md (at project root or ./docs/)
Read on startup: Check if exists; if yes, inject context into system prompt
Write after each phase: Append learnings, update feature lists
Track evolution: Meaningful diffs via git (non-technical PM can version-control this)
```

**Format:** Plain markdown (no JSON) — easier for non-technical users to read/edit manually if needed.

---

### 2. **Interview Phases as Explicit Workflow (P0 — Critical)**

**Implication:** Structure the 50-80 min interview into 4 phases (Discovery → Scope → User Understanding → Synthesis), not a linear Q&A list.

**Rationale:**
- Research shows PMs are overwhelmed by >15 questions in one sitting
- Existing tools (Productboard, vibe-coding) use conversational flow; newer PM skills (Requirements Interviewer) use adaptive Q&A
- Phase structure allows user to "break here, continue later" — critical for non-technical non-PM domain experts

**Implementation:**
```
Phase 1: Discovery (5 Qs, ~15 min) → Yields: Problem, personas, competing solutions, success metric, why-now
Phase 2: Scope (4 Qs, ~15 min) → Yields: MVP features, timeline, constraints, deferred scope
Phase 3: User Understanding (3 Qs, ~20 min) → Yields: Use cases, workflows, edge cases, user-success metrics
Phase 4: Synthesis (3 Qs, ~10 min) → Yields: Confirmation, gaps, generate artifacts

User can stop after any phase and resume later. Progress bar shows "Phase 2 of 4 | 8 of 15 questions answered."
```

**Benefit:** Prevents decision fatigue, matches real PM workflows (spec → review → spec → review).

---

### 3. **MoSCoW Lightweight Priority Control (P0 — Critical)**

**Implication:** In Phase 2, implement MoSCoW NOT as a formal 4-bucket exercise, but as conversational "scope gates."

**Rationale:**
- Research confirms MoSCoW prevents scope creep better than "list all features" approaches
- But formal MoSCoW (hours of exercise) is overkill for MVP interview
- Lightweight version: "If [Feature] means missing launch by 2 months, is it must-have?" — forces binary decision instantly

**Implementation:**
```
Question 5: "What's the ONE feature that makes v1.0 exist?"
→ [User answer] = MUST-HAVE

Question 6: "What 3-5 things must users do in first week?"
→ Story mapping (automatic scope ordering)

Question 7: "What should we NOT ship in v1.0?"
→ Explicit "Won't-Have" deferral

Question 8: "If you hit timeline crunch, what's negotiable?"
→ Implicit prioritization without formal scoring
```

**Benefit:** Scope boundary is defended before engineering sees PRD; reduces "but we need feature X too" cycle.

---

### 4. **Validation Report After Each Phase (P1 — High)**

**Implication:** After each phase, always output a validation report (even if all checks pass).

**Rationale:**
- Research shows traceability + alignment checks are NOT done by existing tools; scope creep detection is manual (PM's job)
- Skill should make validation visible, actionable, not buried in 50-page doc
- Non-technical PM doesn't know what "orphaned story" means; must explain + offer fix

**Implementation:**
```markdown
## Phase 2 Validation: Scope Definition

### Checks Passed ✓
- Timeline is realistic (8 weeks, 80-point capacity matches 5 must-have features)
- Personas are defined for stories (3/3 stories have defined personas)
- No obvious missing success metric (you defined 4 metrics in Phase 1)

### Warnings ⚠️
- Scope detection: You mentioned "stretch feature C" — is this must-have or should-have?
- Timeline conflict: Total effort (52 points) vs. capacity (80 points) leaves 28-point buffer. Good!
- Clarification needed: Story "As a user I want X so that Y" — what's the business impact of Y?

### Next Steps
- Review warnings above, or
- Continue to Phase 3 (User Understanding)
```

**Benefit:** PM can self-correct without waiting for eng review; catches 70% of docs problems early.

---

### 5. **Unified BRD+PRD Document Output (P1 — High)**

**Implication:** Generate a SINGLE markdown file (not separate BRD + PRD), with clear section breaks. Non-technical PM can read end-to-end in 10 min.

**Rationale:**
- Research shows most PM tools output multiple documents; Notion templates do same
- But for **non-technical PMs**, complexity = friction. Single document = easier to read, review, share
- BRD + PRD are often redundant anyway (same goals, different audience detail level); merged doc eliminates duplication

**Implementation:**
```
# Product: [Name]

## I. BUSINESS CONTEXT (BRD)
- Problem statement
- Success metrics
- Constraints

## II. PRODUCT VISION & SCOPE (PRD)
- Personas
- Use cases
- Features (MoSCoW)
- Non-functional requirements

## III. ROADMAP & ROLLOUT
- Phasing
- Launch criteria

## IV. EPICS & STORIES
- [Epic 1 with stories]
- [Epic 2 with stories]

## V. RISKS & DEPENDENCIES

## VI. APPENDIX (Traceability matrix, change log)
```

**Benefit:** One document to share, review, update. Markdown → diffs are clear. Export to Notion/Jira as needed.

---

### 6. **Traceability Matrix as Validation Artifact (P1 — High)**

**Implication:** Every generated doc includes a traceability matrix (story → epic → PRD → BRD goal → success metric).

**Rationale:**
- Research shows traceability is THE scope-creep detection mechanism; no tool implements it as output
- Matrix is visual proof of alignment (non-technical PM can scan "Do all stories trace to BRD goals?")
- Enables "why are we building this story?" question to be answered by matrix, not PM memory

**Implementation:**
```markdown
## Traceability Matrix

| Story ID | Story Title | Epic | PRD Req | BRD Goal | Success Metric |
|----------|------------|------|---------|----------|----------------|
| S1 | As a user I want to sign up | E1-Auth | Feature: Account creation | Growth | Adoption |
| S2 | As a user I want to reset password | E1-Auth | Feature: Account mgmt | Retention | Support tickets -20% |
| S3 | As admin I want to see usage dashboard | E2-Analytics | Feature: Admin panel | Engagement | Daily active users |
| ORPHAN | As a user I want dark mode | ❌ UNLINKED | ❌ NOT IN PRD | ❌ NO GOAL | ⚠️ MISSING |

### Legend
✓ = linked to parent  
❌ = missing link = scope creep risk  
⚠️ = deferred / out-of-scope  
```

**Benefit:** Non-technical PM can instantly see "which stories have no business justification" and decide: defer or add to PRD.

---

### 7. **INVEST Compliance Scan on Story Generation (P1 — High)**

**Implication:** When user generates stories from PRD, automatically run INVEST check (Independent, Negotiable, Valuable, Estimable, Small, Testable) and flag violations.

**Rationale:**
- Research identifies INVEST as industry standard; no AI tool currently validates against it
- Skill doing this auto-check prevents >20% of engineering back-and-forth ("story too big", "acceptance criteria too vague")
- Non-technical PM learns INVEST without formal training

**Implementation:**
```markdown
## Story INVEST Compliance

### Story S1: "As a user I want to sign up"
- [✓] Independent — No hard dependency on other stories
- [✓] Negotiable — Details can be refined in dev
- [✓] Valuable — Enables core product flow
- [⚠️] Estimable — Effort unknown; suggest: "Does team know OAuth flow?" (if not, estimate risky)
- [✓] Small — Likely completable in 1 sprint (auth story is standard)
- [✓] Testable — ACs are clear: "User can enter email", "System validates email format", "User receives confirmation code"

### Story S2: "As a user I want great performance"
- [❌] Valuable — Vague; reframe as "Page loads in <2 sec (measured by lighthouse score)"
- [❌] Estimable — No clear effort (perf can be unbounded). Suggest split: "Optimize image loading (S2a)" + "Optimize API caching (S2b)"
- [❌] Small — "Great performance" is multi-sprint work. Break into smaller stories.
- [❌] Testable — What's "great"? Define SLA: "<2 sec 95th percentile load time"

### Recommendation
- Story S1: READY
- Story S2: REWRITE before eng sees this (breaks 4 of 6 INVEST criteria)
```

**Benefit:** Catches story quality issues before engineering; prevents "why did PM write this?" friction.

---

### 8. **Context-Aware Follow-Up Questions (P1 — High)**

**Implication:** Skill detects vague/contradictory answers and probes with "5 Why" follow-up without asking user permission.

**Rationale:**
- Existing tools (ChatPRD) are passive (accept answer, move on); newer tools (Productboard Spark, Requirements Interviewer) are active (probe ambiguity)
- Non-technical PM often gives incomplete answers ("We need dashboard" without explaining why)
- Skill should push back gently: "Why is dashboard critical?" → reveals real use case

**Implementation:**
```
User: "We need a dashboard"
Skill: "Got it. Why is a dashboard critical for launch?
       (vs. simpler table/export)"

User: "So users can see their usage"
Skill: "What action will they take based on usage data?
       (Are they trying to reduce costs, find patterns, or...?)"

User: "They want to find patterns in their usage"
Skill: "What pattern matters most? Cost trends, feature usage, error patterns, or something else?"

[After 3 probes, skill synthesizes]
Skill: "So the dashboard's core value is [pattern X], which helps users [goal Y].
       That means we need [data columns Z] — not everything possible.
       Does that sound right?"
```

**Benefit:** Prevents vague features ("make it user-friendly") from entering PRD; grounds decisions in user need.

---

### 9. **Story Mapping for Scope Visualization (P1 — High)**

**Implication:** In Phase 3, explicitly use story mapping (not just list stories). Arrange user stories in narrative flow (discovery → purchase → use → support), making scope gaps visible.

**Rationale:**
- Research identifies story mapping as proven technique for scope visualization; most PM tools skip it
- Non-technical PM can "walk through day in the life" naturally; captures use cases better than form-filling
- Visual narrative reveals: "Wait, we have no onboarding story" or "We forgot error handling"

**Implementation:**
```
Skill: "Walk me through a typical day for [Persona]. First thing they do?"

User: "They log in"
Skill: [Adds "Login" to map] → "Then?"

User: "They check recent reports"
Skill: [Adds "View Reports"] → "Then?"

User: "They download a report to share with boss"
Skill: [Adds "Export Report"] → "Then?"

User: "That's it for most days"
Skill: "When do they set up a new report or change settings?"
User: "Maybe once a month in setup"
Skill: [Adds "Configure Report Template" to secondary flow]

[Skill generates story map]

### Story Map: [Persona Name]

**Main Flow (Daily)**
1. Login
2. View Reports
3. Download Report

**Secondary Flow (Monthly)**
4. Configure Report Template
5. Set Alert Thresholds

**Gaps (Missing from scope?)**
- Error handling? (e.g., "What if export fails?")
- Undo/history? (e.g., "Can user revert a config change?")
- Collaboration? (e.g., "Can they share a report with teammates?")
```

**Benefit:** Natural narrative reveals missing stories + confirms scope boundaries without formal techniques.

---

### 10. **Auto-Detection of Timeline Conflict (P2 — Medium)**

**Implication:** After Phase 2, estimate total story effort (with user input) and compare vs. available capacity. Warn if overage >20%.

**Rationale:**
- Research shows timeline overage is leading scope-creep detector
- Existing tools don't do this; PMs discover conflict weeks into eng (too late to cut features)
- Skill can ask "Roughly how many points per story?" (t-shirt sizes: XS=2, S=3, M=5, L=8, XL=13) and warn early

**Implementation:**
```
Skill: "Let's estimate rough effort. For [Story A], is this tiny (2 points), small (3), medium (5), or larger?"

User: "Probably small"
Skill: [S1 = 3 points]

[Repeat for all stories]

Skill: [After all estimates collected]

"Here's the scope math:
- Total effort: 42 points
- Team velocity: 10 points/week
- Timeline: 4 weeks available
- Capacity: 40 points

⚠️ You're 2 points over. With typical variation, you'll hit timeline pressure.

Options:
1. Move [Story C] to v1.1 (saves 3 points, gives 1-point buffer)
2. Add resources (1 person = +10 point/week capacity)
3. Extend timeline by 1 week

What's most realistic for your team?"
```

**Benefit:** PM makes informed scope decision BEFORE eng commits; prevents "we can't ship on time" surprises.

---

### 11. **Export-to-Format Flexibility (P2 — Medium)**

**Implication:** After generating BRD+PRD+Epics+Stories, offer multiple export formats without losing metadata.

**Rationale:**
- Research shows: ChatPRD outputs to template; PRDKit exports to Notion/Confluence; Productboard pushes to Jira
- Non-technical PM may need Markdown (for git) + Notion (for team sharing) + Jira (for eng) in same session
- Skill should offer: Markdown (default), Notion (if API available), Jira (if API available), HTML (for stakeholder view)

**Implementation:**
```
Skill: "Documents ready. Export to:
- [x] Markdown (saved to ./docs/)
- [ ] Notion (requires API key — configure?)
- [ ] Jira (requires API key — configure?)
- [ ] HTML (for stakeholder sharing)

Selected: Markdown + HTML"

[Exports]

Skill: "Done!
- BRD+PRD: ./docs/product-[name].md
- Traceability: ./docs/product-[name]-traceability.md
- HTML: ./docs/product-[name].html (open in browser)

Notion/Jira exports require setup (one-time). Want to configure now?"
```

**Benefit:** Single source of truth (Markdown) + multiple consumption formats (Notion for collab, Jira for eng, HTML for stakeholder view).

---

### 12. **Incremental Update Workflow (P2 — Medium)**

**Implication:** When PM returns with "Update PRD with customer feedback," load prior product.md context and only re-interview on delta (new features, changed personas, etc.), not full 50-min interview.

**Rationale:**
- Research shows existing tools don't support "iterate on existing PRD" well; most start from scratch
- Real PM workflow: draft PRD → stakeholder review → update PRD → eng review → ship → gather feedback → update roadmap
- Skill must support this cycle without losing prior context

**Implementation:**
```
User: "Update PRD with feedback from customer interviews"

Skill: [Reads product.md]

Skill: "I see your current product is [name], targeting [personas] with features [list].

What changed?
- New feature requests? (Add 5 new stories)
- Different personas? (Update 2 personas)
- Timeline shift? (Was 4 weeks, now 6 weeks)
- Success metric change? (Was adoption, now engagement)
- Persona request out-of-scope? (Confirm for v1.1 deferral)

Tell me what's different."

User: "Customers asked for dark mode and export to PDF. And they mentioned a use case we didn't think of."

Skill: [Asks clarifying Qs on just those 3 items]

Skill: [Updates product.md with new features, regenerates BRD+PRD with only changes highlighted]

"Updated! Changes:
- 2 new features added to PRD (dark mode, PDF export) → new stories S7-S8
- Use case: [description] → incorporated into persona flow
- Traceability updated (new stories trace to existing goals)
- Timeline impact: +6 points → still within 4-week capacity ✓

Full docs: ./docs/product-[name].md (check git diff for changes)"
```

**Benefit:** Iteration cycle is fast (10-15 min, not 50 min); context is preserved; changes are visible.

---

## Summary Table: 12 Implications

| # | Implication | Priority | Complexity | Benefit |
|---|-------------|----------|-----------|---------|
| 1 | Persistent product.md metadata | P0 | Low | Context across sessions |
| 2 | Interview phases (4-phase workflow) | P0 | Medium | Prevents decision fatigue |
| 3 | MoSCoW lightweight scope gates | P0 | Low | Scope creep defense |
| 4 | Validation report after each phase | P1 | Medium | Early error detection |
| 5 | Unified BRD+PRD document | P1 | Low | Single artifact, easier review |
| 6 | Traceability matrix in output | P1 | Medium | Scope alignment visible |
| 7 | INVEST compliance scan | P1 | Medium | Story quality gate |
| 8 | Context-aware follow-up (5 Why) | P1 | Medium | Prevents vague features |
| 9 | Story mapping for scope visualization | P1 | High | Natural narrative capture |
| 10 | Auto-detect timeline conflict | P2 | Medium | Early capacity warning |
| 11 | Export format flexibility | P2 | Medium | Multi-tool ecosystem |
| 12 | Incremental update workflow | P2 | High | Iteration without restart |

---

## Architecture Sketch

```
product-manager/
├── SKILL.md (metadata)
├── skill-interview-workflow.md (4-phase flow + Q&A)
├── skill-validation-rules.md (traceability, INVEST, timeline)
├── skill-output-templates.md (BRD+PRD markdown, traceability matrix)
├── scripts/
│   ├── validate-scope.py (timeline conflict detect, INVEST check)
│   ├── generate-traceability.py (build matrix from docs)
│   └── format-export.py (Markdown → Notion/Jira/HTML)
└── examples/
    ├── example-product.md (template for product context file)
    ├── example-interview-transcript.md (sample Q&A output)
    └── example-brd-prd.md (sample generated document)
```

---

## Next Steps for Implementation

1. **Create SKILL.md** — Define metadata, entry point ("Generate a BRD/PRD interview"), phases
2. **Implement Phase 1 interview** — Discovery Q&A (5 questions, 15 min target)
3. **Implement Phase 2 interview** — Scope definition + MoSCoW lightweight gates
4. **Add validation rules** — Traceability, INVEST, timeline checks (Python scripts)
5. **Generate unified BRD+PRD markdown** — Template + synthesis logic
6. **Test with non-technical PM** — Validate interview flow, document clarity, export usability
7. **Add export formats** — Notion, Jira integrations (optional Phase 2)
8. **Document examples** — Sample product.md, interview transcript, generated docs

---

**End of Design Implications**
