#!/usr/bin/env python3
"""
competitive_drift_anchors — SCRIPT half of the `competitive_drift` LLM check
(COMPETITION dimension).

`competitive_drift` is an LLM-judgment warn (Script-vs-LLM split) — "this
PRD is losing its competitive edge" is a sensory call no enum-match can make. But
to stop the LLM hallucinating ("mất lợi thế" is the classic over-flag), the design
pins the LLM to STRUCTURED, SCRIPT-precomputed anchors and
forbids it from inventing a competitor or a parity verdict:

    {artifact_id, file, type, scope,
     competitive_parity:[{competitor_id, competitor:<resolved name>, parity}],
     competitors_with_data, all_behind_competitors, incomplete, eligible}

The script RESOLVES the PRD's ID-keyed `competitive_parity` map against the BRD's
DRY competitor identity home (`graph['competitors']`) into NAME-bearing rows, and
pre-computes `competitors_with_data` (the count of parity entries whose value is
NOT `none`) — the LLM does NO counting and never re-parses brd.md. The LLM
only applies the fixed AND-rule against these numbers (see the scaffold in
references/validation-rules-spec.md → "competitive_drift LLM Scaffold").

The anchored rule: a PRD is flag-ELIGIBLE only when it is
`scope: core-value` AND has `competitors_with_data >= 2` real parity verdicts. The
LLM then flags only if EVERY resolved, real (non-`none`) parity is `behind` —
which the script also pre-lists as `all_behind_competitors`. Anything short of
that (`scope != core-value`, < 2 verdicts, or any non-`behind` among them) → the
LLM returns `{finding: null}`. Conservative default: uncertain → do NOT flag.

This script emits ONLY anchors — it never decides flag/no-flag (that is the LLM's
judgment). A PRD that cannot meet the rule (wrong scope, < 2 data points) is still
emitted with `eligible: false` so the LLM returns `{finding: null}` without
inventing data — the explicit anti-hallucination case.

Scope: PRDs (the unit that carries BOTH `scope` and `competitive_parity`).
Epics/stories have no parity map and are skipped. A parity KEY that does
not resolve to a BRD competitor is dropped from the resolved block (the structural
`unknown_ref` error is the consistency check's job, NOT this feeder's) so the LLM
never sees a phantom competitor.

Pure data assembly — no LLM, no judgment, no wall-clock side effects. Always
exits 0 (an advisory feeder, never a gate), mirroring time_realism_anchors.py.

CLI:
    competitive_drift_anchors.py --root <project-dir>
        Prints {schema_version, root, checked_at, anchors:[...]} to stdout. Exits 0.
        (`checked_at` is wall-clock provenance, same envelope as the validate
        findings schema; the deterministic payload is `anchors`.)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from encoding_utils import configure_utf8_console
from spec_graph import build_graph, _now, competitor_id_to_name

configure_utf8_console()

# A PRD must be on the product's core value AND carry at least this many real
# parity verdicts before the drift judgment is even eligible — the anchored
# anti-hallucination gate. `none` parity does NOT count as data.
_MIN_COMPETITORS_WITH_DATA = 2


def build_anchors(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Assemble one anchor record per PRD that declares a `competitive_parity` map.

    Resolves the ID-keyed parity map against the BRD competitor names, counts the
    real (non-`none`) verdicts as `competitors_with_data`, and lists the subset
    whose verdict is `behind` as `all_behind_competitors`. Eligibility (scope ==
    core-value AND competitors_with_data >= 2) is pre-computed so the LLM returns
    `missing_anchor`/no-flag deterministically. Sorted by artifact_id → stable
    order (byte-deterministic). The SCRIPT never decides flag/no-flag — only the numbers."""
    names = competitor_id_to_name(graph)
    anchors: List[Dict[str, Any]] = []
    for n in graph["nodes"]:
        if n.get("type") != "prd":
            continue
        cp = n.get("competitive_parity")
        # A v1 PRD (no parity map) is not a drift unit — skip it entirely, do not
        # emit an empty ineligible anchor (mirrors time anchors skipping PRDs).
        if not isinstance(cp, dict) or not cp:
            continue
        resolved: List[Dict[str, Any]] = []
        for comp_id, parity in cp.items():
            # Drop keys that do not resolve to a BRD competitor: the phantom-ref
            # is the consistency check's `unknown_ref` error, not this feeder's —
            # the LLM must never see an invented competitor.
            if comp_id not in names:
                continue
            resolved.append({
                "competitor_id": comp_id,
                "competitor": names[comp_id],
                "parity": parity,
            })
        resolved.sort(key=lambda r: str(r["competitor_id"]))
        # `none` parity is "tracked but no verdict" — it is NOT a data point. Only
        # real verdicts (ahead/parity/behind) count toward the drift gate. An unset
        # `COMP-A:` parses to Python None (check_consistency allows it); None is the
        # same "no verdict" case as the literal "none" and must not be counted.
        real = [r for r in resolved if r["parity"] not in (None, "none")]
        competitors_with_data = len(real)
        all_behind = [r["competitor"] for r in real if r["parity"] == "behind"]
        scope = n.get("scope")
        incomplete = n.get("status") != "approved"
        eligible = (
            scope == "core-value"
            and competitors_with_data >= _MIN_COMPETITORS_WITH_DATA
        )
        anchors.append({
            "artifact_id": n.get("id"),
            "file": n.get("file"),
            "type": "prd",
            "scope": scope,
            "competitive_parity": resolved,
            "competitors_with_data": competitors_with_data,
            "all_behind_competitors": all_behind,
            "incomplete": incomplete,
            "eligible": eligible,
        })
    anchors.sort(key=lambda a: str(a.get("artifact_id")))
    return anchors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph = build_graph(root)
    anchors = build_anchors(graph)
    output = {
        "schema_version": "1.0",
        "root": str(root),
        "checked_at": _now(),
        "anchors": anchors,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
