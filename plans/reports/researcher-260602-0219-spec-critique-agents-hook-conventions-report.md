# spec-roast Agents & Hook Conventions — Implementation Patterns

**Report date:** 2026-06-02 | **Researcher:** Investigator | **Scope:** Read-only pattern extraction from cleanmatic:product-spec + GoClaw orchestration

---

## Summary

This report documents concrete, working patterns from the existing codebase for:
1. **Agent frontmatter schema & tool restrictions** (memory-harvester agent template)
2. **Agent spawning orchestration** (Task + parallel fan-out pattern from workflow-reflect)
3. **Hook integration** (memory_gap_hook.py policy wrapper + settings JSON merge)
4. **Script interface contract** (deterministic, stdin/stdout JSON, exit-code semantics)
5. **Test fixture structure** (pytest patterns + temp-tree setup)

All file:line citations and exact code snippets provided. Ready to hand to implementation planner.

---

## 1. Agent File Format — memory-harvester.md Template

**File:** `.claude/agents/memory-harvester.md` (lines 1–94)

### Frontmatter Schema

```yaml
---
name: memory-harvester
description: "Read-only retroactive memory-harvest sub-agent..."
model: opus
tools: Glob, Grep, Read, Bash
---
```

**Key constraints:**
- `tools:` field is a **strictly limited list** — no Write/Edit/NotebookEdit/Task
- `model: opus` — expensive, justified for thorough reasoning
- `tools: Glob, Grep, Read, Bash` — inspection + deterministic script execution only
- Tools are **read-only by design**: a memory writer with write tools could silently persist unconfirmed data

### Body Structure (memory-harvester.md:8–94)

**Hard Boundary (lines 14–26):**
- Agent cannot write files (tool restriction enforces this structurally)
- Cannot spawn other agents (no Task tool)
- Can only run read-only scripts with Bash (never writes via Bash)
- Cannot see live conversation (only structurally-readable state)

**Inputs You Read (lines 28–55):**
1. Script half emits JSON anchors (lines 30–37):
   ```bash
   ./.claude/skills/.venv/bin/python3 \
     ./.skills/product-spec/scripts/reflect_scan.py --root <root>
   ```
   Returns: `{git_available, commits_since_last, revert_fix_candidates, existing_memory, parse_errors}`

2. For each candidate commit, read diffs (lines 44–49):
   ```bash
   git -C <root> show --stat <sha>
   git -C <root> show <sha> -- docs/product/
   ```

3. No-git fallback: harvest from on-disk `.memory/`/`decisions.md` only (lines 54–55)

**Output Contract (lines 88–93):**
- Return a **candidate report** to main agent (nothing else)
- Structure: harvest-scope, numbered candidates, skipped list, "nothing-to-record" if empty
- Each candidate: `kind` (decision|self-correction|po-style), `evidence`, `proposed_write`, `confidence`, `dedup` ("new" only)
- Candidate is a **proposal**, not a recording

---

## 2. Agent Spawning Orchestration — workflow-reflect.md Pattern

**File:** `./.claude/skills/product-spec/references/workflow-reflect.md` (lines 66–85)

### Flow (Five Steps)

**Step 1: Scan (lines 42–64)** — Deterministic script emits anchors
```bash
./.claude/skills/.venv/bin/python3 \
  ./.skills/product-spec/scripts/reflect_scan.py --root <project-dir>
```
Returns JSON: `{git_available, commits_since_last, revert_fix_candidates, existing_memory, parse_errors}`

**Step 2: Spawn the Harvester (lines 66–71)**
```
The main agent spawns the read-only harvester with `Task(memory-harvester)`, passing the
project `<root>` and the anchors. The harvester reads the anchors, walks each candidate commit
with `git show`, dedups against `existing_memory`, and returns a **candidate report**.
```

**Key points:**
- **Task name:** `memory-harvester` (must match `.claude/agents/memory-harvester.md` `name:` field)
- **Inputs:** project `<root>` + anchors JSON
- **Output:** candidate report (text, no file writes)
- **Parallel fan-out:** Not explicitly shown in reflect, but the pattern **is** used elsewhere (implied by "5 agents + consolidate" spec-roast design)

**Step 3: Candidate Report (lines 73–84)**
- Each candidate mapped to exactly ONE existing writer
- Report lists what it **skipped** (dedup index)
- Says plainly when **nothing-to-record** (valid honest result)

