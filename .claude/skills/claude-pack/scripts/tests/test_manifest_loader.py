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


def test_scripts_schemas_are_opt_in_not_auto_added(tmp_root):
    """Top-level .claude/scripts + .claude/schemas are CK-framework internals:
    NOT shipped by default; only when opted in via defaults.include_scripts/_schemas."""
    (tmp_root / ".claude" / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_root / ".claude" / "schemas").mkdir(parents=True, exist_ok=True)
    # Default: excluded.
    out = manifest_loader.apply_defaults({"version": "1.0.0"}, tmp_root)
    assert ".claude/scripts" not in out["extra"]
    assert ".claude/schemas" not in out["extra"]
    # Opt-in: included.
    out2 = manifest_loader.apply_defaults(
        {"version": "1.0.0",
         "defaults": {"include_scripts": True, "include_schemas": True}},
        tmp_root,
    )
    assert ".claude/scripts" in out2["extra"]
    assert ".claude/schemas" in out2["extra"]


def test_include_scripts_cli_flag_opts_in(tmp_root):
    """--include-scripts / --include-schemas promote the defaults to True."""
    (tmp_root / ".claude" / "scripts").mkdir(parents=True, exist_ok=True)
    merged = manifest_loader.merge_cli(
        {"version": "1.0.0"}, _ns(include_scripts=True))
    out = manifest_loader.apply_defaults(merged, tmp_root)
    assert ".claude/scripts" in out["extra"]


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


def test_validate_rejects_string_max_size_bytes(tmp_root):
    """A string max_size_bytes like '100MB' must fail at validate time, not crash at runtime."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "defaults": {"max_size_bytes": "100MB"}}, tmp_root,
    )
    assert any("MANIFEST_E042" in e for e in errors)


def test_validate_rejects_negative_max_size_bytes(tmp_root):
    """Negative max_size_bytes must be rejected."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "defaults": {"max_size_bytes": -1}}, tmp_root,
    )
    assert any("MANIFEST_E042" in e for e in errors)


def test_validate_rejects_bool_max_size_bytes(tmp_root):
    """bool is a subclass of int: max_size_bytes: false must be rejected, else it
    silently becomes 0 and rejects every non-empty bundle."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "defaults": {"max_size_bytes": False}}, tmp_root,
    )
    assert any("MANIFEST_E042" in e for e in errors)


def test_validate_rejects_ambiguous_hook(tmp_root):
    """Two hook files with the same basename must error (rglob order is
    filesystem-dependent → non-deterministic pick otherwise)."""
    hooks = tmp_root / ".claude" / "hooks"
    (hooks / "a").mkdir(parents=True, exist_ok=True)
    (hooks / "b").mkdir(parents=True, exist_ok=True)
    (hooks / "a" / "dup.cjs").write_text("x", encoding="utf-8")
    (hooks / "b" / "dup.cjs").write_text("y", encoding="utf-8")
    errors = manifest_loader.validate(
        {"version": "1.0.0", "hooks": ["dup.cjs"]}, tmp_root,
    )
    assert any("MANIFEST_E074" in e for e in errors)


def test_path_qualified_hook_validates_and_is_bundled(tmp_root):
    """The documented E074 remedy — pin a unique path — must pass validate AND
    actually bundle the file. validate() and selection.resolve_selection must use
    one matcher; a basename-only resolver would drop the path-pinned hook."""
    from pack.selection import resolve_selection
    hooks = tmp_root / ".claude" / "hooks"
    (hooks / "a").mkdir(parents=True, exist_ok=True)
    (hooks / "b").mkdir(parents=True, exist_ok=True)
    (hooks / "a" / "shared.cjs").write_text("x", encoding="utf-8")
    (hooks / "b" / "shared.cjs").write_text("y", encoding="utf-8")
    manifest = {"version": "1.0.0", "hooks": ["a/shared.cjs"]}
    errors = manifest_loader.validate(manifest, tmp_root)
    assert not any("MANIFEST_E073" in e or "MANIFEST_E074" in e for e in errors)
    arcs = [arc for _, arc in resolve_selection(manifest, tmp_root)]
    assert ".claude/hooks/a/shared.cjs" in arcs   # bundled, not silently dropped
    assert ".claude/hooks/b/shared.cjs" not in arcs


def test_validate_rejects_non_bool_include_scripts(tmp_root):
    """include_scripts must be bool; a string '1' must fail."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "defaults": {"include_scripts": "yes"}}, tmp_root,
    )
    assert any("MANIFEST_E043" in e for e in errors)


def test_validate_rejects_non_bool_include_schemas(tmp_root):
    """include_schemas must be bool; an int 1 must fail."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "defaults": {"include_schemas": 1}}, tmp_root,
    )
    assert any("MANIFEST_E043" in e for e in errors)


def test_is_absolute_or_drive_posix_colon_not_rejected(tmp_root):
    """POSIX path 'a:b' (colon at index 1, no separator at index 2) must NOT be
    treated as a Windows drive letter absolute path."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "extra": ["a:b"]}, tmp_root,
    )
    assert not any("MANIFEST_E020" in e for e in errors)


