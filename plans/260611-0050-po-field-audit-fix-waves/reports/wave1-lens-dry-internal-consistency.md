## TÓM TẮT

Soát tĩnh 857 file git-tracked của KIT (product-spec v2.3.0, tag `product-spec-v2.3.0`). Nền tảng tốt: version 4 skill đồng bộ (verify_skill_versions exit 0), hooks json ↔ registrar ↔ manifest khớp, không có script chết, không broken-reference trong SKILL/GUIDE của cả 4 skill. Ba phát hiện đắt nhất:
1. **Installer templates ship cho recipient vẫn brand "claude-pack"** — install.sh/.ps1 hardcode tên cũ, hint invoke `/cleanmatic:claude-pack` (skill không tồn tại), INSTALL.md trỏ path troubleshooting đã chết — trong khi token `{{BUNDLE_NAME}}` đã có sẵn.
2. **Không có đường upgrade từ claude-pack v1.x** — installer chỉ ADD/OVERWRITE từng file, không dọn/cảnh báo skill+agent đã rename; PO thật (claude-pack 1.1.0) nếu upgrade sẽ có 2 skill critique + 2 packer + 6 agent cũ song song.
3. **28 file test tracked chưa từng chạy trong CI nào** (telemetry 20, hooks 4, _shared 4 — gồm cả context-footprint regression guard mà CHANGELOG 2.3.0 quảng cáo là "wired into pytest"), dù CONTRIBUTING.md bắt "all tests must pass before a PR is merged".
Ngoài ra: con số "−11.8%" trong CHANGELOG không tái lập được từ lịch sử release (thực tế −6.7%), và một lớp rác ck-local đã commit (13 agents, 2 env.example, 1 schema 0-ref).

## FINDINGS

### [DRY-F01] Installer templates ship còn brand "claude-pack" + link chết + hint skill không tồn tại
- Mức độ: High
- Loại: CORRECTNESS
- Bằng chứng:
  - `.claude/skills/release/assets/templates/install.sh.template:2` — "`# install.sh — recipient installer for claude-pack v{{VERSION}}`"; `:31` — "`log()  { echo "[claude-pack] $*"; }`"; `:348` — "`Invoke skills from Claude Code, e.g. /cleanmatic:claude-pack`"
  - `.claude/skills/release/assets/templates/install.ps1.template:1,34,319` — tương tự (`[claude-pack]`, `/cleanmatic:claude-pack`)
  - `.claude/skills/release/assets/templates/INSTALL.md.template:72` — trỏ "`.claude/skills/claude-pack/references/troubleshooting.md`" trong khi file tồn tại duy nhất ở `.claude/skills/release/references/troubleshooting.md` (ls-files dòng 411)
  - Token đã có sẵn: `pack/pipeline.py:63` `"BUNDLE_NAME": manifest["bundle_name"]`; INSTALL.md.template dùng `{{BUNDLE_NAME}}` 7 lần, còn install.sh.template chỉ có duy nhất `{{VERSION}}` (grep -o `{{...}}`); templates được render + nhúng vào tarball tại `pack/selection.py:150-151`
- Phân tích: mọi bundle v2.x build từ HEAD giao cho recipient một installer tự xưng "claude-pack" (tên 3 version trước), hướng dẫn gõ một skill không tồn tại và một đường dẫn troubleshooting 404 — đúng mặt tiền non-technical PO nhìn thấy đầu tiên sau khi cài. Skill `cleanmatic:release` đã rename từ ≤0.3.0 (release/SKILL.md:21) nhưng 3 template bị bỏ quên.
- Đề xuất: thay chuỗi hardcode bằng `{{BUNDLE_NAME}}` ở cả install.sh/.ps1 template; sửa INSTALL.md.template:72 thành `.claude/skills/release/references/troubleshooting.md`; sửa hint cuối thành `/cleanmatic:product-spec` (skill PO-facing) — kèm 1 test template khẳng định không còn literal "claude-pack" ngoài đoạn back-compat chủ đích.

