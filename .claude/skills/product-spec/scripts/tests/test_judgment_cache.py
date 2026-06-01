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


# ----------------------------------------------------------------------------
# Batch write (--store-batch): validate-ALL-then-write-ONCE.
#
# The per-verdict --store calls collapse N→1 so the orchestration cannot store
# some verdicts and forget others mid-loop. The batch is atomic: a single bad
# entry (a contradiction key, never cacheable) fails the WHOLE batch and writes
# nothing — mirroring the decision_register validate-before-write ordering. Every
# single-store semantic is preserved (validate-stamp reset on model mismatch,
# po_ruling_ref passthrough, deleted-node GC), and the batch additionally persists
# `.memory/last_judged.json` (verdict count + content snapshot hash) so the memory
# gap detector can spot "graph drifted since judged but the cache didn't grow".
# ----------------------------------------------------------------------------

def _keys_for(graph, ids):
    """All single-node invest_quality keys for the given node ids."""
    return {nid: jc.compute_key("invest_quality", node_ids=[nid], graph=graph)
            for nid in ids}


# The fixture carries one story, one epic, one PRD — a real multi-entry batch
# spans all three body-bearing nodes (not just the lone story) so N>1 is exercised.
BATCH_IDS = ["PRD-AUTH-E1-S1", "PRD-AUTH-E1", "PRD-AUTH"]


def _entry(key, verdict=None, po_ruling_ref=None):
    e = {"key": key, "verdict": verdict if verdict is not None else {"finding": None}}
    if po_ruling_ref:
        e["po_ruling_ref"] = po_ruling_ref
    return e


# ---------- Batch test 1: one write persists every entry ----------

def test_store_batch_writes_all(tmp_path):
    """N entries handed to store_batch are all present after ONE read-modify-write —
    the collapse of the per-verdict --store loop into a single call."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    keys = _keys_for(graph, BATCH_IDS)
    assert len(keys) >= 2, "batch test must span more than one node"
    entries = [_entry(k) for k in keys.values()]

    path = jc.store_batch(proj, entries, model_id=MODEL_A)
    assert path is not None

    cache = json.loads(path.read_text(encoding="utf-8"))
    for nid, k in keys.items():
        assert k in cache["entries"], f"{nid} missing after batch write"
    # Every batched node now reports a fresh cache hit.
    for nid in BATCH_IDS:
        assert jc.check(proj, "invest_quality", node_ids=[nid], graph=graph,
                        model_id=MODEL_A)["fresh"] is True


# ---------- Batch test 2: atomic — a bad entry writes NOTHING ----------

def test_store_batch_atomic_on_bad_entry(tmp_path):
    """A `contradiction` key anywhere in the batch (never cacheable) fails the WHOLE
    batch with ValueError and leaves the cache byte-unchanged — validate-all-first,
    write-once. No partial write of the good entries that preceded the bad one."""
    import pytest
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    good = _keys_for(graph, BATCH_IDS)
    # A contradiction key is refused at the per-entry validate pass.
    bad_entry = _entry("contradiction|PRD-AUTH|x||")
    entries = [_entry(k) for k in good.values()] + [bad_entry]

    cache_path = proj / "docs" / "product" / ".memory" / "judgments.json"
    assert not cache_path.exists()

    with pytest.raises(ValueError):
        jc.store_batch(proj, entries, model_id=MODEL_A)

    # NOTHING written — not even the good entries that validated before the bad one.
    assert not cache_path.exists(), "atomic batch must not write on a bad entry"
    # last_judged must not be written either (the whole batch failed).
    assert not (proj / "docs" / "product" / ".memory" / "last_judged.json").exists()


def test_store_batch_atomic_preexisting_cache_unchanged(tmp_path):
    """When a cache already exists, a failing batch leaves it byte-for-byte
    unchanged (atomicity over a non-empty starting state, not just the empty one)."""
    import pytest
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    pre_key = jc.compute_key("invest_quality", node_ids=[BATCH_IDS[0]], graph=graph)
    jc.store(proj, pre_key, verdict={"finding": "pre"}, model_id=MODEL_A)

    cache_path = proj / "docs" / "product" / ".memory" / "judgments.json"
    before = cache_path.read_bytes()

    entries = [_entry(jc.compute_key("invest_quality", node_ids=[nid], graph=graph))
               for nid in BATCH_IDS] + [_entry("contradiction|PRD-AUTH|x||")]
    with pytest.raises(ValueError):
        jc.store_batch(proj, entries, model_id=MODEL_A)

    assert cache_path.read_bytes() == before, "failing batch must not mutate the cache"


# ---------- Batch test 3: model mismatch resets the cache, then stores ----------

def test_store_batch_model_mismatch_resets(tmp_path):
    """A batch under a NEW model id resets the (old-model) cache before storing —
    same stamp-reset semantic as single --store, so a stale-model verdict can never
    survive alongside a fresh-model batch."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    old_key = jc.compute_key("invest_quality", node_ids=[BATCH_IDS[0]], graph=graph)
    jc.store(proj, old_key, verdict={"finding": "old"}, model_id=MODEL_A)

    # Batch under MODEL_B → the MODEL_A cache is reset; only the batch survives.
    new_keys = _keys_for(graph, BATCH_IDS)
    path = jc.store_batch(proj, [_entry(k) for k in new_keys.values()],
                          model_id=MODEL_B)
    cache = json.loads(path.read_text(encoding="utf-8"))
    assert cache["model_id"] == MODEL_B
    for k in new_keys.values():
        assert k in cache["entries"]
    # The reset means the new model sees only fresh-model entries; querying the
    # old model id is now a full miss.
    assert jc.check(proj, "invest_quality", node_ids=[BATCH_IDS[0]], graph=graph,
                    model_id=MODEL_A)["stale"] is True
    assert jc.check(proj, "invest_quality", node_ids=[BATCH_IDS[0]], graph=graph,
                    model_id=MODEL_B)["fresh"] is True


