---
phase: 8
title: "soft-fence-and-status-nudge"
status: pending
priority: P2
effort: "5h"
dependencies: []
---

# Phase 8: soft-fence-and-status-nudge

## Overview
Soft fence (F3 script path-assert + F2 advisory `check_fence.py`) and the `--status` pull-nudge. No hooks, no settings.json. **F1 prose** (the "skill only writes docs/product/" rule) is handled by **P3** (boundary guardrail).

**Split to break the fs_guard↔last_validated cycle (red-team RT-5):**
- **P8a (Wave 1, deps [])** — `fs_guard.py` + `check_fence.py` + path-assert wiring. Foundational; parallel-safe with P1 (distinct files). P5/P6/P7 import `fs_guard` (they run later, W4–W6), so it exists first.
- **P8b (Wave 6, gated on P6)** — `--status` + `references/workflow-status.md`. Reads the `last_validated.json` marker that **P6 writes** (P6 owns the validate-hub). Runs after P6 to avoid a dependency cycle (P6 needs P8a's `fs_guard`; P8b needs P6's marker).

## Requirements
- Functional:
  - **F3 path-assert (red-team RT-6 retarget):** a shared `fs_guard._assert_under_docs_product(path, root)` called at the REAL write chokepoints — `render_html._write_visual` (covers board/explorer/all HTML via `render_board.py:95`→here), `render_export.write_export` (`render_export.py:262`), `generate_templates.py` (`fh.write` ~line 463). **The 4 string-returning renderers (render_ascii/render_mermaid + board/explorer pre-delegation) do NOT write disk — do NOT guard them.** New memory writers (`decision_register.py` P5, `judgment_cache.py` P6, `behavioral_memory.py` P7) import `fs_guard` for their own writes.
  - **Honesty caveat (concrete):** the impact report at `docs/product/impact/<ts>.md` is written by the LLM composing a body directly (`workflow-validate.md:61`), NOT via a script → **NOT covered by F3** (only the prose F1 rule + advisory F2 apply there). Snapshot writes (`spec_graph.write_snapshot`) compute paths under `docs/product/` by construction (safe-by-path; P1-owned, not re-guarded here).
  - **F2 `check_fence.py`**: advisory pull script — scans `git status`/recently-touched files, reports files outside `docs/product/`. Advisory, never blocks. Feeds 3E (P7).
  - **`--status` nudge (N2) [P8b]**: pull flow listing unvalidated changes (snapshot delta since `last_validated.json` — **written by P6**, read-only here), drafts, overdue (reuse `time_advisory.py`), stale approvals. New `references/workflow-status.md`; SKILL.md `--status` row added by **P2** (P8b confirms accuracy).
- Non-functional: self-contained, 0 wiring; honesty — F2/F3 do NOT block raw LLM Write nor LLM-direct body writes (only script-path + advisory). All committed.

## Architecture
- F3: `_assert_under_docs_product(path, root)` lives in a **new `fs_guard.py`** (committed — NOT extending the widely-imported `encoding_utils.py`, to keep ownership clean). Called at the 3 real write chokepoints (see Requirements) + imported by the new memory writers.
- F2 `check_fence.py`: deterministic scan; emits JSON findings (files outside `docs/product/`). No LLM.
- `--status` [P8b]: composes `time_advisory.py` (overdue) + snapshot delta (unvalidated changes since the `last_validated.json` marker **P6 writes**) + draft count. Mostly an LLM-pull flow doc in `workflow-status.md`. P8b only READS the marker.

## Related Code Files
- Create: `scripts/fs_guard.py`, `scripts/check_fence.py`, `references/workflow-status.md`, `scripts/tests/test_check_fence.py`, `scripts/tests/test_fs_guard.py`, `scripts/tests/test_status.py`
- Modify (real write chokepoints ONLY): `scripts/render_html.py` (`_write_visual` ~1019-1026), `scripts/render_export.py` (`write_export` ~262), `scripts/generate_templates.py` (`fh.write` ~459-464)
- Do NOT modify (string-returning, no disk write): `render_ascii.py`, `render_mermaid.py`, `render_board.py`/`render_explorer.py` (delegate to `render_html._write_visual`)
- NOT owned here: SKILL.md `--status`/`--decision` rows (P2), CLAUDE.md F1 prose (P3), `last_validated.json` write (P6)

## Tests (write FIRST — TDD)
1. `test_path_assert_allows_under_docs_product` → write inside `docs/product/` ok.
2. `test_path_assert_blocks_escape` → resolved path outside (incl. `..` traversal / symlink) → friendly error, no write.
3. `test_check_fence_flags_outside` → a file outside `docs/product/` touched → reported.
4. `test_check_fence_clean` → only `docs/product/` touched → empty findings, exit 0.
5. `test_status_lists_unvalidated` **[P8b]** → with a `last_validated.json` fixture (the marker P6 writes), snapshot delta since that marker → unvalidated nodes listed; overdue via time_advisory. (No-marker → degrade gracefully to "no validation baseline yet", not "everything unvalidated".)
6. `test_path_assert_real_chokepoint` → calling `render_html._write_visual` / `render_export.write_export` / `generate_templates` with an out-of-tree target → blocked; in-tree → writes.
- Run existing renderer tests first (baseline) — path-assert must not break current in-tree writes.

## Implementation Steps
**P8a (W1):** 1. Write fence tests (red). 2. Implement `fs_guard._assert_under_docs_product`; call from the 3 real chokepoints (`render_html._write_visual`, `render_export.write_export`, `generate_templates` write). 3. Implement `check_fence.py`. 4. Fence tests green; renderer suite no regression.
**P8b (W6, after P6):** 5. Implement `--status` + `references/workflow-status.md`; reuse `time_advisory.py` + snapshot delta + the P6-written `last_validated.json` (read-only). 6. Confirm the SKILL.md `--status` row (P2-authored) matches the shipped output. 7. Status test green.

## Success Criteria
- [ ] Path-assert blocks out-of-tree writes (incl. traversal) with friendly error; in-tree writes unaffected.
- [ ] `check_fence.py` reports outside-`docs/product/` touches; clean run = empty/exit 0.
- [ ] `--status` lists unvalidated changes + drafts + overdue; documented.
- [ ] Honesty caveat (no raw-LLM-write block) stated in workflow-status.md / fence docs.

## Risk Assessment
- Path-assert false-positive on legit writes → comprehensive renderer test baseline.
- F2 illusion of safety → explicit honesty caveat (only script-path + advisory).
- Parallel-safe with P1 (Wave 1): distinct files (no spec_graph.py / workflow-validate.md edits here).
