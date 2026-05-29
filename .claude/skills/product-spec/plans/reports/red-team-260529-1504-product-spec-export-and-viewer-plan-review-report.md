# Red-Team Review — product-spec Export + Viewer plan

Date: 2026-05-29 · Reviewer: hostile plan red-team (READ-ONLY) · Subject: `plans/260529-1504-product-spec-export-and-viewer/` (plan.md + 7 phases)
Method: every claim verified against LIVE source under `.claude/skills/product-spec/`; plan's own file:line citations distrusted.

Baselines confirmed green before review: **product-spec 92 passed**, **claude-pack 77 passed** (matches plan's gate numbers exactly).

---

## VERDICT (up front)

**Not implementable as written.** Two CRITICAL flaws block the foundation:

1. **Phase 1's `ancestors()` / digest model is built on a graph that has no Vision node and no BRD node** — both are explicitly absent from `build_edges()`/`build_nodes()`. The plan repeatedly asserts the digest emits "Vision→BRD→goals→PRD→Epic→Story" and that a PRD's ancestors "include its BRD-G* goals **+ the BRD**." Reverse-BFS over edges can reach goals but can **never** reach Vision or a BRD container — they aren't graph nodes. The digest's headline feature (ancestor context) is structurally impossible via the stated mechanism.
2. **The HTML token-expansion mechanism (`str.replace("{{k}}", v)` in `render_html.assemble`) is a server-side injection/corruption sink the plan never accounts for.** Spec content containing the literal text `{{view_body}}`, `{{footer_note}}`, `{{mermaid_js}}`, etc. is live during expansion — even inside the "inert" embedded-JSON blob and even after `_escape()` (which does not escape `{`/`}`). Phase 2's "embedded JSON + client DOMPurify" model assumes the JSON is inert server-side; it is not.

**Phases needing revision before any build: Phase 1 (re-found the digest hierarchy model) and Phase 2 (token mechanism + sanitize completeness).** Phases 3/4/5 inherit both and cannot be correct until 1+2 are fixed. Phase 6 is lower-risk than the plan fears (good news — see HIGH-4). Phase 8/cross-skill concerns are largely defused by evidence (see MED-9).

---

## CRITICAL

### C1 — `ancestors()` cannot deliver "Vision + BRD" context; the canonical hierarchy references non-existent nodes
**Where:** Phase 1 (`phase-01-foundation.md` L19, L24, L40, L57, L65); design D4.
**Evidence (live):**
- `spec_graph.build_edges()` (`spec_graph.py:119-135`) emits edges ONLY for story→epic, epic→prd, prd→brd_goal. **Goals have no outbound edge** (comment L131-134 confirms the `goal→"BRD"` edge was deliberately removed; regression test `test_mermaid_tree_has_no_phantom_brd_node`, `test_visualize.py:216-225`, enforces its absence).
- `build_nodes()` (`spec_graph.py:64-81`): for `type=="brd"` it appends ONLY goal nodes — **the `id: BRD` singleton from brd.md is never added as a node.** Verified empirically: fixture graph node IDs = `PRODUCT, BRD-G1, BRD-G2, PRD-AUTH, PRD-AUTH-E1, PRD-AUTH-E1-S1` — no `BRD`, no vision node.
- Vision: `vision.md` (when present) produces an **isolated** node (type=vision) with **zero edges** — `build_edges` has no vision branch. Reverse-BFS from any node can never reach it.
- Empirical reverse-BFS: `ancestors(PRD-AUTH-E1-S1) = {BRD-G1, PRD-AUTH, PRD-AUTH-E1}`; `ancestors(PRD-AUTH) = {BRD-G1}`. No vision, no BRD container — ever.

**Why it breaks the plan:** Phase 1 success criterion "ancestors() returns correct transitive parents **incl. BRD goals for a PRD**" is satisfiable for the *goals* part, but the requirement text "a PRD's ancestors include its `BRD-G*` goals **+ the BRD**" (L19) is impossible. The digest "canonical hierarchy order (Vision→BRD→goals→PRD→Epic→Story)" (L40) and the design's acceptance "Vision(struct)+BRD(struct)+PRD-AUTH(full)…" (design §10) name two layers that are NOT in the graph node set. F1 export of "the whole context in one pass" silently omits Vision and BRD narrative.

**Concrete fix:** Phase 1 must stop pretending Vision/BRD are graph-reachable ancestors. Two options, pick one and document:
- (a) **Special-case outside the edge graph:** the digest assembler explicitly pulls the Vision artifact and BRD artifact from `load_artifacts()` (they ARE parsed, just not nodified) and prepends them as synthetic `role=ancestor` entries whenever the selection includes any goal/PRD descendant. `ancestors()` stays a pure edge walk (returns goals + PRD chain); the Vision/BRD framing is a separate, documented assembler step.
- (b) Add Vision + BRD as real nodes with edges (goal→BRD→vision via PRODUCT) — but this reintroduces the exact phantom-box bug the team already killed and would break `test_mermaid_tree_has_no_phantom_brd_node` + `test_mermaid_tree_skips_vision_node`. **Not recommended.**
Update Phase 1 requirements/success-criteria and the design's §10 acceptance to match whichever path. Add a test asserting a real `vision.md` + `brd.md` present in the fixture actually appear in the digest (current `valid-spec` fixture has **no vision.md** — see C1b).

### C1b — Phase 1 fixture gap will hide the Vision/BRD omission
**Where:** Phase 1 step 1 ("temp spec tree fixture").
**Evidence:** the existing `valid-spec` fixture has no `vision.md` (verified: `docs/product/` contains only PRODUCT.md, brd.md, prds/, epics/, stories/). If Phase 1 reuses it, tests will "pass" while never exercising Vision-in-digest at all, masking C1.
**Concrete fix:** the Phase 1 fixture MUST include a `vision.md` AND assert it lands in the digest with `role=ancestor, verbosity=struct` for a `--depth context` PRD export. Otherwise the headline feature ships untested.

### C2 — `render_html.assemble()` token expansion is a server-side injection/corruption sink the plan ignores
**Where:** Phase 2 (`phase-02-vendor-and-html-body-render.md` L23-24, L29); Phase 6 token-contract extension (L23). Live: `render_html.py:165-166`, shell `visual-html-shell.html:28` `{{mermaid_js}}`, L26 `{{footer_note}}`, L25 `{{view_body}}`.
**Evidence (empirical, run live):**
- `assemble()` does `for k,v in values.items(): shell = shell.replace("{{"+k+"}}", v)` — naive, sequential, whole-document.
- `_escape()` (`render_html.py:109-119`) escapes `& < > " '` but **NOT `{` or `}`**.
- Proven: `product_name = "{{mermaid_js}}"` → after `product_name` is escaped-and-inserted, the later `mermaid_js` replacement scans the whole shell and **injects the full 2.5 MB Mermaid payload into the `.meta` line** (verified: meta line begins `…Product: "use strict";var __esbuild_esm_mermaid=…`).
- Proven bidirectional: a `view_body` containing the literal text `{{footer_note}}` gets the footer substituted into the body (`id="diagram"><pre>see Self-contained HTML. To re-render…`), because `view_body` is replaced first, then `footer_note` re-scans the inserted body.

**Why the plan's defense doesn't cover it:** Phase 2 routes bodies as an embedded JSON blob and relies on **client-side** `DOMPurify.sanitize(marked.parse(...))`. But the JSON blob and ALL new design-system token values pass through this **server-side** `str.replace` FIRST. A spec body, title, persona label, or group label containing `{{view_body}}` / `{{spec-data}}` / `{{mermaid_js}}` is a live token at expansion time — DOMPurify never sees it because the corruption/injection happens before the client runs. Phase 6 explicitly *extends* the token set ("extend with design-system tokens", L23) feeding more spec-derived values through the same mechanism, widening the sink.

**Concrete fix (Phase 2, before any body work):** replace the multi-pass `str.replace` with a **single-pass** substitution that never re-scans inserted content — e.g. `re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), shell)` (one pass, inserted values are not re-examined for tokens). Add a test: a node title / body containing the literal `{{mermaid_js}}` and `{{footer_note}}` must round-trip verbatim into the embedded JSON and NOT trigger payload injection or footer bleed. This is a prerequisite for Phases 3/4/5/6.

---

## HIGH

### H3 — Embedded-JSON `</script>` and attribute-context escaping under-specified
**Where:** Phase 2 L23 ("JSON-escaped (incl. `<\/`)"), L19 (vendor `</script>`→`<\/script>`).
**Evidence:** Plan correctly identifies the `</script>` break for the *vendored lib payload*. For the **embedded JSON data channel** it says "JSON-escaped (incl. `<\/`)" — but standard `json.dumps` does NOT escape `/`; it produces `<\/script>` only if you post-process. More importantly the plan enumerates the embedded-JSON sink but **does not enumerate attribute-context sinks.** Existing `_escape()` escapes quotes (L116-117) "for attribute context… even though current call sites only feed body text" (L111). New shells (board/explorer) will put IDs/status/group labels into HTML **attributes** (`data-status=`, `aria-label=`, `id=`, anchor `href="#<ID>"`). IDs are validated elsewhere but **group labels, persona names, titles** are free text.
**Concrete fix:** Phase 2 must state explicitly: (a) embedded JSON uses `json.dumps(..., ensure_ascii=False)` then a literal `.replace("</", "<\\/")` post-step (test it); (b) any value landing in an HTML attribute goes through `_escape()` (which already handles quotes) — name the attribute sinks in the phase. Add XSS tests for a persona/group label = `"><script>alert(1)</script>` reaching a `data-*`/`aria-label` attribute. The plan's current XSS test set (Phase 2 step 4) only covers *body* payloads, not attribute payloads.

### H4 — Phase 6 regression sizing is BACKWARDS (good news, but the plan over-warns and mis-prioritizes)
**Where:** Phase 6 L35, L57 ("test_visualize.py asserts shell markup → big update"); plan attack-checklist item 5.
**Evidence (live, `test_visualize.py` 958 lines, all 92 read):** the HTML tests do **NOT** assert exact shell markup. They are all **substring/content** checks:
- `test_html_assemble_is_self_contained_string` (L139): `"<!DOCTYPE html>" in html`, `'<div class="mermaid">' in html`, `"flowchart BT" in html`.
- `test_html_escapes_pre_content_when_format_is_pre` (L150): `"&lt;script&gt;" in html`.
- dispatch tests (L159, L259): `'<div class="mermaid">' not in body`, `"<pre>" in body`, `len(body) < 10_000`, `"__esbuild_esm_mermaid" not in body`.
- injection tests (L832-957): regex-scope the `<div class="mermaid">` body only.
**No test asserts the `<style>` block, the `.meta` div text, button markup, or the full shell.** So Phase 6's "skin-only" CSS/head changes will break **almost nothing** — contradicting the plan's repeated "big update / exact-HTML test breakage" framing (L35, L57).
**The REAL Phase 6 risks the plan under-weights:**
1. `test_html_ascii_fallback_view_skips_mermaid_js` (L259) asserts `len(body) < 10_000`. The new shared design-system head (theme-toggle JS + palette CSS + print-CSS + stagger keyframes) inflates EVERY page including ascii-fallback views. **If the shared head pushes a heatmap page over 10 KB, this test fails.** This is the concrete breakage, not "exact markup."
2. `mermaid_js` gating (`render_html.py:153`, `=_load_mermaid_js() if view_format=="mermaid" else ""`) must survive. Plan says "preserve render_html.py:153 behavior" — citation **accurate** (L153 is the gate). But adding the design-system head must not accidentally inline marked/DOMPurify into the 9 legacy views (they don't render bodies). Plan Phase 2 L26 says "body views must omit Mermaid payload" but never says **legacy views must omit the marked/DOMPurify payload** — symmetric bloat risk.
**Concrete fix:** (a) Re-scope Phase 6 risk section: drop the "exact-HTML test breakage" emphasis; ADD "shared-head size budget vs the <10 KB ascii-fallback assertion" as the primary risk — either keep the head lean or raise that bound deliberately with justification. (b) Add an explicit rule + test: legacy views (`tree…delta`) inline NEITHER mermaid (unless mermaid-format) NOR marked/DOMPurify (never — they have no bodies).

### H5 — `--layers` precedence rule produces a surprising/empty export for the default depth
**Where:** Phase 1 L39 ("`--layers story` yields only stories, no Vision/BRD context"); Phase 3 L39.
**Evidence + reasoning:** The locked default is `--depth context` = ancestors struct + target full (D4). The locked precedence is "`--layers` filters which *types* appear; an excluded ancestor type is dropped." Combine them: `--export PRD-AUTH --layers story` (a plausible "give me the stories of AUTH" request) yields **only stories, with zero PRD/epic/goal/vision context** — the export self-describes as PRD-AUTH but contains no PRD. For a stakeholder read-once doc that is a confusing artifact. This is internally consistent with the locked rule, so it is **not a defect to silently change** (per repo rule 3 — guard user decisions). But the plan does not flag the UX trap.
**Concrete fix:** Keep the rule (owner-locked), but Phase 3 must (a) emit a provenance note in the doc header when `--layers` drops the selected root's own type ("Note: --layers story excluded the PRD/epic context for PRD-AUTH"), and (b) `workflow-export.md` must show this exact example so the LLM/PO isn't surprised. Add a test asserting the warning note appears. Do NOT change the precedence without owner confirmation.

---

## MEDIUM

### M6 — Determinism claims for board/export HTML are unverifiable as stated; only md+ascii can assert byte-equality
**Where:** plan.md L65 ("md + ascii outputs deterministic"); Phase 1 L25; Phase 3 L24; design §9.
**Evidence:** `assemble()` injects `generated_at = datetime.now(...)` (`render_html.py:133`); `write()` puts a UTC timestamp in the **filename** (`render_html.py:181-182`). So no HTML output is byte-deterministic — correct, and the plan concedes this ("HTML may carry a timestamp"). The risk: the plan's success criteria for F1 html / board / explorer say "deterministic" loosely. The **digest model** (Phase 1) and the **md** assembler CAN be byte-deterministic ONLY IF: (a) no `dict`/`set` iteration order leaks — `ancestors()` should return a `Set` but the digest emit order must be a **sorted/canonical list**, not set-iteration; (b) board grouping must sort within columns. `downstream()` already returns a `set` (`spec_graph.py:197`); Phase 1 must sort before emit.
**Concrete fix:** Phase 1 success criteria: assert the digest is a **list in canonical sorted order**, and add a test calling `build_digest` twice and asserting `==` (plan mentions this — keep it) PLUS asserting order is independent of `nodes[]` input order (shuffle the fixture nodes, expect identical digest). For HTML, restrict the determinism claim to "sanitized body + structure deterministic; only `generated_at` + filename vary" — which the plan mostly says; make every HTML success-criterion say that explicitly so a future reviewer doesn't assert byte-equality and fail.

### M7 — Stale/imprecise citations (minor, but you said distrust them)
**Where:** several phases.
**Evidence:**
- Phase 2 L36: "install.sh (~L84)". Actual mermaid vendor call is `install.sh:80-81`; L84 is past the closing `fi`. Off by a few lines — the *concept* (add alongside mermaid vendor) is right; the insertion point should be after L84 (`fi`) or as a new step block. **Minor.**
- Phase 2 L34 + plan-wide: "vendored mermaid… gitignored like vendored mermaid." **FALSE.** `.gitignore:118-120` explicitly un-ignores `.claude/skills/product-spec/assets/**`; `git ls-files` confirms `assets/vendor/mermaid.min.js` IS tracked (2.5 MB committed). So the new `marked.min.js`+`purify.min.js` will ALSO be committed, not gitignored. This changes Phase 8/cross-skill analysis (see M9) and means a ~62 KB (marked 48.5 + purify 13.7) addition to the committed tree.
- Phase 4 L32/L54 + Phase 5 L37/L59: "dispatch ~L135-158", "visualize.py:153-158". **Accurate** — the html branch is `visualize.py:145-160`, the mermaid/`<pre>` decision is L153-158. Board/explorer must intercept before L146. Citation good.
- Phase 1 L46: "after downstream() ~L205, before write_snapshot()". **Accurate** — `downstream()` ends L205, `write_snapshot()` starts L208.
**Concrete fix:** correct the gitignore claim everywhere (it materially affects what ships and what claude-pack packs); nudge the install.sh line ref. Other citations are fine.

### M8 — Dispatch special-case must NOT break `--format ascii`/`mermaid` for board/explorer
**Where:** Phase 4 L19/L54, Phase 5 L19/L59.
**Evidence:** `main()` (`visualize.py:135-161`) branches: `ascii` → print ascii body (L135-138); `mermaid` → print mermaid body (L140-143); else html. Board/explorer ascii fallbacks ARE specified (board=grouped lists, explorer=tree). But the plan says "special-case board/explorer **before the mermaid/`<pre>` html branch**" — that's the HTML path only. **For `--format mermaid`, board/explorer have no mermaid renderer** — `_render_mermaid` does `getattr(render_mermaid, view)` (`visualize.py:58`) which will `AttributeError` for `board`/`explorer`. The plan never says what `--viz board --format mermaid` does.
**Concrete fix:** Phases 4/5 must specify the `--format mermaid` behavior for board/explorer: either (a) fall back to ascii (board/explorer carry no Mermaid by design — D-locked), or (b) reject with a clear message. Currently `getattr(render_mermaid,"board")` raises an uncaught `AttributeError`. Add the guard in `_render_mermaid` (and `_render_ascii` already uses `getattr` too — add board/explorer there) + a test for all three formats × both new views.

### M9 — Cross-skill (claude-pack) impact is REAL but bounded; plan's "plans/ already dropped" reassurance is incomplete
**Where:** Phase 7 L60.
**Evidence (live):**
- `pack/selection.py:23-32` packs a skill via `src_dir.rglob("*")` — **every file** under `.claude/skills/product-spec/`, file-granular, sorted by arcname. So the new `assets/vendor/{marked,purify}.min.js`, new `scripts/*.py`, new `assets/templates/*-shell.html`, new `references/workflow-export.md` **all get packed** automatically (they're tracked — see M7). Sorted walk ⇒ determinism preserved for new files. **OK.**
- `docs/product/exports/` is created in the **PO's project**, NOT under `.claude/skills/product-spec/` — so it is NEVER packed. The plan's worry about "exports/ break claude-pack golden" is **unfounded**. `safety_check` doesn't even need an exports rule.
- `test_golden_product_spec.py` (read fully): uses `any("product-spec/SKILL.md" in n …)` substring + negative secret checks. **No exact file-count or file-set assertion.** Adding files won't break it. The `FILE_COUNT` token (L58) is `str(len(selection))` — a value embedded in INSTALL.md, not asserted against a constant. **OK.**
- `test_pack_determinism.py` pins mtime/uid/gid/PAX. New committed files participate in the sorted walk identically. The 2.5 MB mermaid already ships; +62 KB marked/purify is immaterial to determinism (only to tar size). **OK.**
**Residual real risk:** `__pycache__`/`.pyc` from the new test runs — `.gitignore:95-96` re-ignores them and `test_golden_product_spec.py:76` asserts `"/__pycache__/" not in n`. As long as the new scripts don't ship a committed `__pycache__`, fine. The bundled `assets/vendor/*.min.js` will inflate every product-spec pack by ~62 KB — acceptable, but note it.
**Concrete fix:** Replace Phase 7's vague "confirm doesn't break golden/determinism" with the specific assertions above (substring golden + sorted-walk determinism both safe; exports not packed). Add a one-line note that committed vendor libs grow the pack ~62 KB. Run `pytest -m integration` for `test_golden_product_spec` explicitly in the gate (it's marked `@pytest.mark.integration`, NOT in the default run — the plan's Phase 7 command `pytest .../tests -q` will **skip it** unless `-m integration` is added).

---

## LOW

### L10 — YAGNI: 3 explorer modes + treegrid in v1 is the heaviest sub-feature; treegrid is the weakest
**Where:** Phase 5 (1.5d, the biggest phase); design D6.
**Evidence:** Phase 5 itself flags "Treegrid ARIA weakness (W3C APG caveat)" (L60) and makes Tree the default/accessible mode. The treegrid is the highest-effort, lowest-accessibility, owner-locked-but-marginal mode. This is owner-locked (D6) so **do not cut without confirmation** (repo rule 3). But it's the obvious de-scope candidate if effort overruns.
**Concrete fix:** Keep as locked, but Phase 5 should mark Tree + Flat-tabs as the must-ship and Table-tree as the "ship if time" within the phase, so an overrun degrades gracefully instead of blocking F2. Surface to owner as an option only if Phase 5 slips.

### L11 — `--export all` resolution + filename-collision determinism under-specified
**Where:** Phase 3 L22 ("Output path `<select>-<ts>`"), L60 (filename safety).
**Evidence:** `<ts>` is wall-clock; two exports of the same selection in the same second collide (the mermaid snapshot path solved this with a content-hash suffix, `spec_graph.py:223-226` — there's a proven pattern in-repo). `--export all` resolution to "top roots expanded" (Phase 1 L36) is hand-wavy given C1 (no vision/BRD nodes). List-select filename sanitization is mentioned but not specified (comma → `?`).
**Concrete fix:** reuse the snapshot content-hash filename pattern for exports (deterministic, collision-free); specify the list→stem sanitization (e.g. join sorted IDs with `_`, cap length, hash the tail). Define `all` precisely after C1 is resolved.

### L12 — Phase 2 "CDN fallback" contradicts the hard offline constraint for the NEW libs
**Where:** Phase 2 L26 ("if vendor missing → CDN fallback (mirror Mermaid path)") vs plan.md L35 ("**no CDN fallback** for these").
**Evidence:** Direct internal contradiction. `plan.md` Locked-stack L35: "marked+DOMPurify… no CDN fallback for these." Phase 2 L26: "if vendor missing → visible warning banner + CDN fallback (mirror Mermaid path)." A CDN fallback for the **sanitizer** is a security regression (offline guarantee + supply-chain: a tampered CDN DOMPurify defeats the whole XSS mitigation that justified D8/D11).
**Concrete fix:** For marked/DOMPurify specifically, NO CDN fallback — if vendored libs are missing, the body-render views must **fail closed** (render bodies as escaped plain text via server `_escape`, with a visible "run install.sh" banner), never reach for a CDN sanitizer. Align Phase 2 L26 to plan.md L35. (Mermaid CDN fallback for legacy views can stay — it's not a security control.)

---

## What the plan got RIGHT (verified)
- Dispatch interception point (`visualize.py:145-160`, mermaid/pre at L153-158) — citation accurate; board/explorer owning their own HTML writer before that branch is the correct approach.
- `ancestors()` insertion point (`spec_graph.py` after L205) — accurate.
- `mermaid_js` gating line (`render_html.py:153`) — accurate; preserving it is right.
- `downstream()` builds a `to→from` child-map (`spec_graph.py:196`); `ancestors()` inverting to a `from→to` parent-map is the correct mirror — verified by simulation.
- Test counts (92 / 77) — exact.
- claude-pack packs product-spec via `rglob` sorted walk — new files ride along deterministically.
- RAW-`footer_note` INVARIANT (`render_html.py:145-148`) correctly identified; Phase 6's "extend only, never remove tokens, preserve invariant" is the right discipline (modulo C2's mechanism fix).

---

## Unresolved questions (for owner / planner)
1. **C1 resolution path:** synthetic Vision/BRD prepend (option a) vs real nodes (option b, breaks 2 existing tests)? Affects Phase 1 design, fixture, and the digest order spec. Owner-facing because it changes what "the whole spec in one doc" actually contains.
2. **H5 precedence UX:** keep owner-locked `--layers` precedence (yields context-less exports) + add a warning note, or revisit the rule? Locked decision D2 — needs owner sign-off to change; default = keep + warn.
3. **L10 treegrid:** ship Table-tree in v1 (locked D6) or stage it behind Tree+Flat-tabs if Phase 5 overruns? Owner-locked; flag only.
4. **M8:** what should `--viz board|explorer --format mermaid` do — silent ascii fallback or explicit rejection? Not covered by any locked decision.

---

**Status:** DONE
**Summary:** Plan is NOT implementable as written — two CRITICAL foundation flaws: (C1) `ancestors()`/digest cannot deliver Vision+BRD context because neither is a graph node (verified empirically; edges only reach goals), and (C2) `render_html.assemble`'s naive `str.replace` token expansion is a server-side injection/corruption sink that bypasses the client-DOMPurify model (proven live: spec content containing `{{mermaid_js}}` injects the 2.5MB payload). Phase 1 + Phase 2 must be re-founded before Phases 3/4/5 build on them.
**Concerns/Blockers:** Phase 6 regression fear is overstated (tests are substring-based, not exact-markup) but its real risk is the <10KB ascii-page size assertion vs the new shared head; Phase 2's CDN-fallback for the sanitizer contradicts plan.md and is a security regression; the "vendored libs are gitignored" claim is false (they're committed and get packed by claude-pack); `--format mermaid` for board/explorer will `AttributeError` as specified.
