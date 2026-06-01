"""Tests for the Decision Register (decision_register.py) and the PO-preferences
helper.

The Decision Register is the authoritative, append-only home for explicit PO
rulings (`DEC-<n>`). The SCRIPT half owns the deterministic structural work —
allocate the next monotonic ID, validate the `^DEC-\\d+$` grammar + the record
shape, append without overwriting prior records, and list the active ones. The
LLM half (not exercised here) supplies the human rationale prose.

`docs/product/decisions.md` is a visible, committed file written through the
shared soft-fence (`fs_guard`) so a register write can never escape the spec
boundary.

The preferences helper resolves `docs/product/.memory/preferences.yaml` defaults:
a missing key (or a missing file) falls back to a hard-coded default and NEVER
crashes — frontmatter `lang` still wins at artifact level (these are defaults).
"""

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from decision_register import (  # noqa: E402
    alloc_id,
    append_decision,
    list_active,
    parse_decisions,
    DECISION_ID_RE,
    DecisionError,
)
from fs_guard import FenceError  # noqa: E402
import preferences  # noqa: E402


def _decisions_path(root: Path) -> Path:
    return root / "docs" / "product" / "decisions.md"


def _seed(root: Path, *records: str) -> Path:
    """Write a decisions.md with the given record blocks already present."""
    p = _decisions_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    header = "# Decision Register\n\n"
    p.write_text(header + "\n".join(records) + ("\n" if records else ""), encoding="utf-8")
    return p


def _record(dec_id: str, status: str = "active", supersedes: str = "") -> str:
    sup = f"supersedes: {supersedes}\n" if supersedes else ""
    return (
        "---\n"
        f"id: {dec_id}\n"
        f"status: {status}\n"
        "date: 2026-06-01\n"
        f"{sup}"
        "---\n"
        f"## {dec_id} — sample ruling\n\n"
        "Rationale prose here.\n"
    )


# ---------- alloc_id ----------

def test_alloc_id_first(tmp_path):
    # Absent decisions.md → DEC-1.
    assert alloc_id(tmp_path) == "DEC-1"
    # Empty decisions.md (header only, no records) → still DEC-1.
    _seed(tmp_path)
    assert alloc_id(tmp_path) == "DEC-1"


def test_alloc_id_increments(tmp_path):
    # With DEC-1, DEC-2 present → next is DEC-3 (max + 1).
    _seed(tmp_path, _record("DEC-1"), _record("DEC-2"))
    assert alloc_id(tmp_path) == "DEC-3"


def test_alloc_id_ignores_superseded(tmp_path):
    # Numbering is monotonic regardless of status: a superseded DEC-2 still
    # counts toward the max, so the next id is DEC-3 (no reuse of 2).
    _seed(tmp_path, _record("DEC-1", status="active"),
          _record("DEC-2", status="superseded", supersedes="DEC-1"))
    assert alloc_id(tmp_path) == "DEC-3"


def test_alloc_id_gap_uses_max_plus_one(tmp_path):
    # A non-contiguous register (DEC-1, DEC-5) allocates max+1 = DEC-6, never
    # backfilling the 2..4 gap (append-only lineage, no id reuse).
    _seed(tmp_path, _record("DEC-1"), _record("DEC-5"))
    assert alloc_id(tmp_path) == "DEC-6"


# ---------- append_decision ----------

def test_append_validates_grammar(tmp_path):
    # A malformed id is rejected before any write.
    _seed(tmp_path)
    with pytest.raises(DecisionError):
        append_decision(tmp_path, dec_id="DEC-abc", title="bad", rationale="x")
    with pytest.raises(DecisionError):
        append_decision(tmp_path, dec_id="DECISION-1", title="bad", rationale="x")


def test_append_accepts_wellformed_and_is_append_only(tmp_path):
    _seed(tmp_path, _record("DEC-1"))
    before = _decisions_path(tmp_path).read_text(encoding="utf-8")
    out = append_decision(
        tmp_path, dec_id="DEC-2", title="use SePay for VietQR",
        rationale="cheapest QR rail for the target market",
    )
    assert out.exists()
    after = out.read_text(encoding="utf-8")
    # Append-only: the prior DEC-1 record survives verbatim, untouched.
    assert before.rstrip() in after
    # The new record is present and parseable.
    recs = parse_decisions(tmp_path)
    ids = [r["id"] for r in recs]
    assert ids == ["DEC-1", "DEC-2"]
    assert recs[1]["status"] == "active"


