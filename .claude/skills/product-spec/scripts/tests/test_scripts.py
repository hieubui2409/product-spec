"""Tests for product-spec core scripts (Phase 5).

Exercises frontmatter_parser, spec_graph, check_traceability, check_consistency,
build_traceability_matrix, generate_templates against two fixture specs:
  - valid-spec/   : clean spec; should produce zero error-severity findings
                    (warns possible)
  - broken-spec/  : seeded with orphan story, missing AC, dup ID, dangling
                    epic reference, unaddressed BRD goal
"""

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from frontmatter_parser import parse_file, parse_text  # noqa: E402
from spec_graph import build_graph, downstream  # noqa: E402
from check_traceability import check as check_trace  # noqa: E402
from check_consistency import check as check_cons, _enrich_with_ac  # noqa: E402
from build_traceability_matrix import build_matrix, build_index  # noqa: E402
from generate_templates import allocate_id, render  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"
BROKEN = FIXTURES / "broken-spec"


# ---------- frontmatter_parser ----------

def test_parse_valid_frontmatter():
    r = parse_file(VALID / "docs" / "product" / "PRODUCT.md")
    assert r["ok"]
    assert r["frontmatter"]["id"] == "PRODUCT"
    assert "Acme Shop" in r["frontmatter"]["name"]


def test_parse_text_no_frontmatter():
    r = parse_text("# Just a heading")
    assert not r["ok"]
    assert "frontmatter" in r["error"].lower() or "no YAML" in r["error"]


def test_parse_text_malformed_yaml():
    r = parse_text("---\n: : bad\n  indent\n---\nbody")
    assert not r["ok"]
    assert "YAML" in r["error"] or "parse" in r["error"].lower()


# ---------- spec_graph ----------

def test_graph_valid_spec_has_expected_nodes_and_edges():
    g = build_graph(VALID)
    ids = {n["id"] for n in g["nodes"]}
    assert {"PRODUCT", "BRD-G1", "BRD-G2", "PRD-AUTH", "PRD-AUTH-E1", "PRD-AUTH-E1-S1"} <= ids
    edges = {(e["from"], e["to"]) for e in g["edges"]}
    assert ("PRD-AUTH-E1-S1", "PRD-AUTH-E1") in edges
    assert ("PRD-AUTH-E1", "PRD-AUTH") in edges
    assert ("PRD-AUTH", "BRD-G1") in edges


def test_graph_downstream_query():
    g = build_graph(VALID)
    down = downstream(g, "PRD-AUTH")
    assert "PRD-AUTH-E1" in down
    assert "PRD-AUTH-E1-S1" in down


def test_graph_missing_product_dir():
    g = build_graph(Path("/tmp/__does_not_exist__"))
    assert g.get("missing_product_dir") is True
    assert g["nodes"] == []


# ---------- check_traceability ----------

def test_traceability_valid_has_no_errors():
    g = build_graph(VALID)
    findings = check_trace(g)
    errors = [f for f in findings if f["severity"] == "error"]
    # BRD-G2 is unaddressed but that's a warn, not an error
    assert errors == [], f"expected zero errors, got {errors}"


def test_traceability_broken_flags_dangling_link_and_unaddressed():
    g = build_graph(BROKEN)
    findings = check_trace(g)
    checks = {f["check"] for f in findings}
    assert "dangling_link" in checks, "expected dangling_link for PRD-AUTH-E9 reference"
    assert "orphan_brd_goal" in checks, "expected orphan_brd_goal for BRD-G2"


# ---------- check_consistency ----------

def test_consistency_valid_no_errors():
    g = build_graph(VALID)
    _enrich_with_ac(g, VALID)
    findings = check_cons(g)
    errors = [f for f in findings if f["severity"] == "error"]
    assert errors == [], f"expected zero errors on valid spec, got {errors}"


def test_consistency_broken_flags_dup_id_and_missing_ac():
    g = build_graph(BROKEN)
    _enrich_with_ac(g, BROKEN)
    findings = check_cons(g)
    checks = {f["check"] for f in findings}
    assert "dup_id" in checks, "expected dup_id for PRD-AUTH-E1-S1 collision"
    assert "missing_ac" in checks, "expected missing_ac for empty AC story"


# ---------- build_traceability_matrix ----------

def test_matrix_includes_story_row():
    g = build_graph(VALID)
    md = build_matrix(g)
    assert "PRD-AUTH-E1-S1" in md
    assert "PRD-AUTH-E1" in md
    assert "PRD-AUTH" in md
    assert "BRD-G1" in md


