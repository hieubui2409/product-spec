---
phase: 1
title: "Scripts & preferences"
status: pending
priority: P1
effort: "1d"
dependencies: []
---

# Phase 1: Scripts & preferences

## Overview

Build the deterministic core: `critique_scan.py` — a thin (reuse-first) orchestration script that assembles ONE JSON bundle the lens agents consume — plus a `critique_drift_threshold` key in product-spec's `preferences.py`. NO LLM, NO re-analysis: it gathers existing `--validate` findings + judgment-cache verdicts + ancestry context + competitors + prior critique reports, and manages the `last_critique.json` body_hash snapshot. Always exits 0 (advisory).

## Requirements

- **Functional:** given `--root` + `--scope <id|all>`, emit a JSON bundle with: resolved scope target(s), ancestry chain (story→epic→PRD→BRD→vision), structural findings (`check_traceability` + `check_consistency`), cached verdicts (`judgment_cache`), assembled artifact digest (`assemble_digest`, incl. Vision/BRD/PRODUCT singletons), BRD `competitors:`, prior critique report list (repeat-offense), and the drift threshold from preferences. Also a `--snapshot` mode that writes `last_critique.json` (per-node body_hash) and a `--drift` mode that counts body_hash changes vs that marker.
- **Non-functional:** deterministic, stdlib+pyyaml only, exit 0 always (malformed input → `parse_error` field, never crash). All writes pass `fs_guard.assert_under_docs_product`. Runs via shared venv `./.claude/skills/.venv/bin/python3`. Lives under `.claude/skills/spec-critique/scripts/`.

## Architecture

- **Reuse from `product-spec/scripts/`:** `spec_graph` (`build_graph_with_artifacts(root)` for graph+artifacts; `ancestors(graph, id)` → goal/PRD/epic; per-node `body_hash` sha256[:8], goals = `None`; `write_snapshot`/`changed_nodes`), `assemble_digest.build_digest(graph, artifacts, select="all", layers=None, depth="context")` (already walks `_closure` for full ancestry + prepends vision/PRODUCT/BRD as `role=ancestor` singletons), `check_traceability`/`check_consistency` (findings — **subprocess**, stable CLI), `judgment_cache.load_cache(root)` (whole dict; filter by node-id prefix; may be `None` → treat as empty), `preferences`, `fs_guard`, `frontmatter_parser` (BRD competitors).
- **Cross-dir import (CRITICAL — corrected):** `critique_scan.py` lives in a DIFFERENT dir than product-spec scripts, so **bare sibling imports fail**. Copy the `memory_gap_hook._import_*` pattern: a `_psp_dir()` helper resolves `../product-spec/scripts` relative to `__file__`, `sys.path.insert(0, that)`, then import (with a loud error if absent). Use **subprocess** for `check_traceability`/`check_consistency` (avoids the transitive import chain `spec_graph→encoding_utils/status/judgment_cache/decision_register`); import only the pure helpers (`spec_graph`, `assemble_digest`, `judgment_cache.load_cache`, `preferences`, `fs_guard`, `frontmatter_parser`).
- **Ancestry:** use `assemble_digest.build_digest` (gives the full closure incl. ancestors). For the explicit `ancestry` field use `spec_graph.ancestors(graph, id)` (goal/PRD/epic) PLUS the vision/BRD singletons from the digest (NOTE: vision + BRD container are NOT graph nodes — pull them from the digest, not `ancestors()`). For `--scope all`, target = whole tree.
- **Bundle schema (the contract P2/P4 depend on — versioned):**
  ```jsonc
  {
    "bundle_version": 1,
    "scope": "PRD-AUTH-E1-S1" | "all",
    "lang": "vi",
    "target_ids": ["..."],
    "ancestry": { "vision": {...}, "brd_goals": [...], "prd": {...}, "epic": {...} },
    "digest": { /* assemble_digest model */ },
    "structural_findings": [ {check, severity, artifact_id, file, detail, context} ], // real make_finding shape (spec_graph.py)
    "cached_verdicts": [ {key, check, verdict, ...} ],   // load_cache filtered by scope prefix
    "competitors": [ ... ],            // from BRD competitors:
    "prior_reports": [ {path, ts, scope} ],   // docs/product/critique/*.md
    "drift_threshold": 3,
    "parse_errors": []
  }
  ```
