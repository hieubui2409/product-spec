---
phase: 5
title: "Migration + goal/frontmatter correctness"
status: completed
priority: P1
effort: "1.5d"
dependencies: [1, 4]
---

# Phase 05: Migration + goal/frontmatter correctness (Q2)

## Overview
Upgrade biến validate XANH thành ĐỎ trên artifact approved (`metric:` singular) mà không có đường migrate.
Sửa migration + message + thêm các check schema bị nuốt — đi qua GATE cho mọi đụng-chạm approved.

> **Artifact đích (red-team xác minh):** migration nhắm **artifact legacy v1.x của recipient** (PO Cleanmatic-ERP: `brd.md:16` `metric:` singular + approved — repo NGOÀI cây này). Dogfood dev (`docs/product/brd.md`) ĐÃ `metrics:` plural + draft → KHÔNG cần migrate. RED test dùng **fixture legacy** mô phỏng PO, KHÔNG đụng dogfood dev. Xác nhận lại trên bản giống-PO ở rollout (P13).
> **Đụng `spec_graph.py` chung với P4 → P4 đi trước (serialize).**

## Mapping
- **PS-13** (HIGH, BUG-F01) — `check_consistency.py:196-203` `goal_without_metric` đỏ 3 error trên BRD approved (`metric:` số ít); `strict_gate` exit 2; `record_outcome` từ chối mọi goal; `migrate_multidim_fields.py` không migrate `metric→metrics`; message không nêu nguyên nhân.
- **PS-17** (MED, BUG-M1) — `check_consistency.py:141-143` + `spec_graph.py:170-182` goal thiếu `status` (spec ghi required) không check nào bắt; `moscow` trên goal bị drop im lặng khỏi graph.
- **PS-18** (MED, CVR-F09) — `frontmatter-and-id-spec.md:40-44` artifact LLM sinh mang field ngoài spec (`title`, story.`prd`/`brd_goals`, `version` 2-part); validator im lặng; semver-lite không check format.
- **PS-21** (MED, ARC-F09) — `migrate_multidim_fields.py` mồ côi khỏi mọi routing (0 match SKILL.md/references).
- **PS-23** (LOW, BUG-F08) — `check_consistency.py:380` BrokenPipeError traceback khi consumer đóng pipe sớm (`| head` trên ~301KB), vi phạm contract ":12 Always exits 0".

## Requirements
- Functional: migrate `metric→metrics` giữ giá trị + confirm/re-approve theo GATE; message chỉ thẳng key singular; `goal_without_status` (warn→error sau migrate); lint key lạ trong goal; `moscow` không bị drop; check version format; route migrate trong SKILL.md; SIGPIPE-safe.
- Non-functional: **không silent-reverse artifact approved** — mọi sửa approved qua dry-run → hỏi PO → re-approve owner+date.

## Architecture
- **PS-13 (Q2=a) — TÁCH script riêng GATE-safe** (red-team D1/D2): KHÔNG nhồi vào `migrate_multidim_fields.py` (script đó có invariant LOCKED "empty shapes only — never a value" + "approved files NEVER written"; rename-key-giữ-value phá invariant đó). Tạo **`migrate_metric_to_metrics.py`** riêng cho rename `metric:`(str/list)→`metrics:`(list), giữ value. Flow 2 bước CỨNG:
  1. `--dry-run` (mặc định): in diff vào `confirm_required`, **ghi 0 byte** vào approved.
  2. Apply RIÊNG: lệnh `--apply --confirmed-by <PO> --date <ISO>` (2 cờ BẮT BUỘC) mới ghi; thiếu cờ → từ chối. LLM drive AskUserQuestion giữa 2 bước (Keep/Change/Hybrid theo GATE).
  - Message `goal_without_metric` nhận diện key singular: "phát hiện `metric:` (schema cũ) — chạy migrate".
