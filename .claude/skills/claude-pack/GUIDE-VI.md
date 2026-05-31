# Hướng dẫn sử dụng `claude-pack` cho Developer

> Tài liệu này dành cho **developer** muốn đóng gói một tập con của cây `.claude/` (skills, agents, hooks,
> rules…) thành một `tar.gz` **versioned + deterministic** để chia sẻ hoặc cài lên máy khác.
> Ngôn ngữ ở đây mang tính kỹ thuật; các thuật ngữ như `manifest`, `tarball`, `SHA256`, `SOURCE_DATE_EPOCH`
> được giữ nguyên tiếng Anh.
>
> Bản tiếng Anh: [`GUIDE-EN.md`](./GUIDE-EN.md).

---

## 1. Skill này làm gì?

`claude-pack` gom một **tập con được chọn lọc** của `.claude/` (cùng vài file top-level tùy chọn như
`README.md`, `CLAUDE.md`) thành một `tar.gz` đóng dấu version. Mỗi bundle kèm:

- `MANIFEST.json` — liệt kê per-file SHA256.
- `INSTALL.md` — hướng dẫn cài cho người nhận.
- `install.sh` (POSIX) + `install.ps1` (Windows) — installer đa nền tảng, version-aware.

Hai cam kết cốt lõi:

1. **Manifest là source-of-truth.** `.claude/pack.manifest.yaml` khai báo đầu vào build. CLI flag override
   theo từng lần build; chế độ tương tác sinh lại manifest.
2. **Determinism là một hợp đồng.** Cùng source + manifest → `tar.gz` **byte-identical**. Đạt được nhờ PAX
   format, sorted walk (file-granular), `mtime=0`, `uid=gid=0`, gzip header `mtime=0`.

Safety filter **không thể tắt**: `.env`/secrets/keys, `.git/`, runtime caches, session state luôn bị loại.
`settings.json` và `.ck.json` chỉ vào bundle khi opt-in tường minh.

---

## 2. Hai cách ra lệnh — và cách nào nên ưu tiên

### Cách 1 (ưu tiên): Mô tả ý định bằng lời

Bạn nói cho skill biết bạn muốn đóng gói gì; skill chạy `build_manifest` ở chế độ discover, dẫn bạn qua phỏng
vấn manifest, preview rồi pack:

> *"Đóng gói skill product-spec cùng agent planner và researcher để gửi cho đồng nghiệp."*
>
> *"Build cho tôi một bundle từ manifest hiện có, bản version 0.2.0."*
>
> *"Xem trước danh sách file sẽ vào bundle, đừng tạo tarball vội."*

Đây là cách khuyến khích vì LLM lo phần UI (AskUserQuestion) còn script lo phần cấu trúc — đúng với
Script-vs-LLM split.

### Cách 2 (tương đương): Gọi `python -m pack` trực tiếp

