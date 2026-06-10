## PHÁN QUYẾT

### [DRY-F01] → CONFIRMED
- Kiểm chứng: mở `install.sh.template` — dòng 2 `# install.sh — recipient installer for claude-pack v{{VERSION}}`, dòng 31 `log()  { echo "[claude-pack] $*"; }`, dòng 348 `Invoke skills from Claude Code, e.g. /cleanmatic:claude-pack`; `install.ps1.template:1,34,319` y hệt. `INSTALL.md.template:72` trỏ `.claude/skills/claude-pack/references/troubleshooting.md` trong khi ls-files chỉ có `.claude/skills/release/references/troubleshooting.md` (dòng 411). Token: `grep -o '{{...}}'` trên install.sh.template → chỉ `1 {{VERSION}}`; INSTALL.md.template có 7 `{{BUNDLE_NAME}}`; `pack/pipeline.py:63` cấp `"BUNDLE_NAME"`; `pack/selection.py:149-152` render cả 3 template vào tarball. Skill rename ghi tại `release/SKILL.md:21` ("Renamed from `cleanmatic:claude-pack` (≤ 0.3.0)"). Bằng chứng đúng từng dòng, severity High xứng đáng (mặt tiền recipient).

### [DRY-F02] → CONFIRMED
- Kiểm chứng: `install.sh.template:13` đúng nguyên văn `FORCE_OVERWRITE=1 ... overwrite existing (with timestamped backup)`; khối 255-285 chỉ `cp`/`cp -f` + backup, grep `rm |remove|sweep|prune` toàn template chỉ ra 2 dòng về `register_telemetry_hooks.py --remove` (gỡ hook, không dọn file). Chạy lại `grep -in 'upgrade\|rename\|claude-pack\|spec-critique' release/references/troubleshooting.md` → exit 1, 0 match. Sandbox: `ls .claude-po-original/skills` → `claude-pack/ product-spec/ spec-critique/`; agents → 6 file `spec-critique-*` + `memory-harvester.md`. `pack.manifest.yaml:7-19` ship `product-spec-critique`, `release`, 7 agent tên mới. Kịch bản double-skill khi upgrade là tất yếu; High đúng.

### [DRY-F03] → ADJUSTED (sửa con số: 26 file, không phải 28; telemetry 18, không phải 20)
- Kiểm chứng: `grep -rln 'telemetry' .github/workflows/` → exit 1; `grep -rln 'hooks/' .github/workflows/` → exit 1 (6 workflow). Đếm lại từ ls-files: `telemetry/scripts/tests/test_*.py` = **18** (không có conftest tracked), hooks `__tests__` = 4, `_shared/lib/__tests__` = 4 → tổng **26**. `pyproject.toml:2` `testpaths = ["scripts/tests"]`; `product-spec-ci.yml` chỉ chạy `scripts/tests` + `run_evals.py --skill product-spec` (dòng 38-42) và path filter (dòng 5-7) không có `_shared/**`; `cross-skill-bug-class.yml:10-14` không có telemetry (note thêm: telemetry hiện cũng chưa có test `bug_class` nào — grep exit 1 — nên lỗ hổng filter này mới ở mức phòng xa). `CONTRIBUTING.md:69` lệnh pytest 3 đường dẫn + `:75` "All tests must pass before a PR is merged" đúng nguyên văn. Bản chất finding đứng vững, severity High giữ nguyên — thậm chí còn nhẹ tay: tôi chạy đúng lệnh CONTRIBUTING.md:69 và suite này **đang FAIL ở HEAD** (xem DRY-M1).

### [DRY-F04] → CONFIRMED
- Kiểm chứng: `.claude/skills/product-spec/CHANGELOG.md:18` "**6090 → 5371 (−11.8%)**" và root `CHANGELOG.md:30` "−11.8%" đúng nguyên văn; `context_footprint.py:40-42` `ceil(chars/4)`. Đo lại: `e52e077^` (=2.2.2) chars 23030 → **5758**; HEAD → **5371** = **−6.7%**. Quét token_proxy trên **toàn bộ rev-list** của SKILL.md: max từng commit = 5758 ⇒ 6090 chưa bao giờ tồn tại trong lịch sử git — mạnh hơn cả lập luận trần-byte của lens. Đối chứng critique 3820 → 3677 (−3.7%) khớp chính xác. Medium hợp lý.

