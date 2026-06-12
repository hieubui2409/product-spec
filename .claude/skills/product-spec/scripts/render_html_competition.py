#!/usr/bin/env python3
"""HTML-native competition view: parity matrix + threat heatmap.

Like the risk grid, the competition view is an HTML-native <table> that Mermaid
can't express cleanly. NOT a body view: every competitor name / id / parity /
threat is a short structured value escaped server-side through _escape() — the
SAME chokepoint discipline as the risk grid. Inlines NO marked/DOMPurify and NO
Mermaid runtime.

Competitor identity is the BRD's DRY home (graph["competitors"]); per-PRD
parity is the ID-keyed map on each PRD node (node["competitive_parity"]).
A `private:`-stripped url never reaches here (dropped at parse).

Public API:
  competition(graph, lang) → self-contained HTML fragment (scoped CSS + 2 tables)

Not a CLI entry point; imported by render_html.
"""

from __future__ import annotations

from typing import Any, Dict

from render_html_escape import _escape


# ── Competition constants ─────────────────────────────────────────────────────

# Each parity verdict + threat tier maps to a shared design-system *-dim tint so
# the matrix/heatmap follow the light/dark theme like every other surface. An
# off-enum value (separately flagged unknown_enum) falls back to no tint class.
_PARITY_CELL_CLASS = {
    "ahead": "cm-ahead", "parity": "cm-parity", "behind": "cm-behind", "none": "cm-none",
}
_THREAT_CELL_CLASS = {"low": "cm-t-low", "med": "cm-t-med", "high": "cm-t-high"}

# Scoped competition CSS — reuses the shared palette vars (theme-aware) so the
# matrix + heatmap match every other product-spec HTML surface.
_COMPETITION_CSS = (
    "<style>"
    ".comp-section{margin:0 0 1.5rem;}"
    ".comp-matrix,.comp-heatmap{border-collapse:collapse;width:100%;max-width:48rem;}"
    ".comp-matrix th,.comp-matrix td,.comp-heatmap th,.comp-heatmap td{"
    "border:1px solid var(--border);padding:.5rem .6rem;vertical-align:top;text-align:left;}"
    ".comp-matrix thead th,.comp-matrix tbody th,.comp-heatmap thead th,.comp-heatmap tbody th{"
    "background:var(--recessed);color:var(--muted);font-weight:600;font-size:.85rem;}"
    ".cm-caption{caption-side:top;text-align:left;color:var(--muted);font-size:.85rem;margin-bottom:.5rem;}"
    ".cm-empty{color:var(--muted);font-style:italic;}"
    ".cm-ahead{background:var(--green-dim);}"
    ".cm-parity{background:var(--teal-dim);}"
    ".cm-behind{background:var(--red-dim);}"
    ".cm-none{background:var(--surface);color:var(--muted);}"
    ".cm-t-low{background:var(--green-dim);}"
    ".cm-t-med{background:var(--amber-dim);}"
    ".cm-t-high{background:var(--red-dim);}"
    "</style>"
)


# ── Label helpers ─────────────────────────────────────────────────────────────

def _parity_label(val: Any, lang: str) -> str:
    """Localize a parity enum word for display. The enum KEY (English) drives the
    cell CLASS; this only localizes the visible text. EN labels are identity, so
    the EN render still shows the raw enum word; VI translates (best-effort)."""
    from i18n_labels import label
    known = {"ahead", "parity", "behind", "none"}
    # Guard against an unhashable spec value (list/dict from malformed YAML) so
    # the renderer degrades to a raw string, never crashes.
    return label(f"parity_{val}", lang) if isinstance(val, str) and val in known else str(val)


def _threat_label(val: Any, lang: str) -> str:
    """Localize a threat tier for display (EN identity; VI best-effort). Off-enum
    values render raw — they are flagged separately by check_consistency."""
    from i18n_labels import label
    known = {"low", "med", "high"}
    # Guard against an unhashable val (list/dict from malformed YAML).
    return label(f"threat_{val}", lang) if isinstance(val, str) and val in known else str(val)


# ── Table builders ────────────────────────────────────────────────────────────

