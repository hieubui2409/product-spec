# Changelog — cleanmatic:telemetry

All notable changes to this skill are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/); versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [1.1.0] — 2026-06-13

### Added
- **Artifact-edit heat** — a path-only PostToolUse sink (`track_artifact_edits.py`) records which spec
  artifacts are edited (record is exactly `{ts, artifact_path, op, session}` by whitelist — never diff or
  file content), and a new `artifact_heat` lens tallies which artifacts churn most. Fail-open; auto-registered.
- **Usage-summary export + read-only harvester** — `analyze_telemetry.py --export-summary [PATH]` writes a
  markdown aggregate the PO can review and forward; `--auto-suggest` (opt-in) appends suggestions from a
  read-only `harvester.py` that reads self-corrections + repeat-edits and never writes any skill or template
  (boundary A9). Export defaults to the canonical `.claude/telemetry/` dir and honors `CK_TELEMETRY_DIR`.

### Changed
- **Session duration + early-skill reconstruction** — duration and the first skills of a session are
  recovered from the transcript head, with a dedicated script-run session key.
- **Declared workflow-chains moved to an on-demand `data/skill-chains.yaml`** data file (off the
  always-on path); the internal CI suite is wired in.

### Fixed
- **Script-run matcher tightened**, overview lenses isolated from one another, and the validate
  reason localized.

## [1.0.1] — 2026-06-08

### Added
- **Bilingual fixed labels via `--lang vi|en`** (default `vi`). The renderer now localizes every
  fixed scaffolding string (headings, ascii banners, column headers, gate note, disclaimers) through a
  single `_T` dict; dynamic data (numbers, skill ids, script paths) stays language-neutral. The LLM still
  narrates the interpretive prose on top in the chosen language. Resolves the gap where EN/VI was only a
  narration directive and the script output was English-only with a mixed-language gate note.

### Changed
- **Self-contained layout.** The skill's own runtime code (lenses, `analyze_telemetry`,
  `register_telemetry_hooks`, `telemetry_render`, `catalog`, `formatters`, `telemetry_paths`) moved from
  `_shared/lib` + `_shared/scripts` into `.claude/skills/telemetry/scripts/**`, matching the
  self-contained convention of the other three skills. The 5 sink hooks now bootstrap `sys.path` from
  `skills/telemetry/scripts`; the bundle ships the skill dir via the `skills:` walk (no telemetry code under
  `_shared` anymore). Only the cross-skill **eval-gate** (`run_evals`, `llm_eval`) still rides
  `_include_shared: [lib]`. No behaviour change — paths only.

## [1.0.0] — 2026-06-07

### Added
- Initial release. A read-only, plain-Vietnamese **usage & health** read for the product owner, ported and adapted from `human-analyzer`'s `com:skill-analytics` (dev-facing English) — genuine gaps added: ascii + mermaid renderers and VI non-technical narration.
- **8 lenses** via `_shared/scripts/analyze_telemetry.py` (deterministic gather; the skill narrates):
  - `usage` — invocation counts + per-skill token attribution (approx) + never-used catalog.
  - `session` — session count, avg/median duration, files, subagents, skill co-occurrence.
  - `health` — per-script runs/errors/error-rate + avg `ms` (approx).
  - `reliability` — subagent success/api_error/timeout/blocked/unknown per type (new SubagentStop sink).
  - `workflow` — actual skill chains vs declared routing-doc chains; deviations.
  - `validate` — validate-pass **internal-quality** proxy (last-status from `last_validated.json` marker + pass-rate from validate-script exit history); explicitly **NOT** E3 market outcome.
  - `memory` — orphans / dead index entries / broken `[[links]]` / staleness (read-only, no `--apply`).
  - `forensics` — single-session reconstruction (skills/tools/tokens/files/duration).
- **Renderers:** `ascii` (terminal one-glance), `mermaid` (fenced pie/bar, escaped, no network/JS), `md`, `json`.
- **Low-volume gate** ("chưa đủ dữ liệu") suppresses recommendations on thin data.
- **Honesty gate:** every report ends with a mandatory "Cái này KHÔNG đo được" section separating MEASURED from NOT-MEASURED (market/user outcome / E3).

### Notes
- **Read-only:** never edits specs, code, the catalog, or memory; no network. Stdlib-only → runs under system `python3` (no venv needed on recipients).
- **Shipped** in the release bundle (first ships in `product-spec-v2.1.0`): the skill, its 5 sink hooks, and the supporting `_shared` lens/eval code (`_include_shared:[lib,scripts]`). The installer auto-registers the hooks (opt out: `register_telemetry_hooks.py --remove`).
- **Deferred** (see `BACKLOG.md`): rich crash-log `errors.jsonl`, HTML output, E3 market-outcome.
