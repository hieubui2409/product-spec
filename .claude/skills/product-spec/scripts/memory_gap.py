#!/usr/bin/env python3
"""
memory_gap — the deterministic SCRIPT detector for "memory that looks unrecorded".

This is the single DRY home for the four "the LLM probably should have written to
the memory layer but the marker says it didn't" signals. It is SCRIPT-only: it
correlates persisted disk/graph state and emits structured signals — it makes NO
judgment (Script-vs-LLM split, CLAUDE.md). The downstream consumers (`--status`,
the validate forcing-function, the Stop hook, `--reflect` dedup) read these
signals; the LLM decides what to do about each.

It NEVER re-implements a detector it can import. Fence detection is
`check_fence.scan`; the graph + `body_hash` + the validated snapshot are
`spec_graph`; the last-validated marker path is `judgment_cache._last_validated_path`
(and its snapshot loader is `status`); decisions are `decision_register`; the
verdict cache is `judgment_cache`. One home per fact — this module only correlates.

Signals (each `{type, severity, subject, evidence, suggested_writer}`):
  - `fence_breach` — a working-tree change landed OUTSIDE docs/product/. Reuses
    `check_fence.scan` verbatim; the suggested writer is the in-fence move, not a
    memory write. Severity `warn`.
  - `validate_no_marker` — PERSISTED-STATE only: the script CANNOT know a
    `--validate` ran "this session". It compares the LIVE graph against the
    snapshot recorded in `.memory/last_validated.json`. No marker, or the live
    graph drifted from the validated snapshot, → fire. Severity `info`.
  - `approved_changed_no_dec` — an `approved` artifact's `body_hash` changed vs
    the last-validated snapshot but NO active `DEC-<n>` in decisions.md `affects`
    it. A legit re-approval is a FALSE POSITIVE here — it is SURFACED, never
    blocked (the hook nudges once). The PO can `--ack-no-dec <id>` to silence it
    for the current wording. Severity `warn`.
  - `judged_not_stored` — the graph drifted but `judgments.json` did not grow past
    the count recorded in `.memory/last_judged.json`. Marker ABSENT → SKIPPED
    (degrade, never a false fire — the batch-store owns that marker). Severity `info`.

Acks: `--ack-no-dec <node-id>` records `{node_id: body_hash}` in
`.memory/no-dec-acks.json`. `collect()` suppresses `approved_changed_no_dec` for a
node whose CURRENT `body_hash` matches its ack — the PO marks "no DEC needed" ONCE
and is not re-nudged for that wording. A later body change makes the recorded hash
stale, so the signal re-arms automatically (no manual un-ack).

Deterministic: same disk state → same `signals` list (sorted, no wall-clock in the
body). ALWAYS exits 0 (advisory) — a malformed artifact surfaces as a `parse_error`
signal, never a traceback.

CLI:
    memory_gap.py --root <project-dir>          # emit {signals:[...]}, exit 0
    memory_gap.py --root <project-dir> --ack-no-dec <node-id>   # record an ack
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from encoding_utils import configure_utf8_console
from fs_guard import assert_under_docs_product
import check_fence
import decision_register as dr
from spec_graph import build_graph, changed_nodes, diff_graphs
from judgment_cache import load_cache, _last_judged_path, write_last_judged
# status owns the single home for loading the last-validated marker + the snapshot
# graph it points at. Reuse those readers rather than re-deriving the marker/
# snapshot IO (one home for the "what was validated" fact).
from status import _load_last_validated, _load_baseline_snapshot

configure_utf8_console()


def _acks_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "no-dec-acks.json"


# ----------------------------------------------------------------------------
# Marker / ack readers (degrade to None/empty — never raise)
# ----------------------------------------------------------------------------

def _load_acks(root) -> Dict[str, str]:
    """`{node_id: body_hash}` of nodes the PO marked "no DEC needed". A missing or
    corrupt file degrades to {} (no acks) — the safe direction (signal still fires)."""
    path = _acks_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)} \
        if isinstance(data, dict) else {}


def _load_last_judged(root) -> Optional[Dict[str, Any]]:
    """The batch-store marker `{verdict_count, snapshot_hash}` written by the
    judgment-cache batch-store. None when absent/corrupt — `judged_not_stored` is
    then SKIPPED (degrade, never a false fire)."""
    path = _last_judged_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _verdict_count(root) -> int:
    """Current number of cached LLM verdicts. 0 when the cache is absent/corrupt."""
    cache = load_cache(root)
    if cache is None:
        return 0
    entries = cache.get("entries")
    return len(entries) if isinstance(entries, dict) else 0


def ack_no_dec(root, node_id: str) -> Path:
    """Record the node's CURRENT `body_hash` in `.memory/no-dec-acks.json` so
    `approved_changed_no_dec` is suppressed for it while the wording is unchanged.

    A later body edit makes the stored hash stale → the signal re-arms (no manual
    un-ack). The write goes through the soft fence (can never escape the boundary)."""
    graph = build_graph(root)
    node = _node_index(graph).get(node_id)
    body_hash = node.get("body_hash") if isinstance(node, dict) else None
    acks = _load_acks(root)
    acks[node_id] = body_hash if isinstance(body_hash, str) else ""
    path = _acks_path(root)
    assert_under_docs_product(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(acks, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return path


# ----------------------------------------------------------------------------
# Signal builders
# ----------------------------------------------------------------------------

def _signal(stype: str, severity: str, subject: Optional[str], evidence: str,
            suggested_writer: str) -> Dict[str, Any]:
    return {
        "type": stype,
        "severity": severity,
        "subject": subject,
        "evidence": evidence,
        "suggested_writer": suggested_writer,
    }


def _node_index(graph: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {n["id"]: n for n in graph.get("nodes", [])}


# Cap on individually-listed fence breaches before they collapse into one aggregate
# signal. `check_fence` already drops the kit's own `.claude/` tree, but a session that
# legitimately touches many out-of-fence files must still never flood `--status` into an
# over-report — so the tail is summarized, not enumerated, with the full count preserved.
_FENCE_SIGNAL_CAP = 10


def _fence_signals(root) -> List[Dict[str, Any]]:
    """One `fence_breach` per file `check_fence.scan` reports outside the boundary, up to
    `_FENCE_SIGNAL_CAP`; any overflow collapses into a single aggregate signal carrying the
    total count. Reuses the imported scan verbatim — no re-implementation of the porcelain walk."""
    breaches = check_fence.scan(Path(root))
    out: List[Dict[str, Any]] = []
    for f in breaches[:_FENCE_SIGNAL_CAP]:
        out.append(_signal(
            "fence_breach", "warn", f["file"],
            f.get("detail") or f"{f['file']} touched outside docs/product/.",
            "move the file under docs/product/ (the skill only writes specs there)",
        ))
    extra = len(breaches) - _FENCE_SIGNAL_CAP
    if extra > 0:
        out.append(_signal(
            "fence_breach", "warn", None,
            f"+{extra} more files touched outside docs/product/ ({len(breaches)} total).",
            "review the out-of-fence changes; move any that are specs under docs/product/",
        ))
    return out


def _validate_no_marker_signal(graph, baseline_snapshot,
                               marker) -> Optional[Dict[str, Any]]:
    """Fire when there is no validated baseline, or the live graph drifted from the
    validated snapshot. PERSISTED-STATE only — the script cannot know a `--validate`
    ran this session; it compares the live graph against the marker's snapshot."""
    if marker is None or baseline_snapshot is None:
        return _signal(
            "validate_no_marker", "info", None,
            "no last_validated.json marker — the spec has no recorded validation "
            "baseline (or the marker/snapshot is missing).",
            "run --validate to record a baseline (judgment_cache.write_last_validated)",
        )
    diff = diff_graphs(graph, baseline_snapshot)
    drifted = set(changed_nodes(graph, baseline_snapshot)) | set(diff["added"]) | set(diff["removed"])
    if drifted:
        return _signal(
            "validate_no_marker", "info", None,
            "the live graph drifted from the last-validated snapshot "
            f"({', '.join(sorted(drifted))}) — these changes were never validated.",
            "run --validate to re-baseline (judgment_cache.write_last_validated)",
        )
    return None


