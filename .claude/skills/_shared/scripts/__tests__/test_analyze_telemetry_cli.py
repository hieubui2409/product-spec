"""test_analyze_telemetry_cli.py — the CLI spine: lens dispatch + JSON output.
ascii/md/mermaid rendering is covered in the Phase-5 renderer tests; here we
only assert dispatch + the always-available JSON path.
"""
import importlib
import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent
_LIB = _SCRIPTS.parent / "lib"
sys.path.insert(0, str(_LIB))
sys.path.insert(0, str(_SCRIPTS))
FIX = _LIB / "__tests__" / "fixtures"


@pytest.fixture
def cli(monkeypatch):
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(FIX / "telemetry"))
    monkeypatch.setenv("CK_SESSIONS_DIR", str(FIX / "sessions"))
    monkeypatch.setenv("CK_SKILLS_DIR", str(FIX / "skills"))
    for m in ("telemetry_paths", "catalog", "lens_usage_tokens",
              "lens_session_shape", "lens_health", "analyze_telemetry"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import analyze_telemetry
    importlib.reload(analyze_telemetry)
    return analyze_telemetry


def test_single_lens_json(cli, capsys):
    rc = cli.main(["--lens", "usage", "--days", "36500", "--format", "json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["lens"] == "usage_tokens"
    assert out["total_invocations"] == 5


def test_all_lenses_json_is_a_list(cli, capsys, monkeypatch):
    monkeypatch.setenv("CK_MEMORY_DIR", str(FIX / "memory"))
    rc = cli.main(["--lens", "all", "--days", "36500", "--format", "json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert isinstance(out, list)
    assert {d["lens"] for d in out} == {
        "usage_tokens", "session_shape", "health", "reliability",
        "workflow_chains", "validate_proxy", "memory_health",
    }


def test_forensics_and_reliability_lenses_dispatch(cli, capsys, monkeypatch):
    monkeypatch.setenv("CK_SESSIONS_DIR", str(FIX / "sessions"))
    cli.main(["--lens", "forensics", "--format", "json"])
    assert json.loads(capsys.readouterr().out)["lens"] == "forensics"
    cli.main(["--lens", "reliability", "--days", "36500", "--format", "json"])
    assert json.loads(capsys.readouterr().out)["lens"] == "reliability"


def test_unknown_lens_exits_2(cli, capsys):
    assert cli.main(["--lens", "nope"]) == 2


def test_health_lens_json(cli, capsys):
    cli.main(["--lens", "health", "--format", "json"])
    out = json.loads(capsys.readouterr().out)
    assert out["total_runs"] == 4
