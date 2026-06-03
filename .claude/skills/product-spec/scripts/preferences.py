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
  detail_level         concise | standard | verbose — PRODUCT-SPEC output verbosity
                       (sizes vision/PRD/story prose + interview follow-ups). Wired
                       in workflow-interview.md. SEPARATE from critique_detail_level.
  prioritization       moscow | value-effort | manual
  dismissed_reminders  list of reminder keys the PO asked to stop seeing
  critique_drift_threshold  int >=1 (default 3) — node body_hash changes since the
                       last critique before the opt-in product-spec-critique nudge fires.
                       Non-enum: load() passes it through verbatim (no int-check);
                       the consumer (critique_scan) coerces int() defensively.
  critique_level       int 1..9 (default 5) — the cleanmatic:product-spec-critique default
                       voice level when no --level flag is given. Closed enum. Default 5
                       (no-mercy) is the last level before a mandated personal roast (6+);
                       a flagless run is level 5 + the standing-consent reminder.
                       A standing 5/6/7/8 is the PO's explicit consent to that voice;
                       the skill shows the one-line danger reminder each run but does
                       not re-ask. 9 is ALSO a valid standing default, BUT a resolved
                       level of 9 (from this preference OR a --level 9 flag) re-confirms
                       via AskUserQuestion EVERY run and downgrades to 8 on decline —
                       that per-run gate is enforced in workflow-critique, NOT here.
  critique_detail_level  concise | standard | verbose — SPEC-CRITIQUE report verbosity
                       (concise = top-3 + terse per-lens; verbose = full per-lens +
                       extended pre-mortems). SEPARATE from detail_level; the two never
                       bleed into each other.
  critique_address_gender  m | f — level-7 address form: ông/tôi (m) ↔ bà/tôi (f).
                       Vietnamese-only; a no-op in lang: en.
  critique_dialect     bac | trung | nam — level-8+ pronoun, the PO's OWN voice
                       (self-configured, not regional mockery): mày/tao (bac) ↔
                       mi/tau (trung) ↔ nam. Vietnamese-only; a no-op in lang: en.
  critique_profanity   off | abbrev | strong (default strong) — level-9 profanity AIMED
                       AT THE WORK: off ↔ đm/vl (abbrev) ↔ đm/vl/vãi (strong). Default is
                       strong because level 9 re-confirms with the PO every run anyway.
                       The enum is a STRENGTH
                       tier, not a token list — the work-vs-person TARGET rule (and which
                       tokens are IN/OUT) lives in voice-and-tone.md's IN/OUT table, not
                       here. Euphemistic minced oaths (đậu xanh) are IN there; only the
                       LITERAL family-target form (đụ má mày) is OUT.
  critique_inherit     on | off (default on) — product-spec-critique cross-critique INHERIT
                       (parent→child): surface a parent's prior blockers/DEC as the
                       child's inherited risk. ENUM-registered (not bare bool) so the
                       YAML off/on→token coercion below maps it back to "off"/"on".
  critique_rollup      on | off (default on) — product-spec-critique descendant ROLLUP
                       (child→parent): aggregate critiqued children's verdicts onto the
                       parent ("3/5 stories unbuildable").
  critique_inherit_depth  nearest | deep (default nearest) — how far up the ancestry the
                       INHERIT pass walks: nearest critiqued ancestor + most-recent
                       scope=all (nearest), or every critiqued ancestor (deep). The
                       --no-inherit flag beats --inherit deep (off wins over depth).

The level-applicability of the register keys (gender at 7, dialect at ≥8, profanity at
9) and the universal-harm floor are LLM-workflow/voice concerns, not schema concerns
(script-vs-LLM split): this module only stores closed-enum values, it judges nothing.
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
    # PRODUCT-SPEC output verbosity (sizes generated prose + interview follow-ups).
    "detail_level": "standard",
    "prioritization": "moscow",
    "dismissed_reminders": [],
    # Consumed by cleanmatic:product-spec-critique (a separate skill). Non-enum scalar: the
    # read path below leaves it verbatim, so a hand-edited non-int degrades on the
    # consumer side (critique_scan coerces int()), never here.
    "critique_drift_threshold": 3,
    # Default product-spec-critique voice level (1..9) when no --level is passed. Closed
    # enum below. Default 5 (no-mercy) = the last level before a mandated personal
    # roast (6+). A standing 5/6/7/8 is the PO's deliberate consent to that voice;
    # 9 is settable too but re-confirms per run + downgrades to 8 on decline (gate
    # in workflow-critique, NOT a schema cap).
    "critique_level": 5,
    # SPEC-CRITIQUE report verbosity — separate from detail_level above.
    "critique_detail_level": "standard",
    # Level-7 address form (ông/tôi vs bà/tôi); Vietnamese-only, no-op in en.
    "critique_address_gender": "m",
    # Level-8+ pronoun, the PO's own self-configured voice; Vietnamese-only, no-op in en.
    "critique_dialect": "bac",
    # Level-9 profanity aimed at the WORK; no family/sexual-target token representable.
    # Default = strong: level 9 already re-confirms with the PO on EVERY run, so when it
    # does fire, it runs at full power rather than a half-measure.
    "critique_profanity": "strong",
    # product-spec-critique cross-critique context (both default ON, opt-out). ENUM on/off so
    # the YAML bool coercion below maps `critique_inherit: off` back to the "off" token.
    "critique_inherit": "on",
    "critique_rollup": "on",
    "critique_inherit_depth": "nearest",
}

# Closed enums per scalar key. A value outside its set is treated as absent
# (read path: fall back to default; write path: PreferenceError).
ENUMS: Dict[str, frozenset] = {
    "lang": frozenset({"en", "vi"}),
    "detail_level": frozenset({"concise", "standard", "verbose"}),
    "prioritization": frozenset({"moscow", "value-effort", "manual"}),
    # 1..9: 9 is a VALID standing default; the per-run re-confirm + downgrade-to-8
    # for a resolved 9 is workflow behaviour (workflow-critique), not a schema check.
    "critique_level": frozenset(range(1, 10)),
    "critique_detail_level": frozenset({"concise", "standard", "verbose"}),
    "critique_address_gender": frozenset({"m", "f"}),
    "critique_dialect": frozenset({"bac", "trung", "nam"}),
    # Strength tier only; the target-based floor (which tokens are IN/OUT, e.g. the
    # euphemism đậu xanh is IN, the literal đụ má mày is OUT) lives in voice-and-tone.md's
    # IN/OUT table, not in this enum.
    "critique_profanity": frozenset({"off", "abbrev", "strong"}),
    # on/off ENUM-registered (mirroring critique_profanity) so the YAML bool coercion
    # maps `off`/`on` back to the string token instead of leaving a bare Python bool.
    "critique_inherit": frozenset({"on", "off"}),
    "critique_rollup": frozenset({"on", "off"}),
    "critique_inherit_depth": frozenset({"nearest", "deep"}),
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
            # YAML 1.1 parses bare off/on/no/yes as booleans, so `critique_profanity: off`
            # reaches us as Python False. Map it back to the enum's string token so the
            # PO can write the value unquoted and still have it resolve.
            if isinstance(value, bool):
                value = {False: "off", True: "on"}.get(value, value)
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
