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

SCRIPTS_DIR = Path(__file__).resolve().parents[1]            # .../release/scripts
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
    # The release skill is NOT shipped to recipients (dev-only toolchain).
    assert not (target / ".claude" / "skills" / "release" / "SKILL.md").is_file(), \
        "release skill must not be installed to recipients"
    # Verify another shipped skill (product-spec-critique) landed too.
    assert (target / ".claude" / "skills" / "product-spec-critique" / "SKILL.md").is_file(), \
        "product-spec-critique SKILL.md not installed"

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


def _extract_and_install(tmp_path) -> tuple[Path, Path]:
    """Build + extract a bundle and run a clean install into a fresh target.
    Returns (bundle_extract_dir, target_dir) for follow-up upgrade runs."""
    bundle = _build_bundle(tmp_path / "dist")
    extract = tmp_path / "extract"
    extract.mkdir()
    with tarfile.open(bundle, "r:gz") as tar:
        tar.extractall(extract)
    target = tmp_path / "recipient"
    target.mkdir()
    r = _run_install(extract, target)
    assert r.returncode == 0, f"clean install failed: {r.stderr or r.stdout}"
    return extract, target


@pytest.mark.bug_class  # upgrade must never keep a pre-config-gate blocking hook
def test_upgrade_replaces_pre_config_gate_enforcement_hook(tmp_path):
    """An OLD enforcement hook that never calls the config gate `hook_enabled`
    blocks turn-end unconditionally once wired. On a default (no-FORCE) upgrade the
    installer must REPLACE it with the gated bundle copy and leave a backup —
    never silently keep the unsafe copy (the generic skip-existing path would)."""
    extract, target = _extract_and_install(tmp_path)
    hook = target / ".claude" / "hooks" / "memory_gap_hook.py"
    assert hook.is_file() and "hook_enabled" in hook.read_text()  # bundle copy is gated

    # Simulate a stale recipient: a pre-config-gate hook with NO hook_enabled call.
    hook.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "# v1.1.0 memory hook: blocks turn-end unconditionally (no config gate)\n"
        "print('block', file=sys.stderr)\n"
        "sys.exit(2)\n",
        encoding="utf-8",
    )

    r2 = _run_install(extract, target)  # default upgrade, no FORCE_OVERWRITE
    assert r2.returncode == 0, f"upgrade failed: {r2.stderr or r2.stdout}"
    # The unsafe copy was replaced with the gated bundle copy...
    assert "hook_enabled" in hook.read_text(), "pre-config-gate hook was NOT replaced"
    # ...and the prior copy was preserved as a timestamped backup.
    backups = list(hook.parent.glob("memory_gap_hook.py.bak.*"))
    assert backups, "no backup of the replaced hook"
    assert "block', file=sys.stderr" in backups[0].read_text()  # backup is the old unsafe copy


@pytest.mark.bug_class  # a PO-edited gate-aware hook must never be blind-overwritten
def test_upgrade_preserves_po_edited_gate_aware_hook(tmp_path):
    """A gate-aware enforcement hook that the PO locally MODIFIED must not be
    blind-overwritten on a default upgrade — the installer flags a CONFLICT and
    keeps the local copy (FORCE_OVERWRITE=1 is the explicit opt-in to take the
    bundle)."""
    extract, target = _extract_and_install(tmp_path)
    hook = target / ".claude" / "hooks" / "memory_gap_hook.py"
    marker = "\n# PO-LOCAL-TWEAK: keep my change\n"
    hook.write_text(hook.read_text() + marker, encoding="utf-8")  # still gate-aware

    r2 = _run_install(extract, target)  # default upgrade, no FORCE_OVERWRITE
    assert r2.returncode == 0, f"upgrade failed: {r2.stderr or r2.stdout}"
    # The PO edit survives (not clobbered) and the installer reported the conflict.
    assert "PO-LOCAL-TWEAK" in hook.read_text(), "PO edit was blind-overwritten"
    assert "CONFLICT" in (r2.stdout + r2.stderr)


@pytest.mark.bug_class  # an unchanged enforcement hook must re-install cleanly (no false alarm)
def test_reinstall_identical_enforcement_hook_is_clean_skip(tmp_path):
    """The behavioral guard keys on `hook_enabled`; a re-install over the SAME
    gated bundle copy must NOT trip [SECURITY OVERWRITE] (it IS gate-aware) nor
    [CONFLICT] (it is byte-identical) — it falls through to the generic skip."""
    extract, target = _extract_and_install(tmp_path)
    r2 = _run_install(extract, target)  # second identical install
    assert r2.returncode == 0, f"reinstall failed: {r2.stderr or r2.stdout}"
    out = r2.stdout + r2.stderr
    assert "memory_gap_hook.py" not in out or "CONFLICT" not in out, "false CONFLICT on identical hook"
    assert "SECURITY OVERWRITE" not in out, "gate-aware identical hook wrongly force-overwritten"
    # and no spurious backup was created for the untouched hook
    assert not list((target / ".claude" / "hooks").glob("memory_gap_hook.py.bak.*")), \
        "identical re-install left a needless backup"
