"""manifest_on_disk_checks — filesystem existence and containment checks for manifest entries.

``validate_on_disk`` is the second pass of manifest validation: it verifies that
every slug and path referenced in the manifest actually exists on disk and that
its resolved real path stays within the expected category base directory.

The syntactic traversal check (``../../x``) happens earlier in manifest_validator;
this pass catches symlink-based escapes by resolving paths with pathlib and using
``relative_to()`` instead of string-prefix tests.
"""

from __future__ import annotations

from pathlib import Path

from manifest_constants import ManifestError  # type: ignore[import-not-found]
from manifest_path_guards import (  # type: ignore[import-not-found]
    match_hooks,
    resolve_extension,
)


def _as_list(value: object) -> list:
    """A list as-is, anything else as []. Prevents TypeError on malformed scalar categories."""
    return value if isinstance(value, list) else []


def validate_on_disk(
    manifest: dict, root: Path, shared_val: list, errors: list[str]
) -> None:
    """On-disk existence (case-sensitive) + resolve-within-base containment.

    pathlib's relative_to() is used instead of a string-prefix test so the
    check is separator-agnostic (avoids false E021 on Windows builders where
    Path.__str__ uses '\\').
    """
    claude_dir = root / ".claude"
    skills_base = (claude_dir / "skills").resolve()
    for slug in _as_list(manifest.get("skills")):
        if not isinstance(slug, str):
            continue
        skill_dir = claude_dir / "skills" / slug
        if not skill_dir.is_dir():
            errors.append(f"[MANIFEST_E070] missing skill: {slug}")
        else:
            try:
                resolved_skill = skill_dir.resolve()
                resolved_skill.relative_to(skills_base)
            except ValueError:
                errors.append(
                    f"[MANIFEST_E021] skill path escapes skills base: {slug!r}"
                )
            except OSError:
                pass  # broken symlink; E070 will catch missing dir

    for slug in _as_list(manifest.get("agents")):
        if isinstance(slug, str):
            try:
                resolved_agent = resolve_extension(slug, claude_dir / "agents", "agents")
                try:
                    agents_base = (claude_dir / "agents").resolve()
                    resolved_agent.resolve().relative_to(agents_base)
                except ValueError:
                    errors.append(f"[MANIFEST_E021] agent path escapes agents base: {slug!r}")
                except OSError:
                    pass
            except ManifestError as e:
                errors.append(f"[MANIFEST_E071] {e}")

    for slug in _as_list(manifest.get("rules")):
        if isinstance(slug, str):
            try:
                resolved_rule = resolve_extension(slug, claude_dir / "rules", "rules")
                try:
                    rules_base = (claude_dir / "rules").resolve()
                    resolved_rule.resolve().relative_to(rules_base)
                except ValueError:
                    errors.append(f"[MANIFEST_E021] rule path escapes rules base: {slug!r}")
                except OSError:
                    pass
            except ManifestError as e:
                errors.append(f"[MANIFEST_E072] {e}")

    for slug in _as_list(manifest.get("hooks")):
        if isinstance(slug, str):
            # Must match a FILE (a slug naming a directory would pass a bare
            # rglob existence test yet bundle nothing). >1 match is ambiguous:
            # rglob order is filesystem-dependent, so picking one silently would
            # make the tarball non-deterministic across machines. Use the SHARED
            # matcher so this gate and selection.resolve_selection agree on which
            # file(s) a name resolves to (a name that validates here is the same
            # set that gets bundled).
            hook_matches = match_hooks(claude_dir, slug)
            if not hook_matches:
                errors.append(f"[MANIFEST_E073] missing hook: {slug}")
            elif len(hook_matches) > 1:
                errors.append(
                    f"[MANIFEST_E074] ambiguous hook: {slug} matches "
                    f"{len(hook_matches)} files; use a unique name or path"
                )
            else:
                # Containment check for hooks as well.
                try:
                    hooks_base = (claude_dir / "hooks").resolve()
                    hook_matches[0].resolve().relative_to(hooks_base)
                except ValueError:
                    errors.append(
                        f"[MANIFEST_E021] hook path escapes hooks base: {slug!r}"
                    )
                except OSError:
                    pass

    # _include_shared: verify each slug stays within .claude/skills/_shared/.
    # `shared_val` was already type-checked (E010) + coerced to a list by the
    # caller, so a hand-edited scalar can't char-split here.
    shared_base = (claude_dir / "skills" / "_shared").resolve()
    for slug in shared_val:
        if not isinstance(slug, str):
            continue
        shared_dir = claude_dir / "skills" / "_shared" / slug
        if shared_dir.exists():
            try:
                shared_dir.resolve().relative_to(shared_base)
            except ValueError:
                errors.append(
                    f"[MANIFEST_E021] _include_shared path escapes shared base: {slug!r}"
                )
            except OSError:
                pass
