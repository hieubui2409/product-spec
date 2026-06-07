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
