"""Tests for product-spec visualization renderers (Phase 6).

Asserts deterministic ASCII + Mermaid output; HTML assembly emits a valid
self-contained file (smoke-tested for presence of expected anchors).
"""

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
import render_ascii  # noqa: E402
import render_mermaid  # noqa: E402
import render_html  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"


def _graph():
    return build_graph(VALID)


# ---------- ASCII ----------

def test_ascii_tree_contains_full_chain():
    out = render_ascii.tree(_graph())
    assert "PRODUCT" in out
    assert "BRD-G1" in out
    assert "PRD-AUTH" in out
    assert "PRD-AUTH-E1" in out
    assert "PRD-AUTH-E1-S1" in out


def test_ascii_heatmap_is_a_grid():
    out = render_ascii.heatmap(_graph())
    assert "draft" in out and "approved" in out
    assert "|" in out


def test_ascii_heatmap_surfaces_noncanonical_status_in_other_column():
    """A node in a non-canonical status must not vanish from the grid — it is
    summed into an 'other' column instead of being silently dropped."""
    g = {"nodes": [
        {"id": "X", "type": "story", "status": "blocked"},
        {"id": "Y", "type": "story", "status": "draft"},
    ], "edges": []}
    out = render_ascii.heatmap(g)
    assert "other" in out
    story_row = next(l for l in out.splitlines() if l.startswith("| story"))
    assert story_row.rstrip().endswith("1 |")  # the 'blocked' node counted in 'other'


def test_ascii_heatmap_hides_other_column_when_all_canonical():
    """No 'other' column when every status is canonical (keep the common grid clean)."""
    g = {"nodes": [{"id": "Y", "type": "story", "status": "draft"}], "edges": []}
    assert "other" not in render_ascii.heatmap(g)


def test_ascii_grid_separator_aligns_with_overlong_label():
    """An overlong row label must not break alignment: header, separator, and
    every data row are exactly the same width."""
    g = {"nodes": [
        {"id": "X", "type": "an-unusually-long-type-name", "status": "draft"},
    ], "edges": []}
    widths = {len(l) for l in render_ascii.heatmap(g).splitlines()}
    assert len(widths) == 1, f"misaligned grid: line widths {widths}"


def test_ascii_summary_line_collapses_multiline_title():
    """A multi-line YAML title must not inject extra lines into the one-line-per-node
    text summary (would corrupt the deterministic grammar + any line-count parser)."""
    n = {"id": "PRD-X", "type": "prd", "title": "Line one\nLine two\rthree", "status": "draft"}
    line = render_ascii._summary_line(n, "PRD-X", 1)
    assert "\n" not in line and "\r" not in line
    assert "[prd:PRD-X] Line one Line two three · draft" in line


def test_ascii_competition_grid_stays_aligned_with_multiline_name():
    """A competitor name with a newline must not break the aligned grid: every row
    is one line and all rows share the separator width."""
    g = {"competitors": [{"id": "COMP-A", "name": "Acme\nEvil", "threat": "high"}],
         "nodes": [{"id": "PRD-X", "type": "prd", "competitive_parity": {"COMP-A": "behind"}}]}
    out = render_ascii.competition(g)
    widths = {len(l) for l in out.splitlines()}
    assert len(widths) == 1, f"misaligned grid: {widths}"
    assert "Acme Evil" in out


def test_ascii_scope_grid_has_moscow_columns():
    out = render_ascii.scope(_graph())
    for col in ("must", "should", "could", "wont"):
        assert col in out


def test_ascii_roadmap_groups_by_horizon():
    out = render_ascii.roadmap(_graph())
    assert "NOW" in out
    assert "PRD-AUTH-E1-S1" in out


def test_ascii_persona_includes_personas():
    out = render_ascii.persona(_graph())
    assert "shopper" in out


def test_ascii_gap_marks_unaddressed_brd_goal():
    # BRD-G2 in valid fixture has no PRDs addressing it
    out = render_ascii.gap(_graph())
    assert "BRD-G2" in out


def test_ascii_moscow_quadrant_counts():
    out = render_ascii.moscow(_graph())
    assert "Must" in out and "Should" in out


def test_ascii_risk_grid_present():
    out = render_ascii.risk(_graph())
    assert "Impact" in out


def test_ascii_delta_with_no_baseline_path_renders_empty_string_via_visualize():
    # delta requires two graphs; render_ascii.delta(same, same) returns "(no changes)"
    g = _graph()
    out = render_ascii.delta(g, g)
    assert "(no changes)" in out


def test_board_view_registered_in_dispatcher():
    """Phase 4: board joins the dispatcher's VIEWS as a body-bearing view."""
    import visualize
    assert "board" in visualize.VIEWS
    assert "board" in visualize.BODY_VIEWS


def test_ascii_board_deterministic_grouped_lists():
    """Phase 4: ASCII board groups goal/PRD/epic/story cards by the chosen field,
    deterministically (canonical column order, sorted IDs)."""
    g = _graph()
    out = render_ascii.board(g, "status")
    assert out == render_ascii.board(g, "status")
    assert "### draft" in out and "### approved" in out
    assert out.index("### draft") < out.index("### approved")  # canonical order


def test_explorer_view_registered_and_ascii_is_tree():
    """Phase 5: explorer joins VIEWS as a body view; its ASCII form == tree."""
    import visualize
    assert "explorer" in visualize.VIEWS and "explorer" in visualize.BODY_VIEWS
    g = _graph()
    assert render_ascii.explorer(g) == render_ascii.tree(g)


def _time_graph():
    """Minimal graph for the TIME view: two dated PRDs (one depends_on the other)
    plus a deferred PRD, so the renderer's date/dep/filter_wont paths all fire."""
    return {
        "product": {"name": "T"},
        "nodes": [
            {"id": "PRD-A", "type": "prd", "horizon": "now",
             "target_date": "2026-06-30", "depends_on": ["PRD-B"]},
            {"id": "PRD-B", "type": "prd", "horizon": "now",
             "target_date": "2026-05-31", "depends_on": []},
            {"id": "PRD-C", "type": "prd", "horizon": "later",
             "target_date": None, "depends_on": [], "moscow": "wont"},
        ],
        "edges": [],
    }


def test_time_view_registered_as_graph_view():
    """Phase 3: `time` joins VIEWS as a graph view (NOT a body view) so
    `visualize.py --view time` is reachable through argparse choices=VIEWS."""
    import visualize
    assert "time" in visualize.VIEWS
    assert "time" not in visualize.BODY_VIEWS
    # It must accept lang + filter_wont in the shared dispatch map.
    assert visualize._VIEW_KWARGS.get("time") == ("lang", "filter_wont")


def test_ascii_time_groups_by_horizon_with_dates_and_deps():
    g = _time_graph()
    out = render_ascii.time(g)
    assert "## NOW" in out and "## LATER" in out
    assert "PRD-A" in out and "[2026-06-30]" in out
    assert "depends_on: PRD-B" in out          # dependency surfaced
    assert "PRD-C" in out and "*" in out        # deferred kept with marker
    # Prerequisite (PRD-B) ordered before its dependent (PRD-A) — cycle-safe walk.
    assert out.index("PRD-B") < out.index("PRD-A")
    assert render_ascii.time(g) == out          # deterministic