Khi đã có manifest và muốn tự động hóa (CI chẳng hạn), gọi thẳng script qua venv:

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml
```

Hai cách cho cùng kết quả. CLI chỉ là đường automation/CI; LLM là đường tương tác.

> ⚠️ **Lưu ý ranh giới:** Python script **không bao giờ** gọi `AskUserQuestion`. LLM là lớp UI, script là
> lớp cấu trúc. LLM **không bao giờ** sửa tarball trực tiếp.

---

## 3. Toàn bộ tình huống sử dụng — sắp theo thứ tự ưu tiên

Mỗi tình huống gồm: khi nào dùng, **kịch bản hội thoại mẫu**, và lệnh CLI tương đương.

---

### Ưu tiên 1 — Build tương tác từ đầu (chưa có manifest)

**Khi nào dùng:** Chưa có `.claude/pack.manifest.yaml`, hoặc muốn tạo mới bằng phỏng vấn.

Skill chạy `build_manifest --discover` để liệt kê skills/agents/hooks/rules có sẵn, rồi dẫn bạn qua **4 lô
câu hỏi**: (1) version + bundle name, (2) chọn skills/agents/hooks/rules, (3) top-level files, (4) extras +
xử lý `_shared/`. Cuối cùng preview và **chốt bằng prompt xác nhận khóa cứng** trước khi ghi manifest.

#### Kịch bản hội thoại

> **Bạn:** Tạo bundle gồm skill product-spec, agent planner và researcher, hai rule primary-workflow và
> development-rules.
>
> **Skill:** Tôi đã discover repo. Đi qua từng lô nhé.
> - *Version* bundle (SemVer)? Mặc định `0.1.0`. *Bundle name*? Mặc định `claude-pack`.
> - **Skills khả dụng:** product-spec, claude-pack. Bạn chọn `product-spec`.
> - **Agents:** planner, researcher, … → bạn chọn `planner`, `researcher`.
> - **Rules:** bạn chọn `primary-workflow.md`, `development-rules.md`.
> - Top-level: kèm `README.md` / `CLAUDE.md`? (mặc định không)
> - `_shared/`: auto-include các ref? (mặc định false = warn-only)
>
> **Bạn:** Version 1.0.0, không kèm top-level, để `_shared` warn-only.
>
> **Skill:** Tóm tắt: `version=1.0.0, skills=1, agents=2, rules=2`.
> > **Ready to write .claude/pack.manifest.yaml with 1 skills, 2 agents, 2 rules? [y/N]**
>
> **Bạn:** y
>
> **Skill:** Đã ghi manifest. Preview build: N file, tổng dung lượng X. Bạn muốn pack luôn không?

#### Lệnh CLI tương đương

```bash
# LLM tự chạy chuỗi này phía sau:
.claude/skills/.venv/bin/python3 -m build_manifest --discover --root .
.claude/skills/.venv/bin/python3 -m build_manifest --list-questions --root .
# (sau khi thu thập câu trả lời + xác nhận)
echo "$answers_json" | .claude/skills/.venv/bin/python3 -m build_manifest --write --root .
```

> Nếu manifest đã tồn tại, `--write` exit 2 (collision) trừ khi `--force`. Skill phải nêu collision và hỏi lại.

---

### Ưu tiên 2 — Build từ manifest có sẵn

**Khi nào dùng:** Đã có `.claude/pack.manifest.yaml`, chỉ muốn tạo tarball.

#### Kịch bản hội thoại

> **Bạn:** Build bundle từ manifest hiện tại.
>
> **Skill:** Tôi load `.claude/pack.manifest.yaml`, chạy safety_check (loại always-drop), walk sorted, rồi
> ghi `dist/claude-pack-1.0.0.tar.gz` cùng `.sha256` sidecar. Build deterministic — cùng input sẽ ra
> byte-identical.

#### Lệnh CLI tương đương

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml
```

---

### Ưu tiên 3 — Xem trước trước khi pack (Dry-run)

**Khi nào dùng:** Muốn xem **danh sách file + tổng dung lượng** mà không tạo tarball. Có thể kèm SHA256 dự kiến.

#### Kịch bản hội thoại

> **Bạn:** Xem trước những gì sẽ vào bundle, đừng tạo file thật.
>
> **Skill:** Dry-run xong: 47 file, tổng 312 KB nén. Không file always-drop nào lọt qua. Bạn muốn tôi tính
> luôn SHA256 dự kiến của tarball không? (chỉ một pass, không tốn kép)
>
> **Bạn:** Có.

#### Lệnh CLI tương đương

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --dry-run
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --dry-run --compute-sha
```

---

### Ưu tiên 4 — Override version / bundle name cho build ad-hoc

**Khi nào dùng:** Build thử nghiệm với version khác mà không sửa manifest.

> ⚠️ Skill từ chối placeholder `0.0.0-dev` cho build thật (cần `--allow-dev-version`). Version gắn nhãn
> *distribution*, độc lập với version của chính skill.

#### Kịch bản hội thoại

> **Bạn:** Build một bản rc, version 0.2.0-rc1.
>
> **Skill:** Override `version=0.2.0-rc1` cho lần này, manifest giữ nguyên. Output: `dist/claude-pack-0.2.0-rc1.tar.gz`.

#### Lệnh CLI tương đương

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --version 0.2.0-rc1
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --bundle-name my-pack
```

