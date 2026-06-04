"""Risk Hardening (TDD RED).

Closes two grounded bugs and adds two deterministic script warns:
  - bug #3: `prds/*.md` never carried a `risks:` frontmatter key, so
            `--viz risk` only ever saw epic risks. The PRD template must
            gain `risks: {{risks}}` (mirroring epic.md).
  - bug #4: `impact`/`likelihood` were never enum-validated, so a typo like
            `impact: hihg` passed silently. Add risk_impact / risk_likelihood
            / risk_status enums; reuse the existing `invalid_type` finding for
            a malformed (non-dict / description-less) risk entry.
  - `risk_high_ratio` (>50% of risks are `high`) — deterministic ratio, script.
  - `risk_blindspot` (epic with >=5 child stories and 0 risks) — deterministic
    child-story count via the graph, script (NOT LLM — keeps the
    Script-vs-LLM split).

`mitigation` (free text) + `status` (open|mitigated|accepted) are new optional
fields that must parse and pass through into the graph `risks[]` objects so the
HTML risk grid can show them.

All checks are deterministic counts/enums in Python — no LLM, no judgment.
Mirrors the fixture-build + finding-set assertion style of test_scripts.py.
"""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
from check_consistency import check as check_cons, _enrich_with_ac  # noqa: E402
from generate_templates import fill_defaults, render  # noqa: E402
import render_ascii  # noqa: E402
import render_html  # noqa: E402

TEMPLATES = SCRIPTS_DIR.parent / "assets" / "templates"


# ---------------------------------------------------------------------------
# Shared fixture builders — minimal valid spec scaffold (PRODUCT + BRD) so the
# graph builds clean; the test then layers the artifact under test on top.
# ---------------------------------------------------------------------------

_PRODUCT_MD = """---
id: PRODUCT
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [s]
---
"""

_BRD_MD = """---
id: BRD
type: brd
status: draft
lang: en
goals:
  - id: BRD-G1
    title: g
    status: draft
    metrics: [m]
---
"""


def _scaffold(tmp_path: Path) -> Path:
    """Create a minimal docs/product tree (PRODUCT + BRD) and return the project
    root. Callers add prds/epics/stories as needed."""
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(_PRODUCT_MD)
    (prod / "brd.md").write_text(_BRD_MD)
    return proj


def _write_prd(proj: Path, body: str, name: str = "auth.md") -> None:
    (proj / "docs" / "product" / "prds" / name).write_text(body)


def _checks(proj: Path):
    """Build graph + run the full consistency check, return (graph, findings)."""
    g = build_graph(proj)
    _enrich_with_ac(g, proj)
    return g, check_cons(g)


def _scaffold_unique(slug: str) -> Path:
    """A self-contained (no pytest tmp_path) scaffold for the render tests, which
    call render_html.risk(graph) directly rather than parametrizing on tmp_path.
    Uses an isolated temp dir per call so concurrent runs never collide."""
    import tempfile

    proj = Path(tempfile.mkdtemp(prefix=f"risk-{slug}-")) / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(_PRODUCT_MD)
    (prod / "brd.md").write_text(_BRD_MD)
    return proj


def _HTML_GRID_PROJ() -> Path:
    """A scaffold carrying a PRD with two risks (one high/high open, one med/low
    mitigated) — the shared fixture for the HTML-grid render assertions so the
    description/mitigation/status drill-down has real data to surface."""
    proj = _scaffold_unique("html-grid")
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks:
  - description: "Third-party OAuth dependency"
    impact: high
    likelihood: high
    mitigation: "Fallback provider on standby"
    status: open
  - description: "Session fixation"
    impact: med
    likelihood: low
    mitigation: "Rotate session id on login"
    status: mitigated
---
""")
    return proj


# ---------------------------------------------------------------------------
# PRD risks render in --viz risk alongside epic risks (closes bug #3).
# ---------------------------------------------------------------------------

def test_prd_risk_in_graph(tmp_path):
    """A PRD with a valid `risks:` block must (a) be a shape the freshly
    generated PRD template even emits — bug #3 was that `prd.md` had NO
    `risks:` frontmatter key, so the field could never be filled by the
    interview flow — and (b) flow into the graph `risks[]` and the
    `--viz risk` 3x3 grid.

    The discriminating RED assertion is (a): today the PRD template carries
    no `risks:` key, so a generated PRD can never declare a risk.
    """
    # (a) Template / generator must emit a `risks:` frontmatter key — the
    #     actual bug #3 locus. RED today: prd.md has no `{{risks}}` token.
    tmpl = (TEMPLATES / "prd.md").read_text(encoding="utf-8")
    vals = fill_defaults({"id": "PRD-AUTH", "title": "Auth"}, "prd", "PRD-AUTH", "en")
    rendered = render(tmpl, vals, keep_optional=[])
    front = rendered.split("---", 2)[1]
    assert "risks:" in front, (
        "prd.md template must carry a `risks:` frontmatter key (bug #3); "
        f"rendered frontmatter:\n{front}"
    )

    # (b) A hand-authored PRD risk flows into the graph and the risk grid.
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks:
  - description: "Third-party OAuth dependency"
    impact: high
    likelihood: high
    mitigation: "Fallback provider on standby"
    status: open
---
""")
    g = build_graph(proj)
    risk_nodes = [r for r in g["risks"] if r.get("node") == "PRD-AUTH"]
    assert risk_nodes, f"expected PRD-AUTH risk in graph risks[]; got: {g['risks']}"
    grid = render_ascii.risk(g)
    # high impact x high likelihood cell must show a non-zero count.
    high_row = [ln for ln in grid.splitlines() if ln.strip().startswith("| high")]
    assert high_row, f"no high-impact row in risk grid:\n{grid}"
    assert high_row[0].rstrip().endswith("1 |"), (
        f"PRD risk (high/high) not counted in --viz risk grid:\n{grid}"
    )