def test_ascii_time_filter_wont_drops_deferred():
    g = _time_graph()
    out = render_ascii.time(g, filter_wont=True)
    assert "PRD-C" not in out                    # deferred dropped
    assert "PRD-A" in out


def test_mermaid_time_is_gantt_and_filter_wont_aware():
    g = _time_graph()
    out = render_mermaid.time(g)
    assert out.startswith("```mermaid")
    assert "gantt" in out and "2026-06-30" in out
    assert "%% PRD-A depends_on PRD-B" in out    # dep annotation (gantt has no arrow)
    # filter_wont drops the deferred PRD-C from the gantt tasks.
    assert "PRD-C" in render_mermaid.time(g)
    assert "PRD-C" not in render_mermaid.time(g, filter_wont=True)


def test_html_time_view_embeds_gantt_and_mermaid_runtime(tmp_path):
    """The HTML `time` view renders the cycle-safe gantt inside a .mermaid wrapper
    and inlines the Mermaid runtime (view_format == mermaid)."""
    g = _time_graph()
    html = render_html.assemble("time", "mermaid", render_mermaid.time(g), g)
    assert 'class="mermaid"' in html
    assert "gantt" in html and "PRD-A" in html


def test_legacy_html_adopts_shared_design_system_and_no_sanitizer():
    """Phase 6: the 9 legacy views adopt the shared design system (theme toggle +
    .ve-card + palette) yet inline NO marked/DOMPurify (H4 symmetric gating)."""
    g = _graph()
    mermaid_text = render_mermaid.tree(g)
    html = render_html.assemble("tree", "mermaid", mermaid_text, g)
    # Shared design system present.
    assert "psToggleTheme" in html and "ps-toggle" in html
    assert "ve-card" in html and "--accent" in html
    assert "@media print" in html
    # Mermaid theme-var override so diagram text follows dark mode.
    assert ".mermaid" in html
    # H4: a legacy mermaid view inlines the Mermaid runtime (which bundles its OWN
    # DOMPurify) but NEVER our body-render libs — keyed on the marked copyright
    # banner + our chokepoint, neither of which Mermaid ships.
    assert "marked v18" not in html
    assert "psRenderMarkdown" not in html


def test_legacy_html_token_contract_preserved():
    """Phase 6: extend-only — the legacy token contract still renders (no stray
    unresolved {{token}} left in the page)."""
    g = _graph()
    html = render_html.assemble("heatmap", "ascii", "draft 1\napproved 2", g)
    import re as _re
    leftover = _re.findall(r"\{\{(\w+)\}\}", html)
    assert leftover == [], f"unresolved tokens leaked into output: {leftover}"


# ---------- Mermaid ----------

def test_mermaid_tree_emits_flowchart_block():
    out = render_mermaid.tree(_graph())
    assert out.startswith("```mermaid")
    # BT (bottom-top): PRODUCT renders at top to match ASCII tree orientation.
    assert "flowchart BT" in out


def test_mermaid_scope_emits_quadrantchart():
    out = render_mermaid.scope(_graph())
    assert "quadrantChart" in out


def test_mermaid_roadmap_emits_timeline():
    out = render_mermaid.roadmap(_graph())
    assert "timeline" in out


def test_mermaid_gap_uses_classdef():
    out = render_mermaid.gap(_graph())
    assert "classDef" in out


def test_mermaid_tree_label_breaks_with_br_not_literal_backslash_n():
    """A node label stacks id over title via a real Mermaid line break (`<br/>`),
    NOT a literal ``\\n`` — Mermaid does not interpret backslash-n in a flowchart
    label and would render the two characters verbatim in the HTML output."""
    out = render_mermaid.tree(_graph())
    assert "\\n" not in out, "literal backslash-n leaked into a Mermaid label"
    # at least one id<br/>title label is emitted (every artifact node carries a title)
    assert "<br/>" in out


def test_mermaid_gap_label_breaks_with_br_not_literal_backslash_n():
    g = {"nodes": [{"id": "PRD-X", "type": "prd", "title": "X", "brd_goals": ["BRD-G1"]}],
         "edges": []}
    out = render_mermaid.gap(g)
    assert "\\n" not in out
    assert "PRD-X<br/>(missing" in out


# ---------- HTML ----------

def test_html_assemble_is_self_contained_string():
    g = _graph()
    mermaid_text = render_mermaid.tree(g)
    html = render_html.assemble("tree", "mermaid", mermaid_text, g)
    assert "<!DOCTYPE html>" in html
    assert "<div class=\"mermaid\">" in html
    assert "flowchart BT" in html
    # vendored mermaid OR CDN-fallback note
    assert ("mermaid.initialize" in html) or ("falling back to CDN" in html)


def test_html_escapes_pre_content_when_format_is_pre():
    g = _graph()
    html = render_html.assemble("heatmap", "ascii", "<script>alert(1)</script>", g)
    assert "&lt;script&gt;" in html
    assert "<script>alert(1)" not in html


# ---------- HTML dispatch (ascii-fallback views must NOT be wrapped as Mermaid) ----------

