#!/usr/bin/env python3
"""
render_html — assemble a self-contained HTML visualization page.

Reads:
  - assets/templates/visual-html-shell.html (the page skeleton)
  - assets/vendor/mermaid.min.js (vendored Mermaid; pin via install.sh)

If the vendored mermaid.min.js is missing, the renderer falls back to a
CDN-hosted script tag and prints a visible warning banner in the output.

Output is one self-contained file at:
  docs/product/visuals/<view>-<timestamp>.html

CLI usage is via visualize.py.
"""

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from spec_graph import _now
from i18n_labels import label


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "assets" / "templates"
VENDOR = SKILL_ROOT / "assets" / "vendor"
SHELL_PATH = TEMPLATES / "visual-html-shell.html"
VIEWER_HEAD_PARTIAL = TEMPLATES / "_viewer-head.html"
VENDOR_MERMAID = VENDOR / "mermaid.min.js"
VENDOR_MARKED = VENDOR / "marked.min.js"
VENDOR_PURIFY = VENDOR / "purify.min.js"
CDN_FALLBACK = (
    "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"
)


def _load_vendored_mermaid_js() -> Optional[str]:
    """Return the inline Mermaid JS payload if vendored; else None.

    Split out from the CDN-fallback path so each path has a single
    responsibility: this one only reads the local file, returns None on
    miss. The caller decides whether to fall back.
    """
    if VENDOR_MERMAID.exists():
        return VENDOR_MERMAID.read_text(encoding="utf-8")
    return None


def _cdn_fallback_snippet() -> str:
    """Return a <script>-close + CDN-load + <script>-reopen snippet.

    The shell template embeds the returned string inside a `<script>` tag.
    To inject an external `<script src=...>`, this snippet closes the
    surrounding tag, emits the CDN tag, then reopens an empty `<script>`
    so the rest of the shell stays syntactically valid.
    """
    warning = (
        "console.warn('product-spec: vendored mermaid.min.js is missing; "
        "falling back to CDN. Run install.sh to vendor the file for "
        "offline self-containment.');"
    )
    return (
        "/* vendored Mermaid not found — falling back to CDN. */\n"
        + warning
        + "\n</script>\n"
        + f'<script src="{CDN_FALLBACK}"></script>\n'
        + "<script>"
    )


def _load_mermaid_js() -> str:
    """Return either the vendored JS payload or the CDN-fallback snippet.

    Thin compatibility wrapper kept so callers (and tests) that don't care
    about the source can stay one-line. New code should prefer the two
    explicit helpers above to make the source path obvious at the call site.
    """
    vendored = _load_vendored_mermaid_js()
    return vendored if vendored is not None else _cdn_fallback_snippet()


def _render_view_body(view_format: str, view_text: str) -> str:
    """Wrap the per-view body so the page renders Mermaid OR pre text.

    view_format == "mermaid"   -> extract inner Mermaid DSL from fenced block,
                                  wrap in <div class="mermaid">.
    view_format == "html"/"risk-grid" -> view_text is an ALREADY-SAFE HTML
                                  fragment (e.g. the risk() grid, whose spec
                                  text was escaped at build time). Inject as-is
                                  — do NOT re-escape (that would render the
                                  <table> markup as literal text).
    view_format == "pre" / *   -> escape view_text and wrap in <pre> so the
                                  browser renders raw ASCII (used for the
                                  heatmap / persona views where Mermaid has no
                                  clean expression).
    """
    if view_format in ("html", "risk-grid"):
        # Pre-rendered HTML-native fragment. The ONLY safe-HTML view_format:
        # the producer (render_html.risk) is responsible for escaping every
        # spec-derived value through _escape() before assembling the fragment.
        return view_text
    if view_format == "mermaid":
        m = re.search(r"```mermaid\n(.*?)\n```", view_text, re.DOTALL)
        body = m.group(1) if m else view_text
        # Escape only `<` and `>` in the Mermaid DSL body — NOT `&`.
        #
        # Defense-in-depth layer: the HTML parser runs before Mermaid's
        # auto-renderer, so raw `<script>` or `<img onerror=…>` in the DSL
        # body would execute during parsing before securityLevel:strict can
        # intercept.  Escaping `<`/`>` neutralises that class of injection
        # while keeping `-->` as a safe textContent round-trip (`--&gt;` in
        # source decodes back to `-->` when Mermaid reads .textContent).
        #
        # `&` is intentionally NOT escaped here. `_safe_label` (in
        # render_mermaid) already encodes `&` → `&amp;` at the label
        # chokepoint.  Escaping `&` again here would double-encode to
        # `&amp;amp;`, so a node titled "R&D" would render as literal
        # "R&amp;D" in the browser instead of "R&D".
        body_escaped = body.replace("<", "&lt;").replace(">", "&gt;")
        return f'<div class="mermaid">\n{body_escaped}\n</div>'
    return f"<pre>{_escape(view_text)}</pre>"


