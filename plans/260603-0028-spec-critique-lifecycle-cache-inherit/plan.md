---
title: "spec-critique: lifecycle caching + cross-critique inheritance (full 4-idea)"
description: "Wire the already-built scan plumbing (snapshot/drift/prior_reports/judgment reuse) into the live critique flow + add the 4 PO-confirmed caches (findings-index, web-url+TTL, critique-state, humanized-output), cross-critique inheritance (parent→child) + descendant rollup (child→parent). Mode: --hard --tdd."
status: pending
priority: P2
branch: "feat/product-spec-guardrails-and-memory-layer"
tags: [spec-critique, cache, inheritance, tdd]
blockedBy: []
blocks: []
created: "2026-06-02T17:39:11.827Z"
createdBy: "ck:plan"
source: skill
---

# spec-critique: lifecycle caching + cross-critique inheritance (full 4-idea)

## Overview

Implements the AGREED-NOT-IMPLEMENTED brainstorm `plans/reports/spec-critique-lifecycle-cache-design-brainstorm-report.md` (PO-confirmed 2026-06-02) in ONE plan (PO chose "full 4 ý 1 lần").

**Core insight (from brainstorm):** the lens layer is **voice-neutral** — lenses emit `{evidence,critique,why_it_dies,fix,severity}`; voice/level/register are applied only at consolidate+humanize. So lens findings are **independent of level** → cacheable; changing level only re-consolidates, never re-lenses. This is what makes provenance reuse + inheritance cheap.

**Two directions of cross-critique context (both default ON, opt-out):**
- **Inherit (parent→child):** when critiquing node X, surface the parent's prior blockers/DEC-worthy as "vấn đề cha = rủi ro con". Source = prior critique **reports** read via a findings-**index** (not the spec). Consumed by the **consolidator only**; lenses stay blind (anti-anchoring).
- **Rollup (child→parent):** when critiquing a PRD/epic, aggregate the verdicts of its already-critiqued children ("3/5 stories unbuildable → PRD has a delivery problem").

**5 caches (4 PO-adopted + 1 added by red-team R1):** findings-index (`critique-findings-index.json`), web-url cache+TTL (`web-cache/<url-hash>`), per-scope freshness marker (`critique-state.json`), humanized-output cache, **lens-findings cache** (`critique-lens-cache/<hash>.json` — full lens arrays, the store that makes `consolidate_only` real; see R1).

**Economic gate, not safety gate:** every cache/reuse saves tokens only; `--fresh`/`--force` bypass all reuse, `--refresh-web` forces market re-fetch. The Q3 floor + subagent-split invariants are NON-overridable.

### Ground-truth from research (anchors the plan)

- `critique_scan.py` = **497 LOC** (already over the 200 guideline) → new logic goes in focused modules `critique_cache.py` + `critique_inherit.py`, NOT inline. Existing reusable funcs: `emit_bundle`, `write_snapshot`, `compute_drift`, `_build_ancestry` (uses `spec_graph.ancestors()`), `_resolve_targets` (uses `downstream()`), `_prior_reports`, `_live_body_hashes`, `_diff_hashes`.
- Reused product-spec APIs (confirmed signatures): `spec_graph.ancestors(graph,id)` / `downstream(graph,id)` / `build_graph(root)`; `preferences.load/save`; `judgment_cache.load_cache`; `fs_guard.assert_under_docs_product(path,root)`.
- **Critique reports currently have NO YAML frontmatter** (start with `# Critique: <scope> · level N · lenses:`). Provenance (Q1) = **add** frontmatter carrying the per-node `body_hash` map + level/lang/register. `_prior_reports` parses frontmatter when present, **falls back to filename** (existing fixtures lack it → safe degrade = re-lens).
- **No regen harness exists** (`.regen-lenses-*` dropped in commit 301eafe). E2E = hand-committed `voice-ladder9-<lang>-lvl<N>.md`.
- Test infra: `scripts/tests/` with `conftest.py` (sys.path) + `critique_test_support.py` (`make_proj`, `run_scan`, `append_to`). New TDD tests follow this pattern.
- `pack.manifest.yaml` enumerates skills by name → new script modules ship automatically; only a **version bump 1.1.0→1.2.0** + CHANGELOG entry needed (no file-list edit).

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Script: cache+state primitives](./phase-01-script-cache-state-primitives.md) | Pending |
| 2 | [Script: provenance reuse + report frontmatter](./phase-02-script-provenance-reuse-report-frontmatter.md) | Pending |
| 3 | [Script: inherited_context + descendant rollup](./phase-03-script-inherited-context-descendant-rollup.md) | Pending |
| 4 | [Orchestration references + voice floor](./phase-04-orchestration-references-voice-floor.md) | Pending |
| 5 | [E2E fixtures + evals](./phase-05-e2e-fixtures-evals.md) | Pending |
| 6 | [Docs sync + claude-pack release](./phase-06-docs-sync-claude-pack-release.md) | Pending |

