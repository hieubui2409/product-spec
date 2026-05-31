# Research Index: PRD/BRD Skill Design Package

**Date:** May 28, 2026  
**Research ID:** 260528-0818-prd-brd-skill  
**Status:** Complete (4 reports, 18,000+ words)

---

## Document Map

### 1. Executive Summary (START HERE)
**File:** `researcher-260528-0818-prd-brd-skill-executive-summary.md`  
**Length:** 2,500 words (8-10 min read)  
**Audience:** Stakeholders, decision-makers, executives  
**Content:**
- Key findings from all 3 research reports (distilled)
- Competitive positioning (ChatPRD vs. PRDKit vs. Productboard Spark)
- 12 critical design implications (summary table)
- Implementation roadmap (Phase 1, 2, 3 scope + timeline)
- Unresolved questions for stakeholder discussion
- Recommended next steps

**When to read:** First. Get the 30,000-foot view before diving into detailed reports.

---

### 2. Tools & Best Practices Research Report
**File:** `researcher-260528-0818-prd-brd-skill-tools-report.md`  
**Length:** 6,000 words (20-25 min read)  
**Audience:** Product managers, researchers, technical leads  
**Content:**
- **Section 1:** Active market tools (ChatPRD, PRDKit, Productboard Spark, Notion, Jira AI)
  - Interview patterns, strengths, weaknesses
  - Star counts for open-source projects (GTPlanner, Vibe, Ralph, etc.)

- **Section 2:** Open-source GitHub projects (6 projects analyzed)
  - Recurring patterns (no persistence, limited validation, artifact-centric)

- **Section 3:** Document hierarchy conventions (BRD → PRD → Epic → Story)
  - Canonical stack with field definitions
  - INVEST criteria for user stories

- **Section 4:** Requirements elicitation frameworks (5 Whys, JTBD, Story Mapping, MoSCoW, Kano)
  - Best-suited techniques for non-technical PM interview
  - Interview patterns for each framework

- **Section 5:** Scope & consistency validation heuristics
  - Traceability matrix (detection mechanism)
  - Story orphaning, timeline sanity checks, feature creep patterns
  - Validation report example

