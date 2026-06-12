# Phase 6 Implementation Report — #8 artifact-events sink + heat lens

**Date:** 2026-06-12
**Commit:** `3401acab6f4a0d67611896bddd74da0bf1e7d349`

## Landed Items

### A — Hook: `.claude/hooks/track_artifact_edits.py` (NEW)
- PostToolUse hook for Edit/Write/MultiEdit on `docs/product/**` paths
- `_build_record(path, op, session)` — pure-function WHITELIST: builds `{ts, artifact_path, op, session}` by explicit assignment; never receives payload content fields
- `_is_spec_artifact(path)` — path-segment boundary match; accepts both relative and absolute paths
- Sink: `artifact-events.jsonl` via `telemetry_paths.append_event`
- Fail-open via `hook_runtime.run_telemetry_hook`; disabled under pytest

### B — Registration: `register_telemetry_hooks.py` (MODIFIED — append only)
- Added `TRACK_ARTIFACT = _hook_cmd("track_artifact_edits.py")`
- Added `TRACK_ARTIFACT` to `TELEMETRY_CMDS` and `ALL_CMDS`
- Added `"track_artifact_edits.py"` to `_HOOK_BASENAMES` (reconcile/upgrade-safe)
- Appended `TRACK_ARTIFACT` to existing `PostToolUse:Edit|Write|MultiEdit` group's `commands` list — no new matcher group created, no existing entry clobbered

### C — Lens: `.claude/skills/telemetry/scripts/lens_artifact_heat.py` (NEW)
- `gather(days=30)` reads `artifact-events.jsonl`, tallies edits per `artifact_path`, returns `{lens, days, total_edits, rows}` where rows are `{artifact, edits, last_edit}` sorted by edits descending
- Skips malformed JSONL lines silently (fail-soft)
- Respects `days` cutoff window

### D — analyze_telemetry.py (MODIFIED — append only)
- `import lens_artifact_heat` added after existing lens imports
- `"artifact_heat": lambda a: lens_artifact_heat.gather(days=a.days)` appended to `LENSES` dict
- `"artifact_heat"` appended to `OVERVIEW_ORDER`

### E — telemetry_render.py (MODIFIED — append only)
- `heat_h/total/cols/none/a_heat` keys appended to both `"en"` and `"vi"` sub-dicts in `_T`
- `_md_artifact_heat(a, lang)` renderer function added
- `"artifact_heat"` entry appended to `_MD` dispatch dict
- `elif lens == "artifact_heat"` case appended to `render_ascii`

### F — test_analyze_telemetry_cli.py (MODIFIED — contract update)
- `test_all_lenses_json_is_a_list` updated to include `"artifact_heat"` in expected lens set (was listing the full OVERVIEW_ORDER set; new lens added to OVERVIEW_ORDER requires this update)

## Tests — 13 new, all GREEN

### `test_track_artifact_edits.py` (`.claude/hooks/__tests__/`)
| Test | Purpose |
|---|---|
| `test_hook_records_exact_keyset_strips_content` | H3 privacy gate: content-bearing payload → record keys exactly `{ts,artifact_path,op,session}`, all content strings absent from serialized record |
| `test_edit_outside_spec_tree_produces_no_record` | Negative: 5 outside-spec paths → 0 records |
| `test_edit_within_spec_tree_produces_a_record` | Positive counterpart |
| `test_op_field_reflects_tool_name` | Edit/Write/MultiEdit → `op` matches tool |
| `test_malformed_stdin_exits_zero_records_nothing` | Fail-open: bad JSON → continue:true, 0 records |
| `test_empty_stdin_exits_zero_records_nothing` | Fail-open: empty → continue:true, 0 records |
| `test_missing_file_path_produces_no_record` | No `file_path` in payload → 0 records |

### `test_lens_artifact_heat.py` (`.claude/skills/telemetry/scripts/tests/`)
| Test | Purpose |
|---|---|
| `test_heat_lens_tallies_per_artifact_ranked` | PRD-X×3, PRD-Y×1 → rows[0].edits==3, rows[1].edits==1 |
| `test_heat_lens_row_carries_last_edit_timestamp` | `last_edit` = max ts across edits to same path |
| `test_heat_lens_respects_days_window` | Old event excluded by days=1 cutoff |
| `test_empty_sink_returns_empty_rows` | No file → `rows==[]`, `total_edits==0`, no crash |
| `test_empty_sink_file_returns_empty_rows` | Empty file → same |
| `test_malformed_jsonl_lines_skipped_gracefully` | Bad line skipped, valid line counted |

## Test Counts

| Suite | Result |
|---|---|
| telemetry + hooks + `_shared` (primary gate) | **232 passed** |
| product-spec (regression) | **754 passed, 1 failed** (pre-existing `test_dogfood_state_untracked` — unchanged) |

## Privacy Approach — Whitelist Construction (H3 confirmation)

`_build_record` is a **pure function** that accepts only `(path: str, op: str, session: str)`. The caller extracts only `tool_input.file_path` from the payload before calling it. The function constructs the record dict with 4 explicit keys — `ts`, `artifact_path`, `op`, `session` — and nothing else. No content field (new_string, old_string, tool_response, command) is ever passed in or read. Future payload fields cannot leak because they are never received.

The H3 test (`test_hook_records_exact_keyset_strips_content`) feeds a realistic PostToolUse payload containing `tool_input.new_string`, `tool_input.old_string`, `tool_response.content`, `tool_response.stdout` and asserts:
- `set(record.keys()) == {"ts", "artifact_path", "op", "session"}`
- each content string is absent from `json.dumps(record)`

## telemetry_render.py + analyze_telemetry.py — P7 safety

Both files were edited **append-only**:
- `analyze_telemetry.py`: 1 import line appended, 1 LENSES key appended, 1 OVERVIEW_ORDER element appended
- `telemetry_render.py`: 5 label keys appended to `"en"` dict, 5 label keys appended to `"vi"` dict, 1 `_md_*` function added, 1 `_MD` key appended, 1 `elif` branch appended to `render_ascii`

No existing keys were modified. P7 can re-read both files clean; the `grep` anchors for its own insertion points are undisturbed.

## Files Modified

| File | Change |
|---|---|
| `.claude/hooks/track_artifact_edits.py` | NEW — 74 lines |
| `.claude/hooks/__tests__/test_track_artifact_edits.py` | NEW — 148 lines |
| `.claude/skills/telemetry/scripts/lens_artifact_heat.py` | NEW — 60 lines |
| `.claude/skills/telemetry/scripts/tests/test_lens_artifact_heat.py` | NEW — 111 lines |
| `.claude/skills/telemetry/scripts/register_telemetry_hooks.py` | +5 lines (TRACK_ARTIFACT cmd, TELEMETRY_CMDS, ALL_CMDS, _HOOK_BASENAMES, REGISTRATIONS) |
| `.claude/skills/telemetry/scripts/analyze_telemetry.py` | +3 lines (import, LENSES key, OVERVIEW_ORDER) |
| `.claude/skills/telemetry/scripts/telemetry_render.py` | +27 lines (labels ×2 langs, _md_fn, _MD key, ascii elif) |
| `.claude/skills/telemetry/scripts/tests/test_analyze_telemetry_cli.py` | +1 line (contract update) |
| `docs/audit-trail/REVIEW.md` | P6 row ticked |
| `docs/audit-trail/EVIDENCE.md` | P6-8 entry appended |
| `docs/product/decisions.md` | DEC-4 appended |

## Commit

`3401acab6f4a0d67611896bddd74da0bf1e7d349`
`feat(telemetry): add path-only artifact-edit sink and heat lens`
