"""test_safety_check — HARD safety filter contracts."""

from __future__ import annotations

import pytest

import safety_check


def test_drops_env_basename():
    """.env basename dropped."""
    assert safety_check.is_dropped(".claude/.env")[0]
    assert safety_check.is_dropped(".env")[0]


def test_drops_pycache_deep():
    """__pycache__ deeply nested dropped."""
    dropped, rule = safety_check.is_dropped(".claude/skills/foo/scripts/__pycache__/bar.pyc")
    assert dropped
    assert "__pycache__" in rule


def test_allows_regular_file():
    """regular markdown stays."""
    assert not safety_check.is_dropped("docs/dev.md")[0]
    assert not safety_check.is_dropped(".claude/skills/foo/SKILL.md")[0]


def test_no_substring_false_positive():
    """.envfoo NOT dropped (no substring)."""
    assert not safety_check.is_dropped("legitimate/.envfoo")[0]


def test_drops_plans_dir():
    """Internal planning/reports must never ship to recipients."""
    dropped, rule = safety_check.is_dropped(".claude/skills/x/plans/reports/note.md")
    assert dropped
    assert "plans" in rule


def test_expanded_secrets_dropped():
    """expanded secrets list: keys, credentials, certs, tokens."""
    for path in (".envrc", "id_rsa", "id_ed25519", "id_ecdsa",
                 ".netrc", ".pgpass"):
        dropped, _ = safety_check.is_dropped(path)
        assert dropped, f"expected drop for exact basename: {path}"
    for path in ("foo/secrets.json", "bar/credentials.yaml",
                 "baz/cert.pem", "qux/key.key", "x/cacert.p12",
                 "y/keystore.jks", "z/legacy.kdbx",
                 "a/api-token.json", "b/my-secret.json"):
        dropped, _ = safety_check.is_dropped(path)
        assert dropped, f"expected drop for pattern: {path}"
    for path in ("foo/.env.production", "foo/.env-staging", "foo/.env_local"):
        dropped, _ = safety_check.is_dropped(path)
        assert dropped, f"expected .env.* pattern drop: {path}"


def test_top_level_secrets_dropped():
    """Top-level secrets (bare arcname, no slash) must drop — pattern globs are
    **/-prefixed so basename matching is required to catch them."""
    for path in ("deploy.pem", "prod-token.json", ".env.production",
                 "secrets.json", "config.key", "my.p12", "app.pfx",
                 "keystore.jks", "vault.kdbx", ".env-staging"):
        dropped, _ = safety_check.is_dropped(path)
        assert dropped, f"top-level secret LEAKED: {path}"
    # No false positives on lookalike basenames.
    for path in ("tokenizer.md", "keymap.md", "README.md", ".envfoo"):
        dropped, _ = safety_check.is_dropped(path)
        assert not dropped, f"false positive on: {path}"


def test_git_directory_drop():
    """.git/ dropped at any depth."""
    for path in (".git/HEAD", "foo/.git/objects/pack/foo.pack",
                 ".gitlab/ci.yml", "x/.hg/store"):
        dropped, rule = safety_check.is_dropped(path)
        assert dropped, f"VCS not dropped: {path}"
        assert "dir:" in rule


def test_hard_safety_overrides_listing():
    """even if a path is in `extra`, safety drops it (filter is hard)."""
    dropped, _ = safety_check.is_dropped("extra/path/.env")
    assert dropped


def test_optional_paths():
    """settings.json + .ck.json are opt-in."""
    opt, label = safety_check.is_optional(".claude/settings.json")
    assert opt and label == "settings"
    opt, label = safety_check.is_optional(".claude/.ck.json")
    assert opt and label == "ck-config"
    opt, label = safety_check.is_optional("random/file.json")
    assert not opt


