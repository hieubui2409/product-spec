# HA Implementation Blueprint — 4-Lens Deep-Dive

**Date:** 2026-06-06 · **Companion to:** `comparative-learning-260606-1720-human-analyzer-patterns-report.md` · **Source:** 4 read-only Explore sub-agents on `/home/hieubt/Documents/human-analyzer/` (HA)

> **Caveats (đọc trước):**
> 1. **Line-number trong report là gần đúng** — sub-agent đôi khi ước lượng. Verify lại `file:line` trước khi code.
> 2. **CM có ĐÚNG 3 skill**: `product-spec`, `product-spec-critique`, `claude-pack`. (Vài chỗ agent nhầm thành "feature-export/deployment" — đã sửa.)
> 3. Đây là **blueprint tham chiếu để adapt**, KHÔNG phải lệnh implement. Lọc theo YAGNI cho repo 3-skill.

---

## LENS A — Observability / Telemetry

### HA cơ chế (blueprint)

**Root:** `.claude/telemetry/*.jsonl` (gitignored). HA có 12 sink; CM chỉ cần 3.

**Shared writer — 2 bản song song (Node + Python), cố ý KHÔNG share code** (hook không phụ thuộc .ck.json):

`/.claude/hooks/lib/telemetry-paths.cjs` — `appendEvent(name, record)`:
```js
function appendEvent(name, record) {
  if (disabled()) return;                       // CK_TELEMETRY_DISABLED env
  try {
    const p = sinkPath(name);
    try { if (fs.statSync(p).size > MAX_SINK_BYTES) fs.renameSync(p, `${p}.bak`); }
    catch (_) {}                                 // file chưa tồn tại
    fs.appendFileSync(p, `${JSON.stringify(record)}\n`);
  } catch (_) { /* telemetry must never break a hook */ }
}
```
`/.claude/scripts/platform_lib/telemetry.py` — `append_event(name, record)`: cùng pattern + `_rotate_if_large()` 8MB→.bak + disabled khi `PYTEST_CURRENT_TEST`/`CK_TELEMETRY_DISABLED`. **Nguyên tắc vàng: fail-open, im lặng, KHÔNG bao giờ chặn op chính.**

**3 sink lõi + schema:**
| Sink | Trigger (hook) | Schema dòng |
|---|---|---|
| `invocations.jsonl` | `PreToolUse:Skill` (`track-skill-invocation.cjs`) | `{ts, skill, session, args?}` |
| `hook-telemetry.jsonl` | `PostToolUse:Bash` match `skills/.+/scripts/.*\.(py\|sh)` (`track-script-execution.cjs`) | `{ts, source:"hook:bash", script, exit, command?}` |
| `sessions.jsonl` | `Stop` (`emit-session-summary.cjs`) | `{ts, session, skills[], tools{}, files_modified, tokens{}, duration_s}` |

**exit inference** (hook không có exit code thật): regex stderr `Traceback|Error|Exception` → exit=1, else 0. Thô nhưng đủ.

**context-budget-gauge.cjs** (`UserPromptSubmit`): đọc tail transcript 128KB → lấy `message.usage` cuối (input+cache_read+cache_creation) → `pct=current/WINDOW` (default 200K, env `CK_CONTEXT_WINDOW`), `projected=(current+NEXT_EST)/WINDOW` (default +25K). Tier: ≥85% "force-isolate", ≥70% "warn", else im. **Luôn `{continue:true}` — advisory, không block.** Emit `context-gauge.jsonl`.

**Read-back:** `com-skill-analytics/scripts/scan-skill-usage-and-tokens.py` đọc `invocations.jsonl` → `{counts{skill:n}, by_day{}, never_used[], rows[]}`. Token attribution span-model: 1 Skill tool_use mở span, mọi usage assistant sau gán vào skill đó tới Skill kế (chỉ input+output, **loại cache_read**). Test `tests/test_skill_analytics.py` cover: empty file, days-filter, never-used.

### CM adaptation (minimal)
- **Copy nguyên** `telemetry-paths.cjs` + 3 hook (`track-skill-invocation`, `track-script-execution`, `emit-session-summary`).
- `mkdir .claude/telemetry/` + thêm vào `.gitignore`.
- **Schema rút gọn:** invocations `{ts, skill, session}` · hook-telemetry `{ts, source, script, exit}` · sessions `{ts, session, skills, tools, files_modified, tokens, duration_s}`.
- **DROP:** context-gauge (CM ít subagent — cân nhắc P2), errors/instincts/character/material/cascade sinks (không áp dụng).
- **Analytics:** script tối giản đếm invocation, bỏ token attribution + framework filter (chỉ 3 skill).
- **⚠️ claude-pack safety:** verify `.claude/telemetry/` KHÔNG lọt tarball. `pack.manifest.yaml` whitelist-based nên mặc định an toàn, nhưng thêm CI assert: `tar -tzf dist/*.tar.gz | grep -q telemetry && exit 1`. **Đây là câu hỏi mở #1 ở report gốc.**

