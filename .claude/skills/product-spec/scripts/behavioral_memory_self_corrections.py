"""
behavioral_memory_self_corrections — 3E LLM self-correction store.

Owns the recurring-slip log persisted in
`docs/product/.memory/self-corrections.json`. The caller supplies the store
path so behavioral_memory._self_corrections_path remains the monkeypatch
target (tests patch that module-level function, not this one).

All writes go through the shared soft fence (fs_guard) so this store can
never escape the spec boundary.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fs_guard import assert_under_docs_product

from behavioral_memory_po_style import BehavioralError


# The five operating principles a self-correction MUST cite.
VIOLATED_RULES = (
    "frontmatter_source_of_truth",
    "dry",
    "script_vs_llm_split",
    "no_silent_reversal",
    "never_overwrite_prose",
)
_VIOLATED_RULES_SET = frozenset(VIOLATED_RULES)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_raw(path: Path) -> Dict[str, Any]:
    """Parse self-corrections.json at `path`. Missing/corrupt/wrong-shaped file
    degrades to an empty store — the read path never raises."""
    empty: Dict[str, Any] = {"schema_version": "1", "corrections": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return empty
    if not isinstance(data, dict) or not isinstance(data.get("corrections"), list):
        return empty
    return data


def load(path: Path) -> List[Dict[str, Any]]:
    """Return the list of self-correction rows (empty when the store is absent)."""
    return list(load_raw(path).get("corrections", []))


def record(path: Path, *, slip: str, violated_rule: str,
           reminder: str, root=None, now_fn=None) -> Path:
    """Append a slip, or increment the frequency of an identical prior slip.

    `path` is the resolved store path supplied by behavioral_memory so its
    path function stays the sole monkeypatch target. `now_fn` is optionally
    supplied by behavioral_memory so the test's `monkeypatch.setattr(bm, "_now", …)`
    intercepts the timestamp used here — without it the submodule's own `_now()`
    would bypass the patch. Validates BEFORE any write. The write goes through
    the soft fence.
    """
    if not isinstance(slip, str) or not slip.strip():
        raise BehavioralError("self-correction 'slip' must be a non-empty string")
    if not isinstance(reminder, str) or not reminder.strip():
        raise BehavioralError(
            "self-correction 'reminder' must be a non-empty string (the corrective lesson)"
        )
    if violated_rule not in _VIOLATED_RULES_SET:
        raise BehavioralError(
            f"self-correction 'violated_rule' must cite one of the five operating "
            f"principles {list(VIOLATED_RULES)}; got {violated_rule!r}"
        )

    data = load_raw(path)
    rows: List[Dict[str, Any]] = list(data.get("corrections", []))
    now = now_fn() if now_fn is not None else _now()

    for row in rows:
        if row.get("slip") == slip and row.get("violated_rule") == violated_rule:
            row["frequency"] = int(row.get("frequency", 0)) + 1
            row["last_seen"] = now
            row["reminder"] = reminder
            break
    else:
        rows.append({
            "slip": slip,
            "violated_rule": violated_rule,
            "frequency": 1,
            "last_seen": now,
            "reminder": reminder,
        })

    return _write(path, {"schema_version": "1", "corrections": rows}, root=root)


def _write(path: Path, data: Dict[str, Any], root=None) -> Path:
    assert_under_docs_product(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return path
