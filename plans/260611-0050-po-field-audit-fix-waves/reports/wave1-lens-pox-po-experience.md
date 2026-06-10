Đã đủ bằng chứng. Tổng hợp báo cáo cuối.

## TÓM TẮT
PO Cleanmatic là **power user thành công**: 8 ngày (06-02→06-10) dựng 144 artifact (2 nền + 10 PRD + 30 epic + 102 story), 44 DEC, 63 entry change-log, 16 báo cáo critique; vòng critique→DEC→re-approve **thực sự hội tụ** (mọi PRD blocker 3-4 → 0; COMM pass 4 ghi `verdict: converged`), GATE Keep/Change/Hybrid được dùng đúng (DEC-7 CHANGE re-approve, DEC-40 KEEP DEC-4). Pain thật nằm ở: (1) **PO thèm automation trên GitHub đến mức tự chế CI Python vô nghĩa** cho repo toàn markdown — kit không ship action `spec-validate`; (2) **vòng critique đắt**: mỗi pass phải `--fresh` vì `body_hash` "không bắt AC/frontmatter" (chính báo cáo critique tự thú), 13 báo cáo trong một ngày 02:54→23:35 — HEAD đã có fingerprint N1 + `apply_critique_progress.py`, PO chỉ cần upgrade nhưng **không có đường upgrade nào được tài liệu hoá**; (3) **lớp "nhìn" chết sau ngày 2**: 10 file visuals đều 06-03 (board chứa 56/102 story), không `latest` alias, trong khi story approved vẫn trỏ PO "xem AC bằng Explorer view"; PRODUCT.md bản đồ horizon sai với 2 PRD approved mà validate vẫn "0 lỗi"; `.session.md` ôi thiu còn ghi "metric 30 hub (không phải 50)" ngược DEC-43 — đúng nguồn mà GATE-NEVER-ASSUME cho phép assume.

## FINDINGS

### [POX-F01] PO tự chế GitHub Actions CI vô nghĩa — tín hiệu nhu cầu "spec-validate" tự động mà kit không ship
- Mức độ: High
- Loại: FEATURE-GAP
- Bằng chứng: `/home/hieubt/Documents/Cleanmatic-ERP/.github/workflows/python-package.yml:30` (`python -m pip install flake8 pytest`), `:35` (`flake8 . --count --select=E9,F63,F7,F82`), `:40` (`pytest`); commit `9df10cf` "Add GitHub Actions workflow for Python package" (author hunghenei, 2026-06-10 07:58 +0700, đúng template mặc định GitHub). `find /home/hieubt/Documents/Cleanmatic-ERP -name '*.py' | wc -l` → 125, toàn bộ trong `.claude/` (0 file ngoài). `grep -in 'github' /home/hieubt/Documents/product-spec/.claude/pack.manifest.yaml` → 0 match; workflows tracked của KIT chỉ là CI nội bộ kit (`.github/workflows/product-spec-ci.yml`…), không có template cho repo người nhận.
- Phân tích: Repo của PO là tài liệu sản phẩm thuần markdown; workflow này sẽ lint/test **125 file Python của chính kit** trên matrix 3.9–3.11 — không kiểm tra gì spec của PO, và có thể đỏ CI vì lý do PO không hiểu. Hành vi "bấm nút Actions suggested workflow" là bằng chứng trực tiếp PO muốn **kiểm tra tự động trên GitHub mỗi lần push** nhưng kit không cho họ cái gì để bật. PO làm việc nhóm ("3+ người", commit từ tài khoản thứ hai) → nhu cầu validate-on-push là thật.
- Đề xuất: Bundle ship sẵn template `.github/workflows/spec-validate.yml` (chạy `check_traceability` / `check_consistency` / `check_fence` trên `docs/product/`, in summary tiếng Việt PO đọc được vào job summary/PR comment) + installer hỏi PO có muốn bật không. Đây vẫn là validate TÀI LIỆU — trong ranh giới sản phẩm, không sinh code/tech design.

