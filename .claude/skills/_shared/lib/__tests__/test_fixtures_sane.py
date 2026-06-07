"""test_fixtures_sane.py — locks the hand-verifiable counts of the shared
telemetry fixtures so later phases' parity tests rest on a known baseline. If a
fixture drifts, this fails first (clear signal) instead of a downstream lens
test failing cryptically.
"""
import json
from pathlib import Path

FIX = Path(__file__).resolve().parent / "fixtures"
TELE = FIX / "telemetry"


def _lines(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def test_invocations_5_records_3_skills_incl_prompt_expansion():
    recs = _lines(TELE / "invocations.jsonl")
    assert len(recs) == 5
    vias = {r["via"] for r in recs}
    assert "UserPromptExpansion" in vias
    # 3 distinct skills once normalized (product-spec recorded as both slug + dir form)
    raw_skills = {r["skill"] for r in recs}
    assert raw_skills == {
        "cleanmatic:product-spec",
        "product-spec",
        "cleanmatic:release",
        "cleanmatic:product-spec-critique",
    }


def test_hook_telemetry_4_runs_one_error_one_missing_ms():
    recs = _lines(TELE / "hook-telemetry.jsonl")
    assert len(recs) == 4
    assert sum(1 for r in recs if r["exit"] != 0) == 1
    assert sum(1 for r in recs if "ms" not in r) == 1  # graceful-degrade case


def test_sessions_2_records():
    recs = _lines(TELE / "sessions.jsonl")
    assert len(recs) == 2
    assert {r["session"] for r in recs} == {"sessA", "sessB"}


def test_subagent_outcomes_3_records_one_timeout():
    recs = _lines(TELE / "subagent-outcomes.jsonl")
    assert len(recs) == 3
    assert sum(1 for r in recs if r["outcome"] == "timeout") == 1


def test_stray_unknown_sink_present():
    assert (TELE / "unknown-stray.jsonl").exists()


def test_transcript_has_two_skill_spans_with_usage():
    recs = _lines(FIX / "sessions" / "sessB.jsonl")
    skill_spans = [
        b for r in recs
        for b in (r.get("message", {}).get("content") or [])
        if b.get("type") == "tool_use" and b.get("name") == "Skill"
    ]
    assert len(skill_spans) == 2
    assert all("usage" in r["message"] for r in recs)


def test_memory_dir_has_index_orphan_and_dead_entry():
    mem = FIX / "memory"
    assert (mem / "MEMORY.md").exists()
    assert (mem / "good-fact.md").exists()
    assert (mem / "orphan-fact.md").exists()  # orphan: not in MEMORY.md
    assert not (mem / "missing-file.md").exists()  # dead index entry target
    index = (mem / "MEMORY.md").read_text()
    assert "missing-file.md" in index  # the dead entry is referenced
    assert "orphan-fact.md" not in index  # orphan truly absent from index