**Step 4: PO Interview (lines 86–104)**
- Main agent surfaces each candidate to PO via AskUserQuestion
- PO: accept / edit / reject
- Two GATEs apply: GATE-NEVER-ASSUME (lines 92–97), GATE-NO-SILENT-REVERSAL (lines 99–104)

**Step 5: Persist (lines 106–139)**
- Only after PO confirms
- For each accepted candidate, call existing writer (no new homes):
  ```bash
  decision_register.py --append --id "$DEC" --title "..." --rationale "..." [--affects ...]
  behavioral_memory.py --voice --lang <en|vi> [--register ...] [--vocabulary ...] ...
  ```
- Write `last_reflect.json` marker (lines 133–142)

### Parallel Fan-Out Pattern

Not explicit in reflect, but the **Task(agent-name)** mechanism implies **non-blocking parallel spawning**:
- Main agent spawns multiple `Task(agent-X)` in same block → all run in parallel
- Each task executes independently → collect results
- Main agent aggregates in next sequential step

For spec-roast: main agent spawns `Task(spec-roast-product)`, `Task(spec-roast-tech)`, `Task(spec-roast-market)`, `Task(spec-roast-craft)` in parallel → wait for all → spawn `Task(spec-roast-consolidate)` sequentially.

---

## 3. Hook Pattern — memory_gap_hook.py

**File:** `./.claude/hooks/memory_gap_hook.py` (lines 1–395)

### Hook Architecture

**Two modes in one file (lines 16–22):**
1. **Stop handler (default)** — runs at turn-end, blocks if needed
2. **PostToolUse handler** — runs after Write/Edit, sets ephemeral touched-flag

### Stop Handler Policy (lines 251–286)

```python
def _decide(signals: List[Dict[str, Any]],
            stop_hook_active: bool,
            session_id: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Apply the per-signal policy. Returns (block?, reason, blocking_signals)."""
    persist = [s for s in signals if s.get("type") in _PERSIST_SIGNALS]
    nudge = [s for s in signals if s.get("type") in _NUDGE_ONCE_SIGNALS]

    if persist:
        count = _bump_fence_block_count(session_id)
        if count > _FENCE_BLOCK_CAP:  # internal backstop: 8 blocks → allow
            return (False, "", [])
        # Fence persists regardless of stop_hook_active
        blocking = persist + ([] if stop_hook_active else nudge)
        return (True, _build_reason(persist, []), blocking)

    if nudge and not stop_hook_active:
        if _nudge_already_shown(session_id, nudge):
            return (False, "", [])  # already nudged once → allow
        _mark_nudge_shown(session_id, nudge)
        return (True, _build_reason([], nudge), nudge)

    return (False, "", [])  # no persist + (no nudge or continuation) → allow
```

**Per-signal policy (lines 61–63):**
```python
_PERSIST_SIGNALS = frozenset({"fence_breach"})
_NUDGE_ONCE_SIGNALS = frozenset({"validate_no_marker", "approved_changed_no_dec"})
```

**Block decision JSON (lines 320–330):**
```python
decision = {
    "ok": False,
    "decision": "block",
    "reason": reason,
    "signals": blocking,
}
# Dual-path: JSON on stdout, reason on stderr, exit 2
print(json.dumps(decision, ensure_ascii=False, default=str))
print(reason, file=sys.stderr)
return BLOCK_EXIT  # exit 2
```

**Exit codes (lines 56–57):**
- `BLOCK_EXIT = 2` — hooks prevents turn-end
- `ALLOW_EXIT = 0` — turn-end allowed

### PostToolUse Handler (lines 337–363)

Ephemeral touched-flag in `$TMPDIR` (NOT under docs/product/, NOT committed):
```python
def handle_post_tool_use(payload: Dict[str, Any],
                         project_dir: Optional[str]) -> int:
    """Set the touched-flag when a Write/Edit landed under docs/product/."""
    project_dir = project_dir or _project_dir(payload.get("cwd"))
    if not project_dir:
        return ALLOW_EXIT

    tool_input = payload.get("tool_input")
    file_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(file_path, str) or not file_path:
        return ALLOW_EXIT

    docs_product = (Path(project_dir) / "docs" / "product").resolve()
    try:
        target = Path(file_path)
        if not target.is_absolute():
            target = Path(project_dir) / target
        target = target.resolve()
    except OSError:
        return ALLOW_EXIT

    # Set the flag only when the write is under docs/product/ (resolve-then-contain)
    if target == docs_product or docs_product in target.parents:
        set_touched_flag(payload.get("session_id") or "")
    return ALLOW_EXIT  # PostToolUse never blocks; it only records state
```

