"""test_safety_check — HARD safety filter contracts."""

from __future__ import annotations

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
