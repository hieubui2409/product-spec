"""test_lens_product_memory.py — health lens over docs/product/.memory (the PO's
spec-state store, distinct from the assistant `memory` lens). Read-only;
fixture-driven with synthetic .memory trees (no real PO data)."""
import json
import os
import sys
import time
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))

import lens_product_memory  # noqa: E402
from telemetry_render import render_md, render_ascii  # noqa: E402


def _make_store(root: Path, *, files=(), cache_files=0, findings=0) -> Path:
    base = root / "docs" / "product" / ".memory"
    base.mkdir(parents=True, exist_ok=True)
    for name in files:
        (base / name).write_text("{}", encoding="utf-8")
    if cache_files:
        cdir = base / "critique-lens-cache"
        cdir.mkdir(exist_ok=True)
        for i in range(cache_files):
            (cdir / f"c{i}.json").write_text('{"x":1}', encoding="utf-8")
    if findings:
        # Mirror the LIVE index shape: {"entries": {<id>: {...}}, "version": ...}.
        (base / "critique-findings-index.json").write_text(
            json.dumps({"entries": {f"F-{i}": {"id": i} for i in range(findings)}, "version": 1}),
            encoding="utf-8")
    return base


def test_absent_store_is_flagged(tmp_path):
    a = lens_product_memory.gather(root=str(tmp_path))  # no docs/product/.memory
    assert a["present"] is False
    assert a["status"] == "RED"
    assert set(a["missing_files"]) == set(lens_product_memory.EXPECTED_FILES)
    assert a["last_validated_age_days"] is None


def test_populated_store_is_green(tmp_path):
    _make_store(tmp_path, files=lens_product_memory.EXPECTED_FILES, cache_files=3, findings=5)
    a = lens_product_memory.gather(root=str(tmp_path))
    assert a["present"] is True
    assert a["missing_files"] == []
    assert a["cache_count"] == 3 and a["cache_bytes"] > 0
    assert a["findings_count"] == 5
    assert a["last_validated_age_days"] == 0  # just written
    assert a["status"] == "GREEN"


def test_partial_store_lists_missing(tmp_path):
    _make_store(tmp_path, files=("last_validated.json",))
    a = lens_product_memory.gather(root=str(tmp_path))
    assert a["present"] is True
    assert "preferences.yaml" in a["missing_files"]
    assert "last_validated.json" not in a["missing_files"]
    assert a["issue_count"] >= 1


def test_stale_baseline_flagged(tmp_path):
    """A last_validated.json older than STALE_DAYS raises stale_baseline + adds an
    issue — even when every expected file is present."""
    _make_store(tmp_path, files=lens_product_memory.EXPECTED_FILES)
    lv = tmp_path / "docs" / "product" / ".memory" / "last_validated.json"
    old = time.time() - (lens_product_memory.STALE_DAYS + 5) * 86400
    os.utime(lv, (old, old))
    a = lens_product_memory.gather(root=str(tmp_path))
    assert a["last_validated_age_days"] > lens_product_memory.STALE_DAYS
    assert a["stale_baseline"] is True
    assert a["issue_count"] >= 1  # the otherwise-complete store is no longer GREEN-on-everything


def test_render_surfaces_product_memory_vi_and_en(tmp_path):
    _make_store(tmp_path, files=lens_product_memory.EXPECTED_FILES, cache_files=1, findings=2)
    a = lens_product_memory.gather(root=str(tmp_path))
    vi = render_md([a], lang="vi")
    en = render_md([a], lang="en")
    assert "## Bộ nhớ sản phẩm" in vi
    assert "## Product Memory" in en
    assert "Product Memory" not in vi  # no EN label leak into the VI render
    ascii_out = render_ascii([a])
    assert "BỘ NHỚ SẢN PHẨM" in ascii_out
