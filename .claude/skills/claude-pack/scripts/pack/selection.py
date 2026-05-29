"""selection — manifest -> ``[(src_path, arcname), ...]`` resolver.

Pulled out of ``cli.py`` to keep cli.py under the 200-LOC budget.
File-granular sorted walk: never call ``tar.add(dir)``, always per-file
(src, arcname) tuples sorted by ``arcname.encode("utf-8")``.
"""

from __future__ import annotations

from pathlib import Path

import manifest_loader  # type: ignore[import-not-found]
import safety_check  # type: ignore[import-not-found]

from .templates import render_template


def resolve_selection(manifest: dict, root: Path) -> list[tuple[Path, str]]:
    """Map manifest categories -> ``[(src_path, arcname), ...]`` (file-granular, sorted)."""
    claude_dir = root / ".claude"
    entries: list[tuple[Path, str]] = []

    def _walk_dir(src_dir: Path, arc_prefix: str) -> None:
        if not src_dir.is_dir():
            return
        for f in src_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(src_dir).as_posix()
                entries.append((f, f"{arc_prefix}/{rel}".lstrip("/")))

    for slug in manifest.get("skills", []):
        _walk_dir(claude_dir / "skills" / slug, f".claude/skills/{slug}")
    shared = manifest.get("_include_shared") or []
    if isinstance(shared, str):  # tolerate a hand-edited scalar instead of a list
        shared = [s.strip() for s in shared.split(",") if s.strip()]
    for slug in shared:
        _walk_dir(claude_dir / "skills" / "_shared" / slug,
                  f".claude/skills/_shared/{slug}")

    for slug in manifest.get("agents", []):
        try:
            resolved = manifest_loader._resolve_extension(
                slug, claude_dir / "agents", "agents")
        except manifest_loader.ManifestError:
            continue
        rel = resolved.relative_to(claude_dir).as_posix()
        entries.append((resolved, f".claude/{rel}"))

    for slug in manifest.get("rules", []):
        try:
            resolved = manifest_loader._resolve_extension(
                slug, claude_dir / "rules", "rules")
        except manifest_loader.ManifestError:
            continue
        rel = resolved.relative_to(claude_dir).as_posix()
        entries.append((resolved, f".claude/{rel}"))

    hook_names = manifest.get("hooks", [])
    if hook_names:
        # Walk hooks/ ONCE into a basename->paths index, then resolve each requested
        # name via lookup — instead of an rglob() full-tree scan per requested name
        # (O(hooks·tree)). Sorted pick stays deterministic across machines; validate()
        # rejects the >1-match (ambiguous) case before we get here.
        hooks_dir = claude_dir / "hooks"
        by_name: dict[str, list[Path]] = {}
        if hooks_dir.is_dir():
            for m in hooks_dir.rglob("*"):
                if m.is_file():
                    by_name.setdefault(m.name, []).append(m)
        for name in hook_names:
            matches = sorted(by_name.get(name, []), key=lambda m: m.as_posix())
            if matches:
                rel = matches[0].relative_to(claude_dir).as_posix()
                entries.append((matches[0], f".claude/{rel}"))

    for path_entry in manifest.get("extra", []):
        src = root / path_entry
        if src.is_dir():
            _walk_dir(src, path_entry)
        elif src.is_file():
            entries.append((src, path_entry))

    top = manifest.get("top_level") or {}
    if top.get("include_readme") and (root / "README.md").is_file():
        entries.append((root / "README.md", "README.md"))
    if top.get("include_claudemd") and (root / "CLAUDE.md").is_file():
        entries.append((root / "CLAUDE.md", "CLAUDE.md"))
    if top.get("include_settings") and (claude_dir / "settings.json").is_file():
        entries.append((claude_dir / "settings.json", ".claude/settings.json"))
    if top.get("include_ck_config") and (claude_dir / ".ck.json").is_file():
        entries.append((claude_dir / ".ck.json", ".claude/.ck.json"))

    safe: list[tuple[Path, str]] = []
    for src, arc in entries:
        dropped, _ = safety_check.is_dropped(arc)
        if not dropped:
            safe.append((src, arc))

    seen: set[str] = set()
    unique: list[tuple[Path, str]] = []
    for src, arc in safe:
        if arc in seen:
            continue
        seen.add(arc)
        unique.append((src, arc))
    unique.sort(key=lambda x: x[1].encode("utf-8"))
    return unique


def render_embedded(
    skill_root: Path,
    *,
    bundle_root_dir: str,
    manifest_json: bytes,
    tokens: dict[str, str],
) -> list[tuple[str, bytes]]:
    """Render INSTALL.md/install.sh/install.ps1 templates -> embedded payloads."""
    tmpl_dir = skill_root / "assets" / "templates"
    install_md = render_template(tmpl_dir / "INSTALL.md.template", tokens)
    install_sh = render_template(tmpl_dir / "install.sh.template", tokens)
    install_ps1 = render_template(tmpl_dir / "install.ps1.template", tokens)
    embedded = [
        (f"{bundle_root_dir}/MANIFEST.json", manifest_json),
        (f"{bundle_root_dir}/INSTALL.md", install_md),
        (f"{bundle_root_dir}/install.sh", install_sh),
        (f"{bundle_root_dir}/install.ps1", install_ps1),
    ]
    embedded.sort(key=lambda x: x[0].encode("utf-8"))
    return embedded
