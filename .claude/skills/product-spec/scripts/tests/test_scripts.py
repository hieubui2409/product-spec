"""Tests for product-spec core scripts (Phase 5).

Exercises frontmatter_parser, spec_graph, check_traceability, check_consistency,
build_traceability_matrix, generate_templates against two fixture specs:
  - valid-spec/   : clean spec; should produce zero error-severity findings
                    (warns possible)
  - broken-spec/  : seeded with orphan story, missing AC, dup ID, dangling
                    epic reference, unaddressed BRD goal
"""

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from frontmatter_parser import parse_file, parse_text  # noqa: E402
from spec_graph import build_graph, downstream  # noqa: E402
from check_traceability import check as check_trace  # noqa: E402
from check_consistency import check as check_cons, _enrich_with_ac  # noqa: E402
from build_traceability_matrix import build_matrix, build_index  # noqa: E402
from generate_templates import allocate_id, render  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"
BROKEN = FIXTURES / "broken-spec"


# ---------- frontmatter_parser ----------

def test_parse_valid_frontmatter():
    r = parse_file(VALID / "docs" / "product" / "PRODUCT.md")
    assert r["ok"]
    assert r["frontmatter"]["id"] == "PRODUCT"
    assert "Acme Shop" in r["frontmatter"]["name"]


def test_parse_text_no_frontmatter():
    r = parse_text("# Just a heading")
    assert not r["ok"]
    assert "frontmatter" in r["error"].lower() or "no YAML" in r["error"]


def test_parse_text_malformed_yaml():
    r = parse_text("---\n: : bad\n  indent\n---\nbody")
    assert not r["ok"]
    assert "YAML" in r["error"] or "parse" in r["error"].lower()


# ---------- spec_graph ----------

def test_graph_valid_spec_has_expected_nodes_and_edges():
    g = build_graph(VALID)
    ids = {n["id"] for n in g["nodes"]}
    assert {"PRODUCT", "BRD-G1", "BRD-G2", "PRD-AUTH", "PRD-AUTH-E1", "PRD-AUTH-E1-S1"} <= ids
    edges = {(e["from"], e["to"]) for e in g["edges"]}
    assert ("PRD-AUTH-E1-S1", "PRD-AUTH-E1") in edges
    assert ("PRD-AUTH-E1", "PRD-AUTH") in edges
    assert ("PRD-AUTH", "BRD-G1") in edges


def test_graph_downstream_query():
    g = build_graph(VALID)
    down = downstream(g, "PRD-AUTH")
    assert "PRD-AUTH-E1" in down
    assert "PRD-AUTH-E1-S1" in down


def test_graph_missing_product_dir():
    g = build_graph(Path("/tmp/__does_not_exist__"))
    assert g.get("missing_product_dir") is True
    assert g["nodes"] == []


# ---------- check_traceability ----------

def test_traceability_valid_has_no_errors():
    g = build_graph(VALID)
    findings = check_trace(g)
    errors = [f for f in findings if f["severity"] == "error"]
    # BRD-G2 is unaddressed but that's a warn, not an error
    assert errors == [], f"expected zero errors, got {errors}"


def test_traceability_broken_flags_dangling_link_and_unaddressed():
    g = build_graph(BROKEN)
    findings = check_trace(g)
    checks = {f["check"] for f in findings}
    assert "dangling_link" in checks, "expected dangling_link for PRD-AUTH-E9 reference"
    assert "orphan_brd_goal" in checks, "expected orphan_brd_goal for BRD-G2"


# ---------- check_consistency ----------

def test_consistency_valid_no_errors():
    g = build_graph(VALID)
    _enrich_with_ac(g, VALID)
    findings = check_cons(g)
    errors = [f for f in findings if f["severity"] == "error"]
    assert errors == [], f"expected zero errors on valid spec, got {errors}"


def test_consistency_broken_flags_dup_id_and_missing_ac():
    g = build_graph(BROKEN)
    _enrich_with_ac(g, BROKEN)
    findings = check_cons(g)
    checks = {f["check"] for f in findings}
    assert "dup_id" in checks, "expected dup_id for PRD-AUTH-E1-S1 collision"
    assert "missing_ac" in checks, "expected missing_ac for empty AC story"


# ---------- build_traceability_matrix ----------

def test_matrix_includes_story_row():
    g = build_graph(VALID)
    md = build_matrix(g)
    assert "PRD-AUTH-E1-S1" in md
    assert "PRD-AUTH-E1" in md
    assert "PRD-AUTH" in md
    assert "BRD-G1" in md


def test_matrix_index_sorted_by_type():
    g = build_graph(VALID)
    idx = build_index(g)
    types_in_order = [row["type"] for row in idx]
    assert types_in_order == sorted(types_in_order)


# ---------- generate_templates ----------

def test_allocate_id_for_new_story_under_epic():
    g = build_graph(VALID)
    new_id = allocate_id(g, "story", slug=None, parent="PRD-AUTH-E1", session_used=[])
    assert new_id == "PRD-AUTH-E1-S2"


def test_allocate_id_under_different_epic_is_independent():
    """Parent-scoped IDs: two stories under different epics both start at S1."""
    g = build_graph(VALID)
    # Simulate adding a new epic under PRD-AUTH
    new_epic = allocate_id(g, "epic", slug=None, parent="PRD-AUTH", session_used=[])
    assert new_epic == "PRD-AUTH-E2"
    # First story under PRD-AUTH-E2 starts at S1
    new_story = allocate_id(g, "story", slug=None, parent="PRD-AUTH-E2", session_used=[new_epic])
    assert new_story == "PRD-AUTH-E2-S1"


def test_render_optional_section_drop_and_keep():
    template = (
        "static head\n"
        "<!-- OPTIONAL: keep_me -->\nKEPT-BODY\n<!-- /OPTIONAL -->\n"
        "<!-- OPTIONAL: drop_me -->\nDROPPED-BODY\n<!-- /OPTIONAL -->\n"
        "tail with {{token}}"
    )
    out = render(template, {"token": "VALUE"}, keep_optional=["keep_me"])
    assert "KEPT-BODY" in out
    assert "DROPPED-BODY" not in out
    assert "VALUE" in out
    assert "{{token}}" not in out


def test_render_unknown_token_becomes_tbd():
    out = render("hello {{nope}}", values={}, keep_optional=[])
    assert "hello TBD" in out
