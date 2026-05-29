"""Tests for the Phase-1 shared assembler: spec_graph.ancestors() + the
assemble_digest digest model.

Uses the valid-spec fixture, which now carries vision.md AND brd.md (red-team
C1b): the assembler must surface Vision + BRD as prepended singletons, NOT via
the ancestor edge walk (they are not graph nodes).
"""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph, load_artifacts, ancestors  # noqa: E402
import assemble_digest  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


def _graph_and_artifacts():
    graph = build_graph(VALID)
    artifacts = load_artifacts(VALID / "docs" / "product")
    return graph, artifacts


# ---------- ancestors() ----------

def test_ancestors_returns_goal_and_prd_chain_not_vision_brd():
    graph = build_graph(VALID)
    anc = ancestors(graph, "PRD-AUTH-E1-S1")
    assert anc == {"PRD-AUTH-E1", "PRD-AUTH", "BRD-G1"}
    # Vision and the BRD container are NOT graph nodes — never reachable here.
    assert "VISION" not in anc
    assert "BRD" not in anc


def test_ancestors_of_prd_is_just_its_goal():
    graph = build_graph(VALID)
    assert ancestors(graph, "PRD-AUTH") == {"BRD-G1"}


def test_ancestors_of_top_goal_is_empty():
    graph = build_graph(VALID)
    assert ancestors(graph, "BRD-G1") == set()


# ---------- build_digest: singleton prepend ----------

def test_prd_context_digest_prepends_vision_and_brd_singletons():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="PRD-AUTH", depth="context")
    by_type = {e["type"]: e for e in digest}
    assert "vision" in by_type, "Vision singleton must be prepended"
    assert "brd" in by_type, "BRD singleton must be prepended"
    # Singletons are ancestors, compacted at --depth context.
    assert by_type["vision"]["role"] == "ancestor"
    assert by_type["vision"]["verbosity"] == "struct"
    assert by_type["brd"]["role"] == "ancestor"
    assert by_type["brd"]["verbosity"] == "struct"


def test_prd_context_digest_roles_and_verbosity():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="PRD-AUTH", depth="context")
    by_id = {e["id"]: e for e in digest}
    # target = the PRD itself, full.
    assert by_id["PRD-AUTH"]["role"] == "target"
    assert by_id["PRD-AUTH"]["verbosity"] == "full"
    # ancestor goal, compacted.
    assert by_id["BRD-G1"]["role"] == "ancestor"
    assert by_id["BRD-G1"]["verbosity"] == "struct"
    # descendants full; story carries AC.
    assert by_id["PRD-AUTH-E1"]["role"] == "descendant"
    assert by_id["PRD-AUTH-E1-S1"]["role"] == "descendant"
    assert by_id["PRD-AUTH-E1-S1"]["verbosity"] == "full"
    assert isinstance(by_id["PRD-AUTH-E1-S1"]["ac"], list)
    assert len(by_id["PRD-AUTH-E1-S1"]["ac"]) == 2


def test_all_select_includes_full_chain():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="all", depth="context")
    ids = {e["id"] for e in digest}
    for expected in ("PRD-AUTH", "PRD-AUTH-E1", "PRD-AUTH-E1-S1", "BRD-G1", "BRD-G2"):
        assert expected in ids, f"{expected} missing from --export all digest"
    types = {e["type"] for e in digest}
    assert "vision" in types and "brd" in types


# ---------- build_digest: --layers precedence + warning ----------

def test_layers_story_drops_context_and_emits_warning():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="PRD-AUTH", layers=["story"], depth="context")
    kept_types = {e["type"] for e in digest if e["type"] != "_warning"}
    # Only story-layer content survives; vision/brd/goal/prd/epic dropped.
    assert kept_types == {"story"}, f"expected only story content, got {kept_types}"
    warnings = [e for e in digest if e["role"] == "warning"]
    assert warnings, "must emit a provenance warning when --layers drops the root type"
    assert "PRD-AUTH" in warnings[0]["detail"]
    # Warning sorts to the very front.
    assert digest[0]["role"] == "warning"


def test_layers_filter_keeps_only_requested_types():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="all", layers=["prd", "epic"], depth="context")
    kept_types = {e["type"] for e in digest if e["type"] != "_warning"}
    assert kept_types <= {"prd", "epic"}
    assert "story" not in kept_types and "vision" not in kept_types


# ---------- build_digest: depth presets ----------

def test_depth_full_makes_every_entry_full():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="PRD-AUTH", depth="full")
    assert all(e["verbosity"] == "full" for e in digest if e["type"] != "_warning")


