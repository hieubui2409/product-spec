Đã đủ bằng chứng. Tổng hợp báo cáo.

## TÓM TẮT

Quy ước: `PO=/home/hieubt/Documents/Cleanmatic-ERP`, `KIT=/home/hieubt/Documents/product-spec`. PO cài **claude-pack v1.1.0** (built 2026-06-03T05:39:31Z, source `1c5113f` = đúng tag `claude-pack-v1.1.0`), toàn vẹn tuyệt đối: **347/347 file khớp SHA256, 0 missing, 0 mismatch** — PO không vá tay file kit nào. PO đứng sau **9 release** (1.2.0→1.4.0 + 2.0.0→2.3.0), tức **50 commits / 485 files / +31431 −12618 dòng** so với HEAD v2.3.0; trớ trêu: PO cài ngày 06-04 — đúng ngày 1.2.0 và 1.3.0 phát hành, lỗi thời ngay từ ngày đầu. Ba phát hiện đắt nhất: (1) **installer vỡ trên macOS bash 3.2** (`declare -A` line 149) — PO đã dính thật, ghi trong change-log của họ, và HEAD **vẫn chưa sửa** dù quảng bá "multiplatform recipient installer"; (2) **`.session.md` đóng băng 2026-06-02 chứa câu trả lời PO đã bị supersede** (30 hub vs ≥50/DEC-43; "Sepay VÀ Casso MVP" vs DEC-4 chỉ Sepay) trong khi GATE-NEVER-ASSUME cho phép assume từ chính file này; (3) **PO tự chế GitHub Actions CI** (stock python-package.yml) sẽ fail mọi push (pytest exit 5) — tín hiệu nhu cầu CI-validate mà kit chưa từng ship cho người nhận. Tài liệu PO sinh ra nhìn chung đúng grammar (DEC-1→44 liền mạch, ID đúng chuẩn) nhưng frontmatter mang nhiều field ngoài spec của chính kit (cả 2 bản).

## FINDINGS

### [CVR-F01] Recipient installer chết trên macOS bash 3.2 — PO dính thật, HEAD vẫn chưa sửa
- Mức độ: Critical
- Loại: CORRECTNESS
- Bằng chứng:
  - `PO/docs/product/change-log.md:711-718`: "## 2026-06-04 — Cài skill + migrate toàn spec sang format chuẩn v2.0.0 … Cài `.claude/skills` (thủ công vì installer gốc cần bash 4+; macOS có bash 3.2)."
  - `PO/.claude/skills/claude-pack/assets/templates/install.sh.template:149`: `declare -A SKILL_VERDICT` (associative array = bash 4+).
  - `KIT/.claude/skills/release/assets/templates/install.sh.template:149`: y nguyên `declare -A SKILL_VERDICT`.
  - `grep -in "bash" KIT/.claude/skills/release/CHANGELOG.md` → 0 match (chưa từng ghi nhận fix).
  - `PO/INSTALL.md:37` hướng dẫn `bash install.sh` (macOS `bash` mặc định = 3.2).
- Phân tích: Kit cam kết "multiplatform recipient installer" (mô tả skill release) và 1.3.0/2.0.0 khoe installer e2e + SemVer matrix tests — nhưng e2e chạy trên CI Linux, chưa bao giờ chạm ca macOS bash 3.2. PO non-technical phải cài tay (may mà thành công — 347/347 hash khớp chứng tỏ copy đúng), và feedback lỗi này chưa bao giờ quay về kit: 6 release sau, template vẫn vỡ y chỗ cũ. Mọi PO macOS tiếp theo sẽ dính lại.
- Đề xuất: Sửa template bỏ `declare -A` (dùng cấu trúc bash-3-compatible hoặc shebang `#!/usr/bin/env bash` + check `BASH_VERSINFO` fail sớm với thông báo rõ); thêm leg test macOS/bash3.2 vào installer e2e; ghi CHANGELOG release skill.

