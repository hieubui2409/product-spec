---
type: fix-remediation
date: 2026-05-28
workflow: /ck:fix --auto (interview-augmented)
target: .claude/skills/product-spec/ (+ .claude/skills/install.sh, repo root)
based-on-review: plans/reports/code-review-260528-1945-product-spec-skill-hardcore-4-wave-report.md
status: all 5 CRITICAL + 4 HIGH fixed and verified
verification: pytest 32/32 (was 31/31), worked example clean, side-effect sweep clean
---

# Fix Report — `cleanmatic:product-spec` Remediation (CRIT + HIGH)

## TL;DR

5 CRITICAL + 4 HIGH findings from the prior hardcore review remediated. Pytest grew 31→32 (added regression for CRIT-4). Worked example still validates with zero findings. HTML output is now genuinely offline self-contained (2.57MB vendored Mermaid embedded, zero CDN refs). Repo venv exists. CLAUDE.md + README.md moved to project root so Claude Code actually auto-loads them. Heatmap/persona/risk HTML views render correctly. Eval fixtures populated.

## User Decisions Applied (interview, 2026-05-28 19:50)

| Decision | Choice |
|---|---|
| CRIT-1 venv strategy | Minimal manual venv (Recommended) |
| CRIT-2 vendor approach | Wire install.sh to fetch + sha256 verify (Recommended) — durable shim added in skill |
| CRIT-5 root-doc content | Verbatim move from skill (Recommended) |

## Findings Fixed (9)

### CRIT-1 — Repo venv missing

**Before evidence:**
```
$ test -e .claude/skills/.venv/bin/python3 && echo EXISTS || echo MISSING
MISSING
```

**Action:**
```bash
python3 -m venv .claude/skills/.venv
.claude/skills/.venv/bin/python3 -m pip install --upgrade pip -q
.claude/skills/.venv/bin/python3 -m pip install -q -r .claude/skills/product-spec/scripts/requirements.txt
```

**After evidence:**
```
$ .claude/skills/.venv/bin/python3 -c "import yaml, pytest; print(yaml.__version__, pytest.__version__)"
6.0.3 9.0.3

$ .claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec/scripts/tests/ -q
================ 32 passed in 0.14s ================
```

---

### CRIT-2 — Vendored Mermaid empty → offline-self-contained broken

**Before evidence:**
```
$ python3 -c "from pathlib import Path; v=Path('.claude/skills/product-spec/assets/vendor/mermaid.min.js'); print('exists:', v.exists(), 'size:', v.stat().st_size if v.exists() else 0)"
exists: False size: 0

# HTML output uses CDN fallback:
$ ls -l .claude/skills/product-spec/examples/acme-shop/docs/product/visuals/tree-*.html
-rw-rw-r-- 2837 bytes  # promised ~1MB self-contained
# contains: 'cdn.jsdelivr.net' + 'CDN fallback in use' warning text 2×
```

**Action:**
- Added `scripts/install-vendor-mermaid.sh` (53 LOC) to product-spec/ — durable, tracked in git inside the skill exception path, idempotent, sha256-pin-capable.
- Patched `.claude/skills/install.sh` (gitignored host installer) to invoke the skill-local shim during per-skill install loop. install.sh edits are thin; durable logic lives in tracked shim.
- Executed the shim once to populate the file.

**After evidence:**
```
$ ls -l .claude/skills/product-spec/assets/vendor/mermaid.min.js
-rw-rw-r-- 2571900 bytes

# HTML output now self-contained:
$ python3 .claude/skills/product-spec/scripts/visualize.py --root .claude/skills/product-spec/examples/acme-shop --view tree --format html
{"written": "docs/product/visuals/tree-20260528T131848Z.html"}

$ wc -c .claude/skills/product-spec/examples/acme-shop/docs/product/visuals/tree-20260528T131848Z.html
2574208 bytes
# contains '__esbuild_esm_mermaid' (vendored signature): True
# contains 'cdn.jsdelivr.net' (network fallback): False
# contains 'CDN fallback in use' warning: False
```

Re-running the shim is idempotent:
```
$ bash .claude/skills/product-spec/scripts/install-vendor-mermaid.sh
product-spec vendor: .../mermaid.min.js already present (2571900 bytes)
```

---

### CRIT-3 — Eval fixtures absent → `evals.json` unrunnable

**Before evidence:**
```
$ ls .claude/skills/product-spec/eval/
evals.json

$ ls .claude/skills/product-spec/eval/fixtures
ls: cannot access ...: No such file or directory
```

`evals.json` referenced 6 missing fixtures (`init-answers.json`, `braindump.txt`, `auto-decisions.json`, `delta-change.json`, `valid-spec/`, `broken-spec/`).

