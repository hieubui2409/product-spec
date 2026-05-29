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
from assemble_digest import LAYER_FOR_TYPE
from render_ascii import _BOARD_CARD_TYPES, _filter_by_layers, _is_deferred

SKILL_ROOT = Path(__file__).resolve().parent.parent
EXPLORER_SHELL = SKILL_ROOT / "assets" / "templates" / "explorer-shell.html"

_DEPTH_BY_TYPE = {"goal": 0, "prd": 1, "epic": 2, "story": 3}
_LAYER_ORDER = ("goal", "prd", "epic", "story")
_UI_KEYS = ("search", "status", "moscow", "persona", "layer", "all", "unassigned",
            "no_results", "tree", "tabs", "table", "ac_count")


def _maps(artifacts: List[Dict[str, Any]]):
    bodies: Dict[str, str] = {}
    ac_counts: Dict[str, int] = {}
    for a in artifacts:
        if not a.get("ok"):
            continue
        fm = a.get("frontmatter") or {}
        aid = fm.get("id")
        if not aid:
            continue
        bodies[str(aid)] = a.get("body") or ""
        ac = fm.get("acceptance_criteria")
        if isinstance(ac, list):
            ac_counts[str(aid)] = len(ac)
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
            "layer": LAYER_FOR_TYPE.get(n.get("type")) or n.get("type"),
            "ac_count": ac_counts.get(nid, 0),
            "depth": _DEPTH_BY_TYPE.get(n.get("type"), 0),
            "parent": par if par in present_ids else "",  # roots (goals) have no in-set parent
            "body": bodies.get(nid, ""),
        })

    return {
        "items": items,
        "layer_order": [l for l in _LAYER_ORDER if any(i["type"] == l for i in items)],
        "labels": {k: label(k, lang) for k in _UI_KEYS},
    }


def assemble_explorer(graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
                      lang: str, filter_wont: bool, layers: Optional[List[str]]) -> str:
    payload = build_payload(graph, artifacts, lang, filter_wont, layers)
    shell = EXPLORER_SHELL.read_text(encoding="utf-8")
    product_name = (graph.get("product") or {}).get("name") or "(unnamed)"
    generated_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z"
    values = render_html.body_render_values(payload)
    values.update({
        "lang_attr": lang,
        "title": render_html._escape(f"Explorer — {product_name}"),
        "product_name": render_html._escape(product_name),
        "generated_at": generated_at,
    })
    return render_html.substitute(shell, values)


def write(root: Path, graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
          lang: str = "en", filter_wont: bool = False,
          layers: Optional[List[str]] = None) -> Path:
    out_dir = root / "docs" / "product" / "visuals"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = out_dir / f"explorer-{ts}.html"
    target.write_text(assemble_explorer(graph, artifacts, lang, filter_wont, layers), encoding="utf-8")
    return target