- **Công tắc warn→error TƯỜNG MINH** (red-team D3): KHÔNG dùng state toàn cục. Gắn vào **marker/version field trên artifact** (vd `schema_version: 2` ở frontmatter sau migrate). Check: artifact CHƯA migrate (`metric:` hiện diện) → WARN; artifact ĐÃ migrate (`metrics:` + marker) thiếu metric → ERROR. → draft mới luôn bị ERROR đúng spec (không nới gate), chỉ legacy-chưa-migrate được WARN.
- **PS-17**: `goal_without_status` cùng cơ chế marker (WARN cho legacy chưa-migrate, ERROR cho artifact đã-schema-v2); `spec_graph` copy `moscow` vào node; lint generic "key lạ trong goal entry" (bắt cả lớp `metric`-vs-`metrics`). **Lưu ý:** `metric:` singular CHỈ rename trong scope BRD goal — KHÔNG đụng schema record khác (vd outcomes).
- **PS-18**: quyết một chiều — spec-hoá derived field (`title`/`prd`/`brd_goals`) HOẶC warn derived-only; thêm check format version (semver-lite). (Quyết trong phase, ghi DEC.)
- **PS-21**: 1 dòng route SKILL.md "spec cũ sau upgrade → đề nghị migrate (dry-run, hỏi PO)".
- **PS-23**: try/except BrokenPipeError hoặc SIGPIPE default trong helper chung cho mọi script in JSON lớn.

## Related Code Files
- Create: `.claude/skills/product-spec/scripts/migrate_metric_to_metrics.py` (script RIÊNG — KHÔNG sửa `migrate_multidim_fields.py` placeholder-only)
- Modify: `.claude/skills/product-spec/scripts/check_consistency.py` (message, goal_without_status theo marker, lint, SIGPIPE)
- Modify: `.claude/skills/product-spec/scripts/spec_graph.py` (copy moscow) — **sau P4 (serialize)**; `strict_gate.py` (đọc marker schema_version)
- Modify: `.claude/skills/product-spec/scripts/migrate_multidim_fields.py` (CHỈ thêm 1 dòng route/tham chiếu tới script mới — KHÔNG đụng invariant)
- Modify: `.claude/skills/product-spec/SKILL.md` (route migrate, PS-21), `references/frontmatter-and-id-spec.md` (PS-18 quyết + `schema_version` marker)
- Modify: REVIEW.md (5 row), EVIDENCE.md; ghi DEC cho PS-18 + DEC cho marker schema_version

## TDD — tests first (tên test mô tả hành vi, KHÔNG `test_ps13_*`)
1. `test_singular_metric_key_warns_not_errors_on_legacy`: BRD legacy fixture `metric:` singular → WARN (không exit-2); message nêu "metric: (schema cũ)". `test_migrate_dry_run_writes_zero_bytes`: dry-run → diff in ra, file approved KHÔNG đổi byte nào. `test_migrate_apply_requires_confirmed_by_and_date`: `--apply` thiếu cờ → từ chối; đủ cờ → `metric`→`metrics` giữ value + set `schema_version`.
2. `test_goal_without_status_warns_on_legacy_errors_on_schema_v2`: artifact schema_version<2 thiếu status → WARN; schema_version=2 thiếu status → ERROR. `test_moscow_preserved_in_graph_node`.
3. `test_draft_missing_metric_still_errors` (chống nới gate): artifact draft MỚI (schema_version=2) thiếu metric → ERROR đúng spec.
4. `test_unknown_field_in_frontmatter_flagged`: `title`/`prd`/`brd_goals`/`version:"0.3"` → phát hiện (warn/spec-hoá theo quyết).
5. `test_check_consistency_survives_broken_pipe`: `... | head` → KHÔNG traceback, exit 0.

## Implementation Steps
1. Viết RED tests. 2. Tạo `migrate_metric_to_metrics.py` (2 bước: dry-run-0-byte / apply-bắt-cờ). 3. Message + warn-vs-error theo marker `schema_version`. 4. goal_without_status (marker) + moscow + key-lint (scope BRD goal). 5. PS-18 quyết + DEC. 6. SIGPIPE helper chung. 7. route SKILL.md. 8. GREEN. 9. (Trên data thật khi rollout) re-approve theo GATE owner+date. 10. Tick 5 row + EVIDENCE.

