"""test_installer_gitignore_telemetry — install.sh/install.ps1 must append
`.claude/telemetry/` to the recipient's .gitignore (idempotent).

Verifies:
1. Rendered install.sh contains an idempotent gitignore-append guarded by
   `grep -q '.claude/telemetry/'` (no duplicate on second run).
2. Rendered install.ps1 contains an equivalent idempotent append guard.
3. INSTALL.md documents the gitignore behaviour.
4. Shell snippet simulation: running the gitignore-append lines twice against
   a temp .gitignore produces exactly one entry (idempotent).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[2]   # .../release
SCRIPTS_DIR = Path(__file__).resolve().parents[1]  # .../release/scripts

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _render(template_name: str) -> str:
    from pack.templates import render_template
    tokens = {
        "BUNDLE_NAME": "product-spec",
        "VERSION": "0.0.0-test",
        "BUILT_AT": "1970-01-01T00:00:00+00:00",
        "SOURCE_COMMIT": "deadbeef",
        "FILE_COUNT": "42",
        "TOTAL_SIZE": "1 MB",
    }
    tmpl = SKILL_ROOT / "assets" / "templates" / template_name
    return render_template(tmpl, tokens).decode("utf-8")


def _extract_block(rendered: str, start_marker: str, end_marker: str) -> str:
    """Slice the rendered script between two literal markers (start inclusive,
    end exclusive). Lets a test run the REAL shipped block instead of a
    hand-written copy that can silently drift from the template."""
    start = rendered.index(start_marker)
    end = rendered.index(end_marker, start)
    return rendered[start:end]


@pytest.mark.bug_class
def test_install_sh_has_gitignore_telemetry_append():
    """install.sh must append `.claude/telemetry/` to .gitignore when absent."""
    rendered = _render("install.sh.template")
    assert ".claude/telemetry/" in rendered, \
        "install.sh does not append .claude/telemetry/ to .gitignore"


@pytest.mark.bug_class
def test_install_sh_gitignore_append_is_idempotent():
    """install.sh gitignore logic must be guarded by `grep -q` to avoid duplicates."""
    rendered = _render("install.sh.template")
    # The guard pattern: grep -q checks before appending.
    assert "grep -q" in rendered, \
        "install.sh gitignore append is not guarded by grep -q (not idempotent)"
    # Confirm the guard specifically targets the telemetry path.
    assert ".claude/telemetry/" in rendered, \
        "install.sh grep -q guard does not mention .claude/telemetry/"


@pytest.mark.bug_class
def test_install_ps1_has_gitignore_telemetry_append():
    """install.ps1 must append `.claude/telemetry/` to .gitignore when absent."""
    rendered = _render("install.ps1.template")
    assert ".claude/telemetry/" in rendered, \
        "install.ps1 does not append .claude/telemetry/ to .gitignore"


@pytest.mark.bug_class
def test_install_ps1_gitignore_append_is_idempotent():
    """install.ps1 gitignore logic must check before appending to avoid duplicates."""
    rendered = _render("install.ps1.template")
    # PowerShell idiom: -notcontains or -notmatch guard before Add-Content.
    has_guard = (
        "-notcontains" in rendered
        or "-notmatch" in rendered
        or "Select-String" in rendered
        or "Contains" in rendered
    )
    assert has_guard, \
        "install.ps1 gitignore append has no duplication guard (not idempotent)"


@pytest.mark.bug_class
def test_install_md_documents_gitignore():
    """INSTALL.md must document that .claude/telemetry/ is added to .gitignore."""
    rendered = _render("INSTALL.md.template")
    assert ".claude/telemetry/" in rendered, \
        "INSTALL.md does not mention .claude/telemetry/ gitignore entry"


@pytest.mark.bug_class
@pytest.mark.skipif(shutil.which("bash") is None, reason="bash required")
@pytest.mark.parametrize("initial", [
    "node_modules/\n",   # trailing newline present (the easy case)
    "node_modules/",     # NO trailing newline — a bare append would corrupt this
    "",                  # empty file
    None,                # file absent
])
def test_install_sh_gitignore_real_block_runtime(initial):
    """Run the REAL gitignore block extracted from the rendered install.sh twice.

    Two invariants, against every starting state:
    1. Idempotent — exactly one `.claude/telemetry/` entry after two runs.
    2. No corruption — when the existing file's last line lacks a trailing
       newline (`node_modules/`), the entry must land on its OWN line, never
       joined as `node_modules/.claude/telemetry/` (which would both mangle the
       prior entry and leave telemetry un-ignored).

    Extracting the shipped block (rather than re-typing it) means this test fails
    if the template ever regresses to a bare `echo ... >>` append.
    """
    rendered = _render("install.sh.template")
    block = _extract_block(rendered, "# --- Gitignore:", "# --- Summary ---")

    with tempfile.TemporaryDirectory() as tmp_dir:
        gitignore = Path(tmp_dir) / ".gitignore"
        if initial is not None:
            gitignore.write_text(initial, encoding="utf-8")

        # Stub the installer's `log` helper and supply TARGET_DIR, then run the
        # real block twice to prove idempotency.
        harness = (
            "set -e\n"
            "log() { :; }\n"
            f'TARGET_DIR="{tmp_dir}"\n'
            "run_block() {\n"
            f"{block}\n"
            "}\n"
            "run_block\n"
            "run_block\n"
        )
        r = subprocess.run(["bash", "-c", harness], capture_output=True, text=True)
        assert r.returncode == 0, f"gitignore block failed: {r.stderr}"

        content = gitignore.read_text(encoding="utf-8")
        assert content.count(".claude/telemetry/") == 1, (
            f"expected exactly one telemetry entry after two runs; got:\n{content!r}"
        )
        assert ".claude/telemetry/" in content.splitlines(), (
            f"telemetry entry is not on its own line (append corruption): {content!r}"
        )
        assert "node_modules/.claude/telemetry/" not in content, (
            f"append joined the entry onto a no-newline line: {content!r}"
        )


@pytest.mark.bug_class
@pytest.mark.skipif(shutil.which("bash") is None, reason="bash required")
def test_install_sh_skill_verdict_helpers_roundtrip():
    """The bash-3.2 parallel-array verdict helpers (_set_skill_verdict /
    _get_skill_verdict, which replace the bash-4+ `declare -A`) must round-trip:
    a stored verdict is returned for its slug, and an absent slug yields the
    empty string. This exercises the helpers at runtime, not just `bash -n`.
    """
    rendered = _render("install.sh.template")
    block = _extract_block(rendered, "SKILL_VERDICT_SLUGS=()", "compute_skill_verdicts()")

    harness = (
        f"{block}\n"
        '_set_skill_verdict "product-spec" "ADD"\n'
        '_set_skill_verdict "telemetry" "SKIP"\n'
        'echo "a=$(_get_skill_verdict product-spec)"\n'
        'echo "b=$(_get_skill_verdict telemetry)"\n'
        'echo "c=$(_get_skill_verdict missing)"\n'
    )
    r = subprocess.run(["bash", "-c", harness], capture_output=True, text=True)
    assert r.returncode == 0, f"verdict helpers failed: {r.stderr}"
    out = r.stdout
    assert "a=ADD" in out, out
    assert "b=SKIP" in out, out
    # absent slug → empty string (the `c=` line has nothing after the `=`)
    assert "c=\n" in out or out.rstrip().endswith("c="), out
    assert "c=ADD" not in out and "c=SKIP" not in out, out
