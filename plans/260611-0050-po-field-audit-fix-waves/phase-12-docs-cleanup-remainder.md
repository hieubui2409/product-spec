---
phase: 12
title: "Docs/cleanup remainder"
status: pending
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
- [ ] Số changelog tái lập từ 2 tag (test); quy ước ghi.
- [ ] GUIDE đủ flag; inventory test 0 thiếu.
- [ ] State/cache untracked + gitignore; artifact prose giữ.
- [ ] viz ascii ≤120 cột; md giữ full.
- [ ] render_html tách hoặc DEC ngoại lệ; rác ck untrack/DEC.

## Risk Assessment
- `git rm --cached` nhầm artifact prose. Mitigate: liệt kê chính xác state/cache (`.session.md`/`.memory`/`.snapshots`), không đụng prose.
- Tách render_html phá render. Mitigate: smoke test render trước/sau.
