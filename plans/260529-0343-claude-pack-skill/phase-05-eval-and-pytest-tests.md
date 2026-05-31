---
phase: 5
title: "Eval and Pytest Tests"
status: pending
priority: P1
effort: "8h"
dependencies: [2, 3, 4]
---

# Phase 5: Eval and Pytest Tests

## Overview

Three test layers (effort bumped 5h → 8h per validate F4.1; covers 17 base tests + 12 new edge-case tests from red-team findings + golden split):

1. **`scripts/tests/`** — pytest unit + integration tests. Strong determinism gate (byte-identical SHA256). HARD safety enforcement (every CRITICAL finding from red-team has a test). YAML round-trip property tests for manifest.
2. **`eval/evals.json`** — scenario-based grader eval (3 scenarios, mirror product-spec).
3. **Golden split** (R3.Q3): synthetic minimal fixture (BLOCKING unit test) + live product-spec (`pytest -m integration`, NON-blocking on CI). Decouples claude-pack CI from product-spec edits.

Also creates `scripts/requirements-dev.txt` (split from runtime per R3.Q10) and updates `install.sh` for `--dev` flag handling.

## Context Links

- Plan `## API Contracts` + `## Cross-Phase Artifact Mutations` — locked
- Researcher A Q5 (dual-layer test strategy)
- Researcher B Q5 (eval pattern from product-spec)
- Red-team CRITICAL fixes: F2.1, F4.5, F14.2 — every fix gets a verifying test
- Validate report: F1.2, F1.4, F1.6, F4.1, F9.1, F12.1
- Convention: `.claude/skills/product-spec/eval/evals.json`, `product-spec/scripts/tests/`

## Requirements

### Test inventory (29 tests total — was 17, +12 new)

