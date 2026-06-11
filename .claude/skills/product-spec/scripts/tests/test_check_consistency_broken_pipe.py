"""check_consistency must survive a closed downstream pipe (TDD RED).

The script's CLI contract is "always exits 0". But piping its (large) JSON stdout into a
consumer that closes early — e.g. `check_consistency.py --root . | head` — makes the final
`print()` write to a closed pipe, which raises BrokenPipeError and prints a traceback while
exiting non-zero. That breaks the contract and noises the PO's terminal.

This drives the SIGPIPE-safe emit: a broken downstream pipe must end the process cleanly
(exit 0, no traceback on stderr).
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
CHECK = SCRIPTS_DIR / "check_consistency.py"

_PRODUCT_MD = """---
id: PRODUCT
type: product
status: draft
lang: en
name: "Acme"
core_value: "do one thing well"
personas: [user]
---
"""

_BRD_MD = """---
id: BRD
type: brd
status: approved
lang: en
version: 1.0.0
goals:
  - id: BRD-G1
    title: "A goal"
    metrics: [north-star]
    status: approved
---

# BRD
"""

_STORY_TMPL = """---
id: PRD-BULK-E1-S{n}
type: story
epic: PRD-BULK-E1
status: draft
lang: en
version: 0.1.0
scope: in
moscow: must
horizon: now
size: S
acceptance_criteria:
  - "Given precondition {n}, when the user acts, then the system responds."
  - "Given a second precondition {n}, when the user retries, then it still holds."
---

# Story {n}
"""


def _big_spec(tmp_path: Path, n_stories: int = 400) -> Path:
    """A spec with enough story nodes that the JSON stdout comfortably exceeds the OS
    pipe buffer (~64KB) — so a downstream `head` closing early reliably triggers the
    broken-pipe write the fix must absorb."""
    prod = tmp_path / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir()
    (prod / "stories").mkdir()
    (prod / "PRODUCT.md").write_text(_PRODUCT_MD, encoding="utf-8")
    (prod / "brd.md").write_text(_BRD_MD, encoding="utf-8")
    for i in range(n_stories):
        (prod / "stories" / f"PRD-BULK-E1-S{i}.md").write_text(
            _STORY_TMPL.format(n=i), encoding="utf-8"
        )
    return tmp_path


def test_check_consistency_survives_broken_pipe(tmp_path):
    proj = _big_spec(tmp_path)

    producer = subprocess.Popen(
        [sys.executable, str(CHECK), "--root", str(proj)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    # Consumer reads a few bytes then closes — slamming the pipe shut under the producer.
    consumer = subprocess.Popen(
        ["head", "-c", "16"], stdin=producer.stdout, stdout=subprocess.DEVNULL
    )
    producer.stdout.close()  # let the producer receive SIGPIPE/EPIPE, not this process
    consumer.wait()
    _out, err = producer.communicate()

    assert producer.returncode == 0, (
        f"check_consistency must exit 0 on a broken downstream pipe, got {producer.returncode}; "
        f"stderr:\n{err.decode('utf-8', 'replace')}"
    )
    assert b"BrokenPipeError" not in err and b"Traceback" not in err, (
        "a broken pipe must not print a traceback:\n" + err.decode("utf-8", "replace")
    )
