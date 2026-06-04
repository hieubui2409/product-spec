# cleanmatic:product-spec

User-invocable Claude skill for **non-technical product owners**: interview-driven product spec hierarchy (Vision → 1 BRD → many PRDs → Epics → Stories) with strict traceability, validation, and visualization. No code in prose, no engineering jargon.

> 🇬🇧 **English** below · 🇻🇳 **Tiếng Việt** ở nửa dưới (cuộn xuống mục **Tiếng Việt**).

---

## English

## Install

```bash
./install.sh
```

One-shot setup (idempotent). Requires Python 3.11+ and curl/wget. The installer:

1. Creates the per-skill venv at `../.venv/` (next to this folder).
2. Installs `pyyaml` (runtime) from `scripts/requirements.txt`.
3. Vendors Mermaid JS + marked + DOMPurify locally for offline HTML (graph views + body rendering).

Add `--dev` (`./install.sh --dev`) to also install `pytest` + `pytest-cov` from `scripts/requirements-dev.txt` and run the script test suite as a smoke check. The default runtime install ships only `pyyaml` and skips the test gate.

Add `--memory-hook` (`./install.sh --memory-hook`) to opt in to the Tier-1 memory-write Stop-hook reminder (registered into `.claude/settings.local.json`; `--memory-hook-shared` targets the committed `settings.json`). It is **opt-in only and never auto-registered** — a plain `./install.sh` leaves your hooks untouched. See `references/memory-enforcement.md`.

## Quickstart

Invoke from Claude Code, then **talk in plain product language** — no command memorization needed:

```
/cleanmatic:product-spec
```

With no flag, the skill detects the state of `docs/product/` and shows a menu (init, new BRD/PRD, add stories, validate, visualize, approve, summary).

### The 6 things to know before you start

1. **It's a tree with traceability.** Vision → **one** BRD → **many** PRDs → Epics → Stories. Every layer links up to its parent by ID, so any story traces to the business goal it serves.
2. **One home per fact (DRY).** Personas live in `PRODUCT.md`, goals in the BRD, **acceptance criteria only in stories**, competitors declared once in the BRD. Facts are referenced by ID, never duplicated.
3. **Structure is data; your prose is yours.** The machine reads frontmatter (IDs, `status`, `scope`, `metrics`) as source-of-truth and **never overwrites your narrative** — on `--update` it flags affected nodes and asks.
4. **Nothing is approved or reversed silently.** `approved` needs an explicit owner + date; a contradiction with an approved doc always stops for **Keep / Change / Hybrid**.
5. **Preferences are asked once.** Language, detail level, and the **engagement profile** (`interview_rigor` + `action_prompting`) are seeded early and never re-asked — change them with `--lang` or `preferences.py --set`.
6. **Fully offline; bilingual EN/VI.** Everything runs locally after install; IDs and frontmatter keys stay English, prose localizes.

### Learning path (don't learn every flag at once)

- **Day 1 — the spine:** `init → BRD → one PRD → one epic → one story → --validate`. That one thin slice teaches the whole skill.
- **Week 1:** `--approve`, `--update`, `--status`, then `--viz` / `--summary` / `--export` to share. Set `--lang` + the engagement profile early.
- **As you grow:** the decision register (`--decision`), `--apply-critique`, the validate Memory pass, `--reflect`, the opt-in reminder hook.
- **Shortcut:** paste a brain-dump and let `--auto` decompose it (it still confirms every ambiguous split).

Full walkthroughs with sample conversations: **[`GUIDE-EN.md`](./GUIDE-EN.md) / [`GUIDE-VI.md`](./GUIDE-VI.md)**.

### Flags (shortcuts for the conversational asks above)

`--product`, `--brd`, `--prd <slug>`, `--epic`, `--story`, `--auto` (braindump → decompose), `--discover <path(s)>` (seed the interview from raw transcripts/notes), `--validate`, `--strict`, `--approve`, `--update`, `--decision`, `--apply-critique <report>` (turn a critique report into recorded decisions), `--status`, `--summary [--audience exec|release-notes]`, `--viz <view>` (incl. `audit`), `--format ascii|mermaid|html`, `--lang en|vi`, `--voice` (record PO voice), `--reflect` (retroactive memory harvest). Engagement knobs `interview_rigor` (light/standard/deep) + `action_prompting` (minimal/standard/proactive) tune interview challenge-depth and next-action density; set them deterministically via `preferences.py --set KEY=VALUE` (load→merge→save).

## Layout

- `SKILL.md` — lean skeleton (~300 lines), the canonical entry point Claude reads.
- `references/` — full prose for each flag (frontmatter+ID spec, document model, validation rules, visualization spec, interview banks, workflow guides).
- `scripts/` — Python (stdlib + pyyaml). Structural only; LLM owns judgment. Run via `../.venv/bin/python3 scripts/<name>.py --root <project-dir>`.
- `assets/templates/` — markdown templates with `{{token}}` substitution.
- `assets/vendor/` — vendored offline runtimes: `mermaid.min.js` (graph views) + `marked.min.js` + `purify.min.js` (body rendering).
- `eval/` — scenario evals.
- `examples/acme-shop/` — worked sample product spec.

