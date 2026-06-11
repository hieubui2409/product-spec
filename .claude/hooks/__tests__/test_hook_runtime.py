"""test_hook_runtime.py — the shared 7-hook runtime (crash audit + config gate +
telemetry wrapper).

Hermetic: CK_HOOK_LOG_DIR redirects the crash log and CK_HOOK_CONFIG redirects
the per-hook config to tmp_path; PYTEST_CURRENT_TEST is cleared where a write
must actually be asserted (the crash logger is silent under pytest by design,
mirroring telemetry_paths.disabled()).
"""
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HOOKS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HOOKS))


def _fresh(monkeypatch, tmp_path, *, config: dict | None = None, audit: bool = True,
           extra_env: dict | None = None):
    """Reload hook_runtime with a tmp log dir + (optional) tmp config file, with
    PYTEST_CURRENT_TEST cleared so log_hook_error actually writes."""
    monkeypatch.setenv("CK_HOOK_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
    if audit:
        monkeypatch.delenv("CK_HOOK_AUDIT_DISABLED", raising=False)
    if config is not None:
        cfg_path = tmp_path / "product-spec-hooks.json"
        cfg_path.write_text(json.dumps(config), encoding="utf-8")
        monkeypatch.setenv("CK_HOOK_CONFIG", str(cfg_path))
    else:
        monkeypatch.delenv("CK_HOOK_CONFIG", raising=False)
    for k, v in (extra_env or {}).items():
        monkeypatch.setenv(k, v)
    sys.modules.pop("hook_runtime", None)
    import hook_runtime
    importlib.reload(hook_runtime)
    hook_runtime._reset_config_cache()
    return hook_runtime


def _crash_lines(tmp_path) -> list[dict]:
    p = tmp_path / "logs" / "hook-crashes.log"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# crash audit
# ---------------------------------------------------------------------------

class TestCrashAudit:
    def test_forced_exception_logs_exactly_one_line(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path)
        try:
            raise ValueError("boom-marker")
        except ValueError as e:
            hr.log_hook_error("some_hook", e)
        lines = _crash_lines(tmp_path)
        assert len(lines) == 1
        rec = lines[0]
        assert rec["hook"] == "some_hook"
        assert rec["type"] == "ValueError"
        assert "boom-marker" in rec["msg"]

    def test_unwritable_logdir_never_raises(self, tmp_path, monkeypatch):
        # Point the log dir at a path whose parent is a FILE → mkdir fails →
        # logger must swallow, never raise into the caller.
        blocker = tmp_path / "blocker"
        blocker.write_text("x")
        monkeypatch.setenv("CK_HOOK_LOG_DIR", str(blocker / "logs"))
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        sys.modules.pop("hook_runtime", None)
        import hook_runtime
        importlib.reload(hook_runtime)
        # Must not raise.
        hook_runtime.log_hook_error("h", RuntimeError("z"))

    def test_audit_disabled_writes_nothing(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, extra_env={"CK_HOOK_AUDIT_DISABLED": "1"})
        hr.log_hook_error("h", RuntimeError("nope"))
        assert _crash_lines(tmp_path) == []

    def test_over_cap_rotates_to_dot_one(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path)
        logdir = tmp_path / "logs"
        logdir.mkdir(parents=True, exist_ok=True)
        # Pre-fill past the 256 KB ceiling so the next write rotates.
        (logdir / "hook-crashes.log").write_text("x" * (300 * 1024))
        hr.log_hook_error("h", RuntimeError("after-rotate"))
        assert (logdir / "hook-crashes.log.1").exists()
        lines = _crash_lines(tmp_path)
        assert len(lines) == 1 and "after-rotate" in lines[0]["msg"]


# ---------------------------------------------------------------------------
# config gate
# ---------------------------------------------------------------------------

class TestHookEnabled:
    def test_telemetry_missing_key_defaults_enabled(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, config={})
        assert hr.hook_enabled("track_skill_invocation") is True

    def test_enforcement_missing_key_defaults_disabled(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, config={})
        # THE safety-critical assertion: a blocking hook is never fallback-enabled.
        assert hr.hook_enabled("memory_gap_hook") is False
        assert hr.hook_enabled("product_spec_critique_nudge") is False

    def test_explicit_false_telemetry_disables(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, config={"mark_bash_start": False})
        assert hr.hook_enabled("mark_bash_start") is False

    def test_explicit_true_enforcement_enables(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, config={"memory_gap_hook": True})
        assert hr.hook_enabled("memory_gap_hook") is True

    def test_global_telemetry_disabled_off_for_telemetry_not_enforcement(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, config={"memory_gap_hook": True},
                    extra_env={"CK_TELEMETRY_DISABLED": "1"})
        assert hr.hook_enabled("track_script_execution") is False  # telemetry off
        assert hr.hook_enabled("memory_gap_hook") is True          # enforcement unaffected

    def test_global_kill_overrides_explicit_true_telemetry(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, config={"emit_session_summary": True},
                    extra_env={"CK_TELEMETRY_DISABLED": "1"})
        assert hr.hook_enabled("emit_session_summary") is False

    def test_malformed_config_safe_defaults_and_crash_logged(self, tmp_path, monkeypatch):
        cfg_path = tmp_path / "product-spec-hooks.json"
        cfg_path.write_text("{ this is not json", encoding="utf-8")
        monkeypatch.setenv("CK_HOOK_CONFIG", str(cfg_path))
        monkeypatch.setenv("CK_HOOK_LOG_DIR", str(tmp_path / "logs"))
        monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
        monkeypatch.delenv("CK_TELEMETRY_DISABLED", raising=False)
        sys.modules.pop("hook_runtime", None)
        import hook_runtime
        importlib.reload(hook_runtime)
        hook_runtime._reset_config_cache()
        # Safe per-class default: telemetry on, enforcement off.
        assert hook_runtime.hook_enabled("mark_bash_start") is True
        assert hook_runtime.hook_enabled("memory_gap_hook") is False
        assert len(_crash_lines(tmp_path)) >= 1


# ---------------------------------------------------------------------------
# telemetry wrapper
# ---------------------------------------------------------------------------

class TestRunTelemetryHook:
    def test_enabled_runs_core_and_continues(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, config={})
        seen = {}
        out = []
        monkeypatch.setattr(hr.sys.stdout, "write", lambda s: out.append(s))
        hr.run_telemetry_hook("track_skill_invocation",
                              lambda data: seen.update(data), raw='{"k": 1}')
        assert seen == {"k": 1}
        assert '"continue"' in "".join(out)

    def test_disabled_skips_core_still_continues(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, config={"track_skill_invocation": False})
        called = []
        out = []
        monkeypatch.setattr(hr.sys.stdout, "write", lambda s: out.append(s))
        hr.run_telemetry_hook("track_skill_invocation",
                              lambda data: called.append(1), raw='{"k": 1}')
        assert called == []
        assert '"continue"' in "".join(out)

    def test_core_exception_is_crash_logged_and_still_continues(self, tmp_path, monkeypatch):
        hr = _fresh(monkeypatch, tmp_path, config={})
        out = []
        monkeypatch.setattr(hr.sys.stdout, "write", lambda s: out.append(s))

        def boom(_data):
            raise RuntimeError("core-broke")

        hr.run_telemetry_hook("track_script_execution", boom, raw="{}")
        assert '"continue"' in "".join(out)
        assert any("core-broke" in r["msg"] for r in _crash_lines(tmp_path))


# ---------------------------------------------------------------------------
# name-drift guard + import-skip proof
# ---------------------------------------------------------------------------

# The 7 project hooks (file stems). hook_enabled keys MUST equal this set.
_ALL_STEMS = {
    "mark_bash_start", "track_skill_invocation", "track_script_execution",
    "track_subagent_outcome", "emit_session_summary",
    "memory_gap_hook", "product_spec_critique_nudge",
}

# Non-stem config keys: MODE/policy knobs that hook_enabled ignores (it only reads
# the 7 stems above). memory_gap_mode selects advisory|blocking for the memory hook.
_NON_STEM_CONFIG_KEYS = {"memory_gap_mode"}


def test_config_keys_equal_all_seven_hook_stems():
    cfg = json.loads((_HOOKS / "product-spec-hooks.json").read_text())
    keys = {k for k in cfg.keys() if not k.startswith("_")}
    assert keys - _NON_STEM_CONFIG_KEYS == _ALL_STEMS
    # Every key is either a known stem or a known non-stem knob (no typos / drift).
    assert keys <= _ALL_STEMS | _NON_STEM_CONFIG_KEYS
    # And every stem maps to a real hook file (drift guard both directions).
    for stem in _ALL_STEMS:
        assert (_HOOKS / f"{stem}.py").is_file(), f"missing hook file for {stem}"
    # The shipped mode, if present, is one of the two valid values.
    if "memory_gap_mode" in cfg:
        assert cfg["memory_gap_mode"] in {"advisory", "blocking"}


def test_memory_gap_mode_defaults_to_advisory_and_honors_blocking(tmp_path, monkeypatch):
    """memory_gap_mode(): blocking ONLY when explicitly set; everything else
    (absent, empty, typo) falls to the SAFE advisory default."""
    import importlib

    def _mode_for(cfg_obj):
        p = tmp_path / "m.json"
        p.write_text(json.dumps(cfg_obj))
        monkeypatch.setenv("CK_HOOK_CONFIG", str(p))
        sys.modules.pop("hook_runtime", None)
        hr = importlib.import_module("hook_runtime")
        return hr.memory_gap_mode()

    assert _mode_for({}) == "advisory"                                  # absent → advisory
    assert _mode_for({"memory_gap_mode": "advisory"}) == "advisory"
    assert _mode_for({"memory_gap_mode": "blocking"}) == "blocking"     # explicit opt-in
    assert _mode_for({"memory_gap_mode": "BLOCKING"}) == "advisory"     # case-strict → advisory
    assert _mode_for({"memory_gap_mode": "weird"}) == "advisory"        # typo → safe default
    sys.modules.pop("hook_runtime", None)


def test_disabled_telemetry_hook_does_not_import_telemetry_paths(tmp_path):
    """Subprocess proof: a config-disabled telemetry hook must emit continue:true
    WITHOUT importing telemetry_paths (the controllability win)."""
    cfg = tmp_path / "product-spec-hooks.json"
    cfg.write_text(json.dumps({"track_skill_invocation": False}))
    probe = (
        "import sys, json; "
        f"sys.path.insert(0, {str(_HOOKS)!r}); "
        "import hook_runtime; "
        "import track_skill_invocation as h; "
        "h.main(json.dumps({'tool_name':'Skill','tool_input':{'skill':'x'},'session_id':'s'})); "
        "assert 'telemetry_paths' not in sys.modules, 'telemetry_paths was imported while disabled'; "
        "sys.stderr.write('OK')"
    )
    env = dict(os.environ)
    env["CK_HOOK_CONFIG"] = str(cfg)
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("CK_TELEMETRY_DISABLED", None)
    proc = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, env=env)
    assert proc.returncode == 0, f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    assert '"continue"' in proc.stdout
    assert "OK" in proc.stderr
