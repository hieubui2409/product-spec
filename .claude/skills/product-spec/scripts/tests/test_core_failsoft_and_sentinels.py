"""Regression tests for core fail-soft + id-sentinel handling.

Covers the four areas specified for new tests:
  1. generate_templates.load_values — OSError/non-dict JSON raises ValueError
  2. render_export._heading — CR/LF in title/id collapse to space (not injected)
  3. spec_graph.diff_graphs — mixed-type (non-str) personas never raise TypeError
  4. check_consistency dup_id — sentinel <missing-id> / <invalid-id> NOT reported
     as a false-positive dup_id finding

Also covers related behavioural changes:
  5. assemble_digest._entry uses resolve_ac (None/'' AC items filtered, count matches)
  6. assemble_digest unresolved-help subtracts both sentinels
  7. spec_graph.index_artifacts keys by _scalar_id (no drop for malformed-id artifact)
  8. check_consistency._status_inconsistency bare-string brd_goals no crash
  9. check_traceability non-list brd_goals → no duplicate invalid_type finding
 10. generate_templates --id + conflicting --slug for prd raises ValueError
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_templates import load_values, allocate_id  # noqa: E402
from render_export import _heading  # noqa: E402
from spec_graph import (  # noqa: E402
    diff_graphs, index_artifacts, build_graph, load_artifacts,
)
from check_consistency import check as check_cons  # noqa: E402
from check_traceability import check as check_trace  # noqa: E402
import assemble_digest  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


# ── 1. load_values ──────────────────────────────────────────────────────────

def test_load_values_ioerror_raises_valueerror(tmp_path):
    """A path to a directory (not a file) raises ValueError, not OSError."""
    # A directory: p.exists() is True but p.read_text() raises IsADirectoryError
    d = tmp_path / "adir"
    d.mkdir()
    with pytest.raises(ValueError, match="could not read file"):
        load_values(str(d))


def test_load_values_non_dict_json_raises_valueerror(tmp_path):
    """Top-level JSON array raises ValueError."""
    f = tmp_path / "values.json"
    f.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
    with pytest.raises(ValueError, match="top-level JSON must be an object"):
        load_values(str(f))


def test_load_values_non_dict_json_inline_raises_valueerror():
    """Inline JSON number raises ValueError."""
    with pytest.raises(ValueError, match="top-level JSON must be an object"):
        load_values("42")


def test_load_values_non_dict_json_null_raises_valueerror():
    """Inline JSON null raises ValueError."""
    with pytest.raises(ValueError, match="top-level JSON must be an object"):
        load_values("null")


def test_load_values_valid_dict_passes():
    """A valid JSON object (inline) parses correctly."""
    result = load_values('{"name": "Acme", "count": 3}')
    assert result == {"name": "Acme", "count": 3}


def test_load_values_empty_spec_returns_empty():
    assert load_values(None) == {}
    assert load_values("") == {}


# ── 2. render_export._heading CRLF collapse ─────────────────────────────────

def test_heading_collapses_cr_in_title():
    entry = {"id": "PRD-AUTH", "title": "Auth\rService"}
    h = _heading(entry)
    assert "\r" not in h
    assert "Auth Service" in h


def test_heading_collapses_lf_in_title():
    entry = {"id": "PRD-AUTH", "title": "Auth\nService"}
    h = _heading(entry)
    assert "\n" not in h
    assert "Auth Service" in h


def test_heading_collapses_crlf_in_title():
    entry = {"id": "PRD-AUTH", "title": "Auth\r\nService"}
    h = _heading(entry)
    assert "\r" not in h
    assert "\n" not in h
    assert "Auth  Service" in h or "Auth Service" in h  # two spaces or one (double replace)


def test_heading_collapses_newline_in_id():
    entry = {"id": "PRD-AU\nTH", "title": "Auth"}
    h = _heading(entry)
    assert "\n" not in h
    assert "PRD-AU TH" in h


def test_heading_no_title_uses_id_only():
    entry = {"id": "PRD-AUTH", "title": ""}
    h = _heading(entry)
    assert h == "PRD-AUTH"


def test_heading_with_title_uses_dash_separator():
    entry = {"id": "PRD-AUTH", "title": "Authentication"}
    h = _heading(entry)
    assert "PRD-AUTH" in h
    assert "Authentication" in h
    assert "—" in h


# ── 3. diff_graphs mixed-type personas no crash ─────────────────────────────

def test_diff_graphs_mixed_type_personas_no_crash():
    """Non-str persona values (int/dict) must not raise TypeError on sorted()."""
    cur = {
        "nodes": [],
        "edges": [],
        "product": {"name": "A", "core_value": "x", "personas": [1, "admin", {"role": "buyer"}]},
    }
    base = {
        "nodes": [],
        "edges": [],
        "product": {"name": "A", "core_value": "x", "personas": ["admin", "buyer"]},
    }
    result = diff_graphs(cur, base)
    # Should complete without TypeError; personas differ so it is flagged.
    assert "personas" in result["product_changes"]


def test_diff_graphs_identical_personas_no_change():
    cur = {
        "nodes": [],
        "edges": [],
        "product": {"name": "A", "core_value": "x", "personas": ["shopper", "admin"]},
    }
    base = {
        "nodes": [],
        "edges": [],
        "product": {"name": "A", "core_value": "x", "personas": ["admin", "shopper"]},
    }
    result = diff_graphs(cur, base)
    assert "personas" not in result["product_changes"]


def test_diff_graphs_none_personas_no_crash():
    cur = {"nodes": [], "edges": [], "product": {"personas": None}}
    base = {"nodes": [], "edges": [], "product": {"personas": None}}
    result = diff_graphs(cur, base)
    assert result["product_changes"] == []


# ── 4. dup_id sentinel skip ──────────────────────────────────────────────────

def _minimal_graph_with_nodes(nodes):
    return {
        "nodes": nodes,
        "edges": [],
        "competitors": [],
        "root_path": "",
    }


def test_dup_id_sentinel_missing_id_not_reported():
    """Two artifacts with missing id (both get '<missing-id>') must NOT produce
    a false-positive dup_id finding for the sentinel value."""
    graph = _minimal_graph_with_nodes([
        {"id": "<missing-id>", "type": "prd", "file": "prds/a.md",
         "status": "draft", "scope": None, "moscow": None, "horizon": None,
         "size": None, "lang": None, "personas": [], "metrics": [], "brd_goals": [],
         "risks": None, "depends_on": [], "target_date": None, "competitive_parity": None,
         "owner": None, "version": None, "epic": None, "prd": None},
        {"id": "<missing-id>", "type": "prd", "file": "prds/b.md",
         "status": "draft", "scope": None, "moscow": None, "horizon": None,
         "size": None, "lang": None, "personas": [], "metrics": [], "brd_goals": [],
         "risks": None, "depends_on": [], "target_date": None, "competitive_parity": None,
         "owner": None, "version": None, "epic": None, "prd": None},
    ])
    findings = check_cons(graph)
    dup_findings = [f for f in findings if f["check"] == "dup_id"]
    assert dup_findings == [], f"Expected no dup_id for sentinel, got {dup_findings}"


def test_dup_id_sentinel_invalid_id_not_reported():
    """Two artifacts with malformed id (both get '<invalid-id>') must NOT produce
    a false-positive dup_id finding."""
    graph = _minimal_graph_with_nodes([
        {"id": "<invalid-id>", "type": "prd", "file": "prds/a.md",
         "status": "draft", "scope": None, "moscow": None, "horizon": None,
         "size": None, "lang": None, "personas": [], "metrics": [], "brd_goals": [],
         "risks": None, "depends_on": [], "target_date": None, "competitive_parity": None,
         "owner": None, "version": None, "epic": None, "prd": None},
        {"id": "<invalid-id>", "type": "prd", "file": "prds/b.md",
         "status": "draft", "scope": None, "moscow": None, "horizon": None,
         "size": None, "lang": None, "personas": [], "metrics": [], "brd_goals": [],
         "risks": None, "depends_on": [], "target_date": None, "competitive_parity": None,
         "owner": None, "version": None, "epic": None, "prd": None},
    ])
    findings = check_cons(graph)
    dup_findings = [f for f in findings if f["check"] == "dup_id"]
    assert dup_findings == [], f"Expected no dup_id for sentinel, got {dup_findings}"


def test_dup_id_real_collision_still_reported():
    """A genuine ID collision on a real (non-sentinel) ID must still be reported."""
    graph = _minimal_graph_with_nodes([
        {"id": "PRD-AUTH", "type": "prd", "file": "prds/a.md",
         "status": "draft", "scope": None, "moscow": None, "horizon": None,
         "size": None, "lang": None, "personas": [], "metrics": [], "brd_goals": [],
         "risks": None, "depends_on": [], "target_date": None, "competitive_parity": None,
         "owner": None, "version": None, "epic": None, "prd": None},
        {"id": "PRD-AUTH", "type": "prd", "file": "prds/b.md",
         "status": "draft", "scope": None, "moscow": None, "horizon": None,
         "size": None, "lang": None, "personas": [], "metrics": [], "brd_goals": [],
         "risks": None, "depends_on": [], "target_date": None, "competitive_parity": None,
         "owner": None, "version": None, "epic": None, "prd": None},
    ])
    findings = check_cons(graph)
    dup_findings = [f for f in findings if f["check"] == "dup_id"]
    assert len(dup_findings) == 1
    assert dup_findings[0]["artifact_id"] == "PRD-AUTH"


# ── 5. resolve_ac used in _entry (None/'' items filtered) ───────────────────

def test_entry_ac_filters_none_and_empty_items():
    """_entry for a story must use resolve_ac so None/'' AC items are excluded."""
    node = {"id": "PRD-AUTH-E1-S1", "type": "story", "title": "T",
            "status": None, "file": "stories/x.md"}
    artifact = {
        "ok": True,
        "frontmatter": {
            "acceptance_criteria": [None, "", "Given X then Y", None, "Given A then B"],
        },
        "body": "",
    }
    entry = assemble_digest._entry(node, "target", "full", artifact)
    # Only the two non-empty/non-None items should survive.
    assert entry["ac"] == ["Given X then Y", "Given A then B"]
    assert len(entry["ac"]) == 2


def test_entry_ac_none_frontmatter_yields_empty_list():
    """No acceptance_criteria in frontmatter → ac = [] (not None, not crash)."""
    node = {"id": "PRD-AUTH-E1-S1", "type": "story", "title": "T",
            "status": None, "file": "stories/x.md"}
    artifact = {"ok": True, "frontmatter": {}, "body": ""}
    entry = assemble_digest._entry(node, "target", "full", artifact)
    assert entry["ac"] == []


def test_entry_ac_for_non_story_is_none():
    """For a non-story node ac must be None (not a list)."""
    node = {"id": "PRD-AUTH", "type": "prd", "title": "Auth", "status": None, "file": "prds/auth.md"}
    artifact = {
        "ok": True,
        "frontmatter": {"acceptance_criteria": ["something"]},
        "body": "",
    }
    entry = assemble_digest._entry(node, "target", "full", artifact)
    assert entry["ac"] is None


# ── 6. unresolved-help subtracts both sentinels ──────────────────────────────

def test_unresolved_help_excludes_both_sentinels(tmp_path):
    """The ValueError message for an unknown selection must not include either
    <missing-id> or <invalid-id> sentinel in the 'Available IDs' list."""
    # Build a minimal spec with one missing-id artifact so the graph carries
    # both sentinel values.
    prod = tmp_path / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(
        "---\nid: PRODUCT\ntype: product\nstatus: draft\nlang: en\n"
        "name: X\ncore_value: y\npersonas: []\n---\n",
        encoding="utf-8",
    )
    (prod / "brd.md").write_text(
        "---\ntype: brd\nstatus: draft\nlang: en\ngoals:\n  - id: BRD-G1\n"
        "    title: g\n    status: draft\n    metrics: []\n---\n",
        encoding="utf-8",
    )
    # PRD without an id: → will produce a <missing-id> node
    (prod / "prds" / "noId.md").write_text(
        "---\ntype: prd\nstatus: draft\nlang: en\nbrd_goals: [BRD-G1]\n---\n",
        encoding="utf-8",
    )

    graph = build_graph(tmp_path)
    artifacts = load_artifacts(prod)

    with pytest.raises(ValueError) as exc_info:
        assemble_digest.build_digest(graph, artifacts, select="DOES-NOT-EXIST")
    msg = str(exc_info.value)
    assert "<missing-id>" not in msg
    assert "<invalid-id>" not in msg


# ── 7. index_artifacts keys by _scalar_id ───────────────────────────────────

def test_index_artifacts_includes_malformed_id_artifact():
    """An artifact whose frontmatter id is a list (non-str) must be indexed under
    '<invalid-id>' and NOT dropped silently."""
    artifact = {
        "ok": True,
        "frontmatter": {"id": ["a", "b"], "type": "prd"},  # malformed: list, not str
        "body": "body text",
        "file": "prds/bad.md",
    }
    idx = index_artifacts([artifact])
    assert "<invalid-id>" in idx
    assert idx["<invalid-id>"]["body"] == "body text"


def test_index_artifacts_normal_id_unchanged():
    """Normal string ID still works."""
    artifact = {
        "ok": True,
        "frontmatter": {"id": "PRD-AUTH", "type": "prd"},
        "body": "body",
        "file": "prds/auth.md",
    }
    idx = index_artifacts([artifact])
    assert "PRD-AUTH" in idx


# ── 8. _status_inconsistency bare-string brd_goals no crash ─────────────────

def test_status_inconsistency_bare_string_brd_goals_no_crash():
    """A PRD with brd_goals as a bare string must not crash _status_inconsistency;
    it should simply skip the PRD->goal check (invalid_type owns the shape error)."""
    graph = _minimal_graph_with_nodes([
        {"id": "PRD-X", "type": "prd", "file": "prds/x.md",
         "status": "approved", "scope": "in", "moscow": None, "horizon": None,
         "size": None, "lang": None, "personas": [], "metrics": [],
         # bare string instead of list:
         "brd_goals": "BRD-G1",
         "risks": None, "depends_on": [], "target_date": None, "competitive_parity": None,
         "owner": None, "version": None, "epic": None, "prd": None},
    ])
    # Must not raise; just produce findings (invalid_type but no TypeError).
    findings = check_cons(graph)
    checks = {f["check"] for f in findings}
    # invalid_type for brd_goals shape is expected; no crash.
    assert "invalid_type" in checks
    # No status_inconsistency from a bare-string brd_goals.
    status_findings = [f for f in findings if f["check"] == "status_inconsistency"]
    assert status_findings == []


# ── 9. check_traceability non-list brd_goals → no duplicate invalid_type ─────

def test_traceability_non_list_brd_goals_no_duplicate_invalid_type(tmp_path):
    """A bare-string brd_goals must produce exactly ONE invalid_type (from
    check_consistency), not two (check_traceability was also emitting it)."""
    prod = tmp_path / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(
        "---\nid: PRODUCT\ntype: product\nstatus: draft\nlang: en\n"
        "name: X\ncore_value: y\npersonas: []\n---\n", encoding="utf-8"
    )
    (prod / "brd.md").write_text(
        "---\ntype: brd\nstatus: draft\nlang: en\ngoals:\n  - id: BRD-G1\n"
        "    title: g\n    status: draft\n    metrics: []\n---\n", encoding="utf-8"
    )
    (prod / "prds" / "x.md").write_text(
        "---\nid: PRD-X\ntype: prd\nstatus: draft\nlang: en\n"
        "brd_goals: BRD-G1\n---\n", encoding="utf-8"
    )
    graph = build_graph(tmp_path)
    cons_findings = check_cons(graph)
    trace_findings = check_trace(graph)

    # check_consistency emits the invalid_type.
    cons_it = [f for f in cons_findings if f["check"] == "invalid_type" and f.get("context", {}).get("field") == "brd_goals"]
    assert len(cons_it) == 1, f"expected exactly 1 invalid_type from consistency, got {cons_it}"

    # check_traceability must NOT emit a second invalid_type for brd_goals.
    trace_it = [f for f in trace_findings if f["check"] == "invalid_type" and f.get("context", {}).get("field") == "brd_goals"]
    assert trace_it == [], f"expected no invalid_type from traceability, got {trace_it}"


# ── 10. generate_templates --id + conflicting --slug raises ValueError ────────

def test_generate_id_slug_conflict_raises_valueerror(tmp_path):
    """--id PRD-AUTH with --slug checkout (mismatch) must raise ValueError."""
    import argparse
    from generate_templates import _run
    args = argparse.Namespace(
        root=str(tmp_path),
        type="prd",
        id="PRD-AUTH",
        slug="checkout",    # conflicts: PRD-AUTH implies slug=auth, not checkout
        parent=None,
        values=None,
        keep_optional="",
        lang="en",
        write=False,
        force=False,
    )
    # No docs/product dir needed — the ValueError fires before file I/O.
    # But build_graph needs a missing dir to not crash.
    with pytest.raises(ValueError, match="inconsistent"):
        _run(args)


def test_generate_id_slug_consistent_succeeds(tmp_path):
    """--id PRD-AUTH with matching --slug auth (case-insensitive) must succeed."""
    import argparse
    from generate_templates import _run

    prod = tmp_path / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    args = argparse.Namespace(
        root=str(tmp_path),
        type="prd",
        id="PRD-AUTH",
        slug="AUTH",    # consistent (case-insensitive)
        parent=None,
        values=None,
        keep_optional="",
        lang="en",
        write=False,
        force=False,
    )
    # Should not raise.
    result = _run(args)
    assert result == 0