### [DRY-F05] → CONFIRMED
- Kiểm chứng: ls-files `.claude/agents/` = 20 file, `pack.manifest.yaml:12-19` ship đúng 7; 13 tên còn lại khớp danh sách finding; `git log --diff-filter=A` xác nhận `a967688` thêm `brainstormer.md` + `.claude/.env.example`. `git grep 'ck-config\.schema'` → duy nhất self-reference `$id` trong chính file đó (0 ref ngoài); `skill-schema.json` chỉ được `validate-skill-frontmatter.py` dùng. Env.example chứa "ClaudeKit API Key (for VidCap, ReviewWeb services)" (dòng 20) + 9-11 match STITCH/MINIMAX/SePay. Nuance opt-in scripts/schemas khớp `release/SKILL.md:52` + `args.py:54-55`. Medium CLEANUP/YAGNI chuẩn.

### [DRY-F06] → ADJUSTED (bỏ vế "mâu thuẫn với README:282"; giữ vế diff-noise)
- Kiểm chứng: ls-files xác nhận tracked `docs/product/.session.md`, 6 file `.memory/*` (kể cả `critique-lens-cache/7887b727191e3ef3.json`), `visuals/.snapshots/20260606T035806Z-95c4b19b.json`, thêm bởi `58e2d05`. NHƯNG `README.md:282` nguyên văn nói về **telemetry**: "read/write only local gitignored `.claude/telemetry/*.jsonl` sinks" — và `.claude/telemetry/` đúng là gitignored (`check-ignore` exit 0, `.gitignore:170`). README **không có** chữ nào tuyên bố `.session.md`/`.memory` là "local gitignored" (grep `\.session|\.memory` README → 0 match). Vế mâu thuẫn là trích sai đối tượng. Vế còn lại (state per-run commit vào repo → mỗi lần dogfood lại sinh diff vô nghĩa) tự đứng được; giữ Medium CLEANUP.

### [DRY-F07] → CONFIRMED
- Kiểm chứng: chạy lại regex diff flag trên 3 file → ra đúng tập `['--compact-mode', '--do', '--dont', '--flag', '--recurring-asks', '--register', '--vocabulary', '--voice']` thiếu ở CẢ GUIDE-EN (967 dòng) lẫn GUIDE-VI (959 dòng); `grep 'voice\|compact-mode' GUIDE-EN.md` → 0 match. `SKILL.md:63` định nghĩa `--voice` (`--register`/`--vocabulary`/`--recurring-asks`/`--do`/`--dont`), `:61` `--compact-mode`. Critique: `SKILL.md:62` có alias `--warm/--gentle/--blunt/--savage...`, grep `gentle|savage` trên 2 GUIDE critique → 0. Medium UX-PO đúng.

### [DRY-F08] → CONFIRMED
- Kiểm chứng: `docs/audit-trail/REVIEW.md:63-67` đúng nguyên văn PS-2 ("254 exec … 200-LOC guideline — measured by EXECUTABLE lines … a real overage"). Đo cùng thước `grep -cvE '^\s*(#|$)'`: render_html.py **805**/1098, spec_graph.py 491/690, visualize.py 335/500, check_consistency.py 320/400 — khớp từng số. Low + ghi nhận caveat template là đánh giá công bằng.

### [DRY-F09] → CONFIRMED
- Kiểm chứng: `telemetry-readback.md` 75 dòng, bảng sink 4 hàng (invocations/hook-telemetry/sessions/subagent-outcomes); `grep -in 'crash\|hook-audit\|audit'` → exit 1. `hook_runtime.py:18` "`log_hook_error(name, exc) crash audit → .logs/hook-crashes.log`", `:45` `_LOG_NAME = "hook-crashes.log"`. `README.md:26` gộp "memory-gap hook" vào cụm `product-spec-critique`, trong khi `memory_gap_hook.py:2` "opt-in Tier-1 Stop hook for the **product-spec** memory layer". Low đúng.