def _approved_changed_signals(root, graph, baseline_snapshot,
                              acks) -> List[Dict[str, Any]]:
    """One `approved_changed_no_dec` per approved node whose `body_hash` changed vs
    the validated snapshot with no active DEC `affects`-ing it AND no matching ack.

    False-positive nature is documented in the evidence: a legit re-approval also
    fires here — it is SURFACED, never blocked; the PO can `--ack-no-dec <id>`."""
    out: List[Dict[str, Any]] = []
    if baseline_snapshot is None:
        return out  # no baseline → nothing to diff against (validate_no_marker covers it)

    prev = {n["id"]: n for n in baseline_snapshot.get("nodes", [])}
    # Active-DEC `affects` set — the single home for "this node's drift is on record".
    dec_affects = {r.get("affects") for r in dr.list_active(root) if r.get("affects")}

    for n in graph.get("nodes", []):
        if n.get("status") != "approved":
            continue
        nid = n["id"]
        cur_bh = n.get("body_hash")
        prev_bh = prev.get(nid, {}).get("body_hash")
        # Only an actual, known body change counts (both hashes present + differ).
        if not isinstance(cur_bh, str) or not isinstance(prev_bh, str) or cur_bh == prev_bh:
            continue
        if nid in dec_affects:
            continue  # the drift is on record (a DEC affects this node)
        if acks.get(nid) == cur_bh:
            continue  # the PO marked "no DEC needed" for exactly this wording
        out.append(_signal(
            "approved_changed_no_dec", "warn", nid,
            f"approved artifact {nid} body changed since the last validate "
            f"({prev_bh} → {cur_bh}) but no active DEC records the ruling. "
            "False-positive-prone: a legitimate re-approval also fires — surfaced, "
            "never blocked. --ack-no-dec to silence it for this wording.",
            "record the ruling with --decision (decision_register), or --ack-no-dec",
        ))
    return out


