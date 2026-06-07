"""Tests for run_evals — the structural eval-gate harness, on synthetic fixtures.
Run: .claude/skills/.venv/bin/python3 -m pytest .claude/skills/_shared/lib/__tests__/test_run_evals.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run_evals  # type: ignore  # noqa: E402


def _skill(tmp_path: Path, doc: dict, *, helper: str | None = None) -> tuple[Path, Path]:
    skill_dir = tmp_path / "skill"
    (skill_dir / "eval").mkdir(parents=True)
    evals = skill_dir / "eval" / "evals.json"
    evals.write_text(json.dumps(doc), encoding="utf-8")
    if helper:
        (skill_dir / "echo.py").write_text(helper, encoding="utf-8")
    return evals, skill_dir


def test_all_pass_exits_zero(tmp_path):
    # exec writes a file into {out}; assertions check exit 0 + file exists.
    helper = "import sys,os\nopen(os.path.join(sys.argv[1],'made.txt'),'w').write('ok')\nprint('done')\n"
    doc = {
        "skill": "x",
        "scenarios": [{
            "id": "s1",
            "exec": [sys.executable, "echo.py", "{out}"],
            "assertions": [
                {"id": "ran", "_gating": "structural", "check": "exit_zero"},
                {"id": "made", "_gating": "structural", "check": "file_exists", "path": "{out}/made.txt"},
                {"id": "said", "_gating": "structural", "check": "stdout_contains", "substr": "done"},
            ],
        }],
    }
    evals, skill_dir = _skill(tmp_path, doc, helper=helper)
    rc = run_evals.main(["--evals", str(evals), "--skill-dir", str(skill_dir)])
    assert rc == 0


def test_one_fail_exits_one_and_names_it(tmp_path, capsys):
    doc = {
        "scenarios": [{
            "id": "s1",
            "assertions": [
                {"id": "ghost", "_gating": "structural", "check": "file_exists", "path": "{out}/nope.txt"},
            ],
        }],
    }
    evals, skill_dir = _skill(tmp_path, doc)
    rc = run_evals.main(["--evals", str(evals), "--skill-dir", str(skill_dir)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAIL" in out and "ghost" in out


def test_llm_advisory_is_skip_not_pass(tmp_path, capsys):
    doc = {"scenarios": [{"id": "s1", "assertions": [{"id": "judgy", "_gating": "llm_advisory", "text": "vibes"}]}]}
    evals, skill_dir = _skill(tmp_path, doc)
    rc = run_evals.main(["--evals", str(evals), "--skill-dir", str(skill_dir)])
    out = capsys.readouterr().out
    assert rc == 0  # advisory never fails the gate
    assert "SKIP" in out and "0 pass" in out and "1 skip(manual)" in out


def test_unknown_checker_is_hard_fail(tmp_path):
    doc = {"scenarios": [{"id": "s1", "assertions": [{"id": "bad", "_gating": "structural", "check": "frobnicate"}]}]}
    evals, skill_dir = _skill(tmp_path, doc)
    rc = run_evals.main(["--evals", str(evals), "--skill-dir", str(skill_dir)])
    assert rc == 1  # a check naming a nonexistent checker must FAIL loudly, not skip


def test_unmapped_structural_is_loud_nonfatal_then_strict_fatal(tmp_path, capsys):
    doc = {"scenarios": [{"id": "s1", "assertions": [{"id": "todo", "_gating": "structural", "text": "no check yet"}]}]}
    evals, skill_dir = _skill(tmp_path, doc)
    rc = run_evals.main(["--evals", str(evals), "--skill-dir", str(skill_dir)])
    out = capsys.readouterr().out
    assert rc == 0 and "UNMAPPED" in out and "1 unmapped" in out  # visible, counted, non-gating
    rc2 = run_evals.main(["--evals", str(evals), "--skill-dir", str(skill_dir), "--strict-structural"])
    assert rc2 == 1  # strict makes unmapped fatal


def test_bare_string_assertion_is_unmapped(tmp_path, capsys):
    doc = {"scenarios": [{"id": "s1", "assertions": ["tarball exists somewhere"]}]}
    evals, skill_dir = _skill(tmp_path, doc)
    rc = run_evals.main(["--evals", str(evals), "--skill-dir", str(skill_dir)])
    out = capsys.readouterr().out
    assert rc == 0 and "UNMAPPED" in out  # legacy bare strings are not silent passes


def test_missing_evals_is_fatal(tmp_path):
    rc = run_evals.main(["--evals", str(tmp_path / "nope.json"), "--skill-dir", str(tmp_path)])
    assert rc == 2
