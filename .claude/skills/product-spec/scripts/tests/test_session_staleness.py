"""Session-staleness + supersede-sweep guards.

`.session.md` is both a resume source AND an authorised assume-source (a value the
PO already gave there may be assumed). That dual role is the hazard: a session
frozen at date D keeps asserting facts that artifacts edited after D — or decisions
ruled after D — have moved past, so a new session assuming from it can silently
reverse an approved fact. These tests pin the deterministic detector:

- staleness: `.session.md` `updated` < the newest artifact `updated` → stale.
- supersede candidates: active DEC records dated AFTER the session snapshot →
  rulings the session could not have reflected; decisions.md is the authority.

Synthetic fixtures only (no real PO data).
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import session_staleness  # noqa: E402
from spec_graph import build_graph  # noqa: E402
from decision_register import append_decision  # noqa: E402


_PRODUCT = """---
id: PRODUCT
type: product
status: approved
lang: en
created: 2026-05-28
updated: 2026-05-30
name: "X"
core_value: "y"
personas: [shopper]
---
"""

_BRD = """---
id: BRD
type: brd
status: approved
lang: en
created: 2026-05-28
updated: 2026-05-30
goals:
  - id: BRD-G1
    title: g
    status: approved
    metrics: [m]
---
"""


def _story(updated: str) -> str:
    return f"""---
id: PRD-AUTH-E1-S1
type: story
epic: PRD-AUTH-E1
status: approved
lang: en
created: 2026-05-28
updated: {updated}
personas: [shopper]
scope: in
moscow: must
size: S
horizon: now
metrics: [m]
acceptance_criteria:
  - "Given a visitor, when they sign in, then a session is created."
  - "Given a bad password, when they submit, then an error shows."
---
"""


def _session(updated: str) -> str:
    return f"""---
phase: done
lang: en
target: PRD-AUTH-E1-S1
created: 2026-06-01
updated: {updated}
---

# Session notes
"""


def _scaffold(tmp_path: Path, *, session_updated: str, story_updated: str) -> Path:
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(_PRODUCT, encoding="utf-8")
    (prod / "brd.md").write_text(_BRD, encoding="utf-8")
    (prod / "stories" / "story.md").write_text(_story(story_updated), encoding="utf-8")
    (prod / ".session.md").write_text(_session(session_updated), encoding="utf-8")
    return proj


# ------------------------------------------------------------------ staleness

def test_session_stale_when_predates_artifact_edit(tmp_path):
    proj = _scaffold(tmp_path, session_updated="2026-06-02", story_updated="2026-06-10")
    sweep = session_staleness.sweep(proj)
    assert sweep["stale"] is True, "a session older than the newest artifact edit is stale"
    assert sweep["newest_artifact"]["id"] == "PRD-AUTH-E1-S1"
    assert sweep["newest_artifact"]["updated"] == "2026-06-10"
    assert sweep["session_updated"] == "2026-06-02"


def test_session_not_stale_when_newest(tmp_path):
    proj = _scaffold(tmp_path, session_updated="2026-06-15", story_updated="2026-06-10")
    sweep = session_staleness.sweep(proj)
    assert sweep["stale"] is False, "a session newer than every artifact is fresh"


# ------------------------------------------------------- supersede-sweep (DEC)

def test_superseding_decisions_listed_decisions_authoritative(tmp_path):
    proj = _scaffold(tmp_path, session_updated="2026-06-02", story_updated="2026-06-03")
    append_decision(
        proj, dec_id="DEC-1", title="payment provider is Sepay only",
        rationale="single provider keeps reconciliation simple",
        affects="PRD-AUTH", date="2026-06-05",
    )
    sweep = session_staleness.sweep(proj)
    ids = [d["id"] for d in sweep["superseding_decisions"]]
    assert "DEC-1" in ids, "an active DEC dated after the session snapshot is a supersede candidate"
    dec = next(d for d in sweep["superseding_decisions"] if d["id"] == "DEC-1")
    assert dec["date"] == "2026-06-05"
    assert dec["affects"] == "PRD-AUTH"
    assert dec["title"]
    assert sweep["authoritative_source"] == "decisions.md", \
        "Q5: when session and decisions diverge, decisions.md wins"


def test_decision_before_session_not_superseding(tmp_path):
    proj = _scaffold(tmp_path, session_updated="2026-06-02", story_updated="2026-06-03")
    append_decision(
        proj, dec_id="DEC-1", title="ruling made before the session froze",
        rationale="already reflected in the session snapshot", date="2026-06-01",
    )
    sweep = session_staleness.sweep(proj)
    ids = [d["id"] for d in sweep["superseding_decisions"]]
    assert "DEC-1" not in ids, "a DEC dated before the session snapshot is already reflected"


# ------------------------------------------------- validate-gate warn findings

def test_staleness_findings_emit_warn_no_sentinel(tmp_path):
    proj = _scaffold(tmp_path, session_updated="2026-06-02", story_updated="2026-06-10")
    append_decision(
        proj, dec_id="DEC-1", title="post-session ruling",
        rationale="r", date="2026-06-05",
    )
    graph = build_graph(proj)
    findings = session_staleness.staleness_findings(graph)
    checks = {f["check"] for f in findings}
    assert "session_stale" in checks, "a stale session must surface in the validate gate"
    assert "session_superseded" in checks, "post-session decisions must surface"
    assert all(f["severity"] == "warn" for f in findings), "advisory nudge, never a hard error"
    blob = " ".join(str(f) for f in findings)
    assert "<missing-id>" not in blob and "<invalid-id>" not in blob


# ----------------------------------------------------------------- fail-soft

def test_failsoft_no_session_file(tmp_path):
    proj = _scaffold(tmp_path, session_updated="2026-06-02", story_updated="2026-06-10")
    (proj / "docs" / "product" / ".session.md").unlink()
    sweep = session_staleness.sweep(proj)
    assert sweep["stale"] is False
    assert sweep["session_updated"] is None
    assert sweep["superseding_decisions"] == []
    assert session_staleness.staleness_findings(build_graph(proj)) == []


def test_failsoft_unparseable_updated(tmp_path):
    proj = _scaffold(tmp_path, session_updated="not-a-date", story_updated="2026-06-10")
    sweep = session_staleness.sweep(proj)  # must not raise
    assert sweep["stale"] is False
    assert sweep["session_updated"] is None
