"""Goal + frontmatter schema correctness (TDD RED).

Covers the structural gaps where the validator was silent on goal/frontmatter shape:

  - A goal that still carries the OLD singular `metric:` key HAS a metric (just misnamed),
    so it must WARN with a migrate hint — never block validate with an error. A goal with
    NO metric at all still ERRORs (the gate is not loosened).
  - A goal missing the required `status` is caught: WARN on a legacy BRD (no schema_version
    marker), ERROR once the BRD declares schema_version >= 2 (so a fresh/migrated spec is
    fully gated, but a not-yet-migrated legacy spec is not retro-blocked).
  - A goal's `moscow` survives into the graph node (was silently dropped).
  - A story carrying a PRD/BRD parent ref (its parent is the epic) and a malformed `version`
    are surfaced (LLM-hallucinated out-of-spec frontmatter is no longer silently accepted).

Synthetic fixtures only.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from check_consistency import check  # noqa: E402
from spec_graph import build_graph  # noqa: E402
import strict_gate  # noqa: E402

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


def _brd_proj(tmp_path: Path, brd_md: str) -> Path:
    """A minimal product tree carrying just PRODUCT + the supplied brd.md."""
    proj = tmp_path
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir()
    (prod / "stories").mkdir()
    (prod / "PRODUCT.md").write_text(_PRODUCT_MD, encoding="utf-8")
    (prod / "brd.md").write_text(brd_md, encoding="utf-8")
    return proj


def _rows(root: Path):
    return [
        (f["check"], f["artifact_id"], f["severity"], f.get("detail") or "")
        for f in check(build_graph(root))
    ]


# --------------------------------------------------------------------------- #
# Legacy singular `metric:` → WARN with migrate hint (not an error block).
# --------------------------------------------------------------------------- #

_LEGACY_METRIC_BRD = """---
id: BRD
type: brd
status: approved
lang: en
version: 1.0.0
goals:
  - id: BRD-G1
    title: "Goal still on the old metric key"
    metric: [legacy-kpi]
    status: approved
---

# BRD
"""


def test_singular_metric_key_warns_not_errors_on_legacy(tmp_path):
    proj = _brd_proj(tmp_path, _LEGACY_METRIC_BRD)
    rows = _rows(proj)

    metric_msgs = [r for r in rows if r[1] == "BRD-G1" and "metric" in r[3].lower()]
    assert metric_msgs, "the legacy `metric:` key must be surfaced for BRD-G1"
    assert all(sev == "warn" for _c, _a, sev, _d in metric_msgs), \
        "a goal that HAS a metric (under the old key) must WARN, not error-block validate"

    # It must NOT be reported as goal_without_metric (it is not metric-less; it is mis-keyed).
    assert not any(c == "goal_without_metric" and a == "BRD-G1" for c, a, _s, _d in rows)

    # strict_gate must not block on it (no error-severity finding for this goal).
    findings, _g = strict_gate.collect_findings(proj)
    assert not any(f.get("artifact_id") == "BRD-G1" and f.get("severity") == "error" for f in findings), \
        "a legacy metric-key goal must not push strict_gate to exit 2"


# --------------------------------------------------------------------------- #
# goal_without_status: WARN on legacy, ERROR on schema_version >= 2.
# --------------------------------------------------------------------------- #

_LEGACY_NO_STATUS_BRD = """---
id: BRD
type: brd
status: approved
lang: en
version: 1.0.0
goals:
  - id: BRD-G1
    title: "Legacy goal missing status"
    metrics: [north-star]
---

# BRD
"""

_V2_NO_STATUS_BRD = """---
id: BRD
type: brd
status: approved
lang: en
version: 1.0.0
schema_version: 2
goals:
  - id: BRD-G1
    title: "Modern goal missing status"
    metrics: [north-star]
---

