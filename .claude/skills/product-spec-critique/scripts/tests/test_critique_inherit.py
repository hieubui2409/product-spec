"""Tests for critique_inherit.py — inherited_context (parent→child) +
descendant_rollup (child→parent). Hand-built graph dict (functions take `graph`) +
a real fixture root for the index. Chain: BRD-G1 <- PRD-AUTH <- PRD-AUTH-E1 <- {S1,S2,S3}."""

import sys

from critique_test_support import make_proj
import critique_inherit as ci
import critique_cache


def _graph():
    nodes = [
        {"id": "BRD-G1", "type": "goal"},
        {"id": "PRD-AUTH", "type": "prd"},
        {"id": "PRD-AUTH-E1", "type": "epic"},
        {"id": "PRD-AUTH-E1-S1", "type": "story"},
        {"id": "PRD-AUTH-E1-S2", "type": "story"},
        {"id": "PRD-AUTH-E1-S3", "type": "story"},
    ]
    edges = [  # convention: from=child, to=parent
        {"from": "PRD-AUTH", "to": "BRD-G1"},
        {"from": "PRD-AUTH-E1", "to": "PRD-AUTH"},
        {"from": "PRD-AUTH-E1-S1", "to": "PRD-AUTH-E1"},
        {"from": "PRD-AUTH-E1-S2", "to": "PRD-AUTH-E1"},
        {"from": "PRD-AUTH-E1-S3", "to": "PRD-AUTH-E1"},
    ]
    return {"nodes": nodes, "edges": edges}


def _spec_graph():
    psp = str(ci._psp_dir())
    if psp not in sys.path:
        sys.path.insert(0, psp)
    import spec_graph
    return spec_graph


def _blocker(eid, why="w", fix="f", dec_worthy=False):
    return {"evidence_id": eid, "severity": "blocker", "why": why, "fix": fix,
            "dec_worthy": dec_worthy}


def _minor(eid):
    return {"evidence_id": eid, "severity": "minor", "why": "w", "fix": "f",
            "dec_worthy": False}


# ---------------------------------------------------------------------------
# classification
# ---------------------------------------------------------------------------

def test_classify_uses_ancestor_set_not_single_field():
    sg = _spec_graph()
    g = _graph()
    scope = "PRD-AUTH-E1-S1"
    anc = sg.ancestors(g, scope)   # {PRD-AUTH-E1, PRD-AUTH, BRD-G1}
    desc = sg.downstream(g, scope)  # {}
    # grandparent (PRD) and great-grandparent (goal) both inherited via the SET.
    assert ci._classify("PRD-AUTH:1", scope, anc, desc) == "inherited"
    assert ci._classify("BRD-G1:2", scope, anc, desc) == "inherited"
    # self + descendant → repeat; unrelated → drop.
    assert ci._classify("PRD-AUTH-E1-S1:3", scope, anc, desc) == "repeat"
    assert ci._classify("UNREL-X:1", scope, anc, desc) == "drop"


def test_classify_descendant_is_repeat():
    sg = _spec_graph()
    g = _graph()
    scope = "PRD-AUTH-E1"
    anc = sg.ancestors(g, scope)
    desc = sg.downstream(g, scope)  # {S1, S2, S3}
    assert ci._classify("PRD-AUTH-E1-S2:1", scope, anc, desc) == "repeat"


# ---------------------------------------------------------------------------
# inherited_context
# ---------------------------------------------------------------------------

def test_inherited_blockers_only_minor_dropped(tmp_path):
    proj = make_proj(tmp_path)
    ci.index_report_findings(proj, "260603-0001", "PRD-AUTH",
                             [_blocker("PRD-AUTH:10"), _minor("PRD-AUTH:30")])
    got = ci.build_inherited_context(proj, _graph(), "PRD-AUTH-E1")
    assert len(got) == 1
    assert got[0]["evidence_id"] == "PRD-AUTH:10"
    assert got[0]["source"] == "PRD-AUTH@260603-0001"
    assert got[0]["severity"] == "blocker"


def test_inherited_dec_worthy_minor_kept(tmp_path):
    proj = make_proj(tmp_path)
    ci.index_report_findings(proj, "260603-0001", "PRD-AUTH",
                             [{"evidence_id": "PRD-AUTH:5", "severity": "minor",
                               "why": "w", "fix": "f", "dec_worthy": True}])
    got = ci.build_inherited_context(proj, _graph(), "PRD-AUTH-E1")
    assert len(got) == 1 and got[0]["dec_worthy"] is True


def test_inherited_grandparent_goal(tmp_path):
    proj = make_proj(tmp_path)
    ci.index_report_findings(proj, "260603-0001", "all", [_blocker("BRD-G1:1")])
    got = ci.build_inherited_context(proj, _graph(), "PRD-AUTH-E1-S1")
    assert any(x["evidence_id"] == "BRD-G1:1" for x in got)


