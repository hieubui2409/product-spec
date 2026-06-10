## PHÁN QUYẾT

### [ARC-F01] → CONFIRMED
- Kiểm chứng: mở `install.sh.template:285` — đúng nguyên văn `note "[SKIP] $REL (exists; FORCE_OVERWRITE=1 to replace)"` (logic generic-file, hooks không qua nhánh version-skill); `:328` — `if CLAUDE_PROJECT_DIR="$TARGET_DIR" python3 "$REGISTRAR"; then` ✓. `register_telemetry_hooks.py:113` — "# Enforcement hooks (wired-always; config default-false makes them no-op)." và `:116` — `{"event": "Stop", ..., [MEMORY_GAP_STOP, CRITIQUE_STOP]}` ✓. Chạy lại `grep -n 'product-spec-hooks\|hooks.json\|config'` trên hook CŨ của PO → 0 match ✓; hook MỚI của KIT có gate thật (`memory_gap_hook.py:16, 315-318` — "Config gate (default-DISABLED…)"). PO không có cả `settings.json` lẫn `settings.local.json` (ls → "No such file") ✓. Old hook chặn thật: dòng 18 đúng nguyên văn; `"decision": "block"` + comment "stderr+exit 2" có trong cửa sổ 318-330 ✓. Registrar wire theo basename (`_hook_cmd("memory_gap_hook.py")`, :56-58) → trỏ đúng file cũ được giữ lại ✓.
- Ghi chú kiểm chứng thêm (không đổi verdict): đường block còn phụ thuộc import detector thành công — old hook fail-open khi import lỗi (`except Exception: return ALLOW_EXIT`, ~:309-313), và chuỗi import cần PyYAML (`frontmatter_parser.py:19 import yaml`). Trên máy thật của PO venv tồn tại (PO `.gitignore:1-2` tự ghi chú "máy tự tạo lại bằng install.sh"; registrar `_interpreter()` :48-53 sẽ chọn venv) → kịch bản block là thực tế. Critical đứng vững: blocking hook đời cũ, thiết kế gốc "opt-in only, never auto" (old docstring :14), bị wire tự động, không kill-switch nào của bản mới chạm tới nó.

### [ARC-F02] → ADJUSTED (severity Critical → High; thực chất xác nhận)
- Kiểm chứng: `install.sh.template:173` đúng nguyên văn `[STALE] … set FORCE_OVERWRITE=1 to update` + `SKILL_VERDICT="SKIP"` (:174-176) ✓; version PO `"2.0.0"` vs KIT `"2.3.1"` đều ở dòng 11 ✓; grep `rm|unlink|delete` trong install.sh.template → exit 1, 0 match (chỉ cp/mkdir) ✓; `pack.manifest.yaml:7-11` đúng 4 skill, không spec-critique/claude-pack ✓; PO skills = `claude-pack/ product-spec/ spec-critique/` ✓; PO `CLAUDE.md` 11769 bytes, match "spec-critique" tại :113/:117/:127/:131 ✓; INSTALL.md.template đúng 1 match FORCE_OVERWRITE (:80) và không có mục upgrade (sections: Verify/Extract/Install/What/Troubleshooting/Uninstall) ✓.
- Lý do ADJUSTED: (1) Severity — trên đường default, hệ cũ giữ nguyên và TỰ NHẤT QUÁN (skill cũ + 7 agent cũ + CLAUDE.md cũ vẫn vận hành như trước); tác hại là nâng-cấp-im-lặng-không-xảy-ra + 2 bề mặt critique song song + routing cũ — nguy hại UX/nhất quán nặng cho PO non-technical nhưng không chặn workflow, không hỏng dữ liệu → High (phần "bật hook chặn ngầm" — mảnh thật sự Critical — đã tách riêng ở F01). (2) Sửa vặt: PO agents = 6 file `spec-critique-*` + `memory-harvester.md` (tổng 7 agent), không phải "7 agents spec-critique-*".

### [ARC-F03] → CONFIRMED
- Kiểm chứng: chạy lại grep `version-check|update available|newer version|check_update` trên 3 SKILL.md + `release/scripts/` → 0 match (GREP_EXIT=1 — báo cáo ghi "exit 0" là sai chi tiết exit-code của grep-không-match, không đổi bản chất). PO MANIFEST.json: `"built_at": "2026-06-03T05:39:31+00:00"`, `"bundle_version": "1.1.0"`, source 1c5113f ✓. `git tag` KIT: 15 tag đúng trục claude-pack-v0.1.0…v1.4.0 → product-spec-v2.0.0…v2.3.0 ✓. Đề xuất age-beacon offline nằm trong ranh giới kit, hợp lệ.

