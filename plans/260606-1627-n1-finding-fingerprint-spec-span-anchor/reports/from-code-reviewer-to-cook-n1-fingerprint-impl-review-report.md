# N1 finding-fingerprint — implementation review (code-reviewer → cook)

Scope: working-tree diff of `critique_inherit.py`, `critique_cache.py` + 2 test files.
Both suites pass on my run: critique **167**, product-spec **619** (matches claim, no regression).
Method: read diff + full source, traced graph API, ran resolver/normalize/lazy-graph/determinism probes, traced every `_index_rows`/`upsert_findings` caller.

## Acceptance criteria — verdict by criterion

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | line drift (same text :5→:7) → one row, latest ts | PASS (code, not just test) | `_index_rows` key=`fp or eid`, `>=` keeps latest ts (L143-146); probed live |
| 2 | two distinct cited texts on one node → 2 fps | PASS | distinct prose → distinct hash; probed |
| 3 | edit cited text → new fp | PASS | text in hash input (L76); probed |
| 4 | legacy rows w/o field → load+dedup, eid fallback | PASS | `upsert_findings` `f.get(k)`→None (cache L75); `_index_rows` `or eid` (L143) |
| 5 | unresolvable / empty-normalize / BRD-goal structural → None, no merge, no crash | PASS **with caveat** (see MAJOR-1) | all resolver edges return None (probed); empty-normalize→None (L74-75) |

Checklist b/c/d/e/h all verified:
- **b (B1 guard):** correct. `_fingerprint` gates on the *normalized* value (L73-75), not raw — None-on-empty confirmed. `_index_rows` `fp or eid`: `None` is falsy → keys by eid → two None-fp findings keep distinct eids, do NOT merge (probed: 2 rows).
- **c (blast radius):** clean. Both `_index_rows` callers (`_inherited_candidates` L156, `build_descendant_rollup` L231) read only dedup-surviving fields. `_public` (L181) whitelists fields → `finding_fingerprint` does NOT leak into the lens bundle. `upsert_findings` external callers unaffected (`f.get`). `index_report_findings` signature unchanged. Cross-scope merge only newly occurs on the intended line-drift collapse; same-eid two-scope still dedups exactly as pre-N1 (probed).
- **d (lazy graph):** correct. 0 indexable findings → 0 builds; 3 indexable → 1 build (probed). `build_graph(Path(root))` is the right API (`spec_graph.py:245`); `n["file"]` is relative to `docs/product` (`spec_graph.py:100`) so `root/docs/product/file` resolves correctly.
- **e (resolver edges):** all 6 edges (no `:line`, non-int, unknown node, node missing `file`, unreadable file, out-of-range) return None, none raise (probed).
- **h (determinism):** pure sha256, no wall-clock/random; stable across calls (probed).

---

## Findings

### MAJOR-1 — `_BULLET_RE` over-strips leading content digits → false-merge of numbered-list siblings
`critique_inherit.py:58` `_BULLET_RE = ^[\s>#*\-+0-9.)]+`

The class eats leading **content** digits/`+`/`-`, not just markup. Probed:
- `"5xx errors must be retried"` → `"xx errors must be retried"` (lost the `5`)
- `"+10% growth"` → `"% growth"`; `"-5 is invalid"` → `"is invalid"`
- `"3. Xem số dư"` and `"7. Xem số dư"` → **identical** normalized text → **identical fingerprint** (probed `FALSE-MERGE`).

Consequence: two genuinely distinct blockers on the same node+severity that cite numbered-list items with **identical prose but different list numbers** silently merge into one index row → the older finding is dropped, undercount in inherited-context / rollup blocker counts. This is the exact undercount class N1 exists to fix, reintroduced for this line shape. The B1 None-guard does **not** catch it: normalized text is non-empty (`"xem số dư"`), so it yields a real colliding hash, not None.