### [CVR-F02] PO đứng sau 9 release — bảng delta năng lực và hệ quả quan sát được
- Mức độ: High
- Loại: FEATURE-GAP
- Bằng chứng: `git -C KIT tag -l` (15 tag); `git -C KIT log --oneline claude-pack-v1.1.0..product-spec-v2.3.0 | wc -l` = 50; `git -C KIT diff --stat` = "485 files changed, 31431 insertions(+), 12618 deletions(-)"; `KIT/CHANGELOG.md:20-253`. PO: `MANIFEST.json:2-4` (`bundle_version: 1.1.0`, built 2026-06-03), `git -C PO tag` không áp dụng (repo PO chỉ 2 commit 2026-06-10).
- Phân tích — từng nhóm PO KHÔNG có, kèm hệ quả thật trong PO-repo:

| Nhóm (release) | PO không có | Hệ quả quan sát được trong PO-repo |
|---|---|---|
| `--apply-critique`/`--discover`/`--summary --audience`/`--viz audit` (1.2.0, CHANGELOG.md:249-251) | đường chính thống áp critique vào spec | 15 báo cáo critique áp tay qua change-log/DEC — chi tiết CVR-F05 |
| Engagement knobs + end-of-session forcing (1.3.0, CHANGELOG.md:193-200) | Closing-the-Loop cập nhật `.session.md` | `.session.md` đóng băng 06-02, chứa answer superseded — CVR-F03 |
| Finding-fingerprint (1.4.0, CHANGELOG.md:176-181) | dedup repeat-finding | index 0/20 entry có `finding_fingerprint`; TASK×3, COMM×4 re-run — CVR-F04 |
| Telemetry + 5 sink hooks auto-register (2.0.0/2.1.0, CHANGELOG.md:82-95) | mọi số liệu usage/health | `ls PO/.claude/telemetry` → "No such file or directory"; 8 ngày làm việc không số liệu — CVR-F06 |
| "Tests never ship" (2.1.0, CHANGELOG.md:98) | — (PO nhận NGƯỢC: có tests) | 67 đường dẫn `scripts/tests` trong MANIFEST.json — CVR-F08 |
| AGPL LICENSE + CONTRIBUTING (2.2.1, CHANGELOG.md:52-57) | điều khoản sử dụng | `ls PO/LICENSE*` → "no matches found" — CVR-F12 |
| `--learn`/OUT register (2.3.0, CHANGELOG.md:21-23) | vòng đo outcome hậu approve | spec vừa "ĐÓNG TRỌN BỘ" 06-10, không có chỗ ghi target-vs-actual — CVR-F14 |
- Đề xuất: Cung cấp đường nâng cấp được tài liệu hoá 1.1.0→2.3.0 (kèm migration note cho rename — xem CVR-F11) và một kênh thông báo release cho người nhận bundle.

### [CVR-F03] `.session.md` đóng băng 2026-06-02 chứa quyết định đã bị supersede — bẫy cho GATE-NEVER-ASSUME
- Mức độ: High
- Loại: UX-PO
- Bằng chứng:
  - `PO/docs/product/.session.md:4-5`: `last_updated: 2026-06-02`, `phase: initial-spec-complete`; dòng "BRD-G1 metric: 30 hub (không phải 50)"; "Cổng thanh toán: cả Sepay VÀ Casso từ MVP (song song)"; "Tất cả artifacts hiện ở trạng thái `draft`".
  - Thực tế hiện nay: `PO/docs/product/brd.md:16` metric "≤20 lên ≥50 … (khớp North Star VISION — DEC-43, supersede mốc 30 trước)"; `PO/docs/product/decisions.md:43` "## DEC-4 — MVP chỉ tích hợp Sepay; Casso để next"; `PO/docs/product/vision.md:6-7` `status: approved` 2026-06-10.
  - `KIT/CLAUDE.md` GATE-NEVER-ASSUME: "Assume ONLY when: the PO already answered (`.session.md`/`PRODUCT.md`)".
  - `KIT/CHANGELOG.md:198-200` (1.3.0): "End-of-session forcing-function folded into the existing Closing-the-Loop batch".
