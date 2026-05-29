#!/usr/bin/env python3
"""
render_mermaid — emit Mermaid v11 blocks for the 9 visualization views.

Each function returns a string containing a fenced ```mermaid block ready
to paste into markdown. Where a view cannot be expressed cleanly in Mermaid,
the renderer falls back to a `pre`-block with the ASCII version.
"""

from collections import defaultdict
from typing import Any, Dict, List

from i18n_labels import label
from render_ascii import (
    tree as ascii_tree,
    heatmap as ascii_heatmap,
    persona as ascii_persona,
    risk as ascii_risk,
    _is_deferred,
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
        n = nodes_by_id.get(nid)
        if n is None:
            return True
        return not (filter_wont and _is_deferred(n))

    for n in graph["nodes"]:
        # PRODUCT is emitted explicitly above; vision is a narrative doc with
        # no structural role in the tree (no inbound/outbound edges) — skipping
        # both prevents a duplicate PRODUCT box and a stranded empty VISION box.
        if n.get("type") in ("product", "vision"):
            continue
        if not _visible(n["id"]):
            continue
        node_label = _safe_label(f"{n['id']}\\n{n.get('title') or ''}")
        sid = _safe_id(n["id"])
        # Deferred nodes get the `deferred` classDef so the PO can see at a
        # glance which nodes are out-of-scope-but-still-tracked (§15 amendment:
        # default-show with marker, --filter-wont opt-in hide).
        if _is_deferred(n):
            lines.append(f'  {sid}["{node_label} *"]:::deferred')
        else:
            lines.append(f'  {sid}["{node_label}"]')
    for e in graph["edges"]:
        if not (_visible(e["from"]) and _visible(e["to"])):
            continue
        lines.append(f"  {_safe_id(e['from'])} --> {_safe_id(e['to'])}")
    goal_ids = [nid for nid, n in nodes_by_id.items() if n["type"] == "goal" and _visible(nid)]
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
    import re as _re
    out = s.replace("-", "__").replace(":", "_C_")
    return _re.sub(r"[^A-Za-z0-9_]", "_", out)


def heatmap(graph: Dict[str, Any]) -> str:
    # Mermaid lacks a true heatmap; fall back to a plain markdown code fence
    # (NOT HTML <pre>). visualize.py detects the missing ```mermaid prefix and
    # routes the HTML branch through the <pre> wrapper instead.
    return f"```\n{ascii_heatmap(graph)}\n```"


def scope(graph: Dict[str, Any]) -> str:
    # quadrantChart: x = moscow (must..wont), y = scope (out..core-value)
    must = sum(1 for n in graph["nodes"] if n.get("moscow") == "must")
    should = sum(1 for n in graph["nodes"] if n.get("moscow") == "should")
    could = sum(1 for n in graph["nodes"] if n.get("moscow") == "could")
    wont = sum(1 for n in graph["nodes"] if n.get("moscow") == "wont")
    body = f"""quadrantChart
  title Scope x MoSCoW
  x-axis Won't --> Must
  y-axis Out --> Core-Value
  quadrant-1 Must / Core
  quadrant-2 Won't / Core
  quadrant-3 Won't / Out
  quadrant-4 Must / Out
  Must-stories: [0.85, 0.5]
  Should-stories: [0.65, 0.5]
  Could-stories: [0.35, 0.5]
  Won't-stories: [0.15, 0.5]"""
    counts = f"\n%% counts — must:{must} should:{should} could:{could} wont:{wont}"
    return _fence(body + counts)


def roadmap(graph: Dict[str, Any], lang: str = "en", filter_wont: bool = False) -> str:
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    items_by_horizon: Dict[str, List[str]] = defaultdict(list)
    for n in graph["nodes"]:
        if n["type"] not in ("prd", "epic", "story"):
            continue
        if filter_wont and _is_deferred(n):
            continue
        items_by_horizon[n.get("horizon") or "unspecified"].append(n["id"])
    lines = ["timeline", "  title Roadmap"]
    for h in ("now", "next", "later", "unspecified"):
        items = sorted(items_by_horizon.get(h, []))
        if not items and h == "unspecified":
            continue
        section = label(h, lang) if h != "unspecified" else "Unspecified"
        lines.append(f"  section {section}")
        for it in items[:8]:
            marker = " *" if _is_deferred(nodes_by_id.get(it, {})) else ""
            # Route item id through _safe_label: PO-controlled ids may contain
            # markup characters that would inject live HTML in the rendered page.
            safe_it = _safe_label(it)
            lines.append(f"    {safe_it}{marker} : {_safe_label(section)}")
    return _fence("\n".join(lines))


def persona(graph: Dict[str, Any]) -> str:
    # Mermaid swimlane support for persona x feature is limited; fall back to
    # a plain markdown fence (same convention as heatmap/risk).
    return f"```\n{ascii_persona(graph)}\n```"


def gap(graph: Dict[str, Any]) -> str:
    """Match check_traceability.unaddressed_parent semantics by counting only
    inbound edges of the EXPECTED child type. Earlier this counted any
    inbound edge, which diverged on malformed graphs."""
    expected = {"goal": "prd", "prd": "epic", "epic": "story"}
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    matching_children = defaultdict(int)
    for e in graph["edges"]:
        src = nodes_by_id.get(e["from"], {}).get("type")
        target_type = nodes_by_id.get(e["to"], {}).get("type")
        if target_type in expected and expected[target_type] == src:
            matching_children[e["to"]] += 1
    lines = ["flowchart LR", "  classDef gap fill:#fce4e4,stroke:#cc0000"]
    for n in graph["nodes"]:
        if n["type"] in expected and matching_children[n["id"]] == 0:
            sid = _safe_id(n["id"])
            # Route both the node id and the static missing-child text through
            # _safe_label so PO-controlled ids with markup chars cannot inject
            # live HTML when the Mermaid DSL is embedded in the HTML page.
            node_label = _safe_label(f"{n['id']}\\n(missing {expected[n['type']].upper()})")
            lines.append(f'  {sid}["{node_label}"]:::gap')
    if len(lines) == 2:
        lines.append('  OK["(no structural gaps)"]')
    return _fence("\n".join(lines))


def moscow(graph: Dict[str, Any], lang: str = "en") -> str:
    counts = defaultdict(int)
    for n in graph["nodes"]:
        if n["type"] != "story":
            continue
        counts[n.get("moscow") or "?"] += 1
    must_l = label("must", lang)
    should_l = label("should", lang)
    could_l = label("could", lang)
    wont_l = label("wont", lang)
    body = f"""quadrantChart
  title Stories — MoSCoW
  x-axis {wont_l} --> {must_l}
  y-axis {could_l} --> {should_l}
  quadrant-1 {must_l}
  quadrant-2 {should_l}
  quadrant-3 {could_l}
  quadrant-4 {wont_l}
  Stories: [0.5, 0.5]
%% counts: must={counts.get('must',0)} should={counts.get('should',0)} could={counts.get('could',0)} wont={counts.get('wont',0)}"""
    return _fence(body)


def risk(graph: Dict[str, Any]) -> str:
    # Mermaid quadrantChart can't express 3x3 risk cleanly; fall back to a
    # plain markdown fence (same convention as heatmap/persona).
    return f"```\n{ascii_risk(graph)}\n```"


def delta(current: Dict[str, Any], baseline: Dict[str, Any]) -> str:
    cur_ids = {n["id"]: n for n in current.get("nodes", [])}
    base_ids = {n["id"]: n for n in baseline.get("nodes", [])}
    added = sorted(set(cur_ids) - set(base_ids))
    removed = sorted(set(base_ids) - set(cur_ids))
    lines = [
        "flowchart TB",
        "  classDef added fill:#dcedc1",
        "  classDef removed fill:#ffd1d1",
        "  classDef changed fill:#fff3a3",
    ]
    for a in added:
        # Route node ids through _safe_label: PO-controlled ids may contain
        # markup characters that would inject live HTML in the rendered page.
        lines.append(f'  {_safe_id(a)}["+ {_safe_label(a)}"]:::added')
    for r in removed:
        lines.append(f'  {_safe_id(r)}["- {_safe_label(r)}"]:::removed')

    # Product-level changes — emit a single annotated node when name/core_value/personas drifted.
    cur_p = current.get("product") or {}
    base_p = baseline.get("product") or {}
    product_changes: List[str] = []
    for field in ("name", "core_value"):
        if cur_p.get(field) != base_p.get(field):
            product_changes.append(field)
    if sorted(cur_p.get("personas") or []) != sorted(base_p.get("personas") or []):
        product_changes.append("personas")
    if product_changes:
        fields_label = _safe_label(", ".join(product_changes))
        lines.append(f'  PRODUCT["~ PRODUCT ({fields_label})"]:::changed')

    if len(lines) == 4:
        lines.append('  OK["(no changes)"]')
    return _fence("\n".join(lines))
