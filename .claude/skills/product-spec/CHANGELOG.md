# Changelog

All notable changes to **cleanmatic:product-spec** are documented here. This is the human changelog
for the skill; it is NOT the source of the bundle's GitHub Release notes (those stay auto-generated
from commits by `claude-pack-release.yml`). The skill's release identity is its frontmatter
`metadata.version` in `SKILL.md`, verified at release time by `claude-pack/scripts/verify_skill_versions.py`.

Format: [keepachangelog.com](https://keepachangelog.com/en/1.1.0/). Versioning: [semver](https://semver.org/).

## [Unreleased]

Backlog C/D/E — closing the PO pipeline. Additive + backward-compatible.

### Added
- **`--apply-critique <report>` (E1)** — the critique return-edge: consume a `product-spec-critique`
  report and walk each finding Keep / Change+re-approve / Defer, recording one `DEC-<n>` per resolved
  finding. Findings come from the structured lens-cache (not prose); the report path is read-fenced to
  `docs/product/critique/`; DEC writes are atomic (`decision_register --append-alloc`), resumable, and
  injection-sanitized; a Change on an `approved` artifact goes through GATE-NO-SILENT-REVERSAL with a
  deterministic fresh-re-approval guard. Scripts: `parse_critique_report.py`, `apply_critique_progress.py`.
- **`--viz audit` (C9)** — a read-only governance trail joining change-log · approvals · stale-approvals ·
  decision register into one chronological table, with explicit `unreconciled` rows for source
  disagreement. ASCII + `md` only (no HTML). Script: `assemble_audit_trail.py`.
- **`--summary --audience exec|release-notes` (E4)** — audience modifier on `--summary` (no new flag).
  `exec` = the current one-pager; `release-notes` = "what changed since the last approved snapshot" from
  the C9 trail. New `release-notes` template.
- **`--discover <path(s)>` (E2)** — discovery seed: ingest raw upstream text (files AND directories) into
  candidate personas/problems/JTBD to seed the Vision interview. Read-fenced to the project root,
  `.md`/`.txt` only, dotfiles excluded, size-capped, bounded directory recursion. Never auto-commits.
  Script: `ingest_raw_inputs.py`.
- **`goal_without_metric` validation check (C11)** — a BRD goal with empty/missing `metrics` is an
  `error` (enforced by `strict_gate`).

### Changed
- **`_hashable()` consolidated (D11)** — the byte-identical copies in `render_ascii` and
  `render_ascii_board` now share one home in `render_common.py` (product-spec-internal; output unchanged).

## [2.0.0]

- Current shipped baseline (see git history for the full feature set: Vision/BRD/PRD/Epic/Story
  hierarchy, traceability, validation, visualization, decision register, memory-write enforcement).
