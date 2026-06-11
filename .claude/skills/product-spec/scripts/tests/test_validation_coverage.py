"""Validation coverage + over-report guards.

- The advisory fence scan must not flood on the kit's own `.claude/` tree (the PO never
  authors specs there); the `--status` fence signals must cap with the full count, never
  enumerate thousands of breaches.
- An artifact with no `id:` must surface as `missing_id` naming the FILE — the internal
  `<missing-id>` sentinel must never leak into a PO-facing finding — and the product/vision
  singletons must be id-checked (previously they had no pattern, so an absent/typo'd id
  slipped through unflagged).

Synthetic fixtures only (no real PO data).
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import check_fence  # noqa: E402
import memory_gap  # noqa: E402
from spec_graph import build_graph  # noqa: E402
from check_consistency import check as check_cons  # noqa: E402


def _git(root: Path, *a):
    subprocess.run(["git", *a], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t.t")
    _git(root, "config", "user.name", "t")
    _git(root, "commit", "--allow-empty", "-q", "-m", "base")


def _touch(root: Path, rel: str, content: str = "x"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# --------------------------------------------- advisory fence must never over-report

def test_fence_scan_excludes_kit_tree(tmp_path):
    _init_repo(tmp_path)
    _touch(tmp_path, ".claude/skills/x/scripts/a.py")   # kit infra — must be ignored
    _touch(tmp_path, ".claude/settings.json")
    _touch(tmp_path, "src/app.py")                      # genuine out-of-fence — still flagged
    _touch(tmp_path, "docs/product/brd.md")             # in-fence — ok
    files = [f["file"] for f in check_fence.scan(tmp_path)]
    assert not any(f.startswith(".claude/") for f in files), "the kit's own tree must not be a breach"
    assert "src/app.py" in files, "a genuine out-of-fence touch must still surface"
    assert "docs/product/brd.md" not in files


def test_fence_signals_cap_with_total(tmp_path):
    _init_repo(tmp_path)
    for i in range(15):
        _touch(tmp_path, f"src/f{i}.py")
    signals = memory_gap._fence_signals(tmp_path)
    assert len(signals) <= memory_gap._FENCE_SIGNAL_CAP + 1, "must cap the list, not enumerate every breach"
    agg = [s for s in signals if s["subject"] is None]
    assert agg, "an aggregate signal must carry the overflow"
    assert "15 total" in agg[0]["evidence"], "the aggregate must preserve the full breach count"


# ------------------------------ an absent/typo'd id must surface without leaking the sentinel

_PRODUCT_NO_ID = """---
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [s]
---
"""

# Same id-less product, but over the persona soft-cap (4) so the `persona_cap_exceeded`
# check also fires — its detail/artifact_id are a second path the internal sentinel could
# leak through, so the no-leak guarantee must hold there too.
_PRODUCT_NO_ID_OVER_CAP = """---
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [a, b, c, d, e, f]
---
"""

_PRODUCT_WRONG_ID = """---
id: prod
type: product
status: draft
lang: en
name: "X"
core_value: "y"
personas: [s]
---
"""

_BRD = """---
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


def _scaffold(tmp_path: Path, product_md: str) -> Path:
    proj = tmp_path / "proj"
    prod = proj / "docs" / "product"
    (prod / "prds").mkdir(parents=True)
    (prod / "epics").mkdir(parents=True)
    (prod / "stories").mkdir(parents=True)
    (prod / "PRODUCT.md").write_text(product_md, encoding="utf-8")
    (prod / "brd.md").write_text(_BRD, encoding="utf-8")
    return proj


def test_missing_id_names_file_no_sentinel_leak(tmp_path):
    proj = _scaffold(tmp_path, _PRODUCT_NO_ID)
    findings = check_cons(build_graph(proj))
    missing = [f for f in findings if f["check"] == "missing_id"]
    assert missing, "a product with no `id:` must raise missing_id"
    f = missing[0]
    assert "PRODUCT.md" in f["detail"], "the finding must name the offending file"
    assert f["artifact_id"] is None, "the finding must not carry the internal sentinel as artifact_id"
    blob = " ".join(str(x) for x in findings)
    assert "<missing-id>" not in blob, "the internal sentinel must never reach a PO-facing finding"


def test_product_wrong_id_flagged_invalid(tmp_path):
    proj = _scaffold(tmp_path, _PRODUCT_WRONG_ID)
    findings = check_cons(build_graph(proj))
    assert any(f["check"] == "invalid_id" and f["artifact_id"] == "prod" for f in findings), \
        "a product carrying a non-PRODUCT id must be flagged invalid_id"


def test_sentinel_not_leaked_via_other_checks(tmp_path):
    """An id-less node that ALSO trips a second check (here persona_cap_exceeded) must not
    leak the internal sentinel through that finding's artifact_id OR its detail string."""
    proj = _scaffold(tmp_path, _PRODUCT_NO_ID_OVER_CAP)
    findings = check_cons(build_graph(proj))
    caps = [f for f in findings if f["check"] == "persona_cap_exceeded"]
    assert caps, "the over-cap persona list must still be flagged on the id-less node"
    for f in findings:
        assert f["artifact_id"] not in ("<missing-id>", "<invalid-id>"), \
            f"{f['check']} leaked the sentinel as artifact_id"
        assert "<missing-id>" not in (f.get("detail") or ""), \
            f"{f['check']} leaked the sentinel into its detail"
