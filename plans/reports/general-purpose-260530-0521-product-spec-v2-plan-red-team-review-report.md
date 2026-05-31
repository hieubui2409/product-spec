# Red-Team Review — product-spec v2.0.0 Plan (pre-implementation)

**Date:** 2026-05-30  
**Scope:** Plans/phases 01–07 + goal.md + design report §0 (AUTHORITATIVE)  
**Mode:** Adversarial. Attack the PLAN, not the code (no code exists yet).  
**Verdict:** **FIX-FIRST** — 3 HIGH findings that violate stated deal-breakers; rest are MED/LOW.

---

## Findings (prioritized)

---

### F1 — `risk_blindspot` violates G-B1 (Script-vs-LLM split deal-breaker)

**Severity: HIGH**  
**Location:** `goal.md:G-C4`, `phase-02-risk-hardening.md:Requirements`, design report §9

**Issue:** `risk_blindspot` (≥5 child stories, 0 risks) is classified as an LLM check. But counting child stories = graph traversal, and checking if `risks == []` = field presence check. Both are deterministic and closed-form — by the explicit G-B1 definition, "anything answerable by walking edges or counting items, it's script." There is zero LLM judgment involved. Leaving it in the LLM layer introduces non-determinism and defeats the entire split.

**Concrete fix:** Move `risk_blindspot` to the Script layer. Add `_check_risk_blindspot()` to `check_consistency.py` (it already has `matching_child_counts`). Remove it from the LLM prompt catalog. Update goal.md `G-C4` verify method accordingly. No behavioral change — it was always a count threshold.

---

### F2 — `dep_dangling` assigned to wrong script, contradicts existing convention

**Severity: HIGH**  
**Location:** `phase-03-time-and-dependencies.md:Architecture step 3b` ("add `_dep_dangling()` in `check_consistency.py`")

**Issue:** All existing `dangling_link` findings for epic/prd/brd_goals live in `check_traceability.py` (lines 42, 47, 64). The plan routes the new `dep_dangling` (dangling `depends_on` reference) to `check_consistency.py` instead. This splits the dangling-ref family across two scripts, violating the implicit naming convention and making it harder for the orchestrator's merge-findings step to give coherent ordering. It also makes cross-phase review miss the inconsistency until implementation.

**Concrete fix:** Move `_dep_dangling()` (and its call-site) to `check_traceability.py`, alongside the existing `dangling_link` checks. Update phase-03 "Related Code Files" accordingly.

---

### F3 — `time_realism` eval has no specified pinning mechanism — non-deterministic gate

**Severity: HIGH**  
**Location:** `phase-03-time-and-dependencies.md:Risk Assessment` ("evals pin `today_date`"), `goal.md:G-D6`

**Issue:** The plan acknowledges that `time_realism` consumes `today` and says "evals pin `today_date`." But nowhere in phase-03 (nor in the eval sketch at design report §8) is there a concrete mechanism to inject a fixed `today` into the `time_realism` script path. `time_advisory.py` takes `--today <ISO>` explicitly — correct. But `time_realism` is part of the validation flow, not `time_advisory.py`. The script pre-computes `days_remaining = (target_date - today).days` using `datetime.now()` unless overridden. Without a `--today` override flag on the validation-path script, the eval fixture's `days_remaining` will drift as calendar advances and flip from true-positive to false-negative. G-D6 verify will become an unreliable gate.

**Concrete fix:** Add a `--today <ISO>` override parameter to the script/module that computes `time_realism` anchors (same pattern as `time_advisory.py`). Eval fixtures must pass this flag. Document the override in the eval sketch. Phase-03 step 7 must include this.

---

### F4 — `find_dep_cycles` uses recursive DFS — Python stack overflow on large specs

**Severity: MED**  
**Location:** `phase-03-time-and-dependencies.md:Architecture → find_dep_cycles` (the quoted implementation)

**Issue:** The plan's canonical `find_dep_cycles` implementation is recursive. Python's default recursion limit is 1000. A depends_on chain of 950+ PRDs/epics would raise `RecursionError` before detecting any cycle. Verified: a 1000-node chain raises `RecursionError` with the exact code from the plan. Specs with many PRDs (imported from Jira, for example) are in scope.

