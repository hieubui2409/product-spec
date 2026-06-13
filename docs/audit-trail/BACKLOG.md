# Audit-trail BACKLOG — việc hoãn từ các cycle review

Việc đã quyết "làm sau" từ các đợt audit. Khác `REVIEW.md` (ledger defect mở/đóng):
file này giữ **kế hoạch xử lý** đã được chủ kit chốt nhưng chưa khởi công. Khi bắt
đầu làm → chuyển trạng thái plan tương ứng và tick dần row trong REVIEW.md.

## Từ Cycle 3 — field audit Cleanmatic-ERP (2026-06-11)

**Trạng thái: CYCLE 3 GẦN ĐÓNG — toàn bộ wave buildable (P01–P09·P10a·P10b·P11·P12·#9) đã land; RELEASE 2.4.0 SHIPPED 2026-06-12** (tag `product-spec-v2.4.0` đã push + GitHub release live: `product-spec-2.4.0.tar.gz`+sha256). P13 rollout draft (execution thuộc chủ kit). Chỉ còn **2 defect real-transcript mở** (LIB-9 + phần outcome LIB-4) — không sửa được bằng synthetic fixture, cần phiên/transcript thật. Đã đóng: LIB-5,6 (P01) ·
LIB-7,8,10,12,13,14 + carry-in (P02) · LIB-3 + advisory Q6=a-hook + #10 product_memory lens (P03) ·
PS-14 + PSC-2 + PSC-3 (P04: content_hash provenance + scoped bundle + script-enforced persist/prose-fallback/--doctor) ·
PS-13,17,18,21,23 (P05: legacy `metric:` WARN + GATE-safe `migrate_metric_to_metrics.py` entry-scoped/comment-safe +
goal `status`/`moscow`/unknown-key lint + misplaced-parent/version-format + `emit_json` SIGPIPE-safe + migrate routing) ·
PS-15,16 (P06: fence exclude `.claude/` + cap-with-total; absent-id → `missing_id`/singleton id-pattern +
single-home `make_finding` sentinel-scrub + critique target sentinel filter) ·
CVR-F03/POX-F03 + POX-M2 (P07: đề xuất #4 — `session_staleness` warn `.session.md` ôi-thiu vs max(artifact updated) +
supersede-sweep vs DEC postdating session, decisions.md ưu tiên Q5; `open_questions` marker scan → `--status` sổ +
`--approve` gate; artifact `updated` lên node) ·
PACK-3,4,5,6 (P08: parallel-array bash-3.2 thay `declare -A` + brand→`{{BUNDLE_NAME}}` + `top_level.source` ship
recipient-variant README/CLAUDE.md & `rules: []` + release-check guard `check_rule_skill_refs` wired vào pack build +
installer gitignore `.claude/telemetry/` idempotent với newline-guard chống corruption) ·
DRY-F02/ARC-F02/CVR-F11/POX-F09 (P09: `upgrade.sh`/`.ps1` một-lệnh + planner/apply nhúng bundle `_upgrade/` +
legacy-map tường minh signature-gate/hash-diff/symlink-no-follow; sweep atomic + `trap ERR` auto-rollback; migrate dry-run-only) ·
PS-19,20,22,24,25 + LIB-11,15,16 (P12: changelog tái-lập-từ-tag + GUIDE flag-inventory + untrack state/cache +
ascii ≤120 + render_html tách 5 module/nhà-lá `_escape` + LIB-11 DEC tracked-có-chủ-đích + GUIDE dead-ref repoint +
memory-hook desc + regen footprint baseline gate-đỏ-có-sẵn).
**P10b (#6/#13/#14) · P11 (#8/#11/#15) · #9 (horizon↔PRD + persona frontmatter↔body lint + id-backfill migrator):
SHIPPED 2026-06-12 trong release 2.4.0** (plan thứ 2 `plans/260612-2142-remaining-fixwave-to-release-240/`,
8 unit TDD trên synthetic fixture → REVIEW.md P6/P7/P8 + POX-F11/F04/F10 ticked). #9 đã build (KHÔNG còn "DỜI sang
proposals" như draft P13 ghi). Partial: LIB-4 `[~]` (duration/skills xong; outcome-classify defer). **Defer bucket
real-transcript (còn mở):** LIB-9 + LIB-4-outcome — cần phiên thật, không synthetic. Plan gốc P01–P10a/P12:
`plans/260611-0050-po-field-audit-fix-waves/` (plan.md + 13 phase-*.md + reports).

**Quyết định đã chốt (đừng re-litigate):** Q1=a(upgrade.sh+legacy-sweep) · Q2=a(migrate metric→metrics
+confirm/re-approve) · Q3=a(recipient variant) · Q4=a(ship spec-validate.yml) · Q5=a(decisions ưu tiên
+staleness+supersede) · Q6=a(cả-hai: critique cache + memory hook advisory auto-enable) · Q7=a(license
notice) · Q8=d(declared_chains → file YAML on-demand in-skill, KHÔNG repoint .claude/rules).

- [~] **Wave HIGH ledger** — 12 row HIGH Cycle 3 (PACK-3/4/5 · PSC-2/3 · PS-13/14/15 · LIB-3/4/5/6): installer bash 3.2, brand claude-pack sót, bundle ship đồ dev, critique bundle nhét cả corpus, memory critique không cưỡng chế, metric→metrics phá BRD approved, provenance mù AC/BRD, fence_breach flood, hook cũ bật ngầm, telemetry duration/outcome/skills chết, test FAIL tại HEAD, 26 test ngoài CI. **11/12 ĐÓNG** (P01–P09); chỉ **phần outcome của LIB-4** còn defer (real-transcript bucket).
- [x] **Upgrade path 1.x→2.x** — landed (P09): `upgrade.sh`/`.ps1` một-lệnh (dry-run mặc định / `--apply` / `--rollback`) + planner+apply Python nhúng bundle `_upgrade/` (byte-identical, MANIFEST sha256) + legacy-map tường minh (signature-gate, hash-diff cả file-in-map, symlink no-follow). Sweep atomic all-or-nothing + `trap ERR`/try-catch auto-rollback khi install/migrate sau-sweep lỗi; migrate dry-run-only. Biến thể recipient ship từ P08 (Q3=a). → REVIEW/EVIDENCE/phase-09 (DEC-P09).
- [x] **metric→metrics migration** — landed (P05): SEPARATE GATE-safe `migrate_metric_to_metrics.py` (dry-run-0-byte / `--apply` bắt `--confirmed-by`+`--date`, rename entry-scoped + comment-safe, stamp `schema_version: 2`) + message `legacy_metric_key` WARN nêu key singular (Q2=a). `migrate_multidim_fields.py` giữ nguyên invariant placeholder-only.
- [x] **Wave MED/LOW ledger** — đã đóng P12: PS-19,20,22,24,25 + LIB-11(DEC),15,16 (docs/cleanup remainder); phần MED/LOW của cụm P10/P11 (PO-facing surfaces + product-insight) **đã đóng trong release 2.4.0** (POX-F11/F04/F10 + P6/P7/P8 build-new, ledger REVIEW.md ticked).
- [x] **15 đề xuất kiến trúc** (telemetry đầy đủ · memory/insight · self-learning · PO-first) — **ĐÃ SHIP HẾT**: #1 (P09 upgrade) · #3/#10 (P02/P03 telemetry+memory lens) · #4 (P07 staleness) · #5 (P04 cache enforce) · #2/#7/#12 (P10a) · #6/#13/#14 (P10b, release 2.4.0) · #8/#11/#15 (P11, release 2.4.0) · #9 (id-backfill, release 2.4.0). Q4–Q8 đã chốt (xem block "Quyết định đã chốt" trên).
- [~] **Thông báo PO Cleanmatic** — hiện vật rollout ĐÃ SOẠN (P13 draft, bàn giao `docs/rollout/`): checklist nâng cấp + thông điệp mời nâng cấp + notice license AGPL (DRAFT, Q7=a, cần chủ kit rà pháp lý). **Bản mời đã cập nhật mốc đích → 2.4.0 + đổi tên `po-invitation-2.4.0.md`** (rollout/ giờ đồng bộ với release 2.4.0). Phần GỬI/tag/push + PO chạy `upgrade.sh` thuộc **chủ kit** (skill không tự thao tác) — đây là việc duy nhất còn lại để đóng Cycle 3 (cùng 2 defect real-transcript LIB-9 + LIB-4-outcome).
