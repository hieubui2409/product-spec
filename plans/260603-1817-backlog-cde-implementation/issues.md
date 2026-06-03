# Issues & Deferred Decisions — Backlog C/D/E implementation

> Captured during `/ck:cook` ultracode run (2026-06-03). **Not interviewed during the run** per PO
> instruction ("run all, do not interview user … interview user when he asks about it later").
> When the PO asks about any row, interview then. Severity: 🔴 blocks correctness · 🟡 worth a ruling · 🟢 FYI.

## Run configuration (PO directives applied)
- **Workflow:** ultracode — implement directly in main agent, minimal subagent spawns.
- **Reviewer/validator reduction:** single consolidated `code-reviewer` pass at the end (not per-phase); fixers merged (one fix pass folding all findings) instead of one-subagent-per-finding.
- **e2e/example phases (9/10):** lean on committed caches/fixtures + fixture-replay for token economy; correctness/cleanup/consistency/plan-coverage/DRY bars still enforced by the final reviewer.
- **No interview:** all `AskUserQuestion`-worthy forks resolved by the plan's already-recorded PO rulings; anything genuinely undecided is logged below rather than asked.

## Environment notes
- 🟢 Test baseline required two global git settings to go green in this container:
  `commit.gpgsign=false` / `tag.gpgsign=false` (container enforces a signing server that returns 400)
  and `user.name`/`user.email`. Without them 31 git-dependent tests (check_fence, memory_gap, reflect_scan)
  error at `git commit`. These are env-only, not code issues.

## Baseline anchor (regression gate — plan.md:40)
- product-spec **552** · product-spec-critique **150** · claude-pack **134** = **836** collected+passing cases.
- Rule for every phase: collected-passing count must not drop below the per-skill baseline (additive only).

## Post-plan TODO (PO-requested 2026-06-03)
- [ ] **Update `BACKLOG.md`** after plan completes: mark the done C/D/E items (E5, D12, E1, C9, E4, E2, D11, C11) as shipped; note C10/E3 remain parked/deferred.

## Phase status (this run)
| Phase | Item | Status |
|-------|------|--------|
| 1 | E5 per-skill release identity | ✅ done (verifier + 2 CHANGELOGs + CI gate step) |
| 2 | D12 cross-skill CI gate | ✅ done (3 workflows, bug_class in 3 configs, offline guard) |
| 3 | E1 apply-critique loop | ✅ done (parse/progress scripts, atomic DEC, injection-safe, gate, workflow ref) |
| 4 | C9 audit-trail view | ✅ done (assembler, `--viz audit` ascii+md, unreconciled rows) |
| 5 | E4 stakeholder brief | ✅ done (`--summary --audience`, release-notes template, delta helper) |
| 6 | E2 discovery seed | ✅ done (`--discover` ingest, fence/filter/bounded-recursion, workflow ref) |
| 7 | D11 _hashable consolidation | ✅ done (`render_common.py`, output unchanged) |
| 8 | C11 assumption-rigor + goal_without_metric | ✅ done (lens prompts + check + fixtures + eval) |
| 9 | 9a E2E | ⚠️ **partial** — see deferral D1 below |
| 10 | 9b docs sweep + changelog | ⚠️ **partial** — see deferral D2 below |

## Open decisions / deferrals (interview later)

- 🟡 **D1 — Phase 9 LLM-driven critique regeneration deferred.** The deterministic Phase-9 contracts ARE
  done: caches scrubbed (timestamps→canonical, no abs-path/web-cache leak), the committed
  `/e2e/dating-app/` run is locked as Phase-3's E1 freshness fixture with a **desync-guard +
  fixture-replay** test (`test_e2e_freshness_fixture_guard.py`, 4 tests), and the lv7-9 acme harm-floor
  safety fixtures + `test_voice_examples_grounding.py` were left **untouched + green**. What is NOT done:
  actually *driving the real critique LLM pipeline* to (a) regenerate dating-app reports through the new
  flows + full inherit/rollup/cache-hit-miss lifecycle and (b) produce the new **level-5 acme showcase**.
  That needs the critique sub-agent fleet (lens agents + opus consolidator + voice) — an interactive LLM
  run, deliberately NOT spawned here per the "reduce agent spawn / use cache" directive. **Interview the
  PO** when they want the live regeneration; the contracts that keep the suite honest are already in place.
- 🟡 **D2 — Phase 10 GUIDE deep-sweep partial.** Every new surface was registered inline as built:
  `SKILL.md` (both skills), root `CLAUDE.md` pointer table, `references/*` (workflow-apply-critique,
  workflow-discover, visualization-spec, validation-rules-spec, workflow-validate), root `README.md`, and
  all **3 CHANGELOGs** populated. NOT done: the full prose walkthrough rewrite of the four ~750-line
  `GUIDE-EN.md`/`GUIDE-VI.md` PO guides + the **VI native-review pass** (CLAUDE.md bilingual rule). Left
  for a focused docs pass — **interview the PO** on depth/tone before the GUIDE rewrite. Changelog
  backfill of *historical* commits by subject-scope+`--follow` (H5) is also deferred with D1 (the new
  features are recorded under `[Unreleased]`; historical backfill is a separate git-archaeology task).
- 🟢 **D3 — `--format md` is audit-only.** Added `md` to `visualize.py` FORMATS but rejected for every
  non-audit view. If the PO later wants markdown for other views, that's a clean extension.
