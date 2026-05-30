"""Phase-3 tests: F1 read-once Export (md + html).

Markdown is deterministic (asserted by exact two-call equality + content); the
content hash drives a stable, collision-free filename; html embeds the doc as an
inert JSON island rendered through the Phase-2 sanitize chokepoint.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph, load_artifacts  # noqa: E402
from assemble_digest import build_digest  # noqa: E402
import render_export  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"
_FIXED_TS = "2026-01-01T00:00:00Z"


def _digest(select="PRD-AUTH", layers=None, depth="context"):
    graph = build_graph(VALID)
    artifacts = load_artifacts(VALID / "docs" / "product")
    return build_digest(graph, artifacts, select=select, layers=layers, depth=depth)


def _doc(select="PRD-AUTH", layers=None, depth="context", compact_mode="struct"):
    d = _digest(select, layers, depth)
    layers_label = ",".join(layers) if layers else "all"
    return render_export.render_markdown_doc(d, "Acme Shop", select, depth, layers_label, compact_mode, _FIXED_TS)


# ---------- markdown determinism + content ----------

def test_md_doc_is_deterministic():
    assert _doc() == _doc()


def test_md_doc_has_toc_ordered_sections_and_ac():
    doc = _doc(select="PRD-AUTH", depth="context")
    assert "## Contents" in doc
    # TOC anchors derived from IDs.
    assert "(#prd-auth)" in doc
    assert '<a id="prd-auth-e1-s1"></a>' in doc
    # Hierarchy order: vision/brd before goal before prd before epic before story.
    order = [doc.index(t) for t in ("# Spec Export", "## Contents")]
    assert order == sorted(order)
    # Compare SECTION headings (newline-prefixed), not TOC entries.
    assert doc.index("\n## BRD") < doc.index("\n## PRD-AUTH-E1-S1")
    # Story section carries AC items (full verbosity at context depth).
    assert "Acceptance criteria" in doc
    assert "rate-limited for 15 minutes" in doc


def test_md_all_select_includes_full_chain():
    doc = _doc(select="all", depth="context")
    for nid in ("BRD-G1", "BRD-G2", "PRD-AUTH", "PRD-AUTH-E1", "PRD-AUTH-E1-S1"):
        assert f"(#{nid.lower()})" in doc


# ---------- --layers precedence + warning ----------

def test_md_layers_story_drops_context_and_warns_in_header():
    doc = _doc(select="PRD-AUTH", layers=["story"], depth="context")
    assert "⚠" in doc and "PRD-AUTH" in doc
    # Only the story section survives; the PRD/epic/goal headings are gone.
    assert "## PRD-AUTH —" not in doc
    assert "PRD-AUTH-E1-S1" in doc


# ---------- depth presets ----------

def test_md_depth_full_renders_bodies_context_compacts_ancestors():
    full = _doc(select="PRD-AUTH", depth="full")
    context = _doc(select="PRD-AUTH", depth="context")
    # BRD singleton: full shows the BRD narrative body; context shows a struct skeleton.
    assert "acquiring brands" in full
    assert "**goals**" in context  # struct compaction lists goal titles
    assert full != context


# ---------- --compact-mode llm: markers only, NO summarization ----------

def test_compact_mode_llm_emits_markers_and_keeps_full_body():
    doc = _doc(select="PRD-AUTH", depth="context", compact_mode="llm")
    # Ancestors/singletons (struct verbosity) are wrapped for the LLM, NOT summarized.
    assert "<!-- COMPACT:" in doc
    assert "<!-- /COMPACT:" in doc
    # The BRD body text is present verbatim (script did not summarize it).
    assert "acquiring brands" in doc


def test_compact_mode_struct_has_no_llm_markers():
    doc = _doc(select="PRD-AUTH", depth="context", compact_mode="struct")
    assert "<!-- COMPACT:" not in doc


# ---------- --compact-mode llm + --format html is rejected (F5) ----------

def test_compact_llm_with_html_is_rejected(tmp_path):
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    with pytest.raises(ValueError):
        render_export.write_export(proj, "PRD-AUTH", None, "context", "llm", "html", "en")
    # md + llm remains valid (no raise).
    out = render_export.write_export(proj, "PRD-AUTH", None, "context", "llm", "md", "en")
    assert out.suffix == ".md"


# ---------- --export VISION renders one section / one anchor (F8) ----------

def test_export_vision_single_anchor():
    doc = _doc(select="VISION", depth="context")
    assert doc.count('<a id="vision">') == 1
    assert doc.count("(#vision)") == 1  # one TOC entry too


# ---------- html path: sanitized + self-contained ----------

def test_html_doc_is_self_contained_and_embeds_inert_json():
    md = _doc(select="PRD-AUTH")
    html = render_export.render_html_doc(md, build_graph(VALID), _FIXED_TS)
    assert "<!DOCTYPE html>" in html
    assert 'id="ps-spec-data"' in html          # inert JSON island
    assert "DOMPurify" in html and "marked" in html.lower()  # vendored libs inlined
    assert "psRenderMarkdown" in html            # sanitize chokepoint used


def test_html_doc_neutralizes_body_xss_in_json_island():
    malicious = "# Title\n\n</script><script>alert(1)</script>\n"
    html = render_export.render_html_doc(malicious, build_graph(VALID), _FIXED_TS)
    # The breakout sequence must be neutralized inside the data island: every
    # `<` becomes the JSON < escape (round-trips via JSON.parse).
    assert "</script><script>alert(1)" not in html
    assert "\\u003c/script>" in html


# ---------- file write: stem, stable hash, exports/ sandbox ----------

def test_write_export_creates_exports_and_stable_hash(tmp_path):
    import shutil
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    a = render_export.write_export(proj, "PRD-AUTH", None, "context", "struct", "md", "en")
    b = render_export.write_export(proj, "PRD-AUTH", None, "context", "struct", "md", "en")
    exports = proj / "docs" / "product" / "exports"
    assert exports.is_dir()
    # Filename pattern <stem>-<ts>-<hash8>.md; hash identical for identical content.
    assert a.name.startswith("PRD-AUTH-")
    hash_a = a.stem.rsplit("-", 1)[-1]
    hash_b = b.stem.rsplit("-", 1)[-1]
    assert hash_a == hash_b and len(hash_a) == 8
    # Nothing written outside docs/product/.
    assert str(exports) in str(a.resolve())


def test_write_export_html_opens_offline(tmp_path):
    import shutil
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    out = render_export.write_export(proj, "all", None, "context", "struct", "html", "en")
    assert out.suffix == ".html"
    body = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in body and "ps-spec-data" in body


# ---------- CLI ----------

def _run_export(proj, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "render_export.py"), "--root", str(proj), *extra],
        capture_output=True, text=True,
    )


def test_cli_export_emits_written_json(tmp_path):
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    r = _run_export(proj, "--export", "PRD-AUTH", "--format", "md")
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    assert payload["written"].startswith("docs/product/exports/")


def test_cli_export_unresolved_id_exits_nonzero_and_writes_nothing(tmp_path):
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    r = _run_export(proj, "--export", "PRD-TYPO", "--format", "md")
    assert r.returncode != 0
    assert "PRD-TYPO" in r.stderr
    exports = proj / "docs" / "product" / "exports"
    assert not exports.exists() or not list(exports.glob("*")), "no doc on unresolved selection"


def test_cli_export_llm_html_combo_exits_nonzero(tmp_path):
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    r = _run_export(proj, "--export", "PRD-AUTH", "--compact-mode", "llm", "--format", "html")
    assert r.returncode != 0
    assert "incompatible" in r.stderr.lower()


# ---------- HTML export strips the .md provenance frontmatter (no setext H2) ----------

def test_html_export_strips_yaml_frontmatter_from_body():
    md = _doc(select="PRD-AUTH")        # md_doc carries a leading --- … --- block
    assert md.lstrip().startswith("---")
    html = render_export.render_html_doc(md, build_graph(VALID), _FIXED_TS)
    # The body island feeds marked; it must NOT begin with the YAML block (which
    # marked renders as a stray <hr> + garbled setext <h2>).
    blob = html[html.index('id="ps-spec-data"'):]
    doc = json.loads(blob[blob.index(">") + 1: blob.index("</script>")].replace("\\u003c", "<"))["doc"]
    assert not doc.lstrip().startswith("---")
    assert doc.lstrip().startswith("# Spec Export")


def test_strip_frontmatter_is_noop_without_a_block():
    body = "# Title\n\nno frontmatter here\n"
    assert render_export._strip_frontmatter(body) == body


# ---------- _ac_item: no Python repr leak for list / None / dict / nested ----------

def test_ac_item_dict_renders_key_value_not_repr():
    """Dict AC item (YAML mapping) must render as 'key: value' pairs, not {'key': 'value'}."""
    result = render_export._ac_item({"given": "A", "then": "B"})
    assert result == "given: A · then: B"
    assert "{" not in result, "must not leak Python dict repr"


def test_ac_item_plain_string_passthrough():
    assert render_export._ac_item("plain string") == "plain string"


def test_ac_item_none_returns_empty_string():
    """None AC placeholder must return '' — never repr 'None'."""
    result = render_export._ac_item(None)
    assert result == "", f"expected '' for None, got {result!r}"
    assert "None" not in result


def test_ac_item_list_joins_with_semicolon_not_repr():
    """A list AC item (nested list in YAML) must join elements, not produce '[...]' repr."""
    result = render_export._ac_item(["step 1", "step 2"])
    assert result == "step 1; step 2", f"unexpected: {result!r}"
    assert "[" not in result, "must not leak Python list repr"


def test_ac_item_dict_with_nested_list_value_no_repr():
    """A dict whose value is itself a list must not produce a list repr inside the output."""
    result = render_export._ac_item({"given": ["A", "B"], "then": "C"})
    assert "[" not in result, f"nested list leaked as repr: {result!r}"
    assert "A" in result and "B" in result and "then: C" in result


def test_ac_item_dict_with_nested_dict_value_recurses():
    """A dict whose value is itself a dict must recurse, not repr."""
    result = render_export._ac_item({"when": {"event": "login"}})
    assert "{" not in result, f"nested dict leaked as repr: {result!r}"
    assert "event: login" in result


def test_ac_block_none_placeholder_not_counted():
    """An AC list with None/'' placeholders must not appear in the AC bullet list."""
    entry = {
        "type": "story",
        "ac": [None, "", "real criterion"],
    }
    # _ac_block iterates the raw list; None and '' should render as empty strings,
    # not 'None'/''None'' bullets — but resolve_ac (used upstream) already filters
    # them before they reach the export. Verify _ac_item itself does not repr-leak.
    block = render_export._ac_block(entry)
    assert "None" not in block
    assert "real criterion" in block


# ---------- CLI: --layers validation + empty-result fail loud ----------

def test_cli_export_unknown_layer_exits_nonzero(tmp_path):
    proj = tmp_path / "proj"; shutil.copytree(VALID, proj)
    r = _run_export(proj, "--export", "all", "--layers", "prds", "--format", "md")
    assert r.returncode != 0
    assert "prds" in r.stderr


def test_cli_export_cross_vocab_layer_exits_nonzero(tmp_path):
    proj = tmp_path / "proj"; shutil.copytree(VALID, proj)
    # 'goal' is the viewer vocab, not an export layer.
    r = _run_export(proj, "--export", "PRD-AUTH-E1-S1", "--layers", "goal", "--format", "md")
    assert r.returncode != 0


def test_cli_export_vision_excluding_layer_exits_nonzero_and_writes_nothing(tmp_path):
    proj = tmp_path / "proj"; shutil.copytree(VALID, proj)
    r = _run_export(proj, "--export", "VISION", "--layers", "prd", "--format", "md")
    assert r.returncode != 0
    exports = proj / "docs" / "product" / "exports"
    assert not exports.exists() or not list(exports.glob("*")), "no silently-empty doc on contradictory flags"
