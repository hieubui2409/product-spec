<<<REVIEW_MD_CYCLE>>>
## Cycle 3 — 2026-06-11 (field audit: Cleanmatic-ERP PO usage vs kit HEAD)

Nguồn: repo PO Cleanmatic/Cleanmatic-ERP chạy bundle claude-pack v1.1.0 (347/347 file nguyên vẹn) đối chiếu kit HEAD v2.3.0; 5 lens độc lập + 5 critic phản biện trong sandbox, tổng hợp 2026-06-11. Chưa fix gì — mọi row mở.

- [ ] PS-13 · CORRECTNESS · HIGH · `product-spec/scripts/check_consistency.py:196-203` — check `goal_without_metric` mới đỏ 3 error trên BRD approved viết bằng skill cũ (`metric:` số ít), `strict_gate` exit 2, `record_outcome` từ chối mọi goal; `migrate_multidim_fields.py` không migrate `metric→metrics`, message không nêu nguyên nhân → nhận diện key singular trong message + mở rộng migrate (confirm-flow vì artifact approved) + note nâng cấp
- [ ] PS-14 · CORRECTNESS · HIGH · `product-spec/scripts/spec_graph.py:124,466` — provenance hash chỉ phủ body, `CHANGED_FIELDS` không có `acceptance_criteria`, BRD không có node trong body_hash map → sửa AC-only/BRD: critique fast-path reuse kết quả cũ sai → đưa AC + node/hash BRD vào provenance + test "mọi artifact có mặt trong map"
- [ ] PS-15 · CORRECTNESS · HIGH · `product-spec/scripts/check_fence.py:36` + `status.py:194` — fence_breach không cap/exclude: cây sau-cài/chưa-commit → 2.258 cảnh báo / 1,09MB JSON (đếm cả `.claude/` kit tự cài), trái docstring "never an over-report" → exclude `.claude/` + aggregate theo thư mục + cap top-N kèm tổng đếm
- [ ] PS-16 · CORRECTNESS · MED · `check_consistency.py:177` + `spec_graph.py:597-602` — sentinel `<missing-id>` lộ vào finding PO-facing và `target_ids`/`source_files` của bundle critique; type product/vision thiếu `id:` không bị flag riêng → finding `missing_id` nêu tên file + formatter thay sentinel + lọc sentinel khỏi bundle + template `id: PRODUCT`
- [ ] PS-17 · CORRECTNESS · MED · `check_consistency.py:141-143` + `spec_graph.py:170-182` — goal thiếu `status` (spec ghi required) không check nào bắt; `moscow` trên goal bị drop im lặng khỏi graph → thêm `goal_without_status` (warn trước, error sau migrate) + lint key lạ trong goal entry
- [ ] PS-18 · CONSISTENCY · MED · `references/frontmatter-and-id-spec.md:40-44` — artifact LLM sinh mang field ngoài spec (`title`, story.`prd`/`brd_goals`, `version` 2-part) — validator im lặng, semver-lite không được check format → spec-hoá hoặc warn derived-field + check version format
- [ ] PS-19 · CONSISTENCY · MED · `product-spec/CHANGELOG.md:18` + root `CHANGELOG.md:30` — claim "SKILL.md 6090→5371 (−11.8%)" không tái lập từ lịch sử git (thực 5758→5371 = −6.7%; 6090 chưa từng tồn tại ở commit nào) → sửa số so-với-release + quy ước số changelog phải tái lập từ 2 tag
- [ ] PS-20 · CONSISTENCY · MED · `product-spec/GUIDE-EN.md`/`GUIDE-VI.md` — thiếu hẳn `--voice` (+5 flag con) và `--compact-mode` so với SKILL.md; GUIDE critique thiếu alias `--gentle`/`--savage` → bổ sung mục + test flag-inventory SKILL↔GUIDE
- [ ] PS-21 · CONSISTENCY · MED · `product-spec/SKILL.md` — `migrate_multidim_fields.py` mồ côi khỏi mọi routing (0 match SKILL.md/references) → spec v1 sau upgrade ăn warn-noise không ai chỉ đường → thêm route "spec cũ → đề nghị migrate (dry-run, hỏi PO)"
- [ ] PS-22 · CLEANUP · MED · `docs/product/.session.md` + `.memory/*` + `visuals/.snapshots/*` (tracked, commit 58e2d05) — state/cache per-run của dogfood bị commit → diff vô nghĩa mỗi lần dogfood lại → untrack + gitignore, giữ artifact prose
- [ ] PS-23 · CORRECTNESS · LOW · `check_consistency.py:380` — BrokenPipeError traceback khi consumer đóng pipe sớm (`| head` trên output ~301KB), vi phạm contract ":12 Always exits 0" → try/except BrokenPipeError hoặc SIGPIPE default cho mọi script in JSON lớn
- [ ] PS-24 · CONSISTENCY · LOW · `assemble_audit_trail.py` (ascii) — bảng `--viz audit` dòng dài nhất 368 ký tự trên data PO, vô dụng ở terminal 80-120 cột dù cam kết "ascii downgraded, never removed" → truncate cell theo budget cột ~120, giữ full text cho `--format md`
- [ ] PS-25 · CLEANUP · LOW · `render_html.py` — 805 exec-LOC (~4× guideline 200 từng viện dẫn ở PS-2) → tách template tĩnh ra module/asset hoặc ghi ngoại lệ có lý do
- [ ] PSC-2 · CORRECTNESS · HIGH · `product-spec-critique/scripts/critique_signals.py:28` + `critique_bundle.py:117` — `source_files` nhét toàn bộ corpus bất kể scope (PRD đơn: 148 key/700KB, 123 key off-target; all: 1,24MB × 4 lens song song) → lọc theo `target_ids ∪ ancestry ∪ digest`, descendants dùng `verbosity: struct`
- [ ] PSC-3 · CORRECTNESS · HIGH · `references/workflow-critique.md` + `parse_critique_report.py` — ghi lens-cache/`lens_findings_hash`/index/state là bước LLM-flow không cưỡng chế → trên data PO 12/15 report parse ra `findings: 0`, state kẹt pass-1, fingerprint 0/20 entry → script-enforce ghi cache sau mỗi report + fallback bóc heading prose + `--doctor` đối chiếu state↔thư mục critique
- [ ] PACK-3 · CORRECTNESS · HIGH · `release/assets/templates/install.sh.template:149` — `declare -A` chết trên macOS bash 3.2 (PO dính thật, phải cài tay — change-log PO :711-718; không `BASH_VERSINFO` guard; 6 release sau vẫn nguyên) → cấu trúc bash-3-compatible hoặc fail sớm có thông báo rõ + leg e2e macOS/bash3
- [ ] PACK-4 · CORRECTNESS · HIGH · `install.sh.template:2,31,348` (+`install.ps1.template:1,34,319`, `INSTALL.md.template:72`) — installer ship vẫn brand "claude-pack", hint `/cleanmatic:claude-pack` (skill không tồn tại), trỏ troubleshooting path chết; token `{{BUNDLE_NAME}}` có sẵn không dùng → thay token + sửa path + test "không còn literal claude-pack"
- [ ] PACK-5 · CONSISTENCY · HIGH · `pack.manifest.yaml:30-35,47-49` — bundle ship README/CLAUDE.md viết cho dev-kit (repo PO trên GitHub tự xưng "cleanmatic skills", quy trình release trỏ file ma trong context always-on) + 5 rules tham chiếu skill ck không ship (`cook`/`/ck:preview`/`/ck:team`; 101 match `/ck:` trong rules PO) → biến thể recipient cho top-level docs + rules trung tính hoặc bỏ khỏi manifest
- [ ] PACK-6 · ENV · MED · `install.sh.template` (không có bước gitignore) — sau cài/upgrade, telemetry JSONL + `settings.json` registrar tạo nằm trong working tree PO → bị commit lên GitHub (PO .gitignore không có telemetry) → installer append-nếu-thiếu `.claude/telemetry/` vào .gitignore recipient + ghi vào INSTALL.md
- [ ] LIB-3 · CORRECTNESS · HIGH · `hooks/register_telemetry_hooks.py:113-116` — registrar wire enforcement hook vô điều kiện theo basename; upgrade default (install.sh.template:285 SKIP-existing) giữ `memory_gap_hook.py` đời 1.1.0 không config-gate → blocking hook (exit 2) bật ngầm cho PO chưa từng opt-in → version-guard trước khi wire (kiểm marker config-gate trong file đích) + coi hooks là code kit (overwrite-with-backup)
- [ ] LIB-4 · CORRECTNESS · HIGH · `hooks/emit_session_summary.py:60-68,115` — `first_timestamp()` chỉ đọc dòng đầu transcript (record đầu không có ts) → 43/43 session `duration_s:0`; 46/46 subagent `outcome:unknown`; 41/43 `skills:[]` → sửa parse start-ts (scan tới record có ts) + classify outcome từ tail protocol + e2e fixture từng sink
- [ ] LIB-5 · CORRECTNESS · HIGH · `telemetry/scripts/lens_workflow_chains.py:23-25` — hardcode 2 routing doc đã bị xoá ở e52e077 → test tracked FAIL ngay HEAD (1 failed/108), `declared_chains` thành dead code (workflow lens vĩnh viễn 0 chuỗi) → trỏ nguồn routing còn sống hoặc gỡ feature + test
- [ ] LIB-6 · CONSISTENCY · HIGH · `.github/workflows/` (6 workflow) — 26 file test tracked (telemetry 18, hooks 4, _shared 4) không CI nào chạy; path filter thiếu `_shared/**`; CONTRIBUTING.md:75 "all tests must pass" không được enforce → thêm workflow chạy đúng lệnh CONTRIBUTING.md:69 + vá path filter
- [ ] LIB-7 · CORRECTNESS · MED · `hooks/hook_runtime.py:41` + `track_script_execution.py:57-59` — SCRIPT_RE substring-match: grep/ls/glob nhắc tới script cũng thành "script run" (10 record glob literal), validate-proxy đếm grep `check_*` như validate PASS → siết matcher về dạng thực-thi (đầu lệnh/sau interpreter) + fixture từ record thật
- [ ] LIB-8 · CONSISTENCY · MED · `hooks/track_script_execution.py:61-68` — biến `session` đã tính nhưng record không ghi (414/414 record thiếu key, 3 sink kia đều có) → hook-telemetry không join được phiên↔script → thêm `"session"` vào record + cập nhật tests
- [ ] LIB-9 · CORRECTNESS · MED · `hooks/register_telemetry_hooks.py:107-108` — kênh UserPromptExpansion 0 record sau nhiều ngày (7/7 invocation đều PreToolUse:Skill) — kênh slash-command chính của PO có thể mù → e2e 1 phiên thật assert record; nếu event chết → capture qua transcript + xoá registration
- [ ] LIB-10 · CONSISTENCY · MED · `CLAUDE.md:4,8-13` — routing always-on tự nhận "three PO-facing skills", bảng 3 hàng — telemetry (PO-facing, bundle ship 4 skill) vô hình; bản trước-slim có nhắc → thêm hàng telemetry + sửa "three"→"four" + nudge nhẹ trong `--status`
- [ ] LIB-11 · CLEANUP · MED · `.claude/agents/` (13 file ck, commit a967688) + 2 `.env.example` + `schemas/ck-config.schema.json` (0 tham chiếu) — rác ck-local đã commit vào repo nguồn ship → untrack hoặc ghi DEC "tracked có chủ đích, không ship"
- [ ] LIB-12 · CONSISTENCY · LOW · `telemetry/scripts/lens_validate_proxy.py:82` + `telemetry_render.py:182` — reason tiếng Anh hardcode chen giữa output VI (bản dịch `val_na` có sẵn không dùng) → lens trả `reason_code`, render map label localize
- [ ] LIB-13 · CONSISTENCY · LOW · `docs/audit-trail/telemetry-readback.md` — thiếu sink `.logs/hook-crashes.log` + config gate `product-spec-hooks.json` (đồ mới 2.3.0); README.md:26 gán memory-gap hook nhầm vào critique → thêm hàng sink + sửa attribution
- [ ] LIB-14 · CLEANUP · LOW · `hooks/__tests__/test_telemetry_hooks.py:133,194` + `telemetry/.../test_telemetry_paths.py:56,62` — fixture còn dùng id "claude-pack" → đổi sang id trung tính

