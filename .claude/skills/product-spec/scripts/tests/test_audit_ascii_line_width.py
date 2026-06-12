"""ASCII audit trail output must not overflow a 120-column terminal.

Markdown format must keep full untruncated cell text (no truncation side-effect).

The invariant: `render_ascii` with long cell content must produce lines ≤ 120
chars; `render_markdown` must preserve the full text regardless of length.
"""
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from assemble_audit_trail import render_ascii, render_markdown  # noqa: E402

_LONG = "x" * 200  # a cell value that would overflow an 80-120 col terminal

_FIXTURE = {
    "schema_version": "1.0",
    "root": "/tmp/fake",
    "events": [
        {
            "date": "2026-01-01",
            "artifact": "PRD-CHECKOUT",
            "action": "approved",
            "who_approved": "Jane Doe",
            "what_drifted": _LONG,
            "dec_ref": "DEC-1",
            "reconciled": True,
        },
        {
            "date": "2026-01-02",
            "artifact": "PRD-CHECKOUT-E1",
            "action": "approved (stale)",
            "who_approved": "Bob Smith",
            "what_drifted": _LONG,
            "dec_ref": "",
            "reconciled": False,
        },
    ],
    "unreconciled_count": 1,
}

MAX_LINE = 120


def test_ascii_lines_within_budget():
    """Every line produced by render_ascii must be ≤ MAX_LINE characters."""
    output = render_ascii(_FIXTURE)
    long_lines = [line for line in output.splitlines() if len(line) > MAX_LINE]
    assert not long_lines, (
        f"render_ascii produced {len(long_lines)} line(s) exceeding {MAX_LINE} chars. "
        f"Longest: {max(len(l) for l in long_lines)} chars. "
        f"First offender (truncated): {long_lines[0][:80]!r}…"
    )


def test_markdown_preserves_full_text():
    """render_markdown must keep the full cell text (no truncation)."""
    output = render_markdown(_FIXTURE)
    assert _LONG in output, (
        "render_markdown truncated long cell text — only render_ascii should truncate"
    )


def test_ascii_truncation_uses_ellipsis():
    """Truncated ASCII cells should end with '…' to signal truncation."""
    output = render_ascii(_FIXTURE)
    # The long value should appear truncated with an ellipsis somewhere
    assert "…" in output, (
        "render_ascii should use '…' when a cell is truncated for column budget"
    )
