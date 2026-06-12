# Plan — PO field-audit FIX waves (Cleanmatic-ERP v1.1.0 vs kit HEAD v2.3.0)

```yaml
status: pending
created: 2026-06-11
mode: deep + --tdd + --redteam
decision_owner: hieubt
source_audit: docs/audit-trail/REVIEW.md (Cycle 3 — 31 rows mở) + report tổng hợp
scope: TOÀN BỘ — 31 defect ledger (12 HIGH · 13 MED · 6 LOW) + 15 đề xuất kiến trúc
```

Plan này **thay** phiên bản rỗng trước (chủ kit đã chốt "fix toàn bộ" 2026-06-11). Mọi phase
chi tiết execute-ready. TDD bắt buộc mỗi phase (RED test trước → GREEN fix). `--redteam` đã chạy
trên các phase blast-radius cao (P3/P5/P9) — kết quả ở `## Risk register`.

## Nguồn sự thật (đừng đọc lại từ memory — bám file)

- **Ledger 31 defect**: `docs/audit-trail/REVIEW.md` Cycle 3 — mọi row `[ ]`; fix land → tick `[x]` + EVIDENCE.md.
- **Report tổng hợp** (36 finding, drift table, 15 đề xuất, Q1-Q8): `reports/from-multi-agent-po-field-audit-260611-0050-cleanmatic-erp-vs-kit-head-report.md`.
- **Convention EVIDENCE/REVIEW**: `docs/audit-trail/README.md` + `EVIDENCE.md` (before/after runnable, no plan/finding-code ref trong code/commit).
- **Backlog**: `docs/audit-trail/BACKLOG.md` — cập nhật trạng thái khi wave khởi công.

## Quyết định chủ kit (qua AskUserQuestion — KHÔNG re-litigate)

| Q | Chốt | Hệ quả plan |
|---|---|---|
| Q1 upgrade path | (a) `upgrade.sh` + legacy-sweep rồi mời PO lên 2.3.0 | P9 |
| Q2 metric→metrics trên BRD approved | (a) mở rộng `migrate_multidim_fields.py` + confirm/re-approve theo GATE + sửa message ngay | P5 |
| Q3 bundle recipient | (a) biến thể recipient trọn gói (README/CLAUDE.md riêng, rules trung tính, cân nhắc bỏ skill `release`) | P8 |
| Q4 spec-validate.yml CI | (a) Ship template + installer hỏi PO + khuyên xoá python-package.yml | P10 |
| Q5 session stale | (a) `decisions.md` ưu tiên khi lệch + staleness warn + supersede-sweep + open-questions sổ | P7 |
| Q6 memory enforce | (a) **Cả hai** — critique cache script-enforced + memory-hook auto-register (opt-out + config-gate) | P4 (cache) + P3 (hook) |
| Q7 license 1.1.0 | (a) Notice AGPL kèm gói nâng cấp + release-notes hiệu lực bundle <2.2.1 | P13 |
| **Q8 declared_chains** | **(d) Dời declared-chains vào file YAML on-demand sở hữu bởi telemetry skill** (KHÔNG repoint `.claude/rules`, KHÔNG always-on) | P1 |
| Phạm vi | Toàn diện, mọi phase chi tiết sâu | toàn plan |

> **Q8 lai lịch (đã tra git):** 2 routing doc cũ do `e7793b6` (scaffold product-spec đầu tiên 05-28) tạo, `e52e077` (context-flow optimization 06-09) xoá — đồ của bundle, tự thêm tự xoá. Lens chỉ đọc **on-demand** (qua `analyze_telemetry.py`/`telemetry_render.py`), KHÔNG always-on; nhưng 2 doc cũ nằm `.claude/rules/*.md` = vùng nạp-mỗi-phiên (tốn token). (d) dời dữ liệu về file YAML in-skill: giữ feature, 0 token always-on, cắt coupling gây drift.

## Ràng buộc toàn cục (mọi phase tuân)