def test_matrix_index_sorted_by_type():
    g = build_graph(VALID)
    idx = build_index(g)
    types_in_order = [row["type"] for row in idx]
    assert types_in_order == sorted(types_in_order)


# ---------- generate_templates ----------

def test_allocate_id_for_new_story_under_epic():
    g = build_graph(VALID)
    new_id = allocate_id(g, "story", slug=None, parent="PRD-AUTH-E1", session_used=[])
    assert new_id == "PRD-AUTH-E1-S2"


def test_allocate_id_under_different_epic_is_independent():
    """Parent-scoped IDs: two stories under different epics both start at S1."""
    g = build_graph(VALID)
    # Simulate adding a new epic under PRD-AUTH
    new_epic = allocate_id(g, "epic", slug=None, parent="PRD-AUTH", session_used=[])
    assert new_epic == "PRD-AUTH-E2"
    # First story under PRD-AUTH-E2 starts at S1
    new_story = allocate_id(g, "story", slug=None, parent="PRD-AUTH-E2", session_used=[new_epic])
    assert new_story == "PRD-AUTH-E2-S1"


def test_render_optional_section_drop_and_keep():
    template = (
        "static head\n"
        "<!-- OPTIONAL: keep_me -->\nKEPT-BODY\n<!-- /OPTIONAL -->\n"
        "<!-- OPTIONAL: drop_me -->\nDROPPED-BODY\n<!-- /OPTIONAL -->\n"
        "tail with {{token}}"
    )
    out = render(template, {"token": "VALUE"}, keep_optional=["keep_me"])
    assert "KEPT-BODY" in out
    assert "DROPPED-BODY" not in out
    assert "VALUE" in out
    assert "{{token}}" not in out


def test_render_unknown_token_becomes_tbd():
    out = render("hello {{nope}}", values={}, keep_optional=[])
    assert "hello TBD" in out


# ---------- Wave-3 review fix regression tests ----------


def test_w3_c1_fill_defaults_emits_lists_for_list_typed_fields():
    """C-1: Omitting list-typed fields used to leak the string "TBD" into
    YAML, then renderers iterated it per-character ("T", "B", "D"). The
    defaults must be empty lists so downstream consumers see a valid shape."""
    from generate_templates import fill_defaults
    out = fill_defaults({}, "prd", "PRD-X", "en")
    for key in ("personas", "metrics", "brd_goals", "risks", "acceptance_criteria"):
        assert isinstance(out[key], list), (
            f"{key} should default to a list, got {type(out[key]).__name__}: {out[key]!r}"
        )
        assert out[key] == []


def test_w3_c1_fresh_product_init_does_not_leak_tbd_into_personas():
    """C-1 end-to-end: generate a fresh PRODUCT.md, parse it, and assert
    `personas` is a list — never the scalar string "TBD"."""
    import subprocess
    import tempfile
    from pathlib import Path as _P
    import json as _json

    with tempfile.TemporaryDirectory() as td:
        proj = _P(td) / "proj"
        (proj / "docs" / "product").mkdir(parents=True)
        payload = '{"name":"X","one_line_description":"y","current_implementation":"y","deployment":"y","roadmap_one_liner":"y","core_value":"y"}'
        r = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "generate_templates.py"),
             "--root", str(proj), "--type", "product",
             "--values", payload, "--write"],
            check=True, capture_output=True, text=True,
        )
        body = (proj / "docs" / "product" / "PRODUCT.md").read_text()
        # The bug rendered `personas: TBD` (scalar). The fix renders `personas: []`.
        assert "personas: TBD" not in body
        # Validate via the parser.
        parsed = parse_file(proj / "docs" / "product" / "PRODUCT.md")
        assert parsed["ok"], parsed["error"]
        assert isinstance(parsed["frontmatter"]["personas"], list)