### [POX-F02] PRODUCT.md bản đồ phân hệ lệch horizon với 2 PRD approved — validate vẫn báo "0 lỗi"
- Mức độ: High
- Loại: CORRECTNESS
- Bằng chứng: `PRODUCT.md:51` "| Kết nối & Thanh toán nâng cao | PRD-PAYMENT | next |", `PRODUCT.md:54` "| Báo cáo & Phân tích | PRD-REPORT | later |" — nhưng `prds/payment.md:9` `horizon: now` (DEC-39/40, approved 06-10) và `prds/report.md:9` `horizon: now` (DEC-41). `change-log.md:18`: "Validate đầy đủ: 0 lỗi (traceability/consistency/fence)". HEAD cũng không kiểm: `grep -n 'PRODUCT' …/scripts/check_consistency.py` → 0 match (cả `check_consistency_time.py`/`check_traceability.py`).
- Phân tích: PRODUCT.md là "bản đồ phân hệ" — đúng cái bảng một PO non-technical mở ra đầu tiên để trả lời "cái gì vào MVP". Hai PRD được PO kéo vào MVP qua DEC nhưng bản đồ không sync, và validate khẳng định sạch → PO tin nhầm tài liệu nền. Đây là chỗ kit khiến PO sai: horizon là dữ liệu frontmatter có cấu trúc ở cả hai nơi, hoàn toàn check được bằng script.
- Đề xuất: Thêm rule consistency "hàng trong bảng phân hệ PRODUCT.md ↔ `horizon` frontmatter của PRD" (parse bảng theo ID, không theo heading); kèm autosuggest sửa khi PO chạy `--update`. CHƯA AI GIẢI (kể cả HEAD).

### [POX-F03] `.session.md` ôi thiu chứa fact đã bị supersede — đúng nguồn GATE-NEVER-ASSUME cho phép assume
- Mức độ: High
- Loại: CORRECTNESS
- Bằng chứng: `.session.md:4` `last_updated: 2026-06-02`, `:30` "- [x] BRD-G1 metric: 30 hub (không phải 50)", `:51` "Tất cả artifacts hiện ở trạng thái `draft`" — trong khi `brd.md:16` metric "≥50 … (khớp North Star VISION — DEC-43, supersede mốc 30 trước)" và phân bố status thực tế `134 approved / 10 draft`. DEC-43 (decisions.md) ghi rõ nguồn gốc mâu thuẫn: "PO từng chốt 30 ở .session.md 2026-06-02". KIT `CLAUDE.md` GATE-NEVER-ASSUME: "Assume ONLY when: the PO already answered (`.session.md`/`PRODUCT.md`)".
- Phân tích: Suốt 8 ngày làm việc dày đặc, không workflow nào (approve, DEC, critique, update) refresh `.session.md`. File này giờ nói ngược 3 điều: metric (30 vs 50), số lượng (12 epic/11 story vs 30/102), trạng thái (all-draft vs 134 approved). Vì GATE chính thức cho phép LLM assume từ file này, một phiên mới hoàn toàn có thể "đã hỏi rồi, PO chốt 30" → silent reversal đúng nghĩa mà kit thề không làm. Blocker #1 của critique whole-spec (mâu thuẫn 30 vs 50) chính là hậu quả vết này.
- Đề xuất: (a) mọi workflow ghi artifact phải touch `.session.md` (hoặc deprecate field cũ); (b) DEC supersede phải quét `.session.md`/`PRODUCT.md` tìm fact bị thay; (c) validate cảnh báo "session stale" khi `last_updated` < max(`updated`) của artifact. Không thấy cơ chế này ở HEAD (cần kiểm thêm).

### [POX-F04] Visuals chết sau ngày 2: 10 file đều 06-03, 3 lần render trong 4 phút, không "latest", story approved vẫn trỏ vào Explorer cũ
- Mức độ: High
- Loại: UX-PO
- Bằng chứng: `ls visuals/` — toàn bộ 10 file timestamp 2026-06-03 (board+explorer ×3 lượt 23:09:37/23:11:45/23:13:41, roadmap ×2, dashboard ×1, `sales-tree-20260603-231229.html` đặt tên khác format). `md5sum`: 10 hash đều khác nhau (cùng size — chỉ khác timestamp nhúng; KHÔNG byte-identical). `grep -o 'PRD-…-S[0-9]*' board-…231341Z.html | sort -u | wc -l` → 56 story id, so với 102 story hiện tại. `stories/PRD-CARE-E1-S4.md:44` (approved 06-09): "xem bằng Explorer view hoặc đọc frontmatter". HEAD: `grep -n 'latest' …/scripts/render_html.py` → 0 match. Roadmap 2.5MB = vendor mermaid inlined (40 dòng `mermaid`), graph thật rất nhỏ (21 edge, 3 subgraph) — mở được, không phải vấn đề.
- Phân tích: PO render 3 lần trong 4 phút (mỗi lần đẻ thêm bộ file mới cùng nội dung) rồi **bỏ hẳn** — 7 ngày biến động lớn nhất của spec không có lần render nào. Triệu chứng kinh điển: không biết file nào mới nhất, mỗi lần chạy lại rác thêm, không có lý do quay lại. Tệ hơn: kit chuyển AC vào frontmatter và bảo PO "xem bằng Explorer" — con trỏ chỉ vào view đông cứng ở 55% spec.
- Đề xuất: (a) tên file ổn định `board-latest.html` (+ bản timestamp giữ lịch sử, có dọn dẹp); (b) offer re-render sau approve/update lớn, hoặc banner staleness trong HTML ("render lúc X — spec hiện có N node, lệch M"); (c) lệnh `--viz --clean` dọn bản cũ. CHƯA AI GIẢI ở HEAD.

