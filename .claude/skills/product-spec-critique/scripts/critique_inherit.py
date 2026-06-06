#!/usr/bin/env python3
"""critique_inherit.py — the two cross-critique directions as deterministic bundle
keys, consumed by the CONSOLIDATOR only (lenses stay blind — anti-anchoring).

  * inherited_context (parent→child): a parent's prior blockers / DEC-worthy findings
    surfaced as the child's inherited risk. Source = the findings-INDEX, classified
    by GRAPH RELATION against the current scope.
  * descendant_rollup (child→parent): aggregate a parent's already-critiqued children
    ("3/5 critiqued children carry blockers → delivery risk at this parent").

Classification uses `spec_graph.ancestors()`/`downstream()` — the ancestor SET, NOT
the single `prd`/`epic` frontmatter fields (wrong for multi-parent reach). One pass
over the index, deterministic, no wall-clock. The keys sit at the top of the bundle
the lenses receive but the lens prompt is told to ignore them (consolidator-only).
"""

import hashlib
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import critique_cache


def _psp_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "product-spec" / "scripts"


def _import_spec_graph():
    sd = str(_psp_dir())
    if sd not in sys.path:
        sys.path.insert(0, sd)
    import spec_graph
    return spec_graph


# The index is the LOSSY blockers + DEC-worthy cache; inherited surfaces only those.
_INHERIT_SEVERITIES = frozenset({"blocker"})


def _node_of(evidence_id: str) -> str:
    """The node id an evidence-ID points at: strip a trailing `:line` citation
    (`PRD-AUTH:12` → `PRD-AUTH`). IDs themselves carry no colon, so split-once is safe."""
    return str(evidence_id).split(":", 1)[0]


# ---------------------------------------------------------------------------
# finding-level fingerprint (spec-span anchor) — stable per-finding identity
#
# A finding's identity is anchored to the TEXT of the spec line it cites, NOT to
# the LLM's `why` prose (paraphrase-unstable) nor the line NUMBER (drifts when the
# spec reflows). Inserting a paragraph above moves `:5`→`:7` but the line's text is
# unchanged → same fingerprint → recognized as the same finding. Editing the cited
# text → new fingerprint, which is correct (the criticised content changed).
# ---------------------------------------------------------------------------

_MARKER_RE = re.compile(r'^(?:#{1,6}|>+|[-*+])\s+')  # leading md heading/quote/bullet marker


def _normalize_line(text: str) -> str:
    """Light deterministic normalize: drop ONE leading markup marker (heading `#`,
    blockquote `>`, bullet `-*+` — each only when whitespace-followed, so it never
    eats content like `5xx`, `+10%`, `-5`), collapse internal whitespace, trim,
    lowercase. A structural-only line (no alphanumeric — `---`, `***`, `___`, bare
    `>`) collapses to '' → 'no usable anchor'. Leading list NUMBERS are deliberately
    kept as content so two siblings (`3. X` vs `7. X`) do NOT collide."""
    s = (text or "").strip()
    if not re.search(r'[^\W_]', s):  # no alphanumeric → structural-only → no anchor
        return ""
    return re.sub(r'\s+', ' ', _MARKER_RE.sub('', s)).strip().lower()


def _fingerprint(node: str, severity, line_text) -> Optional[str]:
    """Pure fingerprint: sha256(node + severity + normalized text)[:16], or None when
    the normalized text is empty. Hashing '' would COLLIDE distinct findings on the
    same node+severity (the bug this feature removes) → None instead, so the caller
    falls back to the evidence_id key."""
    norm = _normalize_line(line_text)
    if not norm:
        return None
    digest = hashlib.sha256(f"{node}\0{severity or ''}\0{norm}".encode("utf-8"))
    return digest.hexdigest()[:16]


