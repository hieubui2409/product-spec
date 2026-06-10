## PHÁN QUYẾT

### [CVR-F01] → ADJUSTED
- Kiểm chứng: `PO/docs/product/change-log.md:711-718` đúng nguyên văn ("Cài `.claude/skills` (thủ công vì installer gốc cần bash 4+; macOS có bash 3.2)"). `declare -A SKILL_VERDICT` có thật ở dòng 149 cả hai bản (PO template + `KIT/.claude/skills/release/assets/templates/install.sh.template:149` — y hệt). `grep -in bash KIT/.../release/CHANGELOG.md` → exit 1, 0 match. Template `set -euo pipefail` (dòng 19) + không có `BASH_VERSINFO` guard (grep 0 match) → bash 3.2 chết đúng chỗ đó. `INSTALL.md` hướng dẫn `bash install.sh` ✓. "multiplatform" trong `release/SKILL.md:18` ✓.
- Lý do: Sửa diễn giải, không sửa severity. Câu "e2e chạy trên CI Linux, chưa bao giờ chạm ca macOS" không chính xác: `KIT/.github/workflows/release-ci.yml:19` matrix CÓ `macos-latest` và `test_installer_e2e.py` chạy trong leg `-m 'not integration'`. Vấn đề thật tinh vi hơn: workflow chỉ trigger `pull_request` (path-filtered) mà repo KIT có **0 merge commit** (`git log --merges | wc -l` = 0) → không có bằng chứng leg macOS từng chạy; và bash version trên runner macOS không xác minh offline được. Kết luận lõi (template vỡ bash 3.2, PO dính thật, HEAD chưa sửa, không guard) đứng vững — Critical giữ nguyên.

### [CVR-F02] → CONFIRMED
- Kiểm chứng: chạy lại đủ: 15 tag ✓; `git log --oneline claude-pack-v1.1.0..product-spec-v2.3.0 | wc -l` = 50 ✓; diff stat = "485 files changed, 31431 insertions(+), 12618 deletions(-)" ✓ (khớp từng số). `MANIFEST.json` bundle_version 1.1.0, built 2026-06-03T05:39:31, source `1c5113f` = đúng commit tag claude-pack-v1.1.0 ✓. Sau v1.1.0 đúng 9 tag ✓. CHANGELOG: [1.2.0] và [1.3.0] đều đề ngày 2026-06-04 (dòng 221, 188) — "lỗi thời ngay ngày cài" ✓. Từng dòng cite (249-251, 193-200, 176-181, 82-95, 98, 51-57, 21-23) mở ra đều đúng nội dung được gán.

### [CVR-F03] → CONFIRMED
- Kiểm chứng: `.session.md` frontmatter `last_updated: 2026-06-02`, `phase: initial-spec-complete` ✓; dòng 30 "BRD-G1 metric: 30 hub (không phải 50)", dòng 33 "cả Sepay VÀ Casso từ MVP (song song)", dòng 51 "Tất cả artifacts hiện ở trạng thái `draft`" ✓. Đối chứng: `brd.md:16` "≤20 lên ≥50 … DEC-43, supersede mốc 30 trước" ✓; `decisions.md:43` "## DEC-4 — MVP chỉ tích hợp Sepay; Casso để next" ✓; `vision.md:6-7` `status: approved`, 2026-06-10 ✓. Đáng nói thêm: chính `PO/CLAUDE.md:75-80` (bản PO đang chạy) chứa GATE-NEVER-ASSUME cho phép assume từ `.session.md` — bẫy nằm ngay trong máy PO, không chỉ ở HEAD. High xứng đáng.

