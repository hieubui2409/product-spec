#!/usr/bin/env python3
"""
render_ascii — deterministic ASCII renderers for the 9 visualization views.

All functions take the graph JSON (per visualization-spec.md) and return a
plain-text string. Zero dependencies; safe in any terminal.

Deferred items (moscow=wont or scope=out) get a trailing `*` marker so the
PO can see at a glance which nodes are out-of-scope-but-still-tracked. The
`filter_wont` kwarg lets the caller hide them entirely (per the brainstorm
§15 amendment: default show-with-marker, opt-in filter).
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from i18n_labels import label
from spec_graph import (
    CHILD_TYPE_FOR_PARENT,
    matching_child_counts,
    parents_of,
    children_of,
    diff_graphs,
)


def _is_deferred(node: Dict[str, Any]) -> bool:
    """A node is 'deferred' if either MoSCoW says won't OR scope says out."""
    return node.get("moscow") == "wont" or node.get("scope") == "out"


def is_visible(node: Optional[Dict[str, Any]], filter_wont: bool) -> bool:
    """Whether a (possibly missing) node survives --filter-wont. One home for the
    deferred-visibility rule the tree renderers share (a missing node — flagged by
    dangling_link — is kept rendered)."""
    return node is None or not (filter_wont and _is_deferred(node))


def _ascii_product_name(graph: Dict[str, Any]) -> str:
    """The PRODUCT header name for the ASCII tree/forest, or `(no PRODUCT.md)`.
    One home for the ASCII fallback string (render_html.product_name uses a
    different `(unnamed)` fallback for the HTML chrome — intentionally distinct)."""
    return (graph.get("product") or {}).get("name") or "(no PRODUCT.md)"


def _mark(node: Dict[str, Any], text: str) -> str:
    """Suffix the rendered text with a `*` when the node is deferred."""
    return f"{text} *" if _is_deferred(node) else text


def tree(graph: Dict[str, Any], lang: str = "en", filter_wont: bool = False) -> str:
    """Vision -> PRODUCT -> BRD -> goals -> PRDs -> epics -> stories.

    The only localizable token in the tree is the `PRODUCT:` prefix. IDs and
    goal titles are frontmatter-driven (the artifact's own `lang:` field
    governs prose), and the separator dash is locale-neutral.

    `filter_wont=True` drops nodes marked `moscow: wont` or `scope: out` from
    the rendered tree entirely. Default keeps them and suffixes a `*` marker
    so the PO can see what's deferred without losing visibility.
    """
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}

    def _visible(nid: str) -> bool:
        return is_visible(nodes_by_id.get(nid), filter_wont)

    children = children_of(graph)

    lines: List[str] = []
    lines.append(f"{label('product', lang)}: {_ascii_product_name(graph)}")

    goal_ids = sorted([nid for nid, n in nodes_by_id.items() if n["type"] == "goal" and _visible(nid)])
    for i, gid in enumerate(goal_ids):
        last_g = i == len(goal_ids) - 1
        gnode = nodes_by_id[gid]
        glabel = _mark(gnode, f"{gid} — {gnode.get('title') or ''}")
        lines.append(f"{'└── ' if last_g else '├── '}{glabel}")
        prefix_g = "    " if last_g else "│   "
        prds = sorted(pid for pid in children.get(gid, []) if _visible(pid))
        for j, pid in enumerate(prds):
            last_p = j == len(prds) - 1
            plabel = _mark(nodes_by_id.get(pid, {}), pid)
            lines.append(f"{prefix_g}{'└── ' if last_p else '├── '}{plabel}")
            prefix_p = prefix_g + ("    " if last_p else "│   ")
            epics = sorted(eid for eid in children.get(pid, []) if _visible(eid))
            for k, eid in enumerate(epics):
                last_e = k == len(epics) - 1
                elabel = _mark(nodes_by_id.get(eid, {}), eid)
                lines.append(f"{prefix_p}{'└── ' if last_e else '├── '}{elabel}")
                prefix_e = prefix_p + ("    " if last_e else "│   ")
                stories = sorted(sid for sid in children.get(eid, []) if _visible(sid))
                for m, sid in enumerate(stories):
                    last_s = m == len(stories) - 1
                    slabel = _mark(nodes_by_id.get(sid, {}), sid)
                    lines.append(f"{prefix_e}{'└── ' if last_s else '├── '}{slabel}")
    return "\n".join(lines)


