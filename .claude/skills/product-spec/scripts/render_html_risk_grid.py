#!/usr/bin/env python3
"""HTML-native risk grid fragment for the `--viz risk` view.

Isolated from render_html.py so the risk-grid rendering concern (the 3×3
impact×likelihood table + per-cell drill-down) can be maintained independently
of the page-assembly and asset-loading concerns.

Public API: `risk(graph)` → self-contained HTML fragment (scoped <style> + table).
All spec-derived values are escaped server-side through the local `_escape()`
function — identical implementation to render_html._escape, kept here to avoid
a circular import (render_html imports this module).

Not a CLI entry point; imported by render_html.
"""

from __future__ import annotations

from typing import Any, Dict

from render_html_escape import _escape


# ── Risk grid constants ───────────────────────────────────────────────────────

_RISK_IMPACT_ROWS = ("high", "med", "low")        # top-to-bottom (matches ASCII grid)
_RISK_LIKELIHOOD_COLS = ("low", "med", "high")    # left-to-right
_RISK_RANK = {"low": 1, "med": 2, "high": 3}
# Heat tier by impact×likelihood product (1..9): low (green) / mid (amber) / high (red).
# Uses the shared design-system *-dim background tokens so the grid follows the
# light/dark theme like every other product-spec surface.
_RISK_STATUS_BADGE = {"open": "amber", "mitigated": "green", "accepted": "teal"}

# Scoped grid CSS — reuses the shared palette vars (theme-aware) so the grid
# matches every other product-spec HTML surface; injected with the fragment so
# the shared head partial stays untouched.
_RISK_GRID_CSS = (
    "<style>"
    ".risk-grid{border-collapse:collapse;width:100%;max-width:48rem;}"
    ".risk-grid th,.risk-grid td{border:1px solid var(--border);padding:.5rem .6rem;vertical-align:top;text-align:left;}"
    ".risk-grid thead th,.risk-grid tbody th{background:var(--recessed);color:var(--muted);font-weight:600;font-size:.85rem;}"
    ".rg-caption{caption-side:top;text-align:left;color:var(--muted);font-size:.85rem;margin-bottom:.5rem;}"
    ".rg-cell--low{background:var(--green-dim);}.rg-cell--mid{background:var(--amber-dim);}.rg-cell--high{background:var(--red-dim);}"
    ".rg-cell--unrated{background:var(--surface);}"
    ".rg-empty{color:var(--muted);}"
    ".rg-detail summary{cursor:pointer;font-weight:600;}"
    ".rg-list{margin:.4rem 0 0;padding-left:1.1rem;}.rg-list li{margin:.3rem 0;}"
    ".rg-desc{font-weight:600;}.rg-mit{font-size:.85rem;color:var(--text);}"
    ".rg-mit--none{color:var(--muted);font-style:italic;}.rg-mit-label{color:var(--muted);}"
    ".rg-src{font-size:.75rem;color:var(--muted);font-family:ui-monospace,monospace;}"
    ".rg-badge--green{background:var(--green-dim);color:var(--green);}"
    ".rg-badge--amber{background:var(--amber-dim);color:var(--amber);}"
    ".rg-badge--teal{background:var(--teal-dim);color:var(--teal);}"
    "</style>"
)


def _risk_heat_class(impact: str, likelihood: str) -> str:
    score = _RISK_RANK.get(impact, 0) * _RISK_RANK.get(likelihood, 0)
    if score >= 6:
        return "rg-cell--high"
    if score >= 3:
        return "rg-cell--mid"
    return "rg-cell--low"


