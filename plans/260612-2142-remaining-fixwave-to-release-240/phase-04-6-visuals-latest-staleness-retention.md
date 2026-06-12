---
phase: 4
title: '#6 visuals latest + staleness retention'
status: completed
priority: P2
effort: 1.5-2d
dependencies: []
---

# Phase 4: #6 visuals latest + staleness retention (POX-F04/CVR-M3/BUG-F07)

## Overview
Stop visuals from freezing into stale, ever-accumulating HTML files committed to GitHub. Add a stable
`*-latest.html` alias, a staleness banner ("rendered at X, spec drifted N nodes"), content-hash reuse (no new
file when output unchanged), and `--viz --clean` (purge old, keep latest). New **sibling** `visuals_retention.py`
keeps `visualize.py` (500 LOC) from growing.

## Requirements
- Functional: (1) after each render, maintain `<view>-latest.html` → newest `<view>-<ts>.html`; (2) inject a banner
  computing `drifted = len(changed_nodes + added + removed)` vs baseline (reuse `spec_graph.changed_nodes`/`diff_graphs`);
  (3) content-hash: sha256 of rendered HTML; if equal to last render, skip write, return existing path; (4) `--clean`:
  delete old renders per view, keep latest alias target + newest; (5) post-approve re-render nudge (in approve flow, thin call).
- Non-functional: deterministic; no new file on identical content (byte-stable). `--clean` never deletes the latest target.

## Architecture
- New `visuals_retention.py`:
  - `latest_alias(out_path) -> Path` (write/refresh `<view>-latest.html`; symlink, or copy on platforms w/o symlink)
  - `content_hash(html) -> str` + `reuse_if_unchanged(root, view, html) -> Optional[Path]` (sidecar `.hashes/<view>`)
  - `staleness_banner(graph, baseline) -> str` (drifted N nodes; empty when 0)
  - `clean_old_renders(root, keep_latest=True) -> List[Path]` (returns deleted)
- `visualize.py` / `render_html.write()`: call `reuse_if_unchanged` before mkdir/write; after write call `latest_alias`;
  inject `staleness_banner` into the page wrapper; add `--clean` CLI flag dispatching to `clean_old_renders`.

## Related Code Files
- Create: `.claude/skills/product-spec/scripts/visuals_retention.py`
- Modify: `.claude/skills/product-spec/scripts/visualize.py` (CLI `--clean`, banner+alias+reuse wiring — thin calls)
- Modify: `.claude/skills/product-spec/scripts/render_html.py` (hook reuse/alias into `write()` — already split P12)
- Create: `.claude/skills/product-spec/scripts/tests/test_visuals_retention.py`
- Modify: REVIEW.md (tick POX-F04), EVIDENCE.md, DEC

## TDD — tests first
1. `test_identical_content_no_new_file` — render twice unchanged → exactly 1 timestamped file (count==1), reuse path returned.
2. `test_latest_alias_points_to_newest` — render v1 then v2 (changed) → `<view>-latest.html` resolves to v2.
3. `test_staleness_banner_reports_drift` — render, then mutate spec → banner text contains drift count == len(changed+added+removed).
4. `test_banner_absent_when_fresh` (negative) — no drift → no banner / "0".
5. `test_clean_keeps_latest_removes_old` — 3 old renders + clean → only newest+alias remain; deleted list == the rest.
6. `test_clean_never_deletes_latest_target` (negative/no-over-fix) — alias target survives `--clean`.
Fixtures: existing `VALID` valid-spec; mutate via conftest `append_to`.

## Implementation Steps
1. Write 6 RED tests.
2. Implement `visuals_retention.py`.
3. Wire reuse/alias/banner into render path; add `--clean` flag.
4. Add post-approve re-render nudge (thin pointer in approve workflow — no heavy logic).
5. GREEN; product-spec suite + CONTRIBUTING:69.
6. Tick POX-F04; DEC + EVIDENCE.

## Success Criteria
- [ ] 6 tests green incl. 2 negatives; identical content → 0 new file (count assertion).
- [ ] `*-latest.html` always resolves to newest; banner shows hard drift count.
- [ ] `--clean` keeps latest, removes the rest.
- [ ] POX-F04 ticked; DEC + EVIDENCE.

## Risk Assessment
- Symlink unsupported on some FS → fall back to copy for alias; test both paths via a copy-mode flag.
- Hash sidecar drift → store hash alongside file; missing sidecar → treat as changed (safe: writes).
- `--clean` data loss → keep-latest guard + dry-run list returned before unlink in tests.
