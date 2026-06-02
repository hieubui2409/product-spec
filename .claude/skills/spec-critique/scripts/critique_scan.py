#!/usr/bin/env python3
"""critique_scan.py — deterministic bundle assembler for cleanmatic:spec-critique.

Reuse-first, NO LLM, NO re-analysis. It assembles ONE JSON bundle the lens agents
consume, and manages the `last_critique.json` body_hash snapshot. It NEVER judges
quality — that is the lens agents' job. It only gathers existing signals:

  * resolved scope target(s) + descendants
  * ancestry chain (story -> epic -> PRD -> goal -> vision) as judgment context
  * structural findings (check_traceability + check_consistency, run FRESH)
  * cached LLM verdicts (judgment_cache, may be empty if never validated)
  * assembled artifact digest (assemble_digest, incl. vision/PRODUCT/BRD singletons)
  * source_files: each artifact file line-numbered (the `ID:line` citation ground-truth)
  * BRD competitors:
  * prior critique report list (repeat-offense ammo)
  * the drift threshold (preferences)

Modes (exactly one is active):
  (default)                emit the bundle JSON to stdout
  --snapshot               write last_critique.json (per-node body_hash) via fs_guard
  --drift                  count body_hash changes vs last_critique.json (live build)
  --drift --vs-validated   compare validate-time hashes (from judgments.json keys)
                           vs last_critique.json — cheap, no live build unless the
                           cache is absent. This is the Stop-hook path.

ALWAYS exits 0 (advisory). Malformed input degrades to a `parse_errors` field /
sentinel result, never a crash.

Cross-dir import: this script lives in `.claude/skills/spec-critique/scripts/`, a
DIFFERENT dir than the product-spec scripts it reuses, so bare sibling imports
fail. `_psp_dir()` resolves `../../product-spec/scripts` relative to __file__ and
`sys.path.insert`s it (loud error if absent). The `check_*` checkers are run as a
SUBPROCESS (stable CLI) to avoid pulling their transitive import chain into this
process; only the pure helpers are imported.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BUNDLE_VERSION = 2  # v2 adds source_files (line-numbered) + per-entry source_file
DEFAULT_THRESHOLD = 3

# Body-hash sentinels the cache key uses for an absent/bodyless node. They are not
# real content fingerprints, so drift must never count them as a change.
_HASH_SENTINELS = frozenset({"none", "missing"})


# ---------------------------------------------------------------------------
# Cross-dir resolution + import of the reused product-spec helpers
# ---------------------------------------------------------------------------

def _psp_dir() -> Path:
    """The product-spec `scripts/` dir, resolved relative to this file.

    Layout: `.claude/skills/spec-critique/scripts/critique_scan.py`
         -> `.claude/skills/product-spec/scripts/`.
    parents[2] is `.claude/skills/`.
    """
    return Path(__file__).resolve().parents[2] / "product-spec" / "scripts"


def _import_psp():
    """Import the pure product-spec helpers (spec_graph, assemble_digest,
    judgment_cache, preferences, fs_guard, frontmatter_parser). Loud error if the
    product-spec scripts dir is absent — the skill cannot run without it."""
    psp = _psp_dir()
    if not psp.is_dir():
        raise ModuleNotFoundError(
            f"product-spec scripts dir not found at {psp}. spec-critique reuses "
            "product-spec's scripts; install product-spec first."
        )
    sd = str(psp)
    if sd not in sys.path:
        sys.path.insert(0, sd)
    import spec_graph
    import assemble_digest
    import judgment_cache
    import preferences
    import fs_guard
    return spec_graph, assemble_digest, judgment_cache, preferences, fs_guard


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _node_index(graph: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {n["id"]: n for n in graph.get("nodes", [])}


def _numbered_source(root: Path, rel_file: str) -> Optional[str]:
    """Read a source artifact file and return it with 1-based line-number prefixes
    (`<n>: <text>`), so a lens agent cites a real `ID:line` that resolves in the
    PO's own file. The digest body is reused/normalized and carries NO source line
    offsets, so without this the agents invent line numbers (observed: they emit
    bundle-JSON offsets that point past the end of small files). Returns None if the
    file is unreadable."""
    try:
        text = (root / "docs" / "product" / rel_file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return "\n".join(f"{i}: {ln}" for i, ln in enumerate(text.splitlines(), 1))


def _source_files(root: Path, graph: Dict[str, Any]) -> Dict[str, str]:
    """Map every artifact ID to its file's line-numbered content (`<n>: <text>`).

    Keyed by ARTIFACT ID, not file path: the lens cites `<id>:<line>`, so making the
    lookup key the citation prefix itself removes the path-vs-id ambiguity that let
    agents cite a bare `brd.md:79`. Nodes that share a file (the BRD goals all live
    in brd.md) each get their own ID key pointing at that file's content; the BRD
    container node, whose own `file` is None, falls back to its goals' file so
    BRD-level content stays citable as `BRD:<line>`. Per-file reads are cached."""
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
        numbered = _numbered_cached(rel)
        if numbered is not None:
            out[nid] = numbered

    # The BRD container is a digest singleton, not a graph node, so the loop above
    # never reaches it. Add `BRD` (its content is brd.md, the goals' file) so
    # BRD-level prose (competitors, stakeholders) stays citable as `BRD:<line>`.
    if goal_file and "BRD" not in out:
        numbered = _numbered_cached(goal_file)
        if numbered is not None:
            out["BRD"] = numbered
    return out


def _run_check(psp: Path, script: str, root: Path) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Run a check_*.py checker as a subprocess and return (findings, error).

    Subprocess (not import) keeps the checker's transitive import chain out of this
    process. The checker prints a JSON object with a `findings` list; on any failure
    we return ([], <error-string>) so the caller records it in parse_errors."""
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


