#!/usr/bin/env python3
"""
strict_gate — shell-runnable `--strict` enforcement for CI.

The validation-rules-spec defines `--strict` as "errors block, warns advisory".
That gating originally lived only in the LLM orchestration layer, which made it
useless from a CI hook (no LLM in the loop → no enforcement → silent green on
broken specs). This script consumes the structural checkers' JSON output and
exits non-zero when any finding has severity=error.

CLI:
    strict_gate.py --root <project-dir>
        Runs check_traceability + check_consistency, merges findings.
        Exits 0 when no error-severity findings.
        Exits 2 when at least one error-severity finding is present.
        Always writes a human summary to stderr.

Use in CI:
    .claude/skills/.venv/bin/python3 \\
        .claude/skills/product-spec/scripts/strict_gate.py --root .
"""

import argparse
import sys
from pathlib import Path

from encoding_utils import configure_utf8_console
from spec_graph import build_graph
from check_traceability import check as check_trace
from check_consistency import check as check_cons, _enrich_with_ac

configure_utf8_console()

EXIT_OK = 0
EXIT_BLOCKED = 2


def collect_findings(root: Path):
    graph = build_graph(root)
    _enrich_with_ac(graph, root)
    findings = []
    findings.extend(check_trace(graph))
    findings.extend(check_cons(graph))
    return findings, graph


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="project root (contains docs/product/)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    findings, graph = collect_findings(root)
    errors = [f for f in findings if f.get("severity") == "error"]
    warns = [f for f in findings if f.get("severity") == "warn"]

    n_artifacts = len(graph.get("nodes", []))
    summary = (
        f"[strict_gate] {n_artifacts} artifacts checked · "
        f"{len(errors)} errors · {len(warns)} warns"
    )
    print(summary, file=sys.stderr)

    if not errors:
        return EXIT_OK

    print("[strict_gate] BLOCKED on errors:", file=sys.stderr)
    for f in errors:
        aid = f.get("artifact_id") or "?"
        chk = f.get("check") or "?"
        detail = f.get("detail") or ""
        print(f"  - {chk} · {aid} · {detail}", file=sys.stderr)
    return EXIT_BLOCKED


if __name__ == "__main__":
    sys.exit(main())
