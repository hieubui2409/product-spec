# Backlog — `product-spec` + `claude-pack` ecosystem

Source: dual-skill evaluation (2026-05-31). Priority by value/cost. Status: `todo` unless noted.

---

## A. Bridge product-spec ↔ claude-pack (make the pair a real pipeline)

- [ ] **A1 — `product-spec --pack` / export-to-distributable.** Package a spec slice (`docs/product/`) into a versioned, content-hashed tarball + SHA, reusing claude-pack's determinism engine. Current `--export` only emits one HTML/md file; a CI-archivable / hand-off bundle is the missing piece. *First real data-flow link between the two skills.* — **high value**
- [ ] **A2 — Pack a "product-spec starter".** Use claude-pack to bundle product-spec + an empty `docs/product/` seed so a PO in another repo extracts and runs immediately. Realizes claude-pack's stated "seed new repo" use-case (no concrete asset today). — **high value**

## B. Finish claude-pack (v0.1 — clearest gaps)

- [ ] **B3 — Implement `--all`** (currently advertised but dies with exit 1) or remove from flag table. DX debt. — **med**
- [ ] **B4 — Pytest the installer logic.** `semver_compare` (bash) + `Compare-Semver` (ps1) are eyeball-tested only; report flags this as highest risk, uncovered. Add version-compare edge-case matrix run in CI (bash + pwsh). Runs on recipient machine → bug = split-brain skill. — **high**
- [ ] **B5 — Build-and-inspect end-to-end eval.** Actually build tarball → extract → run install.sh → verify. GIT-1 (`.gitignore` swallowed `claude-pack/assets/`) slipped because review was content-only; untracked-file bugs need artifact-level checks. — **high**
- [ ] **B6 — Authenticity option (minisign/sigstore).** SHA256 sidecar only resists corruption, not tampering (attacker swaps both tarball + sidecar). Needed for public distribution. — **med (low if internal-only)**
- [ ] **B7 — `claude-unpack` / verify-only mode.** Lightweight MANIFEST-SHA check before install; today recipient must trust the installer blindly. — **low/med**

## C. Deepen product-spec (go deeper, not wider)

- [ ] **C8 — Audit & possibly cut v2 surface.** `risk` / `competition` / `dashboard` / `explorer` tri-mode: verify real PO usage. If unused, it's YAGNI carrying test/security/ascii-mermaid-html parity cost. 14 views × 3 formats = combinatorial maintenance + proven XSS hotspot. Finishing can mean *cutting*. — **high (maintainability)**
- [ ] **C9 — Semantic spec changelog / audit trail.** Build on existing `.snapshots/` + delta view: what drifted, who approved, when. Turns `change-log.md` into governance-usable audit trail. — **med**
- [ ] **C10 — Round-trip to issue tracker.** Export stories→GitHub Issues/Jira preserving traceability IDs (`PRD-AUTH-E1-S1`). Keeps spec alive without violating "no code generation". — **med**

## D. Shared foundation for the pair (reinforce "ecosystem")

- [ ] **D11 — Extract shared determinism + safety + HTML design-system into a common base** both skills import, instead of each holding its own. Same philosophy, separate code today → drift risk (e.g. XSS escaping patched in product-spec; does claude-pack have analogous HTML sinks?). — **med**
- [ ] **D12 — Dual-skill regression gate in CI.** Turn the manual 10-cycle red-team (report cycle-1) into a repeatable workflow. Both skills share bug classes: symlink leak, case-insensitive bypass, untracked asset. — **med**

---

## Known cons / risk notes (context for above)

**product-spec**
- Surface area too large for v2; ascii "downgraded not removed" → hard to keep parity; viz was the XSS sink (cycle-1).
- LLM-dependent for the most valuable checks (core-value alignment, contradiction) → not reproducible, not CI-gateable.
- CLI surface (`--layers`/`--depth`/`--compact-mode`/`--group-by`/`--filter-wont`) is technical vs the "non-technical PO" positioning.
- Many files >200 LOC (render layer): `render_html.py` 41KB, `render_ascii.py` 30KB, `check_consistency.py` 33KB, `spec_graph.py` 28KB.

**claude-pack**
- v0.1: `--all` dead; no GPG; no zip/zstd; no merge-resolver; no `claude-unpack`.
- Installer logic (highest risk) not pytest-covered.
- SHA256 = corruption-resistant, not tamper-resistant.
- Symlink-leak class (patched once via MANIFEST) is subtle — watch for variants.

**Pairing reality**
- The two skills are orthogonal (spec content vs `.claude/` tooling); paired by *methodology + brand*, not by data flow. Only meta-link today: claude-pack can package product-spec. A1/A2 are the highest-leverage moves to make them a true pipeline.

---

## Open questions

- "claude-ship" in the original ask = `claude-pack` (assumed). Confirm if it actually meant the generic `ship` skill.
- Is claude-pack distribution internal-only or public? Decides B6 (authenticity) priority.
- Are product-spec v2 multi-dim views (risk/competition/dashboard/explorer) actually used by POs? Decides C8 (cut vs keep).
