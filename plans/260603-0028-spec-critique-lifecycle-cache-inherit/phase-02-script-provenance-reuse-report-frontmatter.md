---
phase: 2
title: "Script: provenance reuse + report frontmatter"
status: pending
priority: P1
effort: "1d"
dependencies: [1]
---

# Phase 2: Script — provenance reuse + report frontmatter

## Overview

Make a critique report self-describing so the next run can decide what to reuse. Add YAML frontmatter to critique reports (per-node `body_hash` map + level/lang/register + lens-findings ref), teach `_prior_reports` to read it (fallback to filename), and add the provenance-diff that drives the three reuse outcomes. Add the `--fresh`/`--force` bypass. This is the **economic** gate (token savings), not a safety gate — default ON.

## Requirements

- Functional:
  - **Report frontmatter contract** (NEW — reports today have none, they open with `# Critique: …`). Frontmatter carries:
    ```yaml
    ---
    critique_scope: all | <node-id>
    level: 5
    lang: vi | en
    register: {gender: m, dialect: bac, profanity: strong}   # only when level >= 7, else omitted
    body_hash: {NODE-ID: 8hex, ...}    # per in-scope node, reusing _live_body_hashes
    lens_findings_hash: 16hex          # hash of the lens findings array, ties report to a lens run
    bundle_version: 2
    ---
    ```
    The existing `# Critique: <scope> · level N · lenses:` H1 line stays directly under the frontmatter (human header).
  - **`build_report_frontmatter(root, scope, level, lang, register, lens_findings_hash)` in `critique_scan.py`** → returns the YAML block string. Reuses `_live_body_hashes` (already present) for `body_hash`; does NOT recompute. Carries `lens_findings_hash` (the KEY into the P1 lens-cache that holds the full array — the array itself is stored there by R1, NOT inlined into the report).
  - **`_prior_reports` upgrade:** parse frontmatter when present → richer record `{path, ts, critique_scope, level, lang, body_hash, lens_findings_hash}`; when absent (old fixtures) fall back to filename-derived `{path, ts, scope: None, body_hash: None}` — **do NOT trust the filename for scope** (R4: `partition("-")` mangles real names like `c1-all-lvl3`→`all-lvl3`, `c10-PRD-MATCH-E1-S1-lvl6`). Never crash on malformed frontmatter.
  - **Provenance diff** `compute_provenance_reuse(root, scope, level, lang)` — **scope match uses frontmatter `critique_scope` ONLY** (R4); a filename-only prior is unusable → `none`. Fast-path (R5): consult `critique-state.json`'s `provenance_hash` for the scope before opening the prior report; on hash match skip the file read. Returns one of:
    - `{"reuse": "none"}` — no frontmatter-bearing same-scope prior, or `--fresh`/`--force`, or malformed/filename-only prior.
    - `{"reuse": "consolidate_only", "report": <path>, "lens_findings_hash": …}` — prior frontmatter report exists, `body_hash` map identical (drift=0) but level/lang differs → re-consolidate from the **lens-cache array** keyed by `lens_findings_hash` (P1/R1), do NOT re-lens. (If that lens-cache file is missing → degrade to `relens`, never to a broken reuse.)
    - `{"reuse": "full", "report": <path>}` — drift=0 AND level/lang/register identical → report already current (caller may just point at it).
    - `{"reuse": "relens", "changed_ids": [...]}` — some node `body_hash` changed. Whether re-lens is per-node or whole-scope is decided in P4 against the lens-cache availability (see P4); `changed_ids` is the signal either way.
  - **New CLI flags:** `--fresh` (alias `--force`) on `critique_scan.py` → forces `reuse: none`. Surface in bundle as `provenance: {...}` so the orchestrator (P4) can branch.
  - On a real run, write `critique-state.json` (P1) for the scope: `last_ts`, `provenance_hash` (= hash of body_hash map), `blocker_count`, `drift_since=0`.
- Non-functional:
  - Drift reuses `_diff_hashes` / `_live_body_hashes` already in `critique_scan.py` — no second hashing path (DRY).
  - Everything exits 0 (advisory); provenance never blocks.
  - Frontmatter parse uses the same YAML lib already imported (pyyaml via product-spec); fall back gracefully if a report has a `#`-first body and no `---`.

## Architecture

```
critique_scan.py (modify)
├── build_report_frontmatter(...)         # NEW — emit YAML block (reuses _live_body_hashes)
├── _prior_reports(root)                  # UPGRADE — parse frontmatter, fallback filename
├── compute_provenance_reuse(root, scope, level, lang)  # NEW — the 4-way decision
├── emit_bundle(...)                       # add bundle["provenance"] = compute_provenance_reuse(...)
└── argparse: --fresh / --force            # NEW
```

The decision lives in the Script half; the orchestrator (P4) only *reads* `bundle["provenance"]["reuse"]` and branches. Per Script-vs-LLM split, the script never decides voice — only what is reusable.

