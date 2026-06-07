# STANDARDIZE.md — human-analyzer patterns applied to cleanmatic-skills

The **reverse** of `human-analyzer/STANDARDIZE.md`: patterns this 3-skill repo (`product-spec`,
`product-spec-critique`, `release`) adopted *from* the `human-analyzer` (HA) reference repo. One row per
adopted pattern: where it came from, what landed here, and where CM deliberately diverged. Depth lives in the two
source reports, not duplicated below; this is a retrospective ledger, not a TODO (that stays in `BACKLOG.md`).

Depth sources:
- `plans/reports/comparative-learning-260606-1720-human-analyzer-patterns-report.md`
- `plans/reports/ha-implementation-blueprint-260606-1720-four-lens-deepdive-report.md`

---

| Pattern | HA source | What CM adopted (where it lives) | Divergence / why |
|---|---|---|---|
| **A1 · Telemetry sink** | HA `telemetry-paths.cjs` (12-sink observability) | Fail-open append-only JSONL: `.claude/skills/_shared/lib/telemetry-paths.cjs` + 3 hooks (`track-skill-invocation`, `track-script-execution`, `emit-session-summary`) + idempotent `register_telemetry_hooks.cjs`; sinks gitignored, never bundled. | Schema-trimmed to 3 sinks (CM is smaller). Skill-event uncertain in this CC version → **ship-both** (Skill-tool + prompt-expansion) with cross-process dedup, not HA's single-event assumption. |
| **A2 · Audit-trail ledger** | HA backlog `BL-*` + STANDARDIZE mapping | `docs/audit-trail/` — `EVIDENCE.md` (fixes, runnable before/after), `REVIEW.md` (per-cycle tracker), `README.md` (ID grammar `(PS\|PSC\|PACK\|LIB)-\d+`), `telemetry-readback.md`. | ID grammar is CM-scoped (per-skill prefixes). Code/filenames never reference ledger IDs (review-audit Rule 5) — same discipline as HA. |
| **A3 · Eval harness** | HA `run_evals` structural gate | **Two halves.** Structural: `.claude/skills/_shared/lib/run_evals.py` (`_gating: structural\|llm_advisory`) wired into all 3 CI workflows as a non-blocking-on-manual gate. Advisory: `.claude/skills/_shared/lib/llm_eval.py` judges the 35 `llm_advisory` assertions (13 ps + 22 critique) against `eval/golden/<id>.md` fixtures via an injectable LLM client — local/on-demand (needs a key + review), NOT in CI. | Honest mapping only: release fully runnable (10 checks); ps/critique LLM-heavy parts were marked `UNMAPPED`/`llm_advisory` rather than faked. The advisory judge closes that honest-but-unrun half *without* faking it: missing golden → loud MISSING (never PASS), garbage judge reply → ERROR. Unknown-checker → hard FAIL; no false-green either side. |
| **A4 · Version-sync gate** | *(none — CM-original)* | `verify_skill_versions.py::changelog_top_version` (skips `[Unreleased]` + pre-release) + `test_version_sync.py`; asserts SKILL.md `metadata.version` == per-skill CHANGELOG top for **all three** skills, AND root `/CHANGELOG.md` top == `pack.manifest.yaml` version (bundle identity). | **CM-original; HA has no equivalent.** Bundle/all-release log moved to repo-root `/CHANGELOG.md`; each skill (incl. release) keeps a skill-scoped CHANGELOG — so the old release exclusion is gone, the gate now covers all three. |
| **Repeat-offense polish** | HA instinct-store / learning-loop | Louder repeat surfacing in `critique-consolidator.md` (count `×N` + occurrence refs, level-scaled scold) + `critique-humanizer.md` preserve-set; guarded by `test_repeat_offense_litmus.py`. | **Stayed on the safe side of the boundary HA crossed:** repeat-count is attached *after* judgment, never fed into the per-finding LENS inputs. Litmus proves it catchable (inject → RED). A9 full learning-loop **deferred on purpose** (needs API key + separate review). |
| **Release-changelog model** *(reverse: HA refined → CM adopts back)* | HA `com:release` brainstorm: Keep-a-Changelog `## [Unreleased]` flow, release = pure text-move (lock `[Unreleased]→[X.Y.Z]`, deterministic, no git-read-at-build → kills the S4 auto-clobber fragility), **GitHub Release body = the just-locked changelog section** (one source flows to the Release page), release helper with `--extract/--release/--bump/--push(owner opt-in)/--dry-run`, owner-stops-before-push. | Root `/CHANGELOG.md` = bundle release log with `[Unreleased]` flow; its locked section feeds the GitHub Release body (replacing `generate_release_notes`); helper `release.py` in `.claude/skills/release/scripts/` (CM has no COM skill — release already owns packaging/release). | CM **keeps 3 per-skill changelogs** (HA dropped per-skill → 1-bundle because 59 skills; 3 is light). Two version axes, not one global number: per-skill `changelog==frontmatter`, bundle `root==manifest==tag==release-body`. Release ops (tag push) stay owner-owned — helper prints the tag command, never pushes by default. |

---

**At a glance:** CM took HA's observability (A1), audit discipline (A2), and eval gate (A3); added a version-sync
gate HA lacks (A4); adopted HA's repeat-offense instinct **without** its judgment-contaminating feedback loop; and is
adopting back HA's `[Unreleased]`-flow release-changelog model (deterministic lock + Release-body-from-changelog),
kept to a 3-skill scope (per-skill changelogs retained, helper homed in release).