### [DRY-F02] Không có migration/cleanup path cho người đang cài claude-pack 1.x (PO thật đang ở đó)
- Mức độ: High
- Loại: FEATURE-GAP | UX-PO
- Bằng chứng:
  - install.sh.template chỉ có logic ADD/OVERWRITE từng file: `:13` "`FORCE_OVERWRITE=1 ... overwrite existing (with timestamped backup)`", `:258-282` chỉ `cp -f` + backup; không có bước nào remove/cảnh báo dir cũ
  - `grep -in 'upgrade\|rename\|claude-pack\|spec-critique' .claude/skills/release/references/troubleshooting.md` → 0 match (lệnh chạy, output rỗng)
  - Hiện trạng PO: `ls .claude-po-original/skills` → `claude-pack/ product-spec/ spec-critique/`; agents → `spec-critique-consolidate.md`, `spec-critique-craft.md`… (6 file prefix cũ)
  - Bundle HEAD ship skill `product-spec-critique` + `release` + agents `product-critic.md`… (pack.manifest.yaml dòng 8-19)
- Phân tích: vì skill và agent đều đã đổi TÊN THƯ MỤC/TÊN FILE, upgrade bằng installer mới sẽ để nguyên `spec-critique/`, `claude-pack/`, 6 agent `spec-critique-*` bên cạnh bản mới → Claude Code thấy 2 skill critique gần trùng mô tả, 2 packer, agents đôi — non-technical PO không thể tự chẩn đoán. Đây là kịch bản thật của repo Cleanmatic-ERP.
- Đề xuất: thêm vào installer một bước "renamed-predecessor sweep" (danh sách tên cũ → mới, hỏi trước khi xoá, mặc định cảnh báo) + một mục "Upgrading from claude-pack ≤1.x" trong troubleshooting.md/INSTALL.md.template.

### [DRY-F03] 28 file test tracked không được bất kỳ workflow CI nào chạy; path filter CI hổng
- Mức độ: High
- Loại: CONSISTENCY
- Bằng chứng:
  - `grep -rln 'telemetry' .github/workflows/` → exit 1; `grep -rln 'hooks/' .github/workflows/` → exit 1 (0/6 workflow nhắc tới)
  - File không chạy CI: 20 file `.claude/skills/telemetry/scripts/tests/test_*.py` (đếm từ ls-files), 4 file `.claude/hooks/__tests__/test_*.py` (ls-files dòng 22-25), 4 file `.claude/skills/_shared/lib/__tests__/` (dòng 60-63) — gồm `test_context_footprint_regression_guard.py:1` "Regression guard — wires context_footprint into the pytest check surface"
  - CHANGELOG.md (root, mục 2.3.0 Added): context-footprint "wired into pytest as a regression guard" — nhưng `product-spec/pyproject.toml:2` `testpaths = ["scripts/tests"]` và product-spec-ci.yml:37-42 chỉ chạy `scripts/tests` + `run_evals.py`
  - CONTRIBUTING.md:69 ghi lệnh chạy tay "`pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q`", :75 "All tests must pass before a PR is merged" — không CI nào enforce
  - Path filter hổng kèm theo: product-spec-ci.yml:5-7 không trigger khi `_shared/**` đổi dù bước 42 chạy `_shared/lib/run_evals.py`; cross-skill-bug-class.yml:10-14 không có `.claude/skills/telemetry/**`
- Phân tích: lớp test mới nhất (telemetry 2.2.0, hook hardening + footprint gate 2.3.0) là lớp KHÔNG có lưới CI — chính là chỗ vừa thay đổi nhiều nhất. Claim "regression guard" trong changelog chỉ đúng khi dev nhớ chạy tay đúng rootdir.
- Đề xuất: thêm 1 workflow `telemetry-and-hooks-ci.yml` (hoặc nối vào cross-skill) chạy đúng lệnh CONTRIBUTING.md:69; bổ sung `_shared/**` vào path filter của product-spec-ci/product-spec-critique-ci/release-ci.

### [DRY-F04] Claim "SKILL.md −11.8% (6090 → 5371)" không tái lập được từ lịch sử release
- Mức độ: Medium
- Loại: CONSISTENCY
- Bằng chứng:
  - `product-spec/CHANGELOG.md` mục [2.3.1]: "SKILL.md token proxy **6090 → 5371 (−11.8%)**"; root CHANGELOG.md [2.3.0] lặp lại "product-spec SKILL.md −11.8%"
  - `context_footprint.py:40-42`: `token_proxy = ceil(chars/4)`
  - Đo thật (chạy token_proxy trên file ở 2 đầu commit): `e52e077^` (= trạng thái release 2.2.2) → **5758**, HEAD → **5371** = **−6.7%**; kích thước file 23260 bytes ở cả db5332b/045de8e/3df683f → trần token ceil(23260/4)=5815 < 6090 ⇒ con số 6090 **không tồn tại ở bất kỳ commit nào** (chỉ có thể là trạng thái trung gian sau khi thêm flags --learn, trước compaction, trong cùng commit squash e52e077)
  - Đối chứng: claim của critique "3820 → 3677 (−3.7%)" đo lại khớp CHÍNH XÁC (`critique SKILL.md tokens: 3820 -> 3677 delta -3.7%`)