- **`last_critique.json`:** `{ "critiqued_at": "<ISO>", "scope": "...", "body_hash": { "<node-id>": "<hash8>", ... } }`. Two drift modes, both **skip nodes with `body_hash: None` (goals)** and return `{changed_count, changed_ids, threshold, over}`:
  - `--drift` (default, manual): build_graph live, compare current per-node body_hash vs `last_critique.json`.
  - `--drift --vs-validated` (used by the hook, cheap): take the validate-time per-node body_hash from `judgments.json` keys (`check|scope|body_hash|lang|dep_hash` — body_hash is embedded per scope) vs `last_critique.json`; no live build_graph unless judgments.json is absent (then fall back to one build). This is what lets the Stop hook avoid scanning the tree every stop.

## Related Code Files

- Create: `.claude/skills/spec-critique/scripts/critique_scan.py`
- Create: `.claude/skills/spec-critique/scripts/tests/test_critique_scan.py`
- Create: `.claude/skills/spec-critique/scripts/tests/fixtures/` (minimal docs/product tree — or reuse product-spec test fixtures via copytree)
- Modify: `.claude/skills/product-spec/scripts/preferences.py` (add `critique_drift_threshold: 3` to DEFAULTS; non-enum branch — `load()` won't int-validate, so critique_scan coerces `int(...)` defensively on read)
- Create: `.claude/skills/product-spec/scripts/tests/test_preferences.py` (does NOT exist yet — cover existing defaults + new `critique_drift_threshold`)

## Implementation Steps

1. Confirm exact APIs from `researcher-260602-0224-spec-critique-skill-scripts-conventions-report.md`: `spec_graph` ancestry/body_hash, `assemble_digest.build_digest` signature, `check_*` invocation + finding shape, `judgment_cache` read, `preferences.load/save` + DEFAULTS location, `fs_guard.assert_under_docs_product`.
2. Add `critique_drift_threshold: 3` to `preferences.DEFAULTS`; verify `load()` returns it; add test.
3. Implement `critique_scan.py` arg parsing: `--root` (default CWD), `--scope` (default `all`), `--lang`, `--snapshot`, `--drift`. Default mode = emit bundle.
4. Implement scope resolution + ancestry walk via `spec_graph`.
5. Gather structural findings (subprocess or import) + cached verdicts + digest + competitors + prior `critique/` report list.
6. Assemble + print bundle JSON (stable key order). Wrap `--snapshot` write through `fs_guard`.
7. Implement `--drift` (live build_graph) + `--drift --vs-validated` (validate-time hashes from `judgments.json` vs `last_critique.json`, fallback to one build if cache absent); diff, emit `{changed_count,...,over}`.
8. Tests: bundle **exact top-level key set** (incl. `bundle_version`); finding-shape element keys `{check,severity,artifact_id,file,detail,context}`; ancestry correctness for a deep story; drift count after mutating one node (+ goals with `body_hash:None` skipped); missing-marker drift → `over:false`/first-run sentinel; `load_cache` None-tolerant; malformed artifact → `parse_error`, exit 0; fence rejects out-of-tree write.
9. Run: `./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/spec-critique/scripts/tests/ -q` → green.

## Success Criteria

- [ ] `critique_scan.py --root <fixture> --scope <story-id>` emits bundle with correct ancestry + structural findings + digest, exit 0.
- [ ] `--snapshot` writes `last_critique.json` through `fs_guard`; out-of-tree path raises `FenceError`.
- [ ] `--drift` returns `changed_count`/`over` correctly after a single-node body edit; missing marker handled (no crash).
- [ ] `preferences.load()` returns `critique_drift_threshold=3` by default; PO override respected.
- [ ] Malformed frontmatter → `parse_errors` populated, still exit 0.
- [ ] All new + touched tests pass; no product-spec test regressions.

## Risk Assessment

- **Cross-import fragility (product-spec scripts):** subprocess for `check_*` (stable CLI); import only pure helpers via the `_psp_dir()`+`sys.path.insert` helper (resolves `../product-spec/scripts`), loud error if absent. Confirmed: bare sibling import would `ModuleNotFoundError` (critique_scan is in a different dir).
- **assemble_digest DOES give ancestry** (red-team confirmed `build_digest` walks `_closure` + prepends vision/PRODUCT/BRD singletons; signature `build_digest(graph, artifacts, select, layers, depth)`, needs `build_graph_with_artifacts`). The earlier "may not give ancestry" hedge is dropped.
- **body_hash semantics:** goals = `None` (skip in drift); cosmetic edits flip the hash (false-positive toward threshold) — mitigated by threshold ≥3 + the hook's trigger refinement (Phase 3). Document.
