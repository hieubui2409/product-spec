"""test_upgrade_e2e — end-to-end upgrade tests (shell + build integration).

Covers the 7 required behaviors from the phase spec plus the bash:3.2 syntax
check and bundle-embed verification.

Tests that require bash are skipped when bash is absent.
Tests that require docker are skipped when docker is absent or bash:3.2 unavailable.
Tests that build a real bundle require the repo manifest.

All fixtures are synthetic (tmp_path only) — no real PO data read.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent      # .../release/scripts
_SKILL_ROOT = Path(__file__).resolve().parents[2]      # .../release
_REPO_ROOT = Path(__file__).resolve().parents[5]       # repo root
_MANIFEST_YAML = _REPO_ROOT / ".claude" / "pack.manifest.yaml"
_LEGACY_MAP = _SKILL_ROOT / "assets" / "upgrade" / "legacy-map.json"

if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from upgrade_planner import NOOP, PROMPT, REMOVE, UNLINK_ONLY, plan, load_legacy_map
import upgrade_apply


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _write(path: Path, content: bytes = b"content") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _legacy_map_dict(entries: list[dict], sig_paths: list[str] | None = None) -> dict:
    return {
        "schema_version": "1.0",
        "description": "synthetic test map",
        "legacy_signature_paths": sig_paths or [],
        "entries": entries,
    }


def _synthetic_1x_tree(root: Path) -> Path:
    """Build a synthetic 1.x install tree with legacy artifacts."""
    # Legacy critique skill
    _write(root / ".claude" / "skills" / "spec-critique" / "SKILL.md",
           b"---\nname: cleanmatic:spec-critique\nmetadata:\n  version: '1.1.0'\n---\n")
    _write(root / ".claude" / "skills" / "spec-critique" / "scripts" / "critique.py",
           b"# critique script\n")
    # Legacy pack skill
    _write(root / ".claude" / "skills" / "claude-pack" / "SKILL.md",
           b"---\nname: cleanmatic:claude-pack\nmetadata:\n  version: '1.1.0'\n---\n")
    # Dev rules (legacy)
    for rule in ("primary-workflow.md", "development-rules.md",
                 "orchestration-protocol.md", "documentation-management.md",
                 "review-audit-self-decision.md"):
        _write(root / ".claude" / "rules" / rule, f"# {rule}\n".encode())
    return root


def _build_bundle(out_dir: Path) -> Path:
    """Build a real tarball via the pack CLI; return its path."""
    r = subprocess.run(
        [sys.executable, "-m", "pack",
         "--root", str(_REPO_ROOT),
         "--manifest", str(_MANIFEST_YAML),
         "--version", "0.0.0-test",
         "--allow-dev-version",
         "--out", str(out_dir)],
        cwd=str(_SCRIPTS), capture_output=True, text=True,
    )
    assert r.returncode == 0, f"pack build failed:\n{r.stderr or r.stdout}"
    tarballs = glob.glob(str(out_dir / "*.tar.gz"))
    assert tarballs, f"no tarball produced in {out_dir}"
    return Path(tarballs[0])


def _extract_bundle(bundle: Path, extract_dir: Path) -> Path:
    """Extract bundle; return the root dir inside extract_dir."""
    extract_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle, "r:gz") as tar:
        tar.extractall(extract_dir)
    # bundle root is the top-level dir in the tarball
    dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
    assert dirs, "no dir found after extraction"
    return dirs[0]


def _run_upgrade_sh(bundle_dir: Path, target: Path,
                    flags: list[str] | None = None,
                    env_extra: dict | None = None) -> subprocess.CompletedProcess:
    upgrade_sh = bundle_dir / "upgrade.sh"
    env = {**os.environ, "TARGET_DIR": str(target)}
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(upgrade_sh)] + (flags or [])
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


_has_bash = shutil.which("bash") is not None
_has_manifest = _MANIFEST_YAML.is_file()


# ---------------------------------------------------------------------------
# 1. Dry-run lists plan and writes nothing
# ---------------------------------------------------------------------------
def test_dry_run_lists_plan_and_writes_nothing(tmp_path):
    """planner --dry-run prints the plan and makes zero changes to the tree."""
    target = _synthetic_1x_tree(tmp_path / "repo")

    # Snapshot before
    before: dict[str, bytes] = {}
    for f in sorted(target.rglob("*")):
        if f.is_file():
            before[str(f.relative_to(target))] = f.read_bytes()

    lm = load_legacy_map(_LEGACY_MAP)
    items = plan(target, lm)

    # Plan has at least the two legacy skills
    paths = {i.path for i in items}
    assert ".claude/skills/spec-critique" in paths
    assert ".claude/skills/claude-pack" in paths

    # REMOVE actions for the skills (no signature required)
    for item in items:
        if item.path in (".claude/skills/spec-critique", ".claude/skills/claude-pack"):
            assert item.action in (REMOVE, PROMPT), \
                f"Expected REMOVE or PROMPT for {item.path}, got {item.action}"

    # Tree is byte-for-byte unchanged after plan()
    after: dict[str, bytes] = {}
    for f in sorted(target.rglob("*")):
        if f.is_file():
            after[str(f.relative_to(target))] = f.read_bytes()

    assert before == after, \
        f"plan() modified files:\n  added={set(after)-set(before)}\n  removed={set(before)-set(after)}"

    # No .bak files, no new dirs
    baks = list(target.rglob("*.bak*"))
    assert not baks, f"Unexpected .bak files after dry-run: {baks}"


# ---------------------------------------------------------------------------
# 2. Apply produces clean install (e2e, real bundle + real upgrade.sh)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _has_bash, reason="bash required")
@pytest.mark.skipif(not _has_manifest, reason="repo manifest not present")
def test_apply_produces_clean_install(tmp_path):
    """upgrade.sh --apply removes legacy artifacts, leaves no doubled skills, backup exists."""
    bundle = _build_bundle(tmp_path / "dist")
    bundle_dir = _extract_bundle(bundle, tmp_path / "extract")

    assert (bundle_dir / "upgrade.sh").is_file(), "upgrade.sh not in bundle"

    target = _synthetic_1x_tree(tmp_path / "repo")

    r = _run_upgrade_sh(bundle_dir, target, flags=["--apply"])
    assert r.returncode == 0, f"upgrade.sh --apply failed:\n{r.stderr}\n{r.stdout}"

    # Legacy skills are gone
    assert not (target / ".claude" / "skills" / "spec-critique").exists(), \
        "spec-critique should have been removed"
    assert not (target / ".claude" / "skills" / "claude-pack").exists(), \
        "claude-pack should have been removed"

    # New product-spec-critique skill is present (installed by force-install step)
    assert (target / ".claude" / "skills" / "product-spec-critique" / "SKILL.md").is_file(), \
        "product-spec-critique not installed after upgrade"

    # A timestamped backup dir exists
    backups = list(target.glob("upgrade-backup-*"))
    assert backups, "No upgrade-backup-* dir found after --apply"

    # install.sh ran to completion: CLAUDE.md installed at target root
    claude_md = target / "CLAUDE.md"
    assert claude_md.is_file(), "CLAUDE.md must exist after upgrade (install.sh ran)"
    assert claude_md.stat().st_size > 0, "CLAUDE.md must be non-empty"

    # install.sh ran to completion: .gitignore has telemetry entry (idempotent gitignore step)
    gitignore = target / ".gitignore"
    assert gitignore.is_file(), ".gitignore must exist after upgrade (install.sh ran)"
    assert ".claude/telemetry/" in gitignore.read_text(encoding="utf-8"), \
        ".gitignore must contain .claude/telemetry/ after upgrade"


# ---------------------------------------------------------------------------
# 3. PO-edited legacy file prompts, not deleted
# ---------------------------------------------------------------------------
def test_po_edited_legacy_file_prompts_not_deleted(tmp_path):
    """A legacy entry with pristine_sha256 whose live content differs → PROMPT; apply keeps it."""
    target = tmp_path / "repo"
    original_content = b"original pristine SKILL.md content"
    modified_content = b"PO customised this file - keep me!"
    skill_md = target / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    _write(skill_md, modified_content)

    lm = _legacy_map_dict([{
        "path": ".claude/skills/spec-critique/SKILL.md",
        "kind": "file",
        "action": "remove",
        "superseded_by": ".claude/skills/product-spec-critique",
        "requires_signature": False,
        "reason": "test",
        "pristine_sha256": _sha256(original_content),  # hash of ORIGINAL, not what PO wrote
    }])

    items = plan(target, lm)
    assert len(items) == 1
    assert items[0].action == PROMPT, f"Expected PROMPT, got {items[0].action}"

    # Apply: PROMPT items are kept
    result = upgrade_apply.apply(items, target, target, now_ts="20260612T000000Z")
    assert skill_md.exists(), "PO-edited file must NOT be deleted"
    assert skill_md.read_bytes() == modified_content, "PO content must be preserved"
    assert ".claude/skills/spec-critique/SKILL.md" in result["kept_prompts"]


# ---------------------------------------------------------------------------
# 4. Symlink target not followed on delete
# ---------------------------------------------------------------------------
def test_symlink_target_not_followed_on_delete(tmp_path):
    """A legacy path that is a symlink → planner emits UNLINK_ONLY; apply removes
    only the link; the external target file still exists."""
    target = tmp_path / "repo"
    external_file = tmp_path / "external_data.txt"
    external_file.write_text("external content that must survive", encoding="utf-8")

    link = target / ".claude" / "skills" / "spec-critique"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(external_file)

    lm = _legacy_map_dict([{
        "path": ".claude/skills/spec-critique",
        "kind": "dir",
        "action": "remove",
        "superseded_by": ".claude/skills/product-spec-critique",
        "requires_signature": False,
        "reason": "test",
    }])

    items = plan(target, lm)
    assert items[0].action == UNLINK_ONLY, \
        f"Expected UNLINK_ONLY for symlink, got {items[0].action}"
    assert items[0].is_symlink is True

    result = upgrade_apply.apply(items, target, target, now_ts="20260612T000001Z")

    assert not link.exists() and not link.is_symlink(), "Symlink must be removed"
    assert external_file.exists(), "External target file must NOT be deleted"
    assert external_file.read_text(encoding="utf-8") == "external content that must survive"
    assert ".claude/skills/spec-critique" in result["unlinked"]


# ---------------------------------------------------------------------------
# 5. Rerun keeps original backup (distinct timestamps)
# ---------------------------------------------------------------------------
def test_rerun_keeps_original_backup(tmp_path):
    """Two apply runs with different now_ts produce two distinct backup dirs;
    first backup's contents are intact."""
    target = tmp_path / "repo"
    skill_dir = target / ".claude" / "skills" / "spec-critique"
    skill_md = skill_dir / "SKILL.md"
    _write(skill_md, b"original skill content")
    _write(skill_dir / "scripts" / "helper.py", b"helper")

    lm = _legacy_map_dict([{
        "path": ".claude/skills/spec-critique",
        "kind": "dir",
        "action": "remove",
        "superseded_by": None,
        "requires_signature": False,
        "reason": "test",
    }])

    items = plan(target, lm)

    # First apply
    result1 = upgrade_apply.apply(items, target, target, now_ts="20260101T100000Z")
    backup1 = Path(result1["backup_dir"])
    assert backup1.name == "upgrade-backup-20260101T100000Z"
    first_bak_skill = backup1 / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    assert first_bak_skill.is_file()
    original_bak_content = first_bak_skill.read_bytes()

    # Re-create the tree for the second run
    _write(skill_md, b"re-created content")
    _write(skill_dir / "scripts" / "helper.py", b"helper again")
    items2 = plan(target, lm)

    # Second apply with different timestamp
    result2 = upgrade_apply.apply(items2, target, target, now_ts="20260101T200000Z")
    backup2 = Path(result2["backup_dir"])
    assert backup2.name == "upgrade-backup-20260101T200000Z"

    # Two distinct dirs
    assert backup1 != backup2

    # First backup is intact — not overwritten by second run
    assert first_bak_skill.is_file(), "First backup must not be deleted by second run"
    assert first_bak_skill.read_bytes() == original_bak_content, \
        "First backup content must not be modified by second run"


