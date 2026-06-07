# Hard Review — release skill rename + release-restructure (BREAKING)

**Scope:** uncommitted working-tree (`git mv claude-pack→release`, manifest 1.4.0→2.0.0, new `release.py` engine + tests, 3 CI workflow renames, root `/CHANGELOG.md` move, docs sweep).
**Verdict: SHIP-WITH-FIXES** — one MED CI-gating issue must be resolved before opening this as a PR (or the PR will fail two CI legs). All correctness invariants of `release.py`, build determinism, path-math, and touchpoint coverage pass.

---

## Verification matrix (acceptance criteria)

| AC | Result | Evidence |
|----|--------|----------|
| (a) no dangling functional `claude-pack` ref | PASS | grep across `.claude`/`.github` `*.yml/py/sh/ps1` (excl. plans, history, "renamed"): 0 hits. README/CLAUDE/BACKLOG/STANDARDIZE: only historical/"was claude-pack" phrasing. install-vendor-markdown.sh comment correctly reworded. |
| (b) path-math | PASS | `release.REPO==parents[4]==repo root` (has CHANGELOG + manifest); `verify_skill_versions parents[4]`✓; `test_version_sync parents[5]`✓; `DEFAULT_SKILLS`/`VERSION_SYNCED_SKILLS = (product-spec, product-spec-critique, release)`✓. |
| (c) deterministic `product-spec-2.0.0.tar.gz`, no telemetry/claude-pack, ships release.py | PASS | two clean builds → identical sha `9f07e3b0…`; sidecar `sha256sum -c` OK; 407 entries; `release/scripts/release.py` present (1); `claude-pack` paths 0; telemetry hooks 0. |
| (d) release.py invariants | PASS | unit tests (20/20) + empirical: dry-run writes nothing (manifest stays 2.0.0, no `[3.0.0]` heading leaked), `--extract` read-only + raises on missing, refuses empty `[Unreleased]`, refuses existing version, `--push` requires `--apply` (exit 2), commit/tag/push only when `--apply && --push`, tag prefix `product-spec-v`. |
| (e) CI new paths/filenames/tag glob, body_path, eval `--skill release` | PASS | `release.yml` tag glob `product-spec-v*.*.*`, version derive strips `product-spec-v`, `--extract <ver> > dist/RELEASE-BODY.md` + `body_path:`, files glob `product-spec-*.tar.gz`; `release-ci.yml` eval gate `run_evals.py --skill release` → 10 pass/0 fail; installers exist at new path; relative `$SCRIPT_DIR` resolution survives move. |
| (f) no regression to product-spec / product-spec-critique | PASS | those skills have 0 `claude-pack` refs (excl. history); their changes are unrelated eval/agent work; `verify_skill_versions` green for all 3 (2.2.0 / 1.2.0 / 1.0.0). |

Lock→extract round-trip on the **real** CHANGELOG: `lock_unreleased(text,"2.0.0",…)` then `extract_section(…,"2.0.0")` → 23-line body, fresh `[Unreleased]` empty. So at release time `release.py --release 2.0.0 --apply` (same commit it tags) produces a `[2.0.0]` section that the CI `--extract 2.0.0` will find. Flow is internally consistent.

---

## Findings

