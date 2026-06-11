"""test_installer_bash32_compat — install.sh must be compatible with bash 3.2 (macOS default).

`declare -A` (associative arrays) is bash-4+. This test verifies the rendered install.sh
uses parallel arrays (bash-3.2-safe) instead of declare -A, and that the script passes
bash -n syntax-check under a bash:3.2 Docker image (when Docker is available).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[2]       # .../release
SCRIPTS_DIR = Path(__file__).resolve().parents[1]      # .../release/scripts
REPO_ROOT = Path(__file__).resolve().parents[5]        # repo root


def _render_install_sh(tokens: dict | None = None) -> str:
    """Render install.sh.template with the given tokens (defaults filled)."""
    import sys
    sys.path.insert(0, str(SCRIPTS_DIR))
    from pack.templates import render_template

    default_tokens = {
        "BUNDLE_NAME": "product-spec",
        "VERSION": "0.0.0-test",
        "BUILT_AT": "1970-01-01T00:00:00+00:00",
        "SOURCE_COMMIT": "deadbeef",
        "FILE_COUNT": "42",
        "TOTAL_SIZE": "1 MB",
    }
    if tokens:
        default_tokens.update(tokens)
    tmpl = SKILL_ROOT / "assets" / "templates" / "install.sh.template"
    return render_template(tmpl, default_tokens).decode("utf-8")


@pytest.mark.bug_class
def test_rendered_install_sh_has_no_declare_a():
    """install.sh must not USE `declare -A` (bash-4+); parallel arrays are required for bash-3.2 (macOS).

    Only non-comment executable lines are checked: a comment that mentions the construct
    as a rationale note is acceptable; an actual `declare -A VARNAME` statement is not.
    """
    rendered = _render_install_sh()
    # Filter to non-comment, non-blank lines to allow explanatory comments.
    code_lines = [
        line for line in rendered.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    offending = [ln for ln in code_lines if "declare -A" in ln]
    assert not offending, (
        "install.sh.template has a non-comment `declare -A` (bash-4+ only). "
        "Replace with parallel arrays (SKILL_VERDICT_SLUGS / SKILL_VERDICT_VALUES).\n"
        + "\n".join(offending)
    )


@pytest.mark.bug_class
def test_rendered_install_sh_has_parallel_verdict_arrays():
    """Parallel arrays SKILL_VERDICT_SLUGS and SKILL_VERDICT_VALUES must be present."""
    rendered = _render_install_sh()
    assert "SKILL_VERDICT_SLUGS" in rendered, \
        "SKILL_VERDICT_SLUGS parallel array not found in install.sh"
    assert "SKILL_VERDICT_VALUES" in rendered, \
        "SKILL_VERDICT_VALUES parallel array not found in install.sh"


@pytest.mark.bug_class
def test_rendered_install_sh_bash_syntax_native():
    """install.sh must parse cleanly under the system bash (sanity check for -n)."""
    bash = shutil.which("bash")
    if not bash:
        pytest.skip("bash not found on PATH")
    rendered = _render_install_sh()
    with tempfile.NamedTemporaryFile(suffix=".sh", mode="w", encoding="utf-8", delete=False) as f:
        f.write(rendered)
        tmp_path = f.name
    try:
        r = subprocess.run([bash, "-n", tmp_path], capture_output=True, text=True)
        assert r.returncode == 0, f"bash -n failed:\n{r.stderr}"
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@pytest.mark.bug_class
def test_rendered_install_sh_bash32_syntax():
    """install.sh must pass `bash -n` under bash 3.2 (macOS default shell).

    Runs `docker run --rm bash:3.2 bash -n /tmp/install.sh`. Skipped gracefully
    when docker is not available or the image cannot be pulled.
    """
    docker = shutil.which("docker")
    if not docker:
        pytest.skip("docker not available — skipping bash:3.2 syntax check")

    # Quick connectivity check: can we reach the image?
    probe = subprocess.run(
        [docker, "image", "inspect", "bash:3.2"],
        capture_output=True, text=True,
    )
    if probe.returncode != 0:
        # Try to pull (may fail in offline CI)
        pull = subprocess.run(
            [docker, "pull", "bash:3.2"],
            capture_output=True, text=True, timeout=120,
        )
        if pull.returncode != 0:
            pytest.skip("bash:3.2 Docker image unavailable — skipping e2e bash-3.2 syntax check")

    rendered = _render_install_sh()
    with tempfile.TemporaryDirectory() as tmp_dir:
        script_path = Path(tmp_dir) / "install.sh"
        script_path.write_text(rendered, encoding="utf-8")

        r = subprocess.run(
            [docker, "run", "--rm",
             "-v", f"{tmp_dir}:/x",
             "bash:3.2",
             "bash", "-n", "/x/install.sh"],
            capture_output=True, text=True, timeout=60,
        )
        assert r.returncode == 0, (
            f"bash:3.2 -n rejected install.sh (syntax error):\n{r.stderr}"
        )
