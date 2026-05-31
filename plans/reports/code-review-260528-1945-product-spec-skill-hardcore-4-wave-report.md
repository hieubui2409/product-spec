---
type: code-review
date: 2026-05-28
target: .claude/skills/product-spec/
plan: plans/260528-0912-cleanmatic-product-spec-skill/
build_by: Codex + Gemini (per user)
reviewer: claude (sonnet/opus hardcore — ultrathink, 4-wave)
methodology: Wave1 scan-all → Wave2 deep-dive → Wave3 hardcore → Wave4 cross-validate (brainstorm → plan → reports → impl)
sticky-decisions-ref: plans/reports/brainstorm-decisions-260528-0818-cleanmatic-product-spec-skill-report.md
implementation-report-ref: plans/reports/from-cook-to-pm-260528-1747-product-spec-skill-implementation-report.md
---

# Hardcore Review — `cleanmatic:product-spec` (4-wave)

## TL;DR

Build is **functionally clean** on the structural layer (31/31 pytest, worked example validates, parent-scoped IDs correct, script-vs-LLM split honored). However it ships with **5 critical drifts from the plan/brainstorm**: (1) repo venv missing, (2) vendored Mermaid JS empty → "offline self-contained" promise BROKEN, (3) eval fixtures referenced by `evals.json` do NOT exist (evals unrunnable), (4) HTML renderer has a bug for ASCII-only views (heatmap/persona/risk render as broken Mermaid), (5) skill-folder `CLAUDE.md` + `README.md` are DEAD CODE — Claude Code never auto-loads files at that path (per official docs); both must move to project root + SKILL.md:133 manual ref dropped.

**Verdict:** ship-blocker for v1 production. Engineering quality is high; correctness vs the contract is not.

| Severity | Count | Block ship? |
|----------|-------|-------------|
| **CRITICAL** | 5 | yes |
| **IMPORTANT** | 6 | should fix before v1 |
| **MINOR / OBSERVATIONAL** | 8 | acceptable as known limitations |

---

## Wave 1 — Scan-all inventory (verified)

| Plan artifact | Present | Notes |
|---|---|---|
| Plan phases 1-8 | ✓ all 8 marked `Completed` in `plan.md` | matches |
| SKILL.md skeleton (P1) | ✓ 133 lines, < 300 budget | OK |
| `references/*` 4 specs (P2) | ✓ frontmatter-and-id, document-model, validation-rules, visualization | OK |
| Question banks 5 EN+VI (P3) | ✓ vision/brd/prd/epic-story/frameworks | bilingual present |
| Templates (P4) | ✓ 9 templates + visual-html-shell | OK |
| Scripts (P5) | ✓ 11 files (3 helpers + 4 checkers + generator + viz dispatcher + 3 renderers) | OK |
| Pytest tests | ✓ `scripts/tests/{test_scripts.py,test_visualize.py}` | **31/31 pass — verified** |
| Visualization renderers (P6) | ✓ ascii/mermaid/html | see CRIT-4 below |
| Workflow refs (P7) | ✓ interview/validate/auto-and-update | OK |
| Eval scaffold (P8) | ✓ `eval/evals.json` (4 scenarios) | see CRIT-3 |
| Worked example (P8) | ✓ `examples/acme-shop/` validates clean | verified |

**Verified by command:**
- `pytest .claude/skills/product-spec/scripts/tests/ -v` → 31 passed in 0.13s
- `check_traceability.py --root examples/acme-shop` → `findings: []`
- `check_consistency.py --root examples/acme-shop` → `findings: []`
- `visualize.py --view tree --format ascii --root examples/acme-shop` → renders tree

---

## Wave 2 — Deep dive (by phase)

