# Wave 4 — Cross-Validation, Plan B, Report

**Skill:** `cleanmatic:product-spec` (`.claude/skills/product-spec/`)
**Plan:** `plans/260528-0912-cleanmatic-product-spec-skill/`
**Built by:** Codex + Gemini, through 3 prior code-review + remediation rounds
**This review:** 4-wave hardcore re-audit, parallel-agent driven, ultrathink synthesis.

---

## 0. Executive

- **Pytest:** 76/76 pass (run by Wave-3a agent at 03:08).
- **Prior rounds verified:** 25+ sticky brainstorm decisions, 30+ findings closed across R1/R2/R3, pytest grew 18 → 31 → 32 → 41 → 45 → 57 → 76.
- **NEW findings this wave:** 2 CRIT + 3 HIGH bugs in scripts (Wave-3a), 4 CRIT + 4 HIGH DRY contradictions in spec↔code↔templates (Wave-3b), 1 missing artifact (Wave-1+2).
- **Verdict:** Skill is **NOT** "ship-ready v1" as currently committed. C-1 (XSS) and C-2 (YAML injection) are ship-blockers. DRY drift in 4 places will silently mislead any future re-implementer.
- **No sticky brainstorm decision violated.** All NEW findings are bugs/drift, not policy reversals — safe to fix without user re-confirmation, except 5 items flagged for **PO judgment** below.

---

## 1. Wave roll-up

| Wave | Agent | Report | Result |
|------|-------|--------|--------|
| 1+2 — phase plan vs implementation | general-purpose | `from-ck-code-review-to-reviewer-260529-0303-product-spec-wave12-phase-verification-report.md` | mostly clean; 1 missing README, 1 schema-boundary drift, 2 defensible extras |
| 3a — scripts bug-hunt + pytest | code-reviewer | `from-ck-code-review-to-reviewer-260529-0303-product-spec-wave3-scripts-bughunt-report.md` | 2 CRIT, 3 HIGH, 6 MED, 6 LOW NEW issues; tests green |
| 3b — DRY consistency | code-reviewer | `from-ck-code-review-to-reviewer-260529-0303-product-spec-wave3-dry-consistency-report.md` | 4 CRIT, 4 HIGH, 4 MED NEW contradictions |
| 3c — prior decisions baseline | general-purpose | `from-ck-code-review-to-reviewer-260529-0303-product-spec-prior-decisions-baseline-report.md` | sticky-decision register + 8 truly-outstanding items |

---

## 2. Sticky decisions register (NEVER auto-reverse)

Cataloged in detail in the Wave-3c baseline report. Top traps:

1. **3 viz formats, NOT 4** — ASCII + Mermaid-in-md + inline-vendored Mermaid HTML. SVG/PNG dropped (avoids Mermaid-CLI binary).
2. **Parent-scoped IDs** — `BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1`, `PRD-AUTH-E1-S1`. No central counter.
3. **No jinja2** — stdlib templating only (`generate_templates.py` regex).
4. **VI ships best-effort** + pending-native-review note.
5. **In-skill `CLAUDE.md` REVERSED** — only the repo-root CLAUDE.md is auto-loaded; the skill keeps SKILL.md + references.
6. **Scripts emit JSON, exit 0** — `--strict` gating belongs to LLM layer. `strict_gate.py` added in R3 is the **only** sanctioned exception (CI escape hatch).
7. **VI banks frontmatter keys stay ENGLISH**; only prose localizes.

Any "fix" that touches these must be surfaced to the user (per repo rule `review-audit-self-decision.md` §3). None of the NEW findings below do so.

---

## 3. NEW findings — cross-validated

### CRITICAL — ship-blocker

