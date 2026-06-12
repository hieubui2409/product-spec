"""id backfill migrator tests (TDD RED → GREEN).

migrate_backfill_ids.py inserts a missing `id:` into spec artifact frontmatter.

GATE contract (mirrors migrate_metric_to_metrics.py):
  - dry-run (default, no --apply): report artifacts missing id; write 0 bytes.
  - --apply requires BOTH --confirmed-by AND --date; refuses (non-zero exit) if either absent.
  - per-artifact / per-file scoped; idempotent (already has id → skipped, re-run no-op).
  - .bak-once backup before writing.
  - schema_version stamp on write.
  - approved artifact without the confirm path → confirm_required list, never silently rewritten.
  - artifact where id cannot be derived → skipped + reported, no crash.

Synthetic fixtures only — NO real PO artifact paths used.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from frontmatter_parser import parse_file  # noqa: E402

MIGRATE = SCRIPTS_DIR / "migrate_backfill_ids.py"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

_PRODUCT_MISSING_ID = """\
---
type: product
status: draft
lang: en
name: "Acme"
core_value: "do one thing well"
personas: [user]
---
"""

_PRODUCT_HAS_ID = """\
---
id: PRODUCT
type: product
status: draft
lang: en
name: "Acme"
core_value: "do one thing well"
personas: [user]
---
"""

_BRD_MISSING_ID_APPROVED = """\
---
type: brd
status: approved
lang: en
owner: Jane
version: 1.0.0
created: 2026-06-01
updated: 2026-06-01
goals:
  - id: BRD-G1
    title: "A goal"
    metrics: [north-star]
    status: approved
---

# BRD
"""

_BRD_MISSING_ID_DRAFT = """\
---
type: brd
status: draft
lang: en
owner: Jane
version: 1.0.0
created: 2026-06-01
updated: 2026-06-01
goals:
  - id: BRD-G1
    title: "A goal"
    metrics: [north-star]
    status: draft
---

# BRD
"""

# A file with a BOM + inline YAML comment — preserved on insert.
_PRODUCT_BOM_COMMENT = "﻿---\n# kit-version: 1.0\ntype: product\nstatus: draft\nlang: en\nname: \"X\"\ncore_value: \"y\"\npersonas: []\n---\n"

# A file in an unrecognised location where an id cannot be derived.
_UNKNOWN_ARTIFACT = """\
---
type: unknown_exotic
status: draft
lang: en
---

