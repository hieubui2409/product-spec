#!/usr/bin/env python3
"""critique_bundle.py — the default mode: assemble ONE JSON bundle the lens agents
consume. Reuse-first, NO LLM, NO re-analysis. It gathers existing signals only:

  * resolved scope target(s) + descendants + ancestry frame
  * structural findings (check_traceability + check_consistency, run FRESH)
  * cached LLM verdicts (judgment_cache) + assembled artifact digest
  * source_files: each artifact line-numbered (the `ID:line` citation ground-truth)
  * BRD competitors + prior critique reports (repeat-offense ammo)
  * provenance reuse verdict + inherited_context / descendant_rollup

The signal gatherers live in critique_signals; this module owns the per-run resolvers
(level / drift threshold / inherit gating) + the emit_bundle assembly."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import critique_inherit
from critique_common import BUNDLE_VERSION, _import_psp, _psp_dir, _resolve_targets
from critique_provenance import _prior_reports, compute_provenance_reuse
from critique_signals import (
    _build_ancestry, _cached_verdicts, _source_files, _structural_findings,
)


def _drift_threshold(preferences, root: Path, default: int) -> int:
    """The PO's critique drift threshold. preferences.load() passes this non-enum
    key through verbatim, so coerce defensively here."""
    prefs = preferences.load(root)
    raw = prefs.get("critique_drift_threshold", default)
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return default
    return val if val >= 1 else default


def _coerce_level(raw: Any) -> int:
    """The PO's default critique level (preferences.critique_level), coerced to int
    with a 5 fallback."""
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return 5
    return val if 1 <= val <= 9 else 5


def _resolve_register(prefs: Dict[str, Any], level: int) -> Optional[Dict[str, str]]:
    """The register (gender/dialect/profanity) for a level >= 7 run, read from prefs;
    None below 7 (register is a no-op there). Used by the provenance reuse decision so
    a register flip at the same level re-consolidates rather than serving stale voice
   . The actual voice rendering still happens in the consolidator, not here."""
    if level < 7:
        return None
    return {
        "gender": prefs.get("critique_address_gender", "m"),
        "dialect": prefs.get("critique_dialect", "bac"),
        "profanity": prefs.get("critique_profanity", "strong"),
    }


def _resolve_inherit(prefs: Dict[str, Any], no_inherit: bool,
                     inherit_depth: Optional[str]) -> Tuple[bool, str]:
    """(on, depth) for the inherit pass. Precedence: --no-inherit beats --inherit
    deep (off wins over depth). A --inherit flag implies ON at that depth; else the
    preference decides on/off + depth."""
    if no_inherit:
        return False, "nearest"
    if inherit_depth is not None:
        return True, inherit_depth
    return prefs.get("critique_inherit") == "on", prefs.get("critique_inherit_depth", "nearest")


def emit_bundle(root: Path, scope: str, lang: str, level: Optional[int] = None,
                fresh: bool = False, no_inherit: bool = False,
                no_rollup: bool = False, inherit_depth: Optional[str] = None,
                default_threshold: int = 3) -> Dict[str, Any]:
    spec_graph, assemble_digest, judgment_cache, preferences, _fs = _import_psp()
    prefs = preferences.load(root)
    parse_errors: List[str] = []
    eff_level = level if level is not None else _coerce_level(prefs.get("critique_level"))

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

    inh_on, inh_depth = _resolve_inherit(prefs, no_inherit, inherit_depth)
    inherited_context = (critique_inherit.build_inherited_context(root, graph, scope, inh_depth)
                         if inh_on else [])
    rollup_on = (not no_rollup) and prefs.get("critique_rollup") == "on"
    descendant_rollup = (critique_inherit.build_descendant_rollup(root, graph, scope)
                         if rollup_on else {})

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
        "drift_threshold": _drift_threshold(preferences, root, default_threshold),
        "provenance": compute_provenance_reuse(
            root, scope, eff_level, lang,
            register=_resolve_register(prefs, eff_level), fresh=fresh),
        "inherited_context": inherited_context,
        "descendant_rollup": descendant_rollup,
        "parse_errors": parse_errors,
    }
