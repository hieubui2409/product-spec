# cleanmatic:product-spec-critique

User-invocable Claude skill that gives a product spec an **honest, brutal critique** across four lenses (product / tech / market / craft) in a sarcastic-but-grounded voice. It **consumes** the spec written by `cleanmatic:product-spec`, reuses its `--validate` findings as ammunition, then adds the *why-it-dies / market / craft / cross-lens* judgment that `--validate` deliberately leaves out. Every line carries an evidence `ID:line`, a why-it-dies, and a fix. It **never edits the spec** and **never gates CI**.

> 🇬🇧 **English** below · 🇻🇳 **Tiếng Việt** ở nửa dưới (cuộn xuống mục **Tiếng Việt**).

---

## English

### How it differs from `--validate`

`product-spec --validate` is reproducible, warm, PO-facing, CI-gateable — pass/fail on structure + core-value. `/product-spec-critique` is the opposite by design: **opinionated, non-deterministic** (LLM judgment + web research + a 9-level voice), and therefore kept OUT of the CI gate. It is a *consumer* of validate, not a replacement.

### Install

Adds **no new dependency** — it reuses the shared skill venv (`.claude/skills/.venv`) created by `cleanmatic:product-spec`.

```bash
./install.sh                  # ensure shared venv (reuse if present); no hooks
./install.sh --critique-hook  # opt-in: register the advisory drift-nudge Stop hook
```

The drift-nudge hook is **opt-in only and never auto-registered** — a plain install leaves your hooks untouched. `--critique-hook` writes to the gitignored `.claude/settings.local.json`; `--critique-hook-shared` targets the committed `.claude/settings.json`. Windows: `install.ps1` (`-CritiqueHook` / `-CritiqueHookShared`).

### Quickstart

```
/product-spec-critique                       # critique the whole spec (scope=all, expensive)
/product-spec-critique PRD-CHECKOUT          # critique one PRD (its full ancestry is pulled as context)
/product-spec-critique PRD-CHECKOUT --craft --level 4   # editorial-only, savage
/product-spec-critique --interactive         # pick scope + lenses + level interactively
```

### The 5 things to know before you start

1. **It tears the spec apart but never edits it.** Four lenses → one markdown report under `docs/product/critique/`. Findings return to the spec only via `product-spec --apply-critique`, where you confirm each one.
2. **It never gates CI.** Opinion + web + a 9-level voice = non-deterministic by design — `--validate` is the deterministic gate, this is the judgment on top.
3. **It judges against ancestry.** Even one story is critiqued against its full ancestry (epic → PRD → goal → vision).
4. **Voice level 5 is the ungated default** — it may go after you personally. **Levels 6–9 are dangerous** (roast / competence / character / profanity), never for professional use; **level 9 re-confirms every run.**
5. **The universal-harm floor always holds** — the *target* decides, not the strength: it swears at the WORK, never at who you are (no threats / protected-trait slurs / family-target profanity / self-harm / sexual content), even at level 9, even with consent.

### Learning path

- **First run:** `/product-spec-critique` at the default level, then read the report (severity tally → Top-3 → by-lens).
- **Then focus:** scope to one branch, pick a lens or two, set `critique_detail_level`, try `--no-web`.
- **Voice, carefully:** stay ≤ 5 for anything shared; 6–9 are private "destroy-me" modes for the author only.
- **Integrate:** reuse/inherit/rollup, repeat-offense tracking, and the DEC bridge (`--apply-critique`).

Full walkthroughs with sample dialogues: **[`GUIDE-EN.md`](./GUIDE-EN.md)**.

### Flags

