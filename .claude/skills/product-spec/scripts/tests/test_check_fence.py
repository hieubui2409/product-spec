"""Tests for the advisory fence scan (`check_fence.py`).

ADVISORY ONLY — it never blocks. It scans the working-tree changes (via
`git status --porcelain`) and reports any touched file that lives OUTSIDE
`docs/product/`. A clean run (only docs/product/ touched, or nothing touched)
yields empty findings and exit 0. This feeds the behavioral-memory pass; it is
NOT a write guard (that is fs_guard's job).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import check_fence  # noqa: E402


def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


def _init_repo(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t.t")
    _git(root, "config", "user.name", "t")
    _git(root, "commit", "--allow-empty", "-q", "-m", "base")


def _touch(root: Path, rel: str, content: str = "x"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ---------- API: scan() ----------

def test_check_fence_flags_outside(tmp_path):
    root = tmp_path
    _init_repo(root)
    _touch(root, "docs/product/prds/auth.md")   # in-fence (ok)
    _touch(root, "src/app.py")                   # OUTSIDE (flagged)
    findings = check_fence.scan(root)
    outside = [f["file"] for f in findings]
    assert "src/app.py" in outside
    assert "docs/product/prds/auth.md" not in outside
    # Advisory severity — never an error that would gate CI.
    assert all(f["severity"] in ("warn", "info") for f in findings)
    assert all(f["check"] == "fence_breach" for f in findings)


def test_check_fence_clean(tmp_path):
    root = tmp_path
    _init_repo(root)
    _touch(root, "docs/product/vision.md")
    _touch(root, "docs/product/brd.md")
    findings = check_fence.scan(root)
    assert findings == []


def test_check_fence_nothing_touched(tmp_path):
    root = tmp_path
    _init_repo(root)
    findings = check_fence.scan(root)
    assert findings == []


def test_check_fence_handles_deleted_and_renamed(tmp_path):
    root = tmp_path
    _init_repo(root)
    _touch(root, "config/x.yaml")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "add config")
    # Delete the outside file → still a touch outside the fence.
    (root / "config" / "x.yaml").unlink()
    findings = check_fence.scan(root)
    assert any(f["file"] == "config/x.yaml" for f in findings)


def test_check_fence_not_a_git_repo_degrades(tmp_path):
    # No git repo → advisory cannot read git state; degrade to empty (never crash,
    # never block). It is advisory, so absence of git is not an error.
    findings = check_fence.scan(tmp_path)
    assert findings == []


# ---------- CLI ----------

def test_check_fence_cli_exit_zero_when_clean(tmp_path):
    root = tmp_path
    _init_repo(root)
    _touch(root, "docs/product/vision.md")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "check_fence.py"), "--root", str(root)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["findings"] == []


def test_check_fence_cli_exit_zero_when_breached(tmp_path):
    # ADVISORY: even with a breach the script exits 0 (it never blocks).
    root = tmp_path
    _init_repo(root)
    _touch(root, "outside.txt")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "check_fence.py"), "--root", str(root)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert any(f["file"] == "outside.txt" for f in out["findings"])
