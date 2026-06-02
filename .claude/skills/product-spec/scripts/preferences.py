#!/usr/bin/env python3
"""
preferences — read/write the PO-preferences memory store.

`docs/product/.memory/preferences.yaml` records the product owner's session
defaults so the interview flow does not re-ask the same stylistic questions each
time. These are DEFAULTS only: a per-artifact frontmatter `lang` still WINS over
the preference (the preference seeds the session; the artifact overrides it).

Closed enums + hard-coded defaults: every key has a documented fallback, and a
missing file, a missing key, an out-of-range enum value, or a corrupt YAML file
all resolve to that default and NEVER crash the caller. The interview flow reads
this through `load()`; the read hook itself lives in `workflow-interview.md`.

Keys (all optional in the file):
  lang                 en | vi              — default interview/output language
  detail_level         concise | standard | verbose
  prioritization       moscow | value-effort | manual
  dismissed_reminders  list of reminder keys the PO asked to stop seeing
  critique_drift_threshold  int >=1 (default 3) — node body_hash changes since the
                       last critique before the opt-in spec-critique nudge fires.
                       Non-enum: load() passes it through verbatim (no int-check);
                       the consumer (critique_scan) coerces int() defensively.
  critique_level       int 1..6 (default 3) — the cleanmatic:spec-critique default
                       voice level when no --level flag is given. Closed enum.
                       A standing 5 or 6 is the PO's explicit consent to the
                       brutal/roast voice; the skill still shows the one-line danger
                       reminder each run but does not re-ask (see workflow-critique).
"""

import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from encoding_utils import configure_utf8_console
from fs_guard import assert_under_docs_product

configure_utf8_console()


class PreferenceError(ValueError):
    """Raised by save() when a value violates a closed enum (write-path only).

    The read path is deliberately tolerant — load() never raises — but the write
    path validates so the on-disk file stays canonical for the next read."""


# The single authoritative home for the preference defaults. Adding a key here
# (with its default) is the ONLY place a new preference is registered.
DEFAULTS: Dict[str, Any] = {
    "lang": "en",
    "detail_level": "standard",
    "prioritization": "moscow",
    "dismissed_reminders": [],
    # Consumed by cleanmatic:spec-critique (a separate skill). Non-enum scalar: the
    # read path below leaves it verbatim, so a hand-edited non-int degrades on the
    # consumer side (critique_scan coerces int()), never here.
    "critique_drift_threshold": 3,
    # Default spec-critique voice level (1..6) when no --level is passed. Closed
    # enum below. A standing 5/6 is the PO's deliberate consent to the brutal/roast
    # voice (see workflow-critique's gate handling).
    "critique_level": 3,
}

# Closed enums per scalar key. A value outside its set is treated as absent
# (read path: fall back to default; write path: PreferenceError).
ENUMS: Dict[str, frozenset] = {
    "lang": frozenset({"en", "vi"}),
    "detail_level": frozenset({"concise", "standard", "verbose"}),
    "prioritization": frozenset({"moscow", "value-effort", "manual"}),
    "critique_level": frozenset({1, 2, 3, 4, 5, 6}),
}


def _prefs_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "preferences.yaml"


def load(root) -> Dict[str, Any]:
    """Return the resolved preferences: every key present, defaults filled.

    A missing file, missing key, out-of-range enum, or unparseable YAML all
    degrade to defaults — this function never raises."""
    resolved = dict(DEFAULTS)
    path = _prefs_path(root)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError):
        return resolved
    if not isinstance(raw, dict):
        # A scalar / list top-level (corrupt or hand-mangled) is not a mapping;
        # ignore it wholesale rather than guess.
        return resolved

    for key in DEFAULTS:
        if key not in raw:
            continue
        value = raw[key]
        if key in ENUMS:
            if value in ENUMS[key]:
                resolved[key] = value
            # else: leave the default (defensive against a hand-edited typo)
        elif key == "dismissed_reminders":
            # Coerce to a list of strings; a non-list value is ignored.
            if isinstance(value, list):
                resolved[key] = [str(v) for v in value]
        else:
            resolved[key] = value
    return resolved


def save(root, prefs: Dict[str, Any]) -> Path:
    """Validate + write preferences.yaml through the soft fence.

    Only known keys are persisted (unknown keys are dropped). A scalar key with a
    value outside its closed enum raises PreferenceError before any write."""
    out: Dict[str, Any] = {}
    for key, value in prefs.items():
        if key not in DEFAULTS:
            continue  # drop unknown keys — schema is closed
        if key in ENUMS and value not in ENUMS[key]:
            raise PreferenceError(
                f"preference {key!r}={value!r} is not one of {sorted(ENUMS[key])}"
            )
        if key == "dismissed_reminders" and not isinstance(value, list):
            raise PreferenceError(
                f"preference 'dismissed_reminders' must be a list; got {type(value).__name__}"
            )
        out[key] = value

    path = _prefs_path(root)
    assert_under_docs_product(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline='' keeps the file byte-stable (LF) across platforms.
    with open(path, "w", encoding="utf-8", newline="") as fh:
        yaml.safe_dump(out, fh, sort_keys=True, allow_unicode=True, default_flow_style=False)
    return path


def main() -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    print(json.dumps(load(args.root), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
