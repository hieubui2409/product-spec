---
type: code-review
date: 2026-05-29T03:05
target: .claude/skills/product-spec/scripts/ (Wave 3 — Codex + Gemini after 2 prior review cycles)
reviewer: claude (opus-4-7, hardcore bug-hunt, runtime-probe-first)
prior-waves:
  - plans/reports/code-review-260528-2110-product-spec-skill-hardcore-4wave-rereview-report.md
  - plans/reports/from-ck-code-review-to-fixed-260528-2303-cleanmatic-product-spec-skill-fix-summary-report.md
methodology: read every line of all 14 scripts → run pytest → adversarial inputs (YAML injection, XSS, path traversal, unicode, malformed types) → file/line citations only on reproduced failures
---

# Wave-3 Bug-Hunt — `cleanmatic:product-spec` Python scripts

## Test run

`./.venv/bin/python3 -m pytest .claude/skills/product-spec/scripts/tests/ -v` → **76 passed in 0.88s**. No regressions vs prior wave (which already grew 32→76).

## TL;DR

Prior 2 review waves locked down the Block-1 IMPORTANT items (`--lang vi`, phantom BRD, mermaid-fallback fence, slug at-generate-time-validation for epic/story). Pytest is green.

This wave hunted at the runtime boundary the suite doesn't cover: YAML auto-conversion, untrusted token values, filename collisions, parent-validation gaps, type-mismatch fallthroughs, and HTML/XSS surface. **9 NEW bugs surfaced; 2 are CRITICAL**.

| Severity | Count | NEW vs prior waves |
|---|---|---|
| CRITICAL | 2 | XSS via `product.name`/title into HTML; YAML frontmatter breakout via `--values` token substitution |
| HIGH | 3 | uncaught `TypeError` on YAML-auto-parsed dates in `status` crashes 4/6 JSON scripts; PRD `--slug` validation entirely missing (parallel to wave-2 epic/story fix); `--write` silently overwrites existing files |
| MEDIUM | 4 | `_load_baseline` no JSONDecodeError trap; symlinked story crashes `spec_graph.build_nodes`; `strict_gate` exits 0 on missing `docs/product/`; markdown-table pipe injection in `build_traceability_matrix`; renderers crash on non-hashable status/scope; `--id` override bypasses ID validation |
| LOW / nits | 5 | UTF-8 BOM rejection; gitignore-negation false positive (`!.session.md`); `_status_inconsistency` crashes on list-typed status; `_safe_id` collision (`-` vs `:` → same node); self-reference in `epic:`/`prd:` undetected |

---

## Findings (NEW only — exclude prior-raised-and-fixed)

### CRITICAL

#### C-1. `render_mermaid` Mermaid-label content unescaped → live `<script>` injection into HTML output
**File:** `scripts/render_mermaid.py:34-37, 50, 66` + `scripts/render_html.py:90` + `assets/templates/visual-html-shell.html:25`
**Repro:**
```bash
# PRODUCT.md frontmatter: name: "Test </script><script>alert(1)</script>"
visualize.py --view tree --format html
```
Output HTML line 28: `PRODUCT["PRODUCT: Test </script><script>alert(1)</script>"]` — raw, unescaped, inside `<div class="mermaid">`. Python's `HTMLParser` confirms **3 `<script>` tags** in the output where only 2 are templated → injected `<script>alert(1)</script>` is a live tag.

**Why prior waves missed it:** Wave-2 hardened `_escape` for `<>&"'` in render_html, but the Mermaid body is inserted by `_render_view_body` line 90: `f'<div class="mermaid">\n{body}\n</div>'` where `body` is the inner Mermaid DSL *not* run through `_escape`. The reasoning is "Mermaid will parse it" — but the **HTML parser runs first** and tokenizes any `<script>` it sees inside the div.

**Why `_safe_label` doesn't catch it:** the function only replaces `"`, `[]{}`, backticks, and `\n`. `<` and `>` pass through.

