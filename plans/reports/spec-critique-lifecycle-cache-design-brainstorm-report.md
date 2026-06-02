# Spec-Critique Lifecycle & Cache — Brainstorm Design (consolidated)

Status: AGREED-NOT-IMPLEMENTED (chờ /plan hoặc /cook). Ghi 2026-06-02.
Memory pointer: `~/.claude/.../memory/spec-critique-lifecycle-design.md` (terse) → file này = full discussion.

Hạ tầng nền (snapshot/drift/prior_reports/judgment_cache reuse) ĐÃ có trong `critique_scan.py` nhưng CHƯA nối vào luồng chạy critique. Phát hiện then chốt: **lens layer voice-neutral** — lens chỉ emit `{evidence,critique,why_it_dies,fix,severity}`; voice/level/register áp ở consolidate+humanize. Nên lens findings ĐỘC LẬP với level → cache được, đổi level chỉ re-consolidate. E2e harness `.regen-lenses-*.json` đã chứng minh.

## Q1+Q2 (hợp nhất) — provenance nhúng report
Report frontmatter nhúng `body_hash` map của scope + lens findings + level/lang/register. Step 1 đọc report mới nhất cùng scope:
- drift=0 → reuse findings; đổi level chỉ re-consolidate (KHÔNG re-lens).
- body_hash đổi → re-lens node đó.
Bỏ snapshot global lệch-scope. Gate KINH TẾ (tiết kiệm token, không phải gate an toàn), default ON, `--fresh`/`--force` bỏ qua.
Web/market: cache market findings kèm `web_fetched_at` + TTL (vd 14 ngày); quá hạn re-search dù body_hash chưa đổi; `--refresh-web` ép tươi. 3 lens local cache theo body_hash.

## Q3 — invariant cứng, KHÔNG override
Floor "TARGET quyết định, không phải STRENGTH" + subagent-split (read-only lens/consolidate + Gate-2 humanizer độc lập) là BẤT BIẾN.
- PO override ĐƯỢC: level 1-9, register (gender/dialect), profanity-strength, scope, lenses, detail_level.
- PO KHÔNG override được: chửi gia đình/giới/vùng/slur/đe doạ/self-harm/sexual; gộp subagent vào main agent.
- Vượt → từ chối 1 dòng (report là file chia sẻ được, harm tồn tại bất kể consent). Thêm bảng IN/OUT-of-override vào `voice-and-tone.md`.

## Q4 — cross-critique context inheritance

### Bản chất: inherit JUDGMENT, không phải spec
Spec content của cha thì bundle đã luôn có (`_build_ancestry` + digest; export gộp 1 tài liệu xuyên-chuỗi). Cái export KHÔNG mang = **phán quyết critique trước của cha**. Giá trị duy nhất = không phán lại cái cha đã phán. → chỉ có nghĩa khi critique rời rạc qua nhiều phiên.

### "Nhiều cha" co lại trong thực tế
M:n duy nhất = cạnh PRD↔goal (`build_edges` emit 1 cạnh `brd_goal`/goal; `ancestors()` trả set đầy đủ). Nhưng goal/epic gần như không critique lẻ → "nhiều cha" gần như luôn = {1 PRD cha} + {1 critique `scope=all` trước}. `scope=all` = siêu-cha của mọi node → đa nguồn tự nhiên không cần critique goal lẻ.
LƯU Ý: `_build_ancestry` field `prd`/`epic` cố tình ĐƠN (đúng theo ID grammar 1 PRD+1 epic cha). Inherit PHẢI dùng `ancestors()` set, KHÔNG dùng field đơn đó — hai thứ khác mục đích.

### Cơ chế hợp nhất: phân loại từng FINDING theo evidence-ID
| evidence-ID finding cũ vs scope X | Phân loại | Dùng |
|---|---|---|
| == X hoặc con của X | repeat-offense (default ON) | "lần trước đã nói, chưa sửa" |
| tổ tiên của X | inherited context | "vấn đề cha = rủi ro con" |
| không liên quan | drop | — |
→ repeat-offense + inherit là MỘT pass, khác nhãn. DRY với plumbing `prior_reports` (consolidate.md:49).

