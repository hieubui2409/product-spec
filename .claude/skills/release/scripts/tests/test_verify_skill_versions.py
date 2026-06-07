"""test_verify_skill_versions — release-identity verifier contract.

Scope = semver shape + presence of nested `metadata.version` ONLY. No bundle-equality.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import verify_skill_versions as vsv


def _write_skill(dir_: Path, frontmatter: str) -> Path:
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n\n# skill\n", encoding="utf-8")
    return dir_


def test_valid_nested_version_passes(tmp_path):
    _write_skill(tmp_path / "a", 'name: a\nmetadata:\n  version: "2.0.0"')
    _write_skill(tmp_path / "b", 'name: b\nmetadata:\n  version: "0.1.0"')
    results, ok = vsv.verify([tmp_path / "a", tmp_path / "b"])
    assert ok is True
    assert all(r.ok for r in results)
    assert {r.version for r in results} == {"2.0.0", "0.1.0"}


def test_missing_metadata_block_fails(tmp_path):
    _write_skill(tmp_path / "a", "name: a\nkeywords: [x]")
    results, ok = vsv.verify([tmp_path / "a"])
    assert ok is False
    assert results[0].ok is False
    assert "missing" in results[0].reason.lower()


def test_top_level_version_only_fails(tmp_path):
    # version present but NOT nested under metadata → reject (the gate requires metadata.version).
    _write_skill(tmp_path / "a", 'name: a\nversion: "1.2.3"')
    results, ok = vsv.verify([tmp_path / "a"])
    assert ok is False
    assert results[0].ok is False


def test_garbled_version_fails(tmp_path):
    _write_skill(tmp_path / "a", 'name: a\nmetadata:\n  version: "2.0"')
    results, ok = vsv.verify([tmp_path / "a"])
    assert ok is False
    assert "semver" in results[0].reason.lower() or "match" in results[0].reason.lower()


def test_missing_skill_md_fails(tmp_path):
    (tmp_path / "a").mkdir()
    results, ok = vsv.verify([tmp_path / "a"])
    assert ok is False


def test_real_repo_skills_pass():
    # The live repo's 3 skills must verify green (no bundle-equality asserted).
    root = Path(__file__).resolve().parents[5]  # .../cleanmatic-skills
    skills = [
        root / ".claude/skills/product-spec",
        root / ".claude/skills/product-spec-critique",
        root / ".claude/skills/release",
    ]
    results, ok = vsv.verify(skills)
    assert ok is True, [(r.name, r.reason) for r in results if not r.ok]


def test_cli_exit_zero_on_valid(tmp_path, capsys):
    _write_skill(tmp_path / "a", 'name: a\nmetadata:\n  version: "1.0.0"')
    rc = vsv.main(["--skill", str(tmp_path / "a")])
    assert rc == 0


def test_cli_exit_one_on_invalid(tmp_path):
    _write_skill(tmp_path / "a", "name: a")
    rc = vsv.main(["--skill", str(tmp_path / "a")])
    assert rc == 1