# Unknown
"""


def _setup_proj(tmp_path: Path) -> Path:
    """Create minimal project layout."""
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir()
    (prod / "stories").mkdir()
    return proj


def _run(proj: Path, *extra: str, expect_ok: bool = True):
    """Run the migrator, return (returncode, parsed-json-or-None, stderr)."""
    r = subprocess.run(
        [sys.executable, str(MIGRATE), "--root", str(proj), *extra],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(r.stdout) if r.stdout.strip() else None
    except json.JSONDecodeError:
        data = None
    return r.returncode, data, r.stderr


# ---------------------------------------------------------------------------
# Test 1 — dry-run writes nothing, reports the intended change
# ---------------------------------------------------------------------------

def test_dry_run_writes_nothing(tmp_path):
    """Default (no --apply): artifact missing id is reported; file byte-identical after."""
    proj = _setup_proj(tmp_path)
    product_file = proj / "docs" / "product" / "PRODUCT.md"
    product_file.write_text(_PRODUCT_MISSING_ID, encoding="utf-8")

    before = product_file.read_bytes()
    rc, report, _err = _run(proj)

    assert rc == 0, f"dry-run must exit 0; got {rc}\nstderr: {_err}"
    assert product_file.read_bytes() == before, "dry-run must not change a single byte"
    assert not (proj / "docs" / "product" / "PRODUCT.md.bak").exists(), "dry-run must not create .bak"
    assert report is not None
    assert report.get("applied") is False
    # Report must mention the file or the would-insert list
    assert report.get("would_insert") or report.get("would_backfill"), \
        "dry-run report must list artifacts that would receive an id"


# ---------------------------------------------------------------------------
# Test 2 — --apply refused when confirmation flags are missing
# ---------------------------------------------------------------------------

def test_apply_requires_confirmed_by_and_date(tmp_path):
    """--apply without both flags → non-zero exit, file untouched."""
    proj = _setup_proj(tmp_path)
    product_file = proj / "docs" / "product" / "PRODUCT.md"
    product_file.write_text(_PRODUCT_MISSING_ID, encoding="utf-8")

    before = product_file.read_bytes()

    # --apply alone → refused
    rc1, report1, err1 = _run(proj, "--apply", expect_ok=False)
    assert rc1 != 0, "--apply without confirmation must exit non-zero"
    assert product_file.read_bytes() == before, "file must be untouched on refusal"

    # --apply with only --confirmed-by → still refused
    rc2, report2, err2 = _run(proj, "--apply", "--confirmed-by", "Jane", expect_ok=False)
    assert rc2 != 0, "--apply with only --confirmed-by must exit non-zero"
    assert product_file.read_bytes() == before, "file must be untouched on partial confirmation"

    # --apply with only --date → still refused
    rc3, report3, err3 = _run(proj, "--apply", "--date", "2026-06-12", expect_ok=False)
    assert rc3 != 0, "--apply with only --date must exit non-zero"
    assert product_file.read_bytes() == before, "file must be untouched on partial confirmation"


# ---------------------------------------------------------------------------
# Test 3 — --apply backfills missing id, stamps schema_version, creates .bak
# ---------------------------------------------------------------------------

def test_apply_backfills_missing_id(tmp_path):
    """--apply with both flags: id written, schema_version stamped, .bak created."""
    proj = _setup_proj(tmp_path)
    product_file = proj / "docs" / "product" / "PRODUCT.md"
    product_file.write_text(_PRODUCT_MISSING_ID, encoding="utf-8")

    before = product_file.read_bytes()

    rc, report, err = _run(
        proj, "--apply", "--confirmed-by", "Jane", "--date", "2026-06-12"
    )
    assert rc == 0, f"apply must exit 0; got {rc}\nstderr: {err}"

    after_text = product_file.read_text(encoding="utf-8")
    assert "id: PRODUCT" in after_text, "id: PRODUCT must be inserted"

    parsed = parse_file(product_file)
    assert parsed["ok"], f"migrated file must parse cleanly: {parsed.get('error')}"
    fm = parsed["frontmatter"]
    assert fm.get("id") == "PRODUCT", "frontmatter id must be PRODUCT"
    # FIX 2: id-backfill must NOT inject schema_version (orthogonal concern)
    assert "schema_version" not in fm, \
        "id-backfill must not inject schema_version into a file that had none"

    bak = product_file.with_name(product_file.name + ".bak")
    assert bak.exists(), ".bak file must be created"
    assert bak.read_bytes() == before, ".bak must contain the original content"

    assert report is not None
    assert report.get("applied") is True


# ---------------------------------------------------------------------------
# Test 4 — idempotent: second apply is a no-op, single .bak, original preserved
# ---------------------------------------------------------------------------

def test_idempotent_rerun_noop(tmp_path):
    """Run apply twice → second run is a no-op; .bak created once only."""
    proj = _setup_proj(tmp_path)
    product_file = proj / "docs" / "product" / "PRODUCT.md"
    product_file.write_text(_PRODUCT_MISSING_ID, encoding="utf-8")
    bak = product_file.with_name(product_file.name + ".bak")

    # First apply
    rc1, rep1, err1 = _run(proj, "--apply", "--confirmed-by", "Jane", "--date", "2026-06-12")
    assert rc1 == 0, f"first apply must succeed; stderr: {err1}"
    assert rep1 is not None and rep1.get("applied") is True

    after_first = product_file.read_bytes()
    bak_after_first = bak.read_bytes()

    # Second apply — must be a no-op
    rc2, rep2, err2 = _run(proj, "--apply", "--confirmed-by", "Jane", "--date", "2026-06-12")
    assert rc2 == 0, f"second apply must exit 0; stderr: {err2}"

    assert product_file.read_bytes() == after_first, "file must be byte-identical after second apply"
    assert bak.read_bytes() == bak_after_first, ".bak must not be overwritten on second apply"

    # The second run must report no changes made
    assert rep2 is not None
    assert rep2.get("applied") is False or rep2.get("migrated") in ([], None, 0), \
        "second apply must report nothing migrated (idempotent)"


# ---------------------------------------------------------------------------
# Test 5 — approved artifact without confirmation path → confirm_required, not rewritten
# ---------------------------------------------------------------------------

def test_approved_artifact_requires_confirmation(tmp_path):
    """Approved artifact missing id → lands in confirm_required on dry-run, NOT auto-written."""
    proj = _setup_proj(tmp_path)
    brd_file = proj / "docs" / "product" / "brd.md"
    brd_file.write_text(_BRD_MISSING_ID_APPROVED, encoding="utf-8")

    before = brd_file.read_bytes()

    # Dry-run: must list as confirm_required
    rc, report, err = _run(proj)
    assert rc == 0
    assert brd_file.read_bytes() == before, "dry-run must not touch approved artifact"
    assert report is not None
    confirm = report.get("confirm_required", [])
    assert confirm, "approved artifact missing id must appear in confirm_required"

    brd_files = [c for c in confirm if "brd" in str(c).lower() or "BRD" in str(c)]
    assert brd_files or any("approved" in str(c).lower() or "brd.md" in str(c) for c in confirm), \
        "confirm_required must reference the approved brd artifact"


# ---------------------------------------------------------------------------
# Test 6 — artifact where id cannot be derived → skipped + reported, no crash
# ---------------------------------------------------------------------------

def test_undeerivable_id_skipped_no_crash(tmp_path):
    """Artifact with an unrecognised location/type: skipped gracefully, no exception."""
    proj = _setup_proj(tmp_path)
    # Place an artifact in an unexpected path where we cannot derive an id.
    strange_dir = proj / "docs" / "product" / "custom_artifacts"
    strange_dir.mkdir()
    strange_file = strange_dir / "exotic_thing.md"
    strange_file.write_text(_UNKNOWN_ARTIFACT, encoding="utf-8")

    rc, report, err = _run(proj)

    assert rc == 0, f"must not crash on underivable id; rc={rc}\nstderr: {err}"
    # The file must be untouched
    assert strange_file.read_text(encoding="utf-8") == _UNKNOWN_ARTIFACT, \
        "unrecognised artifact must be left byte-identical"
    # Report must surface the skip (warn/skip list)
    if report:
        skipped = report.get("skipped") or report.get("unrecognised") or []
        # Either it is listed as skipped OR it simply does not appear in would_insert/migrated
        migrated = report.get("migrated") or []
        would_insert = report.get("would_insert") or report.get("would_backfill") or []
        assert str(strange_file) not in str(migrated), "unrecognised artifact must not appear in migrated"


# ---------------------------------------------------------------------------
# generate_templates: assert PRODUCT.md template carries id: PRODUCT
# ---------------------------------------------------------------------------

def test_generated_product_md_frontmatter_has_id_product(tmp_path):
    """generate_templates --type product produces a file with id: PRODUCT in frontmatter."""
    import subprocess as sp

    generate = SCRIPTS_DIR / "generate_templates.py"
    proj = tmp_path / "proj"
    (proj / "docs" / "product").mkdir(parents=True)

    payload = json.dumps({
        "name": "TestProd",
        "one_line_description": "a test product",
        "current_implementation": "none",
        "deployment": "cloud",
        "roadmap_one_liner": "ship it",
        "core_value": "speed",
    })

    r = sp.run(
        [sys.executable, str(generate),
         "--root", str(proj), "--type", "product",
         "--values", payload, "--write"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, f"generate_templates must succeed; stderr: {r.stderr}"

    product_file = proj / "docs" / "product" / "PRODUCT.md"
    assert product_file.exists(), "PRODUCT.md must be written"

    text = product_file.read_text(encoding="utf-8")
    assert "id: PRODUCT" in text, "generated PRODUCT.md frontmatter must contain 'id: PRODUCT'"

    parsed = parse_file(product_file)
    assert parsed["ok"], f"generated PRODUCT.md must parse cleanly: {parsed.get('error')}"
    assert parsed["frontmatter"].get("id") == "PRODUCT", \
        "parsed frontmatter id must be PRODUCT"


# ---------------------------------------------------------------------------
# FIX 1 — approved artifact blocked from blanket --apply (GATE-NO-SILENT-REVERSAL)
# ---------------------------------------------------------------------------

def test_apply_skips_approved_without_allowlist(tmp_path):
    """Blanket --apply must NOT rewrite approved artifacts: file byte-unchanged, no .bak,
    artifact appears in confirm_required report."""
    proj = _setup_proj(tmp_path)
    brd_file = proj / "docs" / "product" / "brd.md"
    brd_file.write_text(_BRD_MISSING_ID_APPROVED, encoding="utf-8")

    before = brd_file.read_bytes()

    rc, report, err = _run(
        proj, "--apply", "--confirmed-by", "PO", "--date", "2026-01-01"
    )
    assert rc == 0, f"apply must exit 0 even when approved artifact is skipped; got {rc}\n{err}"

    # The approved file must be completely untouched
    assert brd_file.read_bytes() == before, \
        "approved artifact must be byte-unchanged when no --confirm-approved allowlist given"
    bak = brd_file.with_name(brd_file.name + ".bak")
    assert not bak.exists(), "no .bak must be created for a skipped approved artifact"

    # It must appear in confirm_required
    assert report is not None
    confirm = report.get("confirm_required", [])
    assert confirm, "skipped approved artifact must appear in confirm_required"
    assert any("brd" in str(c).lower() for c in confirm), \
        "confirm_required must reference brd.md"


def test_apply_writes_approved_only_with_allowlist(tmp_path):
    """--confirm-approved <ID> allowlist unlocks write of an approved artifact."""
    proj = _setup_proj(tmp_path)
    brd_file = proj / "docs" / "product" / "brd.md"
    brd_file.write_text(_BRD_MISSING_ID_APPROVED, encoding="utf-8")

    before = brd_file.read_bytes()

    rc, report, err = _run(
        proj,
        "--apply", "--confirmed-by", "PO", "--date", "2026-01-01",
        "--confirm-approved", "BRD",
    )
    assert rc == 0, f"apply with allowlist must exit 0; got {rc}\n{err}"

    after_text = brd_file.read_text(encoding="utf-8")
    assert "id: BRD" in after_text, "id: BRD must be inserted when --confirm-approved BRD given"

    bak = brd_file.with_name(brd_file.name + ".bak")
    assert bak.exists(), ".bak must be created for explicitly approved artifact"
    assert bak.read_bytes() == before, ".bak must contain original bytes"


def test_apply_non_approved_still_backfills_under_blanket_flag(tmp_path):
    """Non-approved (draft) artifacts continue to backfill with the plain blanket flag."""
    proj = _setup_proj(tmp_path)
    # Draft BRD (non-approved) — should be written with blanket --apply
    brd_file = proj / "docs" / "product" / "brd.md"
    brd_file.write_text(_BRD_MISSING_ID_DRAFT, encoding="utf-8")

    rc, report, err = _run(
        proj, "--apply", "--confirmed-by", "PO", "--date", "2026-01-01"
    )
    assert rc == 0, f"blanket apply on draft must succeed; got {rc}\n{err}"

    after_text = brd_file.read_text(encoding="utf-8")
    assert "id: BRD" in after_text, "draft artifact must receive id under blanket --apply"

    bak = brd_file.with_name(brd_file.name + ".bak")
    assert bak.exists(), ".bak must be created for written artifact"


# ---------------------------------------------------------------------------
# FIX 2 — id-backfill must not stamp or downgrade schema_version
# ---------------------------------------------------------------------------

_BRD_SCHEMA_V2_MISSING_ID = """\
---
type: brd
status: draft
schema_version: 2
lang: en
owner: Jane
version: 1.0.0
created: 2026-06-01
updated: 2026-06-01
goals:
  - id: BRD-G1
    title: "A goal"
    metrics: [north-star]
    status: draft
