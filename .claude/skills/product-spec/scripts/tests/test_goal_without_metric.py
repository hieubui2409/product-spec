"""test_goal_without_metric — C11 Half-B deterministic check.

A BRD goal whose `metrics` is empty or missing → `goal_without_metric` (error). Silent on
goals with >=1 metric. Reproducible + enforced by strict_gate (exit 2).
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from check_consistency import check  # noqa: E402
from spec_graph import build_graph  # noqa: E402
import strict_gate  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
METRICLESS = FIXTURES / "metric-less-goal"
VALID = FIXTURES / "valid-spec"


def _findings_by_artifact(root: Path):
    graph = build_graph(root)
    return [(f["check"], f["artifact_id"], f["severity"]) for f in check(graph)]


def test_fires_on_empty_and_missing_metrics():
    rows = _findings_by_artifact(METRICLESS)
    gwm = {aid for chk, aid, sev in rows if chk == "goal_without_metric"}
    assert gwm == {"BRD-G2", "BRD-G3"}, gwm  # empty list + missing key both flagged
    # severity is error
    assert all(sev == "error" for chk, _aid, sev in rows if chk == "goal_without_metric")


def test_silent_on_goal_with_metric():
    rows = _findings_by_artifact(METRICLESS)
    gwm = {aid for chk, aid, sev in rows if chk == "goal_without_metric"}
    assert "BRD-G1" not in gwm  # has [north-star] → silent


def test_valid_spec_has_no_goal_without_metric():
    rows = _findings_by_artifact(VALID)
    assert not any(chk == "goal_without_metric" for chk, _a, _s in rows)


def test_strict_gate_blocks_on_metric_less_goal():
    findings, _graph = strict_gate.collect_findings(METRICLESS)
    errors = [f for f in findings if f.get("severity") == "error"]
    assert any(f["check"] == "goal_without_metric" for f in errors)


def test_deterministic():
    a = _findings_by_artifact(METRICLESS)
    b = _findings_by_artifact(METRICLESS)
    assert a == b
