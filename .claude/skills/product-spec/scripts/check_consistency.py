#!/usr/bin/env python3
"""
check_consistency — structural consistency checks. No judgment.

Detects:
- missing_ac / low_ac_count   (stories without enough acceptance criteria)
- invalid_id                  (ID does not match parent-scoped grammar)
- dup_id                      (two artifacts share the same ID)
- unknown_enum                (closed-enum field with disallowed value)
- status_inconsistency        (child approved under draft parent, etc.)

Emits findings JSON per validation-rules-spec.md. Always exits 0.

CLI:
    check_consistency.py --root <project-dir>
"""

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from encoding_utils import configure_utf8_console
from spec_graph import build_graph, matching_child_counts, _now

configure_utf8_console()


ID_PATTERN_BY_TYPE = {
    "goal": re.compile(r"^BRD-G[0-9]+$"),
    "prd": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}$"),
    "epic": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+$"),
    "story": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+-S[0-9]+$"),
}

ENUMS = {
    "status": {"draft", "review", "approved"},
    "scope": {"in", "out", "core-value"},
    "moscow": {"must", "should", "could", "wont"},
    "horizon": {"now", "next", "later"},
    "size": {"S", "M", "L"},
    "lang": {"en", "vi"},
    # Risk-entry sub-field enums. Distinct keys from the artifact-level `status`
    # above: a risk's `status` is open|mitigated|accepted, NOT the artifact's
    # draft|review|approved lifecycle. Validated per-entry in _check_risks().
    "risk_impact": {"low", "med", "high"},
    "risk_likelihood": {"low", "med", "high"},
    "risk_status": {"open", "mitigated", "accepted"},
}

# List-typed frontmatter fields. If a generate-templates regression (or a
# manual hand-edit) leaves these as a bare scalar like "TBD", downstream
# renderers iterate it per character and emit phantom personas / dangling
# links. Catch the shape error at validate time so the PO is told exactly
# which field is wrong, instead of staring at three "unknown BRD goal T/B/D"
# errors and wondering what happened.
LIST_FIELDS = (
    "personas",
    "metrics",
    "brd_goals",
    "risks",
    "acceptance_criteria",
)

# Soft cap surfaced as a warn during PO interview. Brainstorm §3 + §11 +
# interview-vision V2 set "cap 2-4 (soft)". Enforced as a warn here so the
# PO sees an explicit signal at validate time instead of trusting the LLM
# to remember to push back during interview.
PERSONA_SOFT_CAP = 4

# When more than this fraction of an artifact's risks sit at `impact: high`,
# `risk_high_ratio` warns (the risk register is top-heavy — the PO is either
# over-rating or genuinely exposed). A strict majority: 3/5 (60%) trips, 2/5
# (40%) does not. Tunable module constant (mirrors PERSONA_SOFT_CAP).
RISK_HIGH_RATIO = 0.5

# An epic with at least this many child stories but zero declared risks trips
# `risk_blindspot` — a sizeable feature with no risk register is a blind spot.
# The child-story count is a deterministic graph traversal (NOT an LLM
# judgment), keeping this in the script layer per the Script-vs-LLM split.
RISK_BLINDSPOT_MIN_STORIES = 5

STATUS_ORDER = {"draft": 0, "review": 1, "approved": 2}

# `depends_on` (the new TIME edge) is allowed on PRD + Epic ONLY (design Q13/Q64).
# A non-empty list on any other artifact type reuses the existing `invalid_type`
# finding — NOT a new check id — keeping the catalog small.
DEPENDS_ON_ALLOWED_TYPES = ("prd", "epic")

