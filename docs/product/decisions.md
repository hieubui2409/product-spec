# Decision Register

---
id: DEC-1
status: active
date: 2026-06-12
affects: decision_register.py
---

## DEC-1 — Add decision-register-view sibling for affects-filter and supersede-chain presentation

The decision_register.py file is at 401 LOC (over the 250-LOC module budget). A dedicated view sibling keeps the main register flat: filter_by_affects, render_supersede_chain (cycle-safe, dangling-soft), render_dashboard_row, render_dashboard_summary. The --list --affects PRD-X dispatch adds ~6 LOC to the main file. Reuses parse_decisions() as the single DEC loader (DRY).

---
id: DEC-2
status: active
date: 2026-06-12
affects: visuals_retention.py, render_html.py, visualize.py
---

## DEC-2 — Build visuals-retention as a new sibling module; retention keep=5

visualize.py is at 500 LOC (over the 250-LOC module budget). New logic lands in visuals_retention.py sibling, keeping visualize.py + render_html.py growth to ~16 wiring lines total (no re-implementation of HTML rendering).

Retention hard count: keep=5 most recent timestamped renders per view. Chosen as a reasonable balance between audit trail (5 history points) and disk footprint (prevents unbounded accumulation). Constant is RETENTION_KEEP in visuals_retention.py — single authoritative source.

Alias is copy-based rather than symlink: Python symlinks are unsupported on some filesystems (FAT32, some Windows mounts) and require elevated permissions on others. A copy is universally portable and the file sizes are small (self-contained HTML, typically <1MB).

Missing sidecar (hash or signature) is treated as "changed": safe default that forces a fresh render rather than silently reusing stale output. Sidecars live in docs/product/visuals/.hashes/ and docs/product/visuals/.signatures/ alongside the renders they describe.

---
id: DEC-3
status: active
date: 2026-06-12
affects: snapshot.py, status_vcs.py, status.py
---

## DEC-3 — Snapshot is opt-in only for 2.4.0; auto-hook before migration deferred

Owner decision (plan.md, red-team H2): snapshot/restore ships as an explicitly invoked CLI operation only. No automatic snapshot call is wired into migrate_backfill_ids.py, migrate_metric_to_metrics.py, or any approve/update path. The auto-before-migrate convenience hook is deferred — it can be added later in the phase that owns the migrator, avoiding the P2/P5 file-ownership collision that motivated the deferral.

VCS-warn thresholds chosen as hard integers (LARGE_DIFF_FILE_COUNT = 5 in status_vcs.py): 5 uncommitted files in the spec tree is a concrete, reviewable signal without being too sensitive for routine editing. The threshold constant is the single authoritative source; changing it is a one-line edit.

Snapshots home: .product-spec-snapshots/ at the project root, gitignored. Chosen over a nested docs/product/.snapshots/ to keep the spec artifact tree clean and to avoid confusion with the existing visuals/.snapshots/ (which stores JSON graph snapshots for --validate baseline, a different purpose). The gitignore entry prevents a repeat of the 88-file backup-leak anti-pattern.

---
id: DEC-4
status: active
date: 2026-06-12
affects: track_artifact_edits.py, lens_artifact_heat.py, register_telemetry_hooks.py
---

## DEC-4 — Artifact-event hook uses whitelist construction for privacy; sink name is artifact-events.jsonl

Privacy-by-construction for the artifact-edit hook (GATE H3): `_build_record` is a pure function that receives only the three pre-extracted values (path, op, session) and builds the record dict by explicit assignment of 4 keys. It never receives the tool payload, so new_string/old_string/tool_response fields cannot leak regardless of future payload changes. A blacklist approach (strip known content keys) would be weaker — a new payload field could slip through.

Sink name `artifact-events.jsonl` (not `artifact_edits.jsonl` or `artifact-edit-events.jsonl`) chosen to be consistent with the existing kebab-case sink names (hook-telemetry.jsonl, subagent-outcomes.jsonl, sessions.jsonl, invocations.jsonl) and to clearly describe the event category rather than the operation name.

Registration appended to the existing `PostToolUse:Edit|Write|MultiEdit` group in REGISTRATIONS (not a new group) so the matcher string is defined exactly once — avoids a second identical-matcher group that the settings reconciler would treat as separate entries.

---
id: DEC-5
status: active
date: 2026-06-12
affects: harvester.py, analyze_telemetry.py, telemetry_render.py
---

## DEC-5 — Harvester is read-only by construction; opt-in flag gates the suggestions section

Boundary A9 (non-negotiable): the harvester must never write to any skill/template/SKILL.md and must
never self-evolve the kit. This is enforced by construction rather than by a runtime check: `harvester.py`
opens files only via read-mode `open()` calls; it has no `open(..., 'w')`, `Path.write_text()`,
`Path.write_bytes()`, or any other write-mode path anywhere in the module. The boundary-A9 test
(`test_harvester_never_writes_anything`) monkeypatches builtin `open` to raise on write-mode AND patches
`Path.write_text`/`Path.write_bytes` to raise — a stronger guard than mtime-diffing (catches writes to
any path, including paths outside `.claude/skills/`).

Opt-in gate: `--auto-suggest` is a store_true flag (absent by default). When absent, no suggestions
section is appended to stdout or to the export file — the output is identical to a normal `--lens` run.
This prevents surprise suggestions content in automated pipelines. When present, suggestions are appended
as a markdown section that the PO reads before deciding whether to act. No auto-send path exists.

Default export path (`.claude/telemetry/usage-summary.md`) lands in the gitignored telemetry dir so
the exported summary is never accidentally committed alongside spec artifacts.