### MED-1 — New `test_bundle_changelog_top_matches_manifest_version` will FAIL PR CI on this changeset (two legs)
The known/expected failure (manifest 2.0.0 vs root CHANGELOG top 1.4.0, because `[Unreleased]` isn't locked until owner-time `release.py --apply`) is **confirmed to be the only reason** that test fails. BUT it is **not just a local annoyance** — the failing test is:

- marked `@pytest.mark.bug_class`, and `cross-skill-bug-class.yml` runs the **release** bug_class leg on `pull_request` for `.claude/skills/release/**` → **fails on PR**.
- collected by `release-ci.yml`'s `pytest scripts/tests -m 'not integration'` (it is NOT marked integration) on `pull_request` for `.claude/skills/release/**` or `.claude/pack.manifest.yaml` → **fails on PR**.

Empirical: exact CI commands both fail; full suite = **193 passed, 1 failed (this one), 19 skipped**.

This creates a chicken-and-egg for landing the changeset: the manifest is bumped to 2.0.0 in the same PR, but the lock that makes CHANGELOG top == 2.0.0 is deferred to owner-time `release.py --release 2.0.0 --apply`. The PR cannot go green until the lock happens, but the design says lock = release-time.

**Why this is real, not theoretical:** if this lands via PR, required-check enforcement blocks the merge; if it lands via direct push to `master`, the merge succeeds but `release-ci.yml` / `cross-skill-bug-class` show red on the branch, and any subsequent PR touching `release/**` or the manifest inherits the red until lock.

**Options (owner's call — do not auto-pick):**
1. **Lock now in this changeset**: run `release.py --release 2.0.0 --apply` as part of landing (locks `[Unreleased]`→`[2.0.0]`, manifest no-op since already 2.0.0), commit, then the PR is green and the tag push is the only remaining owner step. Cleanest; collapses the two-step into one but means `[2.0.0]` is locked before the tag exists (acceptable — Keep a Changelog allows a dated section ahead of the tag).
2. **Mark `test_bundle_changelog_top_matches_manifest_version` to skip when CHANGELOG top is `[Unreleased]`-pending** — i.e. only assert equality once a released section exists at the bumped version. Weakens the gate; not recommended.
3. **Land on a release branch, run the lock there, tag from it.**

Recommend option 1 unless the owner deliberately wants manifest-bumped-but-unlocked on `master` between PR and tag. Surface to owner; this touches the deliberate deferred-lock design decision.

### LOW-1 — `_today()` uses local-tz `datetime.date.today()`
Release date in the locked heading + CI epoch derive independently; a near-midnight UTC boundary could date the CHANGELOG one day off from the commit `%ct`. Cosmetic (date in changelog text only, not identity). `--date` override exists. No action required.

### LOW-2 — `--extract` accepts `Unreleased` as a "version"
`release.py --extract Unreleased` returns the unreleased body (no guard that the arg is a released semver). Harmless — CI always passes a tag-derived semver; `--extract` is read-only. Not worth a guard.

### LOW-3 — `bump_version` strips pre-release before arithmetic (`1.2.3-rc.1 patch → 1.2.4`)
Correct and tested, but note it discards the rc context silently. Fine for this tool's contract.

---

## Confirmed KNOWN/EXPECTED (as described)
- The single version-sync failure IS `test_bundle_changelog_top_matches_manifest_version`, IS by-design, resolves on `release.py --release 2.0.0 --apply`. (Severity elevated to MED-1 only because it gates PR CI, not because the diagnosis is wrong.)
- 8 node failures in `advisory-boundary-policy.test.cjs` are pre-existing: caused by `readRepoFile('claude/agents/code-reviewer.md')` (missing leading `.`), references `code-reviewer.md` not any rename target, file is untracked uncommitted work outside this diff. Unrelated; not fixed.

---

## Positive (risk-calibration)
- `release.py` is genuinely small/deterministic (172 lines, pure-text transforms, git only behind `--apply && --push`). No git/network in dry-run. Tests cover every invariant including REPO path-math locked empirically. This is the opposite of AI-slop — no defensive paranoia, no parallel reimplementation (modelled on the existing `_framework-shared/release.py`).
- Rename touchpoint coverage is thorough: all 4 default-string fallbacks (`build_manifest_writer`, `build_manifest_questions`, `manifest_validator`, `manifest_loader`), interactive default, tag prefix, commit message, eval gate, all 3 workflows, installers, sidecar glob.
- Build determinism verified byte-identical across two clean builds.

---

## Recommended actions (prioritized)
1. **MED-1**: decide the lock-timing (recommend option 1: run `release.py --release 2.0.0 --apply` to lock before the PR/branch goes green), so PR CI passes. Owner decision — do not auto-apply (touches the deferred-lock design).
2. Leave LOW-1/2/3 as-is (documented, not worth churn).
3. Do not touch the pre-existing `advisory-boundary-policy.test.cjs` typo as part of this changeset.

## Unresolved questions
- Is the intent to land this changeset via **PR** (then MED-1 blocks merge until lock) or via **direct push to master** then tag (then MED-1 is just red-on-branch between push and lock)? The fix differs slightly. Needs owner.

**Status: DONE_WITH_CONCERNS** — ship-ready code; one CI-gating sequencing decision (MED-1) needs the owner before the PR can be green.
