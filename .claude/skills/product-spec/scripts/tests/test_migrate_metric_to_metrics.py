"""metric -> metrics rename migration (TDD RED).

A legacy spec whose BRD goal carries the OLD singular `metric:` key (a pre-multidim
shape) cannot reach `metrics: [...]` without a migration — and because such a BRD is
typically `approved`, the rename must NOT be auto-written. This script is the GATE-safe
companion to migrate_multidim_fields.py:

  - dry-run (DEFAULT, no --apply): report which goals carry `metric:`; write ZERO bytes,
    create NO `.bak`. The LLM drives the per-item AskUserQuestion off this report.
  - --apply: write ONLY when BOTH --confirmed-by AND --date are supplied (the explicit
    PO re-approval of an approved artifact). Missing either flag → refused, no write.
    On apply: rename `metric:`(scalar|list) → `metrics:`(list) preserving the value, and
    stamp `schema_version: 2` so the artifact declares it is on the post-migration schema.
  - Analytical script: ALWAYS exits 0; --apply is the only mutating flag.

Scope guard: the rename touches BRD goal entries ONLY — never another record's `metric`
field elsewhere. Synthetic fixtures only (no real PO data).
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from frontmatter_parser import parse_file  # noqa: E402

MIGRATE = SCRIPTS_DIR / "migrate_metric_to_metrics.py"

_PRODUCT_MD = """---
id: PRODUCT
type: product
status: draft
lang: en
name: "Acme"
core_value: "do one thing well"
personas: [user]
---
"""

# An APPROVED legacy BRD: goal carries the OLD singular `metric:` (list value) and NO
# `metrics:` plural key. This is exactly the recipient-style v1.x shape the migration lifts.
_LEGACY_BRD_MD = """---
id: BRD
type: brd
status: approved
lang: en
owner: Jane
version: 1.0.0
created: 2026-06-01
updated: 2026-06-01
goals:
  - id: BRD-G1
    title: "Legacy goal on the old metric key"
    metric: [legacy-kpi]
    status: approved
---

# BRD
"""

# A BRD already on the plural `metrics:` schema — the migration must be a no-op here
# (over-fix guard: a fresh/modern spec is never touched).
_MODERN_BRD_MD = """---
id: BRD
type: brd
status: approved
lang: en
owner: Jane
version: 1.0.0
schema_version: 2
created: 2026-06-01
updated: 2026-06-01
goals:
  - id: BRD-G1
    title: "Modern goal already on metrics"
    metrics: [north-star]
    status: approved
---

# BRD
"""

# A legacy BRD whose `metric:` carries a trailing inline comment — exactly the kind of
# hand-authored shape this migrator runs on. The rename must keep the line valid YAML and
# preserve the comment (a naive flow-list wrap would swallow the `]` into the comment).
_COMMENTED_BRD_MD = """---
id: BRD
type: brd
status: approved
lang: en
owner: Jane
version: 1.0.0
created: 2026-06-01
updated: 2026-06-01
goals:
  - id: BRD-G1
    title: "Legacy goal with a commented scalar metric"
    metric: north-star  # the one true KPI
    status: approved
---

# BRD
"""

# A half-migrated BRD: goal 1 is legacy (`metric:` only), goal 2 already carries a plural
# `metrics:` alongside a stale `metric:`. The migrator must rename ONLY goal 1 and must NOT
# emit a second `metrics:` key on goal 2 (which would be invalid YAML).
_MIXED_BRD_MD = """---
id: BRD
type: brd
status: approved
lang: en
owner: Jane
version: 1.0.0
created: 2026-06-01
updated: 2026-06-01
goals:
  - id: BRD-G1
    title: "Legacy goal on the old key"
    metric: [legacy-only]
    status: approved
  - id: BRD-G2
    title: "Half-migrated goal already on metrics"
    metric: [stale-singular]
    metrics: [already-plural]
    status: approved
---