---

## LENS B — Quality-gate (SANTA / COUNCIL / instinct-store)

### HA cơ chế (blueprint)

**orc:santa** — dual-reviewer post-writing gate (chỉ chạy khi `high_risk`):
- 2 persona/framework (vd PSY: clinical + cross-character). Mỗi reviewer nhận **CHỈ** target files + pre-check JSON, **không** session history, **không** output reviewer kia (input isolation cứng).
- `run-santa-review.py` pre-check deterministic (file inventory, schema, word-count, dates, cross-ref) TRƯỚC khi tốn LLM.
- Merge: PASS+PASS→SHIP; bất kỳ FAIL→gom issue→fix→spawn agent **MỚI** round 2 (fresh, 0 context round 1). **Cap cứng 2 round** ở script; round 2 FAIL→escalate user, không auto round 3.

**orc:council** — 4-voice anti-anchoring (Advocate/Skeptic/Pragmatist/Wildcard), chỉ manual-trigger:
- Mỗi voice nhận **chỉ câu hỏi** (≤500 char) + role, **không** file/context/voice khác (chống anchoring).
- Synthesis là việc LLM (main agent) sau khi gom 4 trả lời. Lưu `.claude/decisions/{date}-council-{slug}.md` append-only, dedup keyword với decision cũ trước khi chạy.

**instinct_store.py** (~270 LOC, `.claude/telemetry/instincts.jsonl`):
- Schema: `{id, text, category, confidence 0-1, evidence_count, last_reinforced, created_at, source_session, tags, status, pinned}`.
- `reinforce()`: `conf += (1-conf)*boost` (asymptotic) · `apply_decay()`: `conf *= e^(-λ·days)` (skip pinned) · `archive_stale()`: conf<0.4 & 30d & !pinned · `get_promotion_candidates()`: conf≥0.8 & evidence≥3 · `_atomic_rewrite()` temp+os.replace.
- **PHÁT HIỆN QUAN TRỌNG:** KHÔNG skill LLM nào gọi `reinforce/decay/archive` để đổi hành vi. Chỉ orchestration đọc để ĐẾM/inventory. → **instinct_store là log + filter, KHÔNG phải learning loop thật.** Learning integration dở dang.

**Verdict cache** (`verdict_cache_keys.py`): key `check|scope|content_hash|lang|dep_hash`; `NEVER_CACHED={crisis_assess, narrative_twist, contradiction}`; lưu **chỉ label scalar** (≤512 char, từ chối non-scalar → không PII vào committed cache).

### Honest verdict + CM adaptation
**CM `product-spec-critique` đã là analog SẠCH HƠN:** 4-lens read-only + consolidator + humanizer, report-only, OUT-of-CI, + có thứ SANTA/COUNCIL KHÔNG có (inherited context parent→child, descendant rollup, web research cache, repeat-offense findings-index, drift snapshot, humanizer gate). SANTA/COUNCIL/instinct **purpose-built cho profile refinement**, không hợp spec critique.

**Slice tối thiểu đáng ghép (low-risk):**
- ✅ `NEVER_CACHED` safety set vào `judgment_cache.py` (vd contradiction, core_value_drift_critical) — chống verdict stale nguy hiểm.
- ✅ Repeat-offense tracking (mở rộng findings-index sẵn có).
- ✅ Dedup awareness: scan `docs/product/critique/` critique cũ cùng scope, surface "đã chạy ngày X, N finding" (như COUNCIL dedup decisions).

**KHÔNG adopt (vi phạm ranh giới report-only/non-deterministic):**
- ❌ instinct_store learning loop → bleed vào decision-making, phá reproducibility. Nếu muốn learning, để hook NGOÀI skill.
- ❌ COUNCIL question-only isolation → critique CẦN context spec, giấu đi là mất.
- ❌ Multi-round fix iteration → đổi contract "1 report/request".
- ❌ Thay verdict-cache → judgment_cache của CM (graph-aware, batch-write, po_ruling_ref bridge) tốt hơn cho spec.

---

## LENS C — Docs discipline & audit-trail

### HA cơ chế (blueprint)

