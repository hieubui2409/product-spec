# Red-team review — N1 finding-level fingerprint (spec-span anchor)

Reviewer: code-reviewer · Date: 2026-06-06 · Verdict: **fix-then-ship** (2 BLOCKER, 3 MAJOR)

Plan reviewed: `plans/260606-1627-n1-finding-fingerprint-spec-span-anchor/{plan,phase-01,phase-02,phase-03}.md`
Design source: `plans/reports/brainstorm-260606-1627-...-report.md`
Code verified: `critique_inherit.py`, `critique_cache.py`, `spec_graph.py`, fixture `valid-spec`, test suite.

---

## BLOCKER

### B1 — Normalization collapses all-punctuation/markup lines to empty string → cross-finding collision (NOT just degradation)

**Plan claim** (phase-02 L34-35, L76, L107): `_normalize_line` does "light normalize"; "empty/whitespace cited line → line_text falsy → fingerprint None → eid fallback. Correct degradation."

**Reality** — two distinct defects compound:

1. The fallback guard is on the **raw** resolved line, not the normalized result. Phase-02 L76:
   `fp = compute_finding_fingerprint(_node_of(eid), sev, line_text) if line_text else None`.
   `_resolve_line_text` returns the RAW line (`lines[line-1]`, phase-02 L61). For a frontmatter delimiter `---` or a date line `2026-05-28`, the raw string is truthy, so `compute_finding_fingerprint` IS called.
2. Inside the hash, `_normalize_line` reduces those to `""`. Verified empirically with the plan's exact regex:
   - `"2026-05-28"` → `""`
   - `"1. 2. 3."` → `""`
   - `"---"` → `""` (frontmatter delimiter)
   - `"## 3.2.1. Reach the ARR goal"` → `"reach the arr goal"` (also strips a meaningful `3.2.1.` numeric prefix)

   Regex `^[\s>#*\-+0-9.)]+` greedily eats leading digits/dots/parens/dashes/hashes/spaces. A line that is *entirely* those chars normalizes to empty.

**Consequence**: every finding on the same `node`+`severity` whose cited line normalizes to `""` produces the **identical** fingerprint `sha256(node\0sev\0"")[:16]`. Two genuinely different blockers on PRD-AUTH that happen to cite (e.g.) a `---` separator and a numbered-list marker line **silently merge into one** — the exact under-count bug (a) this plan exists to fix, reintroduced. This is a false-merge **collision**, not graceful degradation to eid. It is worse than today's behavior for those lines.

**Fix**: After normalizing, if the normalized text is empty → return `None`/skip fingerprint and fall back to eid. I.e. compute `nt = _normalize_line(line_text)`; `fp = compute_finding_fingerprint(node, sev, nt) if nt else None`. Make `compute_finding_fingerprint` take *already-normalized* text, or have the caller branch on the normalized value, not the raw `line_text`. Add a Phase-1 test: finding citing an all-punctuation line → fingerprint None → eid keying (not a shared empty-text fingerprint). The plan's criterion-5 test only covers unresolvable; it does not cover "resolves to a line that normalizes empty."

---

### B2 — BRD-goal findings produce a meaningless, unstable fingerprint anchor

**Plan claim** (plan.md L40, brainstorm L28): "`spec_graph` node carries `file` … Uniform for all node types (BRD-goal nodes share `brd.md` — resolver still node→file→line N)." Treated as acceptable.

**Reality** (`spec_graph.py` L170-186, fixture `brd.md` L10-19): BRD goals are **expanded from `brd.md` frontmatter**, not body lines. `_node_from_goal` sets `file = parent_file` (= `brd.md`) and `body_hash = None`. The goal `BRD-G1` lives in the YAML block (fixture lines 11-14), inside the `---`…`---` fence. There is no body line that "is" goal G1. A real citation `BRD-G1:1` (used verbatim in existing tests, `test_critique_inherit.py` L118, L136, L149) resolves to **line 1 of brd.md = `---`**, which normalizes to `""` (see B1).

**Consequence**: For the entire `goal` node class — which IS in scope (inherit chain reaches goals; `test_inherited_grandparent_goal`) — the fingerprint anchors to frontmatter delimiter / arbitrary YAML text. Combined with B1, every goal-level blocker on the same goal node collapses to one empty-text fingerprint. Even without B1, the anchored text (`id: brd-g1`, `title: "..."`, or `---`) is not the "criticized content" the design premise assumes (brainstorm L64: "anchored to deterministic spec content"); for goals the LLM cites a line number that has no stable relationship to the goal's meaning. The "spec edit → new fingerprint = new finding" invariant (criterion 3) is incoherent for goals: editing the goal `title` in frontmatter may or may not move the cited line.

**Fix**: Either (a) explicitly scope fingerprinting to nodes with a real body (`body_hash is not None`) and document that goal-level findings always fall back to eid keying (acceptable, but state it as a known limitation, not "uniform for all node types"); or (b) for goal nodes, anchor on the goal `id` + `title` from the graph node instead of a brd.md line. Option (a) is YAGNI-correct; the plan must stop claiming uniformity and add a goal-node fallback test asserting eid keying.

