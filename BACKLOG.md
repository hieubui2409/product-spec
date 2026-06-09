# Backlog — `product-spec` + `product-spec-critique` + `release` ecosystem

Source: dual-skill evaluation (2026-05-31). **Groomed 2026-06-03** — reconciled against repo
state; `product-spec-critique` skill folded into scope; pipeline-closing brainstorm items added (§E).
**Re-groomed 2026-06-03 (PM)** — folded 3 PO decisions + C/D/E research grounding
(`plans/reports/research-260603-1758-backlog-cde-grounding-report.md`) + C/D/E brainstorm
(`plans/reports/brainstorm-260603-1758-backlog-cde-approaches-report.md`).
Priority by value/cost. Status: `todo` unless noted.

**PO decisions (2026-06-03):** Q1 release = **internal-only** (B6 → low). · Q2 spec product
**not in market yet** (E3 → deferred). · Q3 E5 = **standardize the loose hybrid** (per-skill
version+changelog, no CI release split). · C10 → **parked** (await task-tracker choice). · D11 →
**close, micro-util only**. · E1 anchoring → pros/cons documented; **A (artifact-id + freshness)
default + C (manual) fallback** recommended, final pick open.

**Recommended C/D/E build order** (brainstorm): **E5 → D12 → E1 → C9 → E4 → E2 → D11**
(stabilize → close the loop → governance/polish → widen → cleanup). C10 parked · E3 deferred.
Status legend: `[ ]` todo · `[~]` in-progress/partial · `[x]` done · `[next]` next-up · `[park]` parked · `[defer]` deferred.
**Build-order C/D/E (E5→D12→E1→C9→E4→E2→D11): ALL SHIPPED** 2026-06-03 (C10 parked · E3 deferred).
**E3 un-deferred + SHIPPED 2026-06-09** (`--learn`, plan 260609-0847) — the "not in market yet" premise lifted.
**Bundle context-flow optimization DONE 2026-06-09** (plan `260609-1048-bundle-context-flow-optimization`,
brainstorm `plans/reports/brainstorm-260609-1048-bundle-context-flow-optimization-report.md`) — measure-first
SKILL.md flag-table compaction: product-spec SKILL.md −11.8% / critique −3.7% (the only per-turn context cost),
elaboration relocated into refs (net info preserved). New `context_footprint.py` harness + GATE co-presence
guard + pytest regression guard; 18 routing-selection evals; best-of-3 sub-agent reasoning judge 18/18 HELD.

---

## v2.0.0 RELEASE — skill rename + restructure (2026-06-07, ✅ SHIPPED, commit `6e64b26`)

PO directive (not a prior backlog item). BREAKING: `cleanmatic:claude-pack` → `cleanmatic:release`; bundle
`claude-pack-{v}.tar.gz` → `product-spec-{v}.tar.gz`; tag `claude-pack-v*` → `product-spec-v*`; CI workflows renamed.

