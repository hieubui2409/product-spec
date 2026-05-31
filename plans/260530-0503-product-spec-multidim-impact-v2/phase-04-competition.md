---
phase: 4
title: "Competition"
status: pending
priority: P2
effort: "1.5d"
dependencies: [3]
---

# Phase 4: Competition

## Overview

Add the COMPETITION dimension: competitors defined once at the BRD (DRY home), referenced by ID from each PRD via a `competitive_parity` map; an HTML-native parity matrix + threat heatmap; a `competitive_drift` LLM warn; OpSec handling of competitor URLs.

## Key Insights (grounded + researcher)

- **Schema reconciliation (important):** the design report §5.1 stores parity as an **ID-keyed MAP** (`competitive_parity: {COMP-ACME: behind}`) — competitor identity lives ONCE in the BRD (DRY, matches the skill's ID philosophy). The R2 researcher report sketched an inline list-of-dict with competitor names duplicated per PRD — **we follow the report (ID-keyed map)**, NOT the inline list. The script RESOLVES the map + BRD competitor names into the LLM input block, so R2's prompt logic still applies on resolved names.
- **competitive_drift (R2):** script pre-computes `competitors_with_data` (count of parity != `none`); LLM flags only if `scope==core-value AND competitors_with_data>=2 AND every relevant parity==behind`; `cited_data` required; uncertain/ missing → `{finding:null}`.
- `brd.md` currently holds competition only as prose `## Market Context` (grounded #6) — we add structured `competitors:` alongside, keep prose.

## Requirements

- **Functional:** BRD `competitors` (id+name+url+threat); PRD `competitive_parity` ID-keyed map (enum ahead/parity/behind/none); enum + ref + shape validation; parity matrix + threat heatmap HTML-native; `competitive_drift` LLM warn; `--summary` gains a competition line.
- **Non-functional:** OpSec — parser ignores any `url` starting `private:`; back-compat; deterministic structural layer; LLM judgment-only for drift.

## Architecture

```yaml
# brd.md — add (DRY home for competitor identity):
competitors:
  - id: COMP-ACME            # ID grammar: COMP-<SLUG>
    name: "Acme Commerce"
    url: "https://acme.example"   # stored only, never fetched; `private:` prefix → IGNORED (OpSec)
    threat: high              # enum low|med|high

# prds/<slug>.md — add (reference by ID, ID-keyed map):
competitive_parity:
  COMP-ACME: behind           # enum ahead|parity|behind|none
  COMP-SHOPIFY: parity
```

- **Validation:** `threat` + parity enum; each `competitive_parity` KEY must resolve to a `graph['competitors'][].id` → else `unknown_ref` error; malformed shape → existing `invalid_type`.
- **LLM input (drift):** script builds `{artifact_id, scope, competitive_parity:[{competitor:<resolved name>, parity}], competitors_with_data, incomplete}` from the ID-keyed map + BRD names → feed R2 scaffold.
- **Views (Q30/Q44, HTML-native):** parity matrix = competitors (rows) × PRDs (cols), cells = parity enum (color-coded via design-system palette); threat heatmap = competitor × threat.

## Related Code Files

- Modify: `assets/templates/brd.md` (+`competitors`), `assets/templates/prd.md` (+`competitive_parity`).
- Modify: `scripts/spec_graph.py` (parse `competitors` from BRD + `competitive_parity` from PRD; **expose a top-level `graph['competitors']` key** — the single DRY home consumed by the consistency check, the renderers, AND the drift LLM-input builder, so nothing re-parses `brd.md` inline — F6; snapshot += parity).
- Modify: `scripts/frontmatter_parser.py` if needed for the OpSec `private:` URL skip (or handle in spec_graph parse).
- Modify: `scripts/check_consistency.py` (enum `threat`/`parity`; `competitive_parity` key resolves against `graph['competitors']` → else `unknown_ref`; malformed entries → existing `invalid_type` (NOT a new `invalid_shape` — F7); COMP-ID grammar).
- Modify: `scripts/render_html.py` (parity matrix + threat heatmap HTML-native), `scripts/visualize.py` (route `competition` view), `scripts/i18n_labels.py` (VI labels for parity/threat enums).
- Modify: `references/validation-rules-spec.md` (rows: enum parity/threat, `unknown_ref`, `competitive_drift`), `references/frontmatter-and-id-spec.md` (COMP-ID grammar + fields), `references/document-model-and-hierarchy.md` (competitor identity = BRD home).
- Modify: `--summary` generator (competition line — Q35).
- Create: `scripts/tests/test_competition.py`; extend `test_check_consistency.py`.

## Tests First (TDD)

| Test | Scenario | Expect |
|------|----------|--------|
| `test_competitors_parse` | BRD with 2 competitors | parsed into graph |
| `test_threat_enum` | `threat: extreme` | `unknown_enum` error |
| `test_parity_enum` | `COMP-X: invalid` | `unknown_enum` error |
| `test_parity_unknown_ref` | parity key `COMP-GHOST` not in BRD | `unknown_ref` error |
| `test_private_url_skipped` | `url: "private:internal/doc"` | URL ignored, no leak in graph/render |
| `test_parity_matrix_render` | 2 comp × 2 PRD | HTML-native matrix, correct cells |
| `test_competition_backcompat` | spec with no competitors | no error, empty |
| eval `competitive-drift` TP | scope=core-value, all behind, ≥2 data | flag + `cited_data.all_behind_competitors` |
| eval `competitive-drift` borderline | one `parity` among behind | no-finding |
| eval `competitive-drift` missing-anchor | scope=in OR <2 data | no-finding |

## Implementation Steps

1. **RED:** `test_competition.py` enum/ref/shape/private-url/matrix cases.
2. Add `competitors` to BRD template + parse (with `private:` URL skip).
3. Add `competitive_parity` map to PRD template + parse.
4. Consistency: enum + `unknown_ref` (parity key vs `graph['competitors']`) + COMP-ID grammar + malformed→`invalid_type` → GREEN.
5. `render_html.py`: parity matrix + threat heatmap HTML-native; route `competition` view in `visualize.py`; VI labels.
6. `competitive_drift` LLM check: script resolves the ID-keyed map → R2 input block; document scaffold in validation-rules-spec; 3 evals.
7. `--summary` competition line.
8. Full pytest + evals green.

## Success Criteria

- [ ] G-E1 competitors@BRD + parity@PRD (ID-keyed) parse + enum-validate.
- [ ] G-E2 parity matrix + threat heatmap render HTML-native.
- [ ] G-E3 (T2) `competitive_drift` flags only with anchors + cites; borderline/missing → no-finding.
- [ ] G-E4 OpSec: `private:`-prefixed URL ignored by parser; not in any render.
- [ ] G-A2 back-compat; G-B1/B2 split; DRY (competitor identity only in BRD).

## Risk Assessment

- **Schema confusion (map vs list)** → explicitly follow the report's ID-keyed map; script bridges to R2's name-based prompt. Cross-phase review must confirm no list-of-dict leaked in. TB.
- **URL OpSec leak** → `private:` skip enforced at parse (single chokepoint) + dedicated test. LOW.
- **Matrix with many competitors × PRDs** → HTML-native table scales; no Mermaid limit. LOW.

## Goal Gates Covered

G-E1, G-E2, G-E3, G-E4 (+ G-A2, G-B1/B2, DRY).
