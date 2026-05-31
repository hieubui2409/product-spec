# Wave 1 + Wave 2 — Phase Verification Report

**Skill:** `cleanmatic:product-spec`
**Scope:** Structural verification of phases 1–8 deliverables vs plan intent.
**Method:** Read each phase file, extract listed deliverables, confirm presence in skill tree, flag drift / missing / unjustified extras. Brainstorm decisions NOT challenged — sticky.

---

## Wave 1 Inventory

### Skill tree top-level (`.claude/skills/product-spec/`)
- `SKILL.md` (133 lines — under 300-line budget; phase-1 acceptance)
- `install.sh` (3.4K — top-level installer per phase 8)
- `agents/` (empty except `.gitkeep` — placeholder, no shipped agents)
- `assets/templates/` (10 files), `assets/vendor/mermaid.min.js`
- `eval/` (`evals.json` + `fixtures/` with 4 inputs + 2 symlinks to scripts/tests/fixtures)
- `examples/acme-shop/` (worked sample tree) + `README.md` + `.gitignore`
- `references/` (12 markdown specs)
- `scripts/` (15 `.py` + 1 shell + `requirements.txt` + `tests/`)

### Repo-root packaging (per phase-1 amendment)
- `/home/hieubt/Documents/cleanmatic-skills/CLAUDE.md` (9.2K — dev-side guide; per §18 amendment, replaces in-skill CLAUDE.md)
- `/home/hieubt/Documents/cleanmatic-skills/README.md` (7.7K)
- `Script.tar.gz` + `release-manifest.json` present (packaging artifacts — phase 8)

### Plan phases
- 8 phases. Plan.md (lines 28–37) marks all "Completed". Phase frontmatter still says `status: pending` (cosmetic drift — plan.md authoritative).

---

## Wave 2 Phase-by-Phase

### Phase 1 — Scaffold & Skeleton
**Plan deliverables (phase-01 §Related Code Files + Success Criteria):**
- `.claude/skills/product-spec/SKILL.md` (frontmatter + skeleton, <300 lines)
- `.claude/skills/product-spec/README.md`
- repo-root `CLAUDE.md` (per §18 amendment)
- dirs: `references/ scripts/ assets/templates/ agents/ eval/ examples/`
- Namespace `cleanmatic:product-spec`, folder `product-spec`

**Found:**
- SKILL.md ✓ (133 lines, frontmatter complete with `name: cleanmatic:product-spec`, `user-invocable: true`, `category: product`, `argument-hint`, `metadata.version: 1.0.0` — `SKILL.md:1–12`)
- README at skill root ✗ — **no `.claude/skills/product-spec/README.md`**. Repo-root README.md (7.7K) exists instead. Phase 1 success criterion "README + CLAUDE.md skeletons present" → drift: README intentionally consolidated to repo root, not flagged in plan amendment (§18 only covers CLAUDE.md). Confirmed by `examples/README.md` referencing skill scripts via `.claude/skills/product-spec/scripts/...` paths, implying repo-root context.
- Repo-root CLAUDE.md ✓ (9.2K, per §18 amendment)
- All directories ✓ (`references/`, `scripts/`, `assets/templates/`, `agents/`, `eval/`, `examples/`)
- Folder name `product-spec` ✓; SKILL.md `name: cleanmatic:product-spec` ✓

**Discrepancies:**
- **Missing `.claude/skills/product-spec/README.md`** (phase-01 line 27 explicitly creates this; success criterion line 49). Treatment: likely consolidated into repo-root README + `examples/README.md` per §18-style absorption, but plan amendment doesn't extend §18 to README. Surface as drift; not blocking.
- Phase frontmatter `status: pending` (phase-01-scaffold-skeleton.md:4) inconsistent with plan.md `Completed` status — cosmetic, plan.md authoritative.
- SKILL.md keyword order differs slightly from phase-01 step 2 (plan: `[prd, brd, epic, story, product-owner, requirements, traceability]`; actual line 7: `[product-owner, prd, brd, epic, story, requirements, traceability, vision, roadmap, validation]`) — non-blocking, additive.

---