### Phase 1 (Scaffold)
- SKILL.md at 133 lines comfortably below 300 budget. Frontmatter complete (name/desc/user-invocable/when_to_use/category/keywords/argument-hint/metadata.version). M1 namespace spike claimed passed in impl report — not independently re-verified here (would require Claude Code reload). 
- **DRIFT (CRIT-1):** repo venv `./.claude/skills/.venv/bin/python3` does NOT exist (`ls` confirms missing). Plan **constraint C1** explicitly: *"for dev/test/install in this repo, use the repo-local venv ./.claude/skills/.venv/bin/python3 ... All phase commands cite the repo venv. State this once; downstream cites it."* Every reference (SKILL.md L117, CLAUDE.md L88-89, workflow-validate L96) cites this path. As shipped, all PO commands will FAIL with "No such file or directory".

### Phase 2 (Reference specs)
- All 4 specs internally consistent. ID grammar (BRD-G<n> / PRD-<SLUG> / PRD-<SLUG>-E<n> / PRD-<SLUG>-E<n>-S<n>) verified parent-scoped, matches code regex in `check_consistency.py:33-38`.
- **`frontmatter-and-id-spec.md:18` claim mis-states code:** "single `--auto` brain-dump batch... keeps an in-memory counter". Code path in `generate_templates.py:191` always passes `session_used=[]` from CLI main; the `--id` override is the actual batch mechanism. Documentation drift from implementation — low risk but inconsistent.

### Phase 3 (Bilingual banks)
- 5 banks present, bilingual (EN | VI side-by-side). VI flagged "best-effort pending native review" — matches §15 plan + brainstorm §18 known open item.
- VI sample at `interview-frameworks.md:11-12` reads idiomatic enough on quick scan; no native review performed here.

### Phase 4 (Templates)
- 9 templates + shell. Token grammar `{{token}}` + `<!-- OPTIONAL: name -->` block markers correctly consumed by `generate_templates.render()`.
- **MINOR:** `story.md:21` declares `acceptance_criteria: {{acceptance_criteria}}` (one-line YAML). If PO passes a list value the render is `acceptance_criteria: ["a", "b"]` (JSON form, per `generate_templates.py:130-131`). Valid YAML but mixes flow style with the block style used in `frontmatter-and-id-spec.md:79-82` example. Cosmetic.

### Phase 5 (Core scripts)
- Single-responsibility, all `< 200 LOC` except `spec_graph.py` (232) and `generate_templates.py` (221) — slightly over the 200-line guide but each carries one cohesive concern. OK.
- All scripts honor `--root` (M5). All emit JSON and exit 0. Strict gate enforced in LLM layer (per `workflow-validate.md:43-47`). Split honored.
- `_status_inconsistency` (line 105) checks story→epic and epic→prd parents; PRDs vs `brd_goals` (list) NOT checked. Per-spec — not promised. Minor gap.
- `check_consistency.py` re-parses story files (line 165 `_enrich_with_ac`) — double-parse cost but isolates AC out of the graph node. Acceptable.

### Phase 6 (Visualization)
- ASCII renderers deterministic (verified by 9 unit tests in `test_visualize.py`).
- Mermaid renderers emit valid v11 syntax for tree/scope/roadmap/gap/moscow/delta; heatmap/persona/risk **intentionally fall back** to `<pre>` ASCII (`render_mermaid.py:51,94,132`). See CRIT-4 for the downstream bug.
- HTML renderer uses CDN fallback because vendor is empty — see CRIT-2.

### Phase 7 (SKILL.md orchestration)
- Flag table complete and matches brainstorm §9. No-flag menu present.
- Workflow Mermaid block in SKILL.md valid.
- `CLAUDE.md` (in skill) duplicates several principles from `SKILL.md` + workflows. Acceptable redundancy by design — but see CRIT-5.

### Phase 8 (Evals + packaging)
- Pytest passes (31/31, verified).
- Worked example validates clean (verified).
- **CRIT-3:** `eval/evals.json` references `fixtures/init-answers.json`, `fixtures/braindump.txt`, `fixtures/auto-decisions.json`, `fixtures/broken-spec`, `fixtures/valid-spec`, `fixtures/delta-change.json` — NONE of these exist in `eval/fixtures/`. The directory `eval/fixtures/` does not exist at all. The implementation report acknowledges *"Live eval runs against evals.json are scaffolded but not executed in this session"* — but the file scaffolding itself is incomplete.

