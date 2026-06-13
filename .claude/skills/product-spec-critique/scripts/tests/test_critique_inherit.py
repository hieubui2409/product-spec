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


def test_index_accepts_raw_lens_schema_keys(tmp_path):
    # Lens agents emit findings keyed by `evidence` (+ `why_it_dies`), not the
    # index-internal `evidence_id`/`why`. The indexer must accept the raw lens
    # shape, else a real critique run indexes nothing (inherit/repeat go blind).
    proj = make_proj(tmp_path)
    ci.index_report_findings(proj, "260603-0009", "PRD-AUTH",
                             [{"lens": "product", "evidence": "PRD-AUTH:10",
                               "severity": "blocker", "why_it_dies": "core value miss",
                               "fix": "do X"}])
    got = ci.build_inherited_context(proj, _graph(), "PRD-AUTH-E1")
    assert len(got) == 1
    assert got[0]["evidence_id"] == "PRD-AUTH:10"
    assert got[0]["severity"] == "blocker"
    assert got[0]["why"] == "core value miss"  # why_it_dies mapped onto why


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


# ---------------------------------------------------------------------------
# N1 — finding-level fingerprint (spec-span anchor): normalize + pure hash
# ---------------------------------------------------------------------------

def test_normalize_line_trims_case_and_markup():
    assert ci._normalize_line("  ## Hello   World ") == "hello world"
    assert ci._normalize_line("- foo BAR") == "foo bar"
    assert ci._normalize_line("owner: Jane Doe") == "owner: jane doe"


def test_normalize_line_structural_only_is_empty():
    # B1: structural-only lines (no alphanumeric) collapse to "" → no usable anchor.
    assert ci._normalize_line("---") == ""
    assert ci._normalize_line("***") == ""
    assert ci._normalize_line("___") == ""
    assert ci._normalize_line("   ") == ""
    assert ci._normalize_line(">") == ""


def test_normalize_line_keeps_numeric_content_no_overstrip():
    # Leading content digits / signs are NOT list markers → kept verbatim, so
    # distinct lines can't collide (the over-strip false-merge the reviewer caught).
    assert ci._normalize_line("5xx errors") == "5xx errors"
    assert ci._normalize_line("+10% growth") == "+10% growth"
    assert ci._normalize_line("-5 points") == "-5 points"
    assert ci._normalize_line("2026-05-28") == "2026-05-28"


def test_fingerprint_pure_stable_and_discriminating():
    base = ci._fingerprint("PRD-AUTH", "blocker", "owner: Jane Doe")
    assert base and base == ci._fingerprint("PRD-AUTH", "blocker", "  owner:  JANE doe ")
    assert base != ci._fingerprint("PRD-AUTH", "major", "owner: Jane Doe")      # 3b severity
    assert base != ci._fingerprint("PRD-OTHER", "blocker", "owner: Jane Doe")   # node
    assert base != ci._fingerprint("PRD-AUTH", "blocker", "a different line")   # text (crit 3)


def test_fingerprint_numbered_siblings_distinct():
    # "3. X" vs "7. X": distinct numbered-list siblings with identical prose must
    # NOT merge (leading list number is kept as content, not stripped).
    a = ci._fingerprint("PRD-AUTH", "blocker", "3. Xem so du")
    b = ci._fingerprint("PRD-AUTH", "blocker", "7. Xem so du")
    assert a and b and a != b


def test_fingerprint_pure_empty_normalize_is_none():
    # B1: hashing "" would collide distinct findings → return None instead.
    assert ci._fingerprint("PRD-AUTH", "blocker", "---") is None
    assert ci._fingerprint("PRD-AUTH", "blocker", "") is None


# ---------------------------------------------------------------------------
# N1 — line resolver (cited spec-line text from the live source)
# ---------------------------------------------------------------------------

def test_resolve_line_text_matches_source(tmp_path):
    proj = make_proj(tmp_path)
    g = _spec_graph().build_graph(proj)
    # PRD-AUTH → prds/auth.md; compare resolver vs a direct read (no hard-coded string).
    src = (proj / "docs" / "product" / "prds" / "auth.md").read_text(
        encoding="utf-8").splitlines()
    assert ci._resolve_line_text(proj, g, "PRD-AUTH:7") == src[6]


def test_resolve_line_text_unresolvable_is_none(tmp_path):
    proj = make_proj(tmp_path)
    g = _spec_graph().build_graph(proj)
    assert ci._resolve_line_text(proj, g, "PRD-AUTH:99999") is None  # out of range
    assert ci._resolve_line_text(proj, g, "NOPE-NODE:1") is None     # unknown node
    assert ci._resolve_line_text(proj, g, "PRD-AUTH") is None        # no :line
    assert ci._resolve_line_text(proj, g, "PRD-AUTH:x") is None      # non-int line


# ---------------------------------------------------------------------------
# N1 — write path attaches finding_fingerprint
# ---------------------------------------------------------------------------

def test_index_writes_fingerprint_for_content_line(tmp_path):
    proj = make_proj(tmp_path)
    # PRD-AUTH:7 = "owner: Jane Doe" (real content line) → non-null fingerprint.
    ci.index_report_findings(proj, "260603-0001", "PRD-AUTH", [_blocker("PRD-AUTH:7")])
    entry = critique_cache.load_index(proj)["PRD-AUTH:7@260603-0001"]
    assert entry.get("finding_fingerprint")


