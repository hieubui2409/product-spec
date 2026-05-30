"""Phase 4 — COMPETITION dimension (TDD RED).

Adds the COMPETITION dimension to the spec model:

  - BRD is the DRY home for competitor IDENTITY: a `competitors:` list of
    `{id, name, url, threat}` (id grammar `COMP-<SLUG>`; threat ∈ low|med|high).
    The graph exposes a top-level `graph['competitors']` key — the single home
    consumed by the consistency check, the renderers, AND the drift LLM-input
    builder (so nothing re-parses brd.md inline; design phase-04 / report §5.1).
  - PRD references competitors by ID via an ID-keyed MAP
    `competitive_parity: {COMP-ACME: behind}` (enum ahead|parity|behind|none).
    We follow the report's ID-keyed map, NOT the R2 inline list-of-dict: the
    competitor name lives ONCE in the BRD (DRY, matches the skill ID philosophy).
  - OpSec: the parser IGNORES any competitor `url` beginning with `private:`
    (design §0.2 / G-E4) — it must never reach the graph or any render.
  - Views: an HTML-native parity matrix (competitors rows × PRDs cols, cells =
    parity enum) + threat heatmap; NOT Mermaid (G-E2 / Q44).

These are the STRUCTURAL pytest cases (deterministic — parse, OpSec skip, render,
back-compat). The enum/`unknown_ref` validation cases live in
test_check_consistency.py (the phase spec's "extend test_check_consistency.py").
The `competitive_drift` LLM judgment is graded by the eval runner (eval/evals.json
ids 11-13), not here (G-B2). Its deterministic SCRIPT half — the parity-resolution
anchor builder `competitive_drift_anchors.build_anchors` — is pytest-gated in
test_competitive_drift.py (the sibling of test_time_realism.py), so this file stays
focused on the parse/render/OpSec structural surface.

Mirrors the fixture-build + finding-set assertion style of test_risk_complete.py.
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
from check_consistency import check as check_cons, _enrich_with_ac  # noqa: E402
from generate_templates import fill_defaults, render  # noqa: E402
import render_html  # noqa: E402

TEMPLATES = SCRIPTS_DIR.parent / "assets" / "templates"


# ---------------------------------------------------------------------------
# Shared fixture builders — minimal valid spec scaffold (PRODUCT + BRD) so the
# graph builds clean; the test then layers competitors / PRDs on top. The BRD
# here carries NO competitors by default; the competitor-bearing tests rewrite
# brd.md via _write_brd().
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
    """Create a minimal docs/product tree (PRODUCT + competitor-less BRD) and
    return the project root. Callers add competitors / prds as needed."""
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(_PRODUCT_MD)
    (prod / "brd.md").write_text(_BRD_MD)
    return proj


def _write_brd(proj: Path, body: str) -> None:
    (proj / "docs" / "product" / "brd.md").write_text(body)


def _write_prd(proj: Path, body: str, name: str = "auth.md") -> None:
    (proj / "docs" / "product" / "prds" / name).write_text(body)


def _checks(proj: Path):
    """Build graph + run the full consistency check, return (graph, findings)."""
    g = build_graph(proj)
    _enrich_with_ac(g, proj)
    return g, check_cons(g)


def _competitors(graph) -> list:
    """The graph's competitor list — the single DRY home. RED today: build_graph
    emits no top-level `competitors` key, so this is [] regardless of the BRD."""
    return graph.get("competitors") or []


# Two competitors at the BRD; the SHOPIFY one carries a `private:` URL so the
# OpSec-skip test and the parse test can share one fixture.
_BRD_TWO_COMP = """---
id: BRD
type: brd
status: draft
lang: en
goals:
  - id: BRD-G1
    title: g
    status: draft
    metrics: [m]
competitors:
  - id: COMP-ACME
    name: "Acme Commerce"
    url: "https://acme.example"
    threat: high
  - id: COMP-SHOPIFY
    name: "Shopify"
    url: "https://shopify.example"
    threat: med
