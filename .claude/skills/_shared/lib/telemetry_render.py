"""telemetry_render.py — the NEW gap over human-analyzer (which ships md/json/html):
ascii (terminal one-glance) + mermaid (fenced charts) renderers, plus md. md/json
reuse formatters.py. NO HTML (D4 — avoids vendored-asset / shipped-render coupling).
NO network, NO inlined JS, NO asset reads — pure text only.

Each renderer takes a LIST of lens aggregates (the "overview" composition) and
dispatches per `lens` key in a stable order. Below-gate lenses render a short
"insufficient data" note instead of recommendations. CM-local (NOT shipped).
"""
from __future__ import annotations

import re

from formatters import markdown_table

_GATE_NOTE = "_Insufficient data (chưa đủ dữ liệu) — raw counts only, no recommendations._"
_NEVER_USED_CAP = 20


def _fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def _mermaid_escape(label: str) -> str:
    """Make a label safe inside a mermaid quoted string: no double-quotes,
    newlines, or the `:`/`;` that break pie/bar syntax."""
    s = str(label).replace('"', "'").replace("\n", " ")
    s = re.sub(r"[:;#]", "-", s)
    return s.strip() or "?"


# --- markdown sections (one per lens) ---------------------------------------

def _md_usage(a, top):
    out = [f"## Skill Usage (last {a['days']} days)\n"]
    if a.get("gated"):
        out.append(_GATE_NOTE + "\n")
    out.append(f"Total invocations: **{a['total_invocations']}** across "
               f"**{a['skills_used']}** skill(s); catalog {a['catalog_size']}.\n")
    rows = [r for r in a["rows"] if r["count"] or r["tokens"]]
    if top:
        rows = rows[:top]
    headers = ["#", "Skill", "Count"]
    if a.get("with_tokens"):
        headers.append("Tokens")
    trows = []
    for i, r in enumerate(rows, 1):
        row = [str(i), r["skill"], str(r["count"])]
        if a.get("with_tokens"):
            row.append(_fmt_tokens(r["tokens"]))
        trows.append(row)
    out.append(markdown_table(headers, trows))
    nu = a["never_used"]
    out.append(f"\n**Never used (owned):** {len(nu)}")
    if nu:
        shown = nu[:_NEVER_USED_CAP]
        out.append(", ".join(shown) + (f" … (+{len(nu) - len(shown)} more)" if len(nu) > len(shown) else ""))
    ext = a.get("never_used_external_count")
    if ext:
        out.append(f"\n_(+{ext} vendored external skills also unused — expected, not prune candidates.)_")
    return "\n".join(out)


def _md_session(a):
    out = ["## Session Shape\n"]
    if a.get("gated"):
        out.append(_GATE_NOTE + "\n")
    out.append(markdown_table(
        ["Metric", "Value"],
        [["Sessions", str(a["sessions"])],
         ["Avg duration (s)", str(a["avg_duration_s"])],
         ["Median duration (s)", str(a["median_duration_s"])],
         ["Files modified (total)", str(a["files_modified_total"])],
         ["Subagents (total)", str(a["subagents_total"])]]))
    if a["top_cooccurrence"]:
        out += ["\n**Skill co-occurrence:**",
                markdown_table(["Pair", "Sessions"], [[p, str(n)] for p, n in a["top_cooccurrence"]])]
    return "\n".join(out)


def _md_health(a):
    out = ["## Script Health (approx)\n"]
    if a.get("gated"):
        out.append(_GATE_NOTE + "\n")
    out.append(f"Runs: **{a['total_runs']}**, errors: **{a['total_errors']}** "
               f"across {a['scripts']} script(s).\n")
    rows = [[r["script"], str(r["runs"]), str(r["errors"]), f"{r['error_rate']}%",
             "—" if r["avg_ms"] is None else f"{r['avg_ms']}ms"] for r in a["rows"]]
    out.append(markdown_table(["Script", "Runs", "Errors", "Err%", "Avg"], rows))
    return "\n".join(out)


def _md_reliability(a):
    out = [f"## Subagent Reliability (last {a['days']} days)\n"]
    if a.get("gated"):
        out.append(_GATE_NOTE + "\n")
    rows = [[r["agent_type"], str(r["total"]), f"{r['success_rate']}%",
             str(r["api_error"]), str(r["timeout"]), str(r["blocked"]), str(r["unknown"])]
            for r in a["rows"]]
    out.append(markdown_table(
        ["Agent Type", "Total", "Success", "API Err", "Timeout", "Blocked", "Unknown"], rows))
    if a["top_failure_modes"]:
        out.append("\n**Top failure modes:** " +
                   ", ".join(f"{m} ({n})" for m, n in a["top_failure_modes"]))
    return "\n".join(out)