## Success Criteria
- [x] Migrate `metric→metrics`: dry-run ghi 0 byte; apply CHỈ chạy với `--confirmed-by --date`; value giữ nguyên + set `schema_version`.
- [x] Legacy `metric:` → WARN; artifact schema_v2 thiếu metric/status → ERROR (draft mới KHÔNG được nới gate).
- [x] `moscow` hiện trong graph; field ngoài spec được flag (DEC ghi dưới); version format check.
- [x] `check_consistency | head` không traceback, exit 0.
- [x] migrate có route SKILL.md.

## Decisions (DEC — ghi tại audit-trail theo convention repo)
> Convention repo (EVIDENCE.md): **không có kit-level DEC-`<n>` registry**; `docs/product/decisions.md` chỉ dành **PO rulings**. Vì vậy DEC thiết kế-skill ghi tại đây + EVIDENCE Note, KHÔNG tạo `decisions.md` mới.

- **DEC-P05-1 — keying severity:** `legacy_metric_key` WARN khoá trên **sự hiện diện key `metric:` số ít** (intrinsic), KHÔNG trên marker `schema_version`. Lý do: fixture hiện hữu (metric-less-goal, valid-spec) KHÔNG cần sửa; goal thật-sự-thiếu-metric vẫn `goal_without_metric` ERROR. `goal_without_status` thì khoá trên marker `schema_version` (WARN nếu <2/absent, ERROR nếu ≥2) vì status không có tín hiệu legacy intrinsic.
- **DEC-P05-2 — tách migrator:** `metric→metrics` (di chuyển VALUE, phải chạm BRD approved) đặt ở script RIÊNG `migrate_metric_to_metrics.py` với GATE 2 bước, KHÔNG nhồi vào `migrate_multidim_fields.py` (invariant LOCKED: empty-shape-only + never-write-approved). `migrate_multidim_fields.py` giữ nguyên.
- **DEC-P05-3 — PS-18 thu hẹp scope (deferral):** chỉ ship `misplaced_parent_field` (story mang `prd`/`brd_goals`) + `bad_version_format` (cả hai node-derivable). **Hoãn:** whitelist frontmatter generic per-type + cờ derived-`title`-trong-frontmatter — brittle, sẽ false-positive trên `created`/`updated`/`version` hợp lệ.
- **DEC-P05-4 — `moscow` ngoài `content_hash`:** `moscow` KHÔNG fold vào provenance `content_hash` của P04 (tránh re-churn cache P04); theo dõi qua `CHANGED_FIELDS` (đã có "moscow").

## Review fold (3-wave + critique-challenge — sửa từ finding code-reviewer)
- **Migrator entry-scoped rename:** `_transform` rename `metric:`→`metrics:` theo TỪNG goal entry; entry đã có `metrics:` plural → bỏ qua (chống tạo key `metrics:` trùng trên goal half-migrated). Order-independent. Test: `test_migrate_skips_goal_already_on_plural_metrics`.
- **Comment-safe scalar wrap:** scalar `metric:` có inline comment (`# ...`) được tách comment, bọc value thành list, ghép lại comment SAU `]` → giữ YAML hợp lệ + giữ comment. Test: `test_migrate_preserves_inline_comment_on_scalar_metric`.
- **BOM no-op:** nhánh không-rename trả về `text` gốc (BOM nguyên), không trả bản đã strip BOM.
- **Critique-challenge MAJOR (DEC location):** finding "DEC chưa ghi vào `docs/product/decisions.md`" được **sửa hướng**, không bác — DEC ghi tại audit-trail (mục trên + EVIDENCE Note) đúng convention; `decisions.md` chỉ cho PO rulings.

## Risk Assessment
- **[red-team D1/D2] phá invariant migrate_multidim hoặc ghi approved trước duyệt.** Mitigate: script RIÊNG; dry-run ghi 0 byte; apply bắt `--confirmed-by --date`; LLM-AskUserQuestion giữa 2 bước.
- **[red-team D3] công tắc warn→error mồ côi.** Mitigate: gắn marker `schema_version` trên artifact (không state toàn cục); test draft-mới-vẫn-error.
- Rename `metric:` đụng schema khác (vd outcomes record). Mitigate: scope rename CHỈ trong BRD goal entry; test không-đụng-schema-khác.