Why prior verification missed it: the red-team B1 analysis covered *all-markup* lines collapsing to `""` (guarded correctly). It did not cover *partial* strip of a non-empty line. The real spec (`docs/product/`) is dense with ordered lists (user stories, risks, interview Qs — 19+ leading-digit lines), so the shape is reachable, though a true false-merge needs identical post-strip prose (narrower than the common distinct-prose case, which is safe — probed `OK-distinct`).

Severity rationale (MAJOR not BLOCKER): confined to the lossy blockers index (never touches user-facing spec content); requires a specific spec shape (duplicate prose across differently-numbered list items); common numbered-list findings with distinct prose are unaffected.

Fix: strip only the markdown *marker glyph*, not embedded content digits. Replace the bullet class so it matches an ordered/unordered list marker as a unit, e.g.
`^\s*(?:[>#*+\-]+\s*|\d+[.)]\s+)*` — i.e. allow `\d+[.)]` only when followed by whitespace (a real list marker), never a bare leading digit that is content (`5xx`, `+10%`). Add tests: `5xx…`, `+10%…`, `-5 …` keep their leading token; `1. X` and `2. X` (distinct list numbers, same prose) → assert they do NOT collide if list-number significance is desired, OR document that list-number is intentionally dropped. Pick one and lock it.

### MINOR-1 — B1 collision survives only because severity+node usually differ
Not a defect in the guard itself, but note the residual: after MAJOR-1 fix, any two non-empty lines that legitimately normalize identical (e.g. two AC bullets with the same sentence on the same node+severity) still merge by design. That is the intended identity model (same content = same finding), so acceptable — but worth a one-line comment at `_fingerprint` stating "identical normalized text on the same node+severity is treated as the same finding by design" so a future reader doesn't file it as a bug.

### NIT-1 — return annotation `_fingerprint(...) -> str` but returns `None`
`critique_inherit.py:68`. Function returns `None` on empty-normalize (L75). Should be `Optional[str]`. `_resolve_line_text`/`_finding_fingerprint` correctly omit the annotation. `Optional` not yet imported from `typing` (L21). No runtime impact (pyflakes doesn't check return types; no mypy in CI). Cosmetic consistency only.

### NIT-2 — `_resolve_line_text` rebuilds the node-index per call
`critique_inherit.py:91` `{x["id"]: x for x in graph.get("nodes", [])}.get(node)` is rebuilt for every finding in the loop. For the lossy blockers index (small N per run) this is negligible — flagging only for awareness, not action (YAGNI; do not pre-optimize).

---

## Style / idioms
Helper placement, docstrings, `\0`-delimited hash input, comment density all match the file's existing conventions. Lazy-graph comment (L260-261) and the `_index_rows` dedup docstring (L132-137) are clear and self-contained (no plan-artifact references — complies with `review-audit-self-decision.md` §5). Pyflakes warnings present are all pre-existing re-export noise in `critique_cache.py`, unrelated to this diff.

---

## Verdict: **fix-then-ship**

One MAJOR (over-strip false-merge) that is a real, in-design-scope undercount regression reachable on this codebase's ordered-list-heavy specs. It is a small regex fix + 3 tests, not a rework. NITs optional. Everything else (B1 guard, blast radius, lazy graph, resolver edges, determinism, legacy tolerance, all 5 acceptance criteria) is correctly implemented and verified empirically, not just by the bundled tests.

## Unresolved questions
1. Is list-number significance intended? i.e. should `1. X` and `2. X` (same prose) be the SAME finding or DIFFERENT? The current code says same (number stripped); the fix could go either way. Needs a one-line design ruling before locking the regex — this is a product/identity decision, not a code call.
2. `lang: vi` specs: `_normalize_line` lowercases + does no Unicode NFC/NFD normalization. Two byte-different-but-visually-identical Vietnamese lines (NFC vs NFD) → different fingerprints. Red-team flagged this as YAGNI-skippable (same file/encoding → same form in practice). Confirm it stays out of scope.
