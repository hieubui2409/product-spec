"""test_telemetry_paths_helpers.py — the lens-facing additions to
telemetry_paths.py: sessions_dir(), memory_dir(), TELEMETRY, and the encoded
project slug. All must honor env overrides (tests redirect to tmp dirs) and
must NOT disturb the existing project_dir()/telemetry_dir() contract.
"""
import importlib
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))


def _load():
    """Reload telemetry_paths fresh (caller sets env via monkeypatch first)."""
    sys.modules.pop("telemetry_paths", None)
    import telemetry_paths
    importlib.reload(telemetry_paths)
    return telemetry_paths


class TestSessionsDir:
    def test_env_override_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_SESSIONS_DIR", str(tmp_path / "sess"))
        mod = _load()
        assert mod.sessions_dir() == tmp_path / "sess"

    def test_default_is_home_projects_encoded_root(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CK_SESSIONS_DIR", raising=False)
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/home/u/Documents/cleanmatic-skills")
        mod = _load()
        expected = Path.home() / ".claude" / "projects" / "-home-u-Documents-cleanmatic-skills"
        assert mod.sessions_dir() == expected


class TestMemoryDir:
    def test_env_override_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_MEMORY_DIR", str(tmp_path / "mem"))
        mod = _load()
        assert mod.memory_dir() == tmp_path / "mem"

    def test_default_is_sessions_dir_slash_memory(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CK_MEMORY_DIR", raising=False)
        monkeypatch.setenv("CK_SESSIONS_DIR", str(tmp_path / "sess"))
        mod = _load()
        assert mod.memory_dir() == tmp_path / "sess" / "memory"


class TestTelemetryConst:
    def test_points_at_dot_claude_telemetry_by_default(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CK_TELEMETRY_DIR", raising=False)
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
        mod = _load()
        assert mod.TELEMETRY == tmp_path / ".claude" / "telemetry"

    def test_env_override_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(tmp_path / "tele"))
        mod = _load()
        assert mod.TELEMETRY == tmp_path / "tele"

    def test_const_has_no_mkdir_side_effect(self, tmp_path, monkeypatch):
        # A read-side const must not create the dir merely by importing.
        target = tmp_path / "tele-nomkdir"
        monkeypatch.setenv("CK_TELEMETRY_DIR", str(target))
        _load()
        assert not target.exists(), "TELEMETRY import must not mkdir"
