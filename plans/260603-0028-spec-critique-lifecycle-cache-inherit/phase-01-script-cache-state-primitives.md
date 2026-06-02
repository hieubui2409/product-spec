---
phase: 1
title: "Script: cache+state primitives"
status: pending
priority: P1
effort: "1d"
dependencies: []
---

# Phase 1: Script — cache + state primitives

## Overview

Create the deterministic data layer that the rest of the plan builds on: a new module `critique_cache.py` holding the 4 PO-adopted caches + the per-scope freshness marker. Pure read/write JSON through the `fs_guard` fence. No bundle wiring yet (that is P2/P3) — this phase delivers tested primitives in isolation.

## Requirements

- Functional:
  - **Findings-index** (`docs/product/.memory/critique-findings-index.json`): `upsert_findings(root, report_ts, scope, findings)` + `load_index(root)`. Keyed by `evidence-ID`; each entry `{evidence_id, severity, why, fix, dec_worthy, report_ts, scope}`. Last-write-wins per `(evidence_id, report_ts)`. This is the query cache that feeds inherit + repeat-offense (P3) so a classify pass reads JSON instead of parsing N markdown reports.
  - **Web-url cache + TTL** (`docs/product/.memory/web-cache/<url-hash>.json`): `get_cached(root, url, ttl_days=14)` → content or `None` if missing/expired; `put_cached(root, url, content)` stamps `fetched_at`. `<url-hash>` = sha256(url)[:16]. TTL default 14 days (brainstorm value).
  - **Critique-state marker** (`docs/product/.memory/critique-state.json`): `load_state(root)` / `save_state(root, scope, **fields)`. Per-scope record `{scope: {last_ts, provenance_hash, blocker_count, drift_since}}`. Modeled on product-spec's `last_validated.json`. Feeds `--status` + freshness (P2/P4).
  - **Humanized-output cache** (`docs/product/.memory/humanized-cache.json`): `get_humanized(root, consolidated_hash)` / `put_humanized(root, consolidated_hash, text)`. Key = sha256 of the consolidated markdown. Reuse when consolidated output is unchanged (changing nothing re-humanizes).
  - **Lens-findings cache** (`docs/product/.memory/critique-lens-cache/<lens_findings_hash>.json`) — **R1, the store that makes `consolidate_only` real**: `get_lens_findings(root, lens_findings_hash)` / `put_lens_findings(root, lens_findings_hash, findings)`. Stores the **FULL** lens-findings array `[{lens, evidence, critique, why_it_dies, fix, severity, source?}, ...]` verbatim — NOT the lossy index subset. `<lens_findings_hash>` = sha256(canonical-json(findings))[:16]. This is what a re-consolidate-at-new-level loads to re-render voice without re-running lenses. Distinct from the findings-index (evidence-ID query cache, blockers+DEC only): two caches, two keys, never conflated.
- Non-functional:
  - All writes go through `fs_guard.assert_under_docs_product(path, root)` BEFORE writing (the memory dir is already under the fence).
  - Tolerant reads: missing/corrupt file → return empty/`None`, never raise (mirror `judgment_cache.load_cache`, `preferences.load`).
  - Deterministic: same inputs → same file bytes (sorted keys, stable separators, no wall-clock except the explicit `fetched_at`/`last_ts` stamps passed in by caller — accept an injectable `now_iso` arg so tests pin time).
  - Keep `critique_cache.py` < 200 LOC; if it grows past, split web-cache into `critique_web_cache.py`.

## Architecture

```
critique_cache.py  (new, ~200 LOC — if it exceeds, split web-cache + lens-cache into critique_web_cache.py)
├── _memory_dir(root) -> Path                 # docs/product/.memory, fenced
├── findings-index:   load_index / upsert_findings        # evidence-ID query cache (lossy: blockers+DEC)
├── web-cache:        get_cached / put_cached / _url_hash  # committed (PO: .memory/ convention)
├── critique-state:   load_state / save_state             # per-scope provenance fast-path marker
├── humanized-cache:  get_humanized / put_humanized        # committed (regenerable)
└── lens-cache:       get_lens_findings / put_lens_findings  # FULL lens arrays (R1) — feeds consolidate_only
```

Reuse, do NOT reinvent: import `fs_guard` via the same `_import_psp()` path `critique_scan.py` already uses (`../../product-spec/scripts`). Time is injected (`now_iso: str` param) so tests are deterministic and we never call a bare `datetime.now()` inside the cache (matches the brainstorm + harness determinism contract).