- **Section 6:** Product context persistence patterns
  - Problem statement (tools don't carry context across sessions)
  - Existing patterns (ChatPRD, PRDKit, GTPlanner, Productboard)
  - Recommended pattern: Single `product.md` metadata file

- **Section 7:** Interview & elicitation best practices
  - 4-phase guided interview structure (50-80 min)
  - Phase 1-4 questions with follow-ups
  - Adaptivity patterns (scope creep control, vague answers)

- **Section 8-11:** Document design, validation rules, context persistence, implementation

- **Appendix:** 10 unresolved questions, sources

**When to read:** After executive summary. Deep dive into tools, frameworks, and industry best practices.

---

### 3. Design Implications Report
**File:** `researcher-260528-0818-prd-brd-skill-design-implications.md`  
**Length:** 3,500 words (12-15 min read)  
**Audience:** Skill developers, architects, product owners  
**Content:**
- **12 Critical Design Implications** (prioritized P0-P2):
  1. Persistent product.md (P0 — critical)
  2. Interview phases as explicit workflow (P0 — critical)
  3. MoSCoW lightweight priority control (P0 — critical)
  4. Validation report after each phase (P1 — high)
  5. Unified BRD+PRD document output (P1 — high)
  6. Traceability matrix as validation artifact (P1 — high)
  7. INVEST compliance scan on story generation (P1 — high)
  8. Context-aware follow-up questions (P1 — high)
  9. Story mapping for scope visualization (P1 — high)
  10. Auto-detection of timeline conflict (P2 — medium)
  11. Export-to-format flexibility (P2 — medium)
  12. Incremental update workflow (P2 — medium)

- **Summary table** (all 12 implications with priority, complexity, benefit)

- **Architecture sketch** (folder structure, file organization)

- **Next steps for implementation** (7 phases: SKILL.md → Phase 1 → Phase 2 → validation → export → test → docs)

**When to read:** After tools report. Use to guide skill implementation decisions.

---

### 4. Recommended Architecture Document
**File:** `researcher-260528-0818-prd-brd-skill-recommended-architecture.md`  
**Length:** 4,500 words (18-20 min read)  
**Audience:** Skill developers, technical leads, implementers  
**Content:**
- **Section 1:** Skill definition (metadata, deliverables)

- **Section 2:** Interview workflow (4 phases with full Q&A)
  - Phase 1: Discovery (5 questions, 15-20 min) → BRD skeleton
  - Phase 2: Scope Definition (4 questions, 15-20 min) → MVP features, roadmap
  - Phase 3: User Understanding (3 questions, 15-20 min) → Personas, use cases, stories
  - Phase 4: Synthesis & Validation (3 questions, 5-10 min) → Final docs, validation report

- **Section 3:** Context persistence model
  - `product.md` file spec, structure, benefits
  - Read on startup, updated after each phase

- **Section 4:** Validation architecture
  - Three-layer validation (phase, story, scope)
  - Implementable rules (Python pseudocode)

- **Section 5:** Document generation (BRD+PRD template, traceability matrix template)

- **Section 6:** Export options (Markdown primary, Notion/Jira/HTML in Phase 2)

- **Section 7:** Incremental update workflow (load product.md, delta questions only)

- **Section 8:** Recommended implementation approach
  - Phase 1 (MVP): 4-6 weeks
  - Phase 2 (Polish): 2-4 weeks
  - Phase 3 (Advanced): 3-6 weeks

- **Section 9:** Success criteria for skill launch (functional, usability, adoption metrics)

- **Section 10:** Known limitations (honest assessment) + mitigation

**When to read:** Technical specification for developers. Use to build the skill.

---

## Reading Paths (By Role)

### Path 1: Executive / Stakeholder (30 min)
1. **Executive Summary** (8-10 min) — Get the strategic view
2. **Tools Report: Section 1** (5 min) — Understand competitive landscape
3. **Design Implications: Summary Table** (3 min) — See all critical decisions
4. **Recommended Architecture: Section 8** (2 min) — Timeline + phases

**Outcome:** Approve architectural recommendation, assign resources, next steps.

---

### Path 2: Product Manager / Researcher (90 min)
1. **Executive Summary** (8-10 min) — Overview
2. **Tools Report** (20-25 min) — Full tools analysis + frameworks
3. **Design Implications** (12-15 min) — All 12 design decisions
4. **Recommended Architecture: Sections 1-3** (10 min) — Interview structure + context model

**Outcome:** Deep understanding of tool landscape, design trade-offs, implementation approach.

---

### Path 3: Skill Developer (180 min)
1. **Executive Summary** (8-10 min) — Strategic context
2. **Tools Report: Sections 1, 4, 6, 7** (25 min) — Tools + frameworks + elicitation
3. **Design Implications** (12-15 min) — All 12 implications + architecture sketch
4. **Recommended Architecture** (45-50 min) — Full spec: phases, validation, templates, roadmap
5. **Tools Report: Section 3** (5 min) — Document hierarchy reference

**Outcome:** Complete specification to implement Phase 1 skill.

---

### Path 4: Architecture Review (120 min)
1. **Executive Summary** (8-10 min) — Strategic context
2. **Design Implications: All 12 + Table** (15 min) — Design decisions
3. **Recommended Architecture: Sections 2-7** (45-50 min) — Workflow, persistence, validation, templates
4. **Tools Report: Sections 5-6** (15 min) — Validation heuristics + context patterns

**Outcome:** Approve architecture, identify risks, implementation plan.

---

## Key Concepts (Quick Reference)

### Document Hierarchy
```
BRD (Business Requirements) — Goals, metrics, constraints
  ↓
PRD (Product Requirements) — Features, personas, use cases
  ↓
Epics — Large work groups
  ↓
Stories — INVEST-compliant tasks for engineering
```

### 4-Phase Interview
```
Phase 1: Discovery (15-20 min, 5 Qs) → BRD skeleton
Phase 2: Scope Definition (15-20 min, 4 Qs) → MVP features
Phase 3: User Understanding (15-20 min, 3 Qs) → Personas, stories
Phase 4: Synthesis & Validation (5-10 min, 3 Qs) → Final docs
```

### Three-Layer Validation
```
Layer 1: Phase validation (all Qs answered?)
Layer 2: Story validation (INVEST compliant?)
Layer 3: Scope validation (traceability complete? timeline OK?)
```

### Persistent Context
```
product.md
├── Product name, vision, personas
├── In-scope & out-of-scope features
├── Success metrics, timeline, constraints
└── Links to generated BRD+PRD+Epics
```

### Design Implications (Ranked)
```
P0 (Critical): product.md, 4-phase interview, lightweight MoSCoW
P1 (High): validation reports, unified doc, traceability, INVEST, follow-up, story mapping
P2 (Medium): timeline conflict detection, export formats, incremental updates
```

---

## Sources & References

### Active Tools (2026)
- [ChatPRD](https://www.chatprd.ai/)
- [PRDKit](https://dynamicbusiness.com/ai-tools/prdkit-ai-powered-prd-generation-tool.html)
- [Productboard Spark](https://support.productboard.com/hc/en-us/articles/44571897288723-Beta-Productboard-Spark)
- [Jira AI Requirements](https://marketplace.atlassian.com/apps/1230496/ai-generated-product-requirements-for-jira)
- [Notion PM Templates](https://www.notion.com/templates/ai-prd-product-manager)

### Open-Source Projects
- [GTPlanner](https://github.com/OpenSQZ/GTPlanner) — Agent PRD for AI coding
- [Vibe Coding Prompt Template](https://github.com/KhazP/vibe-coding-prompt-template) — MVP + Tech Design
- [Ralph](https://github.com/snarktank/ralph) — Autonomous agent loop
- [PRD Creator](https://github.com/AungMyoKyaw/prd-creator) — Gemini-powered generator
- [Agentic PRD Generation](https://github.com/SeeknnDestroy/agentic-prd-generation) — FastAPI + Streamlit
- [PRPs-Agentic-Eng](https://github.com/Wirasm/PRPs-agentic-eng) — Prompts + workflows

### PM Frameworks & Best Practices
- [Reforge: PRD Templates](https://www.reforge.com/blog/product-requirement-document-prd-templates)
- [Atlassian: Product Requirements](https://www.atlassian.com/agile/product-management/requirements)
- [INVEST Criteria](https://platinumedge.com/the-invest-criteria-creating-powerful-user-stories)
- [Requirements Elicitation](https://re-magazine.ireb.org/articles/requirements-elicitation-in-modern-product-discovery)
- [MoSCoW Prioritization](https://www.altexsoft.com/blog/most-popular-prioritization-techniques-and-methods-moscow-rice-kano-model-walking-skeleton-and-others/)
- [Jobs to Be Done](https://medium.com/tkww-design/reinvigorating-the-kano-model-with-jobs-to-be-done-theory-90dcb962d0e4)
- [Scope Creep Prevention](https://www.prodpad.com/glossary/scope-creep/)
- [Traceability Matrix](https://definedlogicllc.medium.com/traceability-keeps-project-scope-requirements-in-sync-1ab255bc4888)

### Claude PM Skills
- [Product-Manager-Skills (GitHub)](https://github.com/deanpeters/Product-Manager-Skills)
- [Claude Code for Product Managers](https://ccforpms.com/)

---

## File Locations (All Reports)

```
/home/hieubt/Documents/cleanmatic-skills/plans/reports/
├── researcher-260528-0818-prd-brd-skill-executive-summary.md (2,500 words)
├── researcher-260528-0818-prd-brd-skill-tools-report.md (6,000 words)
├── researcher-260528-0818-prd-brd-skill-design-implications.md (3,500 words)
├── researcher-260528-0818-prd-brd-skill-recommended-architecture.md (4,500 words)
└── researcher-260528-0818-prd-brd-skill-research-index.md (THIS FILE)
```

**Total research:** 18,000+ words across 5 documents  
**Research time:** May 28, 2026 (1 session)  
**Status:** Complete, ready for review

---

## Quick Decision Checklist

- [ ] **Approved:** 4-phase interview + persistent product.md + validation rules → Proceed to Phase 1
- [ ] **Assigned:** Skill developer (1 FTE, 4-6 weeks) for MVP implementation
- [ ] **Designed:** Phase 1 interview questions (12-15 Qs) refined with real PM feedback
- [ ] **Set:** Success metrics (non-technical PM completes interview without help, 50-80 min, generates shareable BRD+PRD)
- [ ] **Planned:** Phase 2 scope (Notion/Jira export, incremental updates, HTML view)
- [ ] **Addressed:** Unresolved questions (10 listed in tools report section 11, tools report appendix)

---

## Contact & Follow-Up

For questions about:
- **Tool landscape, frameworks, best practices** → See Tools Report (researcher-260528-0818-prd-brd-skill-tools-report.md)
- **Design trade-offs, implications** → See Design Implications (researcher-260528-0818-prd-brd-skill-design-implications.md)
- **Implementation spec, technical details** → See Recommended Architecture (researcher-260528-0818-prd-brd-skill-recommended-architecture.md)
- **Strategic decisions, next steps** → See Executive Summary (researcher-260528-0818-prd-brd-skill-executive-summary.md)

---

**Research Complete. Ready for Review & Decision.**
