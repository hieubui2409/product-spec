"""
template_id_alloc — parent-scoped ID allocation for generate_templates.

Owns the `allocate_id` function and the ID-grammar constants derived from
spec_graph. Kept in a separate module so the allocation logic can be tested
and reasoned about independently from template rendering and file I/O.
"""

import re
from typing import Any, Dict, List, Optional

from spec_graph import ID_PATTERN_BY_TYPE, build_graph


# Strict parent-ID patterns — derived from spec_graph.ID_PATTERN_BY_TYPE (the
# single authoritative home) so a parent passed at generate time fast-fails the
# same way it would be flagged at validate time.
PARENT_PATTERN_FOR_PRD = ID_PATTERN_BY_TYPE["prd"]   # PRD-<SLUG>, slug ≤16 chars
PARENT_PATTERN_FOR_EPIC = ID_PATTERN_BY_TYPE["epic"]  # PRD-<SLUG>-E<n>

# A trailing -E<n> or -E<n>-S<n> means the ID is an epic or story shape — reject
# when a PRD ID is expected so callers can't accidentally pass an epic/story.
PRD_PARENT_LOOKS_LIKE_EPIC_OR_STORY = re.compile(r"-E\d+(-S\d+)?$")

# Bare PRD slug fast-fail (uppercase ASCII letter start, digits/hyphens, ≤16 chars).
SLUG_PATTERN_FOR_PRD = re.compile(r"^[A-Z][A-Z0-9-]{0,15}$")

# Caller-supplied `--id` override patterns — keyed from spec_graph.ID_PATTERN_BY_TYPE
# so an --auto batch caller that pre-allocates IDs cannot smuggle an invalid one
# past the generator.
ID_PATTERN_OVERRIDE: Dict[str, re.Pattern] = {
    # product/vision now live in the canonical ID_PATTERN_BY_TYPE (spread above); only the
    # types absent from it are added here.
    **ID_PATTERN_BY_TYPE,
    "brd": re.compile(r"^BRD$"),
    "exec_summary": re.compile(r"^EXEC-SUMMARY$"),
    "sign_off": re.compile(r".+"),
    "change_log_entry": re.compile(r".+"),
}


def allocate_id(graph: Dict[str, Any], target_type: str,
                slug: Optional[str], parent: Optional[str],
                session_used: List[str]) -> str:
    """Allocate the next parent-scoped ID for `target_type`.

    `session_used` lists IDs already handed out this session so siblings under
    the same parent don't collide (the CLI passes [] for a single-invocation
    call; batch callers accumulate the list).
    """
    existing_ids = {n["id"] for n in graph["nodes"]} | set(session_used)
    if target_type == "goal":
        return _next_with_prefix(existing_ids, "BRD-G")
    if target_type == "prd":
        if not slug:
            raise ValueError("--slug is required for type=prd")
        normalised = slug.upper()
        if not SLUG_PATTERN_FOR_PRD.match(normalised):
            raise ValueError(
                f"--slug must be uppercase ASCII (A-Z, 0-9, hyphen), start with "
                f"a letter, and be ≤16 chars (matches {SLUG_PATTERN_FOR_PRD.pattern}); "
                f"got {slug!r}"
            )
        # A slug like AUTH-E1 mints PRD-AUTH-E1, which collides with the epic-1
        # ID grammar under PRD-AUTH.
        if PRD_PARENT_LOOKS_LIKE_EPIC_OR_STORY.search(normalised):
            raise ValueError(
                f"--slug {slug!r} produces an ID (PRD-{normalised}) that collides "
                f"with the epic/story ID grammar (suffix -{normalised.split('-E', 1)[-1]!r} "
                f"matches -E<n> or -E<n>-S<n>). Use a slug without a trailing -E<n> sequence."
            )
        return f"PRD-{normalised}"
    if target_type == "epic":
        if (
            not parent
            or not PARENT_PATTERN_FOR_PRD.match(parent)
            or PRD_PARENT_LOOKS_LIKE_EPIC_OR_STORY.search(parent)
        ):
            raise ValueError(
                f"--parent must be a valid PRD ID for type=epic "
                f"(PRD-<SLUG>, slug ≤16 chars, no -E<n>/-S<n> suffix); got {parent!r}"
            )
        return _next_with_prefix(existing_ids, f"{parent}-E")
    if target_type == "story":
        if not parent or not PARENT_PATTERN_FOR_EPIC.match(parent):
            raise ValueError(
                f"--parent must be a valid epic ID for type=story "
                f"(pattern {PARENT_PATTERN_FOR_EPIC.pattern}); got {parent!r}"
            )
        return _next_with_prefix(existing_ids, f"{parent}-S")
    if target_type == "product":
        return "PRODUCT"
    if target_type == "vision":
        return "VISION"
    if target_type == "brd":
        return "BRD"
    if target_type == "exec_summary":
        return "EXEC-SUMMARY"
    return ""


def _next_with_prefix(existing: set, prefix: str) -> str:
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    used = []
    for x in existing:
        m = pattern.match(x or "")
        if m:
            used.append(int(m.group(1)))
    n = (max(used) + 1) if used else 1
    return f"{prefix}{n}"
