"""test_release — unit gate for the root-CHANGELOG release-lifecycle engine (release.py).

Every assertion targets pure-text / argparse logic — no git, no network, no real-repo writes — so the
release-cut invariants (refuse-empty, refuse-existing, exact extract, bump arithmetic, --push needs
--apply, the product-spec-v tag prefix, and the REPO path-math) are locked deterministically.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import release


# --- REPO path-math (locked empirically, not assumed) -------------------------

def test_repo_resolves_to_repo_root():
    # scripts → release → skills → .claude → repo. The repo root is the dir that holds .claude/.
    assert (release.REPO / ".claude" / "pack.manifest.yaml").is_file()
    assert (release.REPO / "CHANGELOG.md").is_file()
    # release.py lives 4 parents below the repo root.
    assert release.REPO == Path(release.__file__).resolve().parents[4]


def test_tag_prefix_is_product_spec():
    assert release.TAG_PREFIX == "product-spec-v"


# --- extract_section ----------------------------------------------------------

CHANGELOG_SAMPLE = (
    "# Changelog\n\n"
    "## [Unreleased]\n\n"
    "## [2.0.0] — 2026-06-07\n\n"
    "BREAKING rename.\n\n"
    "### Added\n- thing\n\n"
    "## [1.4.0] — 2026-06-06\n\n"
    "older.\n"
)


def test_extract_section_exact_body():
    body = release.extract_section(CHANGELOG_SAMPLE, "2.0.0")
    assert body == "BREAKING rename.\n\n### Added\n- thing\n"
    # stops at the next heading — the 1.4.0 body must not leak in.
    assert "older." not in body


def test_extract_section_missing_raises():
    with pytest.raises(SystemExit):
        release.extract_section(CHANGELOG_SAMPLE, "9.9.9")


def test_extract_unreleased_empty():
    assert release.extract_section(CHANGELOG_SAMPLE, "Unreleased").strip() == ""


def test_section_exists():
    assert release._section_exists(CHANGELOG_SAMPLE, "2.0.0")
    assert not release._section_exists(CHANGELOG_SAMPLE, "3.0.0")


# --- lock_unreleased ----------------------------------------------------------

def test_lock_unreleased_success_keeps_empty_unreleased():
    text = "# CL\n\n## [Unreleased]\n\nnew feature\n\n## [1.0.0] — 2026-01-01\n\nold\n"
    out = release.lock_unreleased(text, "1.1.0", "2026-06-07")
    assert "## [Unreleased]\n\n## [1.1.0] — 2026-06-07" in out
    # the just-locked section now owns the former Unreleased body.
    assert release.extract_section(out, "1.1.0").strip() == "new feature"
    # a fresh, empty Unreleased remains on top.
    assert release.extract_section(out, "Unreleased").strip() == ""


def test_lock_unreleased_refuses_empty():
    text = "# CL\n\n## [Unreleased]\n\n## [1.0.0] — 2026-01-01\n\nold\n"
    with pytest.raises(SystemExit):
        release.lock_unreleased(text, "1.1.0", "2026-06-07")


def test_lock_unreleased_refuses_existing_version():
    text = "# CL\n\n## [Unreleased]\n\nstuff\n\n## [1.0.0] — 2026-01-01\n\nold\n"
    with pytest.raises(SystemExit):
        release.lock_unreleased(text, "1.0.0", "2026-06-07")


def test_lock_unreleased_refuses_missing_unreleased():
    text = "# CL\n\n## [1.0.0] — 2026-01-01\n\nold\n"
    with pytest.raises(SystemExit):
        release.lock_unreleased(text, "1.1.0", "2026-06-07")


# --- bump_version -------------------------------------------------------------

@pytest.mark.parametrize("base,level,expected", [
    ("1.4.0", "major", "2.0.0"),
    ("1.4.0", "minor", "1.5.0"),
    ("1.4.0", "patch", "1.4.1"),
    ("2.0.0", "major", "3.0.0"),
    ("1.2.3-rc.1", "patch", "1.2.4"),   # pre-release suffix stripped before arithmetic
    ("1.2.3-rc.1", "minor", "1.3.0"),
    ("1.2.3+build.5", "patch", "1.2.4"),       # build metadata stripped before arithmetic
    ("1.2.3-rc.1+build.5", "minor", "1.3.0"),  # both pre-release + build stripped
])
def test_bump_version(base, level, expected):
    assert release.bump_version(base, level) == expected


# --- manifest version round-trip ---------------------------------------------

def test_set_manifest_version_replaces_only_version_line():
    text = "schema_version: '1.0'\nversion: 1.4.0\nbundle_name: product-spec\n"
    out = release.set_manifest_version(text, "2.0.0")
    assert "version: 2.0.0" in out
    assert "schema_version: '1.0'" in out
    assert "bundle_name: product-spec" in out
    assert "1.4.0" not in out


# --- argparse contract --------------------------------------------------------

def test_push_requires_apply():
    with pytest.raises(SystemExit) as e:
        release.main(["--release", "2.0.0", "--push"])
    assert e.value.code == 2


def test_requires_a_mode():
    with pytest.raises(SystemExit) as e:
        release.main([])
    assert e.value.code == 2


def test_pre_release_label_appended_in_dry_run(capsys, monkeypatch, tmp_path):
    # --pre-release appends a label to the version; dry-run must echo it without writing.
    # Point CHANGELOG/MANIFEST at temp files so the dry-run has a non-empty [Unreleased].
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## [Unreleased]\n\n- a pending change\n\n## [2.4.0] — 2026-06-01\n\n- prior\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "pack.manifest.yaml"
    manifest.write_text("version: 2.4.0\nbundle_name: product-spec\n", encoding="utf-8")
    monkeypatch.setattr(release, "CHANGELOG", changelog)
    monkeypatch.setattr(release, "MANIFEST", manifest)

    assert release.main(["--release", "2.5.0", "--pre-release", "rc.1"]) == 0
    out = capsys.readouterr().out
    assert "2.5.0-rc.1" in out
    assert "dry-run" in out  # confirms nothing was written
    # dry-run must not touch the temp files
    assert "[2.5.0-rc.1]" not in changelog.read_text(encoding="utf-8")


def test_extract_on_real_changelog_runs(capsys):
    # --extract reads the real root CHANGELOG; the bundle's current top released version must extract.
    from verify_skill_versions import changelog_top_version
    top = changelog_top_version(release.CHANGELOG)
    assert release.main(["--extract", top]) == 0
    out = capsys.readouterr().out
    assert out  # non-empty section body
