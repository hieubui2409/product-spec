"""Tests for critique_blob_cache.py — the two file-per-key stores (web-cache + TTL,
lens-findings cache). Accessed via the critique_cache facade re-exports."""

from critique_test_support import make_proj
import critique_cache as cc


# ---------------------------------------------------------------------------
# web-cache + TTL
# ---------------------------------------------------------------------------

def test_web_cache_put_then_get_within_ttl(tmp_path):
    proj = make_proj(tmp_path)
    url = "https://example.com/pricing"
    cc.put_cached(proj, url, "page text", now_iso="2026-06-03T00:00:00+00:00")
    got = cc.get_cached(proj, url, ttl_days=14, now_iso="2026-06-10T00:00:00+00:00")
    assert got == "page text"


def test_web_cache_expired_returns_none(tmp_path):
    proj = make_proj(tmp_path)
    url = "https://example.com/pricing"
    cc.put_cached(proj, url, "page text", now_iso="2026-06-03T00:00:00+00:00")
    got = cc.get_cached(proj, url, ttl_days=14, now_iso="2026-06-23T00:00:00+00:00")
    assert got is None


def test_web_cache_unknown_url_returns_none(tmp_path):
    proj = make_proj(tmp_path)
    assert cc.get_cached(proj, "https://nope.example", now_iso="2026-06-03T00:00:00+00:00") is None


def test_web_cache_url_hash_stable(tmp_path):
    url = "https://example.com/x"
    assert cc._url_hash(url) == cc._url_hash(url)
    assert len(cc._url_hash(url)) == 16
    assert cc._url_hash(url) != cc._url_hash("https://example.com/y")


# ---------------------------------------------------------------------------
# lens-findings cache
# ---------------------------------------------------------------------------

def _lens_array():
    return [
        {"lens": "product", "evidence": "PRD-AUTH:12", "critique": "neutral obs",
         "why_it_dies": "no value", "fix": "do X", "severity": "blocker",
         "source": "lens"},
        {"lens": "tech", "evidence": "PRD-AUTH-E1-S1:4", "critique": "untestable AC",
         "why_it_dies": "cannot verify", "fix": "add GWT", "severity": "major"},
    ]


def test_lens_cache_byte_faithful_round_trip(tmp_path):
    proj = make_proj(tmp_path)
    arr = _lens_array()
    h = cc._lens_findings_hash(arr)
    cc.put_lens_findings(proj, h, arr)
    got = cc.get_lens_findings(proj, h)
    assert got == arr  # full array verbatim — no field dropped


def test_lens_cache_hash_stable(tmp_path):
    arr = _lens_array()
    assert cc._lens_findings_hash(arr) == cc._lens_findings_hash(arr)
    assert len(cc._lens_findings_hash(arr)) == 16


def test_lens_cache_unknown_returns_none(tmp_path):
    proj = make_proj(tmp_path)
    assert cc.get_lens_findings(proj, "deadbeefdeadbeef") is None


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------

def test_byte_determinism_same_pinned_time(tmp_path):
    proj = make_proj(tmp_path)
    url = "https://example.com/det"
    cc.put_cached(proj, url, "content", now_iso="2026-06-03T00:00:00+00:00")
    first = (proj / "docs" / "product" / ".memory" / "web-cache"
             / f"{cc._url_hash(url)}.json").read_bytes()
    cc.put_cached(proj, url, "content", now_iso="2026-06-03T00:00:00+00:00")
    second = (proj / "docs" / "product" / ".memory" / "web-cache"
              / f"{cc._url_hash(url)}.json").read_bytes()
    assert first == second
