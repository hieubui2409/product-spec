"""test_e2e_freshness_fixture_guard — Phase 9 (9a): lock the committed `/e2e/dating-app/`
critique run as Phase 3's E1 freshness fixture, and guard it against desync.

Resolves the Phase-3/Phase-9 ordering inversion (red-team H2/H5): the dating-app critique reports
(frontmatter-bearing, with `body_hash` + `lens_findings_hash`) ARE the E1 freshness fixture — no
hand-authored one. These tests:

  * DESYNC GUARD — every committed report's `lens_findings_hash` MUST resolve to a committed
    lens-cache file. If the spec/critique is regenerated and a hash changes without the paired cache
    being committed, this fails loudly (the example went stale).
  * FIXTURE REPLAY — `parse_critique_report` over a committed report asserts REAL structural values
    (cache present, ≥1 fingerprinted finding, freshness tags), NOT a vacuous standalone run.

The whole module skips cleanly if `/e2e/dating-app/` is absent (e.g. a sparse checkout).
"""

from __future__ import annotations

import glob
import os
import re
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import parse_critique_report as pcr  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[5]  # .../cleanmatic-skills
E2E = REPO_ROOT / "e2e" / "dating-app"
REPORTS = E2E / "docs" / "product" / "critique"
LENS_CACHE = E2E / "docs" / "product" / ".memory" / "critique-lens-cache"

pytestmark = pytest.mark.skipif(not E2E.is_dir(), reason="/e2e/dating-app not present in this checkout")


def _reports_with_hash():
    out = []
    for r in sorted(glob.glob(str(REPORTS / "*.md"))):
        text = Path(r).read_text(encoding="utf-8")
        m = re.search(r"^lens_findings_hash:\s*(\S+)", text, re.M)
        if m:
            out.append((Path(r), m.group(1)))
    return out


def test_every_report_hash_resolves_to_committed_cache():
    committed = {os.path.basename(f)[:-5] for f in glob.glob(str(LENS_CACHE / "*.json"))}
    pairs = _reports_with_hash()
    assert pairs, "expected committed dating-app critique reports with a lens_findings_hash"
    unresolved = [(p.name, h) for p, h in pairs if h not in committed]
    assert unresolved == [], (
        f"freshness-fixture DESYNC: these reports reference a lens-cache that isn't committed "
        f"{unresolved}. Regenerate + commit the paired cache (Phase-9 selective-extend rule)."
    )


def test_fixture_replay_asserts_real_values():
    pairs = _reports_with_hash()
    report = pairs[0][0]
    out = pcr.parse_report(report, E2E)
    assert out["cache_present"] is True, "fixture replay must hit the committed lens-cache, not pass vacuously"
    assert out["findings"], "expected ≥1 fingerprinted finding from the committed cache"
    # Every finding carries the deterministic struct E1 depends on.
    for f in out["findings"]:
        assert f["fingerprint"] and len(f["fingerprint"]) == 8
        assert f["lens"]
        assert f["freshness"] in {"fresh", "stale", "unknown", "artifact-missing"}


def test_caches_have_no_live_timestamps():
    # Commit-hygiene (M1): committed caches must carry the canonical scrubbed timestamp, never a
    # real run time (which would churn the example on every regeneration + leak run timing). Only
    # ISO-timestamp-shaped values are in scope — a `last_ts` set to a report-stem LABEL
    # (e.g. "260603-prd-chat-lvl5") is not a wall-clock leak and is left as-is by the scrub.
    iso = re.compile(r"\d{4}-\d{2}-\d{2}T")
    for f in glob.glob(str(E2E / "docs/product/.memory/**/*.json"), recursive=True):
        text = Path(f).read_text(encoding="utf-8")
        for m in re.finditer(r'"(stored_at|fetched_at|last_ts)":\s*"([^"]+)"', text):
            if not iso.match(m.group(2)):
                continue  # non-ISO label (e.g. report stem) — not a timestamp leak
            assert m.group(2) == "2026-06-03T00:00:00+00:00", (
                f"un-scrubbed timestamp {m.group(0)} in {os.path.basename(f)} — re-run the Phase-9 scrub"
            )


def test_no_web_cache_committed():
    # web-cache holds third-party scraped text — never shipped (M1).
    assert not (E2E / "docs" / "product" / ".memory" / "web-cache").exists()
