#!/usr/bin/env python3
"""run_evals — turn a skill's decorative ``evals.json`` into a runnable gate.

Executes each scenario's deterministic (``_gating: structural``) assertions and
exits 0 iff all RUNNABLE structural checks pass. ``llm_advisory`` assertions are
reported ``SKIP(manual)`` (counted, never silently dropped). A structural
assertion with NO machine ``check`` is reported ``UNMAPPED`` (loud, counted,
non-gating by default; gating under ``--strict-structural``) — so manual debt is
visible, never a silent pass. An assertion naming an UNKNOWN checker is a hard
FAIL (misconfiguration), never a skip.

No network, no API key: only deterministic scripts run, in a sandboxed tmp cwd.
Schema-agnostic over the two in-repo shapes (top-level ``evals`` or ``scenarios``).

Usage:
  run_evals.py --skill <name> [--root R] [--strict-structural]
  run_evals.py --evals path/to/evals.json --skill-dir path/to/skill [--strict-structural]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

# Verdicts
PASS, FAIL, SKIP, UNMAPPED = "PASS", "FAIL", "SKIP", "UNMAPPED"


def _scenarios(doc: dict) -> list[dict]:
    return doc.get("evals") or doc.get("scenarios") or []


def _subst(value, ctx: dict):
    """Recursively substitute {out}/{root}/{tmp} placeholders in strings/lists."""
    if isinstance(value, str):
        for k, v in ctx.items():
            value = value.replace("{" + k + "}", str(v))
        return value
    if isinstance(value, list):
        return [_subst(v, ctx) for v in value]
    return value


def _run_exec(execspec: list[str], cwd: Path, ctx: dict) -> subprocess.CompletedProcess:
    argv = _subst(execspec, ctx)
    return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=90)


def _apply_setup(setup: dict, ctx: dict) -> None:
    """Write the scenario's declared files into a fresh runtime root ({runtime_root}).
    Used by scenarios whose fixture cannot be committed (e.g. a dirty repo with .env,
    which the root .gitignore would strip). No network, all inside the tmp root."""
    root = Path(ctx["runtime_root"])
    for rel, body in (setup.get("files") or {}).items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


# --- checkers: each returns (verdict, detail) given (assertion, run, ctx) -------

def _c_file_exists(a, run, ctx):
    p = Path(_subst(a["path"], ctx))
    return (PASS, str(p)) if p.is_file() else (FAIL, f"missing file {p}")


def _c_file_absent(a, run, ctx):
    p = Path(_subst(a["path"], ctx))
    return (FAIL, f"unexpected file {p}") if p.exists() else (PASS, f"absent {p}")


def _c_exit_zero(a, run, ctx):
    if run is None:
        return (FAIL, "no exec run for exit_zero check")
    return (PASS, "exit 0") if run.returncode == 0 else (FAIL, f"exit {run.returncode}: {run.stderr[:160]}")


def _c_stdout_contains(a, run, ctx):
    if run is None:
        return (FAIL, "no exec run")
    needle = _subst(a["substr"], ctx)
    return (PASS, f"found {needle!r}") if needle in (run.stdout + run.stderr) else (FAIL, f"missing {needle!r}")


def _c_stdout_absent(a, run, ctx):
    if run is None:
        return (FAIL, "no exec run")
    needle = _subst(a["substr"], ctx)
    return (FAIL, f"leaked {needle!r}") if needle in (run.stdout + run.stderr) else (PASS, f"absent {needle!r}")


def _c_stdout_json(a, run, ctx):
    if run is None:
        return (FAIL, "no exec run")
    try:
        data = json.loads(run.stdout)
    except Exception as e:  # noqa: BLE001
        return (FAIL, f"stdout not JSON: {e}")
    cur = data
    for key in a["path"].split("."):
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return (FAIL, f"path {a['path']} absent")
    exp = _subst(a.get("equals"), ctx) if "equals" in a else None
    if "equals" in a:
        return (PASS, f"{a['path']}=={cur!r}") if str(cur) == str(exp) else (FAIL, f"{cur!r} != {exp!r}")
    return (PASS, f"{a['path']}=={cur!r}") if cur not in (None, "", []) else (FAIL, f"{a['path']} empty")


def _c_gzip_mtime_zero(a, run, ctx):
    p = Path(_subst(a["path"], ctx))
    if not p.is_file():
        return (FAIL, f"missing {p}")
    with open(p, "rb") as fh:
        header = fh.read(8)
    # gzip header bytes 4..8 = mtime (little-endian); reproducible build → 0.
    return (PASS, "mtime=0") if header[4:8] == b"\x00\x00\x00\x00" else (FAIL, f"mtime bytes {header[4:8]!r}")


def _c_tar_no_member(a, run, ctx):
    p = Path(_subst(a["path"], ctx))
    if not p.is_file():
        return (FAIL, f"missing tar {p}")
    patterns = [_subst(x, ctx) for x in a["patterns"]]
    with tarfile.open(p, "r:gz") as tar:
        names = tar.getnames()
    if len(names) <= a.get("min_members", 0):
        return (FAIL, f"tar too small ({len(names)} members) — vacuous")
    hits = [n for n in names for pat in patterns if pat in n]
    return (FAIL, f"forbidden members: {hits}") if hits else (PASS, f"{len(names)} members, none forbidden")


def _c_sha256_stable(a, run, ctx):
    """Re-run the scenario exec into a 2nd out dir; compare the produced file's bytes."""
    import hashlib

    exec2 = ctx.get("_exec")
    if not exec2:
        return (FAIL, "sha256_stable needs scenario exec")
    rel = a["path"].replace("{out}", "").lstrip("/")
    first = Path(_subst(a["path"], ctx))
    if not first.is_file():
        return (FAIL, f"missing first build {first}")
    h1 = hashlib.sha256(first.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory() as d2:
        ctx2 = dict(ctx, out=d2)
        r2 = _run_exec(exec2, ctx["_cwd"], ctx2)
        if r2.returncode != 0:
            return (FAIL, f"second build failed: {r2.stderr[:160]}")
        second = Path(d2) / rel
        if not second.is_file():
            return (FAIL, f"missing second build {second}")
        h2 = hashlib.sha256(second.read_bytes()).hexdigest()
    return (PASS, f"sha stable {h1[:12]}") if h1 == h2 else (FAIL, f"sha drift {h1[:12]} != {h2[:12]}")


def _c_file_starts_with(a, run, ctx):
    p = Path(_subst(a["path"], ctx))
    if not p.is_file():
        return (FAIL, f"missing {p}")
    prefix = _subst(a["prefix"], ctx)
    return (PASS, "prefix ok") if p.read_text(encoding="utf-8", errors="replace").startswith(prefix) else (FAIL, "prefix mismatch")


CHECKERS = {
    "file_exists": _c_file_exists,
    "file_absent": _c_file_absent,
    "exit_zero": _c_exit_zero,
    "stdout_contains": _c_stdout_contains,
    "stdout_absent": _c_stdout_absent,
    "stdout_json": _c_stdout_json,
    "gzip_mtime_zero": _c_gzip_mtime_zero,
    "tar_no_member": _c_tar_no_member,
    "sha256_stable": _c_sha256_stable,
    "file_starts_with": _c_file_starts_with,
}


def _eval_assertion(a, run, ctx, strict: bool):
    if not isinstance(a, dict):
        return (UNMAPPED, "bare-string assertion (no machine mapping)")
    if a.get("_gating") == "llm_advisory":
        return (SKIP, "manual (llm_advisory)")
    check = a.get("check")
    if not check:
        return (UNMAPPED, "structural, no `check` mapping")
    fn = CHECKERS.get(check)
    if fn is None:
        return (FAIL, f"unknown checker {check!r}")  # misconfiguration is loud, never a skip
    # An assertion may carry its OWN exec (per-assertion script), used when one
    # scenario verifies several independent scripts (e.g. spec_graph + check_consistency).
    local_run = run
    if a.get("exec"):
        try:
            local_run = _run_exec(a["exec"], ctx["_cwd"], ctx)
        except Exception as e:  # noqa: BLE001
            return (FAIL, f"exec failed: {type(e).__name__}: {e}")
    try:
        return fn(a, local_run, ctx)
    except Exception as e:  # noqa: BLE001
        return (FAIL, f"checker {check} raised {type(e).__name__}: {e}")


def run_skill(evals_path: Path, skill_dir: Path, strict: bool) -> tuple[list, dict]:
    doc = json.loads(evals_path.read_text(encoding="utf-8"))
    rows = []
    tally = {PASS: 0, FAIL: 0, SKIP: 0, UNMAPPED: 0}
    repo = skill_dir.resolve().parents[2]  # .claude/skills/<skill> → repo root
    for sc in _scenarios(doc):
        sid = sc.get("id")
        with tempfile.TemporaryDirectory() as out, tempfile.TemporaryDirectory() as rroot:
            exec_cwd = (skill_dir / sc["cwd"]).resolve() if sc.get("cwd") else skill_dir
            ctx = {
                "out": out,
                "runtime_root": rroot,
                "root": str(skill_dir),
                "skill": str(skill_dir),
                "repo": str(repo),
                "py": sys.executable,  # portable: same interpreter that runs the harness (venv/CI)
                "_cwd": exec_cwd,
                "_exec": sc.get("exec"),
            }
            if sc.get("setup"):
                _apply_setup(sc["setup"], ctx)
            run = None
            if sc.get("exec"):
                run = _run_exec(sc["exec"], exec_cwd, ctx)
            for a in sc.get("assertions", []):
                verdict, detail = _eval_assertion(a, run, ctx, strict)
                tally[verdict] += 1
                aid = a.get("id") if isinstance(a, dict) else str(a)[:40]
                rows.append((sid, aid, verdict, detail))
    return rows, tally


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run a skill's structural eval subset as a gate.")
    ap.add_argument("--skill", help="skill name under .claude/skills/")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])  # .claude/skills/_shared/lib → repo root
    ap.add_argument("--evals", type=Path, help="explicit evals.json (overrides --skill)")
    ap.add_argument("--skill-dir", type=Path, help="explicit skill dir (with --evals)")
    ap.add_argument("--strict-structural", action="store_true", help="UNMAPPED structural → fail exit")
    args = ap.parse_args(argv)

    if args.evals:
        evals_path = args.evals
        skill_dir = args.skill_dir or evals_path.parent.parent
    else:
        if not args.skill:
            ap.error("either --skill or --evals is required")
        skill_dir = args.root / ".claude" / "skills" / args.skill
        evals_path = skill_dir / "eval" / "evals.json"
    if not evals_path.is_file():
        print(f"[run_evals] FATAL: evals.json not found at {evals_path}", file=sys.stderr)
        return 2

    rows, tally = run_skill(evals_path, skill_dir, args.strict_structural)
    width = max((len(str(r[1])) for r in rows), default=8)
    for sid, aid, verdict, detail in rows:
        print(f"  [{verdict:<8}] {str(aid):<{width}}  {detail}")
    print(
        f"\n{evals_path.parent.parent.name}: "
        f"{tally[PASS]} pass · {tally[FAIL]} fail · {tally[SKIP]} skip(manual) · {tally[UNMAPPED]} unmapped"
    )
    failed = tally[FAIL] > 0 or (args.strict_structural and tally[UNMAPPED] > 0)
    if failed:
        print("EVAL GATE: FAIL", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