---
"""


# ---------------------------------------------------------------------------
# G-E1 — competitors at the BRD parse into the graph (DRY identity home).
# ---------------------------------------------------------------------------

def test_brd_template_carries_competitors_key():
    """The freshly generated brd.md template must carry a `competitors:`
    frontmatter key — the DRY home for competitor identity (G-E1). RED today:
    brd.md has no `{{competitors}}` token, so the interview flow can never fill
    it (mirrors the bug-#3 template-locus assertion for PRD risks)."""
    tmpl = (TEMPLATES / "brd.md").read_text(encoding="utf-8")
    vals = fill_defaults({"id": "BRD"}, "brd", "BRD", "en")
    rendered = render(tmpl, vals, keep_optional=[])
    front = rendered.split("---", 2)[1]
    assert "competitors:" in front, (
        "brd.md template must carry a `competitors:` frontmatter key (G-E1, "
        f"the DRY identity home); rendered frontmatter:\n{front}"
    )


def test_competitors_parse(tmp_path):
    """A BRD with 2 competitors must surface them on a top-level
    `graph['competitors']` list, each carrying id + name + threat. This is the
    single DRY home the consistency check / renderers / drift builder read."""
    proj = _scaffold(tmp_path)
    _write_brd(proj, _BRD_TWO_COMP)
    g = build_graph(proj)
    comps = _competitors(g)
    by_id = {c.get("id"): c for c in comps if isinstance(c, dict)}
    assert "COMP-ACME" in by_id and "COMP-SHOPIFY" in by_id, (
        f"expected COMP-ACME + COMP-SHOPIFY on graph['competitors']; got: {comps}"
    )
    assert by_id["COMP-ACME"].get("name") == "Acme Commerce", (
        f"competitor name must parse through: {by_id['COMP-ACME']}"
    )
    assert by_id["COMP-ACME"].get("threat") == "high", (
        f"competitor threat must parse through: {by_id['COMP-ACME']}"
    )


# ---------------------------------------------------------------------------
# G-E1 — PRD references competitors by ID via the competitive_parity MAP.
# ---------------------------------------------------------------------------

def test_prd_template_carries_competitive_parity_key():
    """The generated prd.md template must carry a `competitive_parity:`
    frontmatter key (the per-PRD reference into the BRD competitor identity).
    RED today: prd.md has no `{{competitive_parity}}` token."""
    tmpl = (TEMPLATES / "prd.md").read_text(encoding="utf-8")
    vals = fill_defaults({"id": "PRD-AUTH", "title": "Auth"}, "prd", "PRD-AUTH", "en")
    rendered = render(tmpl, vals, keep_optional=[])
    front = rendered.split("---", 2)[1]
    assert "competitive_parity:" in front, (
        "prd.md template must carry a `competitive_parity:` frontmatter key "
        f"(G-E1); rendered frontmatter:\n{front}"
    )


def test_competitive_parity_map_parses_on_prd(tmp_path):
    """A PRD's ID-keyed `competitive_parity` map must land on its graph node so
    the matrix/heatmap renderers and the drift builder can read it. We assert the
    parsed map round-trips the competitor IDs → parity enum values."""
    proj = _scaffold(tmp_path)
    _write_brd(proj, _BRD_TWO_COMP)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
competitive_parity:
  COMP-ACME: behind
  COMP-SHOPIFY: parity
---
""")
    g = build_graph(proj)
    prd = next((n for n in g["nodes"] if n.get("id") == "PRD-AUTH"), None)
    assert prd is not None, "PRD-AUTH must be a graph node"
    cp = prd.get("competitive_parity")
    assert isinstance(cp, dict), (
        f"competitive_parity must parse as an ID-keyed map on the node; got "
        f"{cp!r} ({type(cp).__name__})"
    )
    assert cp.get("COMP-ACME") == "behind" and cp.get("COMP-SHOPIFY") == "parity", (
        f"parity map values must round-trip onto the node: {cp}"
    )


# ---------------------------------------------------------------------------
# G-E4 — OpSec: a `private:`-prefixed competitor URL is IGNORED by the parser
#        and never appears in the graph OR any render.
# ---------------------------------------------------------------------------

_BRD_PRIVATE_URL = """---
id: BRD
type: brd
status: draft
lang: en
goals:
  - id: BRD-G1
    title: g
    status: draft
    metrics: [m]
competitors:
  - id: COMP-ACME
    name: "Acme Commerce"
    url: "private:internal/competitive-teardown.pdf"
    threat: high
---
"""


def test_private_url_skipped(tmp_path):
    """A competitor `url` starting `private:` must be IGNORED at parse (single
    OpSec chokepoint, G-E4): the secret path must not survive onto
    graph['competitors'] in any form. The competitor itself is still kept (only
    the URL is dropped) — its id/name/threat remain usable."""
    proj = _scaffold(tmp_path)
    _write_brd(proj, _BRD_PRIVATE_URL)
    g = build_graph(proj)
    comps = _competitors(g)
    acme = next((c for c in comps if isinstance(c, dict) and c.get("id") == "COMP-ACME"), None)
    assert acme is not None, (
        f"the competitor must still be kept (only the private URL is dropped); got: {comps}"
    )
    # The private URL must be absent — None / empty / not the secret string.
    assert not acme.get("url"), (
        f"a `private:`-prefixed URL must be dropped from the graph competitor; got url={acme.get('url')!r}"
    )
    # Belt-and-braces: the secret path must not leak ANYWHERE in the serialized graph.
    import json
    blob = json.dumps(g, default=str)
    assert "private:internal" not in blob and "competitive-teardown" not in blob, (
        "the private: URL path leaked into the serialized graph"
    )


def test_private_url_not_in_render(tmp_path):
    """The OpSec skip must hold through to the rendered surface too: a
    `private:` competitor URL must never appear in the parity-matrix /
    threat-heatmap HTML (G-E4 — the URL is encouraged-public only, never
    displayed when secret)."""
    proj = _scaffold(tmp_path)
    _write_brd(proj, _BRD_PRIVATE_URL)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
competitive_parity:
  COMP-ACME: behind
---
""")
    g = build_graph(proj)
    html_body = render_html.competition(g)
    assert "private:internal" not in html_body and "competitive-teardown" not in html_body, (
        f"private: URL leaked into the competition render:\n{html_body}"
    )


