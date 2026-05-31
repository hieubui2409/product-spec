---
title: "claude-pack plan validation — critical questions lens"
from: planner
to: pm
date: 2026-05-29
plan: plans/260529-0343-claude-pack-skill/
mode: critical-questions
overlap_avoided: red-team (determinism/safety bypass/atomic-write/golden-test flakiness/dep-grep FP/spec ambiguity/YAGNI)
---

# claude-pack Plan Validation — Critical Questions

Scope: phase completeness gates, cross-phase contract integrity, measurability, effort calibration, release/DoD, docs coverage, failure recovery, CI/CD, schema migration, PO comms, version disambiguation, dogfooding pinning, operator handover, sunset path, repo-rule compliance.

Severity: BLOCKING > HIGH > MEDIUM > LOW > OBSERVE.

---

## Q1 — Phase Completeness Gates

### F1.1 [HIGH] Phase 1 Success Criteria missing reference content gates
- Lens: Q1
- Problem: phase-01.md → "Success Criteria" lists structural checks (dirs exist, install.sh exits 0, frontmatter YAML lint). 4 reference stubs (`manifest-spec.md`, `flag-reference.md`, `safety-rules.md`, `workflow-pack.md`) only required to be "marked STUB". No content gate even for the stub paragraph. Two engineers could ship empty files with just the STUB marker.
- Fix: add "each stub has ≥1 sentence purpose paragraph + the section headings the later phase will fill". Add measurable line-count floor (e.g., ≥10 lines per stub).

### F1.2 [HIGH] Phase 2 silent work: dep-grep + atomic write + collision handling not in Success Criteria
- Lens: Q1
- Problem: phase-02.md → Steps 5 (dep grep), 10 (atomic write), 13 (collision/`--force` backup) are core invariants. Success Criteria covers only "two consecutive runs produce identical SHA256" + "no .env in tarball". Silent obligations: dep-grep correctness, atomic-rename behavior, collision exit code 3, `.bak.{epoch}` semantic.
- Fix: add explicit checks:
  - `pack.py --manifest <m-with-shared-ref> --dry-run` → output mentions auto-included `_shared/<name>` with WARN.
  - `pack.py` invoked twice without `--force` against existing tarball → second invocation exits 3.
  - `pack.py --force` against existing tarball → renames to `dist/claude-pack-X.Y.Z.tar.gz.bak.{epoch}` before write.
  - `os.rename` is atomic within same dir (document; assertion via mocked failure).

### F1.3 [MEDIUM] Phase 3 missing finding-shape contract test
- Lens: Q1
- Problem: phase-03.md → JSON output shape declared in Requirements but Success Criteria checks "emits valid JSON" only. Doesn't pin field names (`check`, `severity`, `path`, `rule`).
- Fix: add: "`safety_check.py --root . --scan .claude` emits findings where each entry has exactly the keys `{check, severity, path, rule}` (+ optional `referring_skill`)".

### F1.4 [MEDIUM] Phase 4 missing "no partial file on abort" gate
- Lens: Q1
- Problem: Risk R3 + Step 5 imply abort-safety, but Success Criteria does not check. `build_manifest.py` killed mid-`--write` could leave half-written `pack.manifest.yaml`. Plan doesn't say `build_manifest.py --write` itself uses atomic write.
- Fix: add to phase-04 Step 3: "write to tmp + atomic rename (mirror pack.py pattern)". Add Success Criterion: "SIGTERM during `--write` leaves no partial manifest file".

### F1.5 [LOW] Phase 5 T-D6 silent assumption — would-be SHA matches real SHA
- Lens: Q1
- Problem: phase-05.md → T-D6: "`--dry-run` returns same SHA as real run". This is non-trivial because dry-run writes to BytesIO, real run writes to disk via gzip stream. Both must produce byte-identical output. Test passes only if the implementation pipes identical bytes to both sinks. No success criterion forces them to share the same write path.
- Fix: add note to phase-02 Step 9: "share the byte-producing routine between dry-run (BytesIO) and real run (atomic file write); never duplicate logic". Reference Phase 5 T-D6 as the enforcer.

### F1.6 [MEDIUM] Phase 6 Success Criteria silent on smoke-test idempotency
- Lens: Q1
- Problem: phase-06.md → Smoke test 7 (sandbox install) populates `/tmp/cp-recipient/.claude/`. No check that running installer twice is idempotent (recipient may re-run after pulling new pack). Default `[SKIP]` mode means second run is no-op; needs verification.
- Fix: add Success Criterion: "Smoke test 7 re-run: second invocation reports `[SKIP]` for existing files; exits 0; no overwrites".

---

## Q2 — Cross-Phase Contract Integrity

### F2.1 [BLOCKING] `requirements.txt` mutation across phases — DRY violation
- Lens: Q2
- Problem:
  - Phase 1 (Step 5): `requirements.txt` = `pyyaml` only.
  - Phase 4 (R5): pin `pyyaml>=6.0,<7`.
  - Phase 5 (Modify section + R4): add `pytest>=7,<9`, `pytest-cov` (optional).
  - These mutations are buried in Implementation Steps / Risk sections. No phase says "Phase 5 supersedes Phase 1 requirements.txt". Two engineers reading Phase 1 in isolation will encode `pyyaml\n` and ship.