def _md_workflow(a):
    out = [f"## Workflow Chains (last {a['days']} days, {a['sessions_analyzed']} sessions)\n"]
    if not a["sufficient"]:
        out.append(f"_Thin data: {a['sessions_analyzed']} < min {a['min_sessions']} sessions — "
                   "observed chains shown, deviation verdicts withheld._\n")
    if a["common_chains"]:
        out += ["**Most common chains:**",
                markdown_table(["Chain", "Count"], [[c["chain"], str(c["count"])] for c in a["common_chains"]])]
    else:
        out.append("_No multi-skill chains observed yet._")
    if a["sufficient"] and a["deviations"]:
        out += ["\n**Deviations from routing docs:**",
                markdown_table(["Chain", "Count"], [[d["chain"], str(d["count"])] for d in a["deviations"]])]
    out.append(f"\n**Declared chains in routing docs:** {len(a['declared_chains'])}")
    return "\n".join(out)


def _md_memory(a):
    out = [f"## Memory Health — {a['status']} ({a['count']} memories, {a['issue_count']} issues)\n",
           f"`{a['memory_dir']}` (read-only)\n"]

    def _sec(title, items):
        out.append(f"**{title}:** {len(items)}")
        if items:
            out.append("- " + "\n- ".join(items))

    _sec("Orphaned files", a["orphans"])
    _sec("Dead index entries", a["dead_entries"])
    _sec("Broken [[links]]", [f"{b['from']} → [[{b['to']}]]" for b in a["broken_links"]])
    _sec("Duplicate names", [f"{n}: {', '.join(fs)}" for n, fs in a["duplicates"].items()])
    # invalid_frontmatter counts toward issue_count → must show detail, else a RED
    # driven only by it would show a headline with no explanation.
    _sec("Invalid frontmatter", [
        f"{m['file']} (missing: {', '.join(m['missing']) or '—'}"
        + (f"; invalid type: {m['invalid_type']}" if m.get("invalid_type") else "") + ")"
        for m in a.get("invalid_frontmatter", [])])
    # stale is informational only (NOT in issue_count) — surface for context.
    _sec("Stale (informational)", [
        f"{m['file']} ({m['type']}, {m['age_days']}d)" for m in a.get("stale", [])])
    return "\n".join(out)


def _md_forensics(a):
    if a["count"] == 0:
        return "## Session Forensics\n\n_No session transcripts found._"
    rows = [[p["session"][:8], str(len(p["skills"])), str(p["tool_calls"]),
             str(p["subagents"]), _fmt_tokens(p["total_tokens"]),
             f"{p['duration_s'] // 60}m", str(len(p["files_modified"]))] for p in a["sessions"]]
    return (f"## Session Forensics ({a['count']} session(s), {_fmt_tokens(a['agg_total_tokens'])} tokens)\n\n"
            + markdown_table(["Session", "Skills", "Tools", "Subagents", "Tokens", "Dur", "Files"], rows))


def _md_validate(a):
    out = ["## Effectiveness Proxy — validate-pass (internal quality)\n"]
    if not a.get("available"):
        out.append(f"_{a.get('reason', 'not available on current data')}_")
        return "\n".join(out)
    if a.get("gated"):
        out.append(_GATE_NOTE + "\n")
    pr = a["validate_pass_rate"]
    pr_str = "n/a (no validate runs in window)" if pr is None else f"{pr}%"
    out.append(markdown_table(
        ["Metric", "Value"],
        [["Validate pass rate", pr_str],
         ["Last status", str(a["last_status"])],
         ["Runs", str(a["total"])],
         ["Source", str(a.get("source", "?"))]]))
    out.append("\n_Measures internal spec quality (validate passed) — NOT market/user "
               "outcome (E3, deferred)._")
    return "\n".join(out)


_MD = {
    "usage_tokens": lambda a, top: _md_usage(a, top),
    "session_shape": lambda a, top: _md_session(a),
    "health": lambda a, top: _md_health(a),
    "reliability": lambda a, top: _md_reliability(a),
    "workflow_chains": lambda a, top: _md_workflow(a),
    "memory_health": lambda a, top: _md_memory(a),
    "forensics": lambda a, top: _md_forensics(a),
    "validate_proxy": lambda a, top: _md_validate(a),
}


def render_md(aggregates: list[dict], top=None) -> str:
    parts = [_MD[a["lens"]](a, top) for a in aggregates if a.get("lens") in _MD]
    return "\n\n".join(parts) if parts else "_No lenses to render._"


# --- ascii (terminal one-glance) --------------------------------------------
# ascii reuses the markdown grids (they render fine in a monospace terminal) but
# leads each lens with a traffic-light status line for a quick scan.

def _light(ok: bool) -> str:
    return "[OK]" if ok else "[!]"


