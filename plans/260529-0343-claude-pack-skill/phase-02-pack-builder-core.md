---
phase: 2
title: "Pack Builder Core"
status: pending
priority: P1
effort: "7h"
dependencies: [1]
---

# Phase 2: Pack Builder Core

## Overview

Implement the `pack/` subpackage — the deterministic tarball builder, **modularized** into 5 files (per PO R3.Q4) to honor the 200-line rule. Reads a resolved manifest (Phase 3 supplies the loader), walks selected paths, applies the safety filter (Phase 3 supplies the rules), normalizes metadata for byte-identical reproducibility, writes `claude-pack-{version}.tar.gz` to `dist/`, embeds `MANIFEST.json` + bundled installers + `INSTALL.md` in the versioned root dir, and writes a `.sha256` sidecar.

**Cross-platform** (POSIX + Windows per R3.Q2): uses `os.replace` (atomic on both); no bash-isms in script logic.

## Context Links

- Plan `## API Contracts` section — locked signatures (`build_tarball`, `normalize_filter`, `build_manifest_json`, `write_sha256_sidecar`, `render_template`)
- Researcher A report: tarfile API, 7 determinism knobs, filter callback, MANIFEST schema, SHA256 sidecar — `plans/reports/from-researcher-to-planner-260529-0343-claude-pack-python-tarball-best-practices-report.md`
- Red-team review (all CRITICAL + HIGH applied): `plans/reports/from-code-reviewer-to-planner-260529-0354-claude-pack-red-team-review-report.md`
- Phase 1 outputs consumed: `assets/templates/*.template`, `references/safety-rules.md` stub

## Requirements

**Functional (18 flags):**
- `python -m pack [--manifest <path>] [--version <semver>] [--out <dir>] [--name <stem>] [--dry-run] [--compute-sha] [--force] [--all] [--skills <list>] [--agents <list>] [--hooks <list>] [--rules <list>] [--extra <paths>] [--include-readme] [--include-claudemd] [--include-settings] [--include-ck-config] [--include-shared <list>] [--source-date-epoch <int|env>] [--max-size <bytes>] [--json]`
- Output filename: `{stem}-{version}.tar.gz` (default stem `claude-pack`)
- Output dir: `dist/` (default), gitignored, auto-created
- Tarball internal: versioned root dir `{stem}-{version}/` containing `MANIFEST.json` + `INSTALL.md` + `install.sh` + `install.ps1` + `.claude/` subtree
- MANIFEST.json schema 1.0: `schema_version`, `bundle_name`, `bundle_version`, `built_at` (ISO 8601), `source_repo` (`git remote get-url origin` fallback empty string), `source_commit` (`git rev-parse HEAD` fallback `unknown`), `total_bytes`, `files: [{path, size, sha256}]`, `checksums: {tarball_sha256, manifest_sha256}` (post-write)
- `.sha256` sidecar in coreutils format: `<hex>  <basename>\n`
- `--dry-run` fast path: file list + total bytes + path; no SHA256 (avoid double-pass)
- `--dry-run --compute-sha`: opt-in adds would-be tarball SHA256 (uses BytesIO, shares byte-producing routine with real run — validate F1.5)
- `--json`: structured JSON output instead of human text (covers stdout + stderr findings)
- `--source-date-epoch <int|env>`: opt-in env var honor (default: ignored, mtime=0)
- `--max-size <bytes>` (default 100 MB): refuse if final tarball exceeds (red-team F14.1)
- Empty selection → exit 1 with `"nothing to pack"` message (red-team F13.1)
- Symlinks rejected with `WARN: dropped symlink {name} → {target}` (red-team F1.3)
- `tmp` cleanup on startup: remove `dist/.*.tmp` older than 1h (validate F7.4)

**Exit codes (LOCKED — single source-of-truth, red-team F17.6 + validate F10.3):**
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation / manifest error |
| 2 | Strict-gate finding (`--strict`) |
| 3 | Output collision (no `--force`) |
| 4 | Write error (disk full, permission, cross-fs replace) |
| 5 | Empty selection / over-max-size |
| 130 | Interrupted (SIGINT) |

**Non-functional:**
- **Deterministic:** two runs on same source tree → byte-identical `tar.gz` (verified by Phase 5 T-D1). Knobs: PAX format, file-granular sorted walk (NOT `tar.add(dir)`), `mtime=0`, `uid=gid=0`, `uname=gname=""`, gzip header `mtime=0`. Sort key: `arcname.encode("utf-8")` (codepoint stable across locales).
- **Safe:** all entries pass through `safety_check.is_dropped()` (Phase 3) before addition. Symlinks rejected unconditionally.
- **Atomic:** write to `dist/.{stem}-{version}.tar.gz.tmp`, fsync, `os.replace()` (atomic on POSIX + Windows). `try/finally` ensures tmp cleanup on exception.
- **Cross-platform:** No POSIX-only syscalls. Tested on Ubuntu, macOS, Windows in Phase 7 CI matrix.