### Chốt default: ON (opt-out), KHÔNG phải opt-in
Lý do: (1) cùng pass với repeat-offense vốn ON → tắt inherit là vứt finding đã phân loại; (2) tự thoái về no-op khi chưa có critique cha → ON không tốn gì lúc không có context; (3) flag thì không ai bật. Đổi lại 2 chốt an toàn:
- Inherited finding ở MỤC RIÊNG "Kế thừa từ cha", KHÔNG cộng tally, ghi nguồn `<parent-id>@<ts>`.
- Fresh-only: chỉ inherit finding evidence-ID còn resolve; cha stale → bỏ/đánh dấu.
- Giữ `--no-inherit` + preference cho PO scope-strict.

### Chống vỡ
| Rủi ro | Xử lý |
|---|---|
| Volume nhiều cha × prose | Chỉ rút blockers + DEC-worthy, KHÔNG prose |
| Mâu thuẫn giữa cha | KHÔNG resolve; surface cả hai như input |
| Stale cha | Fresh-only (tái dùng provenance Q1) |
| Double-count | Mục riêng, không cộng tally |
| Distance decay | Default cha trực tiếp + `all`; full chain = `--inherit=deep` (configurable preferences/flag) |
Consumer = consolidator (đã đọc prior_reports), KHÔNG đẩy vào lens (×4 payload + lệch evidence của X).

### Default vs deep depth — full chain & cost/value
- **Default (nearest+all):** đi ngược, dừng ở tổ-tiên-gần-nhất-CÓ-critique-tươi mỗi nhánh + critique `scope=all` gần nhất. critique story S: PRD cha đã critique → inherit PRD (+all), DỪNG, không lôi critique từng goal.
- **Deep (`--inherit=deep`):** inherit MỌI tổ tiên đã critique cả chuỗi (PRD + từng goal + epic).
- Cost/value: giá trị deep biên & giảm dần (tổ tiên gần đã mang phán quyết; goal-level trùng lặp PRD-level). Cost tuyến tính theo số-tổ-tiên-critique × (blockers+DEC). → default nearest+all = ~90% giá trị, chi phí chặn; deep cost vượt value ở ca thường → ĐÚNG là opt-in.

### Đơn vị inherit: nguồn + injection (làm rõ)
- **Nguồn = critique REPORT, KHÔNG phải spec** (đơn vị = phán quyết, chỉ có trong report). Parse markdown mỗi run = phí → đọc qua findings-index:
  - WRITE-time (step 6): mỗi finding → {evidence-ID, severity, why, fix, dec_worthy, report-ts} → upsert `.memory/critique-findings-index.json`.
  - RUN-time: `critique_scan` đọc INDEX (JSON) → phân loại evidence-ID theo graph-relation với X → tổ tiên + blocker/DEC + fresh-only = `inherited_context`.
  - Report = nguồn gốc sự thật; index = cache truy vấn.
- **Injection:** `critique_scan` ghi `inherited_context` vào BUNDLE (đã có graph+prior_reports, DRY). Lens BỎ QUA key này (bám evidence của X); consolidator tiêu thụ, render mục riêng, không cộng tally. Giống cách step 5 inject register/detail prefs chỉ cho consolidator.
- blockers+DEC = full text (evidence/why/fix) của riêng finding blocker+DEC (index trích sẵn → gần như free). pointer = chỉ "PRD-X@ts: N blockers", consolidator tự đọc report nếu cần.

### Descendant aggregation (gom verdict con lên cha) — CÓ làm (default ON, opt-out)
Khi critique PRD/epic, gom verdict các con đã critique ("3/5 story bị chê unbuildable → PRD có vấn đề delivery"). Cùng logic no-op khi chưa có critique con. Hướng NGƯỢC với inherit (lên thay vì xuống). Bounded = counts + blockers của con, fresh-only.

