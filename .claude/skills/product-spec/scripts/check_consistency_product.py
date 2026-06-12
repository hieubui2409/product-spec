#!/usr/bin/env python3
"""
check_consistency_product — PRODUCT-dimension structural checks for
check_consistency.

Focused sibling (matches check_consistency_schema/_time/_risk/_competition
pattern): rules that police PRODUCT-level cross-artifact consistency.

Emits:
- subsystem_horizon_drift  (warn)  a PRODUCT.md subsystem table row's horizon
                                   disagrees with the matching PRD node's
                                   frontmatter horizon.
- persona_without_portrait (warn)  a persona declared in VISION/BRD frontmatter
                                   has no matching body heading in that artifact.

Both are advisory WARN (not error) — they surface real PO defects without
hard-blocking the validate gate.

Pure functions that accept (graph); root is derived from graph["root_path"].
The caller (check_consistency) folds findings into its list.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from spec_graph import make_finding as _f
from frontmatter_parser import parse_file


# ---------------------------------------------------------------------------
# Subsystem table parser
# ---------------------------------------------------------------------------

# Detect a markdown table row: cells separated by pipes, at least 2 cells.
_TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
# Separator row: cells contain only dashes, colons, whitespace, pipes.
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|\-]+\|\s*$")


def _parse_subsystem_table(body: str) -> Optional[List[Dict[str, str]]]:
    """Parse the first markdown table in `body` that has an 'ID' column and
    a 'Horizon' column (case-insensitive, tolerates column reorder/whitespace).

    Returns a list of dicts keyed by lowercased column name, or None when no
    matching table is found.  Fail-soft: returns None instead of raising on any
    malformed input.
    """
    if not body:
        return None

    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not _TABLE_ROW_RE.match(line):
            i += 1
            continue

        # Potential table header row.
        header_cells = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        if len(header_cells) < 2:
            i += 1
            continue

        # Must be followed by a separator row.
        if i + 1 >= len(lines) or not _TABLE_SEP_RE.match(lines[i + 1]):
            i += 1
            continue

        # Check required columns present.
        if "id" not in header_cells or "horizon" not in header_cells:
            # This table exists but lacks the needed columns — skip, try next.
            i += 2
            continue

        # Parse data rows.
        rows: List[Dict[str, str]] = []
        j = i + 2
        while j < len(lines):
            data_line = lines[j]
            if not _TABLE_ROW_RE.match(data_line):
                break
            cells = [c.strip() for c in data_line.strip().strip("|").split("|")]
            if len(cells) < len(header_cells):
                # Pad short rows so the zip doesn't drop trailing columns.
                cells.extend([""] * (len(header_cells) - len(cells)))
            row = dict(zip(header_cells, cells))
            rows.append(row)
            j += 1

        if rows:
            return rows

        # Empty table body — keep scanning.
        i = j

    return None


# ---------------------------------------------------------------------------
# check_product_subsystems
# ---------------------------------------------------------------------------

def check_product_subsystems(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compare PRODUCT.md subsystem table horizon values against PRD frontmatter.

    For each row in the subsystem table that has a non-empty horizon, look up
    the matching PRD by ID in the graph.  When found and the PRD's frontmatter
    horizon differs, emit one WARN finding.

    Fail-soft: missing PRODUCT.md, no table, or malformed rows → return [].
    """
    findings: List[Dict[str, Any]] = []

    root_path_raw = graph.get("root_path")
    if not root_path_raw:
        return findings

    product_md = Path(root_path_raw) / "docs" / "product" / "PRODUCT.md"
    if not product_md.exists():
        return findings

    result = parse_file(product_md)
    if not result["ok"]:
        return findings

    body = result.get("body") or ""
    rows = _parse_subsystem_table(body)
    if not rows:
        return findings

    # Build a quick id→node lookup from the graph.
    nodes_by_id: Dict[str, Dict[str, Any]] = {
        n["id"]: n for n in graph.get("nodes", []) if n.get("id")
    }

    # Carrier node for findings: attribute to PRODUCT.md.
    product_node = nodes_by_id.get("PRODUCT") or {"id": "PRODUCT", "file": "PRODUCT.md"}

    for row in rows:
        subsystem_id = row.get("id", "").strip()
        table_horizon = row.get("horizon", "").strip().lower()

        if not subsystem_id or not table_horizon:
            # Row has no ID or no horizon — nothing to compare.
            continue

        # Look up the PRD node.  The convention is that a subsystem ID like
        # PAYMENT matches a PRD node whose id IS the subsystem id (e.g.
        # PRD-PAYMENT) or exactly the subsystem id itself.  Try both forms.
        prd_node = nodes_by_id.get(subsystem_id) or nodes_by_id.get(f"PRD-{subsystem_id}")
        if prd_node is None:
            # No matching PRD in the graph — skip (the traceability checker
            # handles dangling references; this rule only validates horizon
            # WHEN the PRD exists).
            continue

        prd_horizon = (prd_node.get("horizon") or "").strip().lower()
        if not prd_horizon:
            # PRD declares no horizon — nothing to compare against.
            continue

        if table_horizon != prd_horizon:
            findings.append(_f(
                "subsystem_horizon_drift",
                "warn",
                product_node,
                (
                    f"Subsystem {subsystem_id}: PRODUCT.md table says horizon={table_horizon!r} "
                    f"but {prd_node['id']} frontmatter says horizon={prd_horizon!r}. "
                    f"Align the table or the PRD."
                ),
                subsystem_id=subsystem_id,
                table_horizon=table_horizon,
                prd_id=prd_node["id"],
                prd_horizon=prd_horizon,
            ))

    return findings