### [ARC-F04] → CONFIRMED
- Kiểm chứng: đếm lại trên data sống (file đã lớn thêm từ lúc lens đo): `sessions.jsonl` 43 dòng — **43/43 duration_s=0** (39+4 hai format); `subagent-outcomes.jsonl` **46/46 "outcome":"unknown"**; **41/43 `"skills":[]`**, 2 record còn lại đúng là ck-plan/ck:plan ✓; `invocations.jsonl` 7 record (brainstorm 1, ck-plan 4, ck:plan 2) — 0 thuộc 4 skill bundle ✓; hook-telemetry nay 343 dòng, 100% exit 0, 126 có `ms` (tỷ lệ khớp hướng 96/235 của báo cáo). Docstring `emit_session_summary.py:8` đúng nguyên văn ✓.
- Kiểm chứng sâu hơn còn XÁC NHẬN root cause: transcript thật mở đầu bằng các record `type=last-prompt/mode/permission-mode` KHÔNG có timestamp (đọc live 3 dòng đầu một transcript trong `~/.claude/projects/...-product-spec/`); `first_timestamp()` chỉ đọc DÒNG ĐẦU (`emit_session_summary.py:60-68`) → trả None → `:115 start = start_ts or last_ts` → delta luôn 0. Finding đúng và còn dưới-mức-nghiêm-trọng-thật: lỗi là cấu trúc, không phải ngẫu nhiên.

### [ARC-F05] → CONFIRMED
- Kiểm chứng: parse record thật — keys invocations = `['session','skill','ts','via']` (không args/flag) ✓; sessions có `"files_modified": 2` (số đếm int, không path) ✓; `track_script_execution.py:5-6` đúng nguyên văn ✓; rà 13 file hooks tracked (`git ls-files`) — 5 telemetry sink + 2 enforcement, không sink nào ghi sự kiện mức artifact/interview ✓ (memory_gap `--post-tool-use` chỉ ghi touched-flag ephemeral trong $TMPDIR, không phải telemetry record). Matcher PostToolUse:Edit|Write|MultiEdit có sẵn tại `register_telemetry_hooks.py:115` ✓.

### [ARC-F06] → CONFIRMED
- Kiểm chứng: `record_outcome.py:3-6` đúng ("append-only home for measured outcomes (`OUT-<n>`)… PO declares target+actual") ✓; `behavioral_memory.py:12-14` đúng (self-corrections.json per-product) ✓; `BACKLOG.md:77` đúng — "A9 quality-gate learning loop (P3, **deferred**…" ✓; `telemetry_paths.py:31` — `d = … Path(project_dir()) / ".claude" / "telemetry"` (báo cáo ghi :32, lệch 1 dòng, vô hại) ✓; `.gitignore:170` ✓; grep `export` trong analyze_telemetry.py → 0 match ✓.

### [ARC-F07] → CONFIRMED
- Kiểm chứng: `grep -n telemetry CLAUDE.md` → 0 match, exit 1 ✓; bảng routing :10-13 đúng 3 hàng ✓; GUIDE-VI product-spec 0 match "telemetry" ✓; REGISTRATIONS (`register_telemetry_hooks.py:106-117`) không có SessionStart/surfacing ✓; telemetry/SKILL.md có "narrate in Vietnamese (default)" đúng vùng :42-44 ✓.

### [ARC-F08] → CONFIRMED
- Kiểm chứng: `grep -o '"via"…' invocations.jsonl` → đúng `7 "via": "PreToolUse:Skill"`, 0 UserPromptExpansion ✓; docstring `append_event_once` (`telemetry_paths.py:216-224`) đúng như mô tả dedup ("only the first (same dedup_key) is recorded") ✓. Finding tự giới hạn đúng mực ("chưa đủ bằng chứng kết luận event không tồn tại") — chuẩn phương pháp.

### [ARC-F09] → CONFIRMED
- Kiểm chứng: grep `migrate_multidim` trong SKILL.md + references/ → exit 1, 0 match ✓; caller thực = `generate_templates.py` + tests (grep -rln) ✓; docstring :3-4 đúng; câu "silence the PRD/Epic 'warn-if-missing' noise" ở dòng 12 (báo cáo ghi :13, lệch 1) ✓; PO PRD đo lại đúng từng số: `risks:` **0/10**, `depends_on:` **2/10** ✓.

