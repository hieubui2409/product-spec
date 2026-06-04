"""pytest scaffolding for the product-spec-critique script suite.

Kept minimal: it only puts `product-spec-critique/scripts` on sys.path so the test modules
can `import critique_scan`. Reusable helpers live in `critique_test_support.py` (a
uniquely-named module so a combined run with product-spec's own `conftest.py`
cannot collide on the module name).
"""

import socket
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


class OfflineGuardViolation(RuntimeError):
    """Raised when a test attempts a real network connection under the offline guard."""


@pytest.fixture(autouse=True)
def _offline_guard(monkeypatch):
    """Offline enforcement.

    The critique skill makes NO network calls at runtime. When ``CK_OFFLINE`` is set
    (the CI gate sets it), block ``socket.socket.connect`` so any *future* net call
    fails loudly instead of silently exfiltrating. Local runs without the env var are
    unaffected (no-op), so this never changes developer-machine behaviour.
    """
    import os

    if not os.environ.get("CK_OFFLINE"):
        return

    def _blocked(*_a, **_k):
        raise OfflineGuardViolation(
            "network access blocked under CK_OFFLINE — critique must stay offline at runtime"
        )

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
