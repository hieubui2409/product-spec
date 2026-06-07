# cleanmatic:telemetry

A **read-only** skill that tells a (non-technical) product owner, **in plain Vietnamese**, how their skills are being used, whether scripts and subagents are healthy, and whether the spec validate passed. Eight opinionated lenses + four output formats; no editing, no CI gate, no network calls.

> 🇬🇧 **English** below · 🇻🇳 **Tiếng Việt** ở nửa dưới (cuộn xuống mục **Tiếng Việt**).

---

## English

### What it is

Three things in one read-only window:

1. **Mức dùng (Usage)** — which skills are invoked, how often, approx. tokens per skill, and which owned skills are never touched.
2. **Sức khỏe (Health)** — which scripts error, run slowly, whether subagents succeed, whether memory is tidy.
3. **A thin internal-quality proxy** — did `product-spec --validate` pass? (This is **not** market effectiveness — that is E3, deliberately deferred.)

### How to run

```bash
/cleanmatic:telemetry                    # default: all lenses, ascii format, Vietnamese
/cleanmatic:telemetry --lens usage       # one lens at a time
/cleanmatic:telemetry --format md --top 10 --lang en    # markdown, top-10 items, English
```

Flags (all optional):

| Flag | Values | Default | Purpose |
|------|--------|---------|---------|
| `--lens` | `usage` / `session` / `health` / `reliability` / `workflow` / `validate` / `memory` / `forensics` / `all` | `all` | Which lens to run |
| `--format` | `ascii` / `md` / `mermaid` / `json` | `ascii` | Output format |
| `--days` | integer | 30 | Lookback period (days) |
| `--top` | integer | (md only) | Limit markdown to top N items |
| `--lang` | `vi` / `en` | `vi` | Fixed label language (VI is default, native quality) |
| `--session` | UUID | — | For forensics: reconstruct one session |
| `--all-sessions` | — | — | For forensics: list all session IDs |

### Install

