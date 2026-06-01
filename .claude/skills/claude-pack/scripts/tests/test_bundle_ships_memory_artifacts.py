"""test_bundle_ships_memory_artifacts — the live bundle ships the memory layer's
top-level agent + hook handler.

The memory-harvester agent and the memory_gap_hook handler live at the repo's
top-level `.claude/agents/` and `.claude/hooks/` (NOT inside a skill subtree), so
the slug-rglob skill walk never picks them up. They reach the recipient only via
explicit `agents:` / `hooks:` manifest entries. These tests guard the resolver
contract end-to-end against the REAL manifest so a future hand-edit that drops or
misnames an entry — or a settings-registration leak — fails loudly.

The hook handler SHIPS as a capability but is NEVER auto-registered in settings:
`include_settings` must stay false, and no settings.json is bundled. Enabling the
hook is an opt-in `install.sh --memory-hook` step on the recipient side.
"""

from __future__ import annotations

from pathlib import Path

import manifest_loader  # type: ignore[import-not-found]
from pack.selection import resolve_selection

REPO_ROOT = Path(__file__).resolve().parents[5]
MANIFEST_PATH = REPO_ROOT / ".claude" / "pack.manifest.yaml"

AGENT_ARC = ".claude/agents/memory-harvester.md"
HOOK_ARC = ".claude/hooks/memory_gap_hook.py"


def _load_real_manifest() -> dict:
    return manifest_loader.load(MANIFEST_PATH)


def test_manifest_lists_memory_agent_and_hook():
    """The real manifest must name the harvester agent and the hook handler so the
    slug walk's blind spot (top-level agents/hooks) is covered by explicit entries."""
    manifest = _load_real_manifest()
    assert "memory-harvester.md" in manifest.get("agents", []), \
        "agents: must list memory-harvester.md (top-level agent, not under a skill)"
    assert "memory_gap_hook.py" in manifest.get("hooks", []), \
        "hooks: must list memory_gap_hook.py (top-level hook handler)"


def test_real_manifest_validates_clean():
    """The hand-edited manifest must still pass validation (no E071/E073/E074:
    missing/ambiguous agent or hook) against the real repo tree."""
    manifest = _load_real_manifest()
    errors = manifest_loader.validate(manifest, REPO_ROOT)
    offending = [e for e in errors
                 if any(code in e for code in
                        ("MANIFEST_E071", "MANIFEST_E073", "MANIFEST_E074"))]
    assert not offending, f"agent/hook resolution errors: {offending}"


def test_selection_bundles_memory_agent_and_hook():
    """Resolving the real manifest against the real repo must place BOTH the
    harvester agent and the hook handler in the bundle file set."""
    manifest = _load_real_manifest()
    arcs = {arc for _, arc in resolve_selection(manifest, REPO_ROOT)}
    assert AGENT_ARC in arcs, f"{AGENT_ARC} missing from bundle file set"
    assert HOOK_ARC in arcs, f"{HOOK_ARC} missing from bundle file set"


def test_no_settings_registration_bundled():
    """The hook ships as a capability but is opt-in: include_settings stays false
    and no settings.json arcname appears, so the bundle never auto-wires the hook."""
    manifest = _load_real_manifest()
    assert manifest.get("top_level", {}).get("include_settings") is False, \
        "include_settings must stay false (opt-in hook, no auto-registration)"
    arcs = {arc for _, arc in resolve_selection(manifest, REPO_ROOT)}
    assert ".claude/settings.json" not in arcs, \
        "settings.json must not be bundled (no auto hook registration)"
