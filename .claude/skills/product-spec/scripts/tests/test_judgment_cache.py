"""Tests for the judgment cache (judgment_cache.py).

The judgment cache reuses LLM verdicts for unchanged nodes so a re-validate of an
unchanged spec issues zero LLM calls on the single-node checks. The SCRIPT half
owns everything deterministic: the cache KEY (check | scope_key | hash(es) | lang
| dep_hash), the staleness verdict (cache hit vs miss), the version/model stamp,
the deletion garbage-collection, and the `--no-cache` bypass. The LLM half (not
exercised here) produces the verdict the script stamps.

Invariants under test:
  - the key is composed deterministically and is order-independent for a pair;
  - a body_hash change (single-node) or a core_value change (drift dep) → stale;
  - `contradiction` is NEVER cached (no entry written, never consulted);
  - a different caller-supplied --model-id, or a bumped cache_version → full miss;
  - the ruled-drift `po_ruling_ref: DEC-n` is a REFERENCE, surfaced on body change
    rather than silently re-flagged (decisions.md stays authoritative);
  - deleted node ids are GC'd from the cache (single-node + pair entries);
  - `last_validated.json` is written on --validate ONLY, through the soft fence.
"""

import json
import shutil
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
import judgment_cache as jc  # noqa: E402
from fs_guard import FenceError  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"

MODEL_A = "claude-opus-4-8"
MODEL_B = "claude-sonnet-4-6"


def _proj(tmp_path: Path) -> Path:
    """A writable copy of the valid-spec fixture."""
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    return proj


def _node(graph, node_id):
    for n in graph["nodes"]:
        if n["id"] == node_id:
            return n
    raise AssertionError(f"node {node_id} not in graph")


# ---------- Test 1: single-node key composition + freshness ----------