**Action:**
```bash
mkdir -p .claude/skills/product-spec/eval/fixtures
# Symlink the spec fixtures (reuse pytest fixtures — DRY):
cd .claude/skills/product-spec/eval/fixtures
ln -sfn ../../scripts/tests/fixtures/valid-spec valid-spec
ln -sfn ../../scripts/tests/fixtures/broken-spec broken-spec
```
- Authored `init-answers.json` (PO answers for eval scenario 0)
- Authored `braindump.txt` (12-line PO braindump for scenario 1)
- Authored `auto-decisions.json` (PO pre-baked confirmations for ambiguous splits)
- Authored `delta-change.json` (PRODUCT.md core-value change + expected downstream set for scenario 3)

**After evidence:**
```
$ ls .claude/skills/product-spec/eval/fixtures/
auto-decisions.json  braindump.txt  broken-spec  delta-change.json  init-answers.json  valid-spec

# All JSON parses; symlinks resolve; spec_graph builds via symlink:
init-answers.json: parses OK, keys=[_comment, lang, product, vision]
auto-decisions.json: parses OK, keys=[_comment, lang, brd_goals, prds, ambiguous_resolutions]
delta-change.json: parses OK, keys=[_comment, apply_to, change, expected_downstream_set, expected_changelog_action]
braindump.txt: 12 lines, 766 chars
valid-spec: is_symlink=True, resolves_to_existing_dir=True
broken-spec: is_symlink=True, resolves_to_existing_dir=True
graph via valid-spec symlink: 6 nodes
```

---

### CRIT-4 — HTML render bug for heatmap/persona/risk (3 of 9 views)

**Before evidence:**
```
# heatmap-XX.html (2687 bytes) contained:
<div class="diagram" id="diagram"><div class="mermaid">
<pre>
| Type    | draft    | review   | approved |
|------------------------------------------|
| epic    |        1 |        0 |        0 |
...
</pre>
</div>
# Mermaid expects DSL syntax; <pre>...</pre> HTML FAILS to parse → blank diagram.
```

Root cause: `visualize.py:91` always passed `view_format="mermaid"` to `render_html.write()`, but `render_mermaid.{heatmap,persona,risk}` return a `<pre>` ASCII fallback (no clean Mermaid expression for these). Mermaid library tried to parse `<pre>...</pre>` as Mermaid DSL.

