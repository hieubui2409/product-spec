---
phase: 7
title: "Session staleness + supersede sweep + open-questions"
status: completed
priority: P2
effort: "1d"
dependencies: [1, 5, 6]
---

# Phase 07: Session staleness + open-questions (đề xuất #4, Q5=a)

> **Serialize:** đụng `check_consistency.py` + `status.py` chung P5/P6/P10 → thứ tự P5→P6→P7→P10; RE-READ 2 file trước khi sửa.

## Overview
`.session.md` đóng băng 06-02 chứa 4 fact bị supersede, nằm ĐÚNG nguồn GATE-NEVER-ASSUME cho phép assume
→ một phiên mới có thể silent-reversal đúng nghĩa. Thêm staleness guard + supersede-sweep + sổ open-questions.

## Mapping
- **CVR-F03 + POX-F03** (High) — `.session.md` đóng băng chứa 4 fact bị supersede (metric 30-vs-50 ngược DEC-43, "Sepay VÀ Casso" ngược DEC-4, "toàn draft" vs 134 approved, đếm artifact cũ). HEAD không có staleness check.
- **POX-M2** (Med) — 3 câu hỏi kinh doanh "Vẫn còn mở" từ 06-02 không có nhà; story `must` mang tham số treo approved với ghi chú "cần PO xác định"; 0/44 DEC đụng; không workflow theo dõi open-questions.

## Requirements
- Functional (Q5=a): khi 2 nguồn lệch → `decisions.md` THẮNG; validate warn khi `.session.md.last_updated` < max(`updated` của artifact); supersede-sweep quét session/PRODUCT.md tìm fact bị DEC thay; sổ open-questions trong `--status`; `--approve` cảnh báo marker "cần PO xác định".
- Non-functional: false-positive warn nhẹ chấp nhận được; KHÔNG loại `.session.md` khỏi nguồn (giữ giá trị resume).

## Architecture
- **Staleness**: validate so `.session.md` last_updated vs max(updated) các artifact → warn "session ôi thiu N ngày, fact có thể bị supersede".
- **Decisions-priority**: khi assume từ `.session.md` mà `decisions.md` có ruling khác → ưu tiên decisions.md + báo lệch (không tự ghi đè session).
- **Supersede-sweep**: quét `.session.md`/`PRODUCT.md` đối chiếu DEC register → liệt kê fact bị thay (vd DEC-43 metric, DEC-4 payment).
- **Open-questions first-class**: scan marker "cần PO xác định"/"Vẫn còn mở" trong story `must` → sổ trong `--status`; `--approve` cảnh báo nếu artifact mang marker chưa giải.

## Related Code Files
- Modify: `.claude/skills/product-spec/scripts/check_consistency.py` (staleness warn) hoặc rule riêng
- Modify: `.claude/skills/product-spec/scripts/status.py` (sổ open-questions)
- Create: supersede-sweep script (đọc decision_register + session/PRODUCT) + test
- Modify: `.claude/skills/product-spec/SKILL.md` (`--approve` cảnh báo marker; ưu tiên decisions.md)
- Modify: REVIEW.md (không có row ledger — đây là build-new #4; ghi DEC), EVIDENCE nếu chạm data PO

## TDD — tests first
1. Staleness RED: `.session.md` last_updated < artifact updated → warn. RED hiện tại (0 staleness check).
2. Decisions-priority RED: session nói metric=30, DEC-43 nói 50 → assume trả 50 + báo lệch.
3. Supersede-sweep RED: fixture session chứa fact bị DEC thay → sweep liệt kê đúng.
4. Open-questions RED: story `must` có "cần PO xác định" → `--status` liệt kê; `--approve` cảnh báo.

## Implementation Steps
1. Viết RED tests. 2. Staleness warn. 3. Decisions-priority resolver. 4. Supersede-sweep script. 5. Open-questions sổ + approve-warn. 6. GREEN. 7. Ghi DEC; EVIDENCE nếu chạm data PO.

## Success Criteria
- [x] `.session.md` ôi thiu → validate warn (`session_stale`: session `updated` < max(artifact `updated`)).
- [x] Lệch session↔decisions → ưu tiên decisions.md + báo (`session_superseded` + `authoritative_source: decisions.md`; KHÔNG ghi đè session).
- [x] Supersede-sweep liệt kê DEC postdating session (criterion gốc "4 fact của PO" là PO-data → defer P13; fixture-test liệt kê đúng DEC-candidate theo ngày).
- [x] Open-questions hiện trong `--status` (`open_questions`); `--approve` open-questions gate cảnh báo marker treo.

## Decisions + review fold (3-wave + critique-challenge)
- **DEC-P07-1 — staleness = content-date, KHÔNG wall-clock:** so `.session.md` `updated` vs `max(artifact updated)`
  (cả hai là ngày commit) → deterministic, reproducible trong gate `--validate`. Khác quy tắc doc "updated > 30 ngày"
  (wall-clock, để ngoài gate như `time_advisory`). Phải extract `updated` lên node (an toàn: ngoài `CHANGED_FIELDS` →
  không churn `--status` delta; per-node `content_hash` không đổi vì nó tính từ body+AC+field-set cố định).
- **DEC-P07-2 — decisions-priority là SCRIPT-liệt-kê + LLM-phán (Q5):** script liệt kê DEC theo NGÀY (postdating session),
  gán `decisions.md` là authoritative; việc đối chiếu prose session↔DEC có mâu thuẫn thật là việc của LLM/PO. "Decisions win"
  hiện thực bằng surfaced-divergence + authority-designation, KHÔNG phải resolver prose tự động. Reviewer m2 xác nhận đây là
  thiết kế đúng (Script-vs-LLM split). Wiring guidance ở `guardrails-and-boundaries.md` (assume-path).
- **DEC-P07-3 — open_questions quét TOÀN cây, không chỉ `must`-AC:** defect POX-M2 có HAI ổ — story `must` (tham số treo trong AC)
  VÀ 3 câu hỏi kinh doanh "Vẫn còn mở" ở session notes; scan chỉ-must-AC sẽ bỏ sót ổ thứ hai. Reviewer M1 (docs khẳng định "must")
  fold bằng cách sửa wording doc/prompt cho khớp scan rộng (giữ code rộng); khoá hợp đồng bằng `test_marker_in_body_not_just_ac`.
- **Minor folds:** inline `_SCAN_GLOBS` (KISS); thêm clause comment `spec_graph` về snapshot-body gồm `updated` (date-only edit →
  đổi snapshot-filename hash, benign); marker diacritic-EXACT (chấp nhận theo plan "false-positive nhẹ"). DEC ghi ở audit-trail
  (không có kit-level DEC registry; `decisions.md` dành cho PO ruling).

## Risk Assessment
- False-positive staleness gây nag. Mitigate: warn-only, so ngày-vs-ngày, không block.
- Parse marker "cần PO xác định" miss biến thể chữ. Mitigate: tập marker + test biến thể; diacritic-exact có chủ đích.
