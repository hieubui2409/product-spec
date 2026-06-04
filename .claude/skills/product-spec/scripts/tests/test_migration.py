"""Impact Engine & Migration (TDD RED).

Covers the two deterministic, script-owned surfaces (the LLM-driven
impact annotation + contradiction protocol are exercised by the `impact-pass`
eval, not here — Script-vs-LLM split):

  1. `migrate_multidim_fields.py` — brings a v1 spec up to the v2 schema by
     adding the new dimension fields as EMPTY placeholders:
         PRD  → risks: [], target_date: null, depends_on: [], competitive_parity: {}
         Epic → risks: [], target_date: null, depends_on: []
         BRD  → competitors: []
     Contract:
       - dry-run default: report which files lack which fields; write NOTHING.
       - --apply: write placeholders; copy each touched original → `*.bak` first.
       - status: approved files are NEVER written — deferred to a
         `confirm_required` list (PO confirms per item; LLM drives the
         AskUserQuestion). This is the no-auto-edit-approved guarantee.
       - idempotent + deterministic: a second --apply run is a no-op (the fields
         are already present), so the `.bak` from the first run is not clobbered
         with an already-migrated copy.

  2. change-log entry schema — the writer/template must carry BOTH
     `affected_set` (ALREADY present — do NOT re-add) AND the
     new `dims` field (the ONLY field this adds).

Mirrors the subprocess + JSON-stdout style of test_scripts.py and the
fixture-build style of test_risk_complete.py.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from frontmatter_parser import parse_file  # noqa: E402
from generate_templates import fill_defaults, render  # noqa: E402

TEMPLATES = SCRIPTS_DIR.parent / "assets" / "templates"
MIGRATE = SCRIPTS_DIR / "migrate_multidim_fields.py"


# ---------------------------------------------------------------------------
# v1 fixtures — a minimal pre-v2 spec: the frontmatter carries NONE of the new
# multidim fields (no risks/target_date/depends_on/competitive_parity/competitors).
# This is exactly the back-compat baseline the migration must lift to v2.
# ---------------------------------------------------------------------------

_V1_PRODUCT_MD = """---
id: PRODUCT
type: product
status: draft
lang: en
name: "Acme Shop"
core_value: "frictionless boutique storefront"
personas: [shopper]
---
"""

_V1_BRD_MD = """---
id: BRD
type: brd
status: draft
lang: en
goals:
  - id: BRD-G1
    title: "Onboard brands"
    metrics: [brands-onboarded]
    status: draft
    owner: Jane
---

# BRD
"""

_V1_PRD_MD = """---
id: PRD-AUTH
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
personas: [shopper]
scope: in
moscow: must
horizon: now
metrics: [signups]
---

# Auth PRD
"""

_V1_EPIC_MD = """---
id: PRD-AUTH-E1
type: epic
prd: PRD-AUTH
brd_goals: [BRD-G1]
status: draft
lang: en
personas: [shopper]
scope: in
moscow: must
horizon: now
metrics: [signups]
---

