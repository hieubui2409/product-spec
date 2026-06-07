# Changelog — cleanmatic:telemetry

All notable changes to this skill are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/); versioning: [SemVer](https://semver.org/).

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
- **Read-only:** never edits specs, code, the catalog, or memory; no network; venv-run.
- **Not shipped** in the release bundle (local PO tooling); the supporting `_shared` lenses + the two new hooks are git-tracked but bundle-excluded by manifest omission.
- **Deferred** (see `BACKLOG.md`): rich crash-log `errors.jsonl`, HTML output, E3 market-outcome.
