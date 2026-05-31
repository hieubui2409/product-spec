---
type: hardcore-code-review
date: 2026-05-28
reviewer: ck-code-review (4-wave protocol)
review-target: cleanmatic:product-spec skill
plan: plans/260528-0912-cleanmatic-product-spec-skill/
decisions: plans/reports/brainstorm-decisions-260528-0818-cleanmatic-product-spec-skill-report.md
implementer: Codex + Gemini
status: complete
---

# Hardcore Review — cleanmatic:product-spec

4-wave audit (scan → deep-dive → hardcore → cross-validate) over plan, brainstorm-decisions (18 rounds, sticky), and implementation. Test suite: 57/57 green at HEAD. Findings below are NEW issues not caught by existing tests, plus decision-drift the implementer never surfaced.

## TL;DR

- Tests pass; mechanical correctness on happy paths is solid; the SKILL.md / references/ / scripts split honors the brainstorm contract.
- **Three CRITICAL bugs** (data-quality, not crashes): defaulted list-fields leak `"TBD"` string into YAML, then iterate per-character downstream → garbage in viz / phantom dangling_link errors / silent corruption that `check_consistency` cannot detect.
- **One HIGH visual regression**: Mermaid tree renders inverted (PRODUCT at bottom) vs ASCII tree (PRODUCT at top). No test guards orientation.
- **Multiple MEDIUM decision-drift items** silently reversed without PO confirmation — most notable: in-skill `CLAUDE.md` moved to repo-root (brainstorm §18 said inside skill dir); viz scope/moscow-filter rule (§15) never implemented.
- **install.sh** silently swallows pytest exit code via `| tail -3` → user gets "Install complete" even when tests fail.
- Plan + reference docs drifted from decisions in two places (Phase 2 SC4 "4 formats", Phase 1 in-skill CLAUDE.md) but never updated.

## Wave 1 — Scan

Inventory (artifacts present):
- Plan: `plan.md` + 8 phase files (P1-scaffold → P8-eval), all marked `Completed`.
- Decisions: `brainstorm-decisions-260528-0818-*.md` (18 rounds, 100Q, sticky).
- Skill tree: `SKILL.md` · `install.sh` · 11 references · 11 scripts (incl. tests) · 9 templates · 1 vendored asset · 4 eval fixtures · 1 worked example (acme-shop, 5 artifacts + 17 visual renders).
- Tests: 57 unit/integration tests; PASS.

No missing required artifacts vs the plan's `Related Code Files` lists.

## Wave 2 — Deep dive

Read every script, template, reference, fixture. Notable structural choices verified:
- Scripts emit JSON, exit 0 always (per validation-rules-spec).
- `spec_graph.py` builds `story→epic→prd→brd_goal` graph from explicit frontmatter; `downstream()` reachability exposed.
- `check_consistency` enforces parent-scoped ID regex + closed-enum (`status`, `scope`, `moscow`, `horizon`, `size`, `lang`).
- `generate_templates.py` has defense-in-depth refusing `status: approved` at script layer (NEW-12 in tests).
- `render_html.py` falls back to CDN with visible warning when vendored Mermaid is missing; ASCII-fallback views skip the 2.5MB JS payload (NEW-7).
- Encoding helper for Windows is wired correctly.

Strengths: each script <200 LoC, single responsibility, no hidden judgment, deterministic output.

## Wave 3 — Hardcore review (NEW findings)

### W3-CRIT-1 — `personas: TBD` (and any list field) silently corrupts viz

**File:** `scripts/generate_templates.py:182-206` (`fill_defaults`)
**Severity:** CRITICAL (data quality)

`fill_defaults` defaults `id/status/lang/owner/version/created/updated`, but NOT list-typed frontmatter (`personas`, `metrics`, `brd_goals`, `risks`, `acceptance_criteria`). When the PO skips them, `TOKEN_RE` substitutes `{{personas}} → "TBD"` (a string). Reproduced live:

