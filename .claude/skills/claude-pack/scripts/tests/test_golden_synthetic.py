"""test_golden_synthetic — synthetic fixture pack tree (BLOCKING unit golden).

Pack a deterministic synthetic skill, extract, compare the file set.
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

from pack.manifest_io import build_manifest_json
from pack.selection import render_embedded, resolve_selection
from pack.tarball import build_tarball


SKILL_ROOT = Path(__file__).resolve().parent.parent.parent

EXPECTED_FILES = frozenset({
    "sample-pack-0.1.0/INSTALL.md",
    "sample-pack-0.1.0/MANIFEST.json",
    "sample-pack-0.1.0/install.ps1",
    "sample-pack-0.1.0/install.sh",
    "sample-pack-0.1.0/.claude/skills/sample-skill/SKILL.md",
    "sample-pack-0.1.0/.claude/skills/sample-skill/scripts/helper.py",
    "sample-pack-0.1.0/.claude/skills/sample-skill/references/spec.md",
})


def test_synthetic_golden_pack(tmp_root):
    """synthetic skill produces the expected file set."""
    manifest = {
        "schema_version": "1.0",
        "version": "0.1.0",
        "bundle_name": "sample-pack",
        "skills": ["sample-skill"],
        "agents": [],
        "hooks": [],
        "rules": [],
        "extra": [],
        "top_level": {"include_readme": False, "include_claudemd": False,
                      "include_settings": False, "include_ck_config": False},
        "defaults": {"include_scripts": False, "include_schemas": False},
        "follow_shared": False,
    }
    selection = resolve_selection(manifest, tmp_root)
    bundle_root = "sample-pack-0.1.0"
    versioned = [(src, f"{bundle_root}/{arc}") for src, arc in selection]
    versioned.sort(key=lambda x: x[1].encode("utf-8"))
    manifest_json = build_manifest_json(versioned, manifest,
                                        source_date_epoch=0, repo_root=tmp_root)
    parsed = json.loads(manifest_json)
    tokens = {
        "BUNDLE_NAME": "sample-pack",
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
        actual = set(tar.getnames())

    assert actual == EXPECTED_FILES, \
        f"\nMissing: {EXPECTED_FILES - actual}\nExtra: {actual - EXPECTED_FILES}"