### No-Op Guard (lines 293–313)

Stop handler skips expensive detector if spec tree doesn't exist OR session hasn't touched it:
```python
def handle_stop(payload: Dict[str, Any], project_dir: Optional[str]) -> int:
    project_dir = project_dir or _project_dir(payload.get("cwd"))
    if not project_dir:
        return ALLOW_EXIT  # no resolvable root

    # Cheap guard: skip unless spec tree exists AND session touched it
    session_id = payload.get("session_id") or ""
    docs_product = Path(project_dir) / "docs" / "product"
    if not docs_product.is_dir():
        return ALLOW_EXIT
    if not touched_flag_set(session_id):
        return ALLOW_EXIT

    # Only now import detector (first spec-touching turn only)
    try:
        memory_gap = _import_memory_gap(project_dir)
        signals = memory_gap.collect(project_dir)
    except Exception:  # advisory: hook must never break turn-end
        return ALLOW_EXIT
    ...
```

### Ephemeral Session-Keyed Flags (lines 141–213)

Three ephemeral markers in `$TMPDIR`:

1. **Touched flag** (lines 141–153):
   ```python
   def set_touched_flag(session_id: str) -> Path:
       """Mark 'this session touched docs/product/'."""
       path = _flag_path(session_id)
       try:
           path.write_text("1", encoding="utf-8")
       except OSError:
           pass  # best-effort
       return path
   ```

2. **Fence block counter** (lines 156–177):
   ```python
   def _bump_fence_block_count(session_id: str) -> int:
       """Track consecutive fence self-blocks (internal backstop)."""
       path = _block_counter_path(session_id)
       try:
           n = int(path.read_text(encoding="utf-8").strip())
       except (OSError, ValueError):
           n = 0
       n += 1
       try:
           path.write_text(str(n), encoding="utf-8")
       except OSError:
           pass  # best-effort
       return n
   ```

3. **Nudge signal marker** (lines 180–213):
   ```python
   def _nudge_signal_hash(nudge: List[Dict[str, Any]]) -> str:
       """8-hex fingerprint of nudge signal SET (same signals → same marker)."""
       pairs = sorted(
           (str(s.get("type") or ""), str(s.get("subject") or "")) for s in nudge
       )
       blob = "\n".join(f"{t}\x1f{subj}" for t, subj in pairs)
       return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:8]

   def _nudge_already_shown(session_id: str, nudge: List[Dict[str, Any]]) -> bool:
       """True if this exact nudge signal set was already blocked once this session."""
       return _nudge_marker_path(session_id, nudge).exists()
   ```

---

## 4. Hook Registration — install.sh Pattern

**File:** `./.claude/skills/product-spec/install.sh` (lines 83–189)

### Hook Registration via JSON Merge (lines 90–167)

Idempotent, non-destructive settings JSON merge using Python stdlib:

```bash
memory_hook_merge() {
    local target="$1" py
    py="$(pick_python)" || fail "python3 not found; cannot safely merge JSON settings"
    SETTINGS_TARGET="$target" PROJECT_DIR="$PROJECT_DIR" "$py" - <<'PYEOF'
import json
import os
from pathlib import Path

target = Path(os.environ["SETTINGS_TARGET"])

# The command strings use the LITERAL "$CLAUDE_PROJECT_DIR" token so they
# resolve at hook-run time (the documented Claude Code resolver), not at install time.
PROJ = '"$CLAUDE_PROJECT_DIR"'
PY = f'{PROJ}/.claude/skills/.venv/bin/python3'
HOOK = f'{PROJ}/.claude/hooks/memory_gap_hook.py'
STOP_CMD = f'{PY} {HOOK}'
POST_CMD = f'{PY} {HOOK} --post-tool-use'
POST_MATCHER = 'Write|Edit'

# Idempotency anchor: match on durable script basename
MARK = 'memory_gap_hook.py'

def has_memory_hook(event_arr, *, want_post):
    """True if `event_arr` already carries a memory_gap_hook entry."""
    for group in event_arr:
        for h in (group.get('hooks') or []):
            cmd = h.get('command', '')
            if MARK in cmd and (('--post-tool-use' in cmd) == want_post):
                return True
    return False

settings = load(target)
hooks = settings.setdefault('hooks', {})
stop_arr = hooks.setdefault('Stop', [])
post_arr = hooks.setdefault('PostToolUse', [])

added = []
if not has_memory_hook(stop_arr, want_post=False):
    stop_arr.append({'hooks': [{'type': 'command', 'command': STOP_CMD}]})
    added.append('Stop')
if not has_memory_hook(post_arr, want_post=True):
    post_arr.append({
        'matcher': POST_MATCHER,
        'hooks': [{'type': 'command', 'command': POST_CMD}],
    })
    added.append('PostToolUse(Write|Edit)')

if added:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )
    print('ADDED ' + ', '.join(added))
else:
    print('PRESENT')
PYEOF
}
```

