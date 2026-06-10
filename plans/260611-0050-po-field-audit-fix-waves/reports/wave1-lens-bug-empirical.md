## TÓM TẮT

Đã chạy đại diện mọi nhóm script của kit HEAD (v2.3.x) trên dữ liệu thật của PO (147 node: 10 PRD/30 epic/102 story) trong sandbox. Không có crash/traceback nào trên happy-path; parser YAML chịu được toàn bộ data PO (0 parse_errors). Nhưng stress test lộ 10 vấn đề thật, 4 ở mức High:

1. **Upgrade phá spec đã approve**: kit mới thêm check `goal_without_metric` nhưng data PO (do chính skill bản cũ viết) dùng `metric:` (số ít) thay vì `metrics:` (list) → 3 error trên BRD đã approved, `strict_gate` exit 2, và đường `--learn` không ghi nổi outcome cho bất kỳ goal nào. Không có migration.
2. **`--status`/`memory_gap` phun 1.09MB JSON với 2.258 cảnh báo `fence_breach`** — một cảnh báo cho MỖI file untracked ngoài `docs/product/`, kể cả chính bộ `.claude/` của kit; không cap, không loại trừ.
3. **Bundle critique luôn nhét toàn bộ corpus**: `source_files` chứa cả 148 artifact (422K chars) kể cả khi scope chỉ 1 PRD → bundle 700KB/PRD, 1.24MB scope=all, đẩy vào 4 lens agent song song.
4. **Test tracked đỏ ngay tại HEAD**: commit e52e077 xoá 2 file routing docs nhưng quên lens + test telemetry phụ thuộc chúng; CI không chạy suite telemetry nên lọt.

## FINDINGS

### [BUG-F01] Check `goal_without_metric` mới phá BRD đã approve của PO — không có đường migrate, message đánh lạc hướng
- Mức độ: High
- Loại: CORRECTNESS
- Bằng chứng:
  - Data PO: `docs/product/brd.md:16` — `metric: Số hub hoạt động tích cực tăng từ ≤20 lên ≥50...` (key **số ít**, giá trị prose; goal `status: approved` toàn file).
  - Spec (cả cũ lẫn mới) yêu cầu key **số nhiều**: `references/frontmatter-and-id-spec.md:89` — `metrics: [brands-onboarded]  # required, ≥1 metric slug`. `spec_graph.py:176` chỉ đọc `goal.get("metrics") or []` → metrics của PO thành `[]`.
  - Check mới: `check_consistency.py:196-203` fire error; chạy thật: `strict_gate.py --root .` → exit **2**, output: `BLOCKED on errors: goal_without_metric · BRD-G1/G2/G3`.
  - Bản PO đang dùng (claude-pack 1.1.0) KHÔNG có check này: `grep goal_without_metric .claude-po-original/skills/product-spec/scripts/*.py` → 0 match → PO chưa từng thấy lỗi, và chính skill cũ (LLM interview) đã viết field sai schema của chính nó.
  - `migrate_multidim_fields.py` không xử lý: `grep metric` trên script → 0 match (chỉ migrate risks/target_date/depends_on/competitive_parity).
  - Hệ quả dây chuyền lên `--learn`: `record_outcome.py --append-alloc --goal BRD-G1 --metric "số hub" ...` → `{"error": "invalid_input", "message": "metric 'số hub' is not in BRD-G1's metrics []; ... pass --force"}` — PO không ghi được outcome cho goal nào nếu không `--force`.
- Phân tích: PO nâng cấp bundle → validate đang xanh bỗng đỏ 3 error trên artifact **approved**, CI strict gate chặn, vòng learn tê liệt. Message "has no success metric" sai thực tế với PO (họ NHÌN THẤY metric trong file) — không hề gợi ý nguyên nhân là `metric:` vs `metrics:`. Sửa thì phải đụng artifact approved → vướng GATE-NO-SILENT-REVERSAL, kit lại không có forcing-function nào dẫn PO qua flow đó.
- Đề xuất: (a) thêm nhánh nhận diện key `metric` (singular/string) trong check → message chỉ thẳng "bạn đang dùng `metric:`, schema cần `metrics: [slug]`"; (b) mở rộng `migrate_multidim_fields.py` migrate `metric` → `metrics` (giữ nguyên giá trị, qua flow confirm vì artifact approved); (c) note nâng cấp trong CHANGELOG/INSTALL cho người dùng bản claude-pack cũ.