---

## Wave 3 — Hardcore (bugs, security, KISS/YAGNI)

### CRIT-1 — Repo venv missing (CONSTRAINT C1 broken)
- **File:** `.claude/skills/.venv/` (does not exist)
- **Plan:** plan.md L41-44 (Global Constraints, C1)
- **Evidence:** `ls /home/hieubt/Documents/cleanmatic-skills/.claude/skills/.venv/bin/python3` → No such file or directory.
- **Impact:** SKILL.md:117, CLAUDE.md:89, workflow-validate.md:96 all hardcode `./.claude/skills/.venv/bin/python3`. First PO command fails.
- **Fix:** run `.claude/skills/install.sh` (which exists, 50KB) to create the venv; OR fall back to home venv `~/.claude/skills/.venv/bin/python3` consistently.
- **Severity:** CRITICAL — ship blocker.

### CRIT-2 — Vendored Mermaid empty → "offline self-contained" violated
- **Files:** `.claude/skills/product-spec/assets/vendor/` (empty, 0 bytes)
- **Plan:** plan.md L46-48 (validate-gate confirmed format = "ASCII + Mermaid + inline-vendored HTML"); visualization-spec.md:3 ("Mermaid JS **vendored inline**"); CLAUDE.md:97 ("No external network calls — everything runs from the repo (vendored Mermaid, stdlib + pyyaml).")
- **Evidence:** `du -b assets/vendor → 0 bytes`. Generated HTML at `examples/acme-shop/docs/product/visuals/tree-*.html` is 2837 bytes (vs. promised ~1MB), contains CDN fallback script `https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js` and warning text 2×.
- **Impact:** The KEY validate-gate decision (drop SVG/PNG to ensure "no external Mermaid-CLI binary") was made precisely to avoid network deps. As shipped, the skill REQUIRES network to render HTML — same failure mode the decision was designed to avoid.
- **Implementation report admits:** *"install.sh integration (auto-download pinned Mermaid JS) is documented but not yet wired into the repo bootstrap."* The shipped install.sh does NOT download Mermaid (verified by grep `mermaid|vendor|product-spec` in install.sh → 0 matches).
- **Fix options:**
  1. Vendor `assets/vendor/mermaid.min.js` directly (one-time commit, ~1MB blob).
  2. Add a post-install hook to install.sh to fetch the pinned version.
  3. Or accept CDN dependency and revise CLAUDE.md:97 + visualization-spec.md:3 to match reality (NOT recommended — silently reverses a confirmed user decision).
- **Severity:** CRITICAL — promise/code drift.

### CRIT-3 — Eval fixtures referenced but absent → evals unrunnable
- **File:** `eval/evals.json` references `fixtures/*` paths; `eval/fixtures/` does NOT exist.
- **Plan:** plan.md (Phase 8 deliverable); brainstorm §12 ("Eval: YES — 3-5 scenario evals"); brainstorm §16 ("Eval scenarios (all 4)").
- **Evidence:** `find eval -type f` → only `evals.json`. The 4 scenarios reference 6 fixture files/dirs that do not exist.
- **Impact:** Evals cannot be executed. The two fixtures that DO exist (`scripts/tests/fixtures/broken-spec`, `valid-spec`) are at the wrong path — used for pytest, not for evals.
- **Fix:** populate `eval/fixtures/{init-answers.json, braindump.txt, auto-decisions.json, delta-change.json, broken-spec/, valid-spec/}`. Cheapest: symlink/copy from `scripts/tests/fixtures/` and author the 4 JSON/TXT files.
- **Severity:** CRITICAL — broken deliverable.

