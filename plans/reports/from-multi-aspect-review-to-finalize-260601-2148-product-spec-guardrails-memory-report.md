# Multi-Aspect Review — product-spec guardrails + memory layer

**Verdict:** SHIP-READY with non-blocking cleanups. No critical/high findings. 14 confirmed (all `is_real=true`); severity-adjusted ceiling = **medium** (4). Nothing breaks routine PO usage or the safety fence's actual protection. All 6 dimensions ran — **none failed / none deferred**.

**Blockers:** none. Recommend a single batched fix pass (doc-wiring + 1 ordering bug) before tagging a release, but it does not gate landing.

---

## 1. Coverage

| Dimension | Ran? | Confirmed findings |
|---|---|---|
| scripts-correctness | ✅ | 4 |
| plan-conformance | ✅ | 0 |
| safety-fence | ✅ | 1 |
| references-integrity | ✅ | 2 |
| dry-and-split | ✅ | 3 |
| test-quality | ✅ | 5 |

Not covered / re-run needed: **none**.

---

## 2. Confirmed counts

By **severity** (as-filed → adjusted on verification):

| Severity | Count (adjusted) | IDs |
|---|---|---|
| critical | 0 | — |
| high | 0 | — |
| medium | 4 | scripts-correctness-2, references-integrity-1, dry-and-split-1, test-quality-1→**low** |
| low | 8 | scripts-correctness-1(↓), scripts-correctness-3, scripts-correctness-4, safety-fence-1, dry-and-split-2(↓), dry-and-split-3, test-quality-1(↓), test-quality-2, test-quality-3 |
| info | 3 | references-integrity-2, test-quality-4, test-quality-5 |

> Note: 3 findings were downgraded on adversarial verification — scripts-correctness-1 (medium→low), dry-and-split-2 (medium→low), test-quality-1 (medium→low). Only **3 genuine medium** remain: scripts-correctness-2, references-integrity-1, dry-and-split-1.

By **dimension**: scripts-correctness 4 · dry-and-split 3 · test-quality 5 · references-integrity 2 · safety-fence 1 · plan-conformance 0.

---

## 3. Confirmed findings (grouped for a batched fix pass)

### GROUP A — The one real logic bug (fix first)

**scripts-correctness-2** · `medium` · Non-atomic supersede-then-append corrupts the Decision Register on append-validation failure
`scripts/decision_register.py:289-297`
- **Evidence:** `--append` flow calls `_supersede_in_place(root, args.supersedes)` (291-292, writes file → flips prior record to `status: superseded`) BEFORE `append_decision(...)` (293) validates title/rationale/dup-id (187-203). Reproduced via real CLI: seed DEC-1 active, then `--append --id DEC-2 --title second --supersedes DEC-1` with `--rationale` omitted → CLI returns `{"error":"invalid_input","written":false}` yet decisions.md shows DEC-1 already flipped to `superseded` and NO DEC-2 → `--list` returns `{"active":[]}`. Corrupt register (zero active + phantom-retired) from a caller error the script otherwise rejects. Violates documented append-only / no-overwrite invariant.
- **Fix:** Reorder — call `append_decision` first (it already validates + re-checks `supersedes in existing_ids`), flip prior record via `_supersede_in_place` only on success. Or validate inputs up front, or wrap both in one read-modify-write.

### GROUP B — Doc-wiring / discoverability (batch all together: SKILL.md index + CLAUDE.md pointer table)

These are all "the prose ships but the LLM's documented load path can't reach it / under-describes it." Single editor pass across `SKILL.md`, root `CLAUDE.md`, and two reference files.

**references-integrity-1** · `medium` · `workflow-status.md` unreachable via documented load mechanism
`references/workflow-status.md` (gap in `SKILL.md:124-144` + `CLAUDE.md:90-107`)
- **Evidence:** `grep -rln workflow-status --include="*.md"` over the skill = ZERO md hits; only `scripts/status.py:8` docstring points to it. NOT in SKILL.md "Loads references/* on Demand" (124-144), NOT in CLAUDE.md "Workflow Pointers" table (94-104). The `--status` SKILL.md flag row (50) describes behavior but never names the file. Both indexes say "Load only the references relevant to the active flag" → an LLM handling `--status` has no documented path to the honesty caveat / script-vs-LLM split / compose-the-nudge steps; reachable only by opening the .py docstring (inverts progressive-disclosure contract). Plan (phase-08:24) assumed the SKILL.md row would make it discoverable, but shipped row carries no pointer.
- **Fix:** Add `| --status | workflow-status.md |` to CLAUDE.md Workflow Pointers table; append `workflow-status.md` to SKILL.md "Loads references/* on Demand" workflow bullet (140-141). Keep status.py:8 docstring as secondary breadcrumb.

