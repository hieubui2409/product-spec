---
phase: 8
title: "Packaging/installer recipient variant"
status: completed
priority: P1
effort: "1.5d"
dependencies: [1, 3]
---

# Phase 08: Packaging/installer recipient variant (Q3=a)

> **Serialize:** đụng `install.sh.template` chung P3 (hooks overwrite) → P3 đi trước; P8 RE-READ template trước khi sửa. Manifest cũng ship `data/skill-chains.yaml` (P1) — đồng bộ.
> **[T1] bash 3.2:** ưu tiên **loại bỏ hẳn `declare -A`** (bash-3-compatible, parallel-array ~+30 LOC). e2e THẬT qua **`docker run bash:3.2`** (docker có sẵn trên máy + CI) — không chỉ static-lint. RED: `docker run --rm -v $PWD:/x bash:3.2 bash /x/install.sh` assert chạy/fail-rõ.

## Overview
Installer chết trên macOS bash 3.2 (PO dính thật), còn ship brand "claude-pack" + link chết + danh tính
dev vào repo recipient. Sửa installer + biến thể recipient trọn gói + gitignore telemetry.

## Mapping
- **PACK-3** (HIGH, CVR-F01) — `install.sh.template:149` `declare -A SKILL_VERDICT` chết trên macOS bash 3.2 (PO cài tay; HEAD chưa sửa; không `BASH_VERSINFO` guard; 6 release vẫn nguyên).
- **PACK-4** (HIGH, DRY-F01) — `install.sh.template:2,31,348` (+`.ps1:1,34,319`, `INSTALL.md.template:72`) installer ship brand "claude-pack", hint `/cleanmatic:claude-pack` (skill không tồn tại), path troubleshooting chết; token `{{BUNDLE_NAME}}` có sẵn không dùng.
- **PACK-5** (HIGH, CVR-M1) — `pack.manifest.yaml:30-35,47-49` bundle ship README/CLAUDE.md viết cho dev-kit + 5 rules tham chiếu skill ck không ship (101 match `/ck:` trong rules PO).
- **PACK-6** (MED, ARC-M1) — `install.sh.template` không gitignore telemetry → JSONL + settings.json registrar nằm trong working tree PO → bị commit.

## Requirements
- Functional: installer chạy trên bash 3.2 (bỏ `declare -A` hoặc fail-sớm có thông báo); token thay brand; biến thể recipient README/CLAUDE.md riêng + rules trung tính (không `/ck:`); installer append `.claude/telemetry/` vào .gitignore recipient.
- Non-functional: giữ literal `claude-pack` back-compat CHỦ ĐÍCH (phân biệt với literal phải đổi).

## Architecture
- **PACK-3**: thay `declare -A` bằng cấu trúc bash-3-compatible (parallel arrays / function) HOẶC `BASH_VERSINFO` guard fail-sớm với thông báo rõ + leg e2e macOS/bash3.
- **PACK-4**: dùng `{{BUNDLE_NAME}}` token thay literal; sửa hint skill (`/cleanmatic:product-spec` ...) + path troubleshooting; áp cả `.sh`/`.ps1`/`INSTALL.md`.
- **PACK-5 (Q3=a)**: manifest có biến thể recipient — README/CLAUDE.md riêng cho recipient (danh tính sản phẩm, không "cleanmatic skills"); rules trung tính (gỡ `/ck:` refs hoặc loại khỏi manifest); cân nhắc bỏ skill `release` khỏi bundle (ghi lý do nếu giữ). Release quét "skill nhắc trong rules ship phải nằm trong bundle".
- **PACK-6**: installer append-nếu-thiếu `.claude/telemetry/` (+ settings.json registrar artifact) vào .gitignore recipient + ghi INSTALL.md.