# ---------------------------------------------------------------------------
# 6. Failure mid-upgrade rolls back (atomic)
# ---------------------------------------------------------------------------
def test_failure_mid_upgrade_rolls_back(tmp_path):
    """If a deletion fails mid-apply, everything already removed is restored
    and the original exception surfaces."""
    target = tmp_path / "repo"
    file_a = target / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    file_b = target / ".claude" / "skills" / "claude-pack" / "SKILL.md"
    _write(file_a, b"spec-critique content")
    _write(file_b, b"claude-pack content")

    lm = _legacy_map_dict([
        {
            "path": ".claude/skills/spec-critique/SKILL.md",
            "kind": "file", "action": "remove",
            "superseded_by": None, "requires_signature": False,
            "reason": "test",
        },
        {
            "path": ".claude/skills/claude-pack/SKILL.md",
            "kind": "file", "action": "remove",
            "superseded_by": None, "requires_signature": False,
            "reason": "test",
        },
    ])
    items = plan(target, lm)
    assert len(items) == 2

    original_delete = upgrade_apply._delete_live
    call_count = [0]

    def fail_on_second(live: Path, is_symlink: bool) -> None:
        call_count[0] += 1
        if call_count[0] >= 2:
            raise OSError("injected failure on second delete")
        original_delete(live, is_symlink)

    with patch.object(upgrade_apply, "_delete_live", side_effect=fail_on_second):
        with pytest.raises(RuntimeError, match="Delete failed"):
            upgrade_apply.apply(items, target, target, now_ts="20260612T000002Z")

    # Tree must be restored to pre-apply state
    assert file_a.exists(), "file_a must be restored after rollback"
    assert file_a.read_bytes() == b"spec-critique content"
    assert file_b.exists(), "file_b must exist (was never deleted)"


