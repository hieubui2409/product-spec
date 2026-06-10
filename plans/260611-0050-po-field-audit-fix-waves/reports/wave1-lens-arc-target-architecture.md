Evidence base is complete. Compiling the report.

## TÓM TẮT
Kit HEAD (product-spec v2.3.0) đã có đủ "xương" cho 5 tiêu chí nhưng 3 mạch máu chính chưa thông: **(c) telemetry** — pipeline 5 hook + 8 lens tự bật khi cài, nhưng trên data thật của chính dev: 41/41 session `duration_s:0`, 40/40 subagent `outcome:"unknown"`, 39/41 `skills:[]` → các lens không trả lời được "PO dùng gì, kẹt đâu"; **(d) insight** — telemetry skill kể chuyện VI rất tốt nhưng vô hình (không có route trong CLAUDE.md, không nudge); product-insight (`--learn`/scorecard) mới ship 2026-06-09, PO thật chưa từng có; **(e) self-learning** — chỉ có self-corrections per-product + outcomes PO tự khai; learning-loop kit-level bị defer chính thức (BACKLOG A9), telemetry local-only → vòng phản hồi dev đứt hẳn. Pain số 1 nhìn từ PO-repo là **upgrade path**: installer HEAD chạy đè lên claude-pack 1.1.0 sẽ (1) mặc định KHÔNG nâng product-spec (STALE KEPT, đòi `FORCE_OVERWRITE=1`), (2) không dọn skill/agent/hook cũ → 2 skill critique song song, và (3) nguy hiểm nhất: registrar auto-wire `memory_gap_hook.py` BẢN CŨ không có config-gate → hook chặn (exit 2) bật ngầm mà PO chưa từng opt-in. 3 phát hiện đắt nhất: ARC-F01 (hook chặn cũ bật ngầm khi upgrade), ARC-F02 (upgrade tạo cài đặt Frankenstein), ARC-F04+F05 (telemetry "có ống nhưng chưa có nước": data chết + thiếu hẳn event tầng artifact/interview).

## FINDINGS

### [ARC-F01] Upgrade đè lên v1.1.0 kích hoạt ngầm hook chặn (memory_gap) bản cũ không có config-gate
- Mức độ: Critical
- Loại: CORRECTNESS
- Bằng chứng:
  - Installer mặc định GIỮ file đã tồn tại: `install.sh.template:285` — `note "[SKIP] $REL (exists; FORCE_OVERWRITE=1 to replace)"`; PO đã có `.claude/hooks/memory_gap_hook.py` (17.3K, `ls` PO hooks: `memory_gap_hook.py  spec_critique_nudge.py`).
  - Installer auto-chạy registrar: `install.sh.template:328` — `if CLAUDE_PROJECT_DIR="$TARGET_DIR" python3 "$REGISTRAR"`.
  - Registrar wire enforcement hook VÔ ĐIỀU KIỆN theo đường dẫn basename: `register_telemetry_hooks.py:113` — `# Enforcement hooks (wired-always; config default-false makes them no-op).` và `:116` — `{"event": "Stop", ..., "commands": [MEMORY_GAP_STOP, CRITIQUE_STOP]}`.
  - Hook CŨ của PO KHÔNG đọc config: `grep -n 'product-spec-hooks\|hooks.json\|config' .../Cleanmatic-ERP/.claude/hooks/memory_gap_hook.py` → `0 matches`; và nó chặn thật: dòng 18 — "then the detector, then emits a block decision or exits 0", dòng 322/326 — `"block"` / "exit 2".
  - PO hiện không có settings.json (`ls .../Cleanmatic-ERP/.claude/settings.json` → "No such file") → trước nay hook cũ chưa từng được wire.
