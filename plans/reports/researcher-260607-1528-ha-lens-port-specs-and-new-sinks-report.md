# HA-to-Cleanmatic Observability Lens Port Specification

**Status:** COMPLETE | **Date:** 2026-06-07 | **Scope:** 4 analytics lenses + 2 new sink schemas + path gaps

---

## Executive Summary

Porting 4 HA observability lenses (forensics, memory-health, workflow-chains, subagent-reliability) to cleanmatic requires **stripping framework-prefix logic** (HA has 6 prefixes: mat/psy/cre/gro/orc/com; cleanmatic has 3 flat skills). Core forensics + memory logic is portable; workflow/reliability analyzers require new infrastructure (errors.jsonl + script-telemetry.jsonl sinks + TaskCompleted hook). cleanmatic's telemetry_paths.py needs 2 new exports: `sessions_dir()` + `SKILLS` path.

---

## PART 1: HA Script Analysis & Port Deltas

### 1.1 Forensics (parse-session-jsonl-forensics.py)

**Purpose:** Streaming JSONL parser; reconstructs session activity (skills, tool calls, tokens, files, subagents, duration).

**HA Inputs:**
- Source: `paths.sessions_dir()` → `~/.claude/projects/{encoded-root}/*.jsonl`
- Records: session transcript JSONL lines (message.content[] → tool_use blocks)
- Reads: `timestamp`, `message.usage`, `message.content[].{type, name, input}`
- Exit code logic: `parse_ts` (ISO8601 w/ Z→+00:00), streaming line-by-line (fail-safe on malformed)

**Core Algorithm:**
1. Stream single transcript file (never loads whole)
2. Extract: skills (from tool_use.name=="Skill" → tool_input.skill), tools (all tool_use by name, counts), files (from Edit/Write/MultiEdit/NotebookEdit → input.file_path), subagents (Task/Agent tool count), tokens (sum of input/output/cache_read/cache_creation), duration (last_ts - first_ts)
3. Aggregate across sessions (optionally filter by --since date)

**Output Dict Shape:**
```json
{
  "session": "session-id",
  "skills": ["skill1", "skill2"],
  "tool_counts": {"Edit": 5, "Bash": 3},
  "tool_calls": 8,
  "files_modified": ["/path/1", "/path/2"],
  "subagents": 2,
  "tokens": {
    "input_tokens": 100000,
    "output_tokens": 50000,
    "cache_read_input_tokens": 10000,
    "cache_creation_input_tokens": 5000
  },
  "total_tokens": 150000,
  "duration_s": 3600,
  "last_ts": "2026-06-07"
}
```

**Dependencies:**
- `platform_lib.paths.sessions_dir()` — single source for session-root resolution
- `platform_lib.formatters.{markdown_table, json_output}`
- `platform_lib.markdown_parser.parse_iso_date`

**Cleanmatic Port Deltas:**
- **STRIP:** No framework logic needed (cleanmatic has no multi-prefix skill names)
- **KEEP:** Streaming, token parsing, duration calculation, file-path extraction all portable as-is
- **ADD:** Call `telemetry_paths.sessions_dir()` instead of `platform_lib.paths.sessions_dir()` (cleanmatic's export at `.claude/skills/_shared/lib/telemetry_paths.py:24`)
- **ADD:** Import formatters from cleanmatic's shared lib (if not present, port HA's markdown_table + json_output helpers)
- **Effort:** ~30 lines changes (path + import swaps); logic unchanged

---

### 1.2 Memory Health (check-memory-system-health.py)

**Purpose:** Scans memory dir, validates frontmatter (name, description, type ∈ {user,feedback,project,reference}), detects orphans/dead-links/duplicates/staleness. Dry-run repair (--fix) or apply (--fix --apply).

**HA Inputs:**
- Source: `paths.memory_dir()` → `~/.claude/projects/{encoded-root}/memory/`
- Reads: MEMORY.md index + *.md memory files (excluding MEMORY.md)
- Frontmatter: {name, description, metadata.type} (type may nest under metadata or top-level)
- Link syntax: `[[name]]` (case-insensitive, regex `\[\[([a-z0-9][a-z0-9-]*)\]\]`)
- Staleness: default 30 days, project-type 14 days

