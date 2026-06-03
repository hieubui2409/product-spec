# Red-Team Review — Phase 9 (capstone E2E + examples + docs + changelogs)

> 2026-06-03 · 2 reviewers (Failure-Mode, Assumption-Destroyer). All `file:line`-evidenced. Strong convergence.
> Verdict: the phase's premise (run fresh E2E + wholesale-delete examples) collides with **committed tests + an
> already-committed `/e2e/dating-app/` run**. Pivot needed.

## 2 Critical · 5 High · 2 Medium

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| C1 | Critical | Wholesale-delete of `examples/` REDS committed tests with no update step: `test_voice_examples_grounding.py` (a **safety harm-floor grounding contract** — hardcodes 6 filenames + fix-labels + citation line-counts), `test_phase7_release.py` (`acme-shop` fixture), `test_golden_product_spec.py` (golden bundle). Violates plan "no test reduction" (plan.md:40). | **PO call** (see Q1) |
| C2/B | Critical | The safety grounding test encodes the OLD example's content (level7-9 fix-labels incl. VI profanity tokens, `ID_LINES`). A faithful rebuild can't satisfy it → safety contract silently lost. | tie to Q1 |
| H1 | High | **`/e2e/dating-app/` already exists committed** (full BRD→PRD→epic→story, 18 critique reports, `.memory/` caches, `.gitignore:143-147` special-cases `/e2e/**`). Phase never reconciles it — duplicates its own deliverable. | **PO call** (Q2) |
| H2 | High | **Ordering inversion:** Phase 3 (E1) needs a frontmatter'd freshness fixture, but Phase 9 (last, `[1..8]`) produces it → circular. `/e2e/dating-app/` critique reports already carry frontmatter → use them as Phase 3's fixture. | **Accept** — designate /e2e as Phase 3 fixture |
| H3 | High | inherit/rollup are OFF by default + existing e2e never exercised them (all `scope:all` voice demos). Need explicit `preferences.yaml` toggles + a parent→child→parent critique sequence with named node ids. | **Accept** — add setup steps |
| H4 | High | 2 driving workflow refs don't exist yet: `workflow-apply-critique.md` (Ph3), `workflow-discover.md` (Ph6) — net-new. `[1..8]` gate is mandatory; `workflow-critique.md` lives in the critique skill, not product-spec. | **Accept** — correct ref grouping |
| H5 | High | Changelog backfill mis-attributable: product-spec's "22 commits" are **contaminated** with `feat(spec-critique)` commits (rename moved through the subtree); critique path has 1 commit. Raw `git log -- <path>` mis-attributes critique features to product-spec. | **Accept** — filter by subject scope + `--follow` |
| M1 | Med | Committed caches carry non-deterministic timestamps + absolute paths + **web-scraped third-party text** (`critique_blob_cache.py:57`, `critique_provenance.py:62`). "leak risk NONE" is wrong (only covers the synthetic seed). | **Accept** — scrub ts/paths, exclude web-cache |
| M2 | Med | Bilingual "two runs / translated pass" contradicts "freeze the pair so body_hash matches" — different bodies → different hashes. | **Accept** — one canonical-lang fixture |
| M3 | Med | "Repeatable script-half smoke" needs LLM-produced artifacts; scripts exit 0 advisory → vacuous green on empty root. It's a fixture-REPLAY against a committed spec, not a standalone smoke. | **Accept** — reframe as fixture-replay asserting real values |

## Verified RIGHT (calibration)
- `critique_inherit`/`critique_rollup`/`critique_inherit_depth` prefs + `--fresh` cache-bypass exist + wired (`critique_bundle.py:71,106`; `SKILL.md:57`).
- Caches ARE under `<root>/docs/product/.memory` (committable, not a global cache) — so "include caches" IS achievable (just needs scrubbing).
- No skill-level CLAUDE.md; root CLAUDE.md (145 lines) mixes all 3 skills — edit the right section only.
- product-spec has a real `--product`/init entrypoint.

## Decisions for PO
1. **examples (C1/C2):** the `acme-shop` level7-9 examples back a SAFETY harm-floor grounding test. Wholesale-delete kills it. Keep acme-shop as the safety fixture + ADD the e2e material as the new showcase example? Or wholesale-delete and rewrite the safety test to glob-discover dynamically?
2. **`/e2e/dating-app/` (H1):** make it the canonical E2E to EXTEND (run the new flows on it, curate it as the example, use as Phase 3 fixture)? Or delete it and run fresh?
3. **Split (M3 + scope):** docs surfaces ≈ 2,400 lines across 10 files (two ~740-line bilingual GUIDEs) + E2E + test-rewiring → 2d is light. Split Phase 9 into 9a (E2E + example + test rewiring) and 9b (docs sweep + changelog)?

## Unresolved
- Which language is the canonical freshness-fixture pair (M2)?
- Is shipping web-cache scraped third-party text in the bundled example acceptable, or always exclude `web-cache/` (M1)?