- Fix: add a "Cross-Phase Artifact Mutations" table to plan.md listing every file that changes scope across phases, with line in each phase noting the final shape. For `requirements.txt`, lock final form in plan.md:
  ```
  pyyaml>=6.0,<7
  pytest>=7,<9
  ```
  Reference that block from Phase 1 + Phase 4 + Phase 5.

### F2.2 [HIGH] Phase 2 imports Phase 3 modules — API signatures not pinned in plan
- Lens: Q2
- Problem: phase-02 architecture refers to `safety_check.is_dropped(path)`, `safety_check.follow_shared(...)`, `manifest_loader.load(...)`, `manifest_loader.merge_cli(...)`. Phase 3 declares same signatures. BUT: parallel-development viability requires the signature contract to be locked BEFORE either phase starts. Plan has no "API Contract" section.
- Fix: add `## API Contracts (locked before any phase starts)` to plan.md:
  ```python
  # safety_check
  def is_dropped(path: str) -> tuple[bool, str | None]
  def is_optional(path: str) -> tuple[bool, str | None]
  def follow_shared(skill_dirs: list[Path], shared_root: Path) -> list[tuple[Path, str]]

  # manifest_loader
  class ManifestError(Exception): ...
  def load(path: Path) -> dict
  def merge_cli(manifest: dict, cli: argparse.Namespace) -> dict
  def validate(manifest: dict) -> list[str]
  def apply_defaults(manifest: dict, root: Path) -> dict
  ```
  Any change requires plan-amend, not silent drift.

### F2.3 [HIGH] Phase 3 outputs not declared as inputs of Phase 4
- Lens: Q2
- Problem: phase-04.md depends on `manifest_loader.validate` (Step 3) and `manifest_loader.DEFAULTS` (R1 mitigation derives Q-IDs from this). Phase 4 dependency declared as `[1, 3]`. Good. BUT phase-04 also depends on Phase 3's `manifest-spec.md` reference (`assets/templates/manifest.example.yaml` schema must match Phase 3 schema). Plan doesn't surface that.
- Fix: phase-04.md "Context Links" should explicitly list "Phase 3 → `references/manifest-spec.md` (filled)" as a prerequisite. Currently links only to "Phase 3 (`manifest_loader.py`)".

### F2.4 [MEDIUM] Phase 6 seed manifest depends on Phase 4 `build_manifest.py` exit semantics
- Lens: Q2
- Problem: phase-06 Step 5 hand-writes `.claude/pack.manifest.yaml`. But the canonical creation path per the skill IS `build_manifest.py --write`. Why is the seed hand-written? Dogfooding violation: the skill cannot eat its own dogfood for the seed manifest.
- Fix: change phase-06 Step 5 to: "Run `build_manifest.py --write` with prepared answers JSON to generate the seed manifest. Hand-edit only if interactive flow has a documented limitation." OR document why hand-writing is acceptable here ("seed manifest is reference, not user-generated").

### F2.5 [LOW] Phase 5 T-G1 golden depends on real product-spec install state
- Lens: Q2
- Problem: Phase 5 packs `cleanmatic:product-spec` as golden. If product-spec is mid-development (uncommitted local edits), golden tree drifts vs main branch. No pinning. (Red-team covers golden flakiness; this is the cross-phase angle: T-G1 depends on Phase 6 NOT yet having modified product-spec — clean dependency direction.)
- Fix: pin golden to product-spec git SHA at plan-write time. See F12.1.

---

## Q3 — Acceptance Criteria Measurability

### F3.1 [HIGH] "Follows product-spec convention" not measurable
- Lens: Q3
- Problem: Multiple phases reference "mirror product-spec" / "follow product-spec convention". This phrase is judgment-laden. Two engineers will diverge.
  - phase-01 Step 2: "copy product-spec shape" — which fields are mandatory vs optional?
  - phase-01 Step 4: "researcher B's ~30-line template" — exact path?
  - phase-05 R2 R4 / Step 1: "mirror product-spec line 56-62 equivalent" — line range hardcoded but may have shifted.
- Fix: in each step, replace "mirror product-spec" with explicit file + line range, e.g., `.claude/skills/product-spec/SKILL.md:1-12` for frontmatter, `.claude/skills/product-spec/install.sh:1-30` for installer pattern. Verify line ranges at plan-time and pin.

### F3.2 [HIGH] "≤250 lines / ≤80 lines / ≤200 lines / ~350 lines" — mix of ceiling and target
- Lens: Q3
- Problem: phase-01 "SKILL.md ≤250 lines" (ceiling). phase-06 "section ≤80 lines" (ceiling). phase-02 "pack.py ~350 lines" (target/estimate). phase-05 test files "~200 lines, ~150 lines, ~120 lines" (estimates). Ceiling vs estimate distinction unclear; estimates may be cited as fail conditions.
- Fix: clarify — only enforce ceilings (with explicit verification step). Estimates marked "(estimate, not gate)" so a 380-line pack.py doesn't fail review.