def _resolve_line_text(root, graph, evidence_id) -> Optional[str]:
    """The RAW text of the spec line an evidence-ID (`<node>:<line>`) cites, or None
    when unresolvable (missing `:line`, non-int line, unknown node, node without a
    `file`, unreadable file, or out-of-range line). Caller degrades to eid keying."""
    if not evidence_id or ":" not in str(evidence_id):
        return None
    node, _, line_s = str(evidence_id).partition(":")
    try:
        line = int(line_s)
    except ValueError:
        return None
    n = {x["id"]: x for x in graph.get("nodes", [])}.get(node)
    if not n or not n.get("file"):
        return None
    try:
        lines = (Path(root) / "docs" / "product" / n["file"]).read_text(
            encoding="utf-8").splitlines()
    except OSError:
        return None
    return lines[line - 1] if 1 <= line <= len(lines) else None


def _finding_fingerprint(root, graph, evidence_id, severity) -> Optional[str]:
    """Fingerprint for a finding's cited spec span, or None ⇒ caller keys by
    evidence_id. None covers: unresolvable citation, an empty/structural line, and
    BRD-goal nodes (whose `file` is brd.md + content lives in frontmatter, so a cited
    structural line normalizes empty) — all safe degrades, no false merge."""
    text = _resolve_line_text(root, graph, evidence_id)
    if text is None:
        return None
    return _fingerprint(_node_of(evidence_id), severity, text)


def _live_ids(graph: Dict[str, Any]) -> Set[str]:
    return {n["id"] for n in graph.get("nodes", [])}


def _classify(evidence_id: str, scope: str, ancestors_set: Set[str],
              descendants_set: Set[str]) -> str:
    """Bucket an evidence-ID vs the current scope X:
      node == X or descendant of X → 'repeat' (existing repeat-offense plumbing)
      node is an ancestor of X      → 'inherited'
      unrelated                     → 'drop'."""
    node = _node_of(evidence_id)
    if node == scope or node in descendants_set:
        return "repeat"
    if node in ancestors_set:
        return "inherited"
    return "drop"


def _index_rows(root) -> List[Dict[str, Any]]:
    """Index entries deduped per FINDING, keeping the most-recent report_ts.

    Dedup key = `finding_fingerprint or evidence_id`: same logical finding across
    re-critiques (same fingerprint, drifted line) collapses to one row; a None/legacy
    fingerprint falls back to the evidence_id key (today's behaviour) — distinct
    None-fingerprint findings keep their distinct eids and do NOT merge."""
    best: Dict[str, Dict[str, Any]] = {}
    for entry in critique_cache.load_index(root).values():
        eid = entry.get("evidence_id")
        if not eid:
            continue
        key = entry.get("finding_fingerprint") or eid
        cur = best.get(key)
        if cur is None or str(entry.get("report_ts") or "") >= str(cur.get("report_ts") or ""):
            best[key] = entry
    return list(best.values())


def _inherited_candidates(root, graph, scope, fresh_only) -> List[Dict[str, Any]]:
    sg = _import_spec_graph()
    anc = sg.ancestors(graph, scope)
    desc = sg.downstream(graph, scope)
    live = _live_ids(graph)
    out: List[Dict[str, Any]] = []
    for entry in _index_rows(root):
        eid = entry["evidence_id"]
        if _classify(eid, scope, anc, desc) != "inherited":
            continue
        node = _node_of(eid)
        if fresh_only and node not in live:  # stale parent (deleted node) → drop
            continue
        sev = entry.get("severity")
        if sev not in _INHERIT_SEVERITIES and not entry.get("dec_worthy"):
            continue  # blockers + DEC-worthy only
        out.append({
            "node": node,
            "scope": entry.get("scope"),
            "source": f"{node}@{entry.get('report_ts')}",
            "evidence_id": eid,
            "severity": sev,
            "why": entry.get("why"),
            "fix": entry.get("fix"),
            "dec_worthy": bool(entry.get("dec_worthy")),
        })
    return out


def _public(c: Dict[str, Any]) -> Dict[str, Any]:
    """The bundle-facing shape (drop the internal `node`/`scope` bookkeeping)."""
    return {k: c[k] for k in ("source", "evidence_id", "severity", "why", "fix",
                              "dec_worthy")}


