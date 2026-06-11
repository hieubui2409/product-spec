---
phase: 2
title: "Telemetry data-quality pack"
status: in-progress
priority: P1
effort: "1.5d"
dependencies: [1]
---

# Phase 02: Telemetry data-quality pack (đề xuất #3)

> **COOK PROGRESS 2026-06-11 (partial):** ✅ **LIB-4** (HIGH — `scan_head` quét tới record đầu có ts → duration không còn 0; + bắt early skills ở head → skills không còn rỗng; 2 test) · ✅ **LIB-8** (record mang `session` join key; 1 test) · ⚠ **LIB-9 DEFER** (verify CC docs: `UserPromptExpansion` HỢP LỆ — không rename; điều tra matcher+e2e). **Suite 205 passed.** **CÒN LẠI:** LIB-7 (SCRIPT_RE matcher), LIB-10 (CLAUDE.md routing+four), LIB-12 (i18n reason_code), LIB-13 (telemetry-readback doc), LIB-14 (fixture id), carry-in (gather_all per-lens isolation), + LIB-9 điều tra. **Review 3-wave + critique chạy khi phase xong.**

## Overview
Telemetry "có ống chưa có nước": 3 trường chủ lực chết trên data thật + data còn lại bẩn. Sửa parse,
classify, matcher, key join để mọi lens phía sau có data thật mà narrate.

> **Carry-in từ cook P01 (review/critique):** `analyze_telemetry.gather_all` là list-comprehension KHÔNG try/except → 1 lens raise (vd workflow lens fail-loud khi `data/skill-chains.yaml` vắng trên recipient) làm crash CẢ `--lens all`/overview (7 lens tối). Thêm per-lens isolation: bọc mỗi lens → error-dict `{lens, error}` (visible, KHÔNG silent drop), GIỮ `declared_chains()` raise ở mức hàm (đừng yếu hoá unit test). Test: 1 lens hỏng → overview vẫn render 6 lens kia + 1 dòng error.

## Mapping (8 row)
- **LIB-4** (HIGH, ARC-F04) — `emit_session_summary.py:60-68,115` `first_timestamp()` chỉ đọc dòng đầu (record đầu không ts) → 43/43 `duration_s:0`; 46/46 subagent `outcome:unknown`; 41/43 `skills:[]`.
- **LIB-7** (MED, ARC-M2) — `hook_runtime.py:41` + `track_script_execution.py:57-59` SCRIPT_RE substring-match → grep/ls/glob đếm như "script run"; validate-proxy đếm grep `check_*` như PASS.
- **LIB-8** (MED, ARC-M3) — `track_script_execution.py:61-68` biến `session` tính nhưng không ghi vào record (414/414 thiếu key).
- **LIB-9** (MED, ARC-F08) — `register_telemetry_hooks.py:107-108` kênh `UserPromptExpansion` 0 record. **⚠ ĐÃ VERIFY (claude-code-guide, dẫn CC hooks docs): `UserPromptExpansion` LÀ event HỢP LỆ** (fire khi slash-command expand, matcher = TÊN command). Giả định "sai tên event" của lens-B → **REFUTED**. 0-record KHÔNG phải do tên sai → nghi `matcher: None` (cần tên command/regex, không None) HOẶC handler không bắt đúng payload, HOẶC PO không gọi skill qua slash trong cửa sổ đo. **KHÔNG rename mù.** Cần: kiểm matcher config + e2e 1 phiên thật → quyết sửa matcher / thêm `UserPromptSubmit` fallback / gỡ. **Defer tới khi điều tra matcher+handler** (không phải fix 1 dòng).
- **LIB-10** (MED, ARC-F07) — `CLAUDE.md:4,8-13` "three PO-facing skills", bảng 3 hàng → telemetry vô hình.
- **LIB-12** (LOW, BUG-F09) — `lens_validate_proxy.py:82` + `telemetry_render.py:182` reason EN hardcode giữa output VI; bản dịch `val_na` có sẵn không dùng.
- **LIB-13** (LOW, DRY-F09) — `telemetry-readback.md` thiếu sink `.logs/hook-crashes.log` + config gate `product-spec-hooks.json`; README.md:26 gán memory-gap hook nhầm critique.
- **LIB-14** (LOW, DRY-F10) — fixture test còn id "claude-pack".

## Requirements
- Functional: duration/outcome/skills tính đúng từ transcript thật; script-run matcher chỉ bắt thực-thi; record mang `session`; UserPromptExpansion được chứng minh (hoặc gỡ); routing nêu telemetry là skill thứ 4.
- Non-functional: fail-open giữ nguyên (telemetry không bao giờ làm vỡ op chính); i18n VI nhất quán.