### [POX-F05] AC canonical nằm trong YAML frontmatter — PO và đồng đội đọc trên GitHub thấy AC dưới dạng YAML thô
- Mức độ: Medium
- Loại: UX-PO
- Bằng chứng: `stories/PRD-CARE-E1-S4.md:44`, `PRD-PAYMENT-E1-S3.md:36`, `PRD-INVENTORY-E3-S1.md:40` — cùng dòng: "*Tiêu chí chấp nhận (AC) là nguồn chuẩn ở `acceptance_criteria` trong phần đầu file (frontmatter)… Đã gỡ bản sao ở thân để tránh lệch.*". AC dài, nhiều dòng escape quote (PRD-CARE-E1-S4 frontmatter dòng 21–31). Repo có 2 người commit (hunghenei + chủ repo) → đọc qua GitHub web là kênh thật.
- Phân tích: Quyết định DRY đúng cho máy nhưng đắt cho người: GitHub render frontmatter thành bảng thô/khối YAML, AC 10 mục lồng `[[ref]]` và escape quote gần như không đọc nổi với non-technical PO. Mitigation duy nhất kit đưa ra là Explorer — đang stale (POX-F04). Nghĩa là phần quan trọng nhất của story (AC) hiện không có chỗ đọc tử tế.
- Đề xuất: `--export` dạng đọc-được per-PRD/story (AC inline, đánh số) thành file/PDF cho PO chia sẻ; hoặc body tự sinh khối AC render-only có marker "generated — đừng sửa tay" (vẫn một nguồn chuẩn). HEAD có sẵn `workflow-export.md` — giải MỘT PHẦN: vấn đề là discoverability (PO chưa từng dùng; không thấy thư mục export nào trong repo).

### [POX-F06] DEC-13 áp dụng nửa vời: persona CSKH có trong frontmatter VISION nhưng không có chân dung trong body — VISION vẫn được approve
- Mức độ: Medium
- Loại: CONSISTENCY
- Bằng chứng: `grep -n 'CSKH' vision.md` → duy nhất dòng 13 (frontmatter `personas:`); body chỉ có 6 section chân dung (dòng 43/59/75/90/105/120 — không có CSKH). `decisions.md:142` DEC-13: "Thêm persona CSKH vào PRODUCT.md/VISION". `PRODUCT.md:30` có hàng CSKH đầy đủ. `vision.md:6-7` `status: approved`, 2026-06-10. `.session.md:13` còn ghi "6 chân dung người dùng".
- Phân tích: Validate chỉ đọc frontmatter ("Frontmatter is source-of-truth") nên đếm đủ 7 persona và im lặng — nhưng PO/stakeholder đọc *body* vision để hiểu CSKH là ai, và không có gì để đọc. Định nghĩa CSKH thực tế đang sống trong DEC-13 + một câu trong bảng PRODUCT.md. Đây là mẫu lỗi "DEC áp dụng một phần" mà không có checklist hậu-DEC nào bắt.
- Đề xuất: (a) check nhẹ "mỗi persona trong frontmatter vision có heading tương ứng trong body" (warning, không error); (b) khi `--update` thêm persona, sinh skeleton section đánh dấu PO-cần-điền. CHƯA AI GIẢI.