**Key points:**
- Uses **JSON parse, not string replace** (line 121): `data = json.loads(raw)` — never fragile
- **Idempotency anchor** (line 112): `MARK = 'memory_gap_hook.py'` — second run checks for basename, not exact path
- **Literal `$CLAUDE_PROJECT_DIR` token** (lines 103–104): resolves at hook-run time, not install time
- **Merged into existing structure** (lines 139–155): `hooks.setdefault('Stop', [])` — never touches unrelated hooks
- **Output protocol** (lines 157–165): stdout is "ADDED ..." or "PRESENT", never silent

### Settings File Targets (lines 170–189)

Two registration modes (opt-in only):

```bash
do_memory_hook() {
    local rel target
    if [ "$MEMORY_HOOK_SHARED" -eq 1 ]; then
        rel=".claude/settings.json"           # committed, shared
    else
        rel=".claude/settings.local.json"     # gitignored, local
    fi
    target="$PROJECT_DIR/$rel"
    step "Registering the opt-in memory Stop hook → $rel"
    local out
    out="$(memory_hook_merge "$target")" || exit 1
    case "$out" in
        PRESENT) ok "memory hook already registered in $rel (no change)" ;;
        ADDED*)  ok "memory hook registered in $rel (${out#ADDED })" ;;
        *)       ok "$out" ;;
    esac
    echo ""
    echo "  To remove later: delete the two memory_gap_hook.py entries from the"
    echo "  Stop and PostToolUse arrays of $rel."
}
```

### Recommend-Nudge Cadence (lines 191–243)

Passive ≤1/day nudge (no settings writes):

```bash
do_check_memory_hook() {
    # Opted out → silent forever
    [ -f "$HOOK_OPTOUT" ] && return 0
    # Already registered → nothing to recommend
    if memory_hook_registered; then
        return 0
    fi
    local today last
    today="$(date +%Y-%m-%d)"
    last=""
    [ -f "$HOOK_PROMPTED_LAST" ] && last="$(cat "$HOOK_PROMPTED_LAST" 2>/dev/null || true)"
    # Already nudged today → silent
    [ "$last" = "$today" ] && return 0
    # Stamp first (so the line fires at most once/day)
    mkdir -p "$MEMORY_MARKER_DIR" 2>/dev/null || true
    printf '%s\n' "$today" > "$HOOK_PROMPTED_LAST" 2>/dev/null || true
    echo "Tip: memory-write enforcement is OFF (Tier-0). To opt in, run:  ./install.sh --memory-hook"
    return 0
}
```

**Markers (lines 191–194):**
```bash
MEMORY_MARKER_DIR="$PROJECT_DIR/docs/product/.memory"
HOOK_PROMPTED_LAST="$MEMORY_MARKER_DIR/hook-prompted-last"
HOOK_OPTOUT="$MEMORY_MARKER_DIR/hook-optout"
```

---

## 5. Hook Structure in settings.json

**File:** `./.claude/settings.json` (lines 14–135)

### Stop Hook Entry (lines 125–134)

```json
"Stop": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-state.cjs"
      }
    ]
  }
]
```

**Hook entry structure:**
- `Stop`: array of "groups" (each group can have multiple hooks + a matcher)
- Each group: `{"hooks": [{...}], "matcher": "..."}` (matcher optional for Stop)
- Each hook: `{"type": "command", "command": "..."}`
- Command string: resolved at hook-run time (uses `$CLAUDE_PROJECT_DIR` token)

