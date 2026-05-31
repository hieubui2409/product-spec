#!/usr/bin/env python3
"""
render_board — F2 `--viz board` html writer. A self-contained kanban: columns =
the chosen group field (status|horizon|moscow), cards = goal/PRD/epic/story
artifacts, click a card → its sanitized body in a panel, plus client-side search
and facet filters.

Security (red-team H3): the server emits ONLY an inert JSON data island; the
client builds every card via safe DOM APIs (textContent / dataset) for metadata
and the sanitize chokepoint (psRenderMarkdown) for bodies, so neither body nor
attribute payloads can inject. No Mermaid here (board carries none by design).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from i18n_labels import label
import render_html
from spec_graph import index_artifacts
from render_ascii import _board_columns, _hashable, _scalar, select_cards

SKILL_ROOT = Path(__file__).resolve().parent.parent
BOARD_SHELL = SKILL_ROOT / "assets" / "templates" / "board-shell.html"

_UI_KEYS = ("search", "status", "moscow", "persona", "layer", "horizon", "unassigned",
            "no_results", "now", "next", "later", "must", "should", "could", "wont",
            "goal", "prd", "epic", "story")


def build_payload(graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
                  group_by: str = "status", lang: str = "en",
                  filter_wont: bool = False, layers: Optional[List[str]] = None,
                  selected_nodes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    bodies = {aid: (a.get("body") or "") for aid, a in index_artifacts(artifacts).items()}
    # Accept pre-selected nodes from the dispatcher (avoids a second select_cards
    # call when _dispatch_body_view already ran it for the empty-check guard).
    cards_nodes = selected_nodes if selected_nodes is not None else select_cards(graph, layers, filter_wont)

    cards: List[Dict[str, Any]] = []
    present: Dict[str, bool] = {}
    for n in sorted(cards_nodes, key=lambda x: str(x["id"])):
        gval = n.get(group_by)
        # Coerce via _hashable (not bare str) so a malformed list/dict enum value
        # yields the SAME column key the ASCII board uses — the two surfaces must
        # not diverge on the same input.
        col = _hashable(gval) if gval not in (None, "") else "unassigned"
        present[col] = True
        cards.append({
            "id": str(n["id"]),
            "type": n.get("type"),
            "title": n.get("title") or "",
            "status": _scalar(n.get("status")),
            "moscow": _scalar(n.get("moscow")),
            "horizon": _scalar(n.get("horizon")),
            "personas": n.get("personas") if isinstance(n.get("personas"), list) else [],
            # Viewer Layer facet = the artifact type (goal/prd/epic/story), so the
            # facet chip + `--layers` agree with the CLI help (not the export bucket
            # where goal→brd, which would render a stray 'brd' chip and no 'goal').
            "layer": n.get("type"),
            "column": col,
            # Goals carry no file body (they expand from brd.md.goals); synthesize
            # one from their structured fields so the detail panel is not empty.
            "body": bodies.get(str(n["id"])) or render_html.goal_detail_md(n, lang),
        })

    # Single source for column ordering: render_ascii._board_columns owns the
    # known-order-first / extra-sorted / unassigned-last logic; importing it
    # replaces the previously duplicated inline block.
    columns = _board_columns(present, group_by)

    return {
        "group_by": group_by,
        "columns": columns,
        "col_labels": {c: label(c, lang) for c in columns},
        "cards": cards,
        "labels": {k: label(k, lang) for k in _UI_KEYS},
    }


def assemble_board(graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
                   group_by: str, lang: str, filter_wont: bool,
                   layers: Optional[List[str]],
                   selected_nodes: Optional[List[Dict[str, Any]]] = None) -> str:
    payload = build_payload(graph, artifacts, group_by, lang, filter_wont, layers,
                            selected_nodes=selected_nodes)
    shell = BOARD_SHELL.read_text(encoding="utf-8")
    title = f"{label('board', lang)} — {render_html.product_name(graph)}"
    return render_html.assemble_body_shell(shell, payload, graph, lang, title)


def write(root: Path, graph: Dict[str, Any], artifacts: List[Dict[str, Any]],
          group_by: str = "status", lang: str = "en", filter_wont: bool = False,
          layers: Optional[List[str]] = None,
          selected_nodes: Optional[List[Dict[str, Any]]] = None) -> Path:
    return render_html._write_visual(
        root, f"board-{render_html.file_timestamp()}.html",
        assemble_board(graph, artifacts, group_by, lang, filter_wont, layers,
                       selected_nodes=selected_nodes))
