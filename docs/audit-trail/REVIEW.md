# REVIEW — per-cycle finding tracker

Status legend: `[ ]` open · `[x]` fixed (→ EVIDENCE entry) · `[~]` partial · `[N/A]` not a defect.

Format (one row per finding):

```
- [ ] <ID> · <CAT> · <SEV> · `file:line` — <symptom> → <fix sketch>
```

Each `[x]` row must have a matching `EVIDENCE.md` entry with runnable before/after.
No plan/finding-code refs (per `review-audit-self-decision.md`, rule 5). Size cap ≤300
lines — roll closed cycles into `## Archive`.

---

## Cycle 0 — 2026-06 (HA-adoption: observability + audit-trail + eval/CI hardening)

- [x] PSC-1 · CORRECTNESS · HIGH · `critique_inherit.py:59` — numbered-sibling findings false-merged → undercount → keep list numbers as content (see EVIDENCE).

### Red-team pass — 8 invariants attacked, each with a reproducible verdict

Each row is a real break attempt (command + observed state), not prose. All held → `[N/A]` (no defect); zero BROKEN, so no new EVIDENCE entries.

- [N/A] INV1 · telemetry∉tarball — planted populated sink + `evil-symlink.jsonl→CLAUDE.md`, ran `python -m pack`, `tar tzf` → only the test file matches "telemetry"; secret marker absent from extracted bundle; 402 members (non-vacuous).
- [N/A] INV2 · telemetry fail-open — `appendEvent` into a `chmod 500` dir AND a circular (non-serializable) record → neither throws (both swallowed); observed op unaffected.
- [N/A] INV3 · JSONL non-forgery — skill name `skillA"\n{"forged":…}\nskillB` → exactly 1 physical line / 1 parsed record / forged record absent (JSON.stringify-only path holds).
- [N/A] INV4 · ledger no-secret/no-plan-ref — grep for sk-/AKIA/PEM/ghp_/xox + `phase-NN`/`F\d`/`§` → only match is the README clause that *states* the rule (inside backticks), no real refs.
- [N/A] INV5 · eval no-false-green — exit-0-but-silent vs `stdout_contains:READY` → FAIL "missing READY"; unknown checker → hard FAIL; `_gating:llm_advisory` → SKIP(manual); gate exit 1. (Bonus: malformed assertion → loud KeyError FAIL, never silent pass.)
- [N/A] INV6 · version-gate no-false-state — `changelog_top_version` skips `[Unreleased]` + `2.0.0-rc1` → picks stable `1.4.0`; missing file → loud ChangelogError; only-Unreleased → loud error; drift test 2.3.0≠2.2.0 RED, real-tree gate green (8/8).
- [N/A] INV7 · Phase-05 litmus catchable — temporarily injected `repeat_count=3` into every `structural_findings` entry → litmus went RED ("repeat-count key leaked into a per-finding LENS input"); reverted → GREEN; no marker left in source.
- [N/A] INV8 · critique determinism — double `run_scan` on identical inputs + planted index → script-side deterministic surface (structural_findings/digest/ancestry/source_files/prior_reports/inherited/rollup) byte-identical.

## Cycle 1 — 2026-06 (release-skill rename + bundle restructure, BREAKING)

`cleanmatic:claude-pack` → `cleanmatic:release`; bundle `claude-pack-{v}.tar.gz` → `product-spec-{v}.tar.gz`;
tag `claude-pack-v*` → `product-spec-v*`; new `release.py` changelog-lifecycle engine.

### Red-team pass — release pipeline attacked, each with a reproducible verdict

All held → `[N/A]` (no defect); zero BROKEN.

