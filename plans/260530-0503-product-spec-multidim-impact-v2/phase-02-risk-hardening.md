---
phase: 2
title: "Risk Hardening"
status: pending
priority: P1
effort: "1d"
dependencies: [1]
---

# Phase 2: Risk Hardening

## Overview

Finish the half-wired RISK dimension (the only dimension with an existing "home"). Closes two **grounded bugs**: #3 `prds/*.md` never carried `risks:` so `--viz risk` only saw epic risks; #4 `impact`/`likelihood` were never enum-validated so typos passed silently. Add `mitigation` + `status` to risk entries, a `risk_high_ratio` script warn, and a `risk_blindspot` **script** warn (deterministic count — NOT LLM; see RT1 F1). Non-breaking (new fields optional) → quick-win, ships independently.

## Key Insights (grounded)

- `assets/templates/epic.md:21` HAS `risks: {{risks}}`; `assets/templates/prd.md` does NOT — bug #3.
- `check_consistency.py` `ENUMS` (~39-46) covers status/scope/moscow/horizon/size/lang — **no** risk enum — bug #4. `LIST_FIELDS` (~54-60) already lists `risks`.
- `spec_graph.py` `_risks()` (~214-223) collects risks from ALL artifact types already — so once `prd.md` carries `risks:`, PRD risks flow into `--viz risk` with no graph change.
- Threshold-as-module-constant pattern already exists (`PERSONA_SOFT_CAP`) — reuse for `RISK_HIGH_RATIO` + `RISK_BLINDSPOT_MIN_STORIES`.

## Requirements

- **Functional:** PRD risks parse + render; `impact`/`likelihood` ∈ {low,med,high} and `status` ∈ {open,mitigated,accepted} enum-validated; bad shape → reuse existing `invalid_type`; `risk_high_ratio` warn when >50% risks are `high`; `risk_blindspot` warn **[script]** when an epic has ≥5 child stories and 0 risks (deterministic count).
- **Non-functional:** back-compat (no `risks:` → empty, no error); deterministic; scripts structural-only, blindspot LLM-only.

## Architecture

New frontmatter (both PRD + Epic):

```yaml
risks:
  - description: "Third-party OAuth dependency"
    impact: high          # enum low|med|high   (ENUM-VALIDATE — bug #4)
    likelihood: med        # enum low|med|high
    mitigation: "Fallback provider on standby"   # new, optional free-text
    status: open           # enum open|mitigated|accepted   (new)
```

Flow: `prd.md` gains `risks:` → `_risks()` already aggregates → existing `--viz risk` 3×3 grid now includes PRDs. `render_html.py` risk view becomes HTML-native grid (Q44; not Mermaid).

## Related Code Files

- Modify: `assets/templates/prd.md` (+`risks: {{risks}}` frontmatter block — mirror epic.md).
- Modify: `assets/templates/epic.md` (+`mitigation`/`status` in the risk dict example).
- Modify: `scripts/check_consistency.py` — extend `ENUMS` with `risk_impact`/`risk_likelihood`/`risk_status`; **reuse existing `invalid_type`** (line ~110) for malformed risk entries (do NOT add a new `invalid_shape` — F7); add `_check_risk_high_ratio()` (`risk_high_ratio`) + `_check_risk_blindspot()` (`risk_blindspot`, deterministic count via graph child-story count); module consts `RISK_HIGH_RATIO=0.5` + `RISK_BLINDSPOT_MIN_STORIES=5`, commented (mirror `PERSONA_SOFT_CAP`).
- Modify: `scripts/spec_graph.py` `_risks()` — pass through `mitigation`/`status` into the risk objects (so HTML grid can show them).
- Modify: `scripts/render_html.py` — risk view = HTML-native 3×3 grid (impact × likelihood) with cell drill-down listing description+mitigation+status. **DONE**: added `render_html.risk()` (self-contained `<table>` fragment, theme-aware scoped CSS, server-escaped spec text, `(unrated)` overflow row for off-enum cells); `_render_view_body` gained a safe `risk-grid` format; risk inlines NO Mermaid runtime / NO marked·DOMPurify (symmetric H4 gating).
- Modify: `scripts/visualize.py` — route `--view risk --format html` to `render_html.risk()` BEFORE the generic Mermaid/`<pre>` fallback. **DONE** (was the missing link: risk previously fell back to ASCII-in-`<pre>`).
- Modify: `scripts/generate_templates.py` — confirm `risks` default fill (LIST_FIELDS already includes it).
- Modify: `references/validation-rules-spec.md` — add `risk_high_ratio` (script) + `risk_blindspot` (script) rows + risk enum note.
- verify/extend (file already existed from a prior cycle — plan staleness): `scripts/tests/test_risk_complete.py` — extended with the HTML-grid render assertions (`<table>` not `<pre>`, mitigation+status surface, escaped spec text, deterministic fragment, end-to-end `visualize.py` dispatch).