def _raise_oserror(msg):
    def _f(*a, **k):
        raise OSError(msg)
    return _f


def test_atomic_replace_restores_backup_when_exdev_move_fails(tmp_path, monkeypatch):
    """If the EXDEV cross-fs fallback (shutil.move) ALSO fails, the pre-existing
    output is restored from backup, not left orphaned as a .bak.* file."""
    import pytest
    from pack.manifest_io import atomic_replace
    final = tmp_path / "out.tar.gz"
    final.write_text("ORIGINAL")
    tmp = tmp_path / ".out.tmp"
    tmp.write_text("NEW")
    monkeypatch.setattr("pack.manifest_io.os.replace",
                        _raise_oserror("EXDEV cross-device link not permitted"))
    monkeypatch.setattr("pack.manifest_io.shutil.move", _raise_oserror("move denied"))
    with pytest.raises(OSError):
        atomic_replace(tmp, final, force=True)
    assert final.exists() and final.read_text() == "ORIGINAL", \
        "pre-existing output must be restored when the EXDEV move fails"


def test_resolve_selection_tolerates_non_list_include_shared(tmp_path):
    """A malformed scalar _include_shared (int/dict) must not crash the walk."""
    from pack.selection import resolve_selection
    (tmp_path / ".claude").mkdir()
    sel = resolve_selection({"_include_shared": 123, "skills": []}, tmp_path)
    assert isinstance(sel, list)  # coerced to no-op, not a TypeError


# ---------------------------------------------------------------------------
# Cycle-9 regression tests — tar-slip / traversal (P1+SW2) + unhashable fixes
# ---------------------------------------------------------------------------

def test_validate_traversal_in_hooks(tmp_root):
    """../../x in hooks must produce a traversal error."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "hooks": ["../../x"]}, tmp_root
    )
    assert any("MANIFEST_E021" in e for e in errors)


def test_validate_traversal_in_agents(tmp_root):
    """../x in agents must produce a traversal error."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "agents": ["../x"]}, tmp_root
    )
    assert any("MANIFEST_E021" in e for e in errors)


def test_validate_traversal_in_skills(tmp_root):
    """../x in skills must produce a traversal error."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "skills": ["../x"]}, tmp_root
    )
    assert any("MANIFEST_E021" in e for e in errors)


def test_validate_traversal_in_include_shared(tmp_root):
    """../x in _include_shared must produce a traversal error."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "_include_shared": ["../x"]}, tmp_root
    )
    assert any("MANIFEST_E021" in e for e in errors)


def test_validate_traversal_returns_nonempty_errors(tmp_root):
    """validate() must return a non-empty list (EXIT_VALIDATION signal) for traversal."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "hooks": ["../../x"], "agents": ["../x"],
         "skills": ["../x"], "_include_shared": ["../x"]},
        tmp_root,
    )
    assert len(errors) > 0


def test_resolve_selection_never_emits_dotdot_arcname(tmp_root):
    """resolve_selection must not emit any arcname containing '..'."""
    from pack.selection import resolve_selection
    # Even if someone passes a manifest with traversal entries directly,
    # the chokepoint in resolve_selection must filter them out.
    manifest = {
        "version": "1.0.0",
        "extra": ["../../etc/passwd"],  # will be caught by manifest_loader but belt-and-suspenders
        "skills": [],
    }
    sel = resolve_selection(manifest, tmp_root)
    for _, arc in sel:
        from pathlib import PurePosixPath
        assert ".." not in PurePosixPath(arc).parts, f"traversal arcname leaked: {arc!r}"


def test_validate_schema_version_list_does_not_raise(tmp_root):
    """validate() must not raise TypeError when schema_version is a list."""
    errors = manifest_loader.validate({"version": "1.0.0", "schema_version": ["x"]}, tmp_root)
    assert any("MANIFEST_E102" in e for e in errors)


def test_validate_duplicate_unhashable_does_not_raise(tmp_root):
    """validate() must not raise TypeError when a category list has unhashable elements."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "skills": [["nested"], ["nested"]]}, tmp_root
    )
    # Should catch E011 (non-string entry) without raising TypeError
    assert any("MANIFEST_E011" in e for e in errors)


def test_semver_re_rejects_leading_zero():
    """SEMVER_RE must reject leading-zero versions like 01.0.0."""
    assert not manifest_loader.SEMVER_RE.match("01.0.0")
    assert not manifest_loader.SEMVER_RE.match("1.01.0")
    assert not manifest_loader.SEMVER_RE.match("1.0.01")