- [N/A] REL-INV1 · refuse-empty-release — `lock_unreleased` on an empty `[Unreleased]` → `SystemExit "[Unreleased] is empty — nothing to release"` (unit `test_lock_unreleased_refuses_empty`).
- [N/A] REL-INV2 · refuse-duplicate-version — `release.py --release 1.4.0 --apply` (1.4.0 already locked) → `❌ [1.4.0] already exists in CHANGELOG.md`, no write.
- [N/A] REL-INV3 · push-needs-apply — `release.py --release 2.0.0 --push` (no `--apply`) → argparse `error: --push requires --apply`, exit 2 (never pushes a dry-run).
- [N/A] REL-INV4 · dry-run-no-write — full dry-run suite leaves `CHANGELOG.md` with 0 `## [2.0.0]` headings + manifest still `2.0.0` (no accidental write off the read-only/preview paths).
- [N/A] REL-INV5 · version-axis-no-drift — `release.py --release X --apply` writes the changelog lock AND the manifest version in one action; the A4 gate (`test_bundle_changelog_top_matches_manifest_version`) ties root `/CHANGELOG.md` top == manifest `version:` so the two axes cannot silently diverge.
- [N/A] REL-INV6 · REPO-path-correct — `release.py` `REPO=parents[4]` resolves to the dir holding `.claude/pack.manifest.yaml` + `CHANGELOG.md` (unit `test_repo_resolves_to_repo_root`); the plan's `parents[3]` guess was wrong and was rejected empirically.
- [N/A] REL-INV7 · telemetry∉tarball after rename — real `python -m pack` build of `product-spec-2.0.0.tar.gz`: `tar tzf | grep -i telemetry` matches only the test-file *name*; no `.claude/telemetry/` dir, no telemetry hooks; no `claude-pack` path anywhere in the bundle.
- [N/A] REL-INV8 · build-determinism after rename — two consecutive `python -m pack` builds → byte-identical sha256 (`90910ffe…`).
- [N/A] REL-INV9 · CI body-fail-closed — if the owner pushes a `product-spec-vX` tag WITHOUT first locking `[X]` in the changelog, `release.yml`'s `release.py --extract X` step raises (no `[X]` section) → the release step fails rather than publishing a release with a wrong/empty body (safe-fail, by design).

## Cycle 2 — 2026-06-09 (learning loop `--learn`: outcome register + viz + discover-back)

New `--learn` umbrella mode: `record_outcome.py` (Outcome Register `OUT-<n>`), `load_outcomes.py`,
`render_outcomes.py` (scorecard / insight-gap / outcome-trend / learning-map / learning), preferences
verdict floors, `assemble_audit_trail` outcomes source. Implementation review (Wave 1) + regression.

### Findings

- [x] PS-1 · CONSISTENCY · LOW · `assemble_audit_trail.py` (outcomes loop) — comment claimed the
  learning-map "filters these outcome rows back out"; it KEEPS them as the map's source nodes. Comment
  corrected (no behavior change). → EVIDENCE PS-1.
- [x] PS-2 · CLEANUP · LOW · `record_outcome.py` (254 exec) + `render_outcomes.py` (211 exec) over the
  200-LOC guideline — measured by EXECUTABLE lines (not docstring-inflated), so a real overage. Split
  along seams: pure verdict core → `outcome_verdict.py`; Phase-5 learning views → `render_learning.py`.
  Now record_outcome 207 · render_outcomes 147 · outcome_verdict 51 · render_learning 67. → EVIDENCE PS-2.
- [x] PS-3 · CORRECTNESS · LOW · `_num` accepted `inf`/`nan` as numeric → a ratio of inf/nan could reach
  `compute_verdict`. Fixed: `_num` rejects non-finite → None → routes to the Hybrid (PO-asserted) path.
  → EVIDENCE PS-3.
- [x] PS-4 · CLEANUP · LOW · `load_outcomes.py` caught bare `except Exception` for a broken `brd.md`.
  Narrowed to `except OutcomeError` (the only thing `load_goals` raises) so a genuine programming error
  surfaces instead of being swallowed. → EVIDENCE PS-4.

_Adversarial probes that held (verdict determinism/direction, hybrid gating, bad-floor rejection,
append-only, goal-schema-untouched, XSS-fail-closed, fence/heading injection, audit back-compat) are
covered by the test suite (`test_record_outcome.py`, `test_outcome_viz.py`) — they are NOT logged as
ledger rows (this ledger holds defects, not passing checks)._

### Wave 2 — regression sweep (cycle 1 of 3)

- [x] PS-5 · CORRECTNESS · MED · `preferences.py` `--set` float branch — a non-numeric/out-of-range
  float floor saved with exit 0, then broke the NEXT `--learn` run (delayed, disconnected failure).
  Now rejected at write time (exit 2, nothing written) + range-checked [0,1], mirroring the enum path.
  Regression-tested. → EVIDENCE PS-5.