# ---------------------------------------------------------------------------
# 7. Upgrade runs migrate dry-run only (never --apply)
# ---------------------------------------------------------------------------
def test_upgrade_runs_migrate_dry_run_only(tmp_path):
    """upgrade.sh must never pass --apply/--confirmed-by to migrate_metric_to_metrics.

    Static check: grep the rendered/source upgrade.sh.template for forbidden flags.
    """
    tmpl = _SKILL_ROOT / "assets" / "templates" / "upgrade.sh.template"
    assert tmpl.is_file(), "upgrade.sh.template must exist"
    content = tmpl.read_text(encoding="utf-8")

    # Must invoke migrate with --dry-run
    assert "migrate_metric_to_metrics" in content, \
        "upgrade.sh.template must invoke migrate_metric_to_metrics"
    assert "--dry-run" in content, \
        "upgrade.sh.template must pass --dry-run to migrate"

    # Must NEVER pass --apply or --confirmed-by to migrate
    import re
    # Look for migrate invocation lines
    migrate_lines = [
        ln for ln in content.splitlines()
        if "migrate_metric_to_metrics" in ln and not ln.strip().startswith("#")
    ]
    for ln in migrate_lines:
        assert "--apply" not in ln, \
            f"upgrade.sh.template passes --apply to migrate (forbidden): {ln!r}"
        assert "--confirmed-by" not in ln, \
            f"upgrade.sh.template passes --confirmed-by to migrate (forbidden): {ln!r}"