### [POX-F07] Vòng critique hội tụ nhưng đắt: mỗi pass phải `--fresh` full-rerun vì cache mù AC/frontmatter — đúng nơi AC được dời vào
- Mức độ: Medium
- Loại: ARCHITECTURE
- Bằng chứng: `critique/20260609T125531Z-PRD-TASK.md` frontmatter `pass: 2`, `prior_report: …121803…`, và nguyên văn: "Build `--fresh` (cache=none) vì các sửa nằm ở AC/frontmatter mà `body_hash` không bắt." Tally chuỗi: TASK b4→b0→b0 (3 pass/2h), COMM b3→b0→b0→b0 (4 pass/2.5h, pass 4 `verdict: converged — đề nghị đóng sổ + duyệt`). Ngày 06-09: 13 báo cáo từ 02:54 đến 23:35. Loop có hiệu quả thật: pass-2 xác nhận "Tám phát hiện tech/craft nặng nhất của lượt 1 … đều đã đóng"; jargon bị chê đã được dời đúng chỗ (`stories/PRD-TASK-E2-S1.md:48` "(quyết định kỹ thuật, không phải AC nghiệp vụ)"). HEAD: `apply_critique_progress.py` docstring "skips already-resolved fingerprints… never re-litigates", KIT `CHANGELOG.md:176` `finding_fingerprint` (N1, ship 1.4.0 — sau bản 1.1.0 PO đang dùng).
- Phân tích: Độ dài giảm 19.7K→13.5K→9.4K vì **spec tốt lên thật** (không phải critique lười) — kết luận hội tụ: CÓ. Nhưng giá mỗi vòng là full 4-lens re-run vì cache hash phần thân trong khi kit đã chuyển dữ liệu quan trọng nhất (AC) vào frontmatter — hai quyết định thiết kế tự đá nhau. PO bù bằng sức người (marathon 21 giờ).
- Đề xuất: (a) hash provenance phải phủ frontmatter (ít nhất `acceptance_criteria`) — ở HEAD tên vẫn là `body_hash`, cần xác minh đã vá chưa; (b) phần fingerprint/progress HEAD đã có → giá trị lớn nhất nằm ở việc đưa PO LÊN ĐƯỢC bản mới (xem POX-F09).

### [POX-F08] `.memory/critique-state.json` desync: kẹt ở pass-1 của TASK, thiếu hẳn 4 scope đã critique
- Mức độ: Medium
- Loại: ENV
- Bằng chứng: `cat .memory/critique-state.json` → chỉ 3 entry (CARE/FINANCE/TASK); entry TASK: `last_ts: 2026-06-09T12:18:03`, `report: …121803Z-PRD-TASK.md` (pass 1) dù pass 2 (12:55) và pass 3 (13:16) đã chạy; COMM/PAYMENT/REPORT/all-scope không có entry. `blocker_count` lệch tally báo cáo (state TASK=3 vs report "blocker 4"; CARE=5 vs "blocker 4") — ghi nhận số liệu, chưa kết luận nguyên nhân.
- Phân tích: Lớp memory để critique "nhớ lần trước" ngừng được ghi từ trưa 06-09 — các run sau (COMM 4 pass, PAYMENT, REPORT, all) chạy ngoài state. Các tính năng dựa trên state (provenance fast-path, drift) thành vô dụng; "Lặp lại từ báo cáo trước" sống nhờ `prior_report` truyền tay. Với PO non-technical, lớp này hỏng im lặng — không ai biết.
- Đề xuất: state ghi atomically cuối MỖI run + validate/`--doctor` đối chiếu state vs thư mục critique/ và cảnh báo lệch. HEAD đã rework cache (CHANGELOG dòng 316–322: state = "per-scope provenance fast-path marker") — giải MỘT PHẦN, cần verify hành vi ghi-mỗi-pass.

### [POX-F09] Không có đường upgrade: PO kẹt ở claude-pack 1.1.0 trong khi kit đã đi tới product-spec v2.3.0 (đổi cả tên bundle lẫn tên skill)
- Mức độ: Medium
- Loại: FEATURE-GAP
- Bằng chứng: `MANIFEST.json`: `"bundle_version": "1.1.0"`, built 2026-06-03; KIT HEAD commit `cc4cf2b` "release: product-spec v2.3.0". `grep -in 'update|upgrade|version' INSTALL.md` → 0 match (không một dòng hướng dẫn lên bản mới). PO cài skill tên `spec-critique`; KIT giờ là `product-spec-critique` (ls hai bên). Tiền lệ upgrade từng xảy ra và cần migration: backup 06-04 cho thấy schema cũ thiếu `type:` field (diff brd.md: bak không có `type: brd`), được `migrate_multidim_fields.py` xử lý.
- Phân tích: Mọi cải tiến đắt giá nhất với chính pain của PO này (fingerprint N1, apply-critique progress, inherit 12.5K) nằm sau 1.1.0. PO không có cách biết bản mới tồn tại, không lệnh upgrade, và việc đổi tên skill giữa chừng khiến upgrade thủ công dễ thành cài-chồng-hai-bản. Họ là khách hàng lý tưởng của upgrade nhưng bị bỏ rơi đúng chỗ đó.
- Đề xuất: (a) mục "Upgrade" trong INSTALL.md (uninstall map tên cũ→mới + chạy migration + giữ nguyên docs/); (b) lệnh `--doctor`/`--version-check` đọc MANIFEST.json và nói bằng tiếng Việt "bạn đang ở 1.1.0, bản hiện hành 2.3.0, được gì khi lên"; (c) installer HEAD nhận diện bundle cũ (kể cả tên cũ) và offer upgrade-in-place. HEAD giải MỘT PHẦN (installer + migrate script có; thiếu toàn bộ phần notify/hướng dẫn).

