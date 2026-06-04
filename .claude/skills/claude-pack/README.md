# cleanmatic:claude-pack

Package opt-in `.claude/` artifacts (skills, agents, hooks, rules) into a versioned, deterministic `tar.gz` for distribution.

> 🇬🇧 **English** below · 🇻🇳 **Tiếng Việt** ở nửa dưới (cuộn xuống mục **Tiếng Việt**).

---

## English

### Install

```bash
./install.sh             # runtime only (pyyaml)
./install.sh --dev       # runtime + dev (pytest + pytest-cov)
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Dev
```

Requires Python 3.11+.

### Quickstart

**LLM-driven (recommended):**

```
/cleanmatic:claude-pack
```

The skill walks you through manifest authoring (interactive) → preview → confirm → pack.

**Manual CLI:**

```bash
# Build from existing manifest
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml

# Dry-run (file list + size, no tarball) + would-be SHA256
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --dry-run --compute-sha
```

Output lands in `dist/claude-pack-{version}.tar.gz` + `.sha256` sidecar.

### The 6 things to know before you start

1. **Manifest is source-of-truth.** `.claude/pack.manifest.yaml` declares the build inputs; CLI flags override per-build, interactive mode regenerates it.
2. **Determinism is a contract.** Same source + manifest → byte-identical `tar.gz` (PAX, sorted walk, `mtime=0`, `uid=gid=0`). Never hand-edit a tarball.
3. **The safety filter is non-removable.** `.env`/secrets/keys, `.git/`, caches are **always dropped**; `settings.json`/`.ck.json`/top-level files are **opt-in only** — no flag can pull a secret back.
4. **Script-vs-LLM split.** Scripts do the structural work; the LLM owns the UI and never edits the tarball.
5. **No auto-install.** The recipient runs the installer by hand — skip-existing default, `FORCE_OVERWRITE=1` to opt in.
6. **Releases are tag-triggered CI only.** Bump `version` + the CHANGELOG, push an annotated tag — **never hand-build + `gh release create`** (a manual build's SHA won't match CI's reproducible build).

### Learning path

- **Build basics:** interactive build (`/cleanmatic:claude-pack`) → preview with `--dry-run` → build from the manifest.
- **Shape the bundle:** override `--version`/`--bundle-name`, content flags (`--skills`/`--agents`/…), opt-in sensitive files (`--include-settings`…), `_shared/` handling (`--include-shared`).
- **Automate in CI:** reproducible build (`--source-date-epoch env`), `--json` output, the exit-code table.
- **Ship & receive:** recipient install (POSIX/Windows, version-aware); for an official release use the tag-triggered pipeline.

Full walkthroughs with sample conversations + the underlying commands: **[`GUIDE-EN.md`](./GUIDE-EN.md)**.

### Layout

```
.claude/skills/claude-pack/
├── SKILL.md          # operating contract (LLM reads this)
├── scripts/          # pack/ subpackage + safety_check + manifest_loader + build_manifest
├── references/       # load-on-demand: manifest-spec, flag-reference, safety-rules, ...
└── assets/templates/ # manifest.example.yaml + INSTALL.md/install.sh/install.ps1 templates
```

Full architecture: `references/maintainers-guide.md`. Reference index: see `SKILL.md` "Load-on-Demand References".

### FAQ

**Why is `dist/` gitignored?** Tarballs are reproducible build artifacts, not source. Commit them only on a tagged release (the CI release pipeline uploads them to GitHub Releases). Same source + manifest always rebuilds the identical bytes.

**Why must I pass a real `version`?** The bundle version labels the *distribution*, not the code; it is decoupled from the skill's own version. We refuse the `0.0.0-dev` placeholder for real builds — pass `--version X.Y.Z` or `--allow-dev-version` for throwaway tests.

**Why is `_shared/` warn-only?** `SKILL.md` files often mention `_shared/<name>` inside example code fences that aren't real dependencies. We strip fenced blocks, then warn — opt in explicitly with `--include-shared <name>`.

**How do I bundle for Windows recipients?** Every bundle ships both `install.sh` and `install.ps1`. The recipient runs `powershell -ExecutionPolicy Bypass -File .\install.ps1`. The installer is version-aware on both platforms (STALE/NEWER/OK SAME per skill).

**Is the build deterministic?** Yes — PAX, file-granular sorted walk, `mtime=0`, `uid/gid=0`, gzip `mtime=0`. Two builds of the same source produce byte-identical tarballs. For source-date reproducibility in CI, pass `--source-date-epoch env`.

---

## Tiếng Việt

Đóng gói các artifact `.claude/` (skills, agents, hooks, rules — chọn lọc) thành một `tar.gz` **versioned + deterministic** để phân phối.

### Cài đặt

```bash
./install.sh             # chỉ runtime (pyyaml)
./install.sh --dev       # runtime + dev (pytest + pytest-cov)
```

Windows: `powershell -ExecutionPolicy Bypass -File .\install.ps1` (thêm `-Dev` nếu cần). Cần Python 3.11+.

### Bắt đầu nhanh

**Qua LLM (khuyến nghị):** gõ `/cleanmatic:claude-pack` — skill dẫn bạn qua soạn manifest (tương tác) → preview → xác nhận → pack.

**CLI thủ công:**

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --dry-run --compute-sha
```

Đầu ra ở `dist/claude-pack-{version}.tar.gz` + sidecar `.sha256`.

### 6 điều cần biết trước khi bắt đầu

1. **Manifest là source-of-truth.** `.claude/pack.manifest.yaml` khai báo đầu vào build; CLI flag override theo lần build, chế độ tương tác sinh lại manifest.
2. **Determinism là hợp đồng.** Cùng source + manifest → `tar.gz` byte-identical (PAX, sorted walk, `mtime=0`, `uid=gid=0`). Đừng sửa tay tarball.
3. **Safety filter không thể tắt.** `.env`/secrets/keys, `.git/`, caches **luôn bị loại**; `settings.json`/`.ck.json`/file top-level **chỉ vào khi opt-in** — không flag nào kéo secret lại được.
4. **Script-vs-LLM split.** Script lo cấu trúc; LLM lo UI và không bao giờ sửa tarball.
5. **Không auto-install.** Người nhận chạy installer bằng tay — skip-existing mặc định, `FORCE_OVERWRITE=1` để opt-in.
6. **Release chỉ kích bằng tag qua CI.** Bump `version` + CHANGELOG, push annotated tag — **không bao giờ hand-build + `gh release create`** (SHA build tay không khớp build reproducible của CI).

### Lộ trình học

- **Build cơ bản:** build tương tác → preview `--dry-run` → build từ manifest.
- **Định hình bundle:** override `--version`/`--bundle-name`, flag nội dung (`--skills`/`--agents`/…), opt-in file nhạy cảm (`--include-settings`…), xử lý `_shared/` (`--include-shared`).
- **Tự động hóa CI:** reproducible build (`--source-date-epoch env`), output `--json`, bảng exit code.
- **Ship & nhận:** cài phía người nhận (POSIX/Windows, version-aware); release chính thức dùng pipeline kích-bằng-tag.

Hướng dẫn đầy đủ kèm hội thoại mẫu + lệnh thực thi: **[`GUIDE-VI.md`](./GUIDE-VI.md)**. Phần FAQ chi tiết ở mục **English** bên trên.