# ---------------------------------------------------------------------------
# e2e: upgrade.sh --apply keeps migrate dry-run (no BRD mutation)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _has_bash, reason="bash required")
@pytest.mark.skipif(not _has_manifest, reason="repo manifest not present")
def test_upgrade_apply_does_not_mutate_brd(tmp_path):
    """After upgrade.sh --apply, any BRD in the target is unmodified (migrate ran dry-run only)."""
    bundle = _build_bundle(tmp_path / "dist")
    bundle_dir = _extract_bundle(bundle, tmp_path / "extract")

    target = _synthetic_1x_tree(tmp_path / "repo")

    # Add a synthetic BRD with a legacy metric: field
    brd = target / "docs" / "product" / "brd.md"
    brd_content = (
        "---\nstatus: approved\n---\n"
        "goals:\n  - id: G-001\n    metric: 100 users\n"
    )
    _write(brd, brd_content.encode())
    original_brd = brd.read_bytes()

    r = _run_upgrade_sh(bundle_dir, target, flags=["--apply"])
    assert r.returncode == 0, f"upgrade failed:\n{r.stderr}\n{r.stdout}"

    # BRD content must be unchanged (migrate was dry-run only)
    assert brd.read_bytes() == original_brd, \
        "BRD was modified — migrate must only run --dry-run in upgrade.sh"

    # No .bak for the BRD
    bak_files = list(brd.parent.glob("brd.md.bak*"))
    assert not bak_files, f"BRD has unexpected .bak files: {bak_files}"