### CRIT-4 — HTML render bug for ASCII-fallback views (heatmap/persona/risk)
- **File:** `scripts/visualize.py:91-92`; `scripts/render_html.py:57-62`; `scripts/render_mermaid.py:51,94,132`.
- **Trace:**
  - For views heatmap/persona/risk, `render_mermaid` returns `f"<pre>\n{ascii_X(graph)}\n</pre>"` (HTML, not Mermaid).
  - `visualize.py:91` calls `render_html.write(root, view, "mermaid", mermaid_text, graph, lang)` — passes view_format=`"mermaid"` unconditionally.
  - `render_html._render_view_body` (line 57-62): when format==`"mermaid"` it regex-greps for ` ```mermaid\n...\n``` `; if not matched (which is the case for our `<pre>` payload), it falls back to `body = view_text` (the raw `<pre>...</pre>` string), then wraps as `<div class="mermaid"><pre>...</pre></div>`.
  - Mermaid library will attempt to render `<pre>...</pre>` as Mermaid syntax → renders blank or shows parse error.
- **Impact:** 3 of 9 HTML views (1/3 of HTML coverage) render broken.
- **Fix:** in `visualize.py`, detect when the mermaid view returns a `<pre>` fallback and pass view_format=`"pre"` instead so `render_html` HTML-escapes and wraps cleanly. OR change `render_mermaid` fallbacks to return a sentinel that the dispatcher routes.
- **Severity:** CRITICAL — silently broken in 1/3 of view×format matrix.

### CRIT-5 — Skill-folder CLAUDE.md + README.md are DEAD CODE (must move to project root)
- **User messages (verbatim):**
  1. "CLAUDE.md must be in project root, not in skill folder."
  2. "The same for README.md must be in project root."
  3. "Claude.md auto append to context, no need manual ref. Check claude guide..."
- **Authoritative finding (Claude Code official docs, verified by claude-code-guide agent):**
  - CLAUDE.md auto-load locations: `~/.claude/CLAUDE.md`, project root `./CLAUDE.md` (or `./.claude/CLAUDE.md`), `./CLAUDE.local.md`, and subdirectory `./<dir>/CLAUDE.md` (lazy-loaded when Claude touches files in that dir).
  - **A CLAUDE.md inside `.claude/skills/<name>/` is NEVER auto-loaded.** Skills load via `SKILL.md`, full stop. Any CLAUDE.md inside a skill folder is dead code unless explicitly referenced from SKILL.md.
  - **README.md is never auto-loaded anywhere** by Claude Code. Pure human doc. Belongs at project root by convention; import into CLAUDE.md via `@README.md` if you want it in Claude's context.
  - Sources: docs.anthropic.com / code.claude.com memory + skills pages.
- **Reverses brainstorm §18 + phase-01 deliverables:** the brainstorm explicitly placed CLAUDE.md "inside skill dir (detailed guide/context for the LLM running the skill)" — but that was operationally false. The file never reached the LLM at runtime; the SKILL.md:133 manual ref ("See CLAUDE.md for the deeper LLM operating guide") was the ONLY load path, and even that doesn't auto-inject — Claude has to read it on demand. Dead-code in practice.
- **Classification (per rule §3 Guard User Decisions):** legitimate USER COURSE-CORRECTION grounded in real platform mechanics, not audit drift. Apply.
- **Current state:**
  - `.claude/skills/product-spec/CLAUDE.md` (118 lines) exists but is INERT (dead code per platform behavior).
  - `.claude/skills/product-spec/README.md` (100 lines) exists but is INERT (no auto-load).
  - Repo root has NO `README.md` and NO `CLAUDE.md` (verified: `ls /home/hieubt/Documents/cleanmatic-skills/{README.md,CLAUDE.md}` → not found).
  - Repo `.claude/rules/CLAUDE.md` exists (rules-pack; separate concern — keep).
- **Required action:**
  1. Move skill-folder `CLAUDE.md` → `/CLAUDE.md` (repo root). Re-scope content from "LLM operating guide for THIS SKILL" to project-wide instructions. The skill-specific content (script CLI contract, ID grammar, 5 operating principles) belongs **inlined into SKILL.md or its `references/*`** — not in a separate file the LLM never sees.
  2. Move skill-folder `README.md` → `/README.md` (repo root). Re-scope to project-wide quickstart. If skill quickstart matters, link from root README to the skill's SKILL.md (already discoverable via `/cleanmatic:product-spec`).
  3. **Drop SKILL.md:133** (`"See CLAUDE.md for the deeper LLM operating guide"`) — it pointed to a file that was never auto-loaded. Either delete the reference or replace with `@references/<file>.md` imports if a content gap remains.
  4. Update phase-01 success criteria + brainstorm-decisions §18 with a "[REVERSED 2026-05-28 by user, grounded in Claude Code auto-load mechanics]" annotation.