| Flag | Purpose |
|------|---------|
| `[scope]` | Artifact ID (`PRD-AUTH`, `PRD-AUTH-E1`, `PRD-AUTH-E1-S1`) or `all` (default). Ancestry always pulled. |
| `--product` / `--tech` / `--market` / `--craft` | Run only the named lens(es). Default = all four. |
| `--interactive` | Pick scope + lenses + level via prompts before running. |
| `--lang vi\|en` | Critique language. Default `vi`. IDs + frontmatter keys stay English. |
| `--no-web` | Disable the market lens's web research; with no BRD `competitors:` it flags missing grounding rather than fabricating. |
| `--fresh` / `--force` | Bypass ALL reuse — force a full fresh run (re-run every lens even if nothing changed). |
| `--refresh-web` | Force the market lens to re-fetch URLs (ignore the 14-day web-cache). `--no-web` still wins. |
| `--no-inherit` | Disable parent→child inherited context (the parent's prior blockers as the child's risk). Beats `--inherit deep`. Default ON. |
| `--no-rollup` | Disable child→parent rollup (critiqued children's verdicts aggregated onto the parent). Default ON. |
| `--inherit nearest\|deep` | Inherit depth (implies ON): `nearest` (default) = nearest critiqued ancestor + latest `all` critique; `deep` = every critiqued ancestor. |
| `--level 1..9` | Voice intensity (default 5, no-mercy). Aliases (1-6 only) `--warm`/`--gentle`/`--blunt`/`--savage`/`--no-mercy`/`--roast`; levels 7-9 use `--level 7/8/9` (no aliases). Levels 1 to 4 forbid personal attack. Level 5 lifts the redline but is the **default baseline** and is **ungated**. Levels 6+ carry a danger gate: **6 (`--roast`) ENFORCES a personal roast; 7 attacks competence (`ông/tôi`); 8 attacks character (`mày/tao`); 9 adds work-targeted profanity (`đm/vl`) and RE-CONFIRMS every run (downgrades to 8 on decline).** ⚠️ 6-9 are forbidden in professional contexts. Register at 7-9 reads `critique_address_gender`/`critique_dialect`/`critique_profanity`. **Universal-harm floor holds at every level (even 9):** profanity at the WORK is fine, never threats / protected-trait slurs / self-harm / sexual / family-target profanity. |

### Output

- **Report:** `docs/product/critique/<ts>-<scope>.md` (markdown only).
- **Marker:** `docs/product/.memory/last_critique.json` (drift snapshot).
- A PO-confirmed major finding can bridge to a Decision (`DEC-<n>`) via product-spec's `decision_register.py`.

### What it does NOT do

- **No spec editing** — it writes a critique report, never touches an artifact.
- **No CI gate** — non-deterministic by design (opinion + web + voice).
- **No code generation** — it is a critique tool, not a build tool.
- **No auto-memory** — only a PO-confirmed `DEC` bridge.
- **No HTML/PDF** (markdown v1), **no new venv**, **no new sample spec** (reuses `product-spec/examples/acme-shop`).

### Worked examples

- `examples/critique-acme-shop-all-level5.md` — the **default-level (5, no-mercy)** showcase over `product-spec/examples/acme-shop` (all four lenses, grounded citations).
- `examples/critique-acme-shop-mobile-level7..9*.md` — the harsh-level harm-floor reference set.
- `e2e/dating-app/docs/product/critique/` — a full worked spec with a scoped critique (`260603-prd-chat-lvl5.md`) exercising the inherit/rollup/cache lifecycle.

---

## Tiếng Việt

Skill (do người dùng gọi) **chê thẳng tay, có căn cứ** một bộ product spec qua bốn lăng kính (product / tech / market / craft) bằng giọng châm biếm-nhưng-có-dẫn-chứng. Nó **dùng lại** spec do `cleanmatic:product-spec` viết, mượn các phát hiện của `--validate` làm đạn, rồi nói thêm phần *vì-sao-chết / thị trường / chữ nghĩa / soi-chéo* mà `--validate` cố tình bỏ qua. Mỗi dòng đều có bằng chứng `mã:dòng`, lý do nó chết, và cách sửa. Nó **không bao giờ sửa spec** và **không bao giờ làm cổng CI**.

### Khác `--validate` ở đâu

`product-spec --validate` thì tái lập được, ấm áp, hướng-tới-PO, gắn được vào CI — đạt/trượt trên cấu trúc + giá trị cốt lõi. `/product-spec-critique` thì cố tình ngược lại: **có quan điểm, không tất định** (phán đoán LLM + tra mạng + giọng 9 mức), nên để NGOÀI cổng CI. Nó là *bên tiêu thụ* validate, không phải bản thay thế.

### Cài đặt

**Không thêm phụ thuộc mới** — dùng lại venv chung (`.claude/skills/.venv`) đã được `cleanmatic:product-spec` tạo.

```bash
./install.sh                  # đảm bảo venv chung (dùng lại nếu đã có); không hook
./install.sh --critique-hook  # tùy chọn: bật Stop hook nhắc-trôi-lệch
```

Hook nhắc-trôi-lệch **chỉ bật khi bạn chọn, không bao giờ tự đăng ký** — cài thường sẽ không đụng tới hook của bạn. `--critique-hook` ghi vào `.claude/settings.local.json` (đã gitignore); `--critique-hook-shared` ghi vào `.claude/settings.json` (được commit). Windows: `install.ps1` (`-CritiqueHook` / `-CritiqueHookShared`).

### Bắt đầu nhanh

```
/product-spec-critique                       # chê toàn bộ spec (scope=all, tốn kém)
/product-spec-critique PRD-CHECKOUT          # chê một PRD (toàn bộ tổ tiên được kéo lên làm bối cảnh)
/product-spec-critique PRD-CHECKOUT --craft --level 4   # chỉ soi chữ nghĩa, gắt
/product-spec-critique --interactive         # tự chọn phạm vi + lăng kính + mức
```

### 5 điều cần biết trước khi bắt đầu

1. **Nó xé spec ra nhưng không bao giờ sửa.** Bốn lăng kính → một báo cáo markdown trong `docs/product/critique/`. Phát hiện chỉ về spec qua `product-spec --apply-critique`, nơi bạn xác nhận từng cái.
2. **Không bao giờ làm cổng CI.** Quan điểm + web + giọng 9 mức = không tất định — `--validate` là cổng tất định, cái này là phán xét chồng lên.
3. **Soi theo chuỗi tổ tiên.** Kể cả một story cũng được chê dựa trên toàn bộ tổ tiên (epic → PRD → mục tiêu → tầm nhìn).
4. **Giọng mức 5 là mặc định không bị chặn** — có thể đá xéo cả bạn. **Mức 6–9 nguy hiểm** (chửi thẳng / năng lực / tính cách / chửi thề), không dùng nơi chuyên nghiệp; **mức 9 hỏi lại mỗi lần chạy.**
5. **Lằn ranh không-bao-giờ-vượt luôn giữ** — *đối tượng* quyết định, không phải độ gắt: nó chửi vào CÔNG VIỆC, không bao giờ nhắm vào con người bạn (không đe dọa / miệt thị đặc điểm / chửi gia đình / tự hại / tình dục), kể cả mức 9, kể cả khi bạn đồng ý.

### Lộ trình học

- **Lần đầu:** `/product-spec-critique` ở mức mặc định, rồi đọc báo cáo (bảng đếm mức độ → Top-3 → theo lăng kính).
- **Rồi thu hẹp:** soi một nhánh, chọn một hai lăng kính, đặt `critique_detail_level`, thử `--no-web`.
- **Giọng, cẩn thận:** giữ ≤ 5 cho mọi thứ sẽ chia sẻ; 6–9 là chế độ "tự hành xác" riêng tư chỉ cho tác giả.
- **Tích hợp:** tái sử dụng/kế thừa/tổng hợp, bắt lỗi lặp lại, và cầu nối DEC (`--apply-critique`).

Hướng dẫn đầy đủ kèm hội thoại mẫu: **[`GUIDE-VI.md`](./GUIDE-VI.md)**. Bảng cờ lệnh đầy đủ ở phần **English** bên trên (token cờ giữ tiếng Anh).

### Đầu ra

- **Báo cáo:** `docs/product/critique/<thời-gian>-<phạm-vi>.md` (chỉ markdown).
- **Mốc:** `docs/product/.memory/last_critique.json` (ảnh chụp trôi-lệch).
- Một phát hiện nặng được PO xác nhận có thể bắc cầu sang Quyết định (`DEC-<n>`) qua `decision_register.py` của product-spec.

### Những điều nó KHÔNG làm

- **Không sửa spec** — chỉ ghi báo cáo, không bao giờ động vào hiện vật.
- **Không làm cổng CI** — bản chất không tất định (quan điểm + web + giọng).
- **Không sinh mã** — là công cụ phê bình, không phải công cụ build.
- **Không tự ghi bộ nhớ** — chỉ có cầu nối `DEC` do PO xác nhận.
- **Không HTML/PDF** (markdown v1), **không venv mới**, **không spec mẫu mới** (dùng lại `product-spec/examples/acme-shop`).
