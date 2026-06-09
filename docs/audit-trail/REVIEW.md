# REVIEW — per-cycle finding tracker

Status legend: `[ ]` open · `[x]` fixed (→ EVIDENCE entry) · `[~]` partial · `[N/A]` not a defect.

Format (one row per finding):

```
- [ ] <ID> · <CAT> · <SEV> · `file:line` — <symptom> → <fix sketch>
```

Each `[x]` row must have a matching `EVIDENCE.md` entry with runnable before/after.
No plan/finding-code refs (per `review-audit-self-decision.md`, rule 5). Size cap ≤300
lines — roll closed cycles into `## Archive`.

---

## Cycle 0 — 2026-06 (HA-adoption: observability + audit-trail + eval/CI hardening)

- [x] PSC-1 · CORRECTNESS · HIGH · `critique_inherit.py:59` — numbered-sibling findings false-merged → undercount → keep list numbers as content (see EVIDENCE).

### Red-team pass — 8 invariants attacked, each with a reproducible verdict

Each row is a real break attempt (command + observed state), not prose. All held → `[N/A]` (no defect); zero BROKEN, so no new EVIDENCE entries.

- [N/A] INV1 · telemetry∉tarball — planted populated sink + `evil-symlink.jsonl→CLAUDE.md`, ran `python -m pack`, `tar tzf` → only the test file matches "telemetry"; secret marker absent from extracted bundle; 402 members (non-vacuous).
- [N/A] INV2 · telemetry fail-open — `appendEvent` into a `chmod 500` dir AND a circular (non-serializable) record → neither throws (both swallowed); observed op unaffected.
- [N/A] INV3 · JSONL non-forgery — skill name `skillA"\n{"forged":…}\nskillB` → exactly 1 physical line / 1 parsed record / forged record absent (JSON.stringify-only path holds).
- [N/A] INV4 · ledger no-secret/no-plan-ref — grep for sk-/AKIA/PEM/ghp_/xox + `phase-NN`/`F\d`/`§` → only match is the README clause that *states* the rule (inside backticks), no real refs.
- [N/A] INV5 · eval no-false-green — exit-0-but-silent vs `stdout_contains:READY` → FAIL "missing READY"; unknown checker → hard FAIL; `_gating:llm_advisory` → SKIP(manual); gate exit 1. (Bonus: malformed assertion → loud KeyError FAIL, never silent pass.)
- [N/A] INV6 · version-gate no-false-state — `changelog_top_version` skips `[Unreleased]` + `2.0.0-rc1` → picks stable `1.4.0`; missing file → loud ChangelogError; only-Unreleased → loud error; drift test 2.3.0≠2.2.0 RED, real-tree gate green (8/8).
- [N/A] INV7 · Phase-05 litmus catchable — temporarily injected `repeat_count=3` into every `structural_findings` entry → litmus went RED ("repeat-count key leaked into a per-finding LENS input"); reverted → GREEN; no marker left in source.
- [N/A] INV8 · critique determinism — double `run_scan` on identical inputs + planted index → script-side deterministic surface (structural_findings/digest/ancestry/source_files/prior_reports/inherited/rollup) byte-identical.

## Cycle 1 — 2026-06 (release-skill rename + bundle restructure, BREAKING)

`cleanmatic:claude-pack` → `cleanmatic:release`; bundle `claude-pack-{v}.tar.gz` → `product-spec-{v}.tar.gz`;
tag `claude-pack-v*` → `product-spec-v*`; new `release.py` changelog-lifecycle engine.

### Red-team pass — release pipeline attacked, each with a reproducible verdict

All held → `[N/A]` (no defect); zero BROKEN.

- [N/A] REL-INV1 · refuse-empty-release — `lock_unreleased` on an empty `[Unreleased]` → `SystemExit "[Unreleased] is empty — nothing to release"` (unit `test_lock_unreleased_refuses_empty`).
- [N/A] REL-INV2 · refuse-duplicate-version — `release.py --release 1.4.0 --apply` (1.4.0 already locked) → `❌ [1.4.0] already exists in CHANGELOG.md`, no write.
- [N/A] REL-INV3 · push-needs-apply — `release.py --release 2.0.0 --push` (no `--apply`) → argparse `error: --push requires --apply`, exit 2 (never pushes a dry-run).
- [N/A] REL-INV4 · dry-run-no-write — full dry-run suite leaves `CHANGELOG.md` with 0 `## [2.0.0]` headings + manifest still `2.0.0` (no accidental write off the read-only/preview paths).
- [N/A] REL-INV5 · version-axis-no-drift — `release.py --release X --apply` writes the changelog lock AND the manifest version in one action; the A4 gate (`test_bundle_changelog_top_matches_manifest_version`) ties root `/CHANGELOG.md` top == manifest `version:` so the two axes cannot silently diverge.
- [N/A] REL-INV6 · REPO-path-correct — `release.py` `REPO=parents[4]` resolves to the dir holding `.claude/pack.manifest.yaml` + `CHANGELOG.md` (unit `test_repo_resolves_to_repo_root`); the plan's `parents[3]` guess was wrong and was rejected empirically.
- [N/A] REL-INV7 · telemetry∉tarball after rename — real `python -m pack` build of `product-spec-2.0.0.tar.gz`: `tar tzf | grep -i telemetry` matches only the test-file *name*; no `.claude/telemetry/` dir, no telemetry hooks; no `claude-pack` path anywhere in the bundle.
- [N/A] REL-INV8 · build-determinism after rename — two consecutive `python -m pack` builds → byte-identical sha256 (`90910ffe…`).
- [N/A] REL-INV9 · CI body-fail-closed — if the owner pushes a `product-spec-vX` tag WITHOUT first locking `[X]` in the changelog, `release.yml`'s `release.py --extract X` step raises (no `[X]` section) → the release step fails rather than publishing a release with a wrong/empty body (safe-fail, by design).

