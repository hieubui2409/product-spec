# Backlog — `product-spec` + `product-spec-critique` + `claude-pack` ecosystem

Source: dual-skill evaluation (2026-05-31). **Groomed 2026-06-03** — reconciled against repo
state; `product-spec-critique` skill folded into scope; pipeline-closing brainstorm items added (§E).
Priority by value/cost. Status: `todo` unless noted.

---

## A. Bridge product-spec ↔ claude-pack (make the pair a real pipeline)

- [ ] **A1 — `product-spec --pack` / export-to-distributable.** Package a spec slice (`docs/product/`) into a versioned, content-hashed tarball + SHA, reusing claude-pack's determinism engine. Current `--export` only emits one HTML/md file; a CI-archivable / hand-off bundle is the missing piece. *First real data-flow link between the two skills.* — **high value**
- [ ] **A2 — Pack a "product-spec starter".** Use claude-pack to bundle product-spec + an empty `docs/product/` seed so a PO in another repo extracts and runs immediately. Realizes claude-pack's stated "seed new repo" use-case (no concrete asset today). — **high value**

## B. Harden claude-pack (now shipped at 1.1.0 — remaining gaps)

- [ ] **B3 — Implement `--all`** (still dies with exit 1 at `pack/cli.py`) or remove from flag table. DX debt. — **med**
- [ ] **B4 — Pytest the installer logic.** `semver_compare` (bash) + `Compare-Semver` (ps1) still **eyeball-only** (no test exercises them as of 2026-06-03); highest uncovered risk. Add a version-compare edge-case matrix in CI (bash + pwsh). Runs on recipient machine → bug = split-brain skill. — **high**
- [~] **B5 — Build-and-inspect end-to-end eval.** *Partial:* golden (`test_golden_product_spec` / `test_golden_synthetic`), determinism, and bundle-ships tests now build + extract + assert arcnames. **Remaining gap:** no test actually *runs* the extracted `install.sh` and verifies a clean install on a throwaway tree. — **med**
- [ ] **B6 — Authenticity option (minisign/sigstore).** SHA256 sidecar resists corruption, not tampering (attacker swaps both tarball + sidecar). **Priority pending** the public-vs-internal distribution decision (see Open questions). — **med (low if internal-only)**
- [ ] **B7 — `claude-unpack` / verify-only mode.** Lightweight MANIFEST-SHA check before install; today recipient must trust the installer blindly (only documented as absent in SKILL/GUIDE). — **low/med**

## C. Deepen product-spec (go deeper, not wider)

- [x] **C8 — v2 multi-dim views: KEEP** *(decided 2026-06-03).* risk / competition / dashboard / explorer confirmed wanted by POs; the cut suggestion is dropped. Standing obligation (not a cut): hold escape/parity discipline across the 14 views × 3 formats — viz was the cycle-1 XSS sink, so this stays a **security-regression watch**. — **resolved**
- [ ] **C9 — Semantic spec changelog / audit trail.** Build on existing `.snapshots/` + delta view: what drifted, who approved, when. Turns `change-log.md` into a governance-usable audit trail. — **med**
- [ ] **C10 — Round-trip to issue tracker.** Export stories→GitHub Issues/Jira preserving traceability IDs (`PRD-AUTH-E1-S1`). Keeps the spec alive without violating "no code generation." *(This is the forward "handoff" edge from the §E pipeline framing — tracked here, not duplicated.)* — **med**

## D. Shared foundation for the ecosystem

- [ ] **D11 — Extract shared determinism + safety + HTML design-system into a common base** all skills import, instead of each holding its own. Same philosophy, separate code today → drift risk (e.g. XSS escaping patched in product-spec; do claude-pack / critique have analogous HTML sinks?). — **med**
- [~] **D12 — Dual-skill regression gate in CI.** *Partial:* `claude-pack-ci` (dry-run) + live `claude-pack-integration` (product-spec dogfood) now exist. **Remaining:** turn the manual 10-cycle red-team (report cycle-1) into a repeatable cross-skill gate covering the shared bug classes (symlink leak, case-insensitive bypass, untracked asset) across all three skills. — **med**

## E. Close the PO pipeline (brainstorm 2026-06-03 — close the edges, don't widen)

Framing: `product-spec` (processing) → `product-spec-critique` (post-processing) is an **open pipeline**
with dangling edges. These close them. Prefer **modes on existing skills** over new skills (YAGNI / anti-bloat);
a new skill is justified only for outward-facing integration.

- [ ] **E1 — Apply-critique loop (the return edge).** `product-spec --apply-critique <report>`: walk each critique finding → **Keep / Change+re-approve / Defer**, recording rulings in the Decision Register (`DEC-<n>`) and honoring GATE-NO-SILENT-REVERSAL. Critique stays report-only; the spec-owning skill consumes its output. *Single biggest structural gap.* **Mode on product-spec.** — **high**
- [ ] **E2 — Discovery seed (the pre-stage).** `product-spec --discover`: ingest raw inputs (interview transcripts, support-ticket dumps, competitor notes) → synthesize candidate personas + problems + JTBD to **seed** the Vision/BRD interview instead of a cold start. Complements (not duplicates) the interview, which assumes you already know your personas. **Mode on product-spec.** — **med-high**
- [ ] **E3 — Outcome tracking (the learning edge).** Record actuals vs each BRD goal's `metrics`; flag specs that shipped-but-missed. Closes spec→build→measure→learn; feeds C9. *Premature if specs aren't reaching real users with measurable metrics yet.* — **med**
- [ ] **E4 — Stakeholder brief.** Generate an exec one-pager / release-notes / pitch outline *from* the spec (bilingual). Different audience, same source-of-truth; distinct from `--export`/`--viz`. — **low**
- [ ] **E5 — Per-skill release identity.** Today `product-spec` + `product-spec-critique` ship as **passive payload** inside the single `claude-pack-vX.Y.Z` bundle — no own SemVer, CHANGELOG, or release cadence (their `SKILL.md` `version` is decorative; CI never reads it). Decide: independent per-skill versioning/changelog, or consciously accept "one bundle, one version." — **med**

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

- Is claude-pack distribution **internal-only or public**? Decides B6 (authenticity) priority.
- E3 outcome-tracking assumes specs reach real users with measurable metrics — is that true yet?
- E5: adopt independent per-skill versioning/changelog, or accept the single-bundle version?