**Git policy (R3 — corrects the earlier false "all gitignored" claim):** `docs/product/.memory/` IS committed in this repo (verified: e2e `.memory/` is tracked). **PO decision (2026-06-03): commit ALL 5 caches** (index/state/lens-cache/web-cache/humanized-cache) following that convention — this phase adds NO `.gitignore` rule. The web-cache-holds-third-party-content trade-off was surfaced; the PO chose commit-all for consistency. Just correct any prose that called these "gitignored runtime data" — they are committed by design.

## Related Code Files

- Create: `.claude/skills/spec-critique/scripts/critique_cache.py`
- Create: `.claude/skills/spec-critique/scripts/tests/test_critique_cache.py`
- (No `.gitignore` edit — PO chose to commit all caches per the `.memory/` convention.)
- Read for context: `.claude/skills/spec-critique/scripts/critique_scan.py` (`_import_psp`, `_now`, `write_snapshot` fence pattern), `.claude/skills/product-spec/scripts/fs_guard.py`, `.../judgment_cache.py` (tolerant-read pattern), `.../preferences.py`
- Read for test pattern: `.claude/skills/spec-critique/scripts/tests/critique_test_support.py`, `conftest.py`

## Implementation Steps (TDD — tests first)

1. **Write `test_critique_cache.py` first** (red). Cases:
   - findings-index: upsert then load returns the entry; second upsert same `(id, ts)` overwrites; different ts coexist; corrupt JSON → `load_index` returns `{}`.
   - web-cache: `put_cached` then `get_cached` within TTL returns content; pinned `now_iso` past TTL → `None`; unknown url → `None`; url-hash stable for same url.
   - critique-state: `save_state(scope=…)` then `load_state` round-trips; two scopes independent; missing file → `{}`.
   - humanized-cache: put/get round-trip; unknown hash → `None`.
   - lens-cache: put a full `[{lens,evidence,critique,why_it_dies,fix,severity,source}]` array, get it back BYTE-faithful (no field dropped); hash stable for same array; unknown hash → `None`.
   - fence: monkeypatch a root and assert a write path resolves under `docs/product/.memory` (no escape).
2. Implement `_memory_dir` + the five cache groups to green the tests (no `.gitignore` edit — all caches committed per PO).
3. Confirm determinism: write twice with same pinned `now_iso`, assert byte-identical files.
4. Run `./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/spec-critique/scripts/tests/test_critique_cache.py -q` → all green.

## Success Criteria

- [ ] `test_critique_cache.py` passes (all FIVE groups green, incl. lens-cache byte-faithful round-trip) under the shared venv.
- [ ] `critique_cache.py` ≤ ~200 LOC (split if exceeded), no bare `datetime.now()` inside cache logic (time injected).
- [ ] All writes fenced via `fs_guard`; corrupt/missing reads degrade to empty, never raise.
- [ ] Byte-determinism test passes (same pinned time → identical bytes).
- [ ] All 5 caches committed per `.memory/` convention (PO decision); NO `.gitignore` edit; prose no longer calls them "gitignored".
- [ ] No change to `critique_scan.py` yet (primitives only; wiring is P2/P3).

## Risk Assessment

- **Risk: web-cache dir proliferation + third-party content committed** (one file per URL, scraped page text). PO chose commit-all (R3), so scraped content DOES enter git — accepted trade-off for `.memory/` consistency. Mitigation: `<url-hash>.json` flat under `web-cache/`; keep entries small (store only what the market lens needs, not whole pages, if feasible); a future `--prune-web-cache` only if bloat bites (YAGNI now).
- **Risk: lens-cache fan-out** (one file per distinct lens run). Mitigation: keyed by `<lens_findings_hash>` so identical runs collapse; committed under `.memory/` like other markers. Acceptable; prune is YAGNI.
- **Risk: schema drift between the 4 JSON files and later phases.** Mitigation: each loader returns a plain dict with documented keys; P3 imports the loaders, never re-opens the files by hand.
- **Risk: duplicating `last_critique.json`.** Mitigation: `critique-state.json` is a per-scope *index* marker (last_ts/provenance/counts), NOT the per-node body_hash snapshot — they are distinct homes. Note this in the module docstring.