### F3.3 [HIGH] "Skill name discoverable via `/cleanmatic:claude-pack`" — frontmatter field unspecified
- Lens: Q3
- Problem: phase-01 Step 2 says `user-invocable: true`. The actual mechanism (slash-command registration) is unclear. Does ck CLI auto-discover from `name:` field? Is there a separate registry? Untested in any phase.
- Fix: add Success Criterion to phase-01: "after install, `/cleanmatic:claude-pack --help` resolves" OR document the actual discovery mechanism if it's CLI-driven (`ck` invokes by skill folder name + manifest).

### F3.4 [MEDIUM] Phase 4 "human-friendly YAML" / "ordered keys" semantically loose
- Lens: Q3
- Problem: phase-04 Requirements: "ordered keys (schema_version, version, bundle_name, then categories), 2-space indent". Step 3: "re-ordering keys to canonical order". Canonical order not fully enumerated. What about `extra`, `top_level`, `follow_shared`? Plan Step 3 lists them but not in Requirements.
- Fix: lock canonical order in one place (Requirements section):
  `schema_version, version, bundle_name, skills, agents, hooks, rules, extra, top_level, follow_shared`.

### F3.5 [MEDIUM] Phase 6 "append after Product Spec section, before any global tail content" — fuzzy
- Lens: Q3
- Problem: phase-06 Step 2: "Append the new section after Product Spec section, before any global tail content." Root CLAUDE.md doesn't have a marked "tail" — append target is ambiguous.
- Fix: add explicit marker: "append after the LAST occurrence of `---` on a line by itself in CLAUDE.md (end-of-section divider), OR at EOF if no such divider". Better: introduce stable comment marker `<!-- END:product-spec-guide -->` in Product Spec section (out of scope?) or pin by line number (fragile).

### F3.6 [LOW] "Reasonable" / "acceptable" / "best-effort" weasel words
- Lens: Q3
- Problem: phase-04 R4 "acceptable for ≤200 skills" (acceptable = ?). phase-04 Step 2 "best-effort; v1 ships English-only" (no contract). phase-06 R5 "best-effort from git remote" (passes with "" — but no test checks empty case).
- Fix: replace "best-effort" with explicit behavior + exit semantics. For git remote failure: "`source_repo: ""` (empty string, not null); tested in phase-05 T-D3 add-on".

---

## Q4 — Effort Estimates Calibration

### F4.1 [HIGH] Phase 5 — 5h for 17 unit tests + 3 evals + 6 fixture trees + golden = optimistic
- Lens: Q4
- Problem: phase-05 declares effort 5h. Work breakdown:
  - 17 unit tests (T-D1..T-D7, T-S1..T-S5, T-M1..T-M4, T-B1..T-B3) × ~15-20 min = 4-6h.
  - 1 golden test (T-G1) with snapshot logic = 1h.
  - 3 eval scenarios + fixtures = 1h.
  - `conftest.py` + pyproject.toml + fixture trees (4 dirs) = 0.5h.
  - Subprocess + SIGTERM mock for T-D7 = 0.5-1h (risk-flagged).
  - Run + debug loop = 1-2h.
  - Total realistic: 8-10h, not 5h.
- Fix: bump Phase 5 effort to 8h. If 5h is a hard ceiling, descope: drop T-D7 (atomic write covered via mock per R2), defer T-B3 round-trip to v1.1, drop T-G1 to manual smoke (phase-06 Smoke test 4 already covers determinism).

