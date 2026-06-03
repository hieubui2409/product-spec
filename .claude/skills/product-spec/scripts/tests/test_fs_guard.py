"""Tests for the soft-fence path-assert.

`fs_guard._assert_under_docs_product` is the shared chokepoint that keeps every
SCRIPT-driven disk write under `<root>/docs/product/`. A resolved path that
escapes (absolute elsewhere, `..` traversal, or a symlink pointing outside) is
refused with a friendly error BEFORE any bytes hit disk. The three real write
chokepoints (render_html._write_visual, render_export.write_export,
generate_templates) call it; in-tree writes must remain unaffected.
"""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from fs_guard import FenceError, assert_under_docs_product  # noqa: E402
import render_html  # noqa: E402
import render_export  # noqa: E402
import generate_templates  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


# ---------- _assert_under_docs_product: allow ----------

def test_path_assert_allows_under_docs_product(tmp_path):
    root = tmp_path
    target = root / "docs" / "product" / "visuals" / "tree.html"
    # Returns the resolved path; never raises for an in-tree target.
    out = assert_under_docs_product(target, root)
    assert out == target.resolve()


def test_path_assert_allows_nested_subdir(tmp_path):
    root = tmp_path
    target = root / "docs" / "product" / "exports" / "deep" / "x.md"
    assert assert_under_docs_product(target, root) == target.resolve()


def test_path_assert_allows_the_dir_root_itself(tmp_path):
    # docs/product itself is in-tree (boundary, not escape).
    root = tmp_path
    target = root / "docs" / "product"
    assert assert_under_docs_product(target, root) == target.resolve()


# ---------- _assert_under_docs_product: block ----------

def test_path_assert_blocks_absolute_escape(tmp_path):
    root = tmp_path
    with pytest.raises(FenceError) as exc:
        assert_under_docs_product(Path("/tmp/evil.html"), root)
    # Friendly message names the offending path and the allowed boundary.
    msg = str(exc.value)
    assert "docs/product" in msg
    assert "evil.html" in msg


def test_path_assert_blocks_dotdot_traversal(tmp_path):
    root = tmp_path
    # docs/product/../../escape.md resolves to <root>/escape.md → outside.
    target = root / "docs" / "product" / ".." / ".." / "escape.md"
    with pytest.raises(FenceError):
        assert_under_docs_product(target, root)


def test_path_assert_blocks_sibling_of_docs_product(tmp_path):
    root = tmp_path
    # docs/other is inside the project but OUTSIDE docs/product.
    target = root / "docs" / "other" / "x.md"
    with pytest.raises(FenceError):
        assert_under_docs_product(target, root)


@pytest.mark.bug_class  # cross-skill invariant: symlink-escape refusal
def test_path_assert_blocks_symlink_escape(tmp_path):
    root = tmp_path
    outside = tmp_path / "outside"
    outside.mkdir()
    dp = root / "docs" / "product"
    dp.mkdir(parents=True)
    # A symlink under docs/product/ that points outside the fence.
    link = dp / "link"
    link.symlink_to(outside, target_is_directory=True)
    target = link / "evil.md"
    with pytest.raises(FenceError):
        assert_under_docs_product(target, root)


def test_path_assert_blocks_prefix_lookalike(tmp_path):
    # `docs/product-extra` shares the string prefix but is a SEPARATE dir; a
    # naive startswith check would wrongly allow it. Must be blocked.
    root = tmp_path
    target = root / "docs" / "product-extra" / "x.md"
    with pytest.raises(FenceError):
        assert_under_docs_product(target, root)


def test_path_assert_no_write_on_block(tmp_path):
    # The guard refuses BEFORE any bytes are written — the target must not exist.
    root = tmp_path
    target = root / "escape.md"
    with pytest.raises(FenceError):
        assert_under_docs_product(target, root)
    assert not target.exists()


# ---------- real chokepoint: render_html._write_visual ----------

def test_write_visual_in_tree_writes(tmp_path):
    out = render_html._write_visual(tmp_path, "tree.html", "<html>ok</html>")
    assert out.exists()
    assert out.read_text(encoding="utf-8") == "<html>ok</html>"
    assert out.is_relative_to(tmp_path / "docs" / "product")


def test_write_visual_blocks_escape(tmp_path):
    # A filename carrying traversal must be refused, no file written.
    with pytest.raises(FenceError):
        render_html._write_visual(tmp_path, "../../escape.html", "<html>x</html>")
    assert not (tmp_path / "escape.html").exists()


# ---------- real chokepoint: render_export.write_export ----------

def test_write_export_in_tree_writes(tmp_path):
    # Copy the valid fixture into a writable tree, then export under it.
    import shutil
    root = tmp_path / "proj"
    shutil.copytree(VALID, root)
    out = render_export.write_export(root, "PRD-AUTH", None, "context", "struct", "md", "en")
    assert out.exists()
    assert out.is_relative_to(root / "docs" / "product")


# ---------- real chokepoint: generate_templates ----------

def test_generate_templates_in_tree_writes(tmp_path):
    import subprocess
    root = tmp_path / "proj"
    (root / "docs" / "product" / "prds").mkdir(parents=True)
    # Minimal PRD parent so a story can be allocated; simpler: generate a PRD.
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "generate_templates.py"),
         "--root", str(root), "--type", "prd", "--slug", "PAY", "--write"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    import json
    resp = json.loads(proc.stdout)
    assert resp["written"] is True
    written = root / resp["path"]
    assert written.exists()
    assert written.is_relative_to(root / "docs" / "product")
