---
phase: 1
title: "CI net + giết test đỏ tại HEAD"
status: completed
priority: P1
effort: "0.5d"
dependencies: []
---

# Phase 01: CI net + giết test đỏ tại HEAD

> **COOKED 2026-06-11** — canonical suite `202 passed` (was `1 failed`); LIB-5/LIB-6 ticked `[x]` +
> EVIDENCE entries. Reviewed (3 waves) + critique-challenged; fixes folded: loader fail-loud on malformed
> data (ValueError), docstring corrected, PO-facing render labels relabeled off "routing docs", footprint
> baseline regenerated (+2 telemetry). **Carry-out:** action #7 (gather_all per-lens isolation) → Phase 02;
> GUIDE-EN/VI stale "routing docs" pointers → ledger **LIB-15** (Phase 12 docs-cleanup).

## Overview
HEAD đã-release đang mang 1 test ĐỎ và 26 file test tracked không CI nào chạy. Dựng lưới CI thật
(chạy đúng lệnh `CONTRIBUTING.md:69`) và sửa test đỏ — để mọi phase TDD sau có chỗ red→green chạy được.

## Mapping
- **LIB-5** (HIGH, BUG-F04) — `lens_workflow_chains.py:23-25` hardcode 2 routing doc đã xoá ở e52e077 → `test_declared_chains_parsed_from_routing_docs` FAIL (`assert 0>=1`, đã verify). **Q8=(d)** dời declared-chains vào file YAML on-demand.
- **LIB-6** (MED, DRY-F03) — 26 file test tracked (telemetry 18, hooks 4, _shared 4) ngoài mọi workflow; path filter thiếu `_shared/**`; `CONTRIBUTING.md:75` "all tests must pass" không enforce.

## Bối cảnh Q8 (đã tra git + xác minh)
2 routing doc cũ (`.claude/rules/skill-{workflow,domain}-routing.md`) do scaffold product-spec đầu tiên (`e7793b6`) tạo, bị `e52e077` (context-flow optimization) **chủ đích xoá** để giảm token always-on. Lens chỉ đọc **on-demand** (qua `analyze_telemetry.py`/`telemetry_render.py`) — KHÔNG always-on. Lỗi gốc: dữ liệu declared nằm sai chỗ (`.claude/rules/*.md` = vùng nạp-mỗi-phiên). KHÔNG có doc sống nào còn định dạng chuỗi `skill→skill` (CLAUDE.md routing là bảng "khi X → Load", 0 mũi tên). → Dời dữ liệu, không trỏ-lại.

## Requirements
- Functional: telemetry suite xanh; CI chạy telemetry+hooks+_shared mọi push/PR đụng path liên quan; declared-vs-actual giữ nguyên qua nguồn YAML.
- Non-functional: **0 token always-on** (file data in-skill, đọc on-demand); cắt coupling tới `.claude/rules/`; không tái-drift.

## Architecture
- **LIB-5 (Q8=d)**: tạo `.claude/skills/telemetry/data/skill-chains.yaml` (sở hữu bởi telemetry skill) liệt kê chuỗi `skill→skill` đã khai báo. `_routing_docs()` → `_load_declared_chains()` đọc file YAML này on-demand (KHÔNG đọc `.claude/rules`). Guard: file vắng/rỗng → raise fail-loud (không trả `[]` im lặng — chính lỗ hổng cũ). Sửa SKILL.md telemetry mô tả nguồn declared = file data này.
- **LIB-6**: workflow mới `.github/workflows/internal-test-suite.yml` chạy nguyên văn `CONTRIBUTING.md:69`; trigger path-filter gồm `_shared/**`, `.claude/hooks/**`, `.claude/skills/telemetry/**`. Vá path filter `product-spec-ci.yml` thêm `_shared/**`.
- **Manifest**: thêm `skill-chains.yaml` vào pack (ship cùng telemetry skill) — phối P8 manifest.

## Related Code Files
- Create: `.claude/skills/telemetry/data/skill-chains.yaml` (nguồn declared on-demand)
- Modify: `.claude/skills/telemetry/scripts/lens_workflow_chains.py` (`_load_declared_chains` đọc YAML + fail-loud)
- Modify: `.claude/skills/telemetry/scripts/tests/test_lens_workflow_chains.py` (assert đọc YAML + fail-loud khi vắng)
- Modify: telemetry `SKILL.md` (nguồn declared = data file), `.claude/pack.manifest.yaml` (ship data file)
- Create: `.github/workflows/internal-test-suite.yml`
- Modify: `.github/workflows/product-spec-ci.yml` (path filter `_shared/**`)
- Modify: `docs/audit-trail/REVIEW.md` (tick LIB-5, LIB-6), `docs/audit-trail/EVIDENCE.md` (2 entry)

## TDD — tests first
1. RED: `pytest .claude/skills/telemetry -q -k declared_chains` → xác nhận FAIL hiện tại (`assert 0>=1`).
2. GREEN test mới (tên mô tả hành vi, KHÔNG `test_lib5`): `test_declared_chains_loaded_from_data_file` — fixture `skill-chains.yaml` có ≥1 chuỗi → `declared` ≥1; `test_declared_chains_raises_when_data_file_missing` — file vắng → raise (không `[]`).
3. RED: CI-lint test chứng minh `internal-test-suite.yml` gọi đúng chuỗi `CONTRIBUTING.md:69` (assert string khớp), chống drift lệnh-vs-doc.

## Implementation Steps
1. Tạo `data/skill-chains.yaml` (điền chuỗi declared thật của bundle: vd product-spec → product-spec-critique → release).
2. Đổi `_routing_docs`→`_load_declared_chains` đọc YAML on-demand + fail-loud. Cập nhật test → GREEN.
3. Sửa telemetry SKILL.md + manifest ship data file.
4. Viết `internal-test-suite.yml` (checkout → `install.sh --dev` → chạy lệnh `:69`); path-filter gồm `_shared/**`.
5. Vá `product-spec-ci.yml` path filter.
6. Chạy full `CONTRIBUTING.md:69` cục bộ → 0 failed.
7. Tick REVIEW.md LIB-5/LIB-6 + 2 EVIDENCE entry.

## Success Criteria
- [x] `pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q` → 0 failed (trước: 1 failed) — **202 passed**.
- [x] declared_chains đọc từ `data/skill-chains.yaml` on-demand; raise khi file vắng + khi malformed; file không nằm `.claude/rules` (0 thêm token always-on; SKILL.md +2 token là cost label đúng, baseline đã regen).
- [x] `internal-test-suite.yml` tồn tại, lệnh khớp `CONTRIBUTING.md:69` (guard-test enforce co-presence).
- [x] `product-spec-ci.yml` trigger khi `_shared/**` đổi.

## Risk Assessment
- Data file lại drift nếu thêm skill mà quên cập nhật. Mitigate: nằm CẠNH lens (dễ thấy) + fail-loud khi rỗng + (tuỳ chọn) test "mọi skill trong manifest xuất hiện ≥1 lần trong chains".
- Workflow mới ngốn CI minutes. Mitigate: path-filter hẹp, chỉ chạy khi đụng test surface.
