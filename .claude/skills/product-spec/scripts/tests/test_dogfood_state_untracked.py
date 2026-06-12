"""Per-run state/cache files must NOT be tracked by git; prose artifacts must remain tracked.

The invariant: files under docs/product/ that hold session state, memory cache,
or snapshot data should never appear in the git index — they are per-run
transients.  Prose artifacts (BRD, PRDs, vision, etc.) must remain tracked.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]  # .../product-spec

# These paths must NOT appear in git ls-files after the untrack step.
STATE_CACHE_PATHS = [
    "docs/product/.session.md",
    "docs/product/.memory/critique-findings-index.json",
    "docs/product/.memory/critique-lens-cache/7887b727191e3ef3.json",
    "docs/product/.memory/critique-state.json",
    "docs/product/.memory/last_critique.json",
    "docs/product/.memory/last_validated.json",
    "docs/product/.memory/preferences.yaml",
    "docs/product/visuals/.snapshots/20260606T035806Z-95c4b19b.json",
]

# At least one known prose artifact must remain tracked.
PROSE_PATHS = [
    "docs/product/PRODUCT.md",
    "docs/product/brd.md",
    "docs/product/vision.md",
]


def _tracked_files() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return set(result.stdout.splitlines())


def test_state_cache_files_are_not_tracked():
    """State/cache files must not appear in git ls-files."""
    tracked = _tracked_files()
    still_tracked = [p for p in STATE_CACHE_PATHS if p in tracked]
    assert not still_tracked, (
        f"These per-run state/cache files are still tracked by git and must be "
        f"removed with `git rm --cached`: {still_tracked}"
    )


def test_prose_artifacts_are_still_tracked():
    """Prose artifacts must still appear in git ls-files after the untrack step."""
    tracked = _tracked_files()
    untracked_prose = [p for p in PROSE_PATHS if p not in tracked]
    assert not untracked_prose, (
        f"These prose artifact files were accidentally untracked: {untracked_prose}"
    )


def test_working_tree_state_files_still_exist_on_disk():
    """Working-tree state/cache files must still exist on disk (git rm --cached, not rm)."""
    # Only assert for files we know exist in the fixture; a missing file that was
    # never created is not a failure — the contract is "don't delete the file, only
    # remove from the index".
    missing = [
        p for p in STATE_CACHE_PATHS
        if not (REPO_ROOT / p).exists()
        # Only assert when the file is expected to exist (skip the lens-cache entry
        # which may not be created in all environments — but prefer to check).
    ]
    # Allow the lens-cache file to be absent (it's a content-addressed cache entry
    # that may not be present in a fresh clone).
    allowed_absent = {"docs/product/.memory/critique-lens-cache/7887b727191e3ef3.json"}
    truly_missing = [p for p in missing if p not in allowed_absent]
    assert not truly_missing, (
        f"These state/cache files were deleted from disk (only the index entry "
        f"should be removed, not the file itself): {truly_missing}"
    )