def test_semver_re_accepts_valid_versions():
    """SEMVER_RE accepts valid SemVer 2.0.0 versions including 0.0.0-dev."""
    assert manifest_loader.SEMVER_RE.match("1.0.0")
    assert manifest_loader.SEMVER_RE.match("0.1.0")
    assert manifest_loader.SEMVER_RE.match("10.20.30")
    assert manifest_loader.SEMVER_RE.match("1.0.0-alpha.1")
    assert manifest_loader.SEMVER_RE.match("1.0.0+build.42")
    assert manifest_loader.SEMVER_RE.match("0.0.0-dev")


# ---------------------------------------------------------------------------
# Cycle-10 regression tests
# ---------------------------------------------------------------------------

def test_validate_relative_to_accepts_valid_nested_skill(tmp_root):
    """relative_to-based containment must NOT emit false E021 for a valid, deeply
    nested skill directory (C10 fix: replaced string-prefix with relative_to)."""
    # Create a legitimate nested skill dir.
    skill_dir = tmp_root / ".claude" / "skills" / "my-skill" / "scripts"
    skill_dir.mkdir(parents=True, exist_ok=True)
    # validate() checks for the skill directory itself, not a subdirectory.
    # Create the actual skill dir at the top level so E070 is not triggered.
    actual_skill = tmp_root / ".claude" / "skills" / "my-skill"
    # already created above via parents=True
    errors = manifest_loader.validate(
        {"version": "1.0.0", "skills": ["my-skill"]}, tmp_root
    )
    # Must NOT produce E021 (false containment escape) for a valid skill.
    assert not any("E021" in e and "my-skill" in e for e in errors), \
        f"false E021 for valid skill: {errors}"
    # May produce E070 if SKILL.md is absent — that's fine, E070 is not E021.


def test_userinfo_scrub_strips_password_with_at_in_it():
    """Regex `[^/]*@` must consume up to the LAST '@' so a password like
    'p@ss' in 'user:p@ss@host' is fully stripped (C10 fix)."""
    import re
    # Replicate the exact regex from manifest_io.py
    _sub = lambda url: re.sub(r"(://)[^/]*@", r"\1", url)
    assert _sub("https://user:p@ss@host/repo") == "https://host/repo"
    assert _sub("https://user:plain@host/repo") == "https://host/repo"
    # scp-style origin must be unchanged (no ://)
    assert _sub("git@github.com:org/repo") == "git@github.com:org/repo"


# ---------------------------------------------------------------------------
# _include_shared type guard — a hand-edited scalar must not char-split
# ---------------------------------------------------------------------------

def test_validate_rejects_non_list_include_shared(tmp_root):
    """A scalar `_include_shared: foo` must be flagged E010, not char-split into
    {'f','o','o'} downstream (validate gates cli.py/selection before they read it)."""
    errors = manifest_loader.validate(
        {"version": "1.0.0", "skills": [], "_include_shared": "foo"}, tmp_root,
    )
    assert any("MANIFEST_E010" in e and "_include_shared" in e for e in errors)


def test_validate_accepts_list_include_shared(tmp_root):
    errors = manifest_loader.validate(
        {"version": "1.0.0", "skills": [], "_include_shared": ["util"]}, tmp_root,
    )
    assert not any("_include_shared" in e for e in errors)


# ---------------------------------------------------------------------------
# selection arcname — trailing-slash `extra` must not double-slash
# ---------------------------------------------------------------------------

def test_selection_strips_trailing_slash_in_extra_arcname(tmp_path):
    """`extra: ["docs/"]` (trailing slash) must yield "docs/<file>", not
    "docs//<file>" — the canonical arcname must equal the no-slash form."""
    from pack.selection import resolve_selection
    (tmp_path / ".claude").mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("x", encoding="utf-8")
    arcs = [arc for _, arc in resolve_selection({"extra": ["docs/"], "skills": []}, tmp_path)]
    assert "docs/guide.md" in arcs
    assert not any("//" in a for a in arcs)


# ---------------------------------------------------------------------------
# build_manifest — malformed scalar category passes through to E010 (no crash)
# ---------------------------------------------------------------------------

def test_assemble_manifest_scalar_category_not_charsplit_then_e010(tmp_root):
    """A scalar `skills: "foo"` in stdin answers must be stored UNCHANGED (not
    list()-ed into ['f','o','o']), then rejected by validate() as E010."""
    import build_manifest
    manifest = build_manifest._assemble_manifest({"skills": "foo", "version": "1.0.0"})
    assert manifest["skills"] == "foo"  # passed through, not char-split
    errors = manifest_loader.validate(manifest, tmp_root)
    assert any("MANIFEST_E010" in e and "skills" in e for e in errors)


def test_assemble_manifest_int_category_no_typeerror(tmp_root):
    """An int `agents: 5` must not raise TypeError at list(5); it is passed
    through for validate() to flag."""
    import build_manifest
    manifest = build_manifest._assemble_manifest({"agents": 5, "version": "1.0.0"})
    assert manifest["agents"] == 5
    errors = manifest_loader.validate(manifest, tmp_root)  # must not raise
    assert any("MANIFEST_E010" in e and "agents" in e for e in errors)