## Architecture (MODULARIZED per R3.Q4)

```
scripts/pack/                              # subpackage; each file < 200 LOC
├── __init__.py        ~10 LOC  → exports main, __version__
├── __main__.py        ~5 LOC   → `python -m pack` entry; calls cli.main()
├── cli.py             ~120 LOC → argparse setup, dispatch
├── tarball.py         ~150 LOC → build_tarball, normalize_filter, gzip wrapper
├── manifest_io.py     ~80 LOC  → build_manifest_json, write_sha256_sidecar, atomic IO
└── templates.py       ~50 LOC  → render_template (token substitution + TemplateError)
```

**Data flow:**
```
cli.main(argv)
 │
 ├─ argparse → args
 ├─ manifest_loader.load(args.manifest) → dict       (Phase 3)
 ├─ manifest_loader.merge_cli(manifest, args) → dict (Phase 3)
 ├─ manifest_loader.validate(manifest, root) → []    (Phase 3, exit 1 on errors)
 ├─ manifest_loader.apply_defaults(manifest, root)   (Phase 3)
 ├─ resolve_selection(manifest, root) → list[(src, arcname)]  (cli.py)
 ├─ safety_check.find_shared_refs(...) → emit warn   (Phase 3, opt-in --include-shared)
 ├─ cleanup_stale_tmp(out_dir, max_age=3600)         (manifest_io.py)
 ├─ if args.dry_run:
 │    print preview JSON / human   → exit 0
 ├─ tarball.build_tarball(selection, manifest, tmp_path,
 │                       source_date_epoch=args.source_date_epoch) → sha256
 ├─ if size > args.max_size: cleanup tmp; exit 5
 ├─ manifest_io.atomic_replace(tmp_path, final_path, force=args.force)
 ├─ manifest_io.write_sha256_sidecar(final_path) → sha256.txt
 └─ print summary {path, size, sha256, file_count}; exit 0
```

**`normalize_filter` (tarball.py — combines safety + determinism):**
```python
def normalize_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    # Reject symlinks unconditionally (red-team F1.3, F2.5)
    if tarinfo.issym() or tarinfo.islnk():
        log_warn(f"dropped symlink {tarinfo.name} → {tarinfo.linkname}")
        return None
    # Always-drop safety (Phase 3)
    dropped, rule = safety_check.is_dropped(tarinfo.name)
    if dropped:
        log_warn(f"dropped {tarinfo.name} (rule: {rule})")
        return None
    # Determinism normalization
    tarinfo.mtime = source_date_epoch  # default 0
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = ""
    if tarinfo.isdir():  tarinfo.mode = 0o755
    elif tarinfo.isfile(): tarinfo.mode = 0o644
    return tarinfo
```

**Gzip wrapper (deterministic mtime=0):**
```python
# tarball.py
import gzip, tarfile
def open_deterministic_tar(out_path: Path, source_date_epoch: int):
    raw = open(out_path, "wb")
    gz = gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9)
    tar = tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT)
    return tar, gz, raw  # caller closes all 3 in reverse order
```

## Related Code Files

**Create:**
- `.claude/skills/claude-pack/scripts/pack/__init__.py`
- `.claude/skills/claude-pack/scripts/pack/__main__.py`
- `.claude/skills/claude-pack/scripts/pack/cli.py` (~120 LOC)
- `.claude/skills/claude-pack/scripts/pack/tarball.py` (~150 LOC)
- `.claude/skills/claude-pack/scripts/pack/manifest_io.py` (~80 LOC)
- `.claude/skills/claude-pack/scripts/pack/templates.py` (~50 LOC)

**Modify:**
- `.claude/skills/claude-pack/references/flag-reference.md` — fill full 18-flag table (was stub from Phase 1)
- root `.gitignore` — add `/dist/` (leading slash anchors to repo root)
- `.claude/skills/claude-pack/SKILL.md` — fill Flags table descriptions (Phase 1 left names only)

## Implementation Steps

1. **Skeleton — 5 files, each <200 LOC** — verify with `wc -l` after each.

2. **cli.py — argparse** with `BooleanOptionalAction(default=None)` for all booleans (`--include-readme`, `--include-claudemd`, `--include-settings`, `--include-ck-config`, `--follow-shared`, `--force`, `--dry-run`, `--compute-sha`, `--json`). `None` means "no override" — manifest wins (red-team F17.2). Use a custom `_VersionAction` so `--version` doesn't collide with Python's built-in (alias to manifest field).

