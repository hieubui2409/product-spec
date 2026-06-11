#!/usr/bin/env python3
"""critique_persist.py — ONE deterministic write of every reuse cache a critique run
produces, plus a --doctor reconciliation.

The workflow's step-6 persistence used to be three separate LLM-remembered Python calls
(lens-cache + findings-index + critique-state). When the agent skipped any of them — most
often the lens-cache — the NEXT `--apply-critique` parsed `findings: 0` and the
critique-state stayed stuck on an earlier pass. `persist_critique_outputs` collapses the
three writes into one call so they happen together, never half-done by an LLM that forgot
a step. `doctor` then diagnoses the exact failure (state says a report/hash exists, but the
file on disk does not)."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import critique_cache
import critique_inherit
from critique_provenance import _report_exists, record_critique_state


def _report_ts(report: Optional[str]) -> str:
    """The findings-index / repeat-offense key timestamp. Mirrors _prior_reports: the
    report filename's leading `<ts>-...` segment; a UTC stamp when there is no report."""
    if report:
        ts = Path(report).stem.partition("-")[0]
        if ts:
            return ts
    return critique_cache._now()


def persist_critique_outputs(root, scope: str, level: int, lang: str,
                             lens_findings: List[Dict[str, Any]], blocker_count: int,
                             register: Optional[Dict[str, str]] = None,
                             report: Optional[str] = None,
                             now_iso: Optional[str] = None) -> Dict[str, Any]:
    """Write lens-cache + findings-index + critique-state in one shot. Returns a record
    of what was written (incl. the `lens_findings_hash` the report frontmatter must
    carry). Idempotent: re-persisting the same array re-puts the same hash file
    harmlessly. An empty/garbage `lens_findings` writes no lens-cache (nothing to key)
    but STILL records critique-state so the next run's fast-path is anchored."""
    findings = lens_findings if isinstance(lens_findings, list) else []
    lh = critique_cache._lens_findings_hash(findings) if findings else None

    wrote_lens_cache = False
    if lh is not None:
        critique_cache.put_lens_findings(root, lh, findings)
        wrote_lens_cache = True

    ts = _report_ts(report)
    critique_inherit.index_report_findings(root, ts, scope, findings)

    record_critique_state(root, scope, level, lang, lh, blocker_count,
                          register=register, report=report, now_iso=now_iso)

    return {
        "lens_findings_hash": lh,
        "wrote_lens_cache": wrote_lens_cache,
        "indexed_findings": len(findings),
        "report_ts": ts,
        "scope": scope,
    }


def doctor(root) -> Dict[str, Any]:
    """Reconcile critique-state against the critique/ dir + lens-cache. For each scope in
    critique-state: does its `report` still exist? does its `lens_findings_hash` resolve to
    a cache file? Plus: reports on disk with no state entry. This surfaces the precise
    failure mode — a state record whose lens-cache was never written (a future
    `consolidate_only` would silently downgrade to a full re-lens)."""
    root = Path(root)
    state = critique_cache.load_state(root)
    crit_dir = root / "docs" / "product" / "critique"

    issues: List[str] = []
    scopes_out: List[Dict[str, Any]] = []
    tracked_reports: set = set()

    for scope, rec in state.items():
        if not isinstance(rec, dict):
            continue
        report = rec.get("report")
        if report:
            tracked_reports.add(report)
        report_exists = _report_exists(root, report)
        lh = rec.get("lens_findings_hash")
        lens_cache_exists = bool(lh) and critique_cache.get_lens_findings(root, lh) is not None
        scopes_out.append({
            "scope": scope,
            "report": report,
            "report_exists": report_exists,
            "lens_findings_hash": lh,
            "lens_cache_exists": lens_cache_exists,
        })
        if report and not report_exists:
            issues.append(f"scope {scope}: state.report {report} is missing on disk")
        if lh and not lens_cache_exists:
            issues.append(
                f"scope {scope}: lens_findings_hash {lh} has no cache file "
                "(a future consolidate_only would downgrade to a full re-lens)")

    on_disk = sorted(p.name for p in crit_dir.glob("*.md")) if crit_dir.is_dir() else []
    untracked = [n for n in on_disk if not any(Path(r).name == n for r in tracked_reports)]

    return {
        "ok": not issues,
        "scopes": scopes_out,
        "reports_on_disk": on_disk,
        "reports_not_in_state": untracked,
        "issues": issues,
    }
