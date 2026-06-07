"""test_version_sync — A4 PR-time gate: each skill's SKILL.md metadata.version must
equal its own CHANGELOG.md top released heading `## [X.Y.Z]`.

Scope = every SHIPPED skill (now four — telemetry ships too). The per-skill changelog
(`.claude/skills/<skill>/CHANGELOG.md`) is pinned to that skill's own version; the
*bundle/release* history now lives in the repo-root `/CHANGELOG.md`, whose top heading is
the bundle identity and must equal `version:` in `.claude/pack.manifest.yaml`. The release
skill is no longer special-cased — its skill changelog tracks the skill version like the rest.

Rides the existing `cross-skill-bug-class.yml` release leg via `@pytest.mark.bug_class`.
Reuses verify_skill_versions' frontmatter parser + changelog helper (no fork).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from verify_skill_versions import ChangelogError, _frontmatter, changelog_top_version

REPO_ROOT = Path(__file__).resolve().parents[5]
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Every shipped skill's CHANGELOG top == its SKILL.md version (telemetry now ships too).
VERSION_SYNCED_SKILLS = ("product-spec", "product-spec-critique", "release", "telemetry")


def _skill_version(skill: str) -> str:
    fm = _frontmatter(SKILLS_DIR / skill / "SKILL.md")
    return str(fm["metadata"]["version"])


# --- helper unit tests (fixtures first — RED before the real wiring) ----------

def _write(p: Path, body: str) -> Path:
    p.write_text(body, encoding="utf-8")
    return p


def test_changelog_skips_unreleased(tmp_path):
    cl = _write(tmp_path / "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\n## [2.2.0] — 2026-06-04\n")
    assert changelog_top_version(cl) == "2.2.0"


def test_changelog_skips_prerelease_and_build_metadata(tmp_path):
    cl = _write(tmp_path / "CHANGELOG.md", "## [Unreleased]\n## [1.3.0-rc.1]\n## [1.2.0+build7]\n## [1.2.0]\n")
    # rc/build headings are not plain [X.Y.Z] → skipped; first released semver wins.
    assert changelog_top_version(cl) == "1.2.0"


def test_changelog_missing_file_raises(tmp_path):
    with pytest.raises(ChangelogError):
        changelog_top_version(tmp_path / "nope.md")


def test_changelog_no_semver_heading_raises(tmp_path):
    cl = _write(tmp_path / "CHANGELOG.md", "# Changelog\n\n## [Unreleased]\n\nnothing released yet\n")
    with pytest.raises(ChangelogError):
        changelog_top_version(cl)


def test_drift_detected_vs_aligned(tmp_path):
    # Drift: SKILL says 2.3.0 but CHANGELOG top is 2.2.0 → mismatch.
    skill = tmp_path / "SKILL.md"
    _write(skill, '---\nname: x\nmetadata:\n  version: "2.3.0"\n---\n# x\n')
    cl = _write(tmp_path / "CHANGELOG.md", "## [Unreleased]\n## [2.2.0]\n")
    assert str(_frontmatter(skill)["metadata"]["version"]) != changelog_top_version(cl)
    # Aligned: bump CHANGELOG to match → equal.
    _write(cl, "## [Unreleased]\n## [2.3.0]\n## [2.2.0]\n")
    assert str(_frontmatter(skill)["metadata"]["version"]) == changelog_top_version(cl)


# --- real-tree gate (the actual A4 assertion) ---------------------------------

@pytest.mark.bug_class
@pytest.mark.parametrize("skill", VERSION_SYNCED_SKILLS)
def test_skill_version_matches_changelog_top(skill):
    skill_version = _skill_version(skill)
    top = changelog_top_version(SKILLS_DIR / skill / "CHANGELOG.md")
    assert skill_version == top, (
        f"{skill}: SKILL.md metadata.version {skill_version!r} != CHANGELOG top {top!r} — "
        f"bump both together (version + a new `## [{skill_version}]` heading)."
    )


@pytest.mark.bug_class
def test_bundle_changelog_top_matches_manifest_version():
    # Bundle release identity: the repo-root /CHANGELOG.md top released heading is the
    # bundle version and must equal `version:` in pack.manifest.yaml (and, at release
    # time, the `product-spec-v<X.Y.Z>` tag). This is the bundle-level half of A4, now
    # that the root file owns the all-release log.
    root_changelog = REPO_ROOT / "CHANGELOG.md"
    manifest = yaml.safe_load((REPO_ROOT / ".claude" / "pack.manifest.yaml").read_text(encoding="utf-8"))
    manifest_version = str(manifest["version"])
    top = changelog_top_version(root_changelog)
    assert manifest_version == top, (
        f"bundle drift: pack.manifest.yaml version {manifest_version!r} != root CHANGELOG top {top!r} — "
        f"bump both together (manifest `version:` + a new `## [{manifest_version}]` entry in /CHANGELOG.md)."
    )
