#!/usr/bin/env python3
"""critique_scan.py — the product-spec-critique CLI entrypoint + public facade.

The deterministic, reuse-first bundle/snapshot/drift assembler for
cleanmatic:product-spec-critique. NO LLM, NO re-analysis — it gathers existing signals into
ONE JSON bundle the lens agents consume, manages the `last_critique.json` body_hash
snapshot, and decides what a re-run may reuse. It NEVER judges quality (the lens
agents' job).

The implementation is split across focused modules:

  * critique_common.py     — cross-dir product-spec import + graph helpers
  * critique_bundle.py     — the default mode (emit_bundle) + its signal gatherers
  * critique_provenance.py — report frontmatter + the 4-way reuse decision
  * critique_drift.py      — --snapshot / --drift
  * critique_inherit.py    — inherited_context + descendant_rollup
  * critique_cache.py      — the cache/state stores

This module is the CLI dispatcher AND the back-compat facade: callers (and tests)
that did `critique_scan.<fn>` keep working via the re-exports below.

Modes (exactly one is active):
  (default)                emit the bundle JSON to stdout
  --snapshot               write last_critique.json (per-node body_hash) via fs_guard
  --drift                  count body_hash changes vs last_critique.json (live build)
  --drift --vs-validated   compare validate-time hashes vs last_critique.json (Stop-hook path)

ALWAYS exits 0 (advisory). Malformed input degrades to a `parse_errors` field /
sentinel result, never a crash."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# --- public facade: re-export the implementation split across the focused modules
# so `critique_scan.<name>` keeps resolving for callers/tests/orchestration ---------
from critique_common import (  # noqa: F401
    BUNDLE_VERSION, DEFAULT_THRESHOLD, _HASH_SENTINELS, _import_psp, _live_body_hashes,
    _node_index, _now, _provenance_hash, _psp_dir, _resolve_targets, _scoped_body_hashes,
)
from critique_provenance import (  # noqa: F401
    _decide_unchanged, _latest_frontmatter_prior, _prior_reports, _read_report_frontmatter,
    build_report_frontmatter, compute_provenance_reuse, record_critique_state,
)
from critique_drift import (  # noqa: F401
    _diff_hashes, _load_marker, _validated_body_hashes, compute_drift, write_snapshot,
)
from critique_bundle import (  # noqa: F401
    _coerce_level, _drift_threshold, _resolve_inherit, emit_bundle,
)
from critique_signals import (  # noqa: F401
    _build_ancestry, _cached_verdicts, _source_files, _structural_findings,
)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="product-spec-critique bundle/snapshot/drift assembler")
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--scope", default="all")
    ap.add_argument("--lang", default="vi")
    ap.add_argument("--level", type=int, default=None,
                    help="target critique level 1..9 (default: preferences.critique_level)")
    ap.add_argument("--fresh", "--force", dest="fresh", action="store_true",
                    help="force provenance reuse=none (bypass all reuse)")
    ap.add_argument("--no-inherit", action="store_true",
                    help="disable parent→child inherited_context (beats --inherit)")
    ap.add_argument("--no-rollup", action="store_true",
                    help="disable child→parent descendant_rollup")
    ap.add_argument("--inherit", choices=["nearest", "deep"], default=None,
                    dest="inherit_depth", help="inherit depth (implies on); --no-inherit wins")
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
            _sg, _ad, _jc, preferences, _fs = _import_psp()
            threshold = _drift_threshold(preferences, root, DEFAULT_THRESHOLD)
            result = compute_drift(root, args.vs_validated, threshold)
        else:
            result = emit_bundle(root, args.scope, args.lang, level=args.level,
                                 fresh=args.fresh, no_inherit=args.no_inherit,
                                 no_rollup=args.no_rollup, inherit_depth=args.inherit_depth,
                                 default_threshold=DEFAULT_THRESHOLD)
    except Exception as exc:  # noqa: BLE001 — advisory tool: never crash a caller
        result = {"error": f"{type(exc).__name__}: {exc}", "scope": args.scope}

    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
