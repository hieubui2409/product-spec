#!/usr/bin/env python3
"""
register_store — shared primitives for the append-only fenced-record registers
(the Decision Register `DEC-<n>` + the Outcome Register `OUT-<n>`).

Both registers store one ruling/measurement per `---`-fenced YAML block and shared
byte-identical structural machinery in lockstep — the block-splitter regex, the
record-fence/heading injection escape, the best-effort file lock, and the raw id
scan. This module is the single home for that machinery so a fix lands once, not
twice. Each register module keeps ONLY its own specifics: the field schema, the
render template, the alloc/append flow, supersede-vs-verdict logic, and its choice
of atomic-vs-plain write.
"""

import contextlib
import re
from pathlib import Path
from typing import List

# Splits a register file into its `---`-fenced record blocks: each starts at a
# line-anchored `---` fence; `fm` = the YAML mini-frontmatter, `body` = the prose.
RECORD_RE = re.compile(
    r"^---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*?)(?=^---\s*$|\Z)",
    re.DOTALL | re.MULTILINE,
)
# A body line that is a bare `---` fence would split the file into a phantom record
# under RECORD_RE; neutralized on write (see escape_injection).
INJ_FENCE_RE = re.compile(r"(?m)^(---+\s*)$")


def escape_injection(text: str, heading_re: "re.Pattern") -> str:
    """Backslash-escape record-fence + register-heading line anchors in PO/finding-
    supplied text so it cannot smuggle a phantom record or heading, while preserving
    the text (markdown-correct: `\\---`, `\\## ` render literally but no longer match
    the line-anchored patterns). `heading_re` is the register's own
    `^##\\s+<PREFIX>` heading anchor (e.g. `## DEC-` / `## OUT-`)."""
    out = INJ_FENCE_RE.sub(r"\\\1", text or "")
    return heading_re.sub(r"\\\1", out)


@contextlib.contextmanager
def register_lock(lock_path):
    """Best-effort exclusive lock so alloc-id + append happen as ONE critical section
    (closes the TOCTOU window where two looped allocs could collide). POSIX uses
    fcntl.flock; on platforms without it the lock degrades to a no-op (single-PO
    desktop use) — the prior behaviour, not a regression. `lock_path` is the full
    path to the register's own lock file."""
    lock_path = Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, "w")
    try:
        try:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        yield
    finally:
        with contextlib.suppress(Exception):
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        fh.close()


def scan_record_ids(text: str) -> List[str]:
    """Every raw `id:` value across all `---`-fenced blocks, INCLUDING blocks whose
    YAML is otherwise unparseable — the source-of-truth for id allocation so a
    corrupt-but-id-bearing block still reserves its number (a later repair can never
    collide with an id allocated meanwhile)."""
    ids: List[str] = []
    for m in RECORD_RE.finditer(text):
        im = re.search(r"^id:\s*(\S+)\s*$", m.group("fm"), re.MULTILINE)
        if im:
            ids.append(im.group(1).strip())
    return ids
