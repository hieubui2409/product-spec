"""test_analyze_telemetry_cli.py — the CLI spine: lens dispatch + JSON output.
ascii/md/mermaid rendering is covered in the Phase-5 renderer tests; here we
only assert dispatch + the always-available JSON path.
"""
import importlib
import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent  # telemetry/scripts (flat modules)
sys.path.insert(0, str(_SCRIPTS))
FIX = Path(__file__).resolve().parent / "fixtures"


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
        "workflow_chains", "validate_proxy", "memory_health", "product_memory",
        "artifact_heat",
    }


def test_forensics_and_reliability_lenses_dispatch(cli, capsys, monkeypatch):
    monkeypatch.setenv("CK_SESSIONS_DIR", str(FIX / "sessions"))
    cli.main(["--lens", "forensics", "--format", "json"])
    assert json.loads(capsys.readouterr().out)["lens"] == "forensics"
    cli.main(["--lens", "reliability", "--days", "36500", "--format", "json"])
    assert json.loads(capsys.readouterr().out)["lens"] == "reliability"


def test_unknown_lens_exits_2(cli, capsys):
    assert cli.main(["--lens", "nope"]) == 2


def test_overview_isolates_a_failing_lens(cli, monkeypatch):
    # One lens raising (e.g. workflow fail-loud when skill-chains.yaml is absent)
    # must NOT blank the overview — it degrades to a VISIBLE error entry while the
    # other lenses still gather. The per-lens gather() keeps raising (loud for unit
    # tests); only gather_all isolates.
    monkeypatch.setenv("CK_MEMORY_DIR", str(FIX / "memory"))

    def boom(_a):
        raise RuntimeError("kaboom")
    monkeypatch.setitem(cli.LENSES, "workflow", boom)

    class _Args:
        days = 36500
        top = 10
        no_tokens = False
        session = None
        all_sessions = False

    data = cli.gather_all(_Args())
    failed = [d for d in data if d.get("lens") == "workflow"]
    assert failed and "kaboom" in failed[0].get("error", "")     # error surfaced, not swallowed
    assert any(d.get("lens") == "usage_tokens" and "error" not in d for d in data)  # others survive


def test_health_lens_json(cli, capsys):
    cli.main(["--lens", "health", "--format", "json"])
    out = json.loads(capsys.readouterr().out)
    assert out["total_runs"] == 4


def test_lang_flag_localizes_ascii(cli, capsys):
    # default (vi) → Vietnamese banner; --lang en → English banner. Same data.
    cli.main(["--lens", "usage", "--days", "36500", "--format", "ascii"])
    vi = capsys.readouterr().out
    cli.main(["--lens", "usage", "--days", "36500", "--format", "ascii", "--lang", "en"])
    en = capsys.readouterr().out
    assert "MỨC DÙNG" in vi and "USAGE" in en
    assert "5" in vi and "5" in en  # the invocation count is language-neutral


def test_lang_rejects_unknown_value(cli):
    with pytest.raises(SystemExit) as e:  # argparse choices guard exits 2
        cli.main(["--lens", "usage", "--lang", "fr"])
    assert e.value.code == 2


# ---------------------------------------------------------------------------
# Export-summary default path honors CK_TELEMETRY_DIR (canonical home)
# ---------------------------------------------------------------------------