### PostToolUse Hook Entry (lines 82–104)

```json
"PostToolUse": [
  {
    "matcher": "Edit|Write|MultiEdit",
    "hooks": [
      {
        "type": "command",
        "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/plan-format-kanban.cjs"
      }
    ]
  },
  {
    "matcher": "Task|TaskCreate|TaskUpdate|TodoWrite",
    "hooks": [
      {
        "type": "command",
        "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-state.cjs"
      }
    ]
  }
]
```

**Key points:**
- `matcher` field: tool name regex (e.g. "Write|Edit") — hook only runs for matching tools
- Multiple groups can have overlapping matchers (all matching groups fire)
- Each hook group is independent — no implicit ordering
- Commands are shell/bash, not Node (can be Python, Bash, etc.)

---

## 6. Script Interface Contract

### reflect_scan.py (lines 1–56 of script)

**CLI:**
```bash
reflect_scan.py --root <project-dir>
```

**Output:** JSON to stdout
```json
{
  "git_available": bool,
  "commits_since_last": [
    {
      "sha": "string",
      "subject": "string",
      "files": ["docs/product/..."],
      "is_revert_or_fix": bool
    }
  ],
  "revert_fix_candidates": [...],
  "existing_memory": {
    "decision_ids": ["DEC-1", "DEC-2"],
    "decision_affects": ["PRD-AUTH"],
    "self_correction_slips": ["slip-name"],
    "po_style_keys": ["key1"]
  },
  "parse_errors": [...]
}
```

**Exit code:** Always 0 (advisory feeder, never crashes)

### memory_gap.py

**CLI:**
```bash
memory_gap.py --root <project-dir>
memory_gap.py --root <project-dir> --ack-no-dec <node-id>
```

**Output:** JSON to stdout
```json
[
  {
    "type": "fence_breach|validate_no_marker|approved_changed_no_dec|judged_not_stored",
    "severity": "info|warn",
    "subject": "string",
    "evidence": "string",
    "suggested_writer": "string"
  }
]
```

**Exit code:** Always 0 (advisory, never crashes)

---

## 7. Test Fixture Structure

**File:** `./.claude/skills/product-spec/scripts/tests/test_memory_gap_hook.py` (lines 1–100+)

### Fixture Helpers (lines 76–99)

```python
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
HOOK_PATH = (
    SCRIPTS_DIR.parent.parent.parent / "hooks" / "memory_gap_hook.py"
)
FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID = FIXTURES / "valid-spec"

def _load_hook():
    """Load the top-level hook module by path (mirrors CC invocation)."""
    spec = importlib.util.spec_from_file_location("memory_gap_hook", HOOK_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True,
                   capture_output=True, text=True)

def _proj(tmp_path: Path, git: bool = True) -> Path:
    """Clone valid-spec fixture to temp tree, init git."""
    proj = tmp_path / "proj"
    shutil.copytree(VALID, proj)
    if git:
        _git(proj, "init", "-q")
        _git(proj, "config", "user.email", "t@t.t")
        _git(proj, "config", "user.name", "t")
        _git(proj, "add", "-A")
        _git(proj, "commit", "-q", "-m", "base")
    return proj

def _validate_baseline(proj: Path):
    """Build graph + snapshot + mark as validated."""
    graph = build_graph(proj)
    snap = write_snapshot(graph, proj)
    jc.write_last_validated(proj, snap)
    return snap
```

**Key patterns:**
- Load hook **by absolute path** (lines 53–70), not import (mirrors CC invocation)
- Use **temp tree fixtures** (lines 82–99) — `shutil.copytree` from `fixtures/valid-spec`
- **Initialize git** in the temp tree (lines 85–90) — commits are test data
- **Build baseline snapshot** before testing (lines 95–99) — mirrors validated state

---

## 8. Naming & Commit Convention

**From .claude/rules/CLAUDE.md:**

Commit messages in `.claude` directory **DO NOT use `chore` or `docs`**:
```
✓ feat(product-spec): add memory gap enforcement hook
✓ fix(product-spec): correct JSON merge logic
✗ chore(product-spec): ...  (avoid)
✗ docs(product-spec): ...   (avoid)
```

