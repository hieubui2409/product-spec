# Cycle 3 — Hardcore Dual-Skill Review — Findings (ALL 30 + 2 refuted)

**Date:** 2026-05-29 18:16 · **Status:** review DONE, **fixes DEFERRED** (owner: stop-at-report, wait for signal, usage limit)
**Skills:** `cleanmatic:product-spec` (primary) + `cleanmatic:claude-pack` (regression-only)
**Primary surface:** the new export + viewers feature (commit `6009c50`, +2673 LOC)
**Method:** Workflow `wf_35ec1289-dda` — 9 finder angles → 1-vote 3-state verify → gap sweep. 42 agents, ~2.98M subagent tokens, 834s.
**Pipeline stats:** 33 raw → 28 deduped → **26 verified** (CONFIRMED/PLAUSIBLE) + **4 sweep** = **30 findings**; **2 REFUTED**.
**Baseline tests (green at review start):** product-spec **156** · claude-pack **77**.

> All 30 reported here (per owner request — not the top-15 the pipeline ranked). Every finding had ≥1 non-REFUTED verifier vote with empirical reproduction on the `valid-spec` fixture. **No code changed this cycle.**

---

## Severity / category roll-up

| Sev | Correctness | Efficiency | Reuse | Simplification | Altitude | Total |
|-----|:-:|:-:|:-:|:-:|:-:|:-:|
| HIGH | 5 | – | – | – | – | **5** |
| MED | 6 | 2 | – | 1 | 2 | **11** |
| LOW | 3 | 2 | 4 | 4 | 1 | **14** |
| **Total** | **14** | **4** | **4** | **5** | **3** | **30** |

claude-pack: **0 findings** (no regression surfaced — unchanged since Cycle 2).
All 30 are in product-spec, all in the new feature (commit 6009c50). **Zero CRITICAL.**

---

## Master list (ranked, most-severe first)