class TestExportSummaryDefaultPathIsCanonical:
    """Without an explicit PATH arg, --export-summary writes to
    <CK_TELEMETRY_DIR>/usage-summary.md (env-aware canonical path)."""

    def test_export_summary_default_path_honors_env(self, tmp_path, monkeypatch):
        """CK_TELEMETRY_DIR set → default export goes to that dir, not the script-relative wrong path.

        Uses --export-summary with no PATH argument to exercise the default path derivation.
        The expected file is <CK_TELEMETRY_DIR>/usage-summary.md.
        """
        telemetry_dir = tmp_path / "canonical_telemetry"
        telemetry_dir.mkdir()

        # Seed minimal invocations so the lens returns something
        import json as _json
        sink = telemetry_dir / "invocations.jsonl"
        records = [
            {"ts": "2026-06-12T10:00:00+00:00", "skill": "cleanmatic:product-spec",
             "session": "s1", "via": "PreToolUse:Skill"},
        ]
        sink.write_text("\n".join(_json.dumps(r) for r in records) + "\n", encoding="utf-8")

        monkeypatch.setenv("CK_TELEMETRY_DIR", str(telemetry_dir))
        monkeypatch.setenv("CK_SESSIONS_DIR", str(FIX / "sessions"))
        monkeypatch.setenv("CK_SKILLS_DIR", str(FIX / "skills"))
        for m in ("telemetry_paths", "catalog", "lens_usage_tokens",
                  "lens_session_shape", "lens_health", "analyze_telemetry"):
            sys.modules.pop(m, None)
        import telemetry_paths
        importlib.reload(telemetry_paths)
        import analyze_telemetry
        importlib.reload(analyze_telemetry)

        # --export-summary without an explicit PATH triggers the default-path logic.
        # (argparse treats --export-summary with no following token as missing the arg,
        # so we call _write_export_summary directly with export_summary=None to isolate
        # the default-path derivation from argparse wiring.)
        class _Args:
            export_summary = None  # no explicit path
            auto_suggest = False
            days = 36500
            top = None
            no_tokens = False
            session = None
            all_sessions = False
            format = "md"
            lang = "vi"
            lens = "usage"
            overview = False

        rendered = analyze_telemetry._render(
            analyze_telemetry.gather_lens("usage", _Args()), "md", _Args()
        )
        # Patch sys.argv[0] to something clearly NOT in the canonical dir, so any
        # script-relative derivation would produce a wrong path.
        orig_argv = sys.argv[:]
        sys.argv = ["/some/wrong/path/script.py"]
        try:
            # Call with export_summary=None — should derive canonical path from telemetry_paths.TELEMETRY
            analyze_telemetry._write_export_summary(rendered, None, _Args())
        finally:
            sys.argv = orig_argv

        expected = telemetry_dir / "usage-summary.md"
        assert expected.exists(), (
            f"--export-summary default must write to CK_TELEMETRY_DIR/usage-summary.md; "
            f"got nothing at {expected}. Files in telemetry_dir: {list(telemetry_dir.iterdir())}"
        )

    def test_explicit_path_arg_overrides_default(self, tmp_path, monkeypatch):
        """Explicit PATH arg to --export-summary still works as before."""
        telemetry_dir = tmp_path / "telem"
        telemetry_dir.mkdir()

        import json as _json
        sink = telemetry_dir / "invocations.jsonl"
        sink.write_text(
            _json.dumps({"ts": "2026-06-12T10:00:00+00:00", "skill": "cleanmatic:product-spec",
                         "session": "s1", "via": "PreToolUse:Skill"}) + "\n",
            encoding="utf-8",
        )

        explicit_out = tmp_path / "custom-out.md"

        monkeypatch.setenv("CK_TELEMETRY_DIR", str(telemetry_dir))
        monkeypatch.setenv("CK_SESSIONS_DIR", str(FIX / "sessions"))
        monkeypatch.setenv("CK_SKILLS_DIR", str(FIX / "skills"))
        for m in ("telemetry_paths", "catalog", "lens_usage_tokens",
                  "lens_session_shape", "lens_health", "analyze_telemetry"):
            sys.modules.pop(m, None)
        import telemetry_paths
        importlib.reload(telemetry_paths)
        import analyze_telemetry
        importlib.reload(analyze_telemetry)

        rc = analyze_telemetry.main([
            "--lens", "usage", "--days", "36500",
            "--export-summary", str(explicit_out),
        ])
        assert rc == 0
        assert explicit_out.exists(), "explicit PATH arg must write to that exact path"
