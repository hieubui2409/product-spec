#!/usr/bin/env python3
"""parse_critique_report — deterministic struct half of `--apply-critique`.

The critique return-edge consumes a product-spec-critique report and walks each finding
with the PO (Keep / Change+re-approve / Defer), recording rulings in the Decision Register.
This script does ONLY the deterministic, testable work; the LLM owns the per-finding
interview + prose judgment (see references/workflow-apply-critique.md).

What it does:
  1. READ-FENCE the report path: resolve + contain under `<root>/docs/product/critique/`.
     `fs_guard` is write-only, so we reuse its `_is_within` for the read side. Traversal /
     symlink-escape is refused with a friendly error — no raw read of arbitrary paths.
  2. Resolve findings from the STRUCTURED lens-cache, NOT the humanized prose. The report
     frontmatter carries `lens_findings_hash` → `docs/product/.memory/critique-lens-cache/<hash>.json`
     (a verbatim list of `{lens,evidence,critique,fix,severity,why_it_dies}`). Prose is bilingual +
     repeats IDs, so regex over it is unreliable. Prose fallback only when the cache is absent.
  3. Emit a deterministic per-finding FINGERPRINT = sha8(lens + artifact_id + normalized critique) —
     the stable key for dedup, resume, and DEC cross-reference (findings have no native id).
  4. FRESHNESS with None-handling: compare the artifact's current CONTENT fingerprint (body +
     acceptance_criteria, see spec_graph.content_hash) against the critique-time per-node map in the
     report frontmatter (wire-name `body_hash`, kept for back-compat but content-based). An AC-only
     edit now reads as `stale` (body_hash alone missed frontmatter AC). If the report predates this
     tracking (map absent or None for the artifact) → `freshness: "unknown"` so the loop WARNS
     ("re-critique or proceed without staleness check") rather than silently skipping.

Output: JSON to stdout, exit 0 (analytical-script contract — a bad input surfaces as a finding,
never a bare traceback).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from encoding_utils import configure_utf8_console
from fs_guard import _is_within
from spec_graph import build_graph

configure_utf8_console()


class ReportFenceError(Exception):
    """Raised when the report path escapes docs/product/critique/."""


def assert_under_critique(report_path, root) -> Path:
    """Return the resolved report path if contained under `<root>/docs/product/critique/`,
    else raise ReportFenceError. Resolve-then-contain (collapses `..`, follows symlinks)."""
    root = Path(root).resolve()
    fence = (root / "docs" / "product" / "critique").resolve()
    target = Path(report_path)
    if not target.is_absolute():
        target = root / target
    resolved = target.resolve(strict=False)
    if resolved != fence and not _is_within(resolved, fence):
        raise ReportFenceError(
            f"refusing to read a critique report outside the boundary: {resolved} is not "
            f"under {fence}. --apply-critique only reads docs/product/critique/."
        )
    return resolved


def _frontmatter(text: str) -> Dict[str, Any]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _normalize(s: str) -> str:
    """Lowercase + collapse whitespace — stabilizes the fingerprint against trivial
    re-wording/reflow of the same critique text."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def fingerprint(lens: str, artifact_id: str, critique: str) -> str:
    """sha8 stable key. \\x1f field separator avoids accidental boundary collisions."""
    raw = "\x1f".join((lens or "", artifact_id or "", _normalize(critique)))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8]


def _artifact_id_from_evidence(evidence: str) -> str:
    """`evidence` is `ID:line` (e.g. `BRD:62`, `PRD-CHAT-E1-S1:12`). Take the ID before
    the first colon. Bare/blank evidence → "" (freshness becomes 'unknown')."""
    ev = (evidence or "").strip()
    return ev.split(":", 1)[0].strip() if ev else ""


def _lens_cache_path(root: Path, lens_findings_hash: str) -> Path:
    return root / "docs" / "product" / ".memory" / "critique-lens-cache" / f"{lens_findings_hash}.json"


def _load_lens_findings(root: Path, lens_findings_hash: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    if not lens_findings_hash:
        return None
    path = _lens_cache_path(root, str(lens_findings_hash))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, list) else None


