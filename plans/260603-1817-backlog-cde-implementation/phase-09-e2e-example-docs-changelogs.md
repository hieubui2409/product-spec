---
phase: 9
title: "9a — E2E (selectively extend /e2e/dating-app) + lv5 acme showcase"
status: pending
priority: P1
effort: "2d"
dependencies: [1, 2, 3, 4, 5, 6, 7, 8]
---

# Phase 9 (9a): E2E + real examples + test rewire

> **Rewritten after Phase-9 red-team (2026-06-03).** Pivots from "fresh run + wholesale delete" to "EXTEND the
> already-committed `/e2e/dating-app/` run, regenerate acme-shop via the real workflow, and rewire the tests
> that bind to examples." Docs + changelogs split out to Phase 10 (9b).

## Overview
Produce the canonical real examples by driving BOTH spec ecosystems THROUGH the workflow, then rewire the
tests that bind to example paths so the suite stays green.

## Key facts (corrected by red-team)
- **`/e2e/dating-app/` already exists committed** — full BRD→PRD→epic→story, 18 critique reports (frontmatter-bearing), `.memory/` caches; `.gitignore:143-147` special-cases `/e2e/**`. It is the base, not greenfield.
- **`examples/` are test-bound:** `test_voice_examples_grounding.py:22-39` hardcodes the 6 acme-shop critique filenames + fix-labels + citation line-counts (a **safety harm-floor grounding contract**); `test_phase7_release.py:44` binds `examples/acme-shop`; `test_golden_product_spec.py` asserts the bundle tree.
- Lifecycle features exist + invocable: `critique_inherit`/`critique_rollup`/`critique_inherit_depth` (`critique_bundle.py:71,106`), `--fresh` (`SKILL.md:57`) — but OFF by default; the existing e2e never exercised them (all `scope:all` voice demos).
- Caches are under `<root>/docs/product/.memory` (committable) but carry timestamps + abs paths + web-scraped text (`critique_blob_cache.py:57`, `critique_provenance.py:62`).

## Decisions applied (PO 2026-06-03)
- **dating-app:** EXTEND the existing committed run **selectively** — KEEP artifacts still valid under the new features; **RE-CREATE only what the new features touch or invalidate** (e.g. critique reports after strengthened lenses, caches after re-runs, the spec if `goal_without_metric` requires goal metrics). Not a blind extend, not a full redo. Run the NEW flows on it: `--apply-critique`, `--discover`, `--viz audit`, `--summary --audience`, `goal_without_metric`, strengthened lenses + the full **critique lifecycle** (rerun→cache-hit, `--fresh`→cache-miss, inherit parent→child, rollup child→parent).
- **acme-shop:** ADD a **level-5** (default) critique showcase produced via the real workflow. **KEEP the existing lv7-9 harm-floor safety fixtures + their grounding test UNTOUCHED** — do not regenerate or delete them (avoids disturbing the safety contract entirely).
- **Examples = the selectively-updated dating-app run + the new lv5 acme showcase + the retained lv7-9 safety fixtures.** No wholesale delete.

## Architecture / approach
### A. Extend dating-app SELECTIVELY (full flow + lifecycle)
- **Audit keep-vs-recreate FIRST:** inventory the existing `/e2e/dating-app/` artifacts; mark each KEEP (still valid) or RECREATE (a new feature touches/invalidates it — e.g. critique reports go stale after strengthened lenses; caches after re-runs; the spec if goals need metrics for `goal_without_metric`). Recreate only the RECREATE set.
- Drive THROUGH the workflow refs (interview→validate→critique→apply-critique→discover→viz→summary). NOTE: `workflow-apply-critique.md` (Ph3) + `workflow-discover.md` (Ph6) are net-new — this phase's `[1..8]` gate is mandatory.
- **inherit/rollup setup (explicit):** set `critique_inherit: on` + `critique_rollup: on` + `critique_inherit_depth` in the run's `preferences.yaml`; critique a PARENT (a named PRD) → then a CHILD story (shows inherit) → re-critique the parent (shows child→parent rollup). Name the exact node ids in the run log.
- **cache cases:** critique unchanged → cache HIT; `--fresh`/edit a node → cache MISS.

### B. acme-shop — add a level-5 real showcase, keep lv7-9 safety fixtures untouched
- ADD a **level-5** critique of acme-shop produced via the real workflow → the default-voice showcase example.
- **KEEP the existing lv7-9 harm-floor safety fixtures + `test_voice_examples_grounding.py` UNTOUCHED** — they remain the safety contract as-is. No regeneration, no deletion, no test rewire. (This is why acme stays lv5: the safety lv7-9 set is left alone.)
- If the lv5 showcase adds new files under `examples/`, the only test impact is re-baselining the golden bundle tree (see E) — NOT the safety grounding test.

