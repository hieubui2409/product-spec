---
phase: 5
title: "E2E fixtures + evals"
status: completed
priority: P1
effort: "2d"
dependencies: [4]
---

# Phase 5: E2E fixtures + evals

## Overview

Prove the wired flow end-to-end AND produce a clean post-R6 regression baseline. Three kinds of coverage: (a) **structural evals** (checkable, added to `evals.json`) for the new lifecycle behaviors; (b) **FULL voice-ladder regen** — ALL 18 fixtures (vi lvl1–9 + en lvl1–9) regenerated under the post-R6 neutralized-lens model, every one carrying the new YAML frontmatter, with NO stale pre-R6/no-frontmatter files left behind (PO decision 2026-06-03, supersedes the earlier "boundary only"); (c) **use-case fixtures** exercising the new cross-critique context. Rationale for full regen: a complete, model-consistent, frontmatter-uniform corpus is the only sound baseline to diff for bugs + regressions — a mix of pre-R6 and post-R6 fixtures would be stale data that masks drift. No prose assertions — voice is judged by the existing grounding tests + llm_advisory evals, never by string-matching the sarcasm.

## Requirements

- **FULL voice-ladder regen — all 18 fixtures (PO decision, supersedes "boundary only"):**
  - `voice-ladder9-vi-lvl1.md … vi-lvl9.md` (9) + `voice-ladder9-en-lvl1.md … en-lvl9.md` (9) = **18**, scope `all`, one per level per lang.
  - **Every file regenerated under the post-R6 neutralized-lens model** (must run AFTER P4's R6 lens refactor — the whole point is a model-consistent baseline) and **carries the new YAML frontmatter** (P2: `critique_scope`/`level`/`lang`/`register`/`body_hash`/`lens_findings_hash`/`bundle_version`), so they double as provenance-parse fixtures.
  - **Remove stale, no mixed data:** overwrite in place (same filenames) so no pre-R6 copy survives; verify via git that all 18 are re-touched and none retains the old (pre-frontmatter) content. **Also reconcile the older ad-hoc `c1-c10` numbered fixtures** (`c1-all-lvl3.md` … `c10-PRD-MATCH-E1-S1-lvl6.md`): these are pre-frontmatter, pre-R6, single-level scope-varied leftovers → **remove them** (the full ladder covers level-variety; the use-case fixtures below cover scope-variety PRD/epic/story + inherit/rollup), UNLESS the implementer finds a coverage gap they uniquely fill — if so, regen them with frontmatter instead of deleting. Either way: no pre-R6/no-frontmatter critique file remains in the dir.
  - Boundary semantics still tracked WITHIN the full set: lv5 = ungated personal-attack baseline; lv8-vi = street `mày/tao`, character attack, NO profanity; lv9-vi = work-targeted profanity, harm floor holds. These three are the canaries the grounding/floor checks watch most closely.
- **Use-case fixtures (the new cross-critique behaviors) — under `e2e/dating-app/docs/product/critique/`:**
  - **Context from PARENT/ANCESTOR (inherit):** critique a child story whose PRD (and a BRD goal) were critiqued earlier with blockers; assert the child report has the "Kế thừa từ cha" section citing `<parent-id>@<ts>`, blockers only, NOT in the tally.
  - **Context from CHILDREN (rollup):** critique a PRD/epic after ≥2 of its child stories were critiqued with blockers; assert the rollup verdict line + counts.
  - **Same node, SAME level (provenance reuse):** critique node X at level L, no spec change, re-run at level L → `provenance.reuse == full` (or `consolidate_only`), lenses NOT re-run.
  - **Same node, DIFFERENT level (re-consolidate only):** critique X at level 3, re-run at level 7, no spec change → `provenance.reuse == consolidate_only`, lens findings reused, voice escalated.
  - **After spec edit (re-lens):** mutate one node body → `provenance.reuse == relens` for exactly that node.
  - **Full use-case of new changes:** one scripted walk: critique `all` → critique a PRD (inherits from `all`, rolls up children) → edit a story → re-critique that story (relens + inherit) → bump level (consolidate_only). This is the integration narrative.
- **`evals.json` additions (structural where possible):**
  - provenance: `reuse=full/consolidate_only/relens` produce the documented header note; `--fresh` forces a full fresh run.
  - inherit: child report has a separate inherited section, evidence cites an ancestor ID, item absent from tally (structural: grep the tally vs the inherited section).
  - rollup: parent report shows child blocker counts.
  - lens-blind: no lens finding cites an evidence-ID outside the scope subtree (structural-ish: IDs resolve within `target_ids`).
  - web-TTL: with a warm web-cache + no `--refresh-web`, the market lens reuses (advisory) — keep honest about non-determinism.
  - keep existing 13 evals intact; append, don't renumber.
- **Unit/grounding test extensions:**
  - `test_voice_examples_grounding.py`: parametrize over **all 18 regenerated ladder fixtures** (citations resolve, fix-label present per level, every finding-line grounded, level-escalation monotonic). Tolerate frontmatter (parse past the `---` block before scanning headings). Since every fixture now carries frontmatter, the scanner can assume it (no mixed pre/post handling needed once the dir is clean).
  - `test_critique_scan.py`: assert new bundle keys (`provenance`, `inherited_context`, `descendant_rollup`) present + shaped; assert a frontmatter report parses into the richer `_prior_reports` record. (The old "no-frontmatter fixture still parses" case stays as a unit-level fixture string in the test, not as a committed file — the committed corpus is now all-frontmatter.)

## Architecture

Fixtures are LLM-generated reports committed as golden files (same as the existing voice-ladder set). The *structural* parts (frontmatter parses, inherited section exists, tally excludes inherited, IDs resolve) are machine-checkable and go in `evals.json` + pytest. The *voice* parts stay advisory (the honest ceiling). The integration walk is documented as an eval scenario, executed manually/with the skill, output committed.

## Related Code Files

- Overwrite (regen, all 18): `e2e/dating-app/docs/product/critique/voice-ladder9-vi-lvl{1..9}.md` + `voice-ladder9-en-lvl{1..9}.md` (post-R6, WITH frontmatter)
- Delete (stale, pre-R6/no-frontmatter): `e2e/dating-app/docs/product/critique/c1-all-lvl3.md` … `c10-PRD-MATCH-E1-S1-lvl6.md` (10 files) — unless a unique coverage gap is found, then regen-with-frontmatter instead
- Create: use-case fixtures (inherit / rollup / provenance walk) under the same critique dir — names like `usecase-inherit-PRD-CHAT-E1-S4-from-parent.md`, `usecase-rollup-PRD-CHAT.md`, `usecase-provenance-walk.md`
- Modify: `.claude/skills/spec-critique/eval/evals.json` (append lifecycle evals, keep 0-12)
- Modify: `.claude/skills/spec-critique/scripts/tests/test_voice_examples_grounding.py` (parametrize over all 18 ladder fixtures, assume frontmatter)
- Modify: `.claude/skills/spec-critique/scripts/tests/test_critique_scan.py` (new bundle keys)
- Read for context: existing `voice-ladder9-*` fixtures (format), `evals.json` (eval shape), `e2e/dating-app/docs/product/` spec + `.memory/`

## Implementation Steps

0. **Precondition:** P4's R6 (lens neutralization) is landed — the corpus must be one model. The existing pre-R6 18 (workflow 2026-06-03) are a correctness REFERENCE only; they are deleted and regenerated, NOT retrofitted.
1. **FULL RE-RUN — the only path (PO decision 2026-06-03): exercise the genuine flow, do not doctor data.** Run the wired skill for real: lenses ONCE per lang → write the full lens array to the P1 **lens-cache** → `consolidate_only` from that cache for each of the 9 levels → humanize → write WITH frontmatter (`build_report_frontmatter`, P2). `--lang vi --level 1..9` + `--lang en --level 1..9`, scope `all`. **DO NOT** prepend frontmatter to old bodies, **DO NOT** hand-edit generated output, **DO NOT** make a stale corpus "look valid" — the whole point is to test the real end-to-end flow (lens-cache → consolidate_only → frontmatter → provenance), so the fixtures must be its genuine output. This also validates the lens-cache "keep findings, consolidate all levels" path (R1) on a real 9-level run. **Purge stale FIRST:** delete the existing 18 pre-R6 bodies + the `c1-c10` set so nothing stale survives; after regen, `grep -L '^---'` over the critique dir must return ZERO no-frontmatter files and the lens-cache must hold the vi + en arrays the frontmatter hashes point to. A fresh run MUST stay floor-clean + en7≠8 + monotonic-escalation vs the reference (regression gate). Commit as the clean golden corpus.
2. Generate the use-case fixtures by running the scripted walk against the dating-app spec. **Precondition (bootstrap, M3):** inherit/rollup need a populated index — critique **parents BEFORE children** (and `all` before a PRD) so the index is seeded; run-1 empty-context is expected, not a bug. The e2e `.memory/` **IS committed** (verified — `judgments.json`/`last_critique.json` are tracked), so commit ALL resulting caches as golden fixtures — `critique-findings-index.json` + `critique-state.json` + `critique-lens-cache/` + `web-cache/` + `humanized-cache.json` (PO chose commit-all, R3; no gitignore).
3. Append the lifecycle evals to `evals.json` (structural gating where the check is mechanical; llm_advisory only where genuinely a judgment).
4. Extend the two pytest modules; the grounding scanner now assumes frontmatter (dir is clean).
5. Run full spec-critique pytest + run ALL 18 ladder fixtures through the grounding test → green; eyeball level-escalation monotonicity across the ladder as the regression canary.

## Success Criteria

- [ ] ALL 18 ladder fixtures (vi 1–9 + en 1–9) regenerated post-R6 WITH frontmatter; grounding test green on all 18; level-escalation monotonic; lv9-vi holds the harm floor (no slur/threat/family-target), lv8-vi has register but no profanity, lv5 is the ungated baseline.
- [ ] No stale data: `grep -L '^---'` over the critique dir returns zero (every committed critique file carries frontmatter); the pre-R6 `c1-c10` set removed (or regen-with-frontmatter); git shows all 18 touched.
- [ ] Use-case fixtures demonstrate: inherit-from-parent (separate section, not in tally), rollup-from-children (counts), provenance full/consolidate_only/relens, and the full integration walk.
- [ ] `evals.json` has appended lifecycle evals; original 0-12 unchanged and not renumbered.
- [ ] `test_voice_examples_grounding.py` + `test_critique_scan.py` green with the full 18-fixture set + new bundle keys.
- [ ] No prose-string assertions on voice (only grounding/structure asserted).

## Risk Assessment

- **Risk: fixtures are LLM-generated → non-deterministic, can't byte-assert.** Mitigation: assert STRUCTURE only (sections exist, IDs resolve, tally excludes inherited, frontmatter parses); never assert sarcasm text. This is the brainstorm's stated honest ceiling.
- **Risk (R6): the lens voice-neutralization (P4) changes voice output → regenerating all 18 under the new model is exactly the point** (a model-consistent baseline). The old 18 fixtures are discarded, not reconciled — so the diff that matters is "post-R6 corpus vs future runs", not "pre vs post R6". Verify level-escalation still climbs monotonically across the regenerated ladder as the regression canary.
- **Risk: e2e `.memory/` commit convention.** Resolved: e2e `.memory/` IS committed (verified). Commit ALL 5 caches as fixtures (PO commit-all, R3). No new convention introduced; no gitignore.
- **Risk: full 18-fixture regen is expensive** (~18 × 6–9 min LLM-generation ≈ 2–2.7 h during cook, sequential). Accepted: PO wants the full corpus for bug/regression context; it is a one-time baseline cost, not per-CI. Run it as a background batch; it does not block the script-half tests (P1–P3).
- **Risk: deleting the `c1-c10` set drops scope-variety goldens.** Mitigation: the use-case fixtures cover PRD/epic/story scopes + inherit/rollup; if a unique c-set scenario is found, regen it with frontmatter instead of deleting. Flag any genuine gap to the PO rather than silently losing coverage.
- **Risk: lens-blind eval is hard to make fully mechanical.** Mitigation: approximate structurally (all lens evidence-IDs ∈ target_ids subtree); flag residual as advisory honestly.
