#!/usr/bin/env python3
"""
decision_register — the Decision Register: the authoritative, append-only home
for explicit PO rulings (`DEC-<n>`).

A decision is recorded when the PO makes a binding call the spec must not
re-litigate: a standalone `--decision`, or a Keep/Change/Hybrid resolve of a
contradiction against an `approved` artifact. The register kills re-litigation —
the next time the same tension surfaces, the orchestration layer reads the
register FIRST and surfaces the prior ruling ("you decided DEC-n because … —
keep or supersede?") instead of re-asking.

SCRIPT-vs-LLM split (CLAUDE.md): this script owns the deterministic structural
work — allocate the next monotonic id, validate the `^DEC-\\d+$` grammar + the
record shape, append WITHOUT overwriting prior records, parse + list. The LLM
owns the human RATIONALE prose it passes in as `--rationale`.

Storage: `docs/product/decisions.md` (visible, committed). Each ruling is one
record block: a `---`-fenced YAML mini-frontmatter (`id`/`status`/`date`/
`affects`/`supersedes`) followed by a `## DEC-<n> — <title>` heading + rationale.
Records are concatenated newest-last. The write goes through the shared soft
fence (`fs_guard`) so a register write can never escape docs/product/.

ID grammar: `^DEC-\\d+$`. `--alloc-id` returns max-existing + 1 (read-then-write;
single-PO, so no lock — a team-mode advisory lock is a future note). Numbering is
monotonic regardless of status: a superseded DEC still counts toward the max, so
ids are never reused.

CLI:
    decision_register.py --root <dir> --alloc-id
    decision_register.py --root <dir> --append --id DEC-2 --title "..." \\
        --rationale "..." [--affects PRD-AUTH] [--supersedes DEC-1]
    decision_register.py --root <dir> --list   # active records as JSON
"""

import argparse
import contextlib
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from encoding_utils import configure_utf8_console
from fs_guard import assert_under_docs_product
# Shared append-only fenced-record machinery (also used by record_outcome): the
# block-splitter regex, injection escape, file lock, and raw id scan live in ONE home.
from register_store import (
    RECORD_RE as _RECORD_RE, escape_injection, register_lock, scan_record_ids,
)

configure_utf8_console()


# This register's own heading anchor. A rationale line that is a bare `---` fence would
# split decisions.md into a phantom record; a `## DEC-<n>` line could smuggle a fake
# decision heading. Both are neutralized on write by the shared escape_injection, which
# backslash-escapes the line anchors (content preserved + markdown-correct: `\---`,
# `\## ` render literally) so the line no longer matches the record/heading patterns.
_INJ_DEC_HEADING_RE = re.compile(r"(?m)^(##\s+DEC-)")


def sanitize_rationale(rationale: str) -> str:
    """Neutralize record-fence / DEC-heading injection in PO/finding-supplied rationale,
    preserving the text (shared escape_injection, with this register's DEC anchor)."""
    return escape_injection(rationale, _INJ_DEC_HEADING_RE)


@contextlib.contextmanager
def _register_lock(root):
    """alloc-id + append as ONE critical section over this register's lock file (a thin
    wrapper over the shared register_lock; closes the looped-alloc TOCTOU window)."""
    with register_lock(Path(root) / "docs" / "product" / ".decision_register.lock"):
        yield


class DecisionError(ValueError):
    """Raised on a grammar/shape/uniqueness violation (surfaced as a JSON
    finding by the CLI; raised directly for library callers)."""


# ID grammar: DEC- followed by one-or-more digits, nothing else. Parent-free and
# globally monotonic — unlike the parent-scoped artifact IDs, a decision is a
# cross-cutting ruling with no single parent.
DECISION_ID_RE = re.compile(r"^DEC-\d+$")

# `_RECORD_RE` (the `---`-fenced block splitter) is imported from register_store —
# shared byte-identically with the Outcome Register.

TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent / "assets" / "templates" / "decision-record.md"
)


def _decisions_path(root) -> Path:
    return Path(root) / "docs" / "product" / "decisions.md"


def parse_decisions(root) -> List[Dict[str, Any]]:
    """Return every record (active AND superseded), in file order.

    Each record is a dict with at least `id`, `status`, `date`; plus `affects`,
    `supersedes`, and `title` when present. A missing file → empty list. A
    record whose YAML is unparseable or whose id is malformed is skipped (the
    register stays fail-soft — a single corrupt block never sinks `--list`)."""
    path = _decisions_path(root)
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return []

    records: List[Dict[str, Any]] = []
    for m in _RECORD_RE.finditer(text):
        try:
            fm = yaml.safe_load(m.group("fm")) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(fm, dict):
            continue
        dec_id = str(fm.get("id", "")).strip()
        if not DECISION_ID_RE.match(dec_id):
            continue
        rec: Dict[str, Any] = {
            "id": dec_id,
            "status": str(fm.get("status", "active")).strip() or "active",
            "date": str(fm.get("date", "")).strip(),
        }
        for opt in ("affects", "supersedes"):
            val = fm.get(opt)
            rec[opt] = str(val).strip() if val not in (None, "") else ""
        rec["title"] = _title_from_body(m.group("body"), dec_id)
        records.append(rec)
    return records