**Fix sketch:**
1. In `render_mermaid._safe_label`, additionally replace `<` → `&lt;` and `>` → `&gt;`. Mermaid v11 label content is HTML-context-safe with these escapes.
2. OR (more robust): in `render_html._render_view_body`, HTML-escape the mermaid DSL body too — but Mermaid will then need entity-decoding. Option 1 is cleaner.
3. Add a regression test: `test_safe_label_strips_script_tags_for_xss_safety`.

**Severity rationale:** the HTML output is intended to be opened in a browser. A malicious PO answer in any of `product.name`, `node.title`, or any title field flows directly into Mermaid label → XSS. `securityLevel: "strict"` on Mermaid only sandboxes Mermaid's own parsing — it does NOT prevent script tags introduced before Mermaid runs.

---

#### C-2. `generate_templates` token substitution allows YAML-frontmatter breakout via `--values`
**File:** `scripts/generate_templates.py:149-156` (`render`/`tok`) + `:196-222` (`fill_defaults`)
**Repro:**
```bash
echo '{"version":"1.0.0\nstatus: approved"}' > values.json
generate_templates.py --type prd --slug X --values values.json
```
Output frontmatter:
```yaml
status: draft
...
version: 1.0.0
status: approved   ← injected
...
```
YAML `safe_load` honors last-wins for duplicate keys → file ships with `status: approved` despite the `if out.get("status") == "approved": raise ValueError` guard in `fill_defaults`. The guard runs on the **dict** before token-substitution; the injection happens **during** token substitution into the template's raw string.

**Why prior waves missed it:** wave-2 added the `status: approved` defense; it didn't notice raw `str(v)` token expansion can insert `\n` into a yaml line.

**Fix sketch:** in `render.tok`, reject (or quote) any string scalar containing `\n` or `\r` when the surrounding template line is a YAML frontmatter line. Simplest correct fix: replace token substitution for scalars with a YAML-aware emit — i.e. for keys that go into frontmatter, dump with `yaml.safe_dump({k: v})` and splice. Pragmatic alternative: in `tok`, if `\n` or `---` appears in `v`, reject:
```python
def tok(m):
    k = m.group("key"); v = values.get(k)
    if isinstance(v, str) and ("\n" in v or v.lstrip().startswith("---")):
        raise ValueError(f"token {k!r} contains frontmatter-breaking chars")
    ...
```
Add test: `test_generate_rejects_multiline_scalar_token`.

**Severity rationale:** this defeats the post-wave-2 "scripts never mint approved" invariant. Any LLM (or hand-crafted values file) can ship an approved-status artifact. Sign-off bypass.

---

### HIGH

#### H-1. YAML auto-date in `status`/`moscow`/`scope` crashes 4 of 6 JSON-emitting scripts (`spec_graph`, `check_traceability`, `check_consistency`, `build_traceability_matrix`)
**Files:** `scripts/spec_graph.py:248`, `check_traceability.py:116`, `check_consistency.py:270`, `build_traceability_matrix.py:96`
**Repro:** PRD with `status: 2026-05-29` (PO mistypes status as a date) →
```
TypeError: Object of type date is not JSON serializable
when serializing dict item 'status'
```
All four scripts use bare `json.dumps(graph_or_findings)`. `frontmatter_parser.py:121` correctly uses `default=str`; the rest don't.

The dt happens because `yaml.safe_load` auto-converts ISO-8601 strings to `datetime.date`. The PO writing `status: 2026-05-29` or `horizon: 2026` triggers it. The `check_consistency.unknown_enum` finding correctly flags the bad enum (visible from `strict_gate`'s stderr — strict_gate doesn't json-dump the graph, so it survives), but the script crashes before printing the JSON.

**Why prior waves missed it:** no fixture exercises an unexpected YAML scalar type in an enum field.

