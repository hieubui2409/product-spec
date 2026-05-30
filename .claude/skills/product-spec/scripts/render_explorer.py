#!/usr/bin/env python3
"""
render_explorer — F2 `--viz explorer` html writer. One self-contained page with
an in-page mode toggle across three layouts that share search + facet filters:

  • Tree       — collapsible <details> nav + click → sanitized body (default mode)
  • Flat-tabs  — one tab per layer type + pane
  • Table-tree — treegrid: depth-indented rows, metadata columns, expand → body

Security mirrors render_board: the server emits an inert JSON island; the client
builds metadata via safe DOM APIs and bodies via the sanitize chokepoint. No
Mermaid (a --format mermaid request falls back to the ascii tree).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from i18n_labels import label
import render_html
from spec_graph import index_artifacts, parents_of, resolve_ac
from render_ascii import select_cards

SKILL_ROOT = Path(__file__).resolve().parent.parent
EXPLORER_SHELL = SKILL_ROOT / "assets" / "templates" / "explorer-shell.html"

# The layer hierarchy order, single source. _DEPTH_BY_TYPE (initial sort rank) is
# derived from it so reordering the hierarchy edits one place; the EMITTED per-item
# depth is recomputed from the reconciled multi-parent chain (see build_payload).
_LAYER_ORDER = ("goal", "prd", "epic", "story")
_DEPTH_BY_TYPE = {t: i for i, t in enumerate(_LAYER_ORDER)}
_UI_KEYS = ("search", "status", "moscow", "persona", "layer", "horizon", "unassigned",
            "no_results", "tree", "tabs", "table", "ac_count",
            "goal", "prd", "epic", "story")


def _maps(artifacts: List[Dict[str, Any]]):
    bodies: Dict[str, str] = {}
    ac_counts: Dict[str, int] = {}
    for aid, a in index_artifacts(artifacts).items():
        bodies[aid] = a.get("body") or ""
        fm = a.get("frontmatter") or {}
        # Use resolve_ac so blank/None entries are excluded — matches the validator
        # (check_consistency) which also calls resolve_ac; counting raw list length
        # over-reported when the PO leaves empty AC placeholder items.
        ac_counts[aid] = len(resolve_ac(fm))
    return bodies, ac_counts


def build_payload(graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
                  lang: str = "en", filter_wont: bool = False,
                  layers: Optional[List[str]] = None,
                  selected_nodes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    bodies, ac_counts = _maps(artifacts)
    # ALL parents per child (shared rule, self-edges already dropped → no cyclic
    # self-parent reaches the client). A multi-goal PRD keeps both goals so the
    # Tree renders it under EACH (matching the ASCII tree), not just the first.
    all_parents = parents_of(graph)

    # Accept pre-selected nodes from the dispatcher (avoids a second select_cards
    # call when _dispatch_body_view already ran it for the empty-check guard).
    nodes = selected_nodes if selected_nodes is not None else select_cards(graph, layers, filter_wont)
    present_ids = {str(n["id"]) for n in nodes}

    def _scalar(v: Any) -> str:
        """Coerce a frontmatter scalar to str: lists/dicts (malformed YAML) become
        "" so a non-string value never lands as array card data in the JSON island."""
        return v if isinstance(v, str) else ""

    items: List[Dict[str, Any]] = []
    for n in sorted(nodes, key=lambda x: (_DEPTH_BY_TYPE.get(x.get("type"), 9), str(x["id"]))):
        nid = str(n["id"])
        # Keep every in-set parent; an empty list = a root (parent pruned, or a goal
        # whose only "parent" is the non-node BRD/PRODUCT container).
        parents = [p for p in all_parents.get(nid, []) if p in present_ids]
        items.append({
            "id": nid,
            "type": n.get("type"),
            "title": n.get("title") or "",
            "status": _scalar(n.get("status")),
            "moscow": _scalar(n.get("moscow")),
            "horizon": _scalar(n.get("horizon")),
            "owner": n.get("owner") or "",
            "personas": n.get("personas") if isinstance(n.get("personas"), list) else [],
            # Layer facet/tab key = artifact type (matches CLI help + the type
            # badge); the Flat-tabs key comes from _LAYER_ORDER which is also type
            # names, so a goal card now lands under the 'goal' tab (was empty when
            # this carried the export bucket 'brd').
            "layer": n.get("type"),
            "ac_count": ac_counts.get(nid, 0),
            "parents": parents,  # multi-parent; roots have []
            "body": bodies.get(nid, ""),
        })

    # Recompute depth from the RECONCILED multi-parent chain (over present_ids):
    # depth = shortest distance to a root, so after a --layers filter prunes an
    # intermediate ancestor the Tree (renders under each surviving parent) and the
    # Table-tree (indents by this depth) agree. Cycle-guarded via the path `stack`.
    parents_by_id = {it["id"]: it["parents"] for it in items}
    _depth_cache: Dict[str, int] = {}

    def _depth(nid: str, stack: frozenset) -> int:
        # Memoize ONLY at the top level (empty stack): a value computed under a
        # non-empty cycle-guard stack is conditioned on that path, so caching it
        # would make the depth of a malformed cyclic node order-dependent. On the
        # acyclic ID-grammar DAG the top-level memo is exact and order-independent.
        if not stack and nid in _depth_cache:
            return _depth_cache[nid]
        ps = [p for p in parents_by_id.get(nid, []) if p in parents_by_id and p not in stack]
        d = 0 if not ps else 1 + min(_depth(p, stack | {nid}) for p in ps)
        if not stack:
            _depth_cache[nid] = d
        return d

    for it in items:
        it["depth"] = _depth(it["id"], frozenset())

    return {
        "items": items,
        "layer_order": [l for l in _LAYER_ORDER if any(i["type"] == l for i in items)],
        "labels": {k: label(k, lang) for k in _UI_KEYS},
    }


def assemble_explorer(graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
                      lang: str, filter_wont: bool, layers: Optional[List[str]],
                      selected_nodes: Optional[List[Dict[str, Any]]] = None) -> str:
    payload = build_payload(graph, artifacts, lang, filter_wont, layers,
                            selected_nodes=selected_nodes)
    shell = EXPLORER_SHELL.read_text(encoding="utf-8")
    title = f"{label('explorer', lang)} — {render_html.product_name(graph)}"
    return render_html.assemble_body_shell(shell, payload, graph, lang, title)


def write(root: Path, graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
          lang: str = "en", filter_wont: bool = False,
          layers: Optional[List[str]] = None,
          selected_nodes: Optional[List[Dict[str, Any]]] = None) -> Path:
    return render_html._write_visual(
        root, f"explorer-{render_html.file_timestamp()}.html",
        assemble_explorer(graph, artifacts, lang, filter_wont, layers,
                          selected_nodes=selected_nodes))
