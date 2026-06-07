"""test_bundle_excludes_telemetry — the A1 telemetry layer must NEVER reach a
recipient bundle.

Two independent layers, deliberately distinct (a leak in either is a real bug):
  1. By construction — the whitelist manifest names no telemetry path, so
     resolve_selection yields no `.claude/telemetry/` member and none of the
     CM-local telemetry hooks. Fast, deterministic, the PRIMARY guarantee.
  2. Regression sentinel — a REAL `python -m pack` build, asserted non-empty
     FIRST (else a vacuous pass), then scanned for any `.claude/telemetry/`
     member or telemetry hook `.py`. Catches a leak that bypasses selection.

Telemetry hooks are CM-repo source but are intentionally absent from the
manifest's `hooks:` list, so they ride neither the slug walk nor an explicit
entry — they stay home.
"""

from __future__ import annotations

import glob
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

import manifest_loader  # type: ignore[import-not-found]
from pack.selection import resolve_selection

REPO_ROOT = Path(__file__).resolve().parents[5]
MANIFEST = REPO_ROOT / ".claude" / "pack.manifest.yaml"

TELEMETRY_HOOK_BASENAMES = {
    "track_skill_invocation.py",
    "track_script_execution.py",
    "emit_session_summary.py",
    # usage-&-health additions (Phase 2) — same exclusion guarantee.
    "mark_bash_start.py",
    "track_subagent_outcome.py",
}

# New sink the SubagentStop hook writes — must never reach a bundle either.
TELEMETRY_SINK_BASENAMES = {"subagent-outcomes.jsonl"}


def _arcs() -> set[str]:
    manifest = manifest_loader.load(MANIFEST)
    return {arc for _, arc in resolve_selection(manifest, REPO_ROOT)}


@pytest.mark.bug_class
def test_selection_excludes_telemetry_by_construction():
    arcs = _arcs()
    leaks = [a for a in arcs if "/.claude/telemetry/" in f"/{a}" or a.startswith(".claude/telemetry/")]
    assert not leaks, f"telemetry sink path leaked into bundle file set: {leaks}"
    hook_leaks = [a for a in arcs if Path(a).name in TELEMETRY_HOOK_BASENAMES]
    assert not hook_leaks, f"CM-local telemetry hook leaked into bundle file set: {hook_leaks}"
    # The cleanmatic:telemetry SKILL dir is CM-local too (absent from manifest skills:).
    skill_leaks = [a for a in arcs if "/.claude/skills/telemetry/" in f"/{a}"
                   or a.startswith(".claude/skills/telemetry/")]
    assert not skill_leaks, f"cleanmatic:telemetry skill leaked into bundle file set: {skill_leaks}"


@pytest.mark.bug_class
def test_real_tarball_excludes_telemetry(tmp_path):
    out_dir = tmp_path / "dist"
    out_dir.mkdir()
    r = subprocess.run(
        [sys.executable, "-m", "pack", "--root", str(REPO_ROOT), "--manifest", str(MANIFEST),
         "--version", "0.0.0-test", "--allow-dev-version", "--out", str(out_dir)],
        capture_output=True, text=True, cwd=str(REPO_ROOT / ".claude" / "skills" / "release" / "scripts"),
    )
    assert r.returncode == 0, f"pack build failed: {r.stderr or r.stdout}"
    tarballs = glob.glob(str(out_dir / "*.tar.gz"))
    assert tarballs, "no tarball produced"

    with tarfile.open(tarballs[0], "r:gz") as tar:
        members = tar.getnames()

    # Guard against a vacuous pass: an empty tar would trivially "exclude" telemetry.
    assert len(members) > 5, f"tarball suspiciously small ({len(members)} members)"

    tel = [m for m in members
           if "/.claude/telemetry/" in f"/{m}" or "/.claude/telemetry" in m
           or "/.claude/skills/telemetry/" in f"/{m}"
           or Path(m).name in (TELEMETRY_HOOK_BASENAMES | TELEMETRY_SINK_BASENAMES)]
    assert not tel, f"telemetry (skill / hook / sink) leaked into the real tarball: {tel}"


@pytest.mark.bug_class
def test_telemetry_exempt_from_version_sync_assertion():
    """telemetry is in verify_skill_versions.DEFAULT_SKILLS (semver-checked) but
    MUST stay OUT of test_version_sync.VERSION_SYNCED_SKILLS — it never ships, so
    its version is not pinned to a bundle/changelog identity (D8)."""
    from verify_skill_versions import DEFAULT_SKILLS
    from test_version_sync import VERSION_SYNCED_SKILLS
    assert "telemetry" in DEFAULT_SKILLS, "telemetry should be semver-checked"
    assert "telemetry" not in VERSION_SYNCED_SKILLS, "telemetry must NOT be changelog-pinned (never ships)"


@pytest.mark.bug_class
def test_no_shipped_script_imports_a_telemetry_module():
    """The D5/F1 guarantee: no SHIPPED skill script imports a CM-local telemetry
    module (telemetry_paths / catalog / lens_* / analyze_telemetry / telemetry_render /
    formatters from _shared). _shared is not bundled → such an import would
    ModuleNotFoundError on a recipient."""
    import re as _re
    shipped = ("product-spec", "product-spec-critique", "release")
    banned = _re.compile(
        r"\b(import|from)\s+(telemetry_paths|catalog|telemetry_render|analyze_telemetry"
        r"|formatters|lens_[a-z_]+)\b")
    offenders = []
    for skill in shipped:
        for py in (REPO_ROOT / ".claude" / "skills" / skill).rglob("*.py"):
            if "__tests__" in py.parts or "tests" in py.parts:
                continue  # tests may import freely; they don't ship-run
            for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                if banned.search(line):
                    offenders.append(f"{py.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not offenders, "shipped script imports a CM-local telemetry module:\n" + "\n".join(offenders)