- [x] PS-6 · CLEANUP · LOW · unused imports — `load_outcomes.py` (`Path`), `render_outcomes.py`
  (`Optional`), `assemble_audit_trail.py` (`yaml`, pre-existing), `preferences.py` (`contextlib`, no
  longer needed after PS-5). pyflakes clean. → EVIDENCE PS-6.
- [x] PS-8 · CONSISTENCY · LOW · `visualize.py` module docstring said "14 views / 3 formats / 9 graph
  views" — now 20 views / 4 formats; refreshed + lists the audit/outcome/learning view groups.
- [x] PS-9 · CONSISTENCY · NIT · `preferences.py` comments referenced `record_outcome._load_floors`
  (renamed + moved by PS-2) — updated to `outcome_verdict.load_floors`.
- [x] PS-7 · DRY · MED · `record_outcome.py` ↔ `decision_register.py` — `_RECORD_RE`, fence/heading
  injection escape, `_register_lock`, id-scan were byte-identical twins. Extracted to a shared
  `register_store.py` (RECORD_RE / escape_injection / register_lock / scan_record_ids); both registers
  import it, each keeps only its own specifics. Byte-identical behavior (pure de-dup). **decision_register
  (critical/old feature) retested + green.** → EVIDENCE PS-7.
- [x] PS-10 · CORRECTNESS · MINOR · `record_outcome.py` `--measured-on` accepted any string (exit 0) vs
  the typed-ISO-date spec → could sort/group wrong downstream. Now validated via `dt.date.fromisoformat`,
  rejects non-ISO (nothing written). Regression-tested. → EVIDENCE PS-10.
- [x] PS-11 · CLEANUP(test-gap) · LOW · `learning_map_ascii` (production-reachable) was untested + no
  dispatcher tests for the 5 learning views. Added a direct ascii test + a dispatcher test across all 5
  views/formats. → EVIDENCE PS-11.
- [x] PS-12 · CLEANUP(test-gap) · NIT · added a direct OUT-side note-injection test (fake `---` fence +
  `## OUT-` heading in a `--note` → neutralized; `parse_outcomes` returns only the real row, phantom not
  counted in id alloc). Cycle-3 NIT; closes the one gap in the shared `escape_injection` coverage.
- NITs accepted (not defects): `BACKLOG.md:17,19` "E3 deferred" sits in a dated 2026-06-03 PO-decision
  snapshot (append-only history; line 20 + the E3 entry carry the live "shipped" status);
  `SKILL.md:55` `--format` row omits the audit-only `md` (pre-existing, out of `--learn` scope).

**Wave 2 cycle 2 → DONE_WITH_CONCERNS** (found PS-5 MAJOR + PS-10/11, all fixed). **Cycle 3 → CLEAN**:
PS-7 refactor verified behavior-preserving (escape order/regexes, lock semantics, id-scan byte-identical
to the old inline copies); decision_register/apply-critique/audit all green; pyflakes clean; i18n
symmetric; docs current. Final suite: **656 passed**. No open defects.

## Cycle 3 — 2026-06-11 (field audit: Cleanmatic-ERP PO usage vs kit HEAD)

Nguồn: repo PO Cleanmatic/Cleanmatic-ERP chạy bundle claude-pack v1.1.0 (347/347 file nguyên vẹn) đối chiếu kit HEAD v2.3.0; 5 lens độc lập + 5 critic phản biện trong sandbox, tổng hợp 2026-06-11. Chưa fix gì — mọi row mở.