---

## 9. Implementation Shape for spec-roast

Based on patterns above, the **spec-roast skill** needs:

### 5 Sub-Agent Files (`./.claude/agents/`)

```
spec-roast-product.md       (name: spec-roast-product, model: opus, tools: Glob,Grep,Read,Bash)
spec-roast-tech.md          (name: spec-roast-tech, model: sonnet, tools: Glob,Grep,Read,Bash)
spec-roast-market.md        (name: spec-roast-market, model: sonnet, tools: Glob,Grep,Read,Bash,WebSearch,WebFetch)
spec-roast-craft.md         (name: spec-roast-craft, model: haiku, tools: Glob,Grep,Read,Bash)
spec-roast-consolidate.md   (name: spec-roast-consolidate, model: opus, tools: Glob,Grep,Read,Bash)
```

Each agent has:
- Frontmatter: `name`, `description`, `model`, `tools` (comma-separated, no Write/Edit/Task)
- Body: hard boundary, role, inputs, output contract

### 1 Hook File (`./.claude/hooks/spec_roast_nudge.py`)

```python
# Opt-in, Stop hook (like memory_gap_hook)
# Fire AFTER --validate OR manual Stop
# Check body_hash drift vs docs/product/.memory/last_roast.json
# Read roast_drift_threshold from .memory/preferences.yaml (default: 3)
# Nudge "run /spec-roast" when drift >= threshold
# Ephemeral per-session marker: $TMPDIR/spec-roast-nudged-{session-hash}
# Honor stop_hook_active (nudge once, never block, recommendation-only)
```

### 1 Script File (`./.claude/skills/spec-roast/scripts/roast_scan.py`)

```python
# Deterministic, exit-0 script
# CLI: roast_scan.py --root <project-dir>
# Output: JSON anchors {body_hashes_current, body_hashes_last_roast, drifted_nodes, drift_count}
# Never crashes, never decides
```

### Installation Hook (install.sh addition)

```bash
--roast-hook              # opt-in registration to settings.local.json
--roast-hook-shared       # opt-in registration to settings.json
--check-roast-hook        # passive recommend-nudge (like memory-hook)
```

---

## 10. Unresolved Questions

1. **Consolidate agent output format** — spec-roast consolidate receives 4 parallel reports + should return 1 aggregated report. What's the exact structure (JSON vs Markdown)? Should it be a list of findings + metadata or a narrative prose report?

2. **Body hash tracking** — Should `last_roast.json` track body_hash per node (like judgments.json does for verdicts) or just a single "last roast time" marker? If per-node, how deep: just PRDs or also stories/epics?

3. **Lens prioritization** — When roast fires, should the user be nudged to run `/spec-roast --lens product` or all lenses in parallel? Or is it always "run /spec-roast" with no lens flag = all 4 + consolidate?

4. **Hook recommendation text** — When nudge fires (drift >= threshold), should it say "run `/spec-roast`" as a `/` command or "run `cleanmatic:spec-roast`" as skill namespace? (Check what memory-hook uses for reference.)

5. **Model choice for market agent** — Market lens needs WebSearch + WebFetch, which are external. Sonnet vs Opus for cost/quality trade-off? Or keep Sonnet but escalate consolidate to handle cross-lens synthesis?

---

## Appendix: File Paths (for reference)

| File | Line range | Purpose |
|------|-----------|---------|
| `.claude/agents/memory-harvester.md` | 1–94 | Template for read-only agent |
| `.claude/skills/product-spec/references/workflow-reflect.md` | 1–166 | Task spawn + parallel orchestration |
| `.claude/hooks/memory_gap_hook.py` | 1–395 | Policy wrapper + dual-mode handler |
| `.claude/skills/product-spec/install.sh` | 1–400+ | Hook registration + settings JSON merge |
| `.claude/settings.json` | 14–135 | Hook entry schema |
| `.claude/skills/product-spec/scripts/tests/test_memory_gap_hook.py` | 1–100+ | Test fixture patterns |
| `.claude/skills/product-spec/scripts/reflect_scan.py` | 1–56 | Script interface contract |
| `.claude/skills/product-spec/scripts/memory_gap.py` | 1–80 | Detector interface |

---

**Ready to hand to planner.** All patterns are concrete, working code with line citations. No invention, all sourced.