- Phân tích: bundle changelog là tài liệu release công khai; một skill ghi số tái lập được, skill kia ghi số chỉ đúng với working-state không bao giờ commit — người đọc diff 2.2.2→2.3.0 sẽ thấy −6.7% và mất niềm tin vào các con số còn lại.
- Đề xuất: sửa chú thích trong 2 CHANGELOG thành "−6.7% so với 2.2.2 (−11.8% so với bản nháp đã thêm learn-loop flags)" hoặc chỉ giữ số so-với-release; quy ước về sau: số trong changelog phải tái lập từ 2 tag.

### [DRY-F05] Rác ck-local đã commit vào repo nguồn ship: 13 agents ngoài bundle, 2 env.example, schema 0-ref
- Mức độ: Medium
- Loại: CLEANUP | YAGNI
- Bằng chứng:
  - 20 agents tracked (ls-files dòng 2-21) nhưng pack.manifest.yaml chỉ ship 7 (dòng 12-19); 13 file còn lại (brainstormer, code-reviewer, code-simplifier, debugger, docs-manager, fullstack-developer, git-manager, journal-writer, planner, project-manager, researcher, tester, ui-ux-designer) thêm bởi commit `a967688 "feat(skills): harden product-spec + claude-pack, add packaging assets and CK files"`
  - `.claude/schemas/ck-config.schema.json`: grep tên file trên toàn bộ tracked set → **0 tham chiếu**; `skill-schema.json` chỉ được `.claude/scripts/validate-skill-frontmatter.py` (cũng là ck tooling) dùng
  - `.claude/.env.example` + `.claude/skills/.env.example` (ls-files dòng 1, 59): nội dung ck framework — "ClaudeKit API Key (for VidCap, ReviewWeb services)", STITCH/MINIMAX/SePay keys của các skill không có trong repo này
  - Nuance: `.claude/scripts/` + `schemas/` được release skill chủ đích coi là "CK-framework internals; opt-in" (`release/SKILL.md:52`, `pack/args.py:54-55`) — nhưng 13 agents và 2 env.example thì không có cơ chế include nào dùng tới
- Phân tích: repo tự nhận là "bộ source ship được"; 13 agent ck + env mẫu chứa hướng dẫn lấy API key của hệ skill khác làm nhiễu scope review, phình tracked set, và dễ bị packer kéo nhầm về sau (manifest agents chọn theo tên — an toàn hiện tại, nhưng người sửa manifest nhìn thư mục 20 file).
- Đề xuất: quyết định một lần (ghi DEC): hoặc untrack 13 agents + 2 env.example + ck-config.schema.json (chuyển sang settings local), hoặc ghi rõ trong README "các file CK-dev này tracked có chủ đích, không ship".

### [DRY-F06] Dogfood `docs/product/` commit cả state phiên + cache dễ vỡ
- Mức độ: Medium
- Loại: CLEANUP | CONSISTENCY
- Bằng chứng: tracked (ls-files dòng 525-531, 546): `docs/product/.session.md`, `.memory/last_validated.json`, `.memory/last_critique.json`, `.memory/critique-state.json`, `.memory/critique-lens-cache/7887b727191e3ef3.json`, `docs/product/visuals/.snapshots/20260606T035806Z-95c4b19b.json` — thêm bởi commit `58e2d05 "docs(product-spec): scaffold So Quy spec + critique report"`. Đối chiếu README.md:282: dữ liệu runtime của kit được tuyên bố "local gitignored".
- Phân tích: spec So Quy làm dogfood là hợp lý, nhưng `.session.md` + cache + snapshot là sản phẩm phụ MỖI LẦN chạy — bất kỳ ai dogfood lại trên KIT sẽ làm bẩn working tree / sinh diff vô nghĩa trong PR; còn mâu thuẫn với chính tuyên bố "session/telemetry state là local".
- Đề xuất: giữ artifact prose (vision/brd/prd/epic/story/critique report), untrack + gitignore `.session.md`, `.memory/*` cache và `visuals/.snapshots/` của thư mục dogfood (test dùng fixtures riêng dưới `scripts/tests/fixtures/`, đã xác nhận không đọc `docs/product/` của repo).