**EVIDENCE.md** (~497 dòng, MANUAL, không lint) — 1 entry/fix:
```markdown
## CYCLE {N}
### {FW}-{N} · {CATEGORY}/{SEVERITY} · {file:line} symptom ngắn
- **Root cause:** {tại sao}
- **Evidence (before):** {command + output — phải reproducible}
- **Fix:** {hành động}
- **Evidence (after):** {command output chứng minh}
- **Note:** {caveat / durable source}
```
ID grammar `{FRAMEWORK}-{N}` (GRO-01, LIB-02). Category: CORRECTNESS/DRY/CONSISTENCY/CLEANUP/ENV/YAGNI; Severity HIGH/MED/LOW. Before/after **bắt buộc runnable command output**, không phải văn xuôi.

**REVIEW.md** (~525 dòng) — finding tracker:
```markdown
## CYCLE {N} — findings
### {FRAMEWORK}
- [x] {ID} · {CAT}/{SEV} · {file:line} — symptom. {fix sketch}   # fixed→EVIDENCE.md
- [ ] {ID} ...   # open
- [~] {ID} ...   # partial/deferred
- [N/A] {ID} ...  # verified non-bug
```
Top: scope (framework reviewed + exclusions + scope-expansion note) + principle "scripts gather, LLM judges". Cycle đánh số, roll-forward item chưa đóng.

**Cycle workflow** (manual, driven bởi `/code-review` skill, KHÔNG có script orchestrator): review→finding `[ ]`→root-cause→fix+test→log EVIDENCE→mark `[x]`→pytest xanh→close→next.

**Nav-docs — thực tế phần lớn HAND-WRITTEN (không auto-gen như tưởng):**
- `MODULES.md`: **semi-derived** — `orc:skill-stocktake --quick` chỉ DETECT drift vs CLAUDE.md, KHÔNG regen bảng. Bảng tay.
- `distilled-principles.md`: 100% tay (5 principle cross-rule). Không generator.
- `knowledge-architecture.md`: tay (asset count cập nhật khi drift).

**CLAUDE.md vs GOAL.md split:** CLAUDE.md = architecture + rules ổn định (load mỗi session). GOAL.md = state động <4000 char (mission, DONE, REMAINING DAG, UNRESOLVED OQ, cycle-log append-only 1-dòng). GOAL.md đọc-trước để context hóa từng turn; cycle log là summary 1 dòng + link report, KHÔNG full transcript → giữ nhỏ.

### CM adaptation (minimal, chống sprawl)
- **Vị trí:** `docs/audit-trail/EVIDENCE.md` + `REVIEW.md` (git-tracked, durable — KHÁC `plans/reports/` ephemeral). **Đây là câu hỏi mở #2.**
- ID grammar CM: `PS-` / `PSC-` / `PACK-` / `LIB-` (shared). Cùng schema HA.
- **Tie Decision Register:** EVIDENCE entry cite `DEC-<n>` khi fix giải quyết conflict đã ruling. decisions.md = "quyết gì", EVIDENCE.md = "đổi gì + bằng chứng".
- **Size target năm 1:** EVIDENCE ≤200 dòng, REVIEW ≤300 dòng (CM ~1/10 scale HA). KHÔNG để thành 50-80K.
- **Cycle:** quý/hậu-major-feature, manual, 1 engineer/1 ngày. Không CI driver.
- **MODULES.md auto-gen? → KHÔNG (chưa).** 3 skill + ~3 import edge = 1 bảng README đủ. Revisit khi ≥10 skill. distilled-principles/knowledge-architecture: defer, nhúng vào CLAUDE.md.

---

## LENS D — CI / Release / Eval

### HA cơ chế (blueprint)

**eval/evals.json** (config-driven golden, no code):
```json
{ "fixture": "e2e/synthetic-project",
  "cases": [{
    "id": "health-check-file-count",
    "script": ".claude/skills/psy-health-check/scripts/score-profile-completeness.py",
    "args": ["--character", "test-alpha", "--json"],
    "extract": {"value": "file_count_assertion.expected"},
    "expected": 50 }] }
```
**eval/run_evals.py** loop: load json → mỗi case `subprocess.run(PY, script, args, timeout=90, capture)` → parse JSON stdout → `_extract()` dot-notation → assert `actual==expected` → PASS/FAIL → exit 0 iff all pass. **No network/no API key** (chỉ nửa deterministic; case dùng `datetime.now()` bị loại). Khác pytest: golden value nằm trong DATA không code, runner subprocess.

**e2e/run-full-pipeline.py** drive trọn pipeline trên `e2e/synthetic-project/` (no-PII): `STEPS=[(framework,label,argv)...]` chạy tuần tự, set `PMC_PROJECT_ROOT/PYTHONPATH/CK_CACHE_DIR`, route exit: 0→OK, 1 & label∈`_FINDINGS_OK`→FINDINGS (verdict hợp lệ không phải lỗi), else→ERROR. Emit bảng markdown, exit 0 iff all OK/FINDINGS.

