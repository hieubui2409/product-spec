"""test_installer_e2e — build a real bundle, extract it, and actually RUN install.sh (B5).

The golden/determinism tests build + extract + assert arcnames but never prove a clean install
works on a recipient tree. This does: `python -m pack` → real tar.gz → extract → run the bundled
`install.sh` against a throwaway `TARGET_DIR` → assert files landed, then a second run is idempotent
(skips existing). POSIX-only (the bundled installer is bash); skipped where bash is absent.
"""

from __future__ import annotations

import glob
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]            # .../claude-pack/scripts
REPO_ROOT = Path(__file__).resolve().parents[5]              # .../cleanmatic-skills
MANIFEST = REPO_ROOT / ".claude" / "pack.manifest.yaml"

pytestmark = [
    pytest.mark.skipif(shutil.which("bash") is None, reason="bash required to run install.sh"),
    pytest.mark.skipif(not MANIFEST.is_file(), reason="repo manifest not present"),
]


def _build_bundle(out_dir: Path) -> Path:
    """Build a real tarball via the pack CLI; return its path."""
    r = subprocess.run(
        [sys.executable, "-m", "pack", "--root", str(REPO_ROOT), "--manifest", str(MANIFEST),
         "--version", "0.0.0-test", "--allow-dev-version", "--out", str(out_dir)],
        cwd=str(SCRIPTS_DIR), capture_output=True, text=True,
    )
    assert r.returncode == 0, f"pack build failed: {r.stderr or r.stdout}"
    tarballs = glob.glob(str(out_dir / "*.tar.gz"))
    assert tarballs, f"no tarball produced in {out_dir}"
    return Path(tarballs[0])


def _run_install(bundle_dir: Path, target: Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    install_sh = next(bundle_dir.rglob("install.sh"))
    import os
    env = {**os.environ, "TARGET_DIR": str(target), "NON_INTERACTIVE": "1"}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", str(install_sh)], capture_output=True, text=True, env=env)


@pytest.mark.bug_class  # cross-cutting invariant: the recipient installer actually installs cleanly
def test_install_clean_then_idempotent(tmp_path):
    bundle = _build_bundle(tmp_path / "dist")
    extract = tmp_path / "extract"
    extract.mkdir()
    with tarfile.open(bundle, "r:gz") as tar:
        tar.extractall(extract)

    target = tmp_path / "recipient"
    target.mkdir()

    # 1) Clean install into an empty tree.
    r1 = _run_install(extract, target)
    assert r1.returncode == 0, f"install failed: {r1.stderr or r1.stdout}"
    # A representative shipped artifact must have landed.
    installed = target / ".claude" / "skills" / "product-spec" / "SKILL.md"
    assert installed.is_file(), f"product-spec SKILL.md not installed:\n{r1.stdout}\n{r1.stderr}"
    assert (target / ".claude" / "skills" / "claude-pack" / "SKILL.md").is_file()

    # 2) Re-run is idempotent: exit 0, existing skills skipped (not clobbered), files still present.
    r2 = _run_install(extract, target)
    assert r2.returncode == 0, f"idempotent re-run failed: {r2.stderr or r2.stdout}"
    assert installed.is_file()
    combined = r2.stdout + r2.stderr
    assert "Skipped" in combined, f"second run should report skips:\n{combined}"


def test_bundle_carries_installer_and_manifest(tmp_path):
    bundle = _build_bundle(tmp_path / "dist")
    with tarfile.open(bundle, "r:gz") as tar:
        names = tar.getnames()
    assert any(n.endswith("/install.sh") for n in names)
    assert any(n.endswith("/install.ps1") for n in names)
    assert any(n.endswith("/MANIFEST.json") for n in names)
    # The whole-tarball SHA sidecar rides next to the artifact.
    assert (bundle.parent / (bundle.name + ".sha256")).is_file()