**references-integrity-2** · `info` · `behavioral-memory.md` omitted from SKILL.md references index
`references/behavioral-memory.md` (SKILL.md:124-144; reachable via workflow-interview.md:142 + workflow-validate.md:129)
- **Evidence:** NOT orphaned — linked from both parent workflows, both registered. But absent from SKILL.md "Loads references/* on Demand" enumeration where every other reference family is listed. Index-completeness nit; discoverability preserved transitively. (Contrast: `guardrails-and-boundaries.md` SKILL.md absence is intentional per phase-03 — routed via CLAUDE.md pointer table.)
- **Fix:** Add a one-line bullet noting it loads transitively via interview/validate final-writer (3D/3E) hooks. Defer if SKILL.md line budget tight.

**dry-and-split-3** · `low` · Plan-phase artifact refs (`P1`, `P8`) leaked into shipped prose + a code comment
`references/workflow-validate.md:45, 133` (+ `judgment_cache.py:392`)
- **Evidence:** §5 (review-audit-self-decision.md) forbids plan-phase refs in shipped artifacts. (1) workflow-validate.md:45 `...body_hash (P1).`; (2) workflow-validate.md:133 `...signal P8's --status reads...`; (3) judgment_cache.py:392 same `P8` leak in a **code comment** (exact §5 case). The *reason* is stable; only the `(P1)`/`P8` tags are unstable coupling. (Distinct from legit `P1..P9` PRD-interview vocabulary in interview-prd.md/workflow-interview.md, and from G-A*/G-B*/GATE-* gate codes in CLAUDE.md.) fs_guard.py:67 `"The plan and..."` is generic/borderline.
- **Fix:** workflow-validate.md:45 drop `(P1)`; workflow-validate.md:133 + judgment_cache.py:392 → `the --validate signal the --status command reads` (drop `P8's`). Optionally simplify fs_guard.py:67.

### GROUP C — DRY single-home drift (script + reference edits)

**dry-and-split-1** · `medium` · `visualization-spec.md` delta field list drifted from `spec_graph.CHANGED_FIELDS` (omits `body_hash`)
`references/visualization-spec.md:168`
- **Evidence:** Line 168 = old 5-field tuple "Changed status, scope, moscow, horizon, size." `body_hash` appears 0× in the file. Impl now drives delta off the 6-field single home `spec_graph.CHANGED_FIELDS = (status, scope, moscow, horizon, size, body_hash)` (spec_graph.py:466), iterated in render_ascii.py:686-695 → a body-only edit emits `~ <id>.body_hash:`. spec_graph.py:461-465 explicitly names the "one home." Sibling prose homes (validation-rules-spec.md:148, workflow-update.md:76, workflow-validate.md:101, workflow-status.md:39) WERE migrated; this file was missed (`git diff HEAD` empty for it). Documentation-only, no runtime impact.
- **Fix:** Rewrite viz-spec:168 to reference the single home, e.g. "Changed nodes per `spec_graph.CHANGED_FIELDS` (status/scope/moscow/horizon/size + body_hash); a body-only edit shows a `body_hash` diff line." Mirror validation-rules-spec.md:148 wording.

**dry-and-split-2** · `low` (was medium) · `behavioral_memory._STRUCTURAL_ENUM_VALUES` is a second hardcoded home for scope/moscow/horizon enums (already drifted)
`scripts/behavioral_memory.py:76-83`
- **Evidence:** Hardcodes a copy of the closed enums; authoritative home is `check_consistency.ENUMS` (check_consistency.py:42-61). Does NOT import it. Copy DRIFTED — adds `"won't"`, which canonical `ENUMS["moscow"]` (`{must,should,could,wont}`) disallows; `won't` is functionally inert (check_consistency would emit `unknown_enum` for any stored `won't`, so it never matches a real value). 4 sibling scripts already `from check_consistency import` (shared-home pattern established). Downgraded: inert member + 3 very stable closed enums = maintainability concern, not a live bug. Script-vs-LLM split itself is correct (persona-label detection rightly LLM-side, 74-75/166-174).
- **Fix:** `from check_consistency import ENUMS`; build the frozenset as `ENUMS["scope"] | ENUMS["moscow"] | ENUMS["horizon"]` (lowercased); drop stray `"won't"`.