| # | Origin | Where | Issue | Verified | Fix size |
|---|--------|-------|-------|----------|---------|
| **C-1** | 3a | `scripts/render_mermaid.py:34-37` | `_safe_label` does NOT escape `<` / `>`. Raw `<script>alert(1)</script>` in `product.name` injects a live `<script>` tag into HTML output. Mermaid's `securityLevel: "strict"` runs AFTER browser tokenization → bypassed. | empirical (HTMLParser found 3 `<script>` tags where 2 expected) | 2 lines |
| **C-2** | 3a | `scripts/generate_templates.py:149-156` | Token substitution returns `str(v)` directly. `--values '{"id":"foo\nstatus: approved"}'` injects a duplicate `status:` key. YAML duplicate-key resolution lets it slip past the wave-2 `status == "approved"` guard at line 216-221. | empirical | ~5 lines |
| **DRY-C1** | 3b | `references/frontmatter-and-id-spec.md:25` vs `assets/templates/exec-summary.md:7` | `type` enum lacks `exec_summary` but exec-summary template emits it. `check_consistency.py` doesn't validate `type` today — so tightening the validator breaks the generator. | grep | spec line + template line, **PO decision** |
| **DRY-C2** | 3b | `references/frontmatter-and-id-spec.md:88` says BRD goal `owner` REQUIRED, but `examples/acme-shop/.../brd.md:11-18`, `scripts/tests/fixtures/valid-spec/.../brd.md`, AND `broken-spec` fixture all omit it | Spec/fixture/example disagree. `check_consistency.py` doesn't enforce → silent. | grep | **PO decision** |
| **DRY-C3** | 3b | `scripts/visualize.py:101` exposes `--diff <path>` while `references/visualization-spec.md:25,104` documents `--viz delta --snapshot <name>` | LLM reading the spec to run delta hits argparse error. | grep | rename flag or update spec |
| **DRY-C4** | 3b | `CLAUDE.md:65` lists `parent` as a frontmatter key | No artifact writes `parent`. `spec_graph.py:115` synthesizes it in-memory only. Dead doc reference. | grep | 1-line edit |

### HIGH

| # | Origin | Where | Issue | Verified | Fix size |
|---|--------|-------|-------|----------|---------|
| **H-1** | 3a | `spec_graph.py:248`, `check_traceability.py:116`, `check_consistency.py:270`, `build_traceability_matrix.py:96` | Bare `json.dumps()` without `default=str`. PyYAML auto-parses `status: 2026-05-29` as `datetime.date`. 4 of 6 JSON-emitting scripts crash → violates "always exit 0, emit JSON" contract. | empirical | 4 × 1-line |
| **H-2** | 3a | `generate_templates.py:90-92` | PRD `--slug` validation missing. Wave-2 NEW-4 fixed epic/story parent validation, missed PRD's own slug. Accepts oversized, lowercase, spaces, special chars, leading digits — directly contradicts `frontmatter-and-id-spec.md` "uppercase ASCII letters/digits, ≤16 chars". | empirical | ~8 lines |
| **H-3** | 3a | `generate_templates.py:255-266` | `--write` silently overwrites existing files. Re-running `--type prd --slug AUTH --write` destroys PO's hand edits. | empirical | ~3 lines (existence check + error) |
| **DRY-H5** | 3b | `references/validation-rules-spec.md:50` + `CLAUDE.md:96` declare "Scripts ALWAYS exit 0"; `strict_gate.py:73` exits 2 by design (sanctioned R3 escape hatch). | Spec text never updated. | grep | 1-line spec edit |
| **DRY-H6** | 3b | `check_consistency.py` emits `invalid_type`, `persona_cap_exceeded`, `session_md_gitignored` — none of these are in the spec's check catalog at `validation-rules-spec.md`. | grep | 3 catalog rows |
| **DRY-H7** | 3b | `validation-rules-spec.md:31` advertises `version_inconsistency`; no implementation anywhere. | grep | drop spec row OR implement |
| **DRY-H8** | 3b | `SKILL.md:68` + `CLAUDE.md:172` say vision.md carries `horizon`; the vision template explicitly forbids it; `examples/acme-shop/docs/product/vision.md:10` ships `horizon: now`. | grep | example fix + 1 doc line |

### MEDIUM (deferable, but log)

3a-Wave: M-1 missing `JSONDecodeError` trap in `_load_baseline`; M-2 symlinked stories crash `build_nodes`; M-3 `strict_gate` exits 0 when `docs/product/` missing (silent CI green); M-4 markdown-pipe-injection in matrix; M-5 ASCII heatmap/scope/persona crashes on non-hashable enum lists; M-6 `--id` override bypasses ID validation.

3b-Wave: sign-off body tokens unspecified; `interview-brd.md` frontmatter idiom drift; BRD `personas` opt-out undocumented; tree.md title-inheritance subtle.

### LOW (won't-fix candidates, log only)

3a: L-1 UTF-8 BOM rejected · L-2 `!.session.md` negation false positive · L-3 list-status crashes `_status_inconsistency` · L-4 `_safe_id` collision `-`/`:` · L-5 self-ref `epic: <own-id>` undetected · L-6 sub-second filename collisions in HTML/snapshot writes.

---

