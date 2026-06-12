"""test_upgrade_apply — unit tests for upgrade_apply.apply() and rollback().

All fixtures are synthetic (tmp_path only). Named by invariant/behavior.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

import sys
_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from upgrade_planner import NOOP, PROMPT, REMOVE, UNLINK_ONLY, PlanItem
import upgrade_apply


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _write(path: Path, content: bytes = b"content") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _item(path: str, action: str, kind: str = "file",
          is_symlink: bool = False) -> PlanItem:
    return PlanItem(
        path=path, kind=kind, action=action,
        reason="test", superseded_by=None,
        modified=[], is_symlink=is_symlink,
        pristine_verified=False,
    )


# ---------------------------------------------------------------------------
# 1. REMOVE action: file backed up then deleted
# ---------------------------------------------------------------------------
def test_remove_action_backs_up_and_deletes_file(tmp_path):
    target = tmp_path / "repo"
    live = target / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    _write(live, b"original")

    items = [_item(".claude/skills/spec-critique/SKILL.md", REMOVE)]
    result = upgrade_apply.apply(items, target, target, now_ts="20260101T000000Z")

    assert ".claude/skills/spec-critique/SKILL.md" in result["removed"]
    assert not live.exists(), "Live file should be deleted"
    backup_dir = Path(result["backup_dir"])
    assert backup_dir.exists()
    backed_up = backup_dir / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    assert backed_up.is_file(), "Backup file should exist"
    assert backed_up.read_bytes() == b"original"


# ---------------------------------------------------------------------------
# 2. REMOVE action: directory backed up then deleted
# ---------------------------------------------------------------------------
def test_remove_action_backs_up_and_deletes_directory(tmp_path):
    target = tmp_path / "repo"
    skill_dir = target / ".claude" / "skills" / "spec-critique"
    _write(skill_dir / "SKILL.md", b"skill content")
    _write(skill_dir / "scripts" / "helper.py", b"helper")

    items = [_item(".claude/skills/spec-critique", REMOVE, kind="dir")]
    result = upgrade_apply.apply(items, target, target, now_ts="20260101T000001Z")

    assert ".claude/skills/spec-critique" in result["removed"]
    assert not skill_dir.exists()
    backup_dir = Path(result["backup_dir"])
    assert (backup_dir / ".claude" / "skills" / "spec-critique" / "SKILL.md").is_file()


# ---------------------------------------------------------------------------
# 3. NOOP action: file untouched
# ---------------------------------------------------------------------------
def test_noop_action_leaves_file_intact(tmp_path):
    target = tmp_path / "repo"
    live = target / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    _write(live, b"keep me")

    items = [_item(".claude/skills/spec-critique/SKILL.md", NOOP)]
    result = upgrade_apply.apply(items, target, target, now_ts="20260101T000002Z")

    assert live.exists()
    assert live.read_bytes() == b"keep me"
    assert ".claude/skills/spec-critique/SKILL.md" in result["noop"]


# ---------------------------------------------------------------------------
# 4. PROMPT action: file kept, reported under kept_prompts
# ---------------------------------------------------------------------------
def test_prompt_action_keeps_file_and_reports_it(tmp_path):
    target = tmp_path / "repo"
    live = target / ".claude" / "rules" / "primary-workflow.md"
    _write(live, b"PO edited this")

    items = [_item(".claude/rules/primary-workflow.md", PROMPT)]
    result = upgrade_apply.apply(items, target, target, now_ts="20260101T000003Z")

    assert live.exists()
    assert live.read_bytes() == b"PO edited this"
    assert ".claude/rules/primary-workflow.md" in result["kept_prompts"]


# ---------------------------------------------------------------------------
# 5. UNLINK_ONLY action: symlink removed, external target survives
# ---------------------------------------------------------------------------
def test_symlink_target_not_followed_on_delete(tmp_path):
    target = tmp_path / "repo"
    external_file = tmp_path / "external.txt"
    external_file.write_text("external content", encoding="utf-8")

    link = target / ".claude" / "skills" / "spec-critique"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(external_file)

    items = [_item(".claude/skills/spec-critique", UNLINK_ONLY,
                   kind="dir", is_symlink=True)]
    result = upgrade_apply.apply(items, target, target, now_ts="20260101T000004Z")

    assert ".claude/skills/spec-critique" in result["unlinked"]
    assert not link.exists() and not link.is_symlink(), "Symlink should be removed"
    assert external_file.exists(), "External target must survive — never follow symlink"
    assert external_file.read_text(encoding="utf-8") == "external content"


# ---------------------------------------------------------------------------
# 6. Rollback-manifest written and complete
# ---------------------------------------------------------------------------
def test_rollback_manifest_written_with_all_removed_items(tmp_path):
    target = tmp_path / "repo"
    _write(target / ".claude" / "skills" / "spec-critique" / "SKILL.md", b"a")
    _write(target / ".claude" / "skills" / "claude-pack" / "SKILL.md", b"b")

    items = [
        _item(".claude/skills/spec-critique/SKILL.md", REMOVE),
        _item(".claude/skills/claude-pack/SKILL.md", REMOVE),
    ]
    result = upgrade_apply.apply(items, target, target, now_ts="20260101T000005Z")

    backup_dir = Path(result["backup_dir"])
    manifest_path = backup_dir / "rollback-manifest.json"
    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(data["entries"]) == 2
    original_paths = {e["original_path"] for e in data["entries"]}
    assert any("spec-critique" in p for p in original_paths)
    assert any("claude-pack" in p for p in original_paths)


# ---------------------------------------------------------------------------
# 7. Rerun keeps original backup (distinct timestamps → two backup dirs)
# ---------------------------------------------------------------------------
def test_rerun_keeps_original_backup(tmp_path):
    target = tmp_path / "repo"
    live = target / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    _write(live, b"original content")

    items = [_item(".claude/skills/spec-critique/SKILL.md", REMOVE)]

    # First run
    result1 = upgrade_apply.apply(items, target, target, now_ts="20260101T000010Z")
    backup1 = Path(result1["backup_dir"])
    assert backup1.name == "upgrade-backup-20260101T000010Z"

    # Restore live file to simulate rerun (planner is not responsible here)
    _write(live, b"content after restoration")

    # Second run with different timestamp
    result2 = upgrade_apply.apply(items, target, target, now_ts="20260101T000020Z")
    backup2 = Path(result2["backup_dir"])
    assert backup2.name == "upgrade-backup-20260101T000020Z"

    # Two distinct backup dirs
    assert backup1 != backup2
    assert backup1.exists(), "First backup dir must not be overwritten"

    # First backup's content is intact
    first_bak = backup1 / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    assert first_bak.is_file()
    assert first_bak.read_bytes() == b"original content"


# ---------------------------------------------------------------------------
# 8. Failure mid-apply rolls back all already-removed items
# ---------------------------------------------------------------------------
def test_failure_mid_upgrade_rolls_back(tmp_path):
    target = tmp_path / "repo"
    file_a = target / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    file_b = target / ".claude" / "skills" / "claude-pack" / "SKILL.md"
    _write(file_a, b"content A")
    _write(file_b, b"content B")

    items = [
        _item(".claude/skills/spec-critique/SKILL.md", REMOVE),
        _item(".claude/skills/claude-pack/SKILL.md", REMOVE),
    ]

    # Inject failure: make the second delete raise
    original_delete = upgrade_apply._delete_live
    call_count = [0]

    def fail_on_second(live: Path, is_symlink: bool) -> None:
        call_count[0] += 1
        if call_count[0] >= 2:
            raise OSError("injected delete failure")
        original_delete(live, is_symlink)

    with patch.object(upgrade_apply, "_delete_live", side_effect=fail_on_second):
        with pytest.raises(RuntimeError, match="Delete failed"):
            upgrade_apply.apply(items, target, target, now_ts="20260101T000030Z")

    # Both files must be restored (atomic rollback)
    assert file_a.exists(), "file_a must be restored after rollback"
    assert file_a.read_bytes() == b"content A"
    # file_b was never deleted (failure happened on it), so it stays
    assert file_b.exists(), "file_b must still exist"


# ---------------------------------------------------------------------------
# 9. Rollback restores files from a backup dir
# ---------------------------------------------------------------------------
def test_rollback_restores_all_backed_up_files(tmp_path):
    target = tmp_path / "repo"
    live_a = target / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    live_b = target / ".claude" / "skills" / "claude-pack" / "SKILL.md"
    _write(live_a, b"original A")
    _write(live_b, b"original B")

    items = [
        _item(".claude/skills/spec-critique/SKILL.md", REMOVE),
        _item(".claude/skills/claude-pack/SKILL.md", REMOVE),
    ]
    result = upgrade_apply.apply(items, target, target, now_ts="20260101T000040Z")
    backup_dir = Path(result["backup_dir"])

    assert not live_a.exists()
    assert not live_b.exists()

    restore_result = upgrade_apply.rollback(backup_dir)

    assert live_a.exists()
    assert live_a.read_bytes() == b"original A"
    assert live_b.exists()
    assert live_b.read_bytes() == b"original B"
    assert len(restore_result["restored"]) == 2


# ---------------------------------------------------------------------------
# 10. Already-absent path is treated as noop (idempotent)
# ---------------------------------------------------------------------------
def test_apply_is_idempotent_for_absent_paths(tmp_path):
    target = tmp_path / "repo"
    # Don't create the file — it's absent
    items = [_item(".claude/skills/spec-critique/SKILL.md", REMOVE)]
    result = upgrade_apply.apply(items, target, target, now_ts="20260101T000050Z")
    # Should not error; treated as noop
    assert ".claude/skills/spec-critique/SKILL.md" in result["noop"]


# ---------------------------------------------------------------------------
# 11. Summary dict has all expected keys
# ---------------------------------------------------------------------------
def test_apply_result_dict_has_all_keys(tmp_path):
    target = tmp_path / "repo"
    result = upgrade_apply.apply([], target, target, now_ts="20260101T000060Z")
    for key in ("removed", "kept_prompts", "unlinked", "noop", "backup_dir"):
        assert key in result, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# 12. Symlink round-trip: apply unlinks; rollback recreates symlink faithfully
# ---------------------------------------------------------------------------
def test_rollback_recreates_symlink_faithfully(tmp_path):
    target = tmp_path / "repo"
    external = tmp_path / "external.txt"
    external.write_text("external content", encoding="utf-8")
    link = target / ".claude" / "skills" / "spec-critique"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(external)

    items = [_item(".claude/skills/spec-critique", UNLINK_ONLY, kind="dir", is_symlink=True)]
    result = upgrade_apply.apply(items, target, target, now_ts="20260101T000070Z")
    assert not link.is_symlink(), "symlink unlinked by apply"
    assert external.exists(), "external target never followed"

    restored = upgrade_apply.rollback(Path(result["backup_dir"]))
    # Truthful restore: reported AND actually a symlink again, pointing at the original target.
    assert link.is_symlink(), "rollback must recreate the symlink"
    assert os.readlink(str(link)) == str(external)
    assert any("spec-critique" in p for p in restored["restored"])
    assert external.read_text(encoding="utf-8") == "external content"


# ---------------------------------------------------------------------------
# 13. Atomic mid-apply rollback restores symlink when a later REMOVE fails
# ---------------------------------------------------------------------------
def test_failure_after_unlink_restores_symlink(tmp_path):
    target = tmp_path / "repo"
    external = tmp_path / "ext.txt"
    external.write_text("ext", encoding="utf-8")
    link = target / ".claude" / "skills" / "spec-critique"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(external)
    victim = target / ".claude" / "skills" / "claude-pack" / "SKILL.md"
    _write(victim, b"v")

    items = [
        _item(".claude/skills/spec-critique", UNLINK_ONLY, kind="dir", is_symlink=True),
        _item(".claude/skills/claude-pack/SKILL.md", REMOVE),
    ]
    original_delete = upgrade_apply._delete_live
    calls = [0]

    def fail_second(live, is_symlink):
        calls[0] += 1
        if calls[0] >= 2:
            raise OSError("injected")
        original_delete(live, is_symlink)

    with patch.object(upgrade_apply, "_delete_live", side_effect=fail_second):
        with pytest.raises(RuntimeError, match="Delete failed"):
            upgrade_apply.apply(items, target, target, now_ts="20260101T000080Z")
    assert link.is_symlink(), "symlink must be restored on atomic rollback"
    assert os.readlink(str(link)) == str(external)
