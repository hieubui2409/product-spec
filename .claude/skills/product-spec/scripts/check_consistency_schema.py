#!/usr/bin/env python3
"""
check_consistency_schema — goal + frontmatter schema-shape checks. No judgment.

Focused sibling of check_consistency (mirrors check_consistency_time / _risk /
_competition): the rules that police artifact/goal SHAPE against the frontmatter spec,
kept out of the main module so it stays lean.

Emits:
- goal_without_metric   (error)  goal with no success metric at all
- legacy_metric_key     (warn)   goal still on the old singular `metric:` → run migrate
- goal_without_status   (warn|error)  goal missing required status; error once the BRD
                                 declares schema_version >= 2 (a migrated/fresh spec is
                                 fully gated; a not-yet-migrated legacy spec only warns)
- unknown_goal_key      (warn)   a stray goal key outside the spec's allowed set
- misplaced_parent_field(warn)   a story carrying prd/brd_goals (its parent is the epic)
- bad_version_format    (warn)   a `version` that is not semver-lite (major.minor.patch)

Pure functions over the already-built graph; the caller (check_consistency) folds these
into its findings list.
"""

from typing import Any, Dict, List

from spec_graph import make_finding as _f, parse_semver


def _schema_version_int(v: Any) -> int:
    """Coerce a BRD `schema_version` marker to an int era (0 when absent/malformed).
    `bool` is excluded first (it subclasses int) so a stray `schema_version: true`
    is treated as 'no marker', not era 1."""
    if isinstance(v, bool):
        return 0
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return 0


def check_goals(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Goal-entry shape checks (metric / status / stray keys)."""
    findings: List[Dict[str, Any]] = []
    for n in graph.get("nodes", []):
        if n.get("type") != "goal":
            continue
        nid = n.get("id") or ""
        unknown = n.get("unknown_goal_keys") or []
        metrics = n.get("metrics")
        has_metrics = isinstance(metrics, list) and bool(metrics)
        has_legacy_metric = "metric" in unknown

        # METRIC. A goal carrying the OLD singular `metric:` HAS a metric (just mis-keyed),
        # so it WARNs with a migrate hint — never error-blocks an approved legacy BRD. A goal
        # with no metric of either spelling still ERRORs (the gate is not loosened).
        if not has_metrics:
            if has_legacy_metric:
                findings.append(_f(
                    "legacy_metric_key", "warn", n,
                    f"Goal {nid} uses the old singular `metric:` key; rename it to `metrics:` "
                    f"by running migrate_metric_to_metrics.py (dry-run, then confirm with the PO).",
                ))
            else:
                findings.append(_f(
                    "goal_without_metric", "error", n,
                    f"BRD goal {nid} has no success metric; at least one metric slug is required.",
                ))

        # STATUS (required per spec). WARN on a not-yet-migrated legacy BRD (no marker),
        # ERROR once the BRD declares schema_version >= 2 — so a fresh/migrated spec is fully
        # gated while a legacy spec is not retroactively blocked.
        status = n.get("status")
        if status in (None, ""):
            sev = "error" if _schema_version_int(n.get("schema_version")) >= 2 else "warn"
            findings.append(_f(
                "goal_without_status", sev, n,
                f"BRD goal {nid} is missing the required `status` (draft|review|approved).",
            ))

        # Any OTHER stray goal key (a typo, a misplaced field). `metric` is excluded — it is
        # already surfaced above as the actionable legacy_metric_key migrate hint.
        for k in unknown:
            if k == "metric":
                continue
            findings.append(_f(
                "unknown_goal_key", "warn", n,
                f"Goal {nid} carries an out-of-spec key `{k}`; allowed goal keys are "
                f"id/title/metrics/status/owner/moscow.",
                key=k,
            ))
    return findings


# A story's only parent reference is `epic` (frontmatter-and-id-spec). A `prd:`/`brd_goals:`
# on a story is an LLM-hallucinated field that belongs on its PRD/epic, not the story.
_STORY_MISPLACED_FIELDS = ("prd", "brd_goals")


def check_frontmatter_schema(graph: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Out-of-spec artifact frontmatter: misplaced parent refs + malformed version."""
    findings: List[Dict[str, Any]] = []
    for n in graph.get("nodes", []):
        ntype = n.get("type")
        nid = n.get("id") or ""

        if ntype == "story":
            misplaced: List[str] = []
            if n.get("prd"):
                misplaced.append("prd")
            bg = n.get("brd_goals")
            if isinstance(bg, list) and bg:
                misplaced.append("brd_goals")
            if misplaced:
                findings.append(_f(
                    "misplaced_parent_field", "warn", n,
                    f"Story {nid} carries {misplaced}, but a story's only parent reference is "
                    f"`epic`; those links belong on its PRD/epic, not the story.",
                    fields=misplaced,
                ))

        ver = n.get("version")
        if isinstance(ver, str) and ver.strip() and parse_semver(ver) is None:
            findings.append(_f(
                "bad_version_format", "warn", n,
                f"{nid} version {ver!r} is not semver-lite (major.minor.patch, e.g. 1.0.0).",
                value=ver,
            ))
    return findings
