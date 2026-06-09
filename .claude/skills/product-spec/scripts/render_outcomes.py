#!/usr/bin/env python3
"""
render_outcomes — ASCII + HTML renderers for the `--learn` outcome views
(scorecard / insight-gap / outcome-trend). Kept in its own module (rather than
swelling render_html's 1k lines) so the NEW dynamic-field surface is isolated and
auditable — every spec-derived value is escaped server-side through render_html's
shared `_escape` chokepoint (viz was a historical XSS sink), fail-closed to text.

Consumes the `load_outcomes` card model; renders nothing it did not escape.
"""

from typing import Any, Dict, List

from i18n_labels import label
from load_outcomes import VERDICT_RANK
from render_html import _escape

_HTML_BADGE = {"hit": "ro-hit", "partial": "ro-partial", "miss": "ro-miss"}
_ASCII_BADGE = {"hit": "[+]", "partial": "[~]", "miss": "[-]"}


# ── shared helpers ───────────────────────────────────────────────────────────

def _trend_symbol(card: Dict[str, Any]) -> str:
    """Verdict direction vs the previous measurement (▲ better / ▼ worse / ▬ same)."""
    latest, prev = card.get("latest"), card.get("prev")
    if not latest or not prev:
        return ""
    cur = VERDICT_RANK.get(str(latest.get("verdict")), 1)
    old = VERDICT_RANK.get(str(prev.get("verdict")), 1)
    return "▲" if cur > old else ("▼" if cur < old else "▬")


def _verdict_word(verdict: str, lang: str) -> str:
    return label(f"verdict_{verdict}", lang) if verdict in VERDICT_RANK else str(verdict)


# ── ASCII ────────────────────────────────────────────────────────────────────

def scorecard(data: Dict[str, Any], lang: str = "en") -> str:
    cards = data.get("cards", [])
    if not cards:
        return label("no_outcomes", lang)
    out = [label("scorecard", lang).upper(), ""]
    for c in cards:
        gid = str(c["goal_id"])
        if c["blind_spot"]:
            out.append(f"  {gid:<14} ({label('unmeasured', lang)}) — {label('blind_spot', lang)}")
            continue
        latest = c["latest"]
        metric = str(c.get("metric") or "")
        verdict = str(latest.get("verdict"))
        badge = _ASCII_BADGE.get(verdict, "[?]")
        unit = str(latest.get("unit") or "")
        tail = f"({label('goal_removed', lang)}) " if c["orphan"] else ""
        out.append(
            f"  {gid:<14} {metric:<18} {label('target', lang)} {latest.get('target')} / "
            f"{label('actual', lang)} {latest.get('actual')} {unit}".rstrip()
            + f"  {badge} {_verdict_word(verdict, lang)} {_trend_symbol(c)} {tail}".rstrip()
        )
    return "\n".join(out)


def insight_gap(data: Dict[str, Any], lang: str = "en") -> str:
    ranked = sorted([c for c in data.get("cards", []) if c.get("gap") is not None],
                    key=lambda c: c["gap"], reverse=True)
    if not ranked:
        return label("no_outcomes", lang)
    out = [f"{label('insight_gap', lang).upper()} ({label('gap', lang)} ↓)", ""]
    for c in ranked:
        gap = c["gap"]
        filled = max(1, min(20, round(gap * 20)))
        bar = "█" * filled + "░" * (20 - filled)
        out.append(f"  {str(c['goal_id']):<14} {str(c.get('metric') or ''):<18} "
                   f"{bar} {gap * 100:.0f}%")
    return "\n".join(out)


def outcome_trend(data: Dict[str, Any], lang: str = "en") -> str:
    rows, periods = _trend_matrix(data)
    if not rows or not periods:
        return label("no_outcomes", lang)
    head = "  " + " " * 22 + " ".join(f"{p[5:]:>8}" for p in periods)  # MM-DD column heads
    out = [label("outcome_trend", lang).upper(), "", head]
    for row_label, cells in rows:
        line = f"  {row_label:<22}" + " ".join(
            f"{(_ASCII_BADGE.get(v, ' · ') if v else ' · '):>8}" for v in cells)
        out.append(line)
    return "\n".join(out)


def _trend_matrix(data: Dict[str, Any]):
    """rows = [(goal·metric label, [verdict|None per period]), …]; periods sorted."""
    periods: List[str] = data.get("periods", [])
    rows = []
    for c in data.get("cards", []):
        if c["blind_spot"]:
            continue
        by_date: Dict[str, str] = {}
        for o in c.get("history", []):
            by_date[str(o.get("measured_on") or "")] = str(o.get("verdict"))
        cells = [by_date.get(p) for p in periods]
        rows.append((f"{c['goal_id']} {c.get('metric') or ''}".strip(), cells))
    return rows, periods


# ── HTML (every dynamic field escaped via _escape) ───────────────────────────

