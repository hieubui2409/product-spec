#!/usr/bin/env python3
"""ingest_raw_inputs — deterministic read-fence + filter for `--discover` (E2).

`--discover` ingests raw upstream text (interview transcripts, support dumps, competitor notes) and
proposes CANDIDATE personas/problems/JTBD to SEED the Vision/BRD interview. This is the broadest read
surface in the skill, so the read side is hard-fenced (Security F3 — `fs_guard` is write-only):

  * **Project-root fence:** every input path is resolved (collapsing `..`, following symlinks) and must
    stay inside the project root; a traversal/symlink-escape is refused (reuse `fs_guard._is_within`).
  * **Extension allow-list:** `.md` / `.txt` only — everything else is rejected.
  * **Dotfile exclusion:** any path component starting with `.` (`.env`, `.aws`, `.ssh`, …) is skipped
    even when reached inside a directory walk — no secret-file disclosure path.
  * **Size cap** per file + **bounded directory recursion** (depth + file-count cap) so `--discover <dir>`
    cannot fan out unbounded.

The script ONLY reads + filters + scaffolds; the LLM synthesizes the candidate seeds and the interview
confirms each field (GATE-NEVER-ASSUME — nothing is committed here). The caller echoes the resolved
accepted list back to the PO for confirmation before any synthesis.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from encoding_utils import configure_utf8_console
from fs_guard import _is_within

configure_utf8_console()

ALLOWED_EXT = {".md", ".txt"}
DEFAULT_MAX_BYTES = 1_000_000   # 1 MB per file
DEFAULT_MAX_FILES = 50          # bounded directory fan-out
DEFAULT_MAX_DEPTH = 4           # bounded directory recursion


def _has_dotfile_component(resolved: Path, root: Path) -> bool:
    """True if any path component (relative to root) starts with a dot — excludes `.env`,
    `.aws`, `.ssh`, `.git`, etc. even when reached inside a walked directory."""
    try:
        rel = resolved.relative_to(root)
    except ValueError:
        return True  # outside root → treat as excluded (the fence rejects it anyway)
    return any(part.startswith(".") for part in rel.parts)


def _classify_file(resolved: Path, root: Path, max_bytes: int) -> Optional[str]:
    """None = accept; otherwise a rejection reason string."""
    if not _is_within(resolved, root):
        return "outside project root"
    if _has_dotfile_component(resolved, root):
        return "dotfile/secret-path excluded"
    if resolved.suffix.lower() not in ALLOWED_EXT:
        return f"extension {resolved.suffix or '(none)'} not in {sorted(ALLOWED_EXT)}"
    try:
        if resolved.stat().st_size > max_bytes:
            return f"file exceeds size cap ({max_bytes} bytes)"
    except OSError as exc:
        return f"stat failed: {exc}"
    return None


def resolve_inputs(paths: List[str], root, *, max_files: int = DEFAULT_MAX_FILES,
                   max_depth: int = DEFAULT_MAX_DEPTH, max_bytes: int = DEFAULT_MAX_BYTES) -> Dict[str, Any]:
    """Resolve + fence + filter the PO-named inputs (files AND directories). Returns
    {accepted, rejected, truncated}. Directories are walked with bounded depth + file-count cap."""
    root = Path(root).resolve()
    accepted: List[str] = []
    rejected: List[Dict[str, str]] = []
    truncated = False

    def _accept_or_reject(p: Path):
        nonlocal truncated
        if len(accepted) >= max_files:
            truncated = True
            return
        # `iterdir()` yields UN-resolved entries and `_is_within` is purely lexical, so resolve
        # FIRST: a symlink reached inside a walked dir must not slip past the fence (the escape
        # the top-level path handling already guards). Store + classify the resolved target.
        resolved = p.resolve(strict=False)
        if not _is_within(resolved, root):
            rejected.append({"path": str(p), "reason": "outside project root (symlink/escape)"})
            return
        reason = _classify_file(resolved, root, max_bytes)
        if reason is None:
            accepted.append(str(resolved))
        else:
            rejected.append({"path": str(resolved), "reason": reason})

    def _walk_dir(d: Path, depth: int):
        nonlocal truncated
        if depth > max_depth:
            truncated = True
            return
        try:
            entries = sorted(d.iterdir())
        except OSError as exc:
            rejected.append({"path": str(d), "reason": f"cannot list dir: {exc}"})
            return
        for entry in entries:
            if len(accepted) >= max_files:
                truncated = True
                return
            # Skip dotted dirs/files outright (no descent into .git/.aws/etc.).
            if entry.name.startswith("."):
                rejected.append({"path": str(entry), "reason": "dotfile/secret-path excluded"})
                continue
            # Resolve BEFORE descending/accepting: a symlinked dir OR file that escapes root is
            # refused here (resolve-then-fence), closing the directory-walk symlink-escape hole.
            entry_resolved = entry.resolve(strict=False)
            if not _is_within(entry_resolved, root):
                rejected.append({"path": str(entry), "reason": "outside project root (symlink/escape)"})
                continue
            if entry.is_dir():
                _walk_dir(entry, depth + 1)
            else:
                _accept_or_reject(entry)

    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = root / p
        resolved = p.resolve(strict=False)
        if not _is_within(resolved, root):
            rejected.append({"path": str(resolved), "reason": "outside project root"})
            continue
        if not resolved.exists():
            rejected.append({"path": str(resolved), "reason": "does not exist"})
            continue
        if resolved.is_dir():
            _walk_dir(resolved, 1)
        else:
            _accept_or_reject(resolved)

    return {"accepted": accepted, "rejected": rejected, "truncated": truncated}


def draft_scaffold(resolution: Dict[str, Any], root, *, max_bytes: int = DEFAULT_MAX_BYTES) -> Dict[str, Any]:
    """Read the accepted files (bounded) + emit an EMPTY candidate scaffold for the LLM to fill.
    The script provides raw text only; persona/problem/JTBD synthesis is the LLM's job, and the
    Vision interview confirms each before anything is written (GATE-NEVER-ASSUME)."""
    root = Path(root).resolve()
    files: List[Dict[str, Any]] = []
    for ap in resolution["accepted"]:
        p = Path(ap)
        try:
            text = p.read_text(encoding="utf-8", errors="replace")[:max_bytes]
        except OSError as exc:
            files.append({"path": ap, "error": str(exc)})
            continue
        files.append({"path": ap, "bytes": len(text), "text": text})
    return {
        "files": files,
        "rejected": resolution["rejected"],
        "truncated": resolution["truncated"],
        # Empty buckets — the LLM proposes candidates; nothing is auto-committed.
        "candidates": {"personas": [], "problems": [], "jtbd": []},
        "note": "candidates are EMPTY by design — the LLM synthesizes them, the Vision interview "
                "confirms each field before any write (GATE-NEVER-ASSUME).",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Read-fence + filter raw discovery inputs.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--path", action="append", default=[], required=True,
                    help="input file or directory (repeatable); fenced to the project root.")
    ap.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    ap.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--scaffold", action="store_true", help="also read accepted files + emit the draft scaffold")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    resolution = resolve_inputs(args.path, root, max_files=args.max_files,
                                max_depth=args.max_depth, max_bytes=args.max_bytes)
    out: Dict[str, Any] = resolution
    if args.scaffold:
        out = draft_scaffold(resolution, root, max_bytes=args.max_bytes)
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