# BRD
"""


def _proj(tmp_path: Path, brd_md: str) -> Path:
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir()
    (prod / "stories").mkdir()
    (prod / "PRODUCT.md").write_text(_PRODUCT_MD, encoding="utf-8")
    (prod / "brd.md").write_text(brd_md, encoding="utf-8")
    return proj


def _run(proj: Path, *extra: str) -> dict:
    """Run the migrator and parse JSON stdout. Always exits 0 (CLI contract)."""
    r = subprocess.run(
        [sys.executable, str(MIGRATE), "--root", str(proj), *extra],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"migrate exited {r.returncode}\nSTDERR:\n{r.stderr}"
    return json.loads(r.stdout)


def test_migrate_dry_run_writes_zero_bytes(tmp_path):
    proj = _proj(tmp_path, _LEGACY_BRD_MD)
    brd = proj / "docs" / "product" / "brd.md"
    before = brd.read_bytes()

    report = _run(proj)  # dry-run default

    assert brd.read_bytes() == before, "dry-run must not change a single byte of the approved BRD"
    assert not (brd.parent / "brd.md.bak").exists(), "dry-run must not create a .bak"
    assert report.get("applied") is False
    blob = json.dumps(report)
    assert "BRD-G1" in blob or "brd.md" in blob, \
        "dry-run report must name the goal/file carrying the legacy metric key"


def test_migrate_apply_requires_confirmed_by_and_date(tmp_path):
    proj = _proj(tmp_path, _LEGACY_BRD_MD)
    brd = proj / "docs" / "product" / "brd.md"
    before = brd.read_bytes()

    # --apply alone (no confirmation) → refused, zero bytes written.
    r1 = _run(proj, "--apply")
    assert brd.read_bytes() == before, "apply without --confirmed-by/--date must not write the approved BRD"
    assert r1.get("applied") is False
    assert r1.get("error"), "refusal must carry an error reason"

    # --apply with only one of the two required flags → still refused.
    r2 = _run(proj, "--apply", "--confirmed-by", "Jane")
    assert brd.read_bytes() == before, "apply with a half-supplied confirmation must not write"
    assert r2.get("applied") is False

    # --apply with BOTH flags → rename + marker, value preserved, original backed up.
    r3 = _run(proj, "--apply", "--confirmed-by", "Jane", "--date", "2026-06-11")
    fm = parse_file(brd)["frontmatter"]
    goal = fm["goals"][0]
    assert "metric" not in goal, "the singular `metric:` key must be renamed away"
    assert goal.get("metrics") == ["legacy-kpi"], "the metric value must be preserved under `metrics:`"
    assert fm.get("schema_version") == 2, "a migrated BRD must declare schema_version: 2"
    assert (brd.parent / "brd.md.bak").exists(), "the pre-migration original must be backed up"
    assert r3.get("applied") is True


def test_migrate_is_noop_on_modern_metrics_spec(tmp_path):
    """Over-fix guard: a BRD already on the plural `metrics:` schema is never touched,
    even with a full confirmation supplied."""
    proj = _proj(tmp_path, _MODERN_BRD_MD)
    brd = proj / "docs" / "product" / "brd.md"
    before = brd.read_bytes()

    report = _run(proj, "--apply", "--confirmed-by", "Jane", "--date", "2026-06-11")

    assert brd.read_bytes() == before, "a modern metrics-plural BRD must be left byte-for-byte"
    assert not (brd.parent / "brd.md.bak").exists(), "no .bak for an untouched modern spec"
    assert report.get("migrated") in ([], None), "nothing to migrate on a modern spec"
    assert report.get("noop") is True, "an --apply that changed nothing must flag noop"
    assert report.get("applied") is False, "a no-op apply did not write → applied stays False"


def test_migrate_preserves_inline_comment_on_scalar_metric(tmp_path):
    """A scalar `metric:` carrying a trailing `# comment` must rename to a valid `metrics:`
    list with the comment intact — the rewritten frontmatter must still parse."""
    proj = _proj(tmp_path, _COMMENTED_BRD_MD)
    brd = proj / "docs" / "product" / "brd.md"

    _run(proj, "--apply", "--confirmed-by", "Jane", "--date", "2026-06-11")

    parsed = parse_file(brd)
    assert parsed["ok"], "the migrated BRD must remain parseable (comment must not break the list)"
    goal = parsed["frontmatter"]["goals"][0]
    assert goal.get("metrics") == ["north-star"], "the scalar value must be preserved as a 1-item list"
    assert "metric" not in goal, "the singular key must be renamed away"
    assert "# the one true KPI" in brd.read_text(encoding="utf-8"), "the inline comment must survive"


def test_migrate_skips_goal_already_on_plural_metrics(tmp_path):
    """A half-migrated goal (a stale `metric:` next to a real `metrics:`) must be left alone:
    renaming it would emit a duplicate `metrics:` key. Only the truly-legacy goal migrates."""
    proj = _proj(tmp_path, _MIXED_BRD_MD)
    brd = proj / "docs" / "product" / "brd.md"

    report = _run(proj, "--apply", "--confirmed-by", "Jane", "--date", "2026-06-11")

    assert report.get("applied") is True
    raw = brd.read_text(encoding="utf-8")
    g2 = raw.split("- id: BRD-G2", 1)[1]
    assert g2.count("metrics:") == 1, "must not create a second metrics: key on the half-migrated goal"
    parsed = parse_file(brd)
    assert parsed["ok"], "the migrated BRD must remain parseable"
    goals = {g["id"]: g for g in parsed["frontmatter"]["goals"]}
    assert goals["BRD-G1"].get("metrics") == ["legacy-only"], "the legacy goal must migrate"
    assert goals["BRD-G2"].get("metrics") == ["already-plural"], "the plural goal's metrics must be untouched"