def _hashable(v: Any) -> str:
    """Coerce frontmatter values that should be enum scalars to a string.

    A PO who writes `status: [draft]` (list) or some other unhashable shape
    would otherwise crash dict indexing. Render the unexpected shape verbatim
    so the validator can flag `unknown_enum` separately, but never blow up
    the viz renderer.
    """
    if v is None:
        return "?"
    if isinstance(v, (list, dict, set)):
        return f"?{v!r}"
    return str(v)


def _grid(corner: str, cols: List[str], rows: List[List[str]]) -> str:
    """Render an aligned ASCII table whose column widths derive from the widest
    value in each column (header or any row), so an overlong row label can never
    outgrow the separator line.

    `corner` is the top-left header cell; `cols` are the data-column headers.
    Each row is `[row_label, cell_0, cell_1, ...]` with one pre-stringified cell
    per `cols` entry. The label column is left-aligned; data cells are
    right-aligned (counts read better flush-right).
    """
    label_w = max([len(corner)] + [len(r[0]) for r in rows])
    col_w = [
        max([len(c)] + [len(r[i + 1]) for r in rows])
        for i, c in enumerate(cols)
    ]

    def _row(lbl: str, cells: List[str], right: bool) -> str:
        body = " | ".join(
            f"{v:>{w}}" if right else f"{v:<{w}}"
            for v, w in zip(cells, col_w)
        )
        return f"| {lbl:<{label_w}} | {body} |"

    header = _row(corner, list(cols), right=False)
    sep = "|" + "-" * (len(header) - 2) + "|"
    lines = [header, sep]
    for r in rows:
        lines.append(_row(r[0], r[1:], right=True))
    return "\n".join(lines)


def heatmap(graph: Dict[str, Any]) -> str:
    """status grid: rows=type, cols=canonical status (+ 'other').

    Non-canonical statuses — anything outside draft/review/approved, already
    flagged as an enum error by check_consistency — are summed into an 'other'
    column so a node in a bad state is never silently dropped from the grid.
    The 'other' column appears only when at least one such node exists.
    """
    canon = ["draft", "review", "approved"]
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    other: Dict[str, int] = defaultdict(int)
    for n in graph["nodes"]:
        t = _hashable(n.get("type"))
        s = _hashable(n.get("status"))
        if s in canon:
            counts[t][s] += 1
        else:
            other[t] += 1
    types = sorted(set(counts) | set(other))
    cols = list(canon) + (["other"] if any(other.values()) else [])
    rows = [
        [t]
        + [str(counts[t].get(s, 0)) for s in canon]
        + ([str(other.get(t, 0))] if "other" in cols else [])
        for t in types
    ]
    return _grid("Type", cols, rows)


def scope(graph: Dict[str, Any]) -> str:
    """scope tag x MoSCoW grid."""
    cells: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for n in graph["nodes"]:
        sc = _hashable(n.get("scope"))
        ms = _hashable(n.get("moscow"))
        cells[sc][ms] += 1
    rows_order = ["in", "core-value", "out"]
    cols = ["must", "should", "could", "wont"]
    rows = [[r] + [str(cells[r].get(c, 0)) for c in cols] for r in rows_order]
    return _grid("Scope", cols, rows)