- Phân tích: Kit coi `.session.md` là nguồn hợp lệ để assume thay vì hỏi. Bản PO dùng (trước 1.3.0) không có forcing-function giữ file này tươi → 8 ngày làm việc, file chứa 3 mệnh đề đã sai (metric 30 vs 50, Casso-MVP vs DEC-4, "toàn draft" vs toàn approved). Một phiên LLM mới hoàn toàn có thể assume "Casso trong MVP" mà không hỏi — silent reversal đúng nghĩa, do chính dữ liệu mồi của kit.
- Đề xuất: Khi nâng cấp PO lên bản có Closing-the-Loop, thêm bước one-shot "reconcile `.session.md` với Decision Register" (mọi answer trong `.session.md` mâu thuẫn DEC phải bị gạch/cập nhật kèm pointer DEC); cân nhắc để GATE ưu tiên `decisions.md` hơn `.session.md` khi hai nguồn lệch.

### [CVR-F04] Trí nhớ critique chỉ ghi 3/15 run và không có fingerprint — re-critique mất bộ nhớ
- Mức độ: High
- Loại: FEATURE-GAP
- Bằng chứng:
  - `ls PO/docs/product/critique/` = 15 báo cáo, trong đó PRD-TASK ×3 (20260609T121803Z/125531Z/131658Z), PRD-COMM ×4 (140204Z/154942Z/163510Z/164651Z).
  - `PO/docs/product/.memory/critique-findings-index.json`: 20 entries, `report_ts` chỉ gồm `{025434Z: 8, 084007Z: 8, 121803Z: 4}` (CARE/FINANCE/TASK-lần-đầu); **0/20** entry có `finding_fingerprint`.
  - `PO/docs/product/.memory/critique-state.json`: chỉ 3 key (PRD-CARE, PRD-FINANCE, PRD-TASK), TASK `last_ts: 2026-06-09T12:18` — 2 run TASK sau và 4 run COMM, PAYMENT, REPORT, 2 run `all`, HR (06-05), all (06-04) đều không để lại dấu vết.
  - `KIT/CHANGELOG.md:176-181` (1.4.0): fingerprint để "a logical blocker re-critiqued after a line shift is counted once instead of inflating the rollup".
- Phân tích: PO chạy critique lặp nhiều vòng trong một ngày (TASK 3 lần trong 1 giờ, COMM 4 lần trong 3 giờ — pattern sửa-rồi-chạy-lại) nhưng 12/15 run không được index/state ghi nhận → repeat-offense memory mà skill quảng cáo gần như không hoạt động với dữ liệu thật; bản 1.4.0 (fingerprint) lẫn polish 2.0.0 đều chưa tới tay PO. Nguyên nhân 12 run không được ghi: chưa xác định (bước ghi index do LLM flow đảm nhiệm, không script nào cưỡng chế) — bản thân điều đó là điểm yếu thiết kế quan sát được.
- Đề xuất: Nâng cấp critique lên 1.2.x; thêm bước script-enforced (hook hoặc post-run check) xác nhận index/state được cập nhật sau mỗi report; backfill index từ 12 report mồ côi nếu PO upgrade.

### [CVR-F05] Không có `--apply-critique`: 15 báo cáo critique được áp tay qua change-log/DEC
- Mức độ: Medium
- Loại: FEATURE-GAP
- Bằng chứng: `grep -c "apply-critique|--discover|--learn" PO/.claude/skills/product-spec/SKILL.md` = **0** (HEAD = 8); PO product-spec `SKILL.md:11` version `2.0.0` — `--apply-critique` vào product-spec 2.1.0 (`KIT/CHANGELOG.md:249-251`); `grep -c critique PO/docs/product/change-log.md` = 58; `change-log.md:284`: "**Nguồn:** PO rule 4 mục DEC-worthy sau critique".
- Phân tích: Vòng lặp critique→sửa của PO tồn tại và chạy nhiều (58 lần nhắc "critique" trong change-log, 44 DEC) nhưng hoàn toàn thủ công qua LLM ad-hoc — đúng cái lỗ mà 1.2.0 vá một ngày sau khi PO build bundle. Chi phí: các vòng COMM ×4/TASK ×3 ở CVR-F04 chính là chi phí lặp của flow tay.
- Đề xuất: Ưu tiên `--apply-critique` trong gói nâng cấp cho PO; kiểm tra các sửa đổi tay đã làm có khớp semantics `--apply-critique` không trước khi bật.

