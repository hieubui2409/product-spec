# Hook-Mechanics Findings — gate for the Tier-1 `memory_gap_hook.py`

Verification spike. **No shipped code.** Confirms or corrects the Claude Code (CC) hook assumptions the Stop-hook
phase and its installer phase are built on, so the hook is built on verified mechanics rather than guesses.

## Method + honesty disclaimer

- **CC version:** `2.1.159 (Claude Code)` (from `claude --version` on this machine).
- **Evidence base — three sources, no live in-session spike:**
  1. Official CC hook docs (`anthropics/claude-code` → `plugins/plugin-dev/skills/hook-development/SKILL.md` +
     `references/advanced.md`), retrieved current.
  2. The installed `.claude/settings.json` hook block (real shape on this repo) + the existing ck-managed
     `.claude/hooks/*.cjs` handlers, which show what stdin CC actually delivers locally (`scout-block.cjs`,
     `privacy-block.cjs`, `session-state.cjs`).
  3. Local environment probes (`.claude/.gitignore`, venv interpreter, settings layout).
- **HONEST LIMITATION:** a *live* throwaway logging hook was **not** registered + triggered inside this workflow run
  (the workflow agent cannot safely register a Stop hook and force a self-continuation mid-run, and must leave **zero**
  scratch artifacts behind). The Stop-block / `stop_hook_active` / 8-cap items are therefore confirmed from **documented
  CC mechanics + the local handler shape**, not from an observed in-session continuation. Every item that rests only on
  documentation (not on a locally-observed payload) is marked **ASSUMED-FALLBACK** below with the exact adaptation the
  hook phase must take if the installed CC differs. The hook phase's own pytest (`test_memory_gap_hook.py`) feeds
  synthetic stdin and therefore does **not** depend on a live spike to pass — but the runtime block/continue contract
  does, so the items below are the live-behavior checklist for the first manual smoke against a real `Stop` turn.

## Assumptions: CONFIRMED vs ASSUMED-FALLBACK

