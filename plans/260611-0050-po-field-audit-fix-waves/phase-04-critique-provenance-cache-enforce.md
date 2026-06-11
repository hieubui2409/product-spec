---
phase: 4
title: "Critique provenance + cache enforcement"
status: pending
priority: P1
effort: "1.5d"
dependencies: [1]
---

# Phase 04: Critique provenance + cache enforcement (đề xuất #5, Q6-cache)

## Overview
Critique provenance mù đúng chỗ quan trọng nhất (AC/frontmatter), bundle nhét cả corpus, memory critique
ghi bằng LLM-flow không cưỡng chế → 12/15 report PO mất đường parse. Sửa cả 3 để fast-path/dedup/resume đáng tin.

## Mapping
- **PS-14** (HIGH, POX-F07/M3) — `spec_graph.py:124,466` provenance hash CHỈ body; `CHANGED_FIELDS` không có `acceptance_criteria`; BRD không có node trong body_hash map → sửa AC-only/BRD bị fast-path reuse kết quả cũ SAI.
- **PSC-2** (HIGH, BUG-F03) — `critique_signals.py:28` + `critique_bundle.py:117` `source_files` nhét toàn corpus bất kể scope (PRD đơn 148 key/700KB, 123 key off-target; all 1,24MB × 4 lens song song).
- **PSC-3** (HIGH, BUG-F06) — `workflow-critique.md` + `parse_critique_report.py` ghi lens-cache/`lens_findings_hash`/index/state là bước LLM-flow không cưỡng chế → 12/15 report parse `findings:0`, state kẹt pass-1.

## Requirements
- Functional: hash phủ `acceptance_criteria`; BRD có node trong body_hash map; bundle lọc theo scope; consolidator LUÔN ghi cache/index/state qua SCRIPT (không phụ thuộc LLM nhớ ghi).
- Non-functional: thay đổi hash invalidate cache cũ 1 lần (mong đợi, ghi rõ).

## Architecture
- **PS-14**: provenance hash mở rộng phủ `acceptance_criteria` (frontmatter); thêm node + hash cho BRD vào map. `CHANGED_FIELDS` gồm `acceptance_criteria`. Test "mọi artifact có mặt trong body_hash map".
- **PSC-2**: `source_files` lọc theo `target_ids ∪ ancestry ∪ digest`; descendants ở scope=all dùng `verbosity: struct` (struct thay full).
- **PSC-3**: consolidator script-enforce ghi cache + `lens_findings_hash` sau MỖI report (không để LLM-flow quên); `parse_critique_report` thêm fallback bóc heading `[severity][lens]` từ prose khi cache vắng; thêm `--doctor` đối chiếu state↔thư mục critique.

## Related Code Files (path đã xác minh vị trí thật — red-team bắt swap)
- Modify: `.claude/skills/product-spec/scripts/spec_graph.py` (hash AC + node BRD + CHANGED_FIELDS) — **P4 đi TRƯỚC P5 trên file này (serialize)**
- Modify: `.claude/skills/product-spec-critique/scripts/critique_provenance.py` (fast-path dùng hash mới) — ở **critique/**, KHÔNG product-spec/
- Modify: `.claude/skills/product-spec-critique/scripts/critique_signals.py`, `critique_bundle.py` (lọc scope)
- Modify: `.claude/skills/product-spec/scripts/parse_critique_report.py` (script-enforce ghi + prose-fallback + `--doctor`) — ở **product-spec/**, KHÔNG critique/
- Modify: `.claude/skills/product-spec-critique/references/workflow-critique.md` (bước ghi do script, không LLM)
- Modify: REVIEW.md (PS-14, PSC-2, PSC-3), EVIDENCE.md

> **Lưu ý cross-skill (PSC-3):** parser+state nằm 2 skill — `parse_critique_report.py` (consumer apply-critique) ở **product-spec/**; `workflow-critique.md` + cache scripts (writer) ở **product-spec-critique/**. Sửa cả hai phía.

## TDD — tests first
1. PS-14 RED: sửa CHỈ `acceptance_criteria` của 1 story approved → assert provenance đổi (fast-path KHÔNG reuse). RED hiện tại (body-only → "unchanged"). + test "mọi artifact (gồm BRD) có node trong map".
2. PSC-2 RED: `critique_scan --scope PRD-X` → assert `source_files` chỉ chứa target∪ancestry, KHÔNG 123 key off-target; bundle PRD-X ≠ bundle all. RED (hiện 148 key giống nhau).
3. PSC-3 RED: chạy consolidator → assert cache + `lens_findings_hash` + index ghi ra ĐĨA mà không cần LLM; `parse_critique_report` trên report-không-cache → fallback prose trả findings>0; `--doctor` phát hiện state↔dir lệch.

## Implementation Steps
1. Viết RED tests (1-3). 2. Mở rộng hash AC + node BRD + CHANGED_FIELDS. 3. Lọc bundle theo scope + struct descendants. 4. Script-enforce ghi cache/index + prose-fallback + `--doctor`. 5. GREEN. 6. Ghi note "cache rebuild lần đầu". 7. Tick 3 row + EVIDENCE.

## Success Criteria
- [ ] Sửa AC-only/BRD → critique KHÔNG fast-path reuse (provenance đổi).
- [ ] Mọi artifact có node trong body_hash map (test).
- [ ] Bundle PRD-X chỉ chứa target∪ancestry; payload giảm rõ rệt vs all.
- [ ] Consolidator ghi cache/index không phụ thuộc LLM; prose-fallback parse được report cũ; `--doctor` báo lệch.

## Risk Assessment
- Đổi hash → invalidate toàn bộ cache critique cũ 1 lần. Mitigate: ghi rõ trong CHANGELOG/note "rebuild mong đợi"; không phải lỗi.
- Lọc scope quá hẹp → mất ancestry cần thiết. Mitigate: union target∪ancestry∪digest, test off-target vs on-target.