def _risk_cell_detail(cell_risks: list) -> str:
    """The drill-down body for one grid cell: a <details> listing each risk's
    description + mitigation + status badge. All spec text escaped server-side.
    Sorted by description so the cell body is deterministic."""
    items = []
    for r in sorted(cell_risks, key=lambda r: str(r.get("description") or "")):
        desc = _escape(str(r.get("description") or "(no description)"))
        status = str(r.get("status") or "")
        badge = ""
        if status:
            # Known statuses get a semantic tint; an off-enum status (separately
            # flagged unknown_enum) falls back to the shared neutral badge--type
            # so it still renders as a recognizable pill, never an undefined class.
            tone = _RISK_STATUS_BADGE.get(status)
            cls = f"rg-badge--{tone}" if tone else "badge--type"
            badge = f' <span class="badge {cls}">{_escape(status)}</span>'
        mit = r.get("mitigation")
        mit_html = (
            f'<div class="rg-mit"><span class="rg-mit-label">Mitigation:</span> {_escape(str(mit))}</div>'
            if mit else '<div class="rg-mit rg-mit--none">No mitigation recorded</div>'
        )
        node = _escape(str(r.get("node") or ""))
        src = f'<div class="rg-src">{node}</div>' if node else ""
        items.append(f'<li><div class="rg-desc">{desc}{badge}</div>{mit_html}{src}</li>')
    inner = "".join(items)
    return f'<details class="rg-detail"><summary>{len(cell_risks)}</summary><ul class="rg-list">{inner}</ul></details>'


def risk(graph: Dict[str, Any]) -> str:
    """HTML-native 3×3 risk grid (impact rows × likelihood cols).

    Each cell shows its risk count; a non-empty cell expands (<details>) to the
    description + mitigation + status of every risk it holds — the rendered
    surface for each risk's mitigation/status (dead data until shown). Risks whose
    impact/likelihood are absent/typo'd land in an `(unrated)` overflow row so
    they are never silently dropped (the enum typo is separately flagged by
    check_consistency). Returns a self-contained fragment (scoped <style> + the
    table); deterministic — no timestamp inside the fragment."""
    risks_list = graph.get("risks") or []
    # Bucket risks into the 3×3 matrix; collect anything off-enum into `unrated`.
    cells: Dict[str, Dict[str, list]] = {i: {lk: [] for lk in _RISK_LIKELIHOOD_COLS} for i in _RISK_IMPACT_ROWS}
    unrated: list = []
    for r in risks_list:
        if not isinstance(r, dict):
            continue
        imp, lik = r.get("impact"), r.get("likelihood")
        if imp in _RISK_IMPACT_ROWS and lik in _RISK_LIKELIHOOD_COLS:
            cells[imp][lik].append(r)
        else:
            unrated.append(r)

    head_cols = "".join(f"<th scope='col'>{_escape(l)}</th>" for l in _RISK_LIKELIHOOD_COLS)
    body_rows = []
    for imp in _RISK_IMPACT_ROWS:
        tds = []
        for lik in _RISK_LIKELIHOOD_COLS:
            cell = cells[imp][lik]
            heat = _risk_heat_class(imp, lik)
            inner = _risk_cell_detail(cell) if cell else '<span class="rg-empty">0</span>'
            tds.append(f'<td class="rg-cell {heat}">{inner}</td>')
        body_rows.append(f"<tr><th scope='row'>{_escape(imp)}</th>{''.join(tds)}</tr>")

    unrated_row = ""
    if unrated:
        span = len(_RISK_LIKELIHOOD_COLS)
        unrated_row = (
            f"<tr><th scope='row'>{_escape('(unrated)')}</th>"
            f'<td class="rg-cell rg-cell--unrated" colspan="{span}">{_risk_cell_detail(unrated)}</td></tr>'
        )

    empty_note = "" if risks_list else '<p class="ps-meta">No risks recorded on any PRD or Epic yet.</p>'
    return (
        _RISK_GRID_CSS
        + '<table class="risk-grid"><caption class="rg-caption">Risk: impact (rows) × likelihood (columns). '
        'Click a count to see description, mitigation, and status.</caption>'
        f"<thead><tr><th scope='col'>impact \\ likelihood</th>{head_cols}</tr></thead>"
        f"<tbody>{''.join(body_rows)}{unrated_row}</tbody></table>"
        + empty_note
    )
