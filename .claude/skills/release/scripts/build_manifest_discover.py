"""build_manifest_discover — filesystem scanner that enumerates available items under .claude/.

``discover(root)`` is the first step of the interactive manifest-builder flow: it
catalogs which skills, agents, hooks, and rules exist on disk so the question bank
(build_manifest_questions) can offer only valid options. Running at interview time
guarantees options stay current without a separate sync step.
"""

from __future__ import annotations

from pathlib import Path


def discover(root: Path) -> dict:
    """Enumerate available items under ``.claude/``."""
    claude = root / ".claude"
    skills_dir = claude / "skills"
    agents_dir = claude / "agents"
    rules_dir = claude / "rules"
    hooks_dir = claude / "hooks"

    available_skills: list[str] = []
    if skills_dir.is_dir():
        for entry in sorted(skills_dir.iterdir()):
            if (entry.is_dir() and entry.name not in {"_shared", ".venv"}
                    and (entry / "SKILL.md").is_file()):
                available_skills.append(entry.name)

    def _basenames(directory: Path, suffix: str) -> list[str]:
        """Return stem names that are unambiguous (1:1 stem → file).

        Stems that map to more than one file (same stem, different directories)
        are excluded because ``manifest_loader._resolve_extension`` would be
        ambiguous on them — including them as options would produce MANIFEST_E071/
        E072 collisions at validate time.
        """
        if not directory.is_dir():
            return []
        stem_to_paths: dict[str, list[str]] = {}
        for p in directory.rglob(f"*{suffix}"):
            if p.is_file():
                stem_to_paths.setdefault(p.stem, []).append(str(p))
        # Only offer stems that have exactly one backing file.
        return sorted(stem for stem, paths in stem_to_paths.items() if len(paths) == 1)

    def _filenames(directory: Path) -> list[str]:
        """Return relative posix paths for all files under directory (recursive).

        Hooks may live in subdirectories; using rglob here aligns with
        ``manifest_loader.match_hooks`` which also recurses, so offered options
        match what validates and ships.
        """
        if not directory.is_dir():
            return []
        base = directory
        return sorted(
            p.relative_to(base).as_posix()
            for p in directory.rglob("*")
            if p.is_file()
        )

    return {
        "available_skills": available_skills,
        "available_agents": _basenames(agents_dir, ".md"),
        "available_hooks": _filenames(hooks_dir),
        "available_rules": _basenames(rules_dir, ".md"),
        "has_readme": (root / "README.md").is_file(),
        "has_claudemd": (root / "CLAUDE.md").is_file(),
        "has_settings": (claude / "settings.json").is_file(),
        "has_ck_config": (claude / ".ck.json").is_file(),
    }