# ISO calendar-date shape (YYYY-MM-DD) for `target_date`. PyYAML auto-parses a
# valid date to a datetime.date; a malformed/quoted value stays a str and is
# caught by this shape check (→ invalid_type). Only the SHAPE is structural;
# overdue-vs-today is advisory and lives in time_advisory.py (out of this gate).
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    id_to_nodes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for n in graph["nodes"]:
        id_to_nodes[n["id"]].append(n)

    for nid, ns in id_to_nodes.items():
        if len(ns) > 1:
            files = sorted({n.get("file") for n in ns if n.get("file")})
            findings.append({
                "check": "dup_id",
                "severity": "error",
                "artifact_id": nid,
                "file": None,
                "detail": f"Duplicate ID {nid} appears in {files}.",
                "context": {"files": list(files)},
            })

    for n in graph["nodes"]:
        ntype = n.get("type")
        nid = n.get("id") or ""
        pattern = ID_PATTERN_BY_TYPE.get(ntype)
        if pattern and not pattern.match(nid):
            findings.append(_f("invalid_id", "error", n, f"ID {nid!r} does not match expected pattern for {ntype}.", expected_pattern=pattern.pattern))

        for field in ("status", "scope", "moscow", "horizon", "size", "lang"):
            v = n.get(field)
            if v is None:
                continue
            if v not in ENUMS[field]:
                findings.append(_f("unknown_enum", "error", n, f"Field {field}={v!r} not in {sorted(ENUMS[field])}.", field=field, value=v))

        for field in LIST_FIELDS:
            v = n.get(field)
            if v is None:
                continue
            if not isinstance(v, list):
                findings.append(_f(
                    "invalid_type",
                    "error",
                    n,
                    f"Field {field}={v!r} must be a YAML list; got {type(v).__name__}.",
                    field=field,
                    value=v,
                ))

        findings.extend(_check_risks(n))
        findings.extend(_check_target_date_shape(n))
        findings.extend(_check_depends_on_type(n))

        # Soft cap on personas — surface as a warn (not blocking). Lives
        # alongside enum checks because the cap shape is closed (count) even
        # though the list contents are free text.
        personas = n.get("personas")
        if isinstance(personas, list) and len(personas) > PERSONA_SOFT_CAP:
            findings.append(_f(
                "persona_cap_exceeded",
                "warn",
                n,
                f"{n['id']} declares {len(personas)} personas; soft cap is {PERSONA_SOFT_CAP}. "
                f"Consider narrowing to the primary buyers.",
                count=len(personas),
                cap=PERSONA_SOFT_CAP,
            ))

        if ntype == "story":
            ac = _resolve_ac(n)
            if not ac:
                findings.append(_f("missing_ac", "error", n, "Story has no acceptance_criteria."))
            elif len(ac) < 2:
                findings.append(_f("low_ac_count", "warn", n, f"Story has {len(ac)} acceptance criteria; >=2 recommended.", count=len(ac)))

    findings.extend(_status_inconsistency(graph))
    findings.extend(_version_inconsistency(graph))
    findings.extend(_self_reference(graph))
    findings.extend(_session_md_gitignore(graph))
    findings.extend(_risk_high_ratio(graph))
    findings.extend(_risk_blindspot(graph))
    findings.extend(_time_child_late(graph))
    findings.extend(_dep_order(graph))
    return findings


# ── TIME-dimension structural checks (pure date comparisons; no wall clock) ──
#
# All deterministic — they compare dates already on the graph, never `today`
# (which would break G-A4 reproducibility). The wall-clock `overdue` advisory is
# deliberately a SEPARATE script (time_advisory.py), outside this gate.


def _parse_iso_date(v: Any):
    """Coerce a node's target_date to a datetime.date for comparison, or None.

    PyYAML already parses a valid `YYYY-MM-DD` to datetime.date (or datetime —
    accept its .date()). A str only reaches here if it slipped the shape gate;
    parse it leniently and return None on failure so a malformed value (already
    flagged invalid_type) simply drops out of the ordering checks."""
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str) and _ISO_DATE_RE.match(v.strip()):
        try:
            return dt.date.fromisoformat(v.strip())
        except ValueError:
            return None
    return None