# ---------- Batch test 4: po_ruling_ref survives the batch ----------

def test_store_batch_po_ruling_passthrough(tmp_path):
    """A `po_ruling_ref: DEC-n` carried on a batched entry survives the write and is
    surfaced on the subsequent fresh hit — the ruled-drift reference is preserved
    end-to-end through the batch path, not just single --store."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    key = jc.compute_key("core_value_drift", node_ids=["PRD-AUTH"], graph=graph)
    jc.store_batch(proj, [_entry(key, verdict={"finding": "weak"},
                                 po_ruling_ref="DEC-7")], model_id=MODEL_A)

    hit = jc.check(proj, "core_value_drift", node_ids=["PRD-AUTH"], graph=graph,
                   model_id=MODEL_A)
    assert hit["fresh"] is True
    assert hit["po_ruling_ref"] == "DEC-7"


# ---------- Batch test 5: legacy single --store still works (regression) ------

def test_single_store_still_works(tmp_path):
    """Adding the batch path must not regress the single --store entry point: a lone
    --store stamp/version/po_ruling_ref flow is byte-for-byte the prior behavior."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    key = jc.compute_key("invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph)
    path = jc.store(proj, key, verdict={"finding": None}, model_id=MODEL_A)
    assert path is not None
    cache = json.loads(path.read_text(encoding="utf-8"))
    assert key in cache["entries"]
    assert cache["model_id"] == MODEL_A
    assert jc.check(proj, "invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph,
                    model_id=MODEL_A)["fresh"] is True


# ---------- Batch test 6: deleted-node entries GC'd during the batch ----------

