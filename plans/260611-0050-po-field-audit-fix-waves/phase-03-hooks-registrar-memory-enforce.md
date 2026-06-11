---
phase: 3
title: "Hooks/registrar safety + memory enforcement"
status: pending
priority: P1
effort: "1d"
dependencies: [1]
---

# Phase 03: Hooks/registrar safety + memory enforcement (đề xuất #10, Q6-hook)

## Overview
Sửa lỗ hổng Critical: upgrade default wire NGẦM blocking hook đời cũ không config-gate. Đồng thời (Q6=a)
auto-register memory hook kèm opt-out + config-gate, và thêm memory-lens hợp nhất narrate sức khoẻ memory sản phẩm.

## Bối cảnh đã xác minh (red-team)
HEAD v2.3.0 **đã default-safe**: `register_telemetry_hooks.py` wire `memory_gap_hook` "wired-always, config-gated"; `product-spec-hooks.json` đã `memory_gap_hook: false` + README ghi "blocking hook never fallback-enabled". Marker `# config-gate` **KHÔNG tồn tại** trong hook nào (chỉ prose trong test fixture). `memory_gap_hook.py` có contract **LOCKED blocking exit-2** khi bật. → LIB-3 KHÔNG phải "đổi default HEAD" (HEAD đã đúng); LIB-3 là **upgrade giữ hook 1.1.0 đời-cũ** (không config-gate) khi installer SKIP-existing.

## Mapping
- **LIB-3** (HIGH/Critical, ARC-F01) — **lỗi thật = upgrade path**: `install.sh.template:285` SKIP-existing giữ `memory_gap_hook.py` đời 1.1.0 (KHÔNG config-gate, blocking vô điều kiện); registrar wire nó → blocking exit-2 bật ngầm cho PO chưa opt-in.
- **Q6-a (hook)** + **CVR-F13** — memory hook auto-register + auto-enable để memory layer hết "chết im" (như telemetry 2.1.0), NHƯNG đụng luật "blocking không bao giờ fallback-enabled" → cần **advisory mode** (DEC).
- **Đề xuất #10 (ARC-F11)** — memory-lens hợp nhất: đọc `docs/product/.memory` (tuổi last_validated, store rỗng/thiếu, cache size) narrate VI.

## Requirements
- Functional: (1) upgrade OVERWRITE hook đời-cũ bằng bản HEAD config-gated (treat hooks là code kit, backup trước); (2) memory hook auto-enable ở **advisory mode** (warn, exit 0) làm default mới, blocking exit-2 GIỮ cho ai opt-in; (3) memory-lens read-only narrate VI.
- Non-functional: KHÔNG ÂM THẦM gỡ blocking của user đã opt-in; thay đổi mode advisory = **ghi DEC**; opt-out = set key `false` trong `product-spec-hooks.json` (đã là cơ chế HEAD).

## Architecture
- **Version-guard (sửa cách)**: KHÔNG grep marker (marker không tồn tại + giả mạo được). Thay bằng **kiểm hành vi**: hook đời-cũ nhận diện qua KHÔNG import/gọi `hook_runtime.hook_enabled` (hoặc đối chiếu version field trong MANIFEST). Hook không-config-gated → overwrite-with-backup bằng bản HEAD.
- **Installer hooks = code kit**: `install.sh.template` overwrite hook kit (KHÔNG SKIP-existing); nếu nội dung khác bản gốc nguyên thuỷ (PO sửa tay) → hash-diff + HỎI Keep/Change (không đè mù); backup `.bak-<ts>` trước.
- **Memory advisory mode (DEC)**: thêm mode advisory (warn, exit 0) vào `memory_gap_hook` + flag config chọn advisory/blocking; auto-enable đặt advisory làm default; **blocking giữ nguyên cho user đã set `true` + opt-in blocking**. Test khẳng định opt-in-blocking KHÔNG bị hạ cấp im lặng.
- **Opt-out định nghĩa rõ**: `memory_gap_hook: false` trong `product-spec-hooks.json` = tắt; file config vắng → enforcement OFF (đã đúng HEAD). Test "config vắng → không exit-2".
- **Memory-lens**: script read-only đọc `docs/product/.memory/*` → narrate VI.