## Cycle 2 — 2026-06-09 (learning loop `--learn`: outcome register + viz + discover-back)

New `--learn` umbrella mode: `record_outcome.py` (Outcome Register `OUT-<n>`), `load_outcomes.py`,
`render_outcomes.py` (scorecard / insight-gap / outcome-trend / learning-map / learning), preferences
verdict floors, `assemble_audit_trail` outcomes source. Implementation review (Wave 1) + regression.

### Findings

- [x] PS-1 · CONSISTENCY · LOW · `assemble_audit_trail.py` (outcomes loop) — comment claimed the
  learning-map "filters these outcome rows back out"; it KEEPS them as the map's source nodes. Comment
  corrected (no behavior change). → EVIDENCE PS-1.
- [x] PS-2 · CLEANUP · LOW · `record_outcome.py` (254 exec) + `render_outcomes.py` (211 exec) over the
  200-LOC guideline — measured by EXECUTABLE lines (not docstring-inflated), so a real overage. Split
  along seams: pure verdict core → `outcome_verdict.py`; Phase-5 learning views → `render_learning.py`.
  Now record_outcome 207 · render_outcomes 147 · outcome_verdict 51 · render_learning 67. → EVIDENCE PS-2.
- [x] PS-3 · CORRECTNESS · LOW · `_num` accepted `inf`/`nan` as numeric → a ratio of inf/nan could reach
  `compute_verdict`. Fixed: `_num` rejects non-finite → None → routes to the Hybrid (PO-asserted) path.
  → EVIDENCE PS-3.
- [x] PS-4 · CLEANUP · LOW · `load_outcomes.py` caught bare `except Exception` for a broken `brd.md`.
  Narrowed to `except OutcomeError` (the only thing `load_goals` raises) so a genuine programming error
  surfaces instead of being swallowed. → EVIDENCE PS-4.

_Adversarial probes that held (verdict determinism/direction, hybrid gating, bad-floor rejection,
append-only, goal-schema-untouched, XSS-fail-closed, fence/heading injection, audit back-compat) are
covered by the test suite (`test_record_outcome.py`, `test_outcome_viz.py`) — they are NOT logged as
ledger rows (this ledger holds defects, not passing checks)._

### Wave 2 — regression sweep (cycle 1 of 3)

- [x] PS-5 · CORRECTNESS · MED · `preferences.py` `--set` float branch — a non-numeric/out-of-range
  float floor saved with exit 0, then broke the NEXT `--learn` run (delayed, disconnected failure).
  Now rejected at write time (exit 2, nothing written) + range-checked [0,1], mirroring the enum path.
  Regression-tested. → EVIDENCE PS-5.
- [x] PS-6 · CLEANUP · LOW · unused imports — `load_outcomes.py` (`Path`), `render_outcomes.py`
  (`Optional`), `assemble_audit_trail.py` (`yaml`, pre-existing), `preferences.py` (`contextlib`, no
  longer needed after PS-5). pyflakes clean. → EVIDENCE PS-6.
- [x] PS-8 · CONSISTENCY · LOW · `visualize.py` module docstring said "14 views / 3 formats / 9 graph
  views" — now 20 views / 4 formats; refreshed + lists the audit/outcome/learning view groups.
- [x] PS-9 · CONSISTENCY · NIT · `preferences.py` comments referenced `record_outcome._load_floors`
  (renamed + moved by PS-2) — updated to `outcome_verdict.load_floors`.
- [x] PS-7 · DRY · MED · `record_outcome.py` ↔ `decision_register.py` — `_RECORD_RE`, fence/heading
  injection escape, `_register_lock`, id-scan were byte-identical twins. Extracted to a shared
  `register_store.py` (RECORD_RE / escape_injection / register_lock / scan_record_ids); both registers
  import it, each keeps only its own specifics. Byte-identical behavior (pure de-dup). **decision_register
  (critical/old feature) retested + green.** → EVIDENCE PS-7.
- [x] PS-10 · CORRECTNESS · MINOR · `record_outcome.py` `--measured-on` accepted any string (exit 0) vs
  the typed-ISO-date spec → could sort/group wrong downstream. Now validated via `dt.date.fromisoformat`,
  rejects non-ISO (nothing written). Regression-tested. → EVIDENCE PS-10.
- [x] PS-11 · CLEANUP(test-gap) · LOW · `learning_map_ascii` (production-reachable) was untested + no
  dispatcher tests for the 5 learning views. Added a direct ascii test + a dispatcher test across all 5
  views/formats. → EVIDENCE PS-11.
- [x] PS-12 · CLEANUP(test-gap) · NIT · added a direct OUT-side note-injection test (fake `---` fence +
  `## OUT-` heading in a `--note` → neutralized; `parse_outcomes` returns only the real row, phantom not
  counted in id alloc). Cycle-3 NIT; closes the one gap in the shared `escape_injection` coverage.
- NITs accepted (not defects): `BACKLOG.md:17,19` "E3 deferred" sits in a dated 2026-06-03 PO-decision
  snapshot (append-only history; line 20 + the E3 entry carry the live "shipped" status);
  `SKILL.md:55` `--format` row omits the audit-only `md` (pre-existing, out of `--learn` scope).

**Wave 2 cycle 2 → DONE_WITH_CONCERNS** (found PS-5 MAJOR + PS-10/11, all fixed). **Cycle 3 → CLEAN**:
PS-7 refactor verified behavior-preserving (escape order/regexes, lock semantics, id-scan byte-identical
to the old inline copies); decision_register/apply-critique/audit all green; pyflakes clean; i18n
symmetric; docs current. Final suite: **656 passed**. No open defects.