def test_append_rejects_duplicate_id(tmp_path):
    # The register is append-only; re-appending an existing id would create a
    # duplicate lineage entry — reject it.
    _seed(tmp_path, _record("DEC-1"))
    with pytest.raises(DecisionError):
        append_decision(tmp_path, dec_id="DEC-1", title="dup", rationale="x")


def test_append_supersede_records_link(tmp_path):
    _seed(tmp_path, _record("DEC-1"))
    append_decision(
        tmp_path, dec_id="DEC-2", title="switch rail", rationale="y",
        supersedes="DEC-1",
    )
    recs = parse_decisions(tmp_path)
    by_id = {r["id"]: r for r in recs}
    assert by_id["DEC-2"]["supersedes"] == "DEC-1"


def test_supersede_preserves_blank_line_before_heading(tmp_path):
    # The in-place status flip must round-trip the record's formatting: the blank
    # line between the closing `---` fence and the `## DEC-n` heading survives, so
    # a committed file written in the canonical template format (fence -> blank
    # line -> heading) does not churn byte-wise on every supersede.
    import decision_register as dr

    # Seed via the real writer so the on-disk record uses the canonical
    # template formatting, then flip it in place.
    append_decision(tmp_path, dec_id="DEC-1", title="first", rationale="z")
    text_before = _decisions_path(tmp_path).read_text(encoding="utf-8")
    assert "---\n\n## DEC-1" in text_before  # canonical format precondition

    flipped = dr._supersede_in_place(tmp_path, "DEC-1")
    assert flipped
    text = _decisions_path(tmp_path).read_text(encoding="utf-8")
    assert "status: superseded" in text
    # fence -> blank line -> heading preserved (not collapsed to ---\n## DEC-1).
    assert "---\n\n## DEC-1" in text
    assert "---\n## DEC-1" not in text


def test_alloc_id_counts_corrupt_but_id_bearing_block(tmp_path):
    # A block with a parseable `id: DEC-5` but otherwise corrupt YAML is
    # fail-soft-skipped by parse_decisions, yet its id is still claimed. alloc_id
    # scans raw text so it counts DEC-5 → next is DEC-6, never reusing 5 (a later
    # repair of that block must not collide).
    corrupt = (
        "---\n"
        "id: DEC-5\n"
        "status: active\n"
        "affects: [unterminated\n"  # invalid YAML → parse_decisions skips it
        "---\n"
        "## DEC-5 — corrupt block\n\n"
        "Rationale.\n"
    )
    _seed(tmp_path, _record("DEC-1"), corrupt)
    # Sanity: parse_decisions fail-soft-skips the corrupt block.
    assert sorted(r["id"] for r in parse_decisions(tmp_path)) == ["DEC-1"]
    # But alloc must still reserve past DEC-5.
    assert alloc_id(tmp_path) == "DEC-6"


def test_supersede_then_invalid_append_leaves_register_untouched(tmp_path, monkeypatch):
    # Regression: an invalid --append --supersedes must NOT retire the prior
    # ruling. Validation (in append_decision) runs BEFORE the in-place flip, so a
    # rejected append (here an empty --rationale) leaves DEC-1 still active and
    # decisions.md byte-identical — no zero-active + phantom-retired register.
    import decision_register as dr

    seeded = _seed(tmp_path, _record("DEC-1"))
    before = seeded.read_text(encoding="utf-8")

    argv = [
        "decision_register.py", "--root", str(tmp_path), "--append",
        "--id", "DEC-2", "--title", "second", "--supersedes", "DEC-1",
        # --rationale deliberately omitted → invalid input
    ]
    monkeypatch.setattr(sys, "argv", argv)
    rc = dr.main()

    assert rc == 0  # analytical-script contract: surface as JSON finding, not crash
    after = seeded.read_text(encoding="utf-8")
    assert after == before  # file untouched on a rejected append
    active_ids = sorted(r["id"] for r in list_active(tmp_path))
    assert active_ids == ["DEC-1"]  # DEC-1 still active, DEC-2 not written


def test_append_honours_soft_fence(tmp_path):
    # The write resolves through fs_guard against the project root; a root whose
    # decisions target would escape docs/product is refused. We assert the write
    # lands strictly under docs/product/ for a normal root.
    out = append_decision(
        tmp_path, dec_id="DEC-1", title="first", rationale="z",
    )
    assert out.is_relative_to(tmp_path / "docs" / "product")


