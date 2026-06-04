#!/usr/bin/env python3
"""
render_mermaid — emit Mermaid v11 blocks for the 11 graph visualization views.

Each function returns a string containing a fenced ```mermaid block ready
to paste into markdown. Where a view cannot be expressed cleanly in Mermaid,
the renderer falls back to a `pre`-block with the ASCII version.
"""

import re
from collections import defaultdict
from typing import Any, Dict, List

from i18n_labels import label
from spec_graph import (
    CHILD_TYPE_FOR_PARENT,
    HORIZON_ORDER,
    moscow_story_counts,
    matching_child_counts,
    diff_graphs,
)
from render_ascii import (
    heatmap as ascii_heatmap,
    persona as ascii_persona,
    risk as ascii_risk,
    competition as ascii_competition,
    _dep_safe_order,
    _is_deferred,
    _scalar,
    is_visible,
)


def _fence(body: str) -> str:
    return f"```mermaid\n{body}\n```"


def _safe_label(s: str) -> str:
    """Sanitize a string for safe embedding inside a Mermaid label.

    Mermaid label syntax `node["..."]` chokes on double-quotes, newlines, and
    bracket/paren characters that mimic Mermaid's own grammar. Replace them
    with visually-similar but non-syntactic equivalents.

    Angle brackets are replaced with single-guillemets so that a label value
    like `<script>alert(1)</script>` cannot reach the browser as a live tag
    in the self-contained HTML output: the HTML parser tokenises raw `<...>`
    sequences before Mermaid's `securityLevel: strict` ever runs.

    `&` is replaced first so that entity-encoded payloads (e.g. `&#60;img`)
    cannot bypass the angle-bracket substitution that follows.
    """
    # & first — prevents entity-encoded payloads from surviving the subsequent
    # angle-bracket substitution (e.g. &#60;img src=x onerror=...&#62;).
    out = (s or "").replace("&", "&amp;")
    out = out.replace('"', "'").replace("\n", " ")
    for ch, repl in (
        ("[", "("), ("]", ")"),
        ("{", "("), ("}", ")"),
        ("`", "'"),
        ("<", "‹"), (">", "›"),
    ):
        out = out.replace(ch, repl)
    return out


def _safe_label_lines(*parts: str) -> str:
    """Build a multi-line Mermaid node label.

    Each part is sanitised independently via `_safe_label`, then joined with a
    skill-emitted `<br/>`. The `<br/>` must NOT pass through `_safe_label` (which
    neutralises angle brackets to guillemets for PO-controlled text) — it is a
    constant separator, never user data, so it reaches Mermaid intact.

    Mermaid 11 splits a flowchart label on `<br/>` into stacked lines even under
    `securityLevel: strict` (htmlLabels off). A literal ``\\n`` is NOT interpreted
    there — it renders as the two characters back-slash-n, which is the visible
    artefact this replaces. Empty parts are dropped so a missing title leaves no
    trailing blank line."""
    return "<br/>".join(_safe_label(p) for p in parts if p)