1. **TDD**: mỗi deliverable viết RED test tái lập defect TRƯỚC, rồi GREEN fix. Phase có mục `## TDD — tests first`.
2. **EVIDENCE/REVIEW**: mỗi fix land → tick row `[x]` ở `REVIEW.md` + entry `EVIDENCE.md` (before/after chạy được). Không nhét plan-ID/finding-code vào code/comment/commit/test-name/migration-name (`review-audit-self-decision.md` rule 5 — giải thích invariant, không nguồn gốc). **Trong phase file dùng `PS-13 RED:` là MÔ TẢ hợp lệ; nhưng tên test/hàm/commit phải mô tả HÀNH VI** (vd `test_goal_singular_metric_key_warns`, KHÔNG `test_ps13_*`/`fix(PS-13)`). CI lint chặn `^def test_(ps|lib|psc|pack)\d+` + commit-msg hook chặn finding-code.
3. **GATE-NO-SILENT-REVERSAL / GATE-NEVER-ASSUME**: mọi đụng artifact `approved` (đặc biệt P5 migration) đi qua dry-run → AskUserQuestion → re-approve owner+date. Không tự lật.
4. **Không phá public contract** trừ khi phase nói rõ + đã được chấp nhận (P8 brand rename, P9 upgrade là breaking có chủ đích).
5. **Verify gate**: lệnh test chuẩn = `CONTRIBUTING.md:69` (`telemetry .claude/hooks _shared`) + suite skill liên quan; broaden khi đụng `_shared`/contract chung.
6. **Fixture-synthetic cho RED/EVIDENCE** (từ lens validate): data PO sống ở repo Cleanmatic-ERP NGOÀI cây này → mọi RED test + EVIDENCE before/after dùng **fixture synthetic in-repo** (liệt kê file fixture cụ thể trong "Related Code Files"); KHÔNG nhét số PO-thật (vd "12/15 report", "4 fact DEC-43") vào lệnh runnable. Số PO-thật chỉ verify ở **rollout P13** trên sandbox-giống-PO. Ngưỡng đo phải **cứng** (byte/boolean/count), không "<<1MB"/"an toàn"/"nhẹ". Mỗi guard/migrate có **negative test** (over-fix): vd hook-HEAD-không-bị-đè, migrate-idempotent, fresh-install-không-bị-upgrade-phá.
7. **Modularization budget** (từ lens feasibility): phase đẩy file qua ~**250 exec-LOC** phải tách module HOẶC ghi DEC ngoại lệ. Hiện đã quá: `spec_graph` 690, `visualize` 500, `decision_register` 401, `check_consistency` 400, `migrate_multidim` 322, `render_html` **1098**. `check_consistency`/`status` bị 3 phase cộng dồn → tách rule-engine sớm (P5/P6). `render_html` (P12/PS-25) **bắt buộc tách**, không DEC-né.

## Phases (13) — bảng tổng

