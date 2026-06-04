"""Tests for the interactive viewers `--viz board` and `--viz explorer`.

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

from spec_graph import build_graph, load_artifacts, resolve_ac  # noqa: E402
import render_ascii  # noqa: E402
import render_board  # noqa: E402
import render_explorer  # noqa: E402
import render_html  # noqa: E402

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


# ---------- goal cards carry a synthesized detail body (no empty panel) --------

def test_goal_detail_md_synthesizes_metrics_and_skips_non_goal():
    """A goal has no file body; goal_detail_md surfaces its metrics (the one field
    no badge/column already shows) so the detail panel is not empty. A non-goal node
    returns "" (caller uses the artifact body)."""
    md = render_html.goal_detail_md({"type": "goal", "metrics": ["arr", "repeat-rate"]}, "en")
    assert "**Metrics:** arr, repeat-rate" in md
    assert render_html.goal_detail_md({"type": "prd"}, "en") == ""
    # a goal with no metrics yields "" rather than a stray empty heading
    assert render_html.goal_detail_md({"type": "goal"}, "en") == ""


def test_goal_detail_md_localizes_labels():
    md = render_html.goal_detail_md({"type": "goal", "metrics": ["arr"]}, "vi")
    assert "**Chỉ số:** arr" in md


def test_board_goal_card_body_is_populated():
    """Regression: clicking a BRD goal card showed an empty panel while PRD/epic/
    story cards showed a body — goals are not in index_artifacts so bodies.get was
    "". The card now carries the synthesized goal body."""
    g, a = _ga()
    payload = render_board.build_payload(g, a, group_by="status")
    goals = [c for c in payload["cards"] if c["type"] == "goal"]
    assert goals and all(c["body"] for c in goals)
    assert any("arr" in c["body"] for c in goals)


def test_explorer_goal_item_body_is_populated():
    g, a = _ga()
    payload = render_explorer.build_payload(g, a)
    goals = [i for i in payload["items"] if i["type"] == "goal"]
    assert goals and all(i["body"] for i in goals)


# ---------- board: XSS (body + attribute) ----------

def test_board_html_neutralizes_body_breakout():
    g, a = _xss_graph_and_artifacts()
    html = render_board.assemble_board(g, a, "status", "en", False, None)
    assert "</script><script>alert(1)</script>" not in html
    assert "\\u003c/script>" in html  # the body's < was escaped in the island


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
    # story → epic → prd → goal chain encoded as parents (list) + depth.
    assert by_id["PRD-AUTH-E1-S1"]["parents"] == ["PRD-AUTH-E1"]
    assert by_id["PRD-AUTH-E1"]["parents"] == ["PRD-AUTH"]
    assert by_id["PRD-AUTH-E1-S1"]["depth"] == 3
    assert by_id["BRD-G1"]["parents"] == []  # goals are tree roots (under PRODUCT)
    assert "story" in payload["layer_order"]


# ---------- explorer: XSS (body + attribute) ----------

def test_explorer_html_neutralizes_body_breakout():
    g, a = _xss_graph_and_artifacts()
    html = render_explorer.assemble_explorer(g, a, "en", False, None)
    assert "</script><script>alert(1)</script>" not in html
    assert "\\u003c/script>" in html


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


# ---------- viewer --layers uses ARTIFACT TYPE (goal works) — Cluster A ----------

def test_board_layers_goal_keeps_goal_cards_with_type_layer():
    g, a = _ga()
    payload = render_board.build_payload(g, a, group_by="status", layers=["goal"])
    assert {c["id"] for c in payload["cards"]} == {"BRD-G1", "BRD-G2"}
    # Layer facet value = artifact type ('goal'), not the export bucket 'brd'.
    assert all(c["layer"] == "goal" for c in payload["cards"])


def test_explorer_goal_layer_value_and_tab_key():
    g, a = _ga()
    payload = render_explorer.build_payload(g, a)
    goals = [i for i in payload["items"] if i["type"] == "goal"]
    assert goals and all(i["layer"] == "goal" for i in goals)
    # Flat-tabs key comes from layer_order; 'goal' must appear so its tab fills
    # (was empty when items carried the export bucket 'brd').
    assert "goal" in payload["layer_order"]


def test_explorer_layers_goal_only_keeps_goals():
    g, a = _ga()
    payload = render_explorer.build_payload(g, a, layers=["goal"])
    assert {i["id"] for i in payload["items"]} == {"BRD-G1", "BRD-G2"}
    assert payload["layer_order"] == ["goal"]


# ---------- explorer Table depth matches Tree root after layer filter (F11) ----------

def test_explorer_depth_recomputed_after_layer_filter():
    g, a = _ga()
    # layers=goal,story prunes epic+prd → the story loses its in-set parent and
    # becomes a Tree root; its Table depth must be 0 too or the modes disagree.
    payload = render_explorer.build_payload(g, a, layers=["goal", "story"])
    by_id = {i["id"]: i for i in payload["items"]}
    s = by_id["PRD-AUTH-E1-S1"]
    assert s["parents"] == [], "story's epic is filtered out → no in-set parent"
    assert s["depth"] == 0, "Table indent must match the Tree root placement"
    assert by_id["BRD-G1"]["depth"] == 0


# ---------- ASCII explorer now honors --layers ----------

def test_ascii_explorer_honors_layers():
    g, _ = _ga()
    full = render_ascii.explorer(g)
    goal_only = render_ascii.explorer(g, layers=["goal"])
    assert goal_only != full, "--layers must no longer be silently ignored"
    assert "BRD-G1" in goal_only
    assert "PRD-AUTH-E1-S1" not in goal_only  # non-goal layers pruned


# ---------- ASCII explorer reparents orphans when goals are filtered out (Q2) ----------

def test_ascii_explorer_layers_excluding_goal_shows_orphans():
    # The goal-rooted tree() would render an empty PRODUCT header here; the
    # orphan-rooted forest must surface the surviving prd/epic/story instead
    # (matching the HTML explorer, which reparents orphans; the ASCII board is
    # flat — no hierarchy — so it is not a parallel).
    g, _ = _ga()
    out = render_ascii.explorer(g, layers=["prd", "epic", "story"])
    assert "PRD-AUTH" in out
    assert "PRD-AUTH-E1-S1" in out          # the surviving leaf is shown, not dropped
    assert "BRD-G1" not in out              # the goal layer was excluded


def test_ascii_explorer_broken_chain_reparents_story_as_root():
    # layers=goal,story prunes prd+epic → the story loses its in-set parent and is
    # rendered as a top-level root (depth 0), parity with the HTML explorer.
    g, _ = _ga()
    out = render_ascii.explorer(g, layers=["goal", "story"])
    lines = out.splitlines()
    story_line = next(l for l in lines if "PRD-AUTH-E1-S1" in l)
    # A root sits directly under PRODUCT (├──/└── with no leading indent pipes).
    assert story_line.lstrip().startswith(("├──", "└──"))
    assert not story_line.startswith(("│", " "))


def test_ascii_explorer_no_layers_still_equals_tree():
    g, _ = _ga()
    assert render_ascii.explorer(g) == render_ascii.tree(g)


def test_ascii_explorer_orphan_forest_survives_cyclic_edge():
    # The orphan-forest recursion descends arbitrary edges; a malformed cycle
    # (epic ← story AND story ← epic) must NOT loop forever — the `seen` guard
    # bounds it. Test completing at all is the assertion (an unguarded recursion
    # would hang); also assert each node renders exactly once.
    g = {
        "product": {"name": "X"},
        "nodes": [
            {"id": "PRD-A", "type": "prd", "title": "A"},
            {"id": "PRD-A-E1", "type": "epic", "title": "E"},
            {"id": "PRD-A-E1-S1", "type": "story", "title": "S"},
        ],
        "edges": [
            {"from": "PRD-A-E1", "to": "PRD-A"},          # epic child of prd
            {"from": "PRD-A-E1-S1", "to": "PRD-A-E1"},    # story child of epic
            {"from": "PRD-A-E1", "to": "PRD-A-E1-S1"},    # MALFORMED back-edge → cycle
        ],
        "risks": [],
    }
    out = render_ascii.explorer(g, layers=["prd", "epic", "story"])
    lines = out.splitlines()
    # Each node renders exactly once (the cycle's back-edge re-render is blocked).
    # endswith avoids the PRD-A-E1 vs PRD-A-E1-S1 prefix collision; the root prd
    # carries a title ("PRD-A — A") so match its line by the "PRD-A — " prefix.
    assert len([l for l in lines if l.endswith("PRD-A-E1")]) == 1       # epic, once
    assert len([l for l in lines if l.endswith("PRD-A-E1-S1")]) == 1    # story, once
    assert len([l for l in lines if "PRD-A — A" in l]) == 1             # root prd, once


# ---------- board HTML column key matches ASCII board on malformed enum ----------

def test_board_html_column_key_uses_hashable_like_ascii():
    # A PO who writes `status: [draft]` (a list) must get the SAME column key on
    # both board surfaces — bare str() and _hashable() diverged before.
    graph = {
        "product": {"name": "Acme"},
        "nodes": [{"id": "PRD-X", "type": "prd", "title": "X", "status": ["draft"]}],
        "edges": [], "risks": [],
    }
    payload = render_board.build_payload(graph, [], group_by="status")
    html_key = payload["cards"][0]["column"]
    ascii_key = render_ascii._hashable(["draft"])
    assert html_key == ascii_key, f"html {html_key!r} != ascii {ascii_key!r}"


# ---------- viewer --layers token validation (CLI exit 2) ----------

def test_cli_viewer_unknown_layer_exits_nonzero(tmp_path):
    proj = tmp_path / "p"; shutil.copytree(VALID, proj)
    r = _run_viz(proj, "--view", "board", "--format", "ascii", "--layers", "stories")
    assert r.returncode != 0
    assert "stories" in r.stderr


# ---------- explorer ac_count matches resolve_ac (validator parity) ----------

def test_explorer_ac_count_matches_resolve_ac():
    """Explorer ac_count badge must equal len(resolve_ac(frontmatter)) — the same
    rule the consistency validator uses. A list with blank/None entries must NOT
    inflate the count (the old raw-len(ac) code over-reported vs the validator)."""
    g, artifacts = _ga()
    payload = render_explorer.build_payload(g, artifacts)
    by_id = {i["id"]: i for i in payload["items"]}

    # Build a ground-truth map from the parsed artifacts via resolve_ac.
    from spec_graph import index_artifacts
    indexed = index_artifacts(artifacts)
    for aid, item in by_id.items():
        fm = (indexed.get(aid) or {}).get("frontmatter") or {}
        expected = len(resolve_ac(fm))
        assert item["ac_count"] == expected, (
            f"{aid}: explorer ac_count={item['ac_count']} "
            f"but resolve_ac gives {expected}"
        )


def test_explorer_ac_count_blank_placeholders_not_counted():
    """Blank/None AC placeholders must not inflate the ac_count badge."""
    graph = {
        "product": {"name": "Acme"},
        "nodes": [{"id": "PRD-X-E1-S1", "type": "story", "title": "S"}],
        "edges": [], "risks": [],
    }
    # Artifact with two blank/None placeholders + one real item.
    artifacts = [{
        "ok": True, "__type_hint": "story",
        "frontmatter": {
            "id": "PRD-X-E1-S1", "type": "story",
            "acceptance_criteria": [None, "", "real criterion"],
        },
        "body": "", "sections": {},
    }]
    payload = render_explorer.build_payload(graph, artifacts)
    item = next(i for i in payload["items"] if i["id"] == "PRD-X-E1-S1")
    assert item["ac_count"] == 1, (
        f"expected 1 (only 'real criterion'); got {item['ac_count']}"
    )


# ---------- board/explorer scalar coercion: list/dict horizon is "" ----------

def test_board_list_horizon_coerced_to_empty_string():
    """A list-valued horizon field (malformed YAML) must be coerced to '' in card
    data — not passed through as an array which would break the JSON island."""
    graph = {
        "product": {"name": "Acme"},
        "nodes": [{"id": "PRD-X", "type": "prd", "title": "X",
                   "status": "draft", "horizon": ["now", "next"]}],
        "edges": [], "risks": [],
    }
    payload = render_board.build_payload(graph, [], group_by="status")
    card = next(c for c in payload["cards"] if c["id"] == "PRD-X")
    assert card["horizon"] == "", f"expected '', got {card['horizon']!r}"


def test_explorer_list_horizon_coerced_to_empty_string():
    """Same as board: list-valued horizon → '' in explorer item data."""
    graph = {
        "product": {"name": "Acme"},
        "nodes": [{"id": "PRD-X", "type": "prd", "title": "X",
                   "status": "draft", "horizon": ["now"]}],
        "edges": [], "risks": [],
    }
    payload = render_explorer.build_payload(graph, [])
    item = next(i for i in payload["items"] if i["id"] == "PRD-X")
    assert item["horizon"] == "", f"expected '', got {item['horizon']!r}"


def test_board_list_status_and_moscow_coerced_to_empty_string():
    """List-valued status/moscow → '' in board card data."""
    graph = {
        "product": {"name": "Acme"},
        "nodes": [{"id": "PRD-X", "type": "prd", "title": "X",
                   "status": ["draft"], "moscow": {"must": True}}],
        "edges": [], "risks": [],
    }
    payload = render_board.build_payload(graph, [], group_by="horizon")
    card = next(c for c in payload["cards"] if c["id"] == "PRD-X")
    assert card["status"] == "", f"expected '' for list status, got {card['status']!r}"
    assert card["moscow"] == "", f"expected '' for dict moscow, got {card['moscow']!r}"


# ---------- visualize: VIEWER_LAYERS equals _BOARD_CARD_TYPES ----------

def test_viewer_layers_equals_board_card_types():
    """VIEWER_LAYERS in visualize.py must be derived from render_ascii._BOARD_CARD_TYPES
    so the two can never silently diverge."""
    sys.path.insert(0, str(SCRIPTS_DIR))
    import visualize
    from render_ascii import _BOARD_CARD_TYPES
    assert tuple(visualize.VIEWER_LAYERS) == tuple(_BOARD_CARD_TYPES), (
        f"VIEWER_LAYERS {visualize.VIEWER_LAYERS!r} != _BOARD_CARD_TYPES {_BOARD_CARD_TYPES!r}"
    )


# ---------- _load_baseline: same-second tiebreak is deterministic ----------

def test_load_baseline_same_second_tiebreak_deterministic(tmp_path):
    """Two snapshots with identical mtime must resolve deterministically by name."""
    import visualize, time as _time, json as _json

    snap_dir = tmp_path / "docs" / "product" / "visuals" / ".snapshots"
    snap_dir.mkdir(parents=True)
    # Write two snapshots with the same mtime.
    a = snap_dir / "a_snap.json"
    b = snap_dir / "b_snap.json"
    a.write_text(_json.dumps({"id": "a"}), encoding="utf-8")
    b.write_text(_json.dumps({"id": "b"}), encoding="utf-8")
    # Force identical mtime for both.
    fixed_mtime = _time.time()
    import os
    os.utime(a, (fixed_mtime, fixed_mtime))
    os.utime(b, (fixed_mtime, fixed_mtime))

    # With 2 snapshots the baseline is snaps[-2] (second-most-recent). With a
    # name tiebreak, snaps sorted by (mtime, name) → [a, b]; baseline = a.
    result = visualize._load_baseline(tmp_path, None)
    assert result == {"id": "a"}, (
        f"expected 'a' (sorted first by name), got {result!r}"
    )