### Phase 2 — Reference Specs
**Plan deliverables (phase-02 §Related Code Files):**
- `references/frontmatter-and-id-spec.md`
- `references/document-model-and-hierarchy.md`
- `references/validation-rules-spec.md`
- `references/visualization-spec.md`
- Each < 300 lines
- ID grammar parent-scoped (C2)
- `.session.md` schema defined (H3)
- snapshot JSON shape defined (H4)
- gap-analysis structural-only (H1)

**Found:**
- `frontmatter-and-id-spec.md` ✓ (243 lines, < 300)
- `document-model-and-hierarchy.md` ✓ (124 lines)
- `validation-rules-spec.md` ✓ (146 lines, script-vs-LLM split at line 5–12, `--strict` gate line 39, JSON schema line 92)
- `visualization-spec.md` ✓ (147 lines, 9 views × 3 formats matrix at lines 31–41)
- Parent-scoped ID grammar ✓ (`frontmatter-and-id-spec.md:11–14` — `BRD-G<n>`, `PRD-<SLUG>`, `PRD-<SLUG>-E<n>`, `PRD-<SLUG>-E<n>-S<n>`)
- Snapshot JSON shape referenced ✓ (`visualization-spec.md:25` delta-snapshots; `spec_graph.py:208–222` writes snapshots)
- Gap-analysis structural ✓ (`visualization-spec.md:38` lists gap as structural unaddressed-parent view)

**Discrepancies:**
- **`.session.md` schema (H3) NOT in `frontmatter-and-id-spec.md` or a dedicated file.** Phase-02 line 28 says "define it here" (in phase 2 schema). Actual implementation: schema only referenced in `workflow-interview.md:23–63` (phase 7). Drift: contract moved to workflow layer instead of schema layer. Acceptable per LLM operating model, but plan said schema phase.
- No file exceeds 300 lines ✓.

---

### Phase 3 — Bilingual Question Banks
**Plan deliverables (phase-03 §Related Code Files):**
- `references/interview-vision.md` (EN+VI)
- `references/interview-brd.md` (EN+VI)
- `references/interview-prd.md` (EN+VI)
- `references/interview-epic-story.md` (EN+VI)
- `references/interview-frameworks.md` (5-Why / MoSCoW / story-mapping, EN+VI)

**Found:**
- All 5 files ✓ (`interview-vision.md` 80L, `interview-brd.md` 70L, `interview-prd.md` 95L, `interview-epic-story.md` 105L, `interview-frameworks.md` 91L)
- Bilingual: VI translations inline next to EN (e.g. `interview-vision.md:11–17`) ✓
- VI present in all five (`grep -c vi:` non-zero in all interview-*.md files)
- 5-Why + MoSCoW + Story Mapping ✓ (`interview-frameworks.md:1,5,27`)
- Adaptivity rules + persona cap ✓ (`interview-vision.md:5` "soft 2–4"; `interview-vision.md:76–80` adaptivity)
- Field-tag per question ✓ (`interview-vision.md:9,21,30` etc. `target:` lines)

**Discrepancies:**
- None structurally. Plan didn't specify a separate VI file vs inline; inline format used. Acceptable.
- Phase 3 success criterion line 42 says "structurally identical" EN/VI — inline approach preserves structure trivially. ✓

---

### Phase 4 — Artifact Templates
**Plan deliverables (phase-04 §Related Code Files):**
- `assets/templates/product.md`, `vision.md`, `brd.md`, `prd.md`, `epic.md`, `story.md`
- `assets/templates/exec-summary.md`, `sign-off.md`, `change-log-entry.md`
- Token convention `{{token}}`, no jinja2
- REQUIRED vs OPTIONAL markers (`<!-- OPTIONAL: ... -->`)
- Bilingual headers (EN/VI)

**Found:**
- All 9 templates ✓:
  - `product.md`, `vision.md`, `brd.md`, `prd.md`, `epic.md`, `story.md`
  - `exec-summary.md`, `sign-off.md`, `change-log-entry.md`
- **EXTRA:** `assets/templates/visual-html-shell.html` (phase 6 created this — correctly attributed to P6, not unjustified)