## Related Code Files
- Modify: `.claude/skills/release/assets/templates/install.sh.template` (hooks overwrite-with-backup + hash-diff-hỏi nếu PO sửa) — **P3 đi TRƯỚC P8 trên file này**
- Modify: `.claude/skills/telemetry/scripts/register_telemetry_hooks.py` (kiểm hành-vi thay marker; auto-enable advisory)
- Modify: `.claude/hooks/memory_gap_hook.py` (thêm advisory mode warn/exit-0; blocking giữ cho opt-in)
- Modify: config `product-spec-hooks.json` (mode advisory/blocking + giữ default-safe)
- Create: memory-lens script (telemetry hoặc product-spec scripts) + test
- Modify: REVIEW.md (LIB-3), EVIDENCE.md; **ghi DEC "memory advisory mode"**

## TDD — tests first (tên test mô tả hành vi, KHÔNG `test_lib3_*`)
1. RED `test_old_hook_without_config_gate_is_overwritten_on_upgrade`: sandbox có `memory_gap_hook.py` đời-cũ (không gọi `hook_enabled`) → sau upgrade, file = bản HEAD config-gated + `.bak` tồn tại. RED hiện tại (SKIP-existing giữ bản cũ).
2. RED `test_upgrade_does_not_silently_wire_blocking_old_hook`: sau registrar trên hook cũ → KHÔNG exit-2 path active (default-safe).
3. RED `test_memory_auto_enable_defaults_to_advisory_exit_zero`: auto-enable → advisory warn, exit 0; `test_opted_in_blocking_not_downgraded`: user đã chọn blocking → vẫn exit-2 (KHÔNG hạ cấp im lặng).
4. RED `test_missing_config_means_enforcement_off`: config vắng → không exit-2.
5. RED `test_po_edited_hook_prompts_before_overwrite`: hook khác bản gốc → hỏi, không đè mù.
6. Memory-lens: fixture `.memory` rỗng/cũ → narrate đúng.

## Implementation Steps
1. Viết RED tests. 2. Kiểm-hành-vi thay marker trong registrar. 3. Installer hooks overwrite-with-backup + hash-diff-hỏi. 4. Advisory mode + auto-enable default advisory + giữ blocking opt-in. 5. Memory-lens read-only. 6. GREEN. 7. Ghi DEC advisory + tick LIB-3 + EVIDENCE.

## Success Criteria
- [ ] Upgrade overwrite hook đời-cũ bằng bản HEAD config-gated (test); không bật ngầm blocking cũ.
- [ ] Hook PO-sửa-tay → hỏi trước khi đè (không đè mù).
- [ ] Auto-enable memory = advisory exit-0; opt-in-blocking KHÔNG bị hạ cấp im lặng (test).
- [ ] Config vắng → enforcement OFF.
- [ ] Memory-lens narrate sức khoẻ `docs/product/.memory`; DEC advisory ghi.

## Risk Assessment
- **[red-team D4/D7] marker config-gate không tồn tại → guard grep-marker sai.** Mitigate: kiểm HÀNH VI (import/gọi `hook_enabled`) hoặc MANIFEST version, KHÔNG grep comment.
- **[red-team D5] advisory auto-enable có thể âm thầm gỡ blocking của user opt-in.** Mitigate: advisory chỉ là default cho auto-enable; blocking giữ cho opt-in; DEC + test `test_opted_in_blocking_not_downgraded`.
- Overwrite hook đè bản PO sửa tay. Mitigate: hash-diff + hỏi + backup `.bak-<ts>`; phối legacy-sweep (P9).