def tree(graph: Dict[str, Any], lang: str = "en", filter_wont: bool = False) -> str:
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    # `flowchart BT` (bottom-top) keeps edge semantics child -> parent while
    # rendering PRODUCT at the visual top — matching the ASCII tree output.
    # Using TB inverted the visual hierarchy: stories at top, PRODUCT at the
    # bottom. Same data, two formats, opposite orientations is hostile UX.
    lines = ["flowchart BT", "  classDef deferred stroke-dasharray: 4 2,opacity:0.6"]
    product_label = label("product", lang)
    product_name = (graph.get("product") or {}).get("name") or product_label
    name = _safe_label(f"{product_label}: {product_name}" if product_name != product_label else product_label)
    lines.append(f'  PRODUCT["{name}"]')

    def _visible(nid: str) -> bool:
        return is_visible(nodes_by_id.get(nid), filter_wont)

    for n in graph["nodes"]:
        # PRODUCT is emitted explicitly above; vision is a narrative doc with
        # no structural role in the tree (no inbound/outbound edges) — skipping
        # both prevents a duplicate PRODUCT box and a stranded empty VISION box.
        if n.get("type") in ("product", "vision"):
            continue
        if not _visible(n["id"]):
            continue
        node_label = _safe_label_lines(n["id"], n.get("title") or "")
        sid = _safe_id(n["id"])
        # Deferred nodes get the `deferred` classDef so the PO can see at a
        # glance which nodes are out-of-scope-but-still-tracked (default show
        # with marker, --filter-wont opt-in hide).
        if _is_deferred(n):
            lines.append(f'  {sid}["{node_label} *"]:::deferred')
        else:
            lines.append(f'  {sid}["{node_label}"]')
    for e in graph["edges"]:
        if not (_visible(e["from"]) and _visible(e["to"])):
            continue
        lines.append(f"  {_safe_id(e['from'])} --> {_safe_id(e['to'])}")
    # Sort goal ids for cross-format parity with the ASCII tree (byte-deterministic).
    goal_ids = sorted(nid for nid, n in nodes_by_id.items() if n.get("type") == "goal" and _visible(nid))
    for gid in goal_ids:
        lines.append(f"  {_safe_id(gid)} --> PRODUCT")
    return _fence("\n".join(lines))


def _safe_id(s: str) -> str:
    # Mermaid node IDs accept alphanumerics + underscores. Map `-` and `:` to
    # distinct sequences so that, for example, `BRD-G:1` and `BRD_G_1` cannot
    # collide on the same generated id and merge two unrelated nodes in the
    # rendered graph.
    #
    # After the named mappings, whitelist-sanitize: any character outside
    # [A-Za-z0-9_] is replaced with `_` so that PO-controlled id values
    # containing `<`, `>`, `"`, `]`, spaces, or other markup characters cannot
    # reach the Mermaid node-identifier position and inject HTML.
    out = s.replace("-", "__").replace(":", "_C_")
    return re.sub(r"[^A-Za-z0-9_]", "_", out)


def heatmap(graph: Dict[str, Any]) -> str:
    # Mermaid lacks a true heatmap; fall back to a plain markdown code fence
    # (NOT HTML <pre>). visualize.py detects the missing ```mermaid prefix and
    # routes the HTML branch through the <pre> wrapper instead.
    return f"```\n{ascii_heatmap(graph)}\n```"


def scope(graph: Dict[str, Any]) -> str:
    # TRUE 2D scatter: x = moscow (wont→must), y = scope (out→core-value, with the
    # neutral `in` bucket at mid-height). One point per POPULATED (moscow, scope)
    # cell at its real coordinates, count in the (quoted) label — the old fixed
    # `*-stories: [_, 0.5]` row collapsed everything onto one horizontal line with
    # overlapping labels and ignored scope entirely (same bug class as moscow).
    xpos = {"wont": 0.15, "could": 0.4, "should": 0.6, "must": 0.85}
    ypos = {"out": 0.18, "in": 0.5, "core-value": 0.82}
    cells: Dict[tuple, int] = {}
    for n in graph["nodes"]:
        if n.get("type") != "story":
            continue
        mo = _scalar(n.get("moscow"))
        sc = _scalar(n.get("scope"))
        if mo in xpos and sc in ypos:
            cells[(mo, sc)] = cells.get((mo, sc), 0) + 1
    lines = [
        "quadrantChart",
        "  title Scope x MoSCoW",
        "  x-axis Won't --> Must",
        "  y-axis Out --> Core-Value",
        "  quadrant-1 Must / Core",
        "  quadrant-2 Won't / Core",
        "  quadrant-3 Won't / Out",
        "  quadrant-4 Must / Out",
    ]
    for (mo, sc), c in sorted(cells.items()):
        lines.append(f'  "{mo} / {sc} ({c})": [{xpos[mo]}, {ypos[sc]}]')
    if len(lines) == 8:  # no story cells → quadrantChart needs ≥1 point
        return "```\nScope x MoSCoW: 0\n```"
    return _fence("\n".join(lines))


