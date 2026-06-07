"""test_lens_usage_tokens.py — parity of the ported headline lens against the
Phase-1 fixtures: invocation counts (flat-slug normalized), token attribution
(span model), never-used catalog, and the low-volume gate.
"""
import importlib
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))
FIX = Path(__file__).resolve().parent / "fixtures"
BIG_DAYS = 36500  # ignore the date window so fixtures never age out of range


@pytest.fixture
def lens(monkeypatch):
    monkeypatch.setenv("CK_TELEMETRY_DIR", str(FIX / "telemetry"))
    monkeypatch.setenv("CK_SESSIONS_DIR", str(FIX / "sessions"))
    monkeypatch.setenv("CK_SKILLS_DIR", str(FIX / "skills"))
    for m in ("telemetry_paths", "catalog", "lens_usage_tokens"):
        sys.modules.pop(m, None)
    import telemetry_paths  # noqa
    importlib.reload(telemetry_paths)
    import lens_usage_tokens
    importlib.reload(lens_usage_tokens)
    return lens_usage_tokens


def test_counts_normalize_slug_and_dir_to_same_skill(lens):
    d = lens.gather(days=BIG_DAYS, with_tokens=False, skills_dir=FIX / "skills")
    counts = {r["skill"]: r["count"] for r in d["rows"]}
    # 'cleanmatic:product-spec' (×2) + 'product-spec' (×1) collapse to product-spec=3
    assert counts["product-spec"] == 3
    assert counts["release"] == 1
    assert counts["product-spec-critique"] == 1
    assert d["total_invocations"] == 5
    assert d["skills_used"] == 3


def test_never_used_is_catalog_minus_used(lens):
    d = lens.gather(days=BIG_DAYS, with_tokens=False, skills_dir=FIX / "skills")
    assert d["catalog_size"] == 4
    assert d["never_used"] == ["telemetry"]


def test_token_attribution_span_model(lens):
    d = lens.gather(days=BIG_DAYS, with_tokens=True, skills_dir=FIX / "skills")
    tokens = {r["skill"]: r["tokens"] for r in d["rows"]}
    # product-spec span: (100+50)+(200+100)=450 ; release span: (80+20)+(40+10)=150
    assert tokens["product-spec"] == 450
    assert tokens["release"] == 150
    assert tokens["product-spec-critique"] == 0


def test_never_used_is_owned_only_external_counted_separately(lens, tmp_path):
    # Catalog = the 4 owned cleanmatic skills + 1 vendored external (ck:plan).
    sk = tmp_path / "skills"
    for s, name in [("product-spec", "cleanmatic:product-spec"),
                    ("product-spec-critique", "cleanmatic:product-spec-critique"),
                    ("release", "cleanmatic:release"),
                    ("telemetry", "cleanmatic:telemetry"),
                    ("ck-plan", "ck:plan")]:
        (sk / s).mkdir(parents=True)
        (sk / s / "SKILL.md").write_text(f"---\nname: {name}\n---\n")
    d = lens.gather(days=BIG_DAYS, with_tokens=False, skills_dir=sk)
    # owned never-used = telemetry only; ck-plan (external, unused) is NOT listed
    assert d["never_used"] == ["telemetry"]
    assert "ck-plan" not in d["never_used"]
    assert d["never_used_external_count"] == 1  # ck-plan
    assert d["owned_size"] == 4
    assert d["catalog_size"] == 5


def test_gate_not_triggered_at_five_invocations(lens):
    d = lens.gather(days=BIG_DAYS, with_tokens=False, skills_dir=FIX / "skills")
    assert d["gated"] is False  # total 5 == threshold → not gated


def test_below_window_yields_zero_and_gated(lens):
    d = lens.gather(days=0, with_tokens=False, skills_dir=FIX / "skills")
    assert d["total_invocations"] == 0
    assert d["gated"] is True
    assert sorted(d["never_used"]) == ["product-spec", "product-spec-critique", "release", "telemetry"]