| ID | Module | Asserts | Origin |
|----|--------|---------|--------|
| T-D1 | pack | Two consecutive runs produce byte-identical tar.gz | Original |
| T-D2 | pack | Tarball has versioned root dir | Original |
| T-D3 | pack | MANIFEST.json schema_version=1.0 with per-file SHA256 | Original |
| T-D4 | pack | Gzip header `data[4:8] == b"\x00\x00\x00\x00"` (0-indexed slice) | Red-team F1.4 |
| T-D5 | pack | All tar entries have uid/gid=0, uname/gname=empty, mode=0o644/0o755 | Original |
| T-D6 | pack | `--dry-run --compute-sha` returns same SHA as real run | Original |
| T-D7a | pack | Mock `tarfile.open` to raise mid-write → no final tarball; `.tmp` cleaned | Red-team F9.1 split |
| T-D7b | pack | `PACK_KILL_AFTER_N_FILES=3` env var → subprocess exits non-zero; final does NOT exist | Red-team F9.1 split |
| T-D8 | pack | Empty selection → exit 5 with "nothing to pack" | Red-team F13.1 |
| T-D9 | pack | `--max-size 1000` against 10KB pack → exit 5 | Red-team F14.1 |
| T-D10 | pack | Symlink in selection → dropped + WARN | Red-team F1.3 |
| T-D11 | pack | Two-run determinism across Python 3.11/3.12/3.13 (Phase 7 CI matrix) | Red-team F1.5 |
| T-D12 | pack | Unknown template token `{{XYZ}}` → exit 1 `TemplateError` | Red-team F17.3 |
| T-D13 | pack | Output collision: 2nd run no `--force` → exit 3 | Original / new gate |
| T-D14 | pack | `--force` renames existing to `.bak.{epoch}` before write | Original / new gate |
| T-D15 | pack | tmp file >1h old in `dist/` cleaned on startup | Validate F7.4 |
| T-D16 | pack | `pack/` subpackage: each `.py` file <200 LOC | R3.Q4 modularization |
| T-S1 | safety | `is_dropped(".env")` true | Original |
| T-S2 | safety | `is_dropped("__pycache__/x.pyc")` true | Original (extended: deep nesting) |
| T-S3 | safety | `is_dropped("docs/dev.md")` false | Original |
| T-S4 | safety | Hard safety: `.env` in `extra` STILL dropped | Original |
| T-S4b | safety | Transitive: `.env` inside packed skill `.claude/skills/foo/.env` dropped | Red-team F9.2 |
| T-S5 | safety | `find_shared_refs` strips code blocks before regex | Red-team F5.1 |
| T-S6 | safety | `is_dropped(".envrc")`, `id_rsa`, `secrets.json`, `*.pem` all true | Red-team F2.1 CRITICAL |
| T-S7 | safety | `is_dropped(".git/HEAD")` true | Red-team F14.2 CRITICAL |
| T-S8 | safety | `is_dropped(".envfoo")` false (no substring FP) | Red-team F2.6 |
| T-S9 | safety | `find_shared_refs` emits `shared_dep_missing` for stale ref | Red-team F5.3 |
| T-M1 | loader | `load` example.yaml returns valid dict | Original |
| T-M2 | loader | `validate` catches bad semver, non-list, duplicates, unknown top-level | Original (+red-team F4.3, F4.6) |
| T-M3 | loader | `merge_cli(skills="foo,bar")` replaces + dedupes | Original |
| T-M3b | loader | `merge_cli` boolean with `BooleanOptionalAction(None)` keeps manifest | Red-team F17.2 |
| T-M4 | loader | `apply_defaults` auto-adds `scripts/`, `schemas/` when present | Original |
| T-M5 | loader | `validate(version="0.0.0-dev")` errors without `--allow-dev-version` | Red-team F4.1 |
| T-M6 | loader | `validate(version="1.0.0+build.42")` accepts SemVer 2.0.0 build metadata | Red-team F4.2 |
| T-M7 | loader | `validate(extra=["/etc/passwd"])` rejects absolute path | Red-team F4.5 CRITICAL |
| T-M8 | loader | `validate(extra=["../foo"])` rejects path traversal | Red-team F4.5 CRITICAL |
| T-M9 | loader | `validate(bundle_name="../etc")` rejects bad chars | Red-team F4.7 |
| T-M10 | loader | `validate(skills=["foo","foo"])` rejects duplicates | Red-team F4.3 |
| T-M11 | loader | `validate(skills=["nonexistent"])` errors on disk-missing | Red-team F4.4 |
| T-B1 | build_manifest | `discover` enumerates skills | Original |
| T-B2 | build_manifest | `--list-questions --discover` has 4 batches | Original |
| T-B3 | build_manifest | Round-trip: discover → list-questions → answers → write → load → equal | Original |
| T-B4 | build_manifest | SIGTERM during `--write` → no partial file at target path | Validate F1.4 |
| T-G1a | golden (unit) | Pack synthetic `fixtures/sample-skill/` → file tree matches `fixtures/golden-pack-sample-skill/` | R3.Q3 BLOCKING |
| T-G1b | golden (integration) | Pack live `cleanmatic:product-spec` → tree matches; marker `@pytest.mark.integration` | R3.Q3 NON-blocking |
| T-T1 | templates | `render_template` unknown `{{TOKEN}}` raises `TemplateError` | Red-team F17.3 |
| T-T2 | install.sh | Bundled installer sandbox re-run is idempotent (`[SKIP]` second run) | Validate F1.6 |
| T-T3 | install.sh | Version detection: STALE / NEWER / OK SAME branches | Red-team F6.1 |

**Functional (`eval/evals.json` scenarios):** 3 scenarios per researcher B convention (init, validate, dry-run); fixtures under `eval/fixtures/`.

**Non-functional:**
- Full pytest suite (excluding integration marker) runs in <15s (relaxed from <5s per red-team F9.3).
- `pytest -m integration` adds <10s (live product-spec pack).
- No network. No tmpfs assumptions. `tmp_path` fixture for isolation.
- `conftest.py` `monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)` per test (red-team F1.5 + validate F8.2).
- `pyproject.toml` at skill root: `[tool.pytest.ini_options] testpaths = ["scripts/tests"] markers = ["integration: live product-spec dogfood test, non-blocking on CI"]`

### requirements-dev.txt (NEW per R3.Q10 + validate F2.1)

Create as **separate file** from runtime `requirements.txt`:
```
pytest>=7,<9
pytest-cov
```

### install.sh update (per R3.Q10)

Modify `install.sh` (from Phase 1) to detect `--dev` flag and conditionally install `requirements-dev.txt`. Phase 1 already has the flag detection scaffold; this phase pins the actual `pip install -r requirements-dev.txt` line.

## Architecture

