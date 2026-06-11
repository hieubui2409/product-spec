# EVIDENCE — fixes + proof

One entry per landed fix. Format (copy the block):

```
### <ID> · <CATEGORY> · <SEVERITY> · `file:line`
- **Root cause:** <one sentence — the invariant/race/contract that broke>
- **Before:** <command> → <observed bad state>
- **Fix:** <one sentence — what changed and why it holds>
- **After:** <command> → <observed good state>
- **Note:** <optional — DEC-<n> ref, residual risk, by-design caveat>
```

Rules: before/after are runnable commands (scrub secrets); no plan/finding-code refs
(explain the *why*, not the origin); ID per the README grammar. Size cap ≤200 lines —
roll the oldest cycle into `## Archive` when exceeded.

---

## Cycle 3 — 2026-06-11 (PO field-audit fixes)

### LIB-5 · CORRECTNESS · HIGH · `telemetry/scripts/lens_workflow_chains.py`
- **Root cause:** the declared-chains source lived in two `.claude/rules/*.md` routing docs that a
  context-flow optimization deleted; the lens read them by hardcoded path and silently returned `[]`
  when they vanished, while a test asserted ≥1 chain → a red test on the default branch.
- **Before:** `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/telemetry -q -k declared_chains`
  → `test_declared_chains_parsed_from_routing_docs FAILED` (`assert 0 >= 1`).
- **Fix:** moved declared chains into an on-demand, in-skill `data/skill-chains.yaml` (read only when the
  lens runs → zero always-on token cost); `declared_chains()` reads it and raises `FileNotFoundError`
  when missing — and `ValueError` on malformed data (non-list `chains`, a string/scalar entry, a null
  step) — instead of silently returning `[]` or char-splitting a string into a fake chain. The SKILL.md
  source-cell label grew +2 tokens; the committed footprint baseline was regenerated in the same change.
- **After:** `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q`
  → `202 passed` (was `1 failed`); new tests `test_declared_chains_loaded_from_data_file`,
  `test_declared_chains_raises_when_data_file_missing`, `..._null_key_is_empty_not_crash`,
  `..._raises_on_malformed_data` all green.
- **Note:** the `data/` dir ships with the skill via the recursive `skills:` walk — no manifest edit.

### LIB-6 · CONSISTENCY · HIGH · `.github/workflows/`
- **Root cause:** 26 tracked test files (telemetry 18, hooks 4, _shared 4) had no workflow;
  `product-spec-ci.yml` path filter omitted `_shared/**` though its eval gate runs
  `_shared/lib/run_evals.py`; CONTRIBUTING's "all tests must pass" was unenforced — LIB-5 was exhibit A.
- **Before:** `grep -l telemetry .github/workflows/*.yml` → no workflow ran the telemetry/hooks/_shared suite.
- **Fix:** added `.github/workflows/internal-test-suite.yml` running the exact CONTRIBUTING.md command on
  telemetry+hooks+_shared; added `_shared/**` to `product-spec-ci.yml` paths; added a guard test asserting
  the workflow and CONTRIBUTING document the same canonical pytest targets.
- **After:** the `_shared` leg of the suite now includes `test_internal_ci_runs_canonical_suite.py`
  (3 tests) → `202 passed`, `0 failed`.
- **Note:** drift guard is a path-presence + co-presence check (workflow ⇄ CONTRIBUTING share the same
  pytest targets); it intentionally does not lock the interpreter, since CI runs system `python` while
  CONTRIBUTING documents the venv path.

## Archive

### Cycle 0 — 2026-06 (condensed; full before/after rolled off per the size cap)
- PSC-1 · CORRECTNESS · HIGH · `product-spec-critique/scripts/critique_inherit.py:59` — fingerprint
  normalizer stripped leading list numbers, merging distinct numbered-sibling findings → undercount.
  Fix: `_MARKER_RE` keeps list numbers as content. (`test_critique_inherit.py`)
- LIB-1 · CORRECTNESS · MED · `_shared/lib/run_evals.py:245` — `--root` default walked `parents[3]`
  (→ `.claude/`, not repo root) → every scenario FATAL'd. Fix: `parents[4]`.
- LIB-2 · CORRECTNESS · MED · `_shared/lib/llm_eval.py` — 35 `llm_advisory` assertions had no runnable
  path (always SKIP). Fix: golden-fixture judge via injectable LLM client (PASS/FAIL/MISSING/ERROR,
  never fabricates); local-on-demand, not CI. (`test_llm_eval.py`, 16 passed)

## Cycle 1 — 2026-06 (release-skill rename + bundle restructure)

### PACK-2 · CORRECTNESS · HIGH · `.claude/skills/release/scripts/release.py:26`
- **Root cause:** the new release-lifecycle engine resolves the repo root by parent-walking from its own path;
  the migration plan *guessed* `REPO=parents[3]`, which would land on `.claude/` (not the repo root) and make
  every `--release/--extract` read/write the WRONG `CHANGELOG.md` + `pack.manifest.yaml` — a release cut against
  a non-file, or worse a silent write to a stray path.
