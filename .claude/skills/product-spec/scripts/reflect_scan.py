#!/usr/bin/env python3
"""
reflect_scan — the deterministic SCRIPT half of the Tier-2 `--reflect` retroactive
harvest.

`--reflect` catches memory writes the inline forcing-functions missed: rulings and
observations that were never recorded, harvested AFTER the fact from
structurally-readable sources only (git history + the on-disk `.memory/`/`decisions.md`
state). This script emits ONLY anchors — it makes NO candidate judgment. The read-only
opus harvester sub-agent (`.claude/agents/memory-harvester.md`) reads these anchors and
proposes candidates; the main agent then interviews the PO and persists ONLY after
confirm (the full flow lives in `references/workflow-reflect.md`). That is the
Script-vs-LLM split (CLAUDE.md): the script correlates disk/git state, the LLM judges.

It NEVER re-implements a reader it can import. The harvest cutoff markers are
`status._load_last_validated` (the validate marker) and the optional `last_reflect.json`
written by a prior harvest; the dedup index reuses `decision_register.parse_decisions`
and `behavioral_memory.load_self_corrections` / `load_po_style` — the SAME readers the
`memory_gap` detector uses (one home per fact; see `references/memory-enforcement.md`
for the single detection-home model). This module only correlates.

Anchors (the emitted envelope):
  - `git_available`          — bool. False when `root` is not a git work tree (or git
                               is unavailable). Then the commit anchors are skipped and
                               only the file-state dedup index is harvested.
  - `commits_since_last`     — commits touching `docs/product/` AFTER the harvest cutoff
                               (the most recent of last_reflect / last_validated; all
                               history when neither marker exists). Each is
                               `{sha, subject, files, is_revert_or_fix}`.
  - `revert_fix_candidates`  — the subset of the above whose subject reads as a
                               revert/fix — a self-correction candidate the inline 3E
                               layer may have missed.
  - `existing_memory`        — the dedup index of what is ALREADY recorded
                               (`decision_ids`, `decision_affects`,
                               `self_correction_slips`, `po_style_keys`) so the harvester
                               never re-proposes a write on record.
  - `parse_errors`           — any artifact the graph could not parse (advisory).

GIT-DEGRADE-SAFE: no git repo → `git_available: false`, empty commit/candidate lists,
the file-state dedup index still harvested, NEVER a crash.

Deterministic: same repo + disk state → the same anchors. Wall-clock provenance
(`scanned_at`) lives OUTSIDE the deterministic body so the compared payload is stable.
ALWAYS exits 0 (advisory feeder) — a malformed artifact surfaces as a `parse_error`
anchor, never a traceback.

CLI:
    reflect_scan.py --root <project-dir>     # emit the anchors envelope, exit 0
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from encoding_utils import configure_utf8_console
from spec_graph import build_graph, _now
import decision_register as dr
import behavioral_memory as bm
# status owns the single home for loading the last-validated marker; reuse it rather
# than re-deriving the marker path (one home for the "what was validated" fact).
from status import _load_last_validated
# check_fence is the single home for the spec-boundary path prefix. A reflect harvest
# only cares about commits that touched the spec tree, so it reuses that constant
# rather than re-declaring it.
from check_fence import FENCE_PREFIX

configure_utf8_console()

# A commit subject reads as a self-correction candidate when it begins with a
# conventional revert/fix marker. Anchored so a "fixture" body word never matches;
# the LLM still judges whether it is truly a recordable slip.
_REVERT_FIX_RE = re.compile(r"^\s*(revert|fix)\b|^\s*revert[:\s]", re.IGNORECASE)


def _last_reflect_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "last_reflect.json"


def _load_last_reflect(root) -> Optional[Dict[str, Any]]:
    """The optional marker a prior `--reflect` confirm wrote (`{reflected_at}`). None
    when absent/corrupt — the harvest then falls back to the validate marker, then to
    full history. Degrade, never raise."""
    try:
        data = json.loads(_last_reflect_path(root).read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _harvest_cutoff(root) -> Optional[str]:
    """The ISO timestamp the commit harvest starts AFTER: the most recent of the
    last-reflect marker and the last-validated marker. None → harvest all history
    (no recorded harvest point yet)."""
    cutoffs: List[str] = []
    reflect = _load_last_reflect(root)
    if reflect and isinstance(reflect.get("reflected_at"), str):
        cutoffs.append(reflect["reflected_at"])
    validated = _load_last_validated(root)
    if validated and isinstance(validated.get("validated_at"), str):
        cutoffs.append(validated["validated_at"])
    return max(cutoffs) if cutoffs else None


# ----------------------------------------------------------------------------
# Git harvest (degrade to empty when not a work tree)
# ----------------------------------------------------------------------------

def _is_git_work_tree(root: Path) -> bool:
    """True only when `root` is inside a git work tree. Any failure (no git, no repo)
    degrades to False — the commit harvest is then skipped, never errored."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(root), capture_output=True, text=True,
        )
    except (OSError, FileNotFoundError):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _commits_since(root: Path, cutoff: Optional[str]) -> List[Dict[str, Any]]:
    """Commits touching `docs/product/` after `cutoff` (all history when None), newest
    first. Each carries `{sha, subject, files, is_revert_or_fix}`. Degrades to [] on
    any git failure (the caller has already gated on `git_available`, but stay soft)."""
    # `-z` makes git NUL-delimit BOTH the per-commit format output and every file name
    # in `--name-only`. So the stdout is a flat NUL-separated stream of fields where a
    # commit-header field carries `<sha>\x1f<subject>\x1e` (the \x1e is the in-format
    # record marker) and each following plain field is one changed path, until the next
    # header field. We use \x1f/\x1e (unit/record separators) so subjects with spaces
    # or newlines never collide with the delimiters.
    args = ["git", "log", "--no-color", "-z",
            "--format=%H%x1f%s%x1e", "--name-only"]
    if cutoff:
        args.append(f"--since={cutoff}")
    args += ["--", FENCE_PREFIX]
    try:
        proc = subprocess.run(args, cwd=str(root), capture_output=True, text=True)
    except (OSError, FileNotFoundError):
        return []
    if proc.returncode != 0:
        return []

    out: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    raw_files: List[str] = []

    def _flush():
        if current is not None:
            files = sorted({
                f.replace("\\", "/").strip()
                for f in raw_files
                if f.strip().replace("\\", "/").startswith(FENCE_PREFIX)
            })
            current["files"] = files
            out.append(current)

    for field in proc.stdout.split("\x00"):
        field = field.strip("\n")
        if not field:
            continue
        if "\x1e" in field:
            # A new commit header field — flush the one in progress, start fresh.
            _flush()
            header = field.split("\x1e", 1)[0]
            sha, _, subject = header.partition("\x1f")
            sha = sha.strip()
            subject = subject.strip()
            current = {
                "sha": sha,
                "subject": subject,
                "files": [],
                "is_revert_or_fix": bool(_REVERT_FIX_RE.search(subject)),
            }
            raw_files = []
        else:
            # A changed-path field belonging to the current commit.
            raw_files.append(field)
    _flush()
    # Drop any header with an empty sha (defensive — should not happen).
    return [c for c in out if c["sha"]]


