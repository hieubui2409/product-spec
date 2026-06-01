#!/usr/bin/env python3
"""
judgment_cache — the deterministic SCRIPT half of the incremental-validate cache.

A re-validate of an unchanged spec should issue ZERO LLM calls on the single-node
quality checks. This module makes that possible without ever letting a stale
verdict slip through: it owns the cache KEY, the staleness verdict (hit vs miss),
the caller-supplied model/version stamp, the deleted-node garbage-collection, and
the `--no-cache` bypass. The LLM produces the verdict; this script only stamps,
keys, and compares it — never judges.

SCRIPT-vs-LLM split (CLAUDE.md): everything here is deterministic structural work
over the spec graph. The cache is an OPTIMIZATION, never authoritative — a miss
is always safe (re-judge), so any doubt resolves to "stale". The validate gate
never depends on a cache hit.

Key grammar:  ``check | scope_key | hashes | lang | dep_hash``
  - single-node check (invest_quality / vagueness / gold_plating / time_realism /
    competitive_drift / core_value_drift):  scope_key = node_id, hashes = body_hash
  - semantic_duplication (a PAIR check): scope_key = the two ids SORTED + joined,
    hashes = the two body_hashes in the SAME sorted order. So `(A,B)` and `(B,A)`
    map to one key — the pair is unordered.
  - core_value_drift additionally stamps dep_hash = ``cv:<hash(core_value)>`` so a
    change to the PRODUCT core-value sentence invalidates every drift verdict even
    when the artifact body is byte-identical.
  - contradiction is NEVER cached (a safety check against approved artifacts must
    run every time) — compute_key / store refuse it; check always reports stale.

Storage: ``docs/product/.memory/judgments.json`` (committed, per the locked
folder-split decision). Schema:

    {cache_version, model_id, entries: {<key>: {verdict, po_ruling_ref?, stored_at}}}

The `model_id` is CALLER-SUPPLIED (`--model-id`), never self-detected: the script
must stay deterministic and the running model is non-deterministic session state.
The orchestration layer knows its own model and passes it; the script treats it as
opaque data it stamps + compares. A different model id, or a bumped
``cache_version``, is a FULL MISS (every entry stale) — a model change can shift
every judgment.

Ruled-drift (`po_ruling_ref: DEC-n`): a verdict may carry a REFERENCE to a PO
ruling in ``decisions.md`` (the authoritative home — never the verdict itself). On
a fresh hit the reference is surfaced so the orchestration suppresses a re-nag. On
a body change the entry invalidates (re-judge the new content, correct) BUT the
prior ruling reference is still surfaced as ``prior_po_ruling_ref`` so the
orchestration can ask "you accepted DEC-n for the prior wording — still applies?"
rather than silently re-flagging (no-silent-reversal; DRY against decisions.md).

All writes go through the shared soft fence (``fs_guard``) so a cache/marker write
can never escape the spec boundary.

CLI:
    judgment_cache.py --root <dir> --check  --check-name <c> --node-ids A[,B] \
        --model-id <id> [--no-cache]
    judgment_cache.py --root <dir> --store  --key <k> --model-id <id> \
        --verdict <json> [--po-ruling-ref DEC-n] [--no-cache]
    judgment_cache.py --root <dir> --gc     # evict entries for deleted node ids
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from encoding_utils import configure_utf8_console
from fs_guard import assert_under_docs_product
from spec_graph import build_graph

configure_utf8_console()


# Bump this when the KEY GRAMMAR or the cache SEMANTICS change in a way that makes
# old entries unsafe to reuse. A mismatch with the on-disk stamp is a full miss
# (every entry re-judged) — the safe direction.
CACHE_VERSION = "1"

# The one check that is NEVER cached: contradiction is a safety check against
# approved artifacts and must re-run on every validate (no entry, never consulted).
NEVER_CACHED = frozenset({"contradiction"})

# Pair checks key on the SORTED two-id tuple (unordered pair). Listed here so the
# arity is one home, not a scatter of `== "semantic_duplication"` literals.
PAIR_CHECKS = frozenset({"semantic_duplication"})

# Checks whose verdict depends on the PRODUCT core-value sentence (not just the
# node body). They stamp a `cv:` dep_hash so a core-value edit invalidates them.
CORE_VALUE_DEP_CHECKS = frozenset({"core_value_drift"})


def _cache_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "judgments.json"


def _last_validated_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "last_validated.json"


def _now() -> str:
    """Memory-layer UTC timestamp (`+00:00` offset form) — one home for the two
    write paths below. Mirrors behavioral_memory._now; intentionally distinct from
    spec_graph._now, which uses the `Z`-suffix graph-snapshot form."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ----------------------------------------------------------------------------
# Key composition (deterministic — the whole point of the cache)
# ----------------------------------------------------------------------------

