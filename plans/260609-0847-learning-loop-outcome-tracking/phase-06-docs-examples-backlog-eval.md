---
phase: 6
title: "Docs+examples+backlog+eval"
status: done
priority: P2
effort: "0.5d"
dependencies: [1, 2, 3, 4, 5]
---

# Phase 6: Docs+examples+backlog+eval

## Overview

Đóng vòng: GUIDE use case PO, example acme-shop outcomes, BACKLOG E3 un-defer, eval scenario,
version bump (E5 per-skill identity).

## Requirements

- Functional:
  - `GUIDE-VI.md` + `GUIDE-EN.md`: use case `--learn` đầy đủ (số liệu + phản hồi), conversation mẫu + flag-equivalent.
  - `examples/acme-shop/docs/product/outcomes.md`: 3–4 OUT mẫu (≥1 hit, 1 miss, 1 lower-is-better latency, 1 blind-spot goal) bám goals acme sẵn (BRD-G1..G6).
  - `BACKLOG.md`: E3 `[defer]` → `[x]` SHIPPED + ghi quyết định (Light/ô dù/outcomes.md/Hybrid/no-quadrant); cập nhật telemetry boundary note (E3 không còn deferred).
  - `eval/evals.json`: scenario `--learn` (record outcome → verdict; feedback → candidate; viz scorecard render).
    **+ GATE scenario (red-team #8):** goal approved trượt → assistant surface Keep/Change/DEC, **KHÔNG auto-sửa goal** (đây là nơi GATE-NO-SILENT-REVERSAL thực sự được kiểm).
  - **E5 version:** bump `SKILL.md metadata.version` + `CHANGELOG.md` product-spec (keepachangelog) — `verify_skill_versions.py` phải pass.
- Non-functional: bilingual; docs trỏ ID/flag chính xác; CHANGELOG khớp version SKILL.md (CI gate A4).

## Related Code Files

- Modify: `.claude/skills/product-spec/GUIDE-VI.md`, `GUIDE-EN.md`
- Create: `.claude/skills/product-spec/examples/acme-shop/docs/product/outcomes.md`
- Modify: `.claude/skills/product-spec/SKILL.md` (version), `.claude/skills/product-spec/CHANGELOG.md`
- Modify: `BACKLOG.md` (E3 un-defer), `.claude/skills/telemetry/SKILL.md`/`GUIDE-VI.md` (boundary note: E3 shipped)
- Modify: `.claude/skills/product-spec/eval/evals.json`

## Implementation Steps

1. Example `outcomes.md` bám goals acme (lower-is-better dùng BRD-G4 payout-latency).
2. GUIDE VI/EN: 2 use case (`--learn` số liệu, `--learn` phản hồi) + viz scorecard.
3. BACKLOG E3 → shipped + quyết định. **Grep telemetry docs cho wording "E3"/"deferred" TRƯỚC khi sửa (red-team #10)** — nếu không khớp/không tồn tại thì bỏ edit telemetry (tránh no-op/sai), chỉ giữ BACKLOG.md flip.
4. eval scenario + chạy `eval/evals.json` smoke.
5. Bump version SKILL.md + CHANGELOG; chạy `verify_skill_versions.py` → pass.
6. Chạy full pytest product-spec → xanh.

## Success Criteria

- [ ] GUIDE VI/EN có use case `--learn` (cả 2 path) + viz.
- [ ] `examples/acme-shop/outcomes.md` parse pass + render scorecard có blind-spot + lower-is-better.
- [ ] BACKLOG E3 đánh dấu shipped + telemetry boundary cập nhật.
- [ ] eval scenario chạy; `verify_skill_versions.py` pass (version SKILL.md == CHANGELOG top).
- [ ] Full pytest product-spec xanh.

## Risk Assessment

- **Version drift fail CI (A4)** → bump cả SKILL.md + CHANGELOG cùng lúc; verify trước commit.
- **Example outcomes lệch goals acme** → bám đúng BRD-G1..G6 + metrics slug sẵn có.
- **Telemetry boundary mâu thuẫn** → cập nhật disclaimer "E3 deferred" → "E3 shipped, telemetry vẫn chỉ internal-quality".
