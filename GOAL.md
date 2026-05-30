# GOAL — Hardcore Dual-Skill Review (15 cycles)

Durable resume anchor for an in-progress, multi-cycle hardcore review of two Claude Code skills
(**`cleanmatic:product-spec`**, **`cleanmatic:claude-pack`**). Per-cycle reports under `plans/reports/`
are **gitignored** (`.gitignore:61`) → this file is the authoritative, self-contained record.
Owner conversation = Vietnamese; this file is English to match the repo docs.

---

## Mission

Max-recall, whole-skill review of both skills, up to **15 cycles**. Each cycle re-runs the same hardcore
review, carries forward prior findings, and **finishes all fixes before the next cycle begins**.

### Locked operating parameters (do NOT re-ask)
- **Scope:** whole skill — every script, reference, template, `SKILL.md`, tests, `install.sh`.
- **Termination:** converge-then-stop — stop after **2 consecutive zero-finding cycles**; hard cap **15** (raised from 10 on 2026-05-30).
- **Fix autonomy:** auto-fix safe findings; **interview** only on risky/ambiguous or locked-decision items.

### Locked design decisions (carry across all cycles — never silently reverse)
1. **scripts/schemas opt-in.** Top-level `.claude/scripts` + `.claude/schemas` are CK internals; not shipped by default (`--include-scripts`/`--include-schemas`).
2. **Commit CK files, seed manifest `agents: []`.** `.claude/{agents,scripts,schemas}` tracked so the repo self-packs reproducibly.
3. **Bundle hygiene:** drop only `plans/` (in `ALWAYS_DROP_DIRS`); keep `eval/`+`tests/`.
4. **`follow_shared`** dir-granular (segment-0), not file-granular — documented, intended.
5. **Safety filter:** case-insensitive across all 3 layers (exact/dirs/patterns); basename + full-arcname.
6. **Installer:** full SemVer-2.0 precedence; recipient per-skill hooks opt-in (`RUN_HOOKS=1`/`-RunHooks`).

### Expanded scope (Cycles 3→15)
v2 product-spec feature shipped before C7 → from C3 on, scope covers the new feature + regression it introduced + ongoing regression sweep on all prior changes.

---

## Progress

| Cycle | Status | Result (count → fixes) |
|-------|--------|------------------------|
| 1 | ✅ DONE | 31 findings, all fixed |
| 2 | ✅ DONE | 23 + 3 late, all fixed |
| 3 | ✅ DONE | 30 (0 CRIT) → 29 full + F15 partial (closed in C4); all product-spec export+viewer |
| 4 | ✅ DONE | 29 → 22 distinct fixes, all applied. 26 agents / ~2.1M tok |
| 5 | ✅ DONE | 39 (0 CRIT/HIGH) → all fixed. Sweep +11. ~31 agents / ~2.0M tok |
| 6 | ✅ DONE | 28 (1 HIGH) → all fixed; caught 3 C5-introduced regressions |
| 7 | ✅ DONE | 5 (3 CRIT · 2 MED) → all fixed. Lean v2-diff pass. 9 agents / ~784K tok |
| 8 | ✅ DONE | 15 → 11 fixes + 3 refuted. Full overlap pass. 23 agents / ~1.88M tok |
| 9 | ✅ DONE | **101** (3 CRIT · 13 HIGH · ~13 MED · ~72 LOW) + 4 extra crash sites → all fixed; 5 refuted. 63 agents / ~4.9M tok |
| 10 | ✅ DONE | **67** (0 CRIT · 1 HIGH · ~14 MED · ~52 LOW) → all fixed; 3 refuted. Watch = C9 regressions. 57 agents / ~4M tok (1st launch throttled, re-ran) |
| 11 → 15 | ⏸️ PENDING | Full C7-style run mode (below). Stop after 2 consecutive zero-finding cycles; cap C15 |

**Convergence:** NOT converged (counter = 0; C10 had 67 findings). BUT trending down: C9 had 3 CRIT + 13 HIGH; **C10 had 0 CRIT + 1 HIGH** — the C9 CRITICALs held and C10 was mostly "second-order" cleanup (stale callers of the C9 hoists, incomplete hoists, doc-drift on new behaviour) + a few new edge cases. The regression-watch caught real C9-introduced bugs (Windows-separator in the tar-slip containment → false E021; userinfo-scrub stop-at-first-@). Convergence plausibly near if C11 keeps trending; cap C15.

**Test state (green):** `product-spec` **382** (was 351; +31 C10 regression tests) · `claude-pack` **117** (was 109; +8 C10 regression tests). (as of C10 close, 2026-05-31).
Run: `PYTHONPATH=.claude/skills/<skill>/scripts ./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/<skill>/scripts/tests -q`