# ---------------------------------------------------------------------------
# G-E2 — parity matrix + threat heatmap render HTML-native (NOT Mermaid).
# ---------------------------------------------------------------------------

def test_parity_matrix_render(tmp_path):
    """2 competitors × 2 PRDs → an HTML-native parity matrix: a real <table>
    (NOT an ASCII grid in <pre>, NOT a Mermaid div) whose rows are competitor
    names, whose columns are PRD ids, and whose cells carry the parity enum
    value for that (competitor, PRD) pair (G-E2 / Q44)."""
    proj = _scaffold(tmp_path)
    _write_brd(proj, _BRD_TWO_COMP)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
competitive_parity:
  COMP-ACME: behind
  COMP-SHOPIFY: parity
---
""", name="auth.md")
    _write_prd(proj, """---
id: PRD-CHECKOUT
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
competitive_parity:
  COMP-ACME: ahead
  COMP-SHOPIFY: none
---
""", name="checkout.md")
    g = build_graph(proj)
    html_body = render_html.competition(g)

    # HTML-native: a real <table>, not the ASCII grid wrapped in <pre>, not Mermaid.
    assert "<table" in html_body, f"parity matrix must render an HTML <table>; got:\n{html_body}"
    assert '<div class="mermaid">' not in html_body, "competition view must not route through Mermaid"

    # Rows = competitor names (the DRY identity from the BRD).
    assert "Acme Commerce" in html_body and "Shopify" in html_body, (
        "competitor names (matrix rows) missing from the parity matrix"
    )
    # Columns = PRD ids (feature-area = PRD, Q48).
    assert "PRD-AUTH" in html_body and "PRD-CHECKOUT" in html_body, (
        "PRD ids (matrix columns) missing from the parity matrix"
    )
    # Cells carry the parity enum values declared on the PRDs.
    for parity_value in ("behind", "parity", "ahead", "none"):
        assert parity_value in html_body, (
            f"parity enum cell {parity_value!r} missing from the matrix:\n{html_body}"
        )


def test_threat_heatmap_render(tmp_path):
    """The threat heatmap surfaces each competitor × threat level (G-E2). Render
    HTML-native and show the competitor name + its threat tier."""
    proj = _scaffold(tmp_path)
    _write_brd(proj, _BRD_TWO_COMP)
    g = build_graph(proj)
    html_body = render_html.competition(g)
    # The high-threat ACME and med-threat SHOPIFY tiers must both surface.
    assert "high" in html_body and "med" in html_body, (
        f"threat tiers (high/med) missing from the competition render:\n{html_body}"
    )


def test_competition_render_escapes_spec_text(tmp_path):
    """Injection guard (G-A4 chokepoint discipline): a competitor name with
    HTML metacharacters must be escaped server-side. The competition view is NOT
    a body view — it inlines no DOMPurify/marked — so any `<`/`>` in a PO-entered
    competitor name must be neutralized at render time (same discipline as the
    risk grid)."""
    proj = _scaffold(tmp_path)
    _write_brd(proj, """---