### [CVR-F04] → ADJUSTED
- Kiểm chứng: 15 report ✓ (TASK ×3, COMM ×4 đúng timestamp). Index: 20 entries, `report_ts` = {025434Z: 8, 084007Z: 8, 121803Z: 4} ✓ khớp từng con số; **0/20** có `finding_fingerprint` ✓ (entry keys: dec_worthy, evidence_id, fix, report_ts, scope, severity, why). `critique-state.json` đúng 3 key, TASK `last_ts` 2026-06-09T12:18:03 ✓. CHANGELOG 1.4.0 fingerprint ✓.
- Lý do: Sửa diễn giải nhẹ: câu "2 run all… đều không để lại dấu vết" bỏ sót `last_critique.json` — store thứ 4 CÓ ghi run cuối (`critiqued_at: 2026-06-09T23:37:02+00:00, scope: all`, kèm body_hash). Chính xác là: 12/15 run vắng mặt khỏi **index/state**, nhưng run all cuối để lại snapshot ở last_critique.json. Lõi finding (memory repeat-offense gần như không hoạt động, 0 fingerprint) và High giữ nguyên.

### [CVR-F05] → CONFIRMED
- Kiểm chứng: `grep -cE "apply-critique|--discover|--learn"` PO SKILL.md = **0**, KIT HEAD = **8** ✓. PO product-spec `SKILL.md:11` version "2.0.0" ✓; `--apply-critique` vào từ bundle 1.2.0 (CHANGELOG:221-228, 249-251) ✓. `grep -c critique change-log.md` = 58 ✓; dòng 284 đúng nguyên văn ✓.

### [CVR-F06] → CONFIRMED
- Kiểm chứng: `ls -d PO/.claude/telemetry` → "No such file or directory" ✓; `PO/.claude/` chỉ có agents/hooks/rules/skills (không settings.json) ✓; installer v1.1.0 của PO: `grep -c telemetry install.sh` = 0 ✓; CHANGELOG 2.1.0:88-91 "auto-registered by the installer" ✓; khối lượng (15 critique, 63 entry `grep -c "^## "`, 102 story `ls | wc -l`) ✓ cả ba.

### [CVR-F07] → CONFIRMED
- Kiểm chứng: `git -C PO log` đúng 2 commit, `9df10cf 2026-06-10 07:58:11` cách initial commit (07:36:45) ~22 phút ✓. `python-package.yml:38-40` step pytest trần ✓ (matrix py3.9-3.11). Tự chạy lại mô phỏng trong sandbox: `python3 -m pytest -q -p no:cacheprovider` → "Pytest: No tests collected", **PYTEST_EXIT=5** ✓ (pytest mặc định bỏ qua hidden dir `.claude` → repo toàn markdown không collect gì → exit 5 → step đỏ). Lens đã tự khai caveat mô phỏng trong GIỚI HẠN — trung thực. High hợp lý: mỗi push sau này đỏ, PO non-technical sẽ hiểu nhầm.

### [CVR-F08] → CONFIRMED
- Kiểm chứng: `grep -c "scripts/tests" PO/MANIFEST.json` = **67** ✓; trên đĩa `ls PO/.claude/skills/product-spec/scripts/tests/` = 32 mục (test_*.py + fixtures/ + conftest.py) ✓; `KIT/CHANGELOG.md:98` "**Tests never ship.** `safety_catalog.ALWAYS_DROP_DIRS`…" ✓ nguyên văn. Suy luận nối sang F07 ("repo có Python+tests → GitHub gợi ý CI Python") là inference hợp lý được dán nhãn đúng mức.

### [CVR-F09] → CONFIRMED
- Kiểm chứng: parent-link table bản PO (dòng 40-42) và HEAD y hệt: CHỈ story→`epic`, epic→`prd`, PRD→`brd_goals` ✓. Artifact thật: `PRD-SALES-E1-S1.md` có thêm `prd: PRD-SALES` + `brd_goals: [BRD-G1]`; `PRD-SALES-E1.md` có `brd_goals: [BRD-G1, BRD-G3]` ✓. `` grep '`title`' `` cả 2 spec = 0 ✓ (bonus củng cố: template chính thức `assets/templates/story.md`/`vision.md` bản PO cũng không có `title:` — field do LLM tự chế). Version 2-part: vision "0.3", PRD-SALES "1.0", story "0.6" ✓; `_SEMVER_RE = ^(\d+)\.(\d+)\.(\d+)$` (check_consistency.py:100) không match "0.3" → bị bỏ qua im lặng ✓; docstring còn nói "the dedicated parse check handles it" nhưng grep không tìm thấy check version-format chuyên trách nào → còn nặng hơn lens nêu. Đính chính số dòng nhỏ, không đổi nghĩa: version row ở spec dòng ~33 (không phải 28); chỗ so child≤parent là call-site dòng 206 / def `_version_inconsistency` dòng 217 (không phải 203).

