"""selection — manifest -> ``[(src_path, arcname), ...]`` resolver.

Pulled out of ``cli.py`` to keep cli.py under the 200-LOC budget.
File-granular sorted walk: never call ``tar.add(dir)``, always per-file
(src, arcname) tuples sorted by ``arcname.encode("utf-8")``.
"""

from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath

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
        # Strip slashes so a trailing-slash `extra` entry (e.g. "docs/") can't
        # compose a "docs//file" double-slash arcname that diverges from "docs".
        arc_prefix = arc_prefix.strip("/")
        for f in src_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(src_dir).as_posix()
                entries.append((f, f"{arc_prefix}/{rel}".lstrip("/")))

    for slug in manifest.get("skills", []):
        _walk_dir(claude_dir / "skills" / slug, f".claude/skills/{slug}")
    shared = manifest.get("_include_shared") or []
    if isinstance(shared, str):  # tolerate a hand-edited scalar instead of a list
        shared = [s.strip() for s in shared.split(",") if s.strip()]
    elif not isinstance(shared, list):  # a malformed scalar (int/dict) is not iterable
        shared = []
    for slug in shared:
        _walk_dir(claude_dir / "skills" / "_shared" / slug,
                  f".claude/skills/_shared/{slug}")

    # agents + rules resolve identically (only the category differs) — one loop.
    for category in ("agents", "rules"):
        for slug in manifest.get(category, []):
            try:
                resolved = manifest_loader._resolve_extension(
                    slug, claude_dir / category, category)
            except manifest_loader.ManifestError:
                continue
            rel = resolved.relative_to(claude_dir).as_posix()
            entries.append((resolved, f".claude/{rel}"))

    for name in manifest.get("hooks", []):
        # Use the SHARED matcher (rglob) so a hook name that passed validate() —
        # incl. a path-qualified `a/foo.cjs` or a glob `*.sh` — resolves to the SAME
        # file(s) here and actually gets bundled. validate() rejects the >1-match
        # (ambiguous) case before we get here, so the sorted pick is deterministic.
        matches = manifest_loader.match_hooks(claude_dir, name)
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
    # When `top_level.source` is set, ship README.md/CLAUDE.md from that directory
    # (recipient-variant copies) instead of the repo root (dev-kit copies).
    # Falls back to repo root when the source dir or file is absent — back-compat.
    _top_src_str = top.get("source", "")
    _top_src_dir: Path | None = (root / _top_src_str) if _top_src_str else None
    def _top_file(filename: str) -> Path:
        """Return the best available source for a top-level file."""
        if _top_src_dir is not None:
            candidate = _top_src_dir / filename
            if candidate.is_file():
                return candidate
        return root / filename

    if top.get("include_readme"):
        readme_src = _top_file("README.md")
        if readme_src.is_file():
            entries.append((readme_src, "README.md"))
    if top.get("include_claudemd"):
        claudemd_src = _top_file("CLAUDE.md")
        if claudemd_src.is_file():
            entries.append((claudemd_src, "CLAUDE.md"))
    if top.get("include_settings") and (claude_dir / "settings.json").is_file():
        entries.append((claude_dir / "settings.json", ".claude/settings.json"))
    if top.get("include_ck_config") and (claude_dir / ".ck.json").is_file():
        entries.append((claude_dir / ".ck.json", ".claude/.ck.json"))

    root_resolved = root.resolve()

    safe: list[tuple[Path, str]] = []
    for src, arc in entries:
        # Belt-and-suspenders chokepoint: reject any arcname that would cause
        # tar-slip (path traversal or absolute), regardless of which category
        # produced it.  manifest_loader.validate() enforces the same rule on
        # manifest inputs; this layer catches any category added in the future.
        arc_pure = PurePosixPath(arc)
        if ".." in arc_pure.parts or arc_pure.is_absolute():
            sys.stderr.write(
                f"WARN: rejected arcname with traversal/absolute: {arc!r} (src: {src})\n"
            )
            continue
        # Also verify the resolved source path stays within the repo root to
        # guard against symlink-based escapes.  Use relative_to() instead of a
        # string-prefix test so the check is separator-agnostic (avoids false
        # positives on Windows builders where Path.__str__ uses '\\').
        try:
            src_resolved = src.resolve()
            src_resolved.relative_to(root_resolved)
        except ValueError:
            sys.stderr.write(
                f"WARN: rejected src escaping repo root: {src} (arcname: {arc!r})\n"
            )
            continue
        except OSError:
            pass  # broken symlink: let tarball's is_dropped/missing-file paths handle it

        dropped, _ = safety_check.is_dropped(arc)
        if not dropped:
            safe.append((src, arc))

    # Sort by (arcname-bytes, src-string) BEFORE the dedup loop so the collision
    # survivor is path-deterministic (independent of rglob/iteration order).
    safe.sort(key=lambda x: (x[1].encode("utf-8"), str(x[0])))

    seen: dict[str, Path] = {}
    unique: list[tuple[Path, str]] = []
    for src, arc in safe:
        if arc in seen:
            # Two DIFFERENT sources resolving to one arcname (e.g. overlapping
            # `extra` paths): keep the first, but never drop SILENTLY — the
            # recipient would be missing content with no signal. Same src twice
            # is a harmless true-duplicate (no warn).
            if seen[arc] != src:
                sys.stderr.write(
                    f"WARN: arcname collision {arc!r}: keeping {seen[arc]}, "
                    f"dropping {src}\n"
                )
            continue
        seen[arc] = src
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
    """Render installer/upgrade templates and embed verbatim upgrade payload.

    Returns sorted (arcname, bytes) list. _upgrade/ files are verbatim copies
    (no token substitution) so shipped Python modules are byte-identical to tested source.
    """
    t = skill_root / "assets" / "templates"
    u = skill_root / "assets" / "upgrade"
    s = skill_root / "scripts"
    r = bundle_root_dir
    embedded = [
        (f"{r}/MANIFEST.json",                    manifest_json),
        (f"{r}/INSTALL.md",                        render_template(t / "INSTALL.md.template", tokens)),
        (f"{r}/install.sh",                        render_template(t / "install.sh.template", tokens)),
        (f"{r}/install.ps1",                       render_template(t / "install.ps1.template", tokens)),
        (f"{r}/upgrade.sh",                        render_template(t / "upgrade.sh.template", tokens)),
        (f"{r}/upgrade.ps1",                       render_template(t / "upgrade.ps1.template", tokens)),
        (f"{r}/_upgrade/upgrade_planner.py",       (s / "upgrade_planner.py").read_bytes()),
        (f"{r}/_upgrade/upgrade_apply.py",         (s / "upgrade_apply.py").read_bytes()),
        (f"{r}/_upgrade/legacy-map.json",          (u / "legacy-map.json").read_bytes()),
    ]
    embedded.sort(key=lambda x: x[0].encode("utf-8"))
    return embedded
