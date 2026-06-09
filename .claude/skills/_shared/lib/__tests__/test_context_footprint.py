"""Tests for context_footprint — the per-skill SKILL.md/ref token harness + GATE co-presence guard.
Run: .claude/skills/.venv/bin/python3 -m pytest .claude/skills/_shared/lib/__tests__/test_context_footprint.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import context_footprint as cf  # type: ignore  # noqa: E402

ALWAYS_ON = (
    "<GATE-NO-SILENT-REVERSAL>\nfull prose home.\n</GATE-NO-SILENT-REVERSAL>\n"
    "<GATE-NEVER-ASSUME>\nfull prose home.\n</GATE-NEVER-ASSUME>\n"
)


# --- token proxy -------------------------------------------------------------

def test_token_proxy_monotone_and_deterministic():
    small = cf.token_proxy("ab")
    big = cf.token_proxy("ab" * 100)
    assert big > small
    assert cf.token_proxy("hello world") == cf.token_proxy("hello world")  # deterministic


def test_token_proxy_is_ceil_chars_over_4():
    assert cf.token_proxy("a" * 4) == 1
    assert cf.token_proxy("a" * 5) == 2  # ceil(5/4)
    assert cf.token_proxy("") == 0


# --- measure_skill -----------------------------------------------------------

def _mk_skill(root: Path, name: str, skill_md: str, refs: dict[str, str]) -> Path:
    sk = root / ".claude" / "skills" / name
    (sk / "references").mkdir(parents=True)
    (sk / "SKILL.md").write_text(skill_md, encoding="utf-8")
    for fn, body in refs.items():
        (sk / "references" / fn).write_text(body, encoding="utf-8")
    return sk


def test_measure_skill_reports_skill_md_refs_and_total(tmp_path):
    sk = _mk_skill(tmp_path, "demo", "# demo\n" + "x" * 40, {"a.md": "y" * 80})
    m = cf.measure_skill(sk)
    assert m["skill_md_tokens"] > 0
    assert "a.md" in m["refs"]
    assert m["total_tokens"] == m["skill_md_tokens"] + m["refs"]["a.md"]


def test_measure_skill_malformed_no_flag_table_is_graceful(tmp_path):
    sk = _mk_skill(tmp_path, "noflags", "# just a heading, no flag table\nprose only", {})
    m = cf.measure_skill(sk)  # must not raise
    assert m["skill_md_tokens"] > 0
    assert m["flag_rows"] == []  # advisory: empty, not a crash


# --- baseline / compare / gate ----------------------------------------------

def test_compare_shrunk_ref_is_negative_delta(tmp_path):
    base = {"demo": {"skill_md_tokens": 100, "total_tokens": 200, "refs": {"a.md": 100}}}
    after = {"demo": {"skill_md_tokens": 100, "total_tokens": 160, "refs": {"a.md": 60}}}
    diff = cf.compare(base, after)
    assert diff["demo"]["total_delta"] == -40
    assert diff["demo"]["skill_md_delta"] == 0


def test_gate_fails_when_skill_md_grows(tmp_path):
    base = {"demo": {"skill_md_tokens": 100, "total_tokens": 200, "refs": {}}}
    after = {"demo": {"skill_md_tokens": 120, "total_tokens": 220, "refs": {}}}
    ok, regressions = cf.gate(cf.compare(base, after))
    assert ok is False
    assert any("demo" in r for r in regressions)


def test_gate_passes_when_skill_md_shrinks(tmp_path):
    base = {"demo": {"skill_md_tokens": 120, "total_tokens": 220, "refs": {}}}
    after = {"demo": {"skill_md_tokens": 100, "total_tokens": 200, "refs": {}}}
    ok, regressions = cf.gate(cf.compare(base, after))
    assert ok is True
    assert regressions == []


# --- GATE co-presence check (the safety guard) -------------------------------

def test_copresence_pointer_with_alwayson_home_passes(tmp_path):
    # SKILL.md references a GATE as a pointer; its full-prose home is always-on → reachable.
    sk = _mk_skill(tmp_path, "demo",
                   "# demo\n| flag | does X, see GATE-NEVER-ASSUME |\n",
                   {"a.md": "see GATE-NO-SILENT-REVERSAL for the rule"})
    failures = cf.copresence_check([sk], ALWAYS_ON)
    assert failures == []


def test_copresence_pointer_with_unreachable_home_fails(tmp_path):
    # A GATE referenced nowhere-homed (not always-on, not full-prose in the skill) → FAIL.
    sk = _mk_skill(tmp_path, "demo",
                   "# demo\n| flag | guarded by GATE-PHANTOM-RULE |\n", {})
    failures = cf.copresence_check([sk], ALWAYS_ON)
    assert failures
    assert any("GATE-PHANTOM-RULE" in f for f in failures)


def test_copresence_sees_colon_pointer_form(tmp_path):
    # The compacted flag rows use the colon form `GATE:NAME`; the home is the hyphen tag form.
    # The check must normalize both to the same key and resolve the always-on home.
    sk = _mk_skill(tmp_path, "demo",
                   "# demo\n| flag | log a call · GATE:NO-SILENT-REVERSAL · see ref |\n", {})
    assert cf._gate_names("GATE:NO-SILENT-REVERSAL") == {"GATE-NO-SILENT-REVERSAL"}
    assert cf.copresence_check([sk], ALWAYS_ON) == []


def test_copresence_colon_pointer_unreachable_fails(tmp_path):
    # A colon-form pointer to a GATE with no home anywhere must FAIL (the BLOCKER-2 guard,
    # on the exact convention the compacted SKILL.md rows use).
    sk = _mk_skill(tmp_path, "demo", "# demo\n| flag | GATE:PHANTOM-COLON-RULE |\n", {})
    failures = cf.copresence_check([sk], ALWAYS_ON)
    assert any("GATE-PHANTOM-COLON-RULE" in f for f in failures)


def test_gate_names_edge_cases():
    # single-char suffix is caught; mid-word is rejected; a trailing dash is excluded from the name.
    assert cf._gate_names("see GATE-X here") == {"GATE-X"}
    assert cf._gate_names("MITIGATE-RISK plan") == set()        # mid-word: no match
    assert cf._gate_names("GATEWAY-DRUG") == set()              # mid-word: no match
    assert cf._gate_names("GATE-FOO- trailing") == {"GATE-FOO"}  # dash not part of the name
    assert cf._gate_names("bare GATE: noname") == set()         # no suffix → no match


def test_copresence_full_home_in_skill_is_reachable(tmp_path):
    # GATE not always-on, but full-prose home (tag block) lives in the skill itself → reachable.
    sk = _mk_skill(tmp_path, "demo",
                   "# demo\n<GATE-LOCAL-RULE>\nfull prose.\n</GATE-LOCAL-RULE>\n| flag | see GATE-LOCAL-RULE |\n",
                   {})
    failures = cf.copresence_check([sk], ALWAYS_ON)
    assert failures == []


# --- CLI smoke ---------------------------------------------------------------

def test_cli_baseline_then_gate_roundtrip(tmp_path, capsys):
    sk = _mk_skill(tmp_path, "demo", "# demo\n| flag | see GATE-NEVER-ASSUME |\n", {"a.md": "z" * 40})
    always = tmp_path / "CLAUDE.md"
    always.write_text(ALWAYS_ON, encoding="utf-8")
    base_json = tmp_path / "base.json"
    rc = cf.main(["--baseline", "--skills", str(sk), "--always-on", str(always), "--out", str(base_json)])
    assert rc == 0
    assert base_json.is_file()
    data = json.loads(base_json.read_text())
    assert "demo" in data
    # compare same tree against itself → no regression, exit 0
    rc2 = cf.main(["--compare", str(base_json), "--skills", str(sk), "--always-on", str(always), "--gate"])
    assert rc2 == 0