### [CVR-F10] → ADJUSTED
- Kiểm chứng: `stat -c %s change-log.md` = 91531 bytes (=89.4K) ✓; 63 entry ✓; không cơ chế rotate/archive cho change-log trong scripts (các grep-hit prune/truncate đều thuộc ngữ cảnh khác: ingest_raw_inputs giới hạn input, render_explorer prune layer) ✓; `assemble_audit_trail.py` `path.read_text` đọc nguyên file ✓.
- Lý do: Bỏ sub-claim "dangling reference". `PO/.gitignore` có dòng **`docs/product/stories.bak-*/`** (mục "Bản nháp/sao lưu tạm") — thư mục backup bị cố ý gitignore, nên vắng mặt trong bản clone GitHub là HÀNH VI MONG ĐỢI, không suy ra được "hiện vật không tồn tại" trên máy PO. Lens không kiểm .gitignore trước khi kết luận. Phần size/không-cap/đọc-nguyên-file giữ nguyên, Medium giữ nguyên.

### [CVR-F11] → ADJUSTED
- Kiểm chứng: renames đúng cite (CHANGELOG ~110-118 claude-pack→release; 230-237 spec-critique→product-spec-critique + 6 agent + hook) ✓; PO giữ 7 agent `spec-critique-*`/memory-harvester + 3 skill slug cũ ✓; HEAD agents là product-critic/tech-critic/… ✓; `INSTALL.md:76-81` uninstall = rm -rf tay ✓; leftover untracked `KIT/.claude/skills/spec-critique/` có thật (`ls -d` thấy dir, `git ls-files` đếm 0) ✓; bak vision frontmatter v1 không `type:` ✓; chi phí migrate 06-04 (67→0, 85 file) ✓.
- Lý do: Một sub-claim SAI thực tế: "PO spec-critique không có `metadata.version`" — mở `PO/.claude/skills/spec-critique/SKILL.md:10-12` thấy rõ `metadata: author: cleanmatic / version: "1.0.0"`. Grep của lens chỉ bắt `bundle_version` dòng 106 mà bỏ sót frontmatter. Luận điểm "gate A4 không áp được lên nó" vì thế sụp (và A4 vốn là gate dev-side, không liên quan recipient). Lõi finding (không có migration path cho rename → nguy cơ hai bộ skill/agent/hook chồng nhau khi upgrade) vẫn đứng — Medium giữ.

### [CVR-F12] → CONFIRMED
- Kiểm chứng: `ls PO/LICENSE* PO/CONTRIBUTING*` → no matches ✓; `grep -ci license PO/README.md` = 0 (bản README ship kèm cũng không nhắc license) ✓; `KIT/LICENSE` = AGPL-3.0 ✓; CHANGELOG 2.2.1:53-57 đúng nguyên văn "(AGPL requires the license to accompany distributed copies)" ✓. Nhãn loại CORRECTNESS hơi gượng (bản chất là khoảng trống phân phối/pháp lý) nhưng không đáng hạ verdict.

### [CVR-F13] → CONFIRMED
- Kiểm chứng: `PO/.claude/settings.json` không tồn tại ✓; `memory_gap_hook.py:13` "(opt-in only, never auto)" ✓; `INSTALL.md:45` "Optional (opt-in, off by default)" ✓; `.memory/` chỉ có 4 hiện vật critique (lens-cache/, findings-index, state, last_critique) — zero behavioral/po-style artifact ✓; HEAD hook docstring vẫn "opt-in Tier-1 Stop hook" ✓. Caveat settings.local.json gitignored đã được lens tự khai. Low đúng mức.

### [CVR-F14] → CONFIRMED
- Kiểm chứng: `change-log.md:3-10` "🎉 ĐÓNG TRỌN BỘ SPEC… TOÀN BỘ SPEC APPROVED: VISION + BRD + 10/10 PRD" ✓; brd.md metrics định lượng (≥50 hub, ≤30 phút, ≥60%) ✓; `outcomes.md` có trong KIT templates, VẮNG trong PO templates ✓; CHANGELOG 2.3.0:21-23 `--learn`/OUT register ✓.