- [x] **Skill/bundle/tag rename + CI rewire** — `git mv` (history preserved), 4 default-string sites, 3 workflow files (`release.yml`/`release-ci.yml`/`release-integration.yml`) + `cross-skill-bug-class` filter, manifest `1.4.0→2.0.0`, release skill `0.2.0→1.0.0`.
- [x] **`release.py` changelog-lifecycle engine** — `--extract/--release/--bump/--pre-release/--date/--apply/--push`; lock `[Unreleased]→[X.Y.Z]` + manifest bump; owner-owned tag push; `REPO=parents[4]` (plan's `parents[3]` guess rejected empirically); 20 unit tests. Adopts HA `_framework-shared/release.py`, drops `release_notes`/PII gate, reuses `pack/`.
- [x] **CI release body from locked CHANGELOG** — `release.yml` runs `release.py --extract <ver>` → `body_path` (replaces `generate_release_notes`).
- [x] **Telemetry hooks `.cjs`→Python** (PO policy: our hooks must be Python) — `track_skill_invocation`/`track_script_execution`/`emit_session_summary`/`telemetry_paths`/`register_telemetry_hooks` rewritten; temp `telemetry-spike` dropped; `settings.json` re-registered to python; 56 tests green.
- [x] **`.gitignore` policy fix** — track our `*.py` hooks + `_shared` python (`run_evals`/`llm_eval` were wrongly ignored → broke a commit); ck `*.cjs` stay ignored.
- [x] **Audit-trail** — `REVIEW.md` Cycle 1 (9 release-pipeline invariants attacked, all held) + `EVIDENCE.md` PACK-2 (REPO path-math).

**Owner-owned remaining (not done by tooling):** `git tag product-spec-v2.0.0 && git push origin HEAD && git push origin product-spec-v2.0.0` → fires `release.yml`.

---

## NEW (2026-06-06, ungroomed)

- [x] ~~**N1 — Repeat-offense finding-level fingerprint (`product-spec-critique`).**~~ ✅ **SHIPPED 2026-06-06** (commits `74f4f29` feat + `791f47f` plan-complete + `226b9af` release 1.3.0→1.4.0). `finding_fingerprint` = normalized hash of (node + critique/why, **line-number dropped**) added to row index → per-finding repeat-offense + line-drift-immune; `:line` is citation-only. Plan: `plans/260606-1627-n1-finding-fingerprint-spec-span-anchor/` (status: completed). Index-empty bug fixed separately (`critique_inherit.py:188`). — **done**

---

## HA-ADOPTION (2026-06-06, groomed + planned + red-teamed)

Learn-back from `human-analyzer` (HA) — CM is the source repo; HA built observability/audit/eval layers on top; adopt those filtered to a 3-skill repo (YAGNI). Source: `plans/reports/comparative-learning-260606-1720-human-analyzer-patterns-report.md` + `plans/reports/ha-implementation-blueprint-260606-1720-four-lens-deepdive-report.md`. **Plan:** `plans/260606-2205-ha-adoption-observability-eval-audit/` (7 phases, `--tdd --redteam`). **Red-team:** `plans/reports/from-code-reviewer-to-planner-red-team-plan-review-260606-2257-ha-adoption.md` (verdict PROCEED-WITH-CHANGES, all applied).

**PO decisions (2026-06-06):** audit-trail → `docs/audit-trail/` (dev, durable). · telemetry → gitignore + CI-assert tarball-exclusion. · STANDARDIZE.md reverse → yes (light). · A9 learning loop → **deferred** (boundary-dirty); the safe slice (repeat-offense *surfacing*) already exists via N1 + findings-index → only "louder presentation" in Phase 05, litmus-bound. · **H1:** release CHANGELOG is bundle-versioned (E5) → A4 excludes release. · **C2:** reshape release evals too (not defer).

**In scope (P0+P1 + polish):** ✅ **ALL SHIPPED 2026-06-07** — plan `260606-2205-ha-adoption-observability-eval-audit/` (Phases 01–07 complete). Reverse ledger: `STANDARDIZE.md` (repo root); fixes/verdicts: `docs/audit-trail/{EVIDENCE,REVIEW}.md`.
- [x] ~~**A1 — Telemetry sink**~~ ✅ fail-open JSONL `_shared/lib/telemetry-paths.cjs` + 3 hooks + `register_telemetry_hooks.cjs`; gitignored + tarball-exclusion test. Hook-event uncertainty resolved by **ship-both** (Skill-tool + prompt-expansion, dedup); bash exit via coarse `tool_response` inference.
- [x] ~~**A2 — Cycle audit-trail**~~ ✅ `docs/audit-trail/{EVIDENCE,REVIEW,README,telemetry-readback}.md`, ID grammar `(PS|PSC|PACK|LIB)-\d+`, size-capped (54/32 lines now).
- [x] ~~**A3 — run_evals harness**~~ ✅ `_shared/lib/run_evals.py` (`_gating: structural|llm_advisory`), 3 CI wirings; release 10 runnable checks, ps/critique honest UNMAPPED for LLM parts (LIB-1 `--root` depth fixed).
- [x] ~~**A3-defer — llm_advisory judge harness**~~ ✅ `_shared/lib/llm_eval.py` (LIB-2): judges 35 advisory assertions (13 ps + 22 critique) against `eval/golden/<id>.md` via injectable LLM client; 15 synthetic tests (no key). MISSING golden → loud (never PASS), garbage judge → ERROR; `--gen` drafts review-gated goldens. Local/on-demand, not CI. **Remaining owner-gated:** running real `--gen` + judge needs an API key + human golden-review (deferred by design).
- [x] ~~**A4 — Version-sync CI gate**~~ ✅ `verify_skill_versions.py::changelog_top_version` + `test_version_sync.py`; ps+critique only, release excluded by design. CM-original.
- [x] ~~**Repeat-offense surfacing polish**~~ ✅ louder count `×N`+occurrence in consolidator/humanizer; `test_repeat_offense_litmus.py` proves boundary catchable (inject→RED).
- [x] ~~**Reverse STANDARDIZE.md**~~ ✅ `STANDARDIZE.md` repo root, 5-row table + divergences (≤60 lines).
- [x] ~~**Red-team adversarial review** (Phase 07)~~ ✅ 8 invariants attacked, all held (reproducible command+state); 0 BROKEN; verdicts in `REVIEW.md`.

**Telemetry usage-&-health skill (`cleanmatic:telemetry`) — SHIPPED 2026-06-07** (plan `260607-1500-telemetry-insights-skill/`, Phases 1–8). xia PORT of `human-analyzer`'s `com:skill-analytics` (dev-facing EN) → cleanmatic (flat slugs, VI non-tech narration). Architecture: scripts gather (deterministic) / skill narrates (LLM). **SHIPPED in the bundle (product-spec-v2.1.0)** — skill + 5 sink hooks + shared lens/eval code via `_include_shared:[lib,scripts]`; the installer auto-registers the hooks (opt out: `register_telemetry_hooks.py --remove`). Reverses the original CM-local/not-bundled decision (D5/D8) per PO 2026-06-08.
- [x] ~~**8 lenses**~~ ✅ `_shared/lib/lens_*.py` + `_shared/scripts/analyze_telemetry.py`: usage+tokens, session-shape, coarse-health, reliability, workflow-chains, memory-health (read-only), forensics, validate-pass proxy. Flat-slug catalog (`catalog.py` reads SKILL.md `name:`). Low-volume gate.
- [x] ~~**2 new sinks (hook-only)**~~ ✅ `subagent-outcomes.jsonl` (SubagentStop) + `ms` on `hook-telemetry.jsonl` (Pre/Post:Bash pairing). atexit/excepthook still NOT used — hook-only keeps the sinks fail-open + decoupled (the old "ModuleNotFoundError because `_shared` not bundled" rationale no longer applies now that `_shared` ships). Pairing keyed on command-hash only (live Pre/Post session_id is asymmetric).
- [x] ~~**Renderers**~~ ✅ `telemetry_render.py`: ascii (terminal) + mermaid (escaped, no network/JS) — the genuine gap over HA — plus md/json from `formatters.py`. NO HTML (D4).
- [x] ~~**Effectiveness proxy**~~ ✅ validate-pass = INTERNAL quality (last-status from `last_validated.json` marker + pass-rate from validate-script exit history); honest n/a when no runs. Explicitly **NOT E3**.
- [x] ~~**Packaging guards**~~ ✅ (REVERSED to ship 2026-06-08) `telemetry` in BOTH `DEFAULT_SKILLS` and `VERSION_SYNCED_SKILLS` (ships → changelog-pinned); manifest lists the skill + 5 hooks + `_include_shared:[lib,scripts]`; `__tests__`/`tests` dropped from the bundle by `safety_catalog`; bundle-INCLUDE test + "core skills stay telemetry-independent" test green.
- [defer] **Rich `errors.jsonl` crash-log** (stack traces via excepthook) — DEFERRED (YAGNI): the old bundle-leak blocker is gone now that the telemetry modules ship, but there's no demand yet. Script failures stay as the coarse `exit` in `hook-telemetry.jsonl`. Revisit on demand.
- [defer] **HTML telemetry output** — out of scope (avoids vendored-asset / shipped-render coupling, F1). A future separate plan only.
- [note] **E3 outcome tracking** SHIPPED 2026-06-09 (`--learn`). The telemetry validate proxy stays internal-quality only — `--learn` records PO-declared outcomes vs goals (offline), still NOT a market-effectiveness metric. The internal-quality vs market-effectiveness boundary is unchanged; only E3's deferred status lifted.

**Out of scope this round (P2/P3):** A5 context-gauge · A6 e2e pipeline · A7 PreCompact digest (all P2) · A8 nav-doc auto-gen (P3, 3-skill = low value) · A9 quality-gate learning loop (P3, **deferred** — dirties report-only/non-deterministic boundary; the safe slice shipped as repeat-offense polish).

---

## A. Bridge product-spec ↔ release — CLOSED (premise was flawed)

> **2026-06-04 (PO critique):** Group A conflated two different jobs — *distributing a tool* (release's
> real job) vs *versioning living content* (git's job). The spec is co-located with the code in the same
> repo, so **git is the single source of truth + versioning + diff**, and the skill already provides the
> sync surface (`change-log.md`, `decisions.md`, `--viz audit`, `--summary --audience release-notes`,
> `--approve` snapshots, `--viz delta`). Packing the spec fights the living spec→code→spec-update pipeline.
> Both items dropped.

- [x] ~~**A1 — `product-spec --pack` / export-to-distributable.**~~ **DROPPED 2026-06-04 (PO critique):** a tarball is strictly worse than the repo for a *living* spec — you can't diff opaque tarballs, and the spec→code→update→code-update loop would force a churny tarball-per-edit. Every need it claimed is already met: "what changed" → `--summary --audience release-notes` + `--viz audit` + `git diff docs/product/`; "lock scope for release X" → `--approve` (owner+date+version) + `.snapshots/` + `--viz delta`; "mid-phase change to approved spec" → GATE-NO-SILENT-REVERSAL + Decision Register + `--update` (no new pack); "single source of truth, dev-read/PO-write" → `docs/product/` in-repo + branch protection/CODEOWNERS. Residual external-hand-off sliver is served by the existing `--export` (readable doc); authenticity there = B6 (signing), not a spec pack. — **cut (YAGNI)**
- [x] ~~**A2 — Pack a "product-spec starter".**~~ **DROPPED 2026-06-04 (PO critique — redundant three ways):** (1) the "empty `docs/product/` seed" is dead weight — product-spec **self-scaffolds** `docs/product/` on no-flag init / `--product`; (2) product-spec already ships in the bundle and release already builds a single-skill bundle via **`--skills product-spec`** — no new asset needed; (3) onboarding is already prompt-driven (README.md + CLAUDE.md → install bundle → `/cleanmatic:product-spec` → the AI interviews + generates). Nothing left for a static "starter" to add. — **cut (YAGNI)**

## B. Harden release (now shipped at 1.1.0 — remaining gaps)

- [x] **B3 — Removed `--all`** *(2026-06-04)*. The flag never worked (errored exit 1) and is against the curated-distribution design (the manifest + `--skills` is the interface); dropped the arg/handler + docs rather than implement a "pack everything" anti-feature. — **done (removed, KISS)**
- [x] **B4 — Pytest the installer semver logic** *(2026-06-04)*. `test_installer_semver.py` extracts the real `semver_compare` (bash) from the template and runs a 19-case edge matrix (leading-zero octal trap, pre-release < release, numeric vs alphanumeric identifiers, build-metadata-ignored, ASCII collation `RC`<`rc`) + an antisymmetry check; `Compare-Semver` (ps1) parity runs on the Windows CI leg (skipped where `pwsh` absent). Both marked `bug_class`. — **done**
- [x] **B5 — Run-the-extracted-`install.sh` e2e** *(2026-06-04)*. `test_installer_e2e.py` builds a real bundle via `python -m pack`, extracts it, runs the bundled `install.sh` into a throwaway `TARGET_DIR`, asserts the files actually land, then asserts a second run is idempotent (skips existing). Closes the "we build bundles but never prove they install" gap. — **done**
- [defer] **B6 — Authenticity option (minisign/sigstore).** SHA256 sidecar resists corruption, not tampering (attacker swaps both tarball + sidecar). **DECIDED 2026-06-03: distribution is internal-only → deprioritized to low.** Revisit only if distribution goes public. — **low (was med)**
- [ ] **B7 — `install.sh --verify-only` (NOT a standalone `claude-unpack`).** *Re-scoped 2026-06-04 (PO critique): a standalone pre-installed `claude-unpack` companion is a **bootstrap circle*** — verifying the distribution of release would require first distributing+trusting claude-unpack (turtles). Resolution: the verifier must ride **inside** the bundle like `install.sh` already does. Three tiers: **(1) integrity/transit** is already solved by the coreutils `.sha256` sidecar (`sha256sum -c`, no release-specific tool); **(2) content-vs-MANIFEST per-file** = the only real residue → add a `--verify-only` flag to the bundled `install.sh` that walks `MANIFEST.json` and checks each file's SHA (today `install.sh.template:28` only checks MANIFEST *exists*). Low value (largely redundant with the whole-tarball sidecar). **(3) authenticity/tampering CANNOT be self-verified** — an attacker swaps tarball+sidecar+MANIFEST+verifier together; it needs an **out-of-band trust anchor (a signature/key the recipient already trusts)** = **B6**, using a general-purpose verifier (minisign/cosign), not a release tool. → **Do (2) only if cheap; the valuable "can I trust the source" intent is B6, not B7.** — **low (de-scoped)**

## C. Deepen product-spec (go deeper, not wider)

- [x] **C8 — v2 multi-dim views: KEEP** *(decided 2026-06-03).* risk / competition / dashboard / explorer confirmed wanted by POs; the cut suggestion is dropped. Standing obligation (not a cut): hold escape/parity discipline across the 14 views × 3 formats — viz was the cycle-1 XSS sink, so this stays a **security-regression watch**. — **resolved**
- [x] **C9 — Semantic spec changelog / audit trail.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 4): `--viz audit` (`assemble_audit_trail.py`, ASCII+md, `unreconciled` rows, reuses status.py loaders). Build on existing `.snapshots/` + delta view: what drifted, who approved, when. Turns `change-log.md` into a governance-usable audit trail. *Research 2026-06-03: infra mostly EXISTS — `spec_graph.py` `diff_graphs()`/`changed_nodes()`, `change-log-entry.md` template (has author/date/dims), `approval:` frontmatter, `status.py` `stale_approvals`, `decision_register.py`. Gap = one unified audit-trail VIEW. Mostly assembly, not new build. Brainstorm: read-only `--audit` view (or `--viz audit`) joining change-log + approval + stale_approvals + DEC refs; columns when·artifact·action·who-approved·what-drifted·DEC. Keep it a viewer (read-only). Feeds future E3.* — **med (build-order #4)**
- [park] **C10 — Round-trip to issue tracker.** Export stories→GitHub Issues/Jira preserving traceability IDs (`PRD-AUTH-E1-S1`). Keeps the spec alive without violating "no code generation." *(Forward "handoff" edge from §E.)* **PARKED 2026-06-03 (PO):** blocked on a prior decision — *which task tracker is the target*. When chosen, build as a **separate outward-facing skill + bridge infra** reading product-spec's exported artifact (one-way idempotent, back-ref issue number into story frontmatter). Keeps product-spec's no-runtime-network + non-tech-PO promises intact. Not actioned this round. — **parked (await tracker choice)**

## D. Shared foundation for the ecosystem

- [x] **D11 — Shared foundation: CLOSED to micro-util only.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 7): `_hashable()` consolidated into `render_common.py` (product-spec-internal, output byte-unchanged). Per red-team: `_now()` left divergent (intentional), no cross-skill module (unbundlable). 🟥 *Research 2026-06-03 REFUTED the premise: actual duplication ≈ 0* (determinism only in release; HTML/escaping only in product-spec; **critique & release generate NO HTML** → no analogous XSS sink). **DECIDED 2026-06-03 (PO): close the "common base" ambition; consolidate ONLY the genuine micro-dup** — `_now()` (×4) + `_hashable()` (×3) → one tiny shared util the 3 skills import (verify release bundles it). Determinism/safety/design-system extraction = dropped (YAGNI). — **low (build-order #7)**
- [x] **D12 — Cross-skill regression gate in CI.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 2): `product-spec-ci.yml` + `product-spec-critique-ci.yml` (1 OS × 2 Python, path-filtered, per-skill-dir scoped; critique offline-enforced via `CK_OFFLINE` socket guard) + `cross-skill-bug-class.yml`; `bug_class` marker registered in all 3 pytest configs. *Partial:* `release-ci` (dry-run) + live `release-integration` (product-spec dogfood) + `release-release` exist. ⚠️ *Research 2026-06-03: product-spec (31 tests) & product-spec-critique (10 tests) have NO dedicated CI workflow — run by hand.* The "10-cycle red-team" = C9→C10→C11 chain (`plans/reports/cycle-11-…md`; bugs 101→67→37; symlink/case-insensitive/XSS held every cycle). **Remaining:** add CI workflows running the 50 existing tests for all 3 skills + a shared bug-class matrix (symlink leak, case-insensitive bypass, untracked asset). *Brainstorm: 2 thin workflows (1 OS × 2 Python is enough — argue down release's 3×3) + a centralized bug-class test module. Build BEFORE E1/E2 so new features land on a gated suite.* — **med (build-order #2 — highest-leverage in D)**

## E. Close the PO pipeline (brainstorm 2026-06-03 — close the edges, don't widen)

Framing: `product-spec` (processing) → `product-spec-critique` (post-processing) is an **open pipeline**
with dangling edges. These close them. Prefer **modes on existing skills** over new skills (YAGNI / anti-bloat);
a new skill is justified only for outward-facing integration.

- [x] **E1 — Apply-critique loop (the return edge).** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 3): `--apply-critique <report>` — lens-cache-JSON parse + per-finding fingerprint + freshness (None-safe), read-fenced to `docs/product/critique/`, atomic+resumable+injection-safe DEC writes (`decision_register --append-alloc`), deterministic GATE re-approval guard. Scripts `parse_critique_report.py`/`apply_critique_progress.py`, ref `workflow-apply-critique.md`. `product-spec --apply-critique <report>`: walk each critique finding → **Keep / Change+re-approve / Defer**, recording rulings in the Decision Register (`DEC-<n>`) and honoring GATE-NO-SILENT-REVERSAL. Critique stays report-only; the spec-owning skill consumes its output. *Single biggest structural gap.* **Mode on product-spec.** *Research 2026-06-03: flag does NOT exist yet (new feature). Infra MATURE — DEC register + `decision_register.py`, GATE in `guardrails-and-boundaries.md:102`, `--update` impact-pass. ⚠️ critique findings have NO stable ID (transient) → must anchor by `evidence ID:line`; design for `:line` drift when spec changes after critique. **Brainstorm anchoring options (pros/cons in report): A** anchor by artifact-id + `body_hash` freshness warning, **B** require freshest critique (hash-gate), **C** manual per-finding PO confirm. **Recommended: A default + C fallback** (B's correctness real but friction kills adoption). Final pick OPEN.* — **high (build-order #3 — biggest structural gap)**
- [x] **E2 — Discovery seed (the pre-stage).** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 6): `--discover <path(s)>` — read-fenced ingest (`ingest_raw_inputs.py`): project-root fence, `.md`/`.txt` allow-list, dotfile exclusion, size cap, bounded directory recursion (depth+count); empty candidate buckets (no auto-commit, GATE-NEVER-ASSUME); ref `workflow-discover.md`. `product-spec --discover`: ingest raw inputs (interview transcripts, support-ticket dumps, competitor notes) → synthesize candidate personas + problems + JTBD to **seed** the Vision/BRD interview instead of a cold start. Complements (not duplicates) the interview, which assumes you already know your personas. **Mode on product-spec.** *Research 2026-06-03: flag does NOT exist (closest = `--auto` brain-dump). Vision interview V1–V7 asks personas as an OPEN question (assumes you know them) → seeding is genuinely additive. Brainstorm: scope TIGHT — text in → candidate persona/problem/JTBD bullets out → interview confirms (never auto-commit personas, GATE-NEVER-ASSUME). Easiest item to over-build; if the `--auto` distinction blurs, merge into `--auto` rather than ship 2 flags. Do AFTER E1 proves the loop.* — **med-high (build-order #6)**
- [x] **E3 — Outcome tracking (the learning edge).** ✅ **SHIPPED 2026-06-09** (plan 260609-0847): `--learn` umbrella mode (un-defers E3 — the "not in market yet" premise lifted now the PO has real insight). *Outcomes loop:* `record_outcome.py` appends `OUT-<n>` to `docs/product/outcomes.md` (per-outcome fenced block, append-only, never touches the BRD goal schema) with a deterministic 3-tier verdict (hit/partial/miss, direction-aware, floors configurable via `preferences.py`); a `miss` on an approved goal is *surfaced* (Keep/Change/DEC), never auto-edited. *Feedback loop (discover-back):* reuses `ingest_raw_inputs.py` → candidate problems/personas → `--update`. Viz: `scorecard` (+blind-spot) · `insight-gap` · `outcome-trend` · `learning-map` (extends `assemble_audit_trail`, no schema bump) · `learning` dashboard. **PO decisions: Light verdict · both loops · mode on product-spec · `outcomes.md` register (not goal schema) · `--learn` umbrella · Hybrid verdict · no quadrant.** Closes spec→build→measure→learn; feeds C9. — **shipped**
- [x] **E4 — Stakeholder brief.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 5): `--summary --audience exec|release-notes` (no new flag — DRY over the value path); `release-notes` pulls the since-last-approved delta from the C9 trail (`assemble_audit_trail.since_last_approved`); new `release-notes` template. Generate an exec one-pager / release-notes / pitch outline *from* the spec (bilingual). Different audience, same source-of-truth; distinct from `--export`/`--viz`. *Research 2026-06-03: `--summary` (fixed exec template) + `--export` (flexible tree-slice) assemblers already exist → E4 = thin mode reusing them, cheap. Both inherit session `lang`; no per-flag lang override today. Brainstorm: thin `--brief` mode w/ audience preset (exec one-pager / release-notes) reusing the assemblers; release-notes flavor pulls from C9's trail → sequence after C9 if that flavor wanted (exec one-pager can ship before).* — **low (build-order #5 — cheap)**
- [x] **E5 — Per-skill release identity.** ✅ **SHIPPED 2026-06-03** (plan 260603-1817 Phase 1): per-skill `CHANGELOG.md` for product-spec + critique; `verify_skill_versions.py` (nested `metadata.version`, semver shape+presence only, no bundle-equality) wired into `release.yml` before build. Today `product-spec` + `product-spec-critique` ship as **passive payload** inside the single `product-spec-vX.Y.Z` bundle; their `SKILL.md` `version` is decorative (`2.0.0`/`1.0.0`); CI reads tag only, never SKILL.md. **DECIDED 2026-06-03: standardize the loose hybrid** — give each skill its own CHANGELOG + keep version in SKILL.md, but DO NOT split the CI release (one bundle tag stays the release unit). *Research: only release has CHANGELOG (keepachangelog); pattern ≈ Changesets (per-package changelog, single release). Cheap: +2 CHANGELOGs, make CI verify SKILL.md version matches bundle. Brainstorm: Changesets-lite, NO new tooling — add CHANGELOG.md to product-spec + critique (keepachangelog), keep version in each SKILL.md as truth, make `release.yml` read+verify versions (fail on drift), bundle tag stays single release unit.* — **med (build-order #1 — do first, scope locked)**

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

**release**
- `--all` dead; no GPG/authenticity; no zip/zstd; no merge-resolver; no `claude-unpack`.
- Installer logic (highest risk) still not pytest-covered (B4).
- SHA256 = corruption-resistant, not tamper-resistant.
- Symlink-leak class (patched once via MANIFEST) is subtle — watch for variants.

**Pairing reality**
- product-spec ↔ product-spec-critique are now a genuine processing / post-processing pair; the open edges (E1/E2) are the highest-leverage links to make it a closed loop. release remains orthogonal tooling — it *packages* the pair (A1/A2 deepen that), it is not part of the spec data flow.

---

## Open questions

**Resolved 2026-06-03:**
- ~~release internal-only or public?~~ → **internal-only** (B6 → low).
- ~~E3 specs reaching real users yet?~~ → **resolved 2026-06-09: PO now has real insight → E3 shipped (`--learn`).**
- ~~E5 per-skill versioning vs single-bundle?~~ → **standardize loose hybrid** (per-skill changelog, single CI release).

**Resolved 2026-06-03 (PM, from brainstorm):**
- ~~C10 positioning?~~ → **parked** until the target task tracker is chosen; then a separate outward-facing skill reads product-spec's exported artifact.
- ~~D11 closure?~~ → **close to micro-util only**; drop the design-system ambition.

**Resolved-by-ship (2026-06-03/07):**
- ~~E1 anchoring final pick~~ → shipped with **A (artifact-id + freshness) default + C (manual) fallback**.
- ~~E2 vs `--auto`~~ → shipped as a separate `--discover` flag.
- ~~D12 CI matrix~~ → shipped at **1 OS × 2 Python** (path-filtered, per-skill-dir).

**Still open:**
- **C10 target:** which task tracker (GitHub Issues / Jira / other)? Decides when C10 un-parks. *(The only genuinely-open question.)*
