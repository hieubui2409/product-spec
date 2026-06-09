#!/usr/bin/env python3
"""assemble_audit_trail — the governance audit view (`--viz audit`).

A read-only chronological join of data the skill ALREADY captures — change-log, approval
metadata, stale approvals, decision register — into one table: *when · artifact · action ·
who-approved · what-drifted · DEC*. Deterministic struct here; the LLM only narrates.

DRY: reuses `status.build_status` for the stale-approval + baseline facts rather than re-reading
snapshots, and `decision_register.parse_decisions` for the DEC rows.

Source-disagreement rule: the four sources have NO referential integrity. When an approval or
a stale-approval flag has NO corroborating change-log entry or DEC, the row is emitted as an explicit
``unreconciled`` event — never silently dropped. An audit that hides an inconsistency is worse than none.

This module assembles the data + renders ASCII / markdown only. The HTML fragment lives in
`render_html.audit`, which escapes every dynamic field server-side (no injection channel here).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from decision_register import parse_decisions
from record_outcome import parse_outcomes
from encoding_utils import configure_utf8_console
from spec_graph import build_graph_with_artifacts
from status import build_status

configure_utf8_console()

# Bilingual column labels (the audit view's own small label set; i18n_labels owns the viz facets).
_AUDIT_LABELS = {
    "en": {"when": "When", "artifact": "Artifact", "action": "Action", "who": "Who approved",
           "drift": "What drifted", "dec": "DEC", "title": "Audit Trail", "empty": "No audit events yet.",
           "unreconciled": "unreconciled"},
    "vi": {"when": "Thời điểm", "artifact": "Tài liệu", "action": "Hành động", "who": "Người duyệt",
           "drift": "Thay đổi", "dec": "DEC", "title": "Nhật ký kiểm toán", "empty": "Chưa có sự kiện kiểm toán.",
           "unreconciled": "chưa đối soát"},
}

_CL_HEADING_RE = re.compile(r"^##\s+(?P<date>\d{4}-\d{2}-\d{2})\s+—\s+(?P<type>.+?)\s*$", re.MULTILINE)
_CL_ARTIFACT_RE = re.compile(r"\*\*Artifact[^:]*:\*\*\s*(?P<ids>.+)$", re.MULTILINE)
_CL_ACTION_RE = re.compile(r"\*\*Action[^:]*:\*\*\s*(?P<action>.+)$", re.MULTILINE)
_CL_DIMS_RE = re.compile(r"\*\*Dimensions[^:]*:\*\*\s*(?P<dims>.+)$", re.MULTILINE)
_ID_RE = re.compile(r"\b([A-Z][A-Z0-9-]*(?:-E\d+)?(?:-S\d+)?|VISION|PRODUCT|BRD(?:-G\d+)?)\b")


def _parse_change_log(root: Path) -> List[Dict[str, Any]]:
    path = root / "docs" / "product" / "change-log.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return []
    entries: List[Dict[str, Any]] = []
    matches = list(_CL_HEADING_RE.finditer(text))
    for i, m in enumerate(matches):
        block = text[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        ids_m = _CL_ARTIFACT_RE.search(block)
        ids = _ID_RE.findall(ids_m.group("ids")) if ids_m else []
        action_m = _CL_ACTION_RE.search(block)
        dims_m = _CL_DIMS_RE.search(block)
        entries.append({
            "date": m.group("date"),
            "type": m.group("type").split("|")[0].strip(),
            "artifacts": [i for i in ids if i],
            "action": action_m.group("action").split("|")[0].strip() if action_m else "",
            "dims": dims_m.group("dims").split("|")[0].strip() if dims_m else "",
        })
    return entries


def _approvals(root: Path) -> List[Dict[str, Any]]:
    _graph, artifacts = build_graph_with_artifacts(root)
    out: List[Dict[str, Any]] = []
    for art in artifacts:
        fm = art.get("frontmatter") or {}
        approval = fm.get("approval")
        if isinstance(approval, dict) and (approval.get("approved_by") or approval.get("approved_at")):
            out.append({
                "artifact": str(fm.get("id") or "").strip(),
                "approved_by": str(approval.get("approved_by") or "").strip(),
                "approved_at": str(approval.get("approved_at") or "").strip(),
            })
    return out


def assemble(root, today: Optional[str] = None) -> Dict[str, Any]:
    root = Path(root).resolve()
    change_log = _parse_change_log(root)
    approvals = _approvals(root)
    decisions = parse_decisions(root)
    status = build_status(root, today=today)
    stale = set(status.get("stale_approvals", []))

    # Artifacts mentioned by a change-log entry or a DEC `affects` → "corroborated".
    corroborated = set()
    for e in change_log:
        corroborated.update(e["artifacts"])
    dec_by_artifact: Dict[str, List[str]] = {}
    for d in decisions:
        aff = (d.get("affects") or "").strip()
        if aff:
            corroborated.add(aff)
            dec_by_artifact.setdefault(aff, []).append(d["id"])

    events: List[Dict[str, Any]] = []

    for e in change_log:
        for aid in (e["artifacts"] or [""]):
            events.append({
                "date": e["date"], "artifact": aid, "action": e["action"] or e["type"],
                "who_approved": "", "what_drifted": e["dims"],
                "dec_ref": ",".join(dec_by_artifact.get(aid, [])), "reconciled": True,
            })

    for a in approvals:
        aid = a["artifact"]
        is_stale = aid in stale
        reconciled = (aid in corroborated)
        events.append({
            "date": a["approved_at"], "artifact": aid,
            "action": "approved" + (" (stale)" if is_stale else ""),
            "who_approved": a["approved_by"],
            "what_drifted": "approval predates current wording" if is_stale else "",
            "dec_ref": ",".join(dec_by_artifact.get(aid, [])),
            # Corroboration (a change-log entry or a DEC affecting this artifact) is the sole
            # criterion — an approval/stale flag with NONE is unreconciled, never dropped.
            "reconciled": reconciled,
        })

    for d in decisions:
        events.append({
            "date": d.get("date", ""), "artifact": (d.get("affects") or "").strip(),
            "action": f"decision ({d.get('status','active')})", "who_approved": "",
            "what_drifted": d.get("title", ""), "dec_ref": d["id"], "reconciled": True,
        })

    # Outcome measurements (the --learn quantitative loop) map into the SAME six event
    # keys — NO new columns, NO schema bump (red-team #3): the artifact is the measured
    # goal, the action carries the verdict, what_drifted carries target/actual/metric.
    # With no outcomes.md this loop adds nothing → the audit trail is byte-identical to
    # before (back-compat). The learning-map view consumes these outcome rows as its
    # source nodes (it keeps them, not filters them out).
    for o in parse_outcomes(root):
        gid = str(o.get("goal") or "").strip()
        events.append({
            "date": str(o.get("measured_on") or ""), "artifact": gid,
            "action": f"outcome: {o.get('verdict')}", "who_approved": "",
            "what_drifted": f"target {o.get('target')} / actual {o.get('actual')} ({o.get('metric')})",
            "dec_ref": ",".join(dec_by_artifact.get(gid, [])), "reconciled": True,
        })

    events.sort(key=lambda ev: (ev["date"] or "", ev["artifact"], ev["dec_ref"]))
    return {"schema_version": "1.0", "root": str(root), "events": events,
            "unreconciled_count": sum(1 for e in events if not e["reconciled"])}


# --------------------------------------------------------------------------- renderers (ASCII + md)

def _rows(data: Dict[str, Any], lang: str):
    lab = _AUDIT_LABELS.get(lang, _AUDIT_LABELS["en"])
    header = [lab["when"], lab["artifact"], lab["action"], lab["who"], lab["drift"], lab["dec"]]
    rows = []
    for e in data["events"]:
        action = e["action"]
        if not e["reconciled"]:
            action = f"{action} [{lab['unreconciled']}]"
        rows.append([e["date"] or "-", e["artifact"] or "-", action or "-",
                     e["who_approved"] or "-", e["what_drifted"] or "-", e["dec_ref"] or "-"])
    return lab, header, rows


def render_ascii(data: Dict[str, Any], lang: str = "en") -> str:
    lab, header, rows = _rows(data, lang)
    if not rows:
        return f"{lab['title']}\n{lab['empty']}"
    cols = list(zip(header, *rows)) if rows else [(h,) for h in header]
    widths = [max(len(str(c)) for c in col) for col in cols]
    def fmt(r): return "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r))
    line = "  ".join("-" * w for w in widths)
    return "\n".join([lab["title"], "", fmt(header), line, *[fmt(r) for r in rows]])


def render_markdown(data: Dict[str, Any], lang: str = "en") -> str:
    lab, header, rows = _rows(data, lang)
    if not rows:
        return f"## {lab['title']}\n\n{lab['empty']}\n"
    out = [f"## {lab['title']}", "", "| " + " | ".join(header) + " |",
           "| " + " | ".join("---" for _ in header) + " |"]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def since_last_approved(root, today: Optional[str] = None) -> Dict[str, Any]:
    """The `--summary --audience release-notes` delta: audit events on/after the most
    recent approval date. Reuses `assemble` (DRY) — same source-of-truth as the audit view.
    Returns {since, events}. `since` is None when nothing is approved yet (→ all events)."""
    data = assemble(root, today=today)
    approval_dates = [e["date"] for e in data["events"]
                      if e["action"].startswith("approved") and e["date"]]
    since = max(approval_dates) if approval_dates else None
    events = [e for e in data["events"] if not since or (e["date"] and e["date"] >= since)]
    return {"since": since, "events": events}


def render_release_delta_md(delta: Dict[str, Any], lang: str = "en") -> str:
    """Bullet list of since-last-approved events for the release-notes `{{changes_since_approved}}`
    token. Plain markdown bullets — fills the value path; the template render does the rest."""
    lab = _AUDIT_LABELS.get(lang, _AUDIT_LABELS["en"])
    if not delta["events"]:
        return lab["empty"]
    lines = []
    for e in delta["events"]:
        bits = [e["date"] or "-", e["artifact"] or "-", e["action"] or "-"]
        if e["dec_ref"]:
            bits.append(f"({e['dec_ref']})")
        lines.append("- " + " · ".join(bits))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Assemble + render the governance audit trail.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--format", default="ascii", choices=["ascii", "md", "json"])
    ap.add_argument("--lang", default="en", choices=["en", "vi"])
    ap.add_argument("--today", default=None)
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    data = assemble(root, today=args.today)
    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.format == "md":
        print(render_markdown(data, args.lang))
    else:
        print(render_ascii(data, args.lang))
    return 0


if __name__ == "__main__":
    sys.exit(main())
