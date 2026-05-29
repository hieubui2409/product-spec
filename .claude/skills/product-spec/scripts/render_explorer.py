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

import datetime as dt
from pathlib import Path
from typing import Any, Dict, List, Optional

from i18n_labels import label
import render_html
from spec_graph import index_artifacts
from render_ascii import _BOARD_CARD_TYPES, _filter_by_layers, _is_deferred

SKILL_ROOT = Path(__file__).resolve().parent.parent
EXPLORER_SHELL = SKILL_ROOT / "assets" / "templates" / "explorer-shell.html"

# Sort rank only; the EMITTED per-item depth is recomputed from the reconciled
# parent chain (see build_payload) so it stays correct after a --layers filter.
_DEPTH_BY_TYPE = {"goal": 0, "prd": 1, "epic": 2, "story": 3}
_LAYER_ORDER = ("goal", "prd", "epic", "story")
_UI_KEYS = ("search", "status", "moscow", "persona", "layer", "all", "unassigned",
            "no_results", "tree", "tabs", "table", "ac_count",
            "goal", "prd", "epic", "story")


def _maps(artifacts: List[Dict[str, Any]]):
    bodies: Dict[str, str] = {}
    ac_counts: Dict[str, int] = {}
    for aid, a in index_artifacts(artifacts).items():
        bodies[aid] = a.get("body") or ""
        ac = (a.get("frontmatter") or {}).get("acceptance_criteria")
        if isinstance(ac, list):
            ac_counts[aid] = len(ac)
    return bodies, ac_counts


def build_payload(graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
                  lang: str = "en", filter_wont: bool = False,
                  layers: Optional[List[str]] = None) -> Dict[str, Any]:
    bodies, ac_counts = _maps(artifacts)
    parent_of: Dict[str, str] = {}
    for e in graph["edges"]:
        parent_of.setdefault(str(e["from"]), str(e["to"]))  # first parent wins (tree edge)

    nodes = [n for n in graph["nodes"] if n.get("type") in _BOARD_CARD_TYPES]
    nodes = _filter_by_layers(nodes, layers)
    if filter_wont:
        nodes = [n for n in nodes if not _is_deferred(n)]
    present_ids = {str(n["id"]) for n in nodes}

    items: List[Dict[str, Any]] = []
    for n in sorted(nodes, key=lambda x: (_DEPTH_BY_TYPE.get(x.get("type"), 9), str(x["id"]))):
        nid = str(n["id"])
        par = parent_of.get(nid, "")
        items.append({
            "id": nid,
            "type": n.get("type"),
            "title": n.get("title") or "",
            "status": n.get("status") or "",
            "moscow": n.get("moscow") or "",
            "horizon": n.get("horizon") or "",
            "owner": n.get("owner") or "",
            "personas": n.get("personas") if isinstance(n.get("personas"), list) else [],
            # Layer facet/tab key = artifact type (matches CLI help + the type
            # badge); the Flat-tabs key comes from _LAYER_ORDER which is also type
            # names, so a goal card now lands under the 'goal' tab (was empty when
            # this carried the export bucket 'brd').
            "layer": n.get("type"),
            "ac_count": ac_counts.get(nid, 0),
            "parent": par if par in present_ids else "",  # roots (goals) have no in-set parent
            "body": bodies.get(nid, ""),
        })

    # Recompute depth from the RECONCILED parent chain (over present_ids) rather
    # than the static per-type depth: after a --layers filter prunes intermediate
    # ancestors, a story whose epic is gone becomes a root (parent=""), so Tree
    # renders it at the root and Table-tree must indent it 0 too — otherwise the
    # two modes disagree (Tree root vs Table indented under nothing).
    parent_by_id = {it["id"]: it["parent"] for it in items}

    def _depth(nid: str) -> int:
        d = 0
        seen: set = set()
        p = parent_by_id.get(nid, "")
        while p and p not in seen:
            seen.add(p)
            d += 1
            p = parent_by_id.get(p, "")
        return d

    for it in items:
        it["depth"] = _depth(it["id"])

    return {
        "items": items,
        "layer_order": [l for l in _LAYER_ORDER if any(i["type"] == l for i in items)],
        "labels": {k: label(k, lang) for k in _UI_KEYS},
    }


def assemble_explorer(graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
                      lang: str, filter_wont: bool, layers: Optional[List[str]]) -> str:
    payload = build_payload(graph, artifacts, lang, filter_wont, layers)
    shell = EXPLORER_SHELL.read_text(encoding="utf-8")
    title = f"Explorer — {render_html.product_name(graph)}"
    return render_html.assemble_body_shell(shell, payload, graph, lang, title)


def write(root: Path, graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
          lang: str = "en", filter_wont: bool = False,
          layers: Optional[List[str]] = None) -> Path:
    out_dir = root / "docs" / "product" / "visuals"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = out_dir / f"explorer-{ts}.html"
    target.write_text(assemble_explorer(graph, artifacts, lang, filter_wont, layers), encoding="utf-8")
    return target