### [CVR-F06] Zero telemetry: 8 ngày vận hành thật không một dòng số liệu
- Mức độ: Medium
- Loại: FEATURE-GAP
- Bằng chứng: `ls -d PO/.claude/telemetry` → "No such file or directory"; PO không có `settings.json` trong `.claude/` (ls lỗi); `KIT/CHANGELOG.md:82-91` (2.1.0): 5 sink hooks "auto-registered by the installer"; khối lượng PO thật: 15 critique, 63 entry change-log, 102 story — đều "vô hình" với kit.
- Phân tích: Toàn bộ giá trị của skill telemetry (usage & health, script lỗi/chậm, sub-agent reliability) ra đời từ 2.0.0/2.1.0 — sau PO 4-5 ngày. Hệ quả thật: không ai (kể cả chủ kit) biết script nào lỗi/chậm trong 8 ngày PO dùng; lỗi installer macOS (CVR-F01) chỉ tình cờ lộ qua change-log prose của PO chứ không qua kênh nào của kit.
- Đề xuất: Khi nâng cấp, installer 2.1.0+ tự đăng ký sinks — kiểm tra idempotent trên repo đã có dữ liệu cũ; cân nhắc cơ chế "phone-home-free feedback" (file export PO gửi tay) vì PO repo cho thấy feedback không tự quay về.

### [CVR-F07] PO tự chế CI GitHub Actions — fail mọi push (pytest exit 5), kit không ship recipient CI
- Mức độ: High
- Loại: UX-PO
- Bằng chứng: `git -C PO log` → `9df10cf 2026-06-10 07:58:11 +0700 Add GitHub Actions workflow for Python package` (22 phút sau initial commit); `PO/.github/workflows/python-package.yml:38-40`: step `pytest` trần; mô phỏng tại sandbox root (cùng cấu trúc: toàn markdown + code Python nằm trong hidden dir `.claude` mà pytest mặc định bỏ qua): `python3 -m pytest -q -p no:cacheprovider` → "no tests ran in 0.01s", **EXIT=5** → step fail → workflow đỏ.
- Phân tích: PO non-technical vừa đẩy repo lên GitHub đã với lấy CI mẫu "Python package" — tín hiệu rõ họ muốn một cổng kiểm tự động. Kit có validate deterministic (0 lỗi được PO khoe trong change-log) nhưng chưa bao giờ ship một workflow template chạy `--validate` cho repo người nhận; chân không đó được PO lấp bằng một workflow vừa sai mục tiêu vừa fail vĩnh viễn (mỗi push sau này sẽ đỏ — PO sẽ tưởng spec có vấn đề).
- Đề xuất: Ship kèm bundle một `spec-validate.yml` mẫu (chạy check_traceability/check_consistency/check_fence trên docs/product/, không phụ thuộc venv) + một dòng INSTALL.md; khuyên PO xoá python-package.yml.

### [CVR-F08] v1.1.0 ship 67 đường dẫn test/fixture vào repo PO — điều 2.1.0 phải sửa
- Mức độ: Medium
- Loại: CLEANUP
- Bằng chứng: `grep -c "scripts/tests" PO/MANIFEST.json` = 67; trên đĩa `ls PO/.claude/skills/product-spec/scripts/tests/` = 32 mục (test_*.py + fixtures/); `KIT/CHANGELOG.md:98` (2.1.0): "**Tests never ship.** `safety_catalog.ALWAYS_DROP_DIRS` now drops `__tests__/` and `tests/` from every bundle."
- Phân tích: Kit tự thừa nhận (bằng fix 2.1.0) rằng test không nên tới máy người nhận; PO giữ đúng bản còn rò. Rác này không vô hại: nó là mồi trực tiếp cho CVR-F07 (PO thấy repo "có Python + tests" → chọn CI Python) và phồng repo PO (fixtures broken-spec, golden specs…).
- Đề xuất: Tài liệu nâng cấp nên kèm bước dọn `**/scripts/tests/` cũ (installer semver-overwrite không xoá file thừa — xác nhận hành vi rồi mới khuyên).