### [ARC-F10] → CONFIRMED
- Kiểm chứng: `pack.manifest.yaml:31-35` ship đúng 5 rules ✓; `primary-workflow.md:10` ("load `.claude/skills/cook/references/workflow-routing.md`"), `:29` ("/ck:preview"), `orchestration-protocol.md:42` ("use `/ck:team`") — cả 3 đúng nguyên văn ✓; manifest không ship cook/preview/team ✓.

### [ARC-F11] → ADJUSTED (một claim tuyệt đối sai; phần gap chính vẫn đúng)
- Kiểm chứng: `lens_memory_health.py:1-3` đúng nguyên văn (audit memory dir của assistant `~/.claude/projects/<root>/memory/`) ✓; telemetry/SKILL.md:59 ✓; PO `docs/product/.memory/` đúng 4 mục (critique-lens-cache/, critique-findings-index.json, critique-state.json, last_critique.json), không có last_validated.json/preferences ✓.
- Lý do ADJUSTED: câu "KIT cũng không có lens nào đọc `docs/product/.memory` (rà 8 lens scripts)" **sai**: `lens_validate_proxy.py:6` — "1. last_validated.json marker (docs/product/.memory/, written on --validate)" — một lens CÓ đọc thư mục này. Claim đúng phải thu hẹp thành: không lens nào đánh giá SỨC KHỎE memory sản phẩm (store nào rỗng/thiếu, po-style, self-corrections, cache size) — validate-proxy chỉ đọc 1 marker cho mục đích pass/fail. Severity Medium và đề xuất hợp nhất vẫn đứng.

### [ARC-F12] → CONFIRMED
- Kiểm chứng: `install.sh.template:348` đúng nguyên văn `log "Done. Invoke skills from Claude Code, e.g. /cleanmatic:claude-pack"` ✓; manifest không có claude-pack, KIT không có thư mục skill đó (ls → No such file) ✓; `templates.py:3-4` — token format `{{UPPERCASE_NAME}}`, chuỗi không chứa `{{}}` → ship nguyên văn ✓.

### [ARC-F13] → CONFIRMED
- Kiểm chứng: `pack.manifest.yaml:9` — `- release` ✓; `CLAUDE.md:15-16` — "code/CLI vocabulary for `release`" ✓. Finding đã tự ghi nhận giả thuyết re-share một cách trung thực; Low/YAGNI đúng cỡ.

## BỎ SÓT (≤3)

### [ARC-M1] Telemetry JSONL + settings.json sẽ nằm trong working tree PO và bị commit lên GitHub — lá chắn gitignore không đi theo bundle
- Mức độ: Medium
- Loại: ENV
- Bằng chứng:
  - KIT chỉ chắn phía dev: `.gitignore:170` — `/.claude/telemetry/`; bundle KHÔNG ship gitignore nào cho recipient: `pack.manifest.yaml:37-39` (`extra:` chỉ `LICENSE`, `CONTRIBUTING.md`); `grep -n gitignore` trên install.sh.template + INSTALL.md.template → exit 1, 0 match.
  - PO `.gitignore` (35 dòng): grep `telemetry` → 0 match; chỉ ignore `settings.local.json` (:15), không ignore `.claude/settings.json`.
  - Sau install, registrar auto-bật 5 sink ghi vào `<repo>/.claude/telemetry/` (`telemetry_paths.py:31`, mkdir luôn) và TẠO `settings.json` mới (`register_telemetry_hooks.py:121-124` — "Treat absence as an empty config so auto-registration can create it").
- Phân tích: lens đã xếp "telemetry → gitignore + CI-assert tarball-exclusion" vào mục "Đã kiểm và SẠCH" — chỉ đúng cho repo dev. Trên repo PO sau upgrade, mỗi phiên đẻ thêm JSONL (session UUID, đường dẫn file, tool counts) untracked + settings.json → diff lạ làm PO non-technical bối rối, dữ liệu sử dụng nội bộ bị đẩy lên GitHub, hooks bị áp lên mọi người clone repo. Đây là khoảng trống đúng địa hạt "kiến trúc telemetry cho PO".
- Đề xuất: installer thêm bước append-nếu-thiếu `.claude/telemetry/` (cân nhắc cả `.claude/settings.json`) vào .gitignore recipient (tạo file nếu chưa có) + 1 dòng giải thích VI; tối thiểu ghi vào mục "What gets installed" của INSTALL.md.

