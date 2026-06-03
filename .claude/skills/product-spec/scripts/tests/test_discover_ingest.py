"""test_discover_ingest — E2 `--discover` read-fence + filter contracts (Security F3).

Covers: traversal/symlink rejected; directory input walked with bounded recursion (depth + count
cap); dotfile (`.env`) skipped even inside a dir; non-`.md/.txt` rejected; oversize rejected; ingest
fixture transcripts → candidate draft; and the GATE: NO persona committed without a confirm step
(the scaffold's candidate buckets are EMPTY by design).
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import ingest_raw_inputs as iri  # noqa: E402


def _root(tmp_path: Path) -> Path:
    (tmp_path / "inputs").mkdir(parents=True)
    return tmp_path


def test_traversal_rejected(tmp_path):
    root = _root(tmp_path)
    (tmp_path.parent / "secret.md").write_text("secret", encoding="utf-8")
    res = iri.resolve_inputs(["../secret.md"], root)
    assert res["accepted"] == []
    assert any("outside project root" in r["reason"] for r in res["rejected"])


def test_symlink_escape_rejected(tmp_path):
    root = _root(tmp_path)
    outside = tmp_path.parent / "outside_dir"
    outside.mkdir(exist_ok=True)
    (outside / "leak.md").write_text("secret", encoding="utf-8")
    link = root / "inputs" / "link.md"
    link.symlink_to(outside / "leak.md")
    res = iri.resolve_inputs(["inputs/link.md"], root)
    assert res["accepted"] == []


def test_walk_symlinked_file_escape_rejected(tmp_path):
    # CRITICAL regression: a symlinked .md FILE *inside a walked directory* pointing outside root
    # must be rejected, not read (the directory-walk fence, not just the top-level path).
    root = _root(tmp_path)
    outside = tmp_path.parent / "outside_secrets"
    outside.mkdir(exist_ok=True)
    (outside / "creds.txt").write_text("TOP SECRET", encoding="utf-8")
    (root / "inputs" / "leak.md").symlink_to(outside / "creds.txt")
    res = iri.resolve_inputs(["inputs"], root)  # walk the dir, not the symlink directly
    assert all("creds" not in a and "leak" not in a for a in res["accepted"]), res["accepted"]
    assert any("symlink/escape" in r["reason"] for r in res["rejected"])
    # And the scaffold must not read its contents.
    scaffold = iri.draft_scaffold(res, root)
    assert all("TOP SECRET" not in f.get("text", "") for f in scaffold["files"])


def test_walk_symlinked_dir_escape_rejected(tmp_path):
    # A symlinked DIRECTORY inside a walked directory pointing outside root must not be descended.
    root = _root(tmp_path)
    outside = tmp_path.parent / "outside_dir2"
    outside.mkdir(exist_ok=True)
    (outside / "leak.md").write_text("ESCAPED CONTENT", encoding="utf-8")
    (root / "inputs" / "subdir").symlink_to(outside, target_is_directory=True)
    res = iri.resolve_inputs(["inputs"], root)
    assert all("leak.md" not in a for a in res["accepted"])
    assert any("symlink/escape" in r["reason"] for r in res["rejected"])
    scaffold = iri.draft_scaffold(res, root)
    assert all("ESCAPED CONTENT" not in f.get("text", "") for f in scaffold["files"])


def test_non_md_txt_rejected(tmp_path):
    root = _root(tmp_path)
    (root / "inputs" / "a.pdf").write_text("x", encoding="utf-8")
    res = iri.resolve_inputs(["inputs/a.pdf"], root)
    assert res["accepted"] == []
    assert any("extension" in r["reason"] for r in res["rejected"])


def test_dotfile_excluded_even_inside_dir(tmp_path):
    root = _root(tmp_path)
    (root / "inputs" / ".env").write_text("SECRET=1", encoding="utf-8")
    (root / "inputs" / "notes.md").write_text("real transcript", encoding="utf-8")
    res = iri.resolve_inputs(["inputs"], root)
    assert all(".env" not in a for a in res["accepted"])
    assert any("notes.md" in a for a in res["accepted"])
    assert any(".env" in r["path"] for r in res["rejected"])


def test_oversize_rejected(tmp_path):
    root = _root(tmp_path)
    big = root / "inputs" / "big.txt"
    big.write_text("x" * 5000, encoding="utf-8")
    res = iri.resolve_inputs(["inputs/big.txt"], root, max_bytes=1000)
    assert res["accepted"] == []
    assert any("size cap" in r["reason"] for r in res["rejected"])


def test_directory_bounded_recursion_depth(tmp_path):
    root = _root(tmp_path)
    deep = root / "inputs" / "a" / "b" / "c" / "d" / "e"
    deep.mkdir(parents=True)
    (deep / "deep.md").write_text("too deep", encoding="utf-8")
    (root / "inputs" / "top.md").write_text("ok", encoding="utf-8")
    res = iri.resolve_inputs(["inputs"], root, max_depth=2)
    assert any("top.md" in a for a in res["accepted"])
    assert all("deep.md" not in a for a in res["accepted"])  # beyond depth cap
    assert res["truncated"] is True


def test_directory_bounded_recursion_file_count(tmp_path):
    root = _root(tmp_path)
    for i in range(10):
        (root / "inputs" / f"f{i}.md").write_text("x", encoding="utf-8")
    res = iri.resolve_inputs(["inputs"], root, max_files=3)
    assert len(res["accepted"]) == 3
    assert res["truncated"] is True


def test_scaffold_reads_transcripts_and_keeps_candidates_empty(tmp_path):
    # GATE: a transcript ingests into raw text but the candidate buckets stay EMPTY —
    # nothing is committed without the interview confirming each field.
    root = _root(tmp_path)
    (root / "inputs" / "interview.md").write_text(
        "User says: I can never find a tailor I trust near me.", encoding="utf-8")
    res = iri.resolve_inputs(["inputs/interview.md"], root)
    scaffold = iri.draft_scaffold(res, root)
    assert scaffold["files"] and "tailor" in scaffold["files"][0]["text"]
    assert scaffold["candidates"] == {"personas": [], "problems": [], "jtbd": []}


def test_nonexistent_path_rejected(tmp_path):
    root = _root(tmp_path)
    res = iri.resolve_inputs(["inputs/nope.md"], root)
    assert res["accepted"] == []
    assert any("does not exist" in r["reason"] for r in res["rejected"])