- Field-observations (không lên row): PO đứng sau HEAD 9 release (lỗi thời ngay ngày cài); tự chế GH Actions fail vĩnh viễn vì thèm validate-on-push; `.session.md` đóng băng 06-02 chứa 4 fact bị supersede — đúng nguồn GATE-NEVER-ASSUME cho phép assume; visuals đóng băng 06-03 (56/102 story) + 88 file backup tracked; critique marathon 13 report/ngày trên bản không fingerprint.
- Khoảng trống kiến trúc không-phải-defect: upgrade-path 1.x→2.x (cài đặt Frankenstein), version-beacon, artifact-events, self-learning/feedback-loop về dev, memory-lens hợp nhất, rotation change-log, snapshot/restore — 15 đề xuất xếp hạng trong report.
- Phản biện: 0/58 finding lens bị REFUTED toàn phần; 13 ADJUSTED (2 đổi severity: ARC-F02 Critical→High, POX-F07 Medium→High); 13 finding do critic bổ sung được nhận vào.
- Chi tiết: plans/reports/
<<<END_REVIEW>>>
<<<FULL_REPORT>>>
# Field audit: Cleanmatic-ERP (PO, claude-pack v1.1.0) đối chiếu kit product-spec HEAD (v2.3.0) — 2026-06-11

Phương pháp: 5 lens độc lập (CVR cam-kết-vs-thực-tế · BUG thực nghiệm · DRY tĩnh · POX trải nghiệm PO · ARC kiến trúc đích) → 5 critic phản biện tái-chạy từng bằng chứng → tổng hợp này.
Evidence-only (path:line / lệnh+output); thao tác phá chỉ trong sandbox; KIT và PO-repo không bị ghi.

## 1. Executive summary

1. PO Cleanmatic là power-user thành công: 8 ngày dựng 147 node (10 PRD/30 epic/102 story), 44 DEC liền mạch, vòng critique→DEC→re-approve hội tụ thật (blocker 3-4 → 0, COMM pass-4 `converged`). Bundle 1.1.0 nguyên vẹn 347/347 SHA256 — PO không vá tay gì. Vấn đề nằm ở kit, không nằm ở PO.
2. **Upgrade hiện là bãi mìn** — nhóm phát hiện đắt nhất: installer chết trên macOS bash 3.2 (PACK-3, PO dính thật, HEAD chưa sửa); upgrade default tạo cài đặt Frankenstein (2 skill critique, agent đôi, CLAUDE.md cũ — ARC-F02/DRY-F02); registrar wire ngầm blocking hook đời cũ không config-gate (LIB-3, Critical); check mới `goal_without_metric` đỏ 3 error trên BRD approved mà không có migration (PS-13).
3. **Telemetry "có ống chưa có nước"**: 3 trường chủ lực chết trên data thật (duration 43/43 = 0, outcome 46/46 unknown, skills 41/43 rỗng — LIB-4), data còn lại bẩn (grep bị đếm như script-run — LIB-7), test tracked FAIL ngay tại HEAD vì lens trỏ doc đã xoá (LIB-5), và 26 file test không nằm trong CI nào (LIB-6).
4. **Critique provenance mù đúng chỗ quan trọng nhất**: hash chỉ phủ body trong khi kit dời AC vào frontmatter; BRD không có node → sửa AC/BRD có thể bị fast-path reuse kết quả cũ sai (PS-14, critic nâng Medium→High); bundle nhét toàn bộ corpus bất kể scope (PSC-2); memory critique ghi bằng LLM-flow không cưỡng chế → 12/15 report PO mất đường parse (PSC-3).
5. Pain thật của PO chỉ ra khoảng trống sản phẩm: tự chế GitHub Actions fail vĩnh viễn (muốn validate-on-push), `.session.md` ôi thiu chứa 4 fact bị supersede ngay trong nguồn GATE cho phép assume, visuals đóng băng từ ngày 2, không có cách biết bản mới tồn tại.
6. Kết quả phản biện: 45/58 CONFIRMED, 13 ADJUSTED, **0 REFUTED toàn phần**; 13 finding bổ sung từ critic. Ledger nhận 31 defect kit (12 HIGH · 13 MED · 6 LOW); 24 quan sát hiện trường/khoảng trống (sau gộp) đi vào report + 15 đề xuất xếp hạng ở mục 4.

## 2. PO đang đứng ở đâu (drift v1.1.0 → v2.3.0)

Trạng thái (lens CVR, critic xác nhận từng số): PO cài claude-pack **v1.1.0** (built 2026-06-03T05:39:31Z, source `1c5113f` = đúng tag), cài tay 06-04 vì installer vỡ bash 3.2; toàn vẹn 347/347 file khớp SHA256. HEAD = product-spec **v2.3.0** (`cc4cf2b`): cách nhau **9 release / 50 commits / 485 files / +31431 −12618 dòng**. Trớ trêu: 1.2.0 và 1.3.0 phát hành đúng ngày PO cài (06-04) — lỗi thời ngay từ ngày đầu. [CVR-F02 · CONFIRMED]

