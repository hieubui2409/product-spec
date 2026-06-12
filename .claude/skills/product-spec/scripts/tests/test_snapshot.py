"""Tests for snapshot/restore engine (snapshot.py) and VCS-warn checks (status_vcs.py).

TDD: these tests were written BEFORE the implementation. They define the contract.

Snapshot engine:
  - make_snapshot(spec_root, snapshots_home, ts) → Path  (deterministic ts via injection)
  - restore_snapshot(spec_root, snapshots_home, ts, *, confirm=False) → None
  - list_snapshots(snapshots_home) → List[str]

VCS-warn checks:
  - vcs_warnings(spec_root) → List[Dict]
    Possible warning types: "spec_tree_untracked", "large_uncommitted_diff"
    Thresholds: UNTRACKED_FILE_WARN = 1 (any untracked = outside git counts)
                LARGE_DIFF_FILE_COUNT = 5 (≥5 uncommitted files in spec tree)

Fixtures: throwaway git repos in tmp dirs (never touch the real repo's git state).
No real PO data — only synthetic artifacts.
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

# --- helpers -----------------------------------------------------------------

def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=str(root), check=True,
                   capture_output=True, text=True)


def _make_spec_tree(root: Path) -> Path:
    """Create a minimal synthetic spec tree under root/docs/product/."""
    spec = root / "docs" / "product"
    spec.mkdir(parents=True, exist_ok=True)
    (spec / "PRODUCT.md").write_text(
        "---\nid: PRODUCT\ntype: product\n---\n\n# Product\n", encoding="utf-8"
    )
    stories = spec / "stories"
    stories.mkdir(exist_ok=True)
    (stories / "S1.md").write_text(
        "---\nid: S1\ntype: story\n---\n\n# Story 1\n", encoding="utf-8"
    )
    return spec


def _make_git_proj(tmp: Path) -> Path:
    """Spec tree inside a committed git repo — clean working tree."""
    proj = tmp / "proj"
    proj.mkdir(parents=True, exist_ok=True)
    _make_spec_tree(proj)
    _git(proj, "init", "-q")
    _git(proj, "config", "user.email", "t@t.t")
    _git(proj, "config", "user.name", "t")
    _git(proj, "add", "-A")
    _git(proj, "commit", "-q", "-m", "base")
    return proj


def _make_non_git_proj(tmp: Path) -> Path:
    """Spec tree with NO git repo — simulates outside-git scenario."""
    proj = tmp / "proj"
    proj.mkdir()
    _make_spec_tree(proj)
    return proj


def _snapshots_home(proj: Path) -> Path:
    return proj / ".product-spec-snapshots"


# =============================================================================
# snapshot.py tests
# =============================================================================

def test_snapshot_captures_spec_tree(tmp_path):
    """make_snapshot → snapshot dir exists with copied artifacts + README."""
    import snapshot as snap

    proj = _make_non_git_proj(tmp_path)
    home = _snapshots_home(proj)
    spec_root = proj / "docs" / "product"

    result = snap.make_snapshot(spec_root, home, ts="20260612T000001")

    assert result.is_dir(), "snapshot dir must exist"
    assert (result / "README.md").is_file(), "snapshot dir must contain README"
    assert (result / "PRODUCT.md").is_file(), "PRODUCT.md must be copied"
    assert (result / "stories" / "S1.md").is_file(), "nested file must be copied"


def test_snapshot_timestamped_distinct(tmp_path):
    """Two snapshots with different injected ts → two distinct dirs, both exist."""
    import snapshot as snap

    proj = _make_non_git_proj(tmp_path)
    home = _snapshots_home(proj)
    spec_root = proj / "docs" / "product"

    r1 = snap.make_snapshot(spec_root, home, ts="20260612T000001")
    r2 = snap.make_snapshot(spec_root, home, ts="20260612T000002")

    assert r1 != r2, "distinct timestamps must produce distinct snapshot dirs"
    assert r1.is_dir() and r2.is_dir(), "both snapshot dirs must exist"
    assert (r1 / "PRODUCT.md").is_file(), "first snapshot must be intact"
    assert (r2 / "PRODUCT.md").is_file(), "second snapshot must be intact"


def test_restore_brings_back_snapshot(tmp_path):
    """snapshot, mutate/delete an artifact, restore (clean target) → tree matches snapshot."""
    import snapshot as snap

    proj = _make_non_git_proj(tmp_path)
    home = _snapshots_home(proj)
    spec_root = proj / "docs" / "product"

    # Capture state
    result = snap.make_snapshot(spec_root, home, ts="20260612T000001")

    # Mutate the live tree
    (spec_root / "PRODUCT.md").write_text("--- MUTATED ---\n", encoding="utf-8")
    (spec_root / "stories" / "S1.md").unlink()  # delete a file

    # Restore (no dirty-uncommitted files — this is a non-git proj, confirm not needed)
    snap.restore_snapshot(spec_root, home, "20260612T000001", confirm=True)

    assert (spec_root / "PRODUCT.md").read_text(encoding="utf-8").startswith(
        "---\nid: PRODUCT"
    ), "PRODUCT.md must be restored to snapshot content"
    assert (spec_root / "stories" / "S1.md").is_file(), "deleted file must be restored"


def test_restore_refuses_dirty_without_confirm(tmp_path):
    """restore without confirm=True on a dirty git tree → refuses, returns non-zero / raises,
    live tree is untouched."""
    import snapshot as snap

    proj = _make_git_proj(tmp_path)
    home = _snapshots_home(proj)
    spec_root = proj / "docs" / "product"

    # Capture clean snapshot
    snap.make_snapshot(spec_root, home, ts="20260612T000001")

    # Dirty the working tree (uncommitted change)
    (spec_root / "PRODUCT.md").write_text(
        "---\nid: PRODUCT\ntype: product\n---\n\n# DIRTY\n", encoding="utf-8"
    )
    dirty_content = (spec_root / "PRODUCT.md").read_text(encoding="utf-8")

    # Must refuse without confirm
    import pytest
    with pytest.raises(Exception) as exc_info:
        snap.restore_snapshot(spec_root, home, "20260612T000001", confirm=False)

    # Error must be informative
    assert exc_info.value is not None

    # Live tree must be untouched
    assert (spec_root / "PRODUCT.md").read_text(encoding="utf-8") == dirty_content, \
        "dirty file must not be overwritten when confirm=False"


def test_snapshot_list_empty_no_crash(tmp_path):
    """list_snapshots with no snapshots → empty list, no exception, exit 0 behavior."""
    import snapshot as snap

    home = tmp_path / "empty-snapshots"
    # home does NOT exist yet

    result = snap.list_snapshots(home)

    assert isinstance(result, list), "list_snapshots must return a list"
    assert result == [], "empty snapshots home → empty list"


# =============================================================================
# status_vcs.py tests
# =============================================================================

def test_vcs_warn_when_spec_tree_untracked(tmp_path):
    """spec tree not in git (no .git repo) → at least one 'spec_tree_untracked' warning."""
    import status_vcs

    proj = _make_non_git_proj(tmp_path)
    warnings = status_vcs.vcs_warnings(proj / "docs" / "product")

    types = [w["type"] for w in warnings]
    assert "spec_tree_untracked" in types, (
        f"expected 'spec_tree_untracked' warning for non-git spec tree; got: {types}"
    )


def test_vcs_warn_large_uncommitted_diff(tmp_path):
    """
    Both directions tested:
    - ≥ LARGE_DIFF_FILE_COUNT uncommitted files in spec tree → 'large_uncommitted_diff' warning
    - < LARGE_DIFF_FILE_COUNT uncommitted files → no such warning
    """
    import status_vcs

    # Build a git repo for a clean reference
    proj_large = _make_git_proj(tmp_path / "large")
    spec_large = proj_large / "docs" / "product"

    # Add enough new files to exceed the threshold (LARGE_DIFF_FILE_COUNT = 5)
    for i in range(6):  # 6 > 5
        (spec_large / f"extra_{i}.md").write_text(
            f"---\nid: EXTRA{i}\ntype: story\n---\n\n# Extra {i}\n", encoding="utf-8"
        )
    # NOT committed → large diff

    warnings_large = status_vcs.vcs_warnings(spec_large)
    large_types = [w["type"] for w in warnings_large]
    assert "large_uncommitted_diff" in large_types, (
        f"expected 'large_uncommitted_diff' when 6 files uncommitted; got: {large_types}"
    )

    # Under threshold: just 1 uncommitted file
    proj_small = _make_git_proj(tmp_path / "small")
    spec_small = proj_small / "docs" / "product"
    (spec_small / "one_more.md").write_text(
        "---\nid: ONE\ntype: story\n---\n\n# One\n", encoding="utf-8"
    )
    # NOT committed → small diff (1 file < 5)

    warnings_small = status_vcs.vcs_warnings(spec_small)
    small_types = [w["type"] for w in warnings_small]
    assert "large_uncommitted_diff" not in small_types, (
        f"expected NO 'large_uncommitted_diff' with only 1 uncommitted file; got: {small_types}"
    )