### [BUG-F02] `status.py`/`memory_gap.py` phun 2.258 `fence_breach` (1.09MB JSON) — không cap, đếm cả chính file kit
- Mức độ: High
- Loại: ARCHITECTURE
- Bằng chứng: `status.py --root .` exit 0 nhưng stdout **1.086.985 bytes**; đếm: `Counter({'fence_breach': 2258, 'validate_no_marker': 1})`. Sandbox có 2.265 đường dẫn untracked (`git -C <sandbox> status --porcelain -uall | wc -l` = 2265, trong đó 1.913 thuộc `.claude/`). Nguồn: `check_fence.py:36` `FENCE_PREFIX = "docs/product/"` — mọi path ngoài fence thành 1 finding, không có cap/aggregate; `memory_gap.py:151-160` map 1-1 sang signal; `status.py:194` nhúng nguyên mảng.
- Phân tích: Kịch bản rất thật: PO cài bundle nhưng chưa commit `.claude/` (hoặc có thư mục làm việc bẩn) rồi hỏi "spec tôi ổn không?" → script trả 1MB JSON, LLM phải nuốt 2.258 dòng cảnh báo trùng dạng — tràn context hoặc nudge thành vô dụng. Bộ `.claude/` do chính kit cài mà bị kit báo "touched outside the spec boundary" là tự báo động giả.
- Đề xuất: (a) exclude mặc định `.claude/`, `.claude-po-original/`, pattern gitignore-style; (b) aggregate theo thư mục gốc + cap (ví dụ top 20 + `"...and N more"`); (c) tổng số giữ trong field count để LLM narrate.

### [BUG-F03] Bundle critique nhét toàn bộ corpus bất kể scope — 700KB/1 PRD, 1.24MB scope=all, nhân 4 lens
- Mức độ: High
- Loại: ARCHITECTURE
- Bằng chứng: `critique_scan.py --root . --scope PRD-SALES --lang vi` → file **699.415 bytes**; trong đó `source_files` = 148 key / 422.111 chars, **123 key không thuộc target_ids** (đo bằng script trên output). Scope=all → **1.236.477 bytes**, digest 147 entry trong đó 145 `verbosity: full` (515.910 chars). Nguồn: `critique_signals.py:28` `_source_files(root, graph)` loop **mọi** node của graph (`for n in nodes: ... out[nid] = numbered`), không lọc theo scope; `critique_bundle.py:117` gọi thẳng.
- Phân tích: Workflow spawn 4 lens agent, mỗi agent đọc nguyên bundle (`workflow-critique.md:122`) → với spec cỡ PO (147 node) là ~170-300K token context **mỗi lens**. Lens PRD-SALES không bao giờ cite story của 9 PRD khác — 60%+ payload là chết. Đây là điểm sẽ gãy đầu tiên khi spec PO lớn thêm.
- Đề xuất: lọc `source_files` theo `target_ids ∪ ancestry ∪ digest ids` (giữ key-by-ID nguyên vẹn); cân nhắc `verbosity: struct` cho descendants ở scope=all.