## Related Code Files
- Modify: `.claude/skills/release/assets/templates/install.sh.template`, `install.ps1.template`, `INSTALL.md.template`
- Modify: `.claude/pack.manifest.yaml` (recipient variant top-level + rules trung tính)
- Create: recipient README/CLAUDE.md variant + rules trung tính (assets)
- Create: release-check "skill trong rules ship ⊆ bundle"
- Modify: REVIEW.md (PACK-3/4/5/6), EVIDENCE.md

## TDD — tests first
1. PACK-3 RED: chạy installer dưới bash 3.2 (container/`bash --posix` mô phỏng) → hiện FAIL `declare -A`; sau fix → chạy hoặc fail-sớm có thông báo. e2e leg macOS/bash3.
2. PACK-4 RED: build bundle → grep literal `claude-pack`/`/cleanmatic:claude-pack` trong installer → hiện match; sau fix → chỉ còn literal back-compat chủ đích (test phân biệt).
3. PACK-5 RED: bundle README/CLAUDE.md → assert KHÔNG "cleanmatic skills"/`/ck:`; release-check skill∈bundle.
4. PACK-6 RED: sau install giả lập → `.gitignore` recipient chứa `.claude/telemetry/`.

## Implementation Steps
1. Viết RED tests. 2. bash-3 compat + guard. 3. token + sửa hint/path 3 file. 4. recipient variant manifest + assets + rules trung tính. 5. gitignore append + INSTALL doc. 6. release-check skill⊆bundle. 7. GREEN. 8. Tick 4 row + EVIDENCE.

## Success Criteria
- [x] Installer chạy/fail-sớm-rõ trên bash 3.2; e2e leg xanh. (`docker bash:3.2 bash -n` + runtime verdict round-trip)
- [x] Không còn literal `claude-pack` ngoài back-compat chủ đích (test). (`test_installer_branding.py`)
- [x] Bundle recipient README/CLAUDE.md không danh tính dev/`-ck:`; release-check skill⊆bundle. (`test_bundle_recipient_variant.py` + guard wired vào `pack/cli`)
- [x] Installer gitignore telemetry recipient. (+ newline-guard chống corruption; regression test chạy block thật)

## Risk Assessment
- **[red-team] Brand rename phá literal back-compat cần giữ.** Mitigate: test phân biệt literal-giữ vs literal-đổi (whitelist back-compat).
- Bỏ skill `release` khỏi bundle có thể mất tính re-share. Mitigate: quyết + ghi lý do vào manifest (Q3 cho phép "cân nhắc").

## Decisions (DEC-P08)
- **DEC-P08-1 — release-check guard chạy ở PACK-build, không phải publish-time.** `check_rule_skill_refs` wired vào `pack/cli._load_and_validate` (gate mọi build), KHÔNG ở `release.py` publish-time, vì nó canh *thành phần recipient-bundle* (rule ship trỏ skill ngoài bundle). Hiện `rules: []` → guard là no-op (safety-net hướng tương lai). Owner: hieubt · 2026-06-12.
- **DEC-P08-2 — install.ps1 newline-guard correct-by-construction.** Không có PowerShell runtime trong CI nên leg PS1 chỉ verify tĩnh (`EndsWith("`n")` guard trước `Add-Content`); leg bash là leg runtime-proven (docker bash:3.2 + test chạy block thật). Owner: hieubt · 2026-06-12.
- **DEC-P08-3 — `top_level.source` hard E-code path-safety tại validate-time.** Traversal/absolute trong `source` bị reject sớm (E020/E021 qua `check_path_safety`) thay vì dựa WARN-and-skip ở `selection.py` — nhất quán với `_include_shared`. Owner: hieubt · 2026-06-12.
- **DEC-P08-4 — bỏ CONTRIBUTING.md khỏi recipient bundle (PO ruling 2026-06-12).** CONTRIBUTING.md là nội dung dev-kit (DCO, pull-request flow, internal pytest setup) vô dụng với end-user; AGPL-3.0 chỉ bắt buộc LICENSE + source. Gỡ khỏi manifest `extra:`, regression test `test_contributing_md_not_in_bundle` canh giữ. Owner: hieubt · 2026-06-12.
