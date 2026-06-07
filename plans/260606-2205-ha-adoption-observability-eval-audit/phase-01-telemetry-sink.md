# Phase 01 — Telemetry sink (A1)

**Item:** A1 · **Prio:** P0 · **Effort:** S · **Status:** pending · **Depends:** none

## Context links
- Blueprint Lens A: `plans/reports/ha-implementation-blueprint-260606-1720-four-lens-deepdive-report.md` (§LENS A)
- HA source: `human-analyzer/.claude/hooks/lib/telemetry-paths.cjs`, `scripts/platform_lib/telemetry.py`

## Overview
CM is blind: no record of which skill runs, which script errors, adoption rate. Add minimal append-only JSONL sinks written by hooks. Fail-open, silent, never blocks the observed op.

## ⛔ GATE C1/H2 — hook events are UNVERIFIED (spike before any code)
Red-team verified: **`settings.json` has NO `Skill` matcher**; HA's event vocabulary is not authoritative for CM's runtime. Before coding:
- **Spike 1 (skill invocation):** write a one-line debug hook, invoke a skill two ways (Skill-tool call vs slash-command). Determine which event fires — candidates: `PreToolUse` matcher `Skill` (if skills route through the Skill tool) vs `UserPromptExpansion` (slash-command expansion). **Re-target `track-skill-invocation` to whatever actually fires.** Do not assume.
- **Spike 2 (bash exit):** dump `PostToolUse:Bash` `tool_response` shape. If it exposes `exit_code` → use it directly (delete the stderr-regex). If not → listen to the distinct **`PostToolUseFailure`** event for the failure signal. The stderr-regex `Error|Exception` hack is a false-positive generator (benign logs) → **only a last resort, not the design**.
- Record verified events as "events confirmed against Claude Code vX.Y" in this phase before implementation.

## Key insights
- HA has 12 sinks; CM needs **3**. Drop context-gauge (→ Phase A5 later), errors/instincts/character/etc.
- **Exit signal: prefer real `exit_code` (Spike 2) or `PostToolUseFailure`; stderr-regex is fallback only** (see gate above).
- `_shared/lib/` currently holds only `plan-table-parser.cjs` → telemetry helper is net-new. Consistent placement.
- The 3 new `.claude/hooks/*.cjs` are **CM-local dev tooling** — NOT in `pack.manifest.yaml hooks:[]` (which lists only the 2 `.py` hooks). They must NOT ship in the bundle; do not "fix" this by adding them to the manifest.
- `settings.json` matchers in use: SessionStart, UserPromptSubmit, PreToolUse(Write·Bash|Glob|Grep|Read|Edit|Write), PostToolUse(Edit|Write|MultiEdit·Task|TaskCreate…), SubagentStart, SubagentStop(Plan), Stop. → register into the correct shape (append, see H3 below).

## Requirements
**Functional**
- Each Skill invocation → 1 line in `invocations.jsonl` `{ts, skill, session}`.
- Each skill-script Bash run → 1 line in `hook-telemetry.jsonl` `{ts, source:"hook:bash", script, exit}`.
- Each session Stop → 1 line in `sessions.jsonl` `{ts, session, skills[], tools{}, files_modified, duration_s}` (drop `tokens` — CM not needed v1).
- Readable by `jq`.

**Non-functional**
- Fail-open: any write error swallowed silently.
- Disabled when `CK_TELEMETRY_DISABLED` env set OR `PYTEST_CURRENT_TEST` (no telemetry during tests).
- Size rotation: sink > 8MB → rename `.bak`.

## Architecture
```
<verified skill-invoke event>  → track-skill-invocation.cjs → invocations.jsonl   (event TBD by Spike 1)
PostToolUse:Bash               → track-script-execution.cjs  → hook-telemetry.jsonl (match skills/.+/scripts/.*\.(py|sh); exit via Spike 2)
Stop                           → emit-session-summary.cjs    → sessions.jsonl
                                   ▲ all use _shared/lib/telemetry-paths.cjs (appendEvent)
```
- `appendEvent(name, record)`: `if disabled() return; rotate-if-large; appendFileSync(JSON+\n); catch → swallow`.
- Sinks live in `.claude/telemetry/*.jsonl`.

## Related code files
**Create**
- `.claude/skills/_shared/lib/telemetry-paths.cjs` — `appendEvent`, `sinkPath`, `disabled`, rotation.
- `.claude/hooks/track-skill-invocation.cjs`
- `.claude/hooks/track-script-execution.cjs`
- `.claude/hooks/emit-session-summary.cjs`
- `.claude/telemetry/.gitkeep` (dir placeholder; sinks gitignored)

**Modify**
- `.claude/settings.json` — register 3 hooks: `<verified skill-invoke event>` (Spike 1), `PostToolUse:Bash`, `Stop` (append).
- `.gitignore` — add `.claude/telemetry/*.jsonl` + `*.jsonl.bak` (keep `.gitkeep`).