def roadmap(graph: Dict[str, Any], lang: str = "en", filter_wont: bool = False) -> str:
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    items_by_horizon: Dict[str, List[str]] = defaultdict(list)
    for n in graph["nodes"]:
        if n["type"] not in ("prd", "epic", "story"):
            continue
        if filter_wont and _is_deferred(n):
            continue
        h = n.get("horizon")
        items_by_horizon[h if isinstance(h, str) else "unspecified"].append(n["id"])
    lines = ["timeline", "  title Roadmap"]
    for h in (*HORIZON_ORDER, "unspecified"):
        items = sorted(items_by_horizon.get(h, []))
        if not items:
            continue
        section = label(h, lang) if h != "unspecified" else "Unspecified"
        lines.append(f"  section {section}")
        for it in items:
            node = nodes_by_id.get(it, {})
            marker = " *" if _is_deferred(node) else ""
            # Show the human title next to the ID (the timeline used to print bare
            # IDs). Route the whole event text through _safe_label: PO-controlled
            # ids/titles may contain markup chars that would inject live HTML.
            title = node.get("title") or ""
            event = f"{it} — {title}" if title else it
            lines.append(f"    {_safe_label(event)}{marker} : {_safe_label(section)}")
    return _fence("\n".join(lines))


def persona(graph: Dict[str, Any], filter_wont: bool = False) -> str:
    # Mermaid swimlane support for persona x feature is limited; fall back to
    # a plain markdown fence (same convention as heatmap/risk). Thread
    # filter_wont so the mermaid/html persona honors --filter-wont like the
    # ascii persona (the dispatcher passes it through).
    return f"```\n{ascii_persona(graph, filter_wont=filter_wont)}\n```"


def gap(graph: Dict[str, Any]) -> str:
    """Match check_traceability.unaddressed_parent semantics via the shared
    spec_graph.matching_child_counts (counts only EXPECTED-child-type inbound
    edges, so a wrong-type edge on a malformed graph cannot mask a gap)."""
    counts = matching_child_counts(graph)
    # Dark ink pinned in the classDef: the pastel fill is theme-independent, so a
    # theme-driven label color would wash out (light text on light pink in dark mode).
    lines = ["flowchart LR", "  classDef gap fill:#fce4e4,stroke:#cc0000,color:#1f2328"]
    for n in graph["nodes"]:
        if n["type"] in CHILD_TYPE_FOR_PARENT and counts.get(n["id"], 0) == 0:
            sid = _safe_id(n["id"])
            # Route both the node id and the static missing-child text through
            # _safe_label so PO-controlled ids with markup chars cannot inject
            # live HTML when the Mermaid DSL is embedded in the HTML page.
            node_label = _safe_label_lines(n["id"], f"(missing {CHILD_TYPE_FOR_PARENT[n['type']].upper()})")
            lines.append(f'  {sid}["{node_label}"]:::gap')
    if len(lines) == 2:
        lines.append('  OK["(no structural gaps)"]')
    return _fence("\n".join(lines))


