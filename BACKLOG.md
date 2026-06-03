# Backlog — `product-spec` + `product-spec-critique` + `claude-pack` ecosystem

Source: dual-skill evaluation (2026-05-31). **Groomed 2026-06-03** — reconciled against repo
state; `product-spec-critique` skill folded into scope; pipeline-closing brainstorm items added (§E).
**Re-groomed 2026-06-03 (PM)** — folded 3 PO decisions + C/D/E research grounding
(`plans/reports/research-260603-1758-backlog-cde-grounding-report.md`) + C/D/E brainstorm
(`plans/reports/brainstorm-260603-1758-backlog-cde-approaches-report.md`).
Priority by value/cost. Status: `todo` unless noted.

**PO decisions (2026-06-03):** Q1 claude-pack = **internal-only** (B6 → low). · Q2 spec product
**not in market yet** (E3 → deferred). · Q3 E5 = **standardize the loose hybrid** (per-skill
version+changelog, no CI release split). · C10 → **parked** (await task-tracker choice). · D11 →
**close, micro-util only**. · E1 anchoring → pros/cons documented; **A (artifact-id + freshness)
default + C (manual) fallback** recommended, final pick open.

**Recommended C/D/E build order** (brainstorm): **E5 → D12 → E1 → C9 → E4 → E2 → D11**
(stabilize → close the loop → governance/polish → widen → cleanup). C10 parked · E3 deferred.
Status legend: `[ ]` todo · `[~]` in-progress/partial · `[x]` done · `[next]` next-up · `[park]` parked · `[defer]` deferred.

---

## A. Bridge product-spec ↔ claude-pack (make the pair a real pipeline)

- [ ] **A1 — `product-spec --pack` / export-to-distributable.** Package a spec slice (`docs/product/`) into a versioned, content-hashed tarball + SHA, reusing claude-pack's determinism engine. Current `--export` only emits one HTML/md file; a CI-archivable / hand-off bundle is the missing piece. *First real data-flow link between the two skills.* — **high value**
- [ ] **A2 — Pack a "product-spec starter".** Use claude-pack to bundle product-spec + an empty `docs/product/` seed so a PO in another repo extracts and runs immediately. Realizes claude-pack's stated "seed new repo" use-case (no concrete asset today). — **high value**

## B. Harden claude-pack (now shipped at 1.1.0 — remaining gaps)

- [ ] **B3 — Implement `--all`** (still dies with exit 1 at `pack/cli.py`) or remove from flag table. DX debt. — **med**
- [ ] **B4 — Pytest the installer logic.** `semver_compare` (bash) + `Compare-Semver` (ps1) still **eyeball-only** (no test exercises them as of 2026-06-03); highest uncovered risk. Add a version-compare edge-case matrix in CI (bash + pwsh). Runs on recipient machine → bug = split-brain skill. — **high**
- [~] **B5 — Build-and-inspect end-to-end eval.** *Partial:* golden (`test_golden_product_spec` / `test_golden_synthetic`), determinism, and bundle-ships tests now build + extract + assert arcnames. **Remaining gap:** no test actually *runs* the extracted `install.sh` and verifies a clean install on a throwaway tree. — **med**
- [defer] **B6 — Authenticity option (minisign/sigstore).** SHA256 sidecar resists corruption, not tampering (attacker swaps both tarball + sidecar). **DECIDED 2026-06-03: distribution is internal-only → deprioritized to low.** Revisit only if distribution goes public. — **low (was med)**
- [ ] **B7 — `claude-unpack` / verify-only mode.** Lightweight MANIFEST-SHA check before install; today recipient must trust the installer blindly (only documented as absent in SKILL/GUIDE). — **low/med**

## C. Deepen product-spec (go deeper, not wider)