def test_append_fence_blocks_escape(tmp_path, monkeypatch):
    # Negative path: if the register's target resolves outside docs/product/
    # (here forced via a tampered path helper), the write is refused by the soft
    # fence BEFORE any bytes touch disk — never silently written out-of-tree.
    import decision_register as dr

    escape = tmp_path / "escape" / "decisions.md"
    monkeypatch.setattr(dr, "_decisions_path", lambda root: escape)
    with pytest.raises(FenceError):
        append_decision(tmp_path, dec_id="DEC-1", title="first", rationale="z")
    assert not escape.exists()


# ---------- list_active ----------

def test_list_active_returns_only_active(tmp_path):
    _seed(
        tmp_path,
        _record("DEC-1", status="active"),
        _record("DEC-2", status="superseded", supersedes="DEC-1"),
        _record("DEC-3", status="active"),
    )
    active = list_active(tmp_path)
    ids = sorted(r["id"] for r in active)
    assert ids == ["DEC-1", "DEC-3"]


def test_list_active_empty_register(tmp_path):
    # No file → empty list, no crash.
    assert list_active(tmp_path) == []
    _seed(tmp_path)
    assert list_active(tmp_path) == []


def test_decision_id_regex():
    assert DECISION_ID_RE.match("DEC-1")
    assert DECISION_ID_RE.match("DEC-42")
    assert not DECISION_ID_RE.match("DEC-")
    assert not DECISION_ID_RE.match("DEC-1a")
    assert not DECISION_ID_RE.match("dec-1")
    assert not DECISION_ID_RE.match("DECISION-1")


# ---------- preferences ----------

def test_preferences_missing_key_default(tmp_path):
    # An absent preferences.yaml → every key resolves to its documented default,
    # never a crash.
    prefs = preferences.load(tmp_path)
    assert prefs["lang"] == preferences.DEFAULTS["lang"]
    assert prefs["detail_level"] == preferences.DEFAULTS["detail_level"]
    assert prefs["prioritization"] == preferences.DEFAULTS["prioritization"]
    assert prefs["dismissed_reminders"] == []


def test_preferences_partial_file_fills_gaps(tmp_path):
    # A file that sets only `lang` leaves the other keys on their defaults.
    mem = tmp_path / "docs" / "product" / ".memory"
    mem.mkdir(parents=True)
    (mem / "preferences.yaml").write_text("lang: vi\n", encoding="utf-8")
    prefs = preferences.load(tmp_path)
    assert prefs["lang"] == "vi"
    assert prefs["detail_level"] == preferences.DEFAULTS["detail_level"]


def test_preferences_rejects_unknown_enum_value(tmp_path):
    # A closed-enum key with an out-of-range value falls back to the default
    # (defensive: a hand-edited typo must not poison the interview flow).
    mem = tmp_path / "docs" / "product" / ".memory"
    mem.mkdir(parents=True)
    (mem / "preferences.yaml").write_text("detail_level: verbose-extreme\n", encoding="utf-8")
    prefs = preferences.load(tmp_path)
    assert prefs["detail_level"] == preferences.DEFAULTS["detail_level"]


def test_preferences_malformed_yaml_returns_defaults(tmp_path):
    # A corrupt preferences.yaml never crashes the caller — it yields defaults.
    mem = tmp_path / "docs" / "product" / ".memory"
    mem.mkdir(parents=True)
    (mem / "preferences.yaml").write_text("lang: [unterminated\n", encoding="utf-8")
    prefs = preferences.load(tmp_path)
    assert prefs == preferences.DEFAULTS


def test_preferences_save_roundtrip_under_fence(tmp_path):
    out = preferences.save(tmp_path, {"lang": "vi", "detail_level": "concise"})
    assert out.is_relative_to(tmp_path / "docs" / "product" / ".memory")
    reloaded = preferences.load(tmp_path)
    assert reloaded["lang"] == "vi"
    assert reloaded["detail_level"] == "concise"


def test_preferences_save_rejects_unknown_enum(tmp_path):
    # save() validates before writing — an unknown enum is refused, not silently
    # persisted (keeps the file canonical for the read path).
    with pytest.raises(preferences.PreferenceError):
        preferences.save(tmp_path, {"detail_level": "nonsense"})
