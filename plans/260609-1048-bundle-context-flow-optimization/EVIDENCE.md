# EVIDENCE — Bundle context/flow optimization

Honest, reproducible proof trail for the measure-first SKILL.md flag-table compaction.
The NON-NEGOTIABLE: no edit reduces reasoning effectiveness. Two proofs per change —
**(a)** harness shows SKILL.md tokens dropped + GATE co-presence green; **(b)** STRUCTURE
held (pytest) AND REASONING held (sub-agent best-of-3 routing judge before vs after).

## Phase 0 — verified green baseline (venv interpreter, NOT through the rtk hook)

- `product-spec`: **658 passed** (the plan's structural baseline).
- `product-spec-critique`: **172 passed**.
- `release`: **4 failed** — PRE-EXISTING, OUT OF SCOPE. `pack.manifest.yaml` still lists three
  rules files the uncommitted sibling refactor deleted (`team-coordination-rules.md`,
  `skill-domain-routing.md`, `skill-workflow-routing.md`). Not caused by this plan; this plan
  touches only product-spec/critique SKILL.md + the new harness + evals. Flagged, not fixed.

## Phase 1 — harness + co-presence baseline (BEFORE numbers)

`context_footprint.py --baseline` over all 4 skills, `--always-on` = root `CLAUDE.md`.
Token proxy = `ceil(chars/4)` — approximate, relative-only (PO set no hard %).

| Skill | SKILL.md tokens (before) | total tokens (before) |
|-------|--------------------------|------------------------|
| product-spec | **6090** | 61899 |
| product-spec-critique | **3820** | 20687 |
| release | 2863 | 11996 |
| telemetry | 2205 | 3076 |

- **Co-presence check: GREEN** (exit 0) — every `GATE-*` referenced across SKILL.md/refs has a
  reachable full-prose home (always-on root `CLAUDE.md`, or full-prose in the skill itself).
- Baseline JSON committed at `.claude/skills/_shared/lib/context_footprint_baseline.json`.
- Harness tests: 14 pass (token proxy, baseline/compare/gate, co-presence pass+fail incl. the
  colon-form `GATE:X` pointer + orphan + single-char/mid-word/trailing-dash name edge cases, malformed).

## Phase 2 — routing-selection eval scenarios (the reasoning gate)

Authored `llm_advisory` ROUTING-SELECTION scenarios — ambiguous PO asks that name NO flag; the
assertion judges the router picks the right flag/mode + loads the right ref. These are SKIP in
the deterministic `run_evals` gate (judged by the sub-agent, never mechanically).

- product-spec: **16** routing scenarios (`route-viz`, `route-learn`, `route-set-pref`,
  `route-apply-critique`, `route-discover`, `route-layers`, `route-format`, `route-reflect`,
  `route-summary`, `route-decision`, `route-voice`, `route-compact`, `route-lang`,
  `route-export`, `route-filter-wont`, `route-status`) — one per compacted flag.
- critique: **2** routing scenarios (`route-level`, `route-scope`).
- `run_evals --skill product-spec` → 0 fail (30 skip manual); critique → 0 fail (25 skip manual).
- pytest re-run after authoring: product-spec **658**, critique **172** (no structural regression).

### Sub-agent reasoning-proof recipe (PO-resolved: sub-agent, NO API key, best-of-3)

For each Phase-3 compaction, the reasoning proof (b) is run by spawning **3 independent
sub-agents** (each a Claude instance = the LLM judge). Each judge is given, per scenario:
the ambiguous prompt, BOTH the BEFORE and AFTER `SKILL.md` flag tables (and the relevant
on-demand reference list), and the rubric below. Majority of 3 wins; **a tie or a majority
"after worse" → fail-safe = revert that commit.**

Judge rubric (per routing scenario, yes/no):
1. **BEFORE-routes:** would the verbose SKILL.md route this ambiguous ask to the expected flag/mode? (baseline must be green; a BEFORE=no is a SCENARIO bug, fix the scenario not the skill)
2. **AFTER-routes:** does the compacted SKILL.md still route it to the same expected flag/mode?
3. **GATE-intact:** if the flag carries a safety GATE keyword, is that keyword still present in the compacted row?
4. **Verdict:** `HELD` (AFTER-routes ∧ GATE-intact) or `REGRESSED`.

A scenario is `REGRESSED` iff majority of 3 judges say REGRESSED. Any REGRESSED scenario →
revert the discriminating detail for that flag (restore enough "when to use" to route).

## Phase 3 — compaction results (per skill)

Compacted to one `what · when · GATE · see <ref>` line each:
- product-spec: 16 verbose flags. Terse flags + no-flag menu + always-on lines untouched.
- critique: `--level 1..9` + `[scope]`. Every safety fact kept inline in `--level` (6-9 danger
  gate, level-9 re-confirm-every-run + downgrade-to-8, universal-harm floor at all levels).
- 3 new refs created (`workflow-summary.md`/`workflow-decision.md`/`workflow-lang.md`) + wired into
  the on-demand reference section; all compacted ref-pointers reconciled (no dangling pointer).

**Proof (a) — harness:**
| Skill | SKILL.md before → after | Δ | total Δ |
|-------|-------------------------|---|---------|
| product-spec | 6090 → 5371 | **−719 (−11.8%)** | +339 (3 intentional new refs, lazy-loaded) |
| product-spec-critique | 3820 → 3677 | **−143 (−3.7%)** | −143 |

Co-presence check: **GREEN** (no orphaned GATE pointer).

**Proof (b) — structure + reasoning:**
- pytest: product-spec **658**, critique **172** (structure held).
- Best-of-3 sub-agent routing judge (3 independent judges, majority): **18/18 HELD, 0 REGRESSED,
  unanimous.** No revert needed. Judge brief: `reasoning-judge-brief.md`.

## Phase 4 — final deltas + gates

- Baseline JSON refreshed to the post-optimization state
  (`.claude/skills/_shared/lib/context_footprint_baseline.json`).
- **Regression guard wired into the pytest check surface:**
  `_shared/lib/__tests__/test_context_footprint_regression_guard.py` — measures the live bundle,
  asserts no SKILL.md/total growth vs the committed baseline + co-presence green (40 shared-lib
  tests pass). Manual equivalent: `context_footprint.py --compare <baseline> --gate`.
- **Version handling (deviation from the plan's literal "bump", grounded in repo evidence):**
  product-spec `2.3.0` is **untagged/unreleased** (latest tag `product-spec-v2.2.2`); a 2.3.1 bump
  on top of an unreleased 2.3.0 would be semver-wrong, and the bundle's `release` skill owns the
  version lock. So the optimization is recorded under **`[Unreleased]`** in both CHANGELOGs;
  SKILL.md versions stay synced (`verify_skill_versions.py` OK; `test_version_sync` 10/10). The
  `release` skill locks `[Unreleased]` → the next version at release time.
- BACKLOG: round noted (cross-refs the brainstorm).
- **Final double-gate (all green):** harness SKILL.md reduction confirmed · co-presence green ·
  pytest 658 (product-spec) + 172 (critique) + 37 (shared-lib) · run_evals 0-fail · version-sync 10/10.

### Commit hygiene (resolved/accepted)
This plan's changes form a cohesive, independently-revertable set, fully enumerated above (new
harness + tests + baseline, the compacted SKILL.md rows, 3 new refs, the `route-*` evals, CHANGELOG
`[Unreleased]`, BACKLOG note). The working tree co-mingles the **sibling** `--learn` plan
(`260609-0847`, already DONE) inside the shared `SKILL.md`/`eval/evals.json` — this is **pre-existing
in the inherited working tree, not introduced by this plan**, and cannot be split by file-level
staging. The round is committed as one logical unit at the user-owned finalize step; surgical revert
of the optimization is available via the enumerated file set + this EVIDENCE. No code/coverage/DRY/
regression concern remains.

### Sibling `release` failures — FIXED (later authorized by PO)
The 4 pre-existing `release` failures were fixed on PO request:
- 3× `MANIFEST_E072 missing rules` → removed the 3 stale entries (`team-coordination-rules.md`,
  `skill-domain-routing.md`, `skill-workflow-routing.md`) from `.claude/pack.manifest.yaml` (the
  files were intentionally deleted by the rules-slim refactor; the manifest hadn't caught up).
- 1× `No module named pack` in `test_pack_cli_full_run` → added the missing `cwd=<scripts dir>` to
  the `python -m pack` subprocess (the other release tests already set it; this one omitted it).
- `release` suite now **198 passed, 19 skipped, 0 failed.**