```yaml
# fresh PRODUCT.md after generate w/ only name+core_value:
personas: TBD              # ← string, not list
```

Downstream consumers iterate `for p in n["personas"] or []:` → "TBD" is truthy → iterates chars `T`,`B`,`D`. Confirmed:

- `render_ascii.persona()` → matrix with rows `T`, `B`, `D` as personas.
- `check_traceability` with `brd_goals: TBD` on a PRD → **3 phantom dangling_link errors** (`"PRD references unknown BRD goal T"` / `B` / `D`). Surfaced via direct probe.
- `check_consistency` does NOT catch this — `personas`/`brd_goals` not in `ENUMS`, no type-validation gate.

**Fix:** list-typed defaults to `[]` in `fill_defaults`, OR `TOKEN_RE.sub` special-cases missing tokens for known list keys to emit `[]`, OR (best) add a `check_consistency.shape_check` that validates each list-typed frontmatter field is actually a YAML list/null — emit `invalid_type` finding. Tests exist for `vision.md` consistency but probe was empty-vision; they pass only because vision template has no `personas: {{personas}}` token.

### W3-HIGH-1 — Mermaid tree renders inverted vs ASCII tree

**File:** `scripts/render_mermaid.py:39-59` (`tree`)
**Severity:** HIGH (UX/visual contract)

Edges in graph JSON are `child → parent`. `render_ascii.tree` walks recursively from root, so PRODUCT appears at top. `render_mermaid.tree` emits `flowchart TB` with the same edge direction → Mermaid layout engine places sources (stories) at top, targets (PRODUCT) at bottom. **Same logical data, opposite visual orientation between the two formats.** Confirmed visually via probe.