- Phân tích: "Config default-false makes them no-op" chỉ đúng với file hook MỚI. Đường default-upgrade (không `FORCE_OVERWRITE`) giữ file cũ nhưng registrar vẫn wire nó vào Stop + PostToolUse → PO non-technical bỗng bị một blocking hook đời 1.1.0 chặn cuối phiên, không hiểu vì sao, không biết tắt (config-gate mới không có tác dụng với file cũ).
- Đề xuất (đề xuất kiến trúc #1 — "Registrar version-guard", cỡ S, rủi ro thấp, giá-trị/chi-phí #1): trước khi wire 2 enforcement hook, registrar kiểm file đích có chuỗi nhận diện bản config-gated (vd đọc `product-spec-hooks.json` key trong source) — nếu là bản cũ thì không wire + in cảnh báo; đồng thời installer nên coi `.claude/hooks/*.py` là code kit (overwrite-with-backup mặc định, không áp logic skip-existing như PO-prose).

### [ARC-F02] Installer không có cleanup/uninstall — upgrade tạo cài đặt lai: 2 skill critique song song, CLAUDE.md cũ route về skill cũ, skill chính không được nâng
- Mức độ: Critical
- Loại: ARCHITECTURE
- Bằng chứng:
  - Default không nâng skill cũ: `install.sh.template:173` — `note "[STALE] skill '$slug' ($exist_v → $bundle_v; set FORCE_OVERWRITE=1 to update)"`; PO product-spec SKILL.md `version: "2.0.0"` (dòng 11) vs KIT HEAD `"2.3.1"` (dòng 11) → STALE KEPT.
  - Không có bất kỳ lệnh xóa nào trong installer (toàn bộ vòng lặp chỉ `cp`/`mkdir`, `install.sh.template:221-300`); bundle HEAD không chứa `spec-critique`/`claude-pack` (`pack.manifest.yaml:7-11`: product-spec, release, product-spec-critique, telemetry) → 3 skill cũ của PO (`claude-pack/ product-spec/ spec-critique/` — ls PO skills) và 7 agents `spec-critique-*` tồn tại nguyên vẹn sau upgrade.
  - CLAUDE.md của PO (11.5K, đã tồn tại → SKIP khi không FORCE) vẫn route về skill cũ: PO `CLAUDE.md:117` — "Operates **`cleanmatic:spec-critique`**" và `:127` — "see `.claude/skills/spec-critique/SKILL.md`".
  - INSTALL.md.template không có mục upgrade: grep `FORCE_OVERWRITE` chỉ 1 match tại dòng 80 (mục rollback).
- Phân tích: PO chạy `bash install.sh` (cách duy nhất họ biết) sẽ nhận: product-spec vẫn 2.0.0, product-spec-critique MỚI cài cạnh spec-critique CŨ → hai skill cùng match một yêu cầu critique, agent cũ/mới lẫn lộn, CLAUDE.md (always-on routing) vẫn trỏ bản cũ. Kể cả `FORCE_OVERWRITE=1` cũng chỉ đè file trùng tên — rác cũ vẫn nằm đó và vẫn được Claude Code load như skill hợp lệ. Với đối tượng PO non-technical (tiêu chí a), một biến env tiếng Anh + verdict "[STALE]" trong stdout là không đủ.
- Đề xuất (đề xuất #2 — "Upgrade một lệnh + legacy-cleanup manifest", cỡ M, rủi ro: xóa nhầm file user-sửa → giảm bằng danh sách legacy tường minh + backup; giá-trị/chi-phí #2): bundle ship thêm danh sách legacy-paths đã biết (skills/spec-critique, skills/claude-pack, agents/spec-critique-*.md, hooks/spec_critique_nudge.py) + một `upgrade.sh` (hoặc mode trong installer) = FORCE-đè-có-backup + hỏi-rồi-xóa legacy + thay CLAUDE.md; INSTALL.md thêm mục "Nâng cấp" song ngữ. Lấp F01+F02+F03.

### [ARC-F03] Không tồn tại kênh version-check/notify — PO kẹt 1.1.0 không có cách biết bản mới
- Mức độ: High
- Loại: FEATURE-GAP
- Bằng chứng: `grep -rn 'version-check|update available|newer version|check_update|notify'` trên SKILL.md của release/product-spec/telemetry + toàn bộ `release/scripts/*.py` → 0 kết quả (lệnh chạy exit 0, không match). PO INSTALL.md (v1.1.0) chỉ có Verify/Install, không nói gì về cập nhật. Trục tag KIT đã đi claude-pack-v0.1.0…v1.4.0 → product-spec-v2.0.0…v2.3.0 trong khi PO đứng yên ở bundle built 2026-06-03 (PO MANIFEST.json: `"bundle_version": "1.1.0"`).
- Phân tích: 6 ngày PO làm việc cường độ cao (15 báo cáo critique, change-log 89K) trên bản thiếu toàn bộ telemetry/learn/viz mới. Khoảng cách kit-PO sẽ chỉ giãn thêm nếu không có beacon nào.
- Đề xuất (đề xuất #3 — "Age-beacon offline trong --status", cỡ S, rủi ro: nag nhẹ; rank #4): `status.py` đọc `MANIFEST.json` (đã ship sẵn `built_at`/`bundle_version` — PO MANIFEST.json:2-4) → in 1 dòng VI "Bundle bản 1.1.0, cài N ngày trước — hỏi người phát hành xem có bản mới chưa". Không cần network → giữ no-runtime-network. Kênh chủ động hơn (check GitHub release) nếu muốn thì đặt thành lệnh PO tự gọi trong release skill, không bao giờ tự động.

### [ARC-F04] Ba trường telemetry chủ lực chết trên data thật: duration=0, outcome=unknown, skills=[]
- Mức độ: High
- Loại: CORRECTNESS
- Bằng chứng (data dev thật, `.claude/telemetry/`):
  - `grep -o '"duration_s":...' sessions.jsonl | uniq -c` → `37 "duration_s": 0` + `4 "duration_s":0` = **41/41 bằng 0**, trái với thiết kế `emit_session_summary.py:8` — "Reads the head (real start ts → duration)".
  - `subagent-outcomes.jsonl` → `40 "outcome": "unknown"` = **40/40** (thiết kế thừa nhận fallback honest tại `track_subagent_outcome.py:13` — "Default `unknown` — NEVER fabricate").
  - `sessions.jsonl` skills field: **39/41 `"skills": []`**, 2 record còn lại là `ck-plan`/`ck:plan`; `invocations.jsonl` chỉ 7 record, **0 record nào thuộc 4 skill bundle**; `hook-telemetry.jsonl`: 235/235 `"exit": 0`, chỉ 96/235 có `ms`.
- Phân tích: đây là chính câu trả lời cho tiêu chí (c): sink chạy, fail-open chuẩn, nhưng nội dung không trả lời nổi "PO dùng lệnh gì nhiều, kẹt ở đâu, subagent có ổn không". Session lens sẽ báo duration 0, reliability lens 100% unknown, usage lens gần rỗng — PO bật telemetry xong đọc được rất ít (low-volume gate sẽ che bớt, nhưng che mãi).
- Đề xuất (đề xuất #4 — "Sửa 3 nguồn data chết trước khi thêm gì khác", cỡ S-M, rủi ro thấp; rank #3): (1) debug đường tính `duration_s` từ transcript head; (2) làm giàu classify outcome (đọc tail transcript theo protocol Status DONE/BLOCKED đã chuẩn hóa trong `orchestration-protocol.md`); (3) viết e2e fixture cho từng sink trên transcript thật. Không sửa thì mọi lens và mọi đề xuất insight phía sau đều vô nghĩa.

### [ARC-F05] Thiếu hẳn lớp event sản phẩm: không track artifact nào bị sửa, flag nào được dùng, câu hỏi interview nào bị bỏ qua
- Mức độ: High
- Loại: FEATURE-GAP
- Bằng chứng: schema thật của 3 sink: `invocations.jsonl:1` — `{"ts","skill","session","via"}` (không args/flag); `sessions.jsonl:1` — chỉ có `"files_modified":2` (đếm, không path); `track_script_execution.py:6` — chỉ match "`.claude/skills/<skill>/scripts/<file>.(py|sh)` — ignores plain git/ls/grep". Không sink nào ghi sự kiện mức `docs/product/` (artifact id/loại thao tác) hay mức interview (câu hỏi đặt/bỏ qua) — đã rà cả 5 hook tracked (`git ls-files` .claude/hooks).
- Phân tích: tiêu chí (c)+(d) đòi trả lời "PO kẹt ở đâu". Với schema hiện tại, kể cả data sạch, lens chỉ nói được "skill X gọi N lần, script Y chạy Z ms" — không bao giờ nói được "PRD-CARE bị sửa đi sửa lại 7 lần", "PO toàn bỏ qua câu hỏi competitor" — đúng loại insight một spec-tool cần.
- Đề xuất (đề xuất #5 — "Artifact-events sink", cỡ M, rủi ro privacy thấp: chỉ ghi path tương đối trong docs/product + op, không nội dung, vẫn local-only; rank #5): tái dùng matcher PostToolUse `Edit|Write|MultiEdit` đã đăng ký sẵn cho memory_gap (`register_telemetry_hooks.py:115`) để ghi `{ts, artifact_path, op, session}`; mở rộng `track_skill_invocation` ghi tóm tắt flag (`--validate`, `--learn`…) khi parse được; thêm 1 lens "artifact heat" kể bằng VI.

### [ARC-F06] Self-learning kit-level chưa tồn tại + vòng phản hồi về dev đứt hoàn toàn (telemetry local-only, không có export)
- Mức độ: High
- Loại: FEATURE-GAP
- Bằng chứng:
  - `--learn` chỉ ghi outcome SẢN PHẨM của PO: `record_outcome.py:3-5` — "the append-only home for measured outcomes (`OUT-<n>`)… the PO declares target+actual for a BRD goal metric"; phần behavioral chỉ là per-product: `behavioral_memory.py:12-14` — "`self-corrections.json` … a recurring slip + the operating principle it violated".
  - Kit tự nhận defer learning-loop: `BACKLOG.md:77` — "A9 quality-gate learning loop (P3, **deferred** — dirties report-only/non-deterministic boundary…)".
  - Telemetry không bao giờ rời máy PO: `telemetry_paths.py:32` — `d = … Path(project_dir()) / ".claude" / "telemetry"`; `.gitignore:170` — `/.claude/telemetry/`; grep export/notify (F03) → không có lệnh xuất usage nào.
- Phân tích: tiêu chí (e) hiện chỉ đạt mức "LLM tự nhắc mình trong một product" (self-corrections) + "PO tự khai outcome". Không có mạch nào: usage → cải thiện câu hỏi interview/template/nudge; và dev không bao giờ thấy PO kẹt ở đâu → kit chỉ tiến hóa bằng dogfood của dev.
- Đề xuất (đề xuất #6 — "Usage-summary ẩn danh PO chủ động xuất" + giữ self-learning report-only, cỡ M; rủi ro: privacy → PO đọc/duyệt file trước khi gửi, opt-in từng lần; boundary A9 → chỉ đề-xuất-không-tự-sửa; rank #8): (1) lệnh `telemetry --export-summary` render markdown thuần aggregate (đếm/skill, error-rate, version bundle — khả thi vì các lens đã trả dict aggregate, `formatters.py` có sẵn) để PO tự gửi dev; (2) slice self-learning an toàn: dùng pattern memory-harvester (read-only, `memory-harvester.md:2-4`) đọc self-corrections + repeat-offense findings → report "đề nghị chỉnh interview question/template" cho dev, không bao giờ tự sửa kit.

### [ARC-F07] Telemetry skill vô hình với PO: không có dòng route trong CLAUDE.md, không một nudge nào trỏ tới nó
- Mức độ: Medium
- Loại: UX-PO
- Bằng chứng: bảng routing always-on chỉ có 3 hàng (`CLAUDE.md:10-13`: product-spec / product-spec-critique / release); `grep -n telemetry CLAUDE.md` → 0 match; GUIDE-VI product-spec cũng 0 match "telemetry". Registrar không đăng ký SessionStart hay bất kỳ surfacing nào (`register_telemetry_hooks.py:106-117` chỉ PreToolUse/UserPromptExpansion/PostToolUse/Stop/SubagentStop). Trong khi đó skill nói VI rất chuẩn cho PO: `telemetry/SKILL.md:42-44` — "Run `analyze_telemetry.py --lens all` … **narrate in Vietnamese** (default)" và GUIDE-VI.md:3 viết đúng giọng PO.
- Phân tích: tiêu chí (d) "usage insight" có sản phẩm tốt nhưng zero discoverability: PO không gõ `/cleanmatic:telemetry` thì không bao giờ thấy; mà PO không biết nó tồn tại vì lớp routing luôn-trong-context không nhắc. Insight hoàn toàn pull-based.
- Đề xuất (đề xuất #7 — "Routing + nudge nhẹ", cỡ S, rủi ro nag → advisory + config-gate như critique-nudge; rank #6): thêm hàng telemetry vào bảng CLAUDE.md; thêm 1 dòng gợi ý trong output `--status` ("muốn xem mức dùng & sức khỏe: /cleanmatic:telemetry"); cân nhắc Stop-advisory theo đúng pattern `product_spec_critique_nudge.py` (advisory, never block — docstring dòng 2-8).

### [ARC-F08] Đường ghi nhận cách PO gọi skill (slash-command/UserPromptExpansion) chưa được chứng minh hoạt động — 0 bản ghi trên data thật
- Mức độ: Medium
- Loại: CORRECTNESS
- Bằng chứng: registrar đăng ký 2 đường: `register_telemetry_hooks.py:107-108` — PreToolUse:Skill + `{"event": "UserPromptExpansion", …}`; data thật: `grep -o '"via": …' invocations.jsonl | uniq -c` → `7 "via": "PreToolUse:Skill"`, **0 record via UserPromptExpansion** sau nhiều ngày dùng. Dedup chỉ chặn bản ghi THỨ HAI cùng invocation (`telemetry_paths.py:218-223`) nên nếu event này có fire một mình thì phải thấy record.
- Phân tích: PO non-technical chủ yếu gõ `/cleanmatic:product-spec …` (PO GUIDE dạy vậy). Nếu event UserPromptExpansion không tồn tại/không fire trong Claude Code thật thì toàn bộ usage lens mù đúng kênh chính của PO — khớp với `skills:[]` ở F04. Chưa đủ bằng chứng kết luận event không tồn tại (có thể dev không dùng slash trong cửa sổ này) → cần kiểm chứng chứ không cần tin.
- Đề xuất: 1 phiên e2e thật (gõ slash command trong repo test) + assert record xuất hiện; nếu event không tồn tại → chuyển capture sang nguồn khác (vd đọc transcript trong emit_session_summary đã có sẵn đường parse) và xóa registration chết.

### [ARC-F09] migrate_multidim_fields.py mồ côi khỏi mọi workflow — PO upgrade xong sẽ ăn warn-noise trên spec v1 mà không ai chỉ đường migration
- Mức độ: Medium
- Loại: CONSISTENCY
- Bằng chứng: `grep -rn migrate_multidim .claude/skills/product-spec/SKILL.md references/*.md` → 0 match (callers duy nhất: generate_templates.py + tests). Mục đích script: `migrate_multidim_fields.py:3-4` — "bring an existing v1 spec up to the v2 multidim schema", và :13 — "silence the PRD/Epic 'warn-if-missing' noise". Spec PO là v1-era: `grep -l 'risks:' …/Cleanmatic-ERP/docs/product/prds/*.md | wc -l` → **0/10**; `depends_on:` 2/10.
- Phân tích: sau khi nâng product-spec lên 2.3.1, lần `--validate` đầu của PO trên 10 PRD + 33 epic sẽ xổ hàng loạt cảnh báo thiếu trường mới; SKILL.md không route tới migration → LLM vận hành theo SKILL.md sẽ không biết chạy nó (vi phạm chính nguyên tắc "load SKILL.md, đừng vận hành từ trí nhớ"). Script đã làm rất đúng (dry-run default, không đụng approved) nhưng không ai gọi.
- Đề xuất: thêm 1 dòng route trong SKILL.md (mục validate hoặc update): "spec cũ thiếu trường v2 → đề nghị chạy migrate_multidim_fields (dry-run trước, hỏi PO trước --apply)"; bước upgrade.sh (F02) nên in nhắc này bằng VI.

### [ARC-F10] Bundle ship 5 rules viết cho môi trường dev (ck) — trỏ tới skill không ship cho PO
- Mức độ: Medium
- Loại: CONSISTENCY
- Bằng chứng: `pack.manifest.yaml:30-35` ship `primary-workflow.md`, `orchestration-protocol.md`…; nội dung: `primary-workflow.md:10` — "load `.claude/skills/cook/references/workflow-routing.md`", `:29` — "use `/ck:preview` … load `.claude/skills/preview/references/…`", `orchestration-protocol.md:42` — "use `/ck:team`". Bundle không chứa cook/preview/ck:team (manifest skills chỉ 4).
- Phân tích: trên máy PO các rule này là chỉ dẫn trỏ vào hư không; tệ hơn, chúng kéo Claude của PO về vocabulary dev ("plans/", "lint, typecheck, build") — ngược tiêu chí (a) "speak product language". PO repo v1.1.0 cũng đã dính 8 rules tương tự.
- Đề xuất: tách rules thành 2 lớp — bộ rule trung tính cho recipient (hoặc bỏ hẳn rules khỏi manifest, vì CLAUDE.md + SKILL.md đã đủ contract cho PO), giữ rules ck cho dev repo. Một dòng điều kiện trong build_manifest là đủ.

### [ARC-F11] "Memory" đang là 2 hệ rời nhau — telemetry memory-lens đo nhầm chỗ so với memory sản phẩm của PO
- Mức độ: Medium
- Loại: ARCHITECTURE
- Bằng chứng: lens memory đọc memory của ASSISTANT: `lens_memory_health.py:1-3` — "validates THIS repo's persistent memory dir (memory_dir() → ~/.claude/projects/<root>/memory/)" (cũng tại `telemetry/SKILL.md:59`). Memory SẢN PHẨM của PO nằm chỗ khác và đang dùng thật: `…/Cleanmatic-ERP/docs/product/.memory/` = `critique-lens-cache/ critique-findings-index.json critique-state.json last_critique.json` — KHÔNG có `last_validated.json`, không `preferences.yaml`, không po-style/self-corrections (ls đầu phiên). KIT cũng không có lens nào đọc `docs/product/.memory` (rà 8 lens scripts theo ls-files).
- Phân tích: tiêu chí (d) "memory liền mạch": câu PO cần là "bộ nhớ SẢN PHẨM của tôi có khỏe không" (chưa từng validate — đúng thật, PO không có marker; chưa có sở thích lưu; behavioral store rỗng) — không lens nào trả lời. Lens hiện tại lại audit memory dir của Claude Code, thứ PO không biết tồn tại.
- Đề xuất (đề xuất #8 — "Hợp nhất memory lens", cỡ S, rủi ro thấp, read-only; rank #7): thêm nguồn `docs/product/.memory` vào lens memory (tuổi `last_validated.json`, store nào rỗng/thiếu, kích thước cache) — narration VI: "6 ngày chưa validate", "chưa lưu giọng PO". Tái dùng reader có sẵn của product-spec (status/judgment_cache) đúng nguyên tắc one-home.

### [ARC-F12] Thông điệp cuối installer trỏ skill không còn tồn tại: `/cleanmatic:claude-pack`
- Mức độ: Low
- Loại: CLEANUP
- Bằng chứng: `install.sh.template:348` — `log "Done. Invoke skills from Claude Code, e.g. /cleanmatic:claude-pack"`; bundle HEAD không ship skill claude-pack (`pack.manifest.yaml:7-11`); templates.py chỉ thay token dạng `{{UPPERCASE}}` (`templates.py:3-4`) → chuỗi này ship nguyên văn.
- Phân tích: dòng đầu tiên PO đọc sau khi cài xong chỉ sang một skill không tồn tại — nhỏ nhưng đập thẳng vào tiêu chí (a).
- Đề xuất: thay bằng token `{{BUNDLE_EXAMPLE_SKILL}}` do pack điền từ manifest (skill đầu tiên), hoặc hardcode `/cleanmatic:product-spec`.

### [ARC-F13] Release skill (dev-facing) ship trong bundle cho PO non-technical
- Mức độ: Low
- Loại: YAGNI
- Bằng chứng: `pack.manifest.yaml:9` — `- release`; chính CLAUDE.md kit phân loại nó là "code/CLI vocabulary" (CLAUDE.md:15-16), và quy trình của nó (tag push, CI, tarball) không có vai trò gì trong vòng đời tài liệu sản phẩm của PO.
- Phân tích: tăng bề mặt skill-matching và context cho một người dùng không bao giờ pack bundle; vô hại nhưng ngược tiêu chí (a). (Ghi nhận: có thể là chủ đích để recipient re-share — không có bằng chứng văn bản nào nói vậy trong SKILL.md/README release.)
- Đề xuất: cân nhắc bỏ `release` khỏi manifest recipient-bundle (giữ trong repo dev); nếu giữ thì ghi rõ lý do vào manifest comment.

## GIỚI HẠN & KHÔNG TÌM THẤY
- Đã kiểm và SẠCH: `telemetry_paths.py` fail-open + rotation 8MB + dedup (đọc toàn file); registrar idempotent, reconcile legacy `.cjs` và đổi interpreter (`register_telemetry_hooks.py:84-98,160-162`); installer có traversal-guard (`install.sh.template:224-231`); telemetry data bị gitignore + không vào bundle (`.gitignore:170`, BACKLOG.md:55 "telemetry → gitignore + CI-assert tarball-exclusion"); GUIDE-VI cho cả 4 skill tồn tại và `--learn`/`--reflect` được dạy bằng VI (`product-spec/GUIDE-VI.md:532,888`); vòng `--reflect` đúng thiết kế read-only-rồi-hỏi-PO (`reflect_scan.py:5-13`, `memory-harvester.md:2-4`).
- KHÔNG tìm thấy bằng chứng: bất kỳ cơ chế version-check/notify nào; bất kỳ lệnh export usage nào; bất kỳ event nào ghi artifact/interview; bất kỳ tài liệu nào route tới migrate_multidim_fields.
- Không kiểm được (lý do): hành vi THẬT của installer khi chạy đè lên PO-repo (cấm ghi PO-repo; thao tác sandbox thuộc lens BUG) — phân tích F01/F02 là static-trace theo code; event `UserPromptExpansion` có tồn tại trong Claude Code hiện tại không (cần phiên live, F08); độ chính xác token-attribution của usage lens (cần transcript thật); nội dung `visuals/*.html` 2.5MB và toàn văn change-log.md/decisions.md của PO (chỉ grep theo luật file-lớn — không ảnh hưởng lens ARC).
- Ngoài scope, note 1 dòng: `.claude/agent-memory/` không được track (`git ls-files | grep -c agent-memory` → 0); `.claude/skills/spec-critique/` trong KIT là rác local untracked; `release-manifest.json` root untracked.

Status: DONE
Summary: Đã map 5 tiêu chí đích trên bằng chứng file:line từ KIT HEAD + PO-repo, ra 13 findings (2 Critical về upgrade path, 3 High về telemetry/self-learning) và 8 đề xuất kiến trúc gắn trực tiếp vào khoảng trống có bằng chứng.
Concerns: F01/F02 nên được kiểm chứng động trong sandbox (lens BUG) trước khi sửa; F08 cần 1 phiên e2e live để kết luận.