# Login Epic
"""


def _v1_spec(tmp_path: Path) -> Path:
    """Write a v1 docs/product tree (PRODUCT + BRD + 1 PRD + 1 epic), all WITHOUT
    the v2 multidim fields. Returns the project root."""
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(_V1_PRODUCT_MD, encoding="utf-8")
    (prod / "brd.md").write_text(_V1_BRD_MD, encoding="utf-8")
    (prod / "prds" / "auth.md").write_text(_V1_PRD_MD, encoding="utf-8")
    (prod / "epics" / "PRD-AUTH-E1.md").write_text(_V1_EPIC_MD, encoding="utf-8")
    return proj


def _run_migrate(proj: Path, *extra: str) -> dict:
    """Run migrate_multidim_fields.py and parse its JSON stdout. Analytical
    scripts always exit 0 (CLI contract); --apply is the only mutating flag."""
    r = subprocess.run(
        [sys.executable, str(MIGRATE), "--root", str(proj), *extra],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"migrate exited {r.returncode}\nSTDERR:\n{r.stderr}"
    return json.loads(r.stdout)


# ---------------------------------------------------------------------------
# test_migration_adds_placeholders — a v1 PRD/Epic/BRD missing the v2 fields:
# `--apply` adds empty placeholders and backs up each original to `*.bak`.
# ---------------------------------------------------------------------------

def test_migration_adds_placeholders(tmp_path):
    proj = _v1_spec(tmp_path)
    prod = proj / "docs" / "product"
    prd = prod / "prds" / "auth.md"
    epic = prod / "epics" / "PRD-AUTH-E1.md"
    brd = prod / "brd.md"

    # Pre-condition: none of the v2 fields exist yet (true v1 baseline).
    assert "risks" not in parse_file(prd)["frontmatter"]
    assert "competitive_parity" not in parse_file(prd)["frontmatter"]
    assert "competitors" not in parse_file(brd)["frontmatter"]

    _run_migrate(proj, "--apply")

    # PRD gains all four v2 fields as EMPTY placeholders (not TBD, not absent).
    prd_fm = parse_file(prd)["frontmatter"]
    assert prd_fm.get("risks") == [], "PRD must gain `risks: []` placeholder"
    assert prd_fm.get("depends_on") == [], "PRD must gain `depends_on: []` placeholder"
    assert prd_fm.get("competitive_parity") == {}, "PRD must gain `competitive_parity: {}`"
    assert "target_date" in prd_fm and prd_fm["target_date"] is None, \
        "PRD must gain `target_date: null` placeholder"

    # Epic gains the TIME/RISK fields (no competitive_parity — that's PRD-only).
    epic_fm = parse_file(epic)["frontmatter"]
    assert epic_fm.get("risks") == []
    assert epic_fm.get("depends_on") == []
    assert "target_date" in epic_fm and epic_fm["target_date"] is None

    # BRD gains the competitor-identity list.
    brd_fm = parse_file(brd)["frontmatter"]
    assert brd_fm.get("competitors") == [], "BRD must gain `competitors: []` placeholder"

    # Backups of every touched original must exist (so the PO can revert).
    assert (prod / "prds" / "auth.md.bak").exists(), "PRD original must be backed up to *.bak"
    assert (prod / "epics" / "PRD-AUTH-E1.md.bak").exists(), "Epic original must be backed up"
    assert (prod / "brd.md.bak").exists(), "BRD original must be backed up"

    # The backup is the PRE-migration content (no v2 fields in it).
    bak_fm = parse_file(prod / "prds" / "auth.md.bak")["frontmatter"]
    assert "risks" not in bak_fm, ".bak must hold the original pre-migration frontmatter"


def test_migration_dry_run_writes_nothing(tmp_path):
    """Dry-run (default, no --apply) reports the gaps but mutates NO files and
    creates NO .bak — the report is advisory only."""
    proj = _v1_spec(tmp_path)
    prod = proj / "docs" / "product"
    prd = prod / "prds" / "auth.md"
    before = prd.read_text(encoding="utf-8")

    report = _run_migrate(proj)  # no --apply

    assert prd.read_text(encoding="utf-8") == before, "dry-run must not modify any file"
    assert not (prod / "prds" / "auth.md.bak").exists(), "dry-run must not create .bak files"
    # The report must surface that auth.md (a v1 PRD) is missing v2 fields.
    blob = json.dumps(report)
    assert "auth.md" in blob or "PRD-AUTH" in blob, \
        "dry-run report must name the v1 file(s) that need migration"


# ---------------------------------------------------------------------------
# test_migration_skips_approved — an `approved` artifact is NEVER edited; it is
# deferred to the `confirm_required` list (no-auto-edit-approved).
# ---------------------------------------------------------------------------

def test_migration_skips_approved(tmp_path):
    proj = _v1_spec(tmp_path)
    prod = proj / "docs" / "product"
    prd = prod / "prds" / "auth.md"
    # Promote the PRD to approved (status flip only — still a v1 shape).
    prd.write_text(_V1_PRD_MD.replace("status: draft", "status: approved"), encoding="utf-8")
    before = prd.read_text(encoding="utf-8")

    report = _run_migrate(proj, "--apply")

    # The approved PRD must NOT be written and NOT be backed up.
    assert prd.read_text(encoding="utf-8") == before, \
        "approved artifact must NOT be auto-edited"
    assert "risks" not in parse_file(prd)["frontmatter"], \
        "approved artifact must keep its v1 frontmatter untouched"
    assert not (prod / "prds" / "auth.md.bak").exists(), \
        "approved artifact must not be backed up (it was never written)"

    # It must instead appear in a `confirm_required` list for per-item PO sign-off.
    confirm = report.get("confirm_required")
    assert isinstance(confirm, list), "report must carry a `confirm_required` list"
    flat = json.dumps(confirm)
    assert "PRD-AUTH" in flat or "auth.md" in flat, \
        "approved PRD must be listed in confirm_required for per-item PO confirmation"

    # A non-approved sibling (the epic) is still migrated in the same run.
    epic_fm = parse_file(prod / "epics" / "PRD-AUTH-E1.md")["frontmatter"]
    assert epic_fm.get("risks") == [], \
        "non-approved artifacts are still migrated alongside the deferred approved one"


# ---------------------------------------------------------------------------
# test_migration_idempotent — running --apply twice is a no-op the second time
# (fields already present); the first-run .bak is not overwritten.
# ---------------------------------------------------------------------------

def test_migration_idempotent(tmp_path):
    proj = _v1_spec(tmp_path)
    prod = proj / "docs" / "product"
    prd = prod / "prds" / "auth.md"
    bak = prod / "prds" / "auth.md.bak"

    _run_migrate(proj, "--apply")
    after_first = prd.read_text(encoding="utf-8")
    bak_after_first = bak.read_text(encoding="utf-8")

    report2 = _run_migrate(proj, "--apply")

    # Second run leaves the (already-migrated) files byte-identical.
    assert prd.read_text(encoding="utf-8") == after_first, \
        "second --apply must be a no-op on an already-migrated file (idempotent)"
    # And it must NOT clobber the original-content .bak with a migrated copy.
    assert bak.read_text(encoding="utf-8") == bak_after_first, \
        "second --apply must not overwrite the pre-migration .bak"
    assert "risks" not in parse_file(bak)["frontmatter"], \
        ".bak must still hold the original pre-migration frontmatter after a 2nd run"

    # The second report must record that nothing needed migrating.
    blob = json.dumps(report2)
    assert '"migrated": []' in blob or '"would_migrate": []' in blob \
        or report2.get("migrated") in ([], None) or report2.get("changed") in ([], None), \
        "second run report must show no files were migrated"


# ---------------------------------------------------------------------------
# test_changelog_schema — the change-log entry carries BOTH `affected_set`
# (already present — do NOT re-add) AND the new `dims` field.
# Asserted against the template that generate_templates.py renders for
# --type change_log_entry (the change-log writer).
# ---------------------------------------------------------------------------

def test_changelog_schema():
    """The change-log-entry template must expose both an `affected_set` field
    (pre-existing) and a NEW `dims` field — the only field this adds.

    Discriminating RED assertion: today the template carries `affected_set`
    but has no `dims` line/token, so a rendered entry can never declare which
    dimensions a change touched.
    """
    tmpl_text = (TEMPLATES / "change-log-entry.md").read_text(encoding="utf-8")

    # `affected_set` is the pre-existing field — must remain (no regression).
    assert "{{affected_set}}" in tmpl_text or "affected_set" in tmpl_text, \
        "change-log-entry.md must keep the existing `affected_set` field (do not drop)"

    # `dims` is the new field this phase adds (RED today: not present).
    assert "{{dims}}" in tmpl_text or "dims" in tmpl_text.lower(), \
        "change-log-entry.md must gain a `dims` field (the dimensions touched)"


def test_changelog_renders_dims_value():
    """A rendered change-log entry with a `dims` value must surface that value
    in the output — proves `dims` is a substitutable token, not dead text.

    Uses the same fill_defaults + render path the change-log writer uses.
    """
    tmpl_text = (TEMPLATES / "change-log-entry.md").read_text(encoding="utf-8")
    vals = fill_defaults(
        {
            "date": "2026-05-30",
            "change_type": "update",
            "change_type_vi": "cập nhật",
            "artifact_id": "PRD-AUTH",
            "file": "prds/auth.md",
            "action": "edited scope",
            "reason": "PO request",
            "affected_set": ["PRD-AUTH-E1", "PRD-AUTH-E1-S1"],
            "dims": ["risk", "time"],
            "author": "Jane",
        },
        "change_log_entry",
        "CHANGELOG",
        "en",
    )
    rendered = render(tmpl_text, vals, keep_optional=[])
    # The affected_set values render (existing behaviour) ...
    assert "PRD-AUTH-E1" in rendered
    # ... and the new dims values render too (the field is live).
    assert "risk" in rendered and "time" in rendered, \
        "rendered change-log entry must surface the `dims` values (risk/time)"


# ---------------------------------------------------------------------------
# test_migration_type_scoping — the migration must write each v2 field ONLY onto
# the artifact types whose per-type guards accept it, so a migrated spec never
# trips the very `invalid_type`/`unknown_ref` errors those phases define:
#   - depends_on / target_date / risks → PRD + Epic
#   - competitive_parity → PRD ONLY (an Epic/BRD must NOT gain it)
#   - competitors → BRD ONLY
# A naive migration writing competitive_parity onto an Epic would induce a
# structural regression. We assert both the placed-field set AND that the
# migrated spec still validates with ZERO structural errors (the real risk).
# ---------------------------------------------------------------------------

def test_migration_type_scoping(tmp_path):
    proj = _v1_spec(tmp_path)
    prod = proj / "docs" / "product"

    _run_migrate(proj, "--apply")

    prd_fm = parse_file(prod / "prds" / "auth.md")["frontmatter"]
    epic_fm = parse_file(prod / "epics" / "PRD-AUTH-E1.md")["frontmatter"]
    brd_fm = parse_file(prod / "brd.md")["frontmatter"]

    # competitive_parity is PRD-only — the Epic and BRD must NOT gain it.
    assert "competitive_parity" in prd_fm, "PRD must gain competitive_parity"
    assert "competitive_parity" not in epic_fm, \
        "Epic must NOT gain competitive_parity (PRD-only — the per-type guard rejects it on an epic)"
    assert "competitive_parity" not in brd_fm, "BRD must NOT gain competitive_parity"

    # competitors is BRD-only — neither the PRD nor the Epic may gain it.
    assert "competitors" in brd_fm, "BRD must gain competitors"
    assert "competitors" not in prd_fm and "competitors" not in epic_fm, \
        "competitors is BRD-only (a PRD/Epic competitors list would be a phantom field)"

    # depends_on / target_date / risks are PRD+Epic — never written onto the BRD.
    for f in ("depends_on", "target_date", "risks"):
        assert f not in brd_fm, f"BRD must NOT gain {f} (PRD+Epic-only)"

    # The migrated spec must still validate with ZERO structural errors: the
    # placeholders must not induce invalid_type / unknown_ref / unknown_enum.
    r = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "check_consistency.py"), "--root", str(proj)],
        capture_output=True, text=True,
    )
    assert r.returncode == 0
    errors = [f for f in json.loads(r.stdout).get("findings", []) if f.get("severity") == "error"]
    assert errors == [], f"migrated spec must have 0 structural errors, got: {errors}"


# ---------------------------------------------------------------------------
# test_impact_report_template_exists — the per-change impact report skeleton must
# exist with the columns the impact-pass fills. The LLM composes the body;
# the template fixes the heading + table shape so every report is uniform.
# ---------------------------------------------------------------------------

def test_impact_report_template_exists():
    tmpl = TEMPLATES / "impact-report.md"
    assert tmpl.exists(), "assets/templates/impact-report.md must exist"
    text = tmpl.read_text(encoding="utf-8")
    # The report carries the change-set, the dimension union, and the per-node
    # annotation table (node / dim_touched / interpretation / action).
    for token in ("{{changed_set}}", "{{dims}}", "{{rows}}"):
        assert token in text, f"impact-report.md must carry the {token} token"
    assert "Dim touched" in text and "Suggested action" in text, \
        "impact-report.md must define the affected-node table columns"
    # The optional contradictions block (approved + contradicted) must be present.
    assert "{{contradictions}}" in text, \
        "impact-report.md must carry an (optional) contradictions block for approved nodes"


# ---------------------------------------------------------------------------
# test_snapshot_serializes_dates — write_snapshot must serialize a v2 node's
# target_date (PyYAML parses ISO dates to datetime.date) instead of crashing.
# This is the prerequisite for the --validate impact-pass, which reads the
# snapshot delta; a v2 spec carrying any target_date must snapshot cleanly.
# ---------------------------------------------------------------------------

def test_snapshot_serializes_dates(tmp_path):
    import datetime as _dt
    from spec_graph import write_snapshot  # noqa: E402

    graph = {
        "generated_at": "2026-05-30T00:00:00Z",
        "nodes": [
            {"id": "PRD-A", "type": "prd", "target_date": _dt.date(2026, 8, 1)},
        ],
        "edges": [],
        "product": {},
    }
    # Must not raise TypeError: Object of type date is not JSON serializable.
    snap = write_snapshot(graph, tmp_path)
    loaded = json.loads(snap.read_text(encoding="utf-8"))
    node = next(n for n in loaded["nodes"] if n["id"] == "PRD-A")
    assert node["target_date"] == "2026-08-01", \
        "write_snapshot must coerce a datetime.date target_date to an ISO string"


# ---------------------------------------------------------------------------
# Line-ending preservation (Cycle 7): the migration promises the rest of the
# file is preserved byte-for-byte. A CRLF-authored spec must NOT be silently
# reflowed to LF when placeholder lines are inserted.
# ---------------------------------------------------------------------------

from migrate_multidim_fields import _insert_before_closing_fence, apply_file  # noqa: E402


def test_insert_preserves_crlf_line_endings():
    src = "---\r\nid: PRD-A\r\ntype: prd\r\n---\r\nbody\r\n"
    out = _insert_before_closing_fence(src, ["risks: []", "target_date: null"])
    assert out is not None
    assert "\r\n" in out
    assert out.replace("\r\n", "").find("\n") == -1, "a bare LF leaked into a CRLF file"
    assert "risks: []\r\n" in out and "target_date: null\r\n" in out
    assert "id: PRD-A\r\n" in out  # existing line unchanged


def test_insert_preserves_lf_line_endings():
    src = "---\nid: PRD-A\ntype: prd\n---\nbody\n"
    out = _insert_before_closing_fence(src, ["risks: []"])
    assert out is not None
    assert "\r" not in out
    assert "risks: []\n" in out


def test_apply_file_preserves_crlf_end_to_end(tmp_path):
    prd = tmp_path / "prds"
    prd.mkdir()
    f = prd / "a.md"
    f.write_bytes(b"---\r\nid: PRD-A\r\ntype: prd\r\nbrd_goals: [BRD-G1]\r\nstatus: draft\r\nlang: en\r\n---\r\nbody\r\n")
    assert apply_file(f) is True
    raw = f.read_bytes()
    assert b"\r\n" in raw
    assert raw.replace(b"\r\n", b"").find(b"\n") == -1, "a bare LF leaked into a CRLF file on disk"
    assert b"risks: []" in raw