## BỎ SÓT (≤3, đủ bằng chứng, đúng format finding với prefix CVR-M<n>)

### [CVR-M1] README.md + CLAUDE.md của KIT chiếm danh tính repo người nhận — repo ERP của PO trên GitHub tự giới thiệu là "cleanmatic skills", kèm quy trình release dev-only trong context always-on
- Mức độ: High
- Loại: UX-PO
- Bằng chứng:
  - `PO/README.md:1`: "# cleanmatic skills" — trang nhất repo sản phẩm Cleanmatic-ERP là README của bộ kit (bảng 3 skill, không một dòng về ERP).
  - `PO/MANIFEST.json:1732,1737`: bundle ship `"CLAUDE.md"`, `"README.md"` top-level; `PO/INSTALL.md:30-32` tự khai "installs … PLUS any packed top-level files (e.g. `README.md`, `CLAUDE.md`)".
  - `PO/CLAUDE.md:143`: "Release process — TAG-TRIGGERED CI ONLY… Bump `version:` in `.claude/pack.manifest.yaml`… Push annotated tag `claude-pack-vX.Y.Z`. CI (`.github/workflows/claude-pack-release.yml`)…" — repo PO KHÔNG có pack.manifest.yaml, không có workflow đó (`.github/workflows/` chỉ có python-package.yml), không có branch master (chỉ `main`).
  - HEAD chưa đổi hành vi: `KIT/.claude/pack.manifest.yaml:47-49` `top_level: include_readme: true / include_claudemd: true`.
- Phân tích: Lens soi kỹ delta tính năng nhưng bỏ qua thứ đập vào mắt đầu tiên: bundle "cho recipient" lại ghi 2 file top-level viết cho DEV KIT vào root repo người nhận. Hệ quả kép: (1) danh tính GitHub của repo sản phẩm bị thay bằng danh tính bộ skill; (2) LLM của PO chạy với context always-on chứa quy trình release tag/CI trỏ vào file không tồn tại — nhiễu context và rủi ro LLM làm theo chỉ dẫn ma. Đây là commit-vs-reality thuần: cam kết "recipient installer", thực tế ship tài liệu dev.
- Đề xuất: Tạo biến thể README/CLAUDE.md dành cho recipient (hoặc default `include_readme/include_claudemd: false`), và ghi chú trong INSTALL.md cách bảo toàn README sản phẩm của người nhận.

### [CVR-M2] 8 ngày dựng spec nằm ngoài git history — kit giả định có git (`--reflect` quét git, `.session.md` "must be committed") nhưng không nudge VCS; PO bù bằng backup chép-thư-mục
- Mức độ: Medium
- Loại: ARCHITECTURE
- Bằng chứng:
  - `git -C PO log --pretty='%h %ad %s'` → đúng 2 commit, initial `2d0f44b 2026-06-10 07:36:45 "docs: initial commit…"` — trong khi change-log ghi công việc từ 2026-06-02 (63 entry) và lần cài skill 06-04 (`change-log.md:711`).
  - `PO/.claude/skills/product-spec/SKILL.md:61` (`--reflect`): "scan git + `.memory/` (git-degrade-safe)".
  - `check_consistency.py` `_session_md_gitignore` (KIT dòng 281-284, hàm cùng tên có trong bản PO): "`.session.md` must be committed for cross-machine resume".
  - Bù trừ thủ công: `docs/product.bak-20260604-055349/` (chép tay, được commit) + `.gitignore` dòng `docs/product/stories.bak-*/` (backup chép tay thứ hai, cố ý không commit).
