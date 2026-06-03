# Code Review — spec-critique lifecycle cache + inherit (Script half P1–P3 + modularization)

Scope: `.claude/skills/spec-critique/scripts/` (10 modules + tests) + cross-skill `product-spec/scripts/preferences.py`.
Suites: spec-critique 102 passed; product-spec preferences 23 passed. All modules import standalone (no cycles). All ≤200 LOC.

Overall: solid, contract-faithful, well-tested deterministic layer. The Script-vs-LLM split is respected (no voice/quality judgment). Fence, tolerant-read, determinism, and facade re-exports all verified. Found 2 real semantic bugs (one Medium, one High) the tests miss, plus several lower-severity edge cases. None crash; all degrade. No cross-skill regression from the preferences edit.

---

## HIGH

### H1 — `descendant_rollup` cannot count clean-critiqued children → verdict over-states severity
File: `critique_inherit.py:143-174` (`build_descendant_rollup`)

The findings-index is LOSSY by design: `index_report_findings` (`:177-197`) only writes blockers + DEC-worthy. `build_descendant_rollup` derives `critiqued_child_count` by scanning that index (`:154-162`), so a child that was critiqued and came back **clean** (zero blockers/DEC) leaves no index row and is invisible. Result: `critiqued_child_count` only ever counts children-with-blockers, making `verdict_line` structurally always "N/N carry blockers" (100%).

Reproduced: S1 blocker, S2 critiqued-clean, S3 uncritiqued → rollup returns `critiqued_child_count: 1`, `verdict_line: "1/1 critiqued children carry blockers"`. The plan's intended semantic ("3/5 stories unbuildable", phase-03:25/74) requires the denominator to be *all critiqued children*, including clean ones — which this cannot represent. The test `test_rollup_counts_blocker_children` only seeds blocker children, so it never exposes the gap.

Impact: the consolidator (P4) will render a falsely-alarming "100% of critiqued children carry blockers" whenever any clean children exist. This is a correctness defect in the rollup signal, not just cosmetics.

Fix options (pick one, surface to PO since it touches the rollup contract):
- (a) Make the index record EVERY critiqued node id (a lightweight "critiqued" marker row even with no blocker), so the denominator is real. Cleanest, but widens the index write.
- (b) Drop `critiqued_child_count` / the X/Y ratio entirely and emit only `blocker_children` + `total_child_count` (honest: "2 of 3 children carry blockers; remainder uncritiqued-or-clean").
- (c) Source the critiqued-set from `critique-state.json` per-scope records (which ARE written per real run regardless of blockers) instead of the index. This matches R5's "state knows what was critiqued" model and keeps the index lossy.
Recommend (c): `critique-state.json` already has a per-scope `last_ts`; cross-referencing child scopes there gives a true critiqued-vs-clean denominator without polluting the lossy index.

---

## MEDIUM

### M1 — provenance `full`/`consolidate_only` ignores `register` → wrong-voice reuse at level ≥7
File: `critique_provenance.py:108-119` (`_decide_unchanged`)

`_decide_unchanged` compares only `level` and `lang`. At level ≥7 the *register* (gender/dialect/profanity) is part of the rendered voice and is carried in the report frontmatter (`build_report_frontmatter:92-93`), but: (1) `_prior_reports` (`:60-69`) never extracts `register`, and (2) `record_critique_state` (`:154-174`) never stores it. So two level-7 runs that differ only in register both resolve to `reuse: full` and reuse the prior report verbatim — i.e. a PO switching `critique_dialect` bac→nam, or gender m→f, gets the OLD voice back.

Reproduced: prior report level 7 register `{gender:m,…}`; re-run level 7 (would-be register f) → `reuse: full`. Should be `consolidate_only` (re-render voice from the lens-cache) since the lens findings are register-neutral but the voice is not.

