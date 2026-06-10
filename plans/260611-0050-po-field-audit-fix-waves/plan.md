# Plan — PO field-audit fix waves (Cleanmatic-ERP vs kit HEAD v2.3.0)

```yaml
status: pending
created: 2026-06-11
source_audit: docs/audit-trail/REVIEW.md (Cycle 3 — 2026-06-11, 31 rows mở)
decision_owner: hieubt
```

Plan rỗng có chủ đích — chủ kit quyết định **chưa fix gì**, gom toàn bộ hiện vật audit về đây
để làm sau. Backlog ngắn gọn: `docs/audit-trail/BACKLOG.md`.

## Nguồn sự thật

- **Ledger 31 defect (12 HIGH · 13 MED · 6 LOW)**: `docs/audit-trail/REVIEW.md` Cycle 3 — mọi row `[ ]` mở; fix nào land thì tick + ghi EVIDENCE.md theo convention.
- **Báo cáo tổng hợp đầy đủ** (executive summary, drift table, 36 finding chi tiết, 15 đề xuất kiến trúc xếp hạng, 8 câu hỏi Q1-Q8): `reports/from-multi-agent-po-field-audit-260611-0050-cleanmatic-erp-vs-kit-head-report.md`.
- **Hiện vật từng wave** (5 lens + 5 critic + synthesis raw) trong `reports/wave1-*`, `wave2-*`, `wave3-*`.

## Quyết định chủ kit đã chốt (2026-06-11, qua AskUserQuestion — đừng re-litigate)

- **Q1 upgrade path** → (a) Build `upgrade.sh` + legacy-sweep, rồi mời PO lên 2.3.0.
- **Q2 metric→metrics trên BRD approved** → (a) Mở rộng `migrate_multidim_fields.py` + confirm/re-approve flow theo GATE; kèm sửa message chỉ thẳng nguyên nhân.
- **Q3 bundle cho recipient** → (a) Biến thể recipient trọn gói (README/CLAUDE.md riêng, rules trung tính không `/ck:`, cân nhắc bỏ skill `release`).
- Q4-Q8 (GH Action spec-validate, session-staleness, memory enforcement, license hồi tố, declared_chains) — **chưa chốt**, hỏi lại trước khi làm.

## Phases (dự kiến — sẽ chi tiết hoá khi bắt đầu fix)

1. **Wave HIGH ledger** — PACK-3/4/5, PSC-2/3, PS-13/14/15, LIB-3/4/5/6 (đề xuất #3 #5 trong report).
2. **Upgrade path** — `upgrade.sh` + legacy-sweep + recipient-variant bundle (Q1+Q3, đề xuất #1).
3. **Wave MED/LOW ledger** — 13 MED + 6 LOW còn lại.
4. **Đề xuất kiến trúc** — #2 #4 #6 #7 (PO-facing, cỡ S) rồi #8-#15 theo nhịp; hỏi Q4-Q8 trước.

## Acceptance criteria (khi plan này active)

- Mỗi fix: row REVIEW.md tick `[x]` + entry EVIDENCE.md runnable before/after; suite pytest liên quan xanh.
- Không fix nào silent-reverse quyết định Q1-Q3 đã chốt ở trên.