def test_key_single_node(tmp_path):
    """A single-node key is `check|node_id|body_hash|lang|`; the entry is fresh
    right after a store and goes stale when the node's body_hash changes."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    story = _node(graph, "PRD-AUTH-E1-S1")

    key = jc.compute_key("invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph)
    assert key.startswith("invest_quality|PRD-AUTH-E1-S1|")
    assert story["body_hash"] in key

    jc.store(proj, key, verdict={"finding": None}, model_id=MODEL_A)
    check = jc.check(proj, "invest_quality", node_ids=["PRD-AUTH-E1-S1"],
                     graph=graph, model_id=MODEL_A)
    assert check["fresh"] is True
    assert check["stale"] is False

    # Edit the story body → its body_hash changes → key changes → stale.
    story_path = proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md"
    story_path.write_text(
        story_path.read_text(encoding="utf-8") + "\n\nExtra paragraph.\n",
        encoding="utf-8",
    )
    graph2 = build_graph(proj)
    check2 = jc.check(proj, "invest_quality", node_ids=["PRD-AUTH-E1-S1"],
                      graph=graph2, model_id=MODEL_A)
    assert check2["stale"] is True
    assert check2["fresh"] is False


# ---------- Test 1b: a lang flip is a full miss (lang key segment) ----------

def test_lang_flip_invalidates(tmp_path):
    """The key carries a `lang` segment because a verdict's wording is
    lang-sensitive. Storing a verdict under `en` and then flipping the node's
    frontmatter `lang` en→vi changes the key segment → the entry goes stale even
    though the body is byte-identical (proves the lang segment is load-bearing, not
    inert)."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)

    key_en = jc.compute_key("invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph)
    assert key_en.endswith("|en|") or "|en|" in key_en
    jc.store(proj, key_en, verdict={"finding": None}, model_id=MODEL_A)
    assert jc.check(proj, "invest_quality", node_ids=["PRD-AUTH-E1-S1"],
                    graph=graph, model_id=MODEL_A)["fresh"] is True

    # Flip the story's frontmatter lang en→vi (body text unchanged) AND the PRODUCT
    # lang so the fallback agrees — the lang key segment must now read `vi`.
    story_path = proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md"
    story_path.write_text(
        story_path.read_text(encoding="utf-8").replace("lang: en", "lang: vi", 1),
        encoding="utf-8",
    )
    prod = proj / "docs" / "product" / "PRODUCT.md"
    prod.write_text(prod.read_text(encoding="utf-8").replace("lang: en", "lang: vi", 1),
                    encoding="utf-8")

    graph2 = build_graph(proj)
    key_vi = jc.compute_key("invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph2)
    assert key_vi != key_en, "lang flip must change the key"
    assert "|vi|" in key_vi
    # The en-stored verdict is a full miss under the flipped lang.
    assert jc.check(proj, "invest_quality", node_ids=["PRD-AUTH-E1-S1"],
                    graph=graph2, model_id=MODEL_A)["stale"] is True


# ---------- Test 2: semantic_duplication pair key is order-independent ----------

def test_key_semantic_dup_pair_sorted(tmp_path):
    """A pair check keys on the SORTED (idA, idB) tuple so `(A,B)` and `(B,A)`
    map to the same cache key — the pair is unordered."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)

    k_ab = jc.compute_key("semantic_duplication",
                          node_ids=["PRD-AUTH", "PRD-AUTH-E1"], graph=graph)
    k_ba = jc.compute_key("semantic_duplication",
                          node_ids=["PRD-AUTH-E1", "PRD-AUTH"], graph=graph)
    assert k_ab == k_ba
    # Both ids appear in the key (sorted).
    assert "PRD-AUTH" in k_ab and "PRD-AUTH-E1" in k_ab

    jc.store(proj, k_ab, verdict={"finding": None}, model_id=MODEL_A)
    # Querying with the reversed order still hits the same entry.
    check = jc.check(proj, "semantic_duplication",
                     node_ids=["PRD-AUTH-E1", "PRD-AUTH"], graph=graph,
                     model_id=MODEL_A)
    assert check["fresh"] is True


# ---------- Test 3: core_value_drift dep invalidates on core_value change ----------

def test_core_value_drift_dep_invalidates(tmp_path):
    """core_value_drift carries a dep_hash of the PRODUCT core_value. Changing the
    core_value sentence → the dep_hash changes → the drift entry goes stale even
    though the artifact body is byte-identical."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)

    key = jc.compute_key("core_value_drift", node_ids=["PRD-AUTH"], graph=graph)
    assert "cv:" in key  # dep_hash segment present
    jc.store(proj, key, verdict={"finding": None}, model_id=MODEL_A)
    assert jc.check(proj, "core_value_drift", node_ids=["PRD-AUTH"],
                    graph=graph, model_id=MODEL_A)["fresh"] is True

    # Change PRODUCT.core_value only (the PRD body is untouched).
    prod = proj / "docs" / "product" / "PRODUCT.md"
    text = prod.read_text(encoding="utf-8")
    text = text.replace(
        "Help boutique brands sell directly to fans without middlemen.",
        "A wholly different core value sentence.",
    )
    prod.write_text(text, encoding="utf-8")
    graph2 = build_graph(proj)
    check2 = jc.check(proj, "core_value_drift", node_ids=["PRD-AUTH"],
                      graph=graph2, model_id=MODEL_A)
    assert check2["stale"] is True


# ---------- Test 4: contradiction is never cached ----------

def test_contradiction_never_cached(tmp_path):
    """The contradiction check must never read or write the cache — it is a
    safety check against approved artifacts and must run every time."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)

    # compute_key refuses contradiction.
    import pytest
    with pytest.raises(ValueError):
        jc.compute_key("contradiction", node_ids=["PRD-AUTH"], graph=graph)

    # store refuses contradiction (defensive — never persists an entry).
    with pytest.raises(ValueError):
        jc.store(proj, "contradiction|PRD-AUTH|x||", verdict={"finding": None},
                 model_id=MODEL_A)

    # check on contradiction always reports stale (must always run), and writes
    # no cache file.
    res = jc.check(proj, "contradiction", node_ids=["PRD-AUTH"], graph=graph,
                   model_id=MODEL_A)
    assert res["stale"] is True
    assert res["fresh"] is False
    cache_path = proj / "docs" / "product" / ".memory" / "judgments.json"
    assert not cache_path.exists(), "contradiction must not create the cache file"


# ---------- Test 5: version/model mismatch → full miss ----------

def test_version_model_mismatch_full_miss(tmp_path):
    """A stored verdict under MODEL_A is stale when queried with MODEL_B, and a
    bumped cache_version invalidates every entry (proves the caller-supplied
    model stamp + version stamp actually fire)."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    key = jc.compute_key("invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph)
    jc.store(proj, key, verdict={"finding": None}, model_id=MODEL_A)

    # Same model → fresh.
    assert jc.check(proj, "invest_quality", node_ids=["PRD-AUTH-E1-S1"],
                    graph=graph, model_id=MODEL_A)["fresh"] is True
    # Different caller-supplied model → stale (full miss).
    assert jc.check(proj, "invest_quality", node_ids=["PRD-AUTH-E1-S1"],
                    graph=graph, model_id=MODEL_B)["stale"] is True

    # Bumped cache_version on disk → full miss even for the same model.
    cache_path = proj / "docs" / "product" / ".memory" / "judgments.json"
    data = json.loads(cache_path.read_text(encoding="utf-8"))
    data["cache_version"] = data["cache_version"] + "-bumped"
    cache_path.write_text(json.dumps(data), encoding="utf-8")
    assert jc.check(proj, "invest_quality", node_ids=["PRD-AUTH-E1-S1"],
                    graph=graph, model_id=MODEL_A)["stale"] is True


# ---------- Test 6: po_ruling_ref surfaces the active DEC, no silent re-flag --

def test_po_ruling_ref_surfaces_dec(tmp_path):
    """A ruled-drift entry carries `po_ruling_ref: DEC-n` (a REFERENCE). While the
    body is unchanged the cache hit suppresses a re-flag. On a body change the
    entry invalidates AND the script surfaces the active DEC (decisions.md is
    authoritative) so the orchestration can re-ask instead of silently re-flagging.
    """
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    key = jc.compute_key("core_value_drift", node_ids=["PRD-AUTH"], graph=graph)
    jc.store(proj, key, verdict={"finding": "weak"}, model_id=MODEL_A,
             po_ruling_ref="DEC-3")

    # Body unchanged → fresh hit; the stored ruling reference is exposed so the
    # orchestration knows not to re-nag.
    fresh = jc.check(proj, "core_value_drift", node_ids=["PRD-AUTH"],
                     graph=graph, model_id=MODEL_A)
    assert fresh["fresh"] is True
    assert fresh["po_ruling_ref"] == "DEC-3"

    # Edit the PRD body → the entry invalidates (re-judge the content, correct).
    prd_path = proj / "docs" / "product" / "prds" / "auth.md"
    prd_path.write_text(
        prd_path.read_text(encoding="utf-8") + "\n\nNew scope paragraph.\n",
        encoding="utf-8",
    )
    graph2 = build_graph(proj)
    stale = jc.check(proj, "core_value_drift", node_ids=["PRD-AUTH"],
                     graph=graph2, model_id=MODEL_A)
    assert stale["stale"] is True
    # The script still surfaces the prior ruling reference attached to this
    # node+check, so the orchestration can ask "you accepted DEC-3 for the prior
    # wording — still applies?" rather than silently re-flagging.
    assert stale["prior_po_ruling_ref"] == "DEC-3"


# ---------- Test 7: --no-cache bypass ----------

def test_no_cache_bypass(tmp_path):
    """With no_cache=True, check() always reports stale (cache ignored) and
    store() is a no-op (no entry persisted)."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    key = jc.compute_key("invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph)
    jc.store(proj, key, verdict={"finding": None}, model_id=MODEL_A)

    # Normally a hit, but no_cache ignores it.
    bypass = jc.check(proj, "invest_quality", node_ids=["PRD-AUTH-E1-S1"],
                      graph=graph, model_id=MODEL_A, no_cache=True)
    assert bypass["stale"] is True

    # no_cache store does not persist.
    proj2 = _proj(tmp_path / "two")
    graph2 = build_graph(proj2)
    key2 = jc.compute_key("invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph2)
    jc.store(proj2, key2, verdict={"finding": None}, model_id=MODEL_A, no_cache=True)
    cache_path = proj2 / "docs" / "product" / ".memory" / "judgments.json"
    assert not cache_path.exists()


# ---------- Test 8: incremental — only the changed node is stale ----------

def test_incremental_only_stale(tmp_path):
    """Store verdicts for every story-scoped node, change ONE node's body, then
    --check the per-check stale/fresh split: only the changed node is stale."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    story_ids = [n["id"] for n in graph["nodes"] if n["type"] == "story"]
    assert story_ids, "fixture must carry at least one story"

    for sid in story_ids:
        k = jc.compute_key("invest_quality", node_ids=[sid], graph=graph)
        jc.store(proj, k, verdict={"finding": None}, model_id=MODEL_A)

    # All fresh before any edit.
    split = jc.check_per_check(proj, "invest_quality",
                               node_id_sets=[[s] for s in story_ids],
                               graph=graph, model_id=MODEL_A)
    assert split["stale"] == []
    assert sorted(t[0] for t in split["fresh"]) == sorted(story_ids)

    # Change exactly one story.
    target = story_ids[0]
    sp = proj / "docs" / "product" / "stories" / f"{target}.md"
    sp.write_text(sp.read_text(encoding="utf-8") + "\n\nedit\n", encoding="utf-8")
    graph2 = build_graph(proj)
    split2 = jc.check_per_check(proj, "invest_quality",
                                node_id_sets=[[s] for s in story_ids],
                                graph=graph2, model_id=MODEL_A)
    stale_ids = [t[0] for t in split2["stale"]]
    assert stale_ids == [target]


# ---------- Test 9: deleted node is GC'd (single + pair entries) ----------

def test_deleted_node_evicted(tmp_path):
    """Deleting a node from the graph evicts its single-node AND its pair cache
    entries on the next --check/--store (set-difference vs graph node ids) — no
    dead entries, no id-reuse collision."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    story_id = "PRD-AUTH-E1-S1"

    single = jc.compute_key("invest_quality", node_ids=[story_id], graph=graph)
    pair = jc.compute_key("semantic_duplication",
                          node_ids=["PRD-AUTH", story_id], graph=graph)
    jc.store(proj, single, verdict={"finding": None}, model_id=MODEL_A)
    jc.store(proj, pair, verdict={"finding": None}, model_id=MODEL_A)

    cache_path = proj / "docs" / "product" / ".memory" / "judgments.json"
    data = json.loads(cache_path.read_text(encoding="utf-8"))
    assert single in data["entries"] and pair in data["entries"]

    # Delete the story file → it leaves the graph.
    (proj / "docs" / "product" / "stories" / f"{story_id}.md").unlink()
    graph2 = build_graph(proj)
    assert story_id not in {n["id"] for n in graph2["nodes"]}

    # GC against the new graph: both the single-node and the pair entry vanish.
    jc.gc_deleted(proj, graph2)
    data2 = json.loads(cache_path.read_text(encoding="utf-8"))
    assert single not in data2["entries"]
    assert pair not in data2["entries"]


# ---------- Test 10: last_validated.json written on --validate only ----------

def test_last_validated_written_on_validate_only(tmp_path):
    """`write_last_validated` (the --validate-only marker) writes
    docs/product/.memory/last_validated.json with the snapshot filename + hash,
    through the soft fence. A bare snapshot write (--viz --snapshot) does NOT call
    it, so the marker is the --validate signal the --status command reads."""
    from spec_graph import write_snapshot
    proj = _proj(tmp_path)
    graph = build_graph(proj)

    marker = proj / "docs" / "product" / ".memory" / "last_validated.json"

    # A bare snapshot (the --viz --snapshot path) writes the snapshot but NOT the
    # marker.
    snap = write_snapshot(graph, proj)
    assert snap.exists()
    assert not marker.exists(), "bare snapshot must not write the validate marker"

    # The --validate path writes the marker through the fence.
    out = jc.write_last_validated(proj, snap)
    assert out == marker
    assert marker.exists()
    payload = json.loads(marker.read_text(encoding="utf-8"))
    # snapshot filename + content hash recorded for the --status command.
    assert payload["snapshot"] == snap.name
    assert isinstance(payload["snapshot_hash"], str) and len(payload["snapshot_hash"]) == 8
    assert "validated_at" in payload


def test_last_validated_honours_fence(tmp_path):
    """`write_last_validated` fence-checks the referenced snapshot path before it
    writes the marker. A snapshot reference that resolves outside docs/product/ must
    raise FenceError from the writer itself (exercising the writer's fence wiring,
    not the guard in isolation) — so a tampered snapshot ref can never write the
    marker against an out-of-tree file."""
    proj = _proj(tmp_path)
    import pytest
    with pytest.raises(FenceError):
        jc.write_last_validated(proj, Path("/tmp/escape.json"))
    # And the marker is NOT created when the fence rejects the snapshot ref.
    marker = proj / "docs" / "product" / ".memory" / "last_validated.json"
    assert not marker.exists()
