#!/usr/bin/env python3
"""
session_staleness — reconcile `docs/product/.session.md` against the spec's own
edit clock and the Decision Register.

`.session.md` is BOTH a legitimate resume source AND an authorised assume-source:
GATE-NEVER-ASSUME lets the skill assume a value the PO already gave in `.session.md`.
That dual role is the hazard. A session frozen at date D keeps asserting facts that
artifacts edited after D — or decisions ruled after D — have since moved past, so a
new session that assumes from a stale `.session.md` can silently reverse an approved
fact. This module is the deterministic detector behind the staleness guard.

SCRIPT-vs-LLM split (CLAUDE.md): it owns NO prose judgment. It compares committed
DATES only and lists candidates; the LLM/PO judges whether a session line actually
contradicts a ruling. Two signals:

  - staleness: `.session.md` `updated` < the newest artifact `updated`. The session
    predates a spec edit, so its facts may be stale.
  - supersede candidates: active DEC records dated AFTER `.session.md` `updated` —
    rulings the session snapshot could not have reflected. Per Q5, decisions.md is
    the authority when the two diverge; the session is NEVER auto-rewritten — the
    conflict is surfaced (no-silent-reversal).

Fail-soft everywhere: an absent `.session.md`, an absent/unparseable `updated`, or an
empty register all yield "nothing to flag", never a crash. All findings are `warn`
(an advisory nudge, never a hard gate).

CLI:
    session_staleness.py --root <project-dir>
        Prints the sweep JSON {session_updated, stale, newest_artifact,
        superseding_decisions, authoritative_source}. Always exits 0.
"""

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from encoding_utils import configure_utf8_console, emit_json
from spec_graph import build_graph
from check_consistency_time import parse_iso_date
from decision_register import list_active

configure_utf8_console()

# decisions.md is the authority when a session line and a ruling diverge (Q5). Named
# once here so the sweep payload and the validate-gate finding speak with one voice.
AUTHORITATIVE_SOURCE = "decisions.md"


def _session_path(root: Path) -> Path:
    return Path(root) / "docs" / "product" / ".session.md"


def parse_session_updated(root: Path) -> Optional[dt.date]:
    """Return the `.session.md` frontmatter `updated` as a date, or None.

    None when the file is absent/unreadable, has no YAML frontmatter, or carries an
    absent/unparseable `updated`. Best-effort: a malformed session never crashes the
    detector (the staleness nudge degrades to silence)."""
    path = _session_path(root)
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(fm, dict):
        return None
    return parse_iso_date(str(fm.get("updated"))) if fm.get("updated") is not None else None


def newest_artifact_update(graph: Dict[str, Any]) -> Tuple[Optional[dt.date], Optional[str]]:
    """The latest `updated` date across all artifacts → (date, artifact_id).

    Nodes with an absent/unparseable `updated` are skipped. Returns (None, None) when
    no artifact carries a parseable date."""
    best: Optional[dt.date] = None
    best_id: Optional[str] = None
    for n in graph.get("nodes", []):
        raw = n.get("updated")
        if raw is None:
            continue
        d = parse_iso_date(str(raw))
        if d is None:
            continue
        if best is None or d > best:
            best, best_id = d, n.get("id")
    return best, best_id


def superseding_decisions(root: Path, session_updated: Optional[dt.date]) -> List[Dict[str, Any]]:
    """Active DEC records dated strictly AFTER the session snapshot.

    These are rulings the session could not have reflected — supersede candidates the
    PO/LLM must check the session against. Empty when the session date is unknown (no
    anchor to compare against) or the register is empty. Sorted by id for determinism."""
    if session_updated is None:
        return []
    out: List[Dict[str, Any]] = []
    for rec in list_active(root):
        d = parse_iso_date(rec.get("date"))
        if d is None or d <= session_updated:
            continue
        out.append({
            "id": rec["id"],
            "date": rec.get("date", ""),
            "title": rec.get("title", ""),
            "affects": rec.get("affects", ""),
        })
    out.sort(key=lambda r: r["id"])
    return out


def sweep(root) -> Dict[str, Any]:
    """The full session↔(spec, register) reconciliation for `root`.

    The deterministic payload behind the `--status`/supersede-sweep surface. Builds the
    graph internally so the CLI is standalone. `stale` is True iff the session predates
    the newest artifact edit; `superseding_decisions` lists post-session rulings."""
    root = Path(root).resolve()
    session_updated = parse_session_updated(root)
    graph = build_graph(root)
    newest, newest_id = newest_artifact_update(graph)

    stale = bool(session_updated and newest and session_updated < newest)
    return {
        "session_updated": session_updated.isoformat() if session_updated else None,
        "stale": stale,
        "newest_artifact": (
            {"id": newest_id, "updated": newest.isoformat()} if newest else None
        ),
        "superseding_decisions": superseding_decisions(root, session_updated),
        "authoritative_source": AUTHORITATIVE_SOURCE,
    }


def staleness_findings(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate-gate `warn` findings for a stale / superseded session.

    Reads the project root from `graph["root_path"]` (same contract as the other
    session check). Emits at most two findings — one `session_stale` (session predates
    the newest artifact edit) and one `session_superseded` (post-session rulings the
    session may contradict) — so a long register never floods the gate. Returns [] when
    there is no root, no session date, or nothing to flag."""
    root_raw = graph.get("root_path")
    if not root_raw:
        return []
    root = Path(root_raw)
    session_updated = parse_session_updated(root)
    if session_updated is None:
        return []

    findings: List[Dict[str, Any]] = []
    newest, newest_id = newest_artifact_update(graph)
    if newest and session_updated < newest:
        findings.append({
            "check": "session_stale",
            "severity": "warn",
            "artifact_id": None,
            "file": "docs/product/.session.md",
            "detail": (
                f".session.md updated {session_updated.isoformat()} predates the newest "
                f"artifact edit ({newest_id} updated {newest.isoformat()}); its facts may "
                f"be stale — re-read before assuming from it."
            ),
            "context": {
                "session_updated": session_updated.isoformat(),
                "newest_artifact": newest_id,
                "newest_updated": newest.isoformat(),
            },
        })

    supersed = superseding_decisions(root, session_updated)
    if supersed:
        ids = ", ".join(d["id"] for d in supersed)
        findings.append({
            "check": "session_superseded",
            "severity": "warn",
            "artifact_id": None,
            "file": "docs/product/.session.md",
            "detail": (
                f".session.md (updated {session_updated.isoformat()}) predates "
                f"{len(supersed)} decision(s) [{ids}]; {AUTHORITATIVE_SOURCE} is "
                f"authoritative — verify the session does not contradict them."
            ),
            "context": {
                "authoritative_source": AUTHORITATIVE_SOURCE,
                "decisions": supersed,
            },
        })
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    emit_json({"schema_version": "1.0", **sweep(args.root)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
