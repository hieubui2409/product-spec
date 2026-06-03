#!/usr/bin/env python3
"""apply_critique_progress — resume markers for `--apply-critique` (E1, C4).

Per-finding progress keyed by the deterministic fingerprint → `{dec, disposition}`, stored at
`docs/product/.memory/apply-critique/<lens_findings_hash>.json`. The loop records each resolved
finding here; a re-run reads it FIRST and skips already-resolved fingerprints, so an interrupted
run never double-records a DEC and never re-litigates a resolved finding (the anti-re-litigation
contract). The write is fenced under docs/product/ via `fs_guard` like every other memory write.

CLI:
    apply_critique_progress.py --root <dir> --lens-hash <h> --show
    apply_critique_progress.py --root <dir> --lens-hash <h> --record \\
        --fingerprint <fp> --dec DEC-3 --disposition keep|change|defer
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from encoding_utils import configure_utf8_console
from fs_guard import assert_under_docs_product

configure_utf8_console()

_DISPOSITIONS = {"keep", "change", "defer"}


def progress_path(root, lens_findings_hash: str) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "apply-critique" / f"{lens_findings_hash}.json"


def load_progress(root, lens_findings_hash: str) -> Dict[str, Any]:
    """Resolved fingerprints → {dec, disposition}. Missing/corrupt → empty (fail-soft)."""
    path = progress_path(root, lens_findings_hash)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def record_resolution(root, lens_findings_hash: str, fingerprint: str,
                      dec: Optional[str], disposition: str) -> Dict[str, Any]:
    """Mark one finding resolved. Idempotent per fingerprint (re-record overwrites the
    same key, so a resumed run that re-resolves is harmless). Returns the updated map."""
    if disposition not in _DISPOSITIONS:
        raise ValueError(f"disposition must be one of {sorted(_DISPOSITIONS)}, got {disposition!r}")
    path = progress_path(root, lens_findings_hash)
    assert_under_docs_product(path, root)  # fence before any write
    path.parent.mkdir(parents=True, exist_ok=True)
    data = load_progress(root, lens_findings_hash)
    data[fingerprint] = {"dec": dec, "disposition": disposition}
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
    return data


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--lens-hash", required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--show", action="store_true")
    mode.add_argument("--record", action="store_true")
    ap.add_argument("--fingerprint")
    ap.add_argument("--dec")
    ap.add_argument("--disposition")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.show:
            print(json.dumps({"resolved": load_progress(root, args.lens_hash)}, ensure_ascii=False, indent=2))
            return 0
        if not args.fingerprint or not args.disposition:
            raise ValueError("--record needs --fingerprint and --disposition")
        data = record_resolution(root, args.lens_hash, args.fingerprint, args.dec, args.disposition)
        print(json.dumps({"resolved": data, "written": True}, ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001 — analytical-script contract
        print(json.dumps({"error": "invalid_input", "message": str(exc), "written": False}, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    sys.exit(main())
