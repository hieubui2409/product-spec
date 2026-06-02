"""
behavioral_memory_po_style — 3D PO-style voice store.

Owns the lang-keyed voice block (register, vocabulary, recurring_asks,
do/dont). The caller supplies the store path so the path functions in
behavioral_memory.py remain the single monkeypatching targets (the tests
patch behavioral_memory._po_style_path, not this module's internals).

All writes go through the shared soft fence (fs_guard) so this store can
never escape the spec boundary.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from fs_guard import assert_under_docs_product


# Languages the store is keyed by. Mirrors the bilingual convention (en default).
LANGS = frozenset({"en", "vi"})

# The list-valued voice fields of a po-style lang block.
PO_STYLE_LIST_FIELDS = ("vocabulary", "recurring_asks", "do", "dont")


class BehavioralError(ValueError):
    """Shape violation on the write path. The read path degrades to empty, never raises."""


def _empty_lang_block() -> Dict[str, Any]:
    """A fresh per-lang voice block: every list field empty, register unset."""
    block: Dict[str, Any] = {f: [] for f in PO_STYLE_LIST_FIELDS}
    block["register"] = None
    return block


def load_raw(path: Path) -> Dict[str, Any]:
    """Parse po-style.yaml at `path` into its lang-keyed shape. A missing file,
    non-mapping top level, or unparseable YAML degrades to an empty `{en, vi}` shape.
    """
    shape: Dict[str, Any] = {lang: _empty_lang_block() for lang in sorted(LANGS)}
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


def load(path: Path, lang: str = "en") -> Dict[str, Any]:
    """Return the voice block for ONE language. Reading `vi` never returns `en`
    voice — the store is strictly lang-partitioned."""
    raw = load_raw(path)
    return raw.get(lang, _empty_lang_block())


def _check_str_list(field: str, value: Any) -> List[str]:
    if not isinstance(value, list):
        raise BehavioralError(
            f"po-style field {field!r} must be a list of strings; "
            f"got {type(value).__name__}"
        )
    return [str(v) for v in value]


def _assert_no_structural_copy(field: str, items: List[str],
                                structural_enum_values) -> None:
    """DRY guard: refuse a voice item that is EXACTLY a closed-enum structural value
    (scope/moscow/horizon). Persona-label copy detection is LLM-side only."""
    for item in items:
        token = item.strip().lower()
        if token in structural_enum_values:
            raise BehavioralError(
                f"po-style {field!r} entry {item!r} copies a closed-enum structural "
                f"value (scope/moscow/horizon). Behavioral memory shapes PHRASING "
                f"only; structural facts live in frontmatter (DRY). Use the PO's own "
                f"wording, not an enum value."
            )


def _union_keep_order(existing: List[str], new: List[str]) -> List[str]:
    """Append `new` items not already present, preserving first-seen order."""
    seen = list(existing)
    seen_set = set(existing)
    for item in new:
        if item not in seen_set:
            seen.append(item)
            seen_set.add(item)
    return seen


def record(path: Path, lang: str, structural_enum_values, *,
           vocabulary: Optional[List[str]] = None,
           recurring_asks: Optional[List[str]] = None,
           do: Optional[List[str]] = None,
           dont: Optional[List[str]] = None,
           register: Optional[str] = None,
           root=None) -> Path:
    """Merge an observed voice block into the given `lang` partition and persist.

    `path` is the resolved store path (supplied by behavioral_memory so its
    path function remains the sole monkeypatch target). `structural_enum_values`
    is passed by the caller to avoid a check_consistency import here. Validates
    BEFORE any write. The write goes through the soft fence.
    """
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
        _assert_no_structural_copy(field, items, structural_enum_values)
        additions[field] = items
    if register is not None and not isinstance(register, str):
        raise BehavioralError(
            f"po-style 'register' must be a string; got {type(register).__name__}"
        )
    raw = load_raw(path)
    block = raw.setdefault(lang, _empty_lang_block())
    for field, items in additions.items():
        block[field] = _union_keep_order(block.get(field, []), items)
    if register is not None:
        block["register"] = register
    return _write(path, raw, root=root)


def _write(path: Path, raw: Dict[str, Any], root=None) -> Path:
    """Serialize the lang-keyed shape to `path` under the soft fence."""
    out: Dict[str, Any] = {"version": 1, "voice": {}}
    for lang in sorted(LANGS):
        block = raw.get(lang, _empty_lang_block())
        out["voice"][lang] = {
            **{f: list(block.get(f, [])) for f in PO_STYLE_LIST_FIELDS},
            "register": block.get("register"),
        }
    assert_under_docs_product(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        yaml.safe_dump(out, fh, sort_keys=True, allow_unicode=True,
                       default_flow_style=False)
    return path