### [BUG-F04] Test tracked fail ngay tại HEAD: routing docs bị xoá ở e52e077 nhưng lens + test telemetry còn trỏ vào; CI không chạy suite telemetry
- Mức độ: High
- Loại: CORRECTNESS
- Bằng chứng: `pytest .claude/skills/telemetry/scripts/tests` → `FAILED ...test_lens_workflow_chains.py::test_declared_chains_parsed_from_routing_docs` (`assert 0 >= 1`), **1 failed, 108 passed**. Lens: `lens_workflow_chains.py:23-25` hardcode `root/.claude/rules/skill-workflow-routing.md` + `skill-domain-routing.md`; cả hai không tồn tại (`ls` → No such file) và bị xoá tại `git show e52e077 --stat`: `.claude/rules/skill-domain-routing.md | 154 ---`, `.claude/rules/skill-workflow-routing.md | 68 -`. Test vẫn tracked (`git ls-files` có `test_lens_workflow_chains.py`). CI: `grep working-directory .github/workflows/*.yml` → chỉ product-spec / product-spec-critique / release — **không workflow nào chạy tests telemetry**.
- Phân tích: HEAD (đã release v2.3.0) mang một test đỏ; tính năng `declared_chains` thành dead code — chạy thật trong sandbox ra `WORKFLOW — 0 phiên, 0 chuỗi, 0 sai lệch` vĩnh viễn (declared luôn `[]` → deviation không bao giờ tính). Lỗ hổng CI để lớp bug "xoá file, quên consumer" lọt qua.
- Đề xuất: (a) quyết định số phận `declared_chains` — trỏ sang nguồn routing còn sống (bảng routing trong `CLAUDE.md`?) hoặc gỡ feature + test; (b) thêm job CI cho `.claude/skills/telemetry/scripts/tests`.

### [BUG-F05] Sentinel `<missing-id>` lộ ra finding PO-facing và lọt vào `target_ids`/`source_files` của critique; PRODUCT.md thiếu `id` không bị báo
- Mức độ: Medium
- Loại: UX-PO
- Bằng chứng: PO's `PRODUCT.md` không có `id:`/`type:` trong frontmatter (`grep '^id:'` → 0 match; template cũ lẫn mới đều có `id: PRODUCT`). Finding chạy thật: `"<missing-id> declares 7 personas; soft cap is 4..."` (`artifact_id: "<missing-id>"`). Nguồn: `check_consistency.py:176` nhúng thẳng `{n['id']}` vào detail; trong khi `spec_graph.py:571-576` ghi rõ `ID_SENTINELS` là "internal sentinel... the PO never sees". Check `invalid_id` không phủ type `product`/`vision` (`ID_PATTERN_BY_TYPE` tại `spec_graph.py:597-602` chỉ có goal/prd/epic/story) nên thiếu id không tự thành finding. Bundle critique scope=all: `target_ids[0] = "<missing-id>"`, `source_files` có key `<missing-id>` → lens được lệnh cite `<artifact_id>:<line>` sẽ đẻ ra citation `<missing-id>:n`.
- Phân tích: PO non-technical đọc "`<missing-id>` declares 7 personas" không thể biết file nào, lỗi gì, sửa đâu. Nguyên nhân gốc (PRODUCT.md do skill cũ sinh thiếu `id:`) lại không hề được flag riêng.
- Đề xuất: (a) thêm finding `missing_id` (error/warn) cho mọi artifact thiếu `id`, message nêu tên file; (b) các detail formatter thay sentinel bằng tên file khi gặp `ID_SENTINELS`; (c) critique bundle lọc sentinel khỏi `target_ids`/`source_files`.

### [BUG-F06] `--apply-critique` mất đường deterministic đúng trên báo cáo quan trọng nhất của PO (whole-spec final gate, 2 blocker)
- Mức độ: Medium
- Loại: FEATURE-GAP
- Bằng chứng: `parse_critique_report.py --report docs/product/critique/20260609T233523Z-all.md` → `findings: 0`, note: `"lens-cache absent — fall back to a manual prose walk of the report (best-effort)..."`. Frontmatter báo cáo này CÓ `bundle_version: 2 / level: 5 / scope: all` nhưng **không có `lens_findings_hash`**; `.memory/critique-lens-cache/` chỉ có 3 hash (8b0de699…, d0cfd9…, d22c65…) — không cái nào của run all. Đối chứng: report PRD-CARE parse ra 22 findings + freshness đầy đủ (cache có mặt).
- Phân tích: Báo cáo chốt cuối chứa 2 blocker (mâu thuẫn North Star 30 vs 50; giả định Zalo-switch xuyên 5 PRD) là thứ PO cần walk nhất — nhưng phần struct trả 0 finding, đẩy toàn bộ cho LLM tự bóc prose (rủi ro sót/sai fingerprint, mất resume/dedup). Dữ liệu do bản cũ sinh, song kit mới cũng không có cách tái tạo cache từ prose.
- Đề xuất: workflow consolidator phải LUÔN ghi lens-cache + `lens_findings_hash` vào frontmatter (kể cả scope=all); cho `parse_critique_report` chế độ best-effort bóc heading `[severity][lens]` từ prose để ít nhất ra danh sách thô thay vì 0.