def _node_index(graph: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {n["id"]: n for n in graph.get("nodes", [])}


def _body_hash(node: Optional[Dict[str, Any]]) -> str:
    """The node's body fingerprint, or a stable sentinel when the node is absent
    or has no body (a goal). A missing node yields a key that can never collide
    with a real one and will always miss — the safe direction."""
    if not node:
        return "missing"
    bh = node.get("body_hash")
    return bh if isinstance(bh, str) else "none"


def _lang_segment(nodes: List[Optional[Dict[str, Any]]], graph: Dict[str, Any]) -> str:
    """The judgment language for the key. A verdict's wording is lang-sensitive, so
    a lang flip must miss. Use the first present node's `lang`, else the PRODUCT
    lang, else `en` — deterministic and single-valued per key."""
    for n in nodes:
        if n and isinstance(n.get("lang"), str):
            return n["lang"]
    prod = graph.get("product") or {}
    return prod.get("lang") if isinstance(prod.get("lang"), str) else "en"


def _core_value_dep(check: str, graph: Dict[str, Any]) -> str:
    """The dep_hash segment. For a core-value-dependent check it is
    `cv:<hash(core_value)>` so a core-value edit invalidates the entry; otherwise
    empty (the body_hash already covers the dependency)."""
    if check not in CORE_VALUE_DEP_CHECKS:
        return ""
    prod = graph.get("product") or {}
    cv = prod.get("core_value")
    cv_text = cv if isinstance(cv, str) else ""
    return "cv:" + hashlib.sha256(cv_text.encode("utf-8")).hexdigest()[:8]


def compute_key(check: str, node_ids: List[str], graph: Dict[str, Any]) -> str:
    """Compose the deterministic cache key for `check` over `node_ids`.

    Single-node: `check|node_id|body_hash|lang|dep_hash`.
    Pair check : `check|idA+idB|body_hashA+body_hashB|lang|dep_hash`, with the two
                 ids SORTED so the pair is unordered.
    Refuses `contradiction` (never cached)."""
    if check in NEVER_CACHED:
        raise ValueError(f"{check!r} is never cached (no key)")

    idx = _node_index(graph)
    if check in PAIR_CHECKS:
        if len(node_ids) != 2:
            raise ValueError(f"{check!r} is a pair check; got {len(node_ids)} ids")
        a, b = sorted(node_ids)  # unordered pair → canonical sorted order
        scope_key = f"{a}+{b}"
        hashes = f"{_body_hash(idx.get(a))}+{_body_hash(idx.get(b))}"
        nodes = [idx.get(a), idx.get(b)]
    else:
        if len(node_ids) != 1:
            raise ValueError(f"{check!r} is a single-node check; got {len(node_ids)} ids")
        nid = node_ids[0]
        scope_key = nid
        hashes = _body_hash(idx.get(nid))
        nodes = [idx.get(nid)]

    lang = _lang_segment(nodes, graph)
    dep_hash = _core_value_dep(check, graph)
    return f"{check}|{scope_key}|{hashes}|{lang}|{dep_hash}"


# ----------------------------------------------------------------------------
# Cache file IO + stamp
# ----------------------------------------------------------------------------

def _empty_cache(model_id: str) -> Dict[str, Any]:
    return {"cache_version": CACHE_VERSION, "model_id": model_id, "entries": {}}


def load_cache(root) -> Optional[Dict[str, Any]]:
    """Return the parsed cache dict, or None when the file is absent/corrupt.

    A corrupt or wrong-shaped file degrades to None (treated as a full miss by the
    callers) — the cache is never authoritative, so a parse failure is safe, never
    a crash."""
    path = _cache_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("entries"), dict):
        return None
    return data


def _stamp_valid(cache: Optional[Dict[str, Any]], model_id: str) -> bool:
    """True iff the on-disk stamp matches the current `cache_version` AND the
    caller-supplied `model_id`. A mismatch is a FULL MISS — a model or schema
    change can shift every judgment, so every entry is re-judged."""
    if cache is None:
        return False
    return cache.get("cache_version") == CACHE_VERSION and cache.get("model_id") == model_id