### [DRY-F10] → CONFIRMED
- Kiểm chứng: `test_telemetry_hooks.py:133` `"tool_input": {"skill": "claude-pack"}`, `:194` `"command": "python3 .claude/skills/claude-pack/scripts/foo.py"`; `test_telemetry_paths.py:56` append `"skill": "claude-pack"` + `:62` assert `lines[1]["skill"] == "claude-pack"`. Low CLEANUP, vô hại hành vi — đánh giá đúng tầm.

## BỎ SÓT (≤3, đủ bằng chứng, đúng format finding với prefix DRY-M<n>)

### [DRY-M1] Suite test mà CONTRIBUTING bắt buộc đang FAIL ở HEAD: telemetry workflow-lens đọc 2 routing doc đã bị xoá ở 2.3.0
- Mức độ: High
- Loại: CORRECTNESS | CONSISTENCY
- Bằng chứng:
  - Chạy đúng lệnh `CONTRIBUTING.md:69`: `.claude/skills/.venv/bin/python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q` → "`FAILED ...test_lens_workflow_chains.py::test_declared_chains_parsed_from_routing_docs — 1 failed, 193 passed`" (tái lập với bytecode cache sạch `PYTHONPYCACHEPREFIX`, vẫn fail: `0 = len([])`).
  - Nguyên nhân: `lens_workflow_chains.py:24-25` hardcode `root / "skill-workflow-routing.md"`, `root / "skill-domain-routing.md"` trong `.claude/rules/` — nhưng commit `e52e077` (release 2.3.0, "rules slimmed") đã **xoá** cả 2 file (`git show e52e077 --stat`: `skill-domain-routing.md | 154 ----`, `skill-workflow-routing.md | 68 ----`); test `test_lens_workflow_chains.py:42-46` assert `len(d["declared_chains"]) >= 1` với comment "The real .claude/rules routing docs declare multi-step chains."
  - `CONTRIBUTING.md:75`: "All tests must pass before a PR is merged."
- Phân tích: đây là hệ quả sống của F03 mà lens chỉ suy ra trên giấy — không có CI nên drift "rules slim ↔ telemetry lens" đã lọt vào release 2.3.0: test FAIL thật ở HEAD và tính năng declared-vs-actual của `--lens workflow` (telemetry SKILL.md:57 quảng cáo "actual skill chains vs routing docs") chạy runtime cũng vĩnh viễn `declared_chains=[]` ở cả KIT lẫn bundle (2 file không tracked, không ship). Lens kết luận "không có script chết" sau khi soát tĩnh nhưng không chạy chính lệnh test mình trích dẫn.
- Đề xuất: sửa `_routing_docs()` trỏ vào nguồn còn tồn tại (vd parse chain từ `.claude/rules/primary-workflow.md` hoặc loại bỏ declared-chains + cập nhật test), và nối suite này vào CI như F03 đề xuất — fail này chính là exhibit A.

### [DRY-M2] 5 rule được SHIP trong bundle tham chiếu skill ck-local không tracked/không ship (`cook`, `preview`, `/ck:team`)
- Mức độ: Medium
- Loại: CONSISTENCY | UX-PO
- Bằng chứng:
  - `pack.manifest.yaml:30-35` ship 5 rules: `primary-workflow.md`, `development-rules.md`, `orchestration-protocol.md`, `documentation-management.md`, `review-audit-self-decision.md`.
  - `primary-workflow.md:10` "load `.claude/skills/cook/references/workflow-routing.md`"; `:29` "use `/ck:preview` … load `.claude/skills/preview/references/visual-explanation-routing.md`"; `development-rules.md:27` "`/ck:preview`"; `orchestration-protocol.md:42` "use `/ck:team`".
  - `git -C /home/hieubt/Documents/product-spec ls-files | grep -c 'skills/cook\|skills/preview\|skills/team'` → **0** (các dir này tồn tại local nhưng untracked ck — chỉ "chạy được" trên máy dev).
  - Hiện vật PO thật: `grep '/ck:' /home/hieubt/Documents/Cleanmatic-ERP/.claude/rules/*.md` → 101 match trong 5 file — recipient đã và đang nhận rules trỏ vào skill không có.
