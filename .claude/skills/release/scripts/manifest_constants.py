"""manifest_constants — shared schema constants and error class for the manifest pipeline.

All regex patterns, allowed-key sets, and the ManifestError exception live here so that
manifest_loader, manifest_path_guards, and manifest_validator can import them from a
single leaf module without creating import cycles.
"""

from __future__ import annotations

import re

DEFAULT_SCHEMA_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})

SEMVER_RE = re.compile(
    r"^(?:(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?|0\.0\.0-dev)$"
)
BUNDLE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")

ALLOWED_TOP_LEVEL_KEYS = frozenset({
    "schema_version", "version", "bundle_name",
    "skills", "agents", "hooks", "rules", "extra",
    "top_level", "defaults", "follow_shared",
})

ALLOWED_NESTED_TOP_LEVEL_KEYS = frozenset({
    "include_readme", "include_claudemd",
    "include_settings", "include_ck_config",
    "source",  # optional path (relative to repo root) to recipient-variant README.md/CLAUDE.md
})

# Opt-in flags that set defaults.include_scripts / defaults.include_schemas to True
# when passed on the CLI. Absent from manifest ⇒ False (top-level .claude/scripts and
# .claude/schemas are CK-framework internals, not skill content; skill scripts live
# under skills/<x>/scripts/).
OPT_IN_DEFAULTS_FLAGS = frozenset({"include_scripts", "include_schemas"})

ALLOWED_DEFAULTS_KEYS = frozenset({
    "include_scripts", "include_schemas", "max_size_bytes",
})

LIST_CATEGORIES = ("skills", "agents", "hooks", "rules", "extra")


class ManifestError(Exception):
    """Raised on parse failure or validation error.

    Carries ``file:line:col`` when available (yaml parse errors).
    """