---

## MAJOR

### M1 — Re-critique stability premise is weaker than stated; markdown reflow breaks it

**Plan claim** (criterion 1; brainstorm L66): line-drift immune because "the line's TEXT is unchanged → same fingerprint."

**Reality**: Identity holds ONLY if (i) the LLM cites the byte-identical line across runs AND (ii) the spec line text is byte-identical after normalize. Failure modes the plan under-weights:
- **LLM cites a *nearby* line** for the same issue on re-critique (e.g. `:5` the heading vs `:7` the body sentence). Different text → different fingerprint → **two counted** = the bug criterion 1 claims to fix, untouched. The brainstorm risk section (L122-124) acknowledges this but the plan's acceptance criterion 1 over-promises a guarantee the mechanism cannot deliver.
- **Spec reflow / re-wrap**: editing a paragraph above can re-wrap the cited sentence onto a different line split; the *line's* text changes even though the *finding's* target is unchanged → new fingerprint → false split. Plan treats "text changed = new finding" as always-correct (criterion 3); reflow is a counterexample where text changed but finding did not.

**Consequence**: real-world dedup precision will be materially below the "one counted, not two" promise. Not a correctness crash, but the success metric (brainstorm L129) may not hold in production.

**Fix**: Downgrade criterion-1 language from a guarantee to "immune to *pure line-number* drift (text preserved)"; explicitly list cite-drift and reflow as accepted residuals (already partly in brainstorm Risks — pull into the plan acceptance section so it is not oversold). No code change required, but the TDD test for criterion 1 must use a *pure line shift with identical text* (it does — phase-01 step 4 is fine); just don't claim more than that test proves.

### M2 — Graph build at write time is a SECOND parse and runs at a different time than `critique_scan`'s parse

**Plan claim** (plan.md L38, phase-02 L69, L106): "resolver builds graph from root via `spec_graph.build_graph(root)` (one parse per write, cheap)" / "one graph build per write … acceptable (once per run)."

**Reality**: `index_report_findings` is invoked **by the LLM agent as a separate documented step** (`references/workflow-critique.md` L227, step 3), AFTER `critique_scan.py` already ran and built its own graph. So this is not "one parse per run" — it is an *additional* full `load_artifacts` + parse of every file under `docs/product/`, in a separate process/call from the scan that produced the findings. More importantly: the spec on disk may have been **edited between the scan and the index-write** (the agent runs several steps in between — lens-cache put, snapshot, etc.). If a line moved or the file changed in that window, the resolved line text is taken against a *different* graph state than the one the finding was generated against → fingerprint anchored to the wrong/shifted line from the very first write.

**Consequence**: (1) redundant parse — minor cost, plan's YAGNI defer is fine. (2) **Correctness window**: the resolver reads current disk, not the snapshot the findings were computed from. For the normal case (no edit mid-run) this is fine; if the agent or a hook touches docs/product between scan and index-write, the anchor is wrong. The plan does not acknowledge this temporal gap.

**Fix**: Resolve line text against the SAME graph/snapshot the scan used, not a fresh `build_graph` at write time. Cheapest: have `critique_scan` attach resolved fingerprints when it emits the bundle (it already built the graph), OR pass the snapshot path. If keeping the fresh build, add a note that fingerprint stability assumes docs/product is unchanged between scan and index-write, and that this is a documented precondition. Verify `_import_spec_graph().build_graph(Path(root))` import path actually works from `index_report_findings` — it does (same `_import_spec_graph` already used), so that sub-claim is OK.

### M3 — `version: 1→2` bump is cosmetic; `load_index` ignores it (dead metadata) and "tolerant read" is from absence-of-key, not version

**Plan claim** (plan.md L47, phase-02 L82, criterion 4): "version 1→2, tolerant read of old rows"; phase-02 L82 "load_index already returns the entries dict regardless of version (tolerant) — no read change needed."

**Reality** (`critique_cache.py` L50-56): `load_index` reads `data.get("entries")` and **never inspects `version`**. The bump to 2 changes nothing functional — no reader branches on it, no migration keys off it. Tolerant read of legacy rows works because `_index_rows`'s new key expression `entry.get("finding_fingerprint") or eid` handles a *missing key* (returns eid) — that is the actual back-compat mechanism, and it is independent of the version number. So the version field is **dead metadata** by YAGNI standards.

**Consequence**: Not a bug, but the plan presents the version bump as buying back-compat safety when it buys nothing. Worse: phase-01 step 9 / criterion 4 asserts `version == 2` as a success criterion — that test pins a value no consumer reads, i.e. a phantom assertion that locks in churn without protecting behavior.

**Fix**: Either (a) drop the version bump (YAGNI) and remove the `version == 2` assertions, OR (b) if kept as a forward-looking marker, say so explicitly and do NOT make it a behavioral acceptance criterion. Keep the real tolerant-read test: a legacy row dict with NO `finding_fingerprint` key flows through `_index_rows` and keys by eid without KeyError (phase-01 step 7 — that one is genuinely valuable, keep it).

