"""Tests for the build-age beacon inside the `--status` feeder (`status.py`).

The installer drops `<root>/.claude/MANIFEST.json` (bundle_version + built_at) into
the PO's tree. `--status` surfaces a *build-age* fact — days since the running copy
was packed — so the LLM can nudge "ask the publisher for a newer release". Build-age
(not install-age) is the honest staleness signal: a freshly-installed but already-old
release still reads as stale.

Fail-silent contract: a missing MANIFEST (dev tree / hand-copied spec), malformed
JSON, a missing `built_at`, or an unparseable `built_at` all degrade to `None`. The
beacon is a soft hint — it must NEVER gate, raise, or touch the network. The
`bundle_age` key is ALWAYS present in the report (None when unavailable) so the
LLM-facing contract is stable.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import status  # noqa: E402

from conftest import make_proj, validate_baseline  # noqa: E402,F401


def _proj(tmp_path: Path) -> Path:
    return make_proj(tmp_path, git=False)


def _write_manifest(proj: Path, *, built_at, version="2.3.1") -> None:
    """Drop a MANIFEST.json where the installer puts it: `<root>/.claude/`.

    `built_at` mirrors the real builder output (ISO 8601 with a UTC offset,
    seconds precision); pass a non-string to exercise the malformed path."""
    claude = proj / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "bundle_name": "product-spec",
        "bundle_version": version,
        "built_at": built_at,
        "source_repo": "x",
        "source_commit": "y",
        "total_bytes": 0,
        "files": [],
    }
    (claude / "MANIFEST.json").write_text(
        json.dumps(payload), encoding="utf-8")


# ---------- present + parseable → build-age ----------

def test_bundle_age_reports_build_age(tmp_path):
    """MANIFEST built 30 days before `--today` → age_days == 30 and the version is
    carried through verbatim for the nudge."""
    proj = _proj(tmp_path)
    _write_manifest(proj, built_at="2026-05-13T12:00:00+00:00", version="2.3.1")
    report = status.build_status(proj, today="2026-06-12")
    beacon = report["bundle_age"]
    assert beacon is not None
    assert beacon["age_days"] == 30
    assert beacon["bundle_version"] == "2.3.1"
    assert beacon["built_at"] == "2026-05-13T12:00:00+00:00"


def test_bundle_age_present_on_baseline_path(tmp_path):
    """The beacon rides BOTH the no-baseline and post-validate return paths — a
    validated spec still gets the build-age fact."""
    proj = _proj(tmp_path)
    validate_baseline(proj)
    _write_manifest(proj, built_at="2026-06-10T00:00:00+00:00")
    report = status.build_status(proj, today="2026-06-12")
    assert report["baseline"] is True
    assert report["bundle_age"] is not None
    assert report["bundle_age"]["age_days"] == 2


def test_bundle_age_future_built_at_clamps_to_zero(tmp_path):
    """A built_at AFTER today (clock skew / a build from a machine ahead) clamps to
    0 days rather than reporting a negative age."""
    proj = _proj(tmp_path)
    _write_manifest(proj, built_at="2026-06-17T12:00:00+00:00")
    report = status.build_status(proj, today="2026-06-12")
    assert report["bundle_age"]["age_days"] == 0


# ---------- fail-silent: key present, value None ----------

def test_bundle_age_absent_manifest_is_silent(tmp_path):
    """No MANIFEST (dev tree / hand-copied spec) → key present, value None. No
    crash, no fabricated age."""
    proj = _proj(tmp_path)
    report = status.build_status(proj, today="2026-06-12")
    assert "bundle_age" in report
    assert report["bundle_age"] is None


def test_bundle_age_malformed_json_is_silent(tmp_path):
    proj = _proj(tmp_path)
    claude = proj / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    (claude / "MANIFEST.json").write_text("{ not valid json", encoding="utf-8")
    report = status.build_status(proj, today="2026-06-12")
    assert report["bundle_age"] is None


def test_bundle_age_missing_built_at_is_silent(tmp_path):
    proj = _proj(tmp_path)
    claude = proj / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    (claude / "MANIFEST.json").write_text(
        json.dumps({"bundle_version": "2.3.1"}), encoding="utf-8")
    report = status.build_status(proj, today="2026-06-12")
    assert report["bundle_age"] is None


def test_bundle_age_unparseable_built_at_is_silent(tmp_path):
    proj = _proj(tmp_path)
    _write_manifest(proj, built_at="not-a-timestamp")
    report = status.build_status(proj, today="2026-06-12")
    assert report["bundle_age"] is None


def test_bundle_age_nonstring_built_at_is_silent(tmp_path):
    proj = _proj(tmp_path)
    _write_manifest(proj, built_at=12345)
    report = status.build_status(proj, today="2026-06-12")
    assert report["bundle_age"] is None


def test_bundle_age_empty_version_is_silent(tmp_path):
    """A blank bundle_version would render a half-formed "version  " nudge — the
    fail-silent contract degrades it to None instead of a partial beacon."""
    proj = _proj(tmp_path)
    _write_manifest(proj, built_at="2026-05-13T12:00:00+00:00", version="")
    report = status.build_status(proj, today="2026-06-12")
    assert report["bundle_age"] is None


def test_bundle_age_empty_built_at_is_silent(tmp_path):
    proj = _proj(tmp_path)
    _write_manifest(proj, built_at="")
    report = status.build_status(proj, today="2026-06-12")
    assert report["bundle_age"] is None


# ---------- read-only: the beacon never writes ----------

def test_bundle_age_does_not_touch_manifest(tmp_path):
    """Reading the MANIFEST must not mutate it (status is read-only end-to-end)."""
    proj = _proj(tmp_path)
    _write_manifest(proj, built_at="2026-05-13T12:00:00+00:00")
    manifest = proj / ".claude" / "MANIFEST.json"
    before = manifest.read_bytes()
    status.build_status(proj, today="2026-06-12")
    assert manifest.read_bytes() == before


# ---------- CLI ----------

def test_status_cli_surfaces_bundle_age(tmp_path):
    proj = _proj(tmp_path)
    _write_manifest(proj, built_at="2026-05-13T12:00:00+00:00", version="2.3.1")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "status.py"),
         "--root", str(proj), "--today", "2026-06-12"],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["bundle_age"]["bundle_version"] == "2.3.1"
    assert out["bundle_age"]["age_days"] == 30
