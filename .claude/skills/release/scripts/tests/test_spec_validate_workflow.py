"""test_spec_validate_workflow — the opt-in spec-validate GitHub Action.

The bundle ships a recipient-facing CI workflow that runs the product-spec checks
(traceability · consistency · fence) on docs/product/ and writes a Vietnamese job
summary. These tests build a real bundle and assert:

  1. The rendered spec-validate.yml is valid YAML with the brand token substituted.
  2. It invokes the three installed check scripts on docs/product/ and writes a
     Vietnamese summary to $GITHUB_STEP_SUMMARY.
  3. It has NO kit-file dependency — it references only the installed product-spec
     scripts and docs/product/, never dev-only files (pack manifest, release skill,
     repo-root CI). A recipient who only installed the bundle can run it as-is.
  4. The installer keeps it OUT of the repo root and installs it to
     .github/workflows/ only on explicit opt-in (INSTALL_SPEC_VALIDATE=1).
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest
import yaml

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
MANIFEST = REPO_ROOT / ".claude" / "pack.manifest.yaml"

pytestmark = [
    pytest.mark.skipif(not MANIFEST.is_file(), reason="repo manifest not present"),
]


def _build_bundle(out_dir: Path) -> Path:
    r = subprocess.run(
        [sys.executable, "-m", "pack", "--root", str(REPO_ROOT), "--manifest", str(MANIFEST),
         "--version", "0.0.0-test", "--allow-dev-version", "--out", str(out_dir)],
        cwd=str(SCRIPTS_DIR), capture_output=True, text=True,
    )
    assert r.returncode == 0, f"pack build failed: {r.stderr or r.stdout}"
    tarballs = glob.glob(str(out_dir / "*.tar.gz"))
    assert tarballs, f"no tarball produced in {out_dir}"
    return Path(tarballs[0])


def _extract(bundle: Path, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle, "r:gz") as tar:
        tar.extractall(dest)
    return next(dest.rglob("spec-validate.yml")).parent  # bundle root


def test_workflow_rendered_yaml_is_valid_and_branded(tmp_path):
    root = _extract(_build_bundle(tmp_path / "dist"), tmp_path / "x")
    text = (root / "spec-validate.yml").read_text(encoding="utf-8")
    # No unsubstituted template token survived the build.
    assert "{{" not in text, "an unrendered {{TOKEN}} leaked into spec-validate.yml"
    # Valid YAML (lint). YAML 1.1 maps the bare `on:` key to True — that is fine; we
    # assert structure via the jobs map, which is unambiguous.
    doc = yaml.safe_load(text)
    assert isinstance(doc, dict)
    assert "jobs" in doc and "spec-validate" in doc["jobs"]


def test_workflow_invokes_checks_with_vietnamese_summary(tmp_path):
    root = _extract(_build_bundle(tmp_path / "dist"), tmp_path / "x")
    text = (root / "spec-validate.yml").read_text(encoding="utf-8")
    for script in ("check_traceability.py", "check_consistency.py", "check_fence.py"):
        assert script in text, f"workflow must run {script}"
    assert "docs/product" in text
    assert "$GITHUB_STEP_SUMMARY" in text, "must write a job summary"
    # Vietnamese summary (diacritics present, not an ASCII fallback).
    assert "Kết quả" in text and "đạt" in text


def test_workflow_has_no_kit_file_dependency(tmp_path):
    """It must reference only the installed product-spec scripts + docs/product/ —
    nothing a recipient would not have (dev manifest, release skill, repo-root CI)."""
    root = _extract(_build_bundle(tmp_path / "dist"), tmp_path / "x")
    text = (root / "spec-validate.yml").read_text(encoding="utf-8")
    assert "pack.manifest.yaml" not in text
    assert ".claude/skills/release" not in text
    assert ".claude/skills/_shared" not in text
    # The only kit path it leans on is the installed product-spec scripts dir.
    assert ".claude/skills/product-spec/scripts" in text


def _run_install(bundle_root: Path, target: Path, env_extra: dict) -> subprocess.CompletedProcess:
    install_sh = bundle_root / "install.sh"
    env = {**os.environ, "TARGET_DIR": str(target), "NON_INTERACTIVE": "1", **env_extra}
    return subprocess.run(["bash", str(install_sh)], capture_output=True, text=True, env=env)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash required to run install.sh")
def test_installer_opt_in_lands_workflow_else_absent(tmp_path):
    bundle_root = _extract(_build_bundle(tmp_path / "dist"), tmp_path / "x")
    dst = lambda t: t / ".github" / "workflows" / "spec-validate.yml"

    # Default non-interactive install: opt-in NOT given → workflow absent, and the
    # template is NOT dropped at the repo root by the generic walk.
    t1 = tmp_path / "default"; t1.mkdir()
    r1 = _run_install(bundle_root, t1, {})
    assert r1.returncode == 0, r1.stderr or r1.stdout
    assert not dst(t1).exists(), "workflow must not install without opt-in"
    assert not (t1 / "spec-validate.yml").exists(), "template must not land at repo root"

    # Opt-in install: workflow lands under .github/workflows/.
    t2 = tmp_path / "optin"; t2.mkdir()
    r2 = _run_install(bundle_root, t2, {"INSTALL_SPEC_VALIDATE": "1"})
    assert r2.returncode == 0, r2.stderr or r2.stdout
    assert dst(t2).is_file(), f"opt-in must install the workflow:\n{r2.stdout}\n{r2.stderr}"
    # Installed copy is the bundle template verbatim.
    assert dst(t2).read_bytes() == (bundle_root / "spec-validate.yml").read_bytes()