```
scripts/tests/
├── conftest.py                       — fixtures: tmp_root, sample_claude, monkeypatch SOURCE_DATE_EPOCH
├── test_pack_determinism.py          — T-D1..T-D16
├── test_safety_check.py              — T-S1..T-S9
├── test_manifest_loader.py           — T-M1..T-M11
├── test_build_manifest.py            — T-B1..T-B4
├── test_golden_synthetic.py          — T-G1a (BLOCKING)
├── test_golden_product_spec.py       — T-G1b (@pytest.mark.integration, non-blocking)
├── test_templates.py                 — T-T1
├── test_installer_sandbox.py         — T-T2, T-T3
└── fixtures/
    ├── sample-skill/                 — synthetic minimal skill (golden source)
    ├── golden-pack-sample-skill/     — expected extracted layout
    ├── dirty-claude/                 — .env, .git, __pycache__, symlinks for safety tests
    ├── minimal-claude/               — valid minimal .claude/
    ├── sample.manifest.yaml
    └── interactive-answers.json

eval/
├── evals.json                        — 3 scenarios
└── fixtures/
    ├── minimal.manifest.yaml
    ├── interactive-answers.json
    └── dirty-claude/.env             — intentional test data (empty)
```

## Related Code Files

**Create:**
- `.claude/skills/claude-pack/scripts/requirements-dev.txt` — `pytest>=7,<9\npytest-cov\n`
- `.claude/skills/claude-pack/scripts/tests/conftest.py`
- `.claude/skills/claude-pack/scripts/tests/test_pack_determinism.py` (~280 LOC)
- `.claude/skills/claude-pack/scripts/tests/test_safety_check.py` (~150 LOC)
- `.claude/skills/claude-pack/scripts/tests/test_manifest_loader.py` (~200 LOC)
- `.claude/skills/claude-pack/scripts/tests/test_build_manifest.py` (~180 LOC)
- `.claude/skills/claude-pack/scripts/tests/test_golden_synthetic.py` (~80 LOC)
- `.claude/skills/claude-pack/scripts/tests/test_golden_product_spec.py` (~80 LOC, `@pytest.mark.integration`)
- `.claude/skills/claude-pack/scripts/tests/test_templates.py` (~50 LOC)
- `.claude/skills/claude-pack/scripts/tests/test_installer_sandbox.py` (~120 LOC)
- `.claude/skills/claude-pack/scripts/tests/fixtures/sample-skill/` — synthetic minimal skill (SKILL.md + 2-3 files)
- `.claude/skills/claude-pack/scripts/tests/fixtures/golden-pack-sample-skill/` — expected file tree
- `.claude/skills/claude-pack/scripts/tests/fixtures/dirty-claude/` — `.env`, `.git/HEAD`, `__pycache__/x.pyc`, `symlink → /etc/passwd`
- `.claude/skills/claude-pack/scripts/tests/fixtures/minimal-claude/` — valid minimal `.claude/`
- `.claude/skills/claude-pack/scripts/tests/fixtures/sample.manifest.yaml`
- `.claude/skills/claude-pack/scripts/tests/fixtures/interactive-answers.json`
- `.claude/skills/claude-pack/eval/evals.json`
- `.claude/skills/claude-pack/eval/fixtures/minimal.manifest.yaml`
- `.claude/skills/claude-pack/eval/fixtures/interactive-answers.json`
- `.claude/skills/claude-pack/eval/fixtures/dirty-claude/.env` (empty)
- `.claude/skills/claude-pack/pyproject.toml` — pytest config

**Modify:**
- `.claude/skills/claude-pack/install.sh` — pin `pip install -r requirements-dev.txt` inside `--dev` branch

## Implementation Steps

1. **`requirements-dev.txt`** — exactly:
   ```
   pytest>=7,<9
   pytest-cov
   ```

2. **`pyproject.toml`** — pytest config:
   ```toml
   [tool.pytest.ini_options]
   testpaths = ["scripts/tests"]
   python_files = "test_*.py"
   addopts = "-q --strict-markers"
   markers = [
     "integration: live product-spec dogfood test, non-blocking on CI",
   ]
   ```

3. **`conftest.py`** — fixtures:
   - `tmp_root(tmp_path)`: fresh fake repo with `.claude/` + selected fixtures
   - `sample_manifest_path(tmp_root)`: copies `assets/templates/manifest.example.yaml`
   - `pack_module()`: import path setup (`sys.path.insert(0, ...)` for `from pack import ...`)
   - `autouse fixture`: `monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)` per test
   - `synthetic_skill_dir`: returns path to `fixtures/sample-skill/`

