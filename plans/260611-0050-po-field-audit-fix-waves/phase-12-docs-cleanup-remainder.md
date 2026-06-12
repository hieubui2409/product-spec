---
phase: 12
title: "Docs/cleanup remainder"
status: completed
priority: P3
effort: "1d"
dependencies: [1]
---

# Phase 12: Docs/cleanup remainder (MED/LOW còn lại)

## Overview
Quét nốt các row MED/LOW thuần docs/cleanup không thuộc subsystem nào ở trên: số changelog không tái lập,
GUIDE thiếu flag, dogfood state committed, viz ascii tràn, render_html quá khổ, rác ck-local.

## Mapping (6 row)
- **PS-19** (MED, DRY-F04) — `product-spec/CHANGELOG.md:18` + root `CHANGELOG.md:30` claim "6090→5371 (−11.8%)" không tái lập từ git (thực 5758→5371 = −6.7%; 6090 chưa từng tồn tại) → sửa số so-với-release + quy ước "số changelog phải tái lập từ 2 tag".
- **PS-20** (MED, DRY-F07) — `GUIDE-EN.md`/`GUIDE-VI.md` thiếu `--voice` (+5 flag con) và `--compact-mode`; GUIDE critique thiếu alias `--gentle`/`--savage` → bổ sung + test flag-inventory SKILL↔GUIDE.
- **PS-22** (MED, DRY-F06) — `docs/product/.session.md` + `.memory/*` + `visuals/.snapshots/*` (tracked, 58e2d05) state/cache per-run bị commit → untrack + gitignore, giữ artifact prose.
- **PS-24** (LOW, BUG-F10) — `assemble_audit_trail.py` (ascii) bảng `--viz audit` dòng dài 368 ký tự → truncate cell theo budget ~120 cột, giữ full cho `--format md`.
- **PS-25** (LOW, DRY-F08) — `render_html.py` **1098 dòng tổng / 805 exec-LOC** (~4× guideline 200) → **BẮT BUỘC tách** template tĩnh ra module/asset (KHÔNG DEC-né — quá khổ rõ ràng). Sau tách: smoke test render đúng + mỗi module ≤ ngưỡng ~250.
- **LIB-11** (MED, DRY-F05) — `.claude/agents/` 13 file ck (a967688) + 2 `.env.example` + `schemas/ck-config.schema.json` (0 ref) rác ck-local committed → untrack hoặc ghi DEC "tracked có chủ đích, không ship".

## Requirements
- Functional: số changelog tái lập từ 2 tag; GUIDE đủ flag + test inventory; state/cache untracked + gitignore; viz ascii truncate; render_html tách hoặc ghi ngoại lệ; rác ck untrack hoặc DEC.
- Non-functional: giữ artifact prose của dogfood (chỉ untrack state/cache); không xoá lịch sử.

## Related Code Files
- Modify: `.claude/skills/product-spec/CHANGELOG.md`, root `CHANGELOG.md`, `docs/audit-trail` (quy ước số) — PS-19
- Modify: `GUIDE-EN.md`, `GUIDE-VI.md` + test flag-inventory SKILL↔GUIDE — PS-20
- Modify: `.gitignore` + `git rm --cached` state/cache (PS-22); rác ck (LIB-11)
- Modify: `assemble_audit_trail.py` (truncate ascii) — PS-24; `render_html.py` (tách) — PS-25
- Modify: REVIEW.md (6 row), EVIDENCE.md

## TDD — tests first
1. PS-19 RED: tính lại bằng `context_footprint.py` từ 2 tag → assert số changelog khớp đo-lại; thêm test/quy ước "số phải tái lập".
2. PS-20 RED: test flag-inventory diff SKILL↔GUIDE → hiện thiếu 8 mục; sau bổ sung → 0 thiếu.
3. PS-22 RED: `git ls-files` state/cache → hiện tracked; sau `rm --cached` + gitignore → untracked, artifact prose còn.
4. PS-24 RED: `--viz audit` ascii dòng max → 368; sau → ≤120; `--format md` giữ full.
5. PS-25: render_html LOC đo exec; tách hoặc DEC ngoại lệ (test smoke render vẫn đúng).
6. LIB-11: assert rác ck untracked hoặc DEC tồn tại.

## Implementation Steps
1. Viết RED tests. 2. Sửa số changelog + quy ước. 3. Bổ sung GUIDE + inventory test. 4. untrack state/cache + gitignore + untrack rác ck. 5. truncate viz ascii. 6. tách render_html hoặc DEC. 7. GREEN. 8. Tick 6 row + EVIDENCE.

## Success Criteria
- [x] Số changelog tái lập từ 2 tag (test); quy ước ghi.
- [x] GUIDE đủ flag; inventory test 0 thiếu.
- [x] State/cache untracked + gitignore; artifact prose giữ.
- [x] viz ascii ≤120 cột; md giữ full.
- [x] render_html tách (5 module + nhà-lá escape) + smoke render byte-identical; rác ck = DEC (không untrack).

## Risk Assessment
- `git rm --cached` nhầm artifact prose. Mitigate: liệt kê chính xác state/cache (`.session.md`/`.memory`/`.snapshots`), không đụng prose.
- Tách render_html phá render. Mitigate: smoke test render trước/sau.

## Review + Fold (3-wave + critique-challenge)

Implementation (PS-19/20/22/24 đã có từ wave trước; PS-25 split là việc mới) chạy nền; controller verify độc lập + 3-wave review (cleanup/correctness/coverage/dry/consistency) + critique-challenge. **2 finding fold, 1 nit fix.**

