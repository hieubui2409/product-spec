"""Plain helpers for the product-spec-critique script tests.

A UNIQUELY-named module (not `conftest`) so a combined pytest run across both the
product-spec and product-spec-critique test dirs cannot collide on the `conftest` module
name. product-spec-critique reuses product-spec's `valid-spec` fixture as the input tree.
"""

import io
import json
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent  # product-spec-critique/scripts
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

PSP_SCRIPTS = SCRIPTS_DIR.parent.parent / "product-spec" / "scripts"
VALID = PSP_SCRIPTS / "tests" / "fixtures" / "valid-spec"


def make_proj(tmp_path: Path) -> Path:
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    return proj


def append_to(proj: Path, rel: str, line: str) -> None:
    p = proj / "docs" / "product" / rel
    p.write_text(p.read_text(encoding="utf-8") + line, encoding="utf-8")


def run_scan(proj: Path, *args: str):
    """Invoke critique_scan.main() in-process; return (exit_code, parsed_json)."""
    import critique_scan

    buf = io.StringIO()
    with redirect_stdout(buf):
        code = critique_scan.main(["--root", str(proj), *args])
    return code, json.loads(buf.getvalue())
