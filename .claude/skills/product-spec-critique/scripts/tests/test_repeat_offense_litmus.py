"""test_repeat_offense_litmus — the mechanical guard for the repeat-offense
surfacing boundary (Phase 05).

Litmus: "If the findings-index were deleted, would the set of flagged findings
change? Must be NO." Repeat-count is presentation only — it is attached by the
consolidator AFTER judgment, and never enters the per-finding inputs the LENS
agents judge. This test enforces INPUT-ISOLATION (the critique output itself is
LLM/non-deterministic and is NOT diffed here):

  1. No per-finding lens input (structural_findings / digest entry) carries a
     repeat / occurrence / count key sourced from the index.
  2. The flagged structural_findings set is byte-identical with vs without a
     findings-index present — deleting the index cannot change WHAT is flagged.

A boundary breach (someone feeds repeat-count into a lens input) makes (1) go red.
"""

from __future__ import annotations

import json

import pytest

from critique_test_support import make_proj, run_scan

# Keys that would mean a repeat-count bled into a per-finding lens input.
_FORBIDDEN_SUBSTRINGS = ("repeat", "occurrence", "seen_count", "prior_count", "times_seen")

# Top-level bundle keys the LENS agents are instructed to ignore (consolidator-only).
_CONSOLIDATOR_ONLY = ("prior_reports", "inherited_context", "descendant_rollup")


def _lens_finding_keys(bundle) -> list[str]:
    keys = []
    for f in bundle.get("structural_findings", []) or []:
        keys += list(f.keys())
    for d in bundle.get("digest", []) or []:
        if isinstance(d, dict):
            keys += list(d.keys())
    return keys


@pytest.mark.bug_class
def test_no_repeat_count_in_lens_inputs(tmp_path):
    proj = make_proj(tmp_path)
    _code, bundle = run_scan(proj, "--scope", "all")
    for k in _lens_finding_keys(bundle):
        low = k.lower()
        assert not any(s in low for s in _FORBIDDEN_SUBSTRINGS), (
            f"repeat-count key {k!r} leaked into a per-finding LENS input — boundary breach"
        )


@pytest.mark.bug_class
def test_flagged_set_unchanged_by_index_presence(tmp_path):
    proj = make_proj(tmp_path)
    _c1, before = run_scan(proj, "--scope", "all")
    flagged_before = json.dumps(before["structural_findings"], sort_keys=True)

    # Plant a non-empty findings-index (the repeat-offense data feed).
    memory = proj / "docs" / "product" / ".memory"
    memory.mkdir(parents=True, exist_ok=True)
    (memory / "findings_index.json").write_text(
        json.dumps({"PRD-AUTH-E1-S1:18": {"finding_fingerprint": "deadbeefdeadbeef", "severity": "blocker",
                                           "occurrences": ["PRD-CHECKOUT@2026-01-01", "PRD-CHECKOUT@2026-02-01"]}}),
        encoding="utf-8",
    )
    _c2, after = run_scan(proj, "--scope", "all")
    flagged_after = json.dumps(after["structural_findings"], sort_keys=True)

    assert flagged_before == flagged_after, (
        "the flagged structural-finding set changed when a findings-index was added — "
        "the repeat-count crossed from presentation into judgment (A9 boundary breach)"
    )
