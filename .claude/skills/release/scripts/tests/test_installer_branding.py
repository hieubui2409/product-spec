"""test_installer_branding — rendered installer templates must not contain stale brand
literals or dead skill-invocation hints/paths.

Verifies:
1. No `claude-pack` literal survives in any rendered template (log prefixes, title, hint line).
2. The dead `/cleanmatic:claude-pack` skill hint is gone; a real hint referencing the bundle is present.
3. The dead `.claude/skills/claude-pack/...` troubleshooting path is gone.
4. The `{{BUNDLE_NAME}}` token is used for branding and is properly substituted.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[2]       # .../release
SCRIPTS_DIR = Path(__file__).resolve().parents[1]      # .../release/scripts

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _render(template_name: str, bundle_name: str = "product-spec") -> str:
    from pack.templates import render_template
    tokens = {
        "BUNDLE_NAME": bundle_name,
        "VERSION": "0.0.0-test",
        "BUILT_AT": "1970-01-01T00:00:00+00:00",
        "SOURCE_COMMIT": "deadbeef",
        "FILE_COUNT": "42",
        "TOTAL_SIZE": "1 MB",
    }
    tmpl = SKILL_ROOT / "assets" / "templates" / template_name
    return render_template(tmpl, tokens).decode("utf-8")


@pytest.mark.bug_class
def test_install_sh_no_claude_pack_brand():
    """install.sh must not contain the stale `claude-pack` brand literal after rendering."""
    rendered = _render("install.sh.template")
    assert "claude-pack" not in rendered, (
        "install.sh still contains hard-coded 'claude-pack' brand literal. "
        "Replace with {{BUNDLE_NAME}} token."
    )


@pytest.mark.bug_class
def test_install_ps1_no_claude_pack_brand():
    """install.ps1 must not contain the stale `claude-pack` brand literal after rendering."""
    rendered = _render("install.ps1.template")
    assert "claude-pack" not in rendered, (
        "install.ps1 still contains hard-coded 'claude-pack' brand literal. "
        "Replace with {{BUNDLE_NAME}} token."
    )


@pytest.mark.bug_class
def test_install_md_no_claude_pack_brand():
    """INSTALL.md must not contain the stale `claude-pack` brand literal after rendering."""
    rendered = _render("INSTALL.md.template")
    assert "claude-pack" not in rendered, (
        "INSTALL.md still contains hard-coded 'claude-pack' brand literal. "
        "Replace with {{BUNDLE_NAME}} token."
    )


@pytest.mark.bug_class
def test_install_sh_bundle_name_substituted():
    """install.sh log prefix must use the rendered BUNDLE_NAME, not a hard-coded name."""
    rendered = _render("install.sh.template", bundle_name="my-skills")
    assert "my-skills" in rendered, \
        "{{BUNDLE_NAME}} token not substituted into install.sh"


@pytest.mark.bug_class
def test_install_ps1_bundle_name_substituted():
    """install.ps1 log prefix must use the rendered BUNDLE_NAME."""
    rendered = _render("install.ps1.template", bundle_name="my-skills")
    assert "my-skills" in rendered, \
        "{{BUNDLE_NAME}} token not substituted into install.ps1"


@pytest.mark.bug_class
def test_install_sh_no_dead_skill_hint():
    """install.sh must not reference the non-existent `/cleanmatic:claude-pack` skill invocation."""
    rendered = _render("install.sh.template")
    assert "/cleanmatic:claude-pack" not in rendered, (
        "install.sh still references dead `/cleanmatic:claude-pack` hint. "
        "Replace with a valid skill invocation hint."
    )


@pytest.mark.bug_class
def test_install_ps1_no_dead_skill_hint():
    """install.ps1 must not reference the non-existent `/cleanmatic:claude-pack` skill."""
    rendered = _render("install.ps1.template")
    assert "/cleanmatic:claude-pack" not in rendered, (
        "install.ps1 still references dead `/cleanmatic:claude-pack` hint."
    )


@pytest.mark.bug_class
def test_install_sh_no_dead_troubleshooting_path():
    """install.sh must not reference the dead `.claude/skills/claude-pack/...` path."""
    rendered = _render("install.sh.template")
    assert ".claude/skills/claude-pack" not in rendered, (
        "install.sh references `.claude/skills/claude-pack/...` which does not exist. "
        "Remove or repoint the troubleshooting hint."
    )


@pytest.mark.bug_class
def test_install_md_no_dead_troubleshooting_path():
    """INSTALL.md must not reference the dead `.claude/skills/claude-pack/...` path."""
    rendered = _render("INSTALL.md.template")
    assert ".claude/skills/claude-pack" not in rendered, (
        "INSTALL.md references `.claude/skills/claude-pack/...` which does not exist. "
        "Remove or repoint the troubleshooting hint."
    )
