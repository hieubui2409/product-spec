# Changelog

All notable changes to **cleanmatic:product-spec** are documented here. This is the human changelog
for the skill; it is NOT the source of the bundle's GitHub Release notes (those stay auto-generated
from commits by `claude-pack-release.yml`). The skill's release identity is its frontmatter
`metadata.version` in `SKILL.md`, verified at release time by `claude-pack/scripts/verify_skill_versions.py`.

Format: [keepachangelog.com](https://keepachangelog.com/en/1.1.0/). Versioning: [semver](https://semver.org/).

## [Unreleased]

## [2.2.0] — 2026-06-04

PO engagement-profile knobs. Additive + backward-compatible (13 → 15 preference keys; old
`preferences.yaml` files without the new keys resolve to the documented defaults).

### Added
- **2 engagement knobs in `preferences.yaml`** — `interview_rigor` (light / standard / **deep**) and
  `action_prompting` (minimal / standard / **proactive**), both default `standard` (neutral posture, no
  GATE-NEVER-ASSUME breach). `interview_rigor` sizes how hard the interview challenges claims + probes for
  gaps / edge cases / missing AC, at **all** interview levels (vision/BRD/PRD/epic/story);
  `action_prompting` sizes next-action density. Orthogonal to `detail_level` (verbosity vs rigor —
  "concise but deep" is expressible). Wired LLM-side in `workflow-interview.md` → *Engagement profile*.
- **`preferences.py --set KEY=VALUE` write-CLI** (repeatable) — the deterministic, PO-driven writer for
  the knobs. **load→merge→save**: preserves every other committed key (`save()` is a blind full-dict
  overwrite, so the merge is mandatory — a partial write would clobber unrelated keys). A value outside the
  key's closed enum — OR an **unknown key** — exits non-zero, writing nothing (no silent typo no-op); digit
  strings coerce to int for the int-typed keys (`critique_level`, `critique_drift_threshold`); splits on the
  FIRST `=` only.
- **End-of-session engagement forcing-function** — folded into the existing Closing-the-Loop batch (no new
  interrupt). When the live session shows real evidence, it proposes ONE bidirectional tighten/relax and,
  on PO confirm, persists via `--set`. No auto-write: the only writers are PO-typed `--set` or this
  PO-confirmed prompt.
- **Init-Flow seed** — a one-time strict-first-vs-neutral ask, combined into the existing `detail_level`
  Init-Flow `AskUserQuestion` batch when the total stays ≤4 questions.

### Changed
- **`preferences.py` schema** — `DEFAULTS`/`ENUMS` gain the 2 closed-enum keys (15 keys total). The
  defaults count guard moves 13 → 15.

### Documentation
- **Guide + README restructured** — `GUIDE-EN.md`/`GUIDE-VI.md` now lead with Core concepts, a Learning
  path, and Important caveats, then group the use cases into five approachability tiers (Build / Keep-healthy
  / Share / Tune / Governance-memory); the per-flag sample conversations are preserved. `README.md` rewritten
  into English + Tiếng Việt sections with a 6-must-knows quickstart and learning path. The engagement knobs
  are documented end-to-end (`workflow-interview.md` → Engagement profile, with EN/VI seed-question prose).

### Notes
- **Cut from this round** (red-team + validate): `standing_reminders` (privacy / prompt-injection),
  `--reflect engagement-profile` harvest (no deterministic anchor signal), and critique wiring (marginal
  value vs provenance-rebuild cost — deferred).

## [2.1.0] — 2026-06-04

Closing the PO pipeline (product-spec ↔ product-spec-critique). Additive + backward-compatible.

### Added
- **`--apply-critique <report>`** — the critique return-edge: consume a `product-spec-critique`
  report and walk each finding Keep / Change+re-approve / Defer, recording one `DEC-<n>` per resolved
  finding. Findings come from the structured lens-cache (not prose); the report path is read-fenced to
  `docs/product/critique/`; DEC writes are atomic (`decision_register --append-alloc`), resumable, and
  injection-sanitized; a Change on an `approved` artifact goes through GATE-NO-SILENT-REVERSAL with a
  deterministic fresh-re-approval guard. Scripts: `parse_critique_report.py`, `apply_critique_progress.py`.
- **`--viz audit`** — a read-only governance trail joining change-log · approvals · stale-approvals ·
  decision register into one chronological table, with explicit `unreconciled` rows for source
  disagreement. Renders `ascii` (default) · `md` · `html`; the HTML form escapes every dynamic field
  server-side (`render_html.audit`) guarded by a `bug_class` XSS test. Script: `assemble_audit_trail.py`.
- **`--summary --audience exec|release-notes`** — audience modifier on `--summary` (no new flag).
  `exec` = the current one-pager; `release-notes` = "what changed since the last approved snapshot" from
  the governance audit trail. New `release-notes` template.
- **`--discover <path(s)>`** — discovery seed: ingest raw upstream text (files AND directories) into
  candidate personas/problems/JTBD to seed the Vision interview. Read-fenced to the project root,
  `.md`/`.txt` only, dotfiles excluded, size-capped, bounded directory recursion. Never auto-commits.
  Script: `ingest_raw_inputs.py`.
- **`goal_without_metric` validation check** — a BRD goal with empty/missing `metrics` is an
  `error` (enforced by `strict_gate`).

### Changed
- **`_hashable()` consolidated** — the byte-identical copies in `render_ascii` and
  `render_ascii_board` now share one home in `render_common.py` (product-spec-internal; output unchanged).

## [2.0.0]

Current shipped baseline. History below reconstructed from `feat(product-spec)`/`fix(product-spec)`
commit subjects (not a raw path log), grouped by theme.

### Added
- Vision/BRD/PRD/Epic/Story hierarchy with parent-scoped IDs, traceability, and `--validate`
  (structural scripts + LLM judgment), `--approve`, `--summary`, `--export`, and the `--viz` view family.
- **Memory-write enforcement layer:** deterministic `memory_gap` detector (four signal types); Tier-0
  forcing-functions + a single enforcement reference home; unrecorded-memory signals + reflect hint
  surfaced in `--status`; opt-in Stop hook for memory-gap nudges; `install --memory-hook` registration.
- **`--reflect`** retroactive memory harvest + a read-only harvester agent.
- **`--voice`** flag to record PO style explicitly via `record_po_style`.
- Atomic batch-write path for the judgment cache (`--store-batch`).

### Changed
- Modularized oversized scripts into focused modules; shared test helpers through `conftest`;
  single-homed `FENCE_PREFIX` (via `check_fence` import) and the `last_judged` writer.
- Cross-platform memory-hook interpreter path + completed `install.sh` argument hints.