# ----------------------------------------------------------------------------
# Dedup index — reuse the existing memory readers (no re-homed parser)
# ----------------------------------------------------------------------------

def _existing_memory_index(root) -> Dict[str, List[str]]:
    """What is ALREADY on record, so the harvester never re-proposes it. Reuses the
    SAME readers `memory_gap` uses — `decision_register.parse_decisions` (every DEC,
    active + superseded) and `behavioral_memory.load_self_corrections` / `load_po_style`
    (across both lang partitions). No new parser; one home per fact.

    Lists are sorted so the index is deterministic across runs."""
    decisions = dr.parse_decisions(root)
    decision_ids = sorted({r["id"] for r in decisions if r.get("id")})
    decision_affects = sorted({r["affects"] for r in decisions if r.get("affects")})

    slips = sorted({
        str(c.get("slip")) for c in bm.load_self_corrections(root)
        if c.get("slip")
    })

    # po-style is lang-keyed; surface the recorded field keys per lang that actually
    # carry content, so the harvester can tell "voice already captured for en/vi".
    po_keys: List[str] = []
    for lang in sorted(bm.LANGS):
        style = bm.load_po_style(root, lang)
        for key, val in (style or {}).items():
            if val in (None, "", [], {}):
                continue
            po_keys.append(f"{lang}:{key}")
    po_keys = sorted(set(po_keys))

    return {
        "decision_ids": decision_ids,
        "decision_affects": decision_affects,
        "self_correction_slips": slips,
        "po_style_keys": po_keys,
    }


# ----------------------------------------------------------------------------
# Correlate → anchors
# ----------------------------------------------------------------------------

def collect(root) -> Dict[str, Any]:
    """Build the full reflect anchor envelope for `root`, deterministically.

    Git-degrade-safe: with no work tree the commit anchors are empty and
    `git_available` is False; the file-state dedup index is harvested regardless. A
    malformed artifact surfaces as a `parse_error` anchor (from the graph) — never a
    crash. The returned dict is stable for a given repo + disk state."""
    root = Path(root).resolve()

    git_available = _is_git_work_tree(root)
    if git_available:
        commits = _commits_since(root, _harvest_cutoff(root))
        revert_fix = [c for c in commits if c["is_revert_or_fix"]]
    else:
        commits = []
        revert_fix = []

    # parse_errors come from the graph build; advisory only (never block a harvest).
    parse_errors: List[Dict[str, Any]] = []
    try:
        graph = build_graph(root)
        for pe in graph.get("parse_errors") or []:
            parse_errors.append({
                "type": "parse_error",
                "file": pe.get("file"),
                "detail": f"{pe.get('file')} could not be parsed: {pe.get('error')}",
            })
    except Exception as exc:  # noqa: BLE001 — advisory: a graph failure is surfaced
        parse_errors.append({
            "type": "parse_error", "file": None, "detail": str(exc),
        })

    return {
        "git_available": git_available,
        "commits_since_last": commits,
        "revert_fix_candidates": revert_fix,
        "existing_memory": _existing_memory_index(root),
        "parse_errors": parse_errors,
    }


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    try:
        anchors = collect(root)
    except Exception as exc:  # noqa: BLE001 — advisory contract: never crash
        # Any unexpected failure surfaces as a parse_error anchor + exit 0, never a
        # bare traceback (mirrors the analytical-script advisory contract).
        anchors = {
            "git_available": False,
            "commits_since_last": [],
            "revert_fix_candidates": [],
            "existing_memory": {
                "decision_ids": [], "decision_affects": [],
                "self_correction_slips": [], "po_style_keys": [],
            },
            "parse_errors": [{"type": "parse_error", "file": None, "detail": str(exc)}],
        }

    # `scanned_at` is wall-clock provenance OUTSIDE the deterministic `collect()` body
    # (same envelope discipline as the other anchor feeders).
    output = {"schema_version": "1.0", "root": str(root),
              "scanned_at": _now(), **anchors}
    print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
