---
type: brainstorm-decisions
date: 2026-05-28
skill: cleanmatic:product-spec
status: interview-complete (~100 Q / 18 rounds; ready for /ck:plan)
related-reports:
  - researcher-260528-0818-prd-brd-skill-tools-report.md
  - researcher-260528-0818-prd-brd-skill-recommended-architecture.md
  - researcher-260528-0818-prd-brd-skill-design-implications.md
  - researcher-260528-0818-prd-brd-skill-executive-summary.md
  - researcher-260528-0818-prd-brd-skill-research-index.md
---

# Brainstorm Decisions — `cleanmatic:product-spec` skill

Living decisions log. Sacrifice grammar for concision. Decisions are STICKY (user-confirmed) unless user revises.

## 0. Goal (one line)
A Claude skill for **non-technical product owners** (no code, product-centric) that interviews PO via AskUserQuestion to produce + maintain a traceable product spec hierarchy (Vision→BRD→PRD→Epic→Story), persists product context, validates scope/consistency, and visualizes the tree.

## 1. Identity & architecture
- **Name/namespace:** `cleanmatic:product-spec` (built here in cleanmatic-skills; user-invocable slash command).
- **Architecture:** ONE user-facing skill + heavy logic in `references/` loaded on-demand (lean SKILL.md).
- **Scope model:** SINGLE product per workspace (one context file at known path).
- **Audience:** product owner, non-technical.
- **Language:** BILINGUAL/configurable. `lang: en|vi` field in PRODUCT.md; default English. Localizes PROSE + interview only; frontmatter KEYS + IDs stay stable-English for scripts.
- **Build standard:** follow `skill-creator` conventions (init_skill.py template, references/, scripts/ via shared .venv, eval suite, README/anatomy standard).

## 2. Document model (user's model — OVERRIDES research's "single unified doc")
Hierarchy, STRICT traceability (every child links parent + ultimately a business goal):
```
Vision (separate doc)  →  BRD (ONE, product-wide)  →  PRD (MANY, per feature-area)  →  Epic  →  User Story (+AC)
```
- **Artifacts:** BRD, PRD, Epic, User Story. PRD owns narrative+scope+NFR+metrics; stories = executable decomposition tracing back to PRD reqs (avoids overlap/duplication).
- **BRD vs PRD:** ONE BRD (whole business/product) ; MANY PRDs (one per major feature-area). Epics/stories hang under PRDs.
- **Vision vs context file:** Context = FACTS (atomic one-liners/labels). Vision = STRATEGY (narrative/reasoning). Traceability root = Vision.
- **DRY rule:** one authoritative home per fact. Concept may appear at increasing depth but each fact authored once, expanded never contradicted downstream.

## 3. Product context file ("claude.md placeholder")
- **Path:** `docs/product/PRODUCT.md`.
- **Content (one-liners/labels ONLY — fast-load index / source-of-truth header):**
  - 5 originals: product name, product description, current implementation, deployment, roadmap summary
  - + target users/personas (NAMES/labels only; full profiles live in vision/PRD)
  - + core value / north-star (ONE sentence = yardstick for scope checks)
  - + tech/deploy stack details (under current-impl/deployment)
  - + `lang: en|vi` setting
- **First-run flow:** scaffold template THEN guided init interview to fill it (best of both: option 2 then 1), then proceed to requested action.

## 4. Validation engine
- **Mechanism:** HYBRID. Scripts = structural/deterministic ONLY (zero heuristic judgment). LLM = ALL judgment/semantic.
- **Severity:** CONFIGURABLE, DEFAULT WARN. `--strict` blocks on hard errors (broken traceability / missing AC). Never block by default (PO-friendly).

### Script vs LLM split (user-confirmed "exactly")
| Check | Owner |
|---|---|
| Parse docs, read YAML frontmatter | Script |
| Build story→epic→PRD→BRD→goal graph from explicit links | Script |
| Structural orphan / dangling link (target ID missing) | Script |
| AC PRESENCE (field exists, non-empty, count) | Script |
| ID integrity / duplicate IDs / broken refs | Script |
| Build/refresh traceability matrix table | Script |
| INVEST QUALITY (too big? vague? negotiable?) | LLM |
| AC TESTABILITY (semantic: "user-friendly" = not testable) | LLM |
| Off core-value drift / gold-plating / over-spec | LLM |
| Semantic duplicate / overlap | LLM |
| Contradiction detection | LLM |
| "Why building this" (judgment beyond structural orphan) | LLM |

