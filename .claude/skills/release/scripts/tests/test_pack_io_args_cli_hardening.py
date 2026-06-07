"""Regression tests for pack IO/args/CLI/build_manifest hardening.

Covers:
- manifest_io: source_repo userinfo scrubbing (never ship a credentialed remote URL)
- manifest_io: atomic_replace branches on errno.EXDEV, not a message substring
- pack/args: resolve_epoch rejects a negative --source-date-epoch (SystemExit)
- pack/args: resolve_epoch env branch returns 0 on a unicode-digit value (not ValueError)
- pack/cli: --dry-run reports the max-size gate (over_max_size field)
- build_manifest: discover excludes ambiguous (same-stem) agent/rule names
- build_manifest: discover enumerates hooks in nested subdirectories
"""

from __future__ import annotations

import argparse
import errno
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import pack.manifest_io as manifest_io
from pack.manifest_io import atomic_replace, CollisionError
from pack.args import resolve_epoch
import build_manifest


# ---------------------------------------------------------------------------
# source_repo userinfo scrubbing
# ---------------------------------------------------------------------------

def test_source_repo_scrubs_userinfo(tmp_path):
    """build_manifest_json strips user:token from source_repo URL."""
    selection: list = []
    bundle = {"bundle_name": "test", "version": "1.0.0"}

    with patch.object(manifest_io, "_git_command") as mock_git:
        def fake_git(args, cwd):
            if args[0] == "rev-parse":
                return "abc123"
            if args[0] == "remote":
                return "https://user:supersecrettoken@github.com/org/repo.git"
            return ""
        mock_git.side_effect = fake_git

        result = manifest_io.build_manifest_json(
            selection, bundle, source_date_epoch=0, repo_root=tmp_path,
        )

    import json
    payload = json.loads(result)
    assert "supersecrettoken" not in payload["source_repo"]
    assert payload["source_repo"] == "https://github.com/org/repo.git"


def test_source_repo_scrubs_user_only(tmp_path):
    """build_manifest_json strips user@ (no password) from source_repo URL."""
    selection: list = []
    bundle = {"bundle_name": "test", "version": "1.0.0"}

    with patch.object(manifest_io, "_git_command") as mock_git:
        def fake_git(args, cwd):
            if args[0] == "rev-parse":
                return "abc123"
            if args[0] == "remote":
                return "https://someuser@github.com/org/repo.git"
            return ""
        mock_git.side_effect = fake_git

        result = manifest_io.build_manifest_json(
            selection, bundle, source_date_epoch=0, repo_root=tmp_path,
        )

    import json
    payload = json.loads(result)
    assert "someuser" not in payload["source_repo"]
    assert payload["source_repo"] == "https://github.com/org/repo.git"


def test_source_repo_plain_url_unchanged(tmp_path):
    """build_manifest_json leaves a plain URL (no userinfo) untouched."""
    selection: list = []
    bundle = {"bundle_name": "test", "version": "1.0.0"}

    with patch.object(manifest_io, "_git_command") as mock_git:
        def fake_git(args, cwd):
            if args[0] == "rev-parse":
                return "abc123"
            if args[0] == "remote":
                return "https://github.com/org/repo.git"
            return ""
        mock_git.side_effect = fake_git

        result = manifest_io.build_manifest_json(
            selection, bundle, source_date_epoch=0, repo_root=tmp_path,
        )

    import json
    payload = json.loads(result)
    assert payload["source_repo"] == "https://github.com/org/repo.git"


# ---------------------------------------------------------------------------
# atomic_replace branches on errno.EXDEV, not a message substring
# ---------------------------------------------------------------------------

def test_atomic_replace_exdev_falls_back_to_shutil(tmp_path):
    """atomic_replace uses shutil.move on EXDEV (cross-device errno)."""
    src = tmp_path / "src.tar.gz"
    dst = tmp_path / "dst.tar.gz"
    src.write_bytes(b"data")

    cross_dev_err = OSError(errno.EXDEV, "Invalid cross-device link")

    with patch("pack.manifest_io.os.replace", side_effect=cross_dev_err), \
         patch("pack.manifest_io.shutil.move") as mock_move:
        atomic_replace(src, dst, force=False)

    mock_move.assert_called_once()


def test_atomic_replace_non_exdev_does_not_fall_back(tmp_path):
    """atomic_replace does NOT call shutil.move for non-EXDEV OSErrors."""
    src = tmp_path / "src.tar.gz"
    dst = tmp_path / "dst.tar.gz"
    src.write_bytes(b"data")

    permission_err = OSError(errno.EPERM, "Operation not permitted")

    with patch("pack.manifest_io.os.replace", side_effect=permission_err), \
         patch("pack.manifest_io.shutil.move") as mock_move:
        with pytest.raises(OSError):
            atomic_replace(src, dst, force=False)

    mock_move.assert_not_called()