**Fix:** all four `json.dumps(...)` calls → `json.dumps(..., default=str)`. One-line each. Add test: `test_check_consistency_survives_yaml_date_in_status_field`.

**Contract violation:** CLAUDE.md says "scripts always exit 0; emit JSON findings". This bug exits 1 with a Python traceback to stdout.

---

#### H-2. PRD `--slug` accepts oversized / lowercase / spaces / special chars / starts-with-digit
**File:** `scripts/generate_templates.py:90-92`
**Repro:**
```bash
generate_templates.py --type prd --slug "TOO-LONG-A-SLUG-NAME-WITH-MANY-CHARS"
# → id: PRD-TOO-LONG-A-SLUG-NAME-WITH-MANY-CHARS (38 chars > 16 limit)
generate_templates.py --type prd --slug "auth lower with spaces!"
# → id: "PRD-AUTH LOWER WITH SPACES!" (invalid chars)
generate_templates.py --type prd --slug "9START-WITH-DIGIT"
# → id: PRD-9START-WITH-DIGIT (starts with digit, fails check_consistency.invalid_id later)
```
Wave-2 NEW-4 fixed this for `--type epic` and `--type story` (`PARENT_PATTERN_FOR_PRD/_EPIC`). The wave-2 fix-summary report claims NEW-4 closed; in fact only the **parent** validation was added, not the **own-slug** validation for PRD itself. Same class of bug, missed at the only generation entry point that accepts a raw slug.

**Fix:** in `allocate_id` for `target_type == "prd"`, validate the constructed ID against `ID_PATTERN_BY_TYPE["prd"]` (from `check_consistency`) and `ValueError` on miss:
```python
if target_type == "prd":
    if not slug:
        raise ValueError("--slug is required for type=prd")
    candidate = f"PRD-{slug.upper()}"
    if not PRD_ID_PATTERN.match(candidate):
        raise ValueError(f"--slug yields invalid PRD id {candidate!r}: ...")
    return candidate
```
Add test: `test_generate_prd_rejects_oversized_slug` / `test_generate_prd_rejects_lowercase_slug`.

---

#### H-3. `generate_templates --write` silently overwrites existing artifacts (no collision check)
**File:** `scripts/generate_templates.py:255-266`
**Repro:**
```bash
generate_templates.py --type prd --slug AUTH --write   # writes prds/auth.md (PO edits it)
generate_templates.py --type prd --slug AUTH --write   # silently overwrites; PO edits lost
```
For `--type prd`, the slug determines the path, so re-running emits the same path. For epic/story, the auto-allocator finds the next free ID (so collision is naturally avoided) but the explicit `--id PRD-AUTH-E1` override (used by `--auto` batch per the docstring) bypasses the allocator entirely and overwrites whatever's at `epics/PRD-AUTH-E1.md`.

**Why prior waves missed it:** no test runs `--write` twice.

**Fix:**
```python
if args.write:
    if out_path.exists():
        raise FileExistsError(f"{out_path} already exists; refusing to overwrite without --force")
    ...
```
Plus an optional `--force` flag for the LLM/CI-driven flows that legitimately want to re-emit. Add test: `test_generate_refuses_to_overwrite_existing_file`.

**Severity rationale:** silent data loss on a routine command. PO writes story, then re-runs to "see the template again" → AC and prose are erased.

---

### MEDIUM

#### M-1. `visualize._load_baseline` doesn't trap `json.JSONDecodeError` on corrupt snapshot
**File:** `scripts/visualize.py:82, 92`
**Repro:** `echo "not json" > docs/product/visuals/.snapshots/badfile.json && visualize.py --view delta --diff badfile.json` → unhandled `JSONDecodeError` traceback.
Same pattern at line 92 (auto-discovered baseline).
**Fix:** wrap `json.loads(...)` in try/except → raise `RuntimeError` with descriptive message including the file path.

---