def _title_from_body(body: str, dec_id: str) -> str:
    """Pull the `## DEC-n — <title>` heading text, or "" when absent."""
    m = re.search(rf"^##\s+{re.escape(dec_id)}\s*[—-]\s*(?P<title>.+?)\s*$", body, re.MULTILINE)
    return m.group("title").strip() if m else ""


def list_active(root) -> List[Dict[str, Any]]:
    """Records with `status: active` only — the rulings still in force."""
    return [r for r in parse_decisions(root) if r["status"] == "active"]


def alloc_id(root) -> str:
    """Next free `DEC-<n>` = max-existing + 1 (or DEC-1 on an empty register).

    Monotonic across ALL records regardless of status — a superseded id is never
    reused, so lineage references stay unambiguous.

    The max is taken over the RAW `id:` lines of every `---`-fenced block, not
    just the records `parse_decisions` returns. A block with a parseable
    `id: DEC-n` but otherwise corrupt YAML is fail-soft-skipped on parse, yet its
    id is still claimed — scanning raw text keeps it counted so a later repair of
    that block can never collide with an id allocated in the meantime."""
    used = []
    for dec_id in _scan_all_ids(root):
        m = re.match(r"^DEC-(\d+)$", dec_id)
        if m:
            used.append(int(m.group(1)))
    n = (max(used) + 1) if used else 1
    return f"DEC-{n}"


def _scan_all_ids(root) -> List[str]:
    """Every `id:` value across all `---`-fenced blocks, incl. blocks whose YAML
    is otherwise unparseable. Source-of-truth for id allocation so corrupt-but-
    id-bearing blocks still reserve their number."""
    path = _decisions_path(root)
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return []
    return scan_record_ids(text)


