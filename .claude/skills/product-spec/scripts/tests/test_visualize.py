"""Tests for product-spec visualization renderers (Phase 6).

Asserts deterministic ASCII + Mermaid output; HTML assembly emits a valid
self-contained file (smoke-tested for presence of expected anchors).
"""

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
import render_ascii  # noqa: E402
import render_mermaid  # noqa: E402
import render_html  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


def _graph():
    return build_graph(VALID)


# ---------- ASCII ----------

def test_ascii_tree_contains_full_chain():
    out = render_ascii.tree(_graph())
    assert "PRODUCT" in out
    assert "BRD-G1" in out
    assert "PRD-AUTH" in out
    assert "PRD-AUTH-E1" in out
    assert "PRD-AUTH-E1-S1" in out


def test_ascii_heatmap_is_a_grid():
    out = render_ascii.heatmap(_graph())
    assert "draft" in out and "approved" in out
    assert "|" in out


def test_ascii_scope_grid_has_moscow_columns():
    out = render_ascii.scope(_graph())
    for col in ("must", "should", "could", "wont"):
        assert col in out


def test_ascii_roadmap_groups_by_horizon():
    out = render_ascii.roadmap(_graph())
    assert "NOW" in out
    assert "PRD-AUTH-E1-S1" in out


def test_ascii_persona_includes_personas():
    out = render_ascii.persona(_graph())
    assert "shopper" in out


def test_ascii_gap_marks_unaddressed_brd_goal():
    # BRD-G2 in valid fixture has no PRDs addressing it
    out = render_ascii.gap(_graph())
    assert "BRD-G2" in out


def test_ascii_moscow_quadrant_counts():
    out = render_ascii.moscow(_graph())
    assert "Must" in out and "Should" in out


def test_ascii_risk_grid_present():
    out = render_ascii.risk(_graph())
    assert "Impact" in out


def test_ascii_delta_with_no_baseline_path_renders_empty_string_via_visualize():
    # delta requires two graphs; render_ascii.delta(same, same) returns "(no changes)"
    g = _graph()
    out = render_ascii.delta(g, g)
    assert "(no changes)" in out


# ---------- Mermaid ----------

def test_mermaid_tree_emits_flowchart_block():
    out = render_mermaid.tree(_graph())
    assert out.startswith("```mermaid")
    assert "flowchart TB" in out


def test_mermaid_scope_emits_quadrantchart():
    out = render_mermaid.scope(_graph())
    assert "quadrantChart" in out


def test_mermaid_roadmap_emits_timeline():
    out = render_mermaid.roadmap(_graph())
    assert "timeline" in out


def test_mermaid_gap_uses_classdef():
    out = render_mermaid.gap(_graph())
    assert "classDef" in out


# ---------- HTML ----------

def test_html_assemble_is_self_contained_string():
    g = _graph()
    mermaid_text = render_mermaid.tree(g)
    html = render_html.assemble("tree", "mermaid", mermaid_text, g)
    assert "<!DOCTYPE html>" in html
    assert "<div class=\"mermaid\">" in html
    assert "flowchart TB" in html
    # vendored mermaid OR CDN-fallback note
    assert ("mermaid.initialize" in html) or ("falling back to CDN" in html)


def test_html_escapes_pre_content_when_format_is_pre():
    g = _graph()
    html = render_html.assemble("heatmap", "ascii", "<script>alert(1)</script>", g)
    assert "&lt;script&gt;" in html
    assert "<script>alert(1)" not in html
