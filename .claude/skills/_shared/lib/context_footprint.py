#!/usr/bin/env python3
"""context_footprint — deterministic, offline per-skill context-size harness.

Measures the honest, parseable unit: per-skill ``SKILL.md`` token proxy + each ``references/*.md``
+ the skill total. Two deterministic gates: (1) SIZE (``--gate``) — non-zero if a skill's SKILL.md
or total GREW vs baseline; (2) CO-PRESENCE — every referenced GATE (``GATE-X`` or ``GATE:X``) must
have a reachable full-prose home (always-on root ``CLAUDE.md`` OR inside the skill's files), else
fail (blocks silently orphaning a safety GATE). The per-flag load-set is ADVISORY only (red-team
MAJOR-3). Token proxy = ``ceil(chars/4)``: approximate, relative-only. Stdlib only; JSON output.

Usage:
  context_footprint.py --baseline --skills <dir>... --always-on CLAUDE.md --out base.json
  context_footprint.py --compare base.json --skills <dir>... --always-on CLAUDE.md --gate
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

# Matches BOTH conventions: the always-on home form `GATE-NAME` (tag/heading) and the in-row
# pointer form `GATE:NAME` used in the compacted flag rows. Both normalize to canonical `GATE-NAME`.
# Leading boundary: no mid-word match (`MITIGATE-X`). Suffix: single-char (`GATE-X`) OR multi-char,
# never ending in a dash (the optional tail closes on `[A-Z0-9]`).
GATE_RE = re.compile(r"(?<![A-Za-z])GATE[-:](?P<suffix>[A-Z](?:[A-Z0-9-]*[A-Z0-9])?)")


def _gate_names(text: str) -> set[str]:
    """Every GATE referenced in `text`, normalized to the canonical `GATE-<NAME>` key
    (so a `GATE:NO-SILENT-REVERSAL` pointer resolves to the `GATE-NO-SILENT-REVERSAL` home)."""
    return {"GATE-" + m.group("suffix") for m in GATE_RE.finditer(text)}


# --- token proxy -------------------------------------------------------------

def token_proxy(text: str) -> int:
    """Approximate token count: ceil(chars/4). Relative-only; never absolute truth."""
    return math.ceil(len(text) / 4)


# --- per-skill measurement ---------------------------------------------------

def _flag_rows(skill_md: str) -> list[str]:
    """Advisory: pull markdown flag-table rows (lines starting with `|` that look like
    `| <flag> | <purpose> |`). Skips separator rows. Best-effort, never gated on."""
    rows: list[str] = []
    for line in skill_md.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        if set(line) <= set("|-: "):  # separator row ---|---
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells and cells[0] and not cells[0].lower().startswith("flag"):
            rows.append(line)
    return rows


def measure_skill(skill_dir: Path) -> dict:
    """Token proxy of SKILL.md + each references/*.md + skill total. Graceful when a
    skill has no flag table (size only, no crash)."""
    skill_md_path = skill_dir / "SKILL.md"
    skill_md = skill_md_path.read_text(encoding="utf-8") if skill_md_path.is_file() else ""
    refs: dict[str, int] = {}
    ref_dir = skill_dir / "references"
    if ref_dir.is_dir():
        for ref in sorted(ref_dir.glob("*.md")):
            refs[ref.name] = token_proxy(ref.read_text(encoding="utf-8"))
    skill_md_tokens = token_proxy(skill_md)
    return {
        "skill_md_tokens": skill_md_tokens,
        "refs": refs,
        "total_tokens": skill_md_tokens + sum(refs.values()),
        "flag_rows": _flag_rows(skill_md),  # advisory only
    }


def measure_all(skill_dirs: list[Path]) -> dict:
    return {d.name: measure_skill(d) for d in skill_dirs}


# --- baseline / compare / size gate -----------------------------------------

def compare(base: dict, after: dict) -> dict:
    """Per-skill deltas (negative = shrank). Iterates `after`: a new skill (absent in baseline)
    counts as growth (gate fails until the baseline is refreshed); a skill present in baseline but
    REMOVED from `after` is silently dropped — deletion detection is not a goal of this size gate."""
    diff: dict[str, dict] = {}
    for name, a in after.items():
        b = base.get(name, {"skill_md_tokens": 0, "total_tokens": 0})
        diff[name] = {
            "skill_md_delta": a["skill_md_tokens"] - b.get("skill_md_tokens", 0),
            "total_delta": a["total_tokens"] - b.get("total_tokens", 0),
            "skill_md_tokens": a["skill_md_tokens"],
            "total_tokens": a["total_tokens"],
        }
    return diff


def gate(diff: dict) -> tuple[bool, list[str]]:
    """SIZE gate: fail if any skill's SKILL.md OR total grew vs baseline."""
    regressions: list[str] = []
    for name, d in diff.items():
        if d["skill_md_delta"] > 0:
            regressions.append(f"{name}: SKILL.md grew +{d['skill_md_delta']} tokens")
        if d["total_delta"] > 0:
            regressions.append(f"{name}: skill total grew +{d['total_delta']} tokens")
    return (not regressions, regressions)


# --- GATE co-presence check (the safety guard) ------------------------------

def _full_home_gates(text: str) -> set[str]:
    """GATEs (canonical `GATE-<NAME>`) with a full-prose home in `text`: a `<GATE-X>...</GATE-X>`
    tag block OR a bold definition `**GATE-X:**` / `**GATE:X**` — the canonical full-prose forms
    in this repo. A bare `GATE:X` / `see ... GATE-X` mention is a POINTER, not a home."""
    homes: set[str] = set()
    for gate in _gate_names(text):
        suffix = gate[len("GATE-"):]
        if re.search(rf"<{gate}>.*?</{gate}>", text, re.DOTALL):
            homes.add(gate)
        elif re.search(rf"\*\*GATE[-:]{re.escape(suffix)}:?\*\*", text):
            homes.add(gate)
    return homes


def copresence_check(skill_dirs: list[Path], always_on_text: str) -> list[str]:
    """For every GATE referenced in a skill's SKILL.md / refs (hyphen `GATE-X` or colon `GATE:X`),
    require its full-prose home reachable: always-on (root CLAUDE.md) OR full-prose anywhere in that
    skill's own files (SKILL.md ∪ its refs). NOTE: reachability is pooled per-SKILL, not per-flag
    load-set — the flat-prose per-flag map is unreliable (advisory only, red-team MAJOR-3), so the
    deterministic guard uses the skill-wide pool ∪ always-on. Conservative: a referenced GATE with
    no resolvable home anywhere FAILS (blocks silently orphaning a safety GATE)."""
    always_homes = _full_home_gates(always_on_text)
    failures: list[str] = []
    for sk in skill_dirs:
        files = []
        smd = sk / "SKILL.md"
        if smd.is_file():
            files.append(smd)
        ref_dir = sk / "references"
        if ref_dir.is_dir():
            files.extend(sorted(ref_dir.glob("*.md")))
        texts = {f: f.read_text(encoding="utf-8") for f in files}
        skill_homes = set().union(*(_full_home_gates(t) for t in texts.values())) if texts else set()
        reachable = always_homes | skill_homes
        for f, t in texts.items():
            for g in _gate_names(t):
                if g not in reachable:
                    failures.append(f"{sk.name}/{f.name}: pointer to {g} has no reachable full-prose home")
    return sorted(set(failures))


# --- CLI ---------------------------------------------------------------------

def _print_advisory(measured: dict) -> None:
    for name, m in measured.items():
        print(f"  [advisory] {name}: {len(m['flag_rows'])} flag rows parsed (flat-prose, approximate)",
              file=sys.stderr)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Per-skill SKILL.md/ref token harness + GATE co-presence guard.")
    ap.add_argument("--skills", nargs="+", required=True, help="skill dirs to measure")
    ap.add_argument("--always-on", required=True, help="always-on layer (root CLAUDE.md) for GATE homes")
    ap.add_argument("--baseline", action="store_true", help="write baseline JSON to --out")
    ap.add_argument("--compare", help="baseline JSON to diff the current tree against")
    ap.add_argument("--gate", action="store_true", help="exit non-zero on SKILL.md/total growth")
    ap.add_argument("--out", help="baseline JSON output path")
    args = ap.parse_args(argv)

    skill_dirs = [Path(s) for s in args.skills]
    always_on_text = Path(args.always_on).read_text(encoding="utf-8")
    measured = measure_all(skill_dirs)

    # CO-PRESENCE gate always runs (safety guard, independent of size).
    cop_failures = copresence_check(skill_dirs, always_on_text)

    if args.baseline:
        payload = {n: {k: v for k, v in m.items() if k != "flag_rows"} for n, m in measured.items()}
        out = Path(args.out) if args.out else Path("context_footprint_baseline.json")
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"baseline written: {out}")
        _print_advisory(measured)
        if cop_failures:
            for f in cop_failures:
                print(f"CO-PRESENCE FAIL: {f}", file=sys.stderr)
            return 1
        return 0

    if args.compare:
        base = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        diff = compare(base, measured)
        for name, d in sorted(diff.items()):
            print(f"  {name}: SKILL.md Δ{d['skill_md_delta']:+d} · total Δ{d['total_delta']:+d} tokens")
        ok, regressions = gate(diff)
        for f in cop_failures:
            print(f"CO-PRESENCE FAIL: {f}", file=sys.stderr)
        if args.gate and (not ok or cop_failures):
            for r in regressions:
                print(f"SIZE GATE FAIL: {r}", file=sys.stderr)
            print("CONTEXT FOOTPRINT GATE: FAIL", file=sys.stderr)
            return 1
        return 0

    ap.error("one of --baseline / --compare is required")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