3. **cli.resolve_selection** — map manifest categories to `.claude/` paths:
   - `skills: [foo]` → `.claude/skills/foo/` (recursive)
   - `agents: [bar]` → search `.claude/agents/**/*.md` for basename match; **error if 0 or >1 matches** (red-team F17.1)
   - `hooks: [baz.cjs]` → `.claude/hooks/baz.cjs` (extension required)
   - `rules: [primary-workflow.md]` → search `.claude/rules/**/*.md` for basename match (same error rule as agents)
   - `extra: [docs/dev.md]` → preserve relative path (NO absolute, NO `..` — Phase 3 validate)
   - `top_level.*` → `.claude/{settings.json,.ck.json}` or repo root `README.md`/`CLAUDE.md`
   - **Default-ship** (always added unless explicit `defaults.exclude_*`): `.claude/scripts/`, `.claude/schemas/`
   - **Failed lookups**: exit 1 with `"missing {category}: {slug}"` (case-sensitive check — red-team F4.4)

4. **cli.flat_sort** — emit FILE-GRANULAR (src, arcname) tuples sorted by `arcname.encode("utf-8")` (red-team F1.1, F1.2). Never call `tar.add(directory)` — always per-file `tar.addfile(tarinfo, fileobj)`.

5. **safety_check.find_shared_refs** call — for each selected skill, find `_shared/<x>` refs (Phase 3 strips fenced code blocks first). Emit `WARN: skill X references _shared/foo — use --include-shared foo to include` (red-team F5.1: warn-only by default). If user passes `--include-shared foo`: add `.claude/skills/_shared/foo` to selection.

6. **tarball.build_tarball** — implements deterministic write per architecture diagram. Uses `try/finally` to ensure `tmp` cleanup if exception fires (red-team F3.2). Returns SHA256 hex of completed tarball.

7. **manifest_io.build_manifest_json** — walk selection, compute SHA256 + size per file. JSON shape per researcher A Q4. `built_at` is `datetime.now(UTC).isoformat(timespec="seconds")` UNLESS `source_date_epoch != 0` (then `datetime.fromtimestamp(epoch, UTC).isoformat()`).

8. **templates.render_template** — pure string-substitute `{{TOKEN}}`. Unknown tokens raise `TemplateError(f"unknown template token: {{{{{name}}}}}")` (red-team F17.3). Test Phase 5.

9. **Embed in tar** — order: MANIFEST.json (computed last but embedded first for streaming-extract UX), INSTALL.md, install.sh, install.ps1, then `.claude/` files in sorted order. All as in-memory BytesIO; no temp files on disk.

10. **Dry-run path** — `cli.dry_run()` prints:
    - Default: file list + total bytes + output path
    - `--compute-sha`: + would-be tarball SHA256 (calls `build_tarball(out=BytesIO())` — same byte-producing routine as real run per F1.5)
    - `--json`: structured JSON shape `{files: [...], total_bytes: N, output_path: "...", would_be_sha256: "..." | null}`

11. **Atomic write (`manifest_io.atomic_replace`)** — POSIX + Windows:
    ```python
    def atomic_replace(tmp: Path, final: Path, force: bool):
        if final.exists() and not force:
            raise CollisionError(...)  # exit 3
        if final.exists() and force:
            backup = final.with_suffix(f".bak.{int(time.time())}")
            final.rename(backup)
        try:
            os.replace(tmp, final)  # atomic on POSIX + Windows
        except OSError as e:
            if "Invalid cross-device link" in str(e):
                shutil.move(str(tmp), str(final))  # cross-fs fallback (warn)
            else:
                tmp.unlink(missing_ok=True)
                raise
    ```

12. **gzip mtime verification** — after write, optionally read bytes `[4:8]` of the tar.gz file and assert `== b"\x00\x00\x00\x00"` (red-team F1.4, validated in Phase 5 T-D4 with 0-indexed `data[4:8]` slice).

13. **SHA256 sidecar** — 64KB chunked read; write `dist/{name}.sha256` with `f"{hex}  {basename}\n"`.

14. **Collision + over-size handling** — exit codes per table above. With `--force`: rename existing `{name} → {name}.bak.{epoch}`.

15. **tmp cleanup on startup** — `manifest_io.cleanup_stale_tmp(out_dir, max_age=3600)` walks `dist/.*.tmp` files modified >1h ago and `unlink`s them.

16. **Logging** — default plain text to stdout (INFO) + stderr (WARN/ERROR). `--json` switches both streams to NDJSON: each line `{level, message, ...}`. Final summary line stays in both modes.

17. **Fill `flag-reference.md`** — table with: flag, type, default, manifest field overridden, description, example. All 18 flags.

