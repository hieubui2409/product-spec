#!/usr/bin/env python3
"""
behavioral_memory — read/write/validate the two BEHAVIORAL memory stores.

These extend the memory layer with the part that shapes how the skill *talks*
and *behaves*, distinct from the structural facts (`decisions.md`,
`judgments.json`):

  - **3D PO-style** (`docs/product/.memory/po-style.yaml`, committed): the
    product owner's own voice — register, domain vocabulary, recurring asks,
    and do/don't phrasing — kept **lang-keyed** (`en` / `vi`).
  - **3E LLM-self-correction** (`docs/product/.memory/self-corrections.json`,
    committed): a recurring slip + the operating principle it violated + a
    frequency/last-seen stamp + a corrective reminder.

SCRIPT-vs-LLM split: everything here is deterministic structural work — read,
write, shape-validate, lang-key resolution, frequency increment, the DRY guard.
The LLM observes the PO's voice and decides what to write; the script only
validates the shape and persists it.

All writes go through the shared soft fence (`fs_guard`) so a store write can
never escape the spec boundary.

The path helpers `_po_style_path`, `_self_corrections_path`, and `_now` are
defined at module level here so the test monkeypatches that target this module
by name (`bm._po_style_path`, `bm._now`) continue to intercept correctly. The
submodules (behavioral_memory_po_style, behavioral_memory_self_corrections)
receive the resolved path from these helpers rather than computing it themselves.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from check_consistency import ENUMS
from encoding_utils import configure_utf8_console

import behavioral_memory_po_style as _ps
import behavioral_memory_self_corrections as _sc

configure_utf8_console()


# Re-export so external callers that do `from behavioral_memory import BehavioralError`
# continue to resolve it.
BehavioralError = _ps.BehavioralError

# Re-export closed-enum constants used by the CLI and by tests.
LANGS = _ps.LANGS
PO_STYLE_LIST_FIELDS = _ps.PO_STYLE_LIST_FIELDS
VIOLATED_RULES = _sc.VIOLATED_RULES


# ---------------------------------------------------------------------------
# Path helpers — defined HERE so monkeypatch targets `bm._po_style_path` /
# `bm._self_corrections_path` / `bm._now` at the behavioral_memory module level.
# ---------------------------------------------------------------------------

def _po_style_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "po-style.yaml"


def _self_corrections_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "self-corrections.json"


def _now() -> str:
    """Memory-layer UTC timestamp. Defined here for monkeypatching by tests
    (test_behavioral_memory patches `bm._now`); delegated to self-corrections
    via the submodule's own internal _now (same formula, separate object)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# The CLOSED-ENUM structural values behavioral memory must never re-home.
# Sourced from check_consistency.ENUMS (single home).
_STRUCTURAL_ENUM_VALUES = frozenset(
    v.lower() for v in (ENUMS["scope"] | ENUMS["moscow"] | ENUMS["horizon"])
)


# ---------------------------------------------------------------------------
# 3D PO-style — public API (delegates to behavioral_memory_po_style)
# ---------------------------------------------------------------------------

def _load_po_style_raw(root) -> Dict[str, Any]:
    return _ps.load_raw(_po_style_path(root))


def load_po_style(root, lang: str = "en") -> Dict[str, Any]:
    """Return the voice block for ONE language (defaults filled)."""
    return _ps.load(_po_style_path(root), lang=lang)


def record_po_style(root, lang: str, *,
                    vocabulary: Optional[List[str]] = None,
                    recurring_asks: Optional[List[str]] = None,
                    do: Optional[List[str]] = None,
                    dont: Optional[List[str]] = None,
                    register: Optional[str] = None) -> Path:
    """Merge an observed voice block into the given `lang` partition and persist."""
    return _ps.record(
        _po_style_path(root), lang, _STRUCTURAL_ENUM_VALUES,
        vocabulary=vocabulary, recurring_asks=recurring_asks,
        do=do, dont=dont, register=register, root=root,
    )


def _write_po_style(root, raw: Dict[str, Any]) -> Path:
    """Internal write path — delegates to the submodule."""
    return _ps._write(_po_style_path(root), raw, root=root)


# ---------------------------------------------------------------------------
# 3E self-correction — public API (delegates to behavioral_memory_self_corrections)
# ---------------------------------------------------------------------------

def _load_self_corrections_raw(root) -> Dict[str, Any]:
    return _sc.load_raw(_self_corrections_path(root))


def load_self_corrections(root) -> List[Dict[str, Any]]:
    """Return the list of self-correction rows (empty when the store is absent)."""
    return _sc.load(_self_corrections_path(root))


def record_self_correction(root, *, slip: str, violated_rule: str,
                           reminder: str) -> Path:
    """Append a slip, or increment the frequency of an identical prior slip."""
    return _sc.record(
        _self_corrections_path(root),
        slip=slip, violated_rule=violated_rule, reminder=reminder,
        root=root, now_fn=_now,
    )


def _write_self_corrections(root, data: Dict[str, Any]) -> Path:
    """Internal write path — delegates to the submodule."""
    return _sc._write(_self_corrections_path(root), data, root=root)


# ---------------------------------------------------------------------------
# CLI — read (`--dump`) + the explicit 3D voice WRITE entry point (`--voice`)
# ---------------------------------------------------------------------------

def _split_csv(value: Optional[str]) -> Optional[List[str]]:
    """Parse a comma-separated CLI value into a trimmed, non-empty list."""
    if value is None:
        return None
    return [tok.strip() for tok in value.split(",") if tok.strip()]


def _run_voice(args) -> int:
    fields: Dict[str, Any] = {
        "vocabulary": _split_csv(args.vocabulary),
        "recurring_asks": _split_csv(args.recurring_asks),
        "do": _split_csv(args.do),
        "dont": _split_csv(args.dont),
        "register": args.register,
    }
    if all(v is None for v in fields.values()):
        print(
            "--voice: nothing to record — pass at least one writable field "
            "(--register, --vocabulary, --recurring-asks, --do, --dont).",
            file=sys.stderr,
        )
        return 0

    try:
        path = record_po_style(args.root, args.lang, **fields)
    except BehavioralError as exc:
        print(f"BehavioralError: {exc}", file=sys.stderr)
        return 1
    print(f"recorded voice ({args.lang}) → {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--lang", default="en", choices=sorted(LANGS),
                    help="po-style language partition to read (--dump) or write (--voice)")
    ap.add_argument("--dump", choices=["po-style", "self-corrections"],
                    default="po-style",
                    help="which store to READ and print as JSON (read-only; writes go "
                         "through --voice / record_self_correction)")
    ap.add_argument("--voice", action="store_true",
                    help="WRITE the PO's 3D voice into the --lang partition via "
                         "record_po_style (union-merge lists, latest --register wins)")
    ap.add_argument("--register",
                    help="--voice: the PO's register/tone (scalar; latest-wins)")
    ap.add_argument("--vocabulary",
                    help="--voice: comma-separated PO domain terms (union-merged)")
    ap.add_argument("--recurring-asks", dest="recurring_asks",
                    help="--voice: comma-separated recurring PO asks (union-merged)")
    ap.add_argument("--do",
                    help="--voice: comma-separated do-phrasings (union-merged)")
    ap.add_argument("--dont",
                    help="--voice: comma-separated dont-phrasings (union-merged)")
    args = ap.parse_args()

    if args.voice:
        return _run_voice(args)

    if args.dump == "po-style":
        print(json.dumps(load_po_style(args.root, lang=args.lang),
                         indent=2, ensure_ascii=False))
    else:
        print(json.dumps(load_self_corrections(args.root),
                         indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