4. **`test_pack_determinism.py`** — T-D1..T-D16. Highlights:
   - T-D1: build twice, hash both, assert equal
   - T-D4: `data = tarball.read_bytes(); assert data[4:8] == b"\x00\x00\x00\x00"`
   - T-D7a (mock): `monkeypatch.setattr(tarfile, "open", raising_open)`; assert no final file + `.tmp` cleaned
   - T-D7b (subprocess + env var): `subprocess.run([sys.executable, "-m", "pack", ...], env={**os.environ, "PACK_KILL_AFTER_N_FILES": "3"})`; assert subprocess returncode != 0 + no final file
   - T-D15: create old `.tmp` file with `os.utime(p, (now-7200, now-7200))`; run pack; assert old tmp removed
   - T-D16: `for f in glob("scripts/pack/*.py"): assert len(open(f).readlines()) < 200`

5. **`test_safety_check.py`** — T-S1..T-S9. CRITICAL fixes:
   - T-S6: assert `is_dropped(".envrc")[0]`, `is_dropped("id_rsa")[0]`, `is_dropped("foo/secrets.json")[0]`, `is_dropped("bar/cert.pem")[0]` (red-team F2.1 CRITICAL)
   - T-S7: assert `is_dropped(".git/HEAD")[0]`, `is_dropped("repo/.git/objects/pack/foo.pack")[0]` (red-team F14.2 CRITICAL)
   - T-S5: SKILL.md fixture content includes both inline `_shared/foo` reference AND a `_shared/bar` inside ` ```code block``` `; assert only `foo` returned

6. **`test_manifest_loader.py`** — T-M1..T-M11. CRITICAL fixes:
   - T-M7: `validate({"version": "1.0.0", "extra": ["/etc/passwd"]}, root)` returns non-empty list with "absolute paths not allowed" (red-team F4.5 CRITICAL)
   - T-M8: same with `["../foo"]` → "path traversal not allowed"
   - T-M11: `validate({"version": "1.0.0", "skills": ["nonexistent"]}, root)` errors

7. **`test_build_manifest.py`** — T-B1..T-B4. T-B4: `subprocess.run` with stdin → kill with SIGTERM mid-write (or mock the write step to raise); assert target path is absent + only `.tmp` may exist.

8. **`test_golden_synthetic.py`** (BLOCKING) — T-G1a:
   - `fixtures/sample-skill/`: synthetic minimal skill (SKILL.md, scripts/foo.py, references/spec.md — 3-5 files)
   - Pack it; extract to `tmp_path`; walk both trees; assert `set(extracted.relative_paths) == set(golden.relative_paths)` (exact-set match per red-team F10.2)
   - UPDATE_GOLDEN=1 env var path: refresh golden + exit 0

9. **`test_golden_product_spec.py`** (NON-blocking) — T-G1b:
   - `@pytest.mark.integration`
   - Pack live `.claude/skills/product-spec/`; extract; walk; assert file paths match `fixtures/golden-pack-product-spec/`
   - Docstring: "marker `integration`; run via `pytest -m integration`; CI does NOT include in pre-merge gate per R3.Q3"

10. **`test_templates.py`** — T-T1: `render_template("template with {{UNKNOWN}}", {"VERSION": "1.0"})` raises `TemplateError`.

11. **`test_installer_sandbox.py`** — T-T2, T-T3:
    - T-T2: copy template installer to tmp dir; create fake tarball layout; run installer twice; assert second run all `[SKIP]`
    - T-T3: create existing `.claude/skills/foo/SKILL.md` with various versions; pack a tarball with bundled v0.5.0; run installer; assert STALE/NEWER/OK SAME messages match

12. **`eval/evals.json`** — 3 scenarios per researcher B Q5:
    - Pack product-spec standalone (assertions: tarball exists, sha256 sidecar, schema_version, no secrets, deterministic SHA across re-run)
    - safety_check on dirty-claude (assertions: warn finding for .env, exit 0, no file content echo)
    - Interactive answers → dry-run preview (assertions: no file created, file count matches, would_be_sha stable)

13. **Fixtures** — create fixture trees minimally; `.git/HEAD`, `.env`, `__pycache__/x.pyc`, symlink, etc. Test-time helper writes them if missing.

14. **Modify `install.sh`** — uncomment / pin `pip install -r requirements-dev.txt` inside the `if [[ "$DEV" == "1" ]]; then ...; fi` block.