---

### Ưu tiên 5 — Override nội dung qua CLI (không sửa manifest)

**Khi nào dùng:** Muốn thêm/bớt skills, agents, hooks, rules, hoặc extra path cho một lần build.

> CLI override **thắng** giá trị manifest cho category đó. `--extra` cấm path tuyệt đối và `..`.

#### Kịch bản hội thoại

> **Bạn:** Build như manifest nhưng chỉ lấy mỗi skill product-spec và thêm file docs/onboarding.md.
>
> **Skill:** Override `--skills product-spec --extra docs/onboarding.md`. Các category khác giữ theo manifest.

#### Lệnh CLI tương đương

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml \
  --skills product-spec --extra docs/onboarding.md
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml \
  --agents planner,researcher --rules primary-workflow.md,development-rules.md
```

---

### Ưu tiên 6 — Opt-in các file nhạy cảm / internal

**Khi nào dùng:** Cần kèm `settings.json`, `.ck.json`, README/CLAUDE.md top-level, hoặc internals
`scripts/`/`schemas/`. Tất cả **off mặc định**, phải bật tường minh.

> `settings.json` và `.ck.json` thuộc opt-in catalog của safety filter — chỉ vào bundle qua flag tương ứng.
> Secrets/keys/`.env` **luôn bị loại**, không flag nào kéo lại được.

#### Kịch bản hội thoại

> **Bạn:** Kèm luôn README và CLAUDE.md top-level, và settings.json.
>
> **Skill:** Bật `--include-readme --include-claudemd --include-settings`. Lưu ý `settings.json` là opt-in
> nhạy cảm — đã thêm theo yêu cầu tường minh của bạn. `.env`/secrets vẫn bị loại bất kể gì.

#### Lệnh CLI tương đương

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml \
  --include-readme --include-claudemd --include-settings
# Internals CK-framework (off mặc định):
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml \
  --include-scripts --include-schemas
```

---

### Ưu tiên 7 — Xử lý phụ thuộc `_shared/`

**Khi nào dùng:** Skill được pack có tham chiếu `skills/_shared/<name>`. Mặc định **warn-only** (vì nhiều ref
nằm trong code fence ví dụ, không phải dependency thật — skill strip fenced block rồi mới warn).

#### Kịch bản hội thoại

> **Bạn:** Skill của tôi dùng _shared/lib và _shared/utils, kéo chúng vào luôn.
>
> **Skill:** Opt-in `--include-shared lib,utils`. Nếu bạn muốn ref `_shared/` chưa include bị coi là **lỗi**
> (chặn build), thêm `--strict` (exit 2).

#### Lệnh CLI tương đương

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --include-shared lib,utils
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --follow-shared
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --strict
```

---

### Ưu tiên 8 — Reproducible build cho CI (`SOURCE_DATE_EPOCH`)

**Khi nào dùng:** Muốn build reproducible theo commit date trong CI.

> Mặc định `mtime=0` (fully deterministic). `--source-date-epoch env` honor biến `SOURCE_DATE_EPOCH`; nếu
> biến rỗng/không phải số thì fallback im lặng về 0.

#### Kịch bản hội thoại

> **Bạn:** Trong CI, gắn mtime theo commit cuối.
>
> **Skill:** Set `SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct)` rồi pass `--source-date-epoch env`. Tarball
> vẫn deterministic trên cùng commit.

#### Lệnh CLI tương đương

```bash
SOURCE_DATE_EPOCH=$(git log -1 --pretty=%ct) \
  .claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --source-date-epoch env