def _escape(s: str) -> str:
    # & must be replaced first so subsequent escaped sequences don't get double-escaped.
    # Quotes are escaped to make the function safe for attribute context as well as body
    # context, even though current call sites only feed body text.
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&#39;")
    )


# ── HTML-native risk grid (impact × likelihood) ─────────────────────────────
#
# The risk view is the one graph view Mermaid can't express cleanly (design
# report Q44: matrix/heatmap/risk-grid = HTML-native table). It is NOT a body
# view: risk fields are short structured scalars + free-text, rendered as a
# server-escaped <table> through _escape() — the SAME chokepoint discipline as
# the heatmap/persona <pre> path. It therefore inlines NO marked/DOMPurify and
# NO Mermaid runtime (symmetric payload gating: the grid is plain HTML/CSS).

_RISK_IMPACT_ROWS = ("high", "med", "low")        # top-to-bottom (matches ASCII grid)
_RISK_LIKELIHOOD_COLS = ("low", "med", "high")    # left-to-right
_RISK_RANK = {"low": 1, "med": 2, "high": 3}
# Heat tier by impact×likelihood product (1..9): low (green) / mid (amber) / high (red).
# Uses the shared design-system *-dim background tokens so the grid follows the
# light/dark theme like every other product-spec surface.
_RISK_STATUS_BADGE = {"open": "amber", "mitigated": "green", "accepted": "teal"}


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
    surface for G-C3's mitigation/status (dead data until shown). Risks whose
    impact/likelihood are absent/typo'd land in an `(unrated)` overflow row so
    they are never silently dropped (the enum typo is separately flagged by
    check_consistency). Returns a self-contained fragment (scoped <style> + the
    table); deterministic — no timestamp inside the fragment."""
    risks = graph.get("risks") or []
    # Bucket risks into the 3×3 matrix; collect anything off-enum into `unrated`.
    cells: Dict[str, Dict[str, list]] = {i: {l: [] for l in _RISK_LIKELIHOOD_COLS} for i in _RISK_IMPACT_ROWS}
    unrated: list = []
    for r in risks:
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

    empty_note = "" if risks else '<p class="ps-meta">No risks recorded on any PRD or Epic yet.</p>'
    return (
        _RISK_GRID_CSS
        + '<table class="risk-grid"><caption class="rg-caption">Risk: impact (rows) × likelihood (columns). '
        'Click a count to see description, mitigation, and status.</caption>'
        f"<thead><tr><th scope='col'>impact \\ likelihood</th>{head_cols}</tr></thead>"
        f"<tbody>{''.join(body_rows)}{unrated_row}</tbody></table>"
        + empty_note
    )


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


# ── HTML-native competition view (parity matrix + threat heatmap) ───────────
#
# Like the risk grid, the competition view is an HTML-native <table> Mermaid
# can't express cleanly (design report Q30/Q44). It is NOT a body view: every
# competitor name / id / parity / threat is a short structured value escaped
# server-side through _escape() — the SAME chokepoint discipline as the risk
# grid (G-A4). It inlines NO marked/DOMPurify and NO Mermaid runtime; it routes
# through visualize.py's "html"/"risk-grid"-style native path, never Mermaid.
#
# Competitor IDENTITY is the BRD's DRY home (graph["competitors"]); per-PRD
# parity is the ID-keyed map on each PRD node (node["competitive_parity"]). The
# renderer resolves the two: matrix rows = competitor NAMES (from the BRD),
# matrix cols = PRD ids, cells = the parity enum the PRD declared for that
# competitor. A `private:`-stripped url never reaches here (dropped at parse).

_PARITY_COLS = ("ahead", "parity", "behind", "none")  # legend order
# Each parity verdict + threat tier maps to a shared design-system *-dim tint so
# the matrix/heatmap follow the light/dark theme like every other surface. An
# off-enum value (separately flagged unknown_enum) falls back to no tint class.
_PARITY_CELL_CLASS = {
    "ahead": "cm-ahead", "parity": "cm-parity", "behind": "cm-behind", "none": "cm-none",
}
_THREAT_CELL_CLASS = {"low": "cm-t-low", "med": "cm-t-med", "high": "cm-t-high"}


def _competition_matrix(competitors: list, prds: list, lang: str = "en") -> str:
    """The parity matrix <table>: competitor NAME rows × PRD id columns, cells =
    the parity enum the PRD declared for that competitor (blank when unset). All
    spec text escaped server-side. Deterministic — competitors keep BRD order,
    PRDs are sorted by id. Parity verdicts localize via i18n_labels (`--lang vi`);
    the enum KEY stays English (it's the cell CLASS), only the displayed word
    localizes. An off-enum value (separately flagged unknown_enum) shows raw."""
    head_cols = "".join(f"<th scope='col'>{_escape(str(p['id']))}</th>" for p in prds)
    rows = []
    for c in competitors:
        name = _escape(str(c.get("name") or c.get("id") or "(unnamed)"))
        tds = []
        for p in prds:
            parity = (p.get("competitive_parity") or {})
            val = parity.get(c.get("id")) if isinstance(parity, dict) else None
            cls = _PARITY_CELL_CLASS.get(val, "")
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


def _parity_label(val: Any, lang: str) -> str:
    """Localize a parity enum word for display. The enum KEY (English) drives the
    cell CLASS; this only localizes the visible text. EN labels are identity, so
    the EN render still shows the raw enum word; VI translates (best-effort)."""
    known = {"ahead", "parity", "behind", "none"}
    return label(f"parity_{val}", lang) if val in known else str(val)


def _threat_label(val: Any, lang: str) -> str:
    """Localize a threat tier for display (EN identity; VI best-effort). Off-enum
    values render raw — they are flagged separately by check_consistency."""
    known = {"low", "med", "high"}
    return label(f"threat_{val}", lang) if val in known else str(val)


def _competition_heatmap(competitors: list, lang: str = "en") -> str:
    """The threat heatmap <table>: one row per competitor with its threat tier,
    color-tinted by tier. Server-escaped + deterministic (BRD order). Threat
    tiers localize via i18n_labels; the CLASS stays keyed on the English enum."""
    rows = []
    for c in competitors:
        name = _escape(str(c.get("name") or c.get("id") or "(unnamed)"))
        threat = c.get("threat")
        cls = _THREAT_CELL_CLASS.get(threat, "")
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

    Resolves the BRD's competitor IDENTITY (graph["competitors"]) against each
    PRD's ID-keyed `competitive_parity` map. Returns a self-contained fragment
    (scoped <style> + the two tables); deterministic — no timestamp inside the
    fragment (G-A4). Renders an empty placeholder when no competitors exist so a
    v1 spec can still request the view (G-A2). Every spec-derived value is
    escaped server-side (the view inlines no DOMPurify/marked)."""
    competitors = [c for c in (graph.get("competitors") or []) if isinstance(c, dict)]
    prds = sorted(
        (n for n in graph.get("nodes", []) if n.get("type") == "prd"),
        key=lambda n: str(n.get("id") or ""),
    )
    matrix = _competition_matrix(competitors, prds, lang)
    heatmap = _competition_heatmap(competitors, lang)
    empty_note = "" if competitors else (
        '<p class="ps-meta">No competitors recorded in the BRD yet. '
        'Add a <code>competitors:</code> block to brd.md to populate this view.</p>'
    )
    return (
        _COMPETITION_CSS
        + '<section class="comp-section">'
        + matrix
        + '</section><section class="comp-section">'
        + heatmap
        + "</section>"
        + empty_note
    )


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


# ── HTML-native multi-dimensional dashboard (HTML-only; PO decision §0.2) ───
#
# The dashboard is the new HTML-only multi-dim view (G-G1): ONE self-contained
# page that stacks the existing HTML-native fragments — roadmap-by-horizon +
# risk grid + competition (parity matrix + threat heatmap) — so a PO sees TIME,
# RISK, and COMPETITION at a glance without opening three files. It composes the
# already-escaped builders (risk()/competition()) plus a small roadmap table; it
# adds NO new escaping surface and NO Mermaid runtime (every fragment is plain
# server-escaped HTML, the SAME chokepoint discipline as the risk/competition
# grids). Deterministic — no timestamp inside the fragment (G-A4).

_DASHBOARD_HORIZONS = ("now", "next", "later")


def _dashboard_roadmap(graph: Dict[str, Any], lang: str = "en") -> str:
    """An HTML-native roadmap/deadline table for the dashboard: PRD/Epic/Story
    grouped by horizon (now/next/later/unspecified), each row showing id +
    target_date. Server-escaped + deterministic (sorted by id within horizon).
    Horizon headers localize via i18n_labels."""
    groups: Dict[str, list] = {}
    for n in graph.get("nodes", []):
        if n.get("type") not in ("prd", "epic", "story"):
            continue
        h = n.get("horizon") or "unspecified"
        groups.setdefault(h, []).append(n)

    sections = []
    order = list(_DASHBOARD_HORIZONS) + ["unspecified"]
    for h in order:
        items = sorted(groups.get(h, []), key=lambda n: str(n.get("id") or ""))
        if not items and h == "unspecified":
            continue
        head = _escape(label(h, lang).upper() if h in _DASHBOARD_HORIZONS else "UNSPECIFIED")
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
    on one page (G-G1). Reuses the already-escaped HTML-native builders, so the
    fragment is self-contained and carries no Mermaid runtime. Deterministic."""
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


# Scoped dashboard CSS — only the panel chrome; the embedded risk/competition
# fragments ship their own scoped <style>. Reuses the shared palette vars.
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


# ── Shared body-render substrate (export / board / explorer) ────────────────
#
# Body-bearing HTML outputs render artifact markdown bodies CLIENT-SIDE through
# the chokepoint  DOMPurify.sanitize(marked.parse(md))  (defined in
# _viewer-head.html as psRenderMarkdown). The server NEVER injects body HTML; it
# ships bodies as an inert JSON data island. Two enumerated sinks (red-team H3):
#   1. the embedded-JSON body channel  → escaped via embed_spec_data()
#   2. attribute-context values (data-*, aria-label, id) → built client-side via
#      safe DOM APIs (textContent / dataset) and/or _escape() for server tokens.
#      There is no href channel: bodies are sanitized by DOMPurify, metadata is
#      set via textContent/dataset — no renderer ever emits a spec-derived href.


# The sanitize chokepoint, shipped INSIDE the {{markdown_libs}} block (body views
# only) so legacy graph views inline no marked/DOMPurify code at all (H4). Always
# defined — when the libs are absent it FAILS CLOSED to escaped text, never a CDN.
_BODY_RENDER_JS = (
    "\nfunction psRenderMarkdown(md){"
    "if(window.marked&&window.DOMPurify){return window.DOMPurify.sanitize(window.marked.parse(String(md==null?'':md)));}"
    "return '<pre class=\"ps-fallback\">'+psEscapeHtml(md)+'</pre>';}"
    # Shared detail-panel controls for board + explorer. Defined HERE (body-view
    # only) — not in the shared head — because they call psRenderMarkdown, so the
    # 9 legacy graph views stay free of any sanitizer reference (H4 gating). Each
    # body shell registers its id->record map via psRegisterDetail(byId); inert in
    # the linear export (it has no #ps-detail). Body is the only innerHTML sink.
    "\nvar psDetailById={},psDetailCache={};"
    "\nfunction psRegisterDetail(byId){psDetailById=byId||{};}"
    "\nwindow.psOpenDetail=function(id){var c=psDetailById[id];if(!c){return;}"
    "var t=document.getElementById('ps-detail-title'),b=document.getElementById('ps-detail-body'),d=document.getElementById('ps-detail');"
    "if(!t||!b||!d){return;}"
    "t.textContent=c.id+(c.title?' \\u2014 '+c.title:'');"
    # Memoize the sanitized body per id (immutable) so re-opening the same card
    # does not re-tokenize + re-sanitize — matches the table-tree dataset.loaded guard.
    "b.innerHTML=(psDetailCache[id]||(psDetailCache[id]=psRenderMarkdown(c.body||'_(no body)_')));d.hidden=false;};"
    "\nwindow.psCloseDetail=function(){var d=document.getElementById('ps-detail');if(d){d.hidden=true;}};"
    "\ndocument.addEventListener('keydown',function(e){if(e.key==='Escape'){psCloseDetail();}});"
    # Shared facet/search engine for board + explorer (body views only). Pure,
    # parameterized helpers so both shells share ONE implementation: each shell
    # owns its records array + state shape (board has no mode; explorer adds one)
    # + its render callback; the filter machinery below is identical. Hoisting it
    # here (mirroring psRegisterDetail) closes the board/explorer divergence risk
    # the detail-panel comment calls out. psBuildFacets localizes the Layer-facet
    # chip values (L[v]) so a --lang vi facet matches the Flat-tabs tab labels.
    "\nvar psFacetGroups=['status','moscow','horizon','persona','layer'];"
    "\nfunction psDistinct(records,group){var seen={};records.forEach(function(c){var v=group==='persona'?c.personas:[c[group]];(v||[]).forEach(function(x){if(x){seen[x]=true;}});});return Object.keys(seen).sort();}"
    # `state.facets[g]||{}` guards let the engine tolerate a shell that hasn't
    # pre-declared every psFacetGroups bucket (the group LIST is the single source
    # of truth; a missing bucket no longer throws on first paint). psBuildFacets
    # seeds the bucket for each group it renders.
    "\nfunction psFacetActive(state,g){return Object.keys(state.facets[g]||{}).length>0;}"
    "\nfunction psSelfMatch(state,c){if(state.q){var hay=(c.id+' '+c.title+' '+(c.body||'')).toLowerCase();if(hay.indexOf(state.q)===-1){return false;}}for(var i=0;i<psFacetGroups.length;i++){var g=psFacetGroups[i];if(!psFacetActive(state,g)){continue;}var vals=g==='persona'?(c.personas||[]):[c[g]];if(!vals.some(function(v){return (state.facets[g]||{})[v];})){return false;}}return true;}"
    "\nfunction psBadge(text,cls){var s=document.createElement('span');s.className='badge '+cls;s.textContent=text;return s;}"
    # Shared card-badge emitter (type/status/moscow/persona, in order) — board cards
    # and explorer nodes both call it so the badge set stays identical across viewers.
    "\nfunction psMetaBadges(c,el){if(c.type){el.appendChild(psBadge(c.type,'badge--type'));}if(c.status){el.appendChild(psBadge(c.status,'badge--status'));}if(c.moscow){el.appendChild(psBadge(c.moscow,'badge--moscow'));}(c.personas||[]).forEach(function(p){el.appendChild(psBadge(p,'badge--persona'));});}"
    # Shared search-input wiring (placeholder + lowercased query → onChange) so both
    # shells wire the #ps-search box identically; pass the localized label + the
    # shell's render callback.
    "\nfunction psWireSearch(state,onChange,label){var s=document.getElementById('ps-search');if(!s){return;}s.placeholder=label||'Search…';s.addEventListener('input',function(){state.q=this.value.toLowerCase();onChange();});}"
    "\nfunction psBuildFacets(records,labels,state,onChange){var host=document.getElementById('ps-facets');if(!host){return;}var L=labels||{};psFacetGroups.forEach(function(g){var vals=psDistinct(records,g);if(!vals.length){return;}state.facets[g]=state.facets[g]||{};var lab=document.createElement('span');lab.className='badge badge--type';lab.textContent=(L[g]||g)+':';host.appendChild(lab);vals.forEach(function(v){var b=document.createElement('button');b.type='button';b.textContent=(L[v]||v);b.setAttribute('aria-pressed','false');b.addEventListener('click',function(){if(state.facets[g][v]){delete state.facets[g][v];b.setAttribute('aria-pressed','false');}else{state.facets[g][v]=true;b.setAttribute('aria-pressed','true');}onChange();});host.appendChild(b);});});}"
)


def _load_vendored_markdown_libs() -> Optional[str]:
    """Return the inlined marked + DOMPurify payload, or None if either is
    missing. Escapes the `</script` close-tag hazard at inline time so the
    vendored files stay byte-identical to the CDN originals (hash-pin intact)."""
    if not (VENDOR_MARKED.exists() and VENDOR_PURIFY.exists()):
        return None
    marked_js = VENDOR_MARKED.read_text(encoding="utf-8")
    purify_js = VENDOR_PURIFY.read_text(encoding="utf-8")
    payload = purify_js + "\n" + marked_js
    # The only HTML hazard for inline <script> content is the literal substring
    # `</script` (case-insensitive). A blanket `</`→`<\/` would corrupt minified
    # comparisons like `a</b/`, so escape only the actual close-tag token.
    return re.sub(r"</(script)", r"<\\/\1", payload, flags=re.IGNORECASE)


def viewer_head() -> str:
    """The shared design-system head partial (one source for every HTML output)."""
    return VIEWER_HEAD_PARTIAL.read_text(encoding="utf-8")


def embed_spec_data(payload: Any) -> str:
    """Serialize `payload` into an inert JSON data island.

    Every literal `<` is rewritten to its JSON `\\u003c` escape. This neutralizes
    ALL three script-data hazards at once — `</script>` (breakout), `<script` and
    the `<!--` comment primer (which together drive the WHATWG script-data-double-
    escaped state, where the island's own `</script>` no longer closes the tag and
    the page-bootstrap script is swallowed → a blank render from valid PO prose).
    `\\u003c` round-trips through JSON.parse straight back to `<`, so the rendered
    body is unchanged; only the raw transport is neutered. (HTML entities like
    `&#x3c;` would NOT work here: a <script> element's text is not entity-decoded,
    so the body would show the literal `&#x3c;`.)"""
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")
    return f'<script type="application/json" id="ps-spec-data">{blob}</script>'


def file_timestamp() -> str:
    """Compact UTC stamp (`%Y%m%dT%H%M%SZ`, no colons) for output filenames — one
    source for every writer (export / board / explorer / the 9 graph views). The
    colon-bearing ISO body stamp is `spec_graph._now`; this is its filename twin."""
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def product_name(graph: Dict[str, Any]) -> str:
    """The product display name, or `(unnamed)` — one source for every renderer."""
    return (graph.get("product") or {}).get("name") or "(unnamed)"


def chrome_values(graph: Dict[str, Any], lang: str, title: str) -> Dict[str, str]:
    """The body-shell token preamble shared by export / board / explorer:
    `lang_attr`, escaped `title`, escaped `product_name`, `generated_at`. Pairs
    with body_render_values() (which supplies viewer_head/markdown_libs/spec_data)."""
    return {
        "lang_attr": lang,
        "title": _escape(title),
        "product_name": _escape(product_name(graph)),
        "generated_at": _now(),
    }


def assemble_body_shell(shell: str, payload: Any, graph: Dict[str, Any],
                        lang: str, title: str) -> str:
    """Assemble one body-bearing shell: body-render substrate + chrome preamble →
    single-pass substitute. Collapses the `read → values → update → substitute`
    plumbing that board/explorer (and export) otherwise copy-paste verbatim."""
    values = body_render_values(payload)
    values.update(chrome_values(graph, lang, title))
    return substitute(shell, values)


def markdown_libs_banner() -> str:
    """A visible fail-closed banner shown when the sanitizer libs are absent."""
    return (
        '<div class="ps-banner">Markdown libraries not vendored — bodies shown as '
        'plain text. Run <code>install.sh</code> to enable rich rendering '
        '(offline, no CDN).</div>'
    )


def body_render_values(spec_payload: Any) -> Dict[str, str]:
    """The shared token set every body-bearing shell interpolates:
    `viewer_head` (design system), `markdown_libs` (sanitizer or ""),
    `libs_banner` (fail-closed notice or ""), `spec_data` (inert JSON island)."""
    libs = _load_vendored_markdown_libs()
    return {
        "viewer_head": viewer_head(),
        # libs (or "" when fail-closed) + the always-present sanitize chokepoint.
        "markdown_libs": (libs or "") + _BODY_RENDER_JS,
        "libs_banner": "" if libs is not None else markdown_libs_banner(),
        "spec_data": embed_spec_data(spec_payload),
    }


def assemble(
    view: str,
    view_format: str,
    view_text: str,
    graph: Dict[str, Any],
    lang: str = "en",
) -> str:
    """Build the full HTML page string."""
    shell = SHELL_PATH.read_text(encoding="utf-8")
    title = f"{view.title()} View"

    # The `time` view (TIME dimension) builds its own body from the graph when no
    # body text is supplied: a CYCLE-SAFE Mermaid gantt + depends_on annotations
    # (render_mermaid.time uses a visited-set walk, so a circular depends_on chain
    # terminates instead of hanging this renderer — trade-off T1 / G-D3). Imported
    # lazily: render_mermaid imports render_ascii, neither imports render_html, so
    # there is no import cycle, but the lazy import keeps module-load order simple.
    if view == "time" and not view_text:
        import render_mermaid
        view_text = render_mermaid.time(graph, lang=lang)
        view_format = "mermaid"
    generated_at = _now()
    footer = (
        "Self-contained HTML. To re-render: "
        "python3 visualize.py --view "
        f"{view} --format html --root &lt;dir&gt;"
    )
    if not VENDOR_MERMAID.exists():
        footer = (
            '<strong style="color:#c33">Note:</strong> vendored mermaid.min.js '
            "missing; CDN fallback in use. Run install.sh to vendor it.<br>"
            + footer
        )
    # INVARIANT: footer_note is injected into the HTML template WITHOUT further
    # escaping (it may contain renderer-literal markup such as <strong>).
    # Any spec-derived value added to footer_note in the future MUST be passed
    # through _escape() before interpolation — never interpolated raw.

    # ASCII-fallback views (view_format != "mermaid") render as plain <pre>;
    # the Mermaid runtime is never used, so skipping it saves ~2.5 MB and the
    # cost of an unnecessary `mermaid.initialize()` scan on every page load.
    mermaid_js_payload = _load_mermaid_js() if view_format == "mermaid" else ""

    values = {
        "lang": lang,
        "title": title,
        "generated_at": generated_at,
        "product_name": _escape(product_name(graph)),
        "view": view,
        "view_body": _render_view_body(view_format, view_text),
        "mermaid_js": mermaid_js_payload,
        "footer_note": footer,
        # Phase 6: the 9 legacy views adopt the shared design-system head too, so
        # ALL product-spec HTML (legacy + board/explorer/export) looks identical.
        # EXTEND-only: every prior token + the RAW-footer_note invariant are
        # preserved; legacy views still inline NO SKILL sanitizer — no bodies, so
        # no {{markdown_libs}} block and no psRenderMarkdown chokepoint (H4). NB the
        # mermaid-format payload bundles Mermaid's OWN internal DOMPurify for SVG
        # sanitization; that third-party copy is not a body-render sink and is
        # exempt from H4 — the contract is "no skill body-sanitizer", not "no
        # vendor lib named DOMPurify".
        "viewer_head": viewer_head(),
    }
    return substitute(shell, values)


def substitute(shell: str, values: Dict[str, str]) -> str:
    """Single-pass `{{token}}` substitution.

    A multi-pass `for k,v: shell.replace(...)` re-scans already-inserted content
    on every later key, so a spec-derived value of `"{{mermaid_js}}"` would
    inject the whole Mermaid payload, and a body containing `{{footer_note}}`
    would bleed the footer. A single `re.sub` pass expands each `{{token}}`
    exactly once and never re-scans the inserted value, closing that injection /
    bleed sink (shared by the 9 legacy views and every body-bearing shell).
    Unknown tokens are left verbatim so partial shells fail loudly, not silently.
    """
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), shell)


def _write_visual(root: Path, filename: str, html: str) -> Path:
    """Write a self-contained visual to docs/product/visuals/<filename>. One home for
    the out_dir + mkdir + write_text + return that the 9 graph views and the board /
    explorer writers otherwise copy verbatim."""
    out_dir = root / "docs" / "product" / "visuals"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / filename
    target.write_text(html, encoding="utf-8")
    return target


def write(
    root: Path,
    view: str,
    view_format: str,
    view_text: str,
    graph: Dict[str, Any],
    lang: str = "en",
) -> Path:
    """Write the assembled HTML to docs/product/visuals/<view>-<ts>.html."""
    return _write_visual(root, f"{view}-{file_timestamp()}.html",
                         assemble(view, view_format, view_text, graph, lang))