# --- prose fallback: recover findings from the report markdown when the lens-cache
#     is absent (a report written before script-enforced persistence). Best-effort and
#     LOSSY (no why/fix), but enough to drive the apply loop instead of `findings: 0`.
_SEVERITY_TOKENS = {
    "blocker": "blocker", "chặn": "blocker",
    "major": "major", "nặng": "major",
    "minor": "minor", "nhẹ": "minor",
}
_LENS_TOKENS = {
    "product": "product", "sản phẩm": "product",
    "tech": "tech", "feasibility": "tech", "kỹ thuật": "tech",
    "market": "market", "thị trường": "market",
    "craft": "craft", "editorial": "craft", "biên tập": "craft",
}
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_HEAD_RE = re.compile(r"^#{2,4}\s+(.+?)\s*$")
_BRACKET_RE = re.compile(r"\[([^\]]+)\](?:\s*\[([^\]]+)\])?")
_EVIDENCE_RE = re.compile(r"([A-Za-z][A-Za-z0-9_-]*:\d+)")


def _canon_from(tok: Optional[str], table: Dict[str, str]) -> str:
    """First recognized token (split on ·,/ and whitespace) mapped via `table`, else ''."""
    if not tok:
        return ""
    low = tok.strip().lower()
    for part in re.split(r"[·,/\s]+", low):
        if part in table:
            return table[part]
    for key, val in table.items():  # substring fallback (e.g. a multi-word section head)
        if key in low:
            return val
    return ""