def test_index_goal_node_structural_line_fingerprint_none(tmp_path):
    # B2: BRD-G1 → brd.md line 1 = "---" → normalized empty → fingerprint None
    # (field present, value None) → eid fallback. No crash on the goal-node class.
    proj = make_proj(tmp_path)
    ci.index_report_findings(proj, "260603-0001", "all", [_blocker("BRD-G1:1")])
    entry = critique_cache.load_index(proj)["BRD-G1:1@260603-0001"]
    assert "finding_fingerprint" in entry and entry["finding_fingerprint"] is None


# ---------------------------------------------------------------------------
# N1 — read-path dedup by fingerprint (line-drift immunity + no false-merge)
# ---------------------------------------------------------------------------

def _row(eid, fp, severity="blocker"):
    return {"evidence_id": eid, "severity": severity, "why": "w", "fix": "f",
            "dec_worthy": False, "finding_fingerprint": fp}


def test_index_rows_dedup_same_fingerprint_line_drift(tmp_path):
    # Crit 1: same logical finding re-critiqued after a pure line shift (:5 → :7,
    # identical cited text → identical fp) collapses to ONE row, latest ts/eid kept.
    proj = make_proj(tmp_path)
    fp = "deadbeefdeadbeef"
    critique_cache.upsert_findings(proj, "260603-0001", "PRD-AUTH-E1-S1",
                                   [_row("PRD-AUTH-E1-S1:5", fp)])
    critique_cache.upsert_findings(proj, "260603-0002", "PRD-AUTH-E1-S1",
                                   [_row("PRD-AUTH-E1-S1:7", fp)])
    same = [r for r in ci._index_rows(proj) if r.get("finding_fingerprint") == fp]
    assert len(same) == 1
    assert same[0]["evidence_id"] == "PRD-AUTH-E1-S1:7"  # latest ts wins


def test_index_rows_distinct_fingerprints_kept(tmp_path):
    # Crit 2: two distinct findings on the same node (different fp) stay separate.
    proj = make_proj(tmp_path)
    critique_cache.upsert_findings(proj, "260603-0001", "PRD-AUTH-E1-S1",
                                   [_row("PRD-AUTH-E1-S1:5", "aaaa1111aaaa1111"),
                                    _row("PRD-AUTH-E1-S1:9", "bbbb2222bbbb2222")])
    s1 = [r for r in ci._index_rows(proj)
          if ci._node_of(r["evidence_id"]) == "PRD-AUTH-E1-S1"]
    assert len(s1) == 2


def test_index_rows_none_fingerprint_does_not_merge(tmp_path):
    # B1 guard: rows with fingerprint None must key by eid, NOT collapse to one
    # (a naive `key = fp` with fp=None would merge distinct findings).
    proj = make_proj(tmp_path)
    critique_cache.upsert_findings(proj, "260603-0001", "PRD-AUTH-E1-S1",
                                   [_row("PRD-AUTH-E1-S1:1", None),
                                    _row("PRD-AUTH-E1-S1:2", None)])
    s1 = [r for r in ci._index_rows(proj)
          if ci._node_of(r["evidence_id"]) == "PRD-AUTH-E1-S1"]
    assert len(s1) == 2


def test_index_rows_dedup_mixed_ts_formats_keeps_chronologically_latest(tmp_path):
    # M-2 regression: report_ts mixes filename stamps (YYMMDD) and ISO (_now()).
    # A lexicographic compare wrongly ranks "260601" above "2026-06-14T.." ('6'>'0'
    # at index 2) and keeps the STALE finding; the chronological key must keep the
    # genuinely newer ISO (June-14) finding instead.
    proj = make_proj(tmp_path)
    fp = "feedfacefeedface"
    critique_cache.upsert_findings(proj, "2026-06-14T00:00:00+00:00", "PRD-AUTH-E1-S1",
                                   [_row("PRD-AUTH-E1-S1:9", fp)])
    critique_cache.upsert_findings(proj, "260601", "PRD-AUTH-E1-S1",
                                   [_row("PRD-AUTH-E1-S1:5", fp)])
    same = [r for r in ci._index_rows(proj) if r.get("finding_fingerprint") == fp]
    assert len(same) == 1
    assert same[0]["evidence_id"] == "PRD-AUTH-E1-S1:9"  # ISO June-14 is chronologically latest


def test_rollup_blocker_count_not_inflated_by_line_drift(tmp_path):
    # Crit 1 end-to-end: one logical blocker across two re-critiques (same fp,
    # drifted line) counts ONCE in the rollup, not twice.
    proj = make_proj(tmp_path)
    fp = "cafef00dcafef00d"
    critique_cache.upsert_findings(proj, "260603-0001", "PRD-AUTH-E1-S1",
                                   [_row("PRD-AUTH-E1-S1:5", fp)])
    critique_cache.upsert_findings(proj, "260603-0002", "PRD-AUTH-E1-S1",
                                   [_row("PRD-AUTH-E1-S1:7", fp)])
    roll = ci.build_descendant_rollup(proj, _graph(), "PRD-AUTH-E1")
    bc = {b["id"]: b["blocker_count"] for b in roll["blocker_children"]}
    assert bc["PRD-AUTH-E1-S1"] == 1
