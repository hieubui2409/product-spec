---
title: "Learning Loop (--learn): un-defer E3 outcome tracking + qualitative discover-back"
description: ""
status: done
priority: P2
branch: "master"
tags: []
blockedBy: []
blocks: []
created: "2026-06-09T01:51:00.170Z"
createdBy: "ck:plan"
source: skill
---

# Learning Loop (--learn): un-defer E3 outcome tracking + qualitative discover-back

## Overview

Un-defer **E3** (`BACKLOG.md:114`) + đóng cạnh học định tính, dưới 1 mode ô dù `--learn` trên
`cleanmatic:product-spec`. Tiền đề defer ("product not in market yet") đã mất — PO có insight thật
(firebase, monthly report, order data, review). TDD: khóa verdict deterministic + 2 GATE an toàn +
XSS-regression trước khi code.

**Source brainstorm:** `plans/reports/brainstorm-260609-0847-learning-loop-outcome-tracking-report.md`

**Hai vòng học, 1 mode ô dù:**
- **Định lượng** — `--learn` → số liệu → actual vs target (theo `direction: higher|lower`) →
  verdict `hit|partial|miss` (số: script tính; phi-số: PO khai = Hybrid B3) → append `OUT-<n>` vào
  `docs/product/outcomes.md`.
- **Định tính** (discover-back) — `--learn` → phản hồi → file text qua `ingest_raw_inputs.py`
  (read-fence sẵn) → LLM synth candidate problem/persona/risk mới → feed `--update` delta.

**Quyết định kiến trúc đã chốt (PO):** Light verdict · cả 2 vòng · mode trên product-spec ·
register `outcomes.md` riêng (KHÔNG đụng schema goal) · `--learn` ô dù · Hybrid verdict · KHÔNG
quadrant. Viz: `scorecard`(+blind-spot) · `outcome-trend` · `insight-gap` · `learning-map` ·
`learning`(dashboard gộp HTML-only).

**Chuẩn:** offline (chỉ file) · frontmatter SoT · script-vs-LLM split · DRY (reuse ingest+audit) ·
GATE-NEVER-ASSUME + GATE-NO-SILENT-REVERSAL · PO-facing bilingual · escape discipline (viz là XSS sink cũ).

**OUT scope:** live-connector firebase/DB · parse CSV/JSON analytics thô · BI/quadrant/clustering ·
migrate schema goal · auto-fetch.

**Mẫu code tái dùng:** `decision_register.py` (`--append-alloc`, atomic locked critical section) →
`record_outcome.py`. `visualize.py` (`VIEWS`/`HTML_ONLY_VIEWS` + dispatch) → 5 view mới.
`assemble_audit_trail.py` (join change-log/approval/decision) → +nguồn `outcomes.md` cho learning-map.
`ingest_raw_inputs.py` (read-fence) → feedback path.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Outcome register + record script](./phase-01-outcome-register-record-script.md) | Done |
| 2 | [--learn umbrella routing + GATEs](./phase-02-learn-umbrella-routing-gates.md) | Done |
| 3 | [Feedback path (discover-back)](./phase-03-feedback-path-discover-back.md) | Done |
| 4 | [Viz scorecard+gap+trend](./phase-04-viz-scorecard-gap-trend.md) | Done |
| 5 | [learning-map + dashboard (C9)](./phase-05-learning-map-dashboard-c9.md) | Done |
| 6 | [Docs+examples+backlog+eval](./phase-06-docs-examples-backlog-eval.md) | Done |

## Dependencies

- Không có plan đang mở chồng lấn. Plan cũ nhắc E3 (`260603-1817-backlog-cde-implementation`,
  `260606-2205-ha-adoption…`, `260607-1500-telemetry-insights…`) đều ĐÃ SHIPPED và chỉ tham chiếu
  E3 như boundary deferred → không chặn.
- Phase nội bộ: 1 → 2 → 3 (path A trước path B); 4,5 phụ thuộc 1 (cần `outcomes.md` + loader);
  6 cuối (docs/backlog/eval/version) phụ thuộc 1–5.
- Liên quan **E5** (per-skill release identity): version bump SKILL.md + CHANGELOG ở Phase 6.

## Red-team review (2026-06-09)

Verdict: **PROCEED-WITH-CHANGES** — đã áp dụng. Tóm tắt fix:
- **#1 BLOCKER (storage):** `outcomes.md` = per-outcome **fenced record block** (mẫu `decisions.md`, text-append, regex scan) — KHÔNG `outcomes:` list-of-dicts (tránh phá prose + mất append-only). → Phase 1.
- **#2 (ngưỡng verdict):** dùng **3-tier khớp brainstorm** hit_floor=0.9 / partial_floor=0.5 (không phải 2-tier 0.9–1.0). → Phase 1.
- **#3 (audit schema):** outcome **map vào 6 key sẵn có** của `assemble_audit_trail`, KHÔNG bump schema/thêm cột → `audit` view back-compat. → Phase 5.
- **#4 (metric slug):** validate `--metric` ∈ `goal.metrics` (chặn typo phân mảnh). → Phase 1.
- **#5 (edge):** same goal+metric+date → latest=id lớn nhất; orphan goal-ref → render "đã gỡ", không crash. → Phase 1/4.
- **#6 (viz):** actual=0=miss (≠ chưa-đo); gap clamp≥0 công thức 2 chiều. → Phase 4.
- **#7/#8/#9/#10 (minor):** cadence nudge criterion (P2); GATE thực ở eval (P2/P6); `to_heatmap_graph()` adapter (P4); grep telemetry trước khi sửa (P6).

## Validation Log

### Session 1 (2026-06-09) — 4 câu, all confirmed

Verification: skip (guard — `## Red-team review` đã có bằng chứng verify API codebase). 0 failed.

- **Q1 Ngưỡng verdict** → **config qua `preferences.py`, default 0.9/0.5** (KHÔNG defer). → đổi scope Phase 1 (wire preferences override + test bad-value). Resolves red-team open #2.
- **Q2 Metric slug lệch** → **chặn cứng + `--force`** (đã có Phase 1). Confirmed. Resolves red-team open #5(metric).
- **Q3 Nguồn target** → **LLM gợi ý từ goal title → PO confirm** (GATE-NEVER-ASSUME giữ). → thêm bước Phase 2 target-suggestion.
- **Q4 Storage model** → **per-outcome fenced block** (đã có Phase 1). Confirmed. Resolves red-team #1 BLOCKER.

### Whole-Plan Consistency Sweep
✅ Sạch (2026-06-09): 0 vết "defer/không-làm-phase-này/PO-chốt-ở-cook"; target-source nhất quán (Phase 2 + log); preferences override nhất quán (Phase 1); list-of-dicts chỉ còn ở ngữ cảnh phủ định; ngưỡng 3-tier 0.9/0.5 đồng bộ. 0 mâu thuẫn chưa giải.

### Red-team open questions — trạng thái
1. Storage → Q4 ✅ fenced block. · 2. Ngưỡng → Q1 ✅ preferences config. · 3. Audit schema → ✅ map 6 key (Phase 5). · 4. same goal+metric+date → ✅ latest=max id (Phase 1/4). · 5. metric-slug → Q2 ✅ chặn+force. · Cadence (OQ#2) → deferred, nudge trong workflow-learn.md (Phase 2 criterion).
