"""Tests for llm_eval — the llm_advisory judge harness, fully synthetic.
No network, no API key: every test injects a FakeLLMClient.
Run: .claude/skills/.venv/bin/python3 -m pytest .claude/skills/_shared/lib/__tests__/test_llm_eval.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm_eval  # type: ignore  # noqa: E402
from llm_eval import FakeLLMClient, PASS, FAIL, MISSING, ERROR  # type: ignore  # noqa: E402


def _skill(tmp_path: Path, doc: dict, goldens: dict[str, str] | None = None) -> tuple[Path, Path]:
    skill_dir = tmp_path / "skill"
    (skill_dir / "eval").mkdir(parents=True)
    evals = skill_dir / "eval" / "evals.json"
    evals.write_text(json.dumps(doc), encoding="utf-8")
    for sid, body in (goldens or {}).items():
        g = skill_dir / "eval" / "golden" / f"{sid}.md"
        g.parent.mkdir(parents=True, exist_ok=True)
        g.write_text(body, encoding="utf-8")
    return evals, skill_dir


def _doc(*advisory_ids: str, sid: str = "s1") -> dict:
    return {"scenarios": [{
        "id": sid,
        "prompt": "do the thing",
        "expected_output": "a report with X",
        "assertions": [{"id": i, "_gating": "llm_advisory", "text": f"check {i}"} for i in advisory_ids],
    }]}


# --- parse_verdict (the trust boundary: a judge reply must be PASS/FAIL or ERROR) ---

def test_parse_verdict_clean_json():
    assert llm_eval.parse_verdict('{"verdict":"PASS","rationale":"ok"}') == (PASS, "ok")
    assert llm_eval.parse_verdict('{"verdict":"fail","rationale":"nope"}')[0] == FAIL


def test_parse_verdict_json_embedded_in_prose():
    raw = 'Sure!\n{"verdict": "PASS", "rationale": "cites ID:18"}\nDone.'
    assert llm_eval.parse_verdict(raw) == (PASS, "cites ID:18")


def test_parse_verdict_bare_token_fallback():
    assert llm_eval.parse_verdict("FAIL — tone too soft")[0] == FAIL


def test_parse_verdict_boolean_and_yesno():
    # Real models phrase the verdict as a bool or yes/no, not always the "PASS"/"FAIL" string.
    assert llm_eval.parse_verdict('{"verdict": true, "rationale": "ok"}') == (PASS, "ok")
    assert llm_eval.parse_verdict('{"verdict": false, "rationale": "no"}') == (FAIL, "no")
    assert llm_eval.parse_verdict('{"verdict": "yes", "rationale": "y"}')[0] == PASS
    assert llm_eval.parse_verdict('{"verdict": "no", "rationale": "n"}')[0] == FAIL


def test_parse_verdict_garbage_is_error_not_pass():
    # A judge that returns nonsense must NOT silently count as a pass.
    assert llm_eval.parse_verdict("the vibes are immaculate")[0] == ERROR
    assert llm_eval.parse_verdict("")[0] == ERROR


# --- judging against a golden -------------------------------------------------

def test_pass_when_judge_says_pass(tmp_path):
    doc = _doc("tone")
    evals, skill_dir = _skill(tmp_path, doc, goldens={"s1": "# report\nstrong"})
    client = FakeLLMClient('{"verdict":"PASS","rationale":"good"}')
    rows, tally = llm_eval.run_llm_evals(evals, skill_dir, client)
    assert tally == {PASS: 1, FAIL: 0, MISSING: 0, ERROR: 0}


def test_missing_golden_is_loud_not_pass(tmp_path):
    doc = _doc("tone")  # no golden written
    evals, skill_dir = _skill(tmp_path, doc)
    client = FakeLLMClient('{"verdict":"PASS"}')
    rows, tally = llm_eval.run_llm_evals(evals, skill_dir, client)
    assert tally[MISSING] == 1 and tally[PASS] == 0
    # judge must NOT have been consulted when the golden is absent
    assert client.calls == []


def test_fail_verdict_counts_fail(tmp_path):
    doc = _doc("tone")
    evals, skill_dir = _skill(tmp_path, doc, goldens={"s1": "# report\nweak sauce"})
    client = FakeLLMClient('{"verdict":"FAIL","rationale":"tone too soft"}')
    rows, tally = llm_eval.run_llm_evals(evals, skill_dir, client)
    assert tally[FAIL] == 1


def test_unparseable_judge_is_error(tmp_path):
    doc = _doc("tone")
    evals, skill_dir = _skill(tmp_path, doc, goldens={"s1": "# report"})
    client = FakeLLMClient("I cannot decide")
    rows, tally = llm_eval.run_llm_evals(evals, skill_dir, client)
    assert tally[ERROR] == 1


def test_only_advisory_assertions_judged(tmp_path):
    doc = {"scenarios": [{
        "id": "s1", "prompt": "p", "expected_output": "e",
        "assertions": [
            {"id": "struct", "_gating": "structural", "check": "file_exists", "path": "x"},
            {"id": "judgy", "_gating": "llm_advisory", "text": "tone"},
        ],
    }]}
    evals, skill_dir = _skill(tmp_path, doc, goldens={"s1": "# report"})
    client = FakeLLMClient('{"verdict":"PASS"}')
    rows, tally = llm_eval.run_llm_evals(evals, skill_dir, client)
    assert len(rows) == 1 and rows[0][1] == "judgy"  # structural left to run_evals.py


def test_per_assertion_prompt_carries_assertion_text(tmp_path):
    doc = _doc("tone-level-4")
    evals, skill_dir = _skill(tmp_path, doc, goldens={"s1": "# report body"})
    seen = {}

    def responder(system, user):
        seen["user"] = user
        return '{"verdict":"PASS"}'

    llm_eval.run_llm_evals(evals, skill_dir, FakeLLMClient(responder))
    assert "check tone-level-4" in seen["user"] and "# report body" in seen["user"]


# --- CLI / gating -------------------------------------------------------------

def test_main_exits_one_on_fail(tmp_path, capsys):
    doc = _doc("tone")
    evals, skill_dir = _skill(tmp_path, doc, goldens={"s1": "# r"})
    rc = llm_eval.main(["--evals", str(evals), "--skill-dir", str(skill_dir)],
                       client=FakeLLMClient('{"verdict":"FAIL","rationale":"x"}'))
    assert rc == 1
    assert "FAIL" in capsys.readouterr().out


def test_main_missing_nonfatal_then_strict_fatal(tmp_path):
    doc = _doc("tone")
    evals, skill_dir = _skill(tmp_path, doc)  # no golden
    fake = FakeLLMClient('{"verdict":"PASS"}')
    rc = llm_eval.main(["--evals", str(evals), "--skill-dir", str(skill_dir)], client=fake)
    assert rc == 0  # missing is loud but non-gating by default
    rc2 = llm_eval.main(["--evals", str(evals), "--skill-dir", str(skill_dir), "--strict-missing"], client=fake)
    assert rc2 == 1


def test_main_all_pass_exits_zero(tmp_path, capsys):
    doc = _doc("tone", "fix")
    evals, skill_dir = _skill(tmp_path, doc, goldens={"s1": "# r"})
    rc = llm_eval.main(["--evals", str(evals), "--skill-dir", str(skill_dir)],
                       client=FakeLLMClient('{"verdict":"PASS"}'))
    assert rc == 0
    assert "2 pass" in capsys.readouterr().out


def test_main_missing_evals_fatal(tmp_path):
    rc = llm_eval.main(["--evals", str(tmp_path / "nope.json"), "--skill-dir", str(tmp_path)],
                       client=FakeLLMClient(""))
    assert rc == 2


# --- generation (deferred path, but the orchestration is synthetic-testable) --

def test_gen_writes_draft_marked_golden_and_never_overwrites(tmp_path, capsys):
    doc = _doc("tone", sid="s1")
    evals, skill_dir = _skill(tmp_path, doc)
    fake = FakeLLMClient("GENERATED REPORT BODY")
    rc = llm_eval.main(["--evals", str(evals), "--skill-dir", str(skill_dir), "--gen"], client=fake)
    assert rc == 0
    g = skill_dir / "eval" / "golden" / "s1.md"
    text = g.read_text(encoding="utf-8")
    assert "DRAFT" in text and "NEEDS HUMAN REVIEW" in text and "GENERATED REPORT BODY" in text
    # second --gen must NOT clobber the (now human-owned) golden
    fake2 = FakeLLMClient("DIFFERENT BODY")
    llm_eval.main(["--evals", str(evals), "--skill-dir", str(skill_dir), "--gen"], client=fake2)
    assert g.read_text(encoding="utf-8") == text and fake2.calls == []