def _judged_not_stored_signal(root, graph, baseline_snapshot,
                              marker) -> Optional[Dict[str, Any]]:
    """Fire when the graph drifted from the validated snapshot but the verdict cache
    did NOT grow past the `last_judged.json` count. Marker ABSENT → SKIPPED (the
    batch-store owns the marker; without it there is no count to compare → degrade)."""
    last_judged = _load_last_judged(root)
    if last_judged is None:
        return None  # no marker → skip (degrade, never a false fire)
    if baseline_snapshot is None:
        return None  # no baseline → no drift signal to correlate against
    diff = diff_graphs(graph, baseline_snapshot)
    drifted = set(changed_nodes(graph, baseline_snapshot)) | set(diff["added"]) | set(diff["removed"])
    if not drifted:
        return None
    recorded = last_judged.get("verdict_count")
    recorded = recorded if isinstance(recorded, int) else 0
    if _verdict_count(root) > recorded:
        return None  # the cache grew → judgments were stored, no gap
    return _signal(
        "judged_not_stored", "info", None,
        f"the graph drifted ({', '.join(sorted(drifted))}) but the verdict cache "
        f"did not grow past the last batch-store count ({recorded}) — judgments "
        "may have been made in chat without being persisted.",
        "batch-store the verdicts (judgment_cache --store-batch)",
    )


# ----------------------------------------------------------------------------
# Correlate → signals
# ----------------------------------------------------------------------------

def collect(root) -> List[Dict[str, Any]]:
    """Build every memory-gap signal for `root`, deterministically sorted.

    Order key = (type, subject) so the output is stable across runs (same disk
    state → same list). A malformed artifact surfaces as a `parse_error` signal
    (from the graph's `parse_errors`) — never a crash."""
    root = Path(root).resolve()
    graph = build_graph(root)
    marker = _load_last_validated(root)
    baseline_snapshot = _load_baseline_snapshot(root, marker) if marker else None
    acks = _load_acks(root)

    signals: List[Dict[str, Any]] = []

    # Surface any artifact the graph could not parse (advisory — never block).
    for pe in graph.get("parse_errors") or []:
        signals.append(_signal(
            "parse_error", "warn", pe.get("file"),
            f"{pe.get('file')} could not be parsed: {pe.get('error')}",
            "fix the artifact frontmatter (no memory write applies until it parses)",
        ))

    signals.extend(_fence_signals(root))

    vnm = _validate_no_marker_signal(graph, baseline_snapshot, marker)
    if vnm:
        signals.append(vnm)

    signals.extend(_approved_changed_signals(root, graph, baseline_snapshot, acks))

    jns = _judged_not_stored_signal(root, graph, baseline_snapshot, marker)
    if jns:
        signals.append(jns)

    signals.sort(key=lambda s: (s["type"], s.get("subject") or ""))
    return signals


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument(
        "--ack-no-dec", default=None, metavar="NODE-ID",
        help="record .memory/no-dec-acks.json {node_id: body_hash} so "
             "approved_changed_no_dec is suppressed for this node's current wording",
    )
    args = ap.parse_args()
    root = Path(args.root).resolve()

    try:
        if args.ack_no_dec:
            path = ack_no_dec(root, args.ack_no_dec)
            print(json.dumps(
                {"acked": args.ack_no_dec, "path": str(path.relative_to(root))},
                ensure_ascii=False))
            return 0

        signals = collect(root)
        print(json.dumps({"signals": signals}, indent=2, ensure_ascii=False, default=str))
        return 0
    except Exception as exc:  # noqa: BLE001 — advisory contract: never crash
        # Advisory: any unexpected failure surfaces as a parse_error signal + exit 0,
        # never a bare traceback (mirrors the analytical-script contract).
        print(json.dumps(
            {"signals": [_signal("parse_error", "warn", None, str(exc),
                                 "investigate the spec state")]},
            ensure_ascii=False))
        return 0


if __name__ == "__main__":
    sys.exit(main())
