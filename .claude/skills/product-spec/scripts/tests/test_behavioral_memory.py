"""Tests for the behavioral-memory stores (behavioral_memory.py).

Two NEW behavioral stores extend the memory layer:

  - **3D PO-style** (`docs/product/.memory/po-style.yaml`, committed): the product
    owner's voice — register, their own domain vocabulary, recurring asks, do/don't
    phrasing — kept **lang-keyed** (`en` / `vi`). Read at prose-generation time to
    shape OUTPUT wording; written when the PO corrects generated wording.
  - **3E LLM-self-correction** (`docs/product/.memory/self-corrections.json`,
    committed): a recurring slip + the operating principle it violated + a
    frequency/last-seen stamp + a corrective reminder, read as a pre-flight
    self-check before at-risk operations. It guards BEHAVIOR, not output voice.

The SCRIPT half (exercised here) owns the deterministic structural work: read /
write / shape-validate / lang-key resolution / frequency increment / the DRY guard.
The LLM half (not exercised here) observes the PO's voice and decides what to write.

DRY guard (the split): the pure shape-validator rejects a po-style entry that
copies a CLOSED-ENUM structural value (`scope` in/out/core-value, `moscow`,
`horizon`) — those are script-decidable and have authoritative homes elsewhere.
Persona-label copy detection is NOT in this validator (persona labels are open PO
free-text, not a closed enum, and PRODUCT.md is not passed in) — that is an
LLM-side check, documented in `behavioral-memory.md`, not asserted in pytest.

All writes go through the shared soft fence (`fs_guard`) so a store write can never
escape `docs/product/`.
"""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import behavioral_memory as bm  # noqa: E402
from fs_guard import FenceError  # noqa: E402


# ---------- Test 1: 3D po-style is lang-keyed ----------

def test_po_style_lang_keyed(tmp_path):
    """Voice observations are stored per-lang; reading `vi` never returns `en`
    voice (and vice versa). The PO's vocabulary in one language must not leak into
    the prose generated in the other."""
    bm.record_po_style(
        tmp_path, lang="en",
        vocabulary=["shopper", "store admin"],
        recurring_asks=["always include a one-line summary"],
        do=["use 'shopper' not 'customer'"],
    )
    bm.record_po_style(
        tmp_path, lang="vi",
        vocabulary=["người mua"],
        register="thân thiện nhưng ngắn gọn",
    )

    en = bm.load_po_style(tmp_path, lang="en")
    vi = bm.load_po_style(tmp_path, lang="vi")

    assert "shopper" in en["vocabulary"]
    assert "store admin" in en["vocabulary"]
    # The vi read must NOT surface any en-only vocabulary.
    assert "shopper" not in vi["vocabulary"]
    assert "người mua" in vi["vocabulary"]
    # And the en read must not surface vi-only voice.
    assert vi["register"] == "thân thiện nhưng ngắn gọn"
    assert en.get("register") in (None, "")

    # A lang with no observations resolves to an empty (not crashing) shape.
    none_yet = bm.load_po_style(tmp_path, lang="en")
    assert isinstance(none_yet["vocabulary"], list)


# ---------- Test 2: 3D shape validation ----------

def test_po_style_shape_validate(tmp_path):
    """A malformed po-style entry is rejected before any write; a well-formed one
    is accepted and round-trips."""
    # Bad lang (not a closed-enum value) → rejected.
    with pytest.raises(bm.BehavioralError):
        bm.record_po_style(tmp_path, lang="fr", vocabulary=["x"])

    # A non-list vocabulary → rejected (shape is fixed).
    with pytest.raises(bm.BehavioralError):
        bm.record_po_style(tmp_path, lang="en", vocabulary="shopper")

    # do/dont must be lists too.
    with pytest.raises(bm.BehavioralError):
        bm.record_po_style(tmp_path, lang="en", do="be concise")

    # Well-formed → accepted, written under the fence, and reloadable.
    out = bm.record_po_style(
        tmp_path, lang="en",
        vocabulary=["shopper"], recurring_asks=["one-line summary"],
        do=["use 'shopper'"], dont=["no jargon like churn"],
        register="warm but concise",
    )
    assert out.is_relative_to(tmp_path / "docs" / "product" / ".memory")
    reloaded = bm.load_po_style(tmp_path, lang="en")
    assert reloaded["register"] == "warm but concise"
    assert reloaded["dont"] == ["no jargon like churn"]


# ---------- Test 3: 3E self-correction append + frequency ----------