| # | Phase | Ledger rows | Đề xuất | Deps | Prio | Effort |
|---|---|---|---|---|---|---|
| 01 | CI net + giết test đỏ tại HEAD | LIB-5, LIB-6 | — (Q8=d YAML on-demand) | — | P1 | 0.5d |
| 02 | Telemetry data-quality | LIB-4, LIB-7, LIB-8, LIB-9, LIB-10, LIB-12, LIB-13, LIB-14 | #3 | 01 | P1 | 1.5d |
| 03 | Hooks/registrar safety + memory enforce | LIB-3 | #10 (Q6 hook) | 01 | P1 | 1d |
| 04 | Critique provenance + cache enforce | PS-14, PSC-2, PSC-3 | #5 (Q6 cache) | 01 | P1 | 1.5d |
| 05 | Migration + goal/frontmatter correctness | PS-13, PS-17, PS-18, PS-21, PS-23 | — (Q2) | 01, **04** | P1 | 1.5d |
| 06 | Validation coverage + over-report | PS-15, PS-16 | #9 | 01, 05 | P2 | 1d |
| 07 | Session staleness + open-questions | — (CVR-F03/POX-F03/POX-M2) | #4 (Q5) | 01, 05, **06** | P2 | 1d |
| 08 | Packaging/installer recipient variant | PACK-3, PACK-4, PACK-5, PACK-6 | — (Q3) | 01, **03** | P1 | 1.5d |
| 09 | Upgrade-sweep (2 stage: **9a** planner-safe / **9b** atomic-swap) | — (DRY-F02/ARC-F02) | #1 (Q1) | 03, 05, 08 | P1 | 3.5-4d |
| 10 | PO-facing (2 stage: **10a** ship-critical / **10b** deferred-heavy) | — | #2(Q4),#7,#12 (10a) · #6,#13,#14 (10b) | 01, **07** (10b) | P2 | 4d |
| 11 | Product-insight + self-learning | — | #8,#11,#15 | 02, 03, **12** | P3 | 2d |
| 12 | Docs/cleanup remainder ✅ | PS-19, PS-20, PS-22, PS-24, PS-25, LIB-11, LIB-15, LIB-16 | — | 01 | P3 | 1d |
| 13 | Rollout PO Cleanmatic (**decouple**) | — | (Q7 license) | 08, 09, **10a**, 12 | P2 | 0.5d |

Bao phủ: 31/31 ledger row + 15/15 đề xuất. (Mapping chi tiết trong từng phase file.)