- [x] **C8 — v2 multi-dim views: KEEP** *(decided 2026-06-03).* risk / competition / dashboard / explorer confirmed wanted by POs; the cut suggestion is dropped. Standing obligation (not a cut): hold escape/parity discipline across the 14 views × 3 formats — viz was the cycle-1 XSS sink, so this stays a **security-regression watch**. — **resolved**
- [ ] **C9 — Semantic spec changelog / audit trail.** Build on existing `.snapshots/` + delta view: what drifted, who approved, when. Turns `change-log.md` into a governance-usable audit trail. *Research 2026-06-03: infra mostly EXISTS — `spec_graph.py` `diff_graphs()`/`changed_nodes()`, `change-log-entry.md` template (has author/date/dims), `approval:` frontmatter, `status.py` `stale_approvals`, `decision_register.py`. Gap = one unified audit-trail VIEW. Mostly assembly, not new build. Brainstorm: read-only `--audit` view (or `--viz audit`) joining change-log + approval + stale_approvals + DEC refs; columns when·artifact·action·who-approved·what-drifted·DEC. Keep it a viewer (read-only). Feeds future E3.* — **med (build-order #4)**
- [park] **C10 — Round-trip to issue tracker.** Export stories→GitHub Issues/Jira preserving traceability IDs (`PRD-AUTH-E1-S1`). Keeps the spec alive without violating "no code generation." *(Forward "handoff" edge from §E.)* **PARKED 2026-06-03 (PO):** blocked on a prior decision — *which task tracker is the target*. When chosen, build as a **separate outward-facing skill + bridge infra** reading product-spec's exported artifact (one-way idempotent, back-ref issue number into story frontmatter). Keeps product-spec's no-runtime-network + non-tech-PO promises intact. Not actioned this round. — **parked (await tracker choice)**

## D. Shared foundation for the ecosystem

- [~] **D11 — Shared foundation: CLOSED to micro-util only.** 🟥 *Research 2026-06-03 REFUTED the premise: actual duplication ≈ 0* (determinism only in claude-pack; HTML/escaping only in product-spec; **critique & claude-pack generate NO HTML** → no analogous XSS sink). **DECIDED 2026-06-03 (PO): close the "common base" ambition; consolidate ONLY the genuine micro-dup** — `_now()` (×4) + `_hashable()` (×3) → one tiny shared util the 3 skills import (verify claude-pack bundles it). Determinism/safety/design-system extraction = dropped (YAGNI). — **low (build-order #7)**
- [next] **D12 — Cross-skill regression gate in CI.** *Partial:* `claude-pack-ci` (dry-run) + live `claude-pack-integration` (product-spec dogfood) + `claude-pack-release` exist. ⚠️ *Research 2026-06-03: product-spec (31 tests) & product-spec-critique (10 tests) have NO dedicated CI workflow — run by hand.* The "10-cycle red-team" = C9→C10→C11 chain (`plans/reports/cycle-11-…md`; bugs 101→67→37; symlink/case-insensitive/XSS held every cycle). **Remaining:** add CI workflows running the 50 existing tests for all 3 skills + a shared bug-class matrix (symlink leak, case-insensitive bypass, untracked asset). *Brainstorm: 2 thin workflows (1 OS × 2 Python is enough — argue down claude-pack's 3×3) + a centralized bug-class test module. Build BEFORE E1/E2 so new features land on a gated suite.* — **med (build-order #2 — highest-leverage in D)**

## E. Close the PO pipeline (brainstorm 2026-06-03 — close the edges, don't widen)

Framing: `product-spec` (processing) → `product-spec-critique` (post-processing) is an **open pipeline**
with dangling edges. These close them. Prefer **modes on existing skills** over new skills (YAGNI / anti-bloat);
a new skill is justified only for outward-facing integration.

- [ ] **E1 — Apply-critique loop (the return edge).** `product-spec --apply-critique <report>`: walk each critique finding → **Keep / Change+re-approve / Defer**, recording rulings in the Decision Register (`DEC-<n>`) and honoring GATE-NO-SILENT-REVERSAL. Critique stays report-only; the spec-owning skill consumes its output. *Single biggest structural gap.* **Mode on product-spec.** *Research 2026-06-03: flag does NOT exist yet (new feature). Infra MATURE — DEC register + `decision_register.py`, GATE in `guardrails-and-boundaries.md:102`, `--update` impact-pass. ⚠️ critique findings have NO stable ID (transient) → must anchor by `evidence ID:line`; design for `:line` drift when spec changes after critique. **Brainstorm anchoring options (pros/cons in report): A** anchor by artifact-id + `body_hash` freshness warning, **B** require freshest critique (hash-gate), **C** manual per-finding PO confirm. **Recommended: A default + C fallback** (B's correctness real but friction kills adoption). Final pick OPEN.* — **high (build-order #3 — biggest structural gap)**
- [ ] **E2 — Discovery seed (the pre-stage).** `product-spec --discover`: ingest raw inputs (interview transcripts, support-ticket dumps, competitor notes) → synthesize candidate personas + problems + JTBD to **seed** the Vision/BRD interview instead of a cold start. Complements (not duplicates) the interview, which assumes you already know your personas. **Mode on product-spec.** *Research 2026-06-03: flag does NOT exist (closest = `--auto` brain-dump). Vision interview V1–V7 asks personas as an OPEN question (assumes you know them) → seeding is genuinely additive. Brainstorm: scope TIGHT — text in → candidate persona/problem/JTBD bullets out → interview confirms (never auto-commit personas, GATE-NEVER-ASSUME). Easiest item to over-build; if the `--auto` distinction blurs, merge into `--auto` rather than ship 2 flags. Do AFTER E1 proves the loop.* — **med-high (build-order #6)**
- [defer] **E3 — Outcome tracking (the learning edge).** Record actuals vs each BRD goal's `metrics`; flag specs that shipped-but-missed. Closes spec→build→measure→learn; feeds C9. **DECIDED DEFERRED 2026-06-03: product built from spec is NOT in market yet → premature.** Revisit when a spec ships to real users with measurable metrics. Keep minimal framing only. — **deferred**
- [ ] **E4 — Stakeholder brief.** Generate an exec one-pager / release-notes / pitch outline *from* the spec (bilingual). Different audience, same source-of-truth; distinct from `--export`/`--viz`. *Research 2026-06-03: `--summary` (fixed exec template) + `--export` (flexible tree-slice) assemblers already exist → E4 = thin mode reusing them, cheap. Both inherit session `lang`; no per-flag lang override today. Brainstorm: thin `--brief` mode w/ audience preset (exec one-pager / release-notes) reusing the assemblers; release-notes flavor pulls from C9's trail → sequence after C9 if that flavor wanted (exec one-pager can ship before).* — **low (build-order #5 — cheap)**
- [ ] **E5 — Per-skill release identity.** Today `product-spec` + `product-spec-critique` ship as **passive payload** inside the single `claude-pack-vX.Y.Z` bundle; their `SKILL.md` `version` is decorative (`2.0.0`/`1.0.0`); CI reads tag only, never SKILL.md. **DECIDED 2026-06-03: standardize the loose hybrid** — give each skill its own CHANGELOG + keep version in SKILL.md, but DO NOT split the CI release (one bundle tag stays the release unit). *Research: only claude-pack has CHANGELOG (keepachangelog); pattern ≈ Changesets (per-package changelog, single release). Cheap: +2 CHANGELOGs, make CI verify SKILL.md version matches bundle. Brainstorm: Changesets-lite, NO new tooling — add CHANGELOG.md to product-spec + critique (keepachangelog), keep version in each SKILL.md as truth, make `claude-pack-release.yml` read+verify versions (fail on drift), bundle tag stays single release unit.* — **med (build-order #1 — do first, scope locked)**

---

## Known cons / risk notes (context for above)

**product-spec**
- Surface area large; viz was the XSS sink (cycle-1) → keep escape discipline (C8 kept the views, so this obligation stays).
- LLM-dependent for the most valuable checks (core-value alignment, contradiction) → not reproducible, not CI-gateable.
- CLI surface (`--layers`/`--depth`/`--compact-mode`/`--group-by`/`--filter-wont`) is technical vs the "non-technical PO" positioning.
- Several render files >200 LOC (`render_html.py`, `render_ascii.py`, `check_consistency.py`, `spec_graph.py`).

**product-spec-critique**
- Non-deterministic by design (opinion + web + voice) → deliberately OUT of the reproducible `--validate` CI gate; cannot be regression-gated the same way as product-spec.
- Voice levels 6-9 are danger gates; universal-harm floor enforced — the lens→consolidator→humanizer safety chain must stay intact on any refactor.

**claude-pack**
- `--all` dead; no GPG/authenticity; no zip/zstd; no merge-resolver; no `claude-unpack`.
- Installer logic (highest risk) still not pytest-covered (B4).
- SHA256 = corruption-resistant, not tamper-resistant.
- Symlink-leak class (patched once via MANIFEST) is subtle — watch for variants.

**Pairing reality**
- product-spec ↔ product-spec-critique are now a genuine processing / post-processing pair; the open edges (E1/E2) are the highest-leverage links to make it a closed loop. claude-pack remains orthogonal tooling — it *packages* the pair (A1/A2 deepen that), it is not part of the spec data flow.

---

## Open questions

**Resolved 2026-06-03:**
- ~~claude-pack internal-only or public?~~ → **internal-only** (B6 → low).
- ~~E3 specs reaching real users yet?~~ → **no, not in market** (E3 → deferred).
- ~~E5 per-skill versioning vs single-bundle?~~ → **standardize loose hybrid** (per-skill changelog, single CI release).

**Resolved 2026-06-03 (PM, from brainstorm):**
- ~~C10 positioning?~~ → **parked** until the target task tracker is chosen; then a separate outward-facing skill reads product-spec's exported artifact.
- ~~D11 closure?~~ → **close to micro-util only**; drop the design-system ambition.

**Still open:**
- **E1 anchoring final pick:** accept **A (artifact-id + freshness warning) default + C (manual) fallback**, or require the stricter **B (hash-gate, force re-critique on drift)**? *(Needed before planning E1.)*
- **C10 target:** which task tracker (GitHub Issues / Jira / other)? Decides when C10 un-parks.
- **E2 vs `--auto`:** ship E2 as a separate flag, or prototype inside `--auto` first and split only if the input/output distinction proves real?
- **D12 CI matrix:** OK to drop the 2 new workflows to 1 OS × 2 Python (vs claude-pack's 3×3)?