def _write_cache(root, cache: Dict[str, Any]) -> Path:
    path = _cache_path(root)
    # Soft fence: resolve + contain BEFORE any mkdir/write.
    assert_under_docs_product(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(cache, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return path


# ----------------------------------------------------------------------------
# store / check
# ----------------------------------------------------------------------------

def store(root, key: str, verdict: Any, model_id: str,
          po_ruling_ref: Optional[str] = None, no_cache: bool = False) -> Optional[Path]:
    """Persist one verdict under `key`. No-op (returns None) when `no_cache`.

    Refuses a `contradiction` key (defensive — that check is never cached). If the
    on-disk stamp does not match the caller's `model_id`/version, the cache is
    RESET to the current stamp before storing — a stale-stamp file must not keep
    serving old-model verdicts alongside a fresh one."""
    if no_cache:
        return None
    if key.split("|", 1)[0] in NEVER_CACHED:
        raise ValueError("contradiction is never cached")

    cache = load_cache(root)
    if not _stamp_valid(cache, model_id):
        cache = _empty_cache(model_id)  # reset on a stamp mismatch
    entry: Dict[str, Any] = {
        "verdict": verdict,
        "stored_at": _now(),
    }
    if po_ruling_ref:
        entry["po_ruling_ref"] = po_ruling_ref
    cache["entries"][key] = entry
    return _write_cache(root, cache)


def check(root, check_name: str, node_ids: List[str], graph: Dict[str, Any],
          model_id: str, no_cache: bool = False) -> Dict[str, Any]:
    """Decide hit-or-miss for one (check, node set). Returns:

        {fresh, stale, key, po_ruling_ref?, prior_po_ruling_ref?, verdict?}

    `contradiction` and `no_cache` always report stale (must always run). A stamp
    mismatch is a full miss. On a fresh hit the stored `po_ruling_ref` is surfaced
    so the orchestration suppresses a re-nag; on a stale entry whose KEY-base
    (check + scope_key) matches a prior entry carrying a ruling, that prior
    reference is surfaced as `prior_po_ruling_ref` so the active DEC can be
    re-confirmed rather than silently re-flagged (decisions.md authoritative)."""
    if check_name in NEVER_CACHED:
        return {"fresh": False, "stale": True, "key": None}

    key = compute_key(check_name, node_ids, graph)
    if no_cache:
        return {"fresh": False, "stale": True, "key": key}

    cache = load_cache(root)
    if not _stamp_valid(cache, model_id):
        return {"fresh": False, "stale": True, "key": key}

    entries = cache["entries"]
    hit = entries.get(key)
    if hit is not None:
        out = {"fresh": True, "stale": False, "key": key, "verdict": hit.get("verdict")}
        if hit.get("po_ruling_ref"):
            out["po_ruling_ref"] = hit["po_ruling_ref"]
        return out

    # Miss. Surface a prior ruling attached to the SAME (check, scope_key) under a
    # different content hash — the body changed, but the PO's accepted ruling on
    # that node still deserves a re-confirm (no silent re-flag).
    prior = _prior_ruling_for(check_name, node_ids, entries)
    out = {"fresh": False, "stale": True, "key": key}
    if prior:
        out["prior_po_ruling_ref"] = prior
    return out


def _key_base(key: str) -> str:
    """The `check|scope_key` prefix of a key (identity of the node(s)+check,
    independent of the content hash / lang / dep). Two entries with the same base
    are the same judgment target at different content versions."""
    parts = key.split("|")
    return "|".join(parts[:2]) if len(parts) >= 2 else key


def _prior_ruling_for(check_name: str, node_ids: List[str],
                      entries: Dict[str, Any]) -> Optional[str]:
    """The newest `po_ruling_ref` among cached entries that share this (check,
    scope_key) base — i.e. the same node(s) judged under prior wording. Used to
    surface the active DEC on a body change instead of silently re-flagging."""
    if check_name in PAIR_CHECKS:
        a, b = sorted(node_ids)
        target_scope = f"{a}+{b}"
    else:
        target_scope = node_ids[0]
    target_base = f"{check_name}|{target_scope}"
    candidates: List[Tuple[str, str]] = []
    for k, e in entries.items():
        if _key_base(k) == target_base and isinstance(e, dict) and e.get("po_ruling_ref"):
            candidates.append((e.get("stored_at", ""), e["po_ruling_ref"]))
    if not candidates:
        return None
    candidates.sort()  # newest stored_at last
    return candidates[-1][1]


def check_per_check(root, check_name: str, node_id_sets: List[List[str]],
                    graph: Dict[str, Any], model_id: str,
                    no_cache: bool = False) -> Dict[str, Any]:
    """Split a check's candidate node-sets into stale vs fresh.

    Returns `{check, stale: [(label, key, prior_po_ruling_ref?), …], fresh: […]}`
    where `label` is the single node id (single-node check) or the sorted pair
    string (pair check). The orchestration judges only the `stale` set, then
    stores the new verdicts — turning a whole-spec re-validate into O(Δ)."""
    stale: List[Tuple] = []
    fresh: List[Tuple] = []
    for ids in node_id_sets:
        res = check(root, check_name, ids, graph, model_id, no_cache=no_cache)
        if check_name in PAIR_CHECKS:
            a, b = sorted(ids)
            label = f"{a}+{b}"
        else:
            label = ids[0]
        if res["stale"]:
            stale.append((label, res.get("key"), res.get("prior_po_ruling_ref")))
        else:
            fresh.append((label, res.get("key"), res.get("po_ruling_ref")))
    return {"check": check_name, "stale": stale, "fresh": fresh}


# ----------------------------------------------------------------------------
# Garbage-collect entries for deleted node ids
# ----------------------------------------------------------------------------

def _key_node_ids(key: str) -> List[str]:
    """The node ids a key references (one for single-node, two for a `+`-joined
    pair scope). Read from the scope_key segment so GC needs no per-check knowledge."""
    parts = key.split("|")
    if len(parts) < 2:
        return []
    scope = parts[1]
    return scope.split("+") if "+" in scope else [scope]


def gc_deleted(root, graph: Dict[str, Any], no_cache: bool = False) -> int:
    """Evict every entry referencing a node id no longer in the graph.

    Set-difference vs the current graph node ids: any single-node entry for a
    deleted id, and any pair entry naming a deleted id, is dropped — no dead
    entries linger and a reused id can never collide with a stale verdict.
    Returns the number of entries removed. No-op under `no_cache` or when the
    cache file is absent."""
    if no_cache:
        return 0
    cache = load_cache(root)
    if cache is None:
        return 0
    live = {n["id"] for n in graph.get("nodes", [])}
    survivors: Dict[str, Any] = {}
    removed = 0
    for k, e in cache["entries"].items():
        ids = _key_node_ids(k)
        if all(i in live for i in ids):
            survivors[k] = e
        else:
            removed += 1
    if removed:
        cache["entries"] = survivors
        _write_cache(root, cache)
    return removed


# ----------------------------------------------------------------------------
# last_validated marker (written on --validate ONLY)
# ----------------------------------------------------------------------------

def write_last_validated(root, snapshot_path) -> Path:
    """Write `docs/product/.memory/last_validated.json` recording the validated
    snapshot's filename + content hash, through the soft fence.

    This marker is the `--validate` signal the `--status` command reads ("last
    validated against snapshot X at time T"). It is written ON `--validate` ONLY — a bare
    `--viz --snapshot` writes the snapshot but never this marker, so the snapshot
    timeline and the validate timeline stay distinct."""
    snap = Path(snapshot_path)
    # Fence the referenced snapshot path (it must live under docs/product/).
    assert_under_docs_product(snap, root)
    try:
        body = snap.read_bytes()
        snap_hash = hashlib.sha256(body).hexdigest()[:8]
    except (FileNotFoundError, OSError):
        snap_hash = "missing"

    payload = {
        "snapshot": snap.name,
        "snapshot_hash": snap_hash,
        "validated_at": _now(),
    }
    path = _last_validated_path(root)
    assert_under_docs_product(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return path


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def _parse_ids(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    return [s for s in (p.strip() for p in raw.split(",")) if s]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="emit fresh/stale for a check")
    mode.add_argument("--store", action="store_true", help="store a verdict under --key")
    mode.add_argument("--gc", action="store_true", help="evict deleted-node entries")
    ap.add_argument("--check-name", help="the LLM check id (with --check)")
    ap.add_argument("--node-ids", help="comma-separated node id(s) (with --check)")
    ap.add_argument("--key", help="cache key (with --store)")
    ap.add_argument("--verdict", help="verdict JSON (with --store)")
    ap.add_argument("--po-ruling-ref", default=None, help="DEC-n reference (with --store)")
    ap.add_argument("--model-id", help="CALLER-SUPPLIED model id (required for --check/--store)")
    ap.add_argument("--no-cache", action="store_true", help="bypass the cache entirely")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph = build_graph(root)

    try:
        if args.gc:
            removed = gc_deleted(root, graph, no_cache=args.no_cache)
            print(json.dumps({"removed": removed}, ensure_ascii=False))
            return 0

        if not args.model_id:
            print(json.dumps(
                {"error": "invalid_input", "message": "--model-id is required (caller-supplied)"},
                ensure_ascii=False))
            return 0

        if args.check:
            ids = _parse_ids(args.node_ids)
            res = check(root, args.check_name, ids, graph, args.model_id,
                        no_cache=args.no_cache)
            print(json.dumps(res, indent=2, ensure_ascii=False))
            return 0

        # --store
        verdict = json.loads(args.verdict) if args.verdict else None
        path = store(root, args.key, verdict, args.model_id,
                     po_ruling_ref=args.po_ruling_ref, no_cache=args.no_cache)
        print(json.dumps(
            {"stored": path is not None,
             "path": str(path.relative_to(root)) if path else None},
            ensure_ascii=False))
        return 0
    except (ValueError, Exception) as exc:  # noqa: BLE001 — surface as a finding
        # Analytical-script contract: a bad input surfaces as a JSON finding on
        # stdout + exit 0, never a bare traceback.
        print(json.dumps(
            {"error": "invalid_input", "message": str(exc)}, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    sys.exit(main())
