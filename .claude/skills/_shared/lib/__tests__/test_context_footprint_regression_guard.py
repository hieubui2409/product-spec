"""Regression guard — wires context_footprint into the pytest check surface.

Asserts the LIVE bundle does not regress vs the committed baseline:
  - no skill's SKILL.md or total token count grew vs context_footprint_baseline.json;
  - the GATE co-presence check is green (no GATE pointer with an unreachable full-prose home).

A future edit that regrows a SKILL.md or orphans a safety GATE fails here. A *deliberate*
growth (e.g. a new ref) updates the committed baseline in the same change — same as the
documented `--gate` workflow.

Run: .claude/skills/.venv/bin/python3 -m pytest \
  .claude/skills/_shared/lib/__tests__/test_context_footprint_regression_guard.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import context_footprint as cf  # type: ignore  # noqa: E402

LIB = Path(__file__).resolve().parent.parent           # _shared/lib
REPO = LIB.parents[3]                                   # _shared/lib -> _shared -> skills -> .claude -> repo root
SKILLS = REPO / ".claude" / "skills"
BASELINE = LIB / "context_footprint_baseline.json"
ALWAYS_ON = REPO / "CLAUDE.md"
MEASURED = ["product-spec", "product-spec-critique", "release", "telemetry"]


def _skill_dirs() -> list[Path]:
    return [SKILLS / n for n in MEASURED]


def test_baseline_artifact_present():
    assert BASELINE.is_file(), "committed baseline JSON missing — run --baseline to create it"
    assert ALWAYS_ON.is_file(), "always-on root CLAUDE.md missing"


def test_no_skill_md_or_total_regression_vs_committed_baseline():
    base = json.loads(BASELINE.read_text(encoding="utf-8"))
    live = cf.measure_all(_skill_dirs())
    ok, regressions = cf.gate(cf.compare(base, live))
    assert ok, "context footprint regressed vs committed baseline:\n  " + "\n  ".join(regressions)


def test_gate_copresence_green_on_live_bundle():
    failures = cf.copresence_check(_skill_dirs(), ALWAYS_ON.read_text(encoding="utf-8"))
    assert failures == [], "GATE co-presence failures (orphaned safety GATE pointer):\n  " + "\n  ".join(failures)