def _competition_matrix(competitors: list, prds: list, lang: str, cell_lookup) -> str:
    """The parity matrix <table>: competitor NAME rows × PRD id columns, cells =
    the parity enum the PRD declared for that competitor (blank when unset). All
    spec text escaped server-side. Deterministic — competitors keep BRD order,
    PRDs are sorted by id. Parity verdicts localize via i18n_labels (`--lang vi`);
    the enum KEY stays English (it's the cell CLASS), only the displayed word
    localizes. An off-enum value (separately flagged unknown_enum) shows raw.

    `cell_lookup` is the resolver from render_ascii.resolve_competition — the
    single home for the per-cell resolution rule (required, no inline fallback)."""
    head_cols = "".join(f"<th scope='col'>{_escape(str(p.get('id') or ''))}</th>" for p in prds)
    rows = []
    for c in competitors:
        name = _escape(str(c.get("name") or c.get("id") or "(unnamed)"))
        tds = []
        for p in prds:
            val = cell_lookup(c, p)
            cls = _PARITY_CELL_CLASS.get(val, "") if isinstance(val, (str, type(None))) else ""
            text = _escape(_parity_label(val, lang)) if val is not None else ""
            tds.append(f'<td class="cm-cell {cls}">{text}</td>')
        rows.append(f"<tr><th scope='row'>{name}</th>{''.join(tds)}</tr>")
    body = "".join(rows) or (
        f'<tr><td class="cm-empty" colspan="{len(prds) + 1}">'
        "No competitors declared in the BRD yet.</td></tr>"
    )
    return (
        '<table class="comp-matrix"><caption class="cm-caption">Competitive parity: '
        'competitors (rows) × PRDs (columns). Each cell is the PRD’s parity verdict '
        'for that competitor (ahead / parity / behind / none).</caption>'
        f"<thead><tr><th scope='col'>competitor \\ PRD</th>{head_cols}</tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def _competition_heatmap(competitors: list, lang: str = "en") -> str:
    """The threat heatmap <table>: one row per competitor with its threat tier,
    color-tinted by tier. Server-escaped + deterministic (BRD order). Threat
    tiers localize via i18n_labels; the CLASS stays keyed on the English enum."""
    rows = []
    for c in competitors:
        name = _escape(str(c.get("name") or c.get("id") or "(unnamed)"))
        threat = c.get("threat")
        # Guard the class lookup against an unhashable threat (a list/dict from
        # malformed YAML would raise TypeError in dict.get); the enum typo is
        # flagged separately by check_consistency. Visible text degrades safely.
        cls = _THREAT_CELL_CLASS.get(threat, "") if isinstance(threat, (str, type(None))) else ""
        text = _escape(_threat_label(threat, lang)) if threat is not None else _escape("(unrated)")
        rows.append(
            f"<tr><th scope='row'>{name}</th>"
            f'<td class="cm-cell {cls}">{text}</td></tr>'
        )
    body = "".join(rows) or '<tr><td class="cm-empty" colspan="2">No competitors yet.</td></tr>'
    return (
        '<table class="comp-heatmap"><caption class="cm-caption">Threat heatmap: '
        'each competitor’s threat tier (low / med / high).</caption>'
        "<thead><tr><th scope='col'>competitor</th><th scope='col'>threat</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def competition(graph: Dict[str, Any], lang: str = "en") -> str:
    """HTML-native competition view: parity matrix + threat heatmap.

    Delegates resolution of competitors+PRDs+cell_lookup to
    render_ascii.resolve_competition (single home for the resolution rule).
    Returns a self-contained fragment (scoped <style> + the two tables);
    deterministic — no timestamp inside the fragment. Renders an empty
    placeholder when no competitors exist so a v1 spec can still request the view
    (back-compat). Every spec-derived value is escaped server-side (no DOMPurify/marked)."""
    import render_ascii as _ra
    competitors, prds, cell_lookup = _ra.resolve_competition(graph)
    matrix = _competition_matrix(competitors, prds, lang, cell_lookup=cell_lookup)
    heatmap_frag = _competition_heatmap(competitors, lang)
    empty_note = "" if competitors else (
        '<p class="ps-meta">No competitors recorded in the BRD yet. '
        'Add a <code>competitors:</code> block to brd.md to populate this view.</p>'
    )
    return (
        _COMPETITION_CSS
        + '<section class="comp-section">'
        + matrix
        + '</section><section class="comp-section">'
        + heatmap_frag
        + "</section>"
        + empty_note
    )
