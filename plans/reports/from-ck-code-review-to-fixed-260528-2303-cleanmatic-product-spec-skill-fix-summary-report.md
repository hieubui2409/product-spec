---
type: fix-summary
date: 2026-05-28T23:03
upstream-report: from-ck-code-review-to-planner-260528-2241-cleanmatic-product-spec-skill-hardcore-review-report.md
status: complete
tests-before: 57 passed
tests-after: 76 passed (+19 new regression tests)
---

# Fix Summary — cleanmatic:product-spec hardcore-review findings

All 17 findings from the hardcore review acted on. 2 deferred per PO answer; 15 fixed in code + docs. Test suite grew from 57 → 76 (+19 targeted regression tests, all green).

## Decisions captured (PO interview, this session)

| Drift | PO decision |
|-------|-------------|
| M-1 (CLAUDE.md location, §18) | Keep current (repo-root only); amend §18 with rationale |
| M-2 (viz filter wont/out, §15) | Default show-all WITH visual marker; opt-in `--filter-wont` to hide |

Both amendments recorded in `brainstorm-decisions-260528-0818-...md` (Amendments section).

## Findings × Disposition

| ID | Title | Action | Where |
|----|-------|--------|-------|
| C-1 | personas/list-fields leak "TBD" | FIXED + shape check + e2e test | `generate_templates.py` `LIST_FIELDS` default, `check_consistency.py` `invalid_type` finding, 3 new tests |
| H-1 | Mermaid tree inverted vs ASCII | FIXED + orientation test | `render_mermaid.py` `flowchart TB → BT`, test_w3_h1 |
| H-2 | install.sh swallows pytest exit | FIXED + sanity probe | `install.sh:67` capture-then-tail pattern, validated externally |
| M-1 | §18 silent reversal | AMENDED §18 | brainstorm report, phase-01 |
| M-2 | §15 filter not implemented | IMPLEMENTED + amended §15 | `render_ascii/mermaid` marker (`*` / classDef deferred), `visualize.py --filter-wont`, 5 new tests |
| M-3 | V6 horizon orphan | DELETED V6 | `interview-vision.md` (now V1-V7) |
| M-4 | Phase 2 SC4 "4 formats" | FIXED → "3 formats" | `phase-02-reference-specs.md` |
| M-5 | Phase 1 in-skill CLAUDE.md ref | UPDATED with §18 amendment pointer | `phase-01-scaffold-skeleton.md` |
| M-6 | status_inconsistency skips PRD↔goal | FIXED + test | `check_consistency._status_inconsistency` iterates `brd_goals`, test_w3_m6 |
| M-7 | --viz delta needs 2 snapshots | FIXED + test | `visualize._load_baseline` 1-snap fallback, test_w3_m7 |
| M-8 | No CI-runnable strict gate | NEW `strict_gate.py` + workflow update + 2 tests | new file `scripts/strict_gate.py`, `workflow-validate.md` |
| L-1 | --diff <bad> silent | FIXED — raises FileNotFoundError w/ available list | inside `_load_baseline`, test_w3_l1 |
| L-2 | workflow-validate uses `python3` | FIXED — repo venv path | `workflow-validate.md` Step 1 |
| L-3 | example PRODUCT.md duplicates core_value | FIXED — body stubbed | `examples/acme-shop/.../PRODUCT.md` |
| L-4 | gap-view counts any inbound edge | FIXED — match by expected child type | `render_ascii.gap` + `render_mermaid.gap`, test_w3_l4 |
| L-5 | snapshot filename/body clock skew | FIXED — derive filename from generated_at | `spec_graph.write_snapshot`, test_w3_l5 |
| L-6 | `_escape` quote-escape defensive | NO ACTION — already documented as defensive |
| L-7 | unused BRD goal `parent` claim | CLEANED UP | `spec_graph.PARENT_FIELD_BY_TYPE` (goal removed), spec doc updated |
| N-1 | examples bloat (17 HTML) | DEFERRED per PO |
| N-2 | test coverage gaps | DONE — 19 new tests covering every fix path |
| N-3..N-6 | observations | NOTED — no code action |
| N-7 | persona soft-cap not enforced | NEW warn finding | `check_consistency.persona_cap_exceeded` (soft cap 4), 2 tests |
| N-8 | `.session.md` gitignore guard | NEW warn finding | `check_consistency._session_md_gitignore`, 1 test |