## Architecture
- **LIB-4**: `first_timestamp()` scan tới record ĐẦU TIÊN có `ts` (không đọc mỗi dòng đầu). `outcome` classify từ TAIL theo Status-protocol (`DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT`). `skills` rút từ PreToolUse:Skill records trong transcript.
- **LIB-7**: SCRIPT_RE đòi path đứng-đầu-lệnh hoặc sau-interpreter (`python3? <path>`), bỏ substring/glob. Đồng bộ matcher ở `hook_runtime.py` và `track_script_execution.py` (DRY — 1 nguồn).
- **LIB-8**: thêm `"session"` vào record (biến đã có sẵn). Cập nhật mọi test đọc record.
- **LIB-9** (DEFER — đã verify event hợp lệ): điều tra `matcher: None` (CC docs: matcher nên là tên command/regex) + e2e 1 phiên thật gõ slash-command → assert record. Theo kết quả: (a) sửa matcher; (b) thêm `UserPromptSubmit` làm fallback rộng (bắt mọi prompt-submit); (c) gỡ nếu thật trùng `PreToolUse:Skill`. KHÔNG rename `UserPromptExpansion` (nó hợp lệ).
- **LIB-10**: thêm hàng `telemetry` vào bảng routing CLAUDE.md + sửa "three"→"four"; 1 dòng nudge trong `--status`.
- **LIB-12**: lens trả `reason_code`; render map label localize (dùng `val_na` sẵn có).

## Related Code Files
- Modify: `.claude/hooks/emit_session_summary.py`, `.claude/hooks/hook_runtime.py`, `.claude/hooks/track_script_execution.py`
- Modify: `.claude/skills/telemetry/scripts/register_telemetry_hooks.py` (LIB-9 sau e2e), `lens_validate_proxy.py`, `telemetry_render.py`
- Modify: `CLAUDE.md` (routing + "four"), `docs/audit-trail/telemetry-readback.md`, `.claude/skills/telemetry/README.md`
- Modify: fixtures test còn id "claude-pack" (LIB-14 — grep liệt kê chính xác trước sửa)
- Modify: REVIEW.md (8 row), EVIDENCE.md (8 entry)

## TDD — tests first
1. LIB-4: fixture transcript thật (record đầu KHÔNG ts) → assert `duration_s>0`, `outcome∈{done,...}`, `skills` non-empty cho phiên có skill. RED hiện tại (0/unknown/[]).
2. LIB-7: fixture record chứa `grep ... check_consistency.py` literal → assert KHÔNG đếm như script-run; fixture `python3 .../check_x.py` → đếm. RED hiện tại (substring bắt nhầm).
3. LIB-8: assert mọi record script-run có key `session`. RED (414/414 thiếu).
4. LIB-9 (defer): KHÔNG test rename. Sau điều tra matcher: test assert matcher hợp lệ (không None) HOẶC e2e phiên thật assert record. `UserPromptExpansion` giữ nguyên (hợp lệ).
5. LIB-12: assert output telemetry VI không chứa câu EN hardcode.

## Implementation Steps
1. Viết RED tests (1-5). 2. Sửa `first_timestamp`+classify+skills. 3. Siết SCRIPT_RE (1 nguồn). 4. Thêm `session` key. 5. e2e UserPromptExpansion → quyết giữ/gỡ. 6. routing+i18n+docs. 7. GREEN full suite. 8. Tick 8 row + 8 EVIDENCE.

## Success Criteria
- [ ] Trên fixture data thật: `duration_s>0`, `outcome` phân loại đúng, `skills` non-empty.
- [ ] grep/ls/glob không còn đếm như script-run; validate-proxy không tính grep `check_*` là PASS.
- [ ] 100% record script-run có `session`.
- [ ] LIB-9 (defer): `UserPromptExpansion` đã verify hợp lệ — điều tra matcher/handler, KHÔNG rename. Quyết sửa-matcher/fallback/gỡ sau e2e.
- [ ] CLAUDE.md routing có telemetry, "four"; output telemetry VI thuần.

## Risk Assessment
- Đổi outcome-classify dựa tail-protocol có thể miss format lạ. Mitigate: default `unknown` an toàn + fixture đa dạng.
- Siết SCRIPT_RE quá tay → miss script thật. Mitigate: fixture từ record thật cả 2 chiều.