**Reports (local, gitignored — may be absent on fresh clone):** C1 `.claude/skills/claude-pack/plans/reports/cycle-01-…`; C2/C3/C5/C6 `plans/reports/cycle-0{2,3,5,6}-…`; C4/C7/C8 condensed below only.

---

## Run mode for Cycles 11→15 (Cycle 8+ config, LOCKED 2026-05-30)

Owner directive: remaining cycles run the **FULL C7-style review**, not a narrow correctness-only pass — C7 proved the file-partitioned Workflow surfaces real CRITICALs the build-review missed.

- **Engine:** the **Workflow tool**, file-partitioned finders → consolidate/dedup → per-file verify (3-state) → sweep → main-agent rank → interview → fix. Durable run mode for every remaining cycle.
- **Angles:** ALL 9 (correctness + cleanup + altitude) every cycle. A cycle is "clean" only when finders + sweep return zero across all angles. (Overrides the old "convergence pass = correctness-only" rule.)
- **Relaxations vs C7:** (1) file ownership MAY overlap (angle-finder + subsystem-finder on one file) → consolidate must dedup by `file:line` + same-mechanism; (2) scan-agent count MAY scale up — recall first, no hard cap, quota permitting.
- **Token posture:** prefer a fresh 5-hour window. If exhausted mid-cycle, checkpoint here + resume via `resumeFromRunId` (completed agents cache at 0 cost).

### LOCKED REFUTED list — do NOT re-flag (adjudicated C7/C8; flag only on proven NEW regression)
- `checked_at`/`today`/`root` in `*_anchors.py` + `time_advisory.py` + competitive_drift output = **intended provenance** (documented `validation-rules-spec.md:186` + `frontmatter-and-id-spec.md:231`; sits beside `root`). G-A4 binds the **payload**, which `build_anchors` produces without it. NOT a determinism bug.
- New v2 schema fields optional → v1 back-compat preserved. `depends_on` cycle detection = iterative 3-color DFS. ASCII = deterministic text-summary downgrade (not deleted). competitor `url` `private:` prefix ignored (OpSec). Mermaid graph-views bundle Mermaid's OWN DOMPurify (exempt from the "no SKILL body-sanitizer" contract). `generate_templates.session_used` is a TESTED library mechanism — keep (rule-3).

### Carry-forward regression surface (scrutinize for over/under-guarding + stale callers)
- **C10:** Windows-safe path containment via `Path.relative_to` in `manifest_loader` (skills/agents/rules/hooks/_shared) + `selection.py` (replaced the POSIX `'/'`-prefix test) + `_check_path_safety` extract; `manifest_io` userinfo scrub `[^/]*@` (last-@); `render_ascii.persona` cell key `str(p)`; `assemble_digest._entry` uses `resolve_ac`; `spec_graph.index_artifacts` keys by `_scalar_id` + `ID_SENTINELS`; `check_consistency` dup_id skips sentinels + via `_f`; `_status_inconsistency` brd_goals guard; check_traceability dropped the duplicate brd_goals invalid_type (now check_consistency-only); `render_html.competition` wires `resolve_competition` + drops `_DASHBOARD_HORIZONS`; `generate_templates` load_values OSError/non-dict + `_prd_slug_from_id` + id/slug conflict raise; `render_export._heading` CR/LF collapse; `diff_graphs` str-persona; `build_manifest --write` non-dict-stdin guard; `safety_check` backslash-normalize + drive-letter predicate + walk OSError guard; cli `--dry-run` no FS side-effects + `over_max_size: null` + `resolve_max_size` extract; `templates.render_template` OSError→TemplateError; installers re-validate recipient `$REL` traversal + walk bundle root. **Watch:** the relative_to containment on case-insensitive/symlink FS; the persona str() key vs any other raw-key renderer site.
- **C9:** `spec_graph._scalar_id` (id → str|`<missing-id>`|`<invalid-id>`) + `_scalar_link` (epic/prd → str|None) + node_type coerce + build_edges brd_goals guard + non-str competitor url→None; shared hoists `make_finding`/`HORIZON_ORDER`/`moscow_story_counts`/`competitor_id_to_name`/`resolve_ac`/`ID_PATTERN_BY_TYPE`/`COMP_ID_PATTERN`; `frontmatter_parser` catches `(YAMLError, ValueError)` + `UnicodeDecodeError` + empty-block message; renderer unhashable-key guards (`_hashable`/isinstance) across risk/competition/dashboard/roadmap/time + `_parity_label`/`_threat_label`; `generate_templates` content-only types + PRD slug derive; claude-pack **tar-slip 3-layer containment** (validate all categories + `_include_shared`, selection chokepoint, `is_dropped` traversal drop) + `MANIFEST_E102` (schema_version type) + tightened `SEMVER_RE` (strict 2.0, rejects leading zeros) + `manifest_io` userinfo scrub + `errno.EXDEV` + `args` epoch >=0/ascii guard + install.sh base-10 semver + installers walk bundle root (README/CLAUDE installed). **Watch:** the strict SEMVER_RE now rejects a leading-zero version (intended behavior change); the installer bundle-root walk.
- **C8:** `spec_graph._as_id_list` (depends_on coerce; every consumer assumes a clean list) + `_closure` returns `out-{start}`; `competitive_drift_anchors` None-parity excluded; `generate_templates.fill_defaults` None-restore for LIST/MAP fields + `newline=""` write; `manifest_io.atomic_replace` EXDEV restores backup; `selection` `_include_shared` non-list→`[]` guard + arc-collision WARN; `render_html` `(unrated)` escapes.
- **C7:** `check_consistency` enum guards `isinstance(list,dict)→invalid_type` at 3 sites; `migrate_multidim_fields` `newline=""` + per-file newline detect; `render_mermaid.roadmap` `[:8]` cap removed (watch huge horizon).
- **C5/C6:** shared `match_hooks` (validate + selection); `spec_graph` hoists (`parents_of`/`children_of`/`_closure`, `CHILD_TYPE_FOR_PARENT`, `matching_child_counts`, `diff_graphs`); explorer multi-parent payload; `render_export` i18n; horizon facet+label.