def render_ascii(aggregates: list[dict]) -> str:
    lines = ["== TELEMETRY: USAGE & HEALTH =="]
    for a in aggregates:
        lens = a.get("lens")
        if lens == "usage_tokens":
            ext = a.get("never_used_external_count", 0)
            ext_s = f" (+{ext} ext)" if ext else ""
            lines.append(f"\n{_light(not a.get('gated'))} USAGE — {a['total_invocations']} invocations, "
                         f"{a['skills_used']} used, {len(a['never_used'])} owned never-used{ext_s}")
        elif lens == "session_shape":
            lines.append(f"\n{_light(not a.get('gated'))} SESSIONS — {a['sessions']} sessions, "
                         f"avg {a['avg_duration_s']}s, {a['files_modified_total']} files, "
                         f"{a['subagents_total']} subagents")
        elif lens == "health":
            ok = a["total_errors"] == 0
            lines.append(f"\n{_light(ok)} HEALTH — {a['total_runs']} runs, {a['total_errors']} errors "
                         f"across {a['scripts']} scripts")
            for r in a["rows"][:10]:
                avg = "—" if r["avg_ms"] is None else f"{r['avg_ms']}ms"
                lines.append(f"   {_light(r['errors'] == 0)} {r['script']}  runs={r['runs']} "
                             f"err={r['errors']}({r['error_rate']}%) avg={avg}")
        elif lens == "reliability":
            lines.append(f"\n{_light(not a.get('gated'))} RELIABILITY — {a['total']} subagent runs")
            for r in a["rows"][:10]:
                lines.append(f"   {r['agent_type']}: {r['success_rate']}% ok "
                             f"(api={r['api_error']} timeout={r['timeout']} "
                             f"blocked={r['blocked']} unknown={r['unknown']})")
        elif lens == "workflow_chains":
            tag = _light(a["sufficient"])
            lines.append(f"\n{tag} WORKFLOW — {a['sessions_analyzed']} sessions, "
                         f"{len(a['common_chains'])} chains, {len(a['deviations'])} deviations")
        elif lens == "memory_health":
            lines.append(f"\n{_light(a['status'] == 'GREEN')} MEMORY — {a['status']}, "
                         f"{a['count']} memories, {a['issue_count']} issues "
                         f"(orphans={len(a['orphans'])} dead={len(a['dead_entries'])} "
                         f"broken={len(a['broken_links'])})")
        elif lens == "forensics":
            lines.append(f"\n[i] FORENSICS — {a['count']} session(s), "
                         f"{_fmt_tokens(a['agg_total_tokens'])} tokens")
        elif lens == "validate_proxy":
            if a.get("available"):
                pr = a["validate_pass_rate"]
                pr_str = "n/a" if pr is None else f"{pr}% pass"
                lines.append(f"\n{_light(not a.get('gated'))} VALIDATE-PROXY — "
                             f"{pr_str} (last: {a['last_status']}) [internal quality, not E3]")
            else:
                lines.append(f"\n[i] VALIDATE-PROXY — {a.get('reason', 'unavailable')}")
    return "\n".join(lines)


# --- mermaid (fenced charts; only chart-friendly lenses) --------------------

def _mermaid_pie(title: str, items: list[tuple]) -> str:
    rows = [f'    "{_mermaid_escape(k)}" : {v}' for k, v in items if v]
    if not rows:
        return ""
    return "```mermaid\npie showData\n    title " + _mermaid_escape(title) + "\n" + "\n".join(rows) + "\n```"


def _mermaid_bar(title: str, items: list[tuple]) -> str:
    """xychart-beta bar; falls back cleanly when empty."""
    items = [(k, v) for k, v in items]
    if not items:
        return ""
    labels = ", ".join(f'"{_mermaid_escape(k)}"' for k, _ in items)
    vals = ", ".join(str(v) for _, v in items)
    return ("```mermaid\nxychart-beta\n    title \"" + _mermaid_escape(title) + "\"\n"
            f"    x-axis [{labels}]\n    bar [{vals}]\n```")


def render_mermaid(aggregates: list[dict]) -> str:
    blocks = []
    for a in aggregates:
        lens = a.get("lens")
        if lens == "usage_tokens":
            if a.get("gated"):
                blocks.append("> Skill usage: insufficient data for a chart (chưa đủ dữ liệu).")
                continue
            items = [(r["skill"], r["count"]) for r in a["rows"] if r["count"]]
            blk = _mermaid_pie("Skill usage", items)
            if blk:
                blocks.append(blk)
        elif lens == "health":
            items = [(r["script"].split("/")[-1], r["error_rate"]) for r in a["rows"]]
            blk = _mermaid_bar("Script error-rate (%)", items)
            if blk:
                blocks.append(blk)
        elif lens == "reliability":
            if a.get("gated"):
                blocks.append("> Subagent reliability: insufficient data for a chart (chưa đủ dữ liệu).")
                continue
            items = [(r["agent_type"], r["success_rate"]) for r in a["rows"]]
            blk = _mermaid_bar("Subagent success-rate (%)", items)
            if blk:
                blocks.append(blk)
    return "\n\n".join(blocks) if blocks else "> No chart-friendly data yet."


# overview is just the ordered composition the CLI already passes in.
def render_overview(aggregates: list[dict], fmt: str = "md", top=None) -> str:
    if fmt == "ascii":
        return render_ascii(aggregates)
    if fmt == "mermaid":
        return render_mermaid(aggregates)
    return render_md(aggregates, top=top)