_OUTCOME_CSS = (
    "<style>"
    ".ro-table{border-collapse:collapse;width:100%;max-width:52rem;}"
    ".ro-table th,.ro-table td{border:1px solid var(--border);padding:.45rem .6rem;text-align:left;}"
    ".ro-table thead th{background:var(--recessed);color:var(--muted);font-weight:600;font-size:.85rem;}"
    ".ro-badge{font-weight:600;border-radius:.3rem;padding:.1rem .45rem;font-size:.8rem;}"
    ".ro-hit{background:var(--teal-dim);}.ro-partial{background:#7a5b00;color:#fff;}"
    ".ro-miss{background:#7a1f1f;color:#fff;}.ro-blind{color:var(--muted);font-style:italic;}"
    ".ro-bar{height:.8rem;background:var(--teal-dim);border-radius:.2rem;display:inline-block;vertical-align:middle;}"
    ".ro-bartrack{background:var(--recessed);border-radius:.2rem;display:inline-block;width:14rem;vertical-align:middle;}"
    "</style>"
)


def _badge_html(verdict: str, lang: str) -> str:
    cls = _HTML_BADGE.get(verdict, "")
    return f'<span class="ro-badge {cls}">{_escape(_verdict_word(verdict, lang))}</span>'


def scorecard_html(data: Dict[str, Any], lang: str = "en") -> str:
    cards = data.get("cards", [])
    if not cards:
        return _OUTCOME_CSS + f'<p class="ps-meta">{_escape(label("no_outcomes", lang))}</p>'
    head = (f"<tr><th>{_escape(label('goal', lang))}</th><th>{_escape(label('metrics', lang))}</th>"
            f"<th>{_escape(label('target', lang))}</th><th>{_escape(label('actual', lang))}</th>"
            f"<th>{_escape(label('verdict', lang))}</th><th>{_escape(label('trend', lang))}</th></tr>")
    body = []
    for c in cards:
        gid = _escape(str(c["goal_id"]))
        if c["blind_spot"]:
            body.append(f'<tr><td>{gid}</td><td colspan="5" class="ro-blind">'
                        f'{_escape(label("blind_spot", lang))} — {_escape(label("unmeasured", lang))}</td></tr>')
            continue
        latest = c["latest"]
        verdict = str(latest.get("verdict"))
        unit = _escape(str(latest.get("unit") or ""))
        metric = _escape(str(c.get("metric") or ""))
        if c["orphan"]:
            metric += f' <span class="ro-blind">({_escape(label("goal_removed", lang))})</span>'
        body.append(
            f"<tr><td>{gid}</td><td>{metric}</td>"
            f"<td>{_escape(str(latest.get('target')))} {unit}</td>"
            f"<td>{_escape(str(latest.get('actual')))} {unit}</td>"
            f"<td>{_badge_html(verdict, lang)}</td><td>{_escape(_trend_symbol(c))}</td></tr>")
    return (_OUTCOME_CSS + '<table class="ro-table"><thead>' + head
            + "</thead><tbody>" + "".join(body) + "</tbody></table>")


def insight_gap_html(data: Dict[str, Any], lang: str = "en") -> str:
    ranked = sorted([c for c in data.get("cards", []) if c.get("gap") is not None],
                    key=lambda c: c["gap"], reverse=True)
    if not ranked:
        return _OUTCOME_CSS + f'<p class="ps-meta">{_escape(label("no_outcomes", lang))}</p>'
    rows = []
    for c in ranked:
        pct = c["gap"] * 100
        width = max(2, min(100, round(c["gap"] * 100)))
        bar = f'<span class="ro-bartrack"><span class="ro-bar" style="width:{width}%"></span></span>'
        rows.append(f"<tr><td>{_escape(str(c['goal_id']))}</td><td>{_escape(str(c.get('metric') or ''))}</td>"
                    f"<td>{bar} {pct:.0f}%</td></tr>")
    head = (f"<tr><th>{_escape(label('goal', lang))}</th><th>{_escape(label('metrics', lang))}</th>"
            f"<th>{_escape(label('gap', lang))}</th></tr>")
    return (_OUTCOME_CSS + '<table class="ro-table"><thead>' + head
            + "</thead><tbody>" + "".join(rows) + "</tbody></table>")


def outcome_trend_html(data: Dict[str, Any], lang: str = "en") -> str:
    rows, periods = _trend_matrix(data)
    if not rows or not periods:
        return _OUTCOME_CSS + f'<p class="ps-meta">{_escape(label("no_outcomes", lang))}</p>'
    head = "".join(f"<th scope='col'>{_escape(p)}</th>" for p in periods)
    body = []
    for row_label, cells in rows:
        tds = []
        for v in cells:
            if v in VERDICT_RANK:
                tds.append(f'<td class="ro-badge {_HTML_BADGE.get(v, "")}">{_escape(_verdict_word(v, lang))}</td>')
            else:
                tds.append('<td class="ro-blind">·</td>')
        body.append(f"<tr><th scope='row'>{_escape(row_label)}</th>{''.join(tds)}</tr>")
    return (_OUTCOME_CSS + '<table class="ro-table"><thead>'
            f"<tr><th scope='col'>{_escape(label('goal', lang))}</th>{head}</tr>"
            "</thead><tbody>" + "".join(body) + "</tbody></table>")