### [BUG-F07] Tích tụ output không hồi kết: roadmap HTML 2.5MB/lần render, exports trùng nội dung vẫn ghi file mới
- Mức độ: Medium
- Loại: CLEANUP
- Bằng chứng: `visualize.py --view roadmap --format html` ghi file **2.618.333 chars**, trong đó 1 block `<script>` 2.571.831 chars là mermaid esbuild inline (đo trực tiếp trên file output). Thư mục visuals sandbox: **11MB** (PO repo thật: 6.7MB, có sẵn 2 bản roadmap 2.5MB từ 06-03). Exports: `all-20260610T034005Z-af7d5c83.md` và `all-20260610T042805Z-af7d5c83.md` — **cùng content-hash `af7d5c83`** (383.8K mỗi file) vẫn thành 2 file vì timestamp đổi.
- Phân tích: Mỗi lần PO "cho tôi xem roadmap" là +2.5MB; không có retention/prune, không reuse khi nội dung không đổi. Repo spec của PO phình vô hạn theo số lần xem.
- Đề xuất: (a) khi content-hash trùng file gần nhất → trả đường dẫn cũ thay vì ghi mới; (b) lệnh/flag prune giữ N bản mới nhất mỗi view; (c) cân nhắc external vendor file dùng chung cho các HTML mermaid thay vì inline mỗi file.

### [BUG-F08] `check_consistency.py` traceback `BrokenPipeError` khi consumer đóng pipe sớm
- Mức độ: Low
- Loại: CORRECTNESS
- Bằng chứng: pipe stdout của `check_consistency.py` vào process không đọc stdin → `Traceback ... File ".../check_consistency.py", line 380, in main / print(json.dumps(output, ...)) / BrokenPipeError: [Errno 32] Broken pipe` (nguyên văn từ lần chạy `check_consistency.py --root . | strict_gate.py`).
- Phân tích: Pattern `script | head -50` là thao tác chuẩn của LLM khi output JSON ~300KB (đúng cỡ output thật trên data PO). Docstring tự cam kết "never a bare traceback" — đây là vi phạm contract đó, dù vô hại về data.
- Đề xuất: bọc print cuối trong try/except BrokenPipeError (hoặc `signal(SIGPIPE, SIG_DFL)` trong `configure_utf8_console`) — áp dụng chung cho mọi script in JSON lớn.

### [BUG-F09] Output telemetry tiếng Việt lẫn nguyên câu tiếng Anh hardcode ở dòng VALIDATE-PROXY
- Mức độ: Low
- Loại: CONSISTENCY
- Bằng chứng: chạy `analyze_telemetry.py --lens all --format ascii` (default vi) → giữa banner Việt: `[i] VALIDATE-PROXY — not available on current data (no validate marker, no validate-script runs)`. Nguồn: `lens_validate_proxy.py:82` hardcode reason tiếng Anh; trong khi `telemetry_render.py:173` đã có bản dịch `"val_na": "chưa có dữ liệu"` nhưng nhánh `a_val_na` format thẳng `{reason}` từ lens (`telemetry_render.py:182`).
- Phân tích: Skill cam kết "narrate in Vietnamese (default)" cho PO non-technical; reason kỹ thuật tiếng Anh chen vào đúng dòng PO cần hiểu nhất (vì sao không có số liệu).
- Đề xuất: lens trả `reason_code`, render map sang label đã localize (tận dụng `val_na` sẵn có).

### [BUG-F10] Bảng `--viz audit` ASCII rộng 368 ký tự/dòng trên data PO — không đọc nổi trong terminal
- Mức độ: Low
- Loại: UX-PO
- Bằng chứng: `assemble_audit_trail.py --root . --format ascii --lang vi` → 111 dòng, dòng dài nhất **368 ký tự** (đo `awk max length` trên output); cột "Hành động"/"Thay đổi" không truncate theo bề rộng nào.
- Phân tích: Title change-log tiếng Việt của PO dài tự nhiên → bảng tràn/wrap nát ở mọi terminal 80-120 cột. ASCII là format "downgraded, never removed" — nhưng ở bề rộng này nó vô dụng đúng lúc cần nhất (môi trường không mở được HTML).
- Đề xuất: truncate cell theo budget cột (ellipsis) + tổng bề rộng mục tiêu ~120 cột; giữ full text cho `--format md`.