#### M-2. `spec_graph.build_nodes` crashes with `ValueError` on symlinked story file pointing outside `docs/product/`
**File:** `scripts/spec_graph.py:70`
**Repro:**
```bash
ln -s /tmp/external-story.md docs/product/stories/external-story.md
spec_graph.py --root .
# ValueError: '/tmp/external-story.md' is not in the subpath of '/tmp/.../docs/product'
```
`Path(art["file"]).resolve().relative_to(product_dir.resolve())` resolves the symlink target then attempts a relative-to against `product_dir`. Outside-target → ValueError.

**Fix:** keep the original walk-relative path:
```python
rel = path.relative_to(product_dir).as_posix()  # the walk path is already inside product_dir
```
Or wrap in try/except and use the un-resolved path. Either way, never crash. Add test.

---

#### M-3. `strict_gate` exits 0 with "0 artifacts checked" when `docs/product/` is missing
**File:** `scripts/strict_gate.py:53-65`
**Repro:** `strict_gate.py --root /tmp/empty-dir` → stderr: `0 artifacts checked · 0 errors · 0 warns`; exit 0.
**Impact:** CI hook pointing at the wrong path silently reports green. Worse: a project that ships without `docs/product/` accidentally passes the gate.

**Fix:** when `graph.get("missing_product_dir")` is True, write a clear error to stderr and exit `EXIT_BLOCKED`:
```python
if graph.get("missing_product_dir"):
    print(f"[strict_gate] {root}/docs/product/ does not exist", file=sys.stderr)
    return EXIT_BLOCKED
```

---

#### M-4. `build_traceability_matrix` doesn't escape `|` in cell values → markdown table corruption
**File:** `scripts/build_traceability_matrix.py:32-42`
**Repro:** story with `metrics: ["m1 | extra-column"]` → table row gets 9 cells in a 8-column header. Renderers see malformed table.
**Fix:** add a `_cell(v)` helper that escapes `|` to `\|` (markdown table escape) and replaces newlines with spaces. Apply to every value before `" | ".join`. Add test.

---

#### M-5. ASCII renderers `persona`/`heatmap`/`scope` crash with `TypeError` on non-hashable enum values
**File:** `scripts/render_ascii.py:91, 107, 156`
**Repro:** node with `status: [draft, approved]` (YAML list) → `heatmap`: `TypeError: cannot use 'list' as a dict key`.
**Impact:** PO runs visualize without first running validate; raw YAML mistake → script crash with traceback.
**Fix:** in each function, guard `if not isinstance(v, (str, int)): v = "?"` before using as dict key. Same in `persona()` for set-element use. Sub-bug: `_status_inconsistency` (check_consistency.py:204) has the same crash on `STATUS_ORDER.get(list_value, -1)`.

---

#### M-6. `--id` override on `generate_templates` bypasses ALL ID validation
**File:** `scripts/generate_templates.py:243`
**Repro:**
```bash
generate_templates.py --type story --id "TOTALLY-BOGUS-FORM" --write
# Writes stories/TOTALLY-BOGUS-FORM.md with id: TOTALLY-BOGUS-FORM
```
The `--id` override (designed for `--auto` batch per docstring) bypasses `allocate_id()` where the regex validation lives. Any string is accepted as `id` in the frontmatter and as the filename.
**Fix:** when `args.id` is provided, validate against the expected pattern for `args.type`:
```python
if args.id:
    pat = ID_PATTERN_BY_TYPE.get(args.type)
    if pat and not pat.match(args.id):
        raise ValueError(...)
```

---

### LOW / nits

#### L-1. UTF-8 BOM at file start rejected as "no YAML frontmatter"
**File:** `scripts/frontmatter_parser.py:75`
**Repro:** save any markdown file with UTF-8 BOM (Notepad, some Vim configs) → parse_text returns `error: "no YAML frontmatter (file does not start with '---')"`.
**Fix:** strip `﻿` before the `lstrip()` check:
```python
if text.startswith("﻿"):
    text = text[1:]
```

