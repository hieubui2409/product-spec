"""test_installer_semver — the recipient installer's SemVer precedence (B4).

`semver_compare` (bash, install.sh.template) and `Compare-Semver` (PowerShell, install.ps1.template)
decide STALE / NEWER / OK-SAME on the recipient's machine — a wrong verdict silently keeps a stale
skill or clobbers a newer one (split-brain install). They were eyeball-only; this pins the precedence
rules (incl. the leading-zero octal trap and ASCII pre-release collation) with an edge-case matrix.

The bash function is extracted from the template + run via `bash`; the PowerShell parity test runs only
where `pwsh` exists (skipped on POSIX dev boxes, exercised on the Windows CI leg).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

TEMPLATES = Path(__file__).resolve().parents[2] / "assets" / "templates"
SH_TEMPLATE = TEMPLATES / "install.sh.template"
PS1_TEMPLATE = TEMPLATES / "install.ps1.template"


def _extract_block(text: str, start_pat: str, end_line: str) -> str:
    """Return the source from the line matching `start_pat` through the first line equal to `end_line`."""
    lines = text.splitlines()
    out, capturing = [], False
    for ln in lines:
        if not capturing and re.search(start_pat, ln):
            capturing = True
        if capturing:
            out.append(ln)
            if ln.rstrip() == end_line and len(out) > 1:
                break
    if not out:
        raise AssertionError(f"could not extract block {start_pat!r} from template")
    return "\n".join(out)


# (a, b, expected) — expected is the sign of A vs B: -1 (A<B), 0 (A==B), 1 (A>B).
# The risky cases the function explicitly guards are called out inline.
CASES = [
    ("1.0.0", "1.0.0", 0),
    ("1.2.3", "1.2.4", -1),
    ("1.2.4", "1.2.3", 1),
    ("2.0.0", "1.9.9", 1),
    ("1.10.0", "1.9.0", 1),          # numeric, not lexical (10 > 9)
    ("1.0.08", "1.0.09", -1),        # leading-zero OCTAL TRAP (08/09 are invalid octal)
    ("1.0.10", "1.0.08", 1),         # leading-zero on one side
    ("1.0.0-rc1", "1.0.0", -1),      # pre-release < release
    ("1.0.0", "1.0.0-rc1", 1),
    ("1.0.0-alpha", "1.0.0-alpha.1", -1),   # shorter pre-release is lower
    ("1.0.0-alpha.1", "1.0.0-alpha", 1),
    ("1.0.0-alpha.2", "1.0.0-alpha.10", -1),  # numeric identifier ordering (2 < 10), not lexical
    ("1.0.0-1", "1.0.0-alpha", -1),  # numeric identifier < alphanumeric
    ("1.0.0-alpha", "1.0.0-1", 1),
    ("1.0.0-alpha", "1.0.0-beta", -1),        # alphanumeric ASCII compare
    ("1.0.0-beta", "1.0.0-rc.1", -1),
    ("1.0.0+build1", "1.0.0+build2", 0),      # build metadata IGNORED for precedence
    ("1.0.0-rc1+a", "1.0.0-rc1+b", 0),
    ("1.0.0-RC", "1.0.0-rc", -1),    # ASCII collation (LC_ALL=C): 'R'(82) < 'r'(114)
]


@pytest.fixture(scope="module")
def bash_semver(tmp_path_factory):
    fn = _extract_block(SH_TEMPLATE.read_text(encoding="utf-8"), r"^semver_compare\(\)\s*\{", "}")
    script = tmp_path_factory.mktemp("semver") / "fn.sh"
    script.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + fn + '\nsemver_compare "$1" "$2"\n',
                      encoding="utf-8")

    def run(a: str, b: str) -> int:
        r = subprocess.run(["bash", str(script), a, b], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        return int(r.stdout.strip())

    return run


@pytest.mark.bug_class  # cross-cutting invariant: recipient version verdict must be correct
@pytest.mark.parametrize("a,b,expected", CASES)
def test_bash_semver_compare(bash_semver, a, b, expected):
    assert bash_semver(a, b) == expected, f"semver_compare {a} {b}"


def test_bash_semver_antisymmetry(bash_semver):
    # compare(a,b) == -compare(b,a) for every non-equal pair.
    for a, b, expected in CASES:
        assert bash_semver(a, b) == -bash_semver(b, a), f"asymmetry at {a} vs {b}"


# --------------------------------------------------------------------------- PowerShell parity

_PWSH = shutil.which("pwsh")


@pytest.mark.skipif(_PWSH is None, reason="pwsh not available (Windows CI exercises this leg)")
@pytest.mark.parametrize("a,b,expected", CASES)
def test_ps1_compare_semver(tmp_path, a, b, expected):
    fn = _extract_block(PS1_TEMPLATE.read_text(encoding="utf-8"), r"^function Compare-Semver", "}")
    script = tmp_path / "fn.ps1"
    script.write_text(fn + f'\nWrite-Output (Compare-Semver "{a}" "{b}")\n', encoding="utf-8")
    r = subprocess.run([_PWSH, "-NoProfile", "-File", str(script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert int(r.stdout.strip()) == expected, f"Compare-Semver {a} {b}"