### Scope checks (all in): out-of-scope items, off-core-value drift, orphans/dangling, gold-plating/over-spec.
### Consistency checks (all in): INVEST, AC presence, duplicate/overlapping, contradiction.
### Core-value mechanic: LLM scores each PRD/epic/story vs PRODUCT.md core-value sentence (aligned / weak / off + rationale); PO confirms scope-tag; script only checks tag exists & links resolve.
### Flow: scripts emit structural-truth JSON → LLM layers semantic judgment → human-readable report.

## 5. Scripts (Python, shared .venv)
- **I/O:** scripts emit JSON findings; LLM reads JSON, adds judgment, writes human report. (Scripts do NOT mutate docs / auto-fix.)
- **Script set (all):**
  1. `generate-templates` — scaffold PRODUCT/vision/BRD/PRD/epic/story from templates.
  2. `check-traceability` — parse docs, build graph, flag orphans/dangling/structural-scope → JSON.
  3. `check-consistency` — STRUCTURAL only (AC presence, ID integrity, dup IDs) → JSON.
  4. `build-traceability-matrix` — render matrix table + artifact/ID/status index.
  5. (viz renderer — see §8)

## 6. Interview (skill→PO; NOT the 100-Q brainstorm)
- **Delivery:** AskUserQuestion batches (≤4), options pre-filled w/ best-practice defaults.
- **Adaptivity:** adaptive + 5-Why follow-ups; skip Qs already answered by PRODUCT.md.
- **Frameworks:** 5-Why + **MoSCoW** (scope-gate yardstick) + **Story-Mapping** ("walk me through a user's day" → surfaces missing stories). (Kano secondary, not required.)
- **Pacing:** PHASED + RESUMABLE. Save answers per phase to `docs/product/.session.md`; PO can quit/resume; file archived/removed when phase completes.

## 7. Output / storage / lifecycle
- **Layout:** TYPED SUBFOLDERS under `docs/product/`:
  `PRODUCT.md`, `vision.md`, `brd.md`, `prds/<feature>.md`, `epics/<epic>.md`, `stories/<story>.md`.
- **Granularity:** epics & stories = SEPARATE files each w/ full frontmatter.
- **Update flow:** DELTA UPDATE — load existing, ask only what changed, regenerate affected artifacts, append dated change-log. Preserve prior decisions.
- **Doc drift (PO hand-edits):** FRONTMATTER = SOURCE OF TRUTH. `--validate` detects prose/frontmatter mismatch + stale links + reports. Skill NEVER silently overwrites manual prose edits.
- **Status lifecycle:** `draft → review → approved` (frontmatter). Sign-off → approved. Validate can warn on approved docs w/ open issues.
- **Versioning:** per-artifact semver-lite (v1.0, v1.1 bumped on approved change) + git as real log + change-log summarizes.

## 8. Visualization (first-class feature, in-skill self-contained)
- **Approach:** in-skill self-contained (own Python). No cross-skill dependency.
- **Data source/trigger:** script reads frontmatter → JSON (same JSON as build-traceability-matrix) → render. Single source of truth.
- **Content (all):** traceability tree, coverage/status heatmap, scope/value map, roadmap timeline, **+ persona×feature coverage, gap-analysis (unaddressed parents), delta/diff view, MoSCoW quadrant + risk matrix**.
- **Formats (all):** ASCII tree (terminal), Mermaid (in-markdown), interactive HTML (self-contained, collapsible/zoomable), static SVG/PNG.

## 9. Flags / CLI surface
- `--product <file|prompt>` — load/seed product context.
- Core gen: `--brd`, `--prd`, `--epic`, `--story`.
- `--auto` — **brain-dump → decompose**: PO pastes messy braindump; skill auto-splits into BRD goals/PRDs/epics/stories w/ traceability + flags ambiguities for confirmation.
- `--validate` (checks+matrix), `--summary` (exec one-pager+HTML), `--strict` (block hard errors).
- visualization flags (tree/html/graph/etc.).
- **No-flag default:** DETECT STATE → MENU. No PRODUCT.md → init. Else short AskUserQuestion menu (new BRD? new PRD? add stories? validate? update? visualize?).

