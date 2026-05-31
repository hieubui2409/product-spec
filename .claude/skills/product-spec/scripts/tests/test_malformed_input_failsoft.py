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
- render_ascii.persona: dict/unhashable persona no crash; non-str persona counted.
"""

import datetime as dt

import frontmatter_parser as fp
import spec_graph as sg
import check_consistency as cc
import build_traceability_matrix as bm
import render_ascii as ra
import render_html as rh
import check_traceability as ct
import generate_templates as gt
import migrate_multidim_fields as mm


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


# ── render_ascii.persona fail-soft (Cycle-10 regression) ────────────────────

def _persona_graph(product_personas, stories):
    """Minimal graph for persona() tests: one PRD + epic + given stories."""
    nodes = [
        {"id": "PRD-A", "type": "prd", "brd_goals": [], "epic": None, "prd": None},
        {"id": "PRD-A-E1", "type": "epic", "prd": "PRD-A", "brd_goals": [], "epic": None},
    ] + stories
    g = _graph(nodes)
    g["product"] = {"personas": product_personas}
    return g


def test_persona_dict_persona_does_not_crash():
    """personas:[{role: 'admin'}] is an unhashable value — must not raise TypeError
    when used as a dict key. The grid still renders (shows a str-coerced row)."""
    dict_persona = {"role": "admin"}
    stories = [
        {"id": "PRD-A-E1-S1", "type": "story", "epic": "PRD-A-E1", "prd": None,
         "brd_goals": [], "personas": [dict_persona]},
    ]
    g = _persona_graph([dict_persona], stories)
    result = ra.persona(g)  # must not raise
    assert isinstance(result, str)
    assert "(no personas yet)" not in result  # row was rendered


def test_persona_non_str_scalar_counts_correctly():
    """personas:[5] — a non-str scalar must be treated as str('5') for both the
    row label and the cell key so the count is non-zero, not silently zero."""
    stories = [
        {"id": "PRD-A-E1-S1", "type": "story", "epic": "PRD-A-E1", "prd": None,
         "brd_goals": [], "personas": [5]},
    ]
    g = _persona_graph([5], stories)
    result = ra.persona(g)  # must not raise
    assert isinstance(result, str)
    # The cell for persona '5' vs PRD-A should be '1', not '0'.
    # _grid right-aligns numeric cells so the raw cell is '| ... 1 |' with padding.
    assert "| 5" in result          # row label present
    lines = [l for l in result.splitlines() if l.startswith("| 5")]
    assert lines, "row for persona '5' not found"
    # Extract the count token; right-aligned cell value is the last non-empty token
    # before the trailing '|'. Strip and check it is '1', not '0'.
    cells = [t.strip() for t in lines[0].split("|") if t.strip()]
    # cells[0] = row label, remaining = per-PRD counts
    count_cells = cells[1:]
    assert any(c == "1" for c in count_cells), f"expected count '1' but got {count_cells!r}"


def test_persona_no_crash_on_non_list_risks():
    """render_ascii.risk() on non-list / non-dict-entry risks must not crash."""
    g = _graph([])
    g["risks"] = [None, "bad", {"impact": "high", "likelihood": "low"}]
    result = ra.risk(g)  # must not raise
    assert isinstance(result, str)
    # The one valid risk should show up in the high-impact/low-likelihood cell.
    assert "|" in result


# ── _node_type: malformed `type:` resolves identically everywhere ───────────

def test_node_type_coerces_malformed_type():
    assert sg._node_type({"frontmatter": {"type": "brd"}}) == "brd"
    # truthy non-string `type:` (hand-edit) falls back to the directory hint,
    # never short-circuits the `or` with the raw list.
    assert sg._node_type({"frontmatter": {"type": ["brd"]}, "__type_hint": "brd"}) == "brd"
    assert sg._node_type({"frontmatter": {}, "__type_hint": "prd"}) == "prd"


def test_competitors_survive_malformed_brd_type():
    """A brd.md with a malformed `type: [brd]` still yields its competitors — the
    same coercion build_nodes applies to its goals (no asymmetric vanish)."""
    arts = [{
        "ok": True, "file": "brd.md", "__type_hint": "brd",
        "frontmatter": {"type": ["brd"], "competitors": [
            {"id": "COMP-ACME", "name": "Acme", "url": "https://acme"},
        ]},
    }]
    comps = sg._competitors(arts)
    assert [c["id"] for c in comps] == ["COMP-ACME"]


# ── check_traceability: unhashable brd_goals element must not crash ─────────

def test_check_traceability_unhashable_brd_goal_element_no_crash():
    """A dict element inside a PRD's brd_goals list is unhashable; the membership
    test must skip it rather than raise TypeError and crash the gate."""
    nodes = [
        {"id": "BRD-G1", "type": "goal", "brd_goals": [], "epic": None, "prd": None},
        {"id": "PRD-A", "type": "prd", "brd_goals": [{"nested": "dict"}, "BRD-G1"],
         "epic": None, "prd": None},
    ]
    findings = ct.check(_graph(nodes))  # must not raise
    # the valid "BRD-G1" element still resolves (no dangling_link for it)
    assert not any(f["check"] == "dangling_link" and f.get("context", {}).get("ref") == "BRD-G1"
                   for f in findings)


# ── render_html: bare-scalar metrics + non-str/non-dict product ─────────────

def test_goal_detail_md_bare_scalar_metrics_no_charsplit():
    node = {"type": "goal", "metrics": "single-metric"}
    out = rh.goal_detail_md(node, "en")
    assert "single-metric" in out
    # a char-split would have produced "s, i, n, g, ..." — assert it did not
    assert "s, i, n" not in out


def test_product_name_coerces_non_str_and_non_dict():
    assert rh.product_name({"product": {"name": ["Acme"]}}) == "['Acme']"
    assert rh.product_name({"product": "notadict"}) == "(unnamed)"
    assert rh.product_name({"product": {"name": "Acme"}}) == "Acme"
    assert rh.product_name({}) == "(unnamed)"


# ── render_ascii: non-dict product block must not crash ─────────────────────

def test_ascii_product_helpers_no_crash_on_non_dict_product():
    g = _graph([])
    g["product"] = "notadict"
    assert ra._ascii_product_name(g) == "(no PRODUCT.md)"  # must not raise
    assert isinstance(ra.persona(g), str)                  # must not raise


# ── generate_templates: residual check runs AFTER comment strip ─────────────

def test_residual_token_check_ignores_leading_comment_tokens():
    """An illustrative {{example-token}} inside the leading header comment (which
    is stripped) must NOT trip the residual-token guard."""
    out = gt.render("<!-- see {{example-token}} for usage -->\nid: {{id}}\n",
                    {"id": "PRD-A"}, [])
    assert "id: PRD-A" in out
    assert "example-token" not in out  # the whole comment was stripped


# ── migrate: brd.md type resolution scoped to product-dir root ──────────────

def test_type_for_path_brd_only_at_product_root(tmp_path):
    root = tmp_path / "docs" / "product"
    assert mm._type_for_path(root / "brd.md") == "brd"
    # a file literally named brd.md under prds/ is a PRD (matches the glob), not brd
    assert mm._type_for_path(root / "prds" / "brd.md") == "prd"
    assert mm._type_for_path(root / "epics" / "X.md") == "epic"