> **Decouple rollout (lựa chọn PO):** giữ 1 plan toàn diện NHƯNG **P13 chỉ chặn bởi value-critical** = P8 + P9 + **P10a** (#2 CI) + P12. **P10b** (#6/#13/#14) + **P11** (#8/#11/#15) làm tiếp NHƯNG **KHÔNG chặn rollout** — PO được mời lên 2.3.0 ngay khi value-critical xong. Effort thật ~**21-22d** (P9 ~3.5-4d, P10 ~4d — đã sửa từ ước lượng cũ).
> **Stage split:** **9a** = legacy-map + dry-run-planner + backup-ts + symlink-guard + hash-diff (an toàn); **9b** = staging + atomic-swap + `trap ERR` rollback + `--rollback` (rủi ro nhất — code dễ vỡ). **10a** = #2 spec-validate.yml + #7 age-beacon + #12 AC-nudge (nhẹ, KHÔNG đụng status.py cho #2/#12 → chạy sớm; #7 sau P7); **10b** = #6 visuals + #13 decision-index + #14 snapshot/restore (sau P7).

## File-ownership & serialize (chống đè song song — từ red-team)

Nhiều phase đụng CÙNG file → **single-writer, serialize qua deps** (KHÔNG chạy song song trên cùng file):

| File chung | Phase đụng | Thứ tự bắt buộc |
|---|---|---|
| `spec_graph.py` | P4 (hash AC+BRD), P5 (copy moscow) | P4 → P5 |
| `check_consistency.py` | P5, P6, P7 | P5 → P6 → P7 |
| `status.py` | P6 (aggregate), P7 (open-q), P10 (age-beacon/VCS) | P6 → P7 → P10 |
| `install.sh.template` | P3 (hooks overwrite), P8 (bash3/brand/gitignore) | P3 → P8 → P9 |
| `assemble_audit_trail.py` | P12 (truncate ascii), P11 (rollover contract) | P12 → P11 |

Deps cột trên đã mã hoá thứ tự này. Khi cook: phase sau RE-READ file trước khi sửa (file đã đổi bởi phase trước).

## Thứ tự thực thi (dependency-driven, đã serialize)

```
01 (CI net) ─┬─► 02 ──────────────┐
             ├─► 03 ─► 08 ─┐      ├─► 11 (sau 02,03,12)
             ├─► 04 ─► 05 ─┼─► 09 ────────► 13 (rollout: sau 08,09,10,12)
             │            ├─► 06 ─► 07 ─► 10 ─┘
             └─► 12 ──────┘                 │
                  └────────────► 11 ────────┘
```

- **01 đi trước tất cả**: kill test đỏ + dựng lưới CI để TDD red→green có chỗ chạy thật.
- **04 → 05**: cùng đụng `spec_graph.py`; P4 (critique provenance) đi trước.
- **05 → 06 → 07 → 10**: chuỗi cùng đụng `check_consistency.py`/`status.py`.
- **03 → 08 → 09**: cùng đụng `install.sh.template`; hooks (03) trước, installer (08) sau, upgrade (09) hợp lưu.
- **12 → 11**: cùng đụng `assemble_audit_trail.py`; cleanup truncate (12) trước rollover (11).
- **13 decouple**: rollout chỉ chặn bởi 08 + 09 + **10a** (#2 spec-validate.yml) + 12; **KHÔNG** chờ 10b/11 (làm tiếp song song/sau).

## Acceptance criteria (toàn plan)

- [ ] 31/31 row `REVIEW.md` Cycle 3 → `[x]` + 31 entry `EVIDENCE.md` before/after chạy được.
- [ ] 15/15 đề xuất kiến trúc: implement (build-new) hoặc ghi DEC nếu hoãn có lý do.
- [ ] `CONTRIBUTING.md:69` suite + mọi suite skill liên quan **xanh** (kể cả test đỏ LIB-5 hiện tại).
- [ ] CI thật chạy telemetry+hooks+_shared (LIB-6) — không còn test tracked ngoài lưới.
- [ ] Không fix nào silent-reverse Q1-Q7 đã chốt.
- [ ] `BACKLOG.md` cập nhật trạng thái mỗi wave; Cycle 3 đóng khi 31 row `[x]`.

## Risk register (từ `--redteam` 2 reviewer độc lập — chi tiết ở phase tương ứng)

| Rủi ro | Phase | Giảm thiểu |
|---|---|---|
| **[A1 CRIT] `upgrade.sh` hỏng giữa chừng để lại cài-đặt nửa-vời, không rollback** | 09 | Staging dir + atomic swap cuối; `--rollback` 1 lệnh + `trap ERR` tự gọi khi step exit≠0 |
| **[A2 HIGH] backup `product.bak` tên cố định tự ĐÈ bản gốc khi rerun idempotent** | 09 | Mọi backup mang `-<ts>` + guard không-đè + test "rerun → 2 backup riêng, gốc còn" |
| **[A3 HIGH] legacy-sweep mù symlink → xoá đích ngoài cây kit** | 09 | `is_symlink()` trước mọi xoá; chỉ gỡ link, KHÔNG follow; fixture symlink |
| **[A4 HIGH] file PO-sửa-tay TRÙNG tên legacy → xoá mù không hỏi** | 09 | Hash-diff áp cho CẢ file trong legacy-map; khác bản gốc → hỏi Keep/Change |
| **[D8 HIGH] `upgrade.sh` (bash) không gọi được AskUserQuestion cho GATE migrate** | 09/05 | Upgrade CHỈ chạy migrate `--dry-run` + in `confirm_required` + DỪNG; cấm `--apply` approved trong upgrade |
| **[D1/D2 CRIT] migrate metric→metrics phá invariant "never-write-approved/never-a-value" của `migrate_multidim_fields.py`** | 05 | TÁCH script riêng `migrate_metric_to_metrics` (KHÔNG nhồi vào placeholder-migrator); script CHỈ in diff vào `confirm_required`, ghi 0 byte; lệnh apply RIÊNG bắt buộc `--confirmed-by --date` |
| **[D3 HIGH] công tắc warn→error mồ côi → validate kẹt-warn vĩnh viễn HOẶC tự-đỏ approved cũ** | 05 | Công tắc gắn marker/version field TƯỜNG MINH trên artifact (không state toàn cục) + test downgrade KHÔNG nới gate cho draft mới |
| **[D4/D7 HIGH] marker `# config-gate` KHÔNG tồn tại → version-guard coi MỌI hook (kể cả v2.3.0) là "đời cũ"; marker giả mạo được** | 03 | Guard kiểm HÀNH VI (hook import/gọi `hook_runtime.hook_enabled`) hoặc version field MANIFEST, KHÔNG grep comment; thêm marker vào hook HEAD trước + test hook HEAD đã mang |
| **[D5 HIGH] `memory_gap_hook` có contract LOCKED blocking exit-2; "advisory auto-enable" có thể ÂM THẦM gỡ blocking của user đã opt-in** | 03 | "Advisory" CHỈ là default-mode khi auto-enable; blocking giữ nguyên cho ai opt-in; thay đổi mode = DEC, không tự nới; LIB-3 thực chất = upgrade overwrite hook 1.1.0 cũ (HEAD đã default-safe) |
| Đổi provenance hash (P4) invalidate cache critique cũ 1 lần | 04 | Ghi rõ "cache rebuild lần đầu là mong đợi" + migration note |
| Brand rename installer (P8) phá back-compat literal `claude-pack` chủ đích | 08 | Test phân biệt literal-cần-giữ (back-compat) vs literal-phải-đổi |
| **[T1] bash 3.2 không có trên CI linux (bash 5)** | 08/09 | Loại bỏ `declare -A` hẳn + e2e THẬT qua `docker run bash:3.2` (docker có sẵn), không chỉ static-lint |
| **[LIB-9] `UserPromptExpansion` SAI tên event → 0 record (root cause, không phải "chưa chứng minh")** | 02 | Sửa `→UserPromptSubmit` (event harness thật fire) hoặc gỡ; test TĨNH, KHÔNG treo "phiên live" |
| **[lens] ≥6 file đã >200 exec-LOC, plan thêm nữa (render_html 1098)** | 05/06/12 | Modularization budget ~250 (ràng buộc #7); tách rule-engine sớm; render_html bắt buộc tách |
| spec-validate.yml cần PyYAML trên runner | 10a | `pip install` 1 dòng trong workflow + smoke job |

> **Red-team coverage clean:** 31/31 ledger + 15/15 đề xuất map đúng 1 phase, 0 thiếu/0 đếm-đôi (matrix trong report reviewer). Defect tìm được: 1 BLOCKER (Q8 premise — đã giải bằng (d)), path swap P4 (đã sửa), same-file collisions (đã serialize), P13 dep (đã thêm), + cụm an toàn P3/P5/P9 (đã đưa vào risk + phase).

## Unresolved questions (cần chốt khi cook tới phase, KHÔNG chặn plan)

- **P3 (DEC cần ghi):** Q6=(a) GIỮ — auto-enable memory hook ở advisory mode. Phải ghi DEC + test `test_opted_in_blocking_not_downgraded` (KHÔNG gỡ blocking của user đã opt-in). Version-guard kiểm HÀNH VI (gọi `hook_enabled`) hoặc MANIFEST version, KHÔNG grep marker (marker không tồn tại).
- **P5 (xác nhận artifact đích):** migration nhắm artifact legacy v1.x recipient (PO repo, `metric:` singular approved) — KHÔNG phải dogfood dev (đã `metrics:` plural/draft). RED dùng fixture synthetic; verify số PO-thật ở rollout P13.
- **P9 `.ps1` parity:** ship `upgrade.ps1` wave này hay hoãn (DEC)? Phụ thuộc OS của recipient PO Cleanmatic.
- **P5 marker `schema_version`:** spec-hoá trong `frontmatter-and-id-spec.md` + whitelist khỏi lint PS-18 (P6) để tránh self-flag "key lạ".
- Q1-Q8 đã chốt (Q8=d); scope=1-plan-decouple-rollout; Q6=(a) giữ.