#### L-2. `_session_md_gitignore` false-positive on `!.session.md` (negation, means INCLUDE)
**File:** `scripts/check_consistency.py:174`
**Repro:** `.gitignore` containing `!.session.md` (un-ignore) → warn fires because substring check matches regardless of leading `!`.
**Fix:** `if p.startswith("!"): continue` before the match. One-line.

#### L-3. `_status_inconsistency` crashes when `status` is a YAML list/dict (non-hashable)
**File:** `scripts/check_consistency.py:204-205`
**Repro:** node with `status: [draft, approved]` → `TypeError: cannot use 'list' as a dict key`.
**Note:** `check_consistency.unknown_enum` would catch the bad type, BUT this crash happens in `_status_inconsistency` which runs in the same `check()` call. The crash short-circuits the rest of the findings.
**Fix:** `cs = STATUS_ORDER.get(child.get("status") if isinstance(child.get("status"), str) else "", -1)`.

#### L-4. `render_mermaid._safe_id` collision across distinct IDs
**File:** `scripts/render_mermaid.py:85-86`
**Repro:** `_safe_id("PRD-AUTH-E1-S1") == _safe_id("PRD:AUTH:E1:S1")` (both → `PRD_AUTH_E1_S1`). Mostly theoretical since `:` is illegal in IDs, but the substitution is asymmetric.
**Fix:** use a single sentinel like `_DASH_` and `_COLON_` substitutions, or just `urllib.parse.quote_plus`-style escape with a unique char.

#### L-5. Self-referential parent (`epic: <own-id>`) not flagged by `check_traceability`
**File:** `scripts/check_traceability.py:46-55`
**Repro:** story with `id: X` and `epic: X` (typo) → no findings. Graph emits self-loop edge; `downstream(X)` returns `{X}` (visited-set saves it from infinite loop).
**Impact:** Mermaid renders self-loop arrow on the node — visually confusing.
**Fix:** in check_traceability for story/epic, add `if n["epic"] == n["id"]: flag self_reference error`.

#### L-6 (informational). `spec_graph.write_snapshot` + `render_html.write` use second-resolution filenames → collision when called rapidly within 1 second
**Files:** `scripts/spec_graph.py:219-220`, `scripts/render_html.py:162-163`
**Repro:** loop `for i in 1 2 3; do render_html.write(...); done` within 1 sec → only one HTML file remains; the others are overwritten.
**Impact:** batch generation (e.g. all 9 views per --auto run) within the same second loses files. Tested: 3 rapid `visualize --view tree --format html` → 1 file present, 2 overwritten.
**Fix:** append a 4-digit counter or microseconds: `dt.datetime.now().strftime("%Y%m%dT%H%M%S_%f")[:21] + "Z"` or PID-suffix.
Not high-priority because today's call sites don't loop within 1s, but `--auto` and CI matrix runs are reasonable future use.

---

## Verified-safe areas (checked, found clean)