## 10. Exec artifacts (all in)
- Change-log (dated entry per delta-update).
- 1-page exec summary (markdown, optional HTML).
- Sign-off block (owner/stakeholder fields in BRD/PRD frontmatter).

## 11. Frontmatter schema (rich — "as detailed as possible")
Every artifact carries: `id`, parent-link(s), `status` + :
- priority `moscow: must|should|could|wont` + `scope: in|out|core-value`
- `size: S|M|L` + `horizon`/roadmap-phase
- `owner`, `created`, `updated`, `version`
- `personas: [labels]` + success-metric refs
- **ID scheme:** stable prefixed IDs (e.g. BRD-G1, PRD-AUTH, E1, S1) stored in frontmatter; scripts parse for graph. (NOT slug-based — fragile on rename.)

## 12. Handoff & references & eval
- **Engineering handoff:** NONE. Skill ends at approved product docs (product-only, no ck:plan export).
- **references/ (all + skill-creator standard):** artifact templates, interview question banks (phase-by-phase, bilingual, MoSCoW/5-Why/story-map prompts), validation rules spec (check catalog + severities + JSON schema), frontmatter+ID spec. Plus whatever skill-creator anatomy standard requires (README, etc.).
- **Eval:** YES — 3-5 scenario evals (init-from-scratch, brain-dump decompose, validate-catches-orphan, delta-update) + script unit tests.

## 13. MVP scope
- **v1 = EVERYTHING discussed** (full surface in one pass). User explicitly chose full build over phased MVP.

## Conflicts resolved (research vs user — user wins, logged per rules)
1. Research: single unified BRD+PRD doc → **User: separate docs**. Reason: better traceability + rich frontmatter.
2. Research: fat single `product.md` (vision+personas+scope+metrics) → **User: thin labels-only PRODUCT.md**; depth in vision/BRD. Reason: DRY.
3. Research: rule-based heuristic validation (INVEST scan, 85% threshold, effort/velocity) → **User: scripts structural-only, LLM judgment**. Reclassified INVEST/vagueness/scope-drift/timeline → LLM.
4. Research: effort-points ÷ velocity timeline check → **User: T-shirt + calendar qualitative LLM flag** (engineering-flavored math dropped; PO-friendly).

## 14. Template skeletons (sections; templates mark REQUIRED vs OPTIONAL)
- **Cross-cutting rule:** every template distinguishes REQUIRED (always generated) vs OPTIONAL (offered/collapsible) sections so simple products stay lean.
- **Vision:** strategy core (problem narrative, full personas, value prop, north-star, 1-3yr direction) + principles/non-goals + differentiation.
- **BRD (1, product-wide):** standard business set (problem/opportunity, goals+metrics, stakeholders, constraints, market) + assumptions&risks + goal→metric table. Some sections optional.
- **PRD (per feature):** standard product set (overview/problem, personas, use cases/flows, functional reqs MoSCoW, NFRs, success metrics→BRD goals) + explicit scope in/out + dependencies&risks + open-questions. Some sections optional.
- **Epic:** RICH — goal, business-context (→PRD req + BRD goal), success criteria, scope, risks.
- **Story:** RICH — As-a/I-want/so-that, AC list, size, personas, notes.

## 15. Viz library / auto UX / deferred / metadata
- **HTML viz renderer:** FLAG-DRIVEN by user choice — PO picks output per invocation (tree / Mermaid-in-md / interactive HTML / SVG; HTML richness selectable). Not one fixed lib.
- **--auto brain-dump UX:** decompose → propose full split → AskUserQuestion CONFIRM BATCH on ambiguous items (story vs epic? which PRD?) before writing.
- **Deferred / Won't-have:** `scope: out` / `moscow: wont` + target horizon, item STAYS IN PLACE (single home, full history); viz filters them out.
- **Skill metadata:** `category: product`, `argument-hint: [--flag] [target]`, `keywords: [prd, brd, epic, story, product-owner, requirements, traceability]`, `user-invocable: true`.