def _render_record(
    dec_id: str, title: str, rationale: str, date: str,
    affects: str, supersedes: str, status: str,
) -> str:
    """Fill the decision-record template, stripping the header comment + any
    empty optional link fields so an absent `affects`/`supersedes` does not leak
    a literal `affects:` line into the register."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    # Drop the leading template comment (the WHY/DRY-guard note is for authors).
    template = re.sub(r"\A\s*<!--.*?-->\s*\n", "", template, count=1, flags=re.DOTALL)
    values = {
        "id": dec_id,
        "status": status,
        "date": date,
        "affects": affects,
        "supersedes": supersedes,
        "title": title,
        "rationale": rationale.strip(),
    }
    out = template
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", str(val))
    # Remove link lines the caller did not supply (keeps the YAML clean rather
    # than carrying empty `affects:`/`supersedes:` keys).
    out = re.sub(r"^affects:\s*$\n?", "", out, flags=re.MULTILINE) if not affects else out
    out = re.sub(r"^supersedes:\s*$\n?", "", out, flags=re.MULTILINE) if not supersedes else out
    return out.strip() + "\n"


def append_decision(
    root,
    dec_id: str,
    title: str,
    rationale: str,
    affects: str = "",
    supersedes: str = "",
    date: Optional[str] = None,
    status: str = "active",
) -> Path:
    """Validate + append one record. Append-only: prior records are untouched.

    Raises DecisionError on a malformed id, a duplicate id, or a `supersedes`
    pointing at an id not in the register. Returns the decisions.md path."""
    if not DECISION_ID_RE.match(dec_id):
        raise DecisionError(
            f"decision id {dec_id!r} does not match the grammar {DECISION_ID_RE.pattern}"
        )
    if not title.strip():
        raise DecisionError("a decision needs a non-empty title")
    if not rationale.strip():
        raise DecisionError("a decision needs a non-empty rationale (the WHY)")
    if supersedes and not DECISION_ID_RE.match(supersedes):
        raise DecisionError(
            f"supersedes {supersedes!r} is not a valid decision id "
            f"({DECISION_ID_RE.pattern})"
        )

    existing = parse_decisions(root)
    existing_ids = {r["id"] for r in existing}
    if dec_id in existing_ids:
        raise DecisionError(
            f"{dec_id} already exists in the register; the register is append-only "
            f"(use a fresh --alloc-id, and `supersedes:` to retire the old one)"
        )
    if supersedes and supersedes not in existing_ids:
        raise DecisionError(
            f"supersedes {supersedes} but that id is not in the register"
        )

    record = _render_record(
        dec_id, title, sanitize_rationale(rationale),
        date or dt.date.today().isoformat(),
        affects, supersedes, status,
    )

    path = _decisions_path(root)
    # Soft fence: resolve + contain BEFORE any mkdir/write so a tampered root
    # cannot place the register outside the spec boundary.
    assert_under_docs_product(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        prior = path.read_text(encoding="utf-8")
        sep = "" if prior.endswith("\n\n") else ("\n" if prior.endswith("\n") else "\n\n")
        new_text = prior + sep + record
    else:
        new_text = "# Decision Register\n\n" + record

    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_text)
    return path


def _supersede_in_place(root, dec_id: str) -> bool:
    """Flip an existing active record to `status: superseded` (called when a new
    record supersedes it). Returns True if a record was flipped.

    This is the ONE in-place edit the register makes — and it touches only the
    `status:` line of the retired record, never its rationale (no prose
    overwrite). The new ruling is still appended separately."""
    path = _decisions_path(root)
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return False

    flipped = {"hit": False}

    def _flip(m: re.Match) -> str:
        fm = m.group("fm")
        try:
            data = yaml.safe_load(fm) or {}
        except yaml.YAMLError:
            return m.group(0)
        if isinstance(data, dict) and str(data.get("id", "")).strip() == dec_id:
            new_fm = re.sub(r"^status:\s*\S+\s*$", "status: superseded", fm, count=1, flags=re.MULTILINE)
            flipped["hit"] = True
            # _RECORD_RE consumes the closing-fence newline AND the blank line that
            # follows it into the gap before `body`, so reinsert that blank line to
            # round-trip a committed file byte-stably (---\n\n## DEC-n, not ---\n##).
            return f"---\n{new_fm}\n---\n\n{m.group('body').lstrip(chr(10))}"
        return m.group(0)

    new_text = _RECORD_RE.sub(_flip, text)
    if flipped["hit"]:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)
    return flipped["hit"]


def append_alloc(
    root,
    title: str,
    rationale: str,
    affects: str = "",
    supersedes: str = "",
    date: Optional[str] = None,
    status: str = "active",
) -> Dict[str, Any]:
    """Allocate the next id AND append in ONE locked critical section.

    The apply-critique loop never holds an allocated id across a PO-interaction gap —
    it gathers the ruling first, then calls this once to alloc+append atomically. On a
    dup-id race (shouldn't happen under the lock, but defended) `append_decision` raises
    and we return `{"written": false, ...}` so the loop can abort/retry — never silently
    drop a ruling. Returns a dict mirroring the CLI JSON."""
    with _register_lock(root):
        dec_id = alloc_id(root)
        path = append_decision(
            root, dec_id=dec_id, title=title, rationale=rationale,
            affects=affects, supersedes=supersedes, date=date, status=status,
        )
        if supersedes:
            _supersede_in_place(root, supersedes)
    return {"id": dec_id, "path": str(Path(path).relative_to(Path(root).resolve())), "written": True}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--alloc-id", action="store_true", help="print the next free DEC-<n>")
    mode.add_argument("--append", action="store_true", help="append a decision record")
    mode.add_argument("--append-alloc", action="store_true",
                      help="atomic: alloc the next id AND append in one locked critical section")
    mode.add_argument("--list", action="store_true", help="print active decisions as JSON")
    ap.add_argument("--id", help="decision id (with --append); default = alloc")
    ap.add_argument("--title")
    ap.add_argument("--rationale")
    ap.add_argument("--affects", default="")
    ap.add_argument("--supersedes", default="")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    try:
        if args.alloc_id:
            print(json.dumps({"id": alloc_id(root)}, ensure_ascii=False))
            return 0
        if args.list:
            print(json.dumps({"active": list_active(root)}, indent=2, ensure_ascii=False))
            return 0
        if args.append_alloc:
            result = append_alloc(
                root, title=args.title or "", rationale=args.rationale or "",
                affects=args.affects, supersedes=args.supersedes,
            )
            print(json.dumps(result, ensure_ascii=False))
            return 0
        # --append
        dec_id = args.id or alloc_id(root)
        # Validate + write the new record FIRST. append_decision re-checks title /
        # rationale / dup-id / `supersedes in existing_ids`, so a caller error
        # (empty rationale, colliding id, dangling supersedes) leaves the register
        # byte-untouched. Only on a successful append do we flip the prior record
        # to superseded — otherwise a rejected append would still retire a live
        # ruling, corrupting the register into zero-active + phantom-retired.
        path = append_decision(
            root, dec_id=dec_id, title=args.title or "",
            rationale=args.rationale or "", affects=args.affects,
            supersedes=args.supersedes,
        )
        if args.supersedes:
            _supersede_in_place(root, args.supersedes)
        print(json.dumps(
            {"id": dec_id, "path": str(path.relative_to(root)), "written": True},
            ensure_ascii=False,
        ))
        return 0
    except (DecisionError, Exception) as exc:  # noqa: BLE001 — surface as finding
        # Analytical-script contract: a bad input surfaces as a JSON finding on
        # stdout + exit 0, never a bare traceback.
        print(json.dumps(
            {"error": "invalid_input", "message": str(exc), "written": False},
            ensure_ascii=False,
        ))
        return 0


if __name__ == "__main__":
    sys.exit(main())