### C. Curate + commit hygiene
- Commit the spec artifacts + critique reports + audit output + `.memory/` caches (the lifecycle demonstration), **but scrub:** normalize/strip non-deterministic `stored_at`/`fetched_at`/`last_ts` + absolute `path` fields; **exclude `web-cache/`** (third-party scraped text — do not ship). "Leak risk" = synthetic seed safe, paths/web-text scrubbed.
- **Bilingual:** pick ONE canonical language for the frozen freshness-fixture pair (default `vi`); the other language is illustrative-only (NOT a body_hash fixture) to avoid the two-runs-different-hash contradiction.

### D. Phase 3 freshness fixture (resolve ordering inversion)
- Designate the dating-app critique reports (which carry frontmatter + `body_hash`) as **Phase 3's E1 freshness fixture**. This means the dating-app run (or a minimal frontmatter'd critique fixture) must exist EARLY enough for Phase 3 — see plan dependency note. Add a guard test that fails if the spec example is edited without regenerating the paired critique fixture hash.

### E. Test impact (suite must stay green — plan.md:40) — now MINIMAL
- **`test_voice_examples_grounding.py` — UNTOUCHED** (lv7-9 safety fixtures kept). The safety contract is not disturbed.
- **`test_golden_product_spec.py` — re-baseline** if the lv5 acme showcase adds files under `examples/` (bundle arcname tree changes). `/e2e/dating-app/` is outside the bundled skill tree (`.gitignore:143-147`) so its changes don't affect the golden bundle.
- **`test_phase7_release.py` — only if the acme-shop SPEC changes** (e.g. adding goal metrics for `goal_without_metric`); if the acme spec is unchanged, this stays green. Check + update only if touched.
- The "script-half smoke" is a **fixture-replay** against the committed example: assert real structural values (bundle node count, lens-cache hash present, drift=0) — NOT a standalone run (scripts exit 0 advisory → would pass vacuously on an empty root).

## Related Code Files
- Extend/curate (selective): `e2e/dating-app/**` (keep valid artifacts; recreate only what new features touch; scrub caches; exclude web-cache)
- Add: a **level-5** acme-shop critique showcase under `product-spec-critique/examples/` (do NOT touch the lv7-9 safety fixtures)
- Re-baseline (only if affected): `claude-pack/scripts/tests/test_golden_product_spec.py` (added example files); `product-spec/scripts/tests/test_phase7_release.py` (only if acme SPEC changes for goal metrics)
- UNTOUCHED: `product-spec-critique/scripts/tests/test_voice_examples_grounding.py` (lv7-9 safety contract)
- Reference for Phase 3 fixture: dating-app critique reports

## Implementation Steps
> **TDD:** if added example files change the golden bundle, update that test's baseline FIRST (confirm red→green); keep the lv7-9 safety grounding test green untouched throughout.
1. Audit `/e2e/dating-app` keep-vs-recreate; extend selectively through the workflow: new flows + lifecycle (prefs on; parent→child→parent named nodes; cache hit/miss).
2. Add a **level-5** acme-shop critique showcase via the real workflow; leave lv7-9 safety fixtures + their test untouched.
3. Scrub caches (timestamps/paths) + exclude `web-cache/`; pick canonical-lang fixture.
4. Re-baseline `test_golden_product_spec.py` if example files were added; update `test_phase7_release.py` only if the acme spec changed → suite green.
5. Designate dating-app critique reports as Phase 3's freshness fixture + add the desync-guard test.

## Success Criteria
- [ ] `/e2e/dating-app` extended SELECTIVELY (keep-vs-recreate audited) through the real workflow exercising EVERY new surface + full critique lifecycle (cache hit/miss, inherit, rollup) with named nodes + run log.
- [ ] A **level-5** acme-shop showcase added via real workflow; **lv7-9 safety fixtures + grounding test left untouched + still green**.
- [ ] Caches committed with timestamps/paths scrubbed + `web-cache/` excluded; canonical-lang freshness fixture frozen.
- [ ] Golden bundle re-baselined if files added; `test_phase7_release` updated only if acme spec changed; **full suite green** (no test-count reduction); script-half is a fixture-replay asserting real values (no vacuous pass).
- [ ] dating-app critique reports designated Phase 3's E1 freshness fixture + desync-guard test added.

## Risk Assessment
- Risk: disturbing the safety contract → AVOIDED entirely by keeping lv7-9 fixtures + their test untouched (acme showcase is lv5, additive).
- Risk: committing caches leaks paths/web-text → scrub ts/paths + exclude web-cache (M1).
- Risk: ordering inversion with Phase 3 → dating-app critique reports designated as Phase 3's input (see plan dependencies); if Phase 3 builds first, it uses a minimal frontmatter'd critique fixture copied from `/e2e/dating-app/` that this phase later supersedes.
- Risk: selective keep-vs-recreate mis-judged (keep a stale artifact) → the audit step is explicit; recreate anything a new feature touches.
- Risk: wholesale delete would red committed tests → AVOIDED (selective extend + additive lv5, not delete).
