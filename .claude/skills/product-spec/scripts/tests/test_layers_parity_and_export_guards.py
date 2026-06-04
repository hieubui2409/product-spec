"""Regression tests: --layers fail-loud parity (export + viewers), explorer
multi-parent rendering, ASCII/HTML explorer --filter-wont parity, YAML-safe
export frontmatter, story acceptance-criteria rendering, i18n export title,
persona --filter-wont in mermaid, and the shared parent/diff graph helpers.
"""

import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import assemble_digest  # noqa: E402
import render_export  # noqa: E402
import render_ascii  # noqa: E402
import render_mermaid  # noqa: E402
import render_explorer  # noqa: E402
import render_board  # noqa: E402
import visualize  # noqa: E402
import spec_graph  # noqa: E402
from i18n_labels import label  # noqa: E402
from spec_graph import build_graph, load_artifacts  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


# ---------- small in-memory graph/artifact builders ----------

def _node(nid, ntype, **kw):
    n = {"id": nid, "type": ntype, "title": kw.get("title", nid + " title"),
         "status": kw.get("status"), "scope": kw.get("scope"), "moscow": kw.get("moscow"),
         "horizon": kw.get("horizon"), "personas": kw.get("personas", []),
         "brd_goals": kw.get("brd_goals", []), "epic": kw.get("epic"),
         "prd": kw.get("prd"), "owner": kw.get("owner")}
    return n


def _graph(nodes, edges, product=None):
    return {"product": product or {"name": "Acme"}, "nodes": nodes, "edges": edges,
            "risks": [], "parse_errors": []}


def _art(aid, atype, body="", ac=None):
    fm = {"id": aid, "type": atype}
    if ac is not None:
        fm["acceptance_criteria"] = ac
    return {"ok": True, "frontmatter": fm, "body": body, "__type_hint": atype}


# ---------- shared graph helpers (spec_graph) ----------

def test_parents_of_drops_self_edge():
    # A self-loop (A->A) must not make A its own tree parent — that is what hangs
    # the client; build_edges has no from==to guard so the helper drops it here.
    g = _graph([_node("A", "epic"), _node("B", "story")],
               [{"from": "A", "to": "A"}, {"from": "B", "to": "A"}])
    p = spec_graph.parents_of(g)
    assert p.get("A", []) == []          # self-edge dropped
    assert p.get("B") == ["A"]


def test_parents_of_keeps_all_goals_for_multigoal_prd():
    g = _graph([_node("PRD-X", "prd", brd_goals=["G1", "G2"])],
               [{"from": "PRD-X", "to": "G1"}, {"from": "PRD-X", "to": "G2"}])
    assert spec_graph.parents_of(g)["PRD-X"] == ["G1", "G2"]


def test_diff_graphs_added_removed_and_product_changes():
    cur = _graph([_node("A", "prd"), _node("B", "epic")], [], product={"name": "New", "personas": ["X"]})
    base = _graph([_node("A", "prd")], [], product={"name": "Old", "personas": []})
    d = spec_graph.diff_graphs(cur, base)
    assert d["added"] == ["B"] and d["removed"] == []
    assert "name" in d["product_changes"] and "personas" in d["product_changes"]


# ---------- export --layers fail-loud (Q1) ----------

def test_export_all_layers_filtering_existing_content_raises():
    # `--export all --layers vision` on a spec WITH content but NO vision must fail
    # loud (was a silently-written frontmatter-only doc, exit 0).
    g = _graph([_node("PRD-X", "prd")], [])
    with pytest.raises(ValueError):
        assemble_digest.build_digest(g, [], select="all", layers=["vision"])


def test_export_all_on_genuinely_empty_spec_allowed_empty():
    g = _graph([], [])
    assert assemble_digest.build_digest(g, [], select="all", layers=["vision"]) == []


# ---------- export VISION/PRODUCT resolves without an id: (literal match) ----------

def test_resolve_selection_matches_vision_literal_without_id():
    g = _graph([_node("<missing-id>", "vision")], [])
    spec, singles, unresolved = assemble_digest._resolve_selection("VISION", g)
    assert singles == {"vision"} and unresolved == []


# ---------- --layers exclusion warning partitions surfaced vs absent ----------