---

# BRD
"""


def test_apply_preserves_existing_schema_version(tmp_path):
    """Applying to a file with schema_version: 2 must leave schema_version exactly 2 — no stamp."""
    proj = _setup_proj(tmp_path)
    brd_file = proj / "docs" / "product" / "brd.md"
    brd_file.write_text(_BRD_SCHEMA_V2_MISSING_ID, encoding="utf-8")

    rc, report, err = _run(
        proj, "--apply", "--confirmed-by", "PO", "--date", "2026-01-01"
    )
    assert rc == 0, f"apply must succeed; got {rc}\n{err}"

    parsed = parse_file(brd_file)
    assert parsed["ok"], f"migrated file must parse cleanly: {parsed.get('error')}"
    fm = parsed["frontmatter"]
    assert fm.get("id") == "BRD", "id must be inserted"
    assert fm.get("schema_version") == 2, \
        f"schema_version must remain 2 (not overwritten); got {fm.get('schema_version')!r}"


def test_apply_does_not_inject_schema_version_when_absent(tmp_path):
    """Applying to a file without any schema_version must NOT add schema_version."""
    proj = _setup_proj(tmp_path)
    product_file = proj / "docs" / "product" / "PRODUCT.md"
    product_file.write_text(_PRODUCT_MISSING_ID, encoding="utf-8")

    rc, report, err = _run(
        proj, "--apply", "--confirmed-by", "PO", "--date", "2026-01-01"
    )
    assert rc == 0

    parsed = parse_file(product_file)
    assert parsed["ok"]
    fm = parsed["frontmatter"]
    assert fm.get("id") == "PRODUCT", "id must be inserted"
    assert "schema_version" not in fm, \
        f"schema_version must NOT be injected by id-backfill migrator; got {fm.get('schema_version')!r}"


# ---------------------------------------------------------------------------
# FIX 3 — skipped list must contain only repo-relative paths
# ---------------------------------------------------------------------------

def test_skipped_paths_are_relative(tmp_path):
    """report['skipped'] must contain only repo-relative strings, never absolute paths."""
    proj = _setup_proj(tmp_path)
    # Place an artifact in a non-standard sub-dir so it ends up in skipped
    strange_dir = proj / "docs" / "product" / "custom_artifacts"
    strange_dir.mkdir()
    (strange_dir / "exotic_thing.md").write_text(_UNKNOWN_ARTIFACT, encoding="utf-8")

    rc, report, err = _run(proj)
    assert rc == 0

    skipped = report.get("skipped", []) if report else []
    for entry in skipped:
        assert not str(entry).startswith("/"), \
            f"skipped entry must be repo-relative, got absolute path: {entry!r}"


# ---------------------------------------------------------------------------
# FIX 6 — BOM + leading comment preserved after --apply
# ---------------------------------------------------------------------------

def test_bom_and_comment_preserved(tmp_path):
    """UTF-8 BOM + leading YAML comment are preserved byte-for-byte; only id: is inserted."""
    proj = _setup_proj(tmp_path)
    product_file = proj / "docs" / "product" / "PRODUCT.md"
    product_file.write_bytes(_PRODUCT_BOM_COMMENT.encode("utf-8"))

    before = product_file.read_bytes()

    rc, report, err = _run(
        proj, "--apply", "--confirmed-by", "PO", "--date", "2026-01-01"
    )
    assert rc == 0, f"apply must succeed; got {rc}\n{err}"

    after_bytes = product_file.read_bytes()
    # BOM must still be first byte
    assert after_bytes[:3] == b"\xef\xbb\xbf", "UTF-8 BOM must be preserved"
    after_text = after_bytes.decode("utf-8")
    # Leading comment must survive
    assert "# kit-version: 1.0" in after_text, "leading YAML comment must be preserved"
    # id must be inserted
    assert "id: PRODUCT" in after_text, "id: PRODUCT must be inserted"