# ---------------------------------------------------------------------------
# bash:3.2 syntax check for upgrade.sh
# ---------------------------------------------------------------------------
def test_upgrade_sh_bash32_syntax(tmp_path):
    """upgrade.sh.template must pass `bash -n` under bash:3.2 (syntax check via docker)."""
    docker = shutil.which("docker")
    if not docker:
        pytest.skip("docker not available — skipping bash:3.2 syntax check")

    tmpl = _SKILL_ROOT / "assets" / "templates" / "upgrade.sh.template"
    assert tmpl.is_file(), "upgrade.sh.template must exist"

    # Render with dummy tokens
    sys.path.insert(0, str(_SCRIPTS))
    from pack.templates import render_template
    tokens = {
        "BUNDLE_NAME": "product-spec",
        "VERSION": "0.0.0-test",
        "BUILT_AT": "1970-01-01T00:00:00+00:00",
        "SOURCE_COMMIT": "deadbeef",
        "FILE_COUNT": "42",
        "TOTAL_SIZE": "1 MB",
    }
    rendered = render_template(tmpl, tokens).decode("utf-8")

    # Check bash:3.2 image availability
    probe = subprocess.run(
        [docker, "image", "inspect", "bash:3.2"],
        capture_output=True, text=True,
    )
    if probe.returncode != 0:
        pull = subprocess.run(
            [docker, "pull", "bash:3.2"],
            capture_output=True, text=True, timeout=120,
        )
        if pull.returncode != 0:
            pytest.skip("bash:3.2 Docker image unavailable")

    script_path = tmp_path / "upgrade.sh"
    script_path.write_text(rendered, encoding="utf-8")

    r = subprocess.run(
        [docker, "run", "--rm",
         "-v", f"{tmp_path}:/x",
         "bash:3.2",
         "bash", "-n", "/x/upgrade.sh"],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0, \
        f"bash:3.2 -n rejected upgrade.sh (syntax error):\n{r.stderr}"


# ---------------------------------------------------------------------------
# Bundle embeds upgrade payload (upgrade.sh, _upgrade/upgrade_planner.py, legacy-map.json)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _has_manifest, reason="repo manifest not present")
def test_bundle_embeds_upgrade_payload(tmp_path):
    """The built bundle tarball must contain upgrade.sh and _upgrade/* with MANIFEST entries
    and byte-identical content to the source files."""
    bundle = _build_bundle(tmp_path / "dist")
    bundle_dir = _extract_bundle(bundle, tmp_path / "extract")

    manifest_bytes = None
    extracted_files: dict[str, bytes] = {}
    with tarfile.open(bundle, "r:gz") as tar:
        names = tar.getnames()
        for member in tar.getmembers():
            if member.name.endswith("/MANIFEST.json"):
                manifest_bytes = tar.extractfile(member).read()
            fobj = tar.extractfile(member)
            if fobj is not None:
                extracted_files[member.name] = fobj.read()

    # upgrade.sh at bundle root
    assert any(n.endswith("/upgrade.sh") for n in names), \
        f"upgrade.sh not in bundle. Names sample: {names[:20]}"

    # _upgrade/ payload files
    assert any(n.endswith("/_upgrade/upgrade_planner.py") for n in names), \
        "_upgrade/upgrade_planner.py not in bundle"
    assert any(n.endswith("/_upgrade/upgrade_apply.py") for n in names), \
        "_upgrade/upgrade_apply.py not in bundle"
    assert any(n.endswith("/_upgrade/legacy-map.json") for n in names), \
        "_upgrade/legacy-map.json not in bundle"

    # MANIFEST.json must list all four upgrade files
    assert manifest_bytes is not None, "MANIFEST.json not found in bundle"
    manifest = json.loads(manifest_bytes)
    manifest_paths = {f["path"] for f in manifest.get("files", [])}

    # Each upgrade file must have a MANIFEST entry (integrity coverage)
    for expected_suffix in (
        "/upgrade.sh",
        "/_upgrade/upgrade_planner.py",
        "/_upgrade/upgrade_apply.py",
        "/_upgrade/legacy-map.json",
    ):
        assert any(p.endswith(expected_suffix) for p in manifest_paths), \
            f"MANIFEST.json missing entry for *{expected_suffix}. " \
            f"Paths sample: {sorted(manifest_paths)[:20]}"

    # MANIFEST.json must NOT self-list itself
    assert not any(p.endswith("/MANIFEST.json") for p in manifest_paths), \
        "MANIFEST.json must not self-list in files[]"

    # Byte-integrity: embedded planner/apply/legacy-map must match source files
    source_planner = (_SCRIPTS / "upgrade_planner.py").read_bytes()
    source_apply   = (_SCRIPTS / "upgrade_apply.py").read_bytes()
    source_map     = (_SKILL_ROOT / "assets" / "upgrade" / "legacy-map.json").read_bytes()

    def _find_extracted(suffix: str) -> bytes:
        for name, data in extracted_files.items():
            if name.endswith(suffix):
                return data
        raise AssertionError(f"No extracted file ending with {suffix!r}")

    embedded_planner = _find_extracted("/_upgrade/upgrade_planner.py")
    embedded_apply   = _find_extracted("/_upgrade/upgrade_apply.py")
    embedded_map     = _find_extracted("/_upgrade/legacy-map.json")

    assert embedded_planner == source_planner, \
        "Embedded upgrade_planner.py differs from source — bundle may be stale"
    assert embedded_apply == source_apply, \
        "Embedded upgrade_apply.py differs from source — bundle may be stale"
    assert embedded_map == source_map, \
        "Embedded legacy-map.json differs from source — bundle may be stale"

    # SHA256 integrity: each MANIFEST entry's sha256 must match the extracted bytes
    manifest_by_suffix: dict[str, dict] = {}
    for entry in manifest.get("files", []):
        manifest_by_suffix[entry["path"]] = entry

    for suffix in ("/_upgrade/upgrade_planner.py", "/_upgrade/upgrade_apply.py",
                   "/_upgrade/legacy-map.json", "/upgrade.sh"):
        matching = [e for p, e in manifest_by_suffix.items() if p.endswith(suffix)]
        assert matching, f"MANIFEST entry missing for *{suffix}"
        entry = matching[0]
        if "sha256" in entry:
            ext_bytes = _find_extracted(suffix)
            actual_sha = hashlib.sha256(ext_bytes).hexdigest()
            assert entry["sha256"] == actual_sha, \
                f"MANIFEST sha256 mismatch for {suffix}: manifest={entry['sha256']!r} actual={actual_sha!r}"


# ---------------------------------------------------------------------------
# e2e: upgrade.sh --apply then --rollback restores removed legacy artifact
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _has_bash, reason="bash required")
@pytest.mark.skipif(not _has_manifest, reason="repo manifest not present")
def test_shell_rollback_restores_legacy_artifact(tmp_path):
    """upgrade.sh --apply removes legacy artifacts; upgrade.sh --rollback restores them."""
    bundle = _build_bundle(tmp_path / "dist")
    bundle_dir = _extract_bundle(bundle, tmp_path / "extract")

    target = _synthetic_1x_tree(tmp_path / "repo")
    # Record a legacy artifact path that the sweep will remove
    legacy_skill_md = target / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    assert legacy_skill_md.is_file(), "precondition: legacy SKILL.md must exist before apply"

    r = _run_upgrade_sh(bundle_dir, target, flags=["--apply"])
    assert r.returncode == 0, f"upgrade.sh --apply failed:\n{r.stderr}\n{r.stdout}"
    assert not legacy_skill_md.exists(), "spec-critique SKILL.md should be removed after apply"

    r2 = _run_upgrade_sh(bundle_dir, target, flags=["--rollback"])
    assert r2.returncode == 0, f"upgrade.sh --rollback failed:\n{r2.stderr}\n{r2.stdout}"
    assert legacy_skill_md.exists(), "spec-critique SKILL.md must be restored after rollback"


