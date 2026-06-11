#!/usr/bin/env python3
"""critique_provenance.py — report frontmatter + the reuse decision.

A critique report carries YAML frontmatter so the NEXT run can decide what to reuse
(none / full / consolidate_only / relens). This is the ECONOMIC gate (token savings),
never a safety gate — every outcome is safe; `--fresh`/`--force` forces `none`.

Per the Script-vs-LLM split: this module decides only WHAT is reusable (a structural
diff over body_hash maps + level/lang); it never decides voice. The orchestrator
reads `bundle["provenance"]["reuse"]` and branches."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml  # pyyaml — vendored in the shared venv (product-spec dep)

import critique_cache
from critique_common import (
    BUNDLE_VERSION, _import_psp, _now, _provenance_hash, _scoped_content_hashes,
)


def _read_report_frontmatter(path: Path) -> Optional[Dict[str, Any]]:
    """Parse a critique report's leading YAML frontmatter (`---` … `---`), or None
    when the file has no frontmatter / is malformed / unreadable. NEVER raises — a
    malformed block degrades to None (the report is then filename-fallback)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None
    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _prior_reports(root: Path) -> List[Dict[str, Any]]:
    """Prior critique reports under docs/product/critique/, sorted by filename.

    Frontmatter-bearing reports (new) yield the richer record
    `{path, ts, critique_scope, level, lang, body_hash, lens_findings_hash}`; old
    no-frontmatter reports fall back to `{path, ts, scope: None, body_hash: None}`.
    The filename is NEVER trusted for scope (`c1-all-lvl3.md` would mangle to
    `scope='all-lvl3'`); scope comes from frontmatter `critique_scope` only."""
    crit_dir = root / "docs" / "product" / "critique"
    if not crit_dir.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    for p in sorted(crit_dir.glob("*.md")):
        ts = p.stem.partition("-")[0]  # display/sort only — never used for scope
        fm = _read_report_frontmatter(p)
        if fm and fm.get("critique_scope") is not None:
            bh = fm.get("body_hash")
            out.append({
                "path": str(p),
                "ts": ts,
                "critique_scope": fm.get("critique_scope"),
                "level": fm.get("level"),
                "lang": fm.get("lang"),
                "register": fm.get("register"),  # only present at level >= 7
                "body_hash": bh if isinstance(bh, dict) else None,
                "lens_findings_hash": fm.get("lens_findings_hash"),
            })
        else:
            out.append({"path": str(p), "ts": ts, "scope": None, "body_hash": None})
    return out


def build_report_frontmatter(root: Path, scope: str, level: int, lang: str,
                             register: Optional[Dict[str, str]],
                             lens_findings_hash: str) -> str:
    """Emit the YAML frontmatter block (`---` … `---\\n`) a critique report carries
    so the next run can decide reuse. The per-node map reuses the live scoped CONTENT
    hashes (NOT recomputed elsewhere — DRY). Its frontmatter key stays the wire-name
    `body_hash` for back-compat with already-shipped reports, but the values are the
    content fingerprint (body + acceptance_criteria) — see spec_graph.content_hash.
    `register` is included only at level >= 7. The full lens-findings array is NOT
    inlined here — it lives in the lens-cache keyed by `lens_findings_hash`; the report
    only carries the key."""
    spec_graph = _import_psp()[0]
    fm: Dict[str, Any] = {
        "critique_scope": scope,
        "level": level,
        "lang": lang,
        # wire-name kept for back-compat; holds the content fingerprint (body + AC).
        "body_hash": _scoped_content_hashes(spec_graph, root, scope),
        "lens_findings_hash": lens_findings_hash,
        "bundle_version": BUNDLE_VERSION,
    }
    if level >= 7 and register:
        fm["register"] = register
    block = yaml.safe_dump(fm, sort_keys=True, allow_unicode=True,
                          default_flow_style=False)
    return f"---\n{block}---\n"


def _latest_frontmatter_prior(root: Path, scope: str) -> Optional[Dict[str, Any]]:
    """The most recent frontmatter-bearing prior report whose `critique_scope`
    matches `scope` AND carries a body_hash map. Filename-only priors are excluded
    (never scope-matched by filename). None when there is no usable prior."""
    candidates = [r for r in _prior_reports(root)
                  if r.get("critique_scope") == scope and isinstance(r.get("body_hash"), dict)]
    return candidates[-1] if candidates else None