def build_inherited_context(root, graph, scope: str, depth: str = "nearest",
                            fresh_only: bool = True) -> List[Dict[str, Any]]:
    """Parent→child inherited findings (blockers + DEC-worthy, full text, fresh-only).

    depth='nearest' (default): nearest critiqued ancestor per branch + every
    scope=='all' finding. depth='deep': every critiqued ancestor. Empty when the index
    has nothing relevant (ON costs nothing without context)."""
    cands = _inherited_candidates(root, graph, scope, fresh_only)
    if depth == "deep" or not cands:
        return [_public(c) for c in cands]
    sg = _import_spec_graph()
    cand_nodes = {c["node"] for c in cands}
    kept: List[Dict[str, Any]] = []
    for c in cands:
        if c.get("scope") == "all":
            kept.append(c)
            continue
        node = c["node"]
        # Nearest per branch: drop this node if a NEARER critiqued ancestor exists —
        # i.e. some other candidate b has THIS node among its own ancestors.
        nearer = any(b != node and node in sg.ancestors(graph, b) for b in cand_nodes)
        if not nearer:
            kept.append(c)
    return [_public(c) for c in kept]


def build_descendant_rollup(root, graph, scope: str,
                            fresh_only: bool = True) -> Dict[str, Any]:
    """Child→parent rollup: bounded child counts + blocker children, fresh-only.
    No-op (empty dict) when the parent has no critiqued children. Direction is UP.

    The "was critiqued" set comes from `critique-state.json` (written per real run
    REGARDLESS of blockers), NOT the lossy blockers-only index — so a CLEAN-critiqued
    child still counts toward the denominator (else verdict_line is always N/N).
    Blocker counts come from the index."""
    sg = _import_spec_graph()
    children = sorted(set(sg.children_of(graph).get(scope, [])))
    if not children:
        return {}
    live = _live_ids(graph)
    child_set = set(children)
    # Critiqued children = those with a per-scope critique-state record (clean or not).
    state = critique_cache.load_state(root)
    critiqued: Set[str] = {c for c in children
                           if c in state and (not fresh_only or c in live)}
    blocker_counts: Dict[str, int] = {}
    for entry in _index_rows(root):
        node = _node_of(entry["evidence_id"])
        if node not in child_set:
            continue
        if fresh_only and node not in live:
            continue
        critiqued.add(node)  # a blocker child is critiqued even if state is absent
        if entry.get("severity") == "blocker" or entry.get("dec_worthy"):
            blocker_counts[node] = blocker_counts.get(node, 0) + 1
    if not critiqued:
        return {}
    blocker_children = [{"id": n, "blocker_count": blocker_counts[n]}
                        for n in sorted(blocker_counts)]
    verdict = (f"{len(blocker_children)}/{len(critiqued)} critiqued children "
               f"carry blockers")
    return {
        "critiqued_child_count": len(critiqued),
        "total_child_count": len(children),
        "blocker_children": blocker_children,
        "verdict_line": verdict,
    }


def index_report_findings(root, report_ts: str, scope: str,
                          findings: List[Dict[str, Any]]) -> Any:
    """Write-time wrapper over `critique_cache.upsert_findings`: feed this run's
    blockers + DEC-worthy to the findings-index for the next critique's inherit /
    repeat-offense. LOSSY by design — only blockers + DEC-worthy are indexed."""
    rows: List[Dict[str, Any]] = []
    graph = None  # built lazily on the first indexable finding (critique is read-only,
    #               so the spec is byte-stable across this single run → safe to resolve)
    for f in findings:
        # Lens-agent findings carry the citation under `evidence` (`<id>:<line>`);
        # the index's internal key is `evidence_id`. Accept either so a raw lens
        # array indexes correctly, not just a pre-renamed one.
        eid = f.get("evidence_id") or f.get("evidence")
        if not eid:
            continue
        if f.get("severity") != "blocker" and not f.get("dec_worthy"):
            continue
        if graph is None:
            graph = _import_spec_graph().build_graph(Path(root))
        rows.append({
            "evidence_id": eid,
            "severity": f.get("severity"),
            "why": f.get("why") or f.get("why_it_dies"),
            "fix": f.get("fix"),
            "dec_worthy": bool(f.get("dec_worthy")),
            "finding_fingerprint": _finding_fingerprint(root, graph, eid, f.get("severity")),
        })
    return critique_cache.upsert_findings(root, report_ts, scope, rows)