### [DRY-F07] GUIDE-EN/GUIDE-VI lag SKILL.md: thiếu hẳn `--voice` và `--compact-mode` (product-spec)
- Mức độ: Medium
- Loại: UX-PO | CONSISTENCY
- Bằng chứng: diff tập flag bằng regex trên 3 file → "SKILL not in GUIDE-EN: ['--compact-mode', '--do', '--dont', '--flag', '--recurring-asks', '--register', '--vocabulary', '--voice']" (GUIDE-EN 967 dòng, GUIDE-VI 959 dòng, hai bản đồng bộ nhau — cùng thiếu). `product-spec/SKILL.md:63` định nghĩa `--voice` ("Record the PO's voice into `.memory/po-style.yaml` … `--register`/`--vocabulary`/`--recurring-asks`/`--do`/`--dont`"); `:61` định nghĩa `--compact-mode <m>`. Critique GUIDE cũng thiếu các alias `--gentle`/`--savage`… (critique SKILL.md:62).
- Phân tích: GUIDE là tài liệu PO (đối tượng non-technical) — một tính năng PO-facing nguyên khối (`--voice`, ghi sở thích giọng văn) không xuất hiện ở cả EN lẫn VI nghĩa là PO không bao giờ biết nó tồn tại; trong khi `--learn` (cùng đợt) thì có. Drift kiểu này sẽ rộng dần mỗi release nếu không có guard.
- Đề xuất: bổ sung mục `--voice` + `--compact-mode` vào GUIDE-EN/VI; cân nhắc một test nhẹ kiểu flag-inventory (mọi flag trong bảng SKILL.md phải xuất hiện trong GUIDE hoặc nằm trong allowlist "internal").

### [DRY-F08] render_html.py 805 exec-LOC (≈4× chuẩn 200-LOC kit tự áp qua PS-2)
- Mức độ: Low
- Loại: ARCHITECTURE | CONSISTENCY
- Bằng chứng: `docs/audit-trail/REVIEW.md:64-67` — PS-2 split `record_outcome.py` vì "254 exec … over the 200-LOC guideline — measured by EXECUTABLE lines … a real overage". Đo cùng họ thước (grep -cvE '^\s*(#|$)'; thước PS-2 strict hơn ~10-15%): `render_html.py` **805**/1098, `spec_graph.py` 491/690, `visualize.py` 335/500, `check_consistency.py` 320/400.
- Phân tích: chuẩn đã được viện dẫn để split file 254 dòng nhưng bỏ qua file 805 dòng cùng skill — không nhất quán. Có thể chủ đích (render_html phần lớn là template HTML/JS nhúng), nhưng nếu vậy nên ghi ngoại lệ thay vì im lặng.
- Đề xuất: hoặc tách phần template tĩnh của render_html.py ra asset/module riêng (đã có sẵn họ render_common/render_board/render_explorer), hoặc ghi 1 dòng ngoại lệ có lý do vào REVIEW.md/STANDARDIZE.md để khỏi bị audit lại.

### [DRY-F09] telemetry-readback.md chưa biết tới crash-audit sink + config gate (đồ mới 2.3.0)
- Mức độ: Low
- Loại: CONSISTENCY
- Bằng chứng: `docs/audit-trail/telemetry-readback.md` (75 dòng) liệt kê 4 sink JSONL (dòng 9-12) nhưng `grep -n 'crash\|hook-audit\|audit'` → 0 match; trong khi `hook_runtime.py:18` "`log_hook_error(name, exc) crash audit → .logs/hook-crashes.log`" và `:45` `_LOG_NAME = "hook-crashes.log"` (thêm ở 2.3.0), kèm per-hook gate `product-spec-hooks.json`. Phụ: README.md:26 gán "memory-gap hook" vào cụm `product-spec-critique` trong khi `memory_gap_hook.py:2` tự nhận "Stop hook for the **product-spec** memory layer".
- Phân tích: doc readback là nơi dev/PO tra "hook có khoẻ không" — thiếu đúng sink chẩn đoán crash mới nhất nên khi hook chết âm thầm sẽ không ai biết tra ở đâu.
- Đề xuất: thêm 1 hàng cho `.logs/hook-crashes.log` + 2 dòng về `product-spec-hooks.json`/`CK_HOOK_AUDIT_DISABLED` vào telemetry-readback.md; sửa câu attribution trong README.md:26.