### [CVR-F09] Frontmatter artifact PO mang field ngoài spec của chính kit — validator im lặng (cả 2 bản)
- Mức độ: Medium
- Loại: CONSISTENCY
- Bằng chứng:
  - Spec bản PO `PO/.claude/skills/product-spec/references/frontmatter-and-id-spec.md:40-42` — parent-link table CHỈ định nghĩa: story→`epic`, epic→`prd`, PRD→`brd_goals`; HEAD y hệt (`KIT/...frontmatter-and-id-spec.md:44`).
  - Artifact thật: `PO/docs/product/stories/PRD-SALES-E1-S1.md` frontmatter có thêm `prd: PRD-SALES` + `brd_goals: [BRD-G1]`; `PO/docs/product/epics/PRD-SALES-E1.md` có `brd_goals: [BRD-G1, BRD-G3]`.
  - `title`: mọi artifact PO có `title:` nhưng `grep '\`title\`'` cả 2 bản spec = **0 match**.
  - `version`: spec universal table (dòng 28 bản PO): "semver-lite … e.g. `0.1.0`, `1.0.0` … major.minor.patch" — artifact PO dùng 2-part: vision `version: "0.3"`, PRD-SALES `"1.0"`, story `"0.6"`; không script nào check format (`check_consistency.py:203` chỉ so child ≤ parent).
  - Change-log PO khoe "Validate **0 lỗi**" (`change-log.md:6-10`).
- Phân tích: Kit tuyên ngôn "Frontmatter is source-of-truth" + DRY "one home per fact" (KIT/CLAUDE.md) nhưng chính LLM flow sinh field trace trùng lặp (story.brd_goals lặp lại chuỗi dẫn xuất story→epic→prd→goal mà `spec_graph.py` đã chịu trách nhiệm) và spec doc không theo kịp hiện vật ở cả HEAD. Rủi ro cụ thể: PO đổi `brd_goals` của một PRD → bản copy ở 30 epic/102 story thành stale mà validate không bao giờ kêu.
- Đề xuất: Quyết một chiều — hoặc spec-hoá các field này (title, story.prd, story/epic.brd_goals, version 2-part) + thêm consistency check copy-vs-derived, hoặc tuyên bố chúng derived-only và để validate cảnh báo khi xuất hiện.

### [CVR-F10] change-log.md 89.4K/63 entries sau 8 ngày — không cap/rotate ở cả 2 bản, còn dangling reference
- Mức độ: Medium
- Loại: ARCHITECTURE
- Bằng chứng: `ls` → `change-log.md 89.4K`; `grep -c "^## "` = 63 (8 ngày 06-02→06-10); grep `rotate|archive|truncate|prune` trong scripts product-spec HEAD: không file nào liên quan change-log; HEAD `assemble_audit_trail.py:54-56` đọc **toàn bộ** file (`path.read_text`); bản PO không script nào đụng change-log ngoài `generate_templates.py:62`. Dangling: `change-log.md:646` ghi "Backup: `docs/product/stories.bak-*`" — `ls PO/docs/product/stories.bak*` → "no matches found".
- Phân tích: Nhịp ~8 entry/ngày → cỡ 1MB/3 tháng. Mọi flow đọc nguyên file (audit join ở HEAD, LLM mở file để prepend entry) trả chi phí tuyến tính tăng mãi; với PO non-technical không ai sẽ chủ động cắt file. Dangling backup reference cho thấy audit-trail prose đã bắt đầu trỏ vào hiện vật không tồn tại.
- Đề xuất: Cơ chế archive theo tháng (`change-log/2026-06.md`) hoặc cap+rollover script-side; thêm check nhẹ "đường dẫn nhắc trong change-log có tồn tại".

