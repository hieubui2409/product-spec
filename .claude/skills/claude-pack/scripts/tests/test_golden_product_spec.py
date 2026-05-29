"""test_golden_product_spec — live product-spec pack tree (integration).

Marker ``@pytest.mark.integration``. NOT in CI pre-merge gate.
Run locally via: ``pytest -m integration``.
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

import pytest

from pack.manifest_io import build_manifest_json
from pack.selection import render_embedded, resolve_selection
from pack.tarball import build_tarball


REPO_ROOT = Path(__file__).resolve().parents[5]
SKILL_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.integration
def test_pack_live_product_spec():
    """live product-spec packs to a non-empty tar with expected entries."""
    product_spec_dir = REPO_ROOT / ".claude" / "skills" / "product-spec"
    if not product_spec_dir.is_dir():
        pytest.skip("product-spec not present in this checkout")

    manifest = {
        "schema_version": "1.0",
        "version": "0.1.0",
        "bundle_name": "ps-pack",
        "skills": ["product-spec"],
        "agents": [],
        "hooks": [],
        "rules": [],
        "extra": [],
        "top_level": {"include_readme": False, "include_claudemd": False,
                      "include_settings": False, "include_ck_config": False},
        "defaults": {"include_scripts": False, "include_schemas": False},
        "follow_shared": False,
    }
    selection = resolve_selection(manifest, REPO_ROOT)
    assert selection, "product-spec selection empty"

    bundle_root = "ps-pack-0.1.0"
    versioned = [(src, f"{bundle_root}/{arc}") for src, arc in selection]
    versioned.sort(key=lambda x: x[1].encode("utf-8"))
    manifest_json = build_manifest_json(versioned, manifest,
                                        source_date_epoch=0, repo_root=REPO_ROOT)
    parsed = json.loads(manifest_json)
    tokens = {
        "BUNDLE_NAME": "ps-pack",
        "VERSION": "0.1.0", "BUILT_AT": parsed.get("built_at", ""),
        "SOURCE_COMMIT": "test", "FILE_COUNT": str(len(selection)),
        "TOTAL_SIZE": "x bytes",
    }
    embedded = render_embedded(SKILL_ROOT, bundle_root_dir=bundle_root,
                               manifest_json=manifest_json, tokens=tokens)

    buf = io.BytesIO()
    build_tarball(versioned, embedded, buf, source_date_epoch=0)
    buf.seek(0)
    with tarfile.open(fileobj=buf, mode="r:gz") as tar:
        names = set(tar.getnames())
    assert f"{bundle_root}/MANIFEST.json" in names
    assert f"{bundle_root}/INSTALL.md" in names
    assert any("product-spec/SKILL.md" in n for n in names)
    # No secrets / runtime state
    for n in names:
        assert not n.endswith("/.env"), f"secret leaked: {n}"
        assert "/.git/" not in n, f".git leaked: {n}"
        assert "/__pycache__/" not in n, f"pycache leaked: {n}"
        assert "/.venv/" not in n, f".venv leaked: {n}"