### [DRY-F10] Fixture test còn dùng id "claude-pack" làm dữ liệu mẫu
- Mức độ: Low
- Loại: CLEANUP
- Bằng chứng: `.claude/hooks/__tests__/test_telemetry_hooks.py:133` `"tool_input": {"skill": "claude-pack"}`, `:194` `"command": "python3 .claude/skills/claude-pack/scripts/foo.py"`; `.claude/skills/telemetry/scripts/tests/test_telemetry_paths.py:56,62` (`"skill": "claude-pack"` + assert).
- Phân tích: vô hại về hành vi (id tổng hợp), nhưng là tàn dư rename cuối cùng ngoài các đoạn lịch sử/back-compat chủ đích — khi đã quét sạch F01 thì nên sạch luôn để grep "claude-pack" trên source chỉ còn ra changelog/audit-trail.
- Đề xuất: đổi id mẫu sang tên trung tính (vd "demo-skill") trong 2 file test.

## GIỚI HẠN & KHÔNG TÌM THẤY

**Đã kiểm và SẠCH (không finding):**
- Version sync: SKILL.md 2.3.1/1.2.1/1.1.1/1.0.1 = CHANGELOG per-skill top = ok; `verify_skill_versions.py` exit 0; pack.manifest 2.3.0 = root CHANGELOG top; claim "product-spec 2.3.1" trong CHANGELOG 2.3.0 khớp file.
- Hooks: 8 .py + product-spec-hooks.json (7 key) ↔ `register_telemetry_hooks.py:63-97` (5 telemetry + 2 enforcement) ↔ manifest hooks (9 entry) khớp nhau; claim "auto-registered by installer" xác nhận tại install.sh.template:324-329; không hook khai-mà-thiếu-file hay file-mà-không-đăng-ký; thư mục `workflow-artifact-gate` KHÔNG tracked.
- Broken refs: 0 đường dẫn references/assets/scripts chết trong SKILL/README/GUIDE của cả 4 skill (script quét tự viết); chỉ note nhỏ: `guardrails-and-boundaries.md` chỉ reachable gián tiếp qua `interview-frameworks.md:47`.
- DRY code: check_consistency_*/behavioral_memory_* là submodule import đúng "one home" (check_consistency.py:36-53, behavioral_memory.py:41); render_* không trùng đáng gộp (chỉ 2 helper 3 dòng identical giữa render_ascii/render_ascii_board; build_payload/write của board vs explorer KHÁC nhau); không script nào 0-reference (kiểm theo stem) — không có dead script.
- CI release: `python -m pack` trong release.yml resolve qua `release.pth` do install.sh:69-71 ghi vào venv — không phải bug; release-integration `../.venv` resolve đúng.
- README claims: 4 skills / 7 critique sub-agents / 8 lenses (8 file lens_*.py, ids khớp SKILL.md telemetry) / 5 sink hooks — đều khớp code.
- e2e/dating-app: được `test_e2e_freshness_fixture_guard.py:33` dùng làm fixture — không phải rác.
- plans/: sample 5 plan.md gần nhất (260603-1817, 260607-1500, 260609-0847, 260609-1048, 260609-1110) đều `completed/complete/done` — không có plan "đang mở nhưng đã ship" (vocab status không đồng nhất, mức trivial); REVIEW.md không còn item `[ ]` mở.
- Rename residue trong agents/, CLAUDE.md, README.md root: 0 match "claude-pack"/"spec-critique" trần; các match còn lại nằm ở CHANGELOG lịch sử, audit-trail (PACK prefix back-compat chủ đích), journal — đúng phân loại loại trừ.

**Không kiểm được + lý do:** trạng thái run thật của GitHub Actions (không gọi mạng, chỉ soát tĩnh YAML); claim "best-of-3 sub-agent judge 18/18" (non-deterministic, không tái lập offline); nội dung sâu visuals HTML lớn và change-log.md ~89K của PO (chỉ grep theo luật file lớn); chất lượng prose từng reference (ngoài scope lens tĩnh). Rác untracked (settings.json, skills/spec-critique leftover, release-manifest.json root) — ngoài scope, note 1 dòng theo dặn của chủ repo.

Status: DONE
Summary: Soát tĩnh DRY/correctness/consistency/cleanup trên 857 file tracked của KIT; 10 findings (3 High: installer còn brand claude-pack, thiếu upgrade-path từ 1.x, 28 test file ngoài CI), kèm danh mục đã-kiểm-sạch.