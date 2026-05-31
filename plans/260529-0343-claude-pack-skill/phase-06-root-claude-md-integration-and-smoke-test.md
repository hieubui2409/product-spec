---
phase: 6
title: "Root CLAUDE.md Integration and Smoke Test"
status: pending
priority: P1
effort: "4h"
dependencies: [2, 3, 4, 5]
---

# Phase 6: Root CLAUDE.md Integration and Smoke Test

## Overview

Final integration: append `# Claude Pack — LLM Operating Guide` section to repo-root `CLAUDE.md` with **HTML comment markers** (red-team F11.1) for future-safe idempotent updates, create the 3 new docs (`troubleshooting.md`, `maintainers-guide.md`, FAQ in README), generate the seed `.claude/pack.manifest.yaml` via `build_manifest.py --write` (NOT hand-written per validate F2.4), back-port `--dev` flag pattern to `product-spec/install.sh` (R3.Q10 side-effect), update `.gitignore`, run 7 smoke tests end-to-end.

This phase makes the skill discoverable + invocable in real workflows.

## Context Links

- Plan `## Release Gates` — 0.1.0 gate criteria (all 7 phases done, smoke 7 green, dogfood product-spec)
- Plan `## Cross-Phase Artifact Mutations` — product-spec install.sh retrofit documented
- Researcher B Q8 (root CLAUDE.md integration)
- Red-team F11.1 (HTML markers), F6.1 (installer version-awareness already in Phase 1)
- Validate F1.6 (smoke idempotency), F2.4 (seed via build_manifest), F6.1+F6.2+F6.3 (docs), F13.1 (maintainer's guide), F15.6 (docs-manager), F15.7 (commit message convention)
- Existing convention: root `CLAUDE.md` Product Spec section (lines 1-134)

## Requirements

**Functional:**
- Root `CLAUDE.md` gets new section `# Claude Pack — LLM Operating Guide`, wrapped in HTML markers `<!-- BEGIN: cleanmatic:claude-pack operating guide -->` / `<!-- END: cleanmatic:claude-pack operating guide -->` for future idempotent updates
- Section ≤80 lines, mirrors product-spec convention
- 5 Operating Principles match SKILL.md verbatim (validate F6.5; single source-of-truth = root CLAUDE.md, SKILL.md cross-references)
- `.gitignore` gets `/dist/` (leading slash anchors repo root, red-team F11.1)
- 3 new docs:
  - `references/troubleshooting.md` (≤60 lines, ≥5 common failures, validate F6.1)
  - `references/maintainers-guide.md` (≤200 lines, validate F13.1)
  - `README.md` FAQ section (≥4 questions, validate F6.3)
- `.claude/pack.manifest.yaml` (seed manifest) generated via `build_manifest.py --write` with prepared answers JSON (validate F2.4 — dogfood the skill)
- `.claude/skills/product-spec/install.sh` retrofitted with `--dev` flag (R3.Q10): split into `requirements.txt` (runtime) + `requirements-dev.txt` (pytest)
- 7 smoke tests end-to-end pass

**Non-functional:**
- CLAUDE.md edit is **append-only**: `git diff CLAUDE.md` shows only insertions; no existing content modified (validate F15.5).
- Commit messages use `feat(claude-pack):` or `feat(skill):` — NEVER `chore:` or `docs:` for `.claude/` changes (validate F15.7).
- After Phase 6: delegate to `docs-manager` agent to update `./docs/codebase-summary.md` + `./docs/system-architecture.md` (validate F15.6).

## Architecture

### Root CLAUDE.md section content (LOCKED, ≤80 lines)

```markdown
<!-- BEGIN: cleanmatic:claude-pack operating guide -->

# Claude Pack — LLM Operating Guide

Auto-loaded by Claude Code. Tells you (the LLM) how to operate the
`cleanmatic:claude-pack` skill on behalf of the developer who installed it.

This skill is **developer-facing** (technical), unlike `cleanmatic:product-spec`
which is PO-facing. Use code/CLI vocabulary freely.

## Five Operating Principles

### 1. Manifest is the source-of-truth
`.claude/pack.manifest.yaml` declares build inputs. CLI flags override per-build;
interactive mode regenerates the manifest. Three input surfaces, one resolver
(`manifest_loader.merge_cli`).

### 2. Safety filter is non-negotiable
`safety_check.is_dropped` enforces the always-drop catalog: `.env`/`.envrc`/
secrets/keys, `.git/`, runtime caches, session state. NOT removable via any
flag. `settings.json` + `.ck.json` are opt-in only (`--include-settings`,
`--include-ck-config`).

### 3. Determinism is a contract
Same source + manifest → byte-identical tar.gz. Knobs: PAX, sorted walk
(file-granular), mtime=0 default, uid/gid=0, gzip mtime=0.
`--source-date-epoch` opt-in honors env var.

### 4. Script vs LLM split (non-negotiable)
| Layer | Owns |
|-------|------|
| Scripts | manifest parse, dep grep, safety check, deterministic tarball write |
| LLM | AskUserQuestion interactive flow, summary, confirmation gating |

Scripts NEVER call AskUserQuestion. LLM NEVER edits the tarball directly.

### 5. No auto-install on recipient
v1 ships tarball + bundled installer + `INSTALL.md`. Recipient runs installer
manually. Merge-resolver is out of scope. Installer skip-existing default with
optional `FORCE_OVERWRITE=1` backup; version-aware (STALE/NEWER/OK SAME).

## Script CLI Contract

All scripts under `.claude/skills/claude-pack/scripts/`. Run via shared venv:

    ./.claude/skills/.venv/bin/python3 -m pack [flags]

Or other modules:

    ./.claude/skills/.venv/bin/python3 .claude/skills/claude-pack/scripts/<module>.py

| Script | Purpose |
|--------|---------|
| `pack/` (subpackage) | Build the tarball |
| `safety_check.py` | Walk subtree, emit warn/info findings |
| `manifest_loader.py` | Parse + validate + resolve manifest |
| `build_manifest.py` | Discover + emit questions + write manifest |

Exit codes: 0 success · 1 validation · 2 strict-gate · 3 collision · 4 write
error · 5 empty/oversize · 130 SIGINT.

## Output Layout

    dist/
    ├── claude-pack-{version}.tar.gz
    └── claude-pack-{version}.tar.gz.sha256

Tarball internal (versioned root dir): `MANIFEST.json` + `INSTALL.md` +
`install.sh` + `install.ps1` + `.claude/...`.

`dist/` is gitignored. Recipient verifies SHA256, extracts, runs installer.

## When to Ask vs Assume

Default: AskUserQuestion when invoked without manifest + without CLI flags.
Acceptable to assume only when:
- Manifest exists at `.claude/pack.manifest.yaml` (use as-is, show summary)
- All required CLI flags provided
- Dry-run requested

Never assume:
- Bundle version (refuse `0.0.0-dev` for tagged releases)
- Inclusion of `settings.json`/`.ck.json` (require explicit opt-in flag)
- Overwrite of existing tarball (require `--force`)

## Failure & Drift Handling

- Manifest parse error → `ManifestError` finding; surface to user.
- Missing skill → `selection_missing` finding; abort.
- Safety drop in explicit `extra` listing → `WARN`, drop, continue.
- Mid-build crash → atomic `os.replace` guarantees no partial `.tar.gz`;
  `tmp` files cleaned on next startup.
- See `references/error-catalog.md` for full error → remediation map.

<!-- END: cleanmatic:claude-pack operating guide -->
```

## Related Code Files

**Modify:**
- `/home/hieubt/Documents/cleanmatic-skills/CLAUDE.md` — append guarded section
- `/home/hieubt/Documents/cleanmatic-skills/.gitignore` — add `/dist/`
- `/home/hieubt/Documents/cleanmatic-skills/README.md` (if exists at root) — one-line bullet pointing to skill
- `/home/hieubt/Documents/cleanmatic-skills/.claude/skills/claude-pack/README.md` — fill FAQ section (Phase 1 left placeholder)
- **`/home/hieubt/Documents/cleanmatic-skills/.claude/skills/product-spec/install.sh`** — back-port `--dev` flag pattern (R3.Q10)
- **`/home/hieubt/Documents/cleanmatic-skills/.claude/skills/product-spec/scripts/requirements.txt`** — split out pytest into `requirements-dev.txt`
- `.claude/skills/claude-pack/CHANGELOG.md` — fill `[0.1.0]` entry

**Create:**
- `/home/hieubt/Documents/cleanmatic-skills/.claude/pack.manifest.yaml` — seed via `build_manifest.py --write`
- `.claude/skills/claude-pack/references/troubleshooting.md` (≤60 LOC, ≥5 failure → fix entries)
- `.claude/skills/claude-pack/references/maintainers-guide.md` (≤200 LOC, 6 sections)
- `.claude/skills/product-spec/scripts/requirements-dev.txt` (new; pytest>=7,<9 + pytest-cov)

## Implementation Steps

### CLAUDE.md integration

1. **Read existing CLAUDE.md** to find the end. If marker `<!-- END: cleanmatic:product-spec operating guide -->` exists (added retroactively by a future plan), append after it. Otherwise, append at EOF.

2. **Apply marker pair** — `<!-- BEGIN: cleanmatic:claude-pack operating guide -->` + section content (≤80 lines) + `<!-- END: cleanmatic:claude-pack operating guide -->`. Idempotent: future updates detect markers + replace in-place.

3. **Append-only check** — after edit, run `git diff --stat CLAUDE.md` and verify only insertions (no `-` lines outside the new block).

### .gitignore

4. **Edit `.gitignore`** — add `/dist/` (leading slash anchors repo root only, red-team F11.1). If `dist/` already present, normalize to `/dist/`.

### Seed manifest (via build_manifest.py — DOGFOOD)

5. **Prepare answers JSON** — write `/tmp/seed-answers.json`:
   ```json
   {
     "version": "0.1.0",
     "bundle_name": "claude-pack",
     "skills": ["product-spec", "claude-pack"],
     "agents": ["planner", "researcher"],
     "hooks": [],
     "rules": ["primary-workflow.md", "development-rules.md", "orchestration-protocol.md",
               "documentation-management.md", "review-audit-self-decision.md",
               "team-coordination-rules.md", "skill-domain-routing.md",
               "skill-workflow-routing.md"],
     "extra": [],
     "top_level": {
       "include_readme": true,
       "include_claudemd": true,
       "include_settings": false,
       "include_ck_config": false
     },
     "defaults": {"include_scripts": true, "include_schemas": true},
     "follow_shared": false
   }
   ```

6. **Run dogfood write** — `cat /tmp/seed-answers.json | ./.claude/skills/.venv/bin/python3 .claude/skills/claude-pack/scripts/build_manifest.py --write --out .claude/pack.manifest.yaml --root .`
   - Verify exit 0
   - Verify YAML matches canonical order + header comment

### Docs deliverables

7. **`references/troubleshooting.md`** — ≤60 LOC. ≥5 entries:
   - **SHA256 mismatch on download** → recipient: re-download; verify integrity
   - **Missing `pyyaml`** → recipient: run installer; if `--dev`, ensure venv active
   - **`install.sh` permission denied** → recipient: `chmod +x install.sh` or `bash install.sh`
   - **Symlink rejected during pack** → maintainer: review WARN; symlinks unsupported by design
   - **`absolute paths not allowed` validate error** → user: convert manifest `extra` paths to repo-relative
   - **`refuse 0.0.0-dev` validate error** → user: set semver `version` or pass `--allow-dev-version`

8. **`references/maintainers-guide.md`** — ≤200 LOC. 6 sections:
   1. Architecture overview (data flow + module responsibilities) — 1 mermaid diagram
   2. Adding a new always-drop rule (step-by-step, code change in `safety_check.py`)
   3. Bumping manifest schema (additive vs breaking, schema_version policy)
   4. Refreshing golden test (`UPDATE_GOLDEN=1 pytest -m integration && commit`)
   5. Debugging non-determinism (verify gzip mtime byte; check `SOURCE_DATE_EPOCH`; reproduce on CI matrix)
   6. Adding a CLI flag (touch points: `pack/cli.py` argparse + `flag-reference.md` + SKILL.md flags table)

9. **`README.md` FAQ section** — fill from Phase 1 placeholder. ≥4 questions:
   - "Why is `dist/` gitignored?" — outputs are reproducible; commit on tag only
   - "Why must I pass `--version`?" — bundle version decoupled from skill version; release ladder
   - "Why is `_shared/` warn-only?" — false-positive risk from doc code blocks
   - "How do I bundle for Windows recipients?" — `install.ps1` ships; install.sh.template version-detection works on PowerShell

10. **CHANGELOG.md `[0.1.0]` entry** — list the actual changes (Added: skill scaffold, pack/ subpackage, safety_check, manifest_loader, build_manifest, eval suite, CI pipeline. Notes: warn-only `_shared/` policy; cross-platform pack.py).

### Product-spec retrofit (R3.Q10 side effect)

11. **Create `product-spec/scripts/requirements-dev.txt`** — `pytest>=7,<9\npytest-cov\n` (mirror claude-pack pattern).

12. **Edit `product-spec/scripts/requirements.txt`** — leave only runtime deps (`pyyaml>=6.0,<7`). Remove pytest line if present.

13. **Edit `product-spec/install.sh`** — apply `--dev` flag pattern. Pseudo-diff:
    ```bash
    # detect --dev
    DEV=0
    for arg in "$@"; do [[ "$arg" == "--dev" ]] && DEV=1; done
    # ... existing venv setup ...
    "$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/scripts/requirements.txt"
    if [[ "$DEV" == "1" ]]; then
      "$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/scripts/requirements-dev.txt"
    fi
    ```
    Maintain backward compat: `./install.sh` (no flag) still works, just without pytest now.

14. **Document retrofit in product-spec/CHANGELOG.md** (if exists; if not, add a note to plan's commit message).

### Smoke tests (7 tests, sequential)

15. **Smoke 1 — install** — `./.claude/skills/claude-pack/install.sh --dev`; exit 0; `.venv/bin/python -c "import yaml, pytest"` succeeds.

16. **Smoke 2 — pytest** — `./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/claude-pack/scripts/tests/ -m "not integration" -q`; all green.

17. **Smoke 3 — discovery** — `python -m pack.cli ...` (or `build_manifest.py --discover --root .`); JSON shows `product-spec`, `claude-pack` in `available_skills`.

18. **Smoke 4 — dry-run pack** — `python -m pack --manifest .claude/pack.manifest.yaml --version 0.1.0 --dry-run`; file list printed, no file created. Then `--dry-run --compute-sha`; SHA matches subsequent real-run SHA.

19. **Smoke 5 — real pack** — `python -m pack --manifest .claude/pack.manifest.yaml --version 0.1.0`; `dist/claude-pack-0.1.0.tar.gz` + `.sha256` exist; `sha256sum -c dist/claude-pack-0.1.0.tar.gz.sha256` reports `OK`.

20. **Smoke 6 — extract + verify** — `mkdir /tmp/cp-test && tar -xzf dist/claude-pack-0.1.0.tar.gz -C /tmp/cp-test`; `jq .schema_version /tmp/cp-test/claude-pack-0.1.0/MANIFEST.json` → `"1.0"`; `bash -n /tmp/cp-test/claude-pack-0.1.0/install.sh` exits 0; `pwsh -NoProfile -Command "Get-Content /tmp/cp-test/claude-pack-0.1.0/install.ps1" > /dev/null` if pwsh available.

21. **Smoke 7 — sandbox install + idempotency** — 
    - `mkdir /tmp/cp-recipient && cd /tmp/cp-recipient && bash /tmp/cp-test/claude-pack-0.1.0/install.sh`
    - Verify `/tmp/cp-recipient/.claude/skills/product-spec/SKILL.md` exists
    - **Idempotency check (validate F1.6):** re-run installer; assert second run reports `[SKIP]` for all existing files; exits 0; no overwrites

22. **Determinism re-run** — run Smoke 5 second time; `sha256sum dist/*.tar.gz` matches first run (byte-identical).

### Post-implementation

23. **Delegate to docs-manager** (validate F15.6) — invoke `docs-manager` agent to update `./docs/codebase-summary.md` + `./docs/system-architecture.md` with claude-pack reference.

24. **Commit** — use `feat(claude-pack):` prefix; never `chore:`/`docs:` for `.claude/` changes (validate F15.7).

## Success Criteria

- [ ] Root `CLAUDE.md` has `<!-- BEGIN: cleanmatic:claude-pack operating guide -->` + section + `<!-- END: ... -->` markers
- [ ] Section ≤80 lines (`awk '/BEGIN: cleanmatic:claude-pack/,/END: cleanmatic:claude-pack/' CLAUDE.md | wc -l` ≤ 82)
- [ ] `git diff --stat CLAUDE.md` shows only insertions (no deletions outside the new block)
- [ ] 5 Operating Principles in CLAUDE.md match SKILL.md verbatim (`diff <(awk '/Operating Principles/,/## Script/' CLAUDE.md) <(awk '/Operating Principles/,/## Script/' .claude/skills/claude-pack/SKILL.md)` matches modulo formatting)
- [ ] `.gitignore` contains `/dist/` (`grep -q '^/dist/' .gitignore`)
- [ ] `.claude/pack.manifest.yaml` exists + valid (loads via `manifest_loader.load` + `validate` returns `[]`)
- [ ] Seed manifest generated via `build_manifest.py --write` (NOT hand-edited; `grep -c "Generated by cleanmatic:claude-pack" .claude/pack.manifest.yaml == 1`)
- [ ] `references/troubleshooting.md` exists, ≥5 entries, ≤60 lines
- [ ] `references/maintainers-guide.md` exists, 6 sections, ≤200 lines
- [ ] `README.md` FAQ has ≥4 questions
- [ ] `CHANGELOG.md` `[0.1.0]` entry filled
- [ ] `product-spec/scripts/requirements.txt` no longer contains pytest
- [ ] `product-spec/scripts/requirements-dev.txt` exists with `pytest>=7,<9 + pytest-cov`
- [ ] `product-spec/install.sh` supports `--dev` flag (test: `./product-spec/install.sh --dev` installs pytest; `./product-spec/install.sh` does NOT)
- [ ] Smoke 1-7 all pass
- [ ] Smoke 7 idempotency: second installer run reports all `[SKIP]`
- [ ] Determinism re-run: Smoke 5 second run produces byte-identical SHA256
- [ ] docs-manager agent ran + updated `./docs/codebase-summary.md` and `./docs/system-architecture.md`
- [ ] Commit messages use `feat(claude-pack):` prefix

## Risk Assessment

- **R1: CLAUDE.md markers conflict with future plan** — Mitigation: marker pair is unique enough; future plans can detect + nest if needed.
- **R2: Smoke 7 sandbox install clobbers tester's real `.claude/`** → Use `/tmp/cp-recipient/` only; never `$HOME/.claude/`. Documented in commit message.
- **R3: `.gitignore` `/dist/` swallows unrelated dist/ folder** → Leading slash anchors to repo root only; subdirectories' `dist/` unaffected.
- **R4: Self-referencing seed manifest packs claude-pack v0.1.0 before it's "released"** → Intentional dogfood per phase-02:R4. Smoke 7 ships v0.1.0 contents; CI captures `git describe --tags`.
- **R5: Product-spec retrofit breaks existing product-spec workflow** → Backward compat: `./install.sh` (no flag) still works, just installs runtime deps only. Existing product-spec tests run via `--dev`. Document in commit body.
- **R6: User runs Smoke 7 without backup of their `.claude/`** → Smoke 7 explicitly uses `/tmp/cp-recipient/`; tester must NOT replace `$HOME` arg.
- **R7: docs-manager agent unavailable / fails** → If agent fails, manual edit `./docs/codebase-summary.md` + `./docs/system-architecture.md`; document in commit body.

## Security Considerations

- Seed `.claude/pack.manifest.yaml` is committed; must never reference `.env` or include `settings.json`. Confirm by validating + grep before commit.
- Smoke 7 runs BUNDLED installer inside `/tmp` — never against developer's real environment.
- CLAUDE.md change is reviewable; commit it in a dedicated commit (separate from skill code commit) for clean diff.
- Product-spec retrofit is a deliberate scope expansion; commit message + plan.md document it.

## Next Steps

- Phase 7 (CI Integration) consumes the Smoke 5 + 7 outputs as CI sanity checks.
- After Phase 6 green: trigger `/ck:journal` to write technical journal entry per primary-workflow Step 6.
- After Phase 7 green: tag `claude-pack-v0.1.0` → CI release pipeline builds + uploads to GitHub Releases.
- Release ladder gate: 0.1.0 dogfood done; 0.5.0 awaits multi-OS recipient testing.
