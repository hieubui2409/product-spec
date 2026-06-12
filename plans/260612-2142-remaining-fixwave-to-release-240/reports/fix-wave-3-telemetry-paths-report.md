# Fix Wave 3 — Telemetry Paths, Artifact Boundary, Dead Param

Commit: `2168ea8`

---

## FIX 1 (HIGH): Export path re-derived wrong

**Bug:** `analyze_telemetry._write_export_summary` default path was `Path(sys.argv[0]).resolve().parent.parent.parent / "telemetry" / "usage-summary.md"` — resolves to wherever pytest / the shell lives, not `.claude/telemetry/`. `harvester._telemetry_dir()` hand-rolled the same logic independently.

**Fix:**
- `analyze_telemetry._write_export_summary(rendered, path, args)`: signature changed so `path` accepts `None`; when `None`, resolves via `telemetry_paths.TELEMETRY / "usage-summary.md"` (env-aware, honors `CK_TELEMETRY_DIR`). Caller passes `args.export_summary` directly (was string-coerced before, now `str | None`).
- `harvester.py`: removed `_telemetry_dir()` entirely; replaced its usage with `import telemetry_paths; telemetry_paths.TELEMETRY`.

**Tests (RED first):**
- `test_export_summary_default_path_honors_env` — patches `sys.argv[0]` to a clearly wrong path, calls `_write_export_summary(…, None, …)`, asserts file lands in `CK_TELEMETRY_DIR/usage-summary.md`. Was failing (`TypeError: NoneType` passed to `Path()`); now green.
- `test_explicit_path_arg_overrides_default` — explicit `--export-summary <path>` writes to that exact path. Green throughout (regression guard).
- Existing harvester boundary-A9 and all 5 harvester tests remain green.

---

## FIX 2 (LOW): Artifact-edit hook over-captures sibling dirs

**Bug:** `_is_spec_artifact` looped over `("docs/product/", "docs/product")`. The no-slash variant `"docs/product"` is a substring of `"docs/productx/"` and `"docs/product-archive/"`, so those paths returned `True` — spurious events fired.

**Fix:** Replaced the two-variant substring loop with a single `"docs/product"` needle check that enforces a segment boundary at both ends:
- Left: `idx == 0` or `norm[idx-1] == "/"`
- Right: `after == ""` (exact match) or `after.startswith("/")`

**Tests (RED first):**
- `test_sibling_dir_not_treated_as_spec_artifact` — `docs/productx/a.md`, `docs/product-archive/a.md`, `docs/productfoo/PRODUCT.md` → zero events. Was failing (3 spurious events recorded); now green.
- `test_spec_root_itself_is_still_a_spec_artifact` — `docs/product/PRODUCT.md` → 1 event. Green throughout (regression guard).

---

## FIX 3 (LOW): Dead `_visited` param

**Bug:** `render_supersede_chain(dec_id, records, *, _visited=None)` accepted `_visited` but built its own local `visited: set = set()` and never read the param. Dead parameter creates misleading API surface.

**Fix:** Removed `_visited: Optional[set] = None` from the signature. No caller passes it (confirmed by grep). Cycle-safety and dangling-soft behavior identical — the local `visited` set is untouched.

No new test required (existing cycle and dangling tests in `test_decision_register_view.py` cover the invariants; they remain green).

---

## Verification

```
python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q
→ 241 passed

python3 -m pytest .claude/skills/product-spec -q
→ 1 failed (pre-existing test_dogfood_state_untracked, unrelated)
```
