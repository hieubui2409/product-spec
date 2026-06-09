"""Tests for the `--learn` outcome views: load_outcomes (the join) + render_outcomes
(scorecard / insight-gap / outcome-trend, ASCII + HTML).

The HTML path is the historical XSS sink, so the suite pins the escape contract:
a `<script>` / `"` in any spec-derived field (note/source/metric/title) must come
out escaped, never as a raw payload.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import load_outcomes  # noqa: E402
import render_outcomes  # noqa: E402
import render_learning  # noqa: E402
from record_outcome import append_alloc  # noqa: E402

_BRD = """---
id: BRD
type: brd
status: approved
lang: en
owner: Jane
version: 1.0.0
created: 2026-01-01
updated: 2026-01-01
goals:
  - id: BRD-G1
    title: "Reach $2M GMV"
    metrics: [gmv-year1]
    status: approved
    owner: Jane
  - id: BRD-G2
    title: "Keep payout latency under 3 days"
    metrics: [payout-latency-days]
    status: approved
    owner: Mara
  - id: BRD-G3
    title: "Launch mobile"
    metrics: [mobile-mau]
    status: review
    owner: Devon
---
# BRD
"""


def _proj(tmp_path: Path) -> Path:
    p = tmp_path / "docs" / "product"
    p.mkdir(parents=True)
    (p / "brd.md").write_text(_BRD, encoding="utf-8")
    return tmp_path


def _rec(root, **kw):
    kw.setdefault("unit", ""); kw.setdefault("direction", "higher")
    kw.setdefault("source", ""); kw.setdefault("verdict", None)
    kw.setdefault("note", ""); kw.setdefault("force", False)
    return append_alloc(root, **kw)


# ---------- load_outcomes ----------

def test_latest_is_max_id_on_same_date(tmp_path):
    root = _proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="gmv-year1", target="100", actual="40",
         measured_on="2026-05-31")  # OUT-1 miss
    _rec(root, goal="BRD-G1", metric="gmv-year1", target="100", actual="95",
         measured_on="2026-05-31")  # OUT-2 hit, same date → latest
    data = load_outcomes.load_outcomes(root)
    card = next(c for c in data["cards"] if c["goal_id"] == "BRD-G1")
    assert card["latest"]["id"] == "OUT-2"
    assert card["latest"]["verdict"] == "hit"


def test_blind_spot_for_unmeasured_goal(tmp_path):
    root = _proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="gmv-year1", target="100", actual="95",
         measured_on="2026-05-31")
    data = load_outcomes.load_outcomes(root)
    blind = [c for c in data["cards"] if c["blind_spot"]]
    assert {c["goal_id"] for c in blind} == {"BRD-G2", "BRD-G3"}


def test_orphan_goal_renders_not_crash(tmp_path):
    root = _proj(tmp_path)
    out = root / "docs" / "product" / "outcomes.md"
    out.write_text(
        "# Outcome Register\n\n---\nid: OUT-1\ngoal: BRD-GHOST\nmetric: x\n"
        "target: 100\nactual: 50\nunit: \ndirection: higher\nmeasured_on: 2026-05-31\n"
        "source: \nverdict: miss\n---\n\n## OUT-1 — x @ 2026-05-31\n\n\n",
        encoding="utf-8")
    data = load_outcomes.load_outcomes(root)
    orphan = next(c for c in data["cards"] if c["goal_id"] == "BRD-GHOST")
    assert orphan["orphan"] is True
    # renders without crashing, marks the goal as removed
    html = render_outcomes.scorecard_html(data, lang="en")
    assert "goal removed" in html


def test_gap_formula_lower_is_better_exceeds_target(tmp_path):
    root = _proj(tmp_path)
    # latency 2 days vs 3-day target (lower-is-better, BEAT target) → gap clamped to 0.
    _rec(root, goal="BRD-G2", metric="payout-latency-days", target="3", actual="2",
         direction="lower", measured_on="2026-05-31")
    data = load_outcomes.load_outcomes(root)
    card = next(c for c in data["cards"] if c["goal_id"] == "BRD-G2")
    assert card["gap"] == 0.0


def test_gap_ordering_desc(tmp_path):
    root = _proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="gmv-year1", target="100", actual="90",
         measured_on="2026-05-31")  # gap 0.10
    _rec(root, goal="BRD-G2", metric="payout-latency-days", target="100", actual="40",
         measured_on="2026-05-31")  # gap 0.60
    data = load_outcomes.load_outcomes(root)
    ranked = [c for c in sorted(
        [c for c in data["cards"] if c["gap"] is not None],
        key=lambda c: c["gap"], reverse=True)]
    assert ranked[0]["goal_id"] == "BRD-G2"


# ---------- scorecard: actual=0 is miss, not blind-spot ----------

def test_zero_actual_is_miss_not_blind(tmp_path):
    root = _proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="gmv-year1", target="100", actual="0",
         measured_on="2026-05-31")
    data = load_outcomes.load_outcomes(root)
    card = next(c for c in data["cards"] if c["goal_id"] == "BRD-G1")
    assert card["blind_spot"] is False
    assert card["latest"]["verdict"] == "miss"
    ascii_out = render_outcomes.scorecard(data, lang="en")
    assert "BRD-G1" in ascii_out and "[-]" in ascii_out  # miss badge


# ---------- trend matrix ----------

def test_trend_two_periods_two_columns(tmp_path):
    root = _proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="gmv-year1", target="100", actual="40",
         measured_on="2026-03-31")
    _rec(root, goal="BRD-G1", metric="gmv-year1", target="100", actual="95",
         measured_on="2026-06-30")
    data = load_outcomes.load_outcomes(root)
    rows, periods = render_outcomes._trend_matrix(data)
    assert periods == ["2026-03-31", "2026-06-30"]
    row = next(r for r in rows if r[0].startswith("BRD-G1"))
    assert row[1] == ["miss", "hit"]
    html = render_outcomes.outcome_trend_html(data, lang="en")
    assert html.count("<th scope='col'>2026-") == 2


# ---------- XSS regression ----------

def test_html_escapes_injection_in_note_and_source(tmp_path):
    root = _proj(tmp_path)
    payload = '<script>alert(1)</script>'
    _rec(root, goal="BRD-G1", metric="gmv-year1", target="100", actual="95",
         measured_on="2026-05-31", source='"><img src=x onerror=alert(1)>',
         note=payload)
    data = load_outcomes.load_outcomes(root)
    for html in (render_outcomes.scorecard_html(data, "en"),
                 render_outcomes.insight_gap_html(data, "en"),
                 render_outcomes.outcome_trend_html(data, "en")):
        assert "<script>" not in html
        assert "onerror=alert" not in html


def test_html_escapes_metric_payload(tmp_path):
    # A forced (off-slug) metric carrying markup must be escaped in every view.
    root = _proj(tmp_path)
    _rec(root, goal="BRD-G1", metric='<b>x</b>', target="100", actual="95",
         measured_on="2026-05-31", force=True)
    data = load_outcomes.load_outcomes(root)
    html = render_outcomes.scorecard_html(data, "en")
    assert "<b>x</b>" not in html
    assert "&lt;b&gt;x&lt;/b&gt;" in html


# ---------- Phase 5: audit-trail outcome source + learning-map + dashboard ----------

def _valid_proj(tmp_path):
    import conftest
    return conftest.make_proj(tmp_path, git=False)


def test_audit_trail_back_compat_without_outcomes(tmp_path):
    # No outcomes.md → assemble() adds zero outcome events (byte-compat with the old
    # trail): every event is a change-log/approval/decision row, none an outcome.
    import assemble_audit_trail
    root = _valid_proj(tmp_path)
    data = assemble_audit_trail.assemble(root)
    assert data["schema_version"] == "1.0"
    assert all(not str(e["action"]).startswith("outcome:") for e in data["events"])


def test_audit_trail_maps_outcomes_into_six_keys(tmp_path):
    import assemble_audit_trail
    root = _valid_proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="arr", target="1000000", actual="400000",
         measured_on="2026-05-31")
    data = assemble_audit_trail.assemble(root)
    assert data["schema_version"] == "1.0"  # no schema bump
    outc = [e for e in data["events"] if str(e["action"]).startswith("outcome:")]
    assert len(outc) == 1
    ev = outc[0]
    # mapped into the existing six keys, no new columns
    assert set(ev) == {"date", "artifact", "action", "who_approved", "what_drifted",
                       "dec_ref", "reconciled"}
    assert ev["artifact"] == "BRD-G1"
    assert "arr" in ev["what_drifted"]
    # the audit view still renders (6-col table) with outcomes present
    rendered = assemble_audit_trail.render_ascii(data, "en")
    assert "BRD-G1" in rendered


def test_learning_map_mermaid_joins_outcome_to_goal(tmp_path):
    import assemble_audit_trail
    root = _valid_proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="arr", target="1000000", actual="400000",
         measured_on="2026-05-31")
    audit = assemble_audit_trail.assemble(root)
    mm = render_learning.learning_map_mermaid(audit, "en")
    assert mm.startswith("```mermaid")
    assert "G_BRD" in mm and "-->" in mm  # outcome → goal edge


def test_learning_map_mermaid_escapes_injection(tmp_path):
    import assemble_audit_trail
    root = _valid_proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="arr", target="1000000", actual="400000",
         measured_on="2026-05-31", note="<script>alert(1)</script>")
    audit = assemble_audit_trail.assemble(root)
    mm = render_learning.learning_map_mermaid(audit, "en")
    # mermaid label sanitizer turns < > into guillemets — no raw tag survives
    assert "<script>" not in mm


def test_learning_dashboard_composes_fragments(tmp_path):
    root = _proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="gmv-year1", target="100", actual="40",
         measured_on="2026-05-31")
    data = load_outcomes.load_outcomes(root)
    html = render_learning.learning_dashboard_html(data, "en")
    assert "ro-table" in html           # embeds the scorecard/gap/trend tables
    assert "--viz learning-map" in html  # links to the map


def test_learning_map_ascii_empty_and_populated(tmp_path):
    # The ASCII downgrade path (production-reachable via --viz learning-map --format ascii).
    import assemble_audit_trail
    root = _valid_proj(tmp_path)
    empty = render_learning.learning_map_ascii(assemble_audit_trail.assemble(root), "en")
    assert "no outcomes" in empty.lower()  # no_outcomes label, no crash
    _rec(root, goal="BRD-G1", metric="arr", target="1000000", actual="400000",
         measured_on="2026-05-31")
    populated = render_learning.learning_map_ascii(assemble_audit_trail.assemble(root), "en")
    assert "BRD-G1" in populated and "→" in populated


# ---------- dispatcher-level (visualize.py CLI) for all 5 --learn views ----------

import subprocess  # noqa: E402

_VIZ = SCRIPTS_DIR / "visualize.py"


def _viz(root, *args):
    return subprocess.run([sys.executable, str(_VIZ), "--root", str(root), *args],
                          capture_output=True, text=True)


def test_dispatcher_all_learn_views(tmp_path):
    root = _valid_proj(tmp_path)
    _rec(root, goal="BRD-G1", metric="arr", target="1000000", actual="400000",
         measured_on="2026-05-31")
    # ascii-default views print to stdout, exit 0
    for view in ("scorecard", "insight-gap", "outcome-trend"):
        r = _viz(root, "--view", view, "--format", "ascii")
        assert r.returncode == 0, f"{view}: {r.stderr}"
    # learning-map: ascii + mermaid both exit 0; md is rejected (audit-only)
    assert _viz(root, "--view", "learning-map", "--format", "ascii").returncode == 0
    rm = _viz(root, "--view", "learning-map", "--format", "mermaid")
    assert rm.returncode == 0 and "```mermaid" in rm.stdout
    assert _viz(root, "--view", "learning-map", "--format", "md").returncode == 2
    # learning is HTML-only: a non-html --format still renders HTML with a note
    rl = _viz(root, "--view", "learning", "--format", "ascii")
    assert rl.returncode == 0 and "HTML-only" in rl.stderr