- **Severity:** CRITICAL (user-directed correction + platform-correctness; current state ships dead files claiming to guide an LLM that never sees them).

### IMP-1 — install.sh does not vendor Mermaid
- **File:** `.claude/skills/install.sh` (50KB, repo-wide CK installer)
- **Plan:** phase-06 step 4 implicitly assumed install.sh would download; impl report admits not wired.
- **Fix:** add a `vendor_mermaid()` step. ~10 lines of curl/wget guarded by hash check.

### IMP-2 — render_html.py `_escape` doesn't cover `"` and `'`
- **File:** `scripts/render_html.py:65-68`
- **Risk:** in current usage `_escape` is applied to `product_name` only at HTML-body context (line 19 of shell). If a future change interpolates `product_name` into an attribute, attacker-controlled PRODUCT.md `name` could inject HTML.
- **Fix:** add `&quot;`, `&#39;` to the escape map; cheap defense.
- **Severity:** IMP (defense-in-depth).

### IMP-3 — Mermaid tree renderer emits duplicate PRODUCT node
- **File:** `scripts/render_mermaid.py:32-33` (adds explicit PRODUCT) + the loop at line 34 also iterates the spec_graph PRODUCT node.
- **Status:** acknowledged in impl-report ("cosmetic; doesn't affect graph semantics").
- **Fix:** add `if n["type"] == "product": continue` inside the node loop.
- **Severity:** IMP (visible cosmetic).

### IMP-4 — `--update` workflow integration test missing
- **File:** `references/workflow-auto-and-update.md` prose-only; no automated test.
- **Status:** acknowledged in impl-report. Eval scenario #3 covers `--update` BUT eval fixtures don't exist (see CRIT-3).
- **Fix:** add `test_update_flow.py` integration covering `downstream()` + change-log append; or fix CRIT-3 to enable eval runs.

### IMP-5 — `generate_templates.py` story `--parent` validation weak
- **File:** `scripts/generate_templates.py:88-90`
- **Bug:** "parent must be an epic ID for type=story" check is `"-E" not in parent`. Accepts `PRD-AUTH-E1-S1` as parent (a story itself). Could allow `PRD-AUTH-E1-S1-S1` IDs.
- **Fix:** check pattern `^PRD-[A-Z0-9-]+-E\d+$` not just substring.

### IMP-6 — Bash hooks block reading `vendor/` despite `.ckignore` exception
- **File:** `.claude/.ckignore` line 21 has `!.claude/skills/product-spec/assets/vendor` exception, but `hooks/scout-block.cjs` still blocks Bash access to `vendor` substring in path.
- **Impact:** during review, could not directly `ls vendor/`. Tooling friction; not a security issue.
- **Fix:** scout-block hook should respect `.ckignore` allow-list more precisely.

### MIN findings (low-impact / observational)

- **MIN-1:** Goal→BRD edge (`spec_graph.py:126`) dangles silently because no BRD node is added (only goals expanded). Used implicitly by tree renderer. Document this in graph JSON schema.
- **MIN-2:** Status `PRODUCT.md` has `approved` but PRODUCT type has no `status` allowed-value spec — implicit acceptance.
- **MIN-3:** Roadmap timeline (render_mermaid) limits to 8 items per section (`render_mermaid.py:88 items[:8]`) — silently truncates. Document.
- **MIN-4:** `frontmatter_parser.py:79` lstrips before regex — silently tolerates leading whitespace; OK but not specified.
- **MIN-5:** Test count claim "31/31" matches reality (verified). Implementation report accurate here.
- **MIN-6:** `examples/README.md` exists but `examples/acme-shop/` lacks its own README — minor doc gap.
- **MIN-7:** `.session.md` schema declares `phase: vision | brd | prd | epic | story | done` but workflow-interview.md treats vision+product as one phase (init). Slight schema/workflow drift.
- **MIN-8:** `render_html.py:88` checks `VENDOR_MERMAID.exists()` again for the footer — the value is computed at module import (constant). If install.sh races with render, the answer is consistent for the call; not a bug, just structurally redundant.