def roadmap(graph: Dict[str, Any], lang: str = "en", filter_wont: bool = False) -> str:
    """now / next / later groupings. Section headers localize via i18n_labels.

    Default keeps deferred items with a `*` marker; `filter_wont=True` drops them.
    """
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    groups: Dict[str, List[str]] = defaultdict(list)
    for n in graph["nodes"]:
        if n["type"] not in ("prd", "epic", "story"):
            continue
        if filter_wont and _is_deferred(n):
            continue
        h = n.get("horizon") or "unspecified"
        groups[h].append(n["id"])

    sections = []
    for h in ("now", "next", "later", "unspecified"):
        items = sorted(groups.get(h, []))
        if not items and h == "unspecified":
            continue
        header = label(h, lang).upper() if h != "unspecified" else "UNSPECIFIED"
        sections.append(f"## {header}")
        if not items:
            sections.append("  (empty)")
        else:
            for it in items:
                sections.append(f"  - {_mark(nodes_by_id.get(it, {}), it)}")
    return "\n".join(sections) or "(no PRDs/epics/stories yet)"


def _dep_safe_order(graph: Dict[str, Any]) -> List[str]:
    """PRD+Epic ids in a deterministic, CYCLE-SAFE order over `depends_on`.

    Iterative post-order with a visited-set guard — the SAME guard as
    spec_graph._closure (`if x in seen: continue`) — so a circular chain
    (A→B→A) terminates instead of hanging the renderer (trade-off T1 / G-D3).
    A cycle simply degrades to sorted order for its nodes. Kept local to
    render_ascii (not imported from render_mermaid) so the ASCII path stays
    zero-dependency and the module graph stays acyclic (render_mermaid imports
    render_ascii, never the reverse)."""
    dep_adj: Dict[str, List[str]] = {}
    for n in graph["nodes"]:
        if n.get("type") in ("prd", "epic"):
            dep_adj[n["id"]] = sorted(n.get("depends_on") or [])
    ordered: List[str] = []
    seen: set = set()
    for root in sorted(dep_adj):
        stack = [(root, False)]
        while stack:
            node, processed = stack.pop()
            if processed:
                if node not in ordered:
                    ordered.append(node)
                continue
            if node in seen:
                continue
            seen.add(node)
            stack.append((node, True))
            for dep in dep_adj.get(node, []):
                if dep in dep_adj and dep not in seen:
                    stack.append((dep, False))
    return ordered


def time(graph: Dict[str, Any], lang: str = "en", filter_wont: bool = False) -> str:
    """TIME dimension as a zero-dep text summary (the ASCII default for the
    `time` view). PRD+Epic grouped by horizon (now/next/later); each line carries
    the `target_date` (or `(no date)`) and any `depends_on` prerequisites.

    Rows are emitted in a CYCLE-SAFE dep order (prerequisites before dependents
    where acyclic; a circular chain degrades to sorted order, never hangs —
    trade-off T1 / G-D3). Deferred items keep the `*` marker unless
    `filter_wont` drops them (parity with roadmap)."""
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    order_index = {nid: i for i, nid in enumerate(_dep_safe_order(graph))}

    timed = [
        n for n in graph["nodes"]
        if n.get("type") in ("prd", "epic")
        and not (filter_wont and _is_deferred(n))
    ]
    timed.sort(key=lambda n: (order_index.get(n["id"], len(order_index)), n["id"]))

    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for n in timed:
        groups[n.get("horizon") or "unspecified"].append(n)

    sections: List[str] = []
    for h in ("now", "next", "later", "unspecified"):
        items = groups.get(h, [])
        if not items and h == "unspecified":
            continue
        header = label(h, lang).upper() if h != "unspecified" else "UNSPECIFIED"
        sections.append(f"## {header}")
        if not items:
            sections.append("  (empty)")
            continue
        for n in items:
            td = n.get("target_date")
            date_txt = str(td) if td else f"({label('no_date', lang)})"
            line = f"  - {_mark(n, n['id'])}  [{date_txt}]"
            deps = sorted(n.get("depends_on") or [])
            if deps:
                line += f"  depends_on: {', '.join(deps)}"
            sections.append(line)
    return "\n".join(sections) or "(no PRDs/epics with a horizon yet)"


