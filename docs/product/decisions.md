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
