# Brainstorm — Tối ưu hook của project (telemetry layer)

**Date:** 2026-06-09 · **Status:** Approved → handoff `/ck:plan --tdd --redteam`
**Scope:** refactor (hook_io + own-config toggle) cho 5 telemetry hook. **Crash audit-log (D) áp cho CẢ 7 hook project-authored** (gồm 2 enforcement hook). NGOÀI scope: 11 hook `.cjs` của CK + `.ck.json`.

> **Scope note (PO):** audit-log lỗi hook BẮT BUỘC phủ mọi hook của mình. `memory_gap_hook` + `critique_nudge` tuy không vào refactor hook_io (block-protocol riêng), vẫn phải gọi `log_hook_error()` trong nhánh `except` của chúng (chúng đã có `try/except → ALLOW_EXIT`, chỉ thêm 1 dòng log trước khi return).

## 1. Problem statement

PO đọc bài "ClaudeKit Guard rails" (nhấn exit-code 1 vs 2), muốn tối ưu **hook của mình** (không đụng hook CK), học pattern từ CK.

**Phân loại (scout-verified):**
- **CK-inherited** (`.ck.json` kit "ClaudeKit Engineer"): `session-init, usage-quota-cache-refresh, simplify-gate, dev-rules-reminder, subagent-init, descriptive-name, scout-block, privacy-block, plan-format-kanban, session-state, cook-after-plan-reminder` + 3 CK-origin unwired (`workflow-artifact-gate, team-context-inject, usage-context-awareness`). → KHÔNG đụng.
- **Project-authored (7 `.py`):** telemetry `mark_bash_start, track_script_execution, track_skill_invocation, track_subagent_outcome, emit_session_summary`; enforcement `memory_gap_hook, product_spec_critique_nudge`.

**Phát hiện then chốt — exit-code đã ĐÚNG, không có bug:**
- 5 telemetry hook: fail-open, `try/except`, luôn `{"continue": true}`, exit 0. ✅
- `memory_gap_hook`: đúng `BLOCK_EXIT=2` ở đúng chỗ chặn Stop, có backstop `_FENCE_BLOCK_CAP=8` + nudge-once chống loop. ✅
- `critique_nudge`: `ALLOW_EXIT=0` mọi nhánh, "never exit 2". ✅
- → Bẫy exit-1-thay-vì-2 của bài viết **không xảy ra** ở hook của mình.

## 2. Real optimization opportunities (≠ gợi ý bài báo)

| # | Vấn đề | Bằng chứng |
|---|--------|-----------|
| A | Hot-path spawn: mỗi Bash spawn 2 python (`mark_bash_start` Pre + `track_script_execution` Post) kể cả `git/ls`; matcher settings.json chỉ lọc tool-name → không tránh được spawn-per-Bash | `settings.json` Pre/PostToolUse(Bash); `SCRIPT_RE` |
| B | Thiếu off-switch riêng từng hook; chỉ có env `CK_TELEMETRY_DISABLED` (all-or-nothing). CK có `isHookEnabled()` đọc `.ck.json` | `telemetry_paths.disabled()` |
| C | DRY: read-stdin/parse/emit-continue/fail-open lặp y hệt 5× | 5 file `.py` |
| D | Silent-failure: `except: pass` nuốt lỗi, không signal khi hook chết. **Phủ cả 7 hook của mình** (telemetry + enforcement) | không file `.py` nào log lỗi |

**Sự thật perf (A):** không có cách làm python-spawn nhanh hơn. Lever thật = **off-switch** → A hội tụ vào B.

**`ms` (mark_bash_start):** CÓ dùng — `telemetry_render.py:272/409` render `avg_ms`; `test_lens_health.py:49` test degrade `None→"—"`. Bỏ hook = mất cột duration/script (degrade, không crash). **Quyết: giữ dạng toggleable**, không bỏ cứng.

## 3. Approach đã chọn — #1: `hook_io.py` + own-config

```
.claude/skills/telemetry/scripts/hook_io.py          (MỚI)
  run_telemetry_hook(name, core_fn):
    data = read_stdin_json()                           # C
    if not hook_enabled(name): emit_continue(); return # B + A off-switch
    try: core_fn(data)
    except Exception as e: log_hook_error(name, e)      # D
    emit_continue()                                     # fail-open, {"continue": true}

.claude/hooks/product-spec-hooks.json                (MỚI, committed — KHÔNG đụng .ck.json)
  { "mark_bash_start": true, "track_script_execution": true,
    "track_skill_invocation": true, "track_subagent_outcome": true,
    "emit_session_summary": true }                      # missing-key = enabled (học CK semantics)

.claude/hooks/.logs/telemetry-hooks.log              (dir đã có; chỉ ghi khi exception → 0 cost hot-path)
```

Mỗi hook co còn ~15 dòng: `def core(data): ...` + `run_telemetry_hook("<name>", core)`.
Micro-opt: defer `import telemetry_paths` đến SAU gate enabled (hook bị tắt làm ít việc nhất).

**Rejected — Approach 2 (helper trong telemetry_paths):** không giải C (skeleton vẫn lặp), trộn concern paths+policy.

## 4. Implementation considerations & risks

- **Risk:** refactor 5 fail-open hook có thể phá contract `{"continue": true}` / fail-open.
- **Mitigation:** có sẵn `__tests__/test_telemetry_hooks.py` + `telemetry/scripts/tests/` → **TDD**: lock hành vi hiện tại trước, refactor sau.
- **Boundary:** KHÔNG đụng `.cjs` CK, KHÔNG đụng `.ck.json`. 2 enforcement hook KHÔNG vào refactor hook_io, NHƯNG vẫn phải thêm `log_hook_error()` (D) trong `except` của chúng.
- **`log_hook_error()` là API dùng chung** cho cả 7 hook (đặt trong `hook_io.py` hoặc `telemetry_paths.py` — nơi cả enforcement hook import được; quyết khi plan vì enforcement hook hiện import từ skill scripts khác, không phải telemetry).
- **Compat:** giữ nguyên `CK_TELEMETRY_DISABLED` (global kill-switch) song song own-config (per-hook).

## 5. Success criteria

1. 5 telemetry hook dùng chung `hook_io`; mỗi file ≤ ~20 dòng logic riêng.
2. Tắt 1 hook qua `product-spec-hooks.json` → hook đó emit continue ngay, không spawn việc nặng, không ghi telemetry.
3. Exception trong core_fn → 1 dòng vào `.logs/telemetry-hooks.log`, vẫn `{"continue": true}` + exit 0.
4. Toàn bộ test telemetry cũ PASS không sửa assertion (trừ test mới cho hook_io/toggle/log).
5. `ms`/`avg_ms` vẫn render khi `mark_bash_start` bật; degrade "—" khi tắt.

## 6. Next steps

- `/ck:plan --tdd` với report này làm context.
- Phase gợi ý: (1) test lock hành vi 5 hook hiện tại → (2) `hook_io.py` + own-config loader + logger → (3) refactor lần lượt 5 hook → (4) test toggle + log + degrade → (5) doc ngắn trong telemetry SKILL.md.

## Unresolved questions

- Own-config có cần ship trong release bundle (`pack.manifest.yaml`) không? → quyết khi plan.
- Có muốn `hook_enabled()` đọc cả env override (`CK_HOOK_<NAME>_DISABLED`) ngoài file JSON không? → optional, quyết khi plan.