def persona(graph: Dict[str, Any], filter_wont: bool = False) -> str:
    """persona x feature(PRD/epic) coverage (story count).

    `personas` field on a node must be a YAML list; if a regression leaks a
    bare string (e.g. "TBD" from a missing token), iterating it would emit
    per-character personas. Guard with isinstance(list).
    """
    raw_personas = (graph.get("product") or {}).get("personas")
    personas = sorted(set(raw_personas)) if isinstance(raw_personas, list) else []
    if not personas:
        for n in graph["nodes"]:
            n_personas = n.get("personas")
            if not isinstance(n_personas, list):
                continue
            for p in n_personas:
                if p not in personas:
                    personas.append(p)
        personas = sorted(set(personas))

    visible_prd_ids = [
        n["id"] for n in graph["nodes"]
        if n["type"] == "prd" and not (filter_wont and _is_deferred(n))
    ]
    prds = sorted(visible_prd_ids)
    cells: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    epic_to_prd = {n["id"]: n.get("prd") for n in graph["nodes"] if n["type"] == "epic"}
    for n in graph["nodes"]:
        if n["type"] != "story":
            continue
        if filter_wont and _is_deferred(n):
            continue
        prd_id = epic_to_prd.get(n.get("epic"))
        n_personas = n.get("personas")
        if not isinstance(n_personas, list):
            continue
        for p in n_personas:
            if prd_id:
                cells[p][prd_id] += 1
    if not personas:
        return "(no personas yet)"
    rows = [[p] + [str(cells[p].get(prd, 0)) for prd in prds] for p in personas]
    return _grid("Persona", prds, rows)


def gap(graph: Dict[str, Any]) -> str:
    """Bullet list of unaddressed nodes (gap-analysis input — structural only).

    Counts inbound edges by EXPECTED CHILD TYPE via the shared
    spec_graph.matching_child_counts, so the gap view and
    check_traceability.unaddressed_parent can never disagree (single home for
    the rule; on a malformed graph a wrong-type inbound edge does not mask a gap).
    """
    counts = matching_child_counts(graph)
    out: List[str] = []
    for n in graph["nodes"]:
        kind = n["type"]
        if kind in CHILD_TYPE_FOR_PARENT and counts.get(n["id"], 0) == 0:
            out.append(f"  - {n['id']} ({kind}) has no {CHILD_TYPE_FOR_PARENT[kind].upper()} addressing it")
    return "\n".join(out) or "(no structural gaps)"


def moscow(graph: Dict[str, Any], lang: str = "en") -> str:
    """MoSCoW quadrant counts among stories. Labels localize via i18n_labels."""
    counts: Dict[str, int] = defaultdict(int)
    for n in graph["nodes"]:
        if n["type"] != "story":
            continue
        counts[_hashable(n.get("moscow"))] += 1
    # Width 10 accommodates the longest VI label ("Không làm" = 9 chars).
    rows = [
        f"| {label('must', lang):10}: {counts.get('must', 0):>3} | {label('should', lang):10}: {counts.get('should', 0):>3} |",
        f"| {label('could', lang):10}: {counts.get('could', 0):>3} | {label('wont', lang):10}: {counts.get('wont', 0):>3} |",
    ]
    return "\n".join(rows)


def risk(graph: Dict[str, Any]) -> str:
    """3x3 risk matrix: impact x likelihood."""
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in graph.get("risks", []):
        counts[r.get("impact", "?")][r.get("likelihood", "?")] += 1
    rows_order = ["high", "med", "low"]
    cols = ["low", "med", "high"]
    rows = [[r] + [str(counts[r].get(c, 0)) for c in cols] for r in rows_order]
    return _grid("Impact \\ Lik", cols, rows)


