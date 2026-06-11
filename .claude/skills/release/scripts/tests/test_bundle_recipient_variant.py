"""test_bundle_recipient_variant — bundle must not ship dev-kit content to recipients.

Verifies:
1. `release` skill is NOT in the shipped bundle.
2. Dev workflow rules are NOT shipped.
3. Shipped top-level README.md/CLAUDE.md come from the recipient-variant source
   (contain a recipient marker) and the recipient CLAUDE.md does not contain
   `release` or `/ck:` references.
4. The release-check guard: a manifest whose `rules:` references a skill NOT in
   `skills:` must fail validation (cross-reference guard).
5. `top_level.source` key is accepted by the validator (no MANIFEST_E031 error).
6. `rules:` can be empty/absent without a validator error.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[5]
MANIFEST_PATH = REPO_ROOT / ".claude" / "pack.manifest.yaml"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_real_manifest() -> dict:
    import manifest_loader  # type: ignore[import-not-found]
    return manifest_loader.load(MANIFEST_PATH)


def _resolve(manifest: dict) -> set[str]:
    from pack.selection import resolve_selection  # type: ignore[import-not-found]
    return {arc for _, arc in resolve_selection(manifest, REPO_ROOT)}


# ---------------------------------------------------------------------------
# Recipient bundle must NOT ship the `release` dev/redistribution skill
# ---------------------------------------------------------------------------

@pytest.mark.bug_class
def test_release_skill_not_in_manifest_skills():
    """The `release` skill must be absent from the manifest `skills:` list.

    Recipients are end-users — they receive the product-spec harness, not the
    re-distribution toolchain.
    """
    manifest = _load_real_manifest()
    assert "release" not in manifest.get("skills", []), \
        "manifest `skills:` must not list `release` — recipients don't need it"


@pytest.mark.bug_class
def test_release_skill_not_in_bundle_file_set():
    """No .claude/skills/release/... file must appear in the resolved bundle."""
    manifest = _load_real_manifest()
    arcs = _resolve(manifest)
    release_files = [a for a in arcs if a.startswith(".claude/skills/release/")]
    assert not release_files, (
        f"release skill files leaked into bundle: {release_files[:5]}"
    )


# ---------------------------------------------------------------------------
# Recipient bundle must NOT ship dev workflow rules
# ---------------------------------------------------------------------------

DEV_RULES = [
    "primary-workflow.md",
    "development-rules.md",
    "orchestration-protocol.md",
    "documentation-management.md",
    "review-audit-self-decision.md",
]


@pytest.mark.bug_class
def test_contributing_md_not_in_bundle():
    """CONTRIBUTING.md is dev-kit content (DCO, PR flow, internal test setup) and
    must NOT ship to recipients; only LICENSE travels per AGPL-3.0."""
    manifest = _load_real_manifest()
    assert "CONTRIBUTING.md" not in (manifest.get("extra", []) or []), (
        "CONTRIBUTING.md must not be in manifest `extra:` — it is dev-only"
    )
    arcs = _resolve(manifest)
    assert "CONTRIBUTING.md" not in arcs, "CONTRIBUTING.md leaked into the bundle"


@pytest.mark.bug_class
def test_dev_rules_absent_from_manifest():
    """No dev workflow rule may appear in manifest `rules:`."""
    manifest = _load_real_manifest()
    rules = manifest.get("rules", []) or []
    shipped = [r for r in DEV_RULES if r in rules]
    assert not shipped, (
        f"dev workflow rules still in manifest `rules:`: {shipped}. "
        "Recipients must not receive dev-kit rules."
    )


@pytest.mark.bug_class
def test_dev_rules_absent_from_bundle_file_set():
    """No dev workflow rule file may appear in the resolved bundle arcname set."""
    manifest = _load_real_manifest()
    arcs = _resolve(manifest)
    leaked = [a for a in arcs if any(r in a for r in DEV_RULES)]
    assert not leaked, f"dev rules leaked into bundle: {leaked}"


@pytest.mark.bug_class
def test_empty_rules_list_validates_clean():
    """Manifest with an empty (or absent) `rules:` list must pass validation without errors."""
    import manifest_loader  # type: ignore[import-not-found]
    from manifest_validator import validate  # type: ignore[import-not-found]

    # Minimal manifest — no rules key at all.
    no_rules = {
        "schema_version": "1.0",
        "version": "1.0.0",
        "bundle_name": "test-bundle",
        "skills": [],
    }
    errors = validate(no_rules, REPO_ROOT, allow_dev_version=False)
    rule_errors = [e for e in errors if "rules" in e.lower()]
    assert not rule_errors, f"empty rules caused validation errors: {rule_errors}"

    # Explicit empty list.
    empty_rules = {**no_rules, "rules": []}
    errors2 = validate(empty_rules, REPO_ROOT, allow_dev_version=False)
    rule_errors2 = [e for e in errors2 if "rules" in e.lower()]
    assert not rule_errors2, f"empty rules list caused validation errors: {rule_errors2}"


# ---------------------------------------------------------------------------
# Recipient-variant top-level docs (README/CLAUDE.md) must ship, not dev-repo root
# ---------------------------------------------------------------------------

# A deliberate marker string embedded in the recipient README.md / CLAUDE.md
# that distinguishes them from the dev-repo root files.
RECIPIENT_README_MARKER = "<!-- recipient-variant -->"
RECIPIENT_CLAUDE_MARKER = "<!-- recipient-variant -->"


@pytest.mark.bug_class
def test_top_level_source_key_accepted_by_validator():
    """The manifest key `top_level.source` must be accepted by the validator (no E031 error)."""
    import manifest_loader  # type: ignore[import-not-found]
    from manifest_validator import validate  # type: ignore[import-not-found]

    manifest = {
        "schema_version": "1.0",
        "version": "1.0.0",
        "bundle_name": "test-bundle",
        "skills": [],
        "top_level": {
            "include_readme": True,
            "include_claudemd": True,
            "source": ".claude/skills/release/assets/recipient",
        },
    }
    errors = validate(manifest, REPO_ROOT, allow_dev_version=False)
    unknown_key_errors = [e for e in errors if "MANIFEST_E031" in e]
    assert not unknown_key_errors, (
        f"top_level.source was rejected by validator: {unknown_key_errors}"
    )


@pytest.mark.bug_class
def test_shipped_readme_is_recipient_variant():
    """The shipped README.md must come from the recipient-variant source directory,
    not from the dev repo root."""
    manifest = _load_real_manifest()
    arcs_and_srcs = {
        arc: src
        for src, arc in resolve_selection_with_src(manifest)
    }
    assert "README.md" in arcs_and_srcs, "README.md not found in bundle"
    src_path = arcs_and_srcs["README.md"]
    content = src_path.read_text(encoding="utf-8")
    assert RECIPIENT_README_MARKER in content, (
        f"Shipped README.md ({src_path}) does not contain recipient marker "
        f"{RECIPIENT_README_MARKER!r}. It appears to be the dev-repo root README."
    )


@pytest.mark.bug_class
def test_shipped_claudemd_is_recipient_variant():
    """The shipped CLAUDE.md must come from the recipient-variant source, not the dev repo root."""
    manifest = _load_real_manifest()
    arcs_and_srcs = {
        arc: src
        for src, arc in resolve_selection_with_src(manifest)
    }
    assert "CLAUDE.md" in arcs_and_srcs, "CLAUDE.md not found in bundle"
    src_path = arcs_and_srcs["CLAUDE.md"]
    content = src_path.read_text(encoding="utf-8")
    assert RECIPIENT_CLAUDE_MARKER in content, (
        f"Shipped CLAUDE.md ({src_path}) does not contain recipient marker "
        f"{RECIPIENT_CLAUDE_MARKER!r}. It appears to be the dev-repo root CLAUDE.md."
    )


@pytest.mark.bug_class
def test_recipient_claudemd_no_release_or_ck_refs():
    """Recipient CLAUDE.md must not reference the `release` skill or `/ck:` commands."""
    manifest = _load_real_manifest()
    arcs_and_srcs = {
        arc: src
        for src, arc in resolve_selection_with_src(manifest)
    }
    if "CLAUDE.md" not in arcs_and_srcs:
        pytest.skip("CLAUDE.md not in bundle — skipping content check")
    content = arcs_and_srcs["CLAUDE.md"].read_text(encoding="utf-8")
    assert "release" not in content, \
        "Recipient CLAUDE.md references `release` (dev-only skill); drop it"
    assert "/ck:" not in content, \
        "Recipient CLAUDE.md references `/ck:` (dev-only commands); drop them"


def resolve_selection_with_src(manifest: dict):
    """Return (src_path, arcname) pairs from the real manifest."""
    from pack.selection import resolve_selection  # type: ignore[import-not-found]
    return resolve_selection(manifest, REPO_ROOT)


# ---------------------------------------------------------------------------
# Release-check guard: dangling skill references in shipped rules
# ---------------------------------------------------------------------------

@pytest.mark.bug_class
def test_release_check_guard_fails_on_dangling_rule_skill_ref(tmp_path):
    """A manifest whose shipped rule file references a skill NOT in `skills:`
    must fail the release-check guard.

    Detection heuristic: scan rule file text for `/<skill>:` patterns and
    confirm every referenced skill slug appears in `skills:`.
    """
    from release_check_guard import check_rule_skill_refs  # type: ignore[import-not-found]

    # Create a synthetic rule file that references a non-bundled skill.
    rules_dir = tmp_path / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    rule_file = rules_dir / "my-rule.md"
    rule_file.write_text(
        "# My Rule\n\nUse the /non-bundled-skill:do-thing command.\n",
        encoding="utf-8",
    )

    # Synthetic manifest: ships the rule but NOT the skill it references.
    manifest = {
        "skills": ["product-spec"],    # non-bundled-skill is NOT here
        "rules": ["my-rule.md"],
    }

    errors = check_rule_skill_refs(manifest, tmp_path)
    assert errors, (
        "release-check guard did not flag a rule that references a non-bundled skill"
    )
    assert any("non-bundled-skill" in e for e in errors), (
        f"error message does not name the dangling skill: {errors}"
    )


@pytest.mark.bug_class
def test_release_check_guard_passes_on_empty_rules():
    """release-check guard must pass when `rules:` is empty."""
    from release_check_guard import check_rule_skill_refs  # type: ignore[import-not-found]

    manifest = {"skills": ["product-spec"], "rules": []}
    errors = check_rule_skill_refs(manifest, REPO_ROOT)
    assert not errors, f"empty rules triggered false-positive guard errors: {errors}"


@pytest.mark.bug_class
def test_release_check_guard_passes_on_real_manifest():
    """release-check guard must pass cleanly on the real (post-fix) manifest."""
    from release_check_guard import check_rule_skill_refs  # type: ignore[import-not-found]

    manifest = _load_real_manifest()
    errors = check_rule_skill_refs(manifest, REPO_ROOT)
    assert not errors, (
        f"release-check guard failed on real manifest: {errors}"
    )


@pytest.mark.bug_class
def test_pack_build_aborts_on_dangling_rule_skill_ref(tmp_path, capsys):
    """The guard must actually gate the build: invoking the pack pipeline on a
    manifest whose shipped rule references a non-bundled skill must abort with the
    validation exit code and name the dangling skill on stderr.

    This is the wiring regression — a unit-clean guard that is never called from
    cli would let a dangling reference ship silently.
    """
    from pack.cli import main  # type: ignore[import-not-found]

    rules_dir = tmp_path / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "danger.md").write_text(
        "# Danger\n\nUse the /ghost-skill:run command.\n", encoding="utf-8"
    )

    manifest_path = tmp_path / "m.yaml"
    manifest_path.write_text(
        "schema_version: '1.0'\n"
        "version: 1.0.0\n"
        "bundle_name: test-bundle\n"
        "skills: []\n"
        "rules:\n"
        "- danger.md\n",
        encoding="utf-8",
    )

    rc = main(["--root", str(tmp_path), "--manifest", str(manifest_path), "--dry-run"])
    assert rc == 1, f"pack build did not abort on a dangling rule reference (rc={rc})"
    err = capsys.readouterr().err
    assert "ghost-skill" in err, (
        f"abort message does not name the dangling skill: {err!r}"
    )