# ---------------------------------------------------------------------------
# Impact / likelihood / status enum-validated (closes bug #4).
# ---------------------------------------------------------------------------

def test_risk_impact_typo(tmp_path):
    """`impact: hihg` (typo) must raise `unknown_enum` — bug #4 was that risk
    sub-fields were never enum-validated, so typos passed silently."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks:
  - description: "OAuth dependency"
    impact: hihg
    likelihood: med
    status: open
---
""")
    _, findings = _checks(proj)
    enum_findings = [f for f in findings if f["check"] == "unknown_enum"]
    assert enum_findings, (
        f"expected unknown_enum for impact: hihg; got checks: "
        f"{sorted({f['check'] for f in findings})}"
    )
    assert any("hihg" in str(f.get("detail", "")) or
               (f.get("context") or {}).get("value") == "hihg"
               for f in enum_findings), (
        f"unknown_enum should reference the bad value 'hihg'; got: {enum_findings}"
    )


def test_risk_likelihood_typo(tmp_path):
    """`likelihood: maybe` (not in low|med|high) must raise `unknown_enum`."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks:
  - description: "OAuth dependency"
    impact: high
    likelihood: maybe
    status: open
---
""")
    _, findings = _checks(proj)
    assert any(f["check"] == "unknown_enum" for f in findings), (
        f"expected unknown_enum for likelihood: maybe; got checks: "
        f"{sorted({f['check'] for f in findings})}"
    )


def test_risk_status_enum(tmp_path):
    """`status: closed` (not in open|mitigated|accepted) must raise
    `unknown_enum`. The risk-entry `status` is a NEW enum distinct
    from the artifact-level draft|review|approved status."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks:
  - description: "OAuth dependency"
    impact: high
    likelihood: med
    status: closed
---
""")
    _, findings = _checks(proj)
    assert any(f["check"] == "unknown_enum" for f in findings), (
        f"expected unknown_enum for risk status: closed; got checks: "
        f"{sorted({f['check'] for f in findings})}"
    )


def test_risk_bad_shape(tmp_path):
    """A risk entry that is not a dict (e.g. `risks: ["just a string"]`) must
    raise `invalid_type` — reusing the EXISTING `invalid_type` finding rather
    than inventing a new `invalid_shape`.

    Today `_risks()` silently skips non-dict entries and `LIST_FIELDS` only
    checks that `risks` is itself a list, so a string element passes clean.
    """
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks: ["just a string"]
---
""")
    _, findings = _checks(proj)
    invalid = [f for f in findings if f["check"] == "invalid_type"]
    assert invalid, (
        f"expected invalid_type for a non-dict risk entry; got checks: "
        f"{sorted({f['check'] for f in findings})}"
    )
    assert any(f.get("artifact_id") == "PRD-AUTH" for f in invalid), (
        f"invalid_type should be attributed to PRD-AUTH; got: {invalid}"
    )


# ---------------------------------------------------------------------------
# Mitigation + status parse + surface (graph passthrough → HTML grid).
# ---------------------------------------------------------------------------

def test_risk_mitigation_status_passthrough(tmp_path):
    """`mitigation` (free text) + `status` (enum) on a risk entry must survive
    into the graph `risks[]` objects so render_html can show them in the grid
    drill-down."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks:
  - description: "OAuth dependency"
    impact: high
    likelihood: med
    mitigation: "Fallback provider on standby"
    status: mitigated