@pytest.mark.bug_class  # cross-skill invariant: case-insensitive secret drop
def test_case_insensitive_exact_drops():
    """Uppercase / mixed-case exact basenames must drop (.ENV, ID_RSA, etc.)."""
    for path in (".ENV", ".Env", "some/.ENV", "ID_RSA", "ID_Ed25519", ".NETRC", ".Pgpass"):
        dropped, rule = safety_check.is_dropped(path)
        assert dropped, f"case-insensitive exact drop missed: {path}"
        assert rule is not None and "always-drop:exact:" in rule


def test_case_insensitive_dir_drops():
    """Uppercase / mixed-case directory components must drop (.GIT, __PYCACHE__, .Venv)."""
    for path in (".GIT/config", "foo/.GIT/objects/HEAD", "__PYCACHE__/foo.pyc",
                 ".VENV/bin/python", "NODE_MODULES/pkg/index.js"):
        dropped, rule = safety_check.is_dropped(path)
        assert dropped, f"case-insensitive dir drop missed: {path}"
        assert rule is not None and "always-drop:dir:" in rule


def test_case_insensitive_pattern_drops():
    """Uppercase / mixed-case extension patterns must drop (deploy.PEM, .ENV, ID_RSA path)."""
    for path in ("deploy.PEM", "path/to/DEPLOY.PEM", "server.KEY", "bundle.P12",
                 "SECRETS.json", "CREDENTIALS.yaml", ".ENV.PRODUCTION",
                 "infra/id_rsa.PUB"):
        dropped, rule = safety_check.is_dropped(path)
        assert dropped, f"case-insensitive pattern drop missed: {path}"


def test_traversal_path_dropped():
    """Paths containing '..' must be unconditionally dropped (tar-slip defense)."""
    for path in ("a/../b", "../etc/passwd", "../../secret", ".claude/../.env",
                 "skills/foo/../../bar"):
        dropped, rule = safety_check.is_dropped(path)
        assert dropped, f"traversal path not dropped: {path!r}"
        assert rule == "always-drop:traversal", f"wrong rule for {path!r}: {rule!r}"


def test_absolute_path_dropped():
    """Absolute paths must be unconditionally dropped."""
    for path in ("/etc/passwd", "\\Windows\\system32", "C:/foo"):
        dropped, rule = safety_check.is_dropped(path)
        assert dropped, f"absolute path not dropped: {path!r}"
        assert rule == "always-drop:traversal"


def test_find_shared_refs_strips_code_blocks(tmp_path):
    """regex skips refs inside fenced code blocks."""
    skill = tmp_path / "demo"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "# demo\n"
        "We use _shared/foo for one thing.\n"
        "\n```bash\n# unrelated _shared/bar example only in docs\n```\n",
        encoding="utf-8",
    )
    refs = safety_check.find_shared_refs([skill])
    names = {name for name, _ in refs}
    assert "foo" in names
    assert "bar" not in names


# ---------------------------------------------------------------------------
# Cycle-10 regression tests
# ---------------------------------------------------------------------------

def test_backslash_traversal_dropped():
    """Backslash-encoded traversal 'a\\..\\b' must be dropped (C10 fix)."""
    dropped, rule = safety_check.is_dropped("a\\..\\b")
    assert dropped, "backslash-encoded traversal not dropped"
    assert rule == "always-drop:traversal"


def test_drive_letter_check_does_not_over_drop_posix_colon():
    """POSIX arcname 'a:b' (colon at index 1, no separator follows) must NOT drop.

    The old check was `len(path)>=2 and path[1]==':'` which would falsely drop
    a POSIX path like 'a:b' that happens to have a colon at position 1.
    The fixed check requires the next char to be '/', '\\', or end-of-string.
    """
    dropped, _ = safety_check.is_dropped("a:b")
    assert not dropped, "POSIX path 'a:b' must not be dropped as a drive-letter path"


def test_windows_drive_letter_still_dropped():
    """Windows drive-letter absolute paths (C:/ or C:\\) must still drop."""
    for path in ("C:/foo/bar", "C:\\foo", "D:/"):
        dropped, rule = safety_check.is_dropped(path)
        assert dropped, f"Windows drive path not dropped: {path!r}"
        assert rule == "always-drop:traversal"
