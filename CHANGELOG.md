# Changelog — release history (the whole bundle)

The **project release changelog**. Every tagged release (`product-spec-v*`, formerly `claude-pack-v*`) of the
distributable bundle is recorded here; its top `## [X.Y.Z]` heading is the bundle release identity and must equal
`version:` in `.claude/pack.manifest.yaml`. The bundle ships four skills (`cleanmatic:product-spec`,
`cleanmatic:product-spec-critique`, `cleanmatic:release`, `cleanmatic:telemetry`) plus their agents and hooks
(`cleanmatic:telemetry`'s sink hooks are auto-registered by the installer).
Format: [keepachangelog.com](https://keepachangelog.com/en/1.1.0/). Versioning: [semver](https://semver.org/).

> **Per-skill changelogs live with each skill** — `.claude/skills/<skill>/CHANGELOG.md`, each pinned to that
> skill's own `SKILL.md` `metadata.version` (the A4 PR-gate asserts skill version == skill changelog top for all
> four, including the `release` skill). This root file is the *bundle/release* log; the skill files are the
> *per-skill* logs. On a release: bump each changed skill's `metadata.version` + its CHANGELOG, fill `[Unreleased]`
> here, then run `release.py --release X.Y.Z --apply` (locks `[Unreleased]` → `[X.Y.Z]` + bumps
> `pack.manifest.yaml version:` together). CI `verify_skill_versions.py` fails the release on any missing/malformed
> skill `metadata.version`.

## [Unreleased]

## [2.3.0] — 2026-06-09
### Added
- **product-spec `--learn` (learning loop)** — post-launch outcomes (target vs actual → `OUT-<n>`
  register, 3-tier verdict, learning views) + a discover-back feedback path. (product-spec 2.3.0/2.3.1)
- **Context-footprint harness** (`_shared/lib/context_footprint.py`) — per-skill SKILL.md/ref token
  proxy + size gate + a mechanical GATE co-presence guard, wired into pytest as a regression guard.
- **Telemetry hook hardening** — shared `hook_runtime` with crash audit, per-hook config gate, and a
  hook registrar/installer.

### Changed
- **SKILL.md flag-table compaction (per-turn context flow)** — product-spec SKILL.md −11.8%,
  product-spec-critique −3.7%; elaboration relocated into the references that load when each flag
  fires (net info preserved; routing held — best-of-3 sub-agent judge 18/18). (product-spec 2.3.1,
  critique 1.2.1)
- **Root `CLAUDE.md` / `.claude/rules` slimmed** to an always-on safety + skill-routing layer.

### Fixed
- **`pack.manifest.yaml`** no longer lists three deleted rules files; `test_pack_cli_full_run` sets
  the working dir so `python -m pack` resolves the package.

## [2.2.2] — 2026-06-08
### Changed
- **Root `CLAUDE.md` slimmed to an always-on safety + routing layer** (148 → 60 lines). The three inline
  skill operating guides collapse into a router table that points at each skill's `SKILL.md` (loaded on
  demand); only the cross-skill always-on layer stays inline (the two GATEs, Five Operating Principles, the
  anti-rationalization table). Removed prose (ID grammar, bilingual conventions, workflow pointers, script
  contract, boundaries, failure handling) already lives in the skills' `SKILL.md` / `references`. The shipped
  bundle carries the leaner `CLAUDE.md` (`include_claudemd`). Repointed the now-removed "What This Skill Does
  NOT Do" anchor in `product-spec/references/interview-frameworks.md` to
  `references/guardrails-and-boundaries.md`.

## [2.2.1] — 2026-06-08
### Added
- **AGPL-3.0 license + CONTRIBUTING.** Added `LICENSE` (GNU AGPL-3.0, © 2026 Hieu Bui) and
  `CONTRIBUTING.md` (inbound=outbound, DCO sign-off, dev/test/release workflow). Both are added to the
  manifest `extra:` so every distributed bundle carries the license + contribution terms (AGPL requires the
  license to accompany distributed copies). README gains an EN + VI **License** section: noncommercial-friendly
  but proprietary commercial use requires a separate license.

## [2.2.0] — 2026-06-08
### Changed
- **`cleanmatic:telemetry` is now a self-contained skill.** Its runtime code (8 lenses, `analyze_telemetry`,
  `register_telemetry_hooks`, `telemetry_render`, `catalog`, `formatters`, `telemetry_paths`) moved from
  `_shared/lib` + `_shared/scripts` into `.claude/skills/telemetry/scripts/**`, matching the self-contained
  convention of the other three skills. The 5 sink hooks bootstrap `sys.path` from `skills/telemetry/scripts`;
  the bundle ships the skill dir via the `skills:` walk. `_include_shared` is reduced to `[lib]` — only the
  cross-skill eval-gate (`run_evals`, `llm_eval`) still rides it. No telemetry code remains under `_shared`.
  Pure refactor: behaviour unchanged, verified end-to-end (build, extract-run, installer auto-register).
