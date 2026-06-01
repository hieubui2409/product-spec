#!/usr/bin/env python3
"""
behavioral_memory — read/write/validate the two BEHAVIORAL memory stores.

These extend the memory layer with the part that shapes how the skill *talks* and
*behaves*, distinct from the structural facts (`decisions.md`, `judgments.json`):

  - **3D PO-style** (`docs/product/.memory/po-style.yaml`, committed): the product
    owner's own voice — register, their domain vocabulary, recurring asks, and
    do/don't phrasing — kept **lang-keyed** (`en` / `vi`). It shapes generated
    OUTPUT wording (vision narrative, story descriptions, AskUserQuestion text). It
    never re-homes a structural fact (DRY); it only tunes phrasing.
  - **3E LLM-self-correction** (`docs/product/.memory/self-corrections.json`,
    committed now): a recurring slip + the operating principle it violated + a
    frequency/last-seen stamp + a corrective reminder. It guards the skill's own
    BEHAVIOR (a pre-flight self-check before at-risk operations), never the PO's
    voice. Honesty caveat: these triggers are LLM-discretionary — the store REDUCES
    recurrence, it is not a hard invariant that the store always accrues.

SCRIPT-vs-LLM split (CLAUDE.md): everything here is deterministic structural work —
read, write, shape-validate, lang-key resolution, frequency increment, the DRY
guard. The LLM observes the PO's voice and decides what to write; the script only
validates the shape and persists it. The DRY guard rejects copies of CLOSED-ENUM
structural values (script-decidable); persona-label copy detection is open
free-text and is an LLM-side check (documented in `references/behavioral-memory.md`).

All writes go through the shared soft fence (`fs_guard`) so a store write can never
escape the spec boundary.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from check_consistency import ENUMS
from encoding_utils import configure_utf8_console
from fs_guard import assert_under_docs_product

configure_utf8_console()


class BehavioralError(ValueError):
    """Raised on a write-path shape violation (bad lang, wrong type, missing /
    unknown rule, or a DRY-guard structural-fact copy). The write path validates so
    the on-disk store stays canonical; reads degrade to empty, never raise."""


# Languages the stores are keyed by. Mirrors the bilingual convention (en default).
LANGS = frozenset({"en", "vi"})

# The list-valued voice fields of a po-style lang block. `register` is the one
# scalar. Listing them here keeps the shape in a single home.
PO_STYLE_LIST_FIELDS = ("vocabulary", "recurring_asks", "do", "dont")

# The five operating principles a self-correction MUST cite (CLAUDE.md § Five
# Operating Principles). An un-anchored slip has no corrective lesson, so the
# citation is required and closed to this set.
VIOLATED_RULES = (
    "frontmatter_source_of_truth",  # 1. frontmatter is the structural truth
    "dry",                          # 2. one authoritative home per fact
    "script_vs_llm_split",          # 3. scripts do structure; LLM does judgment
    "no_silent_reversal",           # 4. never auto-flip an approved decision
    "never_overwrite_prose",        # 5. never overwrite the PO's own words
)
_VIOLATED_RULES_SET = frozenset(VIOLATED_RULES)

# The CLOSED-ENUM structural values behavioral memory must never re-home. These
# have authoritative homes in artifact frontmatter; copying one into the PO's
# vocabulary/do/dont would duplicate a fact (DRY violation) and is script-decidable.
# Sourced from the single home (`check_consistency.ENUMS`) so the set never drifts
# from the canonical scope/moscow/horizon enums; lowercased for the trimmed-token
# comparison below.
# Persona labels are deliberately ABSENT here — open free-text, not a closed enum;
# their copy detection is an LLM-side check, not this pure validator's job.
_STRUCTURAL_ENUM_VALUES = frozenset(
    v.lower() for v in (ENUMS["scope"] | ENUMS["moscow"] | ENUMS["horizon"])
)


# ----------------------------------------------------------------------------
# Store paths
# ----------------------------------------------------------------------------

def _po_style_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "po-style.yaml"


def _self_corrections_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "self-corrections.json"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _empty_lang_block() -> Dict[str, Any]:
    """A fresh per-lang voice block: every list field empty, register unset. A read
    of a lang with no observations resolves to this — never a crash."""
    block: Dict[str, Any] = {f: [] for f in PO_STYLE_LIST_FIELDS}
    block["register"] = None
    return block


# ----------------------------------------------------------------------------
# 3D PO-style — lang-keyed voice
# ----------------------------------------------------------------------------

def _load_po_style_raw(root) -> Dict[str, Any]:
    """Parse po-style.yaml into its lang-keyed shape. A missing file, non-mapping
    top level, or unparseable YAML degrades to an empty `{en, vi}` shape — the read
    path never raises (it only seeds prose phrasing; absence is benign)."""
    shape: Dict[str, Any] = {lang: _empty_lang_block() for lang in sorted(LANGS)}
    path = _po_style_path(root)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError):
        return shape
    if not isinstance(raw, dict):
        return shape

    voice = raw.get("voice")
    if not isinstance(voice, dict):
        return shape
    for lang in sorted(LANGS):
        block = voice.get(lang)
        if not isinstance(block, dict):
            continue
        for field in PO_STYLE_LIST_FIELDS:
            value = block.get(field)
            if isinstance(value, list):
                shape[lang][field] = [str(v) for v in value]
        reg = block.get("register")
        if isinstance(reg, str):
            shape[lang]["register"] = reg
    return shape


def load_po_style(root, lang: str = "en") -> Dict[str, Any]:
    """Return the voice block for ONE language (defaults filled). Reading `vi` never
    returns `en` voice — the store is strictly lang-partitioned so the PO's wording
    in one language never leaks into the prose generated in the other.

    An unknown `lang` degrades to an empty block (read path is tolerant)."""
    raw = _load_po_style_raw(root)
    return raw.get(lang, _empty_lang_block())


def _check_str_list(field: str, value: Any) -> List[str]:
    """Validate that a po-style list field is a list of strings; raise otherwise.
    Coerces members to str so a YAML scalar that round-tripped as int still stores
    cleanly — but a non-list (e.g. a bare string) is a real shape error."""
    if not isinstance(value, list):
        raise BehavioralError(
            f"po-style field {field!r} must be a list of strings; "
            f"got {type(value).__name__}"
        )
    return [str(v) for v in value]


def _assert_no_structural_copy(field: str, items: List[str]) -> None:
    """DRY guard: refuse a voice item that is EXACTLY a closed-enum structural value
    (scope/moscow/horizon). Comparison is case-insensitive on the trimmed token, so
    `Must` and `must` are both caught; a natural phrase that merely contains the
    word as a substring (`core shopper journey`) is NOT a copy and passes.

    Persona-label copy detection is intentionally NOT here — persona labels are open
    PO free-text, not a closed enum, and PRODUCT.md is not passed in. That check is
    LLM-side (see references/behavioral-memory.md), per the Script-vs-LLM split."""
    for item in items:
        token = item.strip().lower()
        if token in _STRUCTURAL_ENUM_VALUES:
            raise BehavioralError(
                f"po-style {field!r} entry {item!r} copies a closed-enum structural "
                f"value (scope/moscow/horizon). Behavioral memory shapes PHRASING "
                f"only; structural facts live in frontmatter (DRY). Use the PO's own "
                f"wording, not an enum value."
            )


def record_po_style(root, lang: str, *,
                    vocabulary: Optional[List[str]] = None,
                    recurring_asks: Optional[List[str]] = None,
                    do: Optional[List[str]] = None,
                    dont: Optional[List[str]] = None,
                    register: Optional[str] = None) -> Path:
    """Merge an observed voice block into the given `lang` partition and persist.

    Validates BEFORE any write: `lang` must be a closed-enum value; each list field
    must be a list; and the DRY guard refuses a closed-enum structural copy. List
    fields are UNION-merged (deduped, order-preserving) with what is already stored
    so repeated observations accrue; `register` overwrites (the latest read wins).

    The write goes through the soft fence — it can never escape docs/product/."""
    if lang not in LANGS:
        raise BehavioralError(
            f"lang {lang!r} is not one of {sorted(LANGS)} (the stores are lang-keyed)"
        )

    additions: Dict[str, List[str]] = {}
    for field, value in (
        ("vocabulary", vocabulary),
        ("recurring_asks", recurring_asks),
        ("do", do),
        ("dont", dont),
    ):
        if value is None:
            continue
        items = _check_str_list(field, value)
        _assert_no_structural_copy(field, items)
        additions[field] = items
    if register is not None and not isinstance(register, str):
        raise BehavioralError(
            f"po-style 'register' must be a string; got {type(register).__name__}"
        )

    raw = _load_po_style_raw(root)
    block = raw.setdefault(lang, _empty_lang_block())
    for field, items in additions.items():
        block[field] = _union_keep_order(block.get(field, []), items)
    if register is not None:
        block["register"] = register

    return _write_po_style(root, raw)


def _union_keep_order(existing: List[str], new: List[str]) -> List[str]:
    """Append `new` items not already present, preserving first-seen order. Keeps
    the store stable (no churn from re-observing the same term)."""
    seen = list(existing)
    seen_set = set(existing)
    for item in new:
        if item not in seen_set:
            seen.append(item)
            seen_set.add(item)
    return seen


def _write_po_style(root, raw: Dict[str, Any]) -> Path:
    """Serialize the lang-keyed shape to po-style.yaml under the soft fence. Empty
    list fields and a null register are kept so the on-disk shape is self-describing
    for the next read (and for a human inspecting the committed file)."""
    out: Dict[str, Any] = {"version": 1, "voice": {}}
    for lang in sorted(LANGS):
        block = raw.get(lang, _empty_lang_block())
        out["voice"][lang] = {
            **{f: list(block.get(f, [])) for f in PO_STYLE_LIST_FIELDS},
            "register": block.get("register"),
        }
    path = _po_style_path(root)
    assert_under_docs_product(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline='' keeps the file byte-stable (LF) across platforms.
    with open(path, "w", encoding="utf-8", newline="") as fh:
        yaml.safe_dump(out, fh, sort_keys=True, allow_unicode=True,
                       default_flow_style=False)
    return path


# ----------------------------------------------------------------------------
# 3E self-correction — recurring slips, behavior guard
# ----------------------------------------------------------------------------

def _load_self_corrections_raw(root) -> Dict[str, Any]:
    """Parse self-corrections.json. A missing / corrupt / wrong-shaped file degrades
    to an empty store — the read path never raises (this only nudges a self-check;
    absence is benign)."""
    empty = {"schema_version": "1", "corrections": []}
    path = _self_corrections_path(root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return empty
    if not isinstance(data, dict) or not isinstance(data.get("corrections"), list):
        return empty
    return data


def load_self_corrections(root) -> List[Dict[str, Any]]:
    """Return the list of self-correction rows (empty when the store is absent)."""
    return list(_load_self_corrections_raw(root).get("corrections", []))


def record_self_correction(root, *, slip: str, violated_rule: str,
                           reminder: str) -> Path:
    """Append a slip, or increment the frequency of an identical prior slip.

    Validates BEFORE any write: `slip` and `reminder` must be non-empty, and
    `violated_rule` MUST be one of the five operating principles (`VIOLATED_RULES`)
    — an un-anchored slip carries no corrective lesson. A repeat of the SAME (slip,
    violated_rule) increments `frequency` and refreshes `last_seen` rather than
    duplicating the row; a new slip appends a fresh row (`frequency: 1`).

    The write goes through the soft fence — it can never escape docs/product/."""
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

    data = _load_self_corrections_raw(root)
    rows: List[Dict[str, Any]] = list(data.get("corrections", []))
    now = _now()

    for row in rows:
        if row.get("slip") == slip and row.get("violated_rule") == violated_rule:
            row["frequency"] = int(row.get("frequency", 0)) + 1
            row["last_seen"] = now
            # The latest reminder wins (the corrective phrasing may sharpen).
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

    return _write_self_corrections(root, {"schema_version": "1", "corrections": rows})


def _write_self_corrections(root, data: Dict[str, Any]) -> Path:
    path = _self_corrections_path(root)
    assert_under_docs_product(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    return path


# ----------------------------------------------------------------------------
# CLI — read-only inspection (writes are driven by the LLM via the helpers)
# ----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--lang", default="en", choices=sorted(LANGS),
                    help="which po-style language partition to read")
    ap.add_argument("--store", choices=["po-style", "self-corrections"],
                    default="po-style", help="which store to dump")
    args = ap.parse_args()

    if args.store == "po-style":
        print(json.dumps(load_po_style(args.root, lang=args.lang),
                         indent=2, ensure_ascii=False))
    else:
        print(json.dumps(load_self_corrections(args.root),
                         indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
