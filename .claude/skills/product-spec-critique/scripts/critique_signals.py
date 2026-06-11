#!/usr/bin/env python3
"""critique_signals.py — the read-only signal gatherers emit_bundle composes.

Each function pulls ONE existing signal into the bundle (line-numbered source files,
fresh structural findings, the ancestry frame, cached LLM verdicts). No LLM, no
judgment — assembly only. Split out of critique_bundle, which imports these."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from critique_common import _node_index


def _numbered_source(root: Path, rel_file: str) -> Optional[str]:
    """Read a source artifact file and return it with 1-based line-number prefixes
    (`<n>: <text>`), so a lens agent cites a real `ID:line` that resolves in the PO's
    own file. Returns None if the file is unreadable."""
    try:
        text = (root / "docs" / "product" / rel_file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return "\n".join(f"{i}: {ln}" for i, ln in enumerate(text.splitlines(), 1))


def _source_files(root: Path, graph: Dict[str, Any],
                  include_ids: Optional[Set[str]] = None) -> Dict[str, str]:
    """Map artifact IDs to their file's line-numbered content (`<n>: <text>`).

    Keyed by ARTIFACT ID (the citation prefix itself) so the lens cites `<id>:<line>`
    without path-vs-id ambiguity. Nodes sharing a file each get their own ID key; the
    BRD container (file None) falls back to its goals' file. Per-file reads cached.

    `include_ids` scopes the map: when given, only those ids (the scope target ∪
    ancestry ∪ digest) ship — so a narrow `--scope PRD-X` critique does not pack the
    WHOLE corpus into every lens prompt (×4 cost) just to cite one subtree. `None` =>
    every artifact (scope=='all'). The literal `"BRD"` fallback key rides along whenever
    it (or any goal id) is in scope."""
    nodes = graph.get("nodes", [])
    goal_file = next((n.get("file") for n in nodes
                      if n.get("type") == "goal" and n.get("file")), None)
    cache: Dict[str, Optional[str]] = {}
    out: Dict[str, str] = {}

    def _numbered_cached(rel: str) -> Optional[str]:
        if rel not in cache:
            cache[rel] = _numbered_source(root, rel)
        return cache[rel]

    for n in nodes:
        nid = n.get("id")
        rel = n.get("file")
        if not nid or not rel:
            continue
        if include_ids is not None and nid not in include_ids:
            continue
        numbered = _numbered_cached(rel)
        if numbered is not None:
            out[nid] = numbered

    if goal_file and "BRD" not in out and (include_ids is None or "BRD" in include_ids):
        numbered = _numbered_cached(goal_file)
        if numbered is not None:
            out["BRD"] = numbered
    return out


def _run_check(psp: Path, script: str, root: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Run a check_*.py checker as a subprocess and return (findings, error)."""
    path = psp / script
    if not path.is_file():
        return [], f"{script} not found at {path}"
    try:
        proc = subprocess.run(
            [sys.executable, str(path), "--root", str(root)],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [], f"{script} failed to run: {exc}"
    if proc.returncode != 0:
        return [], f"{script} exited {proc.returncode}: {proc.stderr.strip()[:300]}"
    try:
        data = json.loads(proc.stdout)
    except (json.JSONDecodeError, ValueError) as exc:
        return [], f"{script} emitted non-JSON: {exc}"
    findings = data.get("findings")
    return (findings if isinstance(findings, list) else []), None


def _structural_findings(psp: Path, root: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Fresh structural findings from both checkers, merged. Errors collected."""
    findings: List[Dict[str, Any]] = []
    errors: List[str] = []
    for script in ("check_traceability.py", "check_consistency.py"):
        f, err = _run_check(psp, script, root)
        findings.extend(f)
        if err:
            errors.append(err)
    return findings, errors


def _build_ancestry(spec_graph, graph: Dict[str, Any], digest: List[Dict[str, Any]],
                    scope: str) -> Dict[str, Any]:
    """The explicit ancestry frame: vision + brd_goals + prd + epic. Reuses the
    digest entries (full content already assembled) so we never re-serialize bodies."""
    entries_by_id = {e["id"]: e for e in digest}
    nodes_by_id = _node_index(graph)
    vision = next((e for e in digest if e.get("type") == "vision"), None)

    if scope == "all":
        goal_ids = [n["id"] for n in graph.get("nodes", []) if n.get("type") == "goal"]
        return {
            "vision": vision,
            "brd_goals": [entries_by_id.get(g) or nodes_by_id.get(g) for g in goal_ids],
            "prd": None,
            "epic": None,
        }

    anc_ids = spec_graph.ancestors(graph, scope) if scope in nodes_by_id else set()
    goal_ids = sorted(i for i in anc_ids if nodes_by_id.get(i, {}).get("type") == "goal")
    prd_id = next((i for i in sorted(anc_ids) if nodes_by_id.get(i, {}).get("type") == "prd"), None)
    epic_id = next((i for i in sorted(anc_ids) if nodes_by_id.get(i, {}).get("type") == "epic"), None)
    return {
        "vision": vision,
        "brd_goals": [entries_by_id.get(g) or nodes_by_id.get(g) for g in goal_ids],
        "prd": entries_by_id.get(prd_id) or nodes_by_id.get(prd_id),
        "epic": entries_by_id.get(epic_id) or nodes_by_id.get(epic_id),
    }


def _cached_verdicts(judgment_cache, root: Path, scope: str,
                     target_ids: List[str]) -> List[Dict[str, Any]]:
    """Cached LLM verdicts filtered to the scope. None cache -> []. The cache key is
    `check|scope_key|body_hash|lang|dep_hash`; an entry is in-scope when scope=='all'
    or any of its ids is a target."""
    cache = judgment_cache.load_cache(root)
    if not cache:
        return []
    entries = cache.get("entries")
    if not isinstance(entries, dict):
        return []
    target_set = set(target_ids)
    out: List[Dict[str, Any]] = []
    for key, entry in entries.items():
        parts = str(key).split("|")
        check = parts[0] if parts else ""
        scope_key = parts[1] if len(parts) > 1 else ""
        key_ids = set(scope_key.split("+")) if scope_key else set()
        if scope != "all" and not (key_ids & target_set):
            continue
        rec = {"key": key, "check": check}
        if isinstance(entry, dict):
            rec.update({k: v for k, v in entry.items()})
        else:
            rec["verdict"] = entry
        out.append(rec)
    out.sort(key=lambda r: r["key"])
    return out