---
""")
    g = build_graph(proj)
    risk = next((r for r in g["risks"] if r.get("node") == "PRD-AUTH"), None)
    assert risk is not None, f"PRD-AUTH risk missing from graph: {g['risks']}"
    assert risk.get("mitigation") == "Fallback provider on standby", (
        f"mitigation not passed through into graph risk object: {risk}"
    )
    assert risk.get("status") == "mitigated", (
        f"risk status not passed through into graph risk object: {risk}"
    )


def test_risk_html_grid_surfaces_mitigation_and_status():
    """RENDERED surface: the HTML risk view is an HTML-native <table>
    (NOT the ASCII matrix in <pre>) whose cell drill-down surfaces each risk's
    description + mitigation + status (a dedicated HTML-native risk grid).
    The data-layer passthrough above is dead until a consumer shows
    it; render_html.risk() is that consumer.
    """
    g = build_graph(_HTML_GRID_PROJ())
    html_body = render_html.risk(g)

    # HTML-native: a real <table>, not the ASCII grid wrapped in <pre>.
    assert "<table" in html_body, f"risk view must render an HTML <table>; got:\n{html_body}"
    assert "<pre>| Impact" not in html_body, "risk HTML must not fall back to the ASCII <pre> grid"

    # Drill-down surfaces description + mitigation + status (escaped) for the
    # high/high risk — the whole point of the mitigation/status surface.
    assert "Third-party OAuth dependency" in html_body, "risk description missing from HTML grid"
    assert "Fallback provider on standby" in html_body, "mitigation missing from HTML grid drill-down"
    # status appears as a label/badge text.
    assert "open" in html_body and "mitigated" in html_body, "risk status missing from HTML grid drill-down"


def test_risk_html_grid_escapes_spec_text():
    """Injection guard: spec-derived risk text is HTML-escaped server-side
    (the risk view is NOT a body view — it inlines no DOMPurify/marked — so any
    `<`/`>` in a PO's description/mitigation must be neutralized at render time,
    same chokepoint discipline as the heatmap <pre> path)."""
    proj = _scaffold_unique("PRD-XSS")
    _write_prd(proj, """---
id: PRD-XSS
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks:
  - description: "<script>alert(1)</script>"
    impact: high
    likelihood: high
    status: open
---
""")
    html_body = render_html.risk(build_graph(proj))
    assert "<script>alert(1)" not in html_body, "raw <script> from a risk description leaked unescaped"
    assert "&lt;script&gt;" in html_body, "risk description must be HTML-escaped"


def test_risk_html_grid_deterministic():
    """Same graph → byte-identical HTML grid body (no timestamp inside the
    fragment; the timestamp lives only in the page chrome written by .write())."""
    g = build_graph(_HTML_GRID_PROJ())
    assert render_html.risk(g) == render_html.risk(g)


def test_risk_view_html_dispatch_is_native_table(tmp_path):
    """End-to-end: `visualize.py --view risk --format html` must write a page
    whose diagram is the HTML-native <table>, NOT the Mermaid-fallback ASCII
    <pre>. Mirrors test_visualize.test_html_dispatch_routes_ascii_fallback_view_as_pre_not_mermaid,
    but asserts the OPPOSITE for risk now that it has a native renderer."""
    proj = tmp_path / "proj"
    src = _HTML_GRID_PROJ()
    import shutil
    shutil.copytree(src / "docs", proj / "docs")

    viz = SCRIPTS_DIR / "visualize.py"
    r = subprocess.run(
        [sys.executable, str(viz), "--root", str(proj), "--view", "risk", "--format", "html"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    htmls = sorted((proj / "docs" / "product" / "visuals").glob("risk-*.html"))
    assert htmls, "expected a risk HTML file written"
    body = htmls[-1].read_text(encoding="utf-8")
    assert "<table" in body, "risk page must embed the HTML-native <table>"
    assert '<div class="mermaid">' not in body, "risk page must not route through the Mermaid wrapper"
    assert "<pre>| Impact" not in body, "risk page must not fall back to the ASCII <pre> grid"
    assert "Fallback provider on standby" in body, "mitigation must surface in the rendered risk page"


# ---------------------------------------------------------------------------
# risk_high_ratio (>50% high) + risk_blindspot (>=5 story, 0 risk).
#         Both deterministic counts — script, NOT LLM.
# ---------------------------------------------------------------------------

def test_risk_high_ratio(tmp_path):
    """5 risks, 3 of them `high` (60% > 50%) → `risk_high_ratio` warn.

    Threshold is the commented module const RISK_HIGH_RATIO = 0.5.
    """
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks:
  - description: "r1"
    impact: high
    likelihood: med
    status: open
  - description: "r2"
    impact: high
    likelihood: high
    status: open
  - description: "r3"
    impact: high
    likelihood: low
    status: open
  - description: "r4"
    impact: med
    likelihood: med
    status: open
  - description: "r5"
    impact: low
    likelihood: low
    status: open
---
""")
    _, findings = _checks(proj)
    ratio = [f for f in findings if f["check"] == "risk_high_ratio"]
    assert ratio, (
        f"expected risk_high_ratio warn (3/5 high = 60%); got checks: "
        f"{sorted({f['check'] for f in findings})}"
    )
    assert ratio[0]["severity"] == "warn", (
        f"risk_high_ratio must be a warn, not {ratio[0]['severity']}"
    )


