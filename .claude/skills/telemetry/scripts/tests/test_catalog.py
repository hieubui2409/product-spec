"""test_catalog.py — catalog loader + slug↔dir normalization. Verifies BOTH
recorded forms (prefixed slug and bare dir) resolve to the canonical dir, and
that unknown skills are returned flat (never dropped).
"""
import importlib
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))
FIX = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def cat_mod(monkeypatch):
    monkeypatch.setenv("CK_SKILLS_DIR", str(FIX / "skills"))
    for m in ("telemetry_paths", "catalog"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import catalog
    importlib.reload(catalog)
    return catalog


def test_loads_dirs_and_slug_map(cat_mod):
    cat = cat_mod.load_catalog(FIX / "skills")
    assert cat["dirs"] == {"product-spec", "product-spec-critique", "release", "telemetry"}
    assert cat["slug_to_dir"]["cleanmatic:product-spec"] == "product-spec"
    # all fixture skills carry cleanmatic: names → all owned
    assert cat["owned"] == {"product-spec", "product-spec-critique", "release", "telemetry"}


def test_external_skill_is_not_owned(cat_mod, tmp_path):
    (tmp_path / "ck-plan").mkdir()
    (tmp_path / "ck-plan" / "SKILL.md").write_text("---\nname: ck:plan\n---\n")
    (tmp_path / "product-spec").mkdir()
    (tmp_path / "product-spec" / "SKILL.md").write_text("---\nname: cleanmatic:product-spec\n---\n")
    cat = cat_mod.load_catalog(tmp_path)
    assert cat["owned"] == {"product-spec"}  # ck-plan excluded


def test_prefixed_slug_and_bare_dir_resolve_same(cat_mod):
    cat = cat_mod.load_catalog(FIX / "skills")
    assert cat_mod.to_dir_id("cleanmatic:product-spec", cat) == "product-spec"
    assert cat_mod.to_dir_id("product-spec", cat) == "product-spec"


def test_external_prefix_keeps_hyphen_form_when_dir_exists(cat_mod, tmp_path, monkeypatch):
    # Simulate an external skill whose dir keeps a hyphenated prefix (ck-plan).
    (tmp_path / "ck-plan").mkdir()
    (tmp_path / "ck-plan" / "SKILL.md").write_text("---\nname: ck:plan\n---\n")
    cat = cat_mod.load_catalog(tmp_path)
    assert cat_mod.to_dir_id("ck:plan", cat) == "ck-plan"


def test_unknown_skill_returned_flat_not_dropped(cat_mod):
    cat = cat_mod.load_catalog(FIX / "skills")
    assert cat_mod.to_dir_id("foo:bar", cat) == "foo-bar"
    assert cat_mod.to_dir_id("", cat) == ""


def test_missing_skills_dir_is_fail_soft(cat_mod, tmp_path):
    cat = cat_mod.load_catalog(tmp_path / "nope")
    assert cat["dirs"] == set()
    assert cat_mod.to_dir_id("anything", cat) == "anything"