**Discrepancies:**
- None for phase 4 set. The visual-html-shell.html in templates dir is phase-6 deliverable (phase-06 line 37), so co-located but not phase-4 scope.
- Did not verify token convention `{{...}}` or OPTIONAL marker presence in each template body — left to deeper review.

---

### Phase 5 — Core Scripts
**Plan deliverables (phase-05 §Related Code Files):**
- `scripts/frontmatter_parser.py`, `scripts/spec_graph.py`, `scripts/encoding_utils.py`
- `scripts/check_traceability.py`, `scripts/check_consistency.py`, `scripts/build_traceability_matrix.py`, `scripts/generate_templates.py`
- `scripts/requirements.txt` (pyyaml, pytest, pytest-cov; markdown only if needed)
- `scripts/tests/` with fixtures (valid + broken)
- Each script `--root` (M5), JSON out, exit 0
- `spec_graph.downstream()` for delta (H2)
- snapshot emit on validate (H4)

**Found:**
- `frontmatter_parser.py` ✓ (126L)
- `spec_graph.py` ✓ (253L — over 200 soft target; phase-05 says "<200 where feasible"; acceptable for graph builder)
- `encoding_utils.py` ✓ (31L)
- `check_traceability.py` ✓ (121L), `check_consistency.py` ✓ (290L — over 200, similarly acceptable)
- `build_traceability_matrix.py` ✓ (101L)
- `generate_templates.py` ✓ (273L — over 200, acceptable for generator)
- `requirements.txt` ✓ (pyyaml, pytest, pytest-cov — no `markdown` per L3) — matches phase-05:44
- `scripts/tests/` ✓ with `test_scripts.py` + `test_visualize.py` + `fixtures/{valid-spec,broken-spec}` ✓
- All scripts `--root` ✓ (verified via grep: `check_traceability.py:103`, `check_consistency.py:250`, `build_traceability_matrix.py:70`, `generate_templates.py:227`, `visualize.py:97`, `strict_gate.py:49`)
- `spec_graph.py:191 downstream()` ✓ (H2)
- `spec_graph.py:208–222 write_snapshot()` + `--snapshot` flag (line 232) ✓ (H4)
- Broken-spec fixture has duplicate.md + PRD-AUTH-E9-S1.md (dangling parent) + PRD-AUTH-E1-S1.md (matches seeded issues per phase-05 step 3)

