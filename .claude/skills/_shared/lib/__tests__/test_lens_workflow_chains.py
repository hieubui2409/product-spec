"""test_lens_workflow_chains.py — actual per-session chains (flat-slug normalized)
from the fixture invocation sink, plus deviation/gate logic."""
import importlib
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))
FIX = Path(__file__).resolve().parent / "fixtures"
BIG_DAYS = 36500


@pytest.fixture
def lens(monkeypatch):
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(FIX / "telemetry"))
    monkeypatch.setenv("CK_SKILLS_DIR", str(FIX / "skills"))
    for m in ("telemetry_paths", "catalog", "lens_workflow_chains"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_workflow_chains
    importlib.reload(lens_workflow_chains)
    return lens_workflow_chains


def test_actual_chains_per_session_ordered_and_normalized(lens):
    d = lens.gather(days=BIG_DAYS, skills_dir=FIX / "skills")
    assert d["sessions_analyzed"] == 2
    chains = {c["chain"] for c in d["common_chains"]}
    assert "product-spec → product-spec" in chains  # sessA: two product-spec invocations
    assert "product-spec → release → product-spec-critique" in chains  # sessB, ts-ordered


def test_thin_data_marked_insufficient_and_gated(lens):
    d = lens.gather(days=BIG_DAYS, min_sessions=5, skills_dir=FIX / "skills")
    assert d["sufficient"] is False  # 2 < 5
    assert d["gated"] is True


def test_declared_chains_parsed_from_routing_docs(lens):
    d = lens.gather(days=BIG_DAYS, skills_dir=FIX / "skills")
    # The real .claude/rules routing docs declare multi-step chains.
    assert isinstance(d["declared_chains"], list)
    assert len(d["declared_chains"]) >= 1