- **Before:** plan text "verify `REPO = parents[?]` — expected `parents[3]`" — unverified assumption.
- **Fix:** `REPO = Path(__file__).resolve().parents[4]` (scripts → release → skills → .claude → repo), matching
  the file's real nesting (identical depth to human-analyzer's `_framework-shared/release.py`). Locked by a unit
  test that asserts `REPO/.claude/pack.manifest.yaml` and `REPO/CHANGELOG.md` both exist.
- **After:**
  ```
  $ .claude/skills/.venv/bin/python3 -m pytest .claude/skills/release/scripts/tests/test_release.py -q
  ....................                                                      [100%]
  $ .claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --out /tmp/relbuild --json \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['output_path'])"
  /home/.../dist/.../product-spec-2.0.0.tar.gz   # build twice → identical sha256 90910ffe…
  ```
- **Note:** empirical-over-assumption (`review-audit-self-decision.md` rule 4): the plan's `parents[3]` guess was
  rejected by running the resolution, not by trusting the plan. Bundle-A4 (`root /CHANGELOG.md top == manifest`)
  stays RED until the owner-time `release.py --release 2.0.0 --apply` locks the `[Unreleased]` → `[2.0.0]` section.

## Cycle 2 — 2026-06-09 (learning loop `--learn`)

### PS-1 · CONSISTENCY · LOW · `.claude/skills/product-spec/scripts/assemble_audit_trail.py` (outcomes loop)
- **Root cause:** the outcomes-source loop's comment asserted the learning-map "filters these outcome rows back
  out" — but `render_outcomes._learning_edges` KEEPS rows whose `action` starts with `"outcome:"` (they are the
  map's source nodes). A future maintainer trusting the comment would look for a non-existent filter.
- **Before:** `# … The learning-map view filters these outcome rows back out.`
- **Fix:** reworded to state the truth — the learning-map consumes the outcome rows as its source nodes (keeps,
  not filters). Comment-only; no code path changed.
- **After:**
  ```
  $ cd .claude/skills/product-spec && ../../../.claude/skills/.venv/bin/python3 -m pytest scripts/tests/ -q
  ... 649 passed ...
  ```
- **Note:** no DEC (a doc-accuracy fix, no contradiction with an approved artifact).

### PS-2 · CLEANUP · LOW · `.claude/skills/product-spec/scripts/{record_outcome,render_outcomes}.py`
- **Root cause:** measured by EXECUTABLE lines (not docstrings), `record_outcome.py` was 254 and
  `render_outcomes.py` 211 — both over the 200-LOC guideline, each fusing two concerns.
- **Fix:** extracted the pure verdict core (`_num`/`compute_verdict`/`load_floors`/`load_goals`/enums)
  → `outcome_verdict.py` (re-exported from `record_outcome`, callers unbroken; also fixes `load_outcomes`
  reaching into `record_outcome` for `_num`); Phase-5 learning views → `render_learning.py`.
- **After:** `record_outcome 207 · render_outcomes 147 · outcome_verdict 51 · render_learning 67`;
  `pytest scripts/tests/ -q` → 649 passed.
- **Note:** `record_outcome` stays ~7 over (writer + argparse CLI, one irreducible concern).

### PS-3 · CORRECTNESS · LOW · `.claude/skills/product-spec/scripts/outcome_verdict.py` `_num`
- **Root cause:** `float("inf")` / `float("nan")` parse without error, so `_num` returned a non-finite
  number; an `actual`/`target` of `inf`/`nan` would have flowed into `compute_verdict` and produced a
  nonsense ratio instead of being treated as un-computable.
- **Before:** `_num("inf") → inf` (then `compute_verdict` divides with inf).
- **Fix:** `_num` returns the value only when `math.isfinite(n)`, else `None` — a non-finite token now
  routes to the Hybrid path (a PO-asserted `--verdict` is required), same as any other non-numeric input.
- **After:**
  ```
  $ python3 -c "from outcome_verdict import _num; print(_num('inf'), _num('nan'), _num('1.5'))"
  None None 1.5
  ```
- **Note:** absurd input, but now fails safe (asks the PO) rather than emitting a junk verdict.

### PS-4 · CLEANUP · LOW · `.claude/skills/product-spec/scripts/load_outcomes.py`
- **Root cause:** a bare `except Exception` around `load_goals(root)` (to tolerate a missing/broken
  `brd.md`) also swallowed any programming error inside the loader — a silent-failure hazard.
- **Before:** `except Exception:  # noqa: BLE001` → goals = {} on ANY exception.
- **Fix:** narrowed to `except OutcomeError` — the only exception `load_goals` raises for a
  missing/unparseable BRD. A genuine bug (e.g. an AttributeError) now propagates instead of degrading to
  "no goals".
