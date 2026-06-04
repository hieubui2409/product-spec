"""TIME dimension: the `overdue` advisory.

`overdue` (target_date < today) is NON-deterministic by nature — it consumes the
wall clock — so it lives OUTSIDE the `--validate` structural gate to keep that
gate byte-reproducible. It ships as a standalone `time_advisory.py` that
takes a pinnable `--today <ISO>` and emits an advisory JSON.

This module is the RED spec for that script:
  - `time_advisory.py --root <dir> --today <ISO>` exits 0 and prints JSON.
  - an artifact whose `target_date` is BEFORE `--today` is flagged `overdue`.
  - an artifact whose `target_date` is AFTER `--today` is NOT flagged.
  - the script is advisory-only: it must NOT exit non-zero on an overdue item
    (it is not a gate).

Subprocess-style, mirroring strict_gate / generate_templates tests in
test_scripts.py. No LLM, no judgment — pure date comparison.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))


_PRODUCT_MD = """---
id: PRODUCT
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [s]
---
"""

_BRD_MD = """---
id: BRD
type: brd
status: draft
lang: en
goals:
  - id: BRD-G1
    title: g
    status: draft
    metrics: [m]
---
"""


def _scaffold(tmp_path: Path) -> Path:
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(_PRODUCT_MD)
    (prod / "brd.md").write_text(_BRD_MD)
    return proj


def _write_prd(proj: Path, name: str, prd_id: str, target_date: str) -> None:
    (proj / "docs" / "product" / "prds" / name).write_text(f"""---
id: {prd_id}
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
target_date: {target_date}
---
""")


def _run_advisory(proj: Path, today: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "time_advisory.py"),
         "--root", str(proj), "--today", today],
        capture_output=True, text=True,
    )


def test_time_advisory_overdue(tmp_path):
    """A PRD with target_date 2026-09-30, evaluated at --today 2026-12-01, is
    overdue. The advisory JSON must flag it; the script exits 0 (advisory, not a
    gate)."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, "late.md", "PRD-LATE", "2026-09-30")
    r = _run_advisory(proj, "2026-12-01")
    assert r.returncode == 0, f"time_advisory must exit 0 (advisory, never a gate): {r.stderr}"
    payload = json.loads(r.stdout)
    findings = payload.get("findings", [])
    overdue = [f for f in findings if f["check"] == "overdue"]
    assert overdue, f"expected an overdue finding for PRD-LATE; got: {findings}"
    assert overdue[0]["artifact_id"] == "PRD-LATE"
    assert overdue[0]["severity"] == "advisory", f"overdue must be advisory severity: {overdue[0]}"


def test_time_advisory_not_overdue_when_future(tmp_path):
    """A PRD whose target_date is AFTER --today is not overdue."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, "future.md", "PRD-FUTURE", "2027-01-15")
    r = _run_advisory(proj, "2026-12-01")
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    overdue = [f for f in payload.get("findings", []) if f["check"] == "overdue"]
    assert overdue == [], f"a future target_date must NOT be overdue; got: {overdue}"


def test_time_advisory_no_target_date_silent(tmp_path):
    """A PRD with NO target_date is never overdue (the field is optional)."""
    proj = _scaffold(tmp_path)
    (proj / "docs" / "product" / "prds" / "x.md").write_text("""---
id: PRD-X
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    r = _run_advisory(proj, "2026-12-01")
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    overdue = [f for f in payload.get("findings", []) if f["check"] == "overdue"]
    assert overdue == [], f"no target_date -> no overdue; got: {overdue}"