---

## Per-cycle record (condensed — survives loss of reports)

**Cycle 1 (31, all fixed):** CRITICAL secret-leak via case-sensitivity → safety filter case-insensitive; 3× stored-XSS in self-contained HTML viz → `_safe_label`/`_safe_id` + escape `<`/`>`; `.gitignore` excluded `claude-pack/assets/` (installer templates+manifest) → skill non-functional on fresh clone, fixed; `follow_shared` dead code; MANIFEST symlink hash-leak; installer macOS `shasum` + downgrade split-brain; `brd_goals` per-char iteration; +18.

**Cycle 2 (23+3, all fixed):** C1 regressions — `max_size_bytes:false` bricked builds (reject bool); mermaid HTML double-escaped `&` (escape only `<`/`>`). Packaging CRITICAL: seed manifest + default scripts/schemas untracked → fresh-clone abort (E071) → opt-in flip + commit CK files + `agents:[]`. Bundle leak `plans/` → `ALWAYS_DROP_DIRS`. Non-det hook pick → sorted + `E074`. Installer: version regex anchored, `LC_ALL=C` semver, unparseable-version→SKIP, split STALE_KEPT/WROTE counters. ASCII heatmap `other` column + shared `_grid()`. Docs synced.

**Cycle 3 (30 → 29 full + F15 partial):** product-spec export+viewer (`6009c50`), 0 CRIT. Owner: A=viewer **artifact-type** vocab · B=emit-once+dedup, unresolved→error (exit 2) · C=`llm`+`html` hard-reject · F10=escape-all-`<`. Clusters: layers-by-type, VISION/BRD/PRODUCT singleton split, ASCII explorer forwarding, parse-once DRY. F15 facet/search hoist deferred → done in C4.

**Cycle 4 (29 → 22 fixes, all applied):** owner "fix all, no defer". Q1=fail-loud `--layers` (validate token vs surface vocab + raise on empty-after-filter); Q2=ASCII explorer orphan-root reparent (parity w/ HTML); Q3=hoist facet/search engine into `_BODY_RENDER_JS` (closes F15, verified via node DOM-stub). HTML export frontmatter leak fixed. H4 clarified: "no SKILL body-sanitizer" — Mermaid's bundled DOMPurify is third-party/exempt.

**Cycle 5 (39, all fixed):** owner "fix all". 0 CRIT/HIGH. Q1=fail-loud `--layers` BOTH surfaces (export `all`-branch raises when layers strip pre-existing content; viewers raise on empty-after-filter at `_dispatch_body_view`); Q2=**multi-parent** explorer (payload `parent`→`parents`; PRD under each goal; cycle guard); Q3=qualify CLAUDE.md "no network" claim (Mermaid CDN fallback, doc-only); Q4=fix all incl. pre-existing. DRY hoists to `spec_graph` (`CHILD_TYPE_FOR_PARENT`, `matching_child_counts`, `diff_graphs`, `parents_of`). YAML-safe frontmatter scalars. Sweep +11.

