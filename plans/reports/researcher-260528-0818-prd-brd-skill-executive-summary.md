# Executive Summary: AI-Assisted PRD/BRD Skill Research

**Date:** May 28, 2026  
**Research Scope:** 8+ active tools, 6 open-source projects, industry PM best practices  
**Deliverable:** 3-report research package + architectural recommendation

---

## Key Findings (One-Pagers)

### 1. Tool Landscape Evolution

**Active market:** ChatPRD (100K+ users), PRDKit, Productboard Spark, Notion PM templates, Jira AI

**Trend:** Tools shifted from **form-filling → conversational discovery** in 2024-2025. Non-technical PMs no longer accept "fill template, AI polishes" approach; they expect **adaptive Q&A, scope validation, persistence across sessions.**

**Gap:** No existing tool offers **persistent product context** + **scope creep detection** + **multi-artifact synthesis** together. Each tool is strong in one area (ChatPRD = templates; Productboard = live data; PRDKit = integration) but weak in others.

---

### 2. Document Hierarchy (Canonical)

```
Vision / Business Goals
     ↓
BRD (Business Requirements) — Why build it
     ↓
PRD (Product Requirements) — What to build
     ↓
Epics (Large work groups) — How to organize it
     ↓
User Stories (INVEST-compliant) — Detailed tasks for engineering
```

**Key Distinction:**
- **BRD** = Business goals, success metrics, constraints (stakeholder audience)
- **PRD** = Features, personas, use cases, non-functional requirements (engineering audience)

Most tools conflate these; best practice is separate documents (or clearly sectioned unified doc).

---

### 3. Elicitation Frameworks

**Best-suited for non-technical PM interview (no PhD required):**
1. **5 Whys** — Root cause intent discovery (lightweight, integrates into conversation)
2. **Jobs-to-be-Done (JTBD)** — Emotional + functional motivation (powerful but 45-60 min deep-dive)
3. **Story Mapping** — Scope visualization via narrative flow (natural, reveals gaps)
4. **MoSCoW (Lightweight)** — Scope control without formal exercise ("If this means missing launch, is it must-have?")
5. **Kano Model** — Feature prioritization by satisfaction impact (secondary, use when scope is clear)

**Recommendation:** Integrate 5 Why + Story Mapping + Lightweight MoSCoW into 4-phase interview (12-15 questions, 50-80 min).

---

### 4. Scope Validation Heuristics (Non-ML)

**Three-layer validation architecture:**

| Layer | Check | Rule | Output |
|-------|-------|------|--------|
| **Phase** | Is phase complete? | All required Qs answered | Validation report |
| **Story** | INVEST compliance | Story passes 6/6 criteria | Flag violations |
| **Scope** | Traceability | Story → Epic → PRD → BRD → Metric (unbroken) | Traceability matrix |

**Detection triggers (actionable without ML):**
- Timeline conflict: Sum(effort) / velocity > timeline × 1.2 → Scope overage warning
- Orphaned story: Story has no epic parent → Scope creep risk
- Vague acceptance criteria: <2 per story or uses words like "intuitive" → Quality gate fail
- Undefined persona: Story uses persona not in product.md → Incomplete spec

**Key insight:** Traceability matrix is the most powerful scope-creep detector. Show it to PM early; let them decide what to cut.

---

### 5. Context Persistence Solution

**Problem:** Existing tools don't carry product context across sessions. Each generation starts fresh.

**Solution:** Single `product.md` metadata file (non-technical-PM-editable markdown)

```markdown
# Product: [Name]
Problem: [1-2 sentences]
Personas: [list with brief description]
In-Scope (v1.0): [features A, B, C]
Out-of-Scope (v1.1+): [features X, Y]
Success Metrics: [adoption, engagement, quality targets]
Timeline: [launch date/quarter]
```

**Benefit:** On skill startup, read product.md → provide context-aware guidance. No need to re-interview the entire scope; only ask delta questions ("What changed?").

---

### 6. Interview Structure (Recommended)

**4 Phases, 12-15 questions, 50-80 min:**

| Phase | Goal | Qs | Output | Time |
|-------|------|----|----|------|
| **1: Discovery** | Understand problem, personas, success | 5 | BRD skeleton (problem, goal, metric, timeline) | 15-20 min |
| **2: Scope** | Lock MVP boundary, prevent creep | 4 | Feature list (MoSCoW), story map, roadmap | 15-20 min |
| **3: User Understanding** | Build personas, use cases, stories | 3 | Detailed personas, stories with ACs, workflows | 15-20 min |
| **4: Synthesis** | Confirm, identify gaps, generate docs | 3 | Final BRD+PRD+Traceability, validation report | 5-10 min |

**Key pattern:** Ask one question at a time, wait for full answer, probe with "5 Why" 1-2x to dig deeper. Synthesize after each phase.

**Adaptive:** If PM keeps saying "nice-to-have," ask "Will this be v1.0 or v1.1?" after each one. Lock scope.

---

### 7. Recommended Artifact (Unified BRD+PRD)

**Single markdown file** with clear section breaks:
1. Business Context (BRD): Problem, Goals, Metrics, Constraints
2. Product Vision & Scope (PRD): Personas, Use Cases, Features (MoSCoW), Non-Functional Requirements
3. Roadmap & Rollout: Phasing, Launch Plan
4. Epics & Stories: Structured list with acceptance criteria
5. Risks & Dependencies
6. Appendix: Traceability Matrix, Change Log

**Why unified vs. separate docs?**
- Non-technical PM can read end-to-end in 10 min
- Single artifact = easier to version control (git diffs are clear)
- Reduces redundancy (BRD goals and PRD goals are often the same; separate docs create duplication)
- Export to Notion/Jira/HTML as needed; source stays in Markdown