### [CVR-F11] Đường nâng cấp 1.1.0→2.3.0 không có migration cho rename — PO từng trả giá migration một lần rồi
- Mức độ: Medium
- Loại: ARCHITECTURE
- Bằng chứng: Renames: `KIT/CHANGELOG.md:111-118` (claude-pack→release, tag, artifact) + `:230-237` (skill spec-critique→product-spec-critique, 6 agents→actor-noun, hook rename). PO đang giữ tên cũ: `ls PO/.claude/agents/` = 7 file `spec-critique-*`/memory-harvester; `ls PO/.claude/skills/` = claude-pack/product-spec/spec-critique. HEAD agents = `product-critic.md`, `tech-critic.md`, `critique-consolidator.md`… Uninstall thủ công: `PO/INSTALL.md:76-81` ("rm -rf …"). PO spec-critique không có `metadata.version` (grep "version" SKILL.md chỉ ra `bundle_version` dòng 106) → gate A4 (CHANGELOG.md:151-154) không áp được lên nó. Tiền lệ chi phí: `change-log.md:711-733` — lần cài 06-04 đã tốn "67 error → 0", migrate 85 file, backup tay `docs/product.bak-20260604-055349/` (bak vision còn frontmatter v1: không có `type:`).
- Phân tích: Nếu PO chạy installer 2.3.0, semver-compare chỉ ADD/OVERWRITE theo slug — `spec-critique/` và `claude-pack/` cũ (versionless) sẽ nằm cạnh `product-spec-critique/`/`release/` mới, 7 agent cũ cạnh 6 agent mới, 2 hook cũ cạnh hook mới → hai bộ trigger chồng nhau cho cùng chức năng. Chính máy dev KIT còn leftover `spec-critique/` untracked — hiện tượng đã được chứng minh tại nguồn.
- Đề xuất: Viết `MIGRATION.md` 1.x→2.x (danh sách rm chính xác) hoặc installer biết bảng rename (old-slug → tombstone); bổ sung `metadata.version` về backfill khi upgrade.

### [CVR-F12] Bản phân phối PO không có LICENSE — điều khoản sử dụng không xác định
- Mức độ: Medium
- Loại: CORRECTNESS
- Bằng chứng: `ls PO/LICENSE* PO/CONTRIBUTING*` → "no matches found"; `KIT/LICENSE` (33.7K, AGPL-3.0) + `CONTRIBUTING.md` chỉ xuất hiện từ 2.2.1: `KIT/CHANGELOG.md:53-57` — "Both are added to the manifest `extra:` so every distributed bundle carries the license… (AGPL requires the license to accompany distributed copies)".
- Phân tích: Chính changelog 2.2.1 thừa nhận license phải đi kèm bản phân phối; bản 1.1.0 PO cầm không kèm gì → quyền của PO (dùng thương mại? chỉnh sửa?) không xác định, và chủ kit cũng không có cơ sở ràng buộc AGPL hồi tố lên bundle đã phát.
- Đề xuất: Gửi PO bản license rõ ràng áp cho 1.1.0 (hoặc kèm trong gói nâng cấp); ghi chú trong release notes về hiệu lực license với các bundle phát trước 2.2.1.

### [CVR-F13] Memory layer im lặng: hook opt-in không bật được xác minh, không một artifact behavioral memory sau 8 ngày
- Mức độ: Low
- Loại: UX-PO
- Bằng chứng: `ls PO/.claude/settings.json` → "No such file or directory"; `PO/.claude/hooks/memory_gap_hook.py:13-15`: "the installer registers it in the gitignored `.claude/settings.local.json` (**opt-in only, never auto**)"; `PO/INSTALL.md:45`: "Optional (opt-in, off by default)"; `ls PO/docs/product/.memory/` chỉ có `critique-lens-cache/`, `critique-findings-index.json`, `critique-state.json`, `last_critique.json` — không có behavioral/po-style artifact nào dù bundle ship `memory-harvester.md` agent + 3 script `behavioral_memory*.py`.
- Phân tích: Toàn bộ tầng memory (harvester + gap hook + behavioral_memory) ship đủ 347 file nhưng sau 8 ngày sử dụng thật không sinh nổi một hiện vật — mô hình opt-in-off-by-default với PO non-technical đồng nghĩa chết im. Kit đã tự rút bài học này cho telemetry (2.1.0 auto-register) nhưng memory hook đến HEAD vẫn opt-in.
- Đề xuất: Cân nhắc auto-register memory hook như đã làm với telemetry (kèm opt-out), hoặc ít nhất một nudge trong SKILL.md flow đầu tiên: "memory layer đang tắt".

