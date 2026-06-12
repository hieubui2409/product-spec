"""test_upgrade_planner — unit tests for upgrade_planner.plan().

All tests use synthetic tmp_path fixtures only — no real PO data read.
Named by invariant/behavior, not by phase/finding codes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import sys
_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from upgrade_planner import (
    NOOP, PROMPT, REMOVE, UNLINK_ONLY,
    PlanItem, load_legacy_map, plan,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------
def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, content: bytes = b"original content") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _legacy_map(entries: list[dict], sig_paths: list[str] | None = None) -> dict:
    return {
        "schema_version": "1.0",
        "description": "synthetic test map",
        "legacy_signature_paths": sig_paths or [],
        "entries": entries,
    }


def _simple_file_entry(path: str, requires_sig: bool = False,
                        pristine_sha: str | None = None) -> dict:
    e: dict = {
        "path": path, "kind": "file", "action": "remove",
        "superseded_by": None,
        "requires_signature": requires_sig,
        "reason": f"test entry for {path}",
    }
    if pristine_sha is not None:
        e["pristine_sha256"] = pristine_sha
    return e


def _simple_dir_entry(path: str, requires_sig: bool = False,
                       pristine_sha: dict | None = None) -> dict:
    e: dict = {
        "path": path, "kind": "dir", "action": "remove",
        "superseded_by": ".claude/skills/product-spec-critique",
        "requires_signature": False,
        "reason": f"test dir entry for {path}",
    }
    if pristine_sha is not None:
        e["pristine_sha256"] = pristine_sha
    return e


# ---------------------------------------------------------------------------
# 1. Absent entry → NOOP
# ---------------------------------------------------------------------------
def test_absent_path_produces_noop(tmp_path):
    lm = _legacy_map([_simple_file_entry(".claude/skills/spec-critique/SKILL.md")])
    result = plan(tmp_path, lm)
    assert len(result) == 1
    item = result[0]
    assert item.action == NOOP
    assert "absent" in item.reason


# ---------------------------------------------------------------------------
# 2. Present file with no pristine data → REMOVE (unverified)
# ---------------------------------------------------------------------------
def test_present_file_no_pristine_produces_remove(tmp_path):
    p = tmp_path / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    _write(p)
    lm = _legacy_map([_simple_file_entry(".claude/skills/spec-critique/SKILL.md")])
    result = plan(tmp_path, lm)
    assert result[0].action == REMOVE
    assert result[0].pristine_verified is False


# ---------------------------------------------------------------------------
# 3. Present file matching pristine hash → REMOVE (verified)
# ---------------------------------------------------------------------------
def test_present_file_matching_pristine_hash_produces_remove_verified(tmp_path):
    content = b"pristine content"
    p = tmp_path / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    _write(p, content)
    lm = _legacy_map([_simple_file_entry(
        ".claude/skills/spec-critique/SKILL.md",
        pristine_sha=_sha256(content),
    )])
    result = plan(tmp_path, lm)
    assert result[0].action == REMOVE
    assert result[0].pristine_verified is True


# ---------------------------------------------------------------------------
# 4. Present file differing from pristine hash → PROMPT (not removed)
# ---------------------------------------------------------------------------
def test_po_edited_file_with_pristine_hash_produces_prompt(tmp_path):
    original_content = b"original pristine content"
    modified_content = b"PO edited this file"
    p = tmp_path / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    _write(p, modified_content)
    lm = _legacy_map([_simple_file_entry(
        ".claude/skills/spec-critique/SKILL.md",
        pristine_sha=_sha256(original_content),  # hash of ORIGINAL, not modified
    )])
    result = plan(tmp_path, lm)
    item = result[0]
    assert item.action == PROMPT, f"Expected PROMPT, got {item.action}"
    assert item.pristine_verified is False
    assert ".claude/skills/spec-critique/SKILL.md" in item.modified


# ---------------------------------------------------------------------------
# 5. Symlink at legacy path → UNLINK_ONLY (never follow)
# ---------------------------------------------------------------------------
def test_symlink_at_legacy_path_produces_unlink_only(tmp_path):
    # Create an external target file (outside the target tree)
    external = tmp_path / "external_file.txt"
    external.write_text("external", encoding="utf-8")

    # Create a legacy dir that happens to be a symlink to somewhere outside
    link_path = tmp_path / ".claude" / "skills" / "spec-critique"
    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(external)

    lm = _legacy_map([_simple_dir_entry(".claude/skills/spec-critique")])
    result = plan(tmp_path, lm)
    item = result[0]
    assert item.action == UNLINK_ONLY
    assert item.is_symlink is True
    # External target must still exist (planner does NOT follow the link)
    assert external.exists()


# ---------------------------------------------------------------------------
# 6. requires_signature=True + no signature in target → NOOP
# ---------------------------------------------------------------------------
def test_signature_required_but_absent_produces_noop(tmp_path):
    rule_path = tmp_path / ".claude" / "rules" / "primary-workflow.md"
    _write(rule_path)
    lm = _legacy_map(
        entries=[_simple_file_entry(
            ".claude/rules/primary-workflow.md", requires_sig=True
        )],
        sig_paths=[".claude/skills/spec-critique"],  # this does NOT exist in tmp_path
    )
    result = plan(tmp_path, lm)
    assert result[0].action == NOOP
    assert "no 1.x legacy signature" in result[0].reason


# ---------------------------------------------------------------------------
# 7. requires_signature=True + signature IS present → REMOVE
# ---------------------------------------------------------------------------
def test_signature_required_and_present_proceeds_to_remove(tmp_path):
    rule_path = tmp_path / ".claude" / "rules" / "primary-workflow.md"
    _write(rule_path)
    # Create the signature path
    sig = tmp_path / ".claude" / "skills" / "spec-critique"
    sig.mkdir(parents=True)

    lm = _legacy_map(
        entries=[_simple_file_entry(
            ".claude/rules/primary-workflow.md", requires_sig=True
        )],
        sig_paths=[".claude/skills/spec-critique"],
    )
    result = plan(tmp_path, lm)
    assert result[0].action == REMOVE


# ---------------------------------------------------------------------------
# 8. Dir entry — all files match pristine → REMOVE (verified)
# ---------------------------------------------------------------------------
def test_dir_all_files_match_pristine_produces_remove(tmp_path):
    content_a = b"file a content"
    content_b = b"file b content"
    skill_dir = tmp_path / ".claude" / "skills" / "spec-critique"
    _write(skill_dir / "SKILL.md", content_a)
    _write(skill_dir / "scripts" / "helper.py", content_b)

    pristine_map = {
        "SKILL.md": _sha256(content_a),
        "scripts/helper.py": _sha256(content_b),
    }
    lm = _legacy_map([_simple_dir_entry(
        ".claude/skills/spec-critique", pristine_sha=pristine_map
    )])
    result = plan(tmp_path, lm)
    assert result[0].action == REMOVE
    assert result[0].pristine_verified is True
    assert result[0].modified == []


# ---------------------------------------------------------------------------
# 9. Dir entry — one file modified → PROMPT with modified list
# ---------------------------------------------------------------------------
def test_dir_with_modified_file_produces_prompt_with_modified_list(tmp_path):
    content_a = b"file a original"
    content_b = b"file b original"
    modified_b = b"PO modified this file"
    skill_dir = tmp_path / ".claude" / "skills" / "spec-critique"
    _write(skill_dir / "SKILL.md", content_a)
    _write(skill_dir / "scripts" / "helper.py", modified_b)

    pristine_map = {
        "SKILL.md": _sha256(content_a),
        "scripts/helper.py": _sha256(content_b),  # hash of ORIGINAL
    }
    lm = _legacy_map([_simple_dir_entry(
        ".claude/skills/spec-critique", pristine_sha=pristine_map
    )])
    result = plan(tmp_path, lm)
    item = result[0]
    assert item.action == PROMPT
    assert "scripts/helper.py" in item.modified


# ---------------------------------------------------------------------------
# 10. Dir entry — extra file not in pristine map → PROMPT
# ---------------------------------------------------------------------------
def test_dir_with_extra_file_not_in_pristine_produces_prompt(tmp_path):
    content_a = b"file a"
    skill_dir = tmp_path / ".claude" / "skills" / "spec-critique"
    _write(skill_dir / "SKILL.md", content_a)
    _write(skill_dir / "extra-po-file.md", b"PO added this")

    pristine_map = {
        "SKILL.md": _sha256(content_a),
        # extra-po-file.md NOT in map
    }
    lm = _legacy_map([_simple_dir_entry(
        ".claude/skills/spec-critique", pristine_sha=pristine_map
    )])
    result = plan(tmp_path, lm)
    assert result[0].action == PROMPT
    assert "extra-po-file.md" in result[0].modified


# ---------------------------------------------------------------------------
# 11. to_dict() includes all expected keys
# ---------------------------------------------------------------------------
def test_plan_item_to_dict_has_all_keys(tmp_path):
    _write(tmp_path / ".claude" / "skills" / "spec-critique" / "SKILL.md")
    lm = _legacy_map([_simple_file_entry(".claude/skills/spec-critique/SKILL.md")])
    result = plan(tmp_path, lm)
    d = result[0].to_dict()
    for key in ("path", "kind", "action", "reason", "superseded_by",
                "modified", "is_symlink", "pristine_verified"):
        assert key in d, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# 12. load_legacy_map raises ValueError on bad JSON
# ---------------------------------------------------------------------------
def test_load_legacy_map_raises_on_bad_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{{", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid legacy-map JSON"):
        load_legacy_map(bad)


# ---------------------------------------------------------------------------
# 13. Dry-run: planner modifies NOTHING on disk
# ---------------------------------------------------------------------------
def test_plan_writes_nothing_to_disk(tmp_path):
    """plan() must be pure — no disk writes, no backup files, no mtime changes."""
    skill_dir = tmp_path / ".claude" / "skills" / "spec-critique"
    skill_md = skill_dir / "SKILL.md"
    _write(skill_md, b"original")
    # Record state before
    before_mtime = skill_md.stat().st_mtime
    before_content = skill_md.read_bytes()
    before_files = set(str(f) for f in tmp_path.rglob("*"))

    lm = _legacy_map([_simple_file_entry(".claude/skills/spec-critique/SKILL.md")])
    plan(tmp_path, lm)

    # State must be identical
    assert skill_md.read_bytes() == before_content
    assert skill_md.stat().st_mtime == before_mtime
    after_files = set(str(f) for f in tmp_path.rglob("*"))
    assert after_files == before_files, \
        f"Files changed during plan():\n  added={after_files - before_files}\n  removed={before_files - after_files}"