- Phân tích: lens tuyên bố "Broken refs: 0 … trong SKILL/README/GUIDE của cả 4 skill" nhưng bỏ quên đúng lớp rules tracked-và-ship — nơi Claude bên máy PO bị chỉ thị load file/skill không tồn tại (fail-soft nhưng gây lệnh chết + nhiễu cho non-technical PO). Cùng họ với F01 (drift dev-local vs ship).
- Đề xuất: sửa 3 dòng trên thành điều kiện "nếu skill tồn tại" hoặc bỏ hẳn tham chiếu ck-local khỏi 5 rule ship; thêm vào quét broken-ref của release một bước check path `.claude/skills/...` được nhắc trong rules ship phải nằm trong bundle.

### [DRY-M3] CLAUDE.md (lớp routing always-on) tự nhận "three PO-facing skills" — bỏ rơi telemetry dù bundle ship 4 skill
- Mức độ: Medium
- Loại: CONSISTENCY | UX-PO
- Bằng chứng: `CLAUDE.md:4` "**always-on safety + routing layer** for **three** PO-facing skills"; bảng routing `CLAUDE.md:8-13` chỉ có 3 hàng (product-spec / product-spec-critique / release); `grep -n 'telemetry' CLAUDE.md` → 0 match. Trong khi `README.md:24` "**4 skills** … The user-invocable `/cleanmatic:*` commands", telemetry SKILL.md là skill PO-facing ("plain-Vietnamese read … for the non-technical PO", SKILL.md:74), và bản CLAUDE.md trước khi slim CÓ nhắc telemetry (`git show e52e077^:CLAUDE.md | grep -i telemetry` → match, exit 0).
- Phân tích: cùng đợt slim 2.3.0 gây M1 — telemetry rơi khỏi bảng routing always-on; PO hỏi "skill của tôi được dùng thế nào?" không được CLAUDE.md (tầng luôn-trong-context, tự nhận là routing layer) dẫn tới `telemetry/SKILL.md`, phải trông chờ skill-catalog description. Lens đã soát kỹ README claims (4 skills/7 agents/8 lenses) nhưng không đối chiếu chính CLAUDE.md root — file routing quan trọng nhất.
- Đề xuất: thêm hàng thứ 4 vào bảng routing CLAUDE.md (usage/health/script-error → `telemetry/SKILL.md`) và sửa "three" → "four".

## TÓM TẮT CHẤT LƯỢNG LENS

Độ tin cậy cao: 8/10 CONFIRMED, 2/10 ADJUSTED (F03 đếm sai 28→26, telemetry 20→18; F06 trích README:282 sai đối tượng — dòng đó nói về telemetry sinks, không phải session state), 0 REFUTED; mọi path:line tôi mở lại đều đúng nguyên văn, kể cả các con số đo (token proxy, exec-LOC) tái lập chính xác. Thiên lệch chính: lens trung thành với "soát tĩnh" đến mức không chạy chính lệnh test mà nó trích từ CONTRIBUTING.md:69 — bỏ lỡ test đang FAIL thật ở HEAD (DRY-M1), bằng chứng sống mạnh nhất cho chính finding F03 của nó. Phạm vi quét broken-ref dừng ở SKILL/README/GUIDE, bỏ sót lớp rules ship + CLAUDE.md root (DRY-M2, M3). Mục "đã kiểm sạch" chi tiết và phần lớn kiểm chứng lại đúng — đây là một report đáng tin sau khi chỉnh 2 chỗ trên.