- **Installer registrar path updated** to `.claude/skills/telemetry/scripts/register_telemetry_hooks.py` in
  `install.sh` / `install.ps1` (and the opt-out notice), following the relocation. (release skill → 1.1.1)
- **README rewritten as an ecosystem overview** — frames the bundle as a whole rig (4 skills + critique
  sub-agents + hooks + rules + shared eval-gate + deterministic packager), not just a list of skills; adds a
  "what the harness installs" table and a full `telemetry` section, EN + VI.

### Added
- **`cleanmatic:telemetry` bilingual fixed labels via `--lang vi|en`** (default `vi`). The renderer localizes
  every fixed scaffolding string through a single `_T` dict; dynamic data (numbers, skill ids) stays
  language-neutral; the LLM narrates prose in the chosen language. (telemetry skill → 1.0.1)
- **`cleanmatic:telemetry` user-facing docs** — `README.md`, `GUIDE-EN.md`, `GUIDE-VI.md` added to the skill so
  it matches the documentation depth of the other shipped skills.

## [2.1.0] — 2026-06-08
### Added — cleanmatic:telemetry now ships (usage & health observability)
- **New shipped skill `cleanmatic:telemetry`** — a read-only, plain-Vietnamese **usage & health** read for the
  product owner: 8 lenses (usage+tokens, session-shape, script health, subagent reliability, workflow chains,
  validate-pass internal-quality proxy, memory health, forensics) rendered as ascii/markdown/mermaid/json.
  Deterministic gather (`_shared/scripts/analyze_telemetry.py`) → LLM narration. Reverses the prior
  CM-local/not-bundled decision so end users can read how their own skills are used.
- **5 telemetry sink hooks ship + auto-enable.** `track_skill_invocation`, `track_script_execution`,
  `emit_session_summary`, `mark_bash_start`, `track_subagent_outcome` are bundled and **auto-registered by the
  installer** into the recipient's `settings.json` (idempotent + upgrade-safe; opt out with
  `register_telemetry_hooks.py --remove`). All fail-open + stdlib-only (system `python3`, no venv needed).
- **Eval gate ships too** — `_shared/lib/run_evals.py` (deterministic structural gate) + `llm_eval.py`
  (LLM-judge, offline by default via `FakeLLMClient`) now travel in the bundle, making each skill's already-shipped
  `eval/golden/` fixtures runnable for recipients.
- The shared lens/eval code rides `_include_shared: [lib, scripts]` in `pack.manifest.yaml`.

### Changed
- **Tests never ship.** `safety_catalog.ALWAYS_DROP_DIRS` now drops `__tests__/` and `tests/` from every bundle.
- **Telemetry bundle guard inverted** — `test_bundle_includes_telemetry.py` asserts the telemetry surface IS
  present (sinks + test dirs stay OUT); the `release` skill is bumped to 1.1.0 for the installer + packaging changes.

## [2.0.0] — 2026-06-07

Major release. The **breaking skill rename + bundle restructure**, bundled with everything that accumulated
unreleased since `1.4.0`: the **human-analyzer (HA) adoption** cycle (observability · audit-trail · runnable
eval gate) and the release-skill hardening line. Skill versions this release: `product-spec` **2.2.0**
(unchanged) · `product-spec-critique` **1.2.0** (unchanged) · `release` **1.0.0** (was `claude-pack` 0.2.0 at
1.4.0 — major bump for the breaking rename).

### Changed — BREAKING (skill rename + bundle restructure)
- **Skill renamed** `cleanmatic:claude-pack` → `cleanmatic:release` (dir `.claude/skills/claude-pack/` →
  `.claude/skills/release/`, git history preserved). The skill now owns the full release lifecycle, not just
  the tarball build.
- **Bundle artifact renamed** `claude-pack-{version}.tar.gz` → `product-spec-{version}.tar.gz`
  (`bundle_name: product-spec`; the 4 default-string fallbacks + interactive default updated).
- **Release tag renamed** `claude-pack-v*` → `product-spec-v*`; CI workflows `claude-pack-release.yml` →
  `release.yml`, `claude-pack-ci.yml` → `release-ci.yml`, `claude-pack-integration.yml` →
  `release-integration.yml`; `cross-skill-bug-class.yml` path filter + leg retargeted.

