"""Consistency checks: subsystem-table horizon drift + persona portrait gaps.

Two new deterministic rules (no LLM):
  - check_product_subsystems: PRODUCT.md body subsystem table horizon vs PRD
    frontmatter horizon mismatch → WARN.
  - check_persona_portraits: persona in VISION/BRD frontmatter with no body
    heading → WARN.

All fixtures are synthetic (no real PO data). Covers:
  1. mismatch → warn
  2. aligned → 0 findings (negative/no-over-report)
  3. missing portrait → warn
  4. portrait present → 0 findings (negative)
  5. garbled/no subsystem table → no crash (fail-soft)
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from spec_graph import build_graph  # noqa: E402
from check_consistency_product import (  # noqa: E402
    check_product_subsystems,
    check_persona_portraits,
)


# ---------------------------------------------------------------------------
# Minimal shared fixture helpers
# ---------------------------------------------------------------------------

_PRODUCT_MD_TMPL = """\
---
id: PRODUCT
type: product
status: draft
lang: en
name: "TestCo"
core_value: "test"
personas: []
---

{body}
"""

_BRD_MD = """\
---
id: BRD
type: brd
status: draft
lang: en
goals:
  - id: BRD-G1
    title: g
    status: draft
    metrics: [m]
---
"""

_VISION_MD_TMPL = """\
---
id: VISION
type: vision
status: draft
lang: en
personas: {personas}
---

{body}
"""


def _scaffold(tmp_path: Path) -> Path:
    """Minimal project tree: PRODUCT.md, brd.md, prds/, epics/, stories/."""
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "brd.md").write_text(_BRD_MD, encoding="utf-8")
    return proj


# ---------------------------------------------------------------------------
# check_product_subsystems — subsystem table horizon vs PRD horizon
# ---------------------------------------------------------------------------

def test_subsystem_horizon_mismatch_warns(tmp_path):
    """PRODUCT.md table row PAYMENT horizon=later but PRD-PAYMENT horizon=now → exactly one WARN naming PAYMENT."""
    proj = _scaffold(tmp_path)
    prod = proj / "docs" / "product"

    # PRODUCT.md with a subsystem table
    body = """\
## Subsystems

| ID | Name | Horizon |
|----|------|---------|
| PAYMENT | Payment Gateway | later |
"""
    (prod / "PRODUCT.md").write_text(
        _PRODUCT_MD_TMPL.format(body=body), encoding="utf-8"
    )

    # PRD-PAYMENT has horizon: now — mismatch with table's later
    (prod / "prds" / "payment.md").write_text("""\
---
id: PRD-PAYMENT
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
horizon: now
---
""", encoding="utf-8")

    graph = build_graph(proj)
    findings = check_product_subsystems(graph, proj)

    assert len(findings) == 1, f"Expected 1 finding, got {len(findings)}: {findings}"
    f = findings[0]
    assert f["severity"] == "warn"
    assert "PAYMENT" in f["detail"]


def test_subsystem_horizon_aligned_clean(tmp_path):
    """All subsystem table rows match their PRD horizon → 0 findings (no over-report)."""
    proj = _scaffold(tmp_path)
    prod = proj / "docs" / "product"

    body = """\
## Subsystems

| ID | Name | Horizon |
|----|------|---------|
| PAYMENT | Payment Gateway | now |
"""
    (prod / "PRODUCT.md").write_text(
        _PRODUCT_MD_TMPL.format(body=body), encoding="utf-8"
    )

    (prod / "prds" / "payment.md").write_text("""\
---
id: PRD-PAYMENT
type: prd
brd_goals: [BRD-G1]
status: draft
lang: en
horizon: now
---
""", encoding="utf-8")

    graph = build_graph(proj)
    findings = check_product_subsystems(graph, proj)

    assert findings == [], f"Expected 0 findings, got {findings}"


def test_malformed_subsystem_table_no_crash(tmp_path):
    """Garbled/no table in PRODUCT.md body → empty list, no exception (fail-soft)."""
    proj = _scaffold(tmp_path)
    prod = proj / "docs" / "product"

    # No table at all — just plain text in the body
    body = "This product has no structured subsystem table yet."
    (prod / "PRODUCT.md").write_text(
        _PRODUCT_MD_TMPL.format(body=body), encoding="utf-8"
    )

    graph = build_graph(proj)
    # Must not raise, must return empty
    findings = check_product_subsystems(graph, proj)
    assert findings == [], f"Expected [] for malformed table, got {findings}"


def test_subsystem_no_horizon_column_no_crash(tmp_path):
    """Table without a Horizon column → fail-soft, return []."""
    proj = _scaffold(tmp_path)
    prod = proj / "docs" / "product"

    body = """\
## Subsystems

| ID | Name |
|----|------|
| PAYMENT | Payment Gateway |
"""
    (prod / "PRODUCT.md").write_text(
        _PRODUCT_MD_TMPL.format(body=body), encoding="utf-8"
    )

    graph = build_graph(proj)
    findings = check_product_subsystems(graph, proj)
    assert findings == [], f"Expected [] when no Horizon column, got {findings}"


# ---------------------------------------------------------------------------
# check_persona_portraits — persona in frontmatter vs body heading
# ---------------------------------------------------------------------------

def test_persona_in_frontmatter_without_body_warns(tmp_path):
    """VISION frontmatter persona CSKH with no body ## CSKH heading → WARN."""
    proj = _scaffold(tmp_path)
    prod = proj / "docs" / "product"

    (prod / "PRODUCT.md").write_text(
        _PRODUCT_MD_TMPL.format(body=""), encoding="utf-8"
    )

    # VISION has persona CSKH in frontmatter but no matching body heading
    vision = _VISION_MD_TMPL.format(
        personas="[CSKH]",
        body="## Introduction\n\nSome vision content without a persona section.",
    )
    (prod / "vision.md").write_text(vision, encoding="utf-8")

    graph = build_graph(proj)
    findings = check_persona_portraits(graph, proj)

    assert len(findings) >= 1, f"Expected ≥1 WARN, got {findings}"
    assert all(f["severity"] == "warn" for f in findings)
    # At least one finding should mention CSKH
    details = " ".join(f["detail"] for f in findings)
    assert "CSKH" in details, f"Expected CSKH in detail: {details}"


def test_persona_with_body_portrait_clean(tmp_path):
    """Persona present in body heading → 0 findings (no over-report)."""
    proj = _scaffold(tmp_path)
    prod = proj / "docs" / "product"

    (prod / "PRODUCT.md").write_text(
        _PRODUCT_MD_TMPL.format(body=""), encoding="utf-8"
    )

    # VISION has persona Manager with matching ## Manager body heading
    vision = _VISION_MD_TMPL.format(
        personas="[Manager]",
        body="## Manager\n\nThis persona manages the platform.",
    )
    (prod / "vision.md").write_text(vision, encoding="utf-8")

    graph = build_graph(proj)
    findings = check_persona_portraits(graph, proj)

    assert findings == [], f"Expected 0 findings when portrait present, got {findings}"