| Nhóm năng lực (release) | PO không có | Hệ quả quan sát được trong PO-repo |
|---|---|---|
| `--apply-critique`/`--discover`/`--summary --audience`/`--viz audit` (1.2.0) | đường chính thống áp critique vào spec | 15 báo cáo critique áp tay qua change-log/DEC; 58 lần nhắc "critique" trong change-log [CVR-F05] |
| Engagement knobs + Closing-the-Loop end-of-session (1.3.0) | forcing-function giữ `.session.md` tươi | `.session.md` đóng băng 06-02, chứa 4 fact bị supersede [CVR-F03/POX-F03] |
| Finding-fingerprint (1.4.0) | dedup repeat-finding | index 0/20 entry có fingerprint; TASK ×3, COMM ×4 re-run full [CVR-F04] |
| Telemetry 5 sink + skill telemetry (2.0.0/2.1.0) | mọi số liệu usage/health | `PO/.claude/telemetry` không tồn tại; 8 ngày không số liệu [CVR-F06] |
| "Tests never ship" (2.1.0) | — (PO nhận NGƯỢC) | 67 đường dẫn `scripts/tests` trong MANIFEST; 32 mục test trên đĩa [CVR-F08] |
| AGPL LICENSE + CONTRIBUTING vào manifest (2.2.1) | điều khoản sử dụng | `ls PO/LICENSE*` → không có [CVR-F12] |
| `--learn`/OUT register + hook hardening (2.3.0) | vòng đo outcome hậu-approve | spec "ĐÓNG TRỌN BỘ" 06-10 — đúng lúc cần `--learn` thì không có [CVR-F14] |