### GROUP D — Safety-fence accuracy (1 docstring; locked-scope respected)

**safety-fence-1** · `low` · fs_guard docstring claims "every real write chokepoint" is fenced, but `spec_graph.write_snapshot` + `build_traceability_matrix` bypass the guard
`scripts/fs_guard.py:5-8`
- **Evidence:** Docstring asserts universally. Two real writers do NOT call `assert_under_docs_product`: spec_graph.py:543 `write_snapshot` (snapshots) and build_traceability_matrix.py:111 (matrix). The OMISSION is a LOCKED plan decision (phase-08:28/34 scoped the assert to 3 chokepoints + memory writers) — not a bug. What IS wrong: the docstring's inaccurate universal claim could mislead a maintainer. No current escape vector (both leaf names deterministic, `root` resolved upstream). Documentation-accuracy / defense-in-depth.
- **Fix (prefer a):** (a) tighten docstring to "fence covers SCRIPT writers accepting caller-influenced paths (visual/export/template/memory); write_snapshot + build_traceability_matrix write deterministic hard-coded paths and are intentionally un-fenced." Or (b) route those two through the guard (one line each). Prefer (a) to honor locked 3-writer scope.

### GROUP E — Error-surfacing UX (script mains)

**scripts-correctness-1** · `low` (was medium) · `FenceError` (subclass of `Exception`, not `ValueError`) escapes writers' `except ValueError` handlers as a bare traceback
`fs_guard.py:30` + `generate_templates.py:358,462` + `render_export.py:285,~259` + `visualize.py:276` / `render_html.py:1025-1028`
- **Evidence:** `issubclass(FenceError, ValueError)` is False (empirically). Three new fence callers raise it before the write but mains only catch `ValueError` (visualize also `FileNotFoundError`, and only wraps `_load_baseline` — HTML write paths reach `render_html._write_visual` with no handler). Empirically reproduced for all three: monkeypatched assert → `UNCAUGHT EXCEPTION: FenceError` + exit 1, not clean JSON finding. Violates fail-soft contract (test_malformed_input_failsoft.py; generate_templates.main comment 359-360). NEW path; test_fs_guard.py tests the function but never through a CLI main(). Downgraded: failure is SAFE (fence raises BEFORE any write — no out-of-tree bytes); harm is poor error UX (traceback vs friendly message); realistic trigger is a crafted/symlinked `--root` (slug/parent traversal blocked upstream as ValueError) — adversarial misuse, not routine PO error.
- **Fix:** `except (ValueError, FenceError)` in generate_templates.main, render_export.main, visualize.main — surface as the same `invalid_input` JSON/non-zero. Or make FenceError subclass ValueError (explicit catch preferred for intent clarity).

### GROUP F — Register formatting / id-allocation edge cases (decision_register.py)

**scripts-correctness-3** · `low` · `_supersede_in_place` drops the blank line between frontmatter fence and heading
`scripts/decision_register.py:248-258`
- **Evidence:** `_RECORD_RE`'s `\n---\s*\n` greedily eats the closing-fence newline + the following blank line; `_flip` rebuilds `---\n{body}` → `---\n## DEC-1` (one newline) vs original `---\n\n## DEC-1`. Re-parse/`_title_from_body` still work (cosmetic round-trip churn, not a parse break) — but a committed file's formatting silently churns on every supersede.
- **Fix:** Reinsert the blank line on reconstruction (e.g. `---\n{new_fm}\n---\n\n{body.lstrip(chr(10))}`) or capture inter-fence whitespace so it round-trips byte-stably. Low priority — non-functional.

**scripts-correctness-4** · `low` · `alloc_id` can reuse a DEC id when a record with a parseable id but corrupt YAML is fail-soft-skipped
`scripts/decision_register.py:91-112,126-137`
- **Evidence:** `parse_decisions` skips records with unparseable YAML / bad-grammar id (94-100, fail-soft by design). `alloc_id` derives `max(used)+1` only from returned records (132-136); `append_decision` dup-guard also reads `existing_ids` from parse_decisions (198). So DEC-1 valid + DEC-5 corrupt → alloc returns DEC-2, and a later repair of the corrupt block yields two DEC-5 (breaks "never reused" lineage). Requires abnormal corrupt-block state; fail-soft parsing is a locked decision → edge-case integrity gap.
- **Fix:** When allocating, scan raw text for `^id:\s*DEC-(\d+)` across ALL `---`-fenced blocks (incl. unparseable) for the max; or surface a `parse_error` finding so PO repairs before allocation.

