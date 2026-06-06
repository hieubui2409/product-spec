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

## NEW (2026-06-06, ungroomed)

- [ ] **N1 — Repeat-offense finding-level fingerprint (`product-spec-critique`).** Priority: low/med (enhancement, not a bug). Repeat-offense + inherit hiện match theo **NODE** (`critique_inherit._node_of` cắt `:line`) → bền với dịch dòng nhưng **thô**: (a) không phân biệt 2 finding khác nhau trên cùng node (vd PRD-FUND 4 blocker → gộp thành "node có repeat"); (b) key index `<evidence_id>@<ts>` (`PRD-FUND:101@ts`) dính số dòng nên cùng 1 finding logic sau dịch dòng (`:103`) tạo key mới, store không dedup ở mức finding-logic. **Fix:** thêm `finding_fingerprint` = hash chuẩn hóa của (node + nội dung critique/why, **bỏ số dòng**) vào row index → repeat-offense chính xác tới từng finding + miễn nhiễm dịch dòng; `:line` chỉ còn để trích dẫn. Phạm vi: `critique_cache.upsert_findings` + đường đọc `build_inherited_context`/repeat + test. *Bối cảnh:* phát hiện khi điều tra bug index rỗng (đã fix riêng: `critique_inherit.py:188` đọc nhầm `evidence_id` thay vì `evidence`).

---

## A. Bridge product-spec ↔ claude-pack — CLOSED (premise was flawed)