```bash
./install.sh                    # ensures shared venv, registers telemetry hooks
./install.sh --no-hooks         # runtime only, does NOT auto-register hooks
```

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1 -NoHooks
```

Requires Python 3.9+. Stdlib-only → runs on system `python3`; no venv needed on recipients.

### The 8 lenses at a glance

| Lens | Reads | Shows | Gated? |
|------|-------|-------|--------|
| `usage` | Invocation logs + transcripts | Top invoked skills, token weight (approx), never-used | Below ~5 data points |
| `session` | Session summaries | Count, avg/median duration, co-occurrence, file+tool counts | Below ~5 data points |
| `health` | Script telemetry | Per-script run count, error rate, avg ms (approx) | Below ~5 data points |
| `reliability` | Subagent outcomes | Success / api_error / timeout / blocked / unknown per type | Below ~5 data points |
| `workflow` | Invocations + declared chains | Actual skill chains vs. routing-doc chains; deviations | Below ~5 data points |
| `validate` | Last-validate marker + script runs | Validate pass/fail (internal quality proxy, NOT E3) | Below ~5 data points |
| `memory` | `.claude/projects/*/memory/` | Orphans, dead index entries, broken `[[links]]`, staleness | Always visible (read-only) |
| `forensics` | Session transcript JSONL | One session reconstructed (skills, tools, tokens, duration) | Requires `--session <id>` |

### How lenses work (deterministic gather → LLM narrates)

The skill **never computes** — a Python script (`analyze_telemetry.py`) gathers deterministically, then the LLM **narrates** the results in plain Vietnamese. The split:

- **Script** (`.claude/skills/telemetry/scripts/analyze_telemetry.py`): stdlib-only, no judgment, produces JSON aggregates.
- **Skill** (the LLM): reads the aggregates, narrates them honestly, phrases recommendations as **gợi ý** (suggestions) only.

```bash
# In the cleanmatic dev repo, use the shared venv:
.claude/skills/.venv/bin/python3 .claude/skills/telemetry/scripts/analyze_telemetry.py \
  --lens all --format ascii --days 30

# On recipients (where system python3 is available):
python3 .claude/skills/telemetry/scripts/analyze_telemetry.py \
  --lens all --format ascii --days 30
```

### Data source

Append-only JSONL sinks under `.claude/telemetry/` (gitignored, runtime data only):

- `invocations.jsonl` — skill invocations.
- `sessions.jsonl` — session summaries.
- `hook-telemetry.jsonl` — script runs + errors.
- `subagent-outcomes.jsonl` — subagent success/failure.
- `last_validated.json` — validate marker snapshot.

Five fail-open hooks auto-register on install (opt out: `register_telemetry_hooks.py --remove`).

### Low-volume gate ("chưa đủ dữ liệu")

Below ~5 data points, a lens shows raw counts + **"chưa đủ dữ liệu" (insufficient data)** and suppresses recommendations. On a thin repo, **most lenses ARE gated** — the report says so plainly; no trends are invented.

### The honesty gate (mandatory)

Every report **ends** with **"Cái này KHÔNG đo được"** (This cannot be measured):

- **E3 / market outcome** — whether the product wins in the market. Telemetry sees *usage*, not *value*.
- **Any gated lens** — named explicitly with "chưa đủ dữ liệu".
- **Approx disclaimers** — tokens, ms, exit codes are directional (ước lượng), never exact.

### What it is NOT

- **Not** a market/user-outcome metric (E3). The validate proxy = "spec well-formed", not "users adopted".
- **Not** a writer — never edits specs, code, the catalog, or memory. No `--apply`, no fixes.
- **Not** billing-exact — token attribution and `ms` are directional estimates.
- **Not** a CI gate — opinion-free numbers for the PO to read; nothing blocks on it.
- **Not** a crash-log analyzer — instrumented scripts lack rich `errors.jsonl`; deferred to BACKLOG.

### Learning path

- **First run:** `/cleanmatic:telemetry` at the default (all lenses, ascii) and **read the report**. The structure: tóm tắt (summary) → mức dùng (usage) → sức khỏe (health) → sessions → workflow → validate → memory → "Cái này KHÔNG đo được" (honesty section).
- **Then focus:** `--lens usage` to see which skills are cold, `--lens health` to spot script errors, `--lens validate` for internal quality.
- **Experiment:** try `--format md --top 5` for a concise markdown table, `--format mermaid` for a pie/bar chart.
- **Deep dive:** `--session <id>` to reconstruct a single session's skill/tool/token flow.

### Output

- **Report:** printed to terminal (or written if you redirect stdout).
- **Formats:**
  - `ascii` — terminal-friendly one-glance read.
  - `md` — markdown table + narrative (copy-paste friendly).
  - `mermaid` — pie/bar charts, fenced, no network/JS required.
  - `json` — raw aggregates for scripting.
- **Marker:** `/etc/claude/projects/<root>/memory/` (read-only; script gathers, does not write).

### Boundaries

- **Read-only.** No edits to spec/code/catalog/memory; no network; no venv override required on recipients.
- **No `--apply`.** This is a diagnostic skill, not a fixer. Recommendations are **gợi ý** only.
- **Stdlib-only.** Runs on system `python3` without venv (venv required only during development in cleanmatic repo).
- **GATE-NEVER-ASSUME / GATE-NO-SILENT-REVERSAL:** Not applicable in the usual sense (nothing is written/approved), but the skill still never fabricates a metric — an absent signal is reported as absent.

### Caveats

- **Never-used external skills** (e.g., `ck:code-review`, `com:mcp-builder`) are **not listed** — PO doesn't own them, so non-use is normal. Only **never-used cleanmatic skills** (`cleanmatic:*`) are flagged.
- **Token weight is approximate.** Derived from transcript length + a rough per-skill coefficient; never exact, always labeled "ước lượng".
- **The validate proxy is internal quality only** — see the narration contract (`references/narration-contract.md`) for what "internal quality" means vs. E3.

### Deep links

- **Narration contract (rules for honest language):** `references/narration-contract.md`
- **Operating contract (full SKILL.md):** `SKILL.md`
- **Full walkthrough + use cases:** `GUIDE-EN.md`
- **Lens modules:** `.claude/skills/telemetry/scripts/lens_*.py`
- **Script (deterministic gather):** `.claude/skills/telemetry/scripts/analyze_telemetry.py`

### Worked examples

- (TBD in future releases)

---

## Tiếng Việt

Skill (do người dùng gọi) **chỉ đọc không sửa**, nói cho người làm sản phẩm (không kỹ thuật) **bằng tiếng Việt bình thường**: skills đang được dùng cách nào, script/subagent có khỏe không, spec validate có pass không. Tám lăng kính + bốn định dạng đầu ra; không sửa, không cổng CI, không gọi mạng.

### Đó là cái gì

Ba thứ trong một cửa sổ chỉ-đọc:

1. **Mức dùng (Usage)** — skill nào được gọi, bao nhiêu lần, tokens ước lượng mỗi skill, và skill nào của mình chưa dùng bao giờ.
2. **Sức khỏe (Health)** — script nào chạy lỗi, chạy chậm, subagent có thành công không, bộ nhớ có gọn không.
3. **Một tín hiệu chất lượng nội bộ** — `product-spec --validate` có pass không? (Đây **KHÔNG PHẢI** hiệu quả thị trường — đó là E3, cố tình để dành.)

### Cách chạy

```bash
/cleanmatic:telemetry                    # mặc định: tất cả lăng kính, ascii, tiếng Việt
/cleanmatic:telemetry --lens usage       # từng lăng kính một
/cleanmatic:telemetry --format md --top 10 --lang en    # markdown, top-10, tiếng Anh
```

Cờ (đều là tùy chọn):

| Cờ | Giá trị | Mặc định | Tác dụng |
|------|---------|---------|---------|
| `--lens` | `usage` / `session` / `health` / `reliability` / `workflow` / `validate` / `memory` / `forensics` / `all` | `all` | Lăng kính nào |
| `--format` | `ascii` / `md` / `mermaid` / `json` | `ascii` | Định dạng đầu ra |
| `--days` | số nguyên | 30 | Khoảng thời gian nhìn lại (ngày) |
| `--top` | số nguyên | (chỉ md) | Giới hạn markdown top N mục |
| `--lang` | `vi` / `en` | `vi` | Ngôn ngữ nhãn cố định (VI mặc định, chất lượng native) |
| `--session` | UUID | — | Forensics: dựng lại một phiên |
| `--all-sessions` | — | — | Forensics: liệt kê mọi ID phiên |

### Cài đặt

```bash
./install.sh                    # tạo venv chung, đăng ký hook telemetry
./install.sh --no-hooks         # chỉ runtime, không tự động đăng ký hook
```

Windows: `powershell -ExecutionPolicy Bypass -File .\install.ps1` (thêm `-NoHooks` nếu cần). Cần Python 3.9+. Chỉ dùng STDLIB → chạy trên system `python3`; người nhận không cần venv.

### 8 lăng kính sơ lược

| Lăng kính | Đọc từ | Hiển thị | Bị chặn? |
|------|-------|-------|--------|
| `usage` | Log gọi + transcript | Top invoked skill, token weight (ước lượng), chưa dùng | < ~5 data point |
| `session` | Session summary | Count, avg/median duration, co-occurrence, file+tool | < ~5 data point |
| `health` | Script telemetry | Per-script run, error rate, avg ms (ước lượng) | < ~5 data point |
| `reliability` | Subagent outcome | Success / api_error / timeout / blocked / unknown | < ~5 data point |
| `workflow` | Invocation + declared chain | Actual skill chain vs routing-doc; sai lệch | < ~5 data point |
| `validate` | Validate marker + script run | Validate pass/fail (chất lượng nội bộ, KHÔNG E3) | < ~5 data point |
| `memory` | `.claude/projects/*/memory/` | Hạng mục mồ côi, dead index, broken `[[link]]`, lâu cũ | Luôn thấy (chỉ-đọc) |
| `forensics` | Session transcript JSONL | Một phiên dựng lại (skill, tool, token, duration) | Cần `--session <id>` |

### Lăng kính hoạt động cách nào (gather định tính → LLM kể chuyện)

Skill **không tính toán gì** — một Python script (`analyze_telemetry.py`) gather định tính, rồi LLM **kể chuyện** kết quả bằng tiếng Việt bình thường. Phân công:

- **Script** (`.claude/skills/telemetry/scripts/analyze_telemetry.py`): chỉ STDLIB, không phán đoán, ra JSON aggregates.
- **Skill** (LLM): đọc aggregates, kể chuyện với thật lòng, đề xuất dưới dạng **gợi ý** chứ không phải lệnh.

```bash
# Trong repo cleanmatic, dùng venv chung:
.claude/skills/.venv/bin/python3 .claude/skills/telemetry/scripts/analyze_telemetry.py \
  --lens all --format ascii --days 30