## Implementation Steps

1. **TDD RED** — write `test_risk_complete.py` + extend `test_check_consistency.py` with the failing cases below.
2. Add `risks:` block to `prd.md` template.
3. Extend `ENUMS` (risk_impact/risk_likelihood/risk_status) + wire into the existing per-field enum check so `risks[].impact` etc. validate.
4. Reuse existing `invalid_type` (check_consistency.py:~110) for a risk entry that is not a dict / missing `description` — do NOT invent `invalid_shape` (F7).
5. Add `_check_risk_high_ratio()` → `risk_high_ratio` warn (const `RISK_HIGH_RATIO`).
6. `spec_graph._risks()`: include `mitigation`/`status` in emitted risk objects.
7. `render_html.py`: HTML-native risk grid pulling PRD + Epic risks.
8. Add `_check_risk_blindspot()` (script, deterministic): count child stories per epic via the graph; ≥`RISK_BLINDSPOT_MIN_STORIES` AND 0 risks → `risk_blindspot` warn. No LLM (F1).
9. **GREEN** + refactor; run pytest.

## Tests First (TDD)

| Test | Scenario | Expect |
|------|----------|--------|
| `test_prd_risk_in_graph` | PRD with valid `risks:` | risk appears in graph `risks[]` + `--viz risk` |
| `test_risk_impact_typo` | `impact: hihg` | `unknown_enum` error |
| `test_risk_status_enum` | `status: closed` (not in enum) | `unknown_enum` error |
| `test_risk_bad_shape` | `risks: ["just a string"]` | `invalid_type` error |
| `test_risk_high_ratio` | 5 risks, 3 high (60%) | `risk_high_ratio` warn |
| `test_risk_backcompat` | PRD with no `risks:` | no error, empty risk set |
| `test_risk_blindspot` | epic 6 stories, 0 risk | `risk_blindspot` warn [script, deterministic] |

## Success Criteria

- [x] G-C1: PRD risks render in `--viz risk` alongside epic risks.
- [x] G-C2: enum typos in impact/likelihood/status → `unknown_enum` error.
- [x] G-C3: `mitigation` + `status` parse + **surface in the HTML grid** (`render_html.risk()` `<table>` drill-down — the rendered consumer, not just graph passthrough).
- [x] G-C4: `risk_high_ratio` + `risk_blindspot` (both script, deterministic) fire on the fixtures.
- [x] G-A2 back-compat: a v1 PRD without `risks:` still validates clean (and the empty-risk HTML grid renders a "No risks recorded" note, no crash).
- [x] All new + existing pytest green (230 passed; +4 new HTML-grid tests).

> **Cross-phase note (G-G3):** the HTML-native risk-grid builder now exists in `render_html.risk()`, so Phase 6's dashboard can COMPOSE it (phase-06 "reuse the P2 builder") — the build(P2)/verify(P6) split is intact, no silent deferral.

## Risk Assessment

- **Existing risk-view tests assume epic-only risks** → update fixtures to include a PRD risk; keep determinism (sorted). LOW.
- **Threshold bikeshedding** → `RISK_HIGH_RATIO` is a commented module const, trivially tunable. LOW.

## Goal Gates Covered

G-C1, G-C2, G-C3, G-C4 (+ contributes G-A2, G-B1/G-B2 split).