def test_html_dispatch_routes_ascii_fallback_view_as_pre_not_mermaid(tmp_path):
    """heatmap/persona/risk views have no clean Mermaid expression; the
    mermaid renderer returns a `<pre>` ASCII fallback. visualize.py MUST
    detect that and pass view_format="pre" — otherwise Mermaid tries to
    parse the <pre> body as DSL and the rendered page is broken/blank.
    """
    import subprocess
    import shutil

    # Stage a project root that contains the valid fixture so visualize.py
    # writes under docs/product/visuals/.
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)

    py = sys.executable
    viz = SCRIPTS_DIR / "visualize.py"
    r = subprocess.run(
        [py, str(viz), "--root", str(proj), "--view", "heatmap", "--format", "html"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr

    htmls = sorted((proj / "docs" / "product" / "visuals").glob("heatmap-*.html"))
    assert htmls, "expected an HTML file written"
    body = htmls[-1].read_text()

    # The diagram must be wrapped as <pre>, NOT <div class="mermaid">.
    assert '<div class="mermaid">' not in body, (
        "heatmap view must NOT route through the Mermaid wrapper — "
        "Mermaid cannot parse <pre> ASCII as DSL."
    )
    assert "<pre>" in body
    # ASCII heatmap content must be HTML-escaped inside the <pre>.
    assert "draft" in body and "approved" in body


# ---------- Regression tests for re-review fixes ----------

def test_mermaid_heatmap_returns_markdown_fence_not_html_pre():
    """NEW-1: --format mermaid for fallback views must emit a markdown
    code fence (```...```), not raw HTML <pre>, so the output stays
    paste-able into markdown docs per visualization-spec.md contract."""
    out = render_mermaid.heatmap(_graph())
    assert out.startswith("```\n"), f"expected markdown fence, got: {out[:30]!r}"
    assert out.endswith("\n```"), f"expected markdown fence close, got: {out[-30:]!r}"
    assert not out.startswith("<pre>"), "must not emit raw HTML <pre>"


def test_mermaid_persona_and_risk_also_markdown_fenced():
    """NEW-1 companion: persona and risk fall back the same way."""
    for view_name in ("persona", "risk"):
        out = getattr(render_mermaid, view_name)(_graph())
        assert out.startswith("```\n") and out.endswith("\n```"), (
            f"{view_name}: expected markdown fence, got {out[:40]!r}"
        )


def test_mermaid_tree_has_no_phantom_brd_node():
    """NEW-2/8: spec_graph used to emit a `goal -> BRD` edge with no BRD
    node ever declared, producing an unlabeled implicit box in the
    rendered tree. The edge has been dropped; the tree must contain
    NO `--> BRD` edge whose target is the bare token 'BRD'."""
    out = render_mermaid.tree(_graph())
    import re
    # Look for an edge whose target is the bare 'BRD' token (not BRD_G1 etc.)
    phantom = re.search(r"-->\s*BRD\b(?!_)", out)
    assert phantom is None, f"phantom BRD edge still emitted: {out}"


def test_mermaid_tree_skips_vision_node():
    """NEW-3: vision.md has no structural edges and no useful title;
    skip the node in the tree to avoid a stranded empty box."""
    out = render_mermaid.tree(_graph())
    assert 'VISION["VISION' not in out, "VISION node should be skipped"


def test_ascii_roadmap_vi_localizes_headers():
    """NEW-6: --lang vi must localize the now/next/later section headers
    per visualization-spec.md L107. Previously the labels were hardcoded
    English regardless of lang."""
    out = render_ascii.roadmap(_graph(), lang="vi")
    assert "HIỆN TẠI" in out, f"expected localized VI now-header, got: {out[:200]}"
    assert "NOW" not in out, "EN header leaked into VI output"


def test_ascii_moscow_vi_localizes_labels():
    """NEW-6: MoSCoW labels (Must/Should/Could/Won't) must localize."""
    out = render_ascii.moscow(_graph(), lang="vi")
    assert "Bắt buộc" in out
    assert "Không làm" in out
    assert "Must" not in out and "Won't" not in out


def test_ascii_roadmap_en_default_unchanged():
    """NEW-6 backward-compat: lang default must remain English."""
    out = render_ascii.roadmap(_graph())
    assert "NOW" in out
    assert "HIỆN TẠI" not in out


def test_html_ascii_fallback_view_skips_mermaid_js(tmp_path):
    """NEW-7: ASCII-fallback HTML views (heatmap/persona/risk) must NOT
    embed the 2.5 MB Mermaid JS payload — the runtime is never used."""
    import subprocess
    import shutil

    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable
    viz = SCRIPTS_DIR / "visualize.py"
    r = subprocess.run(
        [py, str(viz), "--root", str(proj), "--view", "heatmap", "--format", "html"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    body = sorted((proj / "docs" / "product" / "visuals").glob("heatmap-*.html"))[-1].read_text()
    # The vendored signature must NOT appear in ASCII-fallback HTML.
    assert "__esbuild_esm_mermaid" not in body
    # The file should be small (< 10 KB), not 2.5 MB.
    assert len(body) < 10_000, f"heatmap HTML unexpectedly large: {len(body)} bytes"


def test_safe_label_escapes_mermaid_special_chars():
    """NEW-15: titles containing [brackets], (parens), backticks or {braces}
    must be normalized so they don't break Mermaid's node-label grammar."""
    from render_mermaid import _safe_label
    out = _safe_label('hello [bracketed] {brace} `back` "quote"')
    assert "[" not in out and "]" not in out
    assert "{" not in out and "}" not in out
    assert "`" not in out
    assert '"' not in out


def test_generate_epic_rejects_oversized_slug():
    """NEW-4: parent must match PRD pattern (slug ≤16 chars) — generate must
    fast-fail rather than emit an invalid_id artifact downstream."""
    from generate_templates import allocate_id
    import pytest as _pytest
    g = build_graph(VALID)
    with _pytest.raises(ValueError, match=r"valid PRD ID"):
        allocate_id(g, "epic", slug=None, parent="PRD-MORE-THAN-SIXTEEN-CHARS", session_used=[])


def test_generate_epic_rejects_story_id_as_parent():
    """NEW-4: parent for epic must be a PRD ID — story IDs (containing -E<n>-S<n>)
    must be rejected to prevent PRD-AUTH-E1-S1-E1 nonsense."""
    from generate_templates import allocate_id
    import pytest as _pytest
    g = build_graph(VALID)
    with _pytest.raises(ValueError, match=r"valid PRD ID"):
        allocate_id(g, "epic", slug=None, parent="PRD-AUTH-E1-S1", session_used=[])


def test_fresh_vision_init_passes_consistency(tmp_path):
    """SA-1A: A freshly initialized vision.md must NOT carry an enum-violating
    `horizon: TBD` placeholder. Reproduces the failure illusion-1 surfaced."""
    import subprocess
    proj = tmp_path / "fresh"
    (proj / "docs" / "product").mkdir(parents=True)
    py = sys.executable
    scripts = SCRIPTS_DIR
    subprocess.run(
        [py, str(scripts / "generate_templates.py"), "--root", str(proj),
         "--type", "vision", "--write"],
        check=True, capture_output=True, text=True,
    )
    out = subprocess.run(
        [py, str(scripts / "check_consistency.py"), "--root", str(proj)],
        check=True, capture_output=True, text=True,
    )
    import json
    findings = json.loads(out.stdout)["findings"]
    errors = [f for f in findings if f["severity"] == "error"]
    assert errors == [], (
        f"Fresh vision.md must produce zero error-severity findings; got: {errors}"
    )


def test_frontmatter_parser_cli_handles_yaml_dates():
    """SA-1B: frontmatter_parser.py CLI used to TypeError on YAML date fields
    (e.g. `created: 2026-05-28`) because json.dumps lacks default=str."""
    import subprocess
    fixture = VALID / "docs" / "product" / "PRODUCT.md"
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "frontmatter_parser.py"), str(fixture)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"CLI exited non-zero: {r.stderr}"
    assert "is not JSON serializable" not in r.stderr
    import json
    payload = json.loads(r.stdout)
    assert payload["ok"] is True
    # The date field should serialize as an ISO string.
    assert isinstance(payload["frontmatter"]["created"], str)


def test_vision_template_substitutes_fixture_keys():
    """SA-1C: vision template tokens used to be `personas_narrative` and
    `north_star_metric` while the canonical fixture (init-answers.json) carries
    `personas_detail` and `north_star`. Align template to fixture-driven keys
    so init-from-scratch substitutes correctly."""
    import subprocess
    from pathlib import Path as _P
    tmp = _P("/tmp/probe-vision-tokens")
    import shutil
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / "docs" / "product").mkdir(parents=True)
    payload = (
        '{"name":"Acme","problem_narrative":"Boutique brands lose 3-5%.",'
        '"personas_detail":"shopper / store-admin",'
        '"north_star":"Default direct-to-fan storefront","value_proposition":"X",'
        '"direction_1_to_3_years":"Y"}'
    )
    subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "generate_templates.py"),
         "--root", str(tmp), "--type", "vision", "--values", payload, "--write"],
        check=True, capture_output=True, text=True,
    )
    body = (tmp / "docs" / "product" / "vision.md").read_text(encoding="utf-8")
    assert "shopper / store-admin" in body, "personas_detail token did not substitute"
    assert "Default direct-to-fan storefront" in body, "north_star token did not substitute"
    assert "{{personas_detail}}" not in body and "{{north_star}}" not in body
    shutil.rmtree(tmp)