> **2026-06-04 (PO critique):** Group A conflated two different jobs — *distributing a tool* (claude-pack's
> real job) vs *versioning living content* (git's job). The spec is co-located with the code in the same
> repo, so **git is the single source of truth + versioning + diff**, and the skill already provides the
> sync surface (`change-log.md`, `decisions.md`, `--viz audit`, `--summary --audience release-notes`,
> `--approve` snapshots, `--viz delta`). Packing the spec fights the living spec→code→spec-update pipeline.
> Both items dropped.

- [x] ~~**A1 — `product-spec --pack` / export-to-distributable.**~~ **DROPPED 2026-06-04 (PO critique):** a tarball is strictly worse than the repo for a *living* spec — you can't diff opaque tarballs, and the spec→code→update→code-update loop would force a churny tarball-per-edit. Every need it claimed is already met: "what changed" → `--summary --audience release-notes` + `--viz audit` + `git diff docs/product/`; "lock scope for release X" → `--approve` (owner+date+version) + `.snapshots/` + `--viz delta`; "mid-phase change to approved spec" → GATE-NO-SILENT-REVERSAL + Decision Register + `--update` (no new pack); "single source of truth, dev-read/PO-write" → `docs/product/` in-repo + branch protection/CODEOWNERS. Residual external-hand-off sliver is served by the existing `--export` (readable doc); authenticity there = B6 (signing), not a spec pack. — **cut (YAGNI)**
- [x] ~~**A2 — Pack a "product-spec starter".**~~ **DROPPED 2026-06-04 (PO critique — redundant three ways):** (1) the "empty `docs/product/` seed" is dead weight — product-spec **self-scaffolds** `docs/product/` on no-flag init / `--product`; (2) product-spec already ships in the bundle and claude-pack already builds a single-skill bundle via **`--skills product-spec`** — no new asset needed; (3) onboarding is already prompt-driven (README.md + CLAUDE.md → install bundle → `/cleanmatic:product-spec` → the AI interviews + generates). Nothing left for a static "starter" to add. — **cut (YAGNI)**

## B. Harden claude-pack (now shipped at 1.1.0 — remaining gaps)

- [x] **B3 — Removed `--all`** *(2026-06-04)*. The flag never worked (errored exit 1) and is against the curated-distribution design (the manifest + `--skills` is the interface); dropped the arg/handler + docs rather than implement a "pack everything" anti-feature. — **done (removed, KISS)**
- [x] **B4 — Pytest the installer semver logic** *(2026-06-04)*. `test_installer_semver.py` extracts the real `semver_compare` (bash) from the template and runs a 19-case edge matrix (leading-zero octal trap, pre-release < release, numeric vs alphanumeric identifiers, build-metadata-ignored, ASCII collation `RC`<`rc`) + an antisymmetry check; `Compare-Semver` (ps1) parity runs on the Windows CI leg (skipped where `pwsh` absent). Both marked `bug_class`. — **done**
- [x] **B5 — Run-the-extracted-`install.sh` e2e** *(2026-06-04)*. `test_installer_e2e.py` builds a real bundle via `python -m pack`, extracts it, runs the bundled `install.sh` into a throwaway `TARGET_DIR`, asserts the files actually land, then asserts a second run is idempotent (skips existing). Closes the "we build bundles but never prove they install" gap. — **done**
- [defer] **B6 — Authenticity option (minisign/sigstore).** SHA256 sidecar resists corruption, not tampering (attacker swaps both tarball + sidecar). **DECIDED 2026-06-03: distribution is internal-only → deprioritized to low.** Revisit only if distribution goes public. — **low (was med)**
- [ ] **B7 — `install.sh --verify-only` (NOT a standalone `claude-unpack`).** *Re-scoped 2026-06-04 (PO critique): a standalone pre-installed `claude-unpack` companion is a **bootstrap circle*** — verifying the distribution of claude-pack would require first distributing+trusting claude-unpack (turtles). Resolution: the verifier must ride **inside** the bundle like `install.sh` already does. Three tiers: **(1) integrity/transit** is already solved by the coreutils `.sha256` sidecar (`sha256sum -c`, no claude-pack-specific tool); **(2) content-vs-MANIFEST per-file** = the only real residue → add a `--verify-only` flag to the bundled `install.sh` that walks `MANIFEST.json` and checks each file's SHA (today `install.sh.template:28` only checks MANIFEST *exists*). Low value (largely redundant with the whole-tarball sidecar). **(3) authenticity/tampering CANNOT be self-verified** — an attacker swaps tarball+sidecar+MANIFEST+verifier together; it needs an **out-of-band trust anchor (a signature/key the recipient already trusts)** = **B6**, using a general-purpose verifier (minisign/cosign), not a claude-pack tool. → **Do (2) only if cheap; the valuable "can I trust the source" intent is B6, not B7.** — **low (de-scoped)**

## C. Deepen product-spec (go deeper, not wider)

- [x] **C8 — v2 multi-dim views: KEEP** *(decided 2026-06-03).* risk / competition / dashboard / explorer confirmed wanted by POs; the cut suggestion is dropped. Standing obligation (not a cut): hold escape/parity discipline across the 14 views × 3 formats — viz was the cycle-1 XSS sink, so this stays a **security-regression watch**. — **resolved**
- [x] **C9 — Semantic spec changelog / audit trail.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 4): `--viz audit` (`assemble_audit_trail.py`, ASCII+md, `unreconciled` rows, reuses status.py loaders). Build on existing `.snapshots/` + delta view: what drifted, who approved, when. Turns `change-log.md` into a governance-usable audit trail. *Research 2026-06-03: infra mostly EXISTS — `spec_graph.py` `diff_graphs()`/`changed_nodes()`, `change-log-entry.md` template (has author/date/dims), `approval:` frontmatter, `status.py` `stale_approvals`, `decision_register.py`. Gap = one unified audit-trail VIEW. Mostly assembly, not new build. Brainstorm: read-only `--audit` view (or `--viz audit`) joining change-log + approval + stale_approvals + DEC refs; columns when·artifact·action·who-approved·what-drifted·DEC. Keep it a viewer (read-only). Feeds future E3.* — **med (build-order #4)**
- [park] **C10 — Round-trip to issue tracker.** Export stories→GitHub Issues/Jira preserving traceability IDs (`PRD-AUTH-E1-S1`). Keeps the spec alive without violating "no code generation." *(Forward "handoff" edge from §E.)* **PARKED 2026-06-03 (PO):** blocked on a prior decision — *which task tracker is the target*. When chosen, build as a **separate outward-facing skill + bridge infra** reading product-spec's exported artifact (one-way idempotent, back-ref issue number into story frontmatter). Keeps product-spec's no-runtime-network + non-tech-PO promises intact. Not actioned this round. — **parked (await tracker choice)**

## D. Shared foundation for the ecosystem

- [x] **D11 — Shared foundation: CLOSED to micro-util only.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 7): `_hashable()` consolidated into `render_common.py` (product-spec-internal, output byte-unchanged). Per red-team: `_now()` left divergent (intentional), no cross-skill module (unbundlable). 🟥 *Research 2026-06-03 REFUTED the premise: actual duplication ≈ 0* (determinism only in claude-pack; HTML/escaping only in product-spec; **critique & claude-pack generate NO HTML** → no analogous XSS sink). **DECIDED 2026-06-03 (PO): close the "common base" ambition; consolidate ONLY the genuine micro-dup** — `_now()` (×4) + `_hashable()` (×3) → one tiny shared util the 3 skills import (verify claude-pack bundles it). Determinism/safety/design-system extraction = dropped (YAGNI). — **low (build-order #7)**
- [x] **D12 — Cross-skill regression gate in CI.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 2): `product-spec-ci.yml` + `product-spec-critique-ci.yml` (1 OS × 2 Python, path-filtered, per-skill-dir scoped; critique offline-enforced via `CK_OFFLINE` socket guard) + `cross-skill-bug-class.yml`; `bug_class` marker registered in all 3 pytest configs. *Partial:* `claude-pack-ci` (dry-run) + live `claude-pack-integration` (product-spec dogfood) + `claude-pack-release` exist. ⚠️ *Research 2026-06-03: product-spec (31 tests) & product-spec-critique (10 tests) have NO dedicated CI workflow — run by hand.* The "10-cycle red-team" = C9→C10→C11 chain (`plans/reports/cycle-11-…md`; bugs 101→67→37; symlink/case-insensitive/XSS held every cycle). **Remaining:** add CI workflows running the 50 existing tests for all 3 skills + a shared bug-class matrix (symlink leak, case-insensitive bypass, untracked asset). *Brainstorm: 2 thin workflows (1 OS × 2 Python is enough — argue down claude-pack's 3×3) + a centralized bug-class test module. Build BEFORE E1/E2 so new features land on a gated suite.* — **med (build-order #2 — highest-leverage in D)**

## E. Close the PO pipeline (brainstorm 2026-06-03 — close the edges, don't widen)

Framing: `product-spec` (processing) → `product-spec-critique` (post-processing) is an **open pipeline**
with dangling edges. These close them. Prefer **modes on existing skills** over new skills (YAGNI / anti-bloat);
a new skill is justified only for outward-facing integration.

- [x] **E1 — Apply-critique loop (the return edge).** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 3): `--apply-critique <report>` — lens-cache-JSON parse + per-finding fingerprint + freshness (None-safe), read-fenced to `docs/product/critique/`, atomic+resumable+injection-safe DEC writes (`decision_register --append-alloc`), deterministic GATE re-approval guard. Scripts `parse_critique_report.py`/`apply_critique_progress.py`, ref `workflow-apply-critique.md`. `product-spec --apply-critique <report>`: walk each critique finding → **Keep / Change+re-approve / Defer**, recording rulings in the Decision Register (`DEC-<n>`) and honoring GATE-NO-SILENT-REVERSAL. Critique stays report-only; the spec-owning skill consumes its output. *Single biggest structural gap.* **Mode on product-spec.** *Research 2026-06-03: flag does NOT exist yet (new feature). Infra MATURE — DEC register + `decision_register.py`, GATE in `guardrails-and-boundaries.md:102`, `--update` impact-pass. ⚠️ critique findings have NO stable ID (transient) → must anchor by `evidence ID:line`; design for `:line` drift when spec changes after critique. **Brainstorm anchoring options (pros/cons in report): A** anchor by artifact-id + `body_hash` freshness warning, **B** require freshest critique (hash-gate), **C** manual per-finding PO confirm. **Recommended: A default + C fallback** (B's correctness real but friction kills adoption). Final pick OPEN.* — **high (build-order #3 — biggest structural gap)**
- [x] **E2 — Discovery seed (the pre-stage).** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 6): `--discover <path(s)>` — read-fenced ingest (`ingest_raw_inputs.py`): project-root fence, `.md`/`.txt` allow-list, dotfile exclusion, size cap, bounded directory recursion (depth+count); empty candidate buckets (no auto-commit, GATE-NEVER-ASSUME); ref `workflow-discover.md`. `product-spec --discover`: ingest raw inputs (interview transcripts, support-ticket dumps, competitor notes) → synthesize candidate personas + problems + JTBD to **seed** the Vision/BRD interview instead of a cold start. Complements (not duplicates) the interview, which assumes you already know your personas. **Mode on product-spec.** *Research 2026-06-03: flag does NOT exist (closest = `--auto` brain-dump). Vision interview V1–V7 asks personas as an OPEN question (assumes you know them) → seeding is genuinely additive. Brainstorm: scope TIGHT — text in → candidate persona/problem/JTBD bullets out → interview confirms (never auto-commit personas, GATE-NEVER-ASSUME). Easiest item to over-build; if the `--auto` distinction blurs, merge into `--auto` rather than ship 2 flags. Do AFTER E1 proves the loop.* — **med-high (build-order #6)**
- [defer] **E3 — Outcome tracking (the learning edge).** Record actuals vs each BRD goal's `metrics`; flag specs that shipped-but-missed. Closes spec→build→measure→learn; feeds C9. **DECIDED DEFERRED 2026-06-03: product built from spec is NOT in market yet → premature.** Revisit when a spec ships to real users with measurable metrics. Keep minimal framing only. — **deferred**
- [x] **E4 — Stakeholder brief.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 5): `--summary --audience exec|release-notes` (no new flag — DRY over the value path); `release-notes` pulls the since-last-approved delta from the C9 trail (`assemble_audit_trail.since_last_approved`); new `release-notes` template. Generate an exec one-pager / release-notes / pitch outline *from* the spec (bilingual). Different audience, same source-of-truth; distinct from `--export`/`--viz`. *Research 2026-06-03: `--summary` (fixed exec template) + `--export` (flexible tree-slice) assemblers already exist → E4 = thin mode reusing them, cheap. Both inherit session `lang`; no per-flag lang override today. Brainstorm: thin `--brief` mode w/ audience preset (exec one-pager / release-notes) reusing the assemblers; release-notes flavor pulls from C9's trail → sequence after C9 if that flavor wanted (exec one-pager can ship before).* — **low (build-order #5 — cheap)**
- [x] **E5 — Per-skill release identity.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 1): per-skill `CHANGELOG.md` for product-spec + critique; `verify_skill_versions.py` (nested `metadata.version`, semver shape+presence only, no bundle-equality) wired into `claude-pack-release.yml` before build. Today `product-spec` + `product-spec-critique` ship as **passive payload** inside the single `claude-pack-vX.Y.Z` bundle; their `SKILL.md` `version` is decorative (`2.0.0`/`1.0.0`); CI reads tag only, never SKILL.md. **DECIDED 2026-06-03: standardize the loose hybrid** — give each skill its own CHANGELOG + keep version in SKILL.md, but DO NOT split the CI release (one bundle tag stays the release unit). *Research: only claude-pack has CHANGELOG (keepachangelog); pattern ≈ Changesets (per-package changelog, single release). Cheap: +2 CHANGELOGs, make CI verify SKILL.md version matches bundle. Brainstorm: Changesets-lite, NO new tooling — add CHANGELOG.md to product-spec + critique (keepachangelog), keep version in each SKILL.md as truth, make `claude-pack-release.yml` read+verify versions (fail on drift), bundle tag stays single release unit.* — **med (build-order #1 — do first, scope locked)**

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