---

## Wave 4 — Cross-validate (brainstorm → plan → impl-report → code)

| Decision (brainstorm) | Plan reflects | Impl-report claims | Code reality |
|---|---|---|---|
| §1 `cleanmatic:` namespace | plan §M1 spike | report: "M1 gate passed" | SKILL.md `name: cleanmatic:product-spec` ✓ |
| §2 hierarchy Vision/PRODUCT.md/BRD/PRD/Epic/Story | plan §"Key Decisions" | report: ✓ | document-model-and-hierarchy.md ✓ |
| §3 thin PRODUCT.md (labels) | yes | yes | PRODUCT.md template ✓ |
| §4 scripts-structural / LLM-judgment | yes | yes | validation-rules-spec.md + scripts ✓ verified |
| §5 stdlib + pyyaml, no jinja2 | yes | yes | requirements.txt: pyyaml, pytest, pytest-cov ✓ |
| §6 phased interview, .session.md committed | yes | partial | references describe it; not yet end-to-end-tested |
| §8 viz **inline-vendored HTML** | plan §"Global Constraints" | report: "vendored + CDN fallback + warning" | **vendor empty (CRIT-2)** |
| §8 viz formats = ASCII+Mermaid+HTML; **SVG/PNG dropped** | yes | yes | render_svg.py absent ✓; 3 renderers present ✓ |
| §11 parent-scoped IDs | plan §C2 | yes | check_consistency.py:33-38 + tests ✓ verified |
| §12 evals (4 scenarios) + script unit tests | plan P8 | "scaffolded; not executed" | **fixtures absent (CRIT-3)** |
| §16 `--approve` warns-not-blocks | yes | yes | workflow-validate.md ✓ |
| §17 contradiction never auto-flip | yes | yes | CLAUDE.md §4 + validation-rules-spec.md §Contradiction Protocol ✓ |
| §18 in-skill CLAUDE.md | yes | yes | **REVERSED by USER (CRIT-5)** |
| Global C1 repo venv | yes | not addressed | **venv absent (CRIT-1)** |
| Global C2 parent-scoped IDs | yes | yes | verified |
| Global M5 `--root` flag | yes | yes | verified all scripts |
| Global H1 gap-analysis structural-only | yes | yes | check_traceability.py:64-70 ✓ |
| Global H4 snapshots JSON for delta | yes | yes | spec_graph.write_snapshot ✓ |

**Drift summary:** 3 broken constraints (C1, validate-gate vendor, P8 fixtures) + 1 user-reversal not yet applied.

---

## Plan B — Remediation Path (Recommended order)

**Block 1 — must-do before any v1 release:**
1. **CRIT-1** (5 min) — run `bash .claude/skills/install.sh` (creates `.venv` per its existing logic). Re-verify all 11 scripts run via the new venv. Update `.gitignore` if needed.
2. **CRIT-5** (~30 min) — move skill `CLAUDE.md`/`README.md` to repo root; revise content to project-wide framing. Update SKILL.md:133 reference. Annotate plan §18 reversal in plan.md.
3. **CRIT-2** (~45 min) — choose: (a) commit vendored `mermaid.min.js` (largest fix; ~1MB) OR (b) extend install.sh with curl-download + sha256 verify. Validate `examples/.../visuals/*.html` opens in airplane-mode browser.
4. **CRIT-3** (~1 hr) — author the 6 missing fixtures under `eval/fixtures/`. Symlink (or copy) `scripts/tests/fixtures/{valid-spec,broken-spec}` and write the 4 JSON/TXT files per evals.json expectations.
5. **CRIT-4** (~20 min) — fix `visualize.py:91` to pass `view_format="pre"` when mermaid renderer returned a `<pre>` fallback. Add a test asserting heatmap HTML output is a valid `<pre>` not a broken `<div class="mermaid">`.