**Core Algorithm:**
1. Glob memory_dir/*.md (skip MEMORY.md index)
2. For each: extract frontmatter, check for missing fields + invalid type
3. Collect all [[links]] in text
4. Parse MEMORY.md index entries (regex extract filenames)
5. Compute: orphans (files not in index), dead entries (index points to no file), broken links, duplicates (same name, multiple files), stale (mtime > threshold)
6. Fix (if --apply): remove dead index lines

**Output Dict Shape:**
```json
{
  "memory_dir": "/path/to/memory",
  "count": 12,
  "orphans": ["file1.md"],
  "dead_entries": ["file2.md"],
  "broken_links": [{"from": "file1.md", "to": "[[missing-name]]"}],
  "duplicates": {"name": ["file1.md", "file2.md"]},
  "stale": [{"file": "old.md", "type": "project", "age_days": 45}],
  "invalid_frontmatter": [{"file": "bad.md", "missing": ["name"], "invalid_type": true}],
  "type_distribution": {"user": 3, "project": 5, "(none)": 1},
  "issue_count": 8,
  "status": "RED|YELLOW|GREEN"
}
```

**Dependencies:**
- `platform_lib.paths.memory_dir()`
- `platform_lib.markdown_parser.extract_frontmatter()`
- `platform_lib.formatters.{markdown_table, json_output}`

**Cleanmatic Port Deltas:**
- **STRIP:** No framework logic
- **KEEP:** Regex, staleness thresholds, duplicate detection, fix-diff logic all portable
- **ADD:** Call `telemetry_paths.memory_dir()` (cleanmatic's export missing; must add)
- **ADD:** Port `extract_frontmatter()` helper or vendor it
- **ADD:** Port formatters (markdown_table, json_output)
- **NEW FILE:** cleanmatic/.claude/skills/_shared/lib/memory_health.py (shared logic module)
- **Effort:** ~50 lines porting; ~30 lines new memory_dir export in telemetry_paths.py

---

### 1.3 Workflow Chains (analyze-workflow-chains.py)

**Purpose:** Reconstructs actual skill sequences per session from invocations.jsonl sink; compares against declared chains in routing docs to flag deviations.

**HA Inputs:**
- Source: `paths.TELEMETRY / "invocations.jsonl"` (written by track-skill-invocation hook)
- Records: {ts, skill, session, via} (via ∈ {PreToolUse:Skill, UserPromptExpansion})
- Invocation format: skill as directory-name ("com-git") or reference form ("com:git")
- Routing docs: .claude/rules/{skill-workflow-routing.md, skill-domain-routing.md}
- Chain syntax: "/ck:plan → /ck:cook → /ck:test" (regex: `(/?[a-z]+:[a-z-]+(?:\s*→\s*/?[a-z]+:[a-z-]+)+)`)

**Core Algorithm:**
1. Parse invocations.jsonl; group by session, sort by ts → list of skills per session
2. Parse routing docs; extract declared chains (regex match; split by →)
3. Compute: actual chain frequencies (Counter), deviations (observed multi-step chains not in declared set)
4. Grade: only flag deviations if session count ≥ min_sessions (default 5)

**Output Dict Shape:**
```json
{
  "days": 30,
  "sessions_analyzed": 15,
  "sufficient": true,
  "min_sessions": 5,
  "common_chains": [
    {"chain": "plan → cook → test", "count": 8},
    {"chain": "scout → debug", "count": 5}
  ],
  "declared_chains": ["plan → cook → test", "scout → debug → brainstorm"],
  "deviations": [
    {"chain": "plan → ship", "count": 2}
  ]
}
```

**Dependencies:**
- `platform_lib.paths.TELEMETRY` (for invocations.jsonl sink path)
- `platform_lib.skill_ids.to_skill_ref()` — convert "com-git" → "com:git" for normalization
- `platform_lib.formatters.{markdown_table, json_output}`

**Cleanmatic Port Deltas:**
- **STRIP:** `skill_ids.to_skill_ref()` (HA's framework-prefix logic) → cleanmatic has NO frameworks; skill names ARE flat refs like "product-spec"
  - REPLACE: `skill = rec.get("skill")` (cleanmatic records flat slug already; no frame prefix conversion needed)
  - DELETE: all `to_skill_ref()` calls
- **CHANGE:** Routing doc path: HA reads from `.claude/rules/skill-*.md` (same in cleanmatic; no change needed)
- **ADD:** Export TELEMETRY from telemetry_paths.py
- **ADD:** Port `formatters` module
- **Effort:** ~20 lines (remove skill_ids import + to_skill_ref calls); logic otherwise intact

---

### 1.4 Subagent Reliability (track-subagent-reliability.py)

**Purpose:** Classifies subagent-transcript outcomes (success|api_error|timeout|incomplete) post-hoc; aggregates success rate + failure modes per agent type.

**HA Inputs:**
- Source: `paths.sessions_dir() / "**/subagents/agent-*.jsonl"` (glob subagent transcripts)
- Records: tail of each transcript (last line → stop_reason, errors)
- Agent type extraction: `agent-{type}-{id}.jsonl` → take leading pure-alpha tokens before first id-like segment (digits)
- Error classification: reuses `com-health-check` core module functions (classify_error, extract_error_text, read_tail_jsonl_lines)

**Core Algorithm:**
1. Glob all subagent-*.jsonl files (filtered by --days)
2. For each: extract agent-type from filename; classify outcome:
   - If last message has stop_reason in (end_turn, stop_sequence) AND no tool_use blocks → success
   - Else extract error text; classify (retryable|non-retryable) → api_error + mode
   - Else (no clean stop, no terminal error) → timeout (process abandoned)
   - Else → incomplete (empty transcript)
3. Aggregate: counts per agent-type + success_rate; top failure modes

**Output Dict Shape:**
```json
{
  "days": 30,
  "total": 42,
  "rows": [
    {
      "agent_type": "code-reviewer",
      "total": 15,
      "success": 12,
      "api_error": 2,
      "timeout": 1,
      "incomplete": 0,
      "success_rate": 80
    }
  ],
  "top_failure_modes": [
    ["context-window-exceeded", 3],
    ["timeout", 2]
  ]
}
```

**Dependencies:**
- `platform_lib.paths.sessions_dir()`
- `platform_lib.formatters.{markdown_table, json_output}`
- `com-health-check/scripts/monitor-session-health-core.py` (error classification core)
  - Functions: `read_tail_jsonl_lines()`, `classify_error()`, `extract_error_text()`

**Cleanmatic Port Deltas:**
- **STRIP:** No framework logic in agent-type extraction
- **CHANGE:** Subagent transcript location: HA stores at `~/.claude/projects/{encoded-root}/subagents/agent-*.jsonl`; cleanmatic uses same (verified in emit_session_summary.py:32-34 slug derivation)
- **ADD:** Port or vendor `com-health-check` core module (error classification); OR rewrite outcome logic inline (short decision tree)
- **ADD:** Export sessions_dir from telemetry_paths.py
- **Effort:** ~40 lines porting; ~60 lines if inlining error classification (recommended: vendor the core to reuse)

---

## PART 2: New Sinks Required (errors.jsonl + script-telemetry.jsonl)

cleanmatic currently writes to: `invocations.jsonl`, `hook-telemetry.jsonl`, `sessions.jsonl`. To port reliability + script telemetry lenses, 2 new sinks must be added.

### 2.1 errors.jsonl Schema & Writer

**Purpose:** Structured error emission from skill scripts (explicit failures + unhandled crashes).

**Record Schema:**
```json
{
  "ts": "2026-06-07T15:28:30Z",
  "script": "path/to/script.py",
  "category": "parse|io|validation|api|import|unhandled",
  "message": "error description (truncated to 200 chars)",
  "context": { "field": "value", "frame": "stack-trace-excerpt" }
}
```

**Writers:**
1. **Explicit emit_error() calls** (HA: platform_lib/errors.py) — skill scripts call `emit_error(category, message, context)` on caught-but-real failures
2. **Auto-crash handler** (HA: platform_lib/telemetry.py:_excepthook) — registers an atexit + excepthook to auto-capture unhandled crashes

**Where to Hook:**
- **Option A (cleanmatic-style):** Add Python function `emit_error(category, message, context, *, script=None)` to `.claude/skills/_shared/lib/telemetry_paths.py`; call `append_event("errors.jsonl", {...})`. Skills import and use directly.
- **Option B (shared core):** Create new module `.claude/skills/_shared/lib/error_emission.py` with auto-excepthook registration (mirrors HA platform_lib).

**Cleanmatic Implementation Touchpoint:**
- File: `.claude/skills/_shared/lib/telemetry_paths.py`
- Add function (after append_event_once, ~10 lines):
  ```python
  def emit_error(category: str, message: str, context: dict | None = None, *, script: str | None = None) -> None:
      """Emit a structured error record to errors.jsonl."""
      import sys
      import time
      append_event("errors.jsonl", {
          "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "script": script or (sys.argv[0] if sys.argv else "unknown"),
          "category": category,
          "message": str(message)[:200],
          "context": context or {},
      })
  ```

**No hook needed:** Skill scripts call emit_error() directly when they catch real errors. Auto-crash capture requires optional atexit registration (only if needed for reliability tracker; cleanmatic can defer).

---

### 2.2 script-telemetry.jsonl Schema & Writer

**Purpose:** Auto-capture script execution metrics (duration, exit code, argv sample).

**Record Schema:**
```json
{
  "ts": "2026-06-07T15:28:30Z",
  "script": "path/to/script.py",
  "exit": 0,
  "ms": 5420,
  "argv": ["--flag", "value", "positional"]
}
```

**Writer:** Auto-atexit handler (registers on import). Tracks script start time + exit state (failed = unhandled exception caught).

**Where to Hook:**
- **Option A (lazy):** Skills manually call `log_script_metrics()` at end
- **Option B (auto, HA-style):** On module import, register atexit handler + excepthook to auto-capture

**Cleanmatic Implementation Touchpoint:**
- File: `.claude/skills/_shared/lib/telemetry_paths.py` (or new file `script_metrics.py`)
- Add (auto-registers on import):
  ```python
  import atexit
  import sys
  import time
  
  _start_time = time.time()
  _failed = False
  
  def _auto_log_script_metrics():
      append_event("script-telemetry.jsonl", {
          "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "script": sys.argv[0] if sys.argv else "unknown",
          "exit": 1 if _failed else 0,
          "ms": int((time.time() - _start_time) * 1000),
          "argv": sys.argv[1:6],
      })
  
  atexit.register(_auto_log_script_metrics)
  ```

**Optional:** Also wrap sys.excepthook to set _failed=True on unhandled exception (allows exit-code classification).

---

### 2.3 TaskCompleted Hook for Subagent Outcome

**Purpose:** Log subagent task completion outcomes (success vs blocked vs timed-out) for reliability tracking.

**Current State:** cleanmatic has `task-completed-handler.cjs` (HA's hook); it reads task_id/task_subject/team_name but does NOT record outcome.

**New Requirement:** When a subagent completes its task (SubagentStop event), emit one record to a new `subagent-outcomes.jsonl` sink:

```json
{
  "ts": "2026-06-07T15:28:30Z",
  "task_id": "1",
  "agent_type": "code-reviewer",
  "outcome": "success|timeout|blocked|api_error",
  "message": "brief outcome description"
}
```

**Implementation Touchpoint:**
- File: `.claude/hooks/task-completed-handler.cjs` (existing)
- Add logic (after line 81, logCompletion call):
  - Read task status (from payload or infer from transcript)
  - Classify outcome (need logic: if status=='completed' → success; if 'blocked' → blocked; else infer from transcript tail)
  - Call Python helper to append to `subagent-outcomes.jsonl`

**Alternative (simpler):** Create new hook `subagent-outcome-logger.py` registered on `SubagentStop` event:
- File: `.claude/hooks/subagent-outcome-logger.py` (new, ~50 lines)
- Register in `.claude/settings.json` under SubagentStop hooks
- Reads: task status from Hook payload + tail of subagent transcript
- Classifies outcome using same logic as reliability tracker (stop_reason, error text)
- Appends to `subagent-outcomes.jsonl`
- Add to settings.json hook registration:
  ```json
  "SubagentStop": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/skills/.venv/bin/python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/subagent-outcome-logger.py"
        }
      ]
    }
  ]
  ```

---

## PART 3: telemetry_paths.py Gaps & Exports Needed

**Current Exports (cleanmatic):**
- `project_dir() → str` — resolves CLAUDE_PROJECT_DIR env or cwd
- `telemetry_dir() → Path` — .claude/telemetry/
- `sink_path(name) → Path` — telemetry_dir() / name
- `append_event(name, record)` — write to sink (fail-open)
- `append_event_once(name, record, dedup_key)` — append guarded by dedup marker

**Missing Exports (required for port):**

1. **sessions_dir() → Path**
   - Return: `Path.home() / ".claude" / "projects" / {encoded_root}`
   - Location: telemetry_paths.py:25 (after project_dir)
   - Logic: encode project_dir path (/ → -) to match Claude Code's project-id convention
   - Used by: forensics (find *.jsonl), reliability (find subagents/agent-*.jsonl)

   ```python
   def sessions_dir() -> Path:
       """Claude Code's per-project session-JSONL dir (== project_dir).
       
       CK_SESSIONS_DIR overrides it (tests point it at a tmp dir)."""
       env = os.environ.get("CK_SESSIONS_DIR")
       if env:
           return Path(env)
       enc = str(project_dir()).replace("/", "-")
       return Path.home() / ".claude" / "projects" / enc
   ```

2. **memory_dir() → Path**
   - Return: `sessions_dir() / "memory"`
   - Override: CK_MEMORY_DIR env
   - Used by: memory-health scanner
   - ~4 lines

   ```python
   def memory_dir() -> Path:
       """Claude Code's per-project persistent memory dir.
       
       CK_MEMORY_DIR overrides it (tests point it at a tmp dir)."""
       env = os.environ.get("CK_MEMORY_DIR")
       if env:
           return Path(env)
       return sessions_dir() / "memory"
   ```

3. **TELEMETRY → Path (module-level constant)**
   - Same as telemetry_dir() (already exists as function)
   - Add: `TELEMETRY = Path(os.environ.get("CK_TELEMETRY_DIR")) if os.environ.get("CK_TELEMETRY_DIR") else Path(project_dir()) / ".claude" / "telemetry"`
   - Used by: workflow-chains analyzer (invocations.jsonl location)

4. **SKILLS → Path (module-level constant, for future use)**
   - Value: `Path(project_dir()) / ".claude" / "skills"`
   - Used by: to locate skill directories
   - Optional, but useful for skill-inventory scripts

**Implementation:** Add to `.claude/skills/_shared/lib/telemetry_paths.py` after project_dir definition (~15 lines total).

---

## PART 4: Port Checklist per Script

### Script 1: parse-session-jsonl-forensics.py ✓

| Item | Status | Details |
|------|--------|---------|
| Core logic portable? | YES | Streaming JSONL parser, token aggregation, duration calc all platform-neutral |
| Framework-logic to strip? | NO | No framework prefixes in cleanmatic |
| Path exports needed? | sessions_dir | Add sessions_dir() to telemetry_paths.py |
| Formatters needed? | YES | Port HA's markdown_table + json_output, or use similar |
| New sinks? | NO | Reads invocations.jsonl (already exists) |
| Hook changes? | NO | |
| Effort estimate | 30 lines changes | Import swaps + path call changes |

### Script 2: check-memory-system-health.py ✓

| Item | Status | Details |
|------|--------|---------|
| Core logic portable? | YES | Frontmatter parsing, link detection, staleness all platform-neutral |
| Framework-logic to strip? | NO | |
| Path exports needed? | memory_dir | Add memory_dir() to telemetry_paths.py |
| Markdown parser needed? | YES | Port extract_frontmatter or use regex |
| New sinks? | NO | Reads MEMORY.md + memory/*.md files |
| Hook changes? | NO | |
| Effort estimate | 50 lines porting + 30 lines new export | Creates shared logic module |

### Script 3: analyze-workflow-chains.py ✓

| Item | Status | Details |
|------|--------|---------|
| Core logic portable? | YES | Chain counting, deviation detection all portable |
| Framework-logic to strip? | YES | DELETE all skill_ids.to_skill_ref() calls (cleanmatic has no frameworks) |
| Path exports needed? | TELEMETRY | Add TELEMETRY constant to telemetry_paths.py |
| Routing doc update? | NO | .claude/rules/skill-workflow-routing.md already exists; same format |
| New sinks? | NO | Reads invocations.jsonl |
| Hook changes? | NO | |
| Effort estimate | 20 lines changes | Remove skill_ids import + to_skill_ref calls |

### Script 4: track-subagent-reliability.py ✓

| Item | Status | Details |
|------|--------|---------|
| Core logic portable? | PARTIAL | Error classification logic is portable; subagent-type extraction is |
| Framework-logic to strip? | NO | Agent-type extraction (filename parsing) is framework-agnostic |
| Path exports needed? | sessions_dir | Add sessions_dir() to telemetry_paths.py |
| Error classification? | YES | OPTION: vendor HA's com-health-check core OR inline simple version |
| New sinks? | subagent-outcomes.jsonl | Writes outcome records (new) |
| Hook changes? | YES | Add SubagentStop hook (subagent-outcome-logger.py) to track outcomes |
| Effort estimate | 60 lines porting + 50 lines new hook | Vendor core OR rewrite classification inline |

---

## PART 5: Unresolved Questions

1. **Error Classification Core:** Should cleanmatic vendor HA's `com-health-check/scripts/monitor-session-health-core.py` as a shared module, or rewrite the outcome classification inline (stop_reason check + error regex)? Vendoring enables code reuse; inline keeps cleanmatic self-contained.

2. **Script Telemetry Auto-Register:** Should script-telemetry.jsonl auto-capture be optional (lazy `log_script_metrics()` call in each skill script) or always-on (atexit registration)? HA does always-on; cleanmatic may prefer explicit calls for clarity.

3. **subagent-outcomes.jsonl Outcome Inference:** When a subagent task is marked completed, how do we classify outcome (success vs timeout vs blocked)? Options:
   - Read task status from Hook payload (if available)
   - Infer from transcript tail (same as reliability tracker)
   - Accept outcome as parameter from TaskCompleted hook (if Claude Code passes it)

4. **Memory DIR Resolution in Tests:** Does cleanmatic's pytest setup already set CK_MEMORY_DIR, or will memory_dir() need a fallback discovery heuristic (like HA's walk-up-for-.claude)?

5. **Skill Inventory Tracking:** Does cleanmatic want an invocation-level skill catalog (which skills are installed / active)? This would require exporting SKILLS path + a script to inventory .claude/skills/*/SKILL.md metadata.

---

## Summary

**Port Scope:**
- **4 scripts:** forensics (30L), memory-health (50L), chains (20L), reliability (60L) = ~160 lines porting + vendor/rewrite
- **2 new sinks:** errors.jsonl + script-telemetry.jsonl (schema defined; <50 lines writers)
- **1 new hook:** subagent-outcome-logger.py (50 lines) on SubagentStop
- **3 path exports:** sessions_dir, memory_dir, TELEMETRY constant (~20 lines to telemetry_paths.py)

**Total Effort:** ~250 lines new code + ~150 lines porting (cleanmatic team-size: 1 researcher + 1 implementer, ~4-6h total).

**Risk:** LOW (HA scripts are deterministic, read-only; new sinks are append-only; hook is fail-open). Highest uncertainty: error classification logic reuse vs rewrite.

---

**Report End**