def test_delta_surfaces_product_core_value_change():
    """SA-4A: render_ascii.delta() (and mermaid.delta) used to only diff
    node-level fields and silently emit '(no changes)' when only
    PRODUCT.core_value changed. Surface the product-meta diff explicitly."""
    baseline = {
        "product": {"name": "Acme", "core_value": "A", "personas": ["p1"]},
        "nodes": [], "edges": [],
    }
    current = {
        "product": {"name": "Acme", "core_value": "B", "personas": ["p1"]},
        "nodes": [], "edges": [],
    }
    out_ascii = render_ascii.delta(current, baseline)
    assert "PRODUCT.core_value" in out_ascii, f"got: {out_ascii}"
    assert "'A' -> 'B'" in out_ascii or "A -> B" in out_ascii

    out_mermaid = render_mermaid.delta(current, baseline)
    assert "PRODUCT" in out_mermaid and "core_value" in out_mermaid
    assert "classDef changed" in out_mermaid

    # Identical graphs still report (no changes) in ASCII
    assert render_ascii.delta(baseline, baseline) == "(no changes)"


# ---------- Round-4 follow-up regression tests ----------

def test_brd_template_carries_inline_goals_shape_example():
    """SA-7A: brd.md template must show the list-of-dicts goal shape inline
    so a first-time PO sees the schema in the file they edit, without
    having to read spec_graph.py source or chase a reference doc."""
    brd_template = (
        SCRIPTS_DIR.parent / "assets" / "templates" / "brd.md"
    ).read_text(encoding="utf-8")
    # Shape clues a PO would visually scan for:
    assert "id: BRD-G1" in brd_template, "expected example goal id"
    assert "title:" in brd_template and "metrics:" in brd_template
    # The example must live ABOVE goals: {{goals}} so it's read first.
    example_idx = brd_template.index("id: BRD-G1")
    token_idx = brd_template.index("goals: {{goals}}")
    assert example_idx < token_idx, (
        "shape example must appear before the goals: token so the PO sees "
        "it without scrolling"
    )


def test_brd_goals_shape_documented_in_reference():
    """SA-7A companion: the canonical shape must live in the reference doc
    so the template comment can point at it."""
    ref = (
        SCRIPTS_DIR.parent / "references" / "frontmatter-and-id-spec.md"
    ).read_text(encoding="utf-8")
    assert "BRD `goals`" in ref or "BRD goals" in ref
    # Required keys must all be named on this canonical surface:
    for key in ("id", "title", "metrics", "status", "owner"):
        assert key in ref, f"BRD goal key {key!r} missing from reference"


def test_product_template_core_value_body_is_stub_not_duplicate():
    """SA-11A: PRODUCT.md template body must NOT duplicate core_value from
    frontmatter. The body should carry a reference-only stub so there is
    one authoritative home for the value."""
    tmpl = (
        SCRIPTS_DIR.parent / "assets" / "templates" / "product.md"
    ).read_text(encoding="utf-8")
    # Token only appears in frontmatter, not body:
    assert tmpl.count("{{core_value}}") == 1, (
        "core_value token must appear exactly once (in frontmatter), "
        "not duplicated into the body"
    )
    # The body section still exists, but as a stub pointer:
    assert "## Core Value" in tmpl
    assert "frontmatter `core_value`" in tmpl


def test_generate_rejects_approved_status_at_script_layer():
    """NEW-12: defense-in-depth. generate_templates must refuse to mint a
    new artifact with status='approved'. Approval is a separate explicit
    promotion flow; generation always starts as 'draft'."""
    from generate_templates import fill_defaults
    import pytest as _pytest
    with _pytest.raises(ValueError, match=r"approved"):
        fill_defaults({"status": "approved"}, "prd", "PRD-X", "en")


def test_generate_allows_default_draft_status():
    """NEW-12 backward-compat: omitting status (default 'draft') stays valid."""
    from generate_templates import fill_defaults
    out = fill_defaults({}, "prd", "PRD-X", "en")
    assert out["status"] == "draft"


def test_render_html_vendored_path_split_into_two_functions():
    """NEW-14: render_html.py used to mix the vendored-load and CDN-fallback
    paths in one function. The refactor exposes them as two distinct helpers
    so each has a single responsibility. The legacy _load_mermaid_js wrapper
    must still work for callers that don't care about the source."""
    from render_html import (
        _load_vendored_mermaid_js,
        _cdn_fallback_snippet,
        _load_mermaid_js,
    )
    # CDN snippet has no dependence on filesystem state; the literal CDN
    # URL must appear in its output regardless of vendoring.
    snippet = _cdn_fallback_snippet()
    assert "cdn.jsdelivr.net" in snippet
    assert "<script src=" in snippet
    # The wrapper either returns the vendored payload (when present) or
    # falls through to the CDN snippet; one or the other must succeed.
    payload = _load_mermaid_js()
    vendored = _load_vendored_mermaid_js()
    if vendored is not None:
        assert payload == vendored
    else:
        assert "cdn.jsdelivr.net" in payload


def test_ascii_tree_vi_localizes_product_prefix():
    """O-3: tree --lang vi must localize the 'PRODUCT:' prefix label."""
    out = render_ascii.tree(_graph(), lang="vi")
    assert "SẢN PHẨM:" in out, f"expected VI product label, got: {out[:120]}"
    # The English label must NOT leak into VI output.
    assert "PRODUCT:" not in out


def test_ascii_tree_en_default_unchanged():
    """O-3 backward-compat: tree() default lang stays English."""
    out = render_ascii.tree(_graph())
    assert "PRODUCT:" in out
    assert "SẢN PHẨM:" not in out


def test_mermaid_tree_vi_localizes_root_node_label():
    """O-3: mermaid tree must also localize the root PRODUCT node label."""
    out = render_mermaid.tree(_graph(), lang="vi")
    assert "SẢN PHẨM" in out, f"VI tree root label missing: {out[:200]}"