def moscow(graph: Dict[str, Any], lang: str = "en") -> str:
    counts = moscow_story_counts(graph)
    must_l = label("must", lang)
    should_l = label("should", lang)
    could_l = label("could", lang)
    wont_l = label("wont", lang)
    # One plotted point PER MoSCoW bucket, placed at its quadrant centre — not a
    # single dot pinned to [0.5, 0.5] (that collapsed every story onto the origin
    # and read as "everything is uncategorised"). Axes: x = wont→must, y =
    # could→should, so the quadrant centres are: must=top-right, should=top-left,
    # could=bottom-left, wont=bottom-right (matching the quadrant-N labels below).
    # Empty buckets are omitted so the chart shows only the buckets in play; the
    # count rides in the (quoted) label — bare "(n)" parens are a lexer error, so
    # every point label is double-quoted (also covers spaces in localized labels).
    centre = {"must": (0.75, 0.75), "should": (0.25, 0.75),
              "could": (0.25, 0.25), "wont": (0.75, 0.25)}
    bucket_label = {"must": must_l, "should": should_l, "could": could_l, "wont": wont_l}
    lines = [
        "quadrantChart",
        "  title Stories — MoSCoW",
        f"  x-axis {wont_l} --> {must_l}",
        f"  y-axis {could_l} --> {should_l}",
        f"  quadrant-1 {must_l}",
        f"  quadrant-2 {should_l}",
        f"  quadrant-3 {could_l}",
        f"  quadrant-4 {wont_l}",
    ]
    points = 0
    for bucket in ("must", "should", "could", "wont"):
        c = counts.get(bucket, 0)
        if not c:
            continue
        x, y = centre[bucket]
        lines.append(f'  "{bucket_label[bucket]} ({c})": [{x}, {y}]')
        points += 1
    # quadrantChart needs ≥1 point to render; an all-empty spec degrades to a note.
    if not points:
        return f"```\n{label('moscow', lang)}: 0\n```"
    return _fence("\n".join(lines))


def risk(graph: Dict[str, Any]) -> str:
    # Mermaid quadrantChart can't express 3x3 risk cleanly; fall back to a
    # plain markdown fence (same convention as heatmap/persona).
    return f"```\n{ascii_risk(graph)}\n```"


def competition(graph: Dict[str, Any]) -> str:
    # The competition view (parity matrix + threat heatmap) is HTML-native by
    # design — Mermaid can't express the comp×PRD matrix cleanly. Fall
    # back to a plain markdown fence around the ASCII grid (same convention as
    # risk/heatmap/persona). The html dispatch routes to render_html.competition.
    return f"```\n{ascii_competition(graph)}\n```"


def time(graph: Dict[str, Any], lang: str = "en", filter_wont: bool = False) -> str:
    """Mermaid `gantt` for the TIME dimension: each PRD/Epic is a
    task, grouped into now/next/later sections, dated by `target_date` when set.

    The depends_on relationships are surfaced as a deterministic, CYCLE-SAFE
    ordering (visited-set walk) plus a `%%` dependency annotation — gantt has no
    cross-task arrow, and a circular chain must not hang the renderer.

    `filter_wont=True` drops deferred (moscow=wont / scope=out) tasks, parity
    with roadmap and the ASCII `time` view.
    """
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    order = _dep_safe_order(graph)
    order_index = {nid: i for i, nid in enumerate(order)}

    timed = [
        n for n in graph["nodes"]
        if n.get("type") in ("prd", "epic")
        and not (filter_wont and _is_deferred(n))
    ]
    # Sort by the cycle-safe dep order first, then id — stable + deterministic.
    timed.sort(key=lambda n: (order_index.get(n["id"], len(order)), n["id"]))

    by_horizon: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for n in timed:
        h = n.get("horizon")
        by_horizon[h if isinstance(h, str) else "unspecified"].append(n)

    # A Mermaid gantt has no "undated" slot: a task line ":id, 1d" is mis-parsed
    # (Mermaid reads the leading token AS a start date → "Invalid date") and a
    # leading undated task crashes the renderer outright ("...reading 'endTime'").
    # So every undated task is anchored on the timeline: chained `after` its
    # predecessor, or — when it sorts first — pinned to the earliest known date.
    # If NOTHING carries a date there is no timeline to draw at all → emit a
    # plain note instead of a structurally-broken gantt.
    dated = [_safe_label(str(n["target_date"])) for n in timed if n.get("target_date")]
    if not dated:
        return f"```\n{label('time_no_dated', lang)}\n```"
    min_date = min(dated)

    lines = ["gantt", f"  title {_safe_label(label('roadmap_deadlines', lang))}", "  dateFormat YYYY-MM-DD"]
    prev_tid = None
    for h in (*HORIZON_ORDER, "unspecified"):
        items = by_horizon.get(h, [])
        if not items:
            continue
        section = label(h, lang) if h != "unspecified" else "Unspecified"
        lines.append(f"  section {_safe_label(section)}")
        for n in items:
            td = n.get("target_date")
            # Task id token must be Mermaid-safe; label is the human id.
            task_label = _safe_label(n["id"])
            tid = _safe_id(n["id"])
            if td:
                # A milestone on the target date (single-day) keeps the gantt
                # valid without inventing a duration the spec never declared.
                lines.append(f"  {task_label} :milestone, {tid}, {_safe_label(str(td))}, 0d")
            elif prev_tid:
                # Undated: trail the previous task (1d placeholder bar) so it still
                # shows, without the id being mistaken for a start date.
                lines.append(f"  {task_label} :{tid}, after {prev_tid}, 1d")
            else:
                # Undated AND sorts first → anchor at the earliest known date.
                lines.append(f"  {task_label} :{tid}, {min_date}, 1d")
            prev_tid = tid

    # Dependency annotations (cycle-safe — `order` was built with a visited set).
    dep_lines = []
    for n in timed:
        for dep in sorted(n.get("depends_on") or []):
            if dep in nodes_by_id:
                dep_lines.append(f"%% {_safe_label(n['id'])} depends_on {_safe_label(dep)}")
    if dep_lines:
        lines.append("")
        lines.extend(dep_lines)
    return _fence("\n".join(lines))