### Added — release lifecycle
- **Changelog-lifecycle engine** `release.py` (modelled on HA `_framework-shared/release.py`):
  `--extract / --release / --bump {major,minor,patch} / --pre-release / --date / --apply / --push`. Locks
  `[Unreleased]` → `[X.Y.Z] — <date>`, opens a fresh `[Unreleased]`, bumps `pack.manifest.yaml`, and prints
  the owner-owned `git tag product-spec-vX.Y.Z && git push`. Refuses an empty `[Unreleased]` or an
  already-locked version; `--push` requires `--apply`. Pure-text, no git-read-at-build → reproducible.
- **CI release body from the locked CHANGELOG** — `release.yml` publishes `release.py --extract <ver>` as the
  GitHub Release `body_path`, replacing `generate_release_notes`.

### Added — observability (A1)
- **Fail-open telemetry sink (Python)** — append-only JSONL via `.claude/skills/_shared/lib/telemetry_paths.py`
  + 3 hooks (`track_skill_invocation.py`, `track_script_execution.py`, `emit_session_summary.py`) wired
  idempotently by `register_telemetry_hooks.py`. Originally prototyped in Node `.cjs`; **rewritten to Python**
  this release (our hooks are Python; ck-managed `*.cjs` stay ignored) and the temporary `telemetry-spike`
  probe was dropped. Sinks are gitignored and **never enter a bundle** (guarded by
  `test_bundle_excludes_telemetry.py`); the skill-event path ships-both (Skill-tool + prompt-expansion) with
  cross-process dedup.

### Added — audit trail (A2)
- **`docs/audit-trail/`** — `EVIDENCE.md` (landed fixes with runnable before/after), `REVIEW.md` (per-cycle
  finding tracker), `README.md` (ID grammar `(PS|PSC|PACK|LIB)-<n>`), `telemetry-readback.md` (sink `jq`
  queries). Ledger IDs never referenced from code/filenames (review-audit Rule 5).

### Added — runnable eval gate (A3)
- **`run_evals.py`** turns each skill's previously-decorative `evals.json` into a runnable **structural** gate
  (`_gating: structural|llm_advisory` + machine `check`/`exec`), wired into the CI legs; `product-spec` +
  `product-spec-critique` `evals.json` reshaped from bare strings to runnable assertions.
- **`llm_eval.py`** — the **advisory** half: judges `llm_advisory` assertions against `eval/golden/<id>.md`
  fixtures via an injectable LLM client. Local/on-demand (needs a key + human review), **not in CI**; never
  fabricates — missing golden → loud MISSING, garbage reply → ERROR, never a false PASS.

### Added — version-sync gate (A4)
- **`test_version_sync.py`** + `changelog_top_version()` (skips `[Unreleased]` / pre-release headings): asserts
  each skill's `SKILL.md` `metadata.version` == its own CHANGELOG top for all three skills, AND root
  `/CHANGELOG.md` top == `pack.manifest.yaml version:` (the bundle identity, tied to the `product-spec-v*` tag).

### Changed — release-skill internals (the unreleased line folded into 1.0.0)
- **Modularized `pack/`** into focused sub-modules (`args`/`cli`/`selection`/`tarball`/`manifest_io`/`templates`;
  `manifest_loader` + `build_manifest` + `safety_check` split out), each under 200 LOC.
- **Recipient-installer tests** — a SemVer precedence matrix (`test_installer_semver.py`, incl. the PowerShell
  Windows leg) + an install e2e (`test_installer_e2e.py`: build → extract → run `install.sh` into a throwaway
  tree → assert clean + idempotent).

### Notes
- `product-spec-critique` repeat-offense surfacing polish (consolidator/humanizer) guarded by
  `test_repeat_offense_litmus.py`; the per-finding fingerprint (N1) shipped in 1.4.0.
- The tag push that fires `release.yml` stays **owner-owned** — `release.py` prints the exact command; this
  release was prepared (changelog locked + manifest bumped) but not pushed by the tool.

## [1.4.0] — 2026-06-06

product-spec-critique finding-fingerprint release. Skill versions this release: product-spec
**2.2.0** (unchanged), product-spec-critique **1.2.0**, claude-pack **0.2.0** (unchanged).
Additive + backward-compatible; the committed findings-index degrades gracefully for legacy rows.

### Changed — product-spec-critique
- **Finding-level fingerprint (N1).** The findings-index now carries a per-finding
  `finding_fingerprint` = `sha256(node + severity + normalize(cited spec-line text))`, anchored to
  the deterministic spec text a finding cites — not the LLM `why` prose (paraphrase-fragile) nor the
  line number (drifts). Inherit + descendant-rollup dedup by fingerprint (falling back to
  `evidence_id`), so a logical blocker re-critiqued after a line shift is counted **once** instead of
  inflating the rollup, and two distinct findings on one node stay distinct.