def _check_target_date_shape(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """target_date must be an ISO calendar date (YYYY-MM-DD). Absent → clean
    (optional, G-D1). A value PyYAML left as a non-ISO string is invalid_type."""
    v = node.get("target_date")
    if v is None:
        return []
    if isinstance(v, (dt.date, dt.datetime)):
        return []
    if isinstance(v, str) and _ISO_DATE_RE.match(v.strip()):
        return []
    return [_f(
        "invalid_type", "error", node,
        f"Field target_date={v!r} must be an ISO date (YYYY-MM-DD).",
        field="target_date", value=v,
    )]


def _check_depends_on_type(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """`depends_on` is allowed on PRD + Epic only. A non-empty list on any other
    artifact type reuses the EXISTING `invalid_type` finding (no new check id).
    An empty/absent list is always fine (the uniform empty default is harmless)."""
    deps = node.get("depends_on")
    if not deps:
        return []
    if node.get("type") in DEPENDS_ON_ALLOWED_TYPES:
        return []
    return [_f(
        "invalid_type", "error", node,
        f"Field depends_on is only valid on {' or '.join(DEPENDS_ON_ALLOWED_TYPES)}; "
        f"{node['id']} is a {node.get('type')}.",
        field="depends_on", value=deps,
    )]


def _time_child_late(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn when a child's target_date is AFTER its parent's (an epic due after
    its PRD finishes is incoherent). Only fires when BOTH dates parse."""
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    for n in graph["nodes"]:
        parent_id = n.get("epic") or n.get("prd")
        if not parent_id:
            continue
        parent = nodes_by_id.get(parent_id)
        if not parent:
            continue
        cd = _parse_iso_date(n.get("target_date"))
        pd = _parse_iso_date(parent.get("target_date"))
        if cd is None or pd is None:
            continue
        if cd > pd:
            findings.append(_f(
                "time_child_late", "warn", n,
                f"{n['id']} target_date {cd} is after parent {parent['id']} "
                f"target_date {pd}; a child cannot finish after its parent.",
                parent_id=parent["id"],
                child_target_date=str(cd),
                parent_target_date=str(pd),
            ))
    return findings


def _dep_order(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn when A depends_on B but A.target_date < B.target_date — A is due
    before the prerequisite it waits on. Only fires when BOTH dates parse."""
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    for n in graph["nodes"]:
        ad = _parse_iso_date(n.get("target_date"))
        if ad is None:
            continue
        for dep in n.get("depends_on") or []:
            target = nodes_by_id.get(dep)
            if not target:
                continue  # dep_dangling owns the missing-ID case
            bd = _parse_iso_date(target.get("target_date"))
            if bd is None:
                continue
            if ad < bd:
                findings.append(_f(
                    "dep_order", "warn", n,
                    f"{n['id']} target_date {ad} is before its prerequisite "
                    f"{target['id']} target_date {bd}; A cannot complete before B.",
                    depends_on=dep,
                    target_date=str(ad),
                    prerequisite_target_date=str(bd),
                ))
    return findings


_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _parse_semver(v: Any) -> Optional[tuple]:
    if not isinstance(v, str):
        return None
    m = _SEMVER_RE.match(v.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _version_inconsistency(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flag any child whose semver `version` exceeds its parent's.

    Rare in practice: child gets a major bump while parent stays behind.
    Spec advertises this check; this is the concrete implementation. Only
    flags when BOTH versions parse cleanly so a missing or malformed
    `version:` is silently ignored (the dedicated parse check handles it).
    """
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    for n in graph["nodes"]:
        parent_id = n.get("epic") or n.get("prd")
        if not parent_id:
            continue
        parent = nodes_by_id.get(parent_id)
        if not parent:
            continue
        cv = _parse_semver(n.get("version"))
        pv = _parse_semver(parent.get("version"))
        if cv is None or pv is None:
            continue
        if cv > pv:
            findings.append(_f(
                "version_inconsistency",
                "warn",
                n,
                f"{n['id']} version {n.get('version')} exceeds parent {parent['id']} version {parent.get('version')}.",
                parent_id=parent["id"],
                child_version=n.get("version"),
                parent_version=parent.get("version"),
            ))
    return findings


def _self_reference(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flag any artifact whose parent reference points at itself.

    Real-world rare but a common LLM hallucination when -auto reassigns IDs.
    Spec catalog row: `self_reference` / error.
    """
    findings: List[Dict[str, Any]] = []
    for n in graph["nodes"]:
        nid = n.get("id")
        if not nid:
            continue
        for key in ("epic", "prd"):
            ref = n.get(key)
            if ref == nid:
                findings.append(_f(
                    "self_reference",
                    "error",
                    n,
                    f"{nid} references itself via `{key}: {nid}`.",
                    field=key,
                ))
        brd_goals = n.get("brd_goals") or []
        if isinstance(brd_goals, list) and nid in brd_goals:
            findings.append(_f(
                "self_reference",
                "error",
                n,
                f"{nid} references itself in `brd_goals`.",
                field="brd_goals",
            ))
    return findings


def _session_md_gitignore(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Brainstorm §16 mandates `.session.md` be committed (cross-machine
    resume). A common accidental footgun is the project-wide `.gitignore`
    excluding `.md` or `docs/product/*` patterns and silently dropping it.

    This check only runs when we have a project root and is best-effort: it
    looks for the session file and for `.gitignore` patterns that would
    likely match it. False positives are acceptable; the finding is `warn`.
    """
    findings: List[Dict[str, Any]] = []
    root_path_raw = graph.get("root_path")
    if not root_path_raw:
        # Not exposed by the graph today — best-effort skip when missing.
        return findings
    root = Path(root_path_raw)
    session = root / "docs" / "product" / ".session.md"
    gitignore = root / ".gitignore"
    if not gitignore.exists() or not session.exists():
        return findings
    try:
        patterns = gitignore.read_text(encoding="utf-8").splitlines()
    except OSError:
        return findings
    for raw in patterns:
        p = raw.strip()
        if not p or p.startswith("#"):
            continue
        # Crude match: a literal `.session.md` or a glob covering it.
        if ".session.md" in p or p in ("*.md", "docs/product/**", "docs/**"):
            findings.append({
                "check": "session_md_gitignored",
                "severity": "warn",
                "artifact_id": None,
                "file": ".gitignore",
                "detail": (
                    f".gitignore pattern {p!r} likely excludes docs/product/.session.md. "
                    f"§16 requires the session file to be committed for cross-machine resume."
                ),
                "context": {"pattern": p},
            })
            break
    return findings


def _check_risks(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate each entry of a node's `risks:` list.

    Two structural checks, both deterministic:
      - a non-dict entry (e.g. `risks: ["just a string"]`) reuses the EXISTING
        `invalid_type` finding rather than inventing a new `invalid_shape` —
        keeps the catalog small; the whole-list shape error (`risks: "TBD"`)
        is already caught by the LIST_FIELDS loop in check().
      - `impact` / `likelihood` / `status` validated against their closed enums
        → `unknown_enum` (mirrors the artifact-level enum check above). A risk's
        `status` is open|mitigated|accepted, distinct from the artifact status.
    """
    raw = node.get("risks")
    if not isinstance(raw, list):
        # None (no risks:) or a bad whole-list shape (handled by LIST_FIELDS).
        return []
    findings: List[Dict[str, Any]] = []
    risk_field_to_enum = {
        "impact": "risk_impact",
        "likelihood": "risk_likelihood",
        "status": "risk_status",
    }
    for entry in raw:
        if not isinstance(entry, dict):
            findings.append(_f(
                "invalid_type",
                "error",
                node,
                f"risks[] entry {entry!r} must be a YAML mapping with a "
                f"`description`; got {type(entry).__name__}.",
                field="risks",
                value=entry,
            ))
            continue
        for risk_field, enum_key in risk_field_to_enum.items():
            val = entry.get(risk_field)
            if val is None:
                continue
            if val not in ENUMS[enum_key]:
                findings.append(_f(
                    "unknown_enum",
                    "error",
                    node,
                    f"risk {risk_field}={val!r} not in {sorted(ENUMS[enum_key])}.",
                    field=f"risks[].{risk_field}",
                    value=val,
                ))
    return findings


def _risk_high_ratio(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn when more than RISK_HIGH_RATIO of an artifact's risks are `high`
    impact. Per-node, deterministic count; only artifacts with at least one
    risk are considered."""
    findings: List[Dict[str, Any]] = []
    for n in graph["nodes"]:
        risks = n.get("risks")
        if not isinstance(risks, list):
            continue
        dict_risks = [r for r in risks if isinstance(r, dict)]
        total = len(dict_risks)
        if total == 0:
            continue
        high = sum(1 for r in dict_risks if r.get("impact") == "high")
        if high / total > RISK_HIGH_RATIO:
            pct = round(high / total * 100)
            findings.append(_f(
                "risk_high_ratio",
                "warn",
                n,
                f"{n['id']} has {high}/{total} risks ({pct}%) at impact=high; "
                f"more than {round(RISK_HIGH_RATIO * 100)}% — review whether the "
                f"register is over-rated or the feature is genuinely high-exposure.",
                high=high,
                total=total,
            ))
    return findings


def _risk_blindspot(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Warn for an epic with >= RISK_BLINDSPOT_MIN_STORIES child stories and zero
    declared risks. The child-story count is a deterministic graph traversal —
    NOT an LLM judgment — keeping the check in the script layer per the
    Script-vs-LLM split."""
    findings: List[Dict[str, Any]] = []
    child_counts = matching_child_counts(graph)
    for n in graph["nodes"]:
        if n.get("type") != "epic":
            continue
        risks = n.get("risks")
        has_risk = isinstance(risks, list) and any(isinstance(r, dict) for r in risks)
        if has_risk:
            continue
        story_count = child_counts.get(n["id"], 0)
        if story_count >= RISK_BLINDSPOT_MIN_STORIES:
            findings.append(_f(
                "risk_blindspot",
                "warn",
                n,
                f"{n['id']} has {story_count} child stories but no declared risks. "
                f"A feature of this size with an empty risk register is a blind spot.",
                story_count=story_count,
            ))
    return findings


def _resolve_ac(node: Dict[str, Any]) -> List[Any]:
    raw = node.get("acceptance_criteria")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [x for x in raw if x not in (None, "")]
    return []


def _status_inconsistency(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}

    def _flag(child: Dict[str, Any], parent: Dict[str, Any]) -> None:
        # `STATUS_ORDER.get(...)` raises TypeError if the value is unhashable
        # (e.g. PO wrote `status: [draft]` as a list). Coerce defensively;
        # the malformed value will be flagged separately by `unknown_enum`.
        child_status = child.get("status")
        parent_status = parent.get("status")
        cs = STATUS_ORDER.get(child_status if isinstance(child_status, str) else "", -1)
        ps = STATUS_ORDER.get(parent_status if isinstance(parent_status, str) else "", -1)
        if cs > ps and cs >= 0 and ps >= 0:
            findings.append(_f(
                "status_inconsistency",
                "warn",
                child,
                f"{child['id']} status={child.get('status')!r} is more advanced than parent {parent['id']} status={parent.get('status')!r}.",
                parent_id=parent["id"],
            ))

    for n in graph["nodes"]:
        # story -> epic, epic -> prd via direct scalar parent field.
        parent_id = n.get("epic") or n.get("prd")
        if parent_id:
            parent = nodes_by_id.get(parent_id)
            if parent:
                _flag(n, parent)

        # prd -> brd_goal via list. Originally skipped; an approved PRD whose
        # BRD goals are still draft is a real inconsistency the LLM-judgment
        # layer cannot see structurally.
        if n.get("type") == "prd":
            for gid in n.get("brd_goals") or []:
                if not isinstance(gid, str):
                    continue
                goal = nodes_by_id.get(gid)
                if goal:
                    _flag(n, goal)

    return findings


def _f(check_id: str, severity: str, node: Dict[str, Any], detail: str, **context) -> Dict[str, Any]:
    return {
        "check": check_id,
        "severity": severity,
        "artifact_id": node.get("id"),
        "file": node.get("file"),
        "detail": detail,
        "context": context or None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    root = Path(args.root).resolve()

    parsed_node_extras: Dict[str, Any] = {}
    graph = build_graph(root)

    # Augment story nodes with their acceptance_criteria from frontmatter
    # (graph nodes intentionally don't carry AC by default; load lazily).
    _enrich_with_ac(graph, root)

    findings = check(graph)
    output = {
        "schema_version": "1.0",
        "root": str(root),
        "checked_at": _now(),
        "findings": findings,
        "graph": graph,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


def _enrich_with_ac(graph: Dict[str, Any], root: Path) -> None:
    """Re-parse story files to attach acceptance_criteria onto graph nodes."""
    from frontmatter_parser import parse_file  # avoid top-level cycle on tests
    product_dir = root / "docs" / "product"
    for n in graph["nodes"]:
        if n.get("type") != "story":
            continue
        f = n.get("file")
        if not f:
            continue
        result = parse_file(product_dir / f)
        if result["ok"]:
            n["acceptance_criteria"] = result["frontmatter"].get("acceptance_criteria") or []


if __name__ == "__main__":
    sys.exit(main())
