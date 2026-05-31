# Cycle 9 — Hardcore Dual-Skill Review (findings + fixes)

Date: 2026-05-31 · Branch: `feat/product-spec-v2-multidim` · Mode: FULL C7-style (Workflow tool, 16 file-partitioned finders, overlap allowed, all 9 angles).

## Run cost
- Finders: 16 (8 product-spec subsystem + 2 claude-pack + 4 cross-cutting overlap + 2 references) → per-file verify (39 files) → 2 sweep gap-finders → sweep-verify.
- 63 agents / ~4.9M tok / ~20.7 min. Raw 106 candidates → **101 kept** (93 primary + 8 sweep), 5 refuted.
- Owner decisions: fix ALL 101 (no accept) · TIGHTEN SEMVER_RE to strict SemVer 2.0 · installers INSTALL top-level README/CLAUDE.

## Severity
3 CRITICAL · 13 HIGH · ~13 MED · ~72 LOW. PLUS 4 extra crash sites found during fix-verification repro (same unhashable-key class the finders under-covered).

## CRITICAL (all fixed + verified)
1. **Tar-slip / arbitrary file write (claude-pack).** `_has_traversal`/`_is_absolute_or_drive` were applied ONLY to `extra`; `skills`/`agents`/`rules`/`hooks`/`_include_shared` emitted a `..` arcname verbatim into the tarball → recipient writes outside the extraction dir. Reproduced end-to-end. Fixed in 3 layers: validate() containment for every category + `_include_shared` (+ resolve-within-base for skills/_shared); resolve_selection chokepoint rejects `..`/absolute arcnames; `is_dropped()` first-rule drops traversal/absolute (tarball inherits). +regression tests (all 4 categories rejected, chokepoint never emits `..`).
2. **Gate crash on out-of-range date.** Unquoted `target_date: 2026-13-99` → PyYAML `construct_yaml_timestamp` raises a bare `ValueError` (not `YAMLError`); `frontmatter_parser.parse_text` only caught `YAMLError` → crashed all 3 gates. Fixed: catch `(yaml.YAMLError, ValueError)` → parse_error finding; strict_gate exits 2 (verified) not crash.
3. **`epic`/`prd`/`id` list/dict poison the graph (carry-forward regression).** C7/C8 `_as_id_list` coerced `depends_on`+`brd_goals` but left the scalar link fields un-coerced → unhashable dict-key crash in every consumer. Fixed at the single source: `spec_graph._scalar_id` (id → str|`<missing-id>`|`<invalid-id>`), `_scalar_link` (epic/prd → str|None), node_type coerce; malformed id surfaces via `invalid_id`, malformed epic/prd via orphan/dangling (fail-soft). +unit/e2e tests.

## HIGH (13, all fixed)
- build_traceability_matrix: TypeError on mixed-type metrics / non-str brd_goals (join), epic/prd dict-key, mixed-id sort → str-coercion at all sites.
- frontmatter_parser: non-UTF-8 file → `UnicodeDecodeError` (ValueError subclass) crashed graph build → caught → encoding parse_error.
- generate_templates: `--type change_log_entry`/`sign_off` always crashed (no OUTPUT_PATH) + PRD `--id` without `--slug` wrote `prds/.md` → content-only path for mapping-less types; slug derived from artifact_id; main() wraps ValueError → JSON finding.
- render_ascii.risk/competition/persona, render_html.competition(parity matrix)/dashboard(roadmap): unhashable spec value used as dict key → `_hashable` routing / isinstance guard / str-projection sort.
- spec_graph: bare-string `brd_goals` char-split into phantom single-char edges → build_edges guards the iteration.
- tar-slip via `--include-shared` (second surface) + list `id:` crash → covered by the CRITICAL coercion + validate containment.

## MED (~13, all fixed)
Credential leak (`git remote get-url origin` w/ userinfo embedded in MANIFEST.json → scrubbed); `schema_version`/duplicate-detection unhashable guards (new `MANIFEST_E102`); quoted calendar-invalid `target_date` now flagged; install.sh SemVer leading-zero octal bug → base-10 (`10#`); README/CLAUDE.md packed-but-not-installed → installers walk the whole bundle root; discover() hooks recursion + ambiguous-stem exclusion; error-catalog gains build_manifest exit codes.

## LOW (~72, all fixed)
Doc-drift (view counts, V1–V8→V1–V7, slug-grammar leading-letter, snapshot-filename/schema, orphan_prd trigger, unknown_ref catalog row, `--filter-wont` lists, `--all` v0.5 claim, case-sensitivity claims, metadata.json breadth, CLAUDE.md exit-code scoping); DRY hoists to spec_graph (`make_finding`, `HORIZON_ORDER`, `moscow_story_counts`, `competitor_id_to_name`, `resolve_ac`, `ID_PATTERN_BY_TYPE`/`COMP_ID_PATTERN`) + render_ascii (`_dep_safe_order`, `_board_columns`, `resolve_competition`); dead code (`parsed_node_extras`, `Tuple` import, `n=1`); edge cases (BOM preserve, frontmatter-region newline detect, empty-frontmatter message, i18n empty-string label, extract_sections dedup, `_ac_item` repr leak, baseline mtime tiebreak, EXDEV errno, negative/unicode epoch, dry-run max-size gate).

## Extra crash sites (beyond the 101 — found in fix-verification repro)
- render_ascii.roadmap + render_ascii.time + render_mermaid.roadmap + render_mermaid.time: horizon used as dict key → coerce to str before bucketing.
- render_html `_parity_label`/`_threat_label`: `val in {set}` membership on an unhashable val → isinstance guard.

## Refuted by verify (5)
PLAUSIBLE/intentional items (e.g. selection collision-order already deterministic for a fixed manifest; render_html assemble() chrome NOT folded into chrome_values — folding would change generated_at source + title escaping, a real behavioral divergence not a bug). render_html P80 chrome-fold left as deliberate divergence with note; comment (P81) fixed.

## Verification
- product-spec **326 → 351** (+25 regression tests) green · claude-pack **78 → 109** (+31) green.
- `examples/acme-shop` strict_gate 0 errors / 0 warns (no regression on real data).
- 14/14 viz view×format combos render on real acme-shop data.
- Live malformed-graph repro: 0 crashes across all 13 graph/native renderers + 3 gate scripts + matrix.

## Execution
Foundation (spec_graph single-source coercion + shared helpers, the gate trio, matrix, render_html crash-safety + the 4 extra sites) by the lead; renderers/viewers, product-spec misc, claude-pack security (tar-slip), claude-pack build/io/cli + installers, and docs by 5 file-partitioned sub-batches (no file overlap). One sub-batch test file renamed off a cycle-numbered name (rule-5).

## Unresolved questions
None. Convergence NOT reached (101 findings → counter stays 0). Next = Cycle 10 (full C7-style; cap C15).