### GROUP G — Test-quality (tighten / de-tautologize tests; no production code change)

**test-quality-1** · `low` (was medium) · `test_last_validated_honours_fence` is tautological — re-tests `assert_under_docs_product`, not `write_last_validated`
`scripts/tests/test_judgment_cache.py:350-359`
- **Evidence:** Docstring promises to test the marker writer's fence wiring, but body calls `assert_under_docs_product(tmp_path/"escape.json", proj)` directly (already covered in test_fs_guard.py:53-60). Deleting the fence at judgment_cache.py:399 leaves this test green. No test covers the negative path (grep: only happy-path snapshots). Downgraded: chokepoint IS tested elsewhere + writer happy-path tested; only negative-path coverage of one call site missing.
- **Fix:** Call `jc.write_last_validated(proj, Path('/tmp/escape.json'))` inside `pytest.raises(FenceError)` to actually exercise line 399.

**test-quality-2** · `low` · New memory-store writers have no negative fence test; `FenceError` imported but unused (dead-import smell)
`scripts/tests/test_behavioral_memory.py:39` (+ test_decision_register.py:35)
- **Evidence:** `from fs_guard import FenceError` never referenced (grep: only import line). Module docstrings claim "a store write can never escape docs/product/" yet tests assert only happy-path `is_relative_to(...)`. Happy-path assertion would still pass if the `assert_under_docs_product` call were deleted from the writer. Unused import = fingerprint of a planned-but-omitted negative test.
- **Fix:** Remove the unused imports, OR add one negative test per writer (monkeypatch path helper / tampered root → `pytest.raises(FenceError)`).

**test-quality-3** · `low` · `test_status_lists_added_and_removed` name/docstring claim "removed" but only the added half runs
`scripts/tests/test_status.py:94-121`
- **Evidence:** Body only creates a new story + asserts `in report['added']`/`['unvalidated']`; never deletes a node, never asserts `report['removed']`. status.py:155 `unvalidated = sorted(set(field_changed)|set(added)|set(removed))` → the `removed` branch is untested (a regression dropping `set(removed)` would pass).
- **Fix:** After baseline, unlink an existing story, rebuild, assert id in `removed` AND `unvalidated`. Or split + rename.

**test-quality-4** · `info` · judgment_cache `lang` key segment never exercised — a lang flip not proven to miss
`scripts/tests/test_judgment_cache.py` (n/a)
- **Evidence:** Key grammar (judgment_cache.py:118-126 `_lang_segment`) is a real branch ("a lang flip must miss") but no test flips lang; test_key_single_node checks only prefix + body_hash. (Distinct from behavioral po-style lang-keying, which IS tested in test_po_style_lang_keyed.) Uncovered branch of a deterministic key.
- **Fix:** Store a verdict under one node lang, rebuild with node/PRODUCT lang flipped en→vi, assert `check()` reports stale (full miss).

**test-quality-5** · `info` · self-correction `last_seen` monotonicity assertion is a no-op within one test second
`scripts/tests/test_behavioral_memory.py:134`
- **Evidence:** Asserts `rows[0]['last_seen'] >= first_seen`; `_now()` is second-granular and both calls run in the same wall-clock second → `>=` trivially satisfied without proving the refresh. The frequency-increment half (1→2, no dup row) IS load-bearing, so info-only.
- **Fix:** Seed first row with an explicitly older `last_seen` (write JSON / monkeypatch `_now`) and assert strict inequality; or drop the weak `>=`.

---

## 4. Refuted on verification

None. All surfaced findings verified `is_real=true` (0 refuted).

---

## 5. Unresolved questions (owner decision)

1. **scripts-correctness-2 reorder** — confirm preferred fix shape: append-then-flip reorder vs validate-up-front vs single read-modify-write. (Behavior-equivalent; pick per code-style preference.)
2. **safety-fence-1** — owner choice: (a) fix docstring only (honors locked 3-writer scope) vs (b) also route write_snapshot + build_traceability_matrix through the guard for defense-in-depth. Plan locked the 3-writer scope; (b) extends it — needs explicit OK.
3. **references-integrity-2 / test-quality-4/5** — info-level; ship as-is or batch into the doc/test cleanup? Defer-OK.
4. **dry-and-split-2 `won't` removal** — confirm dropping the inert `"won't"` member (canonical moscow uses `wont`); no behavioral change but it is an enum-membership edit.