### [POX-F10] Backup toàn-thư-mục 06-04 là cp tay ngoài kit — may mắn không mất gì, nhưng kit không có snapshot/restore chính thức
- Mức độ: Low
- Loại: CLEANUP
- Bằng chứng: `docs/product.bak-20260604-055349/` (440K). `diff -rq` vs hiện tại: only-in-bak **0**, only-in-current 72, differ 86 → không file nào của PO bị mất; diff brd.md toàn thay đổi hợp lệ có hồ sơ (thêm `type: brd` do migration; metric 30→≥50 DEC-43; `competitors: []`→7). Không script nào tạo backup dạng thư mục: `migrate_multidim_fields.py:21` chỉ "copying the original to `<file>.bak`"; `install.sh:258` chỉ backup per-file `$DST.bak.$BACKUP_TS`. Không có lệnh restore/README trong thư mục backup.
- Phân tích: Trước đợt migration 06-04 ai đó (PO hoặc phiên Claude) phải tự `cp -r` cả cây — tức là chưa tin cơ chế an toàn của kit. Backup 440K giờ nằm vĩnh viễn cạnh docs thật, không ai dám xoá, và `grep -r` tương lai sẽ quét trúng nội dung cũ.
- Đề xuất: `--snapshot` / `--restore <ts>` chính thức (tự tạo trước migration/update lớn, tự nhắc dọn sau khi PO xác nhận), kèm README trong thư mục snapshot. CHƯA AI GIẢI.

### [POX-F11] 44 DEC trong một file 32K dạng pseudo-frontmatter — PO không có cách tra "DEC nào đang chi phối PRD-X"
- Mức độ: Low
- Loại: UX-PO
- Bằng chứng: `decisions.md` 32.4K, 44 block `^## DEC`; mỗi DEC mang khối `---\nid/status/date/affects\n---` GIỮA file (decisions.md:3-8, 15-19…) — không phải frontmatter hợp lệ, GitHub render thành đường kẻ ngang + text rời. Trường `affects:` rất giàu (vd DEC-44 `affects: BRD,DEC-2,PRD-TASK,PRD-COMM,PRD-REPORT,PRD-AI,PRD-PAYMENT`) nhưng chỉ tra được bằng Ctrl-F.
- Phân tích: Decision Register đang là tài sản giá trị nhất của PO này (mọi ruling GATE đều ở đây, có cả supersede chain DEC-4→DEC-39→DEC-40) nhưng là phần khó đọc nhất bộ docs. Dashboard/visuals hiện không hiển thị DEC.
- Đề xuất: view "Decision index" trong dashboard (lọc theo `affects`/date/status, vẽ chain supersede) hoặc `--decision --list PRD-X`. HEAD có `decision_register.py` (16K, structured, "kills re-litigation") — giải MỘT PHẦN ở tầng dữ liệu, chưa thấy tầng trình bày cho PO.

