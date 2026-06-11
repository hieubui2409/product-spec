"""release_check_guard — pre-release consistency checks for the bundle manifest.

Public entry point: ``check_rule_skill_refs(manifest, root)`` returns a list of
error strings (empty = clean). Never raises; callers decide whether to abort.

Guard: every skill slug referenced inside a shipped rule file must itself appear
in ``manifest["skills"]``. A rule that invokes ``/some-skill:command`` but
``some-skill`` is not in the bundle produces a dangling reference — the recipient
would see a prompt that mentions a skill they don't have.

Detection heuristic: scan the text of each shipped rule file for ``/<slug>:``
patterns (the Claude Code skill-invocation syntax). This is intentionally simple
and documented: it catches the common ``/skill-name:`` form. It does NOT attempt
to resolve Markdown prose, so a rule that merely *mentions* a slug without the
leading ``/`` and trailing ``:`` is not flagged. False negatives are acceptable;
false positives (flagging a slug that is in the bundle) are impossible by
construction.
"""

from __future__ import annotations

import re
from pathlib import Path

# Matches `/skill-name:` tokens — the Claude Code invocation prefix.
# Slug characters: letters, digits, hyphens (no underscores in skill slugs).
_SKILL_INVOCATION_RE = re.compile(r"/([a-zA-Z][a-zA-Z0-9-]+):")


def check_rule_skill_refs(manifest: dict, root: Path) -> list[str]:
    """Check that every ``/<slug>:`` token in shipped rules resolves to a bundled skill.

    Args:
        manifest: parsed manifest dict (``rules`` and ``skills`` keys consulted).
        root:     repo root Path (rules resolved relative to ``.claude/rules/``).

    Returns:
        List of human-readable error strings; empty when all references are satisfied.
    """
    bundled_skills: set[str] = set(manifest.get("skills", []) or [])
    rules: list[str] = manifest.get("rules", []) or []

    if not rules:
        return []

    rules_dir = root / ".claude" / "rules"
    errors: list[str] = []

    for rule_name in rules:
        if not isinstance(rule_name, str):
            continue
        # Resolve with/without .md extension (mirrors manifest_loader behaviour).
        candidate = rules_dir / rule_name
        if not candidate.is_file():
            candidate = rules_dir / f"{rule_name}.md"
        if not candidate.is_file():
            # Missing file is a manifest validation error (E072), not our concern here.
            continue

        try:
            text = candidate.read_text(encoding="utf-8")
        except OSError:
            continue

        referenced = _SKILL_INVOCATION_RE.findall(text)
        for slug in referenced:
            if slug not in bundled_skills:
                errors.append(
                    f"Rule '{rule_name}' references /{slug}: but '{slug}' is not in "
                    f"manifest skills: {sorted(bundled_skills)}. "
                    f"Either add '{slug}' to skills: or remove the reference."
                )

    return errors