## Caching mở rộng (brainstorm 2)
| Ứng viên | Verdict | Lý do |
|---|---|---|
| Prior-report findings INDEX `.memory/critique-findings-index.json` (evidence-ID→finding, update mỗi write) | RECOMMEND | Nuôi inherit+repeat-offense: pass phân loại đọc index thay vì parse N markdown. Vừa cache vừa hạ tầng Q4 |
| Web-result cache theo URL `.memory/web-cache/<url-hash>`+TTL | RECOMMEND (mở rộng Q2) | Tinh hơn cache-finding: market lens chạy lại vẫn reuse trang đã fetch |
| Humanized output keyed hash(consolidated) | Có, rẻ | Chuỗi Q1/Q2: consolidated không đổi → humanize reuse |
| Structural findings (check_*) | KHÔNG | No-LLM, rẻ; cache = phức tạp thừa (KISS) |
| Bundle JSON toàn phần | KHÔNG | No-LLM, đọc spec rẻ |

## Mở rộng 4 ý
- **Q1**: nhúng graph-hash + ref validate-snapshot ("critique lùi sau N commit"); `--diff` critique (so 2 provenance → finding mới/đã sửa, git-diff cho critique).
- **Q2**: staleness score cho cached finding (bao nhiêu node lân cận đổi → nhãn "[từ cache, spec dịch nhẹ]").
- **Q3**: `--explain-floor` (PO đòi vượt → hiện dòng IN/OUT + gợi cách nói trong-ngưỡng; từ chối → chuyển hướng).
- **Q4**: index + `--diff` + descendant-agg = "critique health trend". Single home `.memory/critique-state.json` (kiểu last_validated.json) per-scope: last-ts/provenance-hash/blocker-count/drift-since → nuôi freshness + inherit + `--status` "scope nào cần critique lại".

## Quyết định PO (chốt 2026-06-02)
- [x] Inherit default = **ON, opt-out** (`--no-inherit`).
- [x] Descendant aggregation = **ON, opt-out** (`--no-rollup`).
- [x] Depth default = nearest+all; **deep = opt-in** (`--inherit=deep`, cost vượt value ở ca thường).
- [x] Adopt **CẢ 4 cache**: findings-index, web-url-cache+TTL, critique-state.json, humanized-output.
- [x] Inherit nguồn = report→findings-index (KHÔNG từ spec); inject = bundle field `inherited_context`, consolidator tiêu thụ, lens bỏ qua.

- [x] Inherit unit = **blockers + DEC-worthy, full text** (index đã trích sẵn evidence/why/fix → mang theo gần như free).
- [x] Implement scope = **full 4 ý 1 lần** (1 plan lớn khi sang /plan).

## Vì sao lens BỎ QUA inherited_context
1. Độc lập/anti-anchoring (cốt): lens neo theo phán quyết cũ → finding tương quan, mất giá trị đa-lens độc lập.
2. Kỷ luật scope: inherited_context nói về tổ tiên, không phải X → lens dễ chê cha, evidence-ID ngoài subtree X, fail grounding.
3. Đúng vai consolidator: "liên hệ critique trước" là tổng hợp/framing — consolidator đã làm (dedup, repeat-offense, top-3). 1 nhà thay vì 4 lens nửa vời. DRY.
4. Chi phí: bundle pass cho 4 lens → đọc inherited_context = ×4 token cho thứ chỉ consolidator cần.
5. Chống double-surface: lens vọng lại + consolidator render = item 2 lần, nguồn lẫn, rò tally. Lens mù → đúng 1 lần ở mục riêng, không vào tally.
Ngoại lệ market ("thấy verdict cha khỏi search lại") xử bằng web/judgment-cache reuse, không bằng nhét prose → vẫn giữ độc lập.

## Next
Brainstorm ĐÓNG. Pending thực thi khác (ngoài 4 ý): re-render vi-lvl6 (đang chạy nền) → commit fix register-bleed → journal. Implement 4 ý: chờ PO gõ /plan hoặc /cook.
