# troubleshooting

Top recipient + maintainer failures and fixes. For error codes, see `error-catalog.md`.

## SHA256 mismatch on download

**Symptom:** `sha256sum -c release-X.Y.Z.tar.gz.sha256` reports `FAILED`.

**Fix:** Re-download the tarball AND its `.sha256` sidecar from the same release. A mismatch means corruption in transit or a tampered file — do NOT extract. If it persists, the publisher's release is bad; ask them to rebuild.

## `ModuleNotFoundError: No module named 'yaml'`

**Symptom:** `python -m pack` fails immediately.

**Fix:** Run the installer first: `bash install.sh` (creates the shared venv + installs pyyaml). Then invoke pack via the venv interpreter: `.claude/skills/.venv/bin/python3 -m pack...`. The system `python3` is NOT the venv — use the venv path.

## `install.sh: Permission denied`

**Symptom:** `./install.sh` won't run.

**Fix:** Either `chmod +x install.sh` then `./install.sh`, or invoke through the interpreter: `bash install.sh`. The latter always works regardless of the execute bit.

## `WARN: dropped symlink... ->...` during pack

**Symptom:** A file you expected is missing from the bundle; stderr shows a symlink WARN.

**Fix:** Symlinks are rejected by design (they can point outside the repo and break on extraction). Replace the symlink with a real file, or pull its target into the manifest as a regular `extra` path.

## `[MANIFEST_E020] absolute paths not allowed in extra`

**Symptom:** Pack exits 1 on a manifest with an `extra` entry like `/home/me/file`.

**Fix:** Convert the path to repo-relative (e.g., `.claude/scripts/file`). Absolute paths and `..` traversal are rejected to keep bundles self-contained and prevent exfiltration.

## `[MANIFEST_E002] refuse to build with placeholder version '0.0.0-dev'`

**Symptom:** Pack refuses to build.

**Fix:** Set a real `version:` in the manifest (e.g., `0.1.0`) or pass `--version 0.1.0`. For throwaway dev builds, pass `--allow-dev-version`.

## `python -m pack` prints "nothing to pack" (exit 5)

**Symptom:** Manifest validates but selection is empty.

**Fix:** Your `skills`/`agents`/`rules`/`extra` lists resolved to zero files on disk. Check spelling; case sensitivity follows the host filesystem (case-sensitive on Linux ext4, case-insensitive on macOS/Windows). Run `build_manifest.py --discover --root.` to see what's actually available.

## Windows: `install.ps1 cannot be loaded because running scripts is disabled`

**Symptom:** PowerShell execution policy blocks the installer.

**Fix:** Invoke with a scoped bypass (does NOT change your global policy): `powershell -ExecutionPolicy Bypass -File.\install.ps1`. Never run `Set-ExecutionPolicy` globally just for this.