**Concrete fix:** Replace the recursive DFS with an iterative 3-color Kahn/DFS. The same algorithm is expressible iteratively with an explicit stack, which the plan already uses in the renderer cycle-safety guard (`seen, stack = set(), [root]`). Consistency win: iterative + visited-set is the pattern the renderer guard uses.

---

### F5 — Orchestrator per-phase fix-loop allows commit with red tests after 2 retries

**Severity: MED**  
**Location:** `phase-01-workflow-orchestration-harness.md:Canonical orchestrator`, fix-loop lines 121–131

**Issue:** After `tries < 2` is exhausted, the outer `for` loop falls through to the `checkpoint` agent invocation regardless of `impl.tests_green`. The checkpoint agent's prompt says "run pytest (must be green) then git add" but there is no schema enforcement (`IMPLEMENT` or similar with required `tests_green: true`) that stops it from committing. An agent under instruction to commit may do so anyway, producing red-state commits that break G-A1/G-H5 and are hard to roll back mid-orchestration.

**Concrete fix:** Add a structural guard before checkpoint: if `tries >= 2 AND !impl.tests_green`, log a human-escalation message and `break` the outer phase loop (or set a `hardBlocked` flag and skip `checkpoint`). The `SHIP` schema at the end can then surface this as a blocker. This avoids silent bad commits.

Additionally: the re-review schema assignment (`pr.verdict = re.verdict; cpr.verdict = re.verdict`) conflates the two reviews into one. A re-run that fixes cross-phase but not phase-review produces a false `pass`. Separate the two re-verdict assignments or use `re.verdict_phase` / `re.verdict_xphase`.

---

### F6 — `competitive_parity` cross-artifact `unknown_ref` check has no specified graph key

**Severity: MED**  
**Location:** `phase-04-competition.md:Architecture`, `check_consistency.py` extension