## GIỚI HẠN & KHÔNG TÌM THẤY

**Đã kiểm và SẠCH (hành vi đúng, không phải finding):**
- `check_traceability.py`: 0 findings trên 147 node PO — hierarchy/links của PO thật sự liền mạch. `spec_graph.py`: 147 nodes/147 edges/0 parse_errors (YAML tiếng Việt, ký tự ≥/≤/→ đều qua); `--downstream BRD-G1` đúng. `build_traceability_matrix.py` OK.
- `decision_register.py --list`: parse đủ DEC-1…DEC-44 từ `decisions.md` 32K, đúng thứ tự, không sót.
- `persona_cap_exceeded` (7 warn) + `risk_high_ratio` (2 warn) là lỗi dữ liệu PO thật, message rõ ràng — kit báo đúng.
- `reflect_scan.py`, `behavioral_memory.py --dump` (stores rỗng hợp lệ), `apply_critique_progress.py --show` (resolved {}), `check_report_language.py` (15 reports, skip `vi` đúng thiết kế), `ingest_raw_inputs.py` (fence + cap 1MB hoạt động, nhận change-log.md 89K ở dry mode), `record_outcome.py --alloc-id`, critique `--drift`/`--vs-validated` (1 node drift, field `source` minh bạch khi thiếu marker validated) — đều exit 0, output đúng contract.
- `visualize.py`: 9 view ascii + mermaid tree/roadmap + html risk/competition/dashboard/board/explorer/audit + 5 learning view đều exit 0; empty-state có message Việt thân thiện ("Chưa ghi kết quả nào — chạy --learn…", "(no baseline yet — run --validate…)"); `--layers bogus` bị reject exit 2 đúng cam kết SKILL.md. Không lệnh nào chạy quá ~0.9s trên data PO (critique_scan scope=all chậm nhất: 0.89s).
- pytest baseline KIT: product-spec **pass toàn bộ** (exit 0); critique suite pass; telemetry **1 failed/108 passed** (= BUG-F04, fail sẵn ở HEAD, không phải do data PO).
- `goal_without_metric` không phải lỗi parser data PO: cùng input, mọi script đọc nhất quán `metrics: []`.

**Không kiểm được / không chạy:**
- `check_consistency_time/_risk/_competition.py` không phải CLI riêng (không có `__main__`/argparse — xác minh bằng grep): chạy trực tiếp exit 0 im lặng; chúng được import vào `check_consistency.py:36/46/53` nên đã test gián tiếp. Tương tự `assemble_digest.py`, `load_outcomes.py`, `render_outcomes.py` là library — test gián tiếp qua `render_export.py` (export all OK, 383.8K) và learning views.
- Telemetry chỉ chạy được trên sandbox (không có data → toàn 0); không chạy trên data telemetry thật của KIT vì `telemetry_dir()` có side-effect `mkdir` trong cây KIT (cấm ghi KIT).
- Không chạy: installer (`install.sh`), hooks Python (cần session Claude thật), eval suites, `ingest --scaffold`, các đường ghi `--voice`/`--append` decision/outcome thành công (chỉ thử đường lỗi để giữ data sandbox sạch cho lens khác), lớp LLM judgment (ngoài scope script).
- 1 lệnh `ls` vào `assets/vendor/` của KIT bị hook scout-block chặn (pattern `vendor`) — đo size vendored mermaid gián tiếp qua file HTML output.
- Traceback của test telemetry fail hiển thị path lạ `/home/hieubt/Documents/cleanmatic-skills/...` — là `__pycache__` cũ (rác local untracked trong KIT) nhúng path checkout cũ; assertion fail là thật, tái lập được với `-B -p no:cacheprovider`.
- Mọi thao tác ghi (visuals/exports/telemetry dir mới) chỉ xảy ra trong SANDBOX; KIT và PO-REPO không bị ghi file nào.