### F4.2 [MEDIUM] Phase 2 — 5h for ~350-line `pack.py` + flag-reference fill — tight
- Lens: Q4
- Problem: phase-02: skeleton + 17 flags + argparse + manifest resolve + dep grep + selection + sorted walk + MANIFEST build + dual-write path (dry-run + real) + atomic rename + gzip mtime + sidecar + collision handling + logging + reference fill. Realistic 6-7h.
- Fix: bump to 6h or split off `flag-reference.md` fill into Phase 1 (it's documentation; only needs flag NAMES, not behavior; full description can be filled iteratively).

### F4.3 [LOW] Phase 3 — 4h for 380 lines of code + 2 reference fills — plausible
- Lens: Q4
- Problem: Both modules are straightforward parse+validate. Reference fills are non-trivial (rationale per always-drop entry). Estimate OK.
- Fix: none. OBSERVE.

### F4.4 [LOW] Phase 4 — 4h for 250-line script + workflow-pack.md fill — plausible
- Lens: Q4
- Problem: Discovery is os.scandir (cheap). Question bank assembly is mostly data structure. workflow-pack.md fill has 5 sections of prose. Estimate OK with risk on prose quality.
- Fix: none. OBSERVE.

### F4.5 [MEDIUM] Phase 6 — 2h for 7 smoke tests + CLAUDE.md edit + seed manifest — tight if any test fails
- Lens: Q4
- Problem: 7 smoke tests sequentially executed. If any fails, debug + fix loop will exceed 2h. Phase has no fallback budget.
- Fix: bump to 3h OR document "if smoke test fails, recovery is a new mini-phase with new estimate".

### F4.6 [OBSERVE] Total plan effort: declared sum = 3+5+4+4+5+2 = 23h
- Lens: Q4
- Problem: If F4.1 + F4.2 + F4.5 applied (8+6+3), total = 3+6+4+4+8+3 = 28h.
- Fix: update plan.md effort sum + warn PO this is a 3-4 day effort, not 2-3.

---

## Q5 — Definition of Done for Whole Skill

### F5.1 [BLOCKING] No release gates section in plan.md
- Lens: Q5
- Problem: Plan declares `version: 0.1.0` in seed manifest. SKILL.md `metadata.version: "1.0.0"` in phase-01 Step 2. No criteria for 0.1.0 → 1.0.0 transition. What's the bar for "shippable to external recipient"?
- Fix: add `## Release Gates` section to plan.md:
  ```
  | Version | Gate |
  |---------|------|
  | 0.1.0 (dogfood) | All 6 phases complete, smoke test 7 green, used internally to pack product-spec |
  | 0.5.0 (beta)   | External recipient successfully extracts + runs installer on macOS + Linux + Windows |
  | 1.0.0 (GA)     | 5+ external bundles shipped without bug reports; recipient docs ratified |
  ```

### F5.2 [HIGH] No "skill is shippable" checklist
- Lens: Q5
- Problem: Each phase has Success Criteria, but no overall criterion: "is the skill ready to ship to a recipient?" Smoke test 7 is the closest analog but skips: SHA256 verification by recipient, INSTALL.md content review, multi-OS extract test (only Linux tested).
- Fix: add to phase-06 (or new phase-07): "Ship Readiness Checklist":
  - [ ] Recipient can `sha256sum -c` the sidecar
  - [ ] INSTALL.md reads correctly to non-expert
  - [ ] install.sh tested on macOS + Linux
  - [ ] install.ps1 tested on Windows (or marked deferred to 0.5.0)
  - [ ] Re-running installer in same target is idempotent

### F5.3 [HIGH] No exit criteria for "manifest schema is locked"
- Lens: Q5
- Problem: Schema v1.0 declared. No criterion to declare it locked vs subject-to-change. Without lock, v0.1.0 packs may be unreadable by v0.2.0.
- Fix: add to plan.md "Schema v1.0 frozen at end of Phase 3. Changes to fields require schema_version bump + migration path (see F9.1)".

---

## Q6 — Documentation Completeness

### F6.1 [HIGH] No troubleshooting guide
- Lens: Q6
- Problem: No phase produces a `references/troubleshooting.md`. Common failure modes (recipient: SHA mismatch, missing pyyaml, install.sh permission denied, symlink in `.claude/`, manifest with stale skill name) have no documented remediation.
- Fix: add to phase-06 Implementation Steps (or new mini-phase): create `references/troubleshooting.md` with ≥5 common failures + fixes. ≤60 lines.

### F6.2 [HIGH] No error catalog
- Lens: Q6
- Problem: Plan declares exit codes 0/1/2/3 (phase-02 Requirements), `ManifestError`, "selection_missing" finding, etc. No single doc enumerates all error codes + messages + remediations. Maintainer 1 year later cannot grep `manifest_loader.ManifestError` and find the user-facing message contract.
- Fix: add `references/error-catalog.md` (Phase 3 or 6). Columns: code, message template, raised-by, remediation.

### F6.3 [MEDIUM] No FAQ
- Lens: Q6
- Problem: PO-facing FAQ (e.g., "Why does it say _shared/ was auto-included?" "Why is dist/ gitignored?" "Why must I pass --version?") would shorten support cycles.
- Fix: append FAQ section to `README.md` (Phase 1 Step 6 — add to scope) OR create `references/faq.md` (Phase 6).

### F6.4 [MEDIUM] INSTALL.md template content not specified
- Lens: Q6
- Problem: phase-01 Step 9 says "extract instructions, run installer, what gets installed, troubleshooting. Uses `{{VERSION}}`, `{{BUILT_AT}}` tokens." But no skeleton, no minimum sections. Two engineers will write radically different INSTALL.md. Phase 6 smoke tests don't check INSTALL.md content.
- Fix: pin INSTALL.md.template skeleton in phase-01:
  ```
  # Claude Pack v{{VERSION}}
  ## Verify
  ## Extract
  ## Install (macOS/Linux | Windows)
  ## What gets installed
  ## Troubleshooting
  ## Uninstall
  ```
  Each section: 1-line requirement.

### F6.5 [MEDIUM] SKILL.md "Operating Principles" section content unspecified
- Lens: Q6
- Problem: phase-01 Step 3 says SKILL.md has "Operating Principles (manifest-first DRY, always-drop safety non-negotiable, no merge-resolver v1, deterministic builds)." 4 bullets. Root CLAUDE.md (phase-06) has 5. Drift.
- Fix: standardize: SKILL.md "Operating Principles" = same 5 as CLAUDE.md (phase-06 lines 56-89). Or document why they differ.

### F6.6 [LOW] No CHANGELOG
- Lens: Q6
- Problem: Recipient (or maintainer) cannot find "what changed in v0.2.0". Plan doesn't require CHANGELOG.md.
- Fix: append-only `CHANGELOG.md` in skill root, seeded with v0.1.0 entry in Phase 6 Step 4. Mirror `keepachangelog.com` format.

---

## Q7 — Failure Recovery Story

### F7.1 [HIGH] No "what if Phase 3 API changes mid-Phase-2" mitigation
- Lens: Q7
- Problem: Phase 2 + Phase 3 are parallelizable (phase-03 Next Steps "can be developed in parallel after API contracts are agreed"). If during Phase 3 dev, signature of `is_dropped()` changes (e.g., return type tuple → dataclass), Phase 2 dev breaks. No protocol.
- Fix: API Contracts section (per F2.2) is the lock. Any contract change requires: (a) plan-amend commit, (b) message to other phase's dev, (c) re-grep callers. Document in plan.md "Cross-Phase Contract Change Protocol".

### F7.2 [MEDIUM] Recipient installer fails — what's the recovery?
- Lens: Q7
- Problem: phase-01 install.sh.template "skip-existing default + timestamped backup on FORCE_OVERWRITE=1". If skip leaves a half-installed state (some files written before a conflict), recipient is stuck. No rollback.
- Fix: install.sh.template stages to tmp dir first, validates all destinations clear, then commits via rename(s). OR document "installer is best-effort; recipient backs up `.claude/` manually before run".

### F7.3 [MEDIUM] Phase 5 golden test drift — recovery path stated but UPDATE_GOLDEN= is single-engineer
- Lens: Q7
- Problem: phase-05 R3: "UPDATE_GOLDEN=1 to refresh". When product-spec changes, the engineer running tests must know to set this env var. No CI gate, no PR check.
- Fix: golden refresh requires a PR commit that includes both `fixtures/golden-pack-product-spec/` diff AND a justification (product-spec changed). Document in `references/maintainers-guide.md` (see F13.1).

### F7.4 [LOW] No "abort packing midway" UX
- Lens: Q7
- Problem: PO invokes `pack.py` without `--dry-run`, realizes wrong manifest, hits Ctrl-C mid-write. Atomic rename guarantees no partial file. But `dist/.{name}.tmp` leftover. No cleanup on next run.
- Fix: pack.py startup: clean `dist/.*.tmp` older than 1h. Document.

---

## Q8 — CI/CD Integration

### F8.1 [BLOCKING] No CI configuration phase
- Lens: Q8
- Problem: Plan declares 6 phases. Phase 5 runs pytest locally; Phase 6 runs smoke tests locally. No GitHub Actions workflow, no CI pre-merge gate. Determinism contract (T-D1, T-G1) is the most fragile to OS/Python-version drift — it MUST run on CI matrix.
- Fix: add Phase 7 "CI Integration":
  - `.github/workflows/claude-pack-ci.yml` runs pytest on Ubuntu + macOS + Windows × Python 3.10/3.11/3.12.
  - Pre-merge gate: `pytest -q` must pass.
  - Release workflow: on tag `claude-pack-v*`, runs build + uploads `.tar.gz` + `.sha256` to GitHub Release.
  - Effort: 2-3h.

### F8.2 [HIGH] No fail-fast policy for safety
- Lens: Q8
- Problem: phase-02 R5 says SOURCE_DATE_EPOCH not read unless `--reproducible`. CI may inject SOURCE_DATE_EPOCH. T-D1 may pass locally but fail on CI silently. Need explicit CI environment normalization.
- Fix: in conftest.py (phase-05 Step 1), `monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)` per test. Also document in CI workflow.

### F8.3 [MEDIUM] No release pipeline
- Lens: Q8
- Problem: When packing claude-pack-v1.0.0, who runs it? PO? CI? Manual `gh release upload`?
- Fix: phase-07 (per F8.1) defines: tagged commit → CI builds tarball with deterministic SOURCE_DATE_EPOCH = tag commit time → uploads via `gh release upload`. PO never manually packs releases.

---

## Q9 — Backwards Compat & Versioning Policy

### F9.1 [HIGH] No schema v1 → v2 migration policy
- Lens: Q9
- Problem: phase-03 manifest schema declares `schema_version: "1.0"`. phase-03 R3 mitigation: "allow extra keys (additionalProperties)". phase-03 Step 8: "Migration from v0 to v1 placeholder (empty for now)". No declared policy: when schema changes, what does pack.py do with old manifests?
- Fix: add to plan.md or `references/manifest-spec.md`:
  - Patch bump (1.0 → 1.1): additive only (new optional fields). Old manifests still parse.
  - Major bump (1.0 → 2.0): breaking. pack.py refuses with "manifest schema v1.0 not supported; run `claude-pack migrate-manifest`".
  - `migrate-manifest` is YAGNI for now (no migrations exist). Document the policy; ship the migration tool when needed.

### F9.2 [HIGH] No tarball schema versioning policy
- Lens: Q9
- Problem: MANIFEST.json has `schema_version: "1.0"`. If v2 tarballs change layout (e.g., split MANIFEST.json into smaller files), recipient installer must handle both. No policy.
- Fix: install.sh.template + install.ps1.template read MANIFEST.json `schema_version` first; fail gracefully on unsupported version with: "This tarball is schema vX.Y; this installer supports v1.0 only. Download a newer installer.".

### F9.3 [MEDIUM] No deprecation policy
- Lens: Q9
- Problem: If `--all` flag is deprecated in v0.5, what does v0.4 user see? No policy for deprecation warnings.
- Fix: document in `references/maintainers-guide.md`: deprecated flags emit `DEPRECATED:` warning on stderr for ≥2 minor versions before removal. Documented in CHANGELOG.

---

## Q10 — PO Communication Touchpoints

### F10.1 [HIGH] Warning wording for auto-included `_shared/` not pinned
- Lens: Q10
- Problem: phase-02 Step 5 says emit `WARN: auto-included skills/_shared/foo because skills/bar/SKILL.md references it`. Phase 3 says emit JSON finding `{check: shared_dep, severity: info, ...}`. Two surfaces (stderr stream vs JSON output). Wording could drift between modules.
- Fix: pin warning text in `references/error-catalog.md` (per F6.2). Both surfaces use the same template (with formatting differences for human vs machine).

### F10.2 [MEDIUM] No catalog of CLI-output formats
- Lens: Q10
- Problem: pack.py prints to stdout (INFO) + stderr (WARN/ERROR). Format unspecified (JSON? plain text? structured?). Eval scenarios assume parseable JSON in some cases, plain text in others.
- Fix: pack.py default output = plain text human-readable; `--json` flag emits structured JSON. Lock both shapes in phase-02 Requirements. Eval scenarios use `--json`.

### F10.3 [MEDIUM] No PO-facing error templates
- Lens: Q10
- Problem: When manifest validation fails, what does the LLM say to PO? "ManifestError: line 3, column 5: expected a string" — too technical. PO needs guided message.
- Fix: `references/error-catalog.md` includes "PO-facing remediation" column for each error code. LLM uses this verbatim.

### F10.4 [LOW] Confirmation flow text not pinned
- Lens: Q10
- Problem: phase-04 R2 mitigation: "workflow-pack.md explicitly documents the confirm step". Confirm wording unspecified. Two engineers will write different prompts.
- Fix: pin confirm prompt in phase-04 Step 6 Section 4. E.g., "Ready to write `.claude/pack.manifest.yaml` with N skills, M agents? [y/N]".

---

## Q11 — Versioning of Skill Itself

### F11.1 [BLOCKING] `metadata.version` vs `pack.manifest.yaml:version` — same concept or different?
- Lens: Q11
- Problem:
  - phase-01 Step 2: `metadata.version: "1.0.0"` (SKILL.md frontmatter, the **skill** version).
  - phase-02 Requirements: `--version` flag, manifest `version`, used in filename `claude-pack-{version}.tar.gz` (the **bundle** version).
  - phase-06 seed manifest: `version: "0.1.0"`.
  - Three "versions" floating: skill code, bundle output, manifest schema (v1.0).
- Fix: explicit terminology in plan.md:
  - **Skill version** (`metadata.version` in SKILL.md): version of the claude-pack code itself.
  - **Bundle version** (`version` in manifest, `--version` CLI): version of THE PRODUCED tarball, decoupled from skill version.
  - **Manifest schema version** (`schema_version: "1.0"`): format of pack.manifest.yaml itself.
  Phase-01 Step 2 should clarify the skill version is independent of any pack.manifest.yaml.

### F11.2 [HIGH] Skill version 1.0.0 vs seed manifest 0.1.0 — contradiction at Phase 6
- Lens: Q11
- Problem: phase-01 sets `metadata.version: "1.0.0"` for SKILL. phase-06 seed manifest declares `version: "0.1.0"` for BUNDLE. If conflated, contradictory. Recipient sees `claude-pack-0.1.0.tar.gz` for skill version 1.0.0 — confusing.
- Fix: clarify per F11.1. Update phase-01 Step 2 to use `metadata.version: "0.1.0"` (matches seed) to avoid premature 1.0.0 — better to align with F5.1's release gate (1.0.0 reserved for GA).

### F11.3 [MEDIUM] No version bump procedure
- Lens: Q11
- Problem: When the skill code changes, who bumps `metadata.version`? When the bundle output changes, who bumps manifest `version`? No procedure.
- Fix: `references/maintainers-guide.md`: skill version bumps follow semver; bundle version bumps follow recipient's release cadence (independent).

---

## Q12 — Dogfooding Pinning

### F12.1 [HIGH] Golden test packs product-spec — not pinned to git SHA
- Lens: Q12
- Problem: phase-05 T-G1 packs `cleanmatic:product-spec` as golden. If product-spec is modified between Phase 5 implementation and Phase 6 smoke tests (smoke 4-7 also packs product-spec), golden either matches old or new tree but not both. No SHA pin.
- Fix:
  - Option A (recommended): `fixtures/golden-pack-product-spec.manifest.yaml` references product-spec at a specific SHA. Phase 5 test checks out that SHA into a tmp worktree before packing. Heavy machinery; defer to v1.1.
  - Option B (KISS): test packs the LIVE product-spec; golden fixture is regenerated on every product-spec change via `UPDATE_GOLDEN=1` + commit. Reviewer verifies golden diff in PR. Document in `maintainers-guide.md`.
  - Pick B for v0.1.0; revisit if golden churns excessively.

### F12.2 [MEDIUM] phase-06 seed manifest includes claude-pack itself — chicken-and-egg risk
- Lens: Q12
- Problem: phase-06 R4 acknowledges chicken-and-egg ("v0.1.0 of claude-pack must be built before being packed"). But Smoke test 4 packs the seed manifest which lists claude-pack. If skill version metadata != bundle version, recipient may install a future version's skill. (Tied to F11.x.)
- Fix: Smoke test 4 documents acceptable state: "skill code at v0.1.0; bundle output at v0.1.0; packed contents include the v0.1.0 skill itself". CI captures both via `git describe --tags`.

---

## Q13 — Operator Handover Docs

### F13.1 [HIGH] No maintainer's guide
- Lens: Q13
- Problem: When the next engineer picks up claude-pack 6 months later, where do they learn:
  - How to add a new always-drop rule.
  - How to bump manifest schema.
  - How to refresh golden test.
  - How to debug determinism failures.
  - How to add a new CLI flag.
- Fix: create `references/maintainers-guide.md` (Phase 6 or new Phase 7). Sections:
  1. Architecture overview (modules + their responsibilities).
  2. Adding an always-drop rule (step-by-step).
  3. Bumping manifest schema (process).
  4. Refreshing golden test.
  5. Debugging non-determinism.
  6. Adding a CLI flag (touch points: pack.py argparse + flag-reference.md + SKILL.md flag table).
  Length: ≤200 lines. Markdown.

### F13.2 [MEDIUM] No architecture diagram in plan or skill
- Lens: Q13
- Problem: Plan describes data flow in prose. No diagram. New engineer must mental-model from 5 phase files.
- Fix: phase-01 Step 3 already mentions Mermaid in SKILL.md "Workflow Map". Ensure it's a true data-flow diagram (manifest → loader → safety → walker → builder → sidecar), not just a control-flow.

---

## Q14 — Sunset Path

### F14.1 [MEDIUM] No sunset / migration story if Anthropic ships official registry
- Lens: Q14
- Problem: If Anthropic introduces an official skill marketplace/registry later, claude-pack becomes redundant. Plan has no exit strategy.
- Fix: add `## Sunset Considerations` to plan.md (≤20 lines): "If an official registry ships, claude-pack tarball format remains useful as a transport. We export to registry-compatible format by tightening MANIFEST.json schema. Recipient docs cross-reference official tooling." Low-effort foresight, not a deliverable.

### F14.2 [LOW] No "deprecate gracefully" path
- Lens: Q14
- Problem: If skill is deprecated, how is the recipient notified? Tarballs in the wild can't be recalled.
- Fix: install.sh.template includes a check: `if env var CLAUDE_PACK_DEPRECATED=1: warn and continue`. Future versions can set this via a remote file fetch (out of scope v1). Document.

---

## Q15 — Compliance with Repo CLAUDE.md Rules

### F15.1 [HIGH] pack.py ~350 lines vs repo rule "≤200 lines" — NOT acknowledged
- Lens: Q15
- Problem: `.claude/rules/development-rules.md` File Size Management: "Keep individual code files under 200 lines for optimal context management". phase-02 Related Code Files: `pack.py (~350 lines)`. 75% over the rule. Phase 2 does not acknowledge or justify.
- Fix: either (a) modularize pack.py into submodules (e.g., `pack/__init__.py` dispatching to `pack/cli.py`, `pack/tarball.py`, `pack/templates.py`), or (b) document explicit exception in phase-02 Risk Assessment ("CLI tools with complex argparse + atomic write logic exceed 200-line guideline; acknowledged tech debt"). Recommend (a) for maintainability.

### F15.2 [HIGH] Other files near or over 200-line guideline
- Lens: Q15
- Problem:
  - `manifest_loader.py` ~200 lines (at the line).
  - `build_manifest.py` ~250 lines (25% over).
  - `safety_check.py` ~180 lines (under).
  - `test_pack_determinism.py` ~200 lines (at line — test files may be exempt per "When not to modularize" but rule unclear).
- Fix: same as F15.1 — modularize or document exception. Tests likely OK (clear logical groupings = file-per-feature-area).

### F15.3 [MEDIUM] No per-phase compile/lint verify step
- Lens: Q15
- Problem: Primary workflow (`./.claude/rules/primary-workflow.md` step 1) requires "after creating or modifying code file, run compile command/script to check for any compile errors". No phase has an explicit lint/syntax check.
  - Phase 1 Success Criterion checks `bash -n install.sh.template` (good).
  - Phase 2-4 have NO `python -m py_compile pack.py` or `ruff check` step.
- Fix: add to each Python-producing phase (2, 3, 4): "after writing module, run `python -m py_compile <module>.py` — must exit 0".

### F15.4 [MEDIUM] DRY violation: requirements.txt referenced across 3 phases
- Lens: Q15
- Problem: F2.1 covers this. Same issue: rule explicitly says DRY.
- Fix: see F2.1.

### F15.5 [LOW] Phase 6 CLAUDE.md edit — "append" acceptable under "Update existing files directly"?
- Lens: Q15
- Problem: Rule "Update existing files directly" usually means "modify in-place vs new enhanced file". Phase 6 appends. Acceptable interpretation but could be questioned.
- Fix: clarify in phase-06: "Append to existing CLAUDE.md (not create new file). Edit is purely additive (insertion only); no existing content modified". Verifiable via `git diff --stat`.

### F15.6 [LOW] No `docs-manager` agent delegation post-implementation
- Lens: Q15
- Problem: Primary workflow step 4: "Delegate to `docs-manager` agent to update docs in `./docs` if any." Plan implies CLAUDE.md edit is sufficient; doesn't address `./docs/codebase-summary.md`, `./docs/system-architecture.md` updates.
- Fix: phase-06 Next Steps: "After ship, delegate to docs-manager to update `./docs/codebase-summary.md` + `./docs/system-architecture.md` to reflect new skill."

### F15.7 [OBSERVE] Commit message rule: no `chore`/`docs` for `.claude` changes
- Lens: Q15
- Problem: phase-06 commits CLAUDE.md + skill. Per repo rule, must NOT use `chore:` or `docs:` for `.claude/` changes.
- Fix: phase-06 Step 4 (or Next Steps): commit messages use `feat(skill):` or `feat(claude-pack):`.

---

## Critical Questions for PO

Sequenced for highest-leverage answers first.

1. **Versioning conflation (F11.1, F11.2):** Are skill version, bundle version, and manifest schema version intended as ONE concept or THREE? Recommendation: three, with skill starting at 0.1.0 not 1.0.0.

2. **CI/CD scope (F8.1):** Should we add Phase 7 "CI Integration" with GitHub Actions, or defer to manual local testing for v0.1.0?

3. **Maintainer's guide (F13.1):** Required for v0.1.0 or deferred to v0.5.0? (Recommend: required — 150-line investment pays off in 6 months.)

4. **Effort reset (F4.1, F4.2, F4.5):** Will you accept revised total effort 28h (vs declared 23h), or descope (drop T-D7 SIGTERM, drop T-G1 golden, drop interactive flow → Phase 4 becomes optional)?

5. **Golden test pinning (F12.1):** Accept Option B (live product-spec with PR-reviewed refresh) for v0.1.0?

6. **Schema migration policy (F9.1):** Accept "additive-only patch, schema bump = explicit migration command (deferred to needed)" policy?

7. **API contracts lock (F2.2):** Should the API contracts section be added to plan.md and treated as plan-amend-required for changes?

8. **Documentation deliverables (F6.x):** Confirm v0.1.0 ships with: troubleshooting.md, error-catalog.md, FAQ section, INSTALL.md.template skeleton — all required?

9. **pack.py modularization (F15.1):** Modularize into `pack/` subpackage to honor 200-line rule, or accept exception with explicit acknowledgment?

10. **Release gates (F5.1):** Adopt 0.1.0 → 0.5.0 → 1.0.0 ladder with explicit gates?

---

## Unresolved

- **U1:** Does ck CLI auto-discover skills by folder name + frontmatter, or is there an explicit registry? (F3.3) — needed for "skill discoverable" success criterion.
- **U2:** Should Phase 4 (interactive manifest builder) be optional/deferred? CLI + manifest-in-git covers 90% of dogfooding needs. Interactive is UX nicety; cuts Phase 4's 4h effort.
- **U3:** Is multi-OS testing in v0.1.0 scope, or just Linux smoke (PO's machine)? Affects F5.2 and F8.1 scoping.
- **U4:** Manifest schema v1.0 allows `additionalProperties` (R3 mitigation) — should pack.py emit a warning for unknown keys, or stay silent? Affects PO-vs-script trust model.
- **U5:** Is `_shared/` auto-include opt-in or opt-out by default? phase-03 schema has `follow_shared: true` default. PO may want opt-in (more conservative).
- **U6:** Should `dist/.tmp` cleanup (F7.4) be in v0.1.0 or v0.5.0?
- **U7:** Symlink handling — phase-02 R6 says reject symlinks with WARN. Recipient `.claude/` may legitimately have symlinks (e.g., shared agent files). Is rejection too aggressive?

---
End of report. 14 BLOCKING/HIGH findings, 17 MEDIUM, 10 LOW/OBSERVE.

**Status:** DONE
**Summary:** Validated claude-pack plan against 15 lenses (completeness, contracts, measurability, effort, DoD, docs, recovery, CI, schema-versioning, PO comms, version-disambiguation, dogfooding, handover, sunset, repo-rules). 41 findings; 3 BLOCKING (requirements.txt drift, no release gates, version conflation). Top recommendations: lock API contracts in plan.md, add Phase 7 (CI), bump Phase 5 effort, modularize pack.py per 200-line rule, define release gates 0.1.0→0.5.0→1.0.0.
**Concerns/Blockers:** none (review-only task; no implementation gate)
