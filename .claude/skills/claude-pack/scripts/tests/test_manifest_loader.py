"""test_manifest_loader — schema validation + CLI merge."""

from __future__ import annotations

import argparse

import manifest_loader


def _ns(**kwargs) -> argparse.Namespace:
    base = {
        "version": None, "bundle_name": None,
        "skills": None, "agents": None, "hooks": None,
        "rules": None, "extra": None,
        "include_readme": None, "include_claudemd": None,
        "include_settings": None, "include_ck_config": None,
        "follow_shared": None, "include_shared": None,
    }
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_load_example_manifest(skill_root, tmp_root):
    """example manifest loads cleanly."""
    m = manifest_loader.load(skill_root / "assets" / "templates" / "manifest.example.yaml")
    assert isinstance(m, dict)
    assert m["version"] == "0.1.0"


def test_validate_rejects_bad_semver(tmp_root):
    errors = manifest_loader.validate({"version": "not-semver"}, tmp_root)
    assert any("MANIFEST_E001" in e for e in errors)


def test_validate_rejects_dev_version_default(tmp_root):
    """refuse 0.0.0-dev without --allow-dev-version."""
    errors = manifest_loader.validate({"version": "0.0.0-dev"}, tmp_root)
    assert any("MANIFEST_E002" in e for e in errors)


def test_validate_accepts_dev_version_with_flag(tmp_root):
    errors = manifest_loader.validate({"version": "0.0.0-dev"}, tmp_root,
                                       allow_dev_version=True)
    assert not any("MANIFEST_E002" in e for e in errors)


def test_validate_accepts_semver_build_metadata(tmp_root):
    """SemVer 2.0.0 build metadata allowed."""
    errors = manifest_loader.validate({"version": "1.0.0+build.42"}, tmp_root)
    assert not any("MANIFEST_E001" in e for e in errors)


def test_validate_absolute_path_rejected(tmp_root):
    """absolute extra path rejected."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "extra": ["/etc/passwd"]}, tmp_root,
    )
    assert any("MANIFEST_E020" in e for e in errors)


def test_validate_traversal_rejected(tmp_root):
    """path traversal rejected."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "extra": ["../foo"]}, tmp_root,
    )
    assert any("MANIFEST_E021" in e for e in errors)


def test_validate_rejects_bad_bundle_name(tmp_root):
    """bundle_name regex enforced."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "bundle_name": "../etc"}, tmp_root,
    )
    assert any("MANIFEST_E003" in e for e in errors)


def test_validate_rejects_duplicates(tmp_root):
    """duplicate entries rejected."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "skills": ["foo", "foo"]}, tmp_root,
    )
    assert any("MANIFEST_E012" in e for e in errors)


def test_validate_missing_skill(tmp_root):
    """non-existent skill rejected."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "skills": ["nonexistent-xyz"]}, tmp_root,
    )
    assert any("MANIFEST_E070" in e for e in errors)


def test_validate_rejects_unknown_top_level(tmp_root):
    errors = manifest_loader.validate(
        {"version": "1.0.0", "weird_field": True}, tmp_root,
    )
    assert any("MANIFEST_E060" in e for e in errors)


def test_validate_rejects_unknown_top_level_nested(tmp_root):
    errors = manifest_loader.validate(
        {"version": "1.0.0", "top_level": {"unknown_flag": True}}, tmp_root,
    )
    assert any("MANIFEST_E031" in e for e in errors)


def test_merge_cli_lists_dedupe():
    """csv split + dedupe."""
    merged = manifest_loader.merge_cli({}, _ns(skills="foo,bar,foo,baz"))
    assert merged["skills"] == ["foo", "bar", "baz"]


def test_merge_cli_boolean_none_keeps_manifest():
    """BooleanOptionalAction default None keeps manifest."""
    manifest = {"top_level": {"include_readme": True}}
    merged = manifest_loader.merge_cli(manifest, _ns(include_readme=None))
    assert merged["top_level"]["include_readme"] is True


def test_merge_cli_boolean_false_overrides():
    manifest = {"top_level": {"include_readme": True}}
    merged = manifest_loader.merge_cli(manifest, _ns(include_readme=False))
    assert merged["top_level"]["include_readme"] is False


def test_apply_defaults_auto_adds_scripts_schemas(tmp_root):
    """scripts/ + schemas/ auto-prepended to extra when present."""
    (tmp_root / ".claude" / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_root / ".claude" / "schemas").mkdir(parents=True, exist_ok=True)
    out = manifest_loader.apply_defaults({"version": "1.0.0"}, tmp_root)
    assert ".claude/scripts" in out["extra"]
    assert ".claude/schemas" in out["extra"]


def test_load_returns_empty_for_empty_file(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("", encoding="utf-8")
    assert manifest_loader.load(p) == {}


def test_load_raises_for_invalid_yaml(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("not: [valid yaml", encoding="utf-8")
    try:
        manifest_loader.load(p)
    except manifest_loader.ManifestError as e:
        assert str(e)
        return
    raise AssertionError("expected ManifestError for invalid YAML")
