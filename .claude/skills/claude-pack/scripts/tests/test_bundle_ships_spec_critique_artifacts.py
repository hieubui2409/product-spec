"""test_bundle_ships_spec_critique_artifacts — the live bundle ships the
spec-critique skill, its 5 lens/consolidate agents, and the drift-nudge hook.

The 5 `spec-critique-*` agents and `spec_critique_nudge.py` live at the repo's
top-level `.claude/agents/` and `.claude/hooks/` (NOT inside the skill subtree),
so the slug-rglob skill walk never picks them up — they reach the recipient ONLY
via explicit `agents:`/`hooks:` manifest entries. The skill dir itself ships via
the `skills: [spec-critique]` slug walk. These tests guard that contract against
the REAL manifest so a future hand-edit that drops an entry fails loudly.

Like the memory hook, the nudge hook SHIPS as a capability but is NEVER
auto-registered: `include_settings` stays false (asserted in the memory ships-test).
"""

from __future__ import annotations

from pathlib import Path

import manifest_loader  # type: ignore[import-not-found]
from pack.selection import resolve_selection

REPO_ROOT = Path(__file__).resolve().parents[5]
MANIFEST_PATH = REPO_ROOT / ".claude" / "pack.manifest.yaml"

AGENT_FILES = [
    "spec-critique-product.md",
    "spec-critique-tech.md",
    "spec-critique-market.md",
    "spec-critique-craft.md",
    "spec-critique-consolidate.md",
    "spec-critique-humanize.md",
]
HOOK_FILE = "spec_critique_nudge.py"
SKILL_SLUG = "spec-critique"

AGENT_ARCS = [f".claude/agents/{a}" for a in AGENT_FILES]
HOOK_ARC = f".claude/hooks/{HOOK_FILE}"
SKILL_PROBE_ARC = ".claude/skills/spec-critique/SKILL.md"


def _load_real_manifest() -> dict:
    return manifest_loader.load(MANIFEST_PATH)


def test_manifest_lists_spec_critique_skill_agents_hook():
    manifest = _load_real_manifest()
    assert SKILL_SLUG in manifest.get("skills", []), \
        "skills: must list spec-critique"
    for a in AGENT_FILES:
        assert a in manifest.get("agents", []), f"agents: must list {a}"
    assert HOOK_FILE in manifest.get("hooks", []), f"hooks: must list {HOOK_FILE}"


def test_real_manifest_validates_clean():
    manifest = _load_real_manifest()
    errors = manifest_loader.validate(manifest, REPO_ROOT)
    offending = [e for e in errors
                 if any(code in e for code in
                        ("MANIFEST_E070", "MANIFEST_E071", "MANIFEST_E073", "MANIFEST_E074"))]
    assert not offending, f"skill/agent/hook resolution errors: {offending}"


def test_selection_bundles_spec_critique_artifacts():
    manifest = _load_real_manifest()
    arcs = {arc for _, arc in resolve_selection(manifest, REPO_ROOT)}
    assert SKILL_PROBE_ARC in arcs, f"{SKILL_PROBE_ARC} missing (skill dir not bundled)"
    for arc in AGENT_ARCS:
        assert arc in arcs, f"{arc} missing from bundle file set"
    assert HOOK_ARC in arcs, f"{HOOK_ARC} missing from bundle file set"


def test_critique_scan_script_bundled():
    """The one new analysis script must ship inside the skill subtree."""
    manifest = _load_real_manifest()
    arcs = {arc for _, arc in resolve_selection(manifest, REPO_ROOT)}
    assert ".claude/skills/spec-critique/scripts/critique_scan.py" in arcs