15. **Run full suite** — `./.claude/skills/.venv/bin/python3 -m pytest .claude/skills/claude-pack/scripts/tests/ -v` all green (excluding `-m integration`); `pytest -m integration` also green locally.

16. **Per-phase compile** — `python -m py_compile scripts/tests/*.py` exits 0.

## Success Criteria

- [ ] `pytest -m "not integration"` runs all 47 tests (T-D1..D16, T-S1..S9, T-M1..M11, T-B1..B4, T-G1a, T-T1..T3) and passes
- [ ] `pytest -m integration` runs T-G1b (live product-spec); passes locally (CI does NOT block on this — Phase 7)
- [ ] Full suite runtime `<15s` (excluding integration); `<25s` total
- [ ] **CRITICAL fix verifications:**
  - [ ] T-S6 (red-team F2.1): `.envrc`, `id_rsa`, `secrets.json`, `*.pem` all dropped — passes
  - [ ] T-S7 (red-team F14.2): `.git/HEAD` dropped — passes
  - [ ] T-M7 (red-team F4.5): absolute path in `extra` rejected — passes
- [ ] T-D4 (gzip mtime=0) passes — `data[4:8] == b"\x00\x00\x00\x00"`
- [ ] T-D1 (determinism) passes — two runs identical SHA256
- [ ] T-D16 (modularization) passes — every `scripts/pack/*.py` < 200 LOC
- [ ] T-G1a (synthetic golden, BLOCKING) passes — file tree exact match
- [ ] T-G1b (live integration) passes locally with `-m integration`
- [ ] T-T2 (installer idempotency, validate F1.6) passes
- [ ] T-T3 (installer version detection, red-team F6.1) passes for all 3 branches
- [ ] T-B4 (atomic write SIGTERM, validate F1.4) passes
- [ ] `eval/evals.json` parses as valid JSON; 3 scenarios; each has ≥3 assertions
- [ ] `scripts/requirements-dev.txt` exists with exactly `pytest>=7,<9 + pytest-cov`
- [ ] `pyproject.toml` exists with pytest config + integration marker
- [ ] `install.sh --dev` installs pytest into venv (`.venv/bin/python -c "import pytest"` succeeds)
- [ ] `python -m py_compile scripts/tests/*.py` exits 0

## Risk Assessment

- **R1: T-D1 fails on macOS due to APFS timestamp precision** → explicit `tarinfo.mtime = 0` per file; gzip mtime=0; no `os.stat` reliance. Phase 7 CI tests macOS.
- **R2: T-D7b SIGTERM race flaky in CI** → Use `PACK_KILL_AFTER_N_FILES` env var (debug-only, documented in code comment + error-catalog) for deterministic trigger.
- **R3: T-G1b breaks when product-spec edited** → `-m integration` not in CI pre-merge per R3.Q3. Engineers run locally + refresh golden via `UPDATE_GOLDEN=1 pytest -m integration` + commit.
- **R4: pytest dev-only adds friction for casual users** → `install.sh` (no flag) ships pyyaml only. Documented in README quickstart.
- **R5: Tests pass locally but CI inherits SOURCE_DATE_EPOCH** → autouse conftest fixture `monkeypatch.delenv` per test. CI workflow also explicitly unsets.
- **R6: 29-test suite drifts as plan amends** → Test catalog mirrored in `references/error-catalog.md` cross-reference; PR diff highlights new tests.
- **R7: 200-line modularization (T-D16) fails when a `pack/` file grows** → Document escape hatch: if a `pack/` module legitimately exceeds, plan-amend records the exception; test updated to skip that file with comment.

## Security Considerations

- Test fixtures intentionally include `.env` (empty), `.git/HEAD` (fake), symlinks. Document in `fixtures/README.md`: "intentional test data; never run production tooling against these directories".
- Tests never write outside `tmp_path` (pytest fixture). T-T2 (installer sandbox) writes to tmp dir; never `$HOME/.claude`.
- T-S4 (hard safety) + T-S6 (expanded secrets) + T-S7 (.git) + T-M7 (absolute paths) collectively codify the security contract. CI red on any failure.

## Next Steps

- Phase 6 dogfoods the test infrastructure: smoke test 2 runs `pytest -q` end-to-end.
- Phase 7 CI Integration: matrix runs `pytest -m "not integration"` on every PR; `pytest -m integration` weekly cron (non-blocking).