## Execution order & dependencies

```
P1 (cache/state primitives, pure data)
  └─> P2 (provenance reuse + report frontmatter)  -- needs critique-state from P1
        └─> P3 (inherited_context + descendant rollup) -- needs findings-index (P1) + provenance helpers (P2)
              └─> P4 (orchestration references wire the scripts into the flow)
                    └─> P5 (e2e fixtures + evals exercise the wired flow)
                          └─> P6 (docs sync + version bump, last)
```

Strictly sequential — each phase consumes the prior. P1–P3 are the deterministic **Script** half (full `--tdd`, unit tests first). P4 is the **LLM-orchestration** half (markdown references; "tested" by P5 fixtures, not unit tests — the brainstorm's honest ceiling: voice/judgment is not unit-testable). P5 mixes structural evals (checkable) + fixture regen. P6 is docs+release.

## TDD boundary (honest)

`--tdd` covers **only the Script half (P1–P3)**: cache keying, index upsert, TTL expiry, evidence-ID graph classification, provenance diff, fresh-only filter — all pure input→output, unit-tested first. The LLM half (lens voice, consolidator judgment, humanizer) is **not** unit-testable; P5 covers it via structural evals + boundary fixtures, never by asserting prose. Do not fake LLM-output assertions to "pass" a phase.

## Red-team resolutions (post-review, before cook)

Two independent reviews (red-team + plan-quality) found 3 blockers + 2 majors. Resolutions, baked into the phases below:

- **R1 — lens-findings store (was the headline-mechanism gap).** The findings-index is a LOSSY evidence-ID query cache (blockers+DEC, `{evidence_id,severity,why,fix,dec_worthy}`) — it CANNOT reconstruct the full lens objects `{lens,evidence,critique,why_it_dies,fix,severity,source}` a re-consolidate needs. The brainstorm Q1 explicitly intended the report to carry **lens findings** (not just a hash). Fix WITHOUT reversing the PO's "đổi level chỉ re-consolidate" decision: add a **5th store — a lens-findings cache** `docs/product/.memory/critique-lens-cache/<lens_findings_hash>.json` holding the FULL lens-findings array. `consolidate_only`/partial-`relens` read THAT; the findings-index stays the evidence-ID cache for inherit/repeat-offense. Two caches, two keys, no conflation. (P1 adds the store; P2 detects+keys; P4 reads it on reuse.)
- **R2 — register the 3 new preferences (cross-skill edit).** `preferences.load()` drops any key not in `DEFAULTS`. `critique_inherit`/`critique_rollup` (enum `{on,off}`, default `on`) + `critique_inherit_depth` (enum `{nearest,deep}`, default `nearest`) MUST be added to `DEFAULTS`+`ENUMS` in **`product-spec/scripts/preferences.py`** (shared skill), with the YAML `on/off→bool` coercion the existing enums get. P3 owns this edit (added to its Modify list) + a `load` round-trip test. The CHANGELOG (P6) notes this as a product-spec touch, not spec-critique-only.
- **R3 — caches are committed, not gitignored (correct the false claim).** `.memory/` IS committed (verified: e2e `.memory/` is tracked). **PO decision (2026-06-03): commit ALL 5 caches** — index/state/lens-cache/web-cache/humanized-cache — following the existing committed-`.memory/` convention; NO new `.gitignore` rule. The trade-off (web-cache holds scraped third-party page content + repo bloat) was surfaced to the PO, who chose commit-all for consistency. P1 just corrects the earlier false "gitignored runtime data" prose; it adds NO `.gitignore` edit.
- **R4 — provenance scope-match uses frontmatter only.** `_prior_reports`' filename parse (`partition("-")`) mangles real names (`c1-all-lvl3`→scope `all-lvl3`). `compute_provenance_reuse` matches scope from frontmatter `critique_scope` ONLY; any filename-only prior → `reuse: none` (safe re-lens). P2 owns this + a `c1-all-lvl3.md`-style degrade test.
- **R5 — `critique-state.json` gets a reader (no dead data).** It is consumed as the provenance **fast-path**: `compute_provenance_reuse` reads `critique-state.json`'s `provenance_hash` to short-circuit before opening the prior report. P2 wires the read. (Forward `--status` "scope nào cần critique lại" stays a documented future consumer, not built here.)

Minor fixups also applied: `--no-inherit` beats `--inherit=deep` (off wins; documented in P3); standardize the display form `--inherit deep` across docs (P6); P2 widens the existing bundle-shape test to a subset assertion when adding `provenance`.

### R6 — Validate finding (PO-confirmed 2026-06-03): the lens is NOT voice-neutral today; refactor it

The brainstorm's load-bearing premise — "**lens layer voice-neutral**, voice applied only at consolidate+humanize" — is the basis for `consolidate_only` (reuse lens findings across levels). **Validate verified this premise is FALSE in the shipped code:** the 4 lens prompts are double-voiced — `spec-critique-product.md:61` writes `critique` "in the active lang/level" and `:86` says "Follow voice-and-tone.md at the `--level`", while `:87` contradictorily says "the consolidator renders the level voice downstream". The `.regen-lenses` harness the brainstorm cited as proof was deleted (commit 301eafe). A level-3-voiced cached `critique` reused to render level 7 would carry level-3 residue → wrong-level output.

**PO decision: refactor the 4 lens prompts to be truly voice-neutral** — the lens `critique` field becomes a neutral grounded observation; the **consolidator is the SOLE home for voice/level/register** (it already has the full level/register logic, `spec-critique-consolidate.md:99-129`). This is a PREREQUISITE for `consolidate_only` correctness and aligns the code with the brainstorm premise. **Added to P4 as its first requirement.** Because the neutralization changes voice output, **P5 regenerates ALL 18 voice-ladder fixtures under the new model** (see R7) so the committed corpus is one model — not a pre/post-R6 mix.

### R7 — Full fixture regen (PO decision 2026-06-03, supersedes the original "boundary only" arg)

The original `/ck:plan` arg said e2e "lv5-en + 8 + 9 vi — boundary only". **PO revised: regenerate ALL 18 voice-ladder fixtures (vi lvl1–9 + en lvl1–9), every one with frontmatter, post-R6, and remove every stale/no-frontmatter critique file** — so there is full, model-consistent context to check bugs + regressions (a pre/post-R6 mix would be stale data masking drift). Baked into P5: overwrite all 18 in place + purge the older `c1-c10` ad-hoc set (regen-with-frontmatter only if a unique coverage gap is found). The 3 boundary levels (lv5 / lv8-vi / lv9-vi) remain the canaries the floor/escalation checks watch hardest, but are no longer the regen scope.

**De-risk evidence (2026-06-03 workflow):** a GATED workflow just regenerated all 18 (vi `{f,trung,strong}` + en `{m,bac,abbrev}` matrix) by running **bundle + 4 lenses ONCE per lang, then consolidate+humanize+JUDGE per level** — i.e. it already executed the R6 neutral-lens + consolidate_only architecture in practice, producing 18 reports with `floor_breaches: []`, `all_clean: true`, `en_7 ≠ en_8` verified. This PROVES the core mechanism works. Those 18 bodies carry no frontmatter and are not in the P1 lens-cache → they are a correctness REFERENCE only. **PO decision: P5 does a FULL RE-RUN, not a retrofit** — regenerate through the genuine wired flow (lenses once → lens-cache → consolidate_only per level → frontmatter), delete the old bodies, do NOT prepend-frontmatter or hand-fix generated data. Rationale (PO): "we need full flow to test, not make it look valid." The retrofit shortcut is explicitly rejected. Cost (~2–2.7 h) accepted; the run doubles as the live test of the lens-cache + consolidate_only path.

## Non-negotiable invariants (Q3, carried from brainstorm)

- **Floor "TARGET decides, not STRENGTH"** + **subagent-split** (read-only lenses/consolidate + independent Gate-2 humanizer) are BẤT BIẾN. PO may override level/register/profanity-strength/scope/lenses/detail; PO may NOT override the harm floor or collapse subagents into the main agent.
- **Lens ignores `inherited_context`** (5 reasons in brainstorm §"Vì sao lens BỎ QUA"): anti-anchoring, scope discipline, consolidator's job, ×4 cost, double-surface. Inherited items go in a SEPARATE report section, NOT into the severity tally.

## Dependencies

No cross-plan blockers. Sibling done-plans (context only): `260602-0219-spec-critique-brutal-skill` (skill creation, DONE per PO), `260602-1528-spec-critique-lv7-9-and-split-detail-level` (levels 7-9 + detail split, complete). This plan extends both; no file conflict (those shipped; this adds new modules + wires references).