## Further reading

- **[`GUIDE-VI.md`](./GUIDE-VI.md) / [`GUIDE-EN.md`](./GUIDE-EN.md)** — end-user guide for the non-technical PO: core concepts, a learning path, then every use case as a full sample conversation (natural-language way preferred + flag equivalent), with worked examples from `examples/acme-shop`.
- Top of `SKILL.md` — flags table + no-flag menu + output contract.
- `../../../CLAUDE.md` (repo-root) — operating principles loaded automatically by Claude Code.
- `references/frontmatter-and-id-spec.md` — canonical YAML schema and parent-scoped ID grammar (`BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1`, `PRD-AUTH-E1-S1`).

---

## Tiếng Việt

Skill Claude (do người dùng gọi) cho **product owner không chuyên kỹ thuật**: dựng cây tài liệu sản phẩm theo phỏng vấn (Tầm nhìn → 1 BRD → nhiều PRD → Epic → Story) với truy vết chặt, kiểm tra, và trực quan hóa. Không code trong văn bản, không thuật ngữ kỹ thuật.

### Cài đặt

```bash
./install.sh
```

Cài một phát (chạy lại được nhiều lần). Cần Python 3.11+ và curl/wget. Bộ cài: (1) tạo venv riêng cho skill ở `../.venv/`; (2) cài `pyyaml`; (3) nhúng sẵn Mermaid + marked + DOMPurify để xuất HTML ngoại tuyến. Thêm `--dev` để cài `pytest` và chạy test; thêm `--memory-hook` để bật lời nhắc bộ nhớ (mặc định tắt, không bao giờ tự bật).

### Bắt đầu nhanh

Gọi từ Claude Code, rồi **nói bằng ngôn ngữ sản phẩm bình thường** — không cần nhớ lệnh:

```
/cleanmatic:product-spec
```

Không kèm cờ, skill phát hiện trạng thái `docs/product/` và hiện menu (khởi tạo, BRD/PRD mới, thêm story, kiểm tra, trực quan hóa, ký duyệt, tóm tắt).

### 6 điều cần biết trước khi bắt đầu

1. **Đây là một cây có truy vết.** Tầm nhìn → **một** BRD → **nhiều** PRD → Epic → Story. Mỗi tầng liên kết lên cha bằng mã, nên mọi story đều truy được về mục tiêu kinh doanh nó phục vụ.
2. **Một nhà cho mỗi dữ kiện (DRY).** Persona ở `PRODUCT.md`, mục tiêu ở BRD, **tiêu chí nghiệm thu chỉ ở story**, đối thủ khai một lần ở BRD. Dữ kiện tham chiếu theo mã, không lặp lại.
3. **Cấu trúc là dữ liệu; câu chữ là của bạn.** Máy đọc frontmatter (mã, `status`, `scope`, `metrics`) làm nguồn-sự-thật và **không bao giờ ghi đè văn bạn viết** — khi `--update` nó gắn cờ phần ảnh hưởng rồi hỏi.
4. **Không gì được duyệt hay đảo ngược âm thầm.** `approved` cần người duyệt + ngày tường minh; mâu thuẫn với tài liệu đã duyệt luôn dừng lại để bạn chọn **Giữ / Đổi / Kết hợp**.
5. **Tùy chọn chỉ hỏi một lần.** Ngôn ngữ, mức chi tiết, và **hồ sơ tương tác** (`interview_rigor` + `action_prompting`) được hỏi sớm rồi không hỏi lại — đổi qua `--lang` hoặc `preferences.py --set`.
6. **Chạy hoàn toàn ngoại tuyến; song ngữ EN/VI.** Mọi thứ chạy cục bộ sau khi cài; mã và khóa frontmatter giữ tiếng Anh, phần văn thì bản địa hóa.

### Lộ trình học (đừng học hết cờ một lúc)

- **Ngày 1 — xương sống:** `khởi tạo → BRD → một PRD → một epic → một story → --validate`. Một lát cắt mỏng đó dạy bạn cả skill.
- **Tuần 1:** `--approve`, `--update`, `--status`, rồi `--viz` / `--summary` / `--export` để chia sẻ. Đặt `--lang` + hồ sơ tương tác sớm.
- **Khi đã quen:** Sổ Quyết Định (`--decision`), `--apply-critique`, lượt Bộ nhớ trong validate, `--reflect`, hook nhắc tùy chọn.
- **Lối tắt:** dán một "bãi ý tưởng" và để `--auto` tự phân rã (vẫn hỏi bạn ở mọi chỗ chia tách mơ hồ).

Hướng dẫn đầy đủ kèm hội thoại mẫu: **[`GUIDE-VI.md`](./GUIDE-VI.md)**. Bảng cờ lệnh đầy đủ ở phần **English** bên trên (token cờ giữ tiếng Anh).
