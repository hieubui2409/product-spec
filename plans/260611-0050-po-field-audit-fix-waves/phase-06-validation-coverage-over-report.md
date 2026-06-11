---
phase: 6
title: "Validation coverage + over-report fixes"
status: completed
priority: P2
effort: "1d"
dependencies: [1, 5]
---

# Phase 06: Validation coverage + over-report (đề xuất #9)

## Overview
Validate "0 lỗi" của PO là thật nhưng RỖNG NGHĨA ở nhiều chỗ: sentinel rò ra PO, over-report flood,
bảng phân hệ ↔ frontmatter không ai check, persona DEC áp nửa vời. Lấp các khoảng trống coverage.

## Mapping
- **PS-15** (HIGH, BUG-F02) — `check_fence.py:36` (`FENCE_PREFIX`, không cap/exclude) + `status.py:194` (nhúng nguyên mảng): cây sau-cài/chưa-commit → 2.258 cảnh báo / 1,09MB JSON (đếm cả `.claude/` kit tự cài), trái docstring "never an over-report" (**ở `status.py:44`**, không phải check_fence — red-team đính chính citation).
- **PS-16** (MED, BUG-F05/POX-M1) — `check_consistency.py:177` + `spec_graph.py:597-602` sentinel `<missing-id>` lộ vào finding PO-facing + `target_ids`/`source_files` bundle; type product/vision thiếu `id:` không bị flag.
- **Đề xuất #9 (POX-F02, POX-F06)** — không script nào check bảng phân hệ PRODUCT.md ↔ `horizon` PRD; persona frontmatter ↔ body heading (DEC áp nửa vời); template `id: PRODUCT` + migration bù id.

## Requirements
- Functional: fence exclude `.claude/` + aggregate theo thư mục + cap top-N giữ tổng; finding `missing_id` nêu tên file + formatter thay sentinel + lọc sentinel khỏi bundle; rule horizon↔PRD; warn persona frontmatter↔body; template id PRODUCT + migration.
- Non-functional: parse bảng md bám ID (không bám heading dễ vỡ).

## Architecture
- **PS-15**: `check_fence` default exclude `.claude/`; `status.py` aggregate breach theo thư mục + cap top-N + giữ tổng count (không nhúng nguyên mảng 2.258).
- **PS-16**: `ID_PATTERN_BY_TYPE` phủ product/vision; finding `missing_id` nêu tên FILE thay sentinel; formatter thay `<missing-id>`; lọc sentinel khỏi `target_ids`/`source_files`; template/migration bù `id: PRODUCT`.
- **#9**: rule mới parse bảng phân hệ PRODUCT.md theo ID, đối chiếu `horizon` PRD frontmatter → warn lệch; warn persona có trong frontmatter VISION nhưng thiếu chân dung body heading.

## Related Code Files
- Modify: `.claude/skills/product-spec/scripts/check_fence.py` (exclude+cap), `status.py` (aggregate)
- Modify: `.claude/skills/product-spec/scripts/check_consistency.py` (missing_id nêu file), `spec_graph.py` (ID_PATTERN product/vision, lọc sentinel)
- Modify: template PRODUCT (`id: PRODUCT`) + migrate bù id
- Create: rule horizon↔PRD + persona frontmatter↔body (check_consistency hoặc rule riêng) + test
- Modify: REVIEW.md (PS-15, PS-16), EVIDENCE.md

## TDD — tests first
1. PS-15 RED: cây có `.claude/` → `status` hiện phun 2.258/1MB; sau fix → exclude `.claude/`, output cap top-N + tổng count. Assert size << 1MB.
2. PS-16 RED: PRODUCT.md thiếu `id:` → finding nêu TÊN FILE (không `<missing-id>`); bundle không chứa sentinel trong target_ids. RED hiện tại.
3. #9 RED: PRODUCT.md ghi PRD horizon `next` nhưng PRD frontmatter `now` → warn; persona trong VISION frontmatter thiếu body heading → warn.

## Implementation Steps
1. Viết RED tests. 2. fence exclude+aggregate+cap. 3. sentinel: ID_PATTERN+formatter+lọc bundle+template+migrate. 4. rule horizon↔PRD + persona. 5. GREEN. 6. Tick PS-15/PS-16 + EVIDENCE; #9 ghi vào EVIDENCE nếu sửa data PO.

## Success Criteria
- [x] `status` trên cây sau-cài: output cap (≤10 + 1 aggregate giữ tổng), exclude `.claude/`, << 1MB.
- [x] Thiếu `id:` → finding `missing_id`/`malformed_id` nêu tên file; sentinel KHÔNG rò vào finding (artifact_id + detail) lẫn bundle `target_ids`.
- [~] (DỜI) horizon PRODUCT.md ↔ PRD frontmatter + persona frontmatter↔body lint → **đề xuất #9**, dời sang cụm proposals (hỏi PO).

## Decisions + review fold (3-wave + critique-challenge)
- **DEC-P06-1 — exclude CHỈ `.claude/`:** fence loại trừ đúng kit-tree `.claude/` (không phải PO spec); mọi path ngoài-fence khác (vd `src/`) VẪN flag. Trade-off đã ghi: spec viết nhầm vào `.claude/` sẽ vô hình — nhưng `.claude/` không phải vị trí spec hợp lệ.
- **DEC-P06-2 — sentinel-scrub single-home:** thay vì sửa từng call-site, `make_finding` (nhà chung của mọi checker) null `artifact_id` sentinel + rewrite sentinel→file trong detail → mọi checker (persona_cap, version, self-ref, schema, time, risk) không thể rò. Reviewer bắt đúng lỗ persona_cap mà test 1-persona của tôi che; đã thêm `test_sentinel_not_leaked_via_other_checks` (>cap personas).
- **DEC-P06-3 — #9 + id-backfill migrator DỜI:** là đề xuất kiến trúc (POX-F02/F06), không phải defect; artifact id-less GIỜ đã bị flag (đó là defect đã đóng), auto-backfill id là proposal — hỏi PO ở cụm proposals.
- **Minor folds:** xoá PS-code khỏi comment test (review-audit-self-decision.md:34); xoá dead override `product`/`vision` ở `template_id_alloc.py` (đã có qua `**ID_PATTERN_BY_TYPE`). Pre-existing: `build_graph` unused-import ở template_id_alloc (có từ HEAD, ngoài scope).

## Risk Assessment
- Exclude `.claude/` quá rộng → miss breach thật trong docs/product. Mitigate: exclude CHỈ `.claude/`, giữ FENCE_PREFIX docs/product.
- Parse bảng md dễ vỡ. Mitigate: bám ID regex, không bám heading text.
