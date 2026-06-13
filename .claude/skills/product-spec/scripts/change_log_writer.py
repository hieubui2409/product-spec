#!/usr/bin/env python3
"""change_log_writer — append-only monthly rotation writer for change-log entries.

Provides `write_change_log_entry(root, entry_md, *, when=None)`:
  - Resolves the month from the entry's heading date or from `when` (YYYY-MM-DD).
  - Writes to `docs/product/change-log/<YYYY-MM>.md` (creates dir/file as needed).
  - Dedup guard: an entry with the same (date, artifact, action) triple is NOT
    appended again (idempotent re-write).
  - `when` is injectable so tests are deterministic; CLI callers pass `when=None`
    to use the entry's own parsed date.

Back-compat: the legacy `docs/product/change-log.md` is untouched by the writer.
`assemble_audit_trail._change_log_paths` reads both the legacy file and the rolled
month files for the full history.

Usage from generate_templates.py --write for change_log_entry:
    from change_log_writer import write_change_log_entry
    write_change_log_entry(root, rendered_entry_md)
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from fs_guard import assert_under_docs_product

# Matches the heading line "## YYYY-MM-DD — ..." that starts every change-log entry.
_HEADING_DATE_RE = re.compile(r"^##\s+(?P<date>\d{4}-\d{2}-\d{2})\s+—", re.MULTILINE)

# These three fields form the dedup key; we extract them from the entry text.
_ARTIFACT_RE = re.compile(r"\*\*Artifact[^:]*:\*\*\s*(?P<ids>.+?)(?:\s*\(|\s*$)", re.MULTILINE)
_ACTION_RE = re.compile(r"\*\*Action[^:]*:\*\*\s*(?P<action>[^|\n]+?)(?:\s*\||\s*$)", re.MULTILINE)


def _is_real_date(date: str) -> bool:
    """True iff `date` is a real YYYY-MM-DD calendar date (rejects 2026-13-45,
    2026-02-30, etc.) — strptime validates format AND calendar validity."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _parse_date(entry_md: str, when: Optional[str]) -> str:
    """Return a YYYY-MM-DD date string for the entry.

    Priority: `when` param (deterministic injection) > heading date in entry text.
    Both sources are validated as REAL calendar dates so the month-key derivation
    (`date[:7]`) can never produce a bogus month dir. Raises ValueError if neither
    is available or the resolved date is not a real date.
    """
    if when:
        if not _is_real_date(when):
            raise ValueError(
                f"write_change_log_entry: `when` must be a real YYYY-MM-DD date, got {when!r}"
            )
        return when
    m = _HEADING_DATE_RE.search(entry_md)
    if m:
        date = m.group("date")
        if not _is_real_date(date):
            raise ValueError(
                f"write_change_log_entry: entry heading date {date!r} is not a real calendar date"
            )
        return date
    raise ValueError(
        "write_change_log_entry: cannot determine entry date — "
        "no `when` provided and no '## YYYY-MM-DD —' heading found in entry_md"
    )


def _month_key(date: str) -> str:
    """Return 'YYYY-MM' from a 'YYYY-MM-DD' date string."""
    return date[:7]


def _dedup_key(entry_md: str, date: str) -> tuple[str, str, str]:
    """Return (date, artifact_id, action) as the dedup triple."""
    art_m = _ARTIFACT_RE.search(entry_md)
    artifact = art_m.group("ids").strip() if art_m else ""
    action_m = _ACTION_RE.search(entry_md)
    action = action_m.group("action").strip() if action_m else ""
    return (date, artifact, action)


def _parse_existing_triples(existing_text: str) -> set[tuple[str, str, str]]:
    """Parse the existing month-file text into a set of (date, artifact, action) triples.

    Uses the same heading, artifact, and action regexes as _dedup_key so the
    comparison is always tuple-vs-tuple — never three independent substring checks.
    """
    triples: set[tuple[str, str, str]] = set()
    heading_re = re.compile(r"^##\s+(?P<date>\d{4}-\d{2}-\d{2})\s+—", re.MULTILINE)
    matches = list(heading_re.finditer(existing_text))
    for i, m in enumerate(matches):
        date = m.group("date")
        block = existing_text[m.end(): matches[i + 1].start() if i + 1 < len(matches) else len(existing_text)]
        art_m = _ARTIFACT_RE.search(block)
        artifact = art_m.group("ids").strip() if art_m else ""
        action_m = _ACTION_RE.search(block)
        action = action_m.group("action").strip() if action_m else ""
        triples.add((date, artifact, action))
    return triples


def _already_present(existing_text: str, dedup_key: tuple[str, str, str]) -> bool:
    """Return True when a matching (date, artifact, action) triple exists in the file.

    Parses the file into per-entry triples and compares as a unit so two entries
    whose fields partially overlap do not falsely suppress a genuinely distinct triple.
    """
    return dedup_key in _parse_existing_triples(existing_text)


def write_change_log_entry(root, entry_md: str, *, when: Optional[str] = None) -> Path:
    """Append `entry_md` to `docs/product/change-log/<YYYY-MM>.md`.

    Args:
        root:     Project root (Path or str).
        entry_md: Rendered change-log entry markdown text.
        when:     Optional YYYY-MM-DD override for the month routing (injectable for
                  deterministic tests). Defaults to the date parsed from entry_md's
                  heading.

    Returns:
        Path to the month file that was written (or already contained the entry).

    Raises:
        ValueError: if the date cannot be determined.
    """
    root = Path(root).resolve()
    date = _parse_date(entry_md, when)
    month = _month_key(date)

    cl_dir = root / "docs" / "product" / "change-log"
    month_file = cl_dir / f"{month}.md"
    # Soft-fence the constructed target before any mkdir/write. `month` is already
    # constrained to YYYY-MM by the validated date, but routing it through the shared
    # assert keeps the "every script write lands under docs/product/" invariant whole.
    assert_under_docs_product(month_file, root)
    cl_dir.mkdir(parents=True, exist_ok=True)

    # Read existing content for dedup check
    existing = ""
    if month_file.exists():
        try:
            existing = month_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            existing = ""

    key = _dedup_key(entry_md, date)
    if _already_present(existing, key):
        return month_file  # idempotent — nothing written

    # Ensure the entry ends with a newline before appending
    body = entry_md if entry_md.endswith("\n") else entry_md + "\n"

    # Append (or create) — newline separator between entries when file non-empty
    separator = "\n" if existing and not existing.endswith("\n\n") else ""
    with open(month_file, "a", encoding="utf-8", newline="") as fh:
        fh.write(separator + body)

    return month_file
