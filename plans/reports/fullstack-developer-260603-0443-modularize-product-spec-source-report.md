# Modularize product-spec source files — implementation report

## Files split

### `check_consistency.py` 807L → 385L
Extracted:
- `check_consistency_time.py` (132L) — TIME-dimension structural checks: `parse_iso_date`, `check_target_date_shape`, `check_depends_on_type`, `time_child_late`, `dep_order`.
- `check_consistency_risk.py` (140L) — RISK-dimension checks: `check_risks`, `risk_high_ratio`, `risk_blindspot`, risk enum constants.
- `check_consistency_competition.py` (148L) — COMPETITION-dimension checks: `check_competitors`, `check_competitive_parity`, competition enum constants.

Facade re-exports `_parse_iso_date` (imported by `time_realism_anchors`, `time_advisory`, `status`) and `COMP_ID_PATTERN`, `competitor_id_to_name` (imported by `spec_graph`). Tests caught one missing re-export immediately on gate.

### `render_ascii.py` 712L → 571L
Extracted:
- `render_ascii_board.py` (194L) — board/explorer renderers and shared card-selection helpers: `board`, `explorer`, `_orphan_forest`, `select_cards`, `_filter_by_layers`, `_board_columns`, `_BOARD_CARD_TYPES`, `_BOARD_GROUP_ORDER`, `_LOCALIZED_COLS`.

`render_ascii.py` re-exports all moved names as facade. `explorer()` in the submodule uses a lazy import of `render_ascii.tree` to avoid circular import. `_is_deferred`, `_hashable`, `_scalar` stay in `render_ascii.py` (imported by `render_mermaid`, `render_board`, `render_explorer`). The remaining 571L is 11 cohesive view renderers (tree/heatmap/scope/roadmap/time/persona/gap/moscow/risk/competition/delta) — no clean further seam.

### `behavioral_memory.py` 424L → 217L
Extracted:
- `behavioral_memory_po_style.py` (166L) — po-style YAML store: `load_raw`, `load`, `record`, `_write`, `_union_keep_order`, `_assert_no_structural_copy`, `BehavioralError`.
- `behavioral_memory_self_corrections.py` (107L) — self-corrections JSON store: `load_raw`, `load`, `record`, `_write`.

Key design: `_po_style_path`, `_self_corrections_path`, and `_now` remain defined at `behavioral_memory` module level (tests monkeypatch `bm._po_style_path`, `bm._self_corrections_path`, `bm._now`). Submodules accept resolved `path` and `now_fn` as parameters — no monkeypatch bypass. One test failure (`test_self_correction_append`) caught on gate from `_now` bypass; fixed by threading `now_fn=_now` through `record_self_correction`.

### `generate_templates.py` 477L → 389L
Extracted:
- `template_id_alloc.py` (110L) — ID allocation: `allocate_id`, `_next_with_prefix`, `ID_PATTERN_OVERRIDE`, `PRD_PARENT_LOOKS_LIKE_EPIC_OR_STORY`, `SLUG_PATTERN_FOR_PRD`, `PARENT_PATTERN_FOR_PRD`, `PARENT_PATTERN_FOR_EPIC`.

Facade re-exports needed constants for the `_run()` function.

### `judgment_cache.py` 658L → 554L
Extracted:
- `judgment_cache_keys.py` (132L) — deterministic key composition: `compute_key`, `graph_content_hash`, `CACHE_VERSION`, `NEVER_CACHED`, `PAIR_CHECKS`, `CORE_VALUE_DEP_CHECKS`, `node_index`, `body_hash`, `lang_segment`, `core_value_dep`, `key_base`, `key_node_ids`.

Facade re-exports all moved names so `jc.compute_key` etc. remain accessible. `hashlib` kept in `judgment_cache.py` for `write_last_validated`'s SHA-256 use. One test failure (`NameError: hashlib`) caught on gate when I removed the import prematurely; fixed immediately.

---

## Files left as-is + reasons

| File | LOC | Reason |
|---|---|---|
| `spec_graph.py` | 690 | UNIVERSAL dependency hub — nearly everything imports it. Per instructions, kept as thin facade risk is too high. Functions are small, no dominant seam. |
| `render_html.py` | 1044 | ~300L of large JS/CSS template strings (`_TOOLTIP_JS`, `_BODY_RENDER_JS`, 4 scoped CSS blocks). Per exclusion clause, template strings stay intact. `_escape` used by every section makes seams artificially coupled. Accepted exception. |
| `render_mermaid.py` | 405 | 11 cohesive Mermaid view renderers + 4 shared helpers. No horizontal seam. |
| `visualize.py` | 382 | Dispatcher with tight routing logic. Splitting `_dispatch`/`_dispatch_body_view` would only add an import for 2 helper functions. |
| `assemble_digest.py` | 360 | `build_digest` calls all private helpers. Tightly coupled pipeline, no clean seam. |
| `decision_register.py` | 346 | parse/append/supersede/list on one register file. Tightly coupled. |
| `memory_gap.py` | 332 | Four detector functions all operate on the same (graph + baseline + judgment_cache) state. |
| `migrate_multidim_fields.py` | 322 | Migration pipeline: plan_file → apply_file → migrate. Tightly coupled. |
| `reflect_scan.py` | 306 | git-degrade-safe anchor builder. Cohesive single responsibility. |
| `render_export.py` | 296 | Export renderer. Single cohesive pipeline. |
| `status.py` | 256 | Status nudge: reads memory markers, emits signals. Cohesive. |
| `check_traceability.py` | 209 | Just over 200L; orphan/dangling/unaddressed-parent checks are a single tight group. No seam. |

---

## Test results (final)

- **product-spec suite:** 552 passed, 0 failed
- **spec-critique suite:** 105 passed, 0 failed
- Intermediate failures caught and fixed before final gate: 2 (missing `_parse_iso_date` re-export; missing `now_fn` threading; `hashlib` removal).

## New modules created (8 total)

```
check_consistency_time.py       132L
check_consistency_risk.py       140L
check_consistency_competition.py 148L
render_ascii_board.py           194L
behavioral_memory_po_style.py   166L
behavioral_memory_self_corrections.py 107L
template_id_alloc.py            110L
judgment_cache_keys.py          132L
```

## Status: DONE_WITH_CONCERNS

**Summary:** 5 source files split into 5 facades + 8 sibling modules. Both test suites (657 total) fully green. Behavior-preserving: no logic changes, only module boundaries moved.

**Concerns:**
- `render_html.py` (1044L) and `spec_graph.py` (690L) remain above 200L — accepted exceptions per the task's exclusion clause and the spec_graph universal-hub instruction.
- `render_ascii.py` (571L) reduced but still above 200L — remaining content is 11 independent view renderers with no clean seam (splitting would produce 11 one-function files).
- `judgment_cache.py` (554L), `generate_templates.py` (389L), `check_consistency.py` (385L), `render_mermaid.py` (405L) also above 200L — assessed as no further clean seam without fragmenting cohesive logic.