def test_depth_brief_makes_every_entry_struct():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="PRD-AUTH", depth="brief")
    assert all(e["verbosity"] == "struct" for e in digest if e["type"] != "_warning")


# ---------- determinism + shuffle independence ----------

def test_digest_is_canonical_sorted_hierarchy_order():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="all", depth="context")
    ranks = [assemble_digest.TYPE_RANK.get(e["type"], 99) for e in digest]
    assert ranks == sorted(ranks), "digest must be emitted in canonical hierarchy order"


def test_digest_independent_of_shuffled_node_order():
    graph, artifacts = _graph_and_artifacts()
    baseline = assemble_digest.build_digest(graph, artifacts, select="all", depth="context")
    # Reverse the node + edge order; a correct assembler sorts before emit.
    shuffled = dict(graph)
    shuffled["nodes"] = list(reversed(graph["nodes"]))
    shuffled["edges"] = list(reversed(graph["edges"]))
    out = assemble_digest.build_digest(shuffled, list(reversed(artifacts)), select="all", depth="context")
    proj = lambda d: [(e["id"], e["type"], e["role"], e["verbosity"]) for e in d]
    assert proj(out) == proj(baseline)


def test_digest_is_deterministic_across_calls():
    graph, artifacts = _graph_and_artifacts()
    a = assemble_digest.build_digest(graph, artifacts, select="all", depth="context")
    b = assemble_digest.build_digest(graph, artifacts, select="all", depth="context")
    assert a == b


# ---------- compact_fields ----------

def test_compact_fields_story_reports_ac_count():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="PRD-AUTH-E1-S1", depth="context")
    story = next(e for e in digest if e["id"] == "PRD-AUTH-E1-S1")
    fields = dict((k, v) for k, v in assemble_digest.compact_fields(story))
    assert "acceptance_criteria" in fields
    assert "2 item(s)" == fields["acceptance_criteria"]


def test_compact_fields_brd_lists_goal_titles():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="all", depth="brief")
    brd = next(e for e in digest if e["type"] == "brd")
    fields = dict((k, v) for k, v in assemble_digest.compact_fields(brd))
    assert "goals" in fields
    assert "ARR" in fields["goals"] or "repeat" in fields["goals"].lower()


# ---------- selection guards: no silent-empty doc (F3/F6) ----------

def test_unresolved_selection_raises_listing_bad_and_valid_ids():
    graph, artifacts = _graph_and_artifacts()
    with pytest.raises(ValueError) as exc:
        assemble_digest.build_digest(graph, artifacts, select="PRD-TYPO", depth="context")
    msg = str(exc.value)
    assert "PRD-TYPO" in msg and "PRD-AUTH" in msg  # names the bad id + the valid set


def test_partial_typo_in_list_still_raises():
    graph, artifacts = _graph_and_artifacts()
    with pytest.raises(ValueError):
        assemble_digest.build_digest(graph, artifacts, select="PRD-AUTH,NOPE", depth="context")


def test_empty_or_whitespace_selection_raises():
    graph, artifacts = _graph_and_artifacts()
    with pytest.raises(ValueError):
        assemble_digest.build_digest(graph, artifacts, select="   ", depth="context")


def test_export_all_on_empty_spec_is_allowed_empty():
    # `all` is the one selection allowed to resolve to nothing (fresh spec).
    graph = {"product": {}, "nodes": [], "edges": [], "risks": []}
    assert assemble_digest.build_digest(graph, [], select="all", depth="context") == []


# ---------- context singletons: emit-once + dedup (F4/F8) ----------

def test_export_vision_renders_vision_exactly_once():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="VISION", depth="context")
    visions = [e for e in digest if e["type"] == "vision"]
    assert len(visions) == 1, "VISION must not render twice (target + singleton dedup)"


def test_export_product_keeps_product_and_emits_no_layers_warning():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="PRODUCT", depth="context")
    assert "product" in {e["type"] for e in digest}, "PRODUCT context must survive the kept filter"
    assert not [e for e in digest if e["type"] == "_warning"], "no --layers passed → no warning"


# ---------- --layers warning collapses per-type, not per-node (F12) ----------

def test_layers_warning_is_one_per_excluded_type():
    graph, artifacts = _graph_and_artifacts()
    digest = assemble_digest.build_digest(graph, artifacts, select="all", layers=["prd"], depth="context")
    warnings = [e for e in digest if e["type"] == "_warning"]
    # goal/epic/story buckets excluded by --layers prd → one warning each.
    assert {w["id"] for w in warnings} == {"goal", "epic", "story"}
    # Two goals exist (BRD-G1/G2) but only ONE 'goal' warning (no per-node flood).
    assert len([w for w in warnings if w["id"] == "goal"]) == 1
