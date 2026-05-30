"""Fail-soft regression tests for malformed frontmatter / graph input.

The validation/parse/render layer must NEVER crash on a hand-edited spec — it
must coerce at the graph source or emit a finding. These cover the foundation
hardening:
- frontmatter_parser: out-of-range date (PyYAML ValueError), non-UTF-8 file,
  empty frontmatter block.
- spec_graph: scalar id/epic/prd coercion; brd_goals never char-split into edges;
  non-string competitor url dropped to None.
- check_consistency: calendar-invalid quoted target_date, duplicate competitor id,
  competitive_parity misplaced on a non-PRD.
- build_traceability_matrix: mixed-type metrics / non-string brd_goals element.
"""

import datetime as dt

import frontmatter_parser as fp
import spec_graph as sg
import check_consistency as cc
import build_traceability_matrix as bm


# ── frontmatter_parser fail-soft ────────────────────────────────────────────

def test_out_of_range_unquoted_date_is_parse_error_not_crash():
    """An unquoted `target_date: 2026-13-99` makes PyYAML raise a bare ValueError
    (not a YAMLError); parse_text must surface it as an error, never propagate."""
    text = "---\nid: PRD-A\ntype: prd\ntarget_date: 2026-13-99\n---\nbody\n"
    res = fp.parse_text(text)
    assert res["ok"] is False
    assert res["error"] and "parse error" in res["error"].lower()


def test_non_utf8_file_is_encoding_error(tmp_path):
    """A non-UTF-8 file raises UnicodeDecodeError (a ValueError subclass, not an
    OSError); parse_file must catch it and return a structured parse_error."""
    p = tmp_path / "bad.md"
    p.write_bytes(b"---\nid: PRD-A\n\xff\xfe not utf-8 \n---\n")
    res = fp.parse_file(p)
    assert res["ok"] is False
    assert "encoding" in (res["error"] or "").lower()


def test_empty_frontmatter_block_reports_accurately():
    """`---\\n---` has a closing fence; the error must say it is empty, not the
    misleading 'missing closing ---'."""
    res = fp.parse_text("---\n---\nbody\n")
    assert res["ok"] is False
    assert res["error"] == "frontmatter block is empty"


# ── spec_graph source coercion ──────────────────────────────────────────────

def test_scalar_id_coercion():
    assert sg._scalar_id("PRD-A") == "PRD-A"
    assert sg._scalar_id(None) == "<missing-id>"
    assert sg._scalar_id("") == "<missing-id>"
    assert sg._scalar_id(["PRD-A"]) == "<invalid-id>"   # list → sentinel, never a dict key crash
    assert sg._scalar_id(123) == "<invalid-id>"


def test_scalar_link_coercion():
    assert sg._scalar_link("PRD-A-E1") == "PRD-A-E1"
    assert sg._scalar_link(None) is None
    assert sg._scalar_link(["PRD-A-E1"]) is None        # list → None, never an unhashable parent key
    assert sg._scalar_link({"x": 1}) is None


def test_build_edges_does_not_charsplit_bare_brd_goals():
    """A bare-string `brd_goals: BRD-G1` (hand-edit) must NOT become one edge per
    character; build_edges only emits edges for list elements that are strings."""
    nodes = [{"id": "PRD-A", "type": "prd", "brd_goals": "BRD-G1"}]
    edges = sg.build_edges(nodes)
    assert edges == []  # not a list → no edges (and definitely no per-char edges)
    # a real list still works, in order
    nodes2 = [{"id": "PRD-B", "type": "prd", "brd_goals": ["BRD-G1", 42, "BRD-G2"]}]
    goals = [e["to"] for e in sg.build_edges(nodes2) if e["kind"] == "brd_goal"]
    assert goals == ["BRD-G1", "BRD-G2"]  # non-str element filtered, order preserved


def test_competitor_non_string_url_dropped_to_none():
    arts = [{
        "ok": True, "file": "brd.md", "__type_hint": "brd",
        "frontmatter": {"type": "brd", "competitors": [
            {"id": "COMP-A", "name": "A", "url": ["x"]},          # non-str url
            {"id": "COMP-B", "name": "B", "url": "private:secret"},  # OpSec drop
            {"id": "COMP-C", "name": "C", "url": "https://ok"},
        ]},
    }]
    comps = sg._competitors(arts)
    by_id = {c["id"]: c for c in comps}
    assert by_id["COMP-A"]["url"] is None
    assert by_id["COMP-B"]["url"] is None
    assert by_id["COMP-C"]["url"] == "https://ok"


# ── check_consistency fail-soft + new checks ────────────────────────────────

def _graph(nodes, competitors=None):
    return {"version": "1.0", "generated_at": "x", "product": {},
            "nodes": nodes, "edges": sg.build_edges(nodes),
            "risks": [], "competitors": competitors or [], "parse_errors": []}


def test_check_does_not_crash_on_unhashable_scalar_fields():
    """A list status / list id reaching check() must not raise (it is coerced at
    the source in production, but check() itself stays defensive)."""
    nodes = [{"id": "<invalid-id>", "type": "prd", "status": ["draft"],
              "brd_goals": [], "epic": None, "prd": None}]
    findings = cc.check(_graph(nodes))  # must not raise
    assert any(f["check"] == "invalid_type" for f in findings)


def test_quoted_calendar_invalid_target_date_flagged():
    nodes = [{"id": "PRD-A", "type": "prd", "target_date": "2026-13-99",
              "brd_goals": [], "epic": None, "prd": None}]
    findings = cc.check(_graph(nodes))
    assert any(f["check"] == "invalid_type" and "target_date" in (f.get("detail") or "")
               for f in findings)


def test_duplicate_competitor_id_flagged():
    comps = [{"id": "COMP-A", "name": "A", "threat": "high"},
             {"id": "COMP-A", "name": "A2", "threat": "low"}]
    findings = cc._check_competitors(_graph([], comps))
    assert any(f["check"] == "dup_id" for f in findings)


def test_competitive_parity_on_non_prd_is_invalid_type():
    story = {"id": "PRD-A-E1-S1", "type": "story", "brd_goals": [], "epic": "PRD-A-E1",
             "prd": None, "competitive_parity": {"COMP-A": "behind"}}
    findings = cc._check_competitive_parity(story, _graph([story]))
    assert any(f["check"] == "invalid_type" for f in findings)


# ── build_traceability_matrix fail-soft ─────────────────────────────────────

def test_matrix_no_crash_on_mixed_metrics_and_brd_goals():
    nodes = [
        {"id": "PRD-A", "type": "prd", "brd_goals": [101, "BRD-G1"], "epic": None, "prd": None},
        {"id": "PRD-A-E1", "type": "epic", "prd": "PRD-A", "brd_goals": [], "epic": None},
        {"id": "PRD-A-E1-S1", "type": "story", "epic": "PRD-A-E1", "prd": None,
         "brd_goals": [], "metrics": [42, "conv"], "status": "draft"},
    ]
    out = bm.build_matrix(_graph(nodes))  # must not raise
    assert isinstance(out, str) and "PRD-A-E1-S1" in out
