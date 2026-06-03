"""pytest scaffolding for the product-spec-critique script suite.

Kept minimal: it only puts `product-spec-critique/scripts` on sys.path so the test modules
can `import critique_scan`. Reusable helpers live in `critique_test_support.py` (a
uniquely-named module so a combined run with product-spec's own `conftest.py`
cannot collide on the module name).
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
