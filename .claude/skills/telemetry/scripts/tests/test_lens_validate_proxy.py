"""test_lens_validate_proxy.py — the validate-pass internal-quality proxy.
Self-contained fixtures (tmp marker + tmp telemetry) so it never couples to the
shared sinks. Asserts the source decision tree: marker present → last status;
validate-script exit history → pass rate; neither → honest unavailable."""
import importlib
import json
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))
BIG = 36500


def _load(monkeypatch, project_dir, tele_dir):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(project_dir))
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(tele_dir))
    for m in ("telemetry_paths", "lens_validate_proxy"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_validate_proxy
    importlib.reload(lens_validate_proxy)
    return lens_validate_proxy


def _marker(project_dir, validated_at="2026-06-06T03:58:36+00:00"):
    p = project_dir / "docs" / "product" / ".memory"
    p.mkdir(parents=True, exist_ok=True)
    (p / "last_validated.json").write_text(json.dumps(
        {"snapshot": "snap.json", "snapshot_hash": "abcd1234", "validated_at": validated_at}))


def _tele(tele_dir, lines):
    tele_dir.mkdir(parents=True, exist_ok=True)
    (tele_dir / "hook-telemetry.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")


def test_unavailable_emits_language_neutral_reason_code(tmp_path, monkeypatch):
    # No English prose in the gathered dict — only a neutral reason_code the
    # renderer localizes. Guards the EN-leaking-into-VI bug at the source.
    lens = _load(monkeypatch, tmp_path / "proj", tmp_path / "tele")
    d = lens.gather(days=BIG)
    assert d["available"] is False
    assert d["not_e3"] is True
    assert d["reason_code"] == "no_data"
    assert "reason" not in d  # prose must not be baked in


def test_marker_gives_last_status_validated(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    _marker(proj)
    lens = _load(monkeypatch, proj, tmp_path / "tele")
    d = lens.gather(days=BIG)
    assert d["available"] is True
    assert d["last_status"] == "validated"
    assert d["validated_at"] == "2026-06-06T03:58:36+00:00"
    assert d["validate_pass_rate"] is None  # marker alone → no rate, NOT 0%


def test_pass_rate_from_validate_script_exits(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    tele = tmp_path / "tele"
    _tele(tele, [
        {"ts": "2026-06-06T10:00:00+00:00", "script": "product-spec/scripts/check_consistency.py", "exit": 0},
        {"ts": "2026-06-06T10:01:00+00:00", "script": "product-spec/scripts/check_traceability.py", "exit": 0},
        {"ts": "2026-06-06T10:02:00+00:00", "script": "product-spec/scripts/strict_gate.py", "exit": 1},
        {"ts": "2026-06-06T10:03:00+00:00", "script": "product-spec/scripts/visualize.py", "exit": 0},  # NOT a validate script
    ])
    lens = _load(monkeypatch, proj, tele)
    d = lens.gather(days=BIG)
    assert d["available"] is True          # runs > 0 even without a marker
    assert d["total"] == 3                 # visualize.py excluded
    assert d["validate_pass_rate"] == 67   # 2/3
    assert d["last_status"] == "never"     # no marker
    assert d["gated"] is True              # 3 < 5
    assert d["internal_quality"] is True and d["not_e3"] is True


def test_combines_marker_and_rate(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    tele = tmp_path / "tele"
    _marker(proj)
    _tele(tele, [
        {"ts": "2026-06-06T10:00:00+00:00", "script": "product-spec/scripts/check_consistency.py", "exit": 0},
    ])
    lens = _load(monkeypatch, proj, tele)
    d = lens.gather(days=BIG)
    assert d["available"] is True
    assert d["last_status"] == "validated"
    assert d["validate_pass_rate"] == 100
