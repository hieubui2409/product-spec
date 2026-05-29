"""test_pack_determinism — tarball reproducibility + safety + LOC budget."""

from __future__ import annotations

import io
import json
import os
import subprocess
import tarfile
import time
from pathlib import Path

import pytest

from pack.manifest_io import (
    CollisionError, atomic_replace, build_manifest_json,
    cleanup_stale_tmp, filter_findings,
)
from pack.selection import render_embedded, resolve_selection
from pack.tarball import build_tarball, verify_gzip_mtime_zero
from pack.templates import TemplateError, render
import manifest_loader


SKILL_ROOT = Path(__file__).resolve().parent.parent.parent


def _pack_to(tmp_root: Path, out_path: Path):
    """Run a full pack from tmp_root into a single .tar.gz at out_path."""
    manifest = manifest_loader.apply_defaults(
        {"version": "0.1.0", "bundle_name": "test-pack",
         "skills": ["sample-skill"]},
        tmp_root,
    )
    selection = resolve_selection(manifest, tmp_root)
    bundle_root = "test-pack-0.1.0"
    versioned = [(src, f"{bundle_root}/{arc}") for src, arc in selection]
    versioned.sort(key=lambda x: x[1].encode("utf-8"))
    manifest_json = build_manifest_json(versioned, manifest,
                                        source_date_epoch=0, repo_root=tmp_root)
    parsed = json.loads(manifest_json)
    tokens = {
        "BUNDLE_NAME": "test-pack",
        "VERSION": "0.1.0", "BUILT_AT": parsed.get("built_at", ""),
        "SOURCE_COMMIT": parsed.get("source_commit", "unknown"),
        "FILE_COUNT": str(len(selection)), "TOTAL_SIZE": "x bytes",
    }
    embedded = render_embedded(
        SKILL_ROOT, bundle_root_dir=bundle_root,
        manifest_json=manifest_json, tokens=tokens,
    )
    with out_path.open("wb") as f:
        sha = build_tarball(versioned, embedded, f, source_date_epoch=0)
    return sha, versioned, embedded


def test_two_runs_byte_identical(tmp_root, tmp_path):
    """two consecutive runs produce identical sha256."""
    p1 = tmp_path / "a.tar.gz"
    p2 = tmp_path / "b.tar.gz"
    sha1, _, _ = _pack_to(tmp_root, p1)
    sha2, _, _ = _pack_to(tmp_root, p2)
    assert sha1 == sha2
    assert p1.read_bytes() == p2.read_bytes()


def test_built_at_deterministic_by_default(tmp_root, tmp_path):
    """built_at must NOT use wall-clock when source_date_epoch=0 (else two runs
    in different seconds differ). Pins to epoch -> byte-identical by default."""
    manifest = manifest_loader.apply_defaults(
        {"version": "0.1.0", "bundle_name": "t"}, tmp_root)
    mj = build_manifest_json([], manifest, source_date_epoch=0, repo_root=tmp_root)
    built_at = json.loads(mj)["built_at"]
    assert built_at == "1970-01-01T00:00:00+00:00", built_at
    mj2 = build_manifest_json([], manifest, source_date_epoch=1700000000,
                              repo_root=tmp_root)
    assert json.loads(mj2)["built_at"].startswith("2023-")


def test_versioned_root_dir(tmp_root, tmp_path):
    """top entries under versioned root."""
    p = tmp_path / "pack.tar.gz"
    _pack_to(tmp_root, p)
    with tarfile.open(p, "r:gz") as tar:
        names = tar.getnames()
    assert any(n.startswith("test-pack-0.1.0/") for n in names)


def test_manifest_json_schema(tmp_root, tmp_path):
    """MANIFEST.json schema_version 1.0 + per-file SHA256."""
    p = tmp_path / "pack.tar.gz"
    _pack_to(tmp_root, p)
    with tarfile.open(p, "r:gz") as tar:
        f = tar.extractfile("test-pack-0.1.0/MANIFEST.json")
        assert f is not None
        manifest = json.loads(f.read())
    assert manifest["schema_version"] == "1.0"
    assert len(manifest["files"]) > 0
    for entry in manifest["files"]:
        assert "sha256" in entry and len(entry["sha256"]) == 64
        assert "size" in entry and entry["size"] >= 0


def test_gzip_mtime_zero(tmp_root, tmp_path):
    """gzip header bytes [4:8] == 00000000."""
    p = tmp_path / "pack.tar.gz"
    _pack_to(tmp_root, p)
    data = p.read_bytes()
    assert data[4:8] == b"\x00\x00\x00\x00"
    assert verify_gzip_mtime_zero(p)


def test_all_entries_normalized(tmp_root, tmp_path):
    """uid/gid=0, uname/gname empty, mode 0o644/0o755."""
    p = tmp_path / "pack.tar.gz"
    _pack_to(tmp_root, p)
    with tarfile.open(p, "r:gz") as tar:
        for info in tar.getmembers():
            assert info.uid == 0
            assert info.gid == 0
            assert info.uname == ""
            assert info.gname == ""
            assert info.mode in (0o644, 0o755)


def test_dry_run_sha_matches_real(tmp_root, tmp_path):
    """BytesIO compute-sha returns same hex as real-file run."""
    real = tmp_path / "real.tar.gz"
    sha_real, versioned, embedded = _pack_to(tmp_root, real)
    sha_buf = build_tarball(versioned, embedded, io.BytesIO(),
                            source_date_epoch=0)
    assert sha_real == sha_buf


