"""Tests for visuals_retention.py — latest-alias, staleness banner,
content-hash reuse, and --clean retention.

Synthetic fixtures only; no real PO numbers embedded.
All render output goes to tmp_path dirs.
"""

import hashlib
import sys
import time
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import visuals_retention  # noqa: E402  (module under test)


# ── helpers ──────────────────────────────────────────────────────────────────

def _visuals_dir(root: Path) -> Path:
    d = root / "docs" / "product" / "visuals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_render(root: Path, view: str, content: str, ts: str) -> Path:
    """Write a fake timestamped render file and return its path."""
    vdir = _visuals_dir(root)
    p = vdir / f"{view}-{ts}.html"
    p.write_text(content, encoding="utf-8")
    return p


def _minimal_graph(node_ids: list[str]) -> dict:
    """Minimal synthetic graph with the given node ids."""
    return {
        "product": {"name": "SyntheticSpec"},
        "nodes": [{"id": nid, "type": "story", "title": f"T-{nid}"} for nid in node_ids],
        "edges": [],
    }


# ── 1. latest alias points to newest render ───────────────────────────────

def test_latest_alias_points_to_newest_render(tmp_path):
    """After two renders the -latest.html must contain the NEWEST render's content."""
    root = tmp_path

    # First render
    p1 = _write_render(root, "tree", "<html>render-v1</html>", "20260101T000000Z")
    latest1 = visuals_retention.latest_alias(p1)
    assert latest1.name == "tree-latest.html"
    assert latest1.read_text(encoding="utf-8") == "<html>render-v1</html>"

    # Second (newer) render — content differs
    p2 = _write_render(root, "tree", "<html>render-v2</html>", "20260101T000001Z")
    latest2 = visuals_retention.latest_alias(p2)
    assert latest2.name == "tree-latest.html"
    # -latest must now hold the v2 content, not v1
    assert latest2.read_text(encoding="utf-8") == "<html>render-v2</html>"


# ── 2. staleness banner when graph drifted ─────────────────────────────────

def test_staleness_banner_when_graph_drifts(tmp_path):
    """After a render, adding nodes to the graph produces a banner that
    names the drift count explicitly."""
    root = tmp_path
    view = "tree"

    # Build a baseline graph signature (3 nodes)
    baseline_graph = _minimal_graph(["S1", "S2", "S3"])

    # Write a render and record its baseline node signature
    html_content = "<html>original render</html>"
    out_path = _write_render(root, view, html_content, "20260101T000000Z")
    visuals_retention.save_render_signature(root, view, out_path, baseline_graph)

    # Mutate the graph (add 2 nodes → drift == 2)
    drifted_graph = _minimal_graph(["S1", "S2", "S3", "S4", "S5"])

    banner = visuals_retention.staleness_banner(root, view, drifted_graph)
    assert banner != "", "expected a non-empty stale banner when graph drifted"
    assert "2" in banner, f"banner must contain the drift count (2), got: {banner!r}"
    assert "stale" in banner.lower() or "drifted" in banner.lower(), (
        f"banner must mention stale/drifted state, got: {banner!r}"
    )


# ── 3. no banner when graph is in sync ────────────────────────────────────

def test_no_banner_when_in_sync(tmp_path):
    """When the graph has not changed since the render, the banner must be empty."""
    root = tmp_path
    view = "tree"

    graph = _minimal_graph(["S1", "S2"])
    html_content = "<html>fresh render</html>"
    out_path = _write_render(root, view, html_content, "20260101T000000Z")
    visuals_retention.save_render_signature(root, view, out_path, graph)

    # Same graph — no drift
    banner = visuals_retention.staleness_banner(root, view, graph)
    assert banner == "", f"expected empty banner for in-sync graph, got: {banner!r}"


# ── 4. content hash reuse skips re-render ─────────────────────────────────

def test_content_hash_reuse_skips_rerender(tmp_path):
    """When the HTML content is byte-for-byte identical to the last render,
    reuse_if_unchanged must return the existing file path (not None)
    and must NOT create a new timestamped file."""
    root = tmp_path
    view = "tree"
    vdir = _visuals_dir(root)

    html = "<html>unchanged content</html>"

    # First write
    p1 = _write_render(root, view, html, "20260101T000000Z")
    visuals_retention.record_content_hash(root, view, p1, html)

    # Attempt second write of identical content
    reused = visuals_retention.reuse_if_unchanged(root, view, html)
    assert reused is not None, (
        "expected reuse_if_unchanged to return existing path for identical content"
    )
    assert reused == p1, f"expected reused path to be {p1}, got {reused}"

    # No new timestamped files beyond the original
    all_renders = sorted(vdir.glob(f"{view}-2*.html"))
    assert len(all_renders) == 1, (
        f"expected exactly 1 timestamped render file, found {len(all_renders)}: {all_renders}"
    )


# ── 5. --clean prunes old keeps latest ────────────────────────────────────

def test_clean_prunes_old_keeps_latest(tmp_path):
    """With keep=3 and 6 timestamped renders, --clean must retain the 3 newest
    plus the -latest alias; the 3 oldest must be deleted."""
    root = tmp_path
    view = "scope"
    vdir = _visuals_dir(root)
    keep_n = 3

    # Create 6 timestamped renders (oldest → newest)
    renders = []
    for i in range(6):
        ts = f"2026010{i+1}T000000Z"
        p = _write_render(root, view, f"<html>render-{i}</html>", ts)
        renders.append(p)

    # Create a -latest alias pointing to the newest
    visuals_retention.latest_alias(renders[-1])

    # Run clean
    deleted = visuals_retention.clean_old_renders(root, view, keep=keep_n)

    # 3 oldest must be deleted
    assert len(deleted) == 3, f"expected 3 deleted, got {len(deleted)}: {deleted}"
    for p in renders[:3]:
        assert not p.exists(), f"old render {p.name} should have been deleted"

    # 3 newest must survive
    for p in renders[3:]:
        assert p.exists(), f"recent render {p.name} should have survived"

    # -latest must survive
    latest = vdir / f"{view}-latest.html"
    assert latest.exists(), "-latest.html must survive --clean"


# ── 6. --clean on empty dir does not crash ────────────────────────────────

def test_clean_on_empty_dir_no_crash(tmp_path):
    """Running clean when no renders exist must be a no-op (return empty list,
    no exception, does not create any file)."""
    root = tmp_path
    _visuals_dir(root)  # ensure dir exists but is empty
    view = "tree"

    deleted = visuals_retention.clean_old_renders(root, view, keep=5)
    assert deleted == [], f"expected empty deleted list on empty dir, got {deleted}"