def test_atomic_replace_string_exdev_does_not_fall_back(tmp_path):
    """Confirm the old string-match path ('EXDEV' in str(e)) is no longer used.

    An OSError whose message text contains 'EXDEV' but whose errno is NOT
    errno.EXDEV must NOT trigger the cross-device fallback.
    """
    src = tmp_path / "src.tar.gz"
    dst = tmp_path / "dst.tar.gz"
    src.write_bytes(b"data")

    # errno=EIO but message text contains 'EXDEV' — old code would have fallen through
    text_only_err = OSError(errno.EIO, "fake EXDEV text in message")

    with patch("pack.manifest_io.os.replace", side_effect=text_only_err), \
         patch("pack.manifest_io.shutil.move") as mock_move:
        with pytest.raises(OSError):
            atomic_replace(src, dst, force=False)

    mock_move.assert_not_called()


# ---------------------------------------------------------------------------
# resolve_epoch rejects negative values
# ---------------------------------------------------------------------------

def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"source_date_epoch": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_resolve_epoch_negative_raises_systemexit():
    """resolve_epoch rejects negative --source-date-epoch."""
    with pytest.raises(SystemExit, match=">="):
        resolve_epoch(_ns(source_date_epoch="-1"))


def test_resolve_epoch_zero_allowed():
    """resolve_epoch accepts 0."""
    assert resolve_epoch(_ns(source_date_epoch="0")) == 0


def test_resolve_epoch_positive_allowed():
    """resolve_epoch accepts positive integer."""
    assert resolve_epoch(_ns(source_date_epoch="1700000000")) == 1700000000


def test_resolve_epoch_none_returns_zero():
    """resolve_epoch returns 0 when no flag given."""
    assert resolve_epoch(_ns(source_date_epoch=None)) == 0


# ---------------------------------------------------------------------------
# resolve_epoch env branch — unicode-digit -> 0 (not ValueError)
# ---------------------------------------------------------------------------

def test_resolve_epoch_env_unicode_digit_returns_zero(monkeypatch):
    """str.isdigit() is True for unicode chars like '²'; str.isascii() guards this.

    An env var that passes isdigit() but not isascii() must return 0, not raise.
    """
    # '²' (SUPERSCRIPT TWO) — isdigit() returns True, isascii() returns False
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "²")
    result = resolve_epoch(_ns(source_date_epoch="env"))
    assert result == 0


def test_resolve_epoch_env_valid_ascii_digit(monkeypatch):
    """resolve_epoch env branch parses a plain ASCII integer."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    assert resolve_epoch(_ns(source_date_epoch="env")) == 1700000000


def test_resolve_epoch_env_empty_returns_zero(monkeypatch):
    """resolve_epoch env branch returns 0 when SOURCE_DATE_EPOCH is absent."""
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    assert resolve_epoch(_ns(source_date_epoch="env")) == 0


# ---------------------------------------------------------------------------
# resolve_epoch upper bound — an over-range epoch would OverflowError deep in
# manifest_io's datetime.fromtimestamp; reject it at the boundary instead.
# ---------------------------------------------------------------------------

def test_resolve_epoch_over_max_raises_systemexit():
    """An epoch beyond year 9999 must be rejected (SystemExit), not crash later."""
    with pytest.raises(SystemExit):
        resolve_epoch(_ns(source_date_epoch=str(10 ** 20)))


def test_resolve_epoch_max_boundary_allowed():
    """The exact ceiling (9999-12-31T23:59:59Z) is accepted."""
    assert resolve_epoch(_ns(source_date_epoch="253402300799")) == 253402300799


def test_resolve_epoch_env_over_max_returns_zero(monkeypatch):
    """An out-of-range env SOURCE_DATE_EPOCH falls back to 0 (ambient provenance)."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", str(10 ** 20))
    assert resolve_epoch(_ns(source_date_epoch="env")) == 0


# ---------------------------------------------------------------------------
# templates.render_template — undecodable bytes become TemplateError
# ---------------------------------------------------------------------------

def test_render_template_undecodable_raises_template_error(tmp_path):
    """A non-UTF-8 template file must surface as TemplateError, not a bare
    UnicodeDecodeError leaking past the documented single-exception contract."""
    from pack.templates import render_template, TemplateError
    p = tmp_path / "bad.tmpl"
    p.write_bytes(b"\xff\xfe not utf-8")
    with pytest.raises(TemplateError):
        render_template(p, {})


# ---------------------------------------------------------------------------
# dry-run reports the max-size gate (over_max_size field)
# ---------------------------------------------------------------------------

