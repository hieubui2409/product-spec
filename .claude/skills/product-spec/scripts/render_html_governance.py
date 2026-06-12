#!/usr/bin/env python3
"""HTML-native governance views: audit trail and multi-dimensional dashboard.

Audit trail: a chronological table of governance events from assemble_audit_trail.
All free-text fields (who_approved, DEC title, "what drifted") are higher
injection-risk than structured graph views — EVERY dynamic value is escaped
server-side through _escape() (no DOMPurify/marked, no href channel).

Dashboard: HTML-only multi-dim view stacking roadmap-by-horizon + risk grid +
competition on one page. Composes the already-escaped HTML-native builders
(risk()/competition()); no new escaping surface and no Mermaid runtime.

Public API:
  audit(data, lang)      → self-contained HTML fragment (scoped CSS + table)
  dashboard(graph, lang) → self-contained HTML fragment (3 stacked panels)

Not a CLI entry point; imported by render_html.
"""

from __future__ import annotations

from typing import Any, Dict

from spec_graph import HORIZON_ORDER
from i18n_labels import label

from render_html_escape import _escape


# ── Audit trail ───────────────────────────────────────────────────────────────

_AUDIT_CSS = (
    "<style>"
    ".audit-table{border-collapse:collapse;width:100%;max-width:60rem;}"
    ".audit-table caption{caption-side:top;text-align:left;color:var(--muted);font-size:.85rem;margin-bottom:.5rem;}"
    ".audit-table th,.audit-table td{border:1px solid var(--border);padding:.5rem .6rem;vertical-align:top;text-align:left;font-size:.9rem;}"
    ".audit-table thead th{background:var(--recessed);color:var(--muted);font-weight:600;}"
    ".audit-unreconciled{background:var(--red-dim);}"
    ".audit-unreconciled td:first-child::before{content:'⚠ ';}"
    ".audit-empty{color:var(--muted);font-style:italic;}"
    "</style>"
)


def audit(data: Dict[str, Any], lang: str = "en") -> str:
    """HTML-native governance audit trail: a chronological table.

    `data` is the dict from `assemble_audit_trail.assemble` (events list). Returns a
    self-contained fragment (scoped <style> + <table>). EVERY spec/PO-derived value is
    escaped server-side via _escape() — the unreconciled rows are flagged with a class +
    a marker, never dropped. Deterministic: no timestamp inside the fragment."""
    from assemble_audit_trail import _AUDIT_LABELS  # lazy: no import cycle
    lab = _AUDIT_LABELS.get(lang, _AUDIT_LABELS["en"])
    events = data.get("events", [])
    if not events:
        return _AUDIT_CSS + f'<p class="audit-empty">{_escape(lab["empty"])}</p>'
    headers = [lab["when"], lab["artifact"], lab["action"], lab["who"], lab["drift"], lab["dec"]]
    head = "".join(f"<th>{_escape(h)}</th>" for h in headers)
    rows = []
    for e in events:
        action = e.get("action", "")
        cls = "" if e.get("reconciled", True) else ' class="audit-unreconciled"'
        if not e.get("reconciled", True):
            action = f'{action} [{lab["unreconciled"]}]'
        cells = [e.get("date") or "-", e.get("artifact") or "-", action or "-",
                 e.get("who_approved") or "-", e.get("what_drifted") or "-", e.get("dec_ref") or "-"]
        tds = "".join(f"<td>{_escape(str(c))}</td>" for c in cells)
        rows.append(f"<tr{cls}>{tds}</tr>")
    return (
        _AUDIT_CSS
        + '<table class="audit-table">'
        + f"<caption>{_escape(lab['title'])}</caption>"
        + f"<thead><tr>{head}</tr></thead>"
        + "<tbody>" + "".join(rows) + "</tbody>"
        + "</table>"
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────

_DASHBOARD_CSS = (
    "<style>"
    ".db-panel{margin:0 0 2rem;}"
    ".db-title{font-size:1.1rem;margin:0 0 .75rem;padding-bottom:.3rem;border-bottom:1px solid var(--border);}"
    ".db-h{font-size:.9rem;color:var(--muted);margin:.75rem 0 .35rem;}"
    ".db-roadmap{border-collapse:collapse;width:100%;max-width:48rem;margin-bottom:.5rem;}"
    ".db-roadmap th,.db-roadmap td{border:1px solid var(--border);padding:.4rem .6rem;text-align:left;}"
    ".db-roadmap thead th,.db-roadmap tbody th{background:var(--recessed);color:var(--muted);font-weight:600;font-size:.85rem;}"
    ".db-nodate,.db-empty{color:var(--muted);font-style:italic;}"
    "</style>"
)


def _dashboard_roadmap(graph: Dict[str, Any], lang: str = "en") -> str:
    """An HTML-native roadmap/deadline table for the dashboard: PRD/Epic/Story
    grouped by horizon (now/next/later/unspecified), each row showing id +
    target_date. Server-escaped + deterministic (sorted by id within horizon).
    Horizon headers localize via i18n_labels. Uses HORIZON_ORDER from spec_graph
    (single source of truth — eliminates the orphaned _DASHBOARD_HORIZONS copy)."""
    groups: Dict[str, list] = {}
    for n in graph.get("nodes", []):
        if not isinstance(n, dict):
            continue
        if n.get("type") not in ("prd", "epic", "story"):
            continue
        # Coerce to a hashable scalar before bucketing: an unhashable horizon
        # (a list/dict from malformed YAML) would raise TypeError in setdefault.
        h = n.get("horizon")
        h = h if isinstance(h, str) else "unspecified"
        groups.setdefault(h, []).append(n)

    sections = []
    order = list(HORIZON_ORDER) + ["unspecified"]
    for h in order:
        items = sorted(groups.get(h, []), key=lambda n: str(n.get("id") or ""))
        if not items and h == "unspecified":
            continue
        head = _escape(label(h, lang).upper() if h in HORIZON_ORDER else "UNSPECIFIED")
        rows = []
        for n in items:
            nid = _escape(str(n.get("id") or ""))
            td = n.get("target_date")
            date_txt = _escape(str(td)) if td else '<span class="db-nodate">—</span>'
            rows.append(f'<tr><th scope="row">{nid}</th><td>{date_txt}</td></tr>')
        body = "".join(rows) or '<tr><td class="db-empty" colspan="2">(none)</td></tr>'
        sections.append(
            f'<h3 class="db-h">{head}</h3>'
            f'<table class="db-roadmap"><thead><tr>'
            f'<th scope="col">item</th><th scope="col">target date</th>'
            f"</tr></thead><tbody>{body}</tbody></table>"
        )
    return "".join(sections) or '<p class="ps-meta">No PRDs/epics/stories with a horizon yet.</p>'


def dashboard(graph: Dict[str, Any], lang: str = "en") -> str:
    """HTML-only multi-dim dashboard: roadmap + risk grid + competition, stacked
    on one page. Reuses the already-escaped HTML-native builders, so the
    fragment is self-contained and carries no Mermaid runtime. Deterministic."""
    from render_html_risk_grid import risk
    from render_html_competition import competition
    return (
        _DASHBOARD_CSS
        + '<section class="db-panel"><h2 class="db-title">Roadmap &amp; Deadlines</h2>'
        + _dashboard_roadmap(graph, lang)
        + '</section>'
        + '<section class="db-panel"><h2 class="db-title">Risk</h2>'
        + risk(graph)
        + '</section>'
        + '<section class="db-panel"><h2 class="db-title">Competition</h2>'
        + competition(graph, lang)
        + '</section>'
    )
