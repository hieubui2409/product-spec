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

- [x] PS-13 · CORRECTNESS · HIGH · `product-spec/scripts/check_consistency.py:196-203` — check `goal_without_metric` mới đỏ 3 error trên BRD approved viết bằng skill cũ (`metric:` số ít), `strict_gate` exit 2, `record_outcome` từ chối mọi goal; `migrate_multidim_fields.py` không migrate `metric→metrics`, message không nêu nguyên nhân → nhận diện key singular trong message + mở rộng migrate (confirm-flow vì artifact approved) + note nâng cấp
- [x] PS-14 · CORRECTNESS · HIGH · `product-spec/scripts/spec_graph.py:124,466` — provenance hash chỉ phủ body, `CHANGED_FIELDS` không có `acceptance_criteria`, BRD không có node trong body_hash map → sửa AC-only/BRD: critique fast-path reuse kết quả cũ sai → đưa AC + node/hash BRD vào provenance + test "mọi artifact có mặt trong map"
- [x] PS-15 · CORRECTNESS · HIGH · `product-spec/scripts/check_fence.py:36` + `status.py:194` — fence_breach không cap/exclude: cây sau-cài/chưa-commit → 2.258 cảnh báo / 1,09MB JSON (đếm cả `.claude/` kit tự cài), trái docstring "never an over-report" → exclude `.claude/` + aggregate theo thư mục + cap top-N kèm tổng đếm
- [x] PS-16 · CORRECTNESS · MED · `check_consistency.py:177` + `spec_graph.py:597-602` — sentinel `<missing-id>` lộ vào finding PO-facing và `target_ids`/`source_files` của bundle critique; type product/vision thiếu `id:` không bị flag riêng → finding `missing_id` nêu tên file + formatter thay sentinel + lọc sentinel khỏi bundle + template `id: PRODUCT`
- [x] PS-17 · CORRECTNESS · MED · `check_consistency.py:141-143` + `spec_graph.py:170-182` — goal thiếu `status` (spec ghi required) không check nào bắt; `moscow` trên goal bị drop im lặng khỏi graph → thêm `goal_without_status` (warn trước, error sau migrate) + lint key lạ trong goal entry
- [x] PS-18 · CONSISTENCY · MED · `references/frontmatter-and-id-spec.md:40-44` — artifact LLM sinh mang field ngoài spec (`title`, story.`prd`/`brd_goals`, `version` 2-part) — validator im lặng, semver-lite không được check format → spec-hoá hoặc warn derived-field + check version format
- [x] PS-19 · CONSISTENCY · MED · `product-spec/CHANGELOG.md:18` + root `CHANGELOG.md:30` — claim "SKILL.md 6090→5371 (−11.8%)" không tái lập từ lịch sử git (thực 5758→5371 = −6.7%; 6090 chưa từng tồn tại ở commit nào) → sửa số so-với-release + quy ước số changelog phải tái lập từ 2 tag
- [x] PS-20 · CONSISTENCY · MED · `product-spec/GUIDE-EN.md`/`GUIDE-VI.md` — thiếu hẳn `--voice` (+5 flag con) và `--compact-mode` so với SKILL.md; GUIDE critique thiếu alias `--gentle`/`--savage` → bổ sung mục + test flag-inventory SKILL↔GUIDE
- [x] PS-21 · CONSISTENCY · MED · `product-spec/SKILL.md` — `migrate_multidim_fields.py` mồ côi khỏi mọi routing (0 match SKILL.md/references) → spec v1 sau upgrade ăn warn-noise không ai chỉ đường → thêm route "spec cũ → đề nghị migrate (dry-run, hỏi PO)"
- [x] PS-22 · CLEANUP · MED · `docs/product/.session.md` + `.memory/*` + `visuals/.snapshots/*` (tracked, commit 58e2d05) — state/cache per-run của dogfood bị commit → diff vô nghĩa mỗi lần dogfood lại → untrack + gitignore, giữ artifact prose
- [x] PS-23 · CORRECTNESS · LOW · `check_consistency.py:380` — BrokenPipeError traceback khi consumer đóng pipe sớm (`| head` trên output ~301KB), vi phạm contract ":12 Always exits 0" → try/except BrokenPipeError hoặc SIGPIPE default cho mọi script in JSON lớn
- [x] PS-24 · CONSISTENCY · LOW · `assemble_audit_trail.py` (ascii) — bảng `--viz audit` dòng dài nhất 368 ký tự trên data PO, vô dụng ở terminal 80-120 cột dù cam kết "ascii downgraded, never removed" → truncate cell theo budget cột ~120, giữ full text cho `--format md`
- [x] PS-25 · CLEANUP · LOW · `render_html.py` — 805 exec-LOC (~4× guideline 200 từng viện dẫn ở PS-2) → tách template tĩnh ra module/asset hoặc ghi ngoại lệ có lý do
- [x] PSC-2 · CORRECTNESS · HIGH · `product-spec-critique/scripts/critique_signals.py:28` + `critique_bundle.py:117` — `source_files` nhét toàn bộ corpus bất kể scope (PRD đơn: 148 key/700KB, 123 key off-target; all: 1,24MB × 4 lens song song) → lọc theo `target_ids ∪ ancestry ∪ digest`, descendants dùng `verbosity: struct`
- [x] PSC-3 · CORRECTNESS · HIGH · `references/workflow-critique.md` + `parse_critique_report.py` — ghi lens-cache/`lens_findings_hash`/index/state là bước LLM-flow không cưỡng chế → trên data PO 12/15 report parse ra `findings: 0`, state kẹt pass-1, fingerprint 0/20 entry → script-enforce ghi cache sau mỗi report + fallback bóc heading prose + `--doctor` đối chiếu state↔thư mục critique
- [x] PACK-3 · CORRECTNESS · HIGH · `release/assets/templates/install.sh.template:149` — `declare -A` chết trên macOS bash 3.2 (PO dính thật, phải cài tay — change-log PO :711-718; không `BASH_VERSINFO` guard; 6 release sau vẫn nguyên) → cấu trúc bash-3-compatible hoặc fail sớm có thông báo rõ + leg e2e macOS/bash3. **ĐÃ LÀM (P08):** parallel-array `SKILL_VERDICT_SLUGS`/`_VALUES` + `_set`/`_get_skill_verdict` thay `declare -A`; verified `docker bash:3.2 bash -n` + runtime round-trip (`test_install_sh_skill_verdict_helpers_roundtrip`) (→ EVIDENCE P08).
- [x] PACK-4 · CORRECTNESS · HIGH · `install.sh.template:2,31,348` (+`install.ps1.template:1,34,319`, `INSTALL.md.template:72`) — installer ship vẫn brand "claude-pack", hint `/cleanmatic:claude-pack` (skill không tồn tại), trỏ troubleshooting path chết; token `{{BUNDLE_NAME}}` có sẵn không dùng → thay token + sửa path + test "không còn literal claude-pack". **ĐÃ LÀM (P08):** literal brand route qua `{{BUNDLE_NAME}}`, back-compat literal có chủ đích được test branding canh giữ (`test_installer_branding.py`) (→ EVIDENCE P08).
- [x] PACK-5 · CONSISTENCY · HIGH · `pack.manifest.yaml:30-35,47-49` — bundle ship README/CLAUDE.md viết cho dev-kit (repo PO trên GitHub tự xưng "cleanmatic skills", quy trình release trỏ file ma trong context always-on) + 5 rules tham chiếu skill ck không ship (`cook`/`/ck:preview`/`/ck:team`; 101 match `/ck:` trong rules PO) → biến thể recipient cho top-level docs + rules trung tính hoặc bỏ khỏi manifest. **ĐÃ LÀM (P08):** `top_level.source` ship README/CLAUDE.md biến thể recipient từ `assets/recipient/` (fallback repo-root) + `rules: []` bỏ dev rules; release-check guard `check_rule_skill_refs` wired vào `pack/cli._load_and_validate` fail build nếu rule ship trỏ skill ngoài bundle (→ EVIDENCE P08).
- [x] PACK-6 · ENV · MED · `install.sh.template` (không có bước gitignore) — sau cài/upgrade, telemetry JSONL + `settings.json` registrar tạo nằm trong working tree PO → bị commit lên GitHub (PO .gitignore không có telemetry) → installer append-nếu-thiếu `.claude/telemetry/` vào .gitignore recipient + ghi vào INSTALL.md. **ĐÃ LÀM (P08):** append idempotent (grep-guard) cả install.sh/install.ps1 + ghi INSTALL.md; **sửa thêm** corruption khi file `.gitignore` không có newline cuối (chèn separator trước khi append) — regression test chạy block THẬT trên fixture no-trailing-newline (→ EVIDENCE P08).
- [x] LIB-3 · CORRECTNESS · HIGH · `hooks/register_telemetry_hooks.py:113-116` — registrar wire enforcement hook vô điều kiện theo basename; upgrade default (install.sh.template:285 SKIP-existing) giữ `memory_gap_hook.py` đời 1.1.0 không config-gate → blocking hook (exit 2) bật ngầm cho PO chưa từng opt-in. **ĐÃ LÀM:** marker `# config-gate` KHÔNG tồn tại (red-team D4/D7) → guard kiểm **HÀNH VI** (`grep hook_enabled`) đặt ở **installer** (đúng home ghi file hook): hook không-gate → overwrite-with-backup; hook gate-aware PO-sửa → `[CONFLICT]` giữ (không đè mù). Kèm **advisory mode** (Q6=a, #10 hook): `memory_gap_mode` default advisory (warn/exit-0) auto-enable, blocking opt-in KHÔNG bị hạ cấp im lặng; + **product_memory lens** narrate `docs/product/.memory` (→ EVIDENCE LIB-3).
- [~] LIB-4 · CORRECTNESS · HIGH · `hooks/emit_session_summary.py:60-68,115` — `first_timestamp()` chỉ đọc dòng đầu transcript (record đầu không có ts) → 43/43 session `duration_s:0`; 46/46 subagent `outcome:unknown`; 41/43 `skills:[]`. **ĐÃ LÀM:** `scan_head()` quét tới record đầu có ts (duration đúng) + gom skills ở head (skills không rỗng) — verified synthetic fixture (→ EVIDENCE LIB-4). **CÒN:** `track_subagent_outcome.classify_from_transcript` đã có sẵn (explicit→stop_reason→taxonomy→unknown) nhưng triệu chứng 46/46-unknown là field-shape mismatch cần transcript subagent THẬT để chỉnh khớp `stop_reason` — defer cùng bucket e2e LIB-9 (constraint #6: data PO ngoài repo, không đoán mù).
- [x] LIB-5 · CORRECTNESS · HIGH · `telemetry/scripts/lens_workflow_chains.py:23-25` — hardcode 2 routing doc đã bị xoá ở e52e077 → test tracked FAIL ngay HEAD (1 failed/108), `declared_chains` thành dead code (workflow lens vĩnh viễn 0 chuỗi) → declared-source dời sang `data/skill-chains.yaml` on-demand (in-skill, 0 token always-on), fail-loud khi vắng (→ EVIDENCE LIB-5).
- [x] LIB-6 · CONSISTENCY · HIGH · `.github/workflows/` (6 workflow) — 26 file test tracked (telemetry 18, hooks 4, _shared 4) không CI nào chạy; path filter thiếu `_shared/**`; CONTRIBUTING.md:75 "all tests must pass" không được enforce → thêm `internal-test-suite.yml` chạy đúng lệnh CONTRIBUTING.md:69 + guard-test chống drift + vá path filter `product-spec-ci.yml` (→ EVIDENCE LIB-6).
- [x] LIB-7 · CORRECTNESS · MED · `hooks/hook_runtime.py:41` + `track_script_execution.py:57-59` — SCRIPT_RE substring-match: grep/ls/glob nhắc tới script cũng thành "script run" (10 record glob literal), validate-proxy đếm grep `check_*` như validate PASS → siết matcher về dạng thực-thi (đầu lệnh/sau interpreter, nhận cả prefix abs/`$VAR` mà vẫn reject reference); battery 8-reject/7-match + 3 test (→ EVIDENCE LIB-7).
- [x] LIB-8 · CONSISTENCY · MED · `hooks/track_script_execution.py:61-68` — biến `session` đã tính nhưng record không ghi (414/414 record thiếu key, 3 sink kia đều có) → hook-telemetry không join được phiên↔script → thêm `"session"` vào record + test (→ EVIDENCE LIB-8).
- [ ] LIB-9 · CORRECTNESS · MED · `hooks/register_telemetry_hooks.py:107-108` — kênh UserPromptExpansion 0 record sau nhiều ngày (7/7 invocation đều PreToolUse:Skill). **ĐÃ VERIFY (claude-code-guide, dẫn CC hooks docs): `UserPromptExpansion` LÀ event HỢP LỆ** (fire khi slash-command expand) — giả định "sai tên event" → REFUTED, KHÔNG rename. 0-record nghi `matcher: None` (CC cần tên command/regex) HOẶC PO không gọi qua slash trong cửa sổ đo → **DEFER:** e2e 1 phiên thật assert record → quyết sửa-matcher / `UserPromptSubmit` fallback / gỡ. Cùng bucket real-transcript với phần outcome của LIB-4.
- [x] LIB-10 · CONSISTENCY · MED · `CLAUDE.md:4,8-13` — routing always-on tự nhận "three PO-facing skills", bảng 3 hàng — telemetry (PO-facing, bundle ship 4 skill) vô hình → "three"→"four" + hàng routing telemetry + nhãn giọng; nudge read-only trỏ telemetry trong ref `--status` (on-demand, regen baseline +107 token ref) (→ EVIDENCE LIB-10).
- [x] LIB-11 · CLEANUP · MED · `.claude/agents/` (13 file ck, commit a967688) + 2 `.env.example` + `schemas/ck-config.schema.json` (0 tham chiếu) — rác ck-local đã commit vào repo nguồn ship → untrack hoặc ghi DEC "tracked có chủ đích, không ship"
- [x] LIB-12 · CONSISTENCY · LOW · `telemetry/scripts/lens_validate_proxy.py:82` + `telemetry_render.py:182` — reason tiếng Anh hardcode chen giữa output VI (bản dịch `val_na` có sẵn không dùng) → lens trả `reason_code` (bỏ prose khỏi dict), render localize qua `_reason_label`/`val_na_reason` (vá cả path json) (→ EVIDENCE LIB-12).
- [x] LIB-13 · CONSISTENCY · LOW · `docs/audit-trail/telemetry-readback.md` — thiếu sink `.logs/hook-crashes.log` + config gate `product-spec-hooks.json` (đồ mới 2.3.0); README.md:26 gán memory-gap hook nhầm vào critique → thêm 2 mục sink/config-gate (verify khớp `hook_runtime`) + sửa attribution README EN+VI (memory-gap→`product-spec`) (→ EVIDENCE LIB-13/14).
- [x] LIB-14 · CLEANUP · LOW · `hooks/__tests__/test_telemetry_hooks.py:133,209` + `telemetry/.../test_telemetry_paths.py:56,62` — fixture còn dùng id "claude-pack" → đổi sang id trung tính `sample-skill` (→ EVIDENCE LIB-13/14).
- [x] LIB-15 · CONSISTENCY · MED · `telemetry/GUIDE-VI.md:257` + `GUIDE-EN.md:257` — trỏ `.claude/rules/skill-workflow-routing.md` (đã xoá e52e077, ship cho PO) → repoint `data/skill-chains.yaml`. **ĐÃ LÀM (P12):** quét rộng bắt thêm dòng 152 (finding chỉ nêu 257) → repoint cả 2 chỗ × 2 lang, khớp convention SKILL.md:57; GUIDE không vào footprint baseline (→ EVIDENCE P12).
- [x] LIB-16 · CONSISTENCY · LOW · `product-spec/SKILL.md:176-177` — mô tả `--memory-hook` ghi vào `.claude/settings.local.json` + `--memory-hook-shared` trỏ `settings.json`; thực tế (install.sh:21-23,60,124) cả hai **flip cờ** `memory_gap_hook` trong `.claude/hooks/product-spec-hooks.json` (không còn settings.local/shared split) → sửa mô tả. **ĐÃ LÀM (P12):** premise verified (install.sh:58-60 alias cùng flag) → mô tả đúng theo product-spec-hooks.json; SKILL.md vào footprint → **regen `context_footprint_baseline.json`** (gate đỏ sẵn từ growth P03-P07 chưa regen — fix luôn, DEC-P12-4) (→ EVIDENCE P12).

- Field-observations (không lên row): PO đứng sau HEAD 9 release (lỗi thời ngay ngày cài); tự chế GH Actions fail vĩnh viễn vì thèm validate-on-push; `.session.md` đóng băng 06-02 chứa 4 fact bị supersede — đúng nguồn GATE-NEVER-ASSUME cho phép assume; visuals đóng băng 06-03 (56/102 story) + 88 file backup tracked; critique marathon 13 report/ngày trên bản không fingerprint.
- Khoảng trống kiến trúc không-phải-defect: ~~upgrade-path 1.x→2.x (cài đặt Frankenstein)~~ **→ ĐÃ LÀM (P09)**, version-beacon, artifact-events, self-learning/feedback-loop về dev, memory-lens hợp nhất, rotation change-log, snapshot/restore — 15 đề xuất xếp hạng trong report.
- Phản biện: 0/58 finding lens bị REFUTED toàn phần; 13 ADJUSTED (2 đổi severity: ARC-F02 Critical→High, POX-F07 Medium→High); 13 finding do critic bổ sung được nhận vào.
- Chi tiết: plans/260611-0050-po-field-audit-fix-waves/ (plan + reports đầy đủ các wave)

### P09 (build-new #1) — Upgrade-một-lệnh + legacy-sweep · 2026-06-12

Build kiến-trúc (không phải defect-row Cycle 3): `upgrade.sh`/`.ps1` một-lệnh + planner/apply Python nhúng
bundle `_upgrade/` + legacy-map tường minh. 3-wave review (cleanup/correctness/coverage/DRY/consistency) +
critique-challenge → fold **14 finding**: 2 HIGH correctness (symlink-rollback báo-thành-công-giả; atomicity
chỉ phủ sweep-loop, trap chỉ in → wire `trap ERR`/try-catch auto-rollback sweep), embed-integrity test
(byte-identity + MANIFEST sha256), drop planner `--rollback` trùng, `--dry-run`/`--apply` mutually-exclusive,
assert→ValueError, bỏ mkdir thừa + process-substitution, gitignore backup, lazy-backup-dir, µs timestamp.
**Descope có chủ đích:** full staging-dir+atomic-swap (plan tự gắn cờ "code dễ vỡ nhất"; sweep đã atomic +
auto-recover + install idempotent → recoverable, 0 mất dữ liệu — DEC-P09-2). Suite **276 passed / 19 skipped**
(+38 vs 238 baseline) + `docker bash:3.2 -n` OK. Quyết định: DEC-P09-1..6 (phase-09). → EVIDENCE P09.

### P12 (docs/cleanup remainder) — 8 row · 2026-06-12

Implementation (PS-19/20/22/24 đã có từ wave trước; PS-25 split là mới) chạy nền; controller verify độc lập +
3-wave review (cleanup/correctness/coverage/DRY/consistency) + critique-challenge. **Bắt 1 regression bảo mật
agent gán nhầm "pre-existing", fold 1 DRY, fix 1 nit, mở rộng 3 việc phát hiện-trong-review.**
- **PS-25 (render_html split):** agent gọi `test_body_render_values_fail_closed_when_libs_absent` "pre-existing
  fail" — thực ra PASS tại HEAD, FAIL sau split (lookup `VENDOR_MARKED` chuyển sang `render_html_assets`, test
  patch facade `render_html.*` thành no-op → vỡ lưới fail-closed). Fix: patch nhà thật + gỡ re-export chết
  (DEC-P12-1). Thêm: `_escape` (chokepoint XSS) nhân 5× **đã drift** → gom 1 nhà-lá `render_html_escape.py`
  (DEC-P12-2). 5 module ≤214 exec-LOC (orchestrator 834→327).
- **PS-19:** số `5758→5371 (−6.7%)` + `3820→3677 (−3.7%)` tái lập **chính xác** từ tag bằng `ceil(len/4)` +
  test pin + quy ước README.  **PS-20:** mọi flag GUIDE tồn tại thật (không flag ma) + inventory test.
  **PS-22:** untrack 8 state/cache, prose giữ.  **PS-24:** ascii ≤120 + comment cap stale fixed.
- **LIB-11 = DEC (không untrack):** premise "rác ck 0-ref" SAI — `skill-schema.json` nạp bởi validator, 7 agent
  ship qua manifest, `reflect_scan` trỏ memory-harvester; untrack sẽ phá kit (DEC-P12-3).
- **Mở rộng (defect-row gộp-nhóm-P12 + phát hiện-trong-review):** LIB-15 (telemetry GUIDE dead-ref ×4, repoint
  `data/skill-chains.yaml`), LIB-16 (SKILL.md memory-hook desc sai → product-spec-hooks.json), và **`_shared`
  footprint regression-guard ĐỎ sẵn** (growth ref P03-P07 chưa regen) → regen baseline (DEC-P12-4).
Verify: **product-spec 708/708 · critique 188/188 · telemetry 124/124 · _shared footprint 43/43** (chạy riêng
process), 0 fail. Leak-scan finding-code CLEAN. Render smoke byte-identical. Quyết định: DEC-P12-1..4 (phase-12). → EVIDENCE P12.

### P10a · #7 age-beacon (build-age) — ARC-F03/CVR-F02 · 2026-06-12 (build-new, ghi DEC)
- **Premise gãy → PO ruling (DEC-P10a-1):** scout: installer loại `MANIFEST.json` khỏi cây cài + không ghi stamp
  → không có nguồn dữ liệu cho beacon. STOP-ASK 4 phương án (build-age MANIFEST / install-stamp / CHANGELOG /
  hoãn) → PO chốt **build-age qua MANIFEST stamp**. Installer (sh+ps1) copy `MANIFEST.json` → `.claude/MANIFEST.json`;
  `status.py._bundle_age` đọc `<root>/.claude/MANIFEST.json` → `bundle_age{bundle_version,built_at,age_days}`,
  age=ngày-kể-từ-đóng-gói (clamp future→0), LLM render dòng VI "đóng gói N ngày trước". DRY split: script emit facts,
  `references/workflow-status.md` giữ prose. Fail-silent (thiếu/hỏng/empty → null, không gate).
- **Critique-challenge (2 finding, đào sâu):** (1) empty-string version lọt `isinstance(str)` → render "bản  " nửa
  vời → thêm guard `not version`/`not built_at` + 2 test. (2) tương tác upgrade P09 → verify planner là **allowlist**
  (`legacy_map.entries` only, không scan-xoá file lạ) → stamp an toàn, upgrade refresh stamp. KHÔNG đụng approved data.
Verify: **product-spec 718/718** (+10) · **release 296/296** (19 skip) · **_shared footprint 17/17** (regen baseline
chỉ product-spec total +336 từ workflow-status.md, 3 skill kia Δ0) — chạy riêng process, 0 fail. Quyết định: DEC-P10a-1 (phase-10). KHÔNG chạm PO data → verify inline (counts ở trên), không bơm EVIDENCE (đang quá cap).