| # | Sev | Cat | Verdict | File:Line | One-line |
|---|-----|-----|---------|-----------|----------|
| F1 | HIGH | correctness | CONFIRMED | render_explorer.py:77 | Explorer Flat-tabs **'goal' tab permanently empty** (item.layer='brd' vs tab key 'goal') |
| F2 | HIGH | correctness | CONFIRMED | render_ascii.py:307 | `--layers goal` (board/explorer) **drops every goal card** (filter uses brd bucket) |
| F3 | HIGH | correctness | CONFIRMED | render_export.py:151 | `--export` **no guard** for unresolved selection → empty doc, exit 0 |
| F4 | HIGH | correctness | CONFIRMED | assemble_digest.py:191 | `--export PRODUCT` **drops product content** + emits misleading `--layers` warning |
| F5 | HIGH | correctness | CONFIRMED | render_export.py:187 | `--compact-mode llm` + `--format html` **silently broken** (markers stripped, no .md artifact) |
| F6 | MED | correctness | CONFIRMED | render_export.py:154 | Typo'd/unknown ID → **silently empty** export, exit 0 (same root as F3) |
| F7 | MED | correctness | CONFIRMED | render_ascii.py:359 | ASCII explorer **discards `--layers`** (not forwarded to `tree()`) |
| F8 | MED | correctness | CONFIRMED | assemble_digest.py:77 | `--export VISION` **double-renders** vision → duplicate `#vision` anchors + TOC |
| F9 | MED | correctness | CONFIRMED | visualize.py:165 | `--layers` help advertises **broken `goal` token** (cluster w/ F1/F2) |
| F10 | MED | correctness | CONFIRMED | render_html.py:186 | `embed_spec_data` not neutralizing `<!--` → **WHATWG double-escape breaks page render** (not XSS) |
| F11 | MED | correctness | CONFIRMED | render_explorer.py:79 | Table-tree **stale depth** after layer filter → Tree vs Table disagree |
| F12 | LOW | correctness | CONFIRMED | assemble_digest.py:178 | `--export all --layers X` **floods header** with one warning per excluded node |
| F13 | LOW | correctness | CONFIRMED | render_board.py:63 | Layer facet UI chip shows **'brd'** for goal cards (cluster w/ F1/F2/F9) |
| F14 | LOW | correctness | CONFIRMED | visualize.py:175 | `--filter-wont` help **understates scope** (also affects board/explorer) |
| F15 | MED | simplification | CONFIRMED | explorer-shell.html:88 | board/explorer **duplicate ~50 lines** of JS helpers (facets/detail/search) |
| F16 | MED | efficiency | CONFIRMED | render_export.py:153 | **Double `load_artifacts`** — build_graph re-parses then export parses again (2×) |
| F17 | MED | efficiency | CONFIRMED | visualize.py:127 | **Same double-parse** on board/explorer HTML path (2×) |
| F18 | MED | altitude | CONFIRMED | explorer-shell.html:43 | Detail-panel CSS **duplicated + already divergent** (explorer missing `:first-child` margin reset) |
| F19 | MED | altitude | PLAUSIBLE | assemble_digest.py:3 | Docstring/CLAUDE.md **overstate "shared assembler"** — viewers don't use `build_digest` |
| F20 | LOW | reuse | CONFIRMED | render_export.py:147 | `_now_iso` re-implements `spec_graph._now` (timestamp formula **8× repo-wide**) |
| F21 | LOW | reuse | PLAUSIBLE | render_board.py:30 | artifact-by-id loop **triplicated** (board/explorer/digest) |
| F22 | LOW | reuse | PLAUSIBLE | render_board.py:86 | body-view **shell preamble** duplicated across 3 renderers |
| F23 | LOW | simplification | CONFIRMED | render_html.py:171 | **Dead code** `_safe_href`/`psSafeHref` (never invoked; tests assert unused code) |
| F24 | LOW | simplification | PLAUSIBLE | render_board.py:83 | shell shape `read→values→update→substitute` duplicated (overlaps F22) |
| F25 | LOW | simplification | CONFIRMED | assemble_digest.py:168 | vision/brd singletons **layer-gated twice** (redundant w/ line 191 filter) |
| F26 | LOW | simplification | PLAUSIBLE | render_export.py:49 | `_section_body` empty-full / struct **fallback expressed twice** |
| F27 | LOW | efficiency | CONFIRMED | assemble_digest.py:143 | `ancestors`/`downstream` **rebuild adjacency per target** → O(targets·edges) |
| F28 | LOW | efficiency | CONFIRMED | render_export.py:159 | Markdown doc **rendered twice** (hash pass + real pass) |
| F29 | LOW | reuse | CONFIRMED | render_explorer.py:33 | id→body loop triplicated (overlaps F21) |
| F30 | LOW | reuse | CONFIRMED | render_board.py:90 | HTML-shell chrome plumbing copy-pasted 3× (overlaps F22) |
| R1 | LOW | correctness | **REFUTED** | render_board.py:53 | goals→'unassigned' under `--group-by moscow/horizon` (by-design, tested) |
| R2 | LOW | correctness | **REFUTED (contested)** | test_html_sanitize.py:78 | `<!--` primer test gap — refutation unsound, contradicts F10 |

---

## Fix clusters (for when fixes resume — fixes deferred this cycle)

The 30 findings collapse to **~9 fix units**. Several findings share one root; fix the root once.

### CLUSTER A — `goal → 'brd'` vocabulary collision (F1, F2, F9, F13) — HIGH
**Root:** board/explorer surfaces present the **artifact-type** vocabulary (`goal,prd,epic,story` — what the CLI help advertises, what the PO is taught) but filter/label off `assemble_digest.LAYER_FOR_TYPE` where `goal→'brd'` (the *export* doc-layer bucket). The two vocabularies disagree **only for goals**.
- F1: `render_explorer.py:77` item `layer="brd"`, but Flat-tabs tab key from `_LAYER_ORDER` is `"goal"` → `c.layer===activeTab` never matches → goal tab empty.
- F2/F9: `render_ascii.py:307` `_filter_by_layers` keeps `LAYER_FOR_TYPE.get(type) in want`; `--layers goal` → `'brd' in {'goal'}` False → all goal cards dropped. CLI help (`visualize.py:165`) advertises the broken `goal` token; undocumented `brd` is what works.
- F13: `render_board.py:63` card `layer="brd"` → Layer facet chip renders raw `'brd'`, no `'goal'` chip (also explorer facet).
**Decision needed (design):** the export path correctly uses bucket vocab (`vision,brd,prd,epic,story`) and is internally consistent — leave it. For the **viewers**, the cards ARE individual goal/prd/epic/story artifacts, so the natural + already-advertised vocab is **type names**. Recommended fix = make `_filter_by_layers` (viewer path only) + the `layer` field in render_board/render_explorer + Flat-tabs/facet labels all use the **artifact type** (`goal`), matching the CLI help. The viewer `--layers` and the export `--layers` then legitimately differ (different surfaces, each self-consistent with its own help). **This is honoring the documented contract, not reversing a user decision — but it touches user-facing viewer vocabulary, so flag for owner confirmation before applying.** Add i18n label for `goal`. Tests: none currently exercise `goal`/`brd` for viewers (gap).

