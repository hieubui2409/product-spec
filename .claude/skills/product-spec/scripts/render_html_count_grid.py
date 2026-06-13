#!/usr/bin/env python3
"""HTML-native count-grid views: status heatmap and persona coverage.

Heatmap (artifact-type × status) and persona (persona × PRD) are plain
integer-count grids that Mermaid can't express cleanly. Renders them as
real <table>s with the same scoped-CSS, server-escaped, no-Mermaid discipline
as the risk/competition grids.

Public API:
  heatmap(graph, lang) → self-contained HTML fragment
  persona(graph, lang, filter_wont) → self-contained HTML fragment

All spec-derived values are escaped server-side through the local _escape().
Not a CLI entry point; imported by render_html.
"""

from __future__ import annotations

from typing import Any, Dict

from render_html_escape import _escape, _tip_scalar


# ── Shared count-grid CSS ──────────────────────────────────────────────────────

_COUNT_GRID_CSS = (
    "<style>"
    ".count-grid{border-collapse:collapse;width:100%;max-width:48rem;}"
    ".count-grid th,.count-grid td{border:1px solid var(--border);padding:.45rem .6rem;text-align:center;}"
    ".count-grid thead th,.count-grid tbody th{background:var(--recessed);color:var(--muted);font-weight:600;font-size:.85rem;text-align:left;}"
    ".cg-caption{caption-side:top;text-align:left;color:var(--muted);font-size:.85rem;margin-bottom:.5rem;}"
    ".cg-cell{font-variant-numeric:tabular-nums;}"
    ".cg-0{color:var(--muted);}"
    ".cg-hit{background:var(--teal-dim);font-weight:600;}"
    "</style>"
)


def _is_deferred_node(n: Dict[str, Any]) -> bool:
    """A node is deferred when moscow=wont OR scope=out — mirrors
    render_ascii._is_deferred so persona's --filter-wont agrees with the ascii view."""
    return _tip_scalar(n.get("moscow")) == "wont" or _tip_scalar(n.get("scope")) == "out"


def _count_grid_html(caption: str, corner: str, col_headers: list, rows: list) -> str:
    """Generic HTML-native count grid. `rows` = [(row_label, [int, …]), …] aligned
    to col_headers; cells are tinted when non-zero, muted `·` when zero. Every
    label is escaped; counts are ints (never spec text), so no further sanitization."""
    head = "".join(f"<th scope='col'>{_escape(str(h))}</th>" for h in col_headers)
    body = []
    for row_label, cells in rows:
        tds = []
        for c in cells:
            cls = "cg-hit" if c else "cg-0"
            tds.append(f'<td class="cg-cell {cls}">{c if c else "·"}</td>')
        body.append(f"<tr><th scope='row'>{_escape(str(row_label))}</th>{''.join(tds)}</tr>")
    return (
        _COUNT_GRID_CSS
        + f'<table class="count-grid"><caption class="cg-caption">{_escape(caption)}</caption>'
        f"<thead><tr><th scope='col'>{_escape(corner)}</th>{head}</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def heatmap(graph: Dict[str, Any], lang: str = "en") -> str:
    """HTML-native status grid: rows = artifact type, cols = canonical status
    (+ an `other` column when an off-enum status exists, so nothing is dropped)."""
    from collections import defaultdict
    canon = ["draft", "review", "approved"]
    counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    other: Dict[str, int] = defaultdict(int)
    for n in graph.get("nodes", []):
        t = _tip_scalar(n.get("type")) or "?"
        s = _tip_scalar(n.get("status"))
        if s in canon:
            counts[t][s] += 1
        else:
            other[t] += 1
    types = sorted(set(counts) | set(other))
    if not types:
        return _COUNT_GRID_CSS + '<p class="ps-meta">No artifacts yet.</p>'
    cols = list(canon) + (["other"] if any(other.values()) else [])
    rows = [(t, [counts[t].get(s, 0) for s in canon]
                + ([other.get(t, 0)] if "other" in cols else [])) for t in types]
    return _count_grid_html("Status coverage — type (rows) × status (columns).",
                            "type \\ status", cols, rows)


def persona(graph: Dict[str, Any], lang: str = "en", filter_wont: bool = False) -> str:
    """HTML-native persona × PRD coverage grid (story counts), mirroring the ascii
    persona: personas from PRODUCT (else union of node personas), PRD columns,
    story counts attributed to the story's epic→PRD."""
    from collections import defaultdict
    nodes = graph.get("nodes", [])
    product = graph.get("product") if isinstance(graph.get("product"), dict) else {}
    raw = product.get("personas")
    personas = sorted({str(p) for p in raw}) if isinstance(raw, list) else []
    if not personas:
        acc: list = []
        for n in nodes:
            np = n.get("personas")
            if isinstance(np, list):
                for p in np:
                    if str(p) not in acc:
                        acc.append(str(p))
        personas = sorted(acc)
    if not personas:
        return _COUNT_GRID_CSS + '<p class="ps-meta">No personas defined yet.</p>'
    prds = sorted(n["id"] for n in nodes
                  if n.get("type") == "prd" and not (filter_wont and _is_deferred_node(n)))
    epic_to_prd = {n["id"]: n.get("prd") for n in nodes if n.get("type") == "epic"}
    cells: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for n in nodes:
        if n.get("type") != "story" or (filter_wont and _is_deferred_node(n)):
            continue
        prd_id = epic_to_prd.get(n.get("epic"))
        np = n.get("personas")
        if not isinstance(np, list) or not prd_id:
            continue
        for p in np:
            cells[str(p)][prd_id] += 1
    rows = [(p, [cells[p].get(prd, 0) for prd in prds]) for p in personas]
    return _count_grid_html("Persona coverage — persona (rows) × PRD (columns), story counts.",
                            "persona \\ PRD", prds, rows)