def test_risk_high_ratio_below_threshold_silent(tmp_path):
    """Boundary: 2 of 5 high (40% < 50%) must NOT warn — guards the threshold
    so it's a strict majority, deterministic."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
risks:
  - description: "r1"
    impact: high
    likelihood: med
    status: open
  - description: "r2"
    impact: high
    likelihood: high
    status: open
  - description: "r3"
    impact: med
    likelihood: low
    status: open
  - description: "r4"
    impact: med
    likelihood: med
    status: open
  - description: "r5"
    impact: low
    likelihood: low
    status: open
---
""")
    _, findings = _checks(proj)
    assert not any(f["check"] == "risk_high_ratio" for f in findings), (
        f"40% high must not trip risk_high_ratio; findings: "
        f"{[f for f in findings if f['check'] == 'risk_high_ratio']}"
    )


def test_risk_blindspot(tmp_path):
    """An epic with >=5 child stories and 0 risks → `risk_blindspot` warn.

    Deterministic: the child-story count comes from the graph edges, NOT an
    LLM judgment (the Script-vs-LLM split keeps this in the script
    layer). Threshold is the commented const RISK_BLINDSPOT_MIN_STORIES = 5.
    """
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    epics = proj / "docs" / "product" / "epics"
    epics.joinpath("PRD-AUTH-E1.md").write_text("""---
id: PRD-AUTH-E1
type: epic
prd: PRD-AUTH
brd_goals: [BRD-G1]
status: draft
lang: en
risks: []
---
""")
    stories = proj / "docs" / "product" / "stories"
    for i in range(1, 7):  # 6 child stories under PRD-AUTH-E1, all risk-free
        stories.joinpath(f"PRD-AUTH-E1-S{i}.md").write_text(f"""---
id: PRD-AUTH-E1-S{i}
type: story
epic: PRD-AUTH-E1
status: draft
lang: en
acceptance_criteria:
  - "ac one"
  - "ac two"
---
""")
    _, findings = _checks(proj)
    blind = [f for f in findings if f["check"] == "risk_blindspot"]
    assert blind, (
        f"expected risk_blindspot for epic with 6 stories and 0 risks; "
        f"got checks: {sorted({f['check'] for f in findings})}"
    )
    assert blind[0]["severity"] == "warn"
    assert blind[0].get("artifact_id") == "PRD-AUTH-E1", (
        f"risk_blindspot must be attributed to the epic; got: {blind}"
    )


def test_risk_blindspot_silent_below_min_stories(tmp_path):
    """Boundary: an epic with 4 child stories (< 5) and 0 risks must NOT warn —
    guards the deterministic threshold against firing too eagerly."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    epics = proj / "docs" / "product" / "epics"
    epics.joinpath("PRD-AUTH-E1.md").write_text("""---
id: PRD-AUTH-E1
type: epic
prd: PRD-AUTH
brd_goals: [BRD-G1]
status: draft
lang: en
risks: []
---
""")
    stories = proj / "docs" / "product" / "stories"
    for i in range(1, 5):  # only 4 stories
        stories.joinpath(f"PRD-AUTH-E1-S{i}.md").write_text(f"""---
id: PRD-AUTH-E1-S{i}
type: story
epic: PRD-AUTH-E1
status: draft
lang: en
acceptance_criteria:
  - "ac one"
  - "ac two"
---
""")
    _, findings = _checks(proj)
    assert not any(f["check"] == "risk_blindspot" for f in findings), (
        f"4 child stories must not trip risk_blindspot; findings: "
        f"{[f for f in findings if f['check'] == 'risk_blindspot']}"
    )


# ---------------------------------------------------------------------------
# Back-compat guard. A v1 PRD with NO `risks:` key must validate clean
#        (no error, empty risk set). Green today; must STAY green after the
#        new fields land. (This is a regression guard, not a RED case.)
# ---------------------------------------------------------------------------

def test_risk_backcompat(tmp_path):
    """A PRD with no `risks:` frontmatter must parse + validate with zero
    risk-related findings and contribute an empty risk set to the graph."""
    proj = _scaffold(tmp_path)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    g, findings = _checks(proj)
    risk_checks = {
        "unknown_enum", "invalid_type", "risk_high_ratio", "risk_blindspot",
    }
    offending = [f for f in findings
                 if f["check"] in risk_checks and f["severity"] == "error"]
    assert offending == [], (
        f"a v1 PRD without risks: must validate clean; got: {offending}"
    )
    assert [r for r in g["risks"] if r.get("node") == "PRD-AUTH"] == [], (
        "a PRD without risks: must contribute no graph risks"
    )
