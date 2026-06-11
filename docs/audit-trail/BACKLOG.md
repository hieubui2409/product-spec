# Audit-trail BACKLOG — việc hoãn từ các cycle review

Việc đã quyết "làm sau" từ các đợt audit. Khác `REVIEW.md` (ledger defect mở/đóng):
file này giữ **kế hoạch xử lý** đã được chủ kit chốt nhưng chưa khởi công. Khi bắt
đầu làm → chuyển trạng thái plan tương ứng và tick dần row trong REVIEW.md.

## Từ Cycle 3 — field audit Cleanmatic-ERP (2026-06-11)

**Trạng thái: ĐÃ CHI TIẾT HOÁ PLAN, CHƯA KHỞI CÔNG CODE** (2026-06-11 — Q4-Q8 đã chốt, 13 phase
execute-ready + red-team 2 reviewer; chưa land fix nào, mọi row REVIEW.md vẫn `[ ]`).
Plan + hiện vật: `plans/260611-0050-po-field-audit-fix-waves/` (plan.md + 13 phase-*.md + reports).

**Quyết định đã chốt (đừng re-litigate):** Q1=a(upgrade.sh+legacy-sweep) · Q2=a(migrate metric→metrics
+confirm/re-approve) · Q3=a(recipient variant) · Q4=a(ship spec-validate.yml) · Q5=a(decisions ưu tiên
+staleness+supersede) · Q6=a(cả-hai: critique cache + memory hook advisory auto-enable) · Q7=a(license
notice) · Q8=d(declared_chains → file YAML on-demand in-skill, KHÔNG repoint .claude/rules).

- [ ] **Wave HIGH ledger** — 12 row HIGH Cycle 3 (PACK-3/4/5 · PSC-2/3 · PS-13/14/15 · LIB-3/4/5/6): installer bash 3.2, brand claude-pack sót, bundle ship đồ dev, critique bundle nhét cả corpus, memory critique không cưỡng chế, metric→metrics phá BRD approved, provenance mù AC/BRD, fence_breach flood, hook cũ bật ngầm, telemetry duration/outcome/skills chết, test FAIL tại HEAD, 26 test ngoài CI.
- [ ] **Upgrade path 1.x→2.x** — build `upgrade.sh` + legacy-sweep (Q1 đã chốt phương án a) + biến thể bundle recipient (Q3 đã chốt phương án a: README/CLAUDE.md riêng, rules trung tính, cân nhắc bỏ skill `release`).
- [ ] **metric→metrics migration** — mở rộng `migrate_multidim_fields.py` + confirm/re-approve flow theo GATE + sửa message (Q2 đã chốt phương án a).
- [ ] **Wave MED/LOW ledger** — 13 MED + 6 LOW còn lại của Cycle 3.
- [ ] **15 đề xuất kiến trúc** (telemetry đầy đủ · memory/insight · self-learning · PO-first) — bảng xếp hạng ở mục 4 của report tổng hợp; trước khi làm phải hỏi lại Q4-Q8 (GH Action spec-validate, session-staleness guard, memory enforcement, license hồi tố 1.1.0, số phận declared_chains).
- [ ] **Thông báo PO Cleanmatic** — sau khi upgrade path sẵn sàng: mời PO lên 2.3.0 (mở khoá apply-critique/fingerprint/telemetry/--learn mà PO đang thiếu) + notice license AGPL nếu Q7 chốt phương án a.
