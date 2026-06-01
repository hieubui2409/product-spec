"""Tests for the per-node body_hash and the shared changed-field rule.

body_hash is the cache key the memory layer depends on, and it closes the
latent impact-pass gap where a body-only edit (frontmatter unchanged) went
undetected. The changed-field rule lives in exactly one home —
spec_graph.CHANGED_FIELDS + spec_graph.changed_nodes — so the --viz delta
surface and the --validate impact-pass cannot drift apart.
"""

import hashlib
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import (  # noqa: E402
    build_graph,
    CHANGED_FIELDS,
    changed_nodes,
)
import render_ascii  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


def _node(graph, node_id):
    for n in graph["nodes"]:
        if n["id"] == node_id:
            return n
    raise AssertionError(f"node {node_id} not in graph")


def _sha8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


# ---------- Test 1: node carries a deterministic body_hash ----------

def test_node_carries_body_hash():
    """Every artifact node carries body_hash == sha256(body)[:8], and the same
    spec built twice yields the same hash (deterministic cache key)."""
    g1 = build_graph(VALID)
    g2 = build_graph(VALID)
    story1 = _node(g1, "PRD-AUTH-E1-S1")
    story2 = _node(g2, "PRD-AUTH-E1-S1")
    assert isinstance(story1["body_hash"], str)
    assert len(story1["body_hash"]) == 8
    assert story1["body_hash"] == story2["body_hash"], "hash must be deterministic"

    # Recompute against the artifact's actual body to prove the formula.
    from frontmatter_parser import parse_file
    body = parse_file(VALID / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md")["body"] or ""
    assert story1["body_hash"] == _sha8(body)


# ---------- Test 2: body_hash changes when only the body changes ----------

def test_body_hash_changes_with_body(tmp_path):
    """Edit the body only (frontmatter byte-identical) → body_hash differs."""
    import shutil
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    story_path = proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md"

    before = build_graph(proj)
    hash_before = _node(before, "PRD-AUTH-E1-S1")["body_hash"]

    text = story_path.read_text(encoding="utf-8")
    story_path.write_text(text + "\n\nAn extra clarifying paragraph.\n", encoding="utf-8")

    after = build_graph(proj)
    hash_after = _node(after, "PRD-AUTH-E1-S1")["body_hash"]

    assert hash_before != hash_after, "body-only edit must change body_hash"


# ---------- Test 3: goal node has body_hash None, no crash ----------

def test_goal_node_body_hash_none():
    """Goals are expanded from brd.md and have no standalone body, so their
    body_hash is None (back-compat). Building the graph must not crash."""
    graph = build_graph(VALID)
    goals = [n for n in graph["nodes"] if n["type"] == "goal"]
    assert goals, "valid-spec must contain at least one goal"
    for g in goals:
        assert g["body_hash"] is None


# ---------- Test 4: old snapshot lacking body_hash → not a body change ----------

def test_old_snapshot_without_body_hash():
    """changed_nodes against a baseline node-dict that has NO body_hash key must
    not mark the node changed on body grounds (unknown baseline) and must not
    raise KeyError."""
    current = {
        "nodes": [
            {"id": "PRD-X", "status": "draft", "scope": "in", "moscow": "must",
             "horizon": "now", "size": "S", "body_hash": "aaaaaaaa"},
        ],
    }
    previous = {
        "nodes": [
            # Pre-upgrade snapshot: identical frontmatter, body_hash key absent.
            {"id": "PRD-X", "status": "draft", "scope": "in", "moscow": "must",
             "horizon": "now", "size": "S"},
        ],
    }
    changed = changed_nodes(current, previous)
    assert changed == [], "absent baseline body_hash must not count as a body change"


# ---------- Test 5: changed_nodes detects body-only + frontmatter changes ----------

def test_changed_nodes_detects_body_only_change():
    """changed_nodes returns the id whose body_hash differs, and still catches a
    frontmatter-only change on the legacy fields (regression lock)."""
    base = {"id": "PRD-X", "status": "draft", "scope": "in", "moscow": "must",
            "horizon": "now", "size": "S", "body_hash": "11111111"}

    # body-only change
    cur_body = {**base, "body_hash": "22222222"}
    previous = {"nodes": [base]}
    current = {"nodes": [cur_body]}
    assert changed_nodes(current, previous) == ["PRD-X"]

    # frontmatter-only change (body_hash identical) still caught
    cur_status = {**base, "status": "approved"}
    current_fm = {"nodes": [cur_status]}
    assert changed_nodes(current_fm, previous) == ["PRD-X"]

    # no change at all
    current_same = {"nodes": [dict(base)]}
    assert changed_nodes(current_same, previous) == []

    # CHANGED_FIELDS must include body_hash + the 5 legacy fields
    assert "body_hash" in CHANGED_FIELDS
    for f in ("status", "scope", "moscow", "horizon", "size"):
        assert f in CHANGED_FIELDS


# ---------- Test 6: first post-upgrade --validate does not flood ----------

def test_first_validate_no_flood():
    """A baseline snapshot missing body_hash on EVERY node must NOT make
    changed_nodes return the whole spec — only nodes with a real frontmatter
    diff. Avoids an impact-flood on the first post-upgrade --validate."""
    # current: every node now carries a body_hash; node B also changed status.
    current = {
        "nodes": [
            {"id": "A", "status": "draft", "scope": "in", "moscow": "must",
             "horizon": "now", "size": "S", "body_hash": "aaaa1111"},
            {"id": "B", "status": "approved", "scope": "in", "moscow": "must",
             "horizon": "now", "size": "M", "body_hash": "bbbb2222"},
            {"id": "C", "status": "draft", "scope": "out", "moscow": "could",
             "horizon": "later", "size": "L", "body_hash": "cccc3333"},
        ],
    }
    # previous (pre-upgrade): no body_hash anywhere; only B's status differs.
    previous = {
        "nodes": [
            {"id": "A", "status": "draft", "scope": "in", "moscow": "must",
             "horizon": "now", "size": "S"},
            {"id": "B", "status": "draft", "scope": "in", "moscow": "must",
             "horizon": "now", "size": "M"},
            {"id": "C", "status": "draft", "scope": "out", "moscow": "could",
             "horizon": "later", "size": "L"},
        ],
    }
    changed = changed_nodes(current, previous)
    assert changed == ["B"], f"only the real frontmatter diff should flag, got {changed}"


# ---------- Test 7: --viz delta surfaces a body-only edit ----------

def test_delta_uses_body_hash():
    """render_ascii.delta() must render a body-only edit as a changed line,
    proving the single shared changed-field rule reaches the delta surface."""
    base = {"id": "PRD-X", "status": "draft", "scope": "in", "moscow": "must",
            "horizon": "now", "size": "S", "body_hash": "deadbeef"}
    baseline = {"nodes": [base], "edges": [], "product": {}}
    current = {"nodes": [{**base, "body_hash": "feedface"}], "edges": [], "product": {}}

    out = render_ascii.delta(current, baseline)
    assert "PRD-X" in out
    assert "body_hash" in out
    assert out != "(no changes)", "body-only edit must not render as no-change"
