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
from typing import Any, Dict, List

from i18n_labels import label


def _is_deferred(node: Dict[str, Any]) -> bool:
    """A node is 'deferred' if either MoSCoW says won't OR scope says out."""
    return node.get("moscow") == "wont" or node.get("scope") == "out"


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
        n = nodes_by_id.get(nid)
        if n is None:
            return True  # missing nodes flagged by dangling_link; keep rendered
        return not (filter_wont and _is_deferred(n))

    children = defaultdict(list)
    for e in graph["edges"]:
        children[e["to"]].append(e["from"])

    lines: List[str] = []
    name = (graph.get("product") or {}).get("name") or "(no PRODUCT.md)"
    lines.append(f"{label('product', lang)}: {name}")

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

    Counts inbound edges by EXPECTED CHILD TYPE so it matches
    check_traceability.unaddressed_parent semantics exactly. Earlier this
    counted any inbound edge, which diverged on malformed graphs where a
    parent had wrong-type inbound edges (e.g., a goal with a stray story
    pointing at it). Single source of truth = the check_traceability rule.
    """
    expected = {"goal": "prd", "prd": "epic", "epic": "story"}
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    matching_children = defaultdict(int)
    for e in graph["edges"]:
        src = nodes_by_id.get(e["from"], {}).get("type")
        target_node = nodes_by_id.get(e["to"], {})
        target_type = target_node.get("type")
        if target_type in expected and expected[target_type] == src:
            matching_children[e["to"]] += 1

    out: List[str] = []
    for n in graph["nodes"]:
        kind = n["type"]
        if kind in expected and matching_children[n["id"]] == 0:
            out.append(f"  - {n['id']} ({kind}) has no {expected[kind].upper()} addressing it")
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


def delta(current: Dict[str, Any], baseline: Dict[str, Any]) -> str:
    """Unified-diff-style: added / removed / changed nodes between two graphs.

    Also surfaces PRODUCT-level changes (`name`, `core_value`, `personas` list)
    so a PRODUCT.md edit (which lives in graph.product meta, not in nodes[])
    shows up in the delta view instead of silently rendering "(no changes)".
    """
    cur_ids = {n["id"]: n for n in current.get("nodes", [])}
    base_ids = {n["id"]: n for n in baseline.get("nodes", [])}
    added = sorted(set(cur_ids) - set(base_ids))
    removed = sorted(set(base_ids) - set(cur_ids))
    changed: List[str] = []
    for nid in sorted(set(cur_ids) & set(base_ids)):
        for field in ("status", "scope", "moscow", "horizon", "size"):
            if cur_ids[nid].get(field) != base_ids[nid].get(field):
                changed.append(f"  ~ {nid}.{field}: {base_ids[nid].get(field)} -> {cur_ids[nid].get(field)}")

    # Product-level diff (name / core_value / personas list).
    cur_p = current.get("product") or {}
    base_p = baseline.get("product") or {}
    for field in ("name", "core_value"):
        if cur_p.get(field) != base_p.get(field):
            changed.append(f"  ~ PRODUCT.{field}: {base_p.get(field)!r} -> {cur_p.get(field)!r}")
    if sorted(cur_p.get("personas") or []) != sorted(base_p.get("personas") or []):
        changed.append(f"  ~ PRODUCT.personas: {base_p.get('personas')} -> {cur_p.get('personas')}")

    lines: List[str] = []
    for a in added:
        lines.append(f"  + {a}")
    for r in removed:
        lines.append(f"  - {r}")
    lines.extend(changed)
    return "\n".join(lines) or "(no changes)"