## Files Touched

**Scripts (mutated):**
- `scripts/generate_templates.py` — `LIST_FIELDS` defaults (C-1)
- `scripts/check_consistency.py` — `LIST_FIELDS` shape check (C-1), persona cap (N-7), `.session.md` gitignore guard (N-8), PRD↔goal status (M-6)
- `scripts/render_ascii.py` — deferred marker helpers, `filter_wont` on tree/roadmap/persona, gap-view DRY fix (L-4), persona list-shape guard
- `scripts/render_mermaid.py` — `flowchart BT` (H-1), deferred classDef + filter (M-2), gap-view DRY fix (L-4)
- `scripts/visualize.py` — `--filter-wont` flag (M-2), 1-snap baseline (M-7), bad-diff raises (L-1)
- `scripts/spec_graph.py` — `root_path` in graph for N-8, snapshot filename from generated_at (L-5), drop unused goal parent field (L-7)
- `install.sh` — capture-then-tail (H-2)

**New files:**
- `scripts/strict_gate.py` — shell-runnable CI strict gate (M-8)

**Tests:**
- `scripts/tests/test_scripts.py` — +10 W3 regression tests
- `scripts/tests/test_visualize.py` — +9 W3 regression tests

**References / docs:**
- `references/interview-vision.md` — V6 deleted, V7→V6 renumber, note (M-3)
- `references/workflow-validate.md` — repo venv paths (L-2), strict_gate doc (M-8)
- `references/frontmatter-and-id-spec.md` — drop goal `parent` claim (L-7)

**Examples:**
- `examples/acme-shop/docs/product/PRODUCT.md` — core_value body stubbed (L-3)

**Plans:**
- `phase-01-scaffold-skeleton.md` — §18 amendment pointer (M-5)
- `phase-02-reference-specs.md` — SC4 → 3 formats (M-4)

**Decisions:**
- `brainstorm-decisions-260528-0818-...md` — Amendments section (§15, §18)

## Verification Evidence

```
$ .claude/skills/.venv/bin/python3 -m pytest .claude/skills/product-spec/scripts/tests/ -q
76 passed in 0.92s

$ bash .claude/skills/product-spec/install.sh
... yaml=6.0.3 pytest=9.0.3
76 passed in 0.85s
─────────────────────────────────────────────────────
Install complete. ...

$ bash /tmp/test-install-failure.sh    # sanity probe: pytest fail → install fails
Correctly captured pytest exit code: 4
Final exit code: 4
```

## What Was NOT Touched

- `references/document-model-and-hierarchy.md` — no findings against it.
- `references/visualization-spec.md` — current content matches shipped 3-format reality.
- Other interview banks (BRD/PRD/Epic/Story/frameworks) — no orphan questions.
- Assets templates — only PRODUCT.md example fixed (template itself was already correct per SA-11A).
- Vendored Mermaid JS — no change.
- `agents/.gitkeep` — placeholder retained.

## Open Items (deferred per PO answer + brainstorm-leftover)

1. **N-1**: examples/visuals/*.html bloat (17 files) — **PO confirmed defer (2026-05-28T23:21)**. Status: accepted-as-is; revisit in a future janitor pass when needed.
2. **VI question-bank native-speaker review** — **PO confirmed (2026-05-28T23:21)**: ship VI best-effort as-is; update later when native-speaker feedback arrives. Status: parked-pending-feedback (no blocker).

## Unresolved Questions

None. All review findings either fixed, amended-in-decisions, or explicitly accepted-as-deferred by PO.