**frameworks-ci.yml** gates (matrix py3.11+3.13, fail-fast:false, all deterministic):
1. py_compile sweep toàn .py · 2. import platform_lib sweep · 3. `validate-all-against-schemas.py` (jsonschema Draft-7) · 4. `orc:audit` referential integrity (exit0) · 5. `pytest -m "not gemini"` · 6. conditional `run_evals.py`.

**cross-framework-bug-class.yml** — `pytest -m bug_class`, named invariant closed-classes:
- missing-module · registry-redefinition (no reassign EVENT_ROUTING…) · glob-scope (phải rglob) · memory-dir-redefinition (gọi paths.memory_dir) · stale-project-name · orc:audit exit0 · schema exit0 · **skill-count == CLAUDE.md** (đếm dir `{fw}-*` == regex `(\d+) framework skills`) · roster-drift.

**Version/CHANGELOG/manifest sync gate: HA KHÔNG CÓ.** Chỉ dựa PR review tay + tag pattern `frameworks-vX.Y.Z` khớp manifest ở release workflow. → **CM thêm cái này là NET-NEW, CM dẫn trước.**

### CM blueprint cho 3 gap
**(a) run_evals.py** đọc `evals.json` sẵn của 3 skill: subprocess script → extract → assert → exit 0/1. Wire vào `product-spec-ci.yml` step sau pytest. Biến evals.json từ "trang trí" thành gate thật. *Không copy:* 6-framework structure, character/roster.

**(b) version-sync gate** (`tests/test_version_sync.py`, `@pytest.mark.bug_class`, mở rộng `cross-skill-bug-class.yml`):
- `test`: SKILL.md `metadata.version` == CHANGELOG.md top `## [X.Y.Z]` (mỗi skill).
- `test`: `pack.manifest.yaml` version == CHANGELOG root top.
- Bắt: bump skill quên CHANGELOG / tag lệch manifest. **High-value, low-effort, HA không có.**

**(c) e2e từ examples/acme-shop:** chain deterministic `init→validate→viz→export`, assert artifact tồn tại + exit 0, no-network. Wire vào CI. *Không copy:* `-m:platform_lib` module syntax, 16-step framework cascade.

---

## Mapping về Adoption Backlog (report gốc)

| Backlog | Lens | Blueprint sẵn ở trên | Prio |
|---|---|---|---|
| A1 telemetry sink | A | Copy telemetry-paths.cjs + 3 hook, schema rút gọn | P0 |
| A2 audit-trail | C | docs/audit-trail/{EVIDENCE,REVIEW}.md, tie DEC-<n>, ≤500 dòng | P0 |
| A3 run_evals harness | D | subprocess loop đọc evals.json | P1 |
| A4 version-sync gate | D | test_version_sync.py bug_class | P1 |
| A5 context-gauge | A | context-budget-gauge.cjs adapt | P2 |
| A6 e2e pipeline | D | run-full-pipeline.py từ acme-shop | P2 |
| A7 PreCompact digest | A/C | (chưa deep-dive — HA `write-framework-delta-compact-digest`) | P2 |
| A8 nav-docs auto-gen | C | **KHÔNG nên** (3 skill) — thực tế HA cũng tay | P3 |
| A9 quality-gate learning | B | **KHÔNG nên** (instinct dở dang + phá ranh giới) | P3 |

**Điều chỉnh sau deep-dive:** A8/A9 xác nhận **đừng làm** — HA's nav-docs phần lớn hand-written (không phải auto-gen như tưởng), và instinct_store **không phải learning loop thật** (không skill nào dùng để đổi hành vi). A4 (version-sync) là nơi CM có thể vượt cả HA.

---

## Cần verify trước khi implement
1. Line-number HA trong report (agent ước lượng) — đọc lại file thật.
2. `telemetry-paths.cjs` đường dẫn sink config (env vs hardcode) — confirm để CM set đúng.
3. evals.json hiện tại của 3 skill: schema có khớp `{cases:[{script,args,extract,expected}]}` không, hay format khác → quyết định run_evals shape.
4. claude-pack manifest/safety: confirm `.claude/telemetry/` bị loại khỏi tarball.

## Unresolved questions
1. Telemetry sink runtime-file có hợp định vị distribution claude-pack? (gitignore + pack-exclude đủ chưa)
2. audit-trail ở `docs/audit-trail/` (durable) hay `plans/reports/` (ephemeral)?
3. evals.json hiện có phản ánh đúng acceptance muốn gate, hay cần định nghĩa lại metric trước khi xây harness?
4. Mở `STANDARDIZE.md`-ngược (CM ghi pattern học từ HA) để khép vòng 2 chiều?