def test_inherited_fresh_only_drops_dead_parent(tmp_path):
    proj = make_proj(tmp_path)
    # Finding on a node NOT present in the live graph → dropped.
    ci.index_report_findings(proj, "260603-0001", "GONE", [_blocker("GONE-NODE:1")])
    got = ci.build_inherited_context(proj, _graph(), "PRD-AUTH-E1")
    assert got == []


def test_inherited_depth_nearest_vs_deep(tmp_path):
    proj = make_proj(tmp_path)
    # blockers on BOTH the epic-parent chain: PRD-AUTH (near) and BRD-G1 (far),
    # neither scope=all → nearest keeps only PRD-AUTH; deep keeps both.
    ci.index_report_findings(proj, "260603-0001", "PRD-AUTH", [_blocker("PRD-AUTH:1")])
    ci.index_report_findings(proj, "260603-0002", "BRD-G1", [_blocker("BRD-G1:1")])
    scope = "PRD-AUTH-E1"
    nearest = {x["evidence_id"] for x in
               ci.build_inherited_context(proj, _graph(), scope, depth="nearest")}
    deep = {x["evidence_id"] for x in
            ci.build_inherited_context(proj, _graph(), scope, depth="deep")}
    assert nearest == {"PRD-AUTH:1"}
    assert deep == {"PRD-AUTH:1", "BRD-G1:1"}


def test_inherited_scope_all_kept_in_nearest(tmp_path):
    proj = make_proj(tmp_path)
    # A scope=all finding on a far ancestor is kept even under nearest.
    ci.index_report_findings(proj, "260603-0001", "all", [_blocker("BRD-G1:1")])
    ci.index_report_findings(proj, "260603-0002", "PRD-AUTH", [_blocker("PRD-AUTH:1")])
    got = {x["evidence_id"] for x in
           ci.build_inherited_context(proj, _graph(), "PRD-AUTH-E1", depth="nearest")}
    assert got == {"BRD-G1:1", "PRD-AUTH:1"}


def test_inherited_empty_index_is_clean_noop(tmp_path):
    proj = make_proj(tmp_path)
    assert ci.build_inherited_context(proj, _graph(), "PRD-AUTH-E1") == []


# ---------------------------------------------------------------------------
# descendant_rollup
# ---------------------------------------------------------------------------

def test_rollup_counts_blocker_children(tmp_path):
    proj = make_proj(tmp_path)
    ci.index_report_findings(proj, "260603-0001", "PRD-AUTH-E1-S1",
                             [_blocker("PRD-AUTH-E1-S1:2")])
    ci.index_report_findings(proj, "260603-0002", "PRD-AUTH-E1-S2",
                             [_blocker("PRD-AUTH-E1-S2:4")])
    roll = ci.build_descendant_rollup(proj, _graph(), "PRD-AUTH-E1")
    assert roll["critiqued_child_count"] == 2
    assert roll["total_child_count"] == 3
    ids = {b["id"] for b in roll["blocker_children"]}
    assert ids == {"PRD-AUTH-E1-S1", "PRD-AUTH-E1-S2"}
    assert "2/2" in roll["verdict_line"]


def test_rollup_counts_clean_critiqued_child(tmp_path):
    # A child critiqued CLEAN (critique-state only, no index row) still counts
    # toward the denominator — else verdict_line is structurally always "N/N".
    proj = make_proj(tmp_path)
    ci.index_report_findings(proj, "260603-0001", "PRD-AUTH-E1-S1",
                             [_blocker("PRD-AUTH-E1-S1:2")])           # S1 blocker
    critique_cache.save_state(proj, "PRD-AUTH-E1-S1", provenance_hash="x")
    critique_cache.save_state(proj, "PRD-AUTH-E1-S2", provenance_hash="y")  # S2 clean
    roll = ci.build_descendant_rollup(proj, _graph(), "PRD-AUTH-E1")
    assert roll["critiqued_child_count"] == 2  # S1 + clean S2 both count
    assert roll["total_child_count"] == 3
    assert {b["id"] for b in roll["blocker_children"]} == {"PRD-AUTH-E1-S1"}
    assert "1/2" in roll["verdict_line"]


def test_rollup_noop_when_no_children_critiqued(tmp_path):
    proj = make_proj(tmp_path)
    assert ci.build_descendant_rollup(proj, _graph(), "PRD-AUTH-E1") == {}


def test_rollup_noop_when_scope_is_leaf(tmp_path):
    proj = make_proj(tmp_path)
    assert ci.build_descendant_rollup(proj, _graph(), "PRD-AUTH-E1-S1") == {}


# ---------------------------------------------------------------------------
# index write hook
# ---------------------------------------------------------------------------

def test_index_report_findings_round_trip(tmp_path):
    proj = make_proj(tmp_path)
    ci.index_report_findings(proj, "260603-0001", "all",
                             [_blocker("PRD-AUTH:1"), _minor("PRD-AUTH-E1:2")])
    idx = critique_cache.load_index(proj)
    # blocker stored; minor (non-DEC) NOT stored (index is lossy: blockers + DEC).
    assert "PRD-AUTH:1@260603-0001" in idx
    assert "PRD-AUTH-E1:2@260603-0001" not in idx
