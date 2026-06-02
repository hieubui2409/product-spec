"""
judgment_cache_keys — deterministic cache-key composition for judgment_cache.

Owns the key grammar, body-hash helpers, and the graph content fingerprint.
All functions are pure and deterministic — no I/O, no timestamps.

Key grammar:  ``check | scope_key | hashes | lang | dep_hash``
  - single-node check: scope_key = node_id, hashes = body_hash
  - pair check (semantic_duplication): scope_key = sorted two-id join,
    hashes = body_hashes in the same sorted order
  - core_value_drift additionally stamps dep_hash = ``cv:<hash(core_value)>``
    so a change to the PRODUCT core-value sentence invalidates every drift
    verdict even when the artifact body is byte-identical.
  - contradiction is NEVER cached — compute_key refuses it.
"""

import hashlib
from typing import Any, Dict, List, Optional

# The one check that is NEVER cached: contradiction must re-run on every validate.
NEVER_CACHED = frozenset({"contradiction"})

# Pair checks key on the SORTED two-id tuple (unordered pair).
PAIR_CHECKS = frozenset({"semantic_duplication"})

# Checks whose verdict depends on the PRODUCT core-value sentence.
CORE_VALUE_DEP_CHECKS = frozenset({"core_value_drift"})

# Bump this when the KEY GRAMMAR or the cache SEMANTICS change in a way that
# makes old entries unsafe to reuse. A mismatch with the on-disk stamp is a
# full miss (every entry re-judged) — the safe direction.
CACHE_VERSION = "1"


def node_index(graph: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {n["id"]: n for n in graph.get("nodes", [])}


def body_hash(node: Optional[Dict[str, Any]]) -> str:
    """The node's body fingerprint, or a stable sentinel when the node is absent
    or has no body (a goal). A missing node yields a key that can never collide
    with a real one and will always miss — the safe direction."""
    if not node:
        return "missing"
    bh = node.get("body_hash")
    return bh if isinstance(bh, str) else "none"


def lang_segment(nodes: List[Optional[Dict[str, Any]]], graph: Dict[str, Any]) -> str:
    """The judgment language for the key. A verdict's wording is lang-sensitive,
    so a lang flip must miss. Use the first present node's `lang`, else the
    PRODUCT lang, else `en` — deterministic and single-valued per key."""
    for n in nodes:
        if n and isinstance(n.get("lang"), str):
            return n["lang"]
    prod = graph.get("product") or {}
    return prod.get("lang") if isinstance(prod.get("lang"), str) else "en"


def core_value_dep(check: str, graph: Dict[str, Any]) -> str:
    """The dep_hash segment. For a core-value-dependent check it is
    `cv:<hash(core_value)>` so a core-value edit invalidates the entry;
    otherwise empty (the body_hash already covers the dependency)."""
    if check not in CORE_VALUE_DEP_CHECKS:
        return ""
    prod = graph.get("product") or {}
    cv = prod.get("core_value")
    cv_text = cv if isinstance(cv, str) else ""
    return "cv:" + hashlib.sha256(cv_text.encode("utf-8")).hexdigest()[:8]


def compute_key(check: str, node_ids: List[str], graph: Dict[str, Any]) -> str:
    """Compose the deterministic cache key for `check` over `node_ids`.

    Single-node: `check|node_id|body_hash|lang|dep_hash`.
    Pair check : `check|idA+idB|body_hashA+body_hashB|lang|dep_hash`, with the
                 two ids SORTED so the pair is unordered.
    Refuses `contradiction` (never cached).
    """
    if check in NEVER_CACHED:
        raise ValueError(f"{check!r} is never cached (no key)")

    idx = node_index(graph)
    if check in PAIR_CHECKS:
        if len(node_ids) != 2:
            raise ValueError(f"{check!r} is a pair check; got {len(node_ids)} ids")
        a, b = sorted(node_ids)
        scope_key = f"{a}+{b}"
        hashes = f"{body_hash(idx.get(a))}+{body_hash(idx.get(b))}"
        nodes = [idx.get(a), idx.get(b)]
    else:
        if len(node_ids) != 1:
            raise ValueError(f"{check!r} is a single-node check; got {len(node_ids)} ids")
        nid = node_ids[0]
        scope_key = nid
        hashes = body_hash(idx.get(nid))
        nodes = [idx.get(nid)]

    lang = lang_segment(nodes, graph)
    dep = core_value_dep(check, graph)
    return f"{check}|{scope_key}|{hashes}|{lang}|{dep}"


def graph_content_hash(graph: Dict[str, Any]) -> str:
    """A deterministic 8-hex content fingerprint of the graph's judged surface.

    Computed over the sorted `id\\x1fbody_hash` pairs of every node — stable
    for identical content (no embedded timestamp). The memory-gap detector
    recomputes this on the live graph and compares it to the `last_judged.json`
    marker to spot drift since the last judged batch.
    """
    pairs = sorted(
        f"{n.get('id', '')}\x1f{body_hash(n)}" for n in graph.get("nodes", [])
    )
    return hashlib.sha256("\n".join(pairs).encode("utf-8")).hexdigest()[:8]


def key_base(key: str) -> str:
    """The `check|scope_key` prefix of a key (identity of the node(s)+check,
    independent of the content hash / lang / dep)."""
    parts = key.split("|")
    return "|".join(parts[:2]) if len(parts) >= 2 else key


def key_node_ids(key: str) -> List[str]:
    """The node ids a key references (one for single-node, two for a `+`-joined
    pair scope). Read from the scope_key segment so GC needs no per-check knowledge."""
    parts = key.split("|")
    if len(parts) < 2:
        return []
    scope = parts[1]
    return scope.split("+") if "+" in scope else [scope]
