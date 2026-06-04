"""Tests for the single-pass token engine, vendored marked+DOMPurify
(fail-closed), the embedded-JSON body channel + attribute sinks, and
the shared design-system substrate.

The client-side sanitize chokepoint (DOMPurify.sanitize(marked.parse(md))) runs
in a browser; here we assert the SERVER guarantees: bodies travel inert as JSON,
attribute values are escaped, the close-tag hazard cannot break out, and the
sanitizer fails closed to escaped text with NO CDN fallback.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import render_html  # noqa: E402


# ---------- C2: single-pass token substitution ----------

def test_substitute_does_not_rescan_inserted_values_no_bleed():
    # OLD multi-pass would expand the inserted {{b}} on a later iteration.
    out = render_html.substitute("X{{a}}Y", {"a": "{{b}}", "b": "BLEED"})
    assert out == "X{{b}}Y", f"footer/value bleed via re-scan: {out!r}"


def test_substitute_value_cannot_inject_another_token_payload():
    shell = "<div>{{view_body}}</div><script>{{mermaid_js}}</script>"
    out = render_html.substitute(shell, {"view_body": "{{mermaid_js}}", "mermaid_js": "PAYLOAD"})
    # The malicious body's literal {{mermaid_js}} must NOT be expanded into the payload.
    assert "<div>{{mermaid_js}}</div>" in out
    assert "<div>PAYLOAD</div>" not in out


def test_substitute_leaves_unknown_tokens_verbatim():
    assert render_html.substitute("a {{unknown}} b", {"x": "1"}) == "a {{unknown}} b"


# ---------- vendored libs present + close-tag escaped ----------

def test_vendored_markdown_libs_load_and_escape_close_tag():
    libs = render_html._load_vendored_markdown_libs()
    assert libs is not None, "marked+DOMPurify must be vendored (run install.sh)"
    assert "DOMPurify" in libs and "marked" in libs.lower()
    # No raw close-tag may survive in the inlined <script> payload.
    assert "</script" not in libs
    assert "</script>" not in libs


def test_chokepoint_order_is_marked_then_purify():
    # The chokepoint ships in the body-view {{markdown_libs}} block (NOT the
    # shared head — H4: legacy views inline no sanitizer code).
    block = render_html.body_render_values({"x": {}})["markdown_libs"]
    # Locked order: parse THEN sanitize. A reversed order would sanitize raw md.
    assert "DOMPurify.sanitize(window.marked.parse(" in block


def test_shared_head_has_no_sanitizer_code():
    """H4: the design-system head must inline NO marked/DOMPurify reference, so
    legacy graph views (which embed only the head) carry no sanitizer code."""
    head = render_html.viewer_head()
    assert "DOMPurify" not in head and "marked" not in head


def test_viewer_head_failclose_has_no_cdn_sanitizer():
    head = render_html.viewer_head()
    # Fail-closed branch returns escaped <pre>, never a network sanitizer.
    assert "ps-fallback" in head
    # No CDN host and no external script load.
    assert "cdn." not in head.lower()
    assert "<script src" not in head.lower()


# ---------- embedded-JSON body channel (injection sink #1) ----------

def test_embed_spec_data_neutralizes_close_tag_breakout():
    payload = {"PRD-X": {"body": "</script><script>alert(1)</script>"}}
    blob = render_html.embed_spec_data(payload)
    # Must sit inside an inert application/json island.
    assert 'type="application/json"' in blob
    # Every `<` in the payload is rewritten to the JSON < escape, so neither
    # the breakout nor a re-opened <script> survives in the island body.
    assert "</script><script>" not in blob
    assert "\\u003c/script>\\u003cscript>alert(1)\\u003c/script>" in blob


def test_embed_spec_data_neutralizes_comment_primer_render_break():
    # An unclosed `<!--` that mentions `<script` would, untreated, drive
    # the WHATWG script-data-double-escaped state and swallow the page bootstrap
    # (blank render). Escaping ALL `<` neutralizes the primer + the `<script`.
    payload = {"PRD-X": {"body": "<!-- a stray <script tag mention, no close"}}
    blob = render_html.embed_spec_data(payload)
    # Inspect only the JSON body (between the wrapper's own <script ...> / </script>).
    inner = blob[blob.index(">") + 1: blob.rindex("</script>")]
    assert "<!--" not in inner and "<script" not in inner and "<" not in inner
    assert "\\u003c!--" in inner and "\\u003cscript" in inner


def test_embed_spec_data_round_trips_via_json_parse():
    # < is a JSON escape that decodes straight back to `<`, so the rendered
    # body is byte-unchanged — only the raw transport is neutered.
    import json as _json
    payload = {"PRD-X": {"body": "before </script> <!-- <script> after"}}
    blob = render_html.embed_spec_data(payload)
    inner = blob[blob.index(">") + 1: blob.rindex("</script>")]
    assert _json.loads(inner) == payload


def test_embed_spec_data_is_deterministic():
    p = {"b": 2, "a": 1}
    assert render_html.embed_spec_data(p) == render_html.embed_spec_data(p)


# ---------- attribute-context sinks (injection sink #2) ----------

def test_escape_neutralizes_attribute_payload():
    payload = '"><script>alert(1)</script>'
    esc = render_html._escape(payload)
    # Quote + angle brackets escaped → cannot close the attribute or open a tag.
    assert '"' not in esc and "<" not in esc and ">" not in esc
    assert "&quot;" in esc and "&lt;script&gt;" in esc


# ---------- L12: fail closed when libs missing ----------

def test_body_render_values_fail_closed_when_libs_absent(monkeypatch, tmp_path):
    monkeypatch.setattr(render_html, "VENDOR_MARKED", tmp_path / "nope-marked.js")
    monkeypatch.setattr(render_html, "VENDOR_PURIFY", tmp_path / "nope-purify.js")
    vals = render_html.body_render_values({"x": {"body": "hi"}})
    # The 62 KB library payload must be ABSENT (no marked copyright banner)…
    assert "marked v18" not in vals["markdown_libs"], "must NOT inline the library when absent"
    # …but the chokepoint def is still present and fail-closes to escaped text.
    assert "psRenderMarkdown" in vals["markdown_libs"]
    assert "ps-fallback" in vals["markdown_libs"]
    assert vals["libs_banner"], "must show a visible fail-closed banner"
    assert "install.sh" in vals["libs_banner"]
    # Never a CDN sanitizer.
    assert "cdn." not in vals["libs_banner"].lower()


def test_body_render_values_present_path():
    vals = render_html.body_render_values({"x": {"body": "hi"}})
    assert "marked v18" in vals["markdown_libs"], "vendored library must inline when present"
    assert vals["libs_banner"] == ""
    assert 'id="ps-spec-data"' in vals["spec_data"]
    assert "ve-card" in vals["viewer_head"]  # design system present


# ---------- symmetric gating — legacy views carry NO markdown libs ----------

def test_legacy_assemble_does_not_embed_skill_sanitizer():
    """H4: legacy graph views render NO bodies, so they ship neither the skill's
    body-sanitizer chokepoint (psRenderMarkdown) nor the vendored {{markdown_libs}}
    block — for BOTH the ascii and mermaid formats.

    The contract is "no SKILL body-sanitizer", not "no vendor lib named DOMPurify":
    the mermaid-format payload bundles Mermaid's OWN internal DOMPurify for SVG
    sanitization, which is unrelated to body rendering and therefore exempt."""
    graph = {"product": {"name": "Acme"},
             "nodes": [{"id": "BRD-G1", "type": "goal", "title": "G"}], "edges": [], "risks": []}
    for fmt, text in (("ascii", "draft 1"), ("mermaid", "```mermaid\ngraph TD\nA-->B\n```")):
        html = render_html.assemble("tree", fmt, text, graph)
        # psRenderMarkdown is the skill body-render chokepoint — it must be absent
        # from graph views. (The .ps-fallback *CSS class* lives in the shared head
        # for all views; only the chokepoint that emits it is body-view-only.)
        assert "psRenderMarkdown" not in html, f"skill body-sanitizer leaked into {fmt} graph view"
    # The ascii path additionally carries no DOMPurify at all (no mermaid bundle).
    assert "DOMPurify" not in render_html.assemble("heatmap", "ascii", "draft 1", graph)