### CLUSTER B — export selection guards / silent-empty (F3, F6, F4, F8, F12) — HIGH/MED
- **F3+F6 (one bug):** `assemble_digest._resolve_targets` (line 77) silently drops any ID not in graph; if all drop, `has_spec_content` False → not even Vision/BRD prepended → `build_digest` returns `[]`; `write_export` still writes a frontmatter-only doc and `main()` prints `{written}` + exit 0. Violates CLAUDE.md no-silent-failure. The sibling `--snapshot` path DOES guard (`visualize.py:98-101` raises with "Available: …"). Fix: detect empty/unresolved selection → error to stderr listing valid IDs, non-zero exit.
- **F4:** `--export PRODUCT` — `type:product` accepted as a target but `LAYER_FOR_TYPE` has no `product` key → `kept` filter (line 191) drops it (`None in layer_set` False), then the warning loop fires a misleading "`--layers [...] excluded the PRODUCT context`" even though no `--layers` was passed. User gets everything-except-PRODUCT.
- **F8:** `--export VISION` — `type:vision` accepted as explicit target (line 77 does NOT type-restrict like line 75's `all` branch) AND re-added as the singleton (lines 166-169) → **two** VISION entries → duplicate `## VISION` headings, **duplicate `<a id="vision">` anchors** (invalid HTML), ambiguous TOC.
- **F12:** warning loop (line 178) fans out one `_warning` per excluded *node*; `--export all --layers prd` on N goals/epics/stories → N near-identical warning blockquotes flood the doc header.
**Unifying fix:** restrict/clean `_resolve_targets` explicit branch + dedup digest entries by id + collapse warnings to one-per-excluded-type + add the empty-selection guard. Decide whether `--export VISION`/`--export PRODUCT` should (a) error ("context-only, use a goal/PRD/epic/story id"), or (b) emit the singleton once. **Owner-facing behavior choice → confirm.**

### CLUSTER C — `--compact-mode llm` + `--format html` (F5) — HIGH
`write_export` always renders markdown (with `<!-- COMPACT:id -->` markers) then, for html, wraps it into the JSON island and renders client-side via `marked.parse`+`DOMPurify.sanitize`. DOMPurify strips HTML comments → markers vanish in the rendered HTML; and there is no `.md` artifact on disk for the documented step-2 LLM rewrite. The two valid pairings (md+llm / html+struct) silently produce a meaningless cross-product. Fix: reject the combo at argparse/`write_export` with a clear message (no silent failure).
*(Verifier correction: marked v18 PRESERVES comments; it's DOMPurify's default config that strips comment nodes — outcome unchanged.)*

### CLUSTER D — viewer `--layers`/depth inconsistencies (F7, F11) — MED
- F7: `render_ascii.explorer()` accepts `layers` (line 355) but calls `tree(...)` without it (line 359) → ASCII explorer ignores `--layers` while ASCII board + HTML explorer honor it. Fix: forward layers (filter nodes before/within `tree`).
- F11: `render_explorer.build_payload` sets `depth` from type (`_DEPTH_BY_TYPE`) but `parent` is reconciled to the filtered set → with `--layers goal,story` a story arrives `parent='' depth=3`; Tree renders it as a root, Table-tree indents it 3.8rem under nothing. Fix: recompute depth from the reconciled parent chain over `present_ids`.

### CLUSTER E — `embed_spec_data` `<!--` primer (F10) — MED — ⚠ see contradiction
`render_html.py:186` neutralizes only `</` (→ `<\/`). It does NOT neutralize the `<!--` comment-open primer. Per the WHATWG script-data tokenizer, `<!--` … `<script`(+space/`/`/`>`) with no intervening `-->` enters **script-data-double-escaped** state, in which the island's own `</script>` does NOT close the element → the following `<script>{{markdown_libs}}</script>` bootstrap is swallowed as inert script-data → marked/DOMPurify never initialize → board/explorer blank, export stuck "Loading…". **Not XSS** (island is `application/json`, downstream is fixed template) — a broken render from valid PO prose (an unclosed HTML comment mentioning `<script`). Standard fix: escape every `<` as `<` in the JSON blob (JSON.parse round-trips; neutralizes `</script>`, `<!--`, `<script` at once) and update the existing close-tag test accordingly.

### CLUSTER F — help-text/contract accuracy (F14) — LOW
`visualize.py:175` `--filter-wont` help says "tree/roadmap/persona" but the flag is also threaded into board/explorer (drops `moscow=wont`/`scope=out` cards). One-line help fix (benign direction; contract string wrong).

### CLUSTER G — duplicate artifact parsing / perf (F16, F17, F27, F28) — MED/LOW
- F16+F17 (one root): `build_graph(root)` internally calls `load_artifacts` but discards the list; `render_export.write_export` (line 153) and `visualize._dispatch_body_view` (line 127) each call `load_artifacts` AGAIN → every export/board/explorer render parses every file **2×**. Fix: have `build_graph` attach/return artifacts (or `build_graph_with_artifacts`) and reuse.
- F27: `build_digest` calls `ancestors`/`downstream` per target; each rebuilds the full edge adjacency from scratch → `--export all` = 2·N full edge passes. Fix: build children/parents index once, pass in.
- F28: `render_markdown_doc` called twice (timestamp-free hash pass + real pass) — whole digest re-walked; differs only by the `generated_at:` line. Fix: hash a fixed-placeholder doc once, or slice the timestamp line.

### CLUSTER H — viewer-renderer DRY triplication (F20, F21, F22, F24, F29, F30) — LOW
The three body-view renderers (render_board / render_explorer / render_export) independently re-implement: (1) the `dt.now(utc)...isoformat()+'Z'` timestamp (8× repo-wide; `spec_graph._now` already exists, `render_export._now_iso` re-adds it) — F20; (2) the artifact-by-id ok-filter+`str(id)`-key loop (`_body_map`/`_maps`/`_index_artifacts`) — F21/F29; (3) the `body_render_values → update({lang_attr,title,product_name,generated_at}) → substitute` chrome preamble + `(graph.get('product') or {}).get('name') or '(unnamed)'` (4×) — F22/F24/F30. Fix: hoist a shared `index_artifacts()` + `chrome_values()`/`assemble_body_shell()` + reuse `spec_graph._now`. (Many of these overlap — one refactor closes 5 findings.)

### CLUSTER I — assorted simplification (F18, F15, F19, F23, F25, F26) — MED→LOW
- F18 (MED, real visual divergence): detail panel — board defines `.ps-detail*` as CSS classes incl `.ps-detail-body :first-child{margin-top:0}`; explorer hardcodes the same geometry inline AND omits the class + margin reset → a body starting with a heading renders extra top-margin only in explorer. Contradicts CLAUDE.md "one design system." Fix: move panel into `_viewer-head.html`.
- F15 (MED): board/explorer duplicate ~50 lines of facet/detail/search JS verbatim → hoist into `_viewer-head.html` (parameterize data-array + render-callback names). **Highest regression risk of the cleanup set (template refactor) — do under test guard.**
- F19 (MED, PLAUSIBLE): `assemble_digest` docstring + CLAUDE.md:115 + workflow-export.md:3 claim the digest "powers the viewers", but `build_digest` is imported only by render_export; viewers share only `LAYER_FOR_TYPE` + `_filter_by_layers`. Fix: narrow the docs (don't force-unify — shapes genuinely differ).
- F23 (LOW): `_safe_href`/`psSafeHref` dead (no caller; bodies go through DOMPurify, metadata via textContent/dataset). The `render_html.py:135` sink comment describes a non-existent href channel. Fix: drop both + tests + comment, or wire it.
- F25 (LOW): vision/brd singleton appends are layer-gated at lines 168/171 AND re-filtered at line 191 (redundant — proven byte-identical across 384 combos). Drop the inline guards.
- F26 (LOW, PLAUSIBLE): `_section_body` empty-`full` fallback and `struct` path both call `_struct_lines` from two spots (note: story `full` also appends AC, so not byte-identical — preserve AC on refactor).

---

## Refuted (2)

- **R1 — render_board.py:53 (REFUTED, sound).** Goals bucket to `unassigned` under `--group-by moscow/horizon` because `spec_graph._node_from_goal` deliberately omits those fields (BRD goals carry only id/title/metrics/status/owner). Asserted-intended by `test_render_viewer.py:63-64,99-100`; ASCII board does the same (no html/ascii drift). `unassigned` is the truthful column — rendering goals under `now`/`must` would invent data. Correct-by-design.

- **R2 — test_html_sanitize.py:78 (REFUTED — ⚠ CONTESTED, I disagree with the refutation).** The sweep flagged that the sanitize test never feeds the `<!--`+`<script` primer (the F10 gap). The verifier REFUTED it, arguing via Python's `stdlib HTMLParser` that `<!--`+`<script` is "not a hazard" and only `</script` can terminate a script element.
  **This refutation is unsound** and directly contradicts **F10 (CONFIRMED)**:
  - The F10 verifier explicitly noted Python's `HTMLParser` does **not** model the script-data-double-escaped state — so any "safe" result from `HTMLParser` is a false negative for real browsers. R2's empirical proof rests on exactly that non-conformant parser.
  - Per the WHATWG HTML tokenizer, after `<!--` (script-data-escaped) a `<script`(+ space/`/`/`>`) enters **script-data-double-escaped**, where `</script>` transitions back to escaped **without closing** the element. So the island's own `</script>` does NOT close → page-render break (F10's exact mechanism). `type="application/json"` does not change tokenization (only execution).
  - **Resolution:** treat F10 as real and the R2 test-coverage gap as **valid**. Definitive settlement needs a **conformant HTML parser / real browser** test (not `HTMLParser`). The robust fix (escape all `<` as `<`) closes both F10 and the R2 gap. ← top open question.

---

## Locked-decision / regression check (clean)

No finding re-flags a locked decision, and no Cycle-1/2 fix regressed. Verifiers REFUTE-gated against the 11 locked decisions + the Cycle-1/2 fixed-list. The Cycle-2 `&`-escaping fix (HTML layer escapes only `</>`) was respected (no `&` re-flag). claude-pack surfaced 0 findings.

---

## Recommended sequencing (when owner signals "fix")

1. **HIGH first, by cluster:** A (goal→brd — confirm vocab) · B (export guards — confirm VISION/PRODUCT behavior) · C (llm+html reject) · then F10/E (escape `<`).
2. **MED:** D (F7/F11) · G-roots (F16/F17 double-parse) · F18 (panel CSS).
3. **LOW correctness:** F12, F14.
4. **Cleanup last, under test guard:** H (DRY refactor — closes F20/21/22/24/29/30 together) · F15 (template JS hoist — riskiest) · F19/F23/F25/F26/F27/F28.
5. Add the missing tests each fix exposes (viewer `--layers goal`, empty/typo/VISION/PRODUCT export, llm+html, `<!--` primer via conformant parser, ASCII explorer `--layers`, Table depth parity).
6. Keep both suites green; then resume Cycle 4 per Expanded Scope.

## Open questions (for owner)

1. **F10/R2 contradiction** — accept F10 (real render-break; fix = escape `<`) and add a conformant-parser/browser test? (My recommendation: yes.)
2. **Cluster A vocab** — viewer `--layers`/facet/tab should use artifact-type names (`goal,…`, matches existing help) — confirm? (Recommend: yes.)
3. **Cluster B** — `--export VISION` / `--export PRODUCT`: **error as context-only**, or **emit the singleton once**? (Recommend: emit once + dedup; error only if truly unresolved.)
4. **Cluster C** — `llm`+`html`: hard reject (recommend) or warn-and-ignore?
5. Scope of cleanup clusters H/I this round vs. defer to a dedicated refactor pass? (F15 template hoist is the only one with real regression risk.)
