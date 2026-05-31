# Product-Spec Skill — Deferred Items Remediation

**Date:** 2026-05-28 22:29
**Scope:** Fix the 4 deferred findings + act on 2 worth-knowing observations the PO approved via interview. Add regression tests. Verify end-to-end.

---

## TL;DR

- **6 items shipped:** SA-7A, SA-11A, NEW-12, NEW-14, O-3, O-5.
- **10 new regression tests** added; **41/41 pytest PASS** (zero regressions in prior 31).
- **5/5 end-to-end smoke tests** confirm behaviors hold against the worked example.
- **Worked example still validates clean** (0 findings / 0 parse errors) after template changes.
- **All 4 unresolved questions** resolved per PO selection.

---

## Item-by-Item Evidence

### 1. SA-7A — BRD `goals` shape (template + reference)

**PO decision:** Both — template inline example + reference doc.

| | Before | After |
|---|---|---|
| Template (`assets/templates/brd.md`) | `goals: {{goals}}` with no shape hint | `goals: {{goals}}` preceded by 13-line YAML comment block showing the list-of-dicts shape with example (`id`, `title`, `metrics`, `status`, `owner`) |
| Reference (`references/frontmatter-and-id-spec.md`) | BRD goals only mentioned in ID grammar + parent-link tables | New section "BRD `goals` (under `brd.md` `goals:` key)" with full shape + example + cross-pointer to template |
| Smoke verification | UC7 had to read `spec_graph.py` source to discover shape | Generated `brd.md` now ships with shape comment inline; smoke test 3 grep'd it back |

**Regression tests:** `test_brd_template_carries_inline_goals_shape_example`, `test_brd_goals_shape_documented_in_reference`.

### 2. SA-11A — PRODUCT.md core_value DRY (replace body with stub)

**PO decision:** Replace body content with reference-only stub.

| | Before | After |
|---|---|---|
| Template (`assets/templates/product.md`) | `## Core Value` heading followed by `{{core_value}}` → token substituted twice (frontmatter + body) | `## Core Value` heading followed by `_(authoritative value lives in frontmatter `core_value` field — see top of file. Body deliberately blank to keep one source of truth.)_` |
| Token count in template | 2 occurrences of `{{core_value}}` | 1 occurrence (frontmatter only) |
| DRY status | Same fact in 2 places → drift possible | One authoritative home (frontmatter) → no drift surface |

**Regression test:** `test_product_template_core_value_body_is_stub_not_duplicate` — verifies `{{core_value}}` count == 1 AND body stub text present.

### 3. NEW-12 — Script-level `--approve` gate (defense-in-depth)

| | Before | After |
|---|---|---|
| `generate_templates.fill_defaults()` | Accepted any `status` value passed via `--values` | Rejects `status: approved` with `ValueError` ("generate_templates refuses to create … with status='approved'. New artifacts must start as 'draft'. Use the explicit approval flow…") |
| Exit code on rejection | (would happily emit approved-from-init artifact) | Exit code **1** with clear message on stderr (smoke test 4 verified) |
| Default status (no `--values`) | `draft` | `draft` (unchanged — backward compatible) |

**Regression tests:** `test_generate_rejects_approved_status_at_script_layer`, `test_generate_allows_default_draft_status`.

### 4. NEW-14 — `render_html.py` CDN-fallback refactor

**Behavior:** Identical to before. Internal split only.

