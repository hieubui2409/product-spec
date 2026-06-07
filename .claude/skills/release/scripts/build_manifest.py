"""build_manifest — interactive manifest builder for cleanmatic:release.

Three modes (mutually exclusive):
- ``--discover`` — scan ``.claude/`` and emit a JSON catalog.
- ``--list-questions`` — emit the canonical question bank as JSON for the LLM
  to walk via ``AskUserQuestion``.
- ``--write`` — read answers JSON from stdin, validate via ``manifest_loader``,
  atomic-write to ``.claude/pack.manifest.yaml``.

Python NEVER calls ``AskUserQuestion`` — the LLM is the UI layer.

Implementation is split across three leaf modules:
- build_manifest_discover  — filesystem scanner (discover())
- build_manifest_questions — question bank (list_questions())
- build_manifest_writer    — assembler + atomic writer (write_manifest())
This file re-exports every public symbol and owns the CLI entry point.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Re-export every public symbol so callers, tests, and monkeypatch targets
# that reference ``build_manifest.X`` continue to resolve correctly.
from build_manifest_discover import discover  # type: ignore[import-not-found]
from build_manifest_questions import list_questions  # type: ignore[import-not-found]
from build_manifest_writer import (  # type: ignore[import-not-found]
    CANONICAL_KEY_ORDER,
    CONFIRM_PROMPT_TEMPLATE,
    EXIT_COLLISION,
    EXIT_OK,
    EXIT_VALIDATION,
    HEADER_COMMENT,
    _assemble_manifest,
    _atomic_write_yaml,
    _reorder,
    write_manifest,
)

__all__ = [
    "discover", "list_questions", "write_manifest",
    "CANONICAL_KEY_ORDER", "HEADER_COMMENT", "CONFIRM_PROMPT_TEMPLATE",
    "EXIT_OK", "EXIT_VALIDATION", "EXIT_COLLISION",
    "_reorder", "_assemble_manifest", "_atomic_write_yaml",
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build_manifest",
                                description="release interactive manifest builder")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--discover", action="store_true")
    mode.add_argument("--list-questions", dest="list_questions", action="store_true")
    mode.add_argument("--write", action="store_true")
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--lang", default="en")
    p.add_argument("--out", type=Path, default=None,
                   help="output manifest path (default: <root>/.claude/pack.manifest.yaml)")
    p.add_argument("--force", action="store_true")
    p.add_argument("--allow-dev-version", action="store_true")
    args = p.parse_args(argv)

    root = args.root.resolve()
    out_path = args.out or (root / ".claude" / "pack.manifest.yaml")

    if args.discover:
        json.dump(discover(root), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return EXIT_OK

    if args.list_questions:
        d = discover(root)
        json.dump(list_questions(d, args.lang), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return EXIT_OK

    if args.write:
        try:
            answers = json.loads(sys.stdin.read() or "{}")
        except json.JSONDecodeError as e:
            sys.stderr.write(f"answers JSON parse error: {e}\n")
            return EXIT_VALIDATION
        if not isinstance(answers, dict):
            sys.stderr.write(
                f"answers JSON must be an object (dict); got {type(answers).__name__}\n"
            )
            return EXIT_VALIDATION
        return write_manifest(answers, out_path, root,
                              force=args.force,
                              allow_dev_version=args.allow_dev_version)

    return EXIT_VALIDATION


if __name__ == "__main__":
    sys.exit(main())