## Related Code Files

- Modify: `.claude/skills/spec-critique/scripts/critique_scan.py` (`_prior_reports`, `emit_bundle`, argparse, +2 new funcs)
- Modify: `.claude/skills/spec-critique/scripts/tests/test_critique_scan.py` (provenance + frontmatter cases)
- Read for context: P1 `critique_cache.py` (`save_state`/`load_state`), `_live_body_hashes`/`_diff_hashes`/`write_snapshot` in `critique_scan.py`

## Implementation Steps (TDD — tests first)

1. **Tests first** (red), extending `test_critique_scan.py` via `make_proj`/`run_scan`:
   - frontmatter round-trip: `build_report_frontmatter` output parses back to the same dict; `register` omitted when level < 7.
   - `_prior_reports` reads a frontmatter report → returns `body_hash`; reads an old no-frontmatter fixture → falls back, `body_hash is None`, no crash.
   - provenance `none`: no prior report → `reuse: none`; with `--fresh` even when a prior exists → `none`; a **filename-only** prior named `c1-all-lvl3.md` MUST degrade to `none` (R4 — assert it does NOT false-match `scope="all-lvl3"`).
   - provenance `consolidate_only`: seed a prior report (frontmatter) with identical body_hash but level 3 AND seed the matching P1 lens-cache file; run at level 7 → `consolidate_only` + prior path + the `lens_findings_hash`. Then assert: lens-cache file MISSING → degrades to `relens`, never a broken reuse.
   - fast-path (R5): with `critique-state.json` `provenance_hash` matching, the decision is reached without reading the prior report body (assert via a spy/monkeypatch that the report file is not opened).
   - provenance `full`: identical body_hash AND identical level/lang → `full`.
   - provenance `relens`: mutate one node body via `append_to` → `relens` with exactly that `changed_ids`.
   - `critique-state.json` written with `last_ts`/`provenance_hash`/`blocker_count`.
2. Implement `build_report_frontmatter`, upgrade `_prior_reports`, add `compute_provenance_reuse` (frontmatter-scope-only + critique-state fast-path + lens-cache-missing→relens degrade), wire `bundle["provenance"]` + `--fresh/--force`. When adding the `provenance` bundle key, **widen the existing bundle-shape test to a subset assertion** (it currently asserts an exact key set — confirm by reading `test_critique_scan.py` first) so P3 can add more keys without re-breaking it.
3. Keep `critique_scan.py` from ballooning: if the provenance block pushes the file well past ~560 LOC, extract `build_report_frontmatter` + `compute_provenance_reuse` into `critique_provenance.py` (decide during impl; note it in the phase report).
4. Run the critique_scan test module → green; run the full spec-critique pytest to confirm no regression in existing bundle-shape tests.

## Success Criteria

- [ ] All new provenance/frontmatter tests green; existing `test_critique_scan.py` still green (bundle keys updated to include `provenance`).
- [ ] `bundle["provenance"]["reuse"]` returns the correct verdict across none/full/consolidate_only/relens; scope matched from frontmatter `critique_scope` only (R4); filename-only prior → `none`.
- [ ] `consolidate_only` carries `lens_findings_hash`; lens-cache-missing degrades to `relens` (never broken reuse).
- [ ] `critique-state.json` `provenance_hash` fast-path avoids the prior-report read on a hash match (R5 — asserted).
- [ ] `--fresh`/`--force` forces `none`.
- [ ] Old no-frontmatter fixtures parse without crashing; `c1-all-lvl3.md`-style name degrades to `none`, NOT a false scope match.
- [ ] `critique-state.json` updated on a run; no second hashing path (reuses `_live_body_hashes`).

## Risk Assessment

- **Risk: frontmatter changes the report format → existing e2e fixtures lack it.** Mitigation: fallback-to-filename keeps old reports valid; new fixtures (P5) get frontmatter. Provenance simply misses on old reports (re-lens) — safe.
- **Risk (was a BLOCKER, now resolved by R1): `consolidate_only` reuse needs the FULL prior lens findings, but the report stores prose and the findings-index is a lossy blockers+DEC subset.** Mitigation: the full lens-findings array lives in the dedicated **lens-cache** `critique-lens-cache/<lens_findings_hash>.json` (P1/R1), written at step-6 (P4). `compute_provenance_reuse` records the `lens_findings_hash`; P4's `consolidate_only` loads the array from the lens-cache (NOT the index, NOT the prose). If the lens-cache file is absent (e.g. an old report), the verdict degrades to `relens` — never a silent half-reuse. The findings-index is a separate evidence-ID cache for inherit/repeat-offense only.
- **Risk: `register` in frontmatter could leak PO config into a shareable file.** Mitigation: only the three closed-enum knob values (no free text); acceptable, already in the report body wording anyway.