def test_w3_c1_invalid_type_finding_when_list_field_is_scalar(tmp_path):
    """C-1 check_consistency shape check: a `personas: TBD` (scalar) must
    produce an `invalid_type` finding so the PO is told exactly what is
    wrong instead of staring at garbled persona-viz rows."""
    proj = tmp_path / "proj"
    (proj / "docs" / "product" / "stories").mkdir(parents=True)
    # Required PRODUCT.md for the spec_graph to attach product meta.
    (proj / "docs" / "product" / "PRODUCT.md").write_text("""---
id: PRODUCT
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [s]
---
""")
    # Story w/ personas as a scalar — simulates a regression / hand-edit.
    (proj / "docs" / "product" / "brd.md").write_text("""---
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
""")
    (proj / "docs" / "product" / "prds").mkdir()
    (proj / "docs" / "product" / "prds" / "x.md").write_text("""---
id: PRD-X
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
personas: TBD
---
""")
    g = build_graph(proj)
    _enrich_with_ac(g, proj)
    findings = check_cons(g)
    checks = {f["check"] for f in findings}
    assert "invalid_type" in checks, (
        f"expected invalid_type finding for personas: TBD; got: {checks}"
    )


def test_w3_m6_status_inconsistency_flags_prd_above_brd_goal(tmp_path):
    """M-6: an `approved` PRD whose BRD goal is still `draft` must be
    flagged via status_inconsistency. Earlier the check skipped the
    PRD-to-goal relationship entirely."""
    proj = tmp_path / "proj"
    (proj / "docs" / "product" / "prds").mkdir(parents=True)
    (proj / "docs" / "product" / "PRODUCT.md").write_text("""---
id: PRODUCT
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [s]
---
""")
    (proj / "docs" / "product" / "brd.md").write_text("""---
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
""")
    (proj / "docs" / "product" / "prds" / "x.md").write_text("""---
id: PRD-X
type: prd
brd_goals: [BRD-G1]
status: approved
lang: en
---
""")
    g = build_graph(proj)
    findings = check_cons(g)
    inconsistencies = [f for f in findings if f["check"] == "status_inconsistency"]
    assert inconsistencies, (
        f"expected status_inconsistency for approved PRD over draft BRD-G1; got: {findings}"
    )
    assert any("PRD-X" == f["artifact_id"] for f in inconsistencies)


def test_w3_n7_persona_cap_exceeded_warn(tmp_path):
    """N-7: declaring more than the soft cap (4) on personas emits a warn —
    so the PO sees an explicit signal at validate time rather than trusting
    the LLM to push back during interview."""
    proj = tmp_path / "proj"
    (proj / "docs" / "product").mkdir(parents=True)
    (proj / "docs" / "product" / "PRODUCT.md").write_text("""---
id: PRODUCT
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [a, b, c, d, e]
---
""")
    g = build_graph(proj)
    findings = check_cons(g)
    caps = [f for f in findings if f["check"] == "persona_cap_exceeded"]
    assert caps, f"expected persona_cap_exceeded; got checks: {[f['check'] for f in findings]}"
    assert caps[0]["severity"] == "warn"


def test_w3_n7_persona_cap_silent_at_or_below_cap(tmp_path):
    """N-7 boundary: 4 personas (cap) must NOT warn."""
    proj = tmp_path / "proj"
    (proj / "docs" / "product").mkdir(parents=True)
    (proj / "docs" / "product" / "PRODUCT.md").write_text("""---
id: PRODUCT
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [a, b, c, d]
---
""")
    g = build_graph(proj)
    findings = check_cons(g)
    assert not any(f["check"] == "persona_cap_exceeded" for f in findings)


def test_w3_n8_session_md_gitignore_warn(tmp_path):
    """N-8: a `.gitignore` excluding `.session.md` produces a warn —
    brainstorm §16 mandates the session file be committed for cross-machine
    resume."""
    proj = tmp_path / "proj"
    (proj / "docs" / "product").mkdir(parents=True)
    (proj / "docs" / "product" / "PRODUCT.md").write_text("""---
id: PRODUCT
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [s]
---
""")
    (proj / "docs" / "product" / ".session.md").write_text("---\nphase: vision\n---\n")
    (proj / ".gitignore").write_text("# project gitignore\n.session.md\n")
    g = build_graph(proj)
    findings = check_cons(g)
    assert any(f["check"] == "session_md_gitignored" for f in findings), (
        f"expected session_md_gitignored finding; got: {[f['check'] for f in findings]}"
    )


def test_w3_m8_strict_gate_exits_zero_on_valid_spec(tmp_path):
    """M-8: shell-runnable strict_gate.py exits 0 on a clean spec."""
    import subprocess
    import shutil
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "strict_gate.py"),
         "--root", str(proj)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"strict_gate flagged a clean spec: {r.stderr}"


