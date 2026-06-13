#!/usr/bin/env python3
"""release — manage the Keep a Changelog lifecycle of the root CHANGELOG.md.

The root CHANGELOG.md is the hand/LLM-maintained truth of record: an ``## [Unreleased]`` section on top
plus locked ``## [X.Y.Z] — <date>`` sections below. This tool performs the deterministic release-cut
transforms; it NEVER auto-derives content from git, so the committed file is reproducible and is only
ever changed by an explicit, recorded release action.

  --extract X.Y.Z              print the body of the [X.Y.Z] section (used as the GitHub Release body)
  --release X.Y.Z              cut a release at an explicit version
  --bump {patch,minor,major}   cut a release at the next version computed from the manifest
  --pre-release LABEL          append a pre-release label to the cut version (rc.1 → X.Y.Z-rc.1)
  --date YYYY-MM-DD            override the release date (default: today)

A release-cut locks ``[Unreleased]`` → ``[X.Y.Z] — <date>``, opens a fresh empty ``[Unreleased]``, and
bumps ``.claude/pack.manifest.yaml``. Dry-run by default — pass ``--apply`` to write. ``--push`` (owner
opt-in, requires ``--apply``) also creates and pushes the ``product-spec-v<ver>`` tag, firing the release
CI; without it the exact git commands are printed for the owner to run.

The actual tarball is built by the release CI from the bumped manifest (``python -m pack``); this tool
only owns the changelog + version lifecycle, not the build.
"""
import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

# scripts → release → skills → .claude → repo
REPO = Path(__file__).resolve().parents[4]
CHANGELOG = REPO / "CHANGELOG.md"
MANIFEST = REPO / ".claude" / "pack.manifest.yaml"

TAG_PREFIX = "product-spec-v"

# Section heading: "## [Unreleased]" or "## [1.2.3] — 2026-06-07" (dash or em-dash separator).
_HEADING = re.compile(r"^## \[([^\]]+)\]", re.M)


def _today() -> str:
    return datetime.date.today().isoformat()


def extract_section(text: str, version: str) -> str:
    """Body of the ``## [version]`` section (heading excluded), up to the next ``## [`` heading."""
    out, capturing = [], False
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            if capturing:
                break
            capturing = m.group(1) == version
            continue
        if capturing:
            out.append(line)
    if not capturing:
        raise SystemExit(f"❌ no [{version}] section in CHANGELOG.md")
    return out and "\n".join(out).strip() + "\n" or ""


def _section_exists(text: str, version: str) -> bool:
    return any(m.group(1) == version for m in _HEADING.finditer(text))


def lock_unreleased(text: str, version: str, date: str) -> str:
    """Insert ``## [version] — date`` directly below ``## [Unreleased]`` so the Unreleased body becomes
    the new version's body and a fresh empty Unreleased remains on top."""
    if not re.search(r"^## \[Unreleased\]\s*$", text, re.M):
        raise SystemExit("❌ no [Unreleased] section to lock")
    if extract_section(text, "Unreleased").strip() == "":
        raise SystemExit("❌ [Unreleased] is empty — nothing to release")
    if _section_exists(text, version):
        raise SystemExit(f"❌ [{version}] already exists in CHANGELOG.md")
    return re.sub(r"^## \[Unreleased\]\s*$",
                  f"## [Unreleased]\n\n## [{version}] — {date}",
                  text, count=1, flags=re.M)


def bump_version(version: str, level: str) -> str:
    core = version.split("+", 1)[0].split("-", 1)[0]
    major, minor, patch = (int(x) for x in core.split("."))
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def manifest_version() -> str:
    m = re.search(r'^version:\s*"?([^"\n]+)"?', MANIFEST.read_text(encoding="utf-8"), re.M)
    if not m:
        raise SystemExit("❌ no version: line in pack.manifest.yaml")
    return m.group(1).strip()


def set_manifest_version(text: str, version: str) -> str:
    return re.sub(r'^version:\s*.*$', f"version: {version}", text, count=1, flags=re.M)


def _git(cmd: list, run: bool):
    line = "git " + " ".join(cmd)
    if run:
        print(f"  $ {line}")
        subprocess.run(["git", "-C", str(REPO), *cmd], check=True)
    else:
        print(f"  {line}")


def _do_extract(args) -> int:
    section = extract_section(CHANGELOG.read_text(encoding="utf-8"), args.extract)
    print(section, end="")
    return 0


def _do_release(args) -> int:
    if args.release:
        version = args.release
    else:
        version = bump_version(manifest_version(), args.bump)
    if args.pre_release:
        version = f"{version}-{args.pre_release}"

    date = args.date or _today()
    text = CHANGELOG.read_text(encoding="utf-8")
    new_changelog = lock_unreleased(text, version, date)

    new_manifest = set_manifest_version(MANIFEST.read_text(encoding="utf-8"), version)
    tag = f"{TAG_PREFIX}{version}"

    verb = "WRITE" if args.apply else "DRY-RUN — would write"
    print(f"{verb}:")
    print(f"  CHANGELOG.md          lock [Unreleased] → [{version}] — {date}")
    print(f"  pack.manifest.yaml    version → {version}")
    if args.apply:
        CHANGELOG.write_text(new_changelog, encoding="utf-8")
        MANIFEST.write_text(new_manifest, encoding="utf-8")

    print(f"\n{'Running' if (args.apply and args.push) else 'Owner runs'} to fire release CI:")
    do_run = args.apply and args.push
    _git(["add", "CHANGELOG.md", ".claude/pack.manifest.yaml"], do_run)
    _git(["commit", "-m", f"release: product-spec v{version}"], do_run)
    _git(["tag", tag], do_run)
    _git(["push", "origin", "HEAD"], do_run)
    _git(["push", "origin", tag], do_run)
    if not args.apply:
        print("\n(dry-run — re-run with --apply to write; add --push to also tag+push)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Manage the root CHANGELOG.md release lifecycle.")
    ap.add_argument("--extract", metavar="X.Y.Z", help="print a version's section body (GitHub release body)")
    ap.add_argument("--release", metavar="X.Y.Z", help="cut a release at an explicit version")
    ap.add_argument("--bump", choices=["patch", "minor", "major"], help="cut a release at the next version")
    ap.add_argument("--pre-release", dest="pre_release", metavar="LABEL", help="pre-release label, e.g. rc.1")
    ap.add_argument("--date", help="release date YYYY-MM-DD (default: today)")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run preview)")
    ap.add_argument("--push", action="store_true", help="owner opt-in: tag + push (requires --apply)")
    args = ap.parse_args(argv)

    if args.extract:
        return _do_extract(args)
    if not (args.release or args.bump):
        ap.error("one of --extract / --release / --bump is required")
    if args.push and not args.apply:
        ap.error("--push requires --apply (refusing to push a dry-run)")
    return _do_release(args)


if __name__ == "__main__":
    raise SystemExit(main())
