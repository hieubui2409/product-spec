# Red-Team Review — Phase 8 (C11 red-team adaptation)

> 2026-06-03 · 2 reviewers (Scope & Complexity Critic, Assumption Destroyer). All findings `file:line`-evidenced.
> Verdict: **Half A (Assumption-Destroyer lens) = gold-plating** (duplicates existing lenses) AND under-scoped if kept.
> **Half B (`goal_without_metric`) = justified**, but severity + code-anchor are wrong as written.

## Severity: 3 Critical · 3 High · 1 Medium (+ Half B confirmed justified)

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| A1 | Critical | Assumption lens **duplicates** product "Riskiest-assumption" (`lens-frameworks.md:16`) + tech "Hidden-deps/assume-success" (`:29,33`). The DRY test that cut Scope/Security/Failure was never applied to the kept lens. | **Cut Half A** (PO call) |
| A2 | Critical | Lens agents live at top-level `.claude/agents/` + `pack.manifest.yaml:11-16` + packaging test `AGENT_FILES`, NOT skill subtree. Plan creates it in the wrong place → 5th lens **not bundled**, CI stays green falsely. | If kept: fix location+manifest+test |
| A3 | Critical | Consolidator hardcodes 4 lenses — header template `lenses: product,tech,market,craft` + 4 fixed sections (`critique-consolidator.md:85,100-104`); tolerates **N<4 not N<5**. "Accept 5 lenses" = multi-point prompt rewrite, not a one-liner. | If kept: rewrite consolidator |
| B1 | Critical | `goal_without_metric: error` turns shipped **`broken-spec` fixture** (both goals `metrics:[]`, `brd.md:11-18`) + **eval** ("flags exactly those issues", `evals.json:30-31`) RED → Phase 2 green-suite gate fails. | **Default `warn`** OR add fixture+eval update steps |
| A4 | High | Wrong code anchor: goal `metrics` populated in `spec_graph._node_from_goal:176` on `type:goal` nodes, NOT `check_consistency.py:88` (that's artifact-level `LIST_FIELDS` type check). | **Re-anchor** to goal-node iteration |
| A5 | High | E1 coupling overstated: lens-cache is a lens-agnostic content-hash array (`critique_blob_cache.py:65-71`); adding a lens is DATA not schema. `dependencies:[3]` not justified by cache. | Downgrade to soft note |
| A6 | High | Missing edit surfaces for a 5th lens: `lens-frameworks.md` bank (`:1` "the 4 banks"), `--assumption` flag + interactive picker (`SKILL.md:53`), README/GUIDE "4 lenses" copy, humanizer. Blast radius undercounted. | If kept: expand inventory |
| A7 | Med | Citation `:87`→ actual `:84`; ck-plan "evidence-discipline mirror" is a no-op (critique already enforces `ID:line` + fix, `critique-consolidator.md:122-123`). | Fix citation; drop mirror |

## Confirmed JUSTIFIED (survives YAGNI)
- `goal_without_metric` is a real gap: spec says goal `metrics` "required ≥1" but no script enforces it (only `render_html.py:876` references metric-less goals descriptively). Keep the check — fix severity (B1) + anchor (A4) + citation (A7).
- Scope-cut of Security/Failure/Scope lenses is sound (product/market cover gold-plating/me-too; spec emits no code).

## The core decision (PO — this is a PO-added phase)
**Half A intent was "adapt the red-team discipline".** Two ways to honor it:
- **(a) Zero-cost (recommended):** CUT the new lens; instead STRENGTHEN the existing product "Riskiest-assumption" + tech "Hidden-deps" rows in `lens-frameworks.md` (e.g. require an explicit "if this assumption is wrong → X" clause). A prompt edit, no new agent, no +25% cost, no bundling/consolidator rewrite, no duplication.
- **(b) Keep new lens:** accept the real blast radius (A2,A3,A6) + +25% per-run cost + the duplication (A1).

## Unresolved (for PO)
1. Half A: cut + strengthen existing lenses (a), or build the new lens at full blast radius (b)?
2. `goal_without_metric`: default `warn` (safe, fixture/eval untouched) or `error` (+ mandatory fixture+eval update)?
3. Phase 8 structure: dissolve (move `goal_without_metric` into the validate work, drop/relocate the lens question to its own backlog line) or keep as a phase?