# BRD
"""


def test_goal_without_status_warns_on_legacy_errors_on_schema_v2(tmp_path):
    legacy_rows = _rows(_brd_proj(tmp_path / "legacy", _LEGACY_NO_STATUS_BRD))
    legacy = [r for r in legacy_rows if r[0] == "goal_without_status" and r[1] == "BRD-G1"]
    assert legacy, "a goal missing status must be caught on a legacy BRD"
    assert legacy[0][2] == "warn", "a not-yet-migrated legacy spec warns (no retro-block)"

    v2_rows = _rows(_brd_proj(tmp_path / "v2", _V2_NO_STATUS_BRD))
    v2 = [r for r in v2_rows if r[0] == "goal_without_status" and r[1] == "BRD-G1"]
    assert v2, "a goal missing status must be caught on a schema_version:2 BRD"
    assert v2[0][2] == "error", "a schema_version:2 spec is fully gated → error"


# --------------------------------------------------------------------------- #
# moscow on a goal survives into the graph node.
# --------------------------------------------------------------------------- #

_MOSCOW_GOAL_BRD = """---
id: BRD
type: brd
status: approved
lang: en
version: 1.0.0
goals:
  - id: BRD-G1
    title: "Goal carrying a moscow priority"
    metrics: [north-star]
    status: approved
    moscow: must
---

# BRD
"""


def test_moscow_preserved_in_graph_node(tmp_path):
    g = build_graph(_brd_proj(tmp_path, _MOSCOW_GOAL_BRD))
    node = next(n for n in g["nodes"] if n["id"] == "BRD-G1")
    assert node.get("moscow") == "must", "a goal's moscow must survive into the graph node (was dropped)"


# --------------------------------------------------------------------------- #
# A schema_version:2 draft goal with NO metric at all still ERRORs (gate not loosened).
# --------------------------------------------------------------------------- #

_V2_NO_METRIC_BRD = """---
id: BRD
type: brd
status: draft
lang: en
version: 1.0.0
schema_version: 2
goals:
  - id: BRD-G1
    title: "Fresh goal with no metric at all"
    status: draft
---

# BRD
"""


def test_draft_missing_metric_still_errors(tmp_path):
    rows = _rows(_brd_proj(tmp_path, _V2_NO_METRIC_BRD))
    gwm = [r for r in rows if r[0] == "goal_without_metric" and r[1] == "BRD-G1"]
    assert gwm, "a metric-less goal must still be caught"
    assert gwm[0][2] == "error", "a fresh schema_version:2 goal with no metric must ERROR (gate intact)"


# --------------------------------------------------------------------------- #
# Out-of-spec frontmatter: a story carrying a PRD/BRD parent ref + a malformed version.
# --------------------------------------------------------------------------- #

_BRD_FOR_STORY = """---
id: BRD
type: brd
status: approved
lang: en
version: 1.0.0
goals:
  - id: BRD-G1
    title: "A goal"
    metrics: [north-star]
    status: approved
---

# BRD
"""

# A story whose parent is (correctly) the epic, but which ALSO carries `prd:` and
# `brd_goals:` (a story's parent is the epic only) and a 2-part `version` (not semver-lite).
_MISPLACED_STORY = """---
id: PRD-AUTH-E1-S1
type: story
epic: PRD-AUTH-E1
prd: PRD-AUTH
brd_goals: [BRD-G1]
status: draft
lang: en
version: "0.3"
scope: in
moscow: must
horizon: now
size: S
acceptance_criteria:
  - "Given x, when y, then z."
  - "Given a, when b, then c."
---

# Story
"""


def test_misplaced_parent_field_and_bad_version_flagged(tmp_path):
    proj = _brd_proj(tmp_path, _BRD_FOR_STORY)
    (proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md").write_text(
        _MISPLACED_STORY, encoding="utf-8"
    )
    rows = _rows(proj)

    assert any(c == "misplaced_parent_field" and a == "PRD-AUTH-E1-S1" for c, a, _s, _d in rows), \
        "a story carrying prd/brd_goals (its parent is the epic) must be flagged"
    assert any(c == "bad_version_format" and a == "PRD-AUTH-E1-S1" for c, a, _s, _d in rows), \
        "a malformed (non semver-lite) version must be flagged"