```

---

### Ưu tiên 9 — Output JSON cho pipeline CI

**Khi nào dùng:** Cần status máy-đọc-được để pipeline parse.

#### Kịch bản hội thoại

> **Bạn:** Build và trả JSON để bước CI sau parse.
>
> **Skill:** Thêm `--json` cho `python -m pack` → status JSON ra stdout. (Lưu ý: `manifest_loader.py`,
> `safety_check.py`, `build_manifest.py` luôn emit JSON, không có flag `--json`.)

#### Lệnh CLI tương đương

```bash
.claude/skills/.venv/bin/python3 -m pack --manifest .claude/pack.manifest.yaml --json
```

---

### Ưu tiên 10 — Phía người nhận: cài bundle (kể cả Windows)

**Khi nào dùng:** Người nhận đã có `claude-pack-{version}.tar.gz`.

Mọi bundle ship **cả hai** installer. Recipient verify SHA256 → extract → chạy installer. Installer
**version-aware** (phát hiện STALE / NEWER / OK SAME mỗi skill), mặc định **skip-existing**; ghi đè qua
`FORCE_OVERWRITE=1` (backup trước).

#### Kịch bản hội thoại

> **Bạn (người nhận, máy Windows):** Tôi nhận được file tar.gz, cài thế nào trên Windows?
>
> **Skill:** Verify checksum, giải nén, rồi chạy `install.ps1`:
> ```powershell
> # PowerShell
> (Get-FileHash claude-pack-1.0.0.tar.gz -Algorithm SHA256).Hash
> tar -xzf claude-pack-1.0.0.tar.gz
> cd claude-pack-1.0.0
> powershell -ExecutionPolicy Bypass -File .\install.ps1
> ```
> Trên POSIX thì dùng `install.sh` tương ứng. Installer skip skill đã tồn tại; muốn ghi đè đặt `FORCE_OVERWRITE=1`.

#### Lệnh tương đương (POSIX)

```bash
sha256sum -c claude-pack-1.0.0.tar.gz.sha256
tar -xzf claude-pack-1.0.0.tar.gz
cd claude-pack-1.0.0 && ./install.sh
FORCE_OVERWRITE=1 ./install.sh      # ghi đè skill đã tồn tại (backup trước)
```

---

## 4. Output Contract

```
dist/
├── claude-pack-{version}.tar.gz          # bundle
└── claude-pack-{version}.tar.gz.sha256   # coreutils-format sidecar
```

Layout bên trong tarball (versioned root dir):

```
claude-pack-{version}/
├── MANIFEST.json     # schema_version "1.0", per-file SHA256
├── INSTALL.md        # render từ INSTALL.md.template
├── install.sh        # POSIX installer
├── install.ps1       # Windows installer
└── .claude/          # subtree được chọn
```

`dist/` được gitignore — tarball là build artifact reproducible, không phải source.

---

## 5. Exit Codes (cho automation)

| Code | Nghĩa |
|------|-------|
| 0 | Success |
| 1 | Validation / manifest error |
| 2 | Strict-gate finding (`--strict`) |
| 3 | Output collision (thiếu `--force`) |
| 4 | Write error (disk full, permission, cross-fs replace) |
| 5 | Empty selection / vượt max-size |
| 130 | Interrupted (SIGINT) |

> `build_manifest.py --write` dùng bộ code riêng: 0 ok · 1 validation · 2 **collision** (khác nghĩa với
> strict-gate ở entry point `python -m pack`).

---

## 6. Những điều skill này KHÔNG làm

- **Không upload remote.** Dùng `gh release upload` thủ công.
- **Không GPG signing v1.** Chỉ SHA256 sidecar.
- **Không có companion `claude-unpack`.** Hợp đồng là `tar -xzf` + bundled installer.
- **Không merge-resolver.** Recipient `install.sh` skip skill đã tồn tại; `FORCE_OVERWRITE=1` để opt-in.
- **Không multi-project packing.** Một `.claude/` root mỗi bundle.
- **Không zip / tar.zst.** Chỉ tar.gz trong v1.

---

## 7. Tham chiếu sâu hơn

- `SKILL.md` — operating contract đầy đủ (flag table, output contract, workflow map).
- `references/manifest-spec.md` — schema manifest.
- `references/flag-reference.md` — chi tiết từng CLI flag + exit codes.
- `references/safety-rules.md` — always-drop + opt-in catalog.
- `references/error-catalog.md` — tra cứu `MANIFEST_E###`.
- `references/troubleshooting.md` — sự cố phía recipient.
- Root `CLAUDE.md` → mục "Claude Pack — LLM Operating Guide" — năm nguyên tắc vận hành (source-of-truth).