def test_layers_warning_splits_surfaced_and_absent_goals():
    # valid-spec: BRD-G1 has PRD-AUTH (surfaced via prd sub-layer); BRD-G2 has no
    # PRD (absent entirely). The warning must say both, not claim G2 is surfaced.
    graph = build_graph(VALID)
    artifacts = load_artifacts(VALID / "docs" / "product")
    digest = assemble_digest.build_digest(graph, artifacts, select="all", layers=["prd"], depth="context")
    warn = next(e for e in digest if e["type"] == "_warning" and e["id"] == "goal")
    assert "appear only via" in warn["detail"] and "BRD-G1" in warn["detail"]
    assert "absent entirely" in warn["detail"] and "BRD-G2" in warn["detail"]


# ---------- YAML-safe export frontmatter ----------

@pytest.mark.parametrize("name", ["Acme: The Shop", "Acme #1 Shop", "Line1\n---\nLine2", 'Acme "Pro"'])
def test_export_frontmatter_is_valid_yaml_for_special_names(name):
    doc = render_export.render_markdown_doc([], name, "all", "context", "all", "struct", "2026-01-01T00:00:00Z")
    fm_text = doc.split("---\n", 2)[1]
    assert yaml.safe_load(fm_text)["product"] == name


def test_export_html_body_strip_survives_newline_in_product_name():
    # A newline in the name must NOT inject a stray \n---\n that makes the HTML
    # body strip cut early and eat real frontmatter into the body.
    doc = render_export.render_markdown_doc([], "Line1\n---\nLine2", "all", "context", "all", "struct", "")
    stripped = render_export._strip_frontmatter(doc)
    assert "export: all" not in stripped  # frontmatter fully stripped, not leaked


# ---------- story acceptance criteria rendering ----------

def test_bodyless_story_full_renders_ac_once():
    entry = {"id": "S", "type": "story", "verbosity": "full", "body": "", "ac": ["Alpha", "Beta"]}
    out = render_export._section_body(entry, "struct")
    assert out.count("Alpha") == 1 and "**Acceptance criteria:**" in out
    assert "acceptance_criteria" not in out  # struct-skeleton AC count must not also appear


def test_llm_compact_body_present_story_includes_ac_and_escapes_arrow():
    entry = {"id": "S", "type": "story", "verbosity": "struct",
             "body": "Narrative with --> arrow", "ac": ["Alpha", "Beta"]}
    out = render_export._section_body(entry, "llm")
    assert "Narrative" in out and "Alpha" in out and "**Acceptance criteria:**" in out
    inner = out.split("-->\n", 1)[1].rsplit("\n<!-- /COMPACT", 1)[0]  # between markers
    assert "-->" not in inner  # body arrow neutralized so it can't close the region


# ---------- export HTML title localized ----------

def test_export_html_title_localized_vi():
    graph = build_graph(VALID)
    html = render_export.render_html_doc("body", graph, "2026-01-01T00:00:00Z", lang="vi")
    assert "Xuất đặc tả" in html and "Spec Export" not in html


# ---------- explorer multi-parent (HTML matches ASCII tree) ----------

def test_explorer_payload_multigoal_prd_lists_all_goals():
    nodes = [_node("G1", "goal"), _node("G2", "goal"), _node("PRD-X", "prd", brd_goals=["G1", "G2"])]
    edges = [{"from": "PRD-X", "to": "G1"}, {"from": "PRD-X", "to": "G2"}]
    g = _graph(nodes, edges)
    arts = [_art("G1", "goal"), _art("G2", "goal"), _art("PRD-X", "prd")]
    payload = render_explorer.build_payload(g, arts)
    prd = next(i for i in payload["items"] if i["id"] == "PRD-X")
    assert sorted(prd["parents"]) == ["G1", "G2"]  # under BOTH goals, not just the first


# ---------- ASCII explorer --filter-wont parity (no-layers + layers) ----------

def _deferred_chain_graph():
    # goal -> prd -> epic(moscow=wont) -> story(moscow=must); ids chosen so the
    # deferred epic id is NOT a substring of the kept story id (clean assertions).
    nodes = [_node("GOAL1", "goal"), _node("PRD1", "prd", brd_goals=["GOAL1"]),
             _node("EPICW", "epic", prd="PRD1", moscow="wont"),
             _node("STORYK", "story", epic="EPICW", moscow="must")]
    edges = [{"from": "PRD1", "to": "GOAL1"}, {"from": "EPICW", "to": "PRD1"},
             {"from": "STORYK", "to": "EPICW"}]
    return _graph(nodes, edges, product={"name": "P"})