# ---------------------------------------------------------------------------
# Persona portrait checker
# ---------------------------------------------------------------------------

# Match ## <heading> or ### <heading> at the start of a line (case-insensitive
# check done after extracting the heading text).
_HEADING_RE = re.compile(r"^#{2,3}\s+(.+)", re.MULTILINE)


def _body_headings(body: str) -> List[str]:
    """Return all ##/### heading texts from `body`, lowercased and stripped."""
    return [m.group(1).strip().lower() for m in _HEADING_RE.finditer(body)]


def _persona_has_portrait(persona_lower: str, headings: List[str]) -> bool:
    """Return True when any heading in `headings` is a portrait for the given persona.

    A heading qualifies when it equals the persona name OR begins with the persona name
    followed by a separator character (space, dash, em-dash, colon).  Matching is
    case-insensitive.  This avoids false positives on descriptive headings like
    ``## Alice — the busy admin`` while still warning when the persona name appears
    nowhere as a heading lead token.
    """
    import re as _re
    # Separator pattern after the persona name: whitespace, dash, en/em-dash, colon.
    _SEP_RE = _re.compile(r"^(.+?)(\s|[-–—:])", _re.UNICODE)
    for heading in headings:
        heading_lower = heading.lower()
        if heading_lower == persona_lower:
            return True
        # Check if the heading starts with persona_lower followed by a separator.
        if heading_lower.startswith(persona_lower):
            rest = heading_lower[len(persona_lower):]
            if rest and rest[0] in (" ", "-", "–", "—", ":"):
                return True
    return False


def check_persona_portraits(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn when a persona named in VISION/BRD frontmatter has no body portrait.

    Conservative: only warns when a persona appears in `personas:` AND has NO
    matching body heading that leads with the persona name (exact match or name
    followed by a separator, e.g. ``## Alice — the busy admin``).  Case-insensitive.

    Fail-soft: missing files, parse errors → skip silently.
    """
    findings: List[Dict[str, Any]] = []

    root_path_raw = graph.get("root_path")
    if not root_path_raw:
        return findings

    product_dir = Path(root_path_raw) / "docs" / "product"

    # Artifacts to scan: VISION and BRD (the two that declare personas in frontmatter).
    candidates = [
        ("vision", product_dir / "vision.md"),
        ("brd", product_dir / "brd.md"),
    ]

    for art_type, art_path in candidates:
        if not art_path.exists():
            continue

        result = parse_file(art_path)
        if not result["ok"]:
            continue

        fm = result.get("frontmatter") or {}
        personas = fm.get("personas")
        if not isinstance(personas, list) or not personas:
            continue

        body = result.get("body") or ""
        headings = _body_headings(body)

        # The carrier node for findings: use the artifact's node from the graph
        # when available; otherwise fall back to a synthetic carrier.
        nodes_by_id: Dict[str, Dict[str, Any]] = {
            n["id"]: n for n in graph.get("nodes", []) if n.get("id")
        }
        artifact_id = fm.get("id") or art_type.upper()
        carrier_node = nodes_by_id.get(artifact_id) or {
            "id": artifact_id,
            "file": art_path.relative_to(product_dir).as_posix(),
        }

        for persona in personas:
            if not isinstance(persona, str) or not persona.strip():
                continue
            persona_lower = persona.strip().lower()
            if not _persona_has_portrait(persona_lower, headings):
                findings.append(_f(
                    "persona_without_portrait",
                    "warn",
                    carrier_node,
                    (
                        f"Persona {persona!r} is declared in {artifact_id} frontmatter "
                        f"but has no `## {persona}` / `### {persona}` body heading. "
                        f"Add a portrait section or remove the persona from the list."
                    ),
                    persona=persona,
                    artifact_id=artifact_id,
                ))

    return findings