def test_w3_m8_strict_gate_exits_non_zero_on_broken_spec(tmp_path):
    """M-8: strict_gate.py exits non-zero on any error-severity finding,
    making CI usage possible without an LLM in the loop."""
    import subprocess
    import shutil
    proj = tmp_path / "proj"
    shutil.copytree(BROKEN, proj)
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "strict_gate.py"),
         "--root", str(proj)],
        capture_output=True, text=True,
    )
    assert r.returncode != 0
    assert "BLOCKED" in r.stderr


# ---------- New regression tests for graph/validation/template fixes ----------


def test_brd_goals_bare_string_produces_single_invalid_type_not_per_char_findings(tmp_path):
    """A PRD with brd_goals as a bare string (e.g. brd_goals: BRD-G1) must produce
    exactly one invalid_type finding, NOT one dangling_link per character of the string."""
    proj = tmp_path / "proj"
    (proj / "docs" / "product" / "prds").mkdir(parents=True)
    (proj / "docs" / "product" / "PRODUCT.md").write_text("""---
id: PRODUCT
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [s]
---
""")
    (proj / "docs" / "product" / "brd.md").write_text("""---
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
""")
    # brd_goals written as a bare scalar string — simulates a hand-edit regression.
    (proj / "docs" / "product" / "prds" / "auth.md").write_text("""---
id: PRD-AUTH
type: prd
brd_goals: BRD-G1
status: draft
lang: en
---
""")
    g = build_graph(proj)
    findings = check_trace(g)

    # Must NOT produce per-character dangling_link entries (B, R, D, -, G, 1, …).
    char_dangling = [
        f for f in findings
        if f["check"] == "dangling_link" and len(f.get("context", {}).get("ref", "")) == 1
    ]
    assert char_dangling == [], (
        f"per-character dangling_link findings detected: {char_dangling}"
    )

    # Must produce exactly one invalid_type finding for brd_goals.
    invalid_type = [f for f in findings if f["check"] == "invalid_type"]
    assert len(invalid_type) == 1, (
        f"expected exactly one invalid_type finding, got: {invalid_type}"
    )
    assert invalid_type[0]["artifact_id"] == "PRD-AUTH"


def test_allocate_id_prd_slug_resembling_epic_is_rejected():
    """A PRD slug whose normalised form ends in -E<n> or -E<n>-S<n> would mint
    an ID that collides with the epic/story grammar. allocate_id must raise."""
    import pytest
    g = build_graph(VALID)
    with pytest.raises(ValueError, match=r"collides"):
        allocate_id(g, "prd", slug="AUTH-E1", parent=None, session_used=[])


def test_render_raises_on_unresolved_hyphenated_token():
    """Tokens with hyphens are not matched by TOKEN_RE ([a-zA-Z0-9_]+),
    so {{bad-key}} would silently pass through into the artifact. render()
    must raise ValueError instead."""
    import pytest
    template = "hello {{bad-key}} world"
    with pytest.raises(ValueError, match=r"unresolved template token"):
        render(template, values={}, keep_optional=[])


def test_write_snapshot_same_second_does_not_overwrite(tmp_path):
    """Two write_snapshot calls with the same timestamp but different graph content
    must produce distinct files (content-hash suffix differentiates them)."""
    from spec_graph import write_snapshot

    snap_dir = tmp_path / "docs" / "product" / "visuals" / ".snapshots"

    graph_a = {
        "version": "1.0",
        "generated_at": "20260529T120000Z",
        "nodes": [{"id": "PRD-A"}],
        "edges": [],
        "risks": [],
        "parse_errors": [],
        "product": {},
        "root_path": str(tmp_path),
    }
    graph_b = {
        **graph_a,
        "nodes": [{"id": "PRD-B"}],  # different content → different hash
    }

    path_a = write_snapshot(graph_a, tmp_path)
    path_b = write_snapshot(graph_b, tmp_path)

    assert path_a != path_b, "distinct graph contents must produce distinct snapshot paths"
    assert path_a.exists(), "snapshot A must exist"
    assert path_b.exists(), "snapshot B must exist"


def test_fill_defaults_restores_list_field_when_caller_passes_none():
    """A caller-supplied None for a list field must not shadow the [] default —
    downstream renderers iterate these (e.g. `for p in personas`)."""
    from generate_templates import fill_defaults
    out = fill_defaults({"personas": None}, "prd", "PRD-X", "en")
    assert out["personas"] == [], f"None must be restored to []: {out.get('personas')!r}"