def _prose_findings(text: str, critique_time: Dict[str, Any],
                    current: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
    """Parse `**[severity][lens] <id>:<line>**` finding markers from the report prose.
    Lens comes from the inline 2nd bracket (Top-3 form) or the enclosing `### <Lens>`
    section. Deduped by (lens, evidence) so a Top-3 item and its per-lens echo collapse.
    why/fix are unavailable in prose → left empty; each row is tagged
    `source: prose-fallback` so the apply loop knows it is best-effort."""
    findings: List[Dict[str, Any]] = []
    seen: set = set()
    cur_lens = ""
    for line in text.splitlines():
        head = _HEAD_RE.match(line)
        if head:
            lens = _canon_from(head.group(1), _LENS_TOKENS)
            if lens:
                cur_lens = lens
            continue
        spans = list(_BOLD_RE.finditer(line))
        for idx, match in enumerate(spans):
            span = match.group(1)
            bracket = _BRACKET_RE.search(span)
            if not bracket:
                continue
            severity = _canon_from(bracket.group(1), _SEVERITY_TOKENS)
            if not severity:
                continue
            ev = _EVIDENCE_RE.search(span)
            if not ev:
                continue
            evidence = ev.group(1)
            lens = _canon_from(bracket.group(2), _LENS_TOKENS) or cur_lens
            key = (lens, evidence)
            if key in seen:
                continue
            seen.add(key)
            aid = _artifact_id_from_evidence(evidence)
            # critique = prose AFTER this marker up to the next marker (or line end), so a
            # line carrying two markers never smears the first marker's text onto the second
            nxt = spans[idx + 1].start() if idx + 1 < len(spans) else len(line)
            critique = line[match.end():nxt].strip(" .:)-")
            findings.append({
                "fingerprint": fingerprint(lens, aid, critique or evidence),
                "lens": lens,
                "artifact_id": aid,
                "evidence": evidence,
                "severity": severity,
                "critique": critique,
                "why_it_dies": "",
                "fix": "",
                "freshness": _freshness(aid, critique_time, current),
                "source": "prose-fallback",
            })
    return findings


def _current_content_hashes(root: Path) -> Dict[str, Optional[str]]:
    """Per-node CONTENT fingerprint (body + acceptance_criteria) of the live spec — the
    freshness comparison base. Keyed to spec_graph.content_hash so an AC-only edit on a
    critiqued artifact reads as `stale`, not silently `fresh` (body_hash alone could not
    see frontmatter AC). The report frontmatter's per-node map (wire-name `body_hash`,
    kept for back-compat) carries these same content fingerprints."""
    graph = build_graph(root)
    out: Dict[str, Optional[str]] = {}
    for node in graph.get("nodes", []):
        nid = node.get("id")
        if nid:
            out[nid] = node.get("content_hash")
    return out


def _freshness(artifact_id: str, critique_time: Dict[str, Any], current: Dict[str, Optional[str]]) -> str:
    """fresh | stale | unknown | artifact-missing. `unknown` = report predates freshness
    tracking (no per-node body_hash at critique time) → loop WARNS, never silently skips."""
    if not artifact_id:
        return "unknown"
    at_critique = critique_time.get(artifact_id) if isinstance(critique_time, dict) else None
    if at_critique in (None, "", "None"):
        return "unknown"
    if artifact_id not in current:
        return "artifact-missing"
    now = current.get(artifact_id)
    if now in (None, ""):
        return "unknown"
    return "fresh" if str(now) == str(at_critique) else "stale"


_PLACEHOLDER_APPROVERS = {"", "tbd", "todo", "<owner>", "owner", "none", "n/a", "na", "pending"}


def reapproval_ok(approved_by: Optional[str], approved_at: Optional[str], dec_date: str):
    """Deterministic GATE-NO-SILENT-REVERSAL guard for a Change on an `approved` artifact.

    A Change ruling may only be written when a FRESH re-approval exists:
      * `approved_by` is a real, non-placeholder owner, AND
      * `approved_at` is on/after the decision date (`dec_date`) — i.e. the PO re-approved
        AFTER deciding to change, not a stale pre-existing approval.

    Returns (ok: bool, reason: str). The loop calls this BEFORE recording a Change DEC; the
    bypass test asserts that a missing/placeholder owner or a stale date returns ok=False —
    the gate cannot be forged by LLM honor alone."""
    by = (approved_by or "").strip().lower()
    if by in _PLACEHOLDER_APPROVERS:
        return False, "re-approval owner is missing or a placeholder — GATE requires a real approver"
    at = (approved_at or "").strip()
    if not at:
        return False, "re-approval date is missing — GATE requires approved_at >= the decision date"
    try:
        from datetime import date
        if date.fromisoformat(at[:10]) < date.fromisoformat(str(dec_date)[:10]):
            return False, f"re-approval {at} predates the decision {dec_date} — stale approval cannot satisfy the GATE"
    except (TypeError, ValueError):
        return False, f"re-approval date {at!r} is not an ISO date"
    return True, "fresh re-approval"


def parse_report(report_path, root) -> Dict[str, Any]:
    root = Path(root).resolve()
    resolved = assert_under_critique(report_path, root)
    text = resolved.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    lens_findings_hash = fm.get("lens_findings_hash")
    critique_time_hashes = fm.get("body_hash") or {}

    raw_findings = _load_lens_findings(root, lens_findings_hash)
    cache_present = raw_findings is not None
    current = _current_content_hashes(root)

    findings: List[Dict[str, Any]] = []
    prose_fallback = False
    if cache_present:
        for f in raw_findings:
            if not isinstance(f, dict):
                continue
            lens = str(f.get("lens", "")).strip()
            evidence = str(f.get("evidence", "")).strip()
            critique = str(f.get("critique", ""))
            artifact_id = _artifact_id_from_evidence(evidence)
            findings.append({
                "fingerprint": fingerprint(lens, artifact_id, critique),
                "lens": lens,
                "artifact_id": artifact_id,
                "evidence": evidence,
                "severity": str(f.get("severity", "")).strip(),
                "critique": critique,
                "why_it_dies": str(f.get("why_it_dies", "")),
                "fix": str(f.get("fix", "")),
                "freshness": _freshness(artifact_id, critique_time_hashes, current),
            })
    else:
        # No lens-cache (report written before script-enforced persistence) → recover
        # what we can from the report prose so the apply loop gets findings, not zero.
        findings = _prose_findings(text, critique_time_hashes, current)
        prose_fallback = bool(findings)

    return {
        "report": str(resolved.relative_to(root)) if _is_within(resolved, root) else str(resolved),
        "lang": fm.get("lang"),
        "level": fm.get("level"),
        "critique_scope": fm.get("critique_scope"),
        "lens_findings_hash": lens_findings_hash,
        "cache_present": cache_present,
        "prose_fallback": prose_fallback,
        "freshness_trackable": bool(critique_time_hashes),
        "findings": findings,
        "note": (
            "" if cache_present else
            "lens-cache absent — findings recovered from the report prose (best-effort, no "
            "why/fix); re-run the critique with --fresh to regenerate the structured cache."
            if prose_fallback else
            "lens-cache absent and no findings could be parsed from the prose; re-run the "
            "critique with --fresh to regenerate the cache."
        ),
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Parse a critique report into fingerprinted, freshness-tagged findings.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--report", required=True, help="path to a critique report under docs/product/critique/")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        result = parse_report(args.report, root)
    except ReportFenceError as exc:
        print(json.dumps({"error": "path_fence", "message": str(exc), "findings": []}, ensure_ascii=False))
        return 0
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"error": "read_failed", "message": str(exc), "findings": []}, ensure_ascii=False))
        return 0
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
