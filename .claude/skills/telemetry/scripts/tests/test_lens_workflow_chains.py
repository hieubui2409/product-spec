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


def test_declared_chains_loaded_from_data_file(lens, monkeypatch, tmp_path):
    # Declared chains now live in an on-demand YAML data file owned by the skill,
    # not in always-on routing docs. Point the lens at a fixture data file.
    data = tmp_path / "skill-chains.yaml"
    data.write_text("chains:\n  - [product-spec, product-spec-critique]\n", encoding="utf-8")
    monkeypatch.setenv("CK_SKILL_CHAINS", str(data))
    d = lens.gather(days=BIG_DAYS, skills_dir=FIX / "skills")
    assert isinstance(d["declared_chains"], list)
    assert len(d["declared_chains"]) >= 1
    assert "product-spec → product-spec-critique" in d["declared_chains"]


def test_declared_chains_raises_when_data_file_missing(lens, monkeypatch, tmp_path):
    # A missing declared-source file is a packaging bug — fail loud, never silently
    # report zero declared chains (the failure mode that shipped a red test before).
    monkeypatch.setenv("CK_SKILL_CHAINS", str(tmp_path / "does-not-exist.yaml"))
    with pytest.raises(FileNotFoundError):
        lens.gather(days=BIG_DAYS, skills_dir=FIX / "skills")


def test_declared_chains_null_key_is_empty_not_crash(lens, monkeypatch, tmp_path):
    # `chains:` explicitly null means "deliberately no declared chains" — empty, not an error.
    data = tmp_path / "skill-chains.yaml"
    data.write_text("chains: null\n", encoding="utf-8")
    monkeypatch.setenv("CK_SKILL_CHAINS", str(data))
    d = lens.gather(days=BIG_DAYS, skills_dir=FIX / "skills")
    assert d["declared_chains"] == []


@pytest.mark.parametrize(
    "bad",
    [
        "chains:\n  - product-spec\n",          # entry is a bare string → would char-split
        "chains:\n  - [product-spec, null]\n",  # null step → would become a "None" skill
        "chains: not-a-list\n",                 # chains is a scalar
    ],
)
def test_declared_chains_raises_on_malformed_data(lens, monkeypatch, tmp_path, bad):
    # Malformed declared data fails loud — never silently char-splits a string into a fake
    # multi-step chain or coerces a null step into a literal "None" skill id.
    data = tmp_path / "skill-chains.yaml"
    data.write_text(bad, encoding="utf-8")
    monkeypatch.setenv("CK_SKILL_CHAINS", str(data))
    with pytest.raises(ValueError):
        lens.gather(days=BIG_DAYS, skills_dir=FIX / "skills")