## BẢNG PAIN → CƠ HỘI (chốt, xếp theo giá trị)
| # | PO pain (bằng chứng) | Cơ hội tính năng (trong ranh giới tài liệu, audience PO) | Trạng thái HEAD |
|---|---|---|---|
| 1 | Thèm check tự động trên GitHub → tự chế CI Python vô nghĩa (F01) | Ship template GH Action `spec-validate` + summary tiếng Việt | **CHƯA AI GIẢI** |
| 2 | Critique 3-4 pass/PRD, mỗi pass `--fresh` vì hash mù AC (F07) | Fingerprint + progress + hash phủ frontmatter | **HEAD giải phần lớn** → giá trị nằm ở upgrade |
| 3 | Visuals stale 100%, không biết bản nào mới, story trỏ Explorer cũ (F04) | `*-latest.html` + auto-render hậu approve + staleness banner + cleanup | CHƯA |
| 4 | PRODUCT.md map sai horizon 2 PRD, validate im (F02) | Rule consistency PRODUCT-map ↔ PRD frontmatter | CHƯA |
| 5 | `.session.md` chứa fact bị supersede, là nguồn assume hợp lệ (F03) | Session auto-refresh + supersede sweep + stale warning | CHƯA (cần kiểm thêm HEAD) |
| 6 | Kẹt 1.1.0, không biết/không thể lên 2.3.0 (F09) | `--version-check` + upgrade-in-place + INSTALL mục Upgrade | MỘT PHẦN |
| 7 | AC trong YAML khó đọc trên GitHub (F05) | Export/render AC inline per story | MỘT PHẦN (`--export` có, PO không biết) |
| 8 | DEC áp dụng nửa (CSKH không có chân dung) (F06) | Persona frontmatter↔body check + skeleton hậu-DEC | CHƯA |
| 9 | Memory critique desync im lặng (F08) | Ghi state mỗi pass + `--doctor` đối chiếu | MỘT PHẦN |
| 10 | Backup tay, không restore (F10) | `--snapshot`/`--restore` chính thức | CHƯA |
| 11 | 44 DEC không tra cứu được theo PRD (F11) | Decision index view | MỘT PHẦN (data layer) |

## GIỚI HẠN & KHÔNG TÌM THẤY
- **Đã kiểm và SẠCH:** TBD/TODO trong prds/epics/stories = 0 match; `lang: vi` 159/159 file (không trộn EN/VI ở prose; jargon EN chỉ còn trong "Ghi chú thiết kế" có chủ đích sau ruling pass-2); 30 epic đều có ≥1 story, tên story↔epic khớp toàn bộ, validate 06-10 ghi "0 parse-error, 0 orphan/dangling (147 node, 147 edge)" (change-log.md:18); personas dùng đúng mã chuẩn xuyên vision→PRD→story trong mọi mẫu đã đọc; AC mẫu đo được, có negative case + fallback (không Given/When/Then nhưng chất lượng tốt); scope `in/out/core-value` được set đầy đủ ở 3 PRD đã đọc trọn (sales/payment/ai).
- Giả thuyết đề bài "3 cặp board/explorer byte-giống-nhau" **bị bác bằng md5sum** (10 hash khác nhau, chỉ trùng size) — báo cáo theo bằng chứng thực.
- Không chạy script validate/critique của kit lên PO-repo (tránh ghi `.memory`/state vào repo chỉ-đọc) — dựa vào claim trong change-log + spot-check thủ công bằng grep.
- Không xác định được tác nhân tạo `product.bak-20260604-055349` (không script nào trong kit tạo backup dạng thư mục — chỉ suy ra là cp thủ công; không có bằng chứng trực tiếp).
- Không kiểm chứng được kết quả thật của GH Actions trên GitHub (không gọi mạng); kết luận F01 dựa trên nội dung file + cấu trúc repo (pytest/flake8 sẽ chạy trên 125 file .py của kit — pass/fail thực tế chưa rõ).
- Chưa verify được ở HEAD: (a) `body_hash` đã phủ frontmatter AC chưa (tên biến vẫn là body); (b) có cơ chế auto-refresh `.session.md` chưa; (c) installer HEAD có upgrade-in-place từ bundle tên cũ `claude-pack`/`spec-critique` không.
- Hook rtk làm méo một số output (ls/grep bị tóm tắt định dạng `n:0:`); các số liệu nghi ngờ đều đã re-run bằng lệnh khác (find -printf, md5sum, sed) trước khi dùng làm bằng chứng.

Status: DONE
Summary: Soi xong PO-repo Cleanmatic-ERP (read-only): 11 findings, PO dùng kit thành công nhưng pain tập trung ở CI/visuals/session-stale/chi-phí-critique; 2 cơ hội giá trị nhất là GH Action spec-validate (chưa ai giải) và đường upgrade lên HEAD (fingerprint đã có sẵn).
Concerns/Blockers: 3 điểm cần verify thêm ở HEAD (body_hash phủ frontmatter?, session auto-refresh?, installer upgrade-in-place?) — nêu trong GIỚI HẠN.