- [ ] PS-13 · CORRECTNESS · HIGH · `product-spec/scripts/check_consistency.py:196-203` — check `goal_without_metric` mới đỏ 3 error trên BRD approved viết bằng skill cũ (`metric:` số ít), `strict_gate` exit 2, `record_outcome` từ chối mọi goal; `migrate_multidim_fields.py` không migrate `metric→metrics`, message không nêu nguyên nhân → nhận diện key singular trong message + mở rộng migrate (confirm-flow vì artifact approved) + note nâng cấp
- [ ] PS-14 · CORRECTNESS · HIGH · `product-spec/scripts/spec_graph.py:124,466` — provenance hash chỉ phủ body, `CHANGED_FIELDS` không có `acceptance_criteria`, BRD không có node trong body_hash map → sửa AC-only/BRD: critique fast-path reuse kết quả cũ sai → đưa AC + node/hash BRD vào provenance + test "mọi artifact có mặt trong map"
- [ ] PS-15 · CORRECTNESS · HIGH · `product-spec/scripts/check_fence.py:36` + `status.py:194` — fence_breach không cap/exclude: cây sau-cài/chưa-commit → 2.258 cảnh báo / 1,09MB JSON (đếm cả `.claude/` kit tự cài), trái docstring "never an over-report" → exclude `.claude/` + aggregate theo thư mục + cap top-N kèm tổng đếm
- [ ] PS-16 · CORRECTNESS · MED · `check_consistency.py:177` + `spec_graph.py:597-602` — sentinel `<missing-id>` lộ vào finding PO-facing và `target_ids`/`source_files` của bundle critique; type product/vision thiếu `id:` không bị flag riêng → finding `missing_id` nêu tên file + formatter thay sentinel + lọc sentinel khỏi bundle + template `id: PRODUCT`
- [ ] PS-17 · CORRECTNESS · MED · `check_consistency.py:141-143` + `spec_graph.py:170-182` — goal thiếu `status` (spec ghi required) không check nào bắt; `moscow` trên goal bị drop im lặng khỏi graph → thêm `goal_without_status` (warn trước, error sau migrate) + lint key lạ trong goal entry
- [ ] PS-18 · CONSISTENCY · MED · `references/frontmatter-and-id-spec.md:40-44` — artifact LLM sinh mang field ngoài spec (`title`, story.`prd`/`brd_goals`, `version` 2-part) — validator im lặng, semver-lite không được check format → spec-hoá hoặc warn derived-field + check version format
- [ ] PS-19 · CONSISTENCY · MED · `product-spec/CHANGELOG.md:18` + root `CHANGELOG.md:30` — claim "SKILL.md 6090→5371 (−11.8%)" không tái lập từ lịch sử git (thực 5758→5371 = −6.7%; 6090 chưa từng tồn tại ở commit nào) → sửa số so-với-release + quy ước số changelog phải tái lập từ 2 tag
- [ ] PS-20 · CONSISTENCY · MED · `product-spec/GUIDE-EN.md`/`GUIDE-VI.md` — thiếu hẳn `--voice` (+5 flag con) và `--compact-mode` so với SKILL.md; GUIDE critique thiếu alias `--gentle`/`--savage` → bổ sung mục + test flag-inventory SKILL↔GUIDE
- [ ] PS-21 · CONSISTENCY · MED · `product-spec/SKILL.md` — `migrate_multidim_fields.py` mồ côi khỏi mọi routing (0 match SKILL.md/references) → spec v1 sau upgrade ăn warn-noise không ai chỉ đường → thêm route "spec cũ → đề nghị migrate (dry-run, hỏi PO)"
- [ ] PS-22 · CLEANUP · MED · `docs/product/.session.md` + `.memory/*` + `visuals/.snapshots/*` (tracked, commit 58e2d05) — state/cache per-run của dogfood bị commit → diff vô nghĩa mỗi lần dogfood lại → untrack + gitignore, giữ artifact prose
- [ ] PS-23 · CORRECTNESS · LOW · `check_consistency.py:380` — BrokenPipeError traceback khi consumer đóng pipe sớm (`| head` trên output ~301KB), vi phạm contract ":12 Always exits 0" → try/except BrokenPipeError hoặc SIGPIPE default cho mọi script in JSON lớn
- [ ] PS-24 · CONSISTENCY · LOW · `assemble_audit_trail.py` (ascii) — bảng `--viz audit` dòng dài nhất 368 ký tự trên data PO, vô dụng ở terminal 80-120 cột dù cam kết "ascii downgraded, never removed" → truncate cell theo budget cột ~120, giữ full text cho `--format md`
- [ ] PS-25 · CLEANUP · LOW · `render_html.py` — 805 exec-LOC (~4× guideline 200 từng viện dẫn ở PS-2) → tách template tĩnh ra module/asset hoặc ghi ngoại lệ có lý do
- [ ] PSC-2 · CORRECTNESS · HIGH · `product-spec-critique/scripts/critique_signals.py:28` + `critique_bundle.py:117` — `source_files` nhét toàn bộ corpus bất kể scope (PRD đơn: 148 key/700KB, 123 key off-target; all: 1,24MB × 4 lens song song) → lọc theo `target_ids ∪ ancestry ∪ digest`, descendants dùng `verbosity: struct`
- [ ] PSC-3 · CORRECTNESS · HIGH · `references/workflow-critique.md` + `parse_critique_report.py` — ghi lens-cache/`lens_findings_hash`/index/state là bước LLM-flow không cưỡng chế → trên data PO 12/15 report parse ra `findings: 0`, state kẹt pass-1, fingerprint 0/20 entry → script-enforce ghi cache sau mỗi report + fallback bóc heading prose + `--doctor` đối chiếu state↔thư mục critique
- [ ] PACK-3 · CORRECTNESS · HIGH · `release/assets/templates/install.sh.template:149` — `declare -A` chết trên macOS bash 3.2 (PO dính thật, phải cài tay — change-log PO :711-718; không `BASH_VERSINFO` guard; 6 release sau vẫn nguyên) → cấu trúc bash-3-compatible hoặc fail sớm có thông báo rõ + leg e2e macOS/bash3
- [ ] PACK-4 · CORRECTNESS · HIGH · `install.sh.template:2,31,348` (+`install.ps1.template:1,34,319`, `INSTALL.md.template:72`) — installer ship vẫn brand "claude-pack", hint `/cleanmatic:claude-pack` (skill không tồn tại), trỏ troubleshooting path chết; token `{{BUNDLE_NAME}}` có sẵn không dùng → thay token + sửa path + test "không còn literal claude-pack"
- [ ] PACK-5 · CONSISTENCY · HIGH · `pack.manifest.yaml:30-35,47-49` — bundle ship README/CLAUDE.md viết cho dev-kit (repo PO trên GitHub tự xưng "cleanmatic skills", quy trình release trỏ file ma trong context always-on) + 5 rules tham chiếu skill ck không ship (`cook`/`/ck:preview`/`/ck:team`; 101 match `/ck:` trong rules PO) → biến thể recipient cho top-level docs + rules trung tính hoặc bỏ khỏi manifest
- [ ] PACK-6 · ENV · MED · `install.sh.template` (không có bước gitignore) — sau cài/upgrade, telemetry JSONL + `settings.json` registrar tạo nằm trong working tree PO → bị commit lên GitHub (PO .gitignore không có telemetry) → installer append-nếu-thiếu `.claude/telemetry/` vào .gitignore recipient + ghi vào INSTALL.md
- [ ] LIB-3 · CORRECTNESS · HIGH · `hooks/register_telemetry_hooks.py:113-116` — registrar wire enforcement hook vô điều kiện theo basename; upgrade default (install.sh.template:285 SKIP-existing) giữ `memory_gap_hook.py` đời 1.1.0 không config-gate → blocking hook (exit 2) bật ngầm cho PO chưa từng opt-in → version-guard trước khi wire (kiểm marker config-gate trong file đích) + coi hooks là code kit (overwrite-with-backup)
- [ ] LIB-4 · CORRECTNESS · HIGH · `hooks/emit_session_summary.py:60-68,115` — `first_timestamp()` chỉ đọc dòng đầu transcript (record đầu không có ts) → 43/43 session `duration_s:0`; 46/46 subagent `outcome:unknown`; 41/43 `skills:[]` → sửa parse start-ts (scan tới record có ts) + classify outcome từ tail protocol + e2e fixture từng sink
- [ ] LIB-5 · CORRECTNESS · HIGH · `telemetry/scripts/lens_workflow_chains.py:23-25` — hardcode 2 routing doc đã bị xoá ở e52e077 → test tracked FAIL ngay HEAD (1 failed/108), `declared_chains` thành dead code (workflow lens vĩnh viễn 0 chuỗi) → trỏ nguồn routing còn sống hoặc gỡ feature + test
- [ ] LIB-6 · CONSISTENCY · HIGH · `.github/workflows/` (6 workflow) — 26 file test tracked (telemetry 18, hooks 4, _shared 4) không CI nào chạy; path filter thiếu `_shared/**`; CONTRIBUTING.md:75 "all tests must pass" không được enforce → thêm workflow chạy đúng lệnh CONTRIBUTING.md:69 + vá path filter
- [ ] LIB-7 · CORRECTNESS · MED · `hooks/hook_runtime.py:41` + `track_script_execution.py:57-59` — SCRIPT_RE substring-match: grep/ls/glob nhắc tới script cũng thành "script run" (10 record glob literal), validate-proxy đếm grep `check_*` như validate PASS → siết matcher về dạng thực-thi (đầu lệnh/sau interpreter) + fixture từ record thật
- [ ] LIB-8 · CONSISTENCY · MED · `hooks/track_script_execution.py:61-68` — biến `session` đã tính nhưng record không ghi (414/414 record thiếu key, 3 sink kia đều có) → hook-telemetry không join được phiên↔script → thêm `"session"` vào record + cập nhật tests
- [ ] LIB-9 · CORRECTNESS · MED · `hooks/register_telemetry_hooks.py:107-108` — kênh UserPromptExpansion 0 record sau nhiều ngày (7/7 invocation đều PreToolUse:Skill) — kênh slash-command chính của PO có thể mù → e2e 1 phiên thật assert record; nếu event chết → capture qua transcript + xoá registration
- [ ] LIB-10 · CONSISTENCY · MED · `CLAUDE.md:4,8-13` — routing always-on tự nhận "three PO-facing skills", bảng 3 hàng — telemetry (PO-facing, bundle ship 4 skill) vô hình; bản trước-slim có nhắc → thêm hàng telemetry + sửa "three"→"four" + nudge nhẹ trong `--status`
- [ ] LIB-11 · CLEANUP · MED · `.claude/agents/` (13 file ck, commit a967688) + 2 `.env.example` + `schemas/ck-config.schema.json` (0 tham chiếu) — rác ck-local đã commit vào repo nguồn ship → untrack hoặc ghi DEC "tracked có chủ đích, không ship"
- [ ] LIB-12 · CONSISTENCY · LOW · `telemetry/scripts/lens_validate_proxy.py:82` + `telemetry_render.py:182` — reason tiếng Anh hardcode chen giữa output VI (bản dịch `val_na` có sẵn không dùng) → lens trả `reason_code`, render map label localize
- [ ] LIB-13 · CONSISTENCY · LOW · `docs/audit-trail/telemetry-readback.md` — thiếu sink `.logs/hook-crashes.log` + config gate `product-spec-hooks.json` (đồ mới 2.3.0); README.md:26 gán memory-gap hook nhầm vào critique → thêm hàng sink + sửa attribution
- [ ] LIB-14 · CLEANUP · LOW · `hooks/__tests__/test_telemetry_hooks.py:133,194` + `telemetry/.../test_telemetry_paths.py:56,62` — fixture còn dùng id "claude-pack" → đổi sang id trung tính

- Field-observations (không lên row): PO đứng sau HEAD 9 release (lỗi thời ngay ngày cài); tự chế GH Actions fail vĩnh viễn vì thèm validate-on-push; `.session.md` đóng băng 06-02 chứa 4 fact bị supersede — đúng nguồn GATE-NEVER-ASSUME cho phép assume; visuals đóng băng 06-03 (56/102 story) + 88 file backup tracked; critique marathon 13 report/ngày trên bản không fingerprint.
- Khoảng trống kiến trúc không-phải-defect: upgrade-path 1.x→2.x (cài đặt Frankenstein), version-beacon, artifact-events, self-learning/feedback-loop về dev, memory-lens hợp nhất, rotation change-log, snapshot/restore — 15 đề xuất xếp hạng trong report.
- Phản biện: 0/58 finding lens bị REFUTED toàn phần; 13 ADJUSTED (2 đổi severity: ARC-F02 Critical→High, POX-F07 Medium→High); 13 finding do critic bổ sung được nhận vào.
- Chi tiết: plans/260611-0050-po-field-audit-fix-waves/ (plan + reports đầy đủ các wave)