- **After:**
  ```
  $ .claude/skills/.venv/bin/python3 -m pytest scripts/tests/test_outcome_viz.py -q   #  20 passed
  ```
- **Note:** behavior unchanged for the intended case (broken brd.md → orphan-only render); only genuine
  errors are now surfaced.

### PS-5 · CORRECTNESS · MED · `.claude/skills/product-spec/scripts/preferences.py` (`--set` float branch)
- **Root cause:** the float-key branch swallowed a bad value (`contextlib.suppress(ValueError)`), so
  `--set outcome_hit_floor=notanumber` saved + exited 0; the failure surfaced only on the NEXT `--learn`
  (in a different module), pointing at a file the PO was told "saved" — unlike every enum key, which
  rejects at write time.
- **Before:** `$ preferences.py --set outcome_hit_floor=notanumber` → `saved preferences →` exit 0.
- **Fix:** reject non-numeric (and out-of-`[0,1]`) at write time, exit 2, nothing written — mirroring
  the enum/unknown-key paths. `contextlib` import dropped (its only use).
- **After:**
  ```
  $ preferences.py --set outcome_hit_floor=notanumber   # exit 2, "must be a number"
  $ preferences.py --set outcome_hit_floor=1.5           # exit 2, "must be in [0,1]"
  $ preferences.py --set outcome_hit_floor=0.95          # exit 0, persists as float 0.95
  $ .claude/skills/.venv/bin/python3 -m pytest scripts/tests/test_preferences.py -q   # passed (+3 new)
  ```

### PS-6/8/9 · CLEANUP+CONSISTENCY · LOW · product-spec scripts (regression-sweep tidy)
- **Fix:** removed unused imports (`load_outcomes` `Path`, `render_outcomes` `Optional`,
  `assemble_audit_trail` `yaml` [pre-existing]); refreshed the stale `visualize.py` module docstring
  (14→20 views, 3→4 formats, +audit/outcome/learning groups); corrected `preferences.py` comments that
  named the renamed `record_outcome._load_floors` → `outcome_verdict.load_floors`.
- **After:** `$ python3 -m pyflakes scripts/*.py` → clean; `pytest scripts/tests/ -q` → 652 passed.

### PS-7 · DRY · MED · `record_outcome.py` ↔ `decision_register.py` (shared register store)
- **Root cause:** the two append-only fenced-record registers reimplemented the same machinery in
  lockstep — `_RECORD_RE`, the fence/heading injection escape, `_register_lock`, and the raw id scan were
  byte-identical twins, so a fix had to land in both.
- **Fix:** extracted the shared primitives into `register_store.py` (`RECORD_RE`, `escape_injection`,
  `register_lock`, `scan_record_ids`). Both registers now import them; each keeps only its own specifics
  (id grammar, heading anchor, field schema, supersede-vs-verdict, atomic-vs-plain write). Behavior is
  byte-identical — same regex object, same lock semantics, same escape — so it is a pure de-dup.
- **After (old feature retested — `decision_register` is critical + heavily used):**
  ```
  $ pytest scripts/tests/test_decision_register.py test_record_outcome.py \
      test_audit_trail.py test_apply_critique.py -q   # all passed
  $ pytest scripts/tests/ -q                          # full suite passed
  $ python3 -m pyflakes scripts/*.py                  # clean (also dropped a pre-existing unused `os`)
  ```
- **Note:** the `[~]` deferral in the Cycle-1 sweep was reversed on PO instruction ("fix all deferred,
  retest old features") — done + retested, no behavior change.

### PS-10 · CORRECTNESS · MINOR · `record_outcome.py` `append_alloc` (`--measured-on`)
- **Root cause:** `--measured-on` accepted any string (exit 0); the field is a typed ISO 8601 date
  (frontmatter-and-id-spec), and a non-date would sort/group wrong in trend columns / latest tiebreak.
- **Fix:** validate with `dt.date.fromisoformat` → `OutcomeError` on failure (nothing written), mirroring
  the goal/metric ref validation already in that function.
- **After:** `record_outcome.py --measured-on not-a-date` → exit non-zero, no write; a valid ISO date
  records. (`test_non_iso_measured_on_rejected`)

### PS-11 · CLEANUP(test-gap) · LOW · learning views test coverage
- **Fix:** added a direct test for `render_learning.learning_map_ascii` (empty + populated) and a
  dispatcher-level test driving all 5 `--learn` views through `visualize.py` (scorecard/insight-gap/
  outcome-trend ascii; learning-map ascii+mermaid; learning-map `--format md` rejected; learning HTML-only
  note). Closes the gap Cycle 2 flagged (production-reachable ASCII downgrade was untested).
- **After:** `pytest scripts/tests/test_outcome_viz.py -q` → passed (new dispatcher + ascii tests green).
