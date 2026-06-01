"""Shared test scaffolding for the product-spec script suite.

pytest auto-loads this file and the tests dir is importable, so these plain
helpers can be pulled in via `from conftest import ...`. They are deliberately
plain functions/constants (NOT fixtures) so call semantics stay identical to the
per-file copies they replace — a fixture would change how call sites read.

Single home for the valid-spec fixtures path + the three byte-identical helpers
that were copy-pasted across the memory-layer test files:
  - `VALID`            — the valid-spec fixtures dir every `_proj` copies from.
  - `make_proj`        — writable copy of the fixture, optional git-init baseline.
  - `validate_baseline`— snapshot the graph + write the last_validated marker.
  - `append_to`        — append a line to a docs/product file.
"""

import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
# Mirror each test file's header so the script modules under scripts/ import the
# same way whether a test pulls them in directly or via these shared helpers.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)


def make_proj(tmp_path: Path, git: bool = True) -> Path:
    """A writable copy of the valid-spec fixture, optionally a committed git repo
    so the fence scan has a clean working-tree baseline (only NEW touches show)."""
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    if git:
        _git(proj, "init", "-q")
        _git(proj, "config", "user.email", "t@t.t")
        _git(proj, "config", "user.name", "t")
        _git(proj, "add", "-A")
        _git(proj, "commit", "-q", "-m", "base")
    return proj


def validate_baseline(proj: Path) -> Path:
    """Simulate a `--validate`: snapshot the current graph + write the
    `last_validated.json` marker pointing at it (what the validate hub does)."""
    from spec_graph import build_graph, write_snapshot
    import judgment_cache as jc

    graph = build_graph(proj)
    snap = write_snapshot(graph, proj)
    jc.write_last_validated(proj, snap)
    return snap


def append_to(proj: Path, rel: str, line: str):
    p = proj / "docs" / "product" / rel
    p.write_text(p.read_text(encoding="utf-8") + line, encoding="utf-8")
