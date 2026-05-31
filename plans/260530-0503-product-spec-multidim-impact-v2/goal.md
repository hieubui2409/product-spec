# goal.md — Definition of Done (review oracle)

> Drives the Workflow orchestrator's **overall-review** + **multi-wave-review** loop (Phase 1).
> Each gate = `{id, statement, verify}`. A wave re-verifies EVERY gate; any FAIL → fix wave → re-verify.
> **Exit condition:** 2 consecutive waves with ZERO fails. Ship only after exit.
> Source of truth: `plans/reports/brainstorm-design-260530-0309-product-spec-multidim-impact-uc3-report.md` (§0 AUTHORITATIVE).

## A — Deal-breakers (Q59; non-negotiable, block ship)

- **G-A1 Traceability + ID integrity** — existing checks pass on v1 + v2 specs; parent-scoped ID grammar unchanged (`BRD-G1`/`PRD-AUTH`/`PRD-AUTH-E1-S1`). *Verify:* **full** `pytest scripts/tests` green (every suite, incl. all new ones — not just traceability/consistency); `--validate` on `examples/acme-shop` → 0 structural errors.
- **G-A2 Back-compat** — a v1 spec (no new fields) parses + validates + visualizes with NO error; new fields optional, absence → null/empty. *Verify:* eval `backcompat-v1-spec` green.
- **G-A3 No-auto-edit-approved** — contradiction with `approved` artifact → keep/change/hybrid surfaced; never auto-flip. *Verify:* eval `impact-pass` approved branch + code-path review.
- **G-A4 Determinism** — same input → byte-identical ASCII/Mermaid/JSON; cycle detection emits sorted/stable output. *Verify:* exact-text pytest; run twice, `diff` empty.

## B — Script-vs-LLM split (Q37)

- **G-B1 Scripts structural-only** — `dep_cycle`, `dep_dangling`, `dep_order`, enum/shape, `time_child_late`, `risk_high_ratio`, `risk_blindspot`, `overdue` are deterministic Python, NO LLM. *Verify:* code review + tests.
- **G-B2 LLM judgment-only** — `time_realism`, `competitive_drift` in LLM layer; every finding cites data points. *Verify:* prompt scaffolds present; hallucination evals pass.

## C — Dimension RISK (Phase 2)

- **G-C1** `prd.md` carries `risks:` (closes grounded bug #3); `--viz risk` shows PRD **and** Epic risks. *Verify:* eval `risk-complete`.
- **G-C2** `impact`/`likelihood`/`status` enum-validated (closes bug #4); typo → `unknown_enum` error. *Verify:* eval `risk-complete` typo branch.
- **G-C3** `mitigation` + `status` (open/mitigated/accepted) supported. *Verify:* template + parser tests.
- **G-C4** `risk_high_ratio` (>50% high) warn [script]; `risk_blindspot` (≥5 story, 0 risk) warn **[script]** — both are deterministic counts (NOT LLM; keeps G-B1 split). *Verify:* tests `risk-high-threshold`, `risk-blindspot`.

## D — Dimension TIME (Phase 3)

- **G-D1** `target_date` (ISO) on PRD+Epic; optional. *Verify:* parser test.
- **G-D2** `depends_on` edge built into graph; `dep_dangling` (error) on unresolved ID. *Verify:* traceability test.
- **G-D3 (T1)** `dep_cycle` (error) detects A→B→…→A; cycle detection is **iterative** (no `RecursionError` on long chains); ALL new renderers walking `depends_on` are cycle-safe (visited-set) — NO hang. *Verify:* pytest self-loop / 2-node / 3-node cycle + long-chain (no RecursionError) + renderer-on-cyclic-graph **terminates** (pytest-timeout marker, not a wall-clock SLA).
- **G-D4** `time_child_late` (warn, deterministic) when child `target_date` > parent. *Verify:* eval `time-child-late`.
- **G-D5** `overdue` advisory via `time_advisory.py --today` (OUTSIDE gate → keeps determinism). *Verify:* eval `time-overdue`.
- **G-D6 (T2)** `time_realism` (LLM warn) flags ONLY with structured anchors (size + #stories + horizon + days_remaining) + cites data; uncertain → no-flag. `days_remaining` is SCRIPT-precomputed from a **pinnable `--today`** (default real today; evals pin it) — keeps the anchor deterministic. *Verify:* eval true-positive + must-not-flag + missing-anchor (today pinned).

## E — Dimension COMPETITION (Phase 4)

- **G-E1** `competitors` at BRD (id+name+url+threat); `competitive_parity` at PRD (enum ahead/parity/behind/none). *Verify:* parser + enum tests.
- **G-E2** parity matrix + threat heatmap render **HTML-native** (not Mermaid). *Verify:* eval `competition-parity`.
- **G-E3 (T2)** `competitive_drift` (LLM warn) anchored to parity enum + cites; conservative. *Verify:* eval true-positive + must-not-flag + missing-anchor.
- **G-E4 OpSec** — parser IGNORES any `url` with `private:` prefix; encourages public URLs only. *Verify:* parser test `private-url-skipped`.

## F — Impact-engine + migration (Phase 5)

- **G-F1** impact-pass runs on `--update` AND `--validate`; uses `downstream()` + LLM 1-liner + action suggestion. *Verify:* eval `impact-pass`.
- **G-F2** output → `docs/product/impact/<ts>.md`; change-log gains `dims` (NOTE: `affected_set` already exists in `change-log-entry.md` — extend, don't re-add). *Verify:* output-file present + change-log `dims` field test.
- **G-F3** migration script: auto draft/review + backup; `approved` confirm-per-item; empty placeholder for missing fields. *Verify:* eval `migration`.

## G — Visualization (Phases 3/4/6)

- **G-G1** per-dim views (`time`, `competition`) + 1 HTML-only `dashboard`. *Verify:* render tests.
- **G-G2** ASCII NOT deleted (§0.2) — HTML-native = new default; ASCII retained as **minimal text-summary tree**; zero-dep terminal path works. *Verify:* render test text-summary present; `test_visualize` tree-text retained.
- **G-G3** matrix / heatmap / risk-grid render HTML-native. *Verify:* `render_html` tests.

## H — Cross-cutting

- **G-H1** Bilingual EN/VI labels for new enums/views via `i18n_labels.py`; VI native-reviewed (review-pending note removed per owner). *Verify:* i18n test.
- **G-H2** Version → **2.0.0** consistent across `SKILL.md`, `CLAUDE.md`, references. *Verify:* grep version == 2.0.0.
- **G-H3** references updated (frontmatter-and-id-spec, validation-rules-spec, document-model, visualization-spec, interview banks). *Verify:* docs review.
- **G-H4** `examples/acme-shop` migrated to v2 + green `--validate`. *Verify:* validate run.
- **G-H5** full `pytest` + all evals green. *Verify:* pytest + eval runner.

## Out of scope (do NOT build — Q6/Q66/Q67)

- COST model / story-points / hours / RICE-WSJF scoring (only `size: S/M/L` proxy stays).
- Auto-fetch competitor data (PO enters by hand; URL stored only).
- Separate `impact` skill (Hướng C rejected).
- Real PDF/SVG/PNG binary.