**Do NOT modify**
- `pack.manifest.yaml` (whitelist already excludes telemetry — verified in Phase 1 CI assert, not by editing manifest).

## Implementation steps
0. **[GATE]** Run Spike 1 + Spike 2 (above); record verified events. Re-target architecture.
1. Write `telemetry-paths.cjs` helper (port HA, schema-trimmed; **`JSON.stringify` is the ONLY serialization path** — no manual field concat). Unit-test rotation + disabled-env + non-serializable-record-swallowed.
2. Write 3 hook scripts; each `require` the helper, build record, call `appendEvent`, always pass-through `{continue:true}`.
3. Register in `settings.json` (append to existing arrays — hooks run in **parallel + dedup by command string**, so cannot clobber; the real check is that the registration JSON shape parses and BOTH hooks on a shared event fire). Verify the Stop array (currently 1 entry, no matcher) accepts a 2nd hook object in the correct shape.
4. `.gitignore` entries + `.gitkeep`.
5. **claude-pack safety (regression sentinel, NOT the primary guarantee):** the primary guarantee is the **whitelist manifest** (telemetry is in no list → excluded by construction). Add a `bug_class` sentinel: build via `python -m pack` (like `test_installer_e2e.py`), assert tarball is **non-empty FIRST** (else vacuous pass), then `tar -tzf … | grep -Eq '(^|/)\.claude/telemetry/' && fail` (anchored, not substring).
6. Read-back: **document `jq` one-liners in `docs/audit-trail/` or a README** (counts per skill, never-used). NO new script unless a counts view is explicitly requested (KISS — decision: jq only for v1).

## Todo
- [ ] **[GATE] Spike 1 + 2: verify real hook events (skill-invoke + bash-exit)**
- [ ] `telemetry-paths.cjs` + unit test (rotation, disabled, non-serializable-swallowed)
- [ ] 3 hook scripts (fail-open verified)
- [ ] `settings.json` registration (no clobber)
- [ ] `.gitignore` + `.gitkeep`
- [ ] claude-pack tarball-excludes-telemetry `bug_class` test
- [ ] read-back: `jq` snippets documented (or tiny scan script)
- [ ] compile check all `.cjs` (`node --check`)

## TDD discipline (red → green → refactor)
- **RED first:** write `telemetry-paths.test` cases BEFORE the helper — (a) `appendEvent` writes one JSON line, (b) `disabled()` true under `CK_TELEMETRY_DISABLED`/`PYTEST_CURRENT_TEST` → zero writes, (c) rotation renames at >8MB, (d) a thrown `appendFileSync` is swallowed (fail-open). Confirm they fail (module not present) for the right reason.
- The claude-pack "tarball excludes telemetry" assertion is written as a failing test against a freshly built bundle, then made green by gitignore + (already-safe) whitelist.
- **GREEN:** minimal helper + hooks to pass. **REFACTOR:** dedup path logic under green.
- Hooks themselves: assert via a harness call that a fake `<verified skill-invoke event>` (Spike 1) yields exactly one `invocations.jsonl` line.

## Red-team angles (tests MUST cover)
- **Leak:** symlink inside `.claude/telemetry/` pointing outside; sink path traversal via crafted skill name → assert no escape, no tarball inclusion.
- **Injection:** skill name / script path containing newlines or `","` → assert JSONL stays one-line-per-event (newline-escaped), not splittable into forged records.
- **Fail-open abuse:** read-only `.claude/telemetry/` dir → op still succeeds, no throw.
- **Clobber:** confirm registering new Stop hook does not drop the existing Stop handler.
- **Disabled bypass:** ensure no code path writes when disabled (incl. rotation side-effect).

## Success criteria
- Run any skill → exactly 1 well-formed JSONL line appears; `jq .` parses it.
- `CK_TELEMETRY_DISABLED=1` → zero writes.
- Built tarball provably excludes `telemetry/` (CI test green).
- A hook error path (simulate write fail) does NOT break the observed tool.

## Risk
- **Phantom event (C1)** → biggest risk: a registered-but-never-firing hook = silent empty telemetry. Mitigated by the Spike gate.
- **No clobber** (docs: hooks run parallel + dedup) → instead verify both Stop hooks fire + registration JSON shape parses; assert telemetry write is order-independent (no shared-file assumption between `emit-session-summary` and `session-state.cjs`).
- **Sink leak into tarball** → primary guarantee = whitelist manifest (excluded by construction); gitignore = commit-hygiene (different threat); CI sentinel = regression catch. Three distinct layers, not one.
- **Untrustworthy `exit`** (H2) → resolved by Spike 2; regex fallback only.
- **Perf**: appendFileSync per tool call — negligible (1 line). Acceptable.

## Security
- No PII beyond skill name + session id + script path. No args captured in v1 (HA optionally logs args — we DROP to avoid leaking flag values).
- Sinks gitignored → never committed, never distributed.

## Next steps
- Exit-inference helper pattern reused by Phase 3 (run_evals subprocess exit handling).
- Context-gauge (A5) is a later upgrade of this sink family.