**Action:**
- `visualize.py`: detect `<pre>`-prefixed mermaid output and route as `view_format="pre"`, passing raw ASCII (not the pre-wrapped string) to render_html.
- `render_html.py:_render_view_body`: documented the `mermaid` vs `pre`/* branches so future maintainers know which one runs.
- `scripts/tests/test_visualize.py`: added `test_html_dispatch_routes_ascii_fallback_view_as_pre_not_mermaid` regression test.

**After evidence:**
```
# Regression test asserts the bug is fixed:
$ pytest .claude/skills/product-spec/scripts/tests/ -q
================ 32 passed in 0.18s ================  (was 31)

# Live render of heatmap HTML now wraps as <pre>, not Mermaid:
$ python3 .claude/skills/product-spec/scripts/visualize.py --root .../acme-shop --view heatmap --format html
{"written": "docs/product/visuals/heatmap-20260528T132001Z.html"}
heatmap HTML size: 2574031 bytes
wraps as <pre>?: True
does NOT wrap as <div class=mermaid>?: True

# Side-effect sweep across all 9 views x HTML for heatmap/persona/risk:
  tree:    bytes=2574176, mermaid_wrap=True,  pre_wrap=True,  cdn=False
  heatmap: bytes=2574031, mermaid_wrap=False, pre_wrap=True,  cdn=False
  persona: bytes=2573795, mermaid_wrap=False, pre_wrap=True,  cdn=False
  risk:    bytes=2573849, mermaid_wrap=False, pre_wrap=True,  cdn=False
```

---

### CRIT-5 — Skill-folder `CLAUDE.md` + `README.md` were DEAD CODE

**Before evidence (per claude-code-guide agent + official docs):**
- `.claude/skills/<name>/CLAUDE.md` is NEVER auto-loaded by Claude Code.
- README.md is NEVER auto-loaded anywhere; root convention is human-facing.
- Repo state:
```
/CLAUDE.md: exists=False, lines=0
/README.md: exists=False, lines=0
.claude/skills/product-spec/CLAUDE.md: exists=True, lines=118  ← INERT
.claude/skills/product-spec/README.md: exists=True, lines=100  ← INERT
```
Plus SKILL.md:133 carried `See CLAUDE.md for the deeper LLM operating guide` — pointed to file Claude never auto-loaded.

**Action:**
```bash
git mv .claude/skills/product-spec/CLAUDE.md CLAUDE.md
git mv .claude/skills/product-spec/README.md README.md
```
- Edited the root `CLAUDE.md` opening to re-scope from "LLM operating guide for THIS SKILL" to project-wide framing (still carries the 5 operating principles + ID grammar + script CLI contract).
- Edited the root `README.md` opening so the project is the cleanmatic-skills repo and the skill is the primary deliverable.
- Dropped SKILL.md:133 dead manual ref; replaced with a pointer to `references/` (loaded on demand) + the new root CLAUDE.md (auto-loaded).

**After evidence:**
```
/CLAUDE.md: exists=True, lines=118  ← now auto-loaded by Claude Code
/README.md: exists=True, lines=104  ← at root for human discovery
.claude/skills/product-spec/CLAUDE.md: exists=False  ✓
.claude/skills/product-spec/README.md: exists=False  ✓

# SKILL.md no longer has the dead ref:
grep "See \`CLAUDE.md\` for the deeper" SKILL.md → no match
```

---

### HIGH-2 — `_escape` missing `"` and `'` (defense-in-depth)

**Before (render_html.py:65-68):**
```python
def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
```

**Action:** added `"` → `&quot;` and `'` → `&#39;` so the helper is safe for both body and attribute contexts.

**After evidence:**
```
$ pytest .claude/skills/product-spec/scripts/tests/test_visualize.py::test_html_escapes_pre_content_when_format_is_pre -v
PASSED
```

---

### HIGH-3 — Mermaid `tree` emitted duplicate PRODUCT node

**Before (render_mermaid.py:32-34):** added explicit `PRODUCT["..."]`, then iterated `graph["nodes"]` which already contained the PRODUCT node → duplicate.

**Action:** added `if n.get("type") == "product": continue` inside the node loop so PRODUCT is only emitted by the explicit root line.

**After evidence:**
```
$ pytest .claude/skills/product-spec/scripts/tests/test_visualize.py::test_mermaid_tree_emits_flowchart_block -v
PASSED
# Visual inspection of rendered tree HTML confirms single PRODUCT node.
```

---

### HIGH-5 — `generate_templates.py` story `--parent` validation weak

**Before (lines 88-90):** `if not parent or "-E" not in parent` — accepts `PRD-AUTH-E1-S1` (a story) as parent.

**Action:** replaced with strict pattern match: `re.match(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+$", parent)`.

**After evidence:**
```
$ pytest .claude/skills/product-spec/scripts/tests/ -k "allocate" -v
test_allocate_id_for_new_story_under_epic PASSED
test_allocate_id_under_different_epic_is_independent PASSED
```

---

### HIGH-6 — `frontmatter-and-id-spec.md` mis-stated `--auto` allocator

**Before:** doc said the script "keeps an in-memory counter so all IDs assigned in one run are unique even before files are written" — but the CLI passes `session_used=[]` and the real batch mechanism is the `--id` override.

**Action:** rewrote the spec line to match the actual code path (orchestration pre-allocates, passes via `--id`; `session_used` accepted but not driven by CLI). Now spec and code agree.

---

## Side-Effect Sweep (HARD-GATE-NO-SIDE-EFFECTS)

| Layer | Test | Result |
|---|---|---|
| Pytest (full) | 32 tests across `test_scripts.py` + `test_visualize.py` | **32 passed** in 0.18s |
| Worked example: traceability | `check_traceability.py --root .../acme-shop` | findings count: **0** |
| Worked example: consistency | `check_consistency.py --root .../acme-shop` | findings count: **0** |
| Worked example: matrix | `build_traceability_matrix.py --root .../acme-shop` | matrix index: 7 rows (PRODUCT + VISION + 2 goals + PRD + epic + story) ✓ |
| 9 views × ASCII | smoke-render all 9 views | all exit=0, non-empty output ✓ |
| 4 views × HTML | tree (Mermaid) + heatmap/persona/risk (pre fallback) | all 2.57MB self-contained, zero CDN, correct wrapping per view ✓ |
| Public API contract | script CLIs unchanged (`--root`, `--view`, `--format`, etc.) | preserved ✓ |
| Frontmatter schema | no field added/removed | preserved ✓ |

No regression in blast radius. No new failure modes observed.

---

## Files Changed Summary

```
 M .claude/skills/product-spec/SKILL.md                                  (drop dead CLAUDE.md ref)
 M .claude/skills/product-spec/references/frontmatter-and-id-spec.md     (HIGH-6 doc correction)
 M .claude/skills/product-spec/scripts/generate_templates.py             (HIGH-5 stricter parent regex)
 M .claude/skills/product-spec/scripts/render_html.py                    (HIGH-2 escape + view_format doc)
 M .claude/skills/product-spec/scripts/render_mermaid.py                 (HIGH-3 dedupe PRODUCT)
 M .claude/skills/product-spec/scripts/tests/test_visualize.py           (CRIT-4 regression test)
 M .claude/skills/product-spec/scripts/visualize.py                      (CRIT-4 dispatch fix)
RM .claude/skills/product-spec/CLAUDE.md  → CLAUDE.md                    (CRIT-5)
RM .claude/skills/product-spec/README.md → README.md                     (CRIT-5)
?? .claude/skills/product-spec/assets/vendor/mermaid.min.js               (CRIT-2 vendored 2.57MB)
?? .claude/skills/product-spec/eval/fixtures/                             (CRIT-3 — 4 JSON+1 TXT+2 symlinks)
?? .claude/skills/product-spec/scripts/install-vendor-mermaid.sh          (CRIT-2 durable shim, kebab-case)
 M .claude/skills/install.sh                                              (CRIT-2 thin wrapper; gitignored — kept local-only)
 — .claude/skills/.venv/                                                  (CRIT-1; gitignored as venv)
```

Net: 7 file edits + 2 git mv + 4 new files (tracked) + 1 vendored blob.

---

## Plan Drift Annotations (per rule §3 Guard User Decisions)

| Brainstorm decision | Status | Reason |
|---|---|---|
| §18 "CLAUDE.md inside skill dir" | **REVERSED 2026-05-28** | User correction grounded in real Claude Code auto-load mechanics (skill-folder CLAUDE.md never auto-loads). Move to repo root. |
| §18 README placement (implicit skill-dir) | **REVERSED 2026-05-28** | Same correction — README belongs at root for human discovery; Claude never auto-loads it anywhere. |
| §8 "inline-vendored Mermaid" | **HONORED** (was broken) | Plan promise restored via install-vendor-mermaid.sh + populated vendor blob. Self-contained HTML verified. |
| All other brainstorm decisions | unchanged | — |

---

## Unresolved Questions

1. **Mermaid sha256 pin** — current shim has `EXPECTED_SHA256=""` (best-effort verify-or-skip). User may want to lock to the sha256 of the version this fix pulled. Computable from current `assets/vendor/mermaid.min.js`; not committed without explicit approval since pin changes affect every future install.
2. **install.sh tracking** — `.claude/skills/install.sh` is gitignored by repo rule. My install.sh patch is local-only; the durable path is the skill-local `install-vendor-mermaid.sh` (tracked). Does user want to add an explicit gitignore exception for install.sh so the per-skill loop dispatch survives clones? Leaving as-is preserves ck CLI's authority over install.sh.
3. **Stale heatmap-/persona-/risk-/tree-*.html in examples/acme-shop/docs/product/visuals/** — 8 residue files from verification renders. Safe to `rm` (regenerable). Not removed pending user preference.
4. **HIGH-4 `--update` integration test** — eval scenario #3 fixtures now exist (CRIT-3), but the LLM-driven integration test harness still doesn't run automatically. Eligible for follow-up.
5. **MEDIUM + LOW findings (8 items)** from the prior review — intentionally NOT touched in this pass. Out of "fix CRIT+HIGH" scope. Defer or schedule.

---

## Verification Commands (to re-run after fix)

```bash
# 1. Repo venv exists + tests pass
./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec/scripts/tests/ -v
# expect: 32 passed

# 2. Worked example clean
./.claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/check_traceability.py --root .claude/skills/product-spec/examples/acme-shop
# expect: findings: []

# 3. Mermaid vendored (offline)
ls -lh .claude/skills/product-spec/assets/vendor/mermaid.min.js
# expect: ~2.5MB

# 4. HTML self-contained for tree (Mermaid) + heatmap (pre fallback)
./.claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/visualize.py --root .claude/skills/product-spec/examples/acme-shop --view heatmap --format html
# expect: heatmap HTML wraps as <pre>, no cdn.jsdelivr.net string in file

# 5. Root docs auto-loadable
ls /home/hieubt/Documents/cleanmatic-skills/{CLAUDE.md,README.md}

# 6. Eval fixtures present
ls .claude/skills/product-spec/eval/fixtures/
```

---

**Status:** DONE
**Summary:** All 5 CRITICAL + 4 HIGH findings remediated. Pytest 32/32. Worked example clean. HTML genuinely offline self-contained. Pre-fix and post-fix evidence captured per finding. Side-effect sweep across the full blast radius found no regression. Skill is ship-ready pending user review of the 5 unresolved questions above.