| | Before | After |
|---|---|---|
| One mixed function `_load_mermaid_js()` doing both vendored-load and CDN-fallback assembly | Two single-responsibility helpers + thin compatibility wrapper |
| `_load_vendored_mermaid_js()` | (didn't exist) | Returns vendored payload or `None` |
| `_cdn_fallback_snippet()` | (didn't exist) | Returns the `</script>...<script src=CDN></script><script>` snippet |
| `_load_mermaid_js()` | Mixed both paths | Thin wrapper: vendored if present, else CDN snippet |
| `Optional` import | (already present line 21) | Reused |

**Regression test:** `test_render_html_vendored_path_split_into_two_functions` — verifies all 3 helpers exist + behave correctly.

### 5. O-3 — Tree view `--lang vi` localization

**PO decision:** Prefix + edge labels (only `PRODUCT:` prefix is meaningfully localizable; goal titles already flow through frontmatter).

| | Before | After |
|---|---|---|
| ASCII tree `--lang vi` | `PRODUCT: Acme Shop` (hardcoded EN) | `SẢN PHẨM: Acme Shop` (VI) — smoke test 1 verified |
| ASCII tree `--lang en` (default) | `PRODUCT: Acme Shop` | `PRODUCT: Acme Shop` (unchanged — backward compatible) — smoke test 2 verified |
| Mermaid tree `--lang vi` | Node label `"PRODUCT"` | Node label includes `"SẢN PHẨM: ..."` |
| `i18n_labels.LABELS` | 7 keys per locale | 8 keys per locale (added `product`) |
| `visualize.py` lang routing | Passed lang to `roadmap` + `moscow` only | Passes lang to `tree` + `roadmap` + `moscow` |

**Regression tests:** `test_ascii_tree_vi_localizes_product_prefix`, `test_ascii_tree_en_default_unchanged`, `test_mermaid_tree_vi_localizes_root_node_label`, `test_visualize_routes_lang_to_tree_view`.

### 6. O-5 — README troubleshooting row for `/tmp/`-workspace `.venv` access

**PO decision:** Document only (skill scope).

| | Before | After |
|---|---|---|
| README troubleshooting table | 6 rows | 7 rows (new: "Running scripts from a workspace under `/tmp/...` can't see the `.venv` binary" → guidance to run from project root or use system `python3` with `pyyaml`) |

No code change. No new test. Documentation-only fix as the PO requested (`O-5 — Document only — add note in skill README about running tests from /tmp/ workspaces`).

---

## Verification Matrix

| Verification path | Result |
|---|---|
| `pytest .claude/skills/product-spec/scripts/tests/test_visualize.py -v` | **41/41 PASS** in 0.48s |
| Smoke 1: `visualize.py --view tree --lang vi` on acme-shop | `SẢN PHẨM: Acme Shop` rendered ✓ |
| Smoke 2: `visualize.py --view tree` (default EN) on acme-shop | `PRODUCT: Acme Shop` rendered ✓ |
| Smoke 3: `generate_templates.py --type brd --write` | New BRD ships with goal-shape comment block ✓ |
| Smoke 4: `generate_templates.py --type prd --values '{"status":"approved"}'` | `ValueError`, exit code 1 ✓ |
| Smoke 5: `check_consistency.py + check_traceability.py` on acme-shop | 0 findings, 0 parse errors ✓ |

---

## Test Inventory Growth

| Session phase | Tests | Delta |
|---|---|---|
| Pre-session baseline | ~18 | — |
| After 4-wave fixes (NEW-1…15) | 31 | +13 |
| After this remediation pass (6 deferred items) | **41** | +10 |

The 10 new tests:
- `test_brd_template_carries_inline_goals_shape_example` (SA-7A)
- `test_brd_goals_shape_documented_in_reference` (SA-7A)
- `test_product_template_core_value_body_is_stub_not_duplicate` (SA-11A)
- `test_generate_rejects_approved_status_at_script_layer` (NEW-12)
- `test_generate_allows_default_draft_status` (NEW-12 backward-compat)
- `test_render_html_vendored_path_split_into_two_functions` (NEW-14)
- `test_ascii_tree_vi_localizes_product_prefix` (O-3)
- `test_ascii_tree_en_default_unchanged` (O-3 backward-compat)
- `test_mermaid_tree_vi_localizes_root_node_label` (O-3)
- `test_visualize_routes_lang_to_tree_view` (O-3 dispatcher integration)

---

## Files Touched

| File | Change |
|---|---|
| `.claude/skills/product-spec/assets/templates/brd.md` | Added 13-line YAML comment block above `goals:` |
| `.claude/skills/product-spec/assets/templates/product.md` | Replaced `{{core_value}}` body with reference-only stub |
| `.claude/skills/product-spec/references/frontmatter-and-id-spec.md` | Added "BRD `goals` (under `brd.md` `goals:` key)" section |
| `.claude/skills/product-spec/scripts/generate_templates.py` | Added `status=='approved'` rejection guard in `fill_defaults` |
| `.claude/skills/product-spec/scripts/render_html.py` | Split `_load_mermaid_js` → `_load_vendored_mermaid_js` + `_cdn_fallback_snippet` (compat wrapper preserved) |
| `.claude/skills/product-spec/scripts/i18n_labels.py` | Added `product` key (EN: `PRODUCT`, VI: `SẢN PHẨM`) |
| `.claude/skills/product-spec/scripts/render_ascii.py` | `tree()` now accepts `lang`, uses `label('product', lang)` |
| `.claude/skills/product-spec/scripts/render_mermaid.py` | `tree()` now accepts `lang`, localizes root node label |
| `.claude/skills/product-spec/scripts/visualize.py` | Lang routing extended to `tree` view |
| `README.md` | Troubleshooting row added for `/tmp/` `.venv` access |
| `.claude/skills/product-spec/scripts/tests/test_visualize.py` | +10 regression tests |

---

## Unresolved Questions Resolution

Per the interview-driven decisions:

| Q | PO decision | Status |
|---|---|---|
| Q1 — SA-7A scope | Template inline + reference doc (both) | Implemented |
| Q2 — SA-11A resolution | Reference-only stub | Implemented |
| Q3 — NEW-12/14 trigger | Fix now (selected in deferred list) | Implemented |
| Q4 — `.venv` sandbox handling | Document only (skill README) | Implemented |

No remaining open questions on the items the PO selected.

---

## Cumulative Skill State

After this remediation:

- **5 original CRITs:** fixed + verified
- **14 re-review findings:** 12 + 2 originally deferred = **all 14 fixed** (NEW-12 + NEW-14 closed this pass)
- **6 sub-agent-surfaced bugs:** SA-1A, 1B, 1C, 4A, 7A, 11A — **all fixed**
- **8 worth-knowing observations:** O-3 (tree --lang) + O-5 (README note) actioned; O-1, O-2, O-4, O-6, O-7, O-8 are by-design or positive signals
- **Pytest:** 41/41 PASS
- **9 visualization views × 3 formats matrix:** 27/27 working
- **65/65 blind sub-agent assertions PASS** (across 11 agents in 4 rounds) — prior verification holds; no behavior change in the user-facing render paths
- **Worked example:** 0 findings, 0 parse errors

**Verdict:** All previously-known gaps closed. Skill production-ready for PO distribution.

---

## Notes / No Open Questions

No outstanding unresolved questions. Next remediation pass would only trigger from a fresh defect surfaced by future real-PO usage.