### [ARC-M2] hook-telemetry nhiễm false-positive: lệnh chỉ NHẮC tới script (grep/sed/ls, glob) cũng bị ghi như một lần chạy — làm bẩn luôn validate-proxy
- Mức độ: Medium
- Loại: CORRECTNESS
- Bằng chứng:
  - Matcher là substring-search thuần, không kiểm script có được THỰC THI: `hook_runtime.py:41` — `SCRIPT_RE = re.compile(r"\.claude/skills/([^\s/]+/scripts/[^\s]+\.(?:py|sh))")`; cổng duy nhất là `m = SCRIPT_RE.search(cmd)` (`track_script_execution.py:57-59`). Docstring hứa khác: `:5-6` — "Filters to commands that **run** a … — ignores plain git/ls/grep" (chỉ đúng khi lệnh không chứa path script).
  - Data thật: **10 record** `"script": "product-spec/scripts/*.py"` — một glob literal, không phải file script nào (sinh từ lệnh dạng `ls/grep/wc …/scripts/*.py`); trong cửa sổ phiên audit read-only hôm nay, record mới vẫn mọc cho đúng các file chỉ bị grep (vd `04:35:34.99 "script": "telemetry/scripts/lens_workflow_chains.py", "exit": 0`).
  - Lan sang tín hiệu effectiveness duy nhất: `lens_validate_proxy.py:9-10` — "hook-telemetry.jsonl validate-script exit history (check_*/strict_gate runs) → the directional pass RATE … (exit 0 = pass)" → một grep nhắc tới `check_*.py` được đếm như một lần validate PASS.
- Phân tích: F04 chỉ ra data CHẾT; lens bỏ qua data BẨN — "script runs" phồng theo mọi thao tác đọc file của LLM, script-health và validate-proxy lệch về hướng lạc quan. Sau upgrade, hiệu ứng này chạy thẳng trên repo PO.
- Đề xuất: siết matcher về dạng thực-thi (path phải đứng đầu lệnh hoặc ngay sau interpreter `python3|bash|sh`), bỏ match glob chưa expand; thêm test fixture lấy từ chính các record glob/grep thật.

### [ARC-M3] Record script-run không mang `session` dù biến đã được tính — hook-telemetry không join được với sessions/invocations
- Mức độ: Medium
- Loại: ARCHITECTURE
- Bằng chứng: `track_script_execution.py:61` — `session = data.get("session_id") or os.environ.get("CK_SESSION_ID") or ""` nhưng record :62-68 chỉ gồm `{ts, source, script, exit}` (+`ms` :69-71), `session` chỉ dùng cho pairing duration. Data thật xác nhận: toàn bộ 414 record chỉ có 2 key-set `('exit','script','source','ts')` ×270 và (+`ms`) ×144 (đếm bằng python trực tiếp). Trong khi 3 sink kia đều mang `session` và `lens_workflow_chains.py:50` join theo `rec.get("session")`.
- Phân tích: mất chiều liên kết "phiên nào chạy/lỗi script nào" — đúng câu hỏi tiêu chí (c) "PO kẹt ở đâu" mà lens tự đặt; sửa 1 dòng, không thêm rủi ro privacy (session id đã có ở invocations/sessions/subagent-outcomes).
- Đề xuất: thêm `"session": session` vào record + cập nhật fixtures/tests; các lens forensics/workflow tận dụng khóa này khi có.

## TÓM TẮT CHẤT LƯỢNG LENS
Độ tin cậy cao: 11/13 CONFIRMED, 2 ADJUSTED (F11 có một claim tuyệt đối sai vì bỏ sót `lens_validate_proxy.py:6`; F02 severity nên hạ Critical→High), 0 REFUTED. Mọi trích dẫn mở ra đều đúng file:dòng (sai số ±1 dòng ở 3 chỗ, vô hại); số liệu telemetry trượt nhẹ chỉ vì file sống tiếp tục ghi — xu hướng 100% zero/unknown giữ nguyên, và kiểm chứng sâu còn tìm ra root cause duration=0 củng cố F04. Thiên lệch nhận thấy: (1) tin "SẠCH" phía dev rồi suy ra recipient an toàn → bỏ sót chuyện gitignore/settings.json không đi theo bundle (M1); (2) tập trung data CHẾT mà bỏ qua data BẨN và khóa join thiếu trong chính sink đang chạy (M2, M3); (3) hơi nghiêng thổi severity ở nhánh upgrade khi tác hại là confusion chứ không phải blocking. Phương pháp tự giới hạn (F08, F13) trung thực, đề xuất đều bám bằng chứng và nằm trong ranh giới kit.
