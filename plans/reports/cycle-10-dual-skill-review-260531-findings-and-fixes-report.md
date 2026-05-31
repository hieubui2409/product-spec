# Cycle 10 — Hardcore Dual-Skill Review (findings + fixes)

Date: 2026-05-31 · Branch: `feat/product-spec-v2-multidim` · Mode: FULL C7-style (Workflow, 16 file-partitioned finders, overlap, all 9 angles) — PRIMARY WATCH = regressions from the C9 fixes.

## Run cost
- First launch THROTTLED (18 subagents got synthetic empty completions — API usage ceiling right after the heavy C9 window; 0 findings, not a clean cycle). Re-launched a few minutes later via `resumeFromRunId`/scriptPath → succeeded.
- 16 finders → per-file verify (33 files) → 2 sweep. 57 agents / ~4M tok / ~14 min.
- Raw 69 candidates → **67 kept** (61 primary + 6 sweep), 3 refuted.

## Severity
**0 CRITICAL · 1 HIGH · ~14 MED · ~52 LOW.** The C9 CRITICALs held (no new CRITICAL). This was a "second-order" cycle: mostly cleanup the large C9 change left behind (stale callers of the hoisted helpers, incomplete hoists, doc-drift on the new behaviour) + a few genuinely new edge cases. The regression-watch worked — several findings were C9-introduced.

## HIGH (fixed + verified)
- **render_ascii.persona() cell key** used the RAW persona value as a dict key while row labels were str-coerced → crashed on an unhashable persona (`[{name:..}]`) AND silently mis-counted a non-str persona (`5` vs label `'5'`). The C9 unhashable-key sweep guarded risk/competition/dashboard/roadmap/heatmap but missed this site. Fixed: `key = str(p)` so cell key + label share one coercion. +regression test.

## C9-regressions caught (the watch earned its keep)
- **Windows separator in the tar-slip containment** (`manifest_loader` ×2 sites + `selection.py`): the resolve-within-base guard used a hardcoded `str(base)+'/'` string-prefix → inverts on a Windows builder → false E021 on EVERY valid skill/_shared. Fixed: separator-agnostic `Path.relative_to` in try/except. (Containment for agents/rules/hooks was also missing → added.)
- **userinfo scrub regex** `(://)[^/@]*@` stopped at the FIRST '@' → a password with a literal '@' leaked a fragment into MANIFEST.json. Fixed: `[^/]*@` (consume to the last '@' in the authority).
- **Stale callers / incomplete hoists from C9:** `assemble_digest._entry` bypassed the hoisted `resolve_ac` (blank-AC export leak); `spec_graph.index_artifacts` keyed by RAW id while nodes key by `_scalar_id` (body/AC/export dropped for a malformed-id artifact); `<invalid-id>` sentinel leaked into PO help + a false-positive `dup_id`; `_DASHBOARD_HORIZONS` was an orphaned copy of `HORIZON_ORDER`; `render_html.competition` re-implemented the hoisted `resolve_competition` inline (wired it + corrected the docstring); `_competitor_names` was a pure passthrough wrapper (inlined); `_status_inconsistency` char-split a bare-string brd_goals (the C9 guard added to build_edges/_self_reference missed it); duplicate `invalid_type` for non-list brd_goals through strict_gate (deduped to check_consistency's LIST_FIELDS home).

## MED (selection)
build_manifest `--write` crashed on non-object stdin JSON (null/list/string) → EXIT_VALIDATION; generate_templates `load_values` OSError/non-dict → ValueError; render_export `_heading` injected raw markdown from a CR/LF id/title; spec_graph `diff_graphs` crashed on mixed-type personas; generate_templates `--id`+conflicting `--slug` wrote a mislocated PRD; safety_check backslash-traversal + drive-letter over-drop; cli `--dry-run` FS side-effects + over_max_size parity (now `null` without --compute-sha); error-catalog missing the C9 `MANIFEST_E102` row.

## LOW (all fixed)
Doc-drift (orphan_story/epic/brd_goal catalog rows, competitive_drift `--validate` runbook gap, delta `size` field, graph-JSON keys, install-template headers, flag-reference `--manifest` spacing, CLAUDE.md CDN view count); DRY (`_check_path_safety` extract, `resolve_max_size` extract, installer exclude-list parity); dead code (`Optional`/`COMP_ID_PATTERN`/`ascii_tree` imports); defensive (recipient-installer traversal re-validate, `templates.render_template` OSError→TemplateError, `_walk_findings` OSError guard, mermaid tree sort parity, i18n `label()` unhashable guard).

## Refuted (3 — correctly held the C9 decisions)
- SEMVER_RE strict-2.0 does NOT reject any genuinely-valid SemVer 2.0 string (regex repro against the canonical valid set).
- build_manifest `EXIT_COLLISION=2` vs pack `2=strict-gate` divergence is intentional (separate entry points, documented).
- The broadened `(yaml.YAMLError, ValueError)` catch does NOT swallow a legitimate non-parse ValueError (the only raising statement in the try is `yaml.safe_load`).

## Judgment call (surfaced)
**#11 depends_on bare-scalar** silently coerced to `[]` with no finding (unlike brd_goals). The "fix" would require reverting the C8 single-source `_as_id_list` coercion (multi-file, risky). Per rule-3, KEPT the coercion (it is the deliberate C8 crash-safety trade-off; wrong-type placement on a non-empty list is still flagged) and added a one-line comment documenting it — no behavior change.

## Verification
- product-spec **351 → 382** (+31 regression tests) · claude-pack **109 → 117** (+8) — both green.
- `examples/acme-shop` strict_gate 0 errors / 0 warns; 14/14 viz view×format combos render on real data.
- Malformed-graph repro: 0 crashes across all 15 graph/native renderers + gates.
- Tar-slip repro: validate rejects `..` in all 4 categories AND a valid nested skill does NOT trip a false E021 (relative_to fix correct on POSIX). pack dry-run exit 0.

## Execution
Foundation render_html crash-safety completed by lead; 4 file-partitioned sub-batches (renderers / ps-core / claude-pack+installers / docs), no file overlap. One sub-batch test file renamed off a cycle-numbered name (rule-5). One pre-existing test updated to reflect the brd_goals invalid_type dedup (#58).

## Unresolved questions
None. Convergence NOT reached (67 findings → counter stays 0). Next = Cycle 11 (full C7-style; cap C15). The C10 fixes (Windows-safe containment, userinfo scrub, persona key, stale-caller cleanup) are the C11 carry-forward watch.