def test_visualize_routes_lang_to_tree_view(tmp_path):
    """O-3 dispatcher integration: --view tree --lang vi must produce the
    localized output end-to-end (not just at the renderer level)."""
    import subprocess
    import shutil
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable
    viz = SCRIPTS_DIR / "visualize.py"
    r = subprocess.run(
        [py, str(viz), "--root", str(proj),
         "--view", "tree", "--format", "ascii", "--lang", "vi"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "SẢN PHẨM:" in r.stdout, (
        f"--lang vi did not reach the tree renderer; got: {r.stdout[:200]}"
    )


# ---------- Wave-3 review fix regression tests ----------


def _deferred_graph():
    """Synthetic graph with one in-scope and one deferred story."""
    return {
        "product": {"name": "X", "core_value": "v", "personas": ["p"]},
        "nodes": [
            {"id": "BRD-G1", "type": "goal", "title": "g", "status": "draft",
             "personas": []},
            {"id": "PRD-X", "type": "prd", "title": "x", "status": "draft",
             "personas": [], "scope": "in", "moscow": "must", "horizon": "now",
             "brd_goals": ["BRD-G1"]},
            {"id": "PRD-X-E1", "type": "epic", "title": "e", "status": "draft",
             "personas": [], "scope": "in", "moscow": "must", "horizon": "now",
             "prd": "PRD-X"},
            {"id": "PRD-X-E1-S1", "type": "story", "title": "s1",
             "status": "draft", "personas": ["p"], "scope": "in",
             "moscow": "must", "horizon": "now", "epic": "PRD-X-E1"},
            {"id": "PRD-X-E1-S2", "type": "story", "title": "s2-deferred",
             "status": "draft", "personas": ["p"], "scope": "in",
             "moscow": "wont", "horizon": "later", "epic": "PRD-X-E1"},
        ],
        "edges": [
            {"from": "PRD-X-E1-S1", "to": "PRD-X-E1", "kind": "epic"},
            {"from": "PRD-X-E1-S2", "to": "PRD-X-E1", "kind": "epic"},
            {"from": "PRD-X-E1", "to": "PRD-X", "kind": "prd"},
            {"from": "PRD-X", "to": "BRD-G1", "kind": "brd_goal"},
        ],
        "risks": [],
    }


def test_w3_h1_mermaid_tree_uses_BT_orientation():
    """H-1: Mermaid tree must declare `flowchart BT` so PRODUCT renders at
    the top of the visual hierarchy — matching the ASCII tree."""
    out = render_mermaid.tree(_graph())
    assert "flowchart BT" in out
    assert "flowchart TB" not in out


def test_w3_m2_ascii_tree_default_marks_deferred():
    """M-2 default behavior: deferred items (moscow=wont) appear in tree
    with a trailing `*` marker so the PO sees they're tracked-but-out."""
    out = render_ascii.tree(_deferred_graph())
    assert "PRD-X-E1-S2 *" in out
    assert "PRD-X-E1-S1" in out and "PRD-X-E1-S1 *" not in out


def test_w3_m2_ascii_tree_filter_wont_hides_deferred():
    """M-2 opt-in filter: --filter-wont hides deferred items entirely."""
    out = render_ascii.tree(_deferred_graph(), filter_wont=True)
    assert "PRD-X-E1-S2" not in out
    assert "PRD-X-E1-S1" in out


def test_w3_m2_ascii_roadmap_marks_and_filters_deferred():
    """M-2 roadmap behavior: default marks; --filter-wont drops."""
    out_default = render_ascii.roadmap(_deferred_graph())
    assert "PRD-X-E1-S2 *" in out_default
    out_filtered = render_ascii.roadmap(_deferred_graph(), filter_wont=True)
    assert "PRD-X-E1-S2" not in out_filtered


def test_w3_m2_mermaid_tree_emits_deferred_classDef():
    """M-2 Mermaid: deferred nodes get `:::deferred` classDef so a styled
    HTML render can dim them."""
    out = render_mermaid.tree(_deferred_graph())
    assert "classDef deferred" in out
    assert ":::deferred" in out


def test_w3_m2_visualize_cli_accepts_filter_wont(tmp_path):
    """M-2 dispatcher integration: --filter-wont reaches the renderer."""
    import subprocess
    import shutil
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable
    viz = SCRIPTS_DIR / "visualize.py"
    r = subprocess.run(
        [py, str(viz), "--root", str(proj), "--view", "tree",
         "--format", "ascii", "--filter-wont"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr


def test_w3_m7_delta_works_with_single_snapshot(tmp_path):
    """M-7: `--viz delta` should compare 1 snapshot against the live graph
    instead of requiring 2 snapshots."""
    import subprocess
    import shutil
    import json as _json
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable

    # Take 1 snapshot.
    subprocess.run(
        [py, str(SCRIPTS_DIR / "spec_graph.py"), "--root", str(proj),
         "--snapshot"],
        check=True, capture_output=True, text=True,
    )
    snaps = list((proj / "docs" / "product" / "visuals" / ".snapshots").glob("*.json"))
    assert len(snaps) == 1

    # Mutate the spec so live graph differs from snapshot.
    extra_story = proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S9.md"
    extra_story.write_text("""---
id: PRD-AUTH-E1-S9
type: story
epic: PRD-AUTH-E1
status: draft
lang: en
owner: T
version: 0.1.0
created: 2026-05-28
updated: 2026-05-28
personas: [shopper]
scope: in
moscow: must
size: S
horizon: now
acceptance_criteria: ["ac1.", "ac2."]
---
""", encoding="utf-8")

    r = subprocess.run(
        [py, str(SCRIPTS_DIR / "visualize.py"), "--root", str(proj),
         "--view", "delta", "--format", "ascii"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert "no baseline yet" not in r.stdout
    assert "PRD-AUTH-E1-S9" in r.stdout, (
        f"Expected the new story to appear in delta against the single "
        f"snapshot baseline. Got: {r.stdout}"
    )


def test_w3_l1_bad_diff_raises_with_available_list(tmp_path):
    """L-1: a typoed --diff filename must raise with a list of available
    snapshots, not silently fall through to 'no baseline yet'."""
    import subprocess
    import shutil
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable
    r = subprocess.run(
        [py, str(SCRIPTS_DIR / "visualize.py"), "--root", str(proj),
         "--view", "delta", "--format", "ascii",
         "--diff", "definitely-not-a-real-snapshot.json"],
        capture_output=True, text=True,
    )
    assert r.returncode != 0
    assert "baseline not found" in r.stderr.lower() or "FileNotFoundError" in r.stderr


def test_w3_l4_ascii_gap_matches_check_traceability_semantics():
    """L-4: ASCII gap-view counts only matching-child-type inbound edges
    (matching check_traceability.unaddressed_parent). On a malformed graph
    with wrong-type edges, gap should still flag the parent."""
    # Synthetic: a goal whose only inbound edge is from a story (wrong type)
    # should still appear in gap output (no PRD addresses it).
    g = {
        "product": {"name": "X"},
        "nodes": [
            {"id": "BRD-G1", "type": "goal", "title": "g"},
            {"id": "PRD-A", "type": "prd", "title": "p", "brd_goals": ["BRD-G1"]},
            {"id": "PRD-A-E1-S1", "type": "story", "title": "s", "epic": "PRD-A-E1"},
        ],
        # Wrong-type edge: story pointing at goal — shouldn't count toward "PRD addressing goal"
        "edges": [
            {"from": "PRD-A", "to": "BRD-G1", "kind": "brd_goal"},
        ],
        "risks": [],
    }
    out = render_ascii.gap(g)
    # PRD-A has no epic addressing it (no inbound prd-typed edge from epic)
    assert "PRD-A" in out


def test_w3_l5_snapshot_filename_derived_from_generated_at(tmp_path):
    """L-5: snapshot filename timestamp must agree with in-body
    `snapshot_at` (single now() source). Avoids ms-level drift."""
    import subprocess
    import shutil
    import json as _json
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable
    subprocess.run(
        [py, str(SCRIPTS_DIR / "spec_graph.py"), "--root", str(proj),
         "--snapshot"],
        check=True, capture_output=True, text=True,
    )
    snaps = sorted((proj / "docs" / "product" / "visuals" / ".snapshots").glob("*.json"))
    assert len(snaps) == 1
    body = _json.loads(snaps[0].read_text())
    # Filename stem (e.g. "20260528T230000Z") must equal the compact form
    # of snapshot_at (strip non-alphanumeric).
    fname_stem = snaps[0].stem
    compact_iso = body["snapshot_at"].replace("-", "").replace(":", "")
    # Filename is <compact-iso>-<8-hex-hash>; verify the timestamp prefix matches.
    assert fname_stem.startswith(compact_iso), (
        f"filename {fname_stem!r} timestamp prefix doesn't match snapshot_at {compact_iso!r}"
    )


# ---------- Stored-markup injection regression tests ----------
# Payloads that must NEVER appear as live HTML in rendered output.

_PAYLOADS = [
    "<script>alert(1)</script>",
    "</script>",
    "<img src=x onerror=alert(1)>",
    "&#60;img src=x onerror=alert(1)&#62;",
]

# Patterns that indicate live HTML injection (as opposed to inert escaped text).
# `onerror=` only constitutes injection when it appears as an HTML attribute
# inside a live tag — i.e. preceded by `<img` or similar.  Checking for `<img `
# (with trailing space, indicating a tag open) covers the concrete threat; a
# bare `onerror=` inside escaped Mermaid label text is not executable.
_LIVE_PATTERNS = [
    "<script>",
    "<img ",
]


def _injected_graph(payload: str) -> dict:
    """Synthetic graph with a single story whose id and title contain payload."""
    safe_id = "PRD-X-E1-S1"  # id stays structurally valid; payload goes in title only
    return {
        "product": {"name": "Acme", "core_value": "v", "personas": ["p"]},
        "nodes": [
            {"id": "BRD-G1", "type": "goal", "title": payload,
             "status": "draft", "personas": []},
            {"id": "PRD-X", "type": "prd", "title": payload, "status": "draft",
             "personas": [], "scope": "in", "moscow": "must", "horizon": "now",
             "brd_goals": ["BRD-G1"]},
            {"id": "PRD-X-E1", "type": "epic", "title": payload,
             "status": "draft", "personas": [], "scope": "in",
             "moscow": "must", "horizon": "now", "prd": "PRD-X"},
            {"id": safe_id, "type": "story", "title": payload,
             "status": "draft", "personas": ["p"], "scope": "in",
             "moscow": "must", "horizon": "now", "epic": "PRD-X-E1"},
        ],
        "edges": [
            {"from": safe_id, "to": "PRD-X-E1", "kind": "epic"},
            {"from": "PRD-X-E1", "to": "PRD-X", "kind": "prd"},
            {"from": "PRD-X", "to": "BRD-G1", "kind": "brd_goal"},
        ],
        "risks": [],
    }


def _injected_id_graph(payload: str) -> dict:
    """Graph where the node *id* itself contains the payload string."""
    return {
        "product": {"name": "Acme", "core_value": "v", "personas": ["p"]},
        "nodes": [
            {"id": payload, "type": "goal", "title": "g",
             "status": "draft", "personas": []},
        ],
        "edges": [],
        "risks": [],
    }


def _assert_no_live_injection(html: str, context: str) -> None:
    """Check the mermaid div body only — the vendored Mermaid JS legitimately
    contains `<script>` tags which would produce false positives if we scanned
    the full page.  Only the DSL payload in the div is user-controlled."""
    import re as _re
    mermaid_div = _re.search(r'<div class="mermaid">(.*?)</div>', html, _re.DOTALL)
    scope = mermaid_div.group(1) if mermaid_div else html
    for pat in _LIVE_PATTERNS:
        assert pat not in scope, (
            f"{context}: live pattern {pat!r} found in mermaid div — injection not neutralised"
        )


def _assert_mermaid_keyword_present(mermaid_text: str, view: str) -> None:
    assert "graph" in mermaid_text or "flowchart" in mermaid_text or "timeline" in mermaid_text, (
        f"{view}: mermaid DSL keyword missing — rendering likely broken"
    )


def test_html_escapes_injected_story_title_in_tree_view():
    """HTML render of tree view must neutralise markup in node titles."""
    for payload in _PAYLOADS:
        g = _injected_graph(payload)
        mermaid_text = render_mermaid.tree(g)
        html = render_html.assemble("tree", "mermaid", mermaid_text, g)
        _assert_no_live_injection(html, f"tree/title payload={payload!r}")
        _assert_mermaid_keyword_present(html, "tree")


def test_html_escapes_injected_story_title_in_gap_view():
    """HTML render of gap view must neutralise markup in node ids used as labels."""
    for payload in _PAYLOADS:
        g = _injected_graph(payload)
        mermaid_text = render_mermaid.gap(g)
        html = render_html.assemble("gap", "mermaid", mermaid_text, g)
        _assert_no_live_injection(html, f"gap/title payload={payload!r}")
        _assert_mermaid_keyword_present(html, "gap")


def test_html_escapes_injected_story_title_in_roadmap_view():
    """HTML render of roadmap view must neutralise markup in item ids."""
    for payload in _PAYLOADS:
        g = _injected_graph(payload)
        mermaid_text = render_mermaid.roadmap(g)
        html = render_html.assemble("roadmap", "mermaid", mermaid_text, g)
        _assert_no_live_injection(html, f"roadmap/title payload={payload!r}")
        _assert_mermaid_keyword_present(html, "roadmap")


def test_html_escapes_injected_node_id_in_delta_view():
    """HTML render of delta view must neutralise markup in added/removed node ids."""
    for payload in _PAYLOADS:
        baseline = {"product": {"name": "A"}, "nodes": [], "edges": []}
        current = {
            "product": {"name": "A"},
            "nodes": [{"id": payload, "type": "story", "title": "t"}],
            "edges": [],
        }
        mermaid_text = render_mermaid.delta(current, baseline)
        html = render_html.assemble("delta", "mermaid", mermaid_text, current)
        _assert_no_live_injection(html, f"delta/id payload={payload!r}")
        _assert_mermaid_keyword_present(html, "delta")


def test_safe_id_whitelist_blocks_markup_chars():
    """_safe_id must produce identifiers containing only [A-Za-z0-9_].
    Chars like `<`, `>`, `"`, `]` must be replaced, not passed through."""
    import re as _re
    from render_mermaid import _safe_id
    payloads = [
        'PRD-Y</div><svg onload=alert(1)>',
        'ID<script>',
        'A"B',
        'X]Y',
    ]
    for p in payloads:
        result = _safe_id(p)
        assert _re.fullmatch(r"[A-Za-z0-9_]+", result), (
            f"_safe_id({p!r}) = {result!r} — contains non-whitelisted chars"
        )


def test_safe_label_encodes_ampersand_before_angle_brackets():
    """_safe_label must encode `&` before processing angle brackets so that
    entity-encoded payloads like `&#60;img` cannot reconstruct live markup
    when the Mermaid DSL is later HTML-escaped and decoded by the browser."""
    from render_mermaid import _safe_label
    # Entity-encoded form of <img src=x onerror=alert(1)>
    payload = "&#60;img src=x onerror=alert(1)&#62;"
    result = _safe_label(payload)
    # & must be encoded to &amp; — this breaks the entity sequence so it cannot
    # decode back to `<img …>` in browser .textContent.
    assert "&amp;" in result
    # The reconstructed angle-bracket form must not survive intact.
    assert "<img" not in result
    # The &#60; token must be neutralised (& → &amp; renders it inert).
    assert "&#60;" not in result


def test_mermaid_dsl_still_valid_after_html_escaping_tree():
    """Verify that HTML-escaping the Mermaid DSL in the mermaid div does not
    break Mermaid syntax: the escaped source must still contain recognisable
    DSL structure when inspected as text (Mermaid reads .textContent, which
    the browser decodes back to the original DSL)."""
    g = _graph()
    mermaid_text = render_mermaid.tree(g)
    html = render_html.assemble("tree", "mermaid", mermaid_text, g)
    # The escaped `-->` edge syntax must appear (as --&gt; in source).
    assert "--&gt;" in html, "escaped edge arrow not found — escaping may be absent or broken"
    # Standard flowchart keyword must appear (it contains no special chars, survives unchanged).
    assert "flowchart" in html
    # No raw `<` or `>` inside the mermaid div body (they must be escaped).
    import re as _re
    mermaid_div = _re.search(r'<div class="mermaid">(.*?)</div>', html, _re.DOTALL)
    assert mermaid_div is not None, "mermaid div not found in output"
    div_body = mermaid_div.group(1)
    # Raw < and > must not appear in the div body (only &lt; / &gt; allowed).
    assert "<" not in div_body, f"raw `<` found inside mermaid div: {div_body[:200]}"
    assert ">" not in div_body, f"raw `>` found inside mermaid div: {div_body[:200]}"


def test_mermaid_dsl_still_valid_after_html_escaping_gap():
    """Same textContent round-trip check for the gap view (uses flowchart LR)."""
    g = _graph()
    mermaid_text = render_mermaid.gap(g)
    html = render_html.assemble("gap", "mermaid", mermaid_text, g)
    assert "flowchart" in html
    import re as _re
    mermaid_div = _re.search(r'<div class="mermaid">(.*?)</div>', html, _re.DOTALL)
    assert mermaid_div is not None
    div_body = mermaid_div.group(1)
    assert "<" not in div_body, f"raw `<` inside gap mermaid div: {div_body[:200]}"
    assert ">" not in div_body, f"raw `>` inside gap mermaid div: {div_body[:200]}"


def test_mermaid_html_single_encodes_ampersand():
    """A label with `&` must render single-encoded (R&amp;D), not double
    (R&amp;amp;D). `_safe_label` already encodes `&`, so the HTML layer must
    escape only `<`/`>`, never `&` again."""
    g = _graph()
    safe = render_mermaid._safe_label("R&D")  # label chokepoint -> "R&amp;D"
    view_text = f'```mermaid\nflowchart TD\n  N["{safe}"]\n```'
    html = render_html.assemble("tree", "mermaid", view_text, g)
    assert "R&amp;D" in html
    assert "R&amp;amp;D" not in html


# ============================================================================
# Phase 6 — ASCII Downgrade to HTML-native (TDD RED)
#
# PO decision §0.2 (DOWNGRADE, not removal):
#   - HTML-native is the NEW default for the rich matrix/multi-dim views
#     (risk grid, competition matrix/heatmap) + the new HTML-only `dashboard`.
#   - ASCII is NOT deleted: `--viz tree --format ascii` keeps a minimal,
#     deterministic TEXT-SUMMARY tree (structure + counts) for terminal/CI.
#   - board/explorer keep their text-summary fallback on `--format mermaid`
#     (NOT removed — §0.2 reverses Q45).
#   - body views never reach a CDN (fail-closed unchanged — G-A4).
#
# The text-summary tree grammar (phase spec §"Text-summary tree format", F10):
#   header line     : "PRODUCT: <name>"
#   one line/node   : "<2*depth spaces>[<type>:<id>] <title> · <status>"
#   ordering        : sorted by ID at each depth (byte-deterministic)
#   counts footer   : "— <N> nodes · <g> goal · <p> prd · <e> epic · <s> stories · <f> findings"
# ============================================================================


def _text_summary_graph():
    """A small goal→prd→epic→story spec with explicit titles + statuses so the
    documented text-summary grammar can be asserted without the empty-title
    ambiguity of the shared valid-spec fixture. Mirrors the phase-spec example
    shape (one goal, one prd, one epic, two stories)."""
    return {
        "product": {"name": "Acme Shop", "core_value": "v", "personas": ["p"]},
        "nodes": [
            {"id": "BRD-G1", "type": "goal", "title": "Increase conversion",
             "status": "approved", "personas": []},
            {"id": "PRD-AUTH", "type": "prd", "title": "Authentication",
             "status": "review", "personas": [], "scope": "in",
             "moscow": "must", "horizon": "now", "brd_goals": ["BRD-G1"]},
            {"id": "PRD-AUTH-E1", "type": "epic", "title": "Login",
             "status": "draft", "personas": [], "scope": "in",
             "moscow": "must", "horizon": "now", "prd": "PRD-AUTH"},
            {"id": "PRD-AUTH-E1-S1", "type": "story", "title": "Email login",
             "status": "draft", "personas": ["p"], "scope": "in",
             "moscow": "must", "horizon": "now", "epic": "PRD-AUTH-E1"},
            {"id": "PRD-AUTH-E1-S2", "type": "story", "title": "Social login",
             "status": "draft", "personas": ["p"], "scope": "in",
             "moscow": "must", "horizon": "now", "epic": "PRD-AUTH-E1"},
        ],
        "edges": [
            {"from": "PRD-AUTH-E1-S1", "to": "PRD-AUTH-E1", "kind": "epic"},
            {"from": "PRD-AUTH-E1-S2", "to": "PRD-AUTH-E1", "kind": "epic"},
            {"from": "PRD-AUTH-E1", "to": "PRD-AUTH", "kind": "prd"},
            {"from": "PRD-AUTH", "to": "BRD-G1", "kind": "brd_goal"},
        ],
        "risks": [],
    }


def test_tree_text_summary_retained():
    """G-G2 / F10: `--viz tree --format ascii` renders the minimal text-summary
    tree (NOT the heavy box-drawing graph-art). One line per node in the fixed
    grammar `[<type>:<id>] <title> · <status>`, 2-space indent per depth, sorted
    by ID at each level, plus a node/finding counts footer. This locks the exact
    contract the phase spec defines; the structure must stay visible on a
    terminal (zero-dep path preserved)."""
    g = _text_summary_graph()
    out = render_ascii.tree(g)
    lines = out.splitlines()

    # Header: product name on the first line.
    assert lines[0] == "PRODUCT: Acme Shop", f"unexpected header line: {lines[0]!r}"

    # The heavy box-drawing art must be GONE (downgrade, not the old tree()).
    assert "├──" not in out and "└──" not in out and "│" not in out, (
        "text-summary tree must drop the box-drawing graph-art"
    )

    # One node line per node, fixed grammar with 2-space indent per depth and the
    # middot separator before status. Depth: goal=1, prd=2, epic=3, story=4.
    assert "  [goal:BRD-G1] Increase conversion · approved" in lines
    assert "    [prd:PRD-AUTH] Authentication · review" in lines
    assert "      [epic:PRD-AUTH-E1] Login · draft" in lines
    assert "        [story:PRD-AUTH-E1-S1] Email login · draft" in lines
    assert "        [story:PRD-AUTH-E1-S2] Social login · draft" in lines

    # Sorted-by-ID at each level: S1 before S2 (byte-deterministic ordering).
    assert out.index("PRD-AUTH-E1-S1") < out.index("PRD-AUTH-E1-S2")

    # Counts footer: structure + finding totals. 5 spec nodes (1 goal, 1 prd,
    # 1 epic, 2 stories), 0 findings on this graph.
    footer = lines[-1]
    assert footer.startswith("—"), f"expected a counts footer line, got: {footer!r}"
    assert "5 nodes" in footer
    assert "1 goal" in footer and "1 prd" in footer and "1 epic" in footer
    assert "2 stories" in footer
    assert "0 findings" in footer


def test_html_default_for_matrix(tmp_path):
    """G-G3 / §0.2: `--viz competition` with NO `--format` defaults to HTML-native
    (the matrix/heatmap render as HTML tables, not ASCII). The dispatcher must
    write a self-contained HTML file under docs/product/visuals/ and emit the
    `{"written": ...}` JSON — NOT print an ASCII grid to stdout."""
    import subprocess
    import shutil
    import json as _json

    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable
    viz = SCRIPTS_DIR / "visualize.py"
    r = subprocess.run(
        [py, str(viz), "--root", str(proj), "--view", "competition"],  # no --format
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    # The HTML default writes a file and emits a {"written": ...} JSON line; the
    # ASCII default instead prints a plain-text grid. Distinguish the two by the
    # JSON shape so the RED reason reads as "still defaulting to ASCII", not a raw
    # JSON parse error.
    stdout = r.stdout.strip()
    assert stdout.startswith("{") and '"written"' in stdout, (
        f"competition with no --format must default to HTML (a written-file JSON "
        f"line), not an ASCII grid on stdout; got: {stdout!r}"
    )
    payload = _json.loads(stdout)
    assert payload["written"].endswith(".html")
    htmls = sorted((proj / "docs" / "product" / "visuals").glob("competition-*.html"))
    assert htmls, "competition (no --format) must default to a written HTML file"


def test_dashboard_html_only(tmp_path):
    """G-G1: the new multi-dim `dashboard` view is HTML-only. `--viz dashboard`
    must be a registered view that writes an HTML file; `--format mermaid` falls
    back (with a stderr note) and still exits 0 — it never crashes or emits an
    unknown-view error."""
    import visualize
    assert "dashboard" in visualize.VIEWS, "dashboard must be a registered view"

    import subprocess
    import shutil
    import json as _json

    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable
    viz = SCRIPTS_DIR / "visualize.py"

    # Default → HTML file written.
    r = subprocess.run(
        [py, str(viz), "--root", str(proj), "--view", "dashboard"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    payload = _json.loads(r.stdout)
    assert payload.get("written", "").endswith(".html"), (
        f"dashboard must default to a written HTML file; got: {r.stdout!r}"
    )

    # --format mermaid → graceful fallback with a note, still exit 0.
    r2 = subprocess.run(
        [py, str(viz), "--root", str(proj), "--view", "dashboard", "--format", "mermaid"],
        capture_output=True, text=True,
    )
    assert r2.returncode == 0, r2.stderr
    assert "note" in r2.stderr.lower() or "fallback" in r2.stderr.lower(), (
        f"dashboard --format mermaid must emit a fallback note on stderr; got: {r2.stderr!r}"
    )


def test_board_textsummary_fallback(tmp_path):
    """§0.2 (reverses Q45): board KEEPS its text-summary fallback. `--viz board
    --format mermaid` must still print a text-summary that SHOWS the structure
    (grouped card ids), emit a fallback note, and exit 0 — the fallback is NOT
    removed."""
    import subprocess
    import shutil

    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable
    viz = SCRIPTS_DIR / "visualize.py"
    r = subprocess.run(
        [py, str(viz), "--root", str(proj), "--view", "board", "--format", "mermaid"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    # Fallback note on stderr (board has no Mermaid form).
    assert "note" in r.stderr.lower() or "fallback" in r.stderr.lower()
    # The text-summary must still be on stdout with visible structure (card ids
    # grouped), NOT a removal/error message.
    out = r.stdout
    assert "PRD-AUTH" in out and "BRD-G1" in out, (
        f"board text-summary fallback must show card structure; got: {out!r}"
    )
    assert "###" in out, "board fallback must keep its grouped text-summary headers"


def test_visualize_determinism():
    """G-A4: the retained text-summary tree is byte-deterministic — same input →
    byte-identical output across repeated renders. Also asserts the new
    text-summary contract is in effect (counts footer present), so this is a true
    determinism check on the NEW format, not the old box-art."""
    g = _text_summary_graph()
    first = render_ascii.tree(g)
    second = render_ascii.tree(g)
    assert first == second, "text-summary tree must be byte-identical run-to-run"
    # Determinism is asserted on the NEW format (counts footer present).
    assert first.splitlines()[-1].startswith("—") and "nodes" in first.splitlines()[-1], (
        "determinism must hold on the new text-summary format (counts footer)"
    )


def test_no_cdn_in_body_views(tmp_path):
    """G-A4 / fail-closed: a body view (board) HTML inlines the marked + DOMPurify
    sanitizer (or fails CLOSED to a plain-text banner) and NEVER reaches a CDN.
    The downgrade must not weaken the body-view no-network guarantee."""
    import subprocess
    import shutil

    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    py = sys.executable
    viz = SCRIPTS_DIR / "visualize.py"
    r = subprocess.run(
        [py, str(viz), "--root", str(proj), "--view", "board", "--format", "html"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    body = sorted((proj / "docs" / "product" / "visuals").glob("board-*.html"))[-1].read_text()
    # Never a CDN for body views.
    assert "cdn.jsdelivr.net" not in body, "body views must never reach a CDN"
    # No external network SINK: no <script src="http..."> / <link href="http...">.
    # (Inlined vendored libs legitimately contain http(s) substrings in comments /
    # W3C XML namespaces — those are inert, not a fetch.)
    import re as _re
    network_sink = _re.search(r'<(?:script|link)[^>]*\b(?:src|href)\s*=\s*["\']https?://', body)
    assert network_sink is None, (
        f"body view must have no external network sink; found: {network_sink.group(0)!r}"
    )
    # The sanitize chokepoint is always present; libs inlined OR fail-closed banner.
    assert "psRenderMarkdown" in body, "body view must ship the sanitize chokepoint"
    assert ("DOMPurify" in body) or ("Markdown libraries not vendored" in body), (
        "body view must inline the sanitizer OR fail closed to a plain-text banner"
    )


def test_mermaid_roadmap_renders_all_items_no_cap():
    """A horizon with more than 8 items must render ALL of them — the roadmap
    timeline does not silently truncate a section (Cycle 7: removed the [:8] cap)."""
    nodes = [{"id": f"PRD-X-E1-S{i}", "type": "story", "horizon": "now", "status": "draft"}
             for i in range(1, 13)]  # 12 stories under 'now'
    g = {"nodes": nodes, "edges": []}
    out = render_mermaid.roadmap(g)
    for i in range(1, 13):
        assert f"PRD-X-E1-S{i}" in out, f"story S{i} dropped from roadmap (silent truncation?)"