def _resolve_targets(spec_graph, graph: Dict[str, Any], scope: str) -> Tuple[List[str], Optional[str]]:
    """Resolve the critique target id-set: scope node + its descendants.

    Returns (target_ids, error). scope == 'all' -> every node. An unknown scope
    yields ([], error) so the caller records a parse_error and emits an empty
    bundle rather than crashing."""
    ids = [n["id"] for n in graph.get("nodes", [])]
    if scope == "all":
        return sorted(ids), None
    if scope not in set(ids):
        return [], f"unknown scope {scope!r}: not an artifact id in the spec"
    targets = {scope} | spec_graph.downstream(graph, scope)
    return sorted(targets), None


def _build_ancestry(spec_graph, graph: Dict[str, Any], digest: List[Dict[str, Any]],
                    scope: str) -> Dict[str, Any]:
    """The explicit ancestry frame: vision + brd_goals + prd + epic.

    Reuses the digest entries (full content already assembled) so we never
    re-serialize bodies. Vision is an isolated graph node (no edges); the BRD
    container is not a node — both surface as digest ancestor/singleton entries.
    `ancestors()` supplies the goal/PRD/epic chain for a scoped node.
    """
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
    `check|scope_key|body_hash|lang|dep_hash` (scope_key may be `idA+idB` for a pair
    check); an entry is in-scope when scope=='all' or any of its ids is a target."""
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


def _prior_reports(root: Path) -> List[Dict[str, Any]]:
    """Prior critique reports under docs/product/critique/, parsed from the
    `<ts>-<scope>.md` filename. Sorted by filename (chronological by ts prefix)."""
    crit_dir = root / "docs" / "product" / "critique"
    if not crit_dir.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    for p in sorted(crit_dir.glob("*.md")):
        stem = p.stem
        ts, _, sc = stem.partition("-")
        out.append({"path": str(p), "ts": ts, "scope": sc or None})
    return out


def _drift_threshold(preferences, root: Path) -> int:
    """The PO's critique drift threshold. preferences.load() passes this non-enum
    key through verbatim (no int-validation), so coerce defensively here."""
    prefs = preferences.load(root)
    raw = prefs.get("critique_drift_threshold", DEFAULT_THRESHOLD)
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_THRESHOLD
    return val if val >= 1 else DEFAULT_THRESHOLD


def _live_body_hashes(spec_graph, root: Path) -> Dict[str, str]:
    """Per-node body_hash from a fresh build_graph. Skips nodes whose body_hash is
    None (goals — no standalone body to fingerprint)."""
    graph = spec_graph.build_graph(root)
    out: Dict[str, str] = {}
    for n in graph.get("nodes", []):
        bh = n.get("body_hash")
        if isinstance(bh, str) and bh not in _HASH_SENTINELS:
            out[n["id"]] = bh
    return out


def _validated_body_hashes(judgment_cache, root: Path) -> Optional[Dict[str, str]]:
    """Validate-time per-node body_hash recovered from judgments.json keys.

    Each single-node key embeds the node's body_hash as its 3rd `|` segment
    (`check|node_id|body_hash|lang|dep_hash`). Pair-check keys (`idA+idB`) are
    skipped — their hash segment is `hashA+hashB`, not a single node's hash.

    The cache GC only evicts entries for DELETED node ids, never a superseded
    body_hash for a still-live id, so a node can carry two distinct validate-time
    hashes (old + new body, both validated). Last-wins on dict iteration would pick
    one arbitrarily — a false-drift source. We instead collect ALL distinct hashes
    per node and keep one ONLY when there is exactly one; a node with conflicting
    hashes is UNCERTAIN and excluded (conservative: a missed drift is silent, a
    false one nags). Returns None when the cache is absent/empty so the caller can
    fall back to a live build."""
    cache = judgment_cache.load_cache(root)
    if not cache:
        return None
    entries = cache.get("entries")
    if not isinstance(entries, dict) or not entries:
        return None
    seen: Dict[str, set] = {}
    for key in entries:
        parts = str(key).split("|")
        if len(parts) < 3:
            continue
        scope_key, body_hash = parts[1], parts[2]
        if "+" in scope_key:  # pair check — composite hash, not a single node's
            continue
        if body_hash and body_hash not in _HASH_SENTINELS:
            seen.setdefault(scope_key, set()).add(body_hash)
    out = {nid: next(iter(hashes)) for nid, hashes in seen.items() if len(hashes) == 1}
    return out or None


def _load_marker(root: Path) -> Optional[Dict[str, Any]]:
    path = root / "docs" / "product" / ".memory" / "last_critique.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _diff_hashes(current: Dict[str, str], previous: Dict[str, str],
                 threshold: int, current_covers_all: bool = True) -> Dict[str, Any]:
    """Count nodes whose body_hash differs between `current` and `previous`.

    `current_covers_all` is the universe contract:
      - True (live --drift): both sides fingerprint EVERY bodied node, so the diff
        universe is the union — an added node (only in current) or a removed node
        (only in previous) is real drift.
      - False (--vs-validated): `current` covers only the VALIDATED subset; a node
        in `previous` but absent from `current` carries no validate-time signal, so
        it must NOT count as changed. The universe is `current` only — a validated
        node whose hash differs from (or is new vs) the critique baseline is drift;
        un-validated baseline nodes are simply unknown, not changed.
    """
    ids = set(current) | set(previous) if current_covers_all else set(current)
    changed = sorted(i for i in ids if current.get(i) != previous.get(i))
    return {
        "changed_count": len(changed),
        "changed_ids": changed,
        "threshold": threshold,
        "over": len(changed) >= threshold,
    }


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def emit_bundle(root: Path, scope: str, lang: str) -> Dict[str, Any]:
    spec_graph, assemble_digest, judgment_cache, preferences, _fs = _import_psp()
    parse_errors: List[str] = []

    graph, artifacts = spec_graph.build_graph_with_artifacts(root)
    for pe in graph.get("parse_errors") or []:
        parse_errors.append(f"{pe.get('file')}: {pe.get('error')}")

    target_ids, scope_err = _resolve_targets(spec_graph, graph, scope)
    if scope_err:
        parse_errors.append(scope_err)

    try:
        digest = assemble_digest.build_digest(graph, artifacts, select=scope,
                                              layers=None, depth="context")
    except ValueError as exc:
        digest = []
        parse_errors.append(f"digest: {exc}")

    findings, ferr = _structural_findings(_psp_dir(), root)
    parse_errors.extend(ferr)

    ancestry = _build_ancestry(spec_graph, graph, digest, scope)

    return {
        "bundle_version": BUNDLE_VERSION,
        "scope": scope,
        "lang": lang,
        "target_ids": target_ids,
        "ancestry": ancestry,
        "digest": digest,
        "source_files": _source_files(root, graph),
        "structural_findings": findings,
        "cached_verdicts": _cached_verdicts(judgment_cache, root, scope, target_ids),
        "competitors": [c for c in (graph.get("competitors") or []) if isinstance(c, dict)],
        "prior_reports": _prior_reports(root),
        "drift_threshold": _drift_threshold(preferences, root),
        "parse_errors": parse_errors,
    }


def write_snapshot(root: Path, scope: str) -> Dict[str, Any]:
    spec_graph, _ad, _jc, _pref, fs_guard = _import_psp()
    body_hash = _live_body_hashes(spec_graph, root)
    marker = {"critiqued_at": _now(), "scope": scope, "body_hash": body_hash}

    path = root / "docs" / "product" / ".memory" / "last_critique.json"
    resolved = fs_guard.assert_under_docs_product(path, root)  # raises FenceError out-of-tree
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved, "w", encoding="utf-8", newline="") as fh:
        json.dump(marker, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return {"snapshot_written": str(resolved), "node_count": len(body_hash), "scope": scope}


def compute_drift(root: Path, vs_validated: bool) -> Dict[str, Any]:
    spec_graph, _ad, judgment_cache, preferences, _fs = _import_psp()
    threshold = _drift_threshold(preferences, root)

    marker = _load_marker(root)
    if marker is None:
        # No baseline critique yet — never "over"; the skill suggests a first run.
        return {"changed_count": 0, "changed_ids": [], "threshold": threshold,
                "over": False, "first_run": True}
    previous = marker.get("body_hash") if isinstance(marker.get("body_hash"), dict) else {}

    current: Optional[Dict[str, str]] = None
    source = "live"
    if vs_validated:
        current = _validated_body_hashes(judgment_cache, root)
        source = "validated"
    if current is None:  # --vs-validated with no cache, or plain --drift
        current = _live_body_hashes(spec_graph, root)
        source = "live"

    # The validated set covers only judged nodes; the live build covers all. Diff
    # over the right universe so --vs-validated does not count un-validated baseline
    # nodes as drift (coverage asymmetry would otherwise misfire the Stop hook).
    result = _diff_hashes(current, previous, threshold,
                          current_covers_all=(source == "live"))
    result["source"] = source
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="spec-critique bundle/snapshot/drift assembler")
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--scope", default="all")
    ap.add_argument("--lang", default="vi")
    ap.add_argument("--snapshot", action="store_true", help="write last_critique.json")
    ap.add_argument("--drift", action="store_true", help="count body_hash drift vs last_critique.json")
    ap.add_argument("--vs-validated", action="store_true",
                    help="(with --drift) compare validate-time hashes, no live build")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    try:
        if args.snapshot:
            result = write_snapshot(root, args.scope)
        elif args.drift:
            result = compute_drift(root, args.vs_validated)
        else:
            result = emit_bundle(root, args.scope, args.lang)
    except Exception as exc:  # noqa: BLE001 — advisory tool: never crash a caller
        result = {"error": f"{type(exc).__name__}: {exc}", "scope": args.scope}

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
