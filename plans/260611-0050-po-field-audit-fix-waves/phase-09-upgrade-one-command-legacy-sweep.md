---
phase: 9
title: "Upgrade-một-lệnh + legacy-sweep"
status: pending
priority: P1
effort: "3.5-4d"
dependencies: [3, 5, 8]
---

# Phase 09: Upgrade-một-lệnh + legacy-sweep (đề xuất #1, Q1=a)

> **2 stage (lens feasibility — atomic-swap là code dễ vỡ nhất plan, tách khỏi planner):**
> **9a (an toàn, ~1.5d):** legacy-map + dry-run-planner + backup-ts + symlink-guard + hash-diff cả-file-in-map.
> **9b (rủi ro, ~2-2.5d):** staging-build + atomic-swap + `trap ERR` rollback + `--rollback` 1-lệnh + verify-post-upgrade. Logic atomic nên ở **tầng Python planner** (deterministic, test được) thay vì bash thuần.
> **Sandbox fixture:** `spec-critique/` còn untracked trên đĩa (di tích rename `1798229`) → mô phỏng được; `claude-pack/` phải synthesize hoàn toàn. **bash 3.2:** dùng `docker run bash:3.2` (docker có sẵn) cho e2e THẬT, không chỉ static-lint.
> **`.ps1` parity:** cân nhắc ship `upgrade.ps1.template` SAU (DEC) nếu recipient không dùng Windows — giảm ~0.75d.

## Overview
Upgrade hiện là bãi mìn: installer chỉ ADD/OVERWRITE (default KHÔNG nâng skill cũ); skill+agent+hook đã rename
→ upgrade tạo cài-đặt-Frankenstein (2 skill critique, 2 packer, agent đôi, CLAUDE.md cũ route skill cũ).
Build `upgrade.sh` + legacy-sweep an toàn để PO 1.x lên 2.3.0 không vỡ.

## Mapping
- **DRY-F02 + ARC-F02 + CVR-F11 + POX-F09** (High) — không có upgrade/migration path từ claude-pack 1.x; installer ADD/OVERWRITE + STALE-skip; troubleshooting 0 dòng về upgrade.
- Tiền đề (đã fix ở phase trước): LIB-3 (hook bật ngầm — P3), PACK-3 (installer bash3 — P8).

## Requirements
- Functional (Q1=a): `upgrade.sh` (hoặc `install.sh --upgrade`): FORCE-đè-có-backup + bảng rename old→new (spec-critique/→product-spec-critique/, claude-pack/→release/, 6 agent, hook cũ) hỏi-rồi-xoá + thay CLAUDE.md cũ + chạy migrate (P5, **dry-run-only**) + mục "Nâng cấp" song ngữ INSTALL.
- Non-functional: **atomic** (staging + swap cuối) + **rollback** + **idempotent** + **dry-run mặc định** + backup-timestamped BẮT BUỘC trước mọi xoá; symlink-safe; không xoá file PO-sửa-tay (kể cả trong legacy-map nếu PO đã sửa).

## Architecture
- **Legacy map tường minh**: bảng (path cũ → hành động): `spec-critique/`→xoá-sau-backup, `claude-pack/`→xoá, agent ck đôi→xoá, hook đời-cũ→overwrite-with-backup (P3 kiểm-hành-vi), CLAUDE.md cũ→thay biến thể recipient (P8).
- **Atomicity (red-team A1)**: build trạng thái mới trong **staging dir** (temp), chỉ **swap atomic** ở cuối khi mọi bước OK; `trap ERR` → tự `--rollback`. `upgrade.sh --rollback` đọc backup-mới-nhất khôi phục 1 lệnh (cho PO non-technical, không cần `cp -r` tay).
- **Backup không-đè (red-team A2)**: MỌI backup mang `-<ts>` (kể cả `docs/product.bak-<ts>`, không tên cố định); guard không-ghi-đè; rerun idempotent → backup mới riêng, bản gốc lần đầu còn nguyên.
- **Symlink-safe (red-team A3)**: trước mọi xoá → `Path.is_symlink()`; nếu symlink → chỉ gỡ link, KHÔNG `rm -rf` đi theo (không xoá đích ngoài cây).
- **Hash-diff cả file trong legacy-map (red-team A4)**: file trong map nhưng nội dung KHÁC bản gốc nguyên thuỷ (PO sửa tay CLAUDE.md/skill cũ) → HỎI Keep/Change, KHÔNG xoá/thay mù.
- **Migrate trong upgrade = dry-run-only (red-team D8)**: `upgrade.sh` (bash) KHÔNG gọi được AskUserQuestion. Upgrade CHỈ chạy `migrate_metric_to_metrics --dry-run` → in `confirm_required` → DỪNG, hướng dẫn PO/LLM chạy bước approve riêng (P5). CẤM `--apply` approved trong upgrade.
- **Flow**: detect version (MANIFEST.json `bundle_version`) → dry-run in KẾ HOẠCH (đè/xoá/giữ, 0 ghi đĩa) → AskUserQuestion mục mơ hồ → backup-ts toàn bộ → build staging → swap atomic → migrate dry-run → verify (no skill đôi, CLAUDE.md mới, hooks an toàn).

