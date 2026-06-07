"""test_bundle_excludes_telemetry — the A1 telemetry layer must NEVER reach a
recipient bundle.

Two independent layers, deliberately distinct (a leak in either is a real bug):
  1. By construction — the whitelist manifest names no telemetry path, so
     resolve_selection yields no `.claude/telemetry/` member and none of the
     CM-local telemetry hooks. Fast, deterministic, the PRIMARY guarantee.
  2. Regression sentinel — a REAL `python -m pack` build, asserted non-empty
     FIRST (else a vacuous pass), then scanned for any `.claude/telemetry/`
     member or telemetry hook `.py`. Catches a leak that bypasses selection.

Telemetry hooks are CM-repo source but are intentionally absent from the
manifest's `hooks:` list, so they ride neither the slug walk nor an explicit
entry — they stay home.
"""

from __future__ import annotations

import glob
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

import manifest_loader  # type: ignore[import-not-found]
from pack.selection import resolve_selection

REPO_ROOT = Path(__file__).resolve().parents[5]
MANIFEST = REPO_ROOT / ".claude" / "pack.manifest.yaml"

TELEMETRY_HOOK_BASENAMES = {
    "track_skill_invocation.py",
    "track_script_execution.py",
    "emit_session_summary.py",
}


def _arcs() -> set[str]:
    manifest = manifest_loader.load(MANIFEST)
    return {arc for _, arc in resolve_selection(manifest, REPO_ROOT)}


@pytest.mark.bug_class
def test_selection_excludes_telemetry_by_construction():
    arcs = _arcs()
    leaks = [a for a in arcs if "/.claude/telemetry/" in f"/{a}" or a.startswith(".claude/telemetry/")]
    assert not leaks, f"telemetry sink path leaked into bundle file set: {leaks}"
    hook_leaks = [a for a in arcs if Path(a).name in TELEMETRY_HOOK_BASENAMES]
    assert not hook_leaks, f"CM-local telemetry hook leaked into bundle file set: {hook_leaks}"


@pytest.mark.bug_class
def test_real_tarball_excludes_telemetry(tmp_path):
    out_dir = tmp_path / "dist"
    out_dir.mkdir()
    r = subprocess.run(
        [sys.executable, "-m", "pack", "--root", str(REPO_ROOT), "--manifest", str(MANIFEST),
         "--version", "0.0.0-test", "--allow-dev-version", "--out", str(out_dir)],
        capture_output=True, text=True, cwd=str(REPO_ROOT / ".claude" / "skills" / "release" / "scripts"),
    )
    assert r.returncode == 0, f"pack build failed: {r.stderr or r.stdout}"
    tarballs = glob.glob(str(out_dir / "*.tar.gz"))
    assert tarballs, "no tarball produced"

    with tarfile.open(tarballs[0], "r:gz") as tar:
        members = tar.getnames()

    # Guard against a vacuous pass: an empty tar would trivially "exclude" telemetry.
    assert len(members) > 5, f"tarball suspiciously small ({len(members)} members)"

    tel = [m for m in members if "/.claude/telemetry/" in f"/{m}" or "/.claude/telemetry" in m or Path(m).name in TELEMETRY_HOOK_BASENAMES]
    assert not tel, f"telemetry leaked into the real tarball: {tel}"
