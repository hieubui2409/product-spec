#!/usr/bin/env python3
"""
render_learning — the Phase-5 `--learn` learning views: the `learning-map` flow
(outcome→goal→`DEC-<n>`, built over the audit trail) + the `learning` HTML-only
dashboard. Split from render_outcomes (the Phase-4 scorecard/gap/trend views) along
the feature seam so each module stays a single concern + under the LOC guideline.

The dashboard reuses render_outcomes' already-escaped fragments (DRY, no new
injection channel); the map sanitizes labels via render_mermaid's mermaid-injection
chokepoint and ids via its whitelist.
"""

from typing import Any, Dict, List

from i18n_labels import label
from render_html import _escape
from render_outcomes import scorecard_html, insight_gap_html, outcome_trend_html


def _learning_edges(audit: Dict[str, Any]):
    """From the audit trail (DRY — assemble_audit_trail), pull the two edge sets the
    learning map draws: outcome→goal and goal→DEC. Outcome/decision events are tagged
    by their `action` prefix in assemble()."""
    events = audit.get("events", [])
    outcomes = [e for e in events if str(e.get("action", "")).startswith("outcome:")]
    decisions = [e for e in events if str(e.get("action", "")).startswith("decision")]
    return outcomes, decisions


def learning_map_mermaid(audit: Dict[str, Any], lang: str = "en") -> str:
    """Mermaid flowchart: each measured outcome → its goal node → any DEC affecting it.
    Labels sanitized via render_mermaid._safe_label (mermaid-injection safe)."""
    from render_mermaid import _fence, _safe_label, _safe_id
    outcomes, decisions = _learning_edges(audit)
    lines = ["flowchart LR"]
    goal_nodes: Dict[str, str] = {}

    def gnode(gid: str) -> str:
        nid = "G_" + _safe_id(gid or "none")
        if gid not in goal_nodes:
            goal_nodes[gid] = nid
            lines.append(f'  {nid}["{_safe_label(gid or "(none)")}"]')
        return nid

    for i, e in enumerate(outcomes):
        oid = f"O{i}"
        olabel = _safe_label(f"{e.get('date', '')} · {e.get('action', '')}")
        lines.append(f'  {oid}["{olabel}"]')
        lines.append(f"  {oid} --> {gnode(str(e.get('artifact') or ''))}")
    for e in decisions:
        gid = str(e.get("artifact") or "")
        ref = str(e.get("dec_ref") or "")
        if not gid or not ref:
            continue
        did = "D_" + _safe_id(ref)
        dlabel = _safe_label(f"{ref}: {e.get('what_drifted', '')}")
        lines.append(f'  {did}["{dlabel}"]')
        lines.append(f"  {gnode(gid)} --> {did}")
    if len(lines) == 1:
        lines.append(f'  empty["{_safe_label(label("no_outcomes", lang))}"]')
    return _fence("\n".join(lines))


def learning_map_ascii(audit: Dict[str, Any], lang: str = "en") -> str:
    """Text-summary downgrade of the learning map (the ascii path for a flow view)."""
    outcomes, decisions = _learning_edges(audit)
    if not outcomes and not decisions:
        return label("no_outcomes", lang)
    dec_by_goal: Dict[str, List[str]] = {}
    for e in decisions:
        if e.get("artifact") and e.get("dec_ref"):
            dec_by_goal.setdefault(str(e["artifact"]), []).append(str(e["dec_ref"]))
    out = [label("learning_map", lang).upper(), ""]
    for e in outcomes:
        gid = str(e.get("artifact") or "")
        decs = ", ".join(dec_by_goal.get(gid, [])) or "—"
        out.append(f"  {e.get('date','')}  {e.get('action','')}  →  {gid}  →  DEC: {decs}")
    return "\n".join(out)


_LEARNING_CSS = (
    "<style>.lo-panel{margin:0 0 2rem;}"
    ".lo-title{font-size:1.1rem;margin:0 0 .75rem;padding-bottom:.3rem;border-bottom:1px solid var(--border);}"
    ".lo-link{color:var(--muted);font-style:italic;}</style>"
)


def learning_dashboard_html(data: Dict[str, Any], lang: str = "en") -> str:
    """HTML-only one-page dashboard: scorecard + insight-gap + outcome-trend stacked,
    with a pointer to the (separately-rendered) learning-map flow. Reuses the already-
    escaped fragments, so it carries no new injection channel."""
    def panel(title_key: str, frag: str) -> str:
        return (f'<section class="lo-panel"><h2 class="lo-title">{_escape(label(title_key, lang))}</h2>'
                f"{frag}</section>")
    return (
        _LEARNING_CSS
        + panel("scorecard", scorecard_html(data, lang))
        + panel("insight_gap", insight_gap_html(data, lang))
        + panel("outcome_trend", outcome_trend_html(data, lang))
        + f'<p class="lo-link">→ {_escape(label("learning_map", lang))}: '
          f'<code>--viz learning-map</code></p>'
    )