18. **Verify per-phase compile** (validate F15.3): `python -m py_compile scripts/pack/{cli,tarball,manifest_io,templates}.py` exits 0 after each file.

## Success Criteria

- [ ] `python -m pack --help` prints all 18 flags
- [ ] `wc -l scripts/pack/*.py | sort -n` — each file < 200 LOC
- [ ] `python -m pack --manifest .claude/pack.manifest.yaml --version 0.1.0 --dry-run` prints file list + total bytes (no SHA)
- [ ] `python -m pack --manifest .claude/pack.manifest.yaml --version 0.1.0 --dry-run --compute-sha` prints file list + total bytes + would-be SHA256
- [ ] `python -m pack --manifest .claude/pack.manifest.yaml --version 0.1.0` creates `dist/claude-pack-0.1.0.tar.gz` + `.sha256` sidecar
- [ ] Two consecutive runs produce byte-identical tar.gz: `sha256sum dist/*.tar.gz` matches
- [ ] `tar tzf dist/claude-pack-0.1.0.tar.gz | head -1` → `claude-pack-0.1.0/`
- [ ] `tar xzOf dist/claude-pack-0.1.0.tar.gz claude-pack-0.1.0/MANIFEST.json | jq .schema_version` → `"1.0"`
- [ ] First 8 bytes of tar.gz: `data[4:8] == b"\x00\x00\x00\x00"` (gzip mtime=0)
- [ ] No `.env`, `metadata.json`, `__pycache__`, `.git/` inside tarball
- [ ] `python -m pack` with manifest that has `extra: ["/etc/passwd"]` → exits 1 with "absolute paths not allowed"
- [ ] `python -m pack` with manifest that has `extra: ["../something"]` → exits 1 with "path traversal not allowed"
- [ ] `python -m pack` with empty selection → exits 5 with "nothing to pack"
- [ ] `python -m pack --max-size 1000` against a 10KB pack → exits 5 with "over max size"
- [ ] Symlink in selection → dropped with `WARN: dropped symlink ...` in stderr
- [ ] Output collision: second run without `--force` → exit 3
- [ ] `--force` renames existing to `.bak.{epoch}` before write
- [ ] `dist/` is gitignored (`grep -q '^/dist/' .gitignore`)
- [ ] `references/flag-reference.md` has 18 rows in the flag table
- [ ] Cross-platform: tests pass on Ubuntu, macOS, Windows in Phase 7 CI (deferred verification)
- [ ] `python -m py_compile scripts/pack/*.py` exits 0

## Risk Assessment

- **R1: Gzip mtime non-zero despite `mtime=0`** → Mitigation: explicit `gzip.GzipFile(mtime=0)` wrap; Phase 5 T-D4 byte-level verify.
- **R2: Per-file addfile slower than `tar.add(dir)`** → Mitigation: profile in Phase 5; budget 2s for 100MB pack. If hot path, batch via `tar.add(name, recursive=False)` per file (same effect).
- **R3: Cross-fs `os.replace` raises** → Mitigation: catch + fall back to `shutil.move` + emit `WARN: atomicity disabled (cross-filesystem write)`.
- **R4: `--source-date-epoch env` flag honors stale env var on dev machine** → Mitigation: argparse explicitly checks `args.source_date_epoch in (None, 0)` before reading env; `--source-date-epoch env` is an explicit opt-in keyword.
- **R5: PowerShell version-detection regex fragile** → Mitigation: covered in Phase 1 R5.
- **R6: Atomic write race condition during force-overwrite backup** → Mitigation: `final → backup` happens before `tmp → final`; if rename interrupted between, manual recovery from `.bak.{epoch}`. Documented in error-catalog.md (Phase 3 creates).
- **R7: 200-line modularization bleeds context if cross-module refactor needed** → Mitigation: API Contracts section in plan.md is the change-control surface. Document any post-Phase-2 module changes there.

## Security Considerations

- Filter callback drops secrets unconditionally even if explicitly listed in manifest (hard safety per Phase 3 expanded list). Test Phase 5 T-S4.
- `INSTALL.md.template` (Phase 1) instructs recipient to `sha256sum -c` before extract.
- `pack.py` reads working directory only; never traverses `..` paths in selection resolution.
- Atomic replace prevents half-written tarball SHA256 mismatch in CI race.
- `--force` requires explicit flag; never silent overwrite.

## Next Steps

- Phase 3 supplies `safety_check.is_dropped` + `manifest_loader.load/validate/merge_cli/apply_defaults` per locked API Contracts (parallel-developable after Phase 1 done).
- Phase 5 verifies all Success Criteria above + cross-platform behavior (deferred to Phase 7 CI).
- Phase 6 dogfoods this Phase by packing `cleanmatic:product-spec` via the seed `.claude/pack.manifest.yaml`.