### [CVR-F14] Spec vừa "đóng trọn bộ" — đúng thời điểm cần `--learn` (2.3.0) thì PO không có
- Mức độ: Low
- Loại: FEATURE-GAP
- Bằng chứng: `PO/docs/product/change-log.md:3-10` (entry 2026-06-10): "🎉 ĐÓNG TRỌN BỘ SPEC… TOÀN BỘ SPEC APPROVED… VISION + BRD + 10/10 PRD"; BRD goals đều có metric định lượng (`brd.md:14-24`: ≥50 hub/12 tháng, ≤30 phút/ngày, ≥60% quay lại); `ls KIT/.../assets/templates/` có `outcomes.md` — `ls PO/.../assets/templates/` không có; `KIT/CHANGELOG.md:21-23` (2.3.0 `--learn`, `OUT-<n>` register).
- Phân tích: Vòng đời PO vừa chạm đúng điểm mà 2.3.0 sinh ra để phục vụ: spec approved xong, bước kế là theo dõi target-vs-actual. Bản 1.1.0 dừng ở approve — không OUT register, không learning view → các metric ≥50/≤30ph/≥60% sẽ không bao giờ được kit đối chiếu thực tế.
- Đề xuất: Đưa `--learn` vào lý do nâng cấp số 1 khi chào PO bản 2.3.0 (đúng giai đoạn, giá trị thấy ngay).

## GIỚI HẠN & KHÔNG TÌM THẤY

- **Toàn vẹn cài đặt (mục 5): SẠCH** — sweep SHA256 cả 347 file trong MANIFEST.json: `TOTAL 347 MISSING 0 MISMATCH 0` → không có bằng chứng PO vá tay bất kỳ file kit nào (vượt yêu cầu "≥5 file").
- **Decision Register sạch**: DEC-1→DEC-44 liền mạch (`count: 44, missing: [], dup: []`), đúng grammar `## DEC-<n> — `.
- **ID grammar artifact đúng chuẩn** ở các mẫu đã soi (PRD-SALES, PRD-SALES-E1, PRD-SALES-E1-S1, PRD-CARE-E1-S1); status enum hợp lệ (`approved` + `approved`/`approved_by` ngày tháng đầy đủ — khớp approval-flow trong spec dòng ~171-182 bản PO).
- `--all` của claude-pack 1.1.0 có trong doc nhưng được ghi trung thực "Not implemented in v0.1 — errors (exit 1)" (`SKILL.md:35`) → không tính finding.
- **Không xác minh được**: PO có bật hook nào qua `~/.claude` hoặc `settings.local.json` trên máy họ không (gitignored, ngoài clone); GH Actions run thật (không truy cập GitHub) — kết luận pytest-fail dựa trên mô phỏng sandbox EXIT=5 cùng cấu trúc root; nguyên nhân gốc việc 12/15 critique run không được index (bước ghi do LLM flow, không log nào còn lại để truy).
- **Không soi**: nội dung business tài liệu PO (lens khác), `visuals/*.html` (chỉ xác nhận tồn tại), thân đầy đủ change-log.md/decisions.md/render_html.py (chỉ grep/sed trích đoạn theo luật file lớn).
- Số liệu thực đếm khác brief nhẹ: 30 epic (brief ~33), 102 story, 15 báo cáo critique (brief 16) — theo `ls | wc -l` trực tiếp.

Status: DONE
Summary: PO xác minh đứng tại claude-pack v1.1.0 (1c5113f, 347/347 file nguyên vẹn), sau HEAD 9 release; 14 findings — đắt nhất là installer vỡ trên macOS bash 3.2 (PO dính thật, HEAD chưa sửa), .session.md stale chứa answer superseded, và PO tự chế CI fail vĩnh viễn do kit không ship recipient CI.
Concerns: Kết luận GH Actions fail dựa trên mô phỏng sandbox (EXIT=5), chưa chạy trên GitHub thật; nguyên nhân index critique ghi thiếu 12/15 run chưa truy được root cause.