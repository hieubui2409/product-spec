"""test_bundle_includes_telemetry — the telemetry usage-&-health skill + its sink
hooks + the shared observability/eval code MUST reach a recipient bundle (the PO
reversed the original CM-local decision so end users can run the lenses).

Two independent layers, deliberately distinct (a regression in either is a real bug):
  1. By construction — the whitelist manifest names the telemetry skill, the 5
     hooks, and `_include_shared: [lib, scripts]`, so resolve_selection yields the
     skill dir, every hook, and the shared lens/eval modules. Fast, deterministic.
  2. Regression sentinel — a REAL `python -m pack` build, asserted non-empty FIRST
     (else a vacuous pass), then scanned to confirm the telemetry surface is present
     AND that two things stay OUT: runtime sinks (`.claude/telemetry/*.jsonl`) and
     test dirs (`__tests__/` / `tests/`, dropped by safety_catalog).

Runtime sinks are gitignored data, never a manifest path → they never ship. Test
suites are dev artifacts dropped by safety_catalog.ALWAYS_DROP_DIRS.
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
    "mark_bash_start.py",
    "track_subagent_outcome.py",
}

# A representative slice of the shared code the skill + hooks need at runtime.
SHARED_MODULE_ARCS = {
    ".claude/skills/_shared/lib/telemetry_paths.py",
    ".claude/skills/_shared/lib/telemetry_render.py",
    ".claude/skills/_shared/lib/lens_usage_tokens.py",
    ".claude/skills/_shared/lib/run_evals.py",
    ".claude/skills/_shared/lib/llm_eval.py",
    ".claude/skills/_shared/scripts/analyze_telemetry.py",
    ".claude/skills/_shared/scripts/register_telemetry_hooks.py",
}

# Runtime sink the SubagentStop hook writes — gitignored data, must NEVER ship.
TELEMETRY_SINK_BASENAMES = {"subagent-outcomes.jsonl"}


def _arcs() -> set[str]:
    manifest = manifest_loader.load(MANIFEST)
    return {arc for _, arc in resolve_selection(manifest, REPO_ROOT)}


@pytest.mark.bug_class
def test_selection_includes_telemetry_by_construction():
    arcs = _arcs()
    # The telemetry skill dir ships.
    assert any(a.startswith(".claude/skills/telemetry/") for a in arcs), \
        "cleanmatic:telemetry skill missing from bundle file set"
    # All 5 sink hooks ship.
    missing_hooks = TELEMETRY_HOOK_BASENAMES - {Path(a).name for a in arcs}
    assert not missing_hooks, f"telemetry hooks missing from bundle file set: {missing_hooks}"
    # The shared lens + eval-gate code ships (so the CLI + hooks import-resolve).
    missing_shared = SHARED_MODULE_ARCS - arcs
    assert not missing_shared, f"shared telemetry/eval modules missing from bundle: {missing_shared}"
    # Runtime sinks are NOT a manifest path → never selected.
    sink_leaks = [a for a in arcs if "/.claude/telemetry/" in f"/{a}" or a.startswith(".claude/telemetry/")]
    assert not sink_leaks, f"runtime telemetry sink leaked into bundle file set: {sink_leaks}"


@pytest.mark.bug_class
def test_real_tarball_includes_telemetry_excludes_sinks_and_tests(tmp_path):
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

    # Guard against a vacuous pass.
    assert len(members) > 5, f"tarball suspiciously small ({len(members)} members)"

    def _present(pred) -> bool:
        return any(pred(m) for m in members)

    # PRESENT: skill dir, every hook, the shared modules.
    assert _present(lambda m: "/.claude/skills/telemetry/" in f"/{m}" or m.startswith(".claude/skills/telemetry/")), \
        "telemetry skill missing from real tarball"
    missing_hooks = TELEMETRY_HOOK_BASENAMES - {Path(m).name for m in members}
    assert not missing_hooks, f"telemetry hooks missing from real tarball: {missing_hooks}"
    missing_shared = {s for s in SHARED_MODULE_ARCS
                      if not _present(lambda m, s=s: m == s or m.endswith("/" + s))}
    assert not missing_shared, f"shared telemetry/eval modules missing from real tarball: {missing_shared}"

    # ABSENT: runtime sinks + test dirs (dropped by safety_catalog).
    sink_leaks = [m for m in members
                  if "/.claude/telemetry/" in f"/{m}"
                  or Path(m).name in TELEMETRY_SINK_BASENAMES]
    assert not sink_leaks, f"runtime telemetry sink leaked into real tarball: {sink_leaks}"
    test_leaks = [m for m in members if "__tests__" in Path(m).parts or "tests" in Path(m).parts]
    assert not test_leaks, f"test artifacts leaked into real tarball: {test_leaks}"


@pytest.mark.bug_class
def test_telemetry_included_in_version_sync():
    """telemetry now SHIPS → it is both semver-checked (DEFAULT_SKILLS) AND
    changelog-pinned (VERSION_SYNCED_SKILLS): its SKILL.md version must equal its
    CHANGELOG top, like every other shipped skill."""
    from verify_skill_versions import DEFAULT_SKILLS
    from test_version_sync import VERSION_SYNCED_SKILLS
    assert "telemetry" in DEFAULT_SKILLS, "telemetry should be semver-checked"
    assert "telemetry" in VERSION_SYNCED_SKILLS, "telemetry now ships → must be changelog-pinned"


@pytest.mark.bug_class
def test_core_skills_stay_telemetry_independent():
    """Hygiene guarantee (narrowed from the old D5/F1 ban): the three CORE skills
    (product-spec, product-spec-critique, release) must NOT import the telemetry/
    eval _shared modules — they stay self-contained and functional even without the
    observability layer. The telemetry skill itself is exempt (it legitimately uses
    _shared, which now ships alongside it)."""
    import re as _re
    core = ("product-spec", "product-spec-critique", "release")
    banned = _re.compile(
        r"\b(import|from)\s+(telemetry_paths|catalog|telemetry_render|analyze_telemetry"
        r"|formatters|lens_[a-z_]+)\b")
    offenders = []
    for skill in core:
        for py in (REPO_ROOT / ".claude" / "skills" / skill).rglob("*.py"):
            if "__tests__" in py.parts or "tests" in py.parts:
                continue  # tests may import freely; they don't ship-run
            for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
                if banned.search(line):
                    offenders.append(f"{py.relative_to(REPO_ROOT)}:{i}: {line.strip()}")
    assert not offenders, "core skill imports a telemetry/eval module (keep them self-contained):\n" + "\n".join(offenders)