| # | Finding | Wave | Critique-challenge → ruling |
|---|---------|------|------------------------------|
| F1 | **Regression bảo mật do split** — agent gán "pre-existing", nhưng `test_body_render_values_fail_closed_when_libs_absent` PASS tại HEAD, FAIL sau split: `body_render_values` chuyển sang `render_html_assets`, đọc `VENDOR_MARKED` từ namespace của chính nó; test patch `render_html.VENDOR_MARKED` (bản re-export) thành no-op → lưới fail-closed mất tác dụng. | correctness | Challenge: "lỗ XSS production?" → KHÔNG (`.exists()` vẫn check filesystem thật); là **vỡ seam test** + bản re-export chết là footgun. Fix sâu: test patch đúng nhà thật (`render_html_assets`) **và** bỏ 2 hằng-số-path re-export chết khỏi facade (chỉ test buggy đọc; visualize.py + bundle không dùng) → triệt footgun, không phá public API. → **DEC-P12-1** |
| F2 | **DRY: `_escape` (chokepoint XSS) nhân bản 5×** sau split, **đã drift** thành 2 hành vi (orchestrator thiếu guard `str(s)`). | dry/consistency | Challenge: "in-scope? có DEC hợp thức hoá nhân bản?" → "dry" là trục review bắt buộc; phase nhân 1→5 bản; không DEC nào endorse; drift đã xảy ra thật (không lý thuyết). Gom về 1 nhà-lá `render_html_escape.py` (bản robust `str(s)` — superset, render byte-identical cho str). → **DEC-P12-2** |
| N1 | PS-24 comment stale: mô tả "fixed caps = 10+20+24+3 + 5*2 = 67 → ~53 left for two free-text columns" — không khớp array thật `[10,20,26,22,30,8]` (cả 6 cột cap cứng, sum 116). | consistency | Sửa comment khớp chiến lược thật (cap mỗi cột + proportional widest-first shrink khi >120). |

Verify độc lập: **product-spec 708/708 · critique 188/188** (chạy riêng process), 0 fail/0 err. PS-19 số `5758→5371 (−6.7%)` + `3820→3677 (−3.7%)` **tái lập chính xác** từ 2 tag bằng `token_proxy = ceil(len/4)` (lệch với `wc -c` đúng bằng ký tự đa-byte UTF-8). PS-20 mọi flag trong GUIDE đều tồn tại thật trong SKILL/references (không flag ma). Leak-scan finding-code CLEAN. Render smoke (`assemble`) byte-identical sau gom `_escape`.

## Decisions (DEC-P12) — Owner: hieubt · 2026-06-12

- **DEC-P12-1 — fail-closed seam fix tại nhà thật + bỏ re-export chết.** Test mô phỏng "libs absent" phải patch `render_html_assets.VENDOR_MARKED/PURIFY` (nơi lookup thật chạy), không phải facade `render_html.*`. Đồng thời gỡ 2 hằng-số-path `VENDOR_MARKED`/`VENDOR_PURIFY` khỏi block re-export của `render_html.py` (chỉ test đọc; visualize.py `import render_html` không chạm; bundle không phụ thuộc) — triệt "nhà-thứ-hai" gây vỡ lưới. Production fail-closed không đổi (`.exists()` luôn check filesystem).
- **DEC-P12-2 — `_escape` một-nhà-lá.** XSS chokepoint gom vào `render_html_escape.py` (leaf, không import sibling → không cycle), 5 module import 1 escaper. Dùng bản robust `str(s)` (superset của bản orchestrator thiếu guard) → render byte-identical cho input str, fix luôn drift đã xảy ra. Bỏ "self-contained copy pattern" không-có-DEC trước đó.
- **DEC-P12-3 — LIB-11 = tracked có chủ đích, KHÔNG untrack (premise FALSIFIED).** Finding "rác ck-local 0-ref" sai: `schemas/skill-schema.json` được `.claude/scripts/validate-skill-frontmatter.py` nạp (`_SCHEMA_PATH`); 7 agent `.claude/agents/*.md` ship qua `pack.manifest.yaml` `agents:`; `reflect_scan.py` tham chiếu `memory-harvester.md`; `.env.example` là template quy ước; `ck-config.schema.json` dùng bởi ck tooling. Untrack sẽ phá kit/validator/bundle. → giữ nguyên tracked, không untrack gì. (Áp dụng review-audit-self-decision: verify trước khi áp finding.)
- **DEC-P12-4 — regen `context_footprint_baseline.json` (gate đỏ có sẵn) + fold LIB-15/16.** Review phát hiện `_shared` footprint regression-guard ĐỎ tại HEAD: `product-spec SKILL.md +16, total +668` vs baseline — **không do P12** (P12 không đụng SKILL.md/references/), mà do ref P03-P07 (guardrails +182, validation-rules +189, workflow-status +144, workflow-validate +137) đã duyệt/commit nhưng quên regen baseline (per-phase verify trước chạy suite từng skill, không chạy `_shared`). Growth hợp lệ (work đã duyệt, không revert) → regen baseline theo đúng protocol guard tự nêu; 3 skill kia Δ0. Cùng lúc fold 2 defect-row doc-drift REVIEW gán "nhóm Phase 12 docs-cleanup" nhưng thiếu khỏi mapping 6-row: **LIB-15** (telemetry GUIDE dead-ref ×4 → `data/skill-chains.yaml`, GUIDE không vào footprint) + **LIB-16** (SKILL.md memory-hook desc sai → `product-spec-hooks.json`; premise verified install.sh:58-60; SKILL.md +18 token gộp vào regen). Verify: `_shared` footprint **43/43** sau regen.