**Block 2 — strongly recommended before v1:**
6. IMP-2 escape function widen (5 min).
7. IMP-3 dedup PRODUCT node in mermaid tree (5 min).
8. IMP-5 stricter `--parent` check in generate_templates (5 min).
9. IMP-1 wire install.sh vendor-fetch (folds into CRIT-2.b).

**Block 3 — post-v1:**
10. IMP-4 add `--update` integration test (folds into CRIT-3 fixture work).
11. IMP-6 scout-block hook refinement (out of skill scope; tooling issue).
12. MIN-1 through MIN-8 — document or defer.

---

## What Worked

- Script-vs-LLM split honored cleanly. No judgment leaked into scripts (verified by reading all 4 checkers + generator).
- Parent-scoped ID grammar implemented + tested + matches spec exactly.
- Snapshot/delta architecture (no `git show` archaeology) implemented as specified.
- Contradiction protocol surfaced in CLAUDE.md + validation-rules-spec.md verbatim; no auto-flip code.
- pytest 31/31 — real coverage of structural correctness, not vanity tests.
- Worked example validates clean — end-to-end sanity gate works.
- YAGNI/KISS — no jinja2, no unnecessary deps, simple `{{token}}` substitution, stdlib templating.
- DRY — frontmatter as source of truth; sections cross-referenced not duplicated.
- Bilingual EN+VI present (with appropriate "pending review" note).

## What's Broken (re-summary)

1. Repo venv missing — first PO command fails.
2. Vendored Mermaid empty — offline promise broken; CDN dependency silently introduced.
3. Eval fixtures absent — evals unrunnable.
4. HTML renders broken for 3 of 9 views (heatmap/persona/risk).
5. CLAUDE.md + README.md still in skill folder (user reversed §18).

## Verification Commands (re-run after fixes)

```bash
# 1. venv ready
./.claude/skills/.venv/bin/python3 --version

# 2. tests pass
./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec/scripts/tests/ -v

# 3. worked example clean
./.claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/check_traceability.py --root .claude/skills/product-spec/examples/acme-shop

# 4. HTML self-contained (no network)
ls -la .claude/skills/product-spec/assets/vendor/mermaid.min.js
# expect: ≥800KB

# 5. eval fixtures present
ls .claude/skills/product-spec/eval/fixtures/

# 6. project root has CLAUDE.md + README.md
ls /home/hieubt/Documents/cleanmatic-skills/{CLAUDE.md,README.md}
```

---

## Unresolved Questions

1. **CRIT-2 fix choice** — vendor mermaid.min.js directly in git (adds ~1MB blob) vs. install.sh fetch (introduces install-time network dep). Which does the user prefer?
2. **CRIT-5 content scope** — when moving CLAUDE.md/README.md to root, should content be (a) verbatim from skill files, (b) re-scoped to project (which currently has only `.claude/rules/CLAUDE.md` and no top-level README), or (c) both — root CLAUDE.md as project-wide + skill keeps a lighter LLM hint file?
3. **VI question banks** — who reviews? (Known open item from brainstorm §18; not blocking.)
4. **Eval grader infrastructure** — runtime for `evals.json` scenarios not specified (LLM-as-judge? assertion harness?). Out of skill scope but unblocks Phase 8 verification.
5. **Skill discovery spike** — impl-report says "M1 spike gate passed" but I did not independently reload Claude Code to verify `/cleanmatic:product-spec` invocable. Recommend user re-confirm.

---

**Status:** DONE_WITH_CONCERNS
**Summary:** 4-wave hardcore review complete. Implementation has high engineering quality but ships with 5 critical drifts from plan + brainstorm + user corrections. Pytest passes, worked example validates, but the "offline" promise and eval scaffold are not delivered, repo venv missing, HTML broken in 3 views, and CLAUDE/README placement reversed by user.
**Concerns:** ship-blocked until Block-1 remediation (CRIT-1..5) applied + verified.