def test_self_correction_append(tmp_path, monkeypatch):
    """A slip entry is appended; a repeat of the SAME slip increments its
    frequency and refreshes last_seen rather than creating a duplicate row.

    `_now` is second-granular, so two writes in the same wall-clock second would
    make a `last_seen` comparison trivially true. Pin `_now` to two explicit,
    distinct stamps (older → newer) so the refresh is proven by a STRICT inequality,
    not merely satisfied by chance."""
    older = "2026-01-01T00:00:00+00:00"
    newer = "2026-01-01T00:00:05+00:00"
    monkeypatch.setattr(bm, "_now", lambda: older)
    p1 = bm.record_self_correction(
        tmp_path, slip="wrote code into a story body",
        violated_rule="script_vs_llm_split",
        reminder="redirect code asks to stories + AC",
    )
    assert p1.is_relative_to(tmp_path / "docs" / "product" / ".memory")
    data = json.loads(p1.read_text(encoding="utf-8"))
    rows = data["corrections"]
    assert len(rows) == 1
    assert rows[0]["frequency"] == 1
    first_seen = rows[0]["last_seen"]
    assert first_seen == older

    # Repeat the SAME slip at a strictly later time → frequency increments, no new
    # row, and last_seen is refreshed forward.
    monkeypatch.setattr(bm, "_now", lambda: newer)
    bm.record_self_correction(
        tmp_path, slip="wrote code into a story body",
        violated_rule="script_vs_llm_split",
        reminder="redirect code asks to stories + AC",
    )
    data = json.loads(p1.read_text(encoding="utf-8"))
    rows = data["corrections"]
    assert len(rows) == 1
    assert rows[0]["frequency"] == 2
    assert rows[0]["last_seen"] > first_seen

    # A DIFFERENT slip → a second row.
    bm.record_self_correction(
        tmp_path, slip="auto-flipped an approved artifact",
        violated_rule="no_silent_reversal",
        reminder="surface keep/change/hybrid; never auto-flip",
    )
    data = json.loads(p1.read_text(encoding="utf-8"))
    assert len(data["corrections"]) == 2


# ---------- Test 4: 3E entry must cite a violated rule ----------

def test_self_correction_cites_rule(tmp_path):
    """Every self-correction entry MUST name the operating principle it violated
    (one of the five). A missing or unknown rule is rejected — an un-anchored slip
    has no corrective lesson."""
    # Missing rule → rejected.
    with pytest.raises(bm.BehavioralError):
        bm.record_self_correction(
            tmp_path, slip="some slip", violated_rule="", reminder="fix it")

    # Unknown rule (not one of the five principles) → rejected.
    with pytest.raises(bm.BehavioralError):
        bm.record_self_correction(
            tmp_path, slip="some slip", violated_rule="made_up_rule",
            reminder="fix it")

    # Each of the five principles is an accepted citation.
    for rule in bm.VIOLATED_RULES:
        bm.record_self_correction(
            tmp_path, slip=f"slip for {rule}", violated_rule=rule,
            reminder="reminder")
    data = json.loads(
        (tmp_path / "docs" / "product" / ".memory" / "self-corrections.json")
        .read_text(encoding="utf-8"))
    cited = {r["violated_rule"] for r in data["corrections"]}
    assert cited == set(bm.VIOLATED_RULES)


# ---------- Test 5: DRY guard — reject closed-enum structural copies ----------

def test_behavioral_no_structural_fact(tmp_path):
    """The script-side DRY guard rejects a po-style entry that copies a CLOSED-ENUM
    structural value into the PO's vocabulary / do / dont — those facts already have
    an authoritative home (frontmatter), and behavioral memory shapes PHRASING only,
    never re-homes structure.

    The closed enums are script-decidable: `scope` (in/out/core-value), `moscow`
    (must/should/could/wont), `horizon` (now/next/later). Persona-label copy
    detection is deliberately OUT of this pure validator (open free-text, not a
    closed enum) → it is an LLM-side check per the Script-vs-LLM split."""
    # A scope enum value smuggled into vocabulary → rejected.
    with pytest.raises(bm.BehavioralError):
        bm.record_po_style(tmp_path, lang="en", vocabulary=["core-value"])
    # A moscow enum value in `do` → rejected.
    with pytest.raises(bm.BehavioralError):
        bm.record_po_style(tmp_path, lang="en", do=["must"])
    # A horizon enum value in `dont` → rejected.
    with pytest.raises(bm.BehavioralError):
        bm.record_po_style(tmp_path, lang="en", dont=["later"])

    # A PO term that merely CONTAINS an enum word as a substring is fine — the guard
    # rejects exact closed-enum copies, not natural phrases that use the word.
    out = bm.record_po_style(
        tmp_path, lang="en",
        vocabulary=["core shopper journey"],  # 'core' substring, not the enum value
        do=["lead with the value the shopper gets"])
    assert out.exists()
    reloaded = bm.load_po_style(tmp_path, lang="en")
    assert "core shopper journey" in reloaded["vocabulary"]


# ---------- Test 6: writers fence the store path before writing ----------

def test_po_style_write_honours_fence(tmp_path, monkeypatch):
    """The po-style writer resolves its target through the soft fence BEFORE
    writing. If the resolved store path would land outside docs/product/ (here:
    a tampered path helper), the write raises FenceError and nothing is written —
    exercising the writer's fence wiring, not the guard in isolation."""
    escape = tmp_path / "escape.yaml"
    monkeypatch.setattr(bm, "_po_style_path", lambda root: escape)
    with pytest.raises(FenceError):
        bm.record_po_style(tmp_path, lang="en", vocabulary=["shopper"])
    assert not escape.exists()


def test_self_correction_write_honours_fence(tmp_path, monkeypatch):
    """The self-correction writer fence-checks its target before writing; a path
    that resolves outside docs/product/ raises FenceError and writes nothing."""
    escape = tmp_path / "escape.json"
    monkeypatch.setattr(bm, "_self_corrections_path", lambda root: escape)
    with pytest.raises(FenceError):
        bm.record_self_correction(
            tmp_path, slip="some slip", violated_rule="dry", reminder="fix it")
    assert not escape.exists()