## 4. Wave-1+2 phase-vs-implementation residuals

- **Missing skill-local README.md.** `phase-01-scaffold-skeleton.md` + `phase-08-eval-tests-packaging.md` both list it. Brainstorm §18 amendment absorbed in-skill `CLAUDE.md` into SKILL.md+references but did NOT cover README. Either add a 30-line `.claude/skills/product-spec/README.md` (install + quickstart) OR document the deliberate drop in plan-amendment §19.
- **.session.md schema-boundary drift.** Phase-2 should have specified it (per H3 boundary rule); actual definition lives in `references/workflow-interview.md` (phase-7). Cosmetic — text is correct; just lives in the wrong reference.
- **Phase frontmatter cosmetic.** All 8 phase files still `status: pending` despite `plan.md` marking all "Completed". One bulk-edit closes it.
- **`strict_gate.py` + `i18n_labels.py` extras.** Both defensible (R3 sanctioned + viz dependency). No action needed but call out in plan-amendment.

---

## 5. Plan B — alternatives for each NEW finding

For every NEW finding, both a forward fix and a fallback ("plan B"):

### Script bugs (3a)

| # | Plan A (recommended) | Plan B |
|---|----------------------|--------|
| C-1 XSS | escape `<` → `‹` and `>` → `›` (or `&lt;` if not inside Mermaid label) in `_safe_label`. 2-line patch. | reject any node label containing `<` / `>` at script level → empirical exit-0 + finding in JSON. Heavier UX cost. |
| C-2 YAML inject | in `tok()`, scan `str(v)` for `\n` → raise `ValueError`. Also: switch to `yaml.safe_dump(v)` for scalar values to escape special chars. | restrict `--values` JSON values to single-line strings via regex in `load_values`. Earlier failure, less granular. |
| H-1 date JSON | add `default=str` to all 4 `json.dumps` calls. 4-char fix. | coerce date-typed YAML keys to ISO strings in `frontmatter_parser._parse` before they ever land in graph. Broader fix, more side-effects to test. |
| H-2 PRD slug | reuse `_validate_slug` helper, call it for `--type prd` before `allocate_id`. 8 lines. | leave validation to LLM layer (per skill/LLM split) — but that means CLI direct calls bypass it. Weaker. |
| H-3 silent overwrite | refuse `--write` if path exists; require `--force` to overwrite. 3 lines. | back up overwritten file to `.bak` before write. Bigger surface, less safe. |

### DRY contradictions (3b)

| # | Plan A (recommended) | Plan B |
|---|----------------------|--------|
| DRY-C1 `exec_summary` type | **PO decides**: extend enum to include `exec_summary` (treat as generated artifact). Update spec, validator next. | drop `type:` from `exec-summary.md` template — exec-summary becomes typeless. Spec stays clean. |
| DRY-C2 BRD owner | **PO decides**: relax spec to `owner` optional (matches fixtures + examples). Update spec line 88. | tighten fixtures + examples to include `owner: TBD`. Spec stays strict. |
| DRY-C3 `--diff` vs `--snapshot` | rename code arg from `--diff` to `--snapshot` (matches spec). 3 line change in visualize.py + README mention. | update `visualization-spec.md` line 25,104 to say `--diff <path>`. Spec follows code. |
| DRY-C4 dead `parent` key | drop `parent` from CLAUDE.md:65 bilingual key list. 1 word delete. | add `parent` as optional override field across all artifact types. Heavy + redundant with existing `epic`/`prd`/`brd_goals`. Reject. |
| DRY-H5 exit-0 wording | spec: add carve-out "except `strict_gate.py` which exits 2 by design". 1 line. | move `strict_gate` out of `scripts/` (e.g., `tools/`) so the "scripts always exit 0" rule stays literal. More refactor. |
| DRY-H6 missing catalog rows | add 3 rows to `validation-rules-spec.md` check catalog. ~10 lines. | drop the 3 checks from `check_consistency.py`. Reduces guarantee. |
| DRY-H7 `version_inconsistency` | drop spec row (YAGNI). 1 line. | implement the check (5–10 lines). Only if PO wants version tracking enforced. |
| DRY-H8 `horizon` on vision.md | move `horizon` out of vision.md template wording; update SKILL.md + CLAUDE.md to say `horizon` lives in PRODUCT.md only; remove `horizon: now` from acme-shop example. | leave horizon dual-homed (vision + PRODUCT), update template comment to allow it. Violates DRY. |

### Wave-1+2 residuals