**Cycle 6 (28, all fixed):** full pass (owner override), 0 CRIT. **Caught 3 C5-introduced regressions:** HIGH — C5 basename-only hook index diverged from `validate()`'s rglob (path-qualified/glob hook silently dropped) → ONE shared `manifest_loader.match_hooks()`; MED — bodyless story AC-double under `--compact-mode llm` → shared `_content_with_ac`; MED — horizon facet had no label → i18n. Added `spec_graph.children_of`/`_closure`. 3 micro-perf accepted (YAGNI).

**Cycle 7 (5, all fixed):** lean v2.0.0-multidim-diff pass via Workflow (5 disjoint finders). Owner "no cut off". **3× CRITICAL** — `check_consistency` enum membership (`v not in <set>`) raises `TypeError` on an unhashable YAML value (`status:[draft]` / competitor `threat:[high]` / risk `impact:[high]`); fixed with `isinstance(list,dict)→invalid_type` guard at 3 sites (matching `_check_competitive_parity`). MED — migration dropped CRLF (`read_text`/`write_text` translated) → `newline=""` + per-file newline detect. MED — `render_mermaid.roadmap` `[:8]` truncated each section → cap removed. +7 tests (314→321); acme-shop `strict_gate` 0/0.

**Cycle 8 (15 → 11 fixes + 3 refuted):** FULL whole-skill via Workflow (13 overlap finders). Owner: Q1=**REFUTE** the `checked_at` cluster (intended provenance) + fix LOW doc-drift; Q2=fix all 4 minor. Fixes — `spec_graph._as_id_list` (depends_on: crash on mixed-list + char-split on bare-string, CRIT+HIGH) + `_closure` `-{start}` (self-descendant, HIGH); `competitive_drift` None-parity excluded (HIGH); `generate_templates.fill_defaults` None-overwrite restore (CRIT) + `newline=""`; `manifest_io.atomic_replace` EXDEV restores backup (CRIT, claude-pack); `selection` `_include_shared` guard (HIGH) + arc-collision WARN (MED); `render_html` `(unrated)` escapes; `session_used` kept (rule-3), docstring overclaim fixed. +7 tests (ps 321→326, cp 78→80). The overlap pass caught 5 CRIT + 6 HIGH the prior 6 cycles missed.

**Cycle 9 (101 → all fixed; 5 refuted):** FULL C7-style via Workflow (16 finders: 8 product-spec subsystem + 2 claude-pack + 4 cross-cutting overlap + 2 references), all 9 angles, per-file verify, 2 sweep. 63 agents / ~4.9M tok. Owner: fix ALL 101 (no accept) · TIGHTEN SEMVER_RE strict-2.0 · installers INSTALL README/CLAUDE. **3 CRITICAL:** (1) **tar-slip / arbitrary-file-write** (claude-pack) — traversal guard applied only to `extra`; `skills`/`agents`/`rules`/`hooks`/`_include_shared` emitted a `..` arcname into the tarball; fixed in 3 layers (validate containment all categories, selection chokepoint, `is_dropped` traversal drop). (2) **gate crash on unquoted out-of-range date** — PyYAML raises bare `ValueError` (not `YAMLError`); `frontmatter_parser` now catches `(YAMLError, ValueError)`. (3) **`epic`/`prd`/`id` list/dict poison the graph** (carry-forward: C7/C8 coerced depends_on+brd_goals but not the scalar links) → `spec_graph._scalar_id`/`_scalar_link` single-source coercion. **13 HIGH** crash-safety family (matrix joins, renderer unhashable-keys, frontmatter UnicodeDecodeError, generate_templates content-only types + PRD slug, brd_goals char-split). **~13 MED** (credential leak in MANIFEST.json scrubbed, schema_version/dup guards `MANIFEST_E102`, install.sh octal-semver, README/CLAUDE install). **~72 LOW** doc-drift + DRY hoists + dead-code + edge-cases. **PLUS 4 extra crash sites** found in fix-verification repro (ascii/mermaid roadmap+time horizon-key, html `_parity_label`/`_threat_label` set-membership). REFUTED 5 (e.g. render_html chrome-fold = deliberate divergence, not a bug). +25 product-spec / +31 claude-pack regression tests (326→351, 78→109); acme-shop strict_gate 0/0; 14/14 viz combos OK. Report: `plans/reports/cycle-09-…`. Executed by lead foundation + 5 file-partitioned sub-batches (no overlap).