def test_ascii_explorer_no_layers_filter_wont_reparents_kept_child():
    g = _deferred_chain_graph()
    out = render_ascii.explorer(g, filter_wont=True)
    assert "STORYK" in out          # kept story survives (reparented), not dropped
    assert "EPICW" not in out       # the deferred epic is hidden


def test_ascii_explorer_layers_filter_wont_reparents_kept_child():
    g = _deferred_chain_graph()
    out = render_ascii.explorer(g, layers=["epic", "story"], filter_wont=True)
    assert "STORYK" in out


# ---------- viewer --layers empty-after-filter fail-loud (Q1, parity) ----------

def test_viewer_layers_empty_after_filter_exits_2(tmp_path):
    g = _graph([_node("BRD-G1", "goal")], [])  # only a goal; --layers prd matches nothing
    rc = visualize._dispatch_body_view("board", "ascii", tmp_path, g, [], "en", False, ["prd"], "status")
    assert rc == 2


def test_viewer_no_layers_empty_is_allowed(tmp_path, capsys):
    g = _graph([_node("BRD-G1", "goal")], [])
    rc = visualize._dispatch_body_view("board", "ascii", tmp_path, g, [], "en", False, None, "status")
    assert rc == 0  # no --layers → allowed (mirrors --export all on a fresh spec)


# ---------- persona --filter-wont parity (mermaid honors it) ----------

def test_llm_compact_bodyless_story_renders_ac_once():
    """A bodyless story under --compact-mode llm must show its AC exactly once — not
    the struct-skeleton count AND the explicit list (the llm branch had a sibling
    gap where AC could render twice)."""
    entry = {"id": "S", "type": "story", "verbosity": "struct", "body": "", "ac": ["Alpha", "Beta"]}
    out = render_export._section_body(entry, "llm")
    assert out.count("**Acceptance criteria:**") == 1
    assert "acceptance_criteria" not in out          # no struct-skeleton AC count
    assert out.count("Alpha") == 1


def test_export_body_h1_localized_and_newline_collapsed():
    vi = render_export.render_markdown_doc([], "Acme", "all", "context", "all", "struct", "", lang="vi")
    assert "# Xuất đặc tả — Acme" in vi               # body H1 localizes like the chrome title
    multiline = render_export.render_markdown_doc([], "Line1\n---\nLine2", "all", "context", "all", "struct", "")
    h1 = next(l for l in multiline.splitlines() if l.startswith("# "))
    assert "Line1" in h1 and "Line2" in h1            # name collapsed onto one heading line


def test_horizon_facet_label_localized_and_shipped():
    assert label("horizon", "en") == "Horizon"
    assert label("horizon", "vi") == "Khung thời gian"
    g = _graph([_node("PRD-X", "prd", horizon="now")], [])
    payload = render_board.build_payload(g, [_art("PRD-X", "prd")], group_by="status", lang="vi")
    assert payload["labels"].get("horizon") == "Khung thời gian"  # ships so client header resolves it


def test_children_of_mirrors_parents_and_drives_downstream():
    g = _graph([], [{"from": "S", "to": "E"}, {"from": "E", "to": "P"}])
    assert spec_graph.children_of(g) == {"E": ["S"], "P": ["E"]}
    assert spec_graph.downstream(g, "P") == {"E", "S"}
    assert spec_graph.ancestors(g, "S") == {"E", "P"}


def test_persona_mermaid_honors_filter_wont():
    nodes = [_node("PRD-W", "prd", moscow="wont", personas=["Shopper"]),
             _node("PRD-W-E1", "epic", prd="PRD-W"),
             _node("PRD-W-E1-S1", "story", epic="PRD-W-E1", personas=["Shopper"])]
    edges = [{"from": "PRD-W-E1", "to": "PRD-W"}, {"from": "PRD-W-E1-S1", "to": "PRD-W-E1"}]
    g = _graph(nodes, edges, product={"name": "P", "personas": ["Shopper"]})
    assert "PRD-W" in render_mermaid.persona(g, filter_wont=False)
    assert "PRD-W" not in render_mermaid.persona(g, filter_wont=True)
