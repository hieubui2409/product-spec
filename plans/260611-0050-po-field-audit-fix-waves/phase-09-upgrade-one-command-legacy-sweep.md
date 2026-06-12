---
phase: 9
title: "Upgrade-một-lệnh + legacy-sweep"
status: completed
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
- [x] `--dry-run` in kế hoạch, **0 ghi đĩa** (settings.json/`.bak` không sinh).
- [x] Sau `--apply`: 0 skill/agent/packer đôi; CLAUDE.md mới; hooks an toàn; backup-ts tồn tại.
- [x] File PO-sửa-tay (kể cả in-map) → hỏi, không xoá im lặng; symlink không bị follow.
- [x] Lỗi giữa chừng → rollback (atomic): sweep self-rollback all-or-nothing + `trap ERR`/try-catch auto-rollback sweep khi install/migrate sau-sweep lỗi; `--rollback` 1 lệnh hoạt động (e2e shell). *(Full staging-swap descope — DEC-P09-2.)*
- [x] Rerun idempotent, backup gốc lần đầu còn nguyên (ts µs riêng); migrate trong upgrade chỉ dry-run.

## Risk Assessment
- **[red-team A1 CRIT] hỏng giữa chừng = Frankenstein, không rollback.** Mitigate: staging + swap atomic + `trap ERR`→`--rollback` 1 lệnh.
- **[red-team A2 HIGH] backup tên cố định đè bản gốc khi rerun.** Mitigate: mọi backup `-<ts>` + guard không-đè + test rerun.
- **[red-team A3 HIGH] symlink → xoá đích ngoài cây.** Mitigate: `is_symlink()` no-follow + fixture.
- **[red-team A4 HIGH] file PO-sửa trùng tên legacy → xoá mù.** Mitigate: hash-diff áp cả file in-map → hỏi.
- **[red-team D8 HIGH] upgrade.sh không AskUserQuestion được cho GATE migrate.** Mitigate: migrate chỉ dry-run trong upgrade, approve tách bước (P5).
- **[T1] Thiếu test thật macOS bash3.** Mitigate: loại bỏ `declare -A` (P8) + sandbox linux; ghi giới hạn rõ.

## Review + Fold (2026-06-12)
3-wave code-review (cleanup/correctness/coverage/DRY/consistency) + báo cáo phase trước làm context →
critique-challenge mọi finding → fold **14** survivor (276 passed / 19 skipped, +38 vs 238; `docker bash:3.2 -n` OK).
HIGH đã đóng: (1) symlink-rollback báo-thành-công-giả — `_copy_to_backup` trả path không-suffix nên restore skip im lặng;
sửa = sidecar + `symlink_target` trong manifest + `os.symlink` recreate, 2 regression test (rollback + atomic-mid-apply).
(2) atomicity chỉ phủ sweep-loop, `trap` chỉ in → install/migrate sau-sweep lỗi = Frankenstein; sửa = `trap ERR`/try-catch
auto-rollback sweep (capture backup sau Step 1), e2e Step-2-fail + e2e shell `--rollback`. Polish: embed-integrity test
(byte-identity + MANIFEST sha256), drop planner `--rollback` trùng, `--dry-run`/`--apply` mutually-exclusive,
assert→ValueError, bỏ mkdir thừa + process-substitution, gitignore `upgrade-backup-*/`, lazy-backup-dir, µs timestamp.

## Decisions (DEC-P09)
- **DEC-P09-1 — Upgrade payload NHÚNG vào bundle `_upgrade/`, không ship qua skill `release`.** Recipient bundle bỏ skill `release` (P08) nên `upgrade_planner.py`/`upgrade_apply.py`/`legacy-map.json` được copy verbatim vào `_upgrade/` ở gốc bundle; "hai nhà": module nguồn (test ở dev-repo) + bản nhúng byte-identical (test `test_bundle_embeds_upgrade_payload` assert byte-identity + MANIFEST sha256). Two-phase MANIFEST build giải vòng phụ-thuộc token↔sha256. Owner: hieubt · 2026-06-12.
- **DEC-P09-2 — Atomicity có-giới-hạn (sweep atomic + auto-rollback), KHÔNG build full staging+swap.** Sweep huỷ-diệt là all-or-nothing (self-rollback trong loop) + `trap ERR`/try-catch tự `--rollback` sweep khi install/migrate sau-sweep lỗi. Full staging-dir+atomic-swap của bước install CỐ Ý không làm: plan tự gắn cờ "code dễ vỡ nhất"; install.sh là force-overwrite/idempotent nên chạy lại `--apply` là phục hồi sạch; mọi xoá đều có backup → **0 mất dữ liệu**. Dư địa: install lỗi có thể để lại file-mới-một-phần cạnh legacy đã khôi phục; recovery là chạy lại `--apply` (đã ghi trong thông báo trap). Owner: hieubt · 2026-06-12.
- **DEC-P09-3 — migrate trong upgrade = DRY-RUN-ONLY.** bash/pwsh không gọi được AskUserQuestion cho GATE approve; upgrade KHÔNG bao giờ truyền `--apply`/`--confirmed-by` cho migrate (static + e2e canh giữ); approve là bước PO riêng (P5). Owner: hieubt · 2026-06-12.
- **DEC-P09-4 — Symlink round-trip trung thực.** Symlink legacy: sweep chỉ UNLINK_ONLY (không follow ra đích ngoài cây); rollback tái-tạo bằng `os.symlink` từ `symlink_target` trong manifest (không phải copy nội-dung-đích thành file thường). 2 test canh giữ. Owner: hieubt · 2026-06-12.
- **DEC-P09-5 — ps1 không có runtime syntax-test.** Môi trường dev/CI không có PowerShell → ps1 chỉ verify qua đối-chiếu cấu trúc với bản bash (đã chứng minh runtime qua `docker bash:3.2`); ps1 dùng chung planner/apply Python nên fix symlink + atomicity áp cho cả hai. Owner: hieubt · 2026-06-12.
- **DEC-P09-6 — Backup nằm trong-cây + gitignore, không tạo dir rỗng.** `backup_root = target` để `--rollback` 1-lệnh `find -maxdepth 1` tìm được; upgrade append `upgrade-backup-*/` vào `.gitignore` target (idempotent, newline-safe) để không bẩn `git status`; backup dir tạo lười (chỉ khi có ≥1 mục thực-backup) nên run all-noop không sinh dir rỗng. ts giây→µs để hai `--apply` cùng-giây không trùng dir. Owner: hieubt · 2026-06-12.