**Cycle 10 (67 → all fixed; 3 refuted):** FULL C7-style via Workflow (16 finders), all 9 angles, per-file verify, 2 sweep — PRIMARY WATCH = regressions from the C9 fixes. 1st launch THROTTLED (18 subagents got synthetic empty completions — API ceiling right after the heavy C9 window, 0 findings = NOT a clean cycle); re-launched minutes later → succeeded. 57 agents / ~4M tok. **0 CRITICAL** (C9 CRITICALs held) **· 1 HIGH** = `render_ascii.persona` cell key used the raw persona value (crash on unhashable + silent mis-count) — the C9 unhashable-key sweep missed this site → `str(p)` key. **C9-regressions caught** (watch earned its keep): Windows `'/'`-prefix in the tar-slip resolve-within-base → false E021 on every valid skill on a Windows builder (→ `relative_to`); userinfo-scrub `[^/@]*@` stopped at first '@' → password-with-@ leak (→ `[^/]*@`); + many stale-caller/incomplete-hoist cleanups (assemble_digest resolve_ac, index_artifacts `_scalar_id`, `<invalid-id>` sentinel leak + false dup_id, orphaned `_DASHBOARD_HORIZONS`, inline `resolve_competition`, `_status_inconsistency` brd_goals char-split, duplicate brd_goals invalid_type). **~14 MED** (build_manifest non-dict-stdin crash, load_values OSError/non-dict, render_export CR/LF heading injection, diff_graphs mixed personas, safety_check backslash/drive-letter, cli dry-run side-effects/over_max_size). **~52 LOW** doc-drift + DRY + dead-code + defensive. **REFUTED 3** (SEMVER strict OK, exit-code divergence intentional, broadened-catch safe — held the C9 decisions). **Judgment:** #11 depends_on bare-scalar kept silently-coerced (reverting C8 single-source would be risky multi-file) + documented — no behavior change. +31 product-spec / +8 claude-pack tests (351→382, 109→117); acme-shop 0/0; tar-slip repro: rejects `..` all 4 categories + valid nested skill no false E021. Report: `plans/reports/cycle-10-…`. Lead render_html crash-safety + 4 file-partitioned sub-batches.

---

## How to resume

1. Re-read this file (carries all prior context + carry-forward surface + REFUTED list).
2. Run the cycle's review (finders → per-file verify → sweep) per the C8+ run mode above.
3. Fix all findings before the next cycle (auto-fix safe; interview risky/locked-decision).
4. Keep both test suites green; add regression tests for new behaviour.
5. Update this file's Progress + Convergence; write/refresh a report under `plans/reports/`.
6. Stop after 2 consecutive zero-finding cycles, or at Cycle 15.

---

## Shipped features (durable review surfaces)

**product-spec v2.0.0 — multi-dimensional impact (2026-05-30, C7's primary surface).** RISK (PRD risks + enum impact/likelihood/status + `risk_high_ratio`/`risk_blindspot` + HTML 3×3 grid) · TIME (`target_date` ISO + `depends_on` edge w/ iterative 3-color DFS + `dep_dangling`/`dep_order`/`time_child_late` + out-of-gate `time_advisory.py --today` + `time_realism` LLM + roadmap/gantt) · COMPETITION (`competitors`@BRD + `competitive_parity`@PRD + HTML parity matrix/threat heatmap + `competitive_drift` LLM + `private:`-URL OpSec) · impact-propagation (`downstream()` + LLM 1-liner) · ASCII→HTML-native default downgrade · v1→v2 migration + back-compat. Plan: `plans/260530-0503-product-spec-multidim-impact-v2/plan.md` (build DoD gates G-A..G-H in `…/goal.md`). Commits (branch `feat/product-spec-v2-multidim`): `c80aa3a` RISK · `3cde05d` TIME · `4951cce` COMPETITION · `9ad5584` impact+migration · `5a5ff74` ASCII · `8f1f5ac` docs+2.0.0. Tests 215→314. SKILL.md 1.1.0→2.0.0.

**product-spec v1.1.0 — read-once Export + interactive Viewer (2026-05-29, C3–C6 surface).** `--export` (read-once md/print-HTML) + `--viz board`/`explorer` + unified ALL `--viz` HTML under one design system (marked+DOMPurify vendored+inlined, print-CSS, theme). New scripts: `assemble_digest.py`, `render_export.py`, `render_board.py`, `render_explorer.py`, `install-vendor-markdown.sh`. Design doc + plan: `.claude/skills/product-spec/plans/…/260529-1504-product-spec-export-and-viewer/`. Tests 92→156.

---

## Open questions
None outstanding. All prior owner decisions locked + applied (folded into the per-cycle record above).