- Phân tích: Toàn bộ cơ chế hậu kiểm/khôi phục của kit đứng trên giả định repo có lịch sử git, nhưng lịch sử công bố cho thấy 8 ngày làm việc dồn vào 1 commit — không diff/rollback/forensics được cho đúng giai đoạn rủi ro nhất (migrate 85 file, 44 DEC, toàn bộ approve). PO non-technical tự xoay sang backup chép-thư-mục — tín hiệu kit thiếu một nudge "init/commit sớm" trong flow. (Giới hạn: không loại trừ PO có repo local bị re-init trước khi push; bằng chứng chỉ nói về lịch sử công bố.)
- Đề xuất: `--status`/`--validate` thêm cảnh báo nhẹ khi `docs/product/` không nằm trong git hoặc có thay đổi chưa commit lớn; Closing-the-Loop gợi ý commit sau mỗi mốc approve.

### [CVR-M3] Viz chỉ được dùng đúng 1 tối (06-03, TRƯỚC migration) — 10 file ~6.7MB committed, toàn bộ stale 7 ngày so với spec đã đóng, 3 run trong 4 phút không bản nào được dọn
- Mức độ: Medium
- Loại: FEATURE-GAP
- Bằng chứng:
  - `ls PO/docs/product/visuals/` → 10 file, TẤT CẢ timestamp 20260603T2309–2313Z: board ×3 (275.9K/bản), explorer ×3 (290.7K), roadmap ×2 (2.5M/bản), dashboard ×1, sales-tree ×1; `du -sh` = 6.7M; `git -C PO ls-files docs/product/visuals/ | wc -l` = 10 (đều committed).
  - 3 run cách nhau ~2 phút (23:09:37 / 23:11:45 / 23:13:41Z) để lại 3 bộ board+explorer md5 khác nhau — không cơ chế overwrite/latest/prune nào can thiệp.
  - Spec sau đó thay đổi lớn: migrate 85 file 06-04 (`change-log.md:711-733`), "ĐÓNG TRỌN BỘ SPEC… TOÀN BỘ SPEC APPROVED" 06-10 (`change-log.md:3-10`) — không một visual nào được sinh lại sau 06-03.
- Phân tích: Visualization là giá trị quảng bá hàng đầu của kit cho PO, nhưng dấu vết sử dụng thật: một buổi tối ngày thứ 2 rồi ngưng hẳn. Hiện vật còn lại trong repo mô tả một spec lỗi thời 7 ngày (trước cả đợt đổi format), gây hiểu nhầm cho bất kỳ ai mở repo xem "trạng thái sản phẩm"; mỗi run đẻ thêm bộ file MB-scale (roadmap 2.5MB ×2) không ai dọn. Câu hỏi cam-kết-vs-thực-tế lens bỏ qua: vì sao PO bỏ viz ngay sau ngày đầu, và kit có biết hiện vật viz của mình đang nói dối về hiện tại không.
- Đề xuất: Ghi thêm bản `*-latest.html` ổn định + dọn/limit bản timestamp cũ; `--status` cảnh báo staleness khi visual mới nhất cũ hơn `updated` mới nhất của artifact; nudge regenerate sau approve/migrate lớn.

## TÓM TẮT CHẤT LƯỢNG LENS

Độ tin cậy tổng thể CAO: tái chạy độc lập khớp chính xác từng con số chủ chốt (347/347 SHA256, 50 commits/485 files/+31431−12618, 63 entry, 20 index entries/0 fingerprint, pytest EXIT=5, DEC 1→44 liền mạch), giới hạn được tự khai trung thực, không vi phạm scope, severity nhìn chung đúng mức. 10/14 CONFIRMED; 4 ADJUSTED vì lỗi diễn giải cục bộ: 1 sub-claim sai thực tế (F11 — spec-critique CÓ `metadata.version: "1.0.0"`), 1 kết luận mù .gitignore (F10 — stories.bak-* bị cố ý ignore, không phải dangling), 2 chỗ kể chuyện quá tay (F01 — CI matrix thật ra có macOS leg nhưng không bằng chứng từng chạy; F04 — run all cuối có để lại dấu ở last_critique.json). Thiên lệch nhận thấy: lens tập trung gần như tuyệt đối vào DELTA TÍNH NĂNG giữa hai phiên bản mà bỏ qua những gì bundle làm với chính repo người nhận — danh tính top-level bị chiếm (M1), giả định git không được kiểm (M2), hiện vật viz chết-mà-vẫn-nằm-đó (M3).