id: BRD
type: brd
status: draft
lang: en
goals:
  - id: BRD-G1
    title: g
    status: draft
    metrics: [m]
competitors:
  - id: COMP-XSS
    name: "<script>alert(1)</script>"
    url: "https://x.example"
    threat: high
---
""")
    g = build_graph(proj)
    html_body = render_html.competition(g)
    assert "<script>alert(1)" not in html_body, "raw <script> from a competitor name leaked unescaped"
    assert "&lt;script&gt;" in html_body, "competitor name must be HTML-escaped"


def test_competition_render_deterministic(tmp_path):
    """G-A4: same graph → byte-identical competition fragment (no timestamp
    inside the fragment; the timestamp lives only in the page chrome)."""
    proj = _scaffold(tmp_path)
    _write_brd(proj, _BRD_TWO_COMP)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
competitive_parity:
  COMP-ACME: behind
  COMP-SHOPIFY: parity
---
""")
    g = build_graph(proj)
    assert render_html.competition(g) == render_html.competition(g)


def test_competition_view_html_dispatch_is_native_table(tmp_path):
    """End-to-end: `visualize.py --view competition --format html` writes a page
    whose diagram is the HTML-native <table>, NOT a Mermaid div and NOT an ASCII
    <pre> fallback (mirrors the risk view's native-table dispatch test)."""
    proj = _scaffold(tmp_path)
    _write_brd(proj, _BRD_TWO_COMP)
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
competitive_parity:
  COMP-ACME: behind
  COMP-SHOPIFY: parity
---
""")
    viz = SCRIPTS_DIR / "visualize.py"
    r = subprocess.run(
        [sys.executable, str(viz), "--root", str(proj), "--view", "competition", "--format", "html"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"competition view dispatch must exit 0: {r.stderr}"
    htmls = sorted((proj / "docs" / "product" / "visuals").glob("competition-*.html"))
    assert htmls, "expected a competition HTML file written"
    body = htmls[-1].read_text(encoding="utf-8")
    assert "<table" in body, "competition page must embed the HTML-native <table>"
    assert '<div class="mermaid">' not in body, "competition page must not route through Mermaid"
    assert "Acme Commerce" in body, "competitor name must surface in the rendered competition page"


# ---------------------------------------------------------------------------
# G-A2 — back-compat. A v1 spec with NO competitors / NO competitive_parity
#        parses + validates + renders with no error and an EMPTY competitor set.
# ---------------------------------------------------------------------------

def test_competition_backcompat(tmp_path):
    """A v1 BRD (no `competitors:`) + a v1 PRD (no `competitive_parity:`) must
    parse + validate with zero competition-related findings and contribute an
    empty competitor set to the graph (G-A2 / G-E* optionality)."""
    proj = _scaffold(tmp_path)  # BRD here carries NO competitors
    _write_prd(proj, """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
---
""")
    g, findings = _checks(proj)
    assert _competitors(g) == [], (
        f"a v1 BRD without competitors: must contribute an empty competitor set; got {_competitors(g)}"
    )
    comp_checks = {"unknown_enum", "unknown_ref", "invalid_type"}
    offending = [f for f in findings
                 if f["check"] in comp_checks and f["severity"] == "error"]
    assert offending == [], (
        f"a v1 spec without competition fields must validate clean; got: {offending}"
    )


def test_competition_render_backcompat_empty(tmp_path):
    """The competition render must not crash on a spec with no competitors — it
    renders an empty/placeholder matrix (G-A2). Guards the renderer's empty path
    so a v1 spec can still ask for the view."""
    proj = _scaffold(tmp_path)  # no competitors
    g = build_graph(proj)
    html_body = render_html.competition(g)  # must not raise
    assert isinstance(html_body, str) and html_body, "empty competition render must return a non-empty string"
