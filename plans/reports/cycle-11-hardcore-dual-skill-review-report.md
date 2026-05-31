# Cycle 11 — Hardcore Dual-Skill Review (product-spec + claude-pack)

**Date:** 2026-05-31 · **Engine:** Workflow tool (FULL C7-style) · **Run:** wf_76dbea94-0a4 · 59 agents / ~3.8M tok
**Result:** 38 raw → 36 deduped → **37 confirmed** + 1 extra (fix-verify) → all fixed · 2 accepted (owner) · 1 refuted
**Severity:** 0 CRIT · 1 HIGH · ~11 MED · ~25 LOW · **Primary watch = regressions from C10 fixes**

## Engine

10 subsystem (8 product-spec + 2 claude-pack) + 4 cross-cutting angle + 2 reference finders, ALL 9 angles →
consolidate/dedup (file:line + mechanism) → adversarial 3-state per-finding verify → 2 whole-skill sweep → verify sweep.

## Fixes applied

### product-spec — code
- **HIGH** `check_traceability.py` — unhashable brd_goals **element** (`[{nested}]`) → set-membership `TypeError`
  crashed gate + strict_gate. Per-element `isinstance(str)` guard (sibling sites already had it; this one was missed by
  the C9/C10 unhashable sweeps).
- **MED (C10 stale-caller, the watch target)** `spec_graph._competitors` — `fm.get("type") or hint` short-circuited on a
  truthy non-string `type: [brd]`, so competitors silently vanished while `build_nodes` (which got the C10 coercion)
  kept the goals on the SAME file. Single-source `_node_type(art)` now used at build_nodes + _competitors + _product_meta.
- **MED** `render_html.product_name` — coerce non-str name + non-dict product → str at the single source (fixes
  export/board/explorer chrome + md heading crash); `goal_detail_md` metrics `isinstance(list)` shape-guard (no char-split).
- **MED** `migrate_multidim_fields` — `apply_file` re-derived type via `_type_for_path` (brd.md-anywhere) diverging from
  the glob; now threads authoritative glob `art_type` + `_type_for_path` brd.md scoped to `parent=="product"`.
- **LOW** `render_ascii._product(graph)` dict-guard (persona/_ascii_product_name); shared `_scalar` hoist (board+explorer);
  `generate_templates.render` strips leading comment BEFORE residual-token check; `_competition_matrix` cell_lookup
  required (dropped dead inline-resolve fork); dead `_PARITY_COLS`/time-view `nodes_by_id`/vestigial f-string removed.

### claude-pack — code
- **MED** `build_manifest._assemble_manifest` — malformed scalar category passed through unchanged (no `list()`
  char-split/TypeError) → `manifest_loader.validate` E010.
- **MED/LOW** `manifest_loader` — `_include_shared` E010 type-guard (both validate read-sites + gates cli.py/selection);
  `_as_list` on the 4 slug-resolution loops + `_check_path_safety` non-list no-op **(extra crash site found by the
  int-category regression test in fix-verification)**.
- **LOW** `args.resolve_epoch` year-9999 `_MAX_EPOCH` ceiling (flag rejects, env clamps to 0); `templates.render_template`
  catches `UnicodeDecodeError`; `selection._walk_dir` `arc_prefix.strip('/')` (trailing-slash extra → no double-slash
  arcname); dead `selection.claude_dir_resolved` removed.

### Doc-drift (both skills)
View counts (mermaid 9→11, SKILL/viz 9→12-graph framing); `--lang` scoped to prose/visual scripts (CLAUDE.md);
visualize/anchors/time_advisory exit-code clarity (validation-rules-spec, workflow-validate, CLAUDE.md); anchor `file`
key added to example; delta drops phantom edge-diff bullet; SKILL.md chrome-localization narrowed; E101 message suffix,
E071/E072 search-root-absent variant, `--bundle-name` CLI default `(manifest)`, pin-within-category advice (claude-pack).

## Owner interview (3 — risky/locked)
1. dashboard/`--lang` chrome doc-drift → **Narrow SKILL.md** (graph/HTML-native page chrome stays English; no code change).
2. board column-vs-facet key divergence → **Accept as documented** (cosmetic; only on validator-flagged malformed enum).
3. ASCII persona int/str collision → **Accept as-is** (C10 str() key correct; personas documented as string labels).

## Refuted (1)
`check_consistency.check_depends_on` out-of-band AC enrich — verifier proved non-issue.

## Verification
- Tests: product-spec **398** (+8) · claude-pack **126** (+9) — all green.
- `acme-shop` strict_gate: 9 artifacts · 0 errors · 0 warns.
- viz: 42/42 combos (14 views × 3 formats) OK. All modified scripts `py_compile` clean.

## Convergence
NOT converged (counter=0). Downward trend holds: C9 101 → C10 67 → **C11 37**; CRIT 3 → 0 → 0. The lone HIGH was a
missed sibling of an already-closed crash family; the top MED was exactly the C10-regression the watch existed for.
Continue to C12; cap C15.

## Unresolved questions
None. All owner decisions applied; carry-forward + REFUTED list updated in GOAL.md.
