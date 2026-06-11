#!/usr/bin/env python3
"""
open_questions — give PO-facing open questions a first-class home.

An acceptance-criterion, a body line, or a `.session.md` note carrying "cần PO xác
định" / "TBD" / "Vẫn còn mở" is an unresolved decision riding inside an artifact that
may already look done. Left implicit it has no home: it does not block `--validate`
(the prose is well-formed) and it is easy to seal `approved` over. The detector scans
the WHOLE spec tree — not just `must` acceptance-criteria — because the real defect
spans both a story `must` (a hanging parameter in an AC) AND free "still-open" business
questions living in the session notes; a must-AC-only scan would miss the latter. It
surfaces every marker so `--status` can list them and the `--approve` flow can warn
before sealing an artifact that still carries one.

SCRIPT-vs-LLM split: a pure marker scan over committed spec text. No judgment about
whether the question is important — it just finds the markers and names the file/line.

Marker set is diacritic-EXACT Vietnamese + English (the PO authors them with full
diacritics; stripping would trade missed-marker risk for false positives). To extend
it, add a pattern to MARKERS and a variant to the test; the scan stays a single
detection home (status and the approve flow both import it — no second scanner).

CLI:
    open_questions.py --root <project-dir>
        Prints {schema_version, open_questions:[{file,line,marker,snippet}...]}.
        Always exits 0.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from encoding_utils import configure_utf8_console, emit_json

configure_utf8_console()

# Open-question markers. Case-insensitive; the Vietnamese ones are matched with full
# diacritics (the PO writes them that way). `TBD` / `to be determined` are bounded so a
# word merely containing the letters does not false-positive.
MARKERS: List[re.Pattern] = [
    re.compile(r"cần\s+PO\s+xác\s+định", re.IGNORECASE),
    re.compile(r"cần\s+xác\s+định", re.IGNORECASE),
    re.compile(r"vẫn\s+còn\s+mở", re.IGNORECASE),
    re.compile(r"chưa\s+chốt", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bto[\s-]be[\s-]determined\b", re.IGNORECASE),
]

# Subtrees under docs/product that are NOT PO prose — generated visuals, graph
# snapshots, the memory layer — are skipped so a marker in machine output never
# false-flags. Everything else (`.session.md` included, where the "still open"
# business questions live) is in scope.
_SKIP_DIR_PARTS = frozenset({"visuals", ".snapshots", ".memory"})


def _snippet(line: str, limit: int = 160) -> str:
    s = line.strip()
    return s if len(s) <= limit else s[: limit - 1] + "…"


def scan_file(path: Path, rel: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every open-question marker hit in one file → [{file, line, marker, snippet}].

    `rel` is the path string reported back (caller passes a root-relative path); it
    defaults to the file name. Unreadable files yield []."""
    label = rel if rel is not None else path.name
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return []
    hits: List[Dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat in MARKERS:
            m = pat.search(line)
            if m:
                hits.append({
                    "file": label,
                    "line": lineno,
                    "marker": m.group(0),
                    "snippet": _snippet(line),
                })
                break  # one hit per line is enough to flag it
    return hits


def scan(root) -> List[Dict[str, Any]]:
    """All open-question markers across the spec's `docs/product` tree.

    Scans every `.md` under docs/product (stories/epics/prds/PRODUCT/brd/.session.md),
    skipping the non-prose visuals/snapshot/memory subtrees. Sorted by (file, line) for
    deterministic output. Empty when docs/product is absent or carries no markers."""
    root_res = Path(root).resolve()
    base = root_res / "docs" / "product"
    if not base.is_dir():
        return []
    hits: List[Dict[str, Any]] = []
    for path in base.glob("**/*.md"):
        if not path.is_file():
            continue
        if _SKIP_DIR_PARTS & set(path.relative_to(base).parts[:-1]):
            continue
        hits.extend(scan_file(path, rel=path.relative_to(root_res).as_posix()))
    hits.sort(key=lambda h: (h["file"], h["line"]))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    emit_json({"schema_version": "1.0", "open_questions": scan(args.root)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