## 16. Disambiguation / evals / sign-off / session hygiene
- **Multi-PRD targeting:** ARG + MENU FALLBACK — accept target arg (`--prd auth`); if omitted, AskUserQuestion list of existing PRDs.
- **Eval scenarios (all 4):** init-from-scratch, brain-dump decompose, validate-catches-issues (orphan + missing AC + off-core-value seeded → flags exactly those), delta-update + viz.
- **Sign-off:** explicit `--approve` action → runs validation first, WARNS (not blocks) on open issues, records owner+date, flips status→approved.
- **.session.md git:** COMMITTED (track for cross-machine/teammate resume).

## 17. Edge cases
- **Contradictory delta-update:** SURFACE + ASK, never auto-flip. Show prior approved decision verbatim vs new input → PO keeps/changes/hybrid → log resolution in change-log. (Matches no-silent-reversal rule.)
- **Duplicate feature/story across PRDs:** LLM flags as semantic duplicate (validation overlap check) → PO decides merge / keep-both / cross-link. Skill never auto-merges.
- **Stale .session.md on next run:** detect → show phase/answers present → PO resume or discard (start fresh).
- **Very large brain-dump (--auto):** CHUNK + incremental confirm — process in sections, decompose each, batch-confirm, accumulate into tree. Scales.

## 18. Skill docs, eval bar, bilingual, roadmap vocab
- **Skill docs:** README (quickstart + flag reference) + `examples/` (worked sample product spec) + full step-by-step walkthrough + **CLAUDE.md inside skill dir** (detailed guide/context for the LLM running the skill). SKILL.md stays lean.
- **Eval bar:** BOTH — structural assertions (expected files created, frontmatter valid, scripts emit expected JSON findings e.g. orphan detected) + LLM-graded rubric (prose quality 0-100 above threshold).
- **Bilingual question banks:** author BOTH EN + VI now (full bilingual v1).
- **Roadmap horizon vocabulary:** `now / next / later` (outcome-oriented, avoids false date precision; PO-friendly).

## Interview status: COMPLETE (~100 Q across 18 rounds)
All architecture, behavior, edge-case, and packaging decisions captured. No open interview items remain. Ready for `/ck:plan`.

## Amendments — 2026-05-28T23:03 (post-build hardcore review)

The hardcore review (4-wave audit) surfaced two decision drifts. Per CLAUDE.md → "No silent reversals", both surfaced to PO for keep/change/hybrid. Recorded answers below; amendments are STICKY going forward (override original wording).

### Amendment to §15 — Deferred items in viz

**Original (§15, last bullet):** "Deferred / Won't-have: `scope: out` / `moscow: wont` + target horizon, item STAYS IN PLACE (single home, full history); viz filters them out."

**PO decision (2026-05-28):** show all by default with a visual marker; opt-in filter via flag.

**Amended rule:**
- `tree`, `roadmap`, `persona` views show deferred items (`moscow == wont` OR `scope == out`) by default with a trailing `*` marker (ASCII) / `:::deferred` classDef (Mermaid).
- `--filter-wont` flag opt-in to hide them entirely.
- `scope`, `moscow`, `heatmap`, `gap`, `risk`, `delta` views always show all (the data itself is the point of those views).

**Rationale:** marking-not-hiding gives the PO visibility of deferred work (single home rule still holds) while making the deferred status visually obvious. Filtering is one flag away when noise becomes a problem.

### Amendment to §18 — CLAUDE.md location

**Original (§18):** "CLAUDE.md inside skill dir (detailed guide/context for the LLM running the skill). SKILL.md stays lean."

**PO decision (2026-05-28):** keep current implementation (repo-root CLAUDE.md only); amend §18 with rationale.

**Amended rule:**
- The operating-guide content is absorbed by `SKILL.md` + `references/*.md` (loaded on demand by flag), both of which DO ship inside the skill ZIP.
- Repo-root `CLAUDE.md` is a dev-side guide (auto-loaded by Claude Code in this development repo). It is NOT part of the shipped skill.
- No `.claude/skills/product-spec/CLAUDE.md` is required or maintained.

**Rationale:** SKILL.md + references/ already absorb the operating guide; root CLAUDE.md placement matches Claude Code's auto-load convention for dev sessions; a duplicated in-skill CLAUDE.md would drift over time and add no new content.

## Unresolved questions (minor — for planning)
- HTML rich-interactive mode: vendor JS inline (heavier, offline) vs CDN-pin (lighter, needs net).
- Persona cap (2-4): hard cap vs soft guidance — confirm during planning.
- VI question-bank: who reviews Vietnamese phrasing quality.
