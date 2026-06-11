# Audit-trail BACKLOG — việc hoãn từ các cycle review

Việc đã quyết "làm sau" từ các đợt audit. Khác `REVIEW.md` (ledger defect mở/đóng):
file này giữ **kế hoạch xử lý** đã được chủ kit chốt nhưng chưa khởi công. Khi bắt
đầu làm → chuyển trạng thái plan tương ứng và tick dần row trong REVIEW.md.

## Từ Cycle 3 — field audit Cleanmatic-ERP (2026-06-11)

**Trạng thái: ĐANG KHỞI CÔNG — P01·P02·P03·P04·P05·P06·P07 đã land** (2026-06-11/12). Đã đóng: LIB-5,6 (P01) ·
LIB-7,8,10,12,13,14 + carry-in (P02) · LIB-3 + advisory Q6=a-hook + #10 product_memory lens (P03) ·
PS-14 + PSC-2 + PSC-3 (P04: content_hash provenance + scoped bundle + script-enforced persist/prose-fallback/--doctor) ·
PS-13,17,18,21,23 (P05: legacy `metric:` WARN + GATE-safe `migrate_metric_to_metrics.py` entry-scoped/comment-safe +
goal `status`/`moscow`/unknown-key lint + misplaced-parent/version-format + `emit_json` SIGPIPE-safe + migrate routing) ·
PS-15,16 (P06: fence exclude `.claude/` + cap-with-total; absent-id → `missing_id`/singleton id-pattern +
single-home `make_finding` sentinel-scrub + critique target sentinel filter) ·
CVR-F03/POX-F03 + POX-M2 (P07: đề xuất #4 — `session_staleness` warn `.session.md` ôi-thiu vs max(artifact updated) +
supersede-sweep vs DEC postdating session, decisions.md ưu tiên Q5; `open_questions` marker scan → `--status` sổ +
`--approve` gate; artifact `updated` lên node).
Partial: LIB-4 `[~]` (duration/skills xong; outcome-classify defer). Defer bucket real-transcript:
LIB-9 + LIB-4-outcome. **Đề xuất #9 (horizon↔PRD + persona frontmatter↔body lint + id backfill migrator) DỜI sang cụm
proposals (hỏi PO trước khi làm).** Còn lại P08→P13. Plan + hiện vật:
`plans/260611-0050-po-field-audit-fix-waves/` (plan.md + 13 phase-*.md + reports).

**Quyết định đã chốt (đừng re-litigate):** Q1=a(upgrade.sh+legacy-sweep) · Q2=a(migrate metric→metrics
+confirm/re-approve) · Q3=a(recipient variant) · Q4=a(ship spec-validate.yml) · Q5=a(decisions ưu tiên
+staleness+supersede) · Q6=a(cả-hai: critique cache + memory hook advisory auto-enable) · Q7=a(license
notice) · Q8=d(declared_chains → file YAML on-demand in-skill, KHÔNG repoint .claude/rules).

- [ ] **Wave HIGH ledger** — 12 row HIGH Cycle 3 (PACK-3/4/5 · PSC-2/3 · PS-13/14/15 · LIB-3/4/5/6): installer bash 3.2, brand claude-pack sót, bundle ship đồ dev, critique bundle nhét cả corpus, memory critique không cưỡng chế, metric→metrics phá BRD approved, provenance mù AC/BRD, fence_breach flood, hook cũ bật ngầm, telemetry duration/outcome/skills chết, test FAIL tại HEAD, 26 test ngoài CI.
- [ ] **Upgrade path 1.x→2.x** — build `upgrade.sh` + legacy-sweep (Q1 đã chốt phương án a) + biến thể bundle recipient (Q3 đã chốt phương án a: README/CLAUDE.md riêng, rules trung tính, cân nhắc bỏ skill `release`).
- [x] **metric→metrics migration** — landed (P05): SEPARATE GATE-safe `migrate_metric_to_metrics.py` (dry-run-0-byte / `--apply` bắt `--confirmed-by`+`--date`, rename entry-scoped + comment-safe, stamp `schema_version: 2`) + message `legacy_metric_key` WARN nêu key singular (Q2=a). `migrate_multidim_fields.py` giữ nguyên invariant placeholder-only.
- [ ] **Wave MED/LOW ledger** — 13 MED + 6 LOW còn lại của Cycle 3.
- [ ] **15 đề xuất kiến trúc** (telemetry đầy đủ · memory/insight · self-learning · PO-first) — bảng xếp hạng ở mục 4 của report tổng hợp; trước khi làm phải hỏi lại Q4-Q8 (GH Action spec-validate, session-staleness guard, memory enforcement, license hồi tố 1.1.0, số phận declared_chains).
- [ ] **Thông báo PO Cleanmatic** — sau khi upgrade path sẵn sàng: mời PO lên 2.3.0 (mở khoá apply-critique/fingerprint/telemetry/--learn mà PO đang thiếu) + notice license AGPL nếu Q7 chốt phương án a.