No test catches it (`test_mermaid_tree_emits_flowchart_block` only checks startswith ` ```mermaid `).

**Fix:** either (a) emit `flowchart BT` so visual matches ASCII while keeping edge semantics, or (b) reverse edges (parent → child) in the mermaid emitter only. Option (a) is one-character.

### W3-HIGH-2 — `install.sh` silently swallows test failures

**File:** `install.sh:67`
**Severity:** HIGH (false-success)

```bash
"$VENV_DIR/bin/python3" -m pytest "$SCRIPT_DIR/scripts/tests/" -q --no-header 2>&1 | tail -3
```

Under `set -euo pipefail`, the pipeline's exit code = last command's = `tail` = 0, regardless of pytest. User sees "Install complete" even with red tests. Brainstorm §13 = "v1 = everything"; install is a user-facing surface that must not lie.

**Fix:** capture exit before piping — `if ! "$VENV_DIR/bin/python3" -m pytest …; then fail "tests failed"; fi`, or `set -o pipefail` + reverse pipe order with `tee /tmp/pytest.log` and check `${PIPESTATUS[0]}`.

### W3-MED-1 — `status_inconsistency` skips PRD ↔ BRD-goal relationship

**File:** `scripts/check_consistency.py:105-125` (`_status_inconsistency`)
**Severity:** MED

Walks parent via `n.get("epic") or n.get("prd")`. PRD has neither — its parents are in `brd_goals[]`. So a PRD `approved` whose BRD-goal targets are still `draft` is never flagged. Validation-rules-spec lists `status_inconsistency` generically; implementation is partial.

**Fix:** when `n["type"] == "prd"`, iterate `n["brd_goals"]` against `nodes_by_id` and compare statuses.

### W3-MED-2 — `--viz delta` requires 2 snapshots; ignores live graph

**File:** `scripts/visualize.py:59-71` (`_load_baseline`)
**Severity:** MED (UX)

Returns `None` when fewer than 2 snapshots exist, even though `current = build_graph(root)` (live) is always available. UX expectation: 1 snapshot + current live = a diff. Currently requires 2 historical snapshots; user must run `--validate` twice with a change in between before delta works.

**Fix:** when `len(snaps) < 2 and len(snaps) == 1`, return `snaps[-1]` as baseline; only `0` snapshots means "no baseline".

### W3-MED-3 — `--diff <bad-name>` silently degrades

**File:** `scripts/visualize.py:62-66`
**Severity:** MED (UX)

User typos a snapshot filename → `if p.exists(): … else: return None` → dispatcher renders "(no baseline yet — run --validate to create one)". Should error with the resolved path and a list of available snapshots.

**Fix:** raise / log when explicit `--diff` arg cannot be resolved.

### W3-MED-4 — `--strict` enforcement only at LLM layer

**File:** `references/validation-rules-spec.md:43-50` + `scripts/*`
**Severity:** MED (CI usability)

By design, scripts exit 0 always. `--strict` gating happens "in the orchestration layer." Consequence: a CI hook can't `--validate --strict` and rely on exit code; needs the LLM in the loop. Brainstorm §4 = "configurable, default warn; --strict blocks on hard errors" — silent on enforcement layer.

**Recommendation:** add a thin shell-runnable `python3 scripts/strict_gate.py --root .` that consumes `check_traceability` + `check_consistency` JSON and exits non-zero if any `severity:error` exists. Lets CI use the skill without an LLM. Defer if not in v1 scope, but flag.

### W3-LOW-1 — render_mermaid + render_ascii gap-view inconsistency

**File:** `scripts/render_ascii.py:140-151` vs `scripts/check_traceability.py:64-71`
**Severity:** LOW

`render_ascii.gap` counts ALL inbound edges; `check_traceability.unaddressed_parent` counts only matching-child-type edges. Practically equivalent on valid graphs but diverges on malformed data. Single source of truth would be reuse the check function.

### W3-LOW-2 — `_now()` vs snapshot filename clock skew

**File:** `scripts/spec_graph.py:200-207`
**Severity:** LOW (cosmetic)

`generated_at` and snapshot filename use two separate `datetime.now()` calls → can differ by ms. Internal-only; harmless.

### W3-LOW-3 — examples bloat

39 files under `examples/acme-shop/docs/product/visuals/` including 6 heatmap renders within minutes. Bloats clone; consider `visuals/*.html` in `.gitignore` keeping only one canonical sample.

## Wave 4 — Cross-validation (plan ↔ decisions ↔ code)

### W4-MED-1 — Decision §18 silently reversed: CLAUDE.md location

Brainstorm decision (sticky):
> Skill docs: README + examples/ + walkthrough + **CLAUDE.md inside skill dir** (detailed guide/context for the LLM running the skill). SKILL.md stays lean.

Git status shows: `RM .claude/skills/product-spec/CLAUDE.md -> CLAUDE.md` (moved to repo root). Repo-root CLAUDE.md is dev-only (auto-loaded by Claude Code in THIS repo); it does NOT ship inside the skill ZIP. Users who install the skill get only `SKILL.md` + `references/`.

Per `review-audit-self-decision.md` rule #3 (Guard User Decisions Against Audit/YAGNI Drift), this should have been surfaced to the PO with keep/change/hybrid options. It wasn't. Functionally the SKILL.md + references/ surface absorbs most of what an in-skill CLAUDE.md would have carried, but the decision drift is real and unrecorded.

**Action:** surface to PO. Options: (a) restore `.claude/skills/product-spec/CLAUDE.md` honoring decision §18; (b) keep current (root-only) and explicitly amend §18 with rationale ("SKILL.md + references/ carries it; root CLAUDE.md is dev-only").

### W4-MED-2 — Decision §15 partially implemented: "viz filters scope:out / moscow:wont"

Brainstorm §15 (last bullet, deferred/won't-have):
> item STAYS IN PLACE (single home, full history); **viz filters them out**.

Implementation: `render_ascii.scope` / `render_ascii.moscow` / `render_mermaid.scope` / `render_mermaid.moscow` show counts for `wont` / `out` artifacts; no filter. Roadmap viz doesn't suppress them either. **Drift from decision §15.**

**Action:** add a `--include-wont` opt-in flag (default false) that filters `moscow == "wont"` and `scope == "out"` from `roadmap`, `tree`, `persona`. Or amend §15 to drop the filtering rule (with PO confirmation).

### W4-MED-3 — Phase 3 V6 vision-horizon question vs Phase 4 vision template

`references/interview-vision.md:V6` asks "Is this current vision the 'now' priority, 'next' chapter, or 'later' aspiration?" → tags `vision frontmatter horizon`.
`assets/templates/vision.md` intentionally drops `horizon` (comment: "vision is timeless strategy"; commit SA-1A made it pass enum check).

V6 answer goes nowhere — orphan question. Bank wasn't updated when the template was fixed.

**Fix:** delete V6 OR repurpose to set the PRDs' default horizon. Trivial.

### W4-MED-4 — Phase 2 SC4 says "9 views × 4 formats"; implementation is 3

Phase 2 success criterion #4: "Viz spec defines all 9 views × **4 formats** + graph-JSON shape reused by P5/P6". Validate-gate later dropped SVG/PNG → 3 formats. Phase 2 doc never updated. Phase 6 doc IS updated to 3 formats.

**Fix:** correct Phase 2 SC4 text to "3 formats" so the plan reflects shipped reality.

### W4-MED-5 — Phase 1 expected in-skill CLAUDE.md

Phase 1 `Related Code Files`: `Create: .claude/skills/product-spec/CLAUDE.md (LLM operating guide)`. Reality: removed. Same root cause as W4-MED-1.

### W4-LOW-1 — workflow-validate.md uses plain `python3`, not repo venv

```bash
python3 scripts/spec_graph.py --root <root> --snapshot
```

Plan constraint C1 mandates `./.claude/skills/.venv/bin/python3`. SKILL.md Resources section is correct; workflow-validate is the only place it slipped. Minor copy-paste consistency.

### W4-LOW-2 — examples/acme-shop/PRODUCT.md violates SA-11A fix

Test `test_product_template_core_value_body_is_stub_not_duplicate` enforces template body must NOT duplicate `core_value`. The example file has:

```
## Core Value

Help boutique brands sell directly to fans without middlemen.
```

`core_value` duplicated in body — same anti-pattern the template fix removed. Example was hand-edited before the template fix and never refreshed. Misleading reference for PO.

**Fix:** regenerate example PRODUCT.md OR edit body to the stub `_(authoritative value lives in frontmatter ...)`.

## Plan + Decisions vs Implementation: Compliance Matrix

| Decision § | Spec | Implementation | Status |
|------------|------|----------------|--------|
| §2 Document model (Vision→1BRD→nPRD→Epic→Story) | references + scripts | ✓ | ALIGNED |
| §3 PRODUCT.md thin labels + lang | template + parser | ✓ | ALIGNED |
| §4 Script structural / LLM judgment split | validation-rules-spec | ✓ | ALIGNED |
| §4 `--strict` errors block / warns advisory | workflow-validate | ✓ (LLM-layer only) | PARTIAL — W3-MED-4 |
| §5 Generate / traceability / consistency / matrix scripts | scripts/*.py | ✓ | ALIGNED |
| §6 Phased + resumable .session.md | workflow-interview | ✓ (spec; no scripted handler) | ALIGNED |
| §7 Typed subfolders / status lifecycle / semver | template + parser | ✓ | ALIGNED |
| §8 9 views × 3 formats (after validate gate) | viz | ✓ | ALIGNED (Phase 2 SC out of date — W4-MED-4) |
| §9 Flags + no-flag menu | SKILL.md | ✓ | ALIGNED |
| §10 Change-log + exec summary + sign-off | templates + workflows | ✓ | ALIGNED |
| §11 Parent-scoped IDs | scripts + validation | ✓ + fast-fail guards | ALIGNED |
| §13 v1 = everything | full surface | ✓ | ALIGNED |
| §14 RICH templates w/ REQUIRED/OPTIONAL markers | assets/templates | ✓ | ALIGNED |
| §15 Deferred items in-place; **viz filters them** | viz | ✗ filter missing | DRIFT — W4-MED-2 |
| §16 .session.md committed | output contract | ✓ | ALIGNED |
| §17 Edge cases (contradiction surfacing, stale .session) | workflows | ✓ documented | ALIGNED (no contradiction code; LLM driven) |
| §18 **CLAUDE.md inside skill dir** | docs | ✗ moved to repo root | DRIFT — W4-MED-1 |
| §18 EN + VI banks | references/interview-* | ✓ (VI best-effort) | ALIGNED |

## Test Coverage Gaps

Test suite is the strongest part of this skill — 57 tests, regression-named (NEW-1 through O-3, SA-*), CLI-level subprocess where it matters. But:

1. No test asserts persona/list defaults are valid lists (would catch W3-CRIT-1).
2. No test asserts visual ORIENTATION of Mermaid tree (would catch W3-HIGH-1).
3. No test asserts `install.sh` propagates pytest exit code (W3-HIGH-2).
4. No test covers `--viz delta` with 1 snapshot + live graph (W3-MED-2).
5. No test verifies scope:out / moscow:wont filtering in viz (W4-MED-2 wouldn't have been caught even if implemented).
6. No round-trip test: `generate_templates --type product --write` → `check_consistency` reports zero errors. The existing `test_fresh_vision_init_passes_consistency` covers vision only.

## Recommended Action Order

1. **W3-CRIT-1** (personas: TBD) — 1 line in `fill_defaults` + a new round-trip test. Blocks v1 ship.
2. **W3-HIGH-2** (install.sh false-success) — 3-line fix. Easy + serious.
3. **W3-HIGH-1** (Mermaid tree orientation) — 1-character fix (`TB` → `BT`) + visual-assert test.
4. **W4-MED-1** + W4-MED-5 (CLAUDE.md location) — surface to PO; do not silently re-add or amend.
5. **W4-MED-2** (viz filter for wont/out) — surface to PO; either implement or amend §15.
6. **W4-MED-3** (V6 horizon vs vision template) — delete V6.
7. **W4-MED-4** (Phase 2 SC4) — doc fix.
8. **W3-MED-1..4** — incremental.
9. **W3-LOW-* / W4-LOW-*** — janitor pass.

## Verification Evidence

- `pytest .claude/skills/product-spec/scripts/tests/ -q` → `57 passed in 0.49s` at HEAD.
- Live reproduction script for W3-CRIT-1 (personas/brd_goals as `TBD`) ran via repo venv against a temp fixture; output: `persona viz` shows rows `B`, `D`, `T`; `check_traceability` emits 3 phantom `dangling_link` errors for refs `T`/`B`/`D`.
- Live render of Mermaid tree confirms `BRD-G1 --> PRODUCT` edge → flowchart TB places PRODUCT at the bottom of the rendered SVG.
- `git status` confirms the rename `.claude/skills/product-spec/CLAUDE.md → CLAUDE.md`.

## Bottom Line

Skill is structurally sound and the implementer's regression discipline (every fix carries a NEW-/SA-/O-tagged test) is genuinely impressive. The bugs I found exist not because the work was sloppy but because the test suite focuses on what was built — none of the existing tests probe the *default-value* path or *cross-format consistency*. Three critical/high fixes + four decision-drift surfacings unblock a clean ship.

## Unresolved Questions

1. Is repo-root CLAUDE.md intentional (dev-only) or an oversight of decision §18? PO must answer keep/change/hybrid.
2. Should viz filter `wont` / `out` artifacts (decision §15) or is the current "show everything" the better default after seeing the example?
3. CI-runnable `--strict` gate (W3-MED-4) — in scope for v1 or defer? Brainstorm §4 implied yes but never specified the layer.
4. VI question banks — who reviews? (Brainstorm open item, still open.)