import subprocess
import sys as _sys

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent


def _write_sample_manifest(tmp_root: Path) -> None:
    manifest_path = tmp_root / ".claude" / "pack.manifest.yaml"
    manifest_path.write_text(
        "schema_version: '1.0'\nversion: 0.0.0-dev\n"
        "bundle_name: test\nskills:\n- sample-skill\n"
        "agents: []\nhooks: []\nrules: []\nextra: []\n"
        "top_level:\n  include_readme: false\n  include_claudemd: false\n"
        "  include_settings: false\n  include_ck_config: false\n"
        "follow_shared: false\n",
        encoding="utf-8",
    )


def _run_pack_subprocess(tmp_root: Path, extra_argv: list[str]) -> dict:
    """Run ``python -m pack`` in a subprocess and return parsed JSON stdout.

    _emit(args, payload, fp=sys.stdout) binds fp to the stdout object at
    definition time, so in-process patching of sys.stdout never reaches it.
    Subprocess avoids the binding problem entirely and matches real-world use.
    """
    import json
    result = subprocess.run(
        [_sys.executable, "-m", "pack",
         "--root", str(tmp_root),
         "--json",
         "--allow-dev-version",
         *extra_argv],
        capture_output=True, text=True,
        cwd=str(_SCRIPTS_DIR),
        env={**os.environ, "SOURCE_DATE_EPOCH": "0"},
    )
    return json.loads(result.stdout)


def test_dry_run_over_max_size_field_present(tmp_root):
    """--dry-run --compute-sha output includes over_max_size: true when compressed > max_size."""
    _write_sample_manifest(tmp_root)
    payload = _run_pack_subprocess(tmp_root, [
        "--dry-run", "--compute-sha", "--max-size", "1",
    ])
    assert "over_max_size" in payload, f"over_max_size missing: {payload}"
    assert "max_size" in payload, f"max_size missing: {payload}"
    assert payload["over_max_size"] is True
    assert payload["max_size"] == 1


def test_dry_run_without_compute_sha_has_over_max_size_null(tmp_root):
    """--dry-run without --compute-sha emits over_max_size: null (not false).

    We cannot know whether the compressed output would exceed max_size without
    actually compressing, so null is the honest value.  Callers must not
    interpret null as a passing verdict.
    """
    _write_sample_manifest(tmp_root)
    payload = _run_pack_subprocess(tmp_root, ["--dry-run"])
    assert "over_max_size" in payload
    assert payload["over_max_size"] is None


# ---------------------------------------------------------------------------
# discover excludes ambiguous stems (same stem, multiple paths)
# ---------------------------------------------------------------------------

def test_discover_excludes_ambiguous_agent_stems(tmp_path):
    """discover does not offer stems that have more than one backing file."""
    agents = tmp_path / ".claude" / "agents"
    (agents / "subdir").mkdir(parents=True)
    (agents / "planner.md").write_text("# planner\n", encoding="utf-8")
    # Same stem 'planner' in a subdirectory — would cause an ambiguous-match error
    (agents / "subdir" / "planner.md").write_text("# planner v2\n", encoding="utf-8")
    # Unique stem — should still be offered
    (agents / "researcher.md").write_text("# researcher\n", encoding="utf-8")

    # Minimal .claude layout
    (tmp_path / ".claude" / "skills").mkdir(exist_ok=True)
    (tmp_path / ".claude" / "rules").mkdir(exist_ok=True)
    (tmp_path / ".claude" / "hooks").mkdir(exist_ok=True)

    d = build_manifest.discover(tmp_path)
    assert "planner" not in d["available_agents"], \
        "ambiguous stem 'planner' must be excluded from offered options"
    assert "researcher" in d["available_agents"], \
        "unambiguous stem 'researcher' must still be offered"


# ---------------------------------------------------------------------------
# discover (hooks) recurses into subdirectories
# ---------------------------------------------------------------------------

def test_discover_hooks_recurses_into_subdirectories(tmp_path):
    """discover enumerates hook files in nested subdirectories."""
    hooks = tmp_path / ".claude" / "hooks"
    (hooks / "subdir").mkdir(parents=True)
    (hooks / "top-hook.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    (hooks / "subdir" / "nested-hook.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    (tmp_path / ".claude" / "agents").mkdir(exist_ok=True)
    (tmp_path / ".claude" / "rules").mkdir(exist_ok=True)
    (tmp_path / ".claude" / "skills").mkdir(exist_ok=True)

    d = build_manifest.discover(tmp_path)
    hook_names = d["available_hooks"]
    assert "top-hook.sh" in hook_names
    assert "subdir/nested-hook.sh" in hook_names, \
        f"nested hook not found in {hook_names}"