# Người nhận (có system python3):
python3 .claude/skills/telemetry/scripts/analyze_telemetry.py \
  --lens all --format ascii --days 30
```

### Nguồn dữ liệu

JSONL sink chỉ-append dưới `.claude/telemetry/` (gitignore, chỉ runtime):

- `invocations.jsonl` — skill gọi.
- `sessions.jsonl` — session tóm tắt.
- `hook-telemetry.jsonl` — script chạy + lỗi.
- `subagent-outcomes.jsonl` — subagent thành công/thất bại.
- `last_validated.json` — validate marker snapshot.

5 hook tự đăng ký fail-open khi cài (opt out: `register_telemetry_hooks.py --remove`).

### Cổng dữ liệu ít ("chưa đủ dữ liệu")

< ~5 data point, lăng kính hiển thị count thô + **"chưa đủ dữ liệu"** và chặn gợi ý. Trên repo mỏng, **hầu hết lăng kính BỊ CHẶN** — báo cáo nói thẳng; không tạo xu hướng.

### Cổng thật lòng (bắt buộc)

Mỗi báo cáo **kết thúc** bằng **"Cái này KHÔNG đo được"**:

- **E3 / hiệu quả thị trường** — sản phẩm thắng trên thị trường không. Telemetry thấy *usage*, không *value*.
- **Lăng kính bị chặn nào** — liệt kê tường minh với "chưa đủ dữ liệu".
- **Tuyên bố ước lượng** — token, ms, exit code là ước lượng, không chính xác.

### Những điều nó KHÔNG phải

- **Không phải** metric E3 / hiệu quả thị trường. Proxy validate = "spec tốt lành", không "user nhận".
- **Không phải** writer — không sửa spec, code, catalog, memory. Không `--apply`, không fix.
- **Không phải** đúng tính tiền — token + ms là ước lượng, không exact.
- **Không phải** cổng CI — số liệu neutral cho PO đọc; không chặn gì.
- **Không phải** crash-log analyzer — script instrumented thiếu rich `errors.jsonl`; đợi BACKLOG.

### Lộ trình học

- **Lần đầu:** `/cleanmatic:telemetry` mặc định (all lense, ascii) rồi **đọc báo cáo**. Cấu trúc: tóm tắt → mức dùng → sức khỏe → session → workflow → validate → memory → "Cái này KHÔNG đo được" (phần thật lòng).
- **Rồi thu hẹp:** `--lens usage` xem skill nào lạnh, `--lens health` bắt script lỗi, `--lens validate` chất lượng nội bộ.
- **Thí nghiệm:** try `--format md --top 5` markdown gọn, `--format mermaid` biểu đồ pie/bar.
- **Sâu hơn:** `--session <id>` dựng lại một phiên (skill/tool/token flow).

### Đầu ra

- **Báo cáo:** in ra terminal (hoặc ghi nếu redirect stdout).
- **Định dạng:**
  - `ascii` — terminal nhìn qua nhanh.
  - `md` — bảng markdown + kể chuyện (copy-paste dễ).
  - `mermaid` — pie/bar chart, fenced, không mạng/JS.
  - `json` — aggregates thô cho script.
- **Mốc:** `/etc/claude/projects/<root>/memory/` (chỉ-đọc; script gather, không ghi).

### Ranh giới

- **Chỉ-đọc.** Không sửa spec/code/catalog/memory; không mạng; người nhận không cần venv.
- **Không `--apply`.** Đây là diagnostic skill, không fixer. Gợi ý thôi.
- **STDLIB-only.** Chạy trên system `python3` mà không venv (venv chỉ cần dev trong cleanmatic repo).
- **GATE-NEVER-ASSUME / GATE-NO-SILENT-REVERSAL:** Không áp dụng thường lệ (không viết/approved), nhưng skill không bao giờ bịa metric — tín hiệu vắng được báo là vắng.

### Cảnh báo

- **Skill external chưa dùng** (e.g., `ck:code-review`, `com:mcp-builder`) **KHÔNG liệt kê** — PO không sở hữu, nên vắng là bình thường. Chỉ **skill cleanmatic chưa dùng** (`cleanmatic:*`) được cảnh báo.
- **Token weight ước lượng.** Từ transcript length + hệ số rough per-skill; không exact, luôn ghi "ước lượng".
- **Validate proxy chỉ chất lượng nội bộ** — xem narration contract (`references/narration-contract.md`) để hiểu "chất lượng nội bộ" vs E3.

### Đường dẫn sâu

- **Hợp đồng kể chuyện (quy tắc ngôn ngữ thật lòng):** `references/narration-contract.md`
- **Hợp đồng hoạt động (SKILL.md đầy đủ):** `SKILL.md`
- **Hướng dẫn đầy đủ + use case:** `GUIDE-VI.md`
- **Module lăng kính:** `.claude/skills/telemetry/scripts/lens_*.py`
- **Script (gather định tính):** `.claude/skills/telemetry/scripts/analyze_telemetry.py`

### Ví dụ làm xong

- (Sẽ có ở phiên bản tương lai)
