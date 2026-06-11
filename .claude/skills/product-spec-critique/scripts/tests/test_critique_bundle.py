"""Tests for critique_bundle.py — emit_bundle signal gathering (ancestry, source
files, cached verdicts, competitors, drift threshold) + the inherited_context /
descendant_rollup gating. Exercised through the critique_scan CLI facade."""

from critique_test_support import make_proj, run_scan

FINDING_KEYS = {"check", "severity", "artifact_id", "file", "detail", "context"}


def test_finding_shape(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    findings = bundle["structural_findings"]
    assert isinstance(findings, list)
    for f in findings:
        assert FINDING_KEYS.issubset(set(f.keys()))


def test_source_files_keyed_by_id_are_line_numbered_ground_truth(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    sources = bundle["source_files"]
    assert isinstance(sources, dict) and sources
    assert "PRD-AUTH-E1-S1" in sources
    assert "stories/PRD-AUTH-E1-S1.md" not in sources  # keyed by id, not path
    numbered = sources["PRD-AUTH-E1-S1"].splitlines()
    raw = (proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md").read_text(
        encoding="utf-8").splitlines()
    assert len(numbered) == len(raw)
    for i, (num_line, raw_line) in enumerate(zip(numbered, raw), 1):
        assert num_line == f"{i}: {raw_line}", f"line {i} prefix mismatch"
    assert "BRD-G1" in sources


def test_source_files_scoped_to_target_and_ancestry(tmp_path):
    """A narrow `--scope <story>` critique must NOT pack the whole corpus into
    source_files: only the target ∪ ancestry ship. BRD-G2 is a sibling goal NOT in this
    story's ancestry → it must be absent, while the in-frame BRD-G1 and the target
    remain. Off-target artifacts ride ×4 lens prompts for nothing otherwise."""
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "PRD-AUTH-E1-S1")
    sources = bundle["source_files"]
    assert "PRD-AUTH-E1-S1" in sources          # the target
    assert "PRD-AUTH" in sources and "PRD-AUTH-E1" in sources  # ancestry chain
    assert "BRD-G1" in sources                  # the story's own goal (in ancestry)
    assert "BRD-G2" not in sources, "off-target sibling goal must not ship in a scoped bundle"


def test_source_files_all_scope_keeps_whole_corpus(tmp_path):
    """scope=='all' is unfiltered: every artifact (including every goal) still ships."""
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    sources = bundle["source_files"]
    for nid in ("PRD-AUTH", "PRD-AUTH-E1", "PRD-AUTH-E1-S1", "BRD-G1", "BRD-G2"):
        assert nid in sources, f"all-scope bundle dropped {nid}"


def test_ancestry_for_deep_story(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "PRD-AUTH-E1-S1")
    anc = bundle["ancestry"]
    assert anc["epic"] and anc["epic"]["id"] == "PRD-AUTH-E1"
    assert anc["prd"] and anc["prd"]["id"] == "PRD-AUTH"
    goal_ids = [g["id"] for g in anc["brd_goals"] if g]
    assert "BRD-G1" in goal_ids
    assert anc["vision"] is not None and anc["vision"]["type"] == "vision"
    assert bundle["target_ids"] == ["PRD-AUTH-E1-S1"]


def test_scope_all_targets_whole_tree(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    assert "PRD-AUTH-E1-S1" in bundle["target_ids"]
    assert "PRD-AUTH" in bundle["target_ids"]


def test_load_cache_none_tolerant(tmp_path):
    proj = make_proj(tmp_path)  # fixture ships no .memory/judgments.json
    _code, bundle = run_scan(proj, "--scope", "all")
    assert bundle["cached_verdicts"] == []


def test_competitors_empty_when_brd_has_none(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    assert bundle["competitors"] == []


def test_drift_threshold_default_and_override(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    assert bundle["drift_threshold"] == 3
    mem = proj / "docs" / "product" / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "preferences.yaml").write_text("critique_drift_threshold: 5\n", encoding="utf-8")
    _code, bundle2 = run_scan(proj, "--scope", "all")
    assert bundle2["drift_threshold"] == 5


# ---------------------------------------------------------------------------
# — inherited_context / descendant_rollup bundle gating
# ---------------------------------------------------------------------------

def _seed_index(proj, ts, scope, eid):
    import critique_inherit
    critique_inherit.index_report_findings(
        proj, ts, scope,
        [{"evidence_id": eid, "severity": "blocker", "why": "w", "fix": "f"}])


def test_bundle_inherited_and_rollup_keys_present(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    assert "inherited_context" in bundle and isinstance(bundle["inherited_context"], list)
    assert "descendant_rollup" in bundle and isinstance(bundle["descendant_rollup"], dict)


def test_inherited_context_populated_for_child_scope(tmp_path):
    proj = make_proj(tmp_path)
    _seed_index(proj, "260603-0001", "PRD-AUTH", "PRD-AUTH:5")
    _code, bundle = run_scan(proj, "--scope", "PRD-AUTH-E1")
    srcs = {x["source"] for x in bundle["inherited_context"]}
    assert any(s.startswith("PRD-AUTH@") for s in srcs)


def test_no_inherit_empties_inherited_context(tmp_path):
    proj = make_proj(tmp_path)
    _seed_index(proj, "260603-0001", "PRD-AUTH", "PRD-AUTH:5")
    _code, bundle = run_scan(proj, "--scope", "PRD-AUTH-E1", "--no-inherit")
    assert bundle["inherited_context"] == []


def test_no_inherit_beats_inherit_deep(tmp_path):
    proj = make_proj(tmp_path)
    _seed_index(proj, "260603-0001", "PRD-AUTH", "PRD-AUTH:5")
    _code, bundle = run_scan(proj, "--scope", "PRD-AUTH-E1", "--no-inherit", "--inherit", "deep")
    assert bundle["inherited_context"] == []


def test_inherit_off_preference_mirrors_flag(tmp_path):
    proj = make_proj(tmp_path)
    mem = proj / "docs" / "product" / ".memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "preferences.yaml").write_text("critique_inherit: off\n", encoding="utf-8")
    _seed_index(proj, "260603-0001", "PRD-AUTH", "PRD-AUTH:5")
    _code, bundle = run_scan(proj, "--scope", "PRD-AUTH-E1")
    assert bundle["inherited_context"] == []


def test_no_rollup_empties_descendant_rollup(tmp_path):
    proj = make_proj(tmp_path)
    _seed_index(proj, "260603-0001", "PRD-AUTH-E1-S1", "PRD-AUTH-E1-S1:2")
    _code, bundle = run_scan(proj, "--scope", "PRD-AUTH-E1", "--no-rollup")
    assert bundle["descendant_rollup"] == {}


def test_inherit_on_empty_index_is_clean_noop(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "PRD-AUTH-E1")
    assert bundle["inherited_context"] == []
    assert bundle["descendant_rollup"] == {}