def competition(graph: Dict[str, Any]) -> str:
    """Text parity matrix + threat list for the COMPETITION dimension.

    The competition view is HTML-native by design (parity matrix + threat
    heatmap; G-E2). This ASCII form is the terminal/CI fallback the dispatcher
    reaches for `--format ascii|mermaid` (mirroring risk's ASCII fallback): rows
    = competitor names, cols = PRD ids, cells = the parity enum (blank when
    unset); a trailing threat column shows each competitor's threat tier.
    Resolves the BRD's competitor identity against each PRD's parity map."""
    competitors = [c for c in (graph.get("competitors") or []) if isinstance(c, dict)]
    prds = sorted(
        (n for n in graph.get("nodes", []) if n.get("type") == "prd"),
        key=lambda n: str(n.get("id") or ""),
    )
    if not competitors:
        return "No competitors recorded in the BRD yet."
    cols = [str(p.get("id") or "") for p in prds] + ["threat"]
    rows = []
    for c in competitors:
        name = str(c.get("name") or c.get("id") or "(unnamed)")
        cells = []
        for p in prds:
            parity = p.get("competitive_parity")
            val = parity.get(c.get("id")) if isinstance(parity, dict) else None
            cells.append(str(val) if val is not None else "-")
        cells.append(str(c.get("threat") or "-"))
        rows.append([name] + cells)
    return _grid("Competitor \\ PRD", cols, rows)


def _filter_by_layers(nodes: List[Dict[str, Any]], layers: Optional[List[str]]) -> List[Dict[str, Any]]:
    """Keep only nodes whose ARTIFACT TYPE is selected. `layers` None or empty →
    keep all. Shared by the ASCII board and the html board/explorer so `--layers`
    filters cards identically across the viewers (single source of truth).

    The viewers filter by artifact type (`goal,prd,epic,story`) — matching the CLI
    help and the cards' own type badge — NOT by the export doc-layer bucket where
    goal→brd. (That bucket vocab is the EXPORT surface only; conflating the two is
    what made `--layers goal` drop every goal card and the explorer 'goal' tab
    empty.)"""
    if not layers:
        return list(nodes)
    want = set(layers)
    return [n for n in nodes if n.get("type") in want]


_BOARD_GROUP_ORDER = {
    "status": ["draft", "review", "approved"],
    "horizon": ["now", "next", "later"],
    "moscow": ["must", "should", "could", "wont"],
}
_BOARD_CARD_TYPES = ("goal", "prd", "epic", "story")
_LOCALIZED_COLS = {"now", "next", "later", "must", "should", "could", "wont", "unassigned"}


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

    order = _BOARD_GROUP_ORDER.get(group_by, [])
    cols = list(order)
    cols += sorted(k for k in groups if k not in order and k != "unassigned")
    if "unassigned" in groups:
        cols.append("unassigned")

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
    prd/epic/story as roots — matching the HTML explorer, which reparents the same
    way (`parent=''` for out-of-set parents). Root determination tests ANY parent
    (via spec_graph.parents_of), so a multi-goal PRD whose first goal is pruned but
    a later goal survives still attaches to the surviving goal instead of floating
    up as a root. (The ASCII board is flat — no hierarchy, no reparenting — so it is
    NOT a parallel here.) For the full, unfiltered graph the roots are exactly the
    goals, so this reproduces `tree()`'s shape."""
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    present = set(nodes_by_id)

    # No visibility filter here: the sole caller (explorer) builds `graph` via
    # select_cards, which already dropped deferred nodes when filter_wont — every
    # present node is renderable. `_mark` still flags any kept deferred node (the
    # layers-only path keeps them with a `*`).
    children = children_of(graph)
    # All parents per child (shared rule); a node is a root when none of its
    # parents survive in the filtered set.
    parents = parents_of(graph)

    lines: List[str] = []
    lines.append(f"{label('product', lang)}: {_ascii_product_name(graph)}")

    # `seen` guards against a malformed cyclic edge (A→B→A) — without it the
    # edge-driven recursion would loop forever (tree() is safe only because its
    # nesting is fixed by type; this forest descends by arbitrary edges).
    def _render(nid: str, prefix: str, last: bool, is_root: bool, seen: set) -> None:
        if nid in seen:
            return
        seen = seen | {nid}
        n = nodes_by_id.get(nid, {})
        title = n.get("title") or ""
        text = f"{nid} — {title}" if (is_root and title) else nid
        lines.append(f"{prefix}{'└── ' if last else '├── '}{_mark(n, text)}")
        kid_prefix = prefix + ("    " if last else "│   ")
        kids = sorted(k for k in children.get(nid, []) if k in present and k not in seen)
        for i, k in enumerate(kids):
            _render(k, kid_prefix, i == len(kids) - 1, False, seen)

    roots = sorted(nid for nid in nodes_by_id
                   if not any(p in present for p in parents.get(nid, [])))
    for i, r in enumerate(roots):
        _render(r, "", i == len(roots) - 1, True, set())
    return "\n".join(lines)