| Item | Plan A | Plan B |
|------|--------|--------|
| Missing skill README.md | add 30-line README (install + quickstart + link to SKILL.md). | add a §19 plan amendment documenting the drop. SKILL.md already covers most of it. |
| .session.md schema drift | move the schema section from `workflow-interview.md` to a new `references/session-schema.md` (or to `frontmatter-and-id-spec.md`). | leave as-is, add a forward pointer in phase-2 spec. Cheapest. |
| Phase frontmatter status | bulk-flip all 8 phase frontmatter `status: pending → completed`. | leave (just cosmetic). |

---

## 6. Recommended implementation order

If user authorizes implementation, follow this order (each step keeps `pytest -q` green; commit per group):

1. **Group A — ship-blockers (no PO judgment needed):** C-1, C-2, H-1, H-2, H-3, DRY-C4, DRY-H5, M-1 (`_load_baseline` JSONDecodeError trap).
2. **Group B — PO-judgment items (gate behind `AskUserQuestion`):** DRY-C1, DRY-C2, DRY-C3, DRY-H8.
3. **Group C — spec-only catch-up:** DRY-H6, DRY-H7, .session.md schema move, phase frontmatter status flip.
4. **Group D — docs:** skill README.md (PO confirms wanted).

After each group: run `./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec/scripts/tests/ -q`. If green, commit with conventional message (no AI references, no phase numbers per `review-audit-self-decision` §5).

Estimated effort: Group A ≈ 30 min; B ≈ 20 min (after PO confirms); C ≈ 15 min; D ≈ 15 min.

---

## 7. What was NOT re-flagged (verified-decisions sticky)

Per `review-audit-self-decision` §1, the following prior-verified items are deliberately left alone:

- Inline-vendored Mermaid blob (R1 fix) — verified safe.
- 3-format viz (R1 confirmed) — `tree.md` example matches.
- `personas: TBD` typing fix (C-1 R3).
- Install.sh exit-code propagation (H-2 R3) — current install.sh lines 51-69 confirm.
- Slug validation for epic/story parents (NEW-4 wave-2).
- VI best-effort with pending-native-review note.
- Examples HTML accumulation: `.gitignore` at examples/.gitignore committed `f7b4893`.

If any Plan-B option above re-opens a sticky decision, the user must be asked explicitly.

---

## 8. Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| C-1 XSS exploited in PO HTML output | LOW (the PO is the writer) but POSSIBLE in shared HTML | HIGH (script execution) | escape `<>` in `_safe_label` |
| C-2 silent self-approval via `--auto` braindump | MEDIUM (LLM-generated `--values` could contain `\n`) | HIGH (bypasses approval gate) | newline reject in `tok` |
| H-1 datetime crash | LOW (only on date-typed status field) | MED (script crash) | `default=str` |
| H-3 overwrite hand-edits | MEDIUM (PO iterates) | HIGH (lost work) | `--force` gate |
| DRY drift compounds | HIGH (next re-implementer will be misled) | MED | apply Plan A across the board |

---

## 9. Unresolved questions for the PO

These are the items the audit CANNOT decide unilaterally without re-opening user decisions:

1. **DRY-C1 `exec_summary` type:** add to the canonical enum or drop from the template?
2. **DRY-C2 BRD goal `owner`:** required (tighten fixtures) or optional (relax spec)?
3. **DRY-C3 `--diff` vs `--snapshot`:** rename the code arg or update the spec?
4. **DRY-H8 `horizon` placement:** vision.md (where SKILL.md says) or PRODUCT.md (where template says)?
5. **Skill README.md:** add it or codify the absorption in a §19 plan-amendment?

If user grants blanket "fix everything per Plan A", treat 1=enum-add, 2=optional, 3=rename, 4=PRODUCT-only, 5=add-README.

---

## 10. Bottom line

- **No silent reversals.** Every NEW finding traces to a real bug, drift, or DRY contradiction. No sticky brainstorm decision is challenged.
- **Implementation gated on user choice for 5 items.** Everything else is mechanical patching.
- **Pytest stays green** after each fix group; Wave-3a verified 76/76 baseline.
- **Code-style rule observed:** all fix sketches above describe the *invariant*, not the audit-tag — per `review-audit-self-decision` §5, code comments must NOT reference plan/finding codes (no "fix per DRY-C2"). The catalog in this report is for the PO, not for codebase comments.

Next action: PO answers question 1–5; controller implements Group A → B → C → D; final `pytest -q` + commit.