## Related Code Files
- Create: `.claude/skills/release/assets/templates/upgrade.sh.template` (+ `.ps1`)
- Modify: `install.sh.template` (mode `--upgrade` gọi legacy-sweep) — phối hợp P8
- Create: legacy-map (data) + verify-post-upgrade script + test
- Modify: `INSTALL.md.template` (mục "Nâng cấp" song ngữ)
- Modify: REVIEW.md (không row ledger riêng — build-new #1; ghi DEC), EVIDENCE

## TDD — tests first (tên test mô tả hành vi)
1. `test_dry_run_lists_plan_and_writes_nothing`: sandbox 1.1.0 giả (spec-critique/ + claude-pack/ + hook cũ + CLAUDE.md cũ) → `--dry-run` → kế hoạch đúng + `git status`/mtime KHÔNG đổi (kể cả settings.json + KHÔNG sinh `.bak`).
2. `test_apply_produces_clean_install`: `--apply` → 0 skill/agent/packer đôi, CLAUDE.md = biến thể mới, hooks config-gated, backup-ts tồn tại.
3. `test_po_edited_legacy_file_prompts_not_deleted`: file TRONG legacy-map nhưng PO sửa (khác hash gốc) → HỎI, không xoá mù.
4. `test_symlink_target_not_followed_on_delete`: fixture symlink trong cây → chỉ gỡ link, đích ngoài cây còn nguyên.
5. `test_rerun_keeps_original_backup`: chạy 2 lần → 2 backup `-<ts>` riêng, bản gốc lần 1 còn nguyên (không bị product.bak đè).
6. `test_failure_mid_upgrade_rolls_back`: inject lỗi giữa chừng (vd migrate raise) → staging huỷ, trạng thái = trước-upgrade (atomic).
7. `test_upgrade_runs_migrate_dry_run_only`: assert upgrade KHÔNG `--apply` migrate trên approved.

## Implementation Steps
1. Viết RED tests + sandbox fixture 1.1.0 (synthesize: spec-critique/ untracked, claude-pack/, hook cũ, CLAUDE.md cũ). 2. legacy-map + dry-run planner (0 ghi). 3. backup-ts + staging build + swap atomic + `trap ERR`→rollback. 4. symlink-guard + hash-diff cả file in-map. 5. migrate `--dry-run` only + DỪNG. 6. verify-post-upgrade + `--rollback`. 7. INSTALL "Nâng cấp" song ngữ. 8. GREEN + idempotent. 9. Ghi DEC + EVIDENCE.

## Success Criteria
- [ ] `--dry-run` in kế hoạch, **0 ghi đĩa** (settings.json/`.bak` không sinh).
- [ ] Sau `--apply`: 0 skill/agent/packer đôi; CLAUDE.md mới; hooks an toàn; backup-ts tồn tại.
- [ ] File PO-sửa-tay (kể cả in-map) → hỏi, không xoá im lặng; symlink không bị follow.
- [ ] Lỗi giữa chừng → rollback về trạng thái trước-upgrade (atomic); `--rollback` 1 lệnh hoạt động.
- [ ] Rerun idempotent, backup gốc lần đầu còn nguyên; migrate trong upgrade chỉ dry-run.

## Risk Assessment
- **[red-team A1 CRIT] hỏng giữa chừng = Frankenstein, không rollback.** Mitigate: staging + swap atomic + `trap ERR`→`--rollback` 1 lệnh.
- **[red-team A2 HIGH] backup tên cố định đè bản gốc khi rerun.** Mitigate: mọi backup `-<ts>` + guard không-đè + test rerun.
- **[red-team A3 HIGH] symlink → xoá đích ngoài cây.** Mitigate: `is_symlink()` no-follow + fixture.
- **[red-team A4 HIGH] file PO-sửa trùng tên legacy → xoá mù.** Mitigate: hash-diff áp cả file in-map → hỏi.
- **[red-team D8 HIGH] upgrade.sh không AskUserQuestion được cho GATE migrate.** Mitigate: migrate chỉ dry-run trong upgrade, approve tách bước (P5).
- **[T1] Thiếu test thật macOS bash3.** Mitigate: loại bỏ `declare -A` (P8) + sandbox linux; ghi giới hạn rõ.