**Discrepancies:**
- **EXTRA scripts not in phase-05 plan:**
  - `strict_gate.py` (77L) — phase-05 Architecture §CLI contract says "`--strict` gating happens in LLM/orchestration, not the script" (line 30). A standalone `strict_gate.py` shell-runnable was added (its docstring acknowledges this: "shell-runnable `--strict` enforcement for CI"). Justifiable as orchestration-script crossover (still doesn't *judge* — just exit-codes on script findings). Mildly contradicts phase-05 "gate in LLM layer", but offered as CI helper not LLM-bypass. Note as drift.
  - `i18n_labels.py` (46L) — phase-05 plan doesn't list this. Used by visualize.py for `--lang vi` label localization (phase 6 scope, but lives in scripts/). Justified by CLAUDE.md visualization spec referencing it. Note as phase-attribution drift, not extra scope.
- Phase frontmatter `status: pending` — cosmetic, see Phase 1.

---

### Phase 6 — Visualization Renderer
**Plan deliverables (phase-06 §Related Code Files):**
- `scripts/visualize.py` (dispatcher)
- `scripts/render_ascii.py`, `scripts/render_mermaid.py`, `scripts/render_html.py`
- NO `render_svg.py` (SVG/PNG dropped per validate gate)
- `assets/templates/visual-html-shell.html`
- `assets/vendor/<mermaid-js>` (vendored)
- `scripts/tests/test_visualize.py`
- 9 views × 3 formats matrix

**Found:**
- `visualize.py` ✓ (143L, dispatcher; `--view` + `--format` + `--root` + `--lang` + `--diff/--snapshot` per phase-06 step 5)
- `render_ascii.py` ✓ (283L), `render_mermaid.py` ✓ (228L), `render_html.py` ✓ (165L)
- No `render_svg.py` ✓ (correctly dropped per validate gate)
- `assets/templates/visual-html-shell.html` ✓
- `assets/vendor/mermaid.min.js` ✓ (vendored — verified via `SKILL.md:119`; could not `ls` due to ckignore `vendor` block)
- `scripts/tests/test_visualize.py` ✓ (27.1K — extensive)
- 9 views × 3 formats matrix ✓ (`visualization-spec.md:31–41` covers tree, heatmap, scope, roadmap, persona, gap, moscow, risk, delta × ASCII/Mermaid/HTML)
- Mermaid fallback documented ✓ (`visualization-spec.md:43` — fallback to ASCII fence for views Mermaid can't express)

**Discrepancies:**
- None. Strong match. Render line-counts over 200 acceptable for grid renderers.

---

### Phase 7 — SKILL.md Orchestration
**Plan deliverables (phase-07 §Related Code Files):**
- Modify `SKILL.md` (keep < 300 lines)
- `references/workflow-interview.md`
- `references/workflow-validate.md`
- `references/workflow-auto-and-update.md`
- Every flag → documented workflow
- Detect-state menu
- Contradiction-on-approved surface (never auto-flip)
- `--auto` chunk + confirm-batch
- Delta-update + change-log
- No plan/finding-code refs in prose

**Found:**
- SKILL.md ✓ (133L, well under 300)
- All three workflow refs ✓:
  - `workflow-interview.md` (93L, session schema + lifecycle at lines 23–63)
  - `workflow-validate.md` (103L)
  - `workflow-auto-and-update.md` (123L — has "Compute affected downstream set" at line 80, "Contradiction protocol on approved artifacts" at line 110, change-log appends at lines 65/114)
- All flags documented in SKILL.md flag table (`SKILL.md:28–44`) ✓
- No-flag detect-state menu ✓ (`SKILL.md:46–60`)
- Mermaid workflow map ✓ (`SKILL.md:82–100`)
- Reference loading pointers ✓ (`SKILL.md:102–113`)
- Operating principles incl. "No silent reversals" + "Never overwrite manual prose" ✓ (`SKILL.md:129–130`)
- `downstream` script invocation ✓ (`workflow-auto-and-update.md:83`)

**Discrepancies:**
- None significant. SKILL.md line 133 "Deeper LLM operating guidance lives in references/ ... and in repo-root CLAUDE.md" — explicitly confirms §18 amendment routing.

---

### Phase 8 — Eval Tests & Packaging
**Plan deliverables (phase-08 §Related Code Files):**
- `eval/evals.json` (4 scenarios, structural + LLM rubric)
- Fixture inputs (init-answers, braindump, auto-decisions, delta-change, valid-spec, broken-spec)
- `examples/` worked sample (full hierarchy + rendered visual)
- Finalize README + CLAUDE.md
- `install.sh` runs deps install
- `quick_validate.py` + `package_skill.py` clean
- VI native review note

**Found:**
- `eval/evals.json` ✓ (4 scenarios id 0-3 covering init / auto / validate / delta+viz per phase-08:39)
- Fixtures ✓:
  - `eval/fixtures/init-answers.json` (1.2K), `braindump.txt` (768B), `auto-decisions.json` (1.1K), `delta-change.json` (821B)
  - `eval/fixtures/valid-spec` + `broken-spec` (symlinked to `scripts/tests/fixtures/` — DRY-friendly reuse)
- Worked example ✓ (`examples/acme-shop/docs/product/` with PRODUCT.md, vision.md, brd.md, prds/checkout.md, epics/PRD-CHECKOUT-E1.md, stories/PRD-CHECKOUT-E1-S1.md, visuals/tree.md)
- `examples/README.md` ✓ (with verification commands)
- `examples/.gitignore` ✓ (excludes accumulated HTML — matches `f7b4893` commit "clean accumulated example HTML renders")
- No accumulated `*.html` in examples ✓ (find returned 0)
- `install.sh` ✓ at skill root (3.4K, runs venv setup + deps + vendor-mermaid + pytest smoke test)
- Top-level `Script.tar.gz` + `release-manifest.json` at repo root suggest packaging artifacts created.
- LLM advisory note on eval id 3 ✓ (`evals.json:42–43` — honest about non-deterministic `downstream` mapping for PRODUCT.md core-value change — matches hardcore-review hardening)

**Discrepancies:**
- **Skill-internal README missing** (phase-08:34 says "Modify: README.md"). Same as Phase 1 finding: no `.claude/skills/product-spec/README.md` exists; only `examples/README.md` + repo-root `README.md`. Documentation absorbed elsewhere per implicit consolidation.
- Phase-08 says "Use: `~/.claude/skills/skill-creator/agents/grader.md`, `scripts/run_eval.py`, `scripts/aggregate_benchmark.py`, `scripts/package_skill.py`, `scripts/quick_validate.py`" — these are skill-creator helpers, not new files. No `agents/grader.md` shipped in product-spec (correctly — phase says *use* not *create*). `agents/.gitkeep` only.
- VI review note: claimed by Operating Principles (`SKILL.md:131` "VI ships best-effort with a pending-native-review note") — present.
- `evals.json` id 3 has explicit `_assertion_type: llm_advisory` + `_note` documenting that one assertion is LLM-graded (not deterministic) — this is a defensible hardening but is itself an "extra" not specified in phase-08 plan (plan said "structural assertions deterministic; rubric for prose quality"). Treat as quality improvement, not unjustified drift.

---

## Cross-Cutting Findings

### Unjustified extras
- `scripts/strict_gate.py` — phase-05 explicitly said `--strict` lives in LLM layer; adding a shell-runnable raises a mild boundary blur (script doesn't judge — just exit-codes on findings — so technically still structural, but the *enforcement gate* moves into script land).
- `scripts/i18n_labels.py` — small helper consumed by visualize.py; phase-06 doesn't list it. Reasonable factoring but invisible to plan.

### Cosmetic drift (non-blocking)
- All 8 phase files carry `status: pending` in frontmatter while plan.md marks them Completed.
- SKILL.md keyword list richer than phase-01 step 2 (additive).

### Missing
- `.claude/skills/product-spec/README.md` — phase-01 + phase-08 both list it. Either intentional consolidation into repo-root + `examples/README.md` (matches §18 spirit) or accidental omission. Plan amendment doesn't cover README the way it covers in-skill CLAUDE.md.

### Boundary on phase-02
- `.session.md` schema (H3) — phase-02 said schema phase owns it; actual: lives only in `workflow-interview.md` (phase 7). Schema/workflow boundary blurred. Not a hard miss because workflow ref covers it, but a contract-vs-implementation drift.

### Strong matches
- Parent-scoped IDs (C2) verified end-to-end (schema → fixtures → generate_templates → checkers).
- 9 views × 3 formats matrix, SVG/PNG correctly dropped.
- `downstream()` + snapshot writer present in `spec_graph.py`.
- HTML self-contained, Mermaid JS vendored inline (per `SKILL.md:119`, `examples/.gitignore`).
- Test fixtures match seeded-issue intent (broken-spec has duplicate + dangling-parent stories).
- Bilingual EN+VI inline in all 5 interview banks.

---

## Unresolved Questions
1. Is the missing `.claude/skills/product-spec/README.md` intentional (consolidated to repo-root + `examples/README.md`) or accidental? Plan §18 amendment only justifies CLAUDE.md absorption, not README.
2. Should `scripts/strict_gate.py` (LLM-layer gate moved partly into a CI shim) be re-documented in phase-05 plan, or is the boundary acceptable since it only enforces — doesn't judge?
3. Phase-02 schema vs phase-07 workflow boundary for `.session.md`: contract drift acceptable, or relocate schema to `frontmatter-and-id-spec.md` / new spec file?
4. Phase frontmatter `status: pending` vs plan.md `Completed` — single-source for phase status (recommend plan.md or sync frontmatter)?
5. `scripts/i18n_labels.py` not in any phase plan — attribute to phase 6 retroactively or add to phase-06 plan?