**Issue:** Phase-04 says `check_consistency` validates that each `competitive_parity` key resolves to a BRD `competitors[].id`. But `check_consistency` operates on graph nodes, and BRD competitor IDs are NOT graph nodes (they're nested dicts inside `brd.md`). For the `unknown_ref` check to work, `spec_graph` must expose a top-level graph key holding the set of valid COMP-IDs (analogous to how `graph['risks']` exists at graph level). Phase-04 says `spec_graph` "exposes competitors" but never names the graph key. Without a named contract, the implementer may re-parse the BRD artifact in-line inside `check_consistency`, duplicating parsing logic and violating DRY.

**Concrete fix:** Explicitly state in phase-04 architecture that `spec_graph` exposes `graph['competitors']` as a list of `{id, name, threat}` dicts (mirroring `graph['risks']`), and that `check_consistency` reads `{c['id'] for c in graph.get('competitors', [])}` to build the valid COMP-ID set.

---

### F7 — `invalid_shape` check ID conflicts with existing `invalid_type` — DRY violation

**Severity: MED**  
**Location:** `phase-02-risk-hardening.md:Implementation Steps step 4`, `validation-rules-spec.md`

**Issue:** Phase-02 introduces `invalid_shape` as a new check ID for a risk entry that is "not a dict / missing `description`." But the existing codebase already uses `invalid_type` (in `check_consistency.py:110` and `check_traceability.py:57`) for "field has wrong YAML type." Both check IDs represent the same class of violation: a field that has the wrong structural type. A second check ID for the same concept fragments the human report and consumer tooling.

**Concrete fix:** Reuse `invalid_type` for the risk-shape check (extend the existing helper or add a parallel call). If the distinction matters — "wrong scalar type" vs "wrong dict structure" — document it explicitly in `validation-rules-spec.md` and name it `invalid_shape` there with a note that it is a structural sub-variant. Currently `invalid_shape` does not exist in the catalog, and phase-07 (G-H3) would need to add it — easy to miss.

---

### F8 — G-A1 verify scope under-specifies test files — gate is blind to new suites

**Severity: MED**  
**Location:** `goal.md:G-A1`

**Issue:** G-A1 verify says "pytest `test_check_traceability` `test_check_consistency` green." Phases 2–5 add four new test files (`test_risk_complete.py`, `test_dep_cycle.py`, `test_competition.py`, `test_migration.py`). A multi-wave gate verifier agent that interprets G-A1 literally runs only the two named files and can declare G-A1 PASS while new tests are red. G-H5 (full pytest) does cover this, but G-A1 is the traceability-integrity gate and it should self-sufficiently cover its own domain.

**Concrete fix:** Update G-A1 verify to: "full `pytest` green (all test files including `test_risk_complete`, `test_dep_cycle`, `test_competition`, `test_migration`)." Or simplify to "full pytest suite green" and reserve the file-specific names for documentation.

---

### F9 — Phase-03 missing `--summary` time line (Q35 partially dropped)

**Severity: MED**  
**Location:** `phase-03-time-and-dependencies.md:Architecture step 3d`, `goal.md:G-G1` coverage

**Issue:** Design report Q35 says "`--summary` gains time + competition." Phase-04 explicitly adds the competition line. Phase-03 does NOT include a `--summary` time-dimension update in its architecture or implementation steps. The time line (next target dates, depends_on summary) is simply absent from the plan. G-H3 says "references updated" but does not call out `--summary` integration for time specifically.

**Concrete fix:** Add to phase-03 step 3d: "extend `--summary` generator with a time section (nearest upcoming `target_date` per PRD, any `dep_order` warnings count)." Add a corresponding test in `test_time_advisory.py` or a new `test_summary_time`.

---

### F10 — Text-summary tree format unspecified — TDD RED phase cannot write an exact-match test

**Severity: MED**  
**Location:** `phase-06-ascii-downgrade-to-html-native.md:Tests First`, `test_tree_text_summary_retained`

**Issue:** Phase-06 says TDD RED: rewrite `test_visualize.py` — "keep tree-text asserts; add text-summary asserts (fail initially)." But the text-summary tree format is not specified anywhere in the plan. The TDD contract requires writing the test FIRST, before implementation. Without knowing the exact output (counts, indentation style, separators), the test author cannot write an exact-text assertion. The test would have to be written as a vague "contains structure" check, which is not deterministic and violates G-A4.

**Concrete fix:** Add a concrete sample output spec to phase-06 (e.g., `"PRD-AUTH (epic: 2, story: 4) [2 risks, target: 2026-09]"` format). This spec becomes the basis for both the test and the implementation.

---

### F11 — SKILL.md output layout missing `docs/product/impact/` — G-H3 incomplete

**Severity: LOW**  
**Location:** `phase-07-docs-and-2-0-0-release.md:Architecture / Doc Surface`, `SKILL.md:Output Contract`

**Issue:** Phase-05 introduces `docs/product/impact/<ts>.md` as a new output location. SKILL.md's output contract layout table does not list this directory. Phase-07's doc surface table updates `SKILL.md` but doesn't explicitly call out adding `impact/` to the layout table. This is easy to omit and would leave the skill's declared output contract stale.

**Concrete fix:** Add "SKILL.md output layout → add `impact/` line" to phase-07 implementation step 3 or step 6.

---

### F12 — G-D3 timing assertion `< 1s` has no specified measurement mechanism

**Severity: LOW**  
**Location:** `goal.md:G-D3`, `phase-03-time-and-dependencies.md:Tests First row test_renderer_terminates_on_cycle`

**Issue:** G-D3 verify says "renderer-on-cyclic-graph terminates <1s." This is a timing assertion in pytest with no specified mechanism (no `pytest-timeout`, no `time.perf_counter`, no `@pytest.mark.timeout`). On loaded CI or slow machines, the assertion is inherently flaky. The plan lists this as a SUCCESS CRITERION but gives no concrete implementation.

**Concrete fix:** Specify the timing mechanism: e.g., `import time; t0 = time.perf_counter(); render(...); assert time.perf_counter() - t0 < 1.0, "cycle renderer hung"`. Or use `pytest-timeout` and document it as a test dependency. Either way, document the approach in phase-03 Tests First.

---

### F13 — `change-log` template already has `affected_set` — phase-05 overstates new work

**Severity: LOW**  
**Location:** `phase-05-impact-engine-and-migration.md:Architecture`, `assets/templates/change-log-entry.md`

**Issue:** Phase-05 says "extend change-log schema + writer (`affected_set` + `dims`)." But `change-log-entry.md` already has `{{affected_set}}` on line 12. Only `dims` is genuinely new. The phase-05 scope statement is slightly inflated and the test `test_changelog_schema` asserting `affected_set` presence will trivially pass against the current template. No blocker, but the test won't actually validate a NEW thing.

**Concrete fix:** Update phase-05 scope statement to "extend change-log schema + writer: add `dims` field (affected_set already present)." Scope the `test_changelog_schema` to assert `dims` is present (the genuinely new field).

---

## T1/T2 Trade-off Sufficiency

**T1 (`dep_cycle` / renderer hang):** The plan's mitigation is sound in spirit (DFS + visited-set guards). The single gap is F4 (recursive implementation will stack-overflow before detecting cycles in large specs). Switch to iterative DFS and T1 is fully mitigated.

**T2 (`time_realism` + `competitive_drift` hallucination):** The structured-anchor approach is solid — AND-logic, conservative default, required `cited_data`, script pre-computes numeric anchors. The `competitive_drift` anchor (scope=core-value, ≥2 competitors with data, all behind) is equally well-bounded. The only gap is F3: without a `--today` override, the `time_realism` eval is non-deterministic. Fix F3 and T2 is fully mitigated.

---

## Cross-Phase Consistency Check

- **`competitive_parity` schema:** Consistently ID-keyed map across report §5.1 and phases 04/05. No list-of-dict leak detected.
- **Renamed/stale fields:** No stale fields found across phases.
- **Check ownership split:**  Two violations — F1 (`risk_blindspot` in wrong layer) and F2 (`dep_dangling` in wrong script). Both fixable before implementation.
- **`dep_cycle` in `check_traceability.py`:** Correct (phase-03 Architecture step 3a). The `dep_dangling` split (F2) is the inconsistency, not `dep_cycle`.

---

## YAGNI / Scope Check

- No COST model, RICE/WSJF scoring detected. Clean.
- Dashboard HTML-only: scoped to one HTML page reusing Phase 2/4 builders. Not over-built.
- `--summary` competition line: Q35 explicitly requests this. Not gold-plating.
- `--summary` time line: MISSING (F9) — this is a scope gap, not gold-plating.
- `time_advisory.py --today`: separate script, out of gate, minimal surface. KISS.

---

## Goal.md Gate Coverage

Gate coverage check: **union of `PHASES[].gates` + `GLOBAL_GATES` == `goal.md` gate set — PASS.** No orphan gates, no dangling gate IDs in the orchestrator.

---

## Unresolved Questions

1. **Impact-pass on `--validate`: what is `changed_id`?** On `--update`, the changed node is explicit. On `--validate`, there is no inherent change. Does impact-pass run for every node (noisy), for a user-specified ID only, or is it skipped on pure `--validate`? Not specified in phase-05 or goal G-F1. This ambiguity will force an implementation decision at cook time without PO input.

2. **`_node_from_artifact` extension:** Phase-03 adds `depends_on` to ALL node types in the graph schema (including stories and BRD goals). This is an implicit graph schema change. Is this intentional? Any consumer that serializes/deserializes graph nodes will see a new field on all types. Not a blocker but worth confirming.

---

## Verdict

**FIX-FIRST.**

Fix F1 (split violation), F2 (dep_dangling owner), F3 (today override for time_realism eval) before cooking. These three directly violate G-B1 (deal-breaker) or will produce a non-deterministic gate that undermines the entire multi-wave review contract. The remaining 10 findings are MED/LOW and can be resolved within the phase red-team step of the orchestrator.