---

### 8. Skill Architecture (Recommended)

**Input:** Non-technical product owner, product idea  
**Process:** 4-phase guided interview (50-80 min)  
**Output:**
- `product.md` — Persistent product metadata (context for future sessions)
- `product-{name}-brd-prd.md` — Unified BRD+PRD document
- `product-{name}-traceability.md` — Traceability matrix (story → BRD goal)
- Validation report (INVEST, timeline, alignment)

**Extensions (Phase 2+):**
- Export to Notion, Jira, Linear (API integration)
- Incremental update workflow ("Update PRD with customer feedback" → load product.md, ask delta Qs only)
- HTML stakeholder view
- Story mapping visualization

---

## 12 Critical Design Implications (Summary)

1. ✅ **Persistent product.md** — Context across sessions
2. ✅ **4-phase interview** — No decision fatigue
3. ✅ **Lightweight MoSCoW** — Scope control via conversation, not formal exercise
4. ✅ **Validation reports after each phase** — Early error detection
5. ✅ **Unified BRD+PRD document** — Single artifact, easy to read
6. ✅ **Traceability matrix in output** — Scope alignment visible to PM
7. ✅ **INVEST compliance scan** — Story quality gate
8. ✅ **Adaptive follow-up (5 Why)** — Prevents vague features
9. ✅ **Story mapping for visualization** — Natural narrative capture of use cases
10. ✅ **Auto-detect timeline conflict** — Early capacity warning
11. ✅ **Export format flexibility** — Markdown + Notion + Jira + HTML
12. ✅ **Incremental update workflow** — Iteration without full re-interview

---

## Competitive Positioning

### vs. ChatPRD
- **ChatPRD:** Template-driven, multiple docs, no scope validation
- **Skill:** Conversational interview, unified doc, scope validation + traceability

### vs. PRDKit
- **PRDKit:** Integration-heavy (Notion/Confluence/Bolt), limited depth
- **Skill:** Persistent context, guided discovery, depth via 4-phase interview

### vs. Productboard Spark
- **Spark:** Live data connectors, enterprise features, but AI only with paid add-on
- **Skill:** Open-source baseline, no external data required, persistent context

### vs. Notion PM Templates
- **Templates:** Cost-effective, Notion-native, but static (no interview, manual fill)
- **Skill:** Guided interview, auto-generated, validation rules

---

## Implementation Roadmap

### Phase 1: MVP Skill (Weeks 1-6)
- 4-phase interview (all 12-15 questions)
- Generate unified BRD+PRD markdown
- Save product.md context file
- Validation rules (traceability, timeline, INVEST)
- Export to Markdown

**Success:** Non-technical PM completes full interview, generates coherent BRD+PRD in 50-80 min

### Phase 2: Polish + Integration (Weeks 7-10)
- Export to Notion / Jira / Linear APIs
- Incremental update workflow
- HTML stakeholder view
- Prompt optimization (reduce tokens)

### Phase 3: Advanced (Weeks 11+)
- Persona synthesis from interview data
- Competitive analysis integration
- AI-assisted story refinement
- Assumption validation loop

---

## Unresolved Questions (For Stakeholder Discussion)

1. Should interview depth adapt based on PM expertise level? (Novice = more Qs; Expert = faster)
2. Auto-push stories to Jira/Linear on export, or leave as Markdown?
3. Optimal # of personas for MVP? (Research: 2-4; some teams use 8+)
4. Scope validation strictness: Block doc generation on timeline conflict, or warn?
5. Who can edit product.md? (PM only, or team-editable?)
6. Should skill help quantify success metrics (e.g., suggest cohort sizes, benchmarks)?
7. Optimized for web/SaaS, or adapt questions for hardware/AI/B2B?
8. Auto-generate 1-page exec summary for stakeholder sign-off?

---

## Recommended Next Steps

1. **Approve architectural recommendation** — Align on 4-phase interview + persistent context + validation rules
2. **Assign skill developer** — 1 FTE, 4-6 weeks for MVP
3. **Design Phase 1 questions** — Refine 12-15 Qs with real PM feedback (maybe test with 2-3 PMs)
4. **Set success metrics** — "Non-technical PM completes full interview without help; generates shareable BRD+PRD in 50-80 min"
5. **Plan Phase 2** — Identify which export integration (Notion? Jira?) provides highest ROI

---

## Report Files (Detailed Reading)

1. **researcher-260528-0818-prd-brd-skill-tools-report.md** (6000 words)
   - Landscape analysis, document hierarchies, frameworks, validation heuristics, context persistence patterns

2. **researcher-260528-0818-prd-brd-skill-design-implications.md** (3500 words)
   - 12 critical design implications, prioritized by impact

3. **researcher-260528-0818-prd-brd-skill-recommended-architecture.md** (4500 words)
   - Full architectural spec: interview workflow, document templates, validation rules, implementation roadmap

---

**Status:** Research complete. Ready for stakeholder review and approval to proceed with Phase 1 (MVP skill development).

---

**Sources used in research:**
- ChatPRD, PRDKit, Productboard Spark, Jira/Confluence, Notion PM templates (active tools)
- GTPlanner, Vibe Coding, Ralph, PRD Creator, Agentic PRD Generation (open-source)
- Reforge, Atlassian, Aha, AltexSoft (documentation standards)
- INVEST criteria, MoSCoW, JTBD, Story Mapping, Kano Model (PM frameworks)
- Requirements Elicitation, Traceability, Scope Management (best practices)