- **Back-compatible by construction.** Additive field, index key unchanged; legacy rows without the
  field degrade to `evidence_id` keying. A structural / unresolvable cited line (`---`, a BRD-goal
  frontmatter fence) yields a null fingerprint → `evidence_id` fallback, never a false merge. Leading
  list numbers are kept as content so numbered siblings (`3. X` vs `7. X`) do not collide. The LLM
  consolidator's prior-reports repeat-offense path is unchanged.

## [1.3.0] — 2026-06-04

product-spec engagement-profile release. Skill versions this release: product-spec **2.2.0**,
product-spec-critique **1.1.0** (unchanged), claude-pack **0.2.0** (unchanged).

### Added — product-spec engagement knobs
- **2 PO engagement knobs** in product-spec's `preferences.yaml` — `interview_rigor`
  (light/standard/**deep**) + `action_prompting` (minimal/standard/**proactive**), both default `standard`.
  Modulate interview challenge-depth (all levels) + next-action density; orthogonal to `detail_level`.
- **`preferences.py --set KEY=VALUE` write-CLI** — deterministic PO-driven writer, **load→merge→save**
  (preserves other committed keys; bad enum → non-zero, nothing written).
- **End-of-session forcing-function** folded into the existing Closing-the-Loop batch (PO-confirmed,
  no auto-write). Full detail in product-spec's CHANGELOG `[2.2.0]`.

### Documentation (all 3 skills)
- **Guides restructured** — every `GUIDE-EN.md`/`GUIDE-VI.md` now leads with a Core-concepts mental model,
  a Learning path, and an Important-caveats section, then groups the use cases into approachability tiers
  (the per-flag sample conversations are preserved). EN/VI parity kept.
- **READMEs bilingual** — each skill `README.md` rewritten into English + Tiếng Việt sections with a
  "things to know before you start" quickstart + learning path; the root `README.md` gains a Tiếng Việt
  section and the engagement-knob row.

### Changed
- **Removed the non-functional `--all` flag** — it errored on use and ran against the curated-distribution
  design; use the manifest or `--skills <list>`.

### Hardening / tests
- **Recipient installer is now tested.** A SemVer precedence matrix (`test_installer_semver.py`) pins the
  bash `semver_compare` (and PowerShell `Compare-Semver` on the Windows CI leg) against the leading-zero,
  pre-release, and ASCII-collation edge cases — a wrong verdict here silently keeps a stale skill or
  clobbers a newer one. An install e2e (`test_installer_e2e.py`) builds a real bundle, extracts it, runs
  the bundled `install.sh` into a throwaway tree, and asserts a clean + idempotent install.

## [1.2.0] — 2026-06-04

Pipeline-closure release: product-spec gains `--apply-critique` / `--viz audit` (ascii·md·html) /
`--summary --audience` / `--discover` / the `goal_without_metric` validate check / `_hashable`
consolidation; product-spec-critique gains strengthened assumption-rigor lens prompts; the bundle
gains the skill-version release gate + cross-skill CI. **Also finalizes the
`agent-naming-conventions` rename** (skill / sub-agents / hook). Skill versions this release:
product-spec **2.1.0**, product-spec-critique **1.1.0**, claude-pack **0.2.0**.

### Changed — naming conventions (`agent-naming-conventions`)
- **Skill renamed `spec-critique` → `product-spec-critique`** — invoke as `cleanmatic:product-spec-critique`
  now. `pack.manifest.yaml` skill entry + all bundle references updated.
- **6 lens/consolidator sub-agents renamed to actor-noun** (`.claude/agents/`):
  `spec-critique-product`→`product-critic`, `-tech`→`tech-critic`, `-market`→`market-critic`,
  `-craft`→`craft-critic`, `-consolidate`→`critique-consolidator`, `-humanize`→`critique-humanizer`.
- **Stop-hook renamed** `spec_critique_nudge.py` → `product_spec_critique_nudge.py`.
- Untracked the ck-managed `release-manifest.json` (regenerated locally; not repo source).

### Added
- **Skill-version release gate** — `scripts/verify_skill_versions.py` asserts each skill's nested
  `metadata.version` is present + semver; wired into `claude-pack-release.yml` before the build (drift
  fails the release). Each of the 3 skills now keeps its own `CHANGELOG.md`.
- **Cross-skill CI** — `product-spec-ci.yml` + `product-spec-critique-ci.yml` (1 OS × 2 Python,
  path-filtered, per-skill-dir scoped; critique offline-enforced) and `cross-skill-bug-class.yml`
  running the `bug_class`-marked safety/robustness invariants per skill. `bug_class` registered in all
  3 pytest configs (product-spec + critique gain a `pyproject.toml`).

### Notes
- Bundle now ships product-spec's new `--apply-critique` / `--viz audit` / `--summary --audience` /
  `--discover` surfaces + `goal_without_metric` validate check, and critique's strengthened
  assumption-rigor lens prompts (see each skill's CHANGELOG).
- **Migration:** if you invoked the old `/spec-critique`, use `/product-spec-critique`; if you referenced
  the old sub-agent or hook filenames directly, update to the new names above.

## [1.1.0] — 2026-06-03

The first release since v1.0.0. Three layers landed together on the way here:
product-spec **memory-write enforcement**, product-spec-critique **lifecycle caching +
cross-critique inheritance**, and product-spec-critique **bilingual-output hardening**. Additive
and backward-compatible; defaults preserve current behaviour. Sections below are grouped
by theme; each carries its own Added/Changed.

---

**Bilingual-output hardening (product-spec-critique).** The consolidator renders English reports
fully in English (a root-cause fix for a Vietnamese-leak regression), the English level-9
voice has a concrete "sustained profanity" floor so it outscales level 8, and a new
advisory language-purity check guards the leak class. Report-only.

### Added — product-spec-critique

- **Advisory en-language-purity check** (`scripts/check_report_language.py`): flags a
  Vietnamese STRUCTURAL leak (heading/label/register denylist) in a `lang: en` report,
  separated from review-only signals (vi glosses, proper nouns, quoted Vietnamese source
  text — legitimate when the source spec is Vietnamese). Never gates (advisory, exit 0).
  Confirms the 18 committed fixtures carry zero structural leak.
- **lens-per-language design decision** recorded in `voice-and-tone.md`: language is a
  source-anchored IDENTITY axis (a lang change re-lenses; it is part of provenance),
  level is the render-time axis. A shared neutral-interlingua lens was considered and
  rejected on YAGNI grounds (a spec is critiqued in one language; the translation cost +
  native-quality loss are real, the saving illusory).

### Changed — product-spec-critique

- **English reports render fully in English.** The consolidate-agent contract was
  vi-only and contradicted `voice-and-tone.md`; headings, why/fix labels, and register
  are now lang-conditioned, with an explicit EN register mapping (dialect/gender are
  no-ops in en; profanity-presence separates L7/L8/L9). Fixes Vietnamese headings/labels
  and (at L9) Vietnamese profanity leaking into en reports.
- **EN level-9 sustained-profanity floor made concrete:** work-targeted profanity in
  >=2 distinct finding blocks PLUS >=1 standalone scorn line, strictly heavier than L8's
  single beat (the mechanical EN L7→L8→L9 boundary).
- **Descendant-rollup heading** renamed `Rủi ro giao hàng` → `Rủi ro bàn giao`
  (handover, not shipping) across the agent, the vi guide, and the language-check denylist.

### Tests & fixtures — product-spec-critique

- **Regenerated the 18 voice-ladder reference fixtures** (vi + en, levels 1-9) via the
  genuine consolidate→humanize agents over a cached neutral lens run (no re-lens), with
  frontmatter + the committed lifecycle caches (lens-cache, findings-index, state).
  Seeded a committed descendant-rollup demo from the real lvl9 blockers.
- **Parametrized the grounding guard** over the 18 fixtures (graph-aware citation
  resolver, the ratio rule, a frontmatter contract check) and added the language-check
  unit tests. product-spec-critique suite: 150 passing.

---

**Lifecycle caching + cross-critique inheritance (product-spec-critique).** Re-running a critique
reuses prior work (token savings, never a safety gate), and a critique can surface a
parent's prior blockers onto a child (and a parent rolls up its critiqued children's
verdicts). Includes a cross-skill touch to product-spec's preferences.

### Added — product-spec-critique

- **Lifecycle caching (5 committed `.memory/` stores).** `critique-findings-index.json`
  (lossy evidence-ID query cache → inherit/repeat-offense), `critique-lens-cache/<hash>.json`
  (the FULL lens-findings array verbatim — the store that makes `consolidate_only` real),
  `critique-state.json` (per-scope provenance fast-path marker), `web-cache/<url-hash>.json`
  (market URL fetch + 14-day TTL), `humanized-cache.json` (reuse humanized output when the
  consolidated text is unchanged).
- **Provenance reuse + report frontmatter.** Critique reports now carry YAML frontmatter
  (`critique_scope`/`level`/`lang`/`register`/`body_hash`/`lens_findings_hash`/`bundle_version`);
  the next run decides reuse 4 ways: `none` / `full` (already current) / `consolidate_only`
  (re-render voice at a new level WITHOUT re-running lenses) / `relens` (a node changed). A
  register flip at the same level re-consolidates (voice is consolidate-time).
- **Cross-critique context.** `inherited_context` (parent→child: a parent's prior blockers
  surfaced as the child's risk, rendered in a separate section, never in the tally) and
  `descendant_rollup` (child→parent: critiqued children's verdicts aggregated onto the
  parent). Consumed by the consolidator ONLY; the lenses stay blind (anti-anchoring).
- **voice-neutral lenses.** The 4 lens prompts now emit a NEUTRAL grounded observation;
  the consolidator is the SOLE home for voice/level/register. This is what makes a cached lens
  finding level-independent (the basis for `consolidate_only`).
- **New flags:** `--fresh`/`--force` (bypass all reuse), `--refresh-web` (force market
  re-fetch), `--no-inherit`, `--no-rollup`, `--inherit nearest|deep` (`--no-inherit` beats
  `--inherit deep`). New bundle keys: `provenance`, `inherited_context`, `descendant_rollup`.
- **Override-boundary table** in `voice-and-tone.md` (the single home): what the PO CAN
  override (level/register/profanity-strength/scope/lenses/detail) vs CANNOT (the universal-harm
  floor + the read-only subagent split).
- **Modularization.** `critique_scan.py` split into focused modules (`critique_common`,
  `critique_bundle`, `critique_signals`, `critique_provenance`, `critique_drift`,
  `critique_inherit`, `critique_cache` + `critique_cache_io` + `critique_blob_cache`).

### Added — product-spec (cross-skill touch)

- **3 critique preferences registered** in `product-spec/scripts/preferences.py` `DEFAULTS`+`ENUMS`
 : `critique_inherit` (on/off), `critique_rollup` (on/off), `critique_inherit_depth`
  (nearest/deep) — all default on/nearest, with the YAML `on/off→token` coercion. Required
  because `preferences.load()` drops any key not registered there.

---

**Memory-write enforcement (product-spec).** The spec skill detects and nudges when a
judgment or ruling that belongs in the committed memory layer looks unrecorded;
claude-pack ships the supporting agent + hook handler.

### Added — product-spec

- **Deterministic `memory_gap` detector** — the single SCRIPT home for the four
  "memory that looks unrecorded" signals (`fence_breach`, `validate_no_marker`,
  `approved_changed_no_dec`, `judged_not_stored`); correlates persisted disk/graph
  state, emits structured signals, makes no judgment (Script-vs-LLM split).
- **Judgment-cache atomic batch-write (`--store-batch`)** — one validate-all-then-
  write-once persist of a whole verdict batch, collapsing the per-verdict `--store`
  loop and its "stored some, forgot others" surface; also writes the
  `.memory/last_judged.json` marker the gap detector reads.
- **`behavioral_memory --voice`** — surfaces the PO-style voice observations.
- **`status` unrecorded-memory signals** — `--status` now folds in the memory-gap
  signals (unvalidated drift, approved edits with no DEC, unstored judgments).
- **Tier-0 forcing-functions + `references/memory-enforcement.md`** — the operating
  guide for when each memory write is owed and which writer owns it.
- **Opt-in Stop hook** `.claude/hooks/memory_gap_hook.py` + `install.sh --memory-hook`
  — a thin policy wrapper that blocks turn-end on a fence breach (persist) or nudges
  once on an unrecorded judgment/ruling; loop-safe via internal backstops.
- **`--reflect` retroactive harvest** + a read-only `memory-harvester` agent that
  scans for memory that should already have been recorded.

### Added — claude-pack

- Bundles the `memory-harvester` agent and the `memory_gap_hook.py` handler so a
  packed install carries the full memory-enforcement surface.

## [1.0.0] — 2026-05-31

First **stable** release. This entry is the consolidated **full changelog** for the
bundle to date (`cleanmatic:product-spec` + `cleanmatic:claude-pack`); the dated
`0.x` sections below remain the per-release history.

### product-spec — the spec skill

- **Core (Phases 1–8).** Strictly-traceable hierarchy Vision → 1 BRD → many PRDs →
  Epics → Stories (+AC); rich YAML frontmatter as source-of-truth; phased bilingual
  (EN/VI) PO interview; deterministic structural scripts vs LLM judgment split;
  evals + a worked `examples/acme-shop`.
- **v2.0.0 multi-dimensional schema.** RISK (per-PRD/epic registers, impact×likelihood
  enum validation, HTML risk grid), TIME (`target_date` + `depends_on` edges,
  cycle-safe roadmap/gantt views, wall-clock advisory outside the validate gate),
  COMPETITION (competitors at the BRD, parity per-PRD; parity matrix + threat heatmap),
  the impact engine, the v1→v2 migration, HTML-native matrix views + the multi-dim
  dashboard, and ASCII downgraded to a deterministic text-summary.
- **Read-once `--export` + board/explorer viewers** — one shared HTML design system,
  vendored Mermaid + marked + DOMPurify, fail-closed sanitize chokepoint.
- **Visualization overhaul (this line).**
  - *Fixed:* Mermaid re-renders on theme toggle (stale light-on-dark scope/moscow
    quadrants + dark roadmap lines are gone); dark-mode legibility for gantt/quadrant/
    timeline labels + delta/gap nodes; `time` gantt no longer errors on undated
    PRDs/epics; `moscow`/`scope` plot one point per bucket/cell (not a centre dot);
    `delta` no longer renders "Unsupported markdown: list"; graph-view zoom works and
    fills the viewport.
  - *Added:* hover-on-ID tooltips across every graph + HTML-native view (incl.
    dashboard); `tree`/`roadmap` show artifact titles (populated from the body H1);
    `persona`/`heatmap` render as HTML-native tables in `--format html`.
  - *Example:* `examples/acme-shop` is a mature ~2-year product spec (44 nodes,
    5 personas, 4 competitors, risks, target dates, full MoSCoW + Now/Next/Later).

### claude-pack — the bundler skill

- Manifest-first selection with CLI override + interactive fallback; byte-deterministic
  tar.gz (PAX, sorted walk, `mtime=0`, `uid=gid=0`) with opt-in `--source-date-epoch`
  (CI builds reproducibly from the tagged commit time); hard always-drop safety filter;
  SemVer-2.0.0 manifest validation; SHA256 sidecar + embedded `MANIFEST.json`; bundled
  multiplatform installer.

### Onboarding & docs

- Per-skill bilingual usage guides (`GUIDE-VI.md` / `GUIDE-EN.md`), Windows-native
  installers (`install.ps1`), venv-bootstrap operating instruction, umbrella `README.md`.

### Hardening

- 11 dual-skill review cycles: tarball path-traversal close, remote-URL/userinfo scrub,
  semver tightening, Windows-safe path containment, crash-safety against malformed
  input, native-reviewed Vietnamese phrasing, DRY/i18n cleanup, regression coverage.

## [0.2.2] — 2026-05-31

### Fixed
- `product-spec` graph-view HTML: **Zoom +/− and Reset now work.** The zoom transform was applied to `#diagram`,
  which carries the shared `.ve-card` entrance animation (`ps-fade`, `animation-fill-mode: both`) — and an animated
  property's computed value wins over inline style, so the scale was silently clobbered. The transform now targets a
  non-animated inner `#diagram-scale` wrapper; `#diagram` keeps `overflow: auto` so a zoomed diagram scrolls instead of
  clipping. Verified live in headless Chrome (3× zoom → `matrix(1.3,…)`, reset → `matrix(1,…)`).

### Changed
- `product-spec` worked example (`examples/acme-shop`): enriched from a thin fixture into a **mature ~2-year product
  spec** — 44 nodes (1 PRODUCT, 1 Vision, 6 BRD goals, 7 PRDs, 11 epics, 18 stories), 5 personas, 4 competitors, risk
  registers, target dates (incl. shipped/past), `depends_on` chains, and full MoSCoW (Must/Should/Could/Won't) +
  Now/Next/Later coverage. Generated via the skill's own `generate_templates.py` (no hand-authoring). Validates clean:
  0 errors on `check_consistency` / `check_traceability`. Gives the board/explorer/risk/competition/MoSCoW views real
  data to render.

## [0.2.1] — 2026-05-31

### Changed
- `claude-pack` usage guides (`GUIDE-VI.md` + `GUIDE-EN.md`): present the **skill flag** form
  (`/cleanmatic:claude-pack --flag`) as the second way to run each use case — matching the product-spec guide
  pattern — and keep the underlying `python -m pack` invocation as a dev-facing "runs under the hood" note.

## [0.2.0] — 2026-05-31

Documentation + onboarding release. No change to the pack builder core or the determinism contract.

### Added
- Per-skill **usage guides** (`GUIDE-VI.md` + `GUIDE-EN.md`) for both bundled skills: every use case as a full sample conversation, covering the natural-language way (preferred) and the flag/CLI equivalent. product-spec guides use the `examples/acme-shop` worked sample.
- `cleanmatic:product-spec/install.ps1` — Windows-native installer (parity with `claude-pack`): creates the shared venv, installs `pyyaml`, and vendors Mermaid + marked + DOMPurify with sha256 verification.
- **Venv-bootstrap operating instruction** in both `SKILL.md` files + repo-root `CLAUDE.md`: when the shared venv is missing, the LLM asks (AskUserQuestion) to run the installer instead of silently failing or falling back to system Python.

### Changed
- Repo-root `README.md` now covers **both** skills (product-spec + claude-pack) as an umbrella, with per-skill install (POSIX + Windows) and deep links.
- Cross-references to the new guides added to both `SKILL.md` + `README.md` files and the two `CLAUDE.md` operating-guide sections.

## [0.1.0] — 2026-05-31 (first bundled release)

First tagged bundle release. The tag sits on top of the **entire initial build of
both skills**, so it ships the complete product-spec skill — from scaffold through
its **v2.0.0 multi-dimensional schema** — alongside the new claude-pack bundler, after
11 dual-skill hardening review cycles.

### Added — product-spec (shipped in this bundle)
- **Core skill (Phases 1–8):** the Vision → BRD → PRD → Epic → Story (+AC) hierarchy,
  rich YAML frontmatter source-of-truth, bilingual (EN/VI) phased PO interview,
  reference specs, artifact templates, structural scripts, the visualization renderer,
  interview question banks, workflow-orchestration references, evals + a worked
  `examples/acme-shop`. Script-vs-LLM split (deterministic checks vs INVEST/drift/dup
  judgment).
- **v2.0.0 multi-dimensional schema:** RISK (registers + enum validation + HTML grid),
  TIME (`target_date` + `depends_on` edges + cycle-safe roadmap/gantt views),
  COMPETITION (competitors at BRD, parity at PRD; matrix + threat heatmap), the impact
  engine, the v1→v2 migration, HTML-native matrix views + the multi-dim dashboard,
  ASCII downgraded to a deterministic text-summary.
- **Read-once `--export` + interactive board / explorer viewers** — one shared HTML
  design system; vendored Mermaid + marked + DOMPurify with a fail-closed sanitize
  chokepoint.

### Added — claude-pack (the bundler)
- Manifest-first selection (`.claude/pack.manifest.yaml`) with CLI flag override and interactive fallback.
- Deterministic tar.gz builder: PAX format, file-granular sorted walk, `mtime=0`, `uid=gid=0`, gzip header `mtime=0`. Same source → byte-identical bytes.
- Always-drop safety filter (HARD, non-negotiable): `.env`/`.envrc`, SSH keys, `.netrc`/`.pgpass`, `.git/` + VCS dirs, runtime caches, session state, build artifacts, `*.pem`/`*.key`/keystores, `*token*.json`/`*secret*.json`. `settings.json` + `.ck.json` opt-in only.
- `_shared/` dependency detection: warn-only (fenced code blocks stripped first); opt-in via `--include-shared`.
- Hardened manifest validation: SemVer 2.0.0 (build metadata), absolute-path + `..`-traversal rejection, duplicate detection, strict known-keys, on-disk existence checks. Stable error codes (`MANIFEST_E###`).
- Bundled multiplatform recipient installer (`install.sh` POSIX + `install.ps1` Windows), version-aware (STALE / NEWER / OK SAME).
- SHA256 sidecar (coreutils format) + embedded `MANIFEST.json` (schema 1.0, per-file SHA256).
- 25 CLI flags including `--dry-run`, `--compute-sha`, `--max-size`, `--source-date-epoch`, `--include-shared`, `--json`.
- Modularized `pack/` subpackage (args, cli, selection, tarball, manifest_io, templates) — each < 200 LOC.
- 57 pytest tests (synthetic golden blocking + live product-spec integration marker) + 3-scenario eval.
- Documentation: SKILL.md, README + FAQ, manifest-spec, flag-reference, safety-rules, workflow-pack, error-catalog, troubleshooting, maintainers-guide.

### CI
- GitHub Actions matrix CI: Ubuntu + macOS + Windows × Python 3.11 / 3.12 / 3.13 (9 jobs, `fail-fast: false`); pre-merge gate runs `pytest -m "not integration"` + a dry-run pack smoke.
- Release pipeline: tag `claude-pack-v*.*.*` → reproducible build (`SOURCE_DATE_EPOCH` from commit time) → SHA256 verify → upload tarball + sidecar to GitHub Releases.
- Weekly integration check (`cron 0 0 * * 0`, `workflow_dispatch`): live product-spec dogfood, non-blocking (`continue-on-error`).

### Notes
- `_shared/` policy is warn-only (not auto-include) to avoid false positives from doc code blocks.
- `pack.py` is cross-platform (POSIX + Windows) via `os.replace`.
- `built_at` is deterministic by default (epoch 0); pass `--source-date-epoch env` for a real provenance date — the release pipeline does this from the git commit time.
- v0.1.0 guarantees **same-OS** byte-identity; cross-OS byte-identity is gated on the 0.5.0 release.
- Side-effect: back-ported the `--dev` flag pattern to `cleanmatic:product-spec/install.sh` (pytest is now dev-only there too).