def delta(current: Dict[str, Any], baseline: Dict[str, Any]) -> str:
    """Mermaid delta: node ADD/REMOVE + PRODUCT drift only. A field-only edit (e.g.
    a story's status flip with no add/remove) renders as '(no changes)' here —
    per-field node diffs appear in the ascii/html delta, not this graph view. This
    node-level-only scope is intentional: the Mermaid delta has never carried a
    per-field loop."""
    d = diff_graphs(current, baseline)  # shared added/removed + product-change set-math
    lines = [
        "flowchart TB",
        # Pin a DARK text color in each classDef: the fills are fixed light pastels
        # in BOTH themes, so theme-driven label color (light in dark mode) would
        # vanish on them. Dark ink on a light pastel reads in light AND dark mode.
        "  classDef added fill:#dcedc1,color:#1f2328",
        "  classDef removed fill:#ffd1d1,color:#1f2328",
        "  classDef changed fill:#fff3a3,color:#1f2328",
    ]
    # Prefix markers are bracketed — NOT a bare "+ " / "- ". Mermaid 11 parses a
    # flowchart htmlLabel as markdown, and a label STARTING with "+ "/"- "/"* " is
    # read as a list item → every node renders "Unsupported markdown: list". "(+)"
    # / "(-)" carry the same add/removed meaning without tripping the list parser.
    for a in d["added"]:
        # Route node ids through _safe_label: PO-controlled ids may contain
        # markup characters that would inject live HTML in the rendered page.
        lines.append(f'  {_safe_id(a)}["(+) {_safe_label(a)}"]:::added')
    for r in d["removed"]:
        lines.append(f'  {_safe_id(r)}["(-) {_safe_label(r)}"]:::removed')

    # Product-level changes — emit a single annotated node when name/core_value/personas drifted.
    if d["product_changes"]:
        fields_label = _safe_label(", ".join(d["product_changes"]))
        lines.append(f'  PRODUCT["~ PRODUCT ({fields_label})"]:::changed')

    if len(lines) == 4:
        lines.append('  OK["(no changes)"]')
    return _fence("\n".join(lines))