def test_store_batch_gc(tmp_path):
    """A batch write GCs entries whose nodes have left the graph — same set-diff vs
    live node ids as single-store GC, folded into the one batch write so dead
    entries never linger after a node deletion."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    doomed = "PRD-AUTH-E1-S1"
    doomed_key = jc.compute_key("invest_quality", node_ids=[doomed], graph=graph)
    jc.store(proj, doomed_key, verdict={"finding": None}, model_id=MODEL_A)

    cache_path = proj / "docs" / "product" / ".memory" / "judgments.json"
    assert doomed_key in json.loads(cache_path.read_text(encoding="utf-8"))["entries"]

    # Delete the story → it leaves the graph.
    (proj / "docs" / "product" / "stories" / f"{doomed}.md").unlink()
    graph2 = build_graph(proj)
    assert doomed not in {n["id"] for n in graph2["nodes"]}

    # Batch-store some OTHER surviving node (the parent epic survives the story
    # deletion); the doomed entry is GC'd in the same write.
    survivor = next(n["id"] for n in graph2["nodes"] if n["id"] == "PRD-AUTH-E1")
    surv_key = jc.compute_key("invest_quality", node_ids=[survivor], graph=graph2)
    jc.store_batch(proj, [_entry(surv_key)], model_id=MODEL_A)

    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    assert doomed_key not in cache["entries"], "deleted-node entry must be GC'd"
    assert surv_key in cache["entries"]


# ---------- Batch test 7: batch store writes last_judged.json ----------

def test_store_batch_writes_last_judged(tmp_path):
    """A batch store persists `.memory/last_judged.json` (verdict count + content
    snapshot hash) through the soft fence so the memory-gap detector can spot drift
    since the last judged batch. The count matches the live cache; the hash is a
    deterministic content fingerprint (stable for identical content)."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    keys = _keys_for(graph, BATCH_IDS)
    jc.store_batch(proj, [_entry(k) for k in keys.values()], model_id=MODEL_A)

    marker = proj / "docs" / "product" / ".memory" / "last_judged.json"
    assert marker.exists()
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["verdict_count"] == len(keys)
    assert isinstance(payload["snapshot_hash"], str) and len(payload["snapshot_hash"]) == 8
    assert "judged_at" in payload

    # The fingerprint is content-derived + deterministic: recomputing it on the same
    # graph yields the identical hash (no embedded timestamp), so the gap detector
    # can recompute + compare it to detect drift.
    assert jc.graph_content_hash(graph) == payload["snapshot_hash"]

    # A content edit changes the fingerprint (so drift is detectable).
    sp = proj / "docs" / "product" / "stories" / "PRD-AUTH-E1-S1.md"
    sp.write_text(sp.read_text(encoding="utf-8") + "\n\nedit\n", encoding="utf-8")
    graph2 = build_graph(proj)
    assert jc.graph_content_hash(graph2) != payload["snapshot_hash"]


def test_store_batch_last_judged_honours_fence(tmp_path, monkeypatch):
    """The last_judged write goes through the soft fence (assert_under_docs_product),
    same chokepoint as every other memory write — a redirected path can never escape
    docs/product/."""
    import pytest
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    key = jc.compute_key("invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph)

    # Force the last_judged path outside docs/product/ → the fence must reject it.
    monkeypatch.setattr(jc, "_last_judged_path",
                        lambda root: Path("/tmp/escape-last-judged.json"))
    with pytest.raises(FenceError):
        jc.store_batch(proj, [_entry(key)], model_id=MODEL_A)
    assert not Path("/tmp/escape-last-judged.json").exists()


# ---------- Batch CLI: --store-batch reads JSON from a file or stdin ----------

def test_store_batch_cli_from_file(tmp_path, capsys, monkeypatch):
    """`--store-batch <file>` reads the JSON entry list from a file and performs the
    one batch write; stdout reports the count + last_judged marker."""
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    keys = _keys_for(graph, BATCH_IDS)
    payload_file = tmp_path / "batch.json"
    payload_file.write_text(
        json.dumps([_entry(k) for k in keys.values()]), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", [
        "judgment_cache.py", "--root", str(proj), "--store-batch", str(payload_file),
        "--model-id", MODEL_A])
    rc = jc.main()
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["stored"] is True
    assert out["count"] == len(keys)

    cache_path = proj / "docs" / "product" / ".memory" / "judgments.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    for k in keys.values():
        assert k in cache["entries"]
    assert (proj / "docs" / "product" / ".memory" / "last_judged.json").exists()


def test_store_batch_cli_from_stdin(tmp_path, capsys, monkeypatch):
    """`--store-batch -` reads the JSON entry list from stdin."""
    import io
    proj = _proj(tmp_path)
    graph = build_graph(proj)
    key = jc.compute_key("invest_quality", node_ids=["PRD-AUTH-E1-S1"], graph=graph)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps([_entry(key)])))
    monkeypatch.setattr(sys, "argv", [
        "judgment_cache.py", "--root", str(proj), "--store-batch", "-",
        "--model-id", MODEL_A])
    rc = jc.main()
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["stored"] is True
    assert out["count"] == 1