- **YAML parse contract** — `frontmatter_parser` cleanly returns `ok=False` with structured error for: missing frontmatter, malformed yaml, file-not-found, non-mapping yaml. CRLF tolerated. Only BOM (L-1) misses.
- **Status enum integrity** — `unknown_enum` correctly flags non-canonical values; the `STATUS_ORDER` comparison is correct (verified L-3 crash doesn't affect normal flow with string statuses).
- **Mermaid `--lang vi` plumbing** — `i18n_labels.label()` falls back correctly on invalid lang. `render_ascii.tree/roadmap/moscow` and `render_mermaid.tree/roadmap/moscow` all wire `lang` through. Wave-2 NEW-6 closed.
- **`--filter-wont` semantics** — ASCII and Mermaid tree/roadmap/persona honor the flag; gap/heatmap/scope/moscow/risk silently ignore (documented).
- **`--keep-optional`** — comma-splitting + set-membership lookup is correct; whitespace-trimmed.
- **`_load_baseline` 1-snapshot fallback** — works correctly; uses live graph as comparison target.
- **`--diff` with non-existent file** — raises FileNotFoundError with available-snapshot list (wave-2 L-1 fix verified).
- **Snapshot filename derived from `generated_at`** — wave-2 L-5 verified.
- **Duplicate-ID detection** — `check_consistency.dup_id` correctly flags two stories sharing an ID across different files.
- **`type` field override of folder hint** — discovered as a latent issue: a story-shaped file in `stories/` with `type: epic` becomes an epic node. Could be a bug (folder/type drift) but is currently working-as-coded; flag for product owner judgment, not a script-layer fix.
- **`--keep-optional` with comma-in-value** — N/A (current optional sections are flat names).
- **`--diff` accepting absolute path outside `.snapshots/`** — by design.
- **install-vendor-mermaid.sh sha256 pinning** — wave-2 NEW-10 verified (line 25 now `a43bc1af...`).
- **install.sh pytest exit code** — wave-2 H-2 verified (capture-then-tail pattern at line 71-81).
- **`--lang vi` ASCII/Mermaid label localization** — verified live: `## NOW` → `## BÂY GIỜ`, MoSCoW labels translate.
- **Tree Mermaid orientation** — wave-2 H-1: `flowchart BT` confirmed line 46.
- **Pytest** — 76/76 pass, 0.88s.

---

## Unresolved questions

1. **C-1 fix scope:** escape `<>` in `_safe_label` (cheap, fixes the XSS) OR introduce a Mermaid-DSL HTML-escape step in render_html.\_render_view_body (more robust, more code)? Recommend the former for v1; the latter for hardening.
2. **C-2 fix direction:** strict `\n` rejection in token values (simpler, breaks legit multi-line markdown body tokens like `overview_problem`) OR detect frontmatter-region vs body-region by line-offset and only reject in frontmatter (more complex)? Recommend a frontmatter-token allowlist: only `id/status/lang/owner/version/created/updated/scope/moscow/horizon/size/epic/prd` tokens go through frontmatter and must be sanitized.
3. **H-3 fix:** ship `--force` as the override flag, or require `--overwrite` to be explicit? Either works. The current claim in the docstring is "default: print only" — relying on the PO to read that is fragile.
4. **M-3 fix:** also exit blocked when `docs/product/` is missing AND no `--allow-missing` flag? Recommended yes.
5. **L-6:** worth fixing now or accept as known limitation? `--auto` batch is the future use case; fixing pre-emptively is one line.
6. **YAML-date footgun (H-1):** beyond the `default=str` band-aid, should `check_consistency` also surface a `yaml_auto_date_in_enum` finding before the JSON dump? That gives the PO an actionable message instead of an opaque traceback. Recommended yes.
7. **`type` field vs folder location:** if the PO writes `type: epic` in `stories/X.md`, is that a bug worth flagging? Currently silent. Recommend a wave-4 `folder_type_mismatch` check.

---

**Status:** DONE_WITH_CONCERNS
**Summary:** 9 NEW bugs surfaced post-wave-2; 2 are CRITICAL (XSS via Mermaid label content; YAML-frontmatter breakout in token substitution). The 4 HIGH/MEDIUM affecting all 4 JSON-dumping scripts (H-1) is one-line fix per script. Prior waves' fixes verified intact: 76/76 pytest pass; `--lang vi` localizes; tree BT-orientation; vendor sha pinned; install.sh exit code propagation; slug validation at-generate-time for epic/story.
**Concerns:** C-1 is the standout — any product name or artifact title that contains `<script>` produces a live XSS in the rendered HTML. C-2 defeats the post-wave-2 "scripts never mint approved" invariant. Both should be blocking for v1.