def test_empty_selection_rejected(tmp_root):
    """empty selection gives 0 entries."""
    manifest = manifest_loader.apply_defaults(
        {"version": "0.1.0", "bundle_name": "x"}, tmp_root)
    manifest["extra"] = []
    manifest["skills"] = []
    sel = resolve_selection(manifest, tmp_root)
    assert sel == []


def test_symlink_dropped(tmp_root, tmp_path):
    """symlink in selection dropped + WARN."""
    skill = tmp_root / ".claude" / "skills" / "sample-skill"
    link = skill / "evil-link"
    try:
        link.symlink_to("/etc/passwd")
    except OSError:
        pytest.skip("symlink not supported on this filesystem")
    p = tmp_path / "pack.tar.gz"
    _pack_to(tmp_root, p)
    with tarfile.open(p, "r:gz") as tar:
        names = tar.getnames()
    assert not any(n.endswith("/evil-link") for n in names)


def test_unknown_template_token_raises():
    """unknown {{TOKEN}} raises TemplateError."""
    with pytest.raises(TemplateError):
        render("{{XYZ}}", {"VERSION": "1.0"})


def test_atomic_replace_collision(tmp_path):
    """collision without force raises CollisionError."""
    src = tmp_path / ".tmp"
    src.write_bytes(b"x")
    dst = tmp_path / "out"
    dst.write_bytes(b"existing")
    with pytest.raises(CollisionError):
        atomic_replace(src, dst, force=False)


def test_atomic_replace_force_backs_up(tmp_path):
    """--force backs up to .bak.{epoch}."""
    src = tmp_path / ".tmp"
    src.write_bytes(b"new")
    dst = tmp_path / "out"
    dst.write_bytes(b"old")
    atomic_replace(src, dst, force=True)
    assert dst.read_bytes() == b"new"
    backups = list(tmp_path.glob("out.bak.*"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == b"old"


def test_cleanup_stale_tmp(tmp_path):
    """tmp files >1h old removed on startup."""
    old_tmp = tmp_path / ".old.tmp"
    fresh_tmp = tmp_path / ".fresh.tmp"
    old_tmp.write_bytes(b"x")
    fresh_tmp.write_bytes(b"y")
    old = time.time() - 7200
    os.utime(old_tmp, (old, old))
    removed = cleanup_stale_tmp(tmp_path, max_age=3600)
    assert removed == 1
    assert not old_tmp.exists()
    assert fresh_tmp.exists()


def test_pack_subpackage_loc_budget():
    """every pack/*.py < 200 LOC."""
    pack_dir = SKILL_ROOT / "scripts" / "pack"
    for f in pack_dir.glob("*.py"):
        loc = len(f.read_text(encoding="utf-8").splitlines())
        assert loc < 200, f"{f.name} has {loc} lines (limit 200)"


def test_all_flag_errors_not_implemented(tmp_root, tmp_path):
    """--all is not implemented in v0.1; must error (exit 1), not silently no-op."""
    from pack.cli import main
    rc = main(["--all", "--root", str(tmp_root), "--out", str(tmp_path / "o")])
    assert rc == 1


def test_strict_gates_on_uncovered_shared_ref(tmp_root, tmp_path):
    """--strict exits 2 when a packed skill references an un-included _shared/ name."""
    from pack.cli import main
    skill = tmp_root / ".claude" / "skills" / "needs-shared"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: cleanmatic:needs-shared\n"
        "metadata:\n  version: \"0.1.0\"\n---\n\n"
        "# needs-shared\n\nUses _shared/common helpers.\n",
        encoding="utf-8",
    )
    manifest = tmp_root / ".claude" / "pack.manifest.yaml"
    manifest.write_text(
        "schema_version: '1.0'\nversion: '0.1.0'\nbundle_name: s\n"
        "skills:\n  - needs-shared\n"
        "agents: []\nhooks: []\nrules: []\nextra: []\n"
        "top_level: {}\n"
        "defaults:\n  include_scripts: false\n  include_schemas: false\n"
        "follow_shared: false\n",
        encoding="utf-8",
    )
    rc = main(["--strict", "--root", str(tmp_root),
               "--manifest", str(manifest), "--out", str(tmp_path / "o")])
    assert rc == 2  # EXIT_STRICT
    # Without --strict it builds fine (warning only).
    rc2 = main(["--root", str(tmp_root),
                "--manifest", str(manifest), "--out", str(tmp_path / "o2")])
    assert rc2 == 0


def test_pack_cli_full_run(tmp_root, tmp_path):
    """End-to-end: invoke python -m pack and verify output structure."""
    venv_py = SKILL_ROOT.parent / ".venv" / "bin" / "python3"
    if not venv_py.is_file():
        pytest.skip("venv not present")
    manifest_path = tmp_root / ".claude" / "pack.manifest.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "schema_version: '1.0'\n"
        "version: '0.1.0'\n"
        "bundle_name: cli-pack\n"
        "skills:\n  - sample-skill\n"
        "agents: []\nhooks: []\nrules: []\nextra: []\n"
        "top_level: {}\n"
        "defaults:\n  include_scripts: false\n  include_schemas: false\n"
        "follow_shared: false\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    result = subprocess.run(
        [str(venv_py), "-m", "pack",
         "--root", str(tmp_root),
         "--manifest", str(manifest_path),
         "--out", str(out_dir),
         "--json"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    final = out_dir / "cli-pack-0.1.0.tar.gz"
    assert final.is_file()
    assert (out_dir / "cli-pack-0.1.0.tar.gz.sha256").is_file()