# ---------------------------------------------------------------------------
# e2e: Step-2 install failure triggers auto-rollback of the legacy sweep
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _has_bash, reason="bash required")
@pytest.mark.skipif(not _has_manifest, reason="repo manifest not present")
def test_step2_failure_auto_rolls_back_sweep(tmp_path):
    """If Step 2 (install) fails, the ERR trap auto-rolls-back the legacy artifacts
    swept by Step 1, and .gitignore gets the upgrade-backup-*/ line."""
    bundle = _build_bundle(tmp_path / "dist")
    bundle_dir = _extract_bundle(bundle, tmp_path / "extract")

    target = _synthetic_1x_tree(tmp_path / "repo")
    legacy_skill_md = target / ".claude" / "skills" / "spec-critique" / "SKILL.md"
    assert legacy_skill_md.is_file(), "precondition: legacy SKILL.md must exist before apply"

    # Overwrite install.sh inside the extracted bundle to always fail
    bad_install = bundle_dir / "install.sh"
    bad_install.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    bad_install.chmod(0o755)

    r = _run_upgrade_sh(bundle_dir, target, flags=["--apply"])
    assert r.returncode != 0, "upgrade.sh --apply should fail when install.sh exits 1"

    # Auto-rollback must have restored the legacy artifact removed in Step 1
    assert legacy_skill_md.exists(), \
        "spec-critique SKILL.md must be auto-restored after Step-2 failure"

    # .gitignore must contain the upgrade-backup-*/ entry (written before Step 2 ran)
    gitignore = target / ".gitignore"
    assert gitignore.is_file(), ".gitignore must exist after Step 1"
    content = gitignore.read_text(encoding="utf-8")
    assert "upgrade-backup-*/" in content, \
        ".gitignore must contain upgrade-backup-*/ after Step 1 completes"