Impact: violates the R6 premise that level/register live ONLY at consolidate — a register change must re-consolidate, not full-reuse. Currently silently serves stale-register output. Bounded to level ≥7 (register only exists there), but exactly the levels where voice differences matter most.

Fix: capture `register` in both `_prior_reports` (add `"register": fm.get("register")`) and `record_critique_state` (add a `register=` field + store it), then in `_decide_unchanged` treat a register mismatch like a level/lang mismatch → fall through to the `consolidate_only`/`relens` branch instead of returning `full`. Add a level-7 register-change test.

### M2 — fast-path returns `reuse: full` / `consolidate_only` pointing at a report that may not exist
File: `critique_provenance.py:135-140`

The R5 fast-path trusts `critique-state.json` and returns `report=state_rec.get("report")` without confirming the file is still on disk. If the prior report was deleted/renamed (e.g. P5's "purge old bodies" step, or a PO housekeeping) but `critique-state.json` lingers, the orchestrator (P4) receives `reuse: full` + a dangling path, or `consolidate_only` for a `lens_findings_hash` whose lens-cache file is still present but whose report is gone. `full` is the riskier case — P4 may "just point at" a nonexistent report.

Impact: P4 could emit a verdict referencing a missing file. Advisory layer so it won't crash the script, but it hands P4 a broken contract. The slow path is safe (it reads `_latest_frontmatter_prior`, which only returns existing files); only the fast-path skips existence.

Fix: in the fast-path, before returning `full`/`consolidate_only`, if `report` is set, verify `Path(report)` (resolved under root) exists; if not, fall through to the slow path. `consolidate_only` already self-heals via the lens-cache-missing→relens degrade in `_decide_unchanged`, so the real exposure is `full` with a dead report. Cheap guard, keeps the fast-path fast on the happy path.

---

## LOW

### L1 — `_node_of("")` returns `""`, which can false-classify as scope when scope is empty
File: `critique_inherit.py:43-46`, `:59-64`

`_node_of` does `str(evidence_id).split(":",1)[0]`; an empty/None-coerced evidence_id yields `""`. `_index_rows` (`:71-73`) and `_inherited_candidates` (`:88`) guard `if not eid: continue`, so a falsy eid is dropped upstream — currently safe. But `index_report_findings` and `upsert_findings` also skip empty eids, so this is defense-in-depth only. No action required; noting because `_classify` itself has no empty-guard and would return `"drop"` for `""` vs any real scope (harmless). Leave as-is.

### L2 — `index_report_findings` `why` fallback to `why_it_dies` not mirrored in `upsert_findings`/inherit output
File: `critique_inherit.py:193` vs `critique_cache.py:47,71`

`index_report_findings` maps `f.get("why") or f.get("why_it_dies")` when extracting, which is correct (lens findings use `why_it_dies`; consolidator findings use `why`). Good. But note the stored field is always `why`, and `_inherited_candidates` (`:103`) reads `entry.get("why")` — consistent. No bug; flagging that the dual-key knowledge lives only in this one extractor, so any future direct `upsert_findings` caller bypassing `index_report_findings` must replicate the `why_it_dies` fallback. Consider a one-line comment on `upsert_findings` pointing at the canonical extractor.

### L3 — `_diff_hashes` "changed" includes added/removed nodes as drift but provenance `relens` reports them too — verify P4 doesn't double-handle
File: `critique_drift.py:58-75`, `critique_provenance.py:147-150`

Both `compute_drift` and `compute_provenance_reuse` compute `changed_ids` as the symmetric set where `live.get(i) != prior.get(i)`, which includes nodes added since the prior (present in `live`, absent in `prior`). For provenance this means a brand-new node forces `relens` with that new id in `changed_ids` — correct. Just confirm P4 treats a `relens` `changed_ids` containing a node with no prior lens findings as "lens this node fresh", not "re-lens an existing finding". Contract note for P4, not a script bug.

### L4 — `get_cached` TTL boundary is strict `>` (exactly-at-TTL is still fresh)
File: `critique_blob_cache.py:50`

`age.total_seconds() > ttl_days*86400` means content exactly `ttl_days` old is still served. Matches the test (`+7d` fresh, `+20d` expired) and is a reasonable choice; documenting the boundary semantics only. No change.

---

## Invariant verification (all PASS)

1. Script-vs-LLM split — PASS. No module renders voice; provenance decides only structural reuse; inherit classifies only graph-relation.
2. R1 lens-cache (full array) vs findings-index (lossy) NEVER conflated — PASS. Two stores, two keys (`critique_blob_cache._lens_findings_hash` vs `critique_cache._index_path`). `consolidate_only` with missing lens-cache degrades to `relens` (`_decide_unchanged:117-119`), verified by `test_provenance_consolidate_only_missing_lens_cache_degrades_relens`.
3. R4 scope from frontmatter `critique_scope` ONLY — PASS. `_prior_reports:57` comment "never used for scope"; `_latest_frontmatter_prior:103` filters on `critique_scope`; filename-only prior → `none` (verified, both `all` and `all-lvl3` queries).
4. R5 critique-state fast-path short-circuits the report read — PASS. `compute_provenance_reuse:135-140`; test asserts `_latest_frontmatter_prior` not called. (See M2 for the existence-check gap.)
5. Inherit uses `ancestors()` SET, blockers+DEC only, fresh-only, `source=<parent-id>@<ts>`, consolidator-only — PASS. `_inherited_candidates:82-107`; grandparent-goal inherit test passes; lens-blind (keys are top-level bundle keys, not in any lens-specific payload).
6. Fence-before-write, tolerant reads, injected `now_iso`, sorted-key JSON — PASS. All writes route `critique_cache_io._write_json` → `fs_guard.assert_under_docs_product` before mkdir; `write_snapshot` (`critique_drift.py:84`) fences directly; reads return `{}`/`None` on corrupt; `now_iso` injectable everywhere; `json.dump(sort_keys=True)`; byte-determinism test passes.
7. Modularization — PASS. No cycles (`critique_cache_io` + `critique_common` are import leaves; verified all 10 import standalone). Facade `critique_scan.<name>` re-exports resolve (tests call `critique_scan.compute_provenance_reuse`, `._scoped_body_hashes`, etc.).

Cross-skill `preferences.py` edit (R2) — PASS, no regression. 3 keys in DEFAULTS+ENUMS; on/off→token coercion correct (`load:176-177` maps `False→"off"`; `"on"` is NOT a profanity-style trap because for inherit/rollup `True→"on"` IS the enum value). `test_critique_inherit_off_coerces_to_token`, `test_cross_critique_save_round_trip`, `test_defaults_has_exactly_thirteen_keys` all green. Note: a YAML `critique_inherit: on` parses to `True→"on"` which IS valid here (unlike profanity), so the bare-`on` token round-trips correctly — confirmed safe.

---

## Recommended actions (priority order)

1. H1 — fix `descendant_rollup` denominator (recommend sourcing critiqued-set from `critique-state.json`, option c). Surface the contract choice to PO.
2. M1 — capture + compare `register` in provenance reuse (store in `_prior_reports` + `record_critique_state`, gate in `_decide_unchanged`). Add level-7 register-change test.
3. M2 — fast-path: verify the prior report exists before returning `full`; else fall through to slow path.
4. L2 — one-line comment marking `index_report_findings` as the canonical finding extractor (the `why_it_dies` fallback home).

## Unresolved questions

- H1: is `critique-state.json` written per-scope for child stories on a real run, or only for the critiqued scope? If only the top scope, option (c) needs P4 to write per-node state. Confirm the intended P4 write granularity before fixing.
- M1: is a register change at the same level expected to `consolidate_only` (re-render) or is full-reuse acceptable because the report body already embeds the register text? Plan R6 implies re-consolidate; confirm with PO.