---

## MINOR

### m1 — `build_descendant_rollup` single-chokepoint claim is CORRECT — but verify the per-row count, not just row count

Traced `build_descendant_rollup` (`critique_inherit.py` L158-166): it iterates `_index_rows(root)` and does `blocker_counts[node] += 1` **per row**. It has NO independent dedup. So fewer rows from `_index_rows` → correct count. The plan's "single chokepoint" assumption (phase-03 L46) **holds** — good. One caveat the plan should test: `_index_rows` dedups across ALL nodes by fingerprint; two DIFFERENT child nodes could in principle share a fingerprint only if they shared node+sev+text — impossible since `node` is in the hash. So no cross-node merge risk. Confirmed safe; just keep phase-03 step 3's explicit verification.

### m2 — severity in hash: low false-split risk, confirmed

Index is blocker + DEC-worthy only (`index_report_findings` L194 filters; `_INHERIT_SEVERITIES = {"blocker"}`). The only severities reaching the hash are effectively `blocker` (DEC-worthy rows may carry `minor`/`major` severity + `dec_worthy=True`). A finding flipping blocker↔major across runs would split. Narrow but non-zero: a DEC-worthy minor that the LLM later rates blocker → two fingerprints. Brainstorm L72 acknowledges "narrow." Acceptable; just keep the criterion-2 severity-sensitivity test honest (different severity → different hash IS the intended behavior, so this is by-design, not a bug).

### m3 — No external index consumer breaks on the new field

Grepped all of `product-spec-critique`: the only `load_index`/`_index_rows` consumers are inside `critique_inherit.py` (+ tests). `critique_scan.py` reaches them via `build_inherited_context` / `build_descendant_rollup`, not raw rows. Additive field is safe; no serializer pins a closed schema. Confirmed — plan's "additive only" claim holds.

---

## NIT

- **n1** phase-01 step 10 wants new tests to "FAIL for the right reason (missing helper/field), NOT import errors." But `compute_finding_fingerprint`/`_resolve_line_text` don't exist yet → tests referencing them at module top-level via `ci.compute_finding_fingerprint` will raise `AttributeError` at call time (fine, that's an assertion-phase failure), but if any test does `from critique_inherit import compute_finding_fingerprint` at import → `ImportError` collection error, which pollutes the `--co -q` baseline count. Mandate attribute-style access (`ci.compute_...`) in red-phase tests so collection still succeeds and the baseline is meaningful.
- **n2** phase-02 normalization lowercases — fine for English specs, but `lang: vi` specs (CLAUDE.md bilingual) have Vietnamese prose; `.lower()` on Vietnamese is generally safe but combining-diacritic normalization (NFC vs NFD) is NOT handled. Two byte-different-but-visually-identical Vietnamese lines (one NFC, one NFD) → different fingerprints. Low likelihood (same file, same encoding) but worth a `unicodedata.normalize("NFC", ...)` in `_normalize_line` for robustness. YAGNI-defensible to skip; flag only.
- **n3** Dependency note (plan.md L61-64): the stale-pending ancestor plan `260603-0028` status flag for the user is appropriate and correctly NOT auto-flipped. Good adherence to GATE-NO-SILENT-REVERSAL. No action.

---

## Verdict: fix-then-ship

The design is sound in the common case (body-node finding, pure line drift) and the read-path single-chokepoint analysis is correct. But **B1 reintroduces the very under-count bug the feature targets** for any all-punctuation/markup line, and **B2 means the entire goal-node class gets a garbage anchor** — both are silent false-merges, the worst failure mode for a dedup key. M2 has a real (if narrow) temporal-correctness gap. M3 shows the version bump is theater. None are unfixable; all are bounded edits to Phase 2 + two added Phase-1 tests. Do not ship as-is.

Required before ship:
1. B1: fall back to eid when *normalized* text is empty; add test.
2. B2: scope fingerprint to body-bearing nodes (or anchor goals on id+title); add goal-node eid-fallback test; correct the "uniform for all node types" claim.
3. M2: resolve against the scan's graph/snapshot (or document the unchanged-between-scan-and-write precondition).
4. M3: drop the `version==2` acceptance assertion (keep version bump optional + non-behavioral); keep the missing-key tolerant-read test.
5. M1: downgrade criterion-1 wording to pure-line-drift; list cite-drift + reflow as accepted residuals in the plan, not just the brainstorm.

## Unresolved questions
- Q1: Does any hook or agent step edit `docs/product` between `critique_scan` and the agent's `index_report_findings` call? If yes, M2 is a live correctness bug, not a theoretical window. (Needs runtime trace of the workflow-critique.md step order vs file mutations.)
- Q2: For goal nodes, is eid-keyed fallback (option B2-a) acceptable to the PO as permanent behavior, or is per-goal granularity actually wanted? (Product decision — do not assume.)
- Q3: Truncation `N=16` hex = 64 bits. Fine for this scale; brainstorm open question already resolved. No action unless index grows to millions (it won't — lossy blocker-only).
