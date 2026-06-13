"""
render_ascii_board — board and explorer ASCII renderers for visualize.py.

Extracted from render_ascii to keep the module focused. Provides the kanban
board view, the orphan-forest explorer view, and the shared card-selection
and column-ordering helpers used by both the ASCII renderers and the HTML
board/explorer payload builders.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from i18n_labels import label
from render_common import _hashable, _is_deferred, _inline, _mark
from spec_graph import children_of, parents_of, HORIZON_ORDER


# Imported from render_ascii to avoid duplicating constants.
# render_ascii imports this module at top-level so we import from spec_graph
# directly (no circular dep: render_ascii_board → spec_graph only).
_BOARD_GROUP_ORDER = {
    "status": ["draft", "review", "approved"],
    "horizon": list(HORIZON_ORDER),
    "moscow": ["must", "should", "could", "wont"],
}
_BOARD_CARD_TYPES = ("goal", "prd", "epic", "story")
_LOCALIZED_COLS = {"now", "next", "later", "must", "should", "could", "wont", "unassigned"}


# _hashable / _is_deferred / _inline / _mark imported from render_common (see import block above).


def _ascii_product_name(graph: Dict[str, Any]) -> str:
    """The PRODUCT header name for the ASCII forest, or `(no PRODUCT.md)`."""
    product = graph.get("product")
    product = product if isinstance(product, dict) else {}
    return _inline(product.get("name") or "(no PRODUCT.md)")


def _filter_by_layers(nodes: List[Dict[str, Any]], layers: Optional[List[str]]) -> List[Dict[str, Any]]:
    """Keep only nodes whose ARTIFACT TYPE is selected. `layers` None or empty →
    keep all. Shared by the ASCII board and the html board/explorer so `--layers`
    filters cards identically across the viewers (single source of truth).

    The viewers filter by artifact type (`goal,prd,epic,story`) — matching the CLI
    help and the cards' own type badge — NOT by the export doc-layer bucket where
    goal→brd."""
    if not layers:
        return list(nodes)
    want = set(layers)
    return [n for n in nodes if n.get("type") in want]


def _board_columns(present_keys: Dict[str, bool], group_by: str) -> List[str]:
    """Canonical column list for a board/kanban view: known-order columns first,
    then extra sorted columns, then 'unassigned' last. Single home used by both
    the ASCII board renderer and the HTML board payload builder so the two surfaces
    can never diverge on column ordering."""
    order = _BOARD_GROUP_ORDER.get(group_by, [])
    cols = list(order)
    cols += sorted(k for k in present_keys if k not in order and k != "unassigned")
    if present_keys.get("unassigned"):
        cols.append("unassigned")
    return cols


def select_cards(graph: Dict[str, Any], layers: Optional[List[str]] = None,
                 filter_wont: bool = False) -> List[Dict[str, Any]]:
    """The shared card/node selection for board + explorer (ASCII and HTML): keep
    the board card types → apply the `--layers` artifact-type filter → optionally
    drop deferred items. One entry point so a future selection rule changes once."""
    nodes = [n for n in graph["nodes"] if n.get("type") in _BOARD_CARD_TYPES]
    nodes = _filter_by_layers(nodes, layers)
    if filter_wont:
        nodes = [n for n in nodes if not _is_deferred(n)]
    return nodes


def board(graph: Dict[str, Any], group_by: str = "status", lang: str = "en",
          filter_wont: bool = False, layers: Optional[List[str]] = None) -> str:
    """Kanban-style grouped lists: columns = the chosen group field, cards =
    goal/PRD/epic/story artifacts. Deterministic (canonical column order, sorted
    IDs). `--layers` filters cards; `filter_wont` drops deferred items."""
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    cards = select_cards(graph, layers, filter_wont)

    groups: Dict[str, List[str]] = defaultdict(list)
    for n in cards:
        v = n.get(group_by)
        key = _hashable(v) if v not in (None, "") else "unassigned"
        groups[key].append(n["id"])

    present_keys = {k: True for k in groups}
    cols = _board_columns(present_keys, group_by)

    lines = [f"## {label('board', lang).upper()} — {group_by}"]
    for c in cols:
        items = sorted(groups.get(c, []))
        header = label(c, lang) if c in _LOCALIZED_COLS else c
        lines.append(f"### {header} ({len(items)})")
        if items:
            for it in items:
                lines.append(f"  - {_mark(nodes_by_id.get(it, {}), it)}")
        else:
            lines.append("  (empty)")
    return "\n".join(lines)


def _orphan_forest(graph: Dict[str, Any], lang: str = "en") -> str:
    """Indented forest for the explorer ASCII fallback when a `--layers` or
    `--filter-wont` filter prunes intermediate ancestors.

    Roots = every visible node with NO parent present in the (filtered) node set,
    so pruning the goal layer (or a deferred intermediate) reparents the surviving
    prd/epic/story as roots. Root determination tests ANY parent (via
    spec_graph.parents_of), so a multi-goal PRD whose first goal is pruned but
    a later goal survives still attaches to the surviving goal.
    """
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    present = set(nodes_by_id)

    children = children_of(graph)
    parents = parents_of(graph)

    lines: List[str] = []
    lines.append(f"{label('product', lang)}: {_ascii_product_name(graph)}")

    # `seen` guards against a malformed cyclic edge (A→B→A).
    def _render(nid: str, prefix: str, last: bool, is_root: bool, seen: set) -> None:
        if nid in seen:
            return
        seen = seen | {nid}
        n = nodes_by_id.get(nid, {})
        title = _inline(n.get("title") or "")
        text = f"{nid} — {title}" if (is_root and title) else nid
        lines.append(f"{prefix}{'└── ' if last else '├── '}{_mark(n, text)}")
        kid_prefix = prefix + ("    " if last else "│   ")
        kids = sorted(k for k in children.get(nid, []) if k in present and k not in seen)
        for i, k in enumerate(kids):
            _render(k, kid_prefix, i == len(kids) - 1, False, seen)

    roots = sorted(nid for nid in nodes_by_id
                   if not any(p in present for p in parents.get(nid, [])))
    if not roots and nodes_by_id:
        # Pure cycle: treat the lowest-id node as a synthetic root.
        roots = [sorted(nodes_by_id.keys())[0]]
        lines.append(f"  (cycle detected among: {', '.join(sorted(nodes_by_id.keys()))})")
    for i, r in enumerate(roots):
        _render(r, "", i == len(roots) - 1, True, set())
    return "\n".join(lines)


def explorer(graph: Dict[str, Any], lang: str = "en",
             filter_wont: bool = False, layers: Optional[List[str]] = None) -> str:
    """ASCII fallback for `--viz explorer` (the interactive modes are html-only).

    With neither `--layers` nor `--filter-wont`, delegates to the goal-rooted
    `tree()` (canonical shape). When EITHER filter is active, renders an
    orphan-rooted forest over the SAME node set the HTML explorer uses so a kept
    child of a pruned/deferred parent is reparented as a root.
    """
    # Avoid circular import: render_ascii.tree is imported lazily here since
    # render_ascii imports this module at its top level.
    if not layers and not filter_wont:
        import render_ascii as _ra
        return _ra.tree(graph, lang=lang, filter_wont=filter_wont)
    keep_nodes = select_cards(graph, layers, filter_wont)
    keep_ids = {n["id"] for n in keep_nodes}
    filtered = {
        **graph,
        "nodes": keep_nodes,
        "edges": [e for e in graph["edges"] if e["from"] in keep_ids and e["to"] in keep_ids],
    }
    return _orphan_forest(filtered, lang=lang)
