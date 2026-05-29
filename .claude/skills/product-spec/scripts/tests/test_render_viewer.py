"""Phase 4/5 tests: F2 interactive viewers `--viz board` and `--viz explorer`.

Both render artifact bodies CLIENT-SIDE: the server emits an inert JSON island,
the client builds metadata via safe DOM APIs (textContent/dataset) and bodies via
the sanitize chokepoint. These tests assert the SERVER guarantees — inert island,
no breakout, no <pre>/Mermaid mis-routing, deterministic ascii fallback.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph, load_artifacts  # noqa: E402
import render_ascii  # noqa: E402
import render_board  # noqa: E402
import render_explorer  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


def _ga():
    return build_graph(VALID), load_artifacts(VALID / "docs" / "product")


def _xss_graph_and_artifacts():
    title_payload = "<img src=x onerror=alert(1)>"
    persona_payload = '"><script>alert(1)</script>'
    graph = {
        "product": {"name": "Acme", "personas": [persona_payload]},
        "nodes": [{
            "id": "PRD-X", "type": "prd", "title": title_payload, "status": "draft",
            "moscow": "must", "horizon": "now", "personas": [persona_payload], "brd_goals": [],
        }],
        "edges": [], "risks": [],
    }
    artifacts = [{
        "ok": True, "__type_hint": "prd",
        "frontmatter": {"id": "PRD-X", "type": "prd"},
        "body": "</script><script>alert(1)</script>", "sections": {},
    }]
    return graph, artifacts


# ---------- board: ASCII determinism + grouping ----------

def test_board_ascii_is_deterministic():
    g, _ = _ga()
    assert render_ascii.board(g, "status") == render_ascii.board(g, "status")


def test_board_ascii_groups_by_status_horizon_moscow():
    g, _ = _ga()
    assert "### draft" in render_ascii.board(g, "status")
    assert "### now" in render_ascii.board(g, "horizon").lower() or "Now" in render_ascii.board(g, "horizon")
    out_m = render_ascii.board(g, "moscow")
    assert "Must" in out_m
    # Goals have no moscow → bucket into the unassigned column.
    assert "unassigned" in out_m


def test_board_ascii_layers_filters_cards():
    g, _ = _ga()
    out = render_ascii.board(g, "status", layers=["story"])
    assert "PRD-AUTH-E1-S1" in out
    assert "PRD-AUTH-E1" not in out.replace("PRD-AUTH-E1-S1", "")  # only the story survives


# ---------- board: html structure ----------

def test_board_html_has_columns_cards_and_no_pre_or_mermaid():
    g, a = _ga()
    html = render_board.assemble_board(g, a, "status", "en", False, None)
    assert "<!DOCTYPE html>" in html
    assert 'id="ps-spec-data"' in html
    # Card ids travel in the inert JSON island.
    assert "PRD-AUTH-E1-S1" in html
    # NOT a <pre> dump and NOT routed through the Mermaid wrapper.
    assert '<div class="mermaid">' not in html
    assert "psRenderMarkdown" in html


def test_board_payload_groups_and_columns():
    g, a = _ga()
    payload = render_board.build_payload(g, a, group_by="status")
    assert payload["columns"][:3] == ["draft", "review", "approved"]
    ids = {c["id"] for c in payload["cards"]}
    assert "PRD-AUTH" in ids and "PRD-AUTH-E1-S1" in ids


def test_board_payload_missing_group_field_buckets_unassigned():
    g, a = _ga()
    payload = render_board.build_payload(g, a, group_by="moscow")
    # goals (no moscow) bucket into the unassigned column.
    assert "unassigned" in payload["columns"]


# ---------- board: XSS (body + attribute) ----------

def test_board_html_neutralizes_body_breakout():
    g, a = _xss_graph_and_artifacts()
    html = render_board.assemble_board(g, a, "status", "en", False, None)
    assert "</script><script>alert(1)</script>" not in html
    assert "<\\/script>" in html  # the body's </ was escaped in the island


def test_board_attribute_payload_only_inert_inside_json_island():
    g, a = _xss_graph_and_artifacts()
    html = render_board.assemble_board(g, a, "status", "en", False, None)
    start = html.index('id="ps-spec-data"')
    end = html.index("</script>", start)
    outside = html[:start] + html[end:]
    # The title/persona payloads must NOT appear as live markup outside the island.
    assert "<img src=x onerror=alert(1)>" not in outside
    assert '"><script>alert(1)</script>' not in outside
    # Client builds metadata via safe DOM APIs (auto-escaping), not string concat.
    assert "textContent" in html and ".dataset" in html


# ---------- board: CLI dispatch ----------

def _run_viz(proj, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "visualize.py"), "--root", str(proj), *extra],
        capture_output=True, text=True,
    )


def test_cli_board_default_format_is_html(tmp_path):
    proj = tmp_path / "p"; shutil.copytree(VALID, proj)
    r = _run_viz(proj, "--view", "board")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["written"].endswith(".html")
    assert sorted((proj / "docs/product/visuals").glob("board-*.html"))


def test_cli_board_mermaid_falls_back_to_ascii(tmp_path):
    proj = tmp_path / "p"; shutil.copytree(VALID, proj)
    r = _run_viz(proj, "--view", "board", "--format", "mermaid")
    assert r.returncode == 0, r.stderr  # no AttributeError on getattr(render_mermaid,'board')
    assert "## BOARD" in r.stdout
    assert "no Mermaid form" in r.stderr


def test_cli_board_group_by_reaches_renderer(tmp_path):
    proj = tmp_path / "p"; shutil.copytree(VALID, proj)
    r = _run_viz(proj, "--view", "board", "--format", "ascii", "--group-by", "moscow")
    assert r.returncode == 0, r.stderr
    assert "— moscow" in r.stdout


# ---------- explorer: ASCII fallback == tree ----------

def test_explorer_ascii_equals_tree():
    g, _ = _ga()
    assert render_ascii.explorer(g) == render_ascii.tree(g)


# ---------- explorer: html has all three modes + toggle + search ----------

def test_explorer_html_has_three_modes_toggle_and_search():
    g, a = _ga()
    html = render_explorer.assemble_explorer(g, a, "en", False, None)
    for root in ('id="ps-view-tree"', 'id="ps-view-tabs"', 'id="ps-view-table"'):
        assert root in html, f"missing mode container {root}"
    assert 'id="ps-modes"' in html          # mode toggle bar
    assert 'id="ps-search"' in html          # shared search
    assert 'treegrid' in html                # table-tree mode (CSS class + role set client-side)
    assert 'localStorage' in html            # persists last mode
    assert '<div class="mermaid">' not in html
    assert "psRenderMarkdown" in html


def test_explorer_payload_carries_hierarchy():
    g, a = _ga()
    payload = render_explorer.build_payload(g, a)
    by_id = {i["id"]: i for i in payload["items"]}
    # story → epic → prd → goal chain encoded as parent + depth.
    assert by_id["PRD-AUTH-E1-S1"]["parent"] == "PRD-AUTH-E1"
    assert by_id["PRD-AUTH-E1"]["parent"] == "PRD-AUTH"
    assert by_id["PRD-AUTH-E1-S1"]["depth"] == 3
    assert by_id["BRD-G1"]["parent"] == ""  # goals are tree roots (under PRODUCT)
    assert "story" in payload["layer_order"]


# ---------- explorer: XSS (body + attribute) ----------

def test_explorer_html_neutralizes_body_breakout():
    g, a = _xss_graph_and_artifacts()
    html = render_explorer.assemble_explorer(g, a, "en", False, None)
    assert "</script><script>alert(1)</script>" not in html
    assert "<\\/script>" in html


def test_explorer_attribute_payload_only_inert_inside_island():
    g, a = _xss_graph_and_artifacts()
    html = render_explorer.assemble_explorer(g, a, "en", False, None)
    start = html.index('id="ps-spec-data"')
    end = html.index("</script>", start)
    outside = html[:start] + html[end:]
    assert "<img src=x onerror=alert(1)>" not in outside
    assert '"><script>alert(1)</script>' not in outside
    assert "textContent" in html


# ---------- explorer: CLI dispatch ----------

def test_cli_explorer_default_html_and_layers(tmp_path):
    proj = tmp_path / "p"; shutil.copytree(VALID, proj)
    r = _run_viz(proj, "--view", "explorer", "--layers", "prd,epic")
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["written"].endswith(".html")


def test_cli_explorer_mermaid_falls_back_to_tree(tmp_path):
    proj = tmp_path / "p"; shutil.copytree(VALID, proj)
    r = _run_viz(proj, "--view", "explorer", "--format", "mermaid")
    assert r.returncode == 0, r.stderr
    assert "PRODUCT:" in r.stdout            # ascii tree fallback
    assert "no Mermaid form" in r.stderr
