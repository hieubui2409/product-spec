---
phase: 3
title: "Feedback path (discover-back)"
status: done
priority: P2
effort: "0.5d"
dependencies: [2]
---

# Phase 3: Feedback path (discover-back)

## Overview

Path phản hồi của `--learn`: file text (review/feedback/insight) → `ingest_raw_inputs.py`
(read-fence sẵn) → LLM synth candidate problem/persona/risk MỚI → feed `--update` delta. Khác
`--discover` ở đích đến (update spec đang có, không seed Vision lạnh). Không auto-commit.

## Requirements

- Functional:
  - `--learn` → "phản hồi" → nhận path(s) → gọi `ingest_raw_inputs.py --root <root> --path … --scaffold`
    (tái dùng nguyên, KHÔNG sửa lõi fence).
  - Echo accepted/rejected list cho PO confirm TRƯỚC khi đọc nội dung (safety net như `--discover`).
  - LLM synth candidate (text vào → bullet ra). **KHÔNG** cluster/NLP/theme-extraction (chống gold-plating).
  - Candidate → feed `--update` delta (so spec hiện có) → mỗi thay đổi PO nhận → 1 `DEC-<n>`.
  - **GATE-NEVER-ASSUME:** không persona/problem nào commit khi PO chưa confirm từng cái.
- Non-functional: offline; bilingual; reuse-only (zero thay đổi `ingest_raw_inputs.py`).

## Architecture

```
--learn feedback ─► ingest_raw_inputs.py --scaffold (accepted/rejected) ─► PO confirm
   ─► LLM synth candidates ─► --update delta (existing spec) ─► PO confirm each ─► DEC-<n>
```

DRY: cùng script ingest với `--discover`; chỉ khác đích candidate (update vs cold Vision).

## Related Code Files

- Modify: `.claude/skills/product-spec/references/workflow-learn.md` (điền path B đầy đủ, bỏ stub)
- Reuse (no edit): `ingest_raw_inputs.py`, `decision_register.py`, `workflow-update.md`, `workflow-discover.md` (đối chiếu)
- Modify: `SKILL.md` (ghi rõ `--learn` phản hồi vs `--discover` cold-start — phân biệt 1 dòng)

## Implementation Steps (TDD)

1. **Test trước** (reuse-surface, deterministic phần script):
   - `ingest_raw_inputs.py` gọi từ feedback path giữ nguyên fence (dotfile/ext/size/traversal) — test gọi lại đảm bảo không regress (có thể reuse test sẵn của ingest).
   - Invariant: không có ghi vào `docs/product/` (persona/problem) trong bước synth (chỉ đề xuất) — assert no write trước PO confirm.
2. Điền path B trong `workflow-learn.md`: ingest → confirm → synth → `--update` → DEC.
3. SKILL.md: 1 dòng phân biệt `--learn`(post-launch, →update) vs `--discover`(cold, →Vision).

## Success Criteria

- [ ] Feedback path chạy: file → ingest (fence giữ nguyên) → candidate → `--update`.
- [ ] Test: không commit candidate nào trước PO confirm (GATE-NEVER-ASSUME invariant).
- [ ] `workflow-learn.md` path B đầy đủ; phân biệt rõ với `--discover`.
- [ ] Zero thay đổi lõi `ingest_raw_inputs.py` (DRY).

## Risk Assessment

- **Lẫn với `--discover`** → doc phân biệt rõ + đích đến khác (update vs Vision); test riêng.
- **Gold-plating clustering** → cấm tường minh trong workflow + review; giữ "text→bullet".