def explorer(graph: Dict[str, Any], lang: str = "en",
             filter_wont: bool = False, layers: Optional[List[str]] = None) -> str:
    """ASCII fallback for `--viz explorer` (the interactive modes are html-only).

    With neither `--layers` nor `--filter-wont`, delegate to the goal-rooted
    `tree()` (canonical shape; preserves `explorer == tree`). When EITHER filter is
    active, render an orphan-rooted forest over the SAME node set the HTML explorer
    uses (select_cards: board card types → --layers → drop deferred when
    filter_wont), so a kept child of a pruned/deferred parent is reparented as a
    root exactly as the HTML explorer does — instead of being silently dropped (the
    fixed-depth `tree()` descent skips a deferred intermediate's whole subtree)."""
    if not layers and not filter_wont:
        return tree(graph, lang=lang, filter_wont=filter_wont)
    keep_nodes = select_cards(graph, layers, filter_wont)
    keep_ids = {n["id"] for n in keep_nodes}
    filtered = {
        **graph,
        "nodes": keep_nodes,
        "edges": [e for e in graph["edges"] if e["from"] in keep_ids and e["to"] in keep_ids],
    }
    # select_cards already dropped deferred nodes when filter_wont; the layers-only
    # path keeps them and _orphan_forest's _mark flags them with a `*`.
    return _orphan_forest(filtered, lang=lang)


def delta(current: Dict[str, Any], baseline: Dict[str, Any]) -> str:
    """Unified-diff-style: added / removed / changed nodes between two graphs.

    Also surfaces PRODUCT-level changes (`name`, `core_value`, `personas` list)
    so a PRODUCT.md edit (which lives in graph.product meta, not in nodes[])
    shows up in the delta view instead of silently rendering "(no changes)".
    """
    d = diff_graphs(current, baseline)  # shared added/removed + product-change set-math
    cur_ids = {n["id"]: n for n in current.get("nodes", [])}
    base_ids = {n["id"]: n for n in baseline.get("nodes", [])}
    changed: List[str] = []
    for nid in sorted(set(cur_ids) & set(base_ids)):
        for field in ("status", "scope", "moscow", "horizon", "size"):
            if cur_ids[nid].get(field) != base_ids[nid].get(field):
                changed.append(f"  ~ {nid}.{field}: {base_ids[nid].get(field)} -> {cur_ids[nid].get(field)}")

    # Product-level diff: format the fields diff_graphs flagged as changed.
    cur_p = current.get("product") or {}
    base_p = baseline.get("product") or {}
    for field in d["product_changes"]:
        if field == "personas":
            changed.append(f"  ~ PRODUCT.personas: {base_p.get('personas')} -> {cur_p.get('personas')}")
        else:
            changed.append(f"  ~ PRODUCT.{field}: {base_p.get(field)!r} -> {cur_p.get(field)!r}")

    lines: List[str] = []
    for a in d["added"]:
        lines.append(f"  + {a}")
    for r in d["removed"]:
        lines.append(f"  - {r}")
    lines.extend(changed)
    return "\n".join(lines) or "(no changes)"