def _decide_unchanged(root: Path, level: int, lang: str,
                      register: Optional[Dict[str, str]], rec: Dict[str, Any],
                      report: Optional[str]) -> Dict[str, Any]:
    """Decide the verdict when the spec body is UNCHANGED vs `rec` (the prior report
    or the critique-state record): `full` only when level+lang+register ALL match
    (register is a voice axis at level >= 7; a gender/dialect/profanity flip must
    re-render); else `consolidate_only` when the lens-cache array is present; else
    `relens` (lens-cache missing → re-lens, never a broken half-reuse)."""
    if (rec.get("level") == level and rec.get("lang") == lang
            and (rec.get("register") or None) == (register or None)):
        return {"reuse": "full", "report": report}
    lh = rec.get("lens_findings_hash")
    if lh and critique_cache.get_lens_findings(root, lh) is not None:
        return {"reuse": "consolidate_only", "report": report, "lens_findings_hash": lh}
    return {"reuse": "relens", "changed_ids": [], "report": report}


def _report_exists(root: Path, rep: Optional[str]) -> bool:
    """True iff the report path (absolute, or relative to root) exists on disk."""
    if not rep:
        return False
    p = Path(rep)
    if not p.is_absolute():
        p = Path(root) / rep
    return p.exists()


def compute_provenance_reuse(root: Path, scope: str, level: int, lang: str,
                             register: Optional[Dict[str, str]] = None,
                             fresh: bool = False) -> Dict[str, Any]:
    """The 4-way reuse decision: none / full / consolidate_only / relens.

    `--fresh`/`--force` forces `none`. Scope is matched from frontmatter
    `critique_scope` ONLY. Fast-path: a `critique-state.json`
    `provenance_hash` match short-circuits BEFORE opening any prior report — UNLESS
    that would return `full` pointing at a report that no longer exists (e.g. purged
    by a regen), in which case it falls through to the slow path."""
    if fresh:
        return {"reuse": "none"}
    spec_graph = _import_psp()[0]
    live = _scoped_content_hashes(spec_graph, root, scope)
    prov_hash = _provenance_hash(live)

    # FAST PATH: trust critique-state on a provenance_hash match — body is known
    # unchanged, so decide from the stored record without reading the prior report.
    state_rec = critique_cache.load_state(root).get(scope) or {}
    if prov_hash and state_rec.get("provenance_hash") == prov_hash:
        decision = _decide_unchanged(root, level, lang, register, state_rec,
                                     report=state_rec.get("report"))
        # A `full` verdict points at a deliverable report — only short-circuit when it
        # actually exists; a dangling path falls through to the slow path.
        if not (decision["reuse"] == "full" and not _report_exists(root, decision.get("report"))):
            return decision

    # SLOW PATH: consult the frontmatter-bearing prior reports.
    prior = _latest_frontmatter_prior(root, scope)
    if prior is None:
        return {"reuse": "none"}
    prior_bh = prior.get("body_hash") or {}
    if prior_bh != live:
        ids = set(live) | set(prior_bh)
        changed = sorted(i for i in ids if live.get(i) != prior_bh.get(i))
        return {"reuse": "relens", "changed_ids": changed, "report": prior["path"]}
    return _decide_unchanged(root, level, lang, register, prior, report=prior["path"])


def record_critique_state(root: Path, scope: str, level: int, lang: str,
                          lens_findings_hash: Optional[str], blocker_count: int,
                          register: Optional[Dict[str, str]] = None,
                          report: Optional[str] = None,
                          now_iso: Optional[str] = None) -> Path:
    """Persist the per-scope critique-state marker (the provenance fast-path source)
    after a real run: provenance_hash (= hash of the scoped body_hash map),
    last_ts, blocker_count, drift_since=0, plus level/lang/register/lens_findings_hash/
    report so the next run's fast-path can fully decide reuse (incl. the register
    voice axis) without reading the report."""
    spec_graph = _import_psp()[0]
    prov_hash = _provenance_hash(_scoped_content_hashes(spec_graph, root, scope))
    return critique_cache.save_state(
        root, scope,
        last_ts=now_iso or _now(),
        provenance_hash=prov_hash,
        blocker_count=blocker_count,
        drift_since=0,
        level=level,
        lang=lang,
        register=register,
        lens_findings_hash=lens_findings_hash,
        report=report,
    )