Mọi cải tiến trúng nhất vào pain của chính PO này (fingerprint, apply-critique, telemetry, learn) đều nằm sau 1.1.0 — nhưng chưa có đường nâng cấp an toàn (xem nhóm E + đề xuất #1).

## 3. Findings xác nhận

Ghi chú: severity là bản cuối sau critic; ID ledger trong ngoặc = defect kit đã lên row Cycle 3 (mục REVIEW.md). Mức map ledger: Critical/High→HIGH, Medium→MED, Low→LOW.

### Nhóm A — CORRECTNESS / BUG (defect kit, chạy được bằng chứng)

**[BUG-F01] (+PS-13) · High · CORRECTNESS — check `goal_without_metric` mới phá BRD đã approve, không đường migrate**
- Bằng chứng: PO `brd.md:16` `metric:` (số ít, prose) vs spec cả 2 bản đòi `metrics:` (`frontmatter-and-id-spec.md:89`); `strict_gate.py --root .` → exit 2 "BLOCKED on errors: goal_without_metric · BRD-G1/G2/G3"; `migrate_multidim_fields.py` 0 match "metric"; `record_outcome --append-alloc` → `"metric ... is not in BRD-G1's metrics []"`, written:false.
- Phân tích: upgrade biến validate xanh thành đỏ trên artifact approved, CI gate chặn, vòng `--learn` tê liệt; message "has no success metric" đánh lạc hướng (PO nhìn thấy metric trong file); sửa phải đụng approved → vướng GATE-NO-SILENT-REVERSAL mà không có flow dẫn.
- Đề xuất: message nhận diện key `metric:` singular; mở rộng migrate (giữ giá trị, confirm-flow); note nâng cấp trong CHANGELOG/INSTALL.
- Critic: CONFIRMED — tái chạy khớp tuyệt đối, kể cả "skill cũ viết sai schema của chính nó".

**[ARC-F01] (+LIB-3) · Critical · CORRECTNESS — upgrade đè 1.1.0 kích hoạt ngầm blocking hook cũ không config-gate**
- Bằng chứng: `install.sh.template:285` SKIP file tồn tại (giữ `memory_gap_hook.py` cũ); `:328` auto-chạy registrar; `register_telemetry_hooks.py:113` "(wired-always; config default-false makes them no-op)" + `:116` wire Stop; hook cũ của PO grep `config|hooks.json` → 0 match, có đường `"block"`/exit 2; PO không có settings.json.
- Phân tích: "default-false = no-op" chỉ đúng với file hook MỚI; đường upgrade default wire file CŨ → PO bị chặn cuối phiên, không biết tắt — trái thiết kế gốc "opt-in only, never auto".
- Đề xuất: registrar version-guard (kiểm marker config-gate trong file đích trước khi wire) + installer coi hooks là code kit (overwrite-with-backup).
- Critic: CONFIRMED — còn xác minh thêm chuỗi import (venv PO tồn tại → kịch bản block thực tế).

**[CVR-F01] (+PACK-3) · Critical · CORRECTNESS — installer chết trên macOS bash 3.2; PO dính thật, HEAD chưa sửa**
- Bằng chứng: PO change-log.md:711-718 "Cài thủ công vì installer gốc cần bash 4+; macOS có bash 3.2"; `install.sh.template:149` `declare -A SKILL_VERDICT` y nguyên ở cả bản PO lẫn HEAD; release CHANGELOG 0 match "bash"; không `BASH_VERSINFO` guard.
- Phân tích: kit quảng bá "multiplatform recipient installer" nhưng mọi PO macOS sẽ dính lại; feedback lỗi chưa từng quay về kit qua 6 release.
- Đề xuất: bỏ `declare -A` hoặc fail sớm có thông báo; leg e2e macOS/bash3; ghi CHANGELOG.
- Critic: ADJUSTED (giữ Critical) — sửa diễn giải: CI matrix CÓ macos-latest nhưng repo 0 merge-commit → không bằng chứng leg từng chạy.

**[POX-F07 (+POX-M3)] (+PS-14) · High (critic nâng từ Medium) · CORRECTNESS — provenance hash mù AC/frontmatter; BRD không có node**
- Bằng chứng: báo cáo critique PO tự thú "Build `--fresh` vì sửa nằm ở AC/frontmatter mà `body_hash` không bắt"; HEAD: `spec_graph.py:124` hash CHỈ body; `:466` `CHANGED_FIELDS` không có `acceptance_criteria`; `critique_provenance.py:141-164` fast-path reuse; body_hash map 144 key — "has BRD: False", BRD node ABSENT (critic POX-M3).
- Phân tích: kit dời AC vào frontmatter rồi hash phần thân — hai quyết định tự đá nhau; sửa AC-only hoặc sửa BRD (đúng loại thay đổi đáng re-critique nhất, vd DEC-43 ngày 06-10) → "spec unchanged" → reuse kết quả cũ SAI. PO 1.1.0 trả giá bằng marathon `--fresh` 21 giờ.
- Đề xuất: hash phủ `acceptance_criteria` (+ thêm node/hash BRD); test "mọi file artifact có mặt trong body_hash map".
- Critic: ADJUSTED — nâng Medium→High sau khi tự xác minh HEAD CHƯA vá; POX-M3 là nhánh độc lập do critic bổ sung, gộp cùng root cause coverage.

**[BUG-F02] (+PS-15) · High · CORRECTNESS — `--status`/memory_gap phun 1,09MB JSON với 2.258 `fence_breach`**
- Bằng chứng: `status.py --root .` exit 0, stdout 1.086.985 bytes; Counter fence_breach=2258 (1.913 thuộc `.claude/`); `check_fence.py:36` `FENCE_PREFIX="docs/product/"` không cap; `status.py:194` nhúng nguyên mảng; docstring tự hứa "never an over-report".
- Phân tích: trạng thái sau-cài/trước-commit (chính lúc PO hỏi "spec tôi ổn không?") → LLM nuốt 2.258 cảnh báo trùng dạng — tràn context, nudge vô dụng; kit tự báo động giả trên file kit tự cài.
- Đề xuất: exclude mặc định `.claude/`; aggregate theo thư mục + cap top-N; giữ tổng trong count.
- Critic: CONFIRMED — số khớp tuyệt đối; ghi chú PO-repo thật hiện sạch → flood nổ ở trạng thái install/cây bẩn (đúng kịch bản lens khoanh).

**[BUG-F03] (+PSC-2) · High · CORRECTNESS — bundle critique nhét toàn bộ corpus bất kể scope**
- Bằng chứng: `critique_scan --scope PRD-SALES` → 699.415 bytes, `source_files` 148 key/422.111 chars, 123 key off-target; scope=all → 1.236.477 bytes; `critique_signals.py:28` loop mọi node không lọc; hai bundle có `source_files` y hệt nhau.
- Phân tích: 4 lens agent song song × ~700KB-1,24MB; 60%+ payload chết — điểm gãy đầu tiên khi spec lớn thêm.
- Đề xuất: lọc theo `target_ids ∪ ancestry ∪ digest`; `verbosity: struct` cho descendants ở scope=all.
- Critic: CONFIRMED — mọi số khớp tuyệt đối.

**[BUG-F04 (+DRY-M1)] (+LIB-5) · High · CORRECTNESS — test tracked FAIL tại HEAD: lens telemetry trỏ 2 routing doc đã xoá**
- Bằng chứng: pytest telemetry → `FAILED test_declared_chains_parsed_from_routing_docs`, 1 failed/108 passed; `lens_workflow_chains.py:23-25` hardcode 2 path bị xoá tại e52e077 (release 2.3.0); chạy runtime → `declared: []` vĩnh viễn.
- Phân tích: HEAD đã-release mang test đỏ; tính năng declared-vs-actual (SKILL.md quảng cáo) thành dead code; lớp bug "xoá file, quên consumer" lọt vì CI không chạy suite telemetry (LIB-6).
- Đề xuất: trỏ nguồn routing còn sống hoặc gỡ feature + test; nối suite vào CI.
- Critic: CONFIRMED (BUG) — DRY-M1 của critic DRY là cùng fail này chạy bằng đúng lệnh CONTRIBUTING.md:69 (1 failed/193) → gộp.

**[ARC-F04] (+LIB-4) · High · CORRECTNESS — 3 trường telemetry chủ lực chết trên data thật**
- Bằng chứng (data dev, critic đếm lại trên file sống): 43/43 session `duration_s:0`; 46/46 subagent `outcome:"unknown"`; 41/43 `skills:[]`; invocations 7 record, 0 thuộc 4 skill bundle. Root cause critic xác minh: transcript mở đầu bằng record không timestamp, `first_timestamp()` chỉ đọc dòng đầu (`emit_session_summary.py:60-68`) → start=last → delta 0.
- Phân tích: trả lời thẳng tiêu chí "telemetry đầy đủ": sink chạy, fail-open chuẩn, nhưng không trả lời nổi "PO dùng gì, kẹt đâu, subagent có ổn không" — mọi lens phía sau vô nghĩa nếu không sửa.
- Đề xuất: sửa parse start-ts; classify outcome từ tail theo protocol Status DONE/BLOCKED; e2e fixture từng sink trên transcript thật.
- Critic: CONFIRMED — còn tìm ra root cause cấu trúc (mạnh hơn lens nêu).

**[BUG-F05 (+POX-M1)] (+PS-16) · Medium · CORRECTNESS — sentinel `<missing-id>` lộ ra finding PO-facing; PRODUCT.md thiếu id không bị báo**
- Bằng chứng: PO `PRODUCT.md` không `id:` (template cả 2 bản có `id: PRODUCT`); finding thật `"<missing-id> declares 7 personas..."`; `spec_graph.py:571-576` tự cam kết "the PO never sees an internal sentinel"; `ID_PATTERN_BY_TYPE` (597-602) không phủ product/vision; bundle all có `target_ids[0]='<missing-id>'`.
- Phân tích: PO đọc không thể biết file nào lỗi gì; nguyên nhân gốc (skill cũ sinh PRODUCT.md thiếu id) không được flag; sentinel rò cả vào provenance/citation của critique; cross-reference-by-ID bất khả thi với chính tài liệu nền.
- Đề xuất: finding `missing_id` nêu tên file; formatter thay sentinel; lọc sentinel khỏi bundle; template/migration bù `id: PRODUCT`.
- Critic: CONFIRMED cả hai (BUG-F05 + POX-M1 critic bổ sung) — gộp cùng root cause.

**[BUG-M1] (+PS-17) · Medium · CORRECTNESS — goal thiếu `status` (spec ghi required) không bị bắt; `moscow` trên goal bị drop im lặng** *(nguồn: critic BUG bổ sung)*
- Bằng chứng: spec `:90` `status: draft # required` mỗi goal; data PO goals chỉ có id/title/metric/moscow; chạy thật 12 findings — 0 về status; `check_consistency.py:141-143` skip field vắng mặt; `spec_graph.py:170-182` không copy moscow → biến mất khỏi mọi view.
- Phân tích: đúng vết xe PS-13 — spec tuyên required nhưng validator chỉ enforce metrics; nếu mai thêm check status, BRD approved của PO lại đỏ tiếp mà vẫn không có migrate; lệch schema 2 chiều bị nuốt im.
- Đề xuất: `goal_without_status` (warn→error sau chu kỳ migrate); lint key lạ trong goal entry (bắt generic cả lớp `metric:`-vs-`metrics:`).

**[BUG-F06 (+CVR-F04, POX-F08)] (+PSC-3) · High · CORRECTNESS — memory critique ghi bằng LLM-flow không cưỡng chế → mất đường deterministic trên 12/15 report**
- Bằng chứng: `parse_critique_report` trên report all → `findings: 0`, "lens-cache absent — fall back to a manual prose walk"; critic parse cả 15 report: chỉ 3 parse được; `.memory/critique-lens-cache/` chỉ 3 hash; index 20 entry/0 fingerprint, state kẹt pass-1 TASK, COMM/PAYMENT/REPORT/all vắng (POX-F08).
- Phân tích: trạng thái mặc định của 80% corpus critique PO, không phải ngoại lệ; report chốt 2 blocker là thứ cần walk nhất; mọi tính năng dựa trên state (fast-path, drift, resume, dedup) hỏng im lặng — và không script nào cưỡng chế bước ghi (điểm yếu thiết kế còn nguyên ở HEAD).
- Đề xuất: consolidator LUÔN ghi cache + `lens_findings_hash` qua script; fallback bóc heading `[severity][lens]` từ prose; `--doctor` đối chiếu state↔thư mục.
- Critic: BUG-F06 ADJUSTED (mở rộng 12/15); CVR-F04 ADJUSTED (last_critique.json CÓ ghi run cuối — đã phản ánh); POX-F08 CONFIRMED. Gộp 3 ID cùng root cause.

**[ARC-M2] (+LIB-7) · Medium · CORRECTNESS — hook-telemetry false-positive: grep/ls cũng thành "script run", làm bẩn validate-proxy** *(nguồn: critic ARC bổ sung)*
- Bằng chứng: `hook_runtime.py:41` SCRIPT_RE substring-search; docstring hứa "Filters to commands that run…"; data thật 10 record glob literal `product-spec/scripts/*.py`; `lens_validate_proxy.py:9-10` đếm exit-0 của `check_*` như validate PASS.
- Phân tích: script-health và validate-proxy lệch về hướng lạc quan theo mọi thao tác đọc file của LLM; sau upgrade chạy thẳng trên repo PO.
- Đề xuất: matcher đòi path đứng đầu lệnh hoặc sau interpreter; bỏ glob; fixture từ record thật.

**[ARC-F08] (+LIB-9) · Medium · CORRECTNESS — kênh UserPromptExpansion 0 record, chưa được chứng minh hoạt động**
- Bằng chứng: registrar đăng ký 2 đường (`:107-108`); data thật 7/7 via `PreToolUse:Skill`, 0 UserPromptExpansion; dedup không thể là nguyên nhân che.
- Phân tích: PO chủ yếu gõ slash-command — nếu event không fire, usage lens mù đúng kênh chính của PO (khớp `skills:[]` ở LIB-4). Chưa đủ bằng chứng kết luận event chết → cần kiểm, không cần tin.
- Đề xuất: e2e 1 phiên thật assert record; nếu chết → capture qua transcript + xoá registration.
- Critic: CONFIRMED (khen tự giới hạn đúng mực).

**[BUG-F08] (+PS-23) · Low · CORRECTNESS — BrokenPipeError traceback khi consumer đóng pipe sớm**
- Bằng chứng: pipe `check_consistency.py` (output thật 301.486 bytes) vào consumer đóng sớm → traceback nguyên văn dòng 380, exit 1.
- Phân tích: `| head` là thao tác chuẩn của LLM trên JSON ~300KB; vi phạm contract `check_consistency.py:12` "Always exits 0".
- Đề xuất: try/except BrokenPipeError hoặc SIGPIPE default trong helper chung cho mọi script in JSON lớn.
- Critic: ADJUSTED — bug thật, sửa nguồn trích (câu "never a bare traceback" thuộc file khác; contract thật là "Always exits 0").

### Nhóm B — DRY / CONSISTENCY / CLEANUP

**[DRY-F01 (+ARC-F12)] (+PACK-4) · High · CORRECTNESS — installer templates ship còn brand "claude-pack" + link chết + hint skill không tồn tại**
- Bằng chứng: `install.sh.template:2,31,348` ("[claude-pack]", hint `/cleanmatic:claude-pack`); `.ps1:1,34,319` y hệt; `INSTALL.md.template:72` trỏ troubleshooting path chết; template chỉ có `{{VERSION}}` dù `{{BUNDLE_NAME}}` được pipeline cấp sẵn.
- Phân tích: mặt tiền đầu tiên PO non-technical nhìn sau khi cài: tên 3 version trước, lệnh gõ vào skill không tồn tại, đường dẫn 404.
- Đề xuất: dùng token + sửa path + test "không còn literal claude-pack ngoài back-compat chủ đích".
- Critic: CONFIRMED cả hai (ARC-F12 gộp — cùng dòng 348).

**[CVR-M1 (+DRY-M2, ARC-F10)] (+PACK-5) · High · CONSISTENCY — bundle ship danh tính + ngữ cảnh dev vào repo người nhận** *(nguồn: critic CVR/DRY bổ sung + lens ARC)*
- Bằng chứng: PO `README.md:1` "# cleanmatic skills" (trang nhất repo ERP); PO `CLAUDE.md:143` quy trình release tag/CI trỏ file không tồn tại trên máy PO; manifest `top_level: include_readme/claudemd: true` (:47-49); 5 rules ship (:30-35) tham chiếu `cook`/`/ck:preview`/`/ck:team` không ship — 101 match `/ck:` trong rules PO thật.
- Phân tích: danh tính GitHub repo sản phẩm bị thay bằng danh tính bộ skill; LLM của PO chạy với context always-on chứa chỉ dẫn ma + vocabulary dev — ngược tiêu chí "speak product language".
- Đề xuất: biến thể README/CLAUDE.md recipient (hoặc default include=false); rules trung tính hoặc bỏ khỏi manifest; release quét "path skill nhắc trong rules ship phải nằm trong bundle".
- Critic: cả 3 mục được critic xác nhận đầy đủ bằng chứng — gộp cùng root cause "manifest ship nội dung dev cho recipient".

**[DRY-F03] (+LIB-6) · High · CONSISTENCY — 26 file test tracked không CI nào chạy; path filter hổng**
- Bằng chứng: grep `telemetry`/`hooks/` trên 6 workflow → 0 match; telemetry 18 + hooks 4 + _shared 4; `pyproject.toml` testpaths chỉ `scripts/tests`; product-spec-ci không trigger khi `_shared/**` đổi; CONTRIBUTING.md:69/75 bắt buộc nhưng không enforce.
- Phân tích: lớp test mới nhất (chỗ vừa đổi nhiều nhất) không có lưới — LIB-5 là exhibit A sống.
- Đề xuất: workflow mới chạy đúng lệnh CONTRIBUTING.md:69; vá path filter `_shared/**`.
- Critic: ADJUSTED — sửa số 28→26 (telemetry 18, không 20); bản chất và High giữ nguyên.

**[DRY-F04] (+PS-19) · Medium · CONSISTENCY — claim "−11.8%" trong 2 CHANGELOG không tái lập được**
- Bằng chứng: claim "6090 → 5371 (−11.8%)"; đo bằng chính `context_footprint.py`: 2.2.2 = 5758 → HEAD 5371 = **−6.7%**; quét toàn rev-list: max 5758 ⇒ 6090 chưa từng tồn tại ở commit nào; đối chứng số của critique (−3.7%) khớp chính xác.
- Phân tích: tài liệu release công khai mang số chỉ đúng với working-state không bao giờ commit → xói mòn niềm tin vào các con số còn lại.
- Đề xuất: sửa thành số so-với-release; quy ước số changelog phải tái lập từ 2 tag.
- Critic: CONFIRMED (quét rev-list mạnh hơn lập luận gốc).

**[DRY-F05] (+LIB-11) · Medium · CLEANUP — rác ck-local đã commit: 13 agents ngoài bundle, 2 env.example, schema 0-ref**
- Bằng chứng: 20 agents tracked vs manifest ship 7; 13 file thêm bởi `a967688`; `ck-config.schema.json` 0 tham chiếu; env.example chứa hướng dẫn API key hệ skill khác.
- Đề xuất: untrack hoặc ghi DEC "tracked có chủ đích, không ship". Critic: CONFIRMED.

**[DRY-F06] (+PS-22) · Medium · CLEANUP — dogfood commit cả state phiên + cache dễ vỡ**
- Bằng chứng: tracked `.session.md`, 6 file `.memory/*`, `visuals/.snapshots/*` (commit 58e2d05).
- Phân tích: sản phẩm phụ mỗi lần chạy → dogfood lại là sinh diff vô nghĩa trong PR.
- Critic: ADJUSTED — bỏ vế "mâu thuẫn README:282" (dòng đó nói về telemetry sinks); vế diff-noise tự đứng, giữ Medium.

**[DRY-F07] (+PS-20) · Medium · CONSISTENCY — GUIDE-EN/VI thiếu hẳn `--voice` và `--compact-mode`**
- Bằng chứng: diff flag SKILL↔GUIDE → thiếu 8 mục ở CẢ hai GUIDE; critique GUIDE thiếu alias `--gentle`/`--savage`.
- Phân tích: tính năng PO-facing nguyên khối PO không bao giờ biết tồn tại; drift sẽ rộng dần nếu không có guard.
- Đề xuất: bổ sung + test flag-inventory. Critic: CONFIRMED.

**[CVR-F09] (+PS-18) · Medium · CONSISTENCY — frontmatter artifact mang field ngoài spec của chính kit, validator im lặng (cả 2 bản)**
- Bằng chứng: parent-link table chỉ định nghĩa story→epic, epic→prd, PRD→brd_goals; artifact thật thêm `prd:`/`brd_goals:` ở story, `title:` mọi nơi (0 match trong spec lẫn template); `version` 2-part ("0.3") vs spec semver-lite — `_SEMVER_RE` không match → bỏ qua im, không có check format chuyên trách dù docstring nhắc.
- Phân tích: vi phạm chính "DRY one home per fact": brd_goals copy ở 30 epic/102 story có thể stale mà validate không bao giờ kêu; "Validate 0 lỗi" của PO là thật nhưng rỗng nghĩa ở các field này.
- Đề xuất: quyết một chiều — spec-hoá (kèm check copy-vs-derived) hoặc tuyên derived-only + warn.
- Critic: CONFIRMED (còn phát hiện docstring trỏ check không tồn tại — nặng hơn lens nêu).

**[ARC-F09] (+PS-21) · Medium · CONSISTENCY — `migrate_multidim_fields.py` mồ côi khỏi mọi workflow**
- Bằng chứng: 0 match trong SKILL.md/references; PO spec v1-era (`risks:` 0/10 PRD) → lần validate đầu sau upgrade xổ warn-noise hàng loạt mà không ai chỉ đường.
- Đề xuất: 1 dòng route trong SKILL.md (dry-run trước, hỏi PO). Critic: CONFIRMED.

**[ARC-F07 (+DRY-M3)] (+LIB-10) · Medium · CONSISTENCY — telemetry vô hình: CLAUDE.md tự nhận "three PO-facing skills", bảng routing 3 hàng**
- Bằng chứng: `CLAUDE.md:4` "three"; bảng :8-13 không có telemetry; bản trước-slim CÓ nhắc (git show e52e077^); GUIDE-VI product-spec 0 match; không nudge/SessionStart nào trỏ tới.
- Phân tích: usage-insight tốt nhưng pull-based thuần — PO không biết tồn tại thì không bao giờ gõ.
- Đề xuất: thêm hàng routing + sửa "three"→"four" + 1 dòng gợi ý trong `--status`. Critic: CONFIRMED cả hai — gộp.

**[ARC-M3] (+LIB-8) · Medium · CONSISTENCY — record script-run không mang `session` dù biến đã tính** *(nguồn: critic ARC bổ sung)*
- Bằng chứng: `track_script_execution.py:61` tính session nhưng record :62-68 chỉ {ts, source, script, exit(,ms)}; 414/414 record thiếu key; 3 sink kia đều có; lens workflow join theo `session`.
- Đề xuất: thêm `"session"` vào record + tests (sửa 1 dòng, không thêm rủi ro privacy).

**[ARC-M1] (+PACK-6) · Medium · ENV — telemetry JSONL + settings.json không được gitignore phía recipient → commit lên GitHub** *(nguồn: critic ARC bổ sung)*
- Bằng chứng: `.gitignore:170` chỉ chắn repo dev; manifest extra chỉ LICENSE/CONTRIBUTING; installer/INSTALL 0 match "gitignore"; PO .gitignore 0 match telemetry; registrar tạo settings.json mới (`:121-124`).
- Phân tích: sau upgrade, mỗi phiên đẻ JSONL (session UUID, path, tool counts) vào working tree PO; hooks bị áp lên mọi người clone.
- Đề xuất: installer append-nếu-thiếu vào .gitignore recipient + ghi INSTALL.md.

**[BUG-F09] (+LIB-12) · Low · CONSISTENCY — câu tiếng Anh hardcode giữa output telemetry tiếng Việt** — `lens_validate_proxy.py:82` reason EN; `telemetry_render.py:173` có sẵn bản dịch `val_na` không dùng. Đề xuất: `reason_code` + map localize. Critic: CONFIRMED.

**[DRY-F09] (+LIB-13) · Low · CONSISTENCY — telemetry-readback.md thiếu sink crash-audit + config gate (đồ mới 2.3.0); README.md:26 gán memory-gap hook nhầm skill** — `hook_runtime.py:18,45`. Critic: CONFIRMED.

**[DRY-F10] (+LIB-14) · Low · CLEANUP — fixture test còn dùng id "claude-pack"** — 2 file test; đổi sang id trung tính. Critic: CONFIRMED.

**[DRY-F08] (+PS-25) · Low · CLEANUP — `render_html.py` 805 exec-LOC ≈ 4× chuẩn 200-LOC kit tự áp qua PS-2** — cùng thước đo PS-2; tách template hoặc ghi ngoại lệ có lý do. Critic: CONFIRMED.

**[BUG-F10] (+PS-24) · Low · CONSISTENCY — bảng `--viz audit` ASCII 368 ký tự/dòng trên data PO** — 111 dòng, không truncate; "ascii downgraded never removed" thành vô dụng đúng lúc cần. Critic: CONFIRMED.

**[BUG-F07] · Medium · CLEANUP — tích tụ output: roadmap 2,5MB/lần render; export trùng content-hash vẫn ghi file mới** — KHÔNG lên ledger: critic xác nhận docstring `render_export.py:12-16` ghi nhận tích tụ là hành vi CÓ CHỦ ĐÍCH → design-gap, xử lý qua đề xuất #6 (retention/latest/reuse-hash). Critic: CONFIRMED (kèm caveat by-design).

### Nhóm C — COMMIT-VS-REALITY (quan sát hiện trường, không lên ledger)

- **[CVR-F05] · Medium · FEATURE-GAP** — Không có `--apply-critique` (vào kit 1 ngày sau khi PO build bundle): 15 báo cáo áp tay qua change-log/DEC (58 lần nhắc "critique"). Giải bằng upgrade. Critic: CONFIRMED.
- **[CVR-F06] · Medium · FEATURE-GAP** — Zero telemetry: 8 ngày vận hành thật không một dòng số liệu; lỗi installer chỉ tình cờ lộ qua prose change-log của PO. Critic: CONFIRMED.
- **[CVR-F08] · Medium · CLEANUP** — v1.1.0 ship 67 đường dẫn test/fixture vào repo PO (điều 2.1.0 đã sửa phía dev); là mồi trực tiếp cho vụ CI Python (nhóm D). Tài liệu upgrade cần bước dọn `**/scripts/tests/` cũ. Critic: CONFIRMED.
- **[CVR-F12] · Medium · CORRECTNESS(phân phối)** — Bản 1.1.0 không kèm LICENSE; chính changelog 2.2.1 thừa nhận AGPL phải đi kèm bản phân phối → quyền của PO không xác định (xem Q7). Critic: CONFIRMED (nhãn loại "hơi gượng" — bản chất pháp lý/phân phối).
- **[CVR-F13] · Low · UX-PO** — Memory layer chết im: hook opt-in-off-by-default, 0 artifact behavioral/po-style sau 8 ngày; kit đã tự rút bài học auto-register cho telemetry nhưng chưa cho memory. Critic: CONFIRMED.
- **[CVR-F14] · Low · FEATURE-GAP** — Spec vừa "ĐÓNG TRỌN BỘ" 06-10 — đúng điểm `--learn` (2.3.0) sinh ra để phục vụ thì PO không có; các metric ≥50/≤30ph/≥60% sẽ không bao giờ được đối chiếu. Critic: CONFIRMED.
- **[CVR-M2] · Medium · ARCHITECTURE** *(critic bổ sung)* — 8 ngày dựng spec dồn vào 1 commit (initial 06-10); kit giả định có git (`--reflect` quét git; `.session.md` "must be committed") nhưng không nudge VCS; PO bù bằng backup chép-thư-mục.

### Nhóm D — PO-EXPERIENCE (quan sát hiện trường + khoảng trống)

- **[CVR-F07 + POX-F01] · High · UX-PO/FEATURE-GAP — PO tự chế GitHub Actions CI fail vĩnh viễn; kit không ship recipient CI.** Bằng chứng: `python-package.yml` (stock template, commit 22 phút sau initial, committer GitHub web-flow = bấm nút suggested-workflow); repo toàn markdown + 125 file .py của kit trong `.claude/` → pytest exit 5 (mô phỏng sandbox) → mỗi push đỏ, PO sẽ tưởng spec có vấn đề. Tín hiệu nhu cầu validate-on-push rõ rệt → đề xuất #2. Critic CVR: CONFIRMED; POX: ADJUSTED (chi tiết "tài khoản thứ hai" sai — cùng account; cách đọc chính được củng cố).
- **[CVR-F03 + POX-F03] · High · UX-PO/CORRECTNESS-nguy-cơ — `.session.md` đóng băng 06-02 chứa 4 fact bị supersede, đúng nguồn GATE-NEVER-ASSUME cho phép assume.** Metric 30-vs-50 (ngược DEC-43), "Sepay VÀ Casso MVP" (ngược DEC-4), "toàn draft" (thực tế 134 approved/10 draft), đếm artifact cũ. HEAD không có staleness check (`check_consistency.py:282-311` chỉ check gitignore); bẫy nằm cả trong máy PO lẫn HEAD → một phiên mới có thể silent-reversal đúng nghĩa. → đề xuất #4. Critic: CONFIRMED cả hai (critic còn tìm thêm fact thứ tư).
- **[POX-F02] · High · CORRECTNESS-dữ-liệu-PO — PRODUCT.md bản đồ phân hệ lệch horizon với 2 PRD approved (PAYMENT/REPORT ghi next/later vs frontmatter `horizon: now`), validate vẫn "0 lỗi"** — không script nào (cả HEAD) check bảng phân hệ ↔ frontmatter. → đề xuất #9. Critic: CONFIRMED (thực tế cả 10 PRD đều `now`).
- **[POX-F04 + CVR-M3] · High · UX-PO — visuals chết sau ngày 2:** 10 file đều 06-03 (board chứa 56/102 story), 3 lần render trong 4 phút không bản nào được dọn, không `latest` alias (HEAD 0 match), story approved vẫn trỏ PO "xem AC bằng Explorer view" — con trỏ vào view đông cứng ở 55% spec; 10 file ~6,7MB committed lên GitHub cho cả đội xem bản sai. → đề xuất #6. Critic: CONFIRMED cả hai.
- **[POX-F05] · Medium · UX-PO — AC canonical nằm trong YAML frontmatter, 102/102 story ghi chú "đã gỡ bản sao ở thân"** → trên GitHub web AC gần như không đọc nổi với non-technical. Critic: ADJUSTED — làm mạnh thêm: `workflow-export.md` + `render_export.py` CÓ SẴN trong bundle 1.1.0 của PO — 8 ngày không hề dùng → vấn đề là discoverability thuần (đề xuất #12).
- **[POX-F06] · Medium · CONSISTENCY-dữ-liệu-PO — DEC-13 áp dụng nửa vời:** persona CSKH có trong frontmatter VISION nhưng không có chân dung trong body; VISION vẫn approve 06-10. Mẫu lỗi "DEC áp dụng một phần" không checklist hậu-DEC nào bắt. → đề xuất #9. Critic: CONFIRMED.
- **[POX-M2] · Medium · FEATURE-GAP** *(critic bổ sung)* — 3 câu hỏi kinh doanh "Vẫn còn mở" từ 06-02 (ngưỡng điểm/quy đổi/ưu đãi hạng) không có nhà: story `must` mang đúng tham số treo đã approve với ghi chú "cần PO xác định trước khi viết code"; 0/44 DEC đụng tới; không workflow nào theo dõi open questions. → đề xuất #4.
- **[POX-F10] · Low · CLEANUP — backup toàn-thư-mục là cp tay ngoài kit; không snapshot/restore chính thức.** Critic bổ sung: `.gitignore` PO không khớp `docs/product.bak-*/` → 88 file backup đang bị track và đã phát tán lên GitHub. → đề xuất #14. Critic: CONFIRMED.
- **[POX-F11] · Low · UX-PO — 44 DEC trong file 32K pseudo-frontmatter, không tra được "DEC nào chi phối PRD-X";** dashboard 0 match DEC. Critic: CONFIRMED (lưu ý: `decision_register.py` data-layer có từ đời 1.1.0 — thiếu là tầng trình bày). → đề xuất #13.

### Nhóm E — ARCHITECTURE-GAP (không lên ledger; ăn vào mục 4)

- **[DRY-F02 + ARC-F02 + CVR-F11 + POX-F09] · High (ARC-F02 critic hạ Critical→High) — không có upgrade/migration path từ claude-pack 1.x.** Installer chỉ ADD/OVERWRITE (mặc định còn KHÔNG nâng skill cũ — `[STALE] … FORCE_OVERWRITE=1`); skill + agent + hook đã rename → upgrade tạo 2 skill critique, 2 packer, agent đôi, CLAUDE.md cũ vẫn route skill cũ; troubleshooting 0 dòng về upgrade; chính máy dev còn leftover `spec-critique/` untracked làm bằng chứng sống. (Mảnh thật sự Critical — hook chặn bật ngầm — đã tách lên ledger LIB-3.) → đề xuất #1. Verdict: DRY CONFIRMED, ARC ADJUSTED (severity), CVR ADJUSTED (1 sub-claim sai — xem mục 5), POX CONFIRMED.
- **[ARC-F03] · High · FEATURE-GAP — không tồn tại kênh version-check/notify;** PO không có cách biết bản mới (INSTALL.md 0 dòng về update). → đề xuất #7 (age-beacon offline). Critic: CONFIRMED.
- **[ARC-F05] · High · FEATURE-GAP — thiếu hẳn lớp event sản phẩm:** không sink nào ghi artifact bị sửa / flag được dùng / câu hỏi interview bị bỏ qua → kể cả data sạch cũng không bao giờ trả lời "PRD-CARE bị sửa 7 lần", "PO toàn bỏ qua câu hỏi competitor". → đề xuất #8. Critic: CONFIRMED.
- **[ARC-F06] · High · FEATURE-GAP — self-learning kit-level chưa tồn tại + vòng phản hồi về dev đứt hẳn:** `--learn` chỉ outcome sản phẩm; behavioral chỉ per-product; A9 deferred chính thức; telemetry local-only, không lệnh export → kit chỉ tiến hoá bằng dogfood của dev (đúng như field audit này phải làm tay). → đề xuất #11. Critic: CONFIRMED.
- **[ARC-F11] · Medium · ARCHITECTURE — hai hệ memory rời nhau:** lens memory audit memory dir của assistant; không lens nào đánh giá SỨC KHỎE memory sản phẩm (`docs/product/.memory`: store rỗng/thiếu, tuổi last_validated, po-style). → đề xuất #10. Critic: ADJUSTED — thu hẹp claim (lens_validate_proxy CÓ đọc 1 marker ở đó).
- **[CVR-F10] · Medium · ARCHITECTURE — change-log.md 89,4K/63 entry sau 8 ngày, không cap/rotate ở cả 2 bản;** HEAD `assemble_audit_trail` đọc nguyên file → chi phí tuyến tính tăng mãi (~1MB/3 tháng). → đề xuất #15. Critic: ADJUSTED — bỏ sub-claim "dangling backup" (bị .gitignore cố ý).
- **[ARC-F13] · Low · YAGNI — skill `release` (dev-facing, code/CLI vocabulary) ship trong bundle cho PO non-technical;** có thể chủ đích cho re-share nhưng không văn bản nào nói vậy → Q3. Critic: CONFIRMED.

## 4. Đề xuất kiến trúc & tính năng

Tiêu chí chủ kit: PO-first · đầu-ra-sản-phẩm · telemetry đầy đủ · memory + usage insight + product insight · self-learning. Tiền đề số 0 — **chỉ-cần-PO-upgrade, không build gì**: lên 2.3.0 là PO có ngay `--apply-critique` (CVR-F05), fingerprint+inherit (CVR-F04), telemetry sinks (CVR-F06), `--learn` (CVR-F14), LICENSE (CVR-F12), tests-never-ship (CVR-F08). Nhưng upgrade hiện không an toàn → #1 đứng đầu bảng.

| # | Tên | Lấp khoảng trống (finding) | Cơ chế phác thảo | Cỡ | Rủi ro | Loại |
|---|---|---|---|---|---|---|
| 1 | Upgrade-một-lệnh + legacy-sweep | DRY-F02, ARC-F02, CVR-F11, POX-F09 (+LIB-3, PACK-3 là tiền đề fix) | `upgrade.sh`/mode: FORCE-đè-có-backup + bảng rename old→new (spec-critique/, claude-pack/, 6 agent, hook cũ) hỏi-rồi-xoá + thay CLAUDE.md + chạy migrate + mục "Nâng cấp" song ngữ trong INSTALL | M | xoá nhầm file user-sửa → danh sách legacy tường minh + backup | build-mới |
| 2 | GH Action `spec-validate.yml` cho recipient | CVR-F07, POX-F01 | template chạy check_traceability/consistency/fence trên `docs/product/`, summary tiếng Việt vào job summary; installer hỏi PO có bật không; khuyên xoá python-package.yml | S | cần PyYAML trên runner → pip install 1 dòng trong workflow | build-mới |
| 3 | Telemetry data-quality pack | LIB-4, LIB-7, LIB-8, LIB-9 | sửa first_timestamp + classify outcome theo Status-protocol + siết SCRIPT_RE + thêm session key + e2e UserPromptExpansion | S-M | thấp | fix-defect (đã lên ledger) |
| 4 | Session-staleness guard + supersede sweep + open-questions first-class | CVR-F03, POX-F03, POX-M2 | validate warn khi `.session.md.last_updated` < max(`updated`); DEC supersede quét session/PRODUCT.md tìm fact bị thay; sổ open-questions trong `--status`; `--approve` cảnh báo marker "cần PO xác định" | S-M | false-positive warn nhẹ | build-mới |
| 5 | Critique provenance + memory enforcement | PS-14 (POX-F07/M3), PSC-3 (BUG-F06/CVR-F04/POX-F08) | hash phủ AC + node BRD; consolidator script-enforce ghi cache/index/state; prose-fallback parser; `--doctor` | M | đổi hash → invalidate cache cũ một lần | fix-defect (đã lên ledger) |
| 6 | Visuals latest + staleness + retention | POX-F04, CVR-M3, BUG-F07 | `*-latest.html` ổn định + banner "render lúc X, spec lệch N node" + `--viz --clean` + reuse khi content-hash trùng + nudge re-render hậu approve | S-M | thấp | build-mới |
| 7 | Version age-beacon trong `--status` | ARC-F03,
| 7 | Version age-beacon trong `--status` | ARC-F03, CVR-F02 | `status.py` đọc MANIFEST.json (`built_at`/`bundle_version` có sẵn) → 1 dòng VI "bản 1.1.0, cài N ngày — hỏi người phát hành bản mới"; không network | S | nag nhẹ | build-mới |
| 8 | Artifact-events sink + lens "artifact heat" | ARC-F05 | tái dùng matcher PostToolUse `Edit\|Write\|MultiEdit` đã đăng ký → ghi `{ts, artifact_path, op, session}` (path-only, local); invocations ghi tóm tắt flag; lens kể VI "PRD nào bị sửa nhiều" | M | privacy thấp (không nội dung) | build-mới |
| 9 | Validation coverage pack | POX-F02, POX-F06, PS-16 (BUG-F05/POX-M1) | rule PRODUCT.md bảng phân hệ ↔ `horizon` PRD (parse theo ID); warn persona frontmatter↔body heading; template `id: PRODUCT` + migration bù id | S-M | parse bảng md dễ vỡ → bám ID, không bám heading | build-mới (một phần fix PS-16) |
| 10 | Memory-lens hợp nhất + memory hook auto-register opt-out | ARC-F11, CVR-F13 | lens đọc `docs/product/.memory` (tuổi last_validated, store rỗng/thiếu, cache size) narrate VI; cân nhắc auto-register memory hook như telemetry 2.1.0 (kèm opt-out + config-gate) | S | nudge/nag → advisory-only | build-mới |
| 11 | Usage-summary export + self-learning slice (report-only) | ARC-F06 | `telemetry --export-summary` markdown aggregate PO duyệt rồi tự gửi dev; harvester read-only đọc self-corrections + repeat-findings → report "đề nghị chỉnh interview/template", không tự sửa (giữ boundary A9) | M | privacy → PO duyệt tay, opt-in từng lần | build-mới |
| 12 | AC-readable surface (discoverability export) | POX-F05 | công cụ ĐÃ CÓ từ 1.1.0 (`workflow-export.md` + `render_export.py`) — chỉ thêm nudge sau approve + 1 dòng GUIDE; hoặc khối AC render-only "generated — đừng sửa tay" | S | đồng bộ 2 nơi nếu chọn render-only | PO-có-sẵn + nudge mới |
| 13 | Decision index view | POX-F11 | dashboard/`--decision --list PRD-X` từ data `decision_register.py` (đã có từ 1.1.0): lọc theo `affects`/date/status, vẽ chain supersede | S | thấp | build-mới (tầng trình bày) |
| 14 | Snapshot/restore chính thức + VCS nudge | POX-F10, CVR-M2 | `--snapshot`/`--restore <ts>` tự tạo trước migration/update lớn + README trong thư mục snapshot; `--status`/validate warn khi docs/product ngoài git hoặc diff lớn chưa commit; Closing-the-Loop gợi ý commit sau mốc approve | S-M | thấp | build-mới |
| 15 | change-log rotation + path-exists check | CVR-F10 | archive theo tháng (`change-log/2026-06.md`) hoặc cap+rollover script-side; check nhẹ "đường dẫn nhắc trong change-log có tồn tại" | S | đổi contract đọc của audit-join → vá assemble_audit_trail cùng lúc | build-mới |

Thứ tự khuyến nghị thực thi: fix ledger HIGH trước (PACK-3/4, LIB-3/4/5, PS-13/14/15, PSC-2/3 — chính là #3/#5) → #1 upgrade path → mời PO lên 2.3.0 (mở khoá toàn bộ "số 0") → #2/#4/#6/#7 (PO-facing, cỡ S) → #8-#15 theo nhịp.

## 5. Findings bị bác

Không có finding nào bị REFUTED toàn phần (0/58 qua 5 critic). Các sub-claim/diễn giải bị bác hoặc chỉnh bên trong 13 finding ADJUSTED:

- CVR-F01: vế "e2e chưa bao giờ chạm macOS" sai — `release-ci.yml:19` matrix CÓ `macos-latest`; nhưng repo 0 merge-commit nên không có bằng chứng leg từng chạy (kết luận lõi giữ nguyên).
- CVR-F04: vế "2 run all không để lại dấu vết" thiếu — `last_critique.json` CÓ ghi run cuối 23:37 (chính xác: vắng mặt khỏi index/state).
- CVR-F10: sub-claim "dangling reference `stories.bak-*`" bác — PO `.gitignore` cố ý ignore thư mục đó; vắng mặt trong clone là hành vi mong đợi.
- CVR-F11: sub-claim "spec-critique không có `metadata.version`" sai — `SKILL.md:10-12` có `version: "1.0.0"`; luận điểm "gate A4 không áp được" sụp theo (lõi migration-gap giữ nguyên).
- BUG-F06: nói NHẸ hơn thực tế — không riêng report all mà 12/15 report mất đường parse (critic mở rộng phạm vi).
- BUG-F08: trích nhầm nguồn cam kết "never a bare traceback" (thuộc file khác); contract thật bị vi phạm là `check_consistency.py:12` "Always exits 0".
- DRY-F03: đếm sai 28 → đúng **26** file test ngoài CI (telemetry 18, không 20).
- DRY-F06: vế "mâu thuẫn README.md:282" bác — dòng đó nói về telemetry sinks (gitignored thật), không nói về `.session.md`/`.memory`.
- POX-F01 + POX-F05: chi tiết "2 người/tài khoản thứ hai commit" sai — cả 2 commit cùng account hunghenei (web-flow vs local); cách đọc chính (PO bấm suggested-workflow trên github.com) lại được củng cố.
- POX-F07: severity bị đánh NON — critic nâng Medium→High sau khi xác minh HEAD chưa vá (hash vẫn body-only).
- ARC-F02: hạ Critical→High — đường upgrade default giữ hệ cũ tự nhất quán, tác hại là confusion/nâng-cấp-không-xảy-ra chứ không chặn workflow (mảnh Critical thật đã tách sang ARC-F01/LIB-3).
- ARC-F11: claim tuyệt đối "không lens nào đọc docs/product/.memory" sai — `lens_validate_proxy.py:6` đọc 1 marker; gap thật là không lens nào đánh giá SỨC KHỎE memory sản phẩm.
- Giả thuyết đầu vào "3 cặp board/explorer byte-identical" — chính lens POX tự bác bằng md5sum (10 hash khác nhau, chỉ trùng size).

## 6. Câu hỏi cụ thể cho chủ kit

**Q1 — Đường nâng cấp cho PO Cleanmatic (và mọi recipient 1.x)?**
(a) Build `upgrade.sh` + legacy-sweep (#1) rồi mời PO lên 2.3.0; (b) viết hướng dẫn tay uninstall→install (nhanh hơn, rủi ro thao tác PO); (c) khuyên PO cài mới vào repo sạch rồi copy `docs/product/` sang.
→ Khuyến nghị: **(a)** — PO non-technical + 3 bẫy đã chứng minh (STALE-skip, hook cũ bật ngầm, skill đôi) khiến (b)/(c) dễ tạo thêm sự cố; (c) là phương án dự phòng chấp nhận được.

**Q2 — Xử lý `metric:` → `metrics:` trên BRD đã approve (PS-13)?**
(a) Mở rộng `migrate_multidim_fields.py` + flow confirm/re-approve theo GATE; (b) check chấp nhận cả key singular (legacy-tolerant, warn thay vì error); (c) chỉ sửa message chỉ thẳng nguyên nhân, để PO tự sửa.
→ Khuyến nghị: **(a)**, kèm sửa message ngay lập tức (phần của (c)) vì migrate cần PO tham gia re-approve.

**Q3 — Nội dung bundle cho recipient: README/CLAUDE.md dev + 5 rules ck + skill `release` (PACK-5, ARC-F13)?**
(a) Biến thể recipient trọn gói (README/CLAUDE.md riêng, rules trung tính, cân nhắc bỏ `release`); (b) chỉ đặt `include_readme/include_claudemd: false` mặc định; (c) giữ nguyên + ghi chú INSTALL.md.
→ Khuyến nghị: **(a)** — repo PO thật đã mất danh tính GitHub và mang 101 tham chiếu `/ck:` chết; nếu giữ `release` cho mục đích re-share thì ghi rõ lý do vào manifest.

**Q4 — Ship template GH Action `spec-validate.yml` cho recipient (đề xuất #2)?**
(a) Có — kèm installer hỏi PO; (b) không — ngoài scope kit; (c) chỉ tài liệu hướng dẫn.
→ Khuyến nghị: **(a)** — PO đã chứng minh nhu cầu bằng cách tự chế CI sai; cỡ S, nằm trọn trong ranh giới tài-liệu.

**Q5 — GATE-NEVER-ASSUME và `.session.md` stale (CVR-F03/POX-F03)?**
(a) Ưu tiên `decisions.md` khi hai nguồn lệch + staleness warning + supersede-sweep; (b) giữ nguyên GATE, chỉ thêm forcing-function refresh; (c) loại `.session.md` khỏi danh sách nguồn assume.
→ Khuyến nghị: **(a)** — (b) không cứu được file đã stale sẵn của PO; (c) quá mạnh, mất giá trị resume.

**Q6 — Cưỡng chế memory: critique cache (PSC-3) và memory hook auto-register (CVR-F13)?**
(a) Cả hai (cache script-enforced + hook auto-register kèm opt-out); (b) chỉ critique cache; (c) giữ opt-in như hiện tại.
→ Khuyến nghị: **(b)** trước (defect đã chứng minh trên 12/15 report); (a) nếu chấp nhận nudge — kit đã có tiền lệ telemetry 2.1.0.

**Q7 — License hồi tố cho bundle 1.1.0 đã phát (CVR-F12)?**
(a) Gửi notice AGPL kèm gói nâng cấp + ghi release-notes về hiệu lực với bundle trước 2.2.1; (b) cấp điều khoản riêng cho các bundle cũ; (c) không làm gì.
→ Khuyến nghị: **(a)** — chính changelog 2.2.1 thừa nhận license phải đi kèm bản phân phối.

**Q8 — Số phận `declared_chains` của telemetry workflow-lens (LIB-5)?**
(a) Trỏ sang nguồn routing còn sống (bảng routing CLAUDE.md) — giữ tính năng SKILL.md quảng cáo; (b) gỡ feature + test (đơn giản nhất); (c) tạo lại 2 file routing doc.
→ Khuyến nghị: **(a)** nếu muốn giữ lời hứa "declared-vs-actual"; nếu không, **(b)** — (c) là chữa ngọn.

## 7. Giới hạn của audit

- Không gọi mạng: kết quả THẬT của GH Actions PO chưa xác minh (kết luận fail dựa mô phỏng sandbox cùng cấu trúc, pytest EXIT=5 — lens CVR/BUG); trạng thái run CI của KIT cũng chỉ soát tĩnh YAML (lens DRY).
- Không ghi KIT/PO-repo: installer/upgrade chưa được chạy ĐÈ thật lên bản PO — phân tích ARC-F01/F02 là static-trace theo code; sự kiện `UserPromptExpansion` cần 1 phiên Claude Code live để kết luận (LIB-9).
- Telemetry chỉ có data thật của dev (PO không có telemetry); kết luận LIB-4/7/8 dựa trên data đó — xu hướng 100% zero/unknown được critic tái đếm trên file sống.
- Nguyên nhân gốc việc 12/15 critique run không được index (PSC-3) không truy được — bước ghi do LLM-flow, không log nào còn lại.
- File lớn (change-log.md ~89K, decisions.md ~32K, visuals tới 2,5MB, render_html.py) chỉ grep/sed trích đoạn theo luật — không đọc trọn.
- Không soi nội dung business của tài liệu PO ngoài phạm vi bằng chứng; lớp LLM-judgment (interview, prose quality) ngoài scope script-audit.
- Vài lệnh bị hook chặn (pattern vendor, chuỗi nhạy cảm) — đều đo lại bằng đường khác trước khi dùng làm bằng chứng (các lens tự khai).
- Mọi ô/bảng trong report truy được về lens/critic: nhãn [CVR/BUG/DRY/POX/ARC-Fnn/Mn] + verdict đính kèm từng finding; con số nào critic tái đo lệch đã ghi chú ngay tại chỗ.
<<<END_REPORT>>>