| # | Assumption the hook depends on | Status | Evidence / fallback |
|---|--------------------------------|--------|---------------------|
| A1 | `Stop`, `PostToolUse`, `SessionStart` events exist and fire | **CONFIRMED** | All three appear in official hook config examples AND are live-registered in this repo's `.claude/settings.json` (`SessionStart`, `PostToolUse`, `Stop` blocks all present + firing ck handlers). |
| A2 | Common stdin fields delivered to every hook: `session_id`, `transcript_path`, `cwd`, `hook_event_name` (`permission_mode` too) | **CONFIRMED** | Official "Common Hook Input Format" lists exactly these. `cwd` is independently confirmed locally — `scout-block.cjs:86` reads `data.cwd`. So **Stop stdin carries `transcript_path` + `cwd`** as the design needs. |
| A3 | `PostToolUse` stdin carries `tool_name` + `tool_input`; a `Write\|Edit` matcher works | **CONFIRMED** | `tool_name`/`tool_input` confirmed both in docs and locally (`scout-block.cjs:83-84`, `privacy-block.cjs:107` destructure `tool_input`/`tool_name`). `Write\|Edit` matcher pattern confirmed live in `settings.json` (`PostToolUse` matcher `Edit\|Write\|MultiEdit`; `PreToolUse` matcher `Write`). |
| A4 | The PostToolUse **result/output** field name (`tool_output` vs `tool_response` vs `tool_result`) | **ASSUMED-FALLBACK** | Docs are internally inconsistent (one place `tool_result`, another `tool_response`); the plan text said `tool_output`. **Fallback / de-risk: the no-op touched-flag guard does NOT need the result field at all** — it only needs `tool_name` + `tool_input.file_path` to decide "a Write/Edit under `docs/product/` happened". The hook must read the file path from `tool_input`, never from the result field, so this ambiguity cannot break it. If a future feature needs the output, read it defensively: `tool_response or tool_result or tool_output`. |
| A5 | A `Stop` hook can **force continuation** and the `reason` reaches the model | **CONFIRMED (contract) / ASSUMED-FALLBACK (live)** | Official Stop output contract: `{"decision":"block","reason":"…","systemMessage":"…"}`; exit `2` = "blocking error, **stderr fed back to Claude**". Both the JSON-`reason` path and exit-2-stderr path are documented to reach the model. Not yet observed live in this run. **Fallback if block has no effect on the installed CC:** emit exit `2` with the actionable text on **stderr** (the documented blocking path) — the hook should write the reason to stderr regardless so it works whether CC honors JSON-`decision` or only exit-2. |
| A6 | `stop_hook_active` appears in `Stop` stdin on a continuation (the nudge-once escape) | **ASSUMED-FALLBACK** | The loop-prevention concept is documented, but `stop_hook_active` is **not** shown in the official common-fields snippet and was not observed live here. This is the single field the **nudge-once** policy (`validate_no_marker`, `approved_changed_no_dec`) hinges on. **Fallback if the field is absent or named differently:** do NOT rely on it for loop-safety. Nudge-once must self-limit via a committed per-turn marker instead — block once, write a `last_judged`/ack stamp keyed to the node+wording, and on the next `Stop` see the stamp and allow. (The phase already plans `no-dec-acks.json` + `last_judged.json`; if `stop_hook_active` is missing, that committed-stamp path becomes the *primary* escape, not just the future-turn ack.) Net: nudge-once degrades to "block-once via marker", never an infinite loop. |
| A7 | Consecutive-block backstop (default 8; env `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) | **ASSUMED-FALLBACK** | Not surfaced in the retrieved docs and not observed live. The **persist** policy (`fence_breach` blocks until the gap is fixed) leans on this cap as its only loop-backstop. **Fallback if the cap does not exist / differs on the installed CC:** the `fence_breach` persist policy must not assume an external cap will save it — add an internal block-count guard (read transcript or a committed per-session block counter; after N self-blocks, downgrade fence persist to one final stderr warning + exit 0). Treat 8 as advisory, not load-bearing. The fence breach is also independently caught by the existing `check_fence`/`fs_guard` chokepoint, so a missing CC cap is not the last line of defense. |
| A8 | `settings.local.json` vs `settings.json` merge precedence (installer targets `.local`) | **CONFIRMED (locally)** | `settings.local.json` is gitignored here (`.claude/.gitignore:62`) → the per-user/per-machine local override file, exactly the right opt-in target for `--memory-hook` (no git noise, never auto-shared). The installer must **parse + reconstruct JSON** and merge into the existing `hooks` object (this repo's `settings.json` already has populated `Stop` + `PostToolUse` arrays — the merge must **append** a hook entry, never replace the array). **Note for the installer phase:** local + shared hooks are *additive* (both fire), so an idempotency guard keyed on command+matcher is mandatory to avoid double-registration; precedence is not "local replaces shared" for hooks, it is "both run". |

## Direct answers to the gated questions

- **Do Stop/PostToolUse/SessionStart fire?** Yes (A1) — confirmed in docs and live in this repo's settings.
- **Can a Stop hook force continuation + does the reason reach the model?** Yes per the documented contract (A5):
  `{"decision":"block","reason":...}` or exit-2-with-stderr. Live-unobserved here → hook should emit the reason on
  **stderr** and exit 2 so it works on the documented blocking path regardless.
- **Does `stop_hook_active` appear on a continuation stop?** **Unverified live (A6).** Build the nudge-once escape so it
  works *with or without* the field — committed per-turn marker is the durable escape; `stop_hook_active` is an
  optimization, not a dependency.
- **Is the 8-cap real?** **Unverified live (A7).** Don't make fence-persist's loop-safety depend solely on
  `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`; add an internal counter backstop.
- **Stop stdin carries `transcript_path` + `cwd`?** Yes (A2) — confirmed.
- **PostToolUse stdin carries tool name/input + does a `Write|Edit` matcher work?** Yes (A3) — confirmed locally; the
  result field name is the only ambiguity, and the no-op guard avoids needing it (A4).
- **settings.local vs settings.json precedence?** Local override is gitignored = correct opt-in target; hooks from both
  files are additive (A8) → idempotency guard required.

## Net guidance for the hook + installer phases

1. **Read only confirmed fields by name:** `transcript_path`, `cwd`, `session_id`, `hook_event_name`, `tool_name`,
   `tool_input` (and `tool_input.file_path`). Treat `stop_hook_active` and the result-output field as **optional** —
   read defensively (`payload.get("stop_hook_active", False)`), never crash if absent.
2. **Block both ways:** write the actionable reason to **stderr** and exit 2, AND emit the JSON
   `{"decision":"block","reason":...}` — so the model gets the reason whether CC honors exit-2-stderr or JSON-decision.
3. **Nudge-once loop-safety = committed marker, not `stop_hook_active`** (A6 fallback). `stop_hook_active`, if present,
   is a fast-path short-circuit on top of the marker.
4. **Fence-persist loop-safety = internal block counter**, with the documented 8-cap as a bonus, not the guarantee
   (A7 fallback).
5. **No-op guard never reads the result field** (A4) — derive "touched docs/product" from `tool_input.file_path`.
6. **Installer:** target gitignored `.claude/settings.local.json`, parse+reconstruct JSON, **append** to the existing
   `hooks.Stop` / `hooks.PostToolUse` arrays, idempotency keyed on command+matcher (A8).

## Deviations from the design's assumptions (call-outs the hook phase must honor)

- **`stop_hook_active` (A6) and the 8-cap env (A7) are NOT live-verified** on this CC build. The design treats both as
  load-bearing for loop-safety. **Required adaptation:** make committed per-turn markers the primary nudge-once escape
  and an internal block counter the primary fence-persist backstop; the CC field/env become optimizations layered on
  top. This keeps the hook loop-safe even if the installed CC names/handles them differently.
- **PostToolUse result field name is ambiguous (A4).** The design mentioned `tool_output`; docs say `tool_result` /
  `tool_response`. **Required adaptation:** the no-op guard reads `tool_input.file_path` only and never the result
  field, sidestepping the ambiguity entirely.
- Everything else (events fire, common stdin fields, `tool_name`/`tool_input`, `Write|Edit` matcher, stderr-exit-2
  blocking contract, `settings.local.json` as the opt-in target) is **CONFIRMED** and can be coded against directly.

## Cleanup / side-effects

No scratch hook, no temp `settings.local.json`, no logging artifact was created or left behind. The repo's
`.claude/settings.json` is unchanged; `.claude/settings.local.json` does not exist. The only file produced by this
spike is this findings note.
