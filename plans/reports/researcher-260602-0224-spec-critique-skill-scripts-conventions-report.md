# Research Report: cleanmatic:spec-roast Skill — Script Reuse Conventions & APIs

**Date:** 2026-06-02 | **Status:** Read-Only Investigation Complete | **Scope:** product-spec skill codebase analysis for spec-roast sibling skill development

---

## Executive Summary

The `cleanmatic:product-spec` skill provides a rich, mature foundation for reuse. Spec-roast (a new skill that consumes product-spec's scripts) must:
1. **Reuse the shared venv** `.claude/skills/.venv` (do NOT create its own)
2. **Register its own opt-in memory hook** via `--roast-hook` flag in `install.sh`/`install.ps1`
3. **Invoke existing scripts** (spec_graph, check_traceability, check_consistency, decision_register, judgment_cache) via concrete CLI signatures
4. **Conform to the soft fence** `fs_guard.assert_under_docs_product()` for any new writes
5. **Emit findings** as JSON with product-spec's `make_finding()` shape

All APIs are deterministic, no LLM judgment in the script layer, and all writes pass through the fs_guard chokepoint.

---

## 1. SKILL.md + References Structure

**File:** `.claude/skills/product-spec/SKILL.md` (lines 1–190)

### Frontmatter (lines 1–12)

```yaml
---
name: cleanmatic:product-spec
description: "Interview-driven product spec hierarchy (Vision/BRD/PRD/Epic/Story) with traceability, validation, and visualization for product owners. Use when a non-technical PO needs to capture, structure, validate, or visualize product requirements without writing code."
user-invocable: true
when_to_use: "Invoke when a product owner asks to draft, refine, validate, decompose, approve, summarize, or visualize a product spec (BRD/PRD/Epic/Story) — or when starting a new product from scratch."
category: product
keywords: [ product-owner, prd, brd, epic, story, requirements, traceability, vision, roadmap, validation ]
argument-hint: "[--flag] [target]"
metadata:
  author: cleanmatic
  version: "2.0.0"
---
```

**Spec-roast equivalent structure (RECOMMENDED):**
```yaml
---
name: cleanmatic:spec-roast
description: "LLM-powered red-team audit of product specs: drift detection, tone/bias analysis, implicit assumptions, contradiction discovery. Use when a spec needs adversarial critique beyond validation."
user-invocable: true
when_to_use: "Invoke when a PO spec needs a roast pass (contradiction hunt, drift detection, implicit assumption audit, tone/bias check)."
category: product
keywords: [ product-owner, validation, red-team, audit, drift, contradiction, tone, bias ]
argument-hint: "[--flag] [target]"
metadata:
  author: cleanmatic
  version: "1.0.0"
---
```

### Lean Skeleton Convention (line 127–149)

Product-spec SKILL.md is ~190 lines. The pattern:
- **Lines 1–25**: Frontmatter + one-paragraph intro.
- **Lines 26–76**: Flags table (each row is a CLI option + purpose). Keep descriptions short (< 200 chars per cell).
- **Lines 63–77**: No-flag menu (what happens when invoked without flags).
- **Lines 78–103**: Output contract (directory structure under `docs/product/`).
- **Lines 105–125**: Workflow map (Mermaid flowchart showing action → route → execution).
- **Lines 127–149**: **"Loads references/* on Demand"** section. This is the KEY skeleton convention:
  ```markdown
  ## Loads `references/*` on Demand

  The lean skeleton above stays under ~300 lines; full prose lives in `references/`:

  - `references/frontmatter-and-id-spec.md` — canonical YAML schema…
  - `references/document-model-and-hierarchy.md` — artifact roles…
  - `references/validation-rules-spec.md` — check catalog…
  - [etc.]

  Load only the references relevant to the active flag…
  ```

**Spec-roast pattern (APPLY):**
- Keep SKILL.md under 250 lines.
- Create `references/` subdirectory with:
  - `roast-checks-catalog.md` — the audit check definitions (contradiction, drift, tone, assumption).
  - `roast-evaluation-framework.md` — scoring model, thresholds, hedging rules.
  - `roast-workflow.md` — the full red-team orchestration flow.
- In SKILL.md, load only the reference relevant to the active flag (e.g., `--roast` loads `roast-workflow.md`).

---

## 2. install.sh / install.ps1: Venv Reuse & Hook Registration

**Files:**
- `.claude/skills/product-spec/install.sh` (lines 1–351)
- `.claude/skills/product-spec/install.ps1` (lines 1–80+)

### Shared Venv Creation (Bash)

**Path:** `.claude/skills/.venv` (created at skill _parent_ level, not per-skill)

```bash
# install.sh lines 277–284
VENV_DIR="$SKILLS_DIR/.venv"

step "Setting up virtual environment at $VENV_DIR"
if [ -x "$VENV_DIR/bin/python3" ]; then
    ok "venv already present"
else
    python3 -m venv "$VENV_DIR"
    ok "venv created"
fi
```

**Key:** `SKILLS_DIR` is `$( cd "$SCRIPT_DIR/.." && pwd )` — the `.claude/skills/` parent. The venv is **shared** across all skills under `.claude/skills/`. Idempotent: re-running detects `-x` (executable bit) and skips.

### Opt-in Memory Hook Registration (Bash)

**Reference:** `install.sh` lines 50–267 (the `memory_hook_merge` function + flags)

#### Flags Parsed (lines 54–64)
```bash
DEV=0
MEMORY_HOOK=0          # --memory-hook / --memory-hook-shared requested
MEMORY_HOOK_SHARED=0   # target settings.json (committed) instead of settings.local.json
CHECK_MEMORY_HOOK=0    # --check-memory-hook passive recommend-nudge
MEMORY_HOOK_OPTOUT=0   # --memory-hook-optout: user said "stop asking" → silence the nudge
for arg in "$@"; do
    case "$arg" in
        --dev) DEV=1 ;;
        --memory-hook) MEMORY_HOOK=1 ;;
        --memory-hook-shared) MEMORY_HOOK=1; MEMORY_HOOK_SHARED=1 ;;
        --check-memory-hook) CHECK_MEMORY_HOOK=1 ;;
        --memory-hook-optout) MEMORY_HOOK_OPTOUT=1 ;;
        -h|--help) sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown arg: $arg…" >&2; exit 2 ;;
    esac
done
```

#### Hook Merge Logic (lines 90–167, simplified)
```python
# Inline Python (lines 93–166)
# Reads target settings file (default .claude/settings.local.json, shared → settings.json)
# Merges in Stop + PostToolUse hook entries (idempotent: matches on 'memory_gap_hook.py' basename)
# Writes back JSON (never string-replace; JSON parse first)

MARK = 'memory_gap_hook.py'  # Idempotency anchor: match on script basename

def has_memory_hook(event_arr, *, want_post):
    """True if `event_arr` already carries a memory_gap_hook entry of the right mode."""
    for group in event_arr:
        for h in (group.get('hooks') or []):
            cmd = h.get('command', '')
            if MARK in cmd and (('--post-tool-use' in cmd) == want_post):
                return True
    return False

stop_arr = hooks.setdefault('Stop', [])
post_arr = hooks.setdefault('PostToolUse', [])

if not has_memory_hook(stop_arr, want_post=False):
    stop_arr.append({'hooks': [{'type': 'command', 'command': STOP_CMD}]})
if not has_memory_hook(post_arr, want_post=True):
    post_arr.append({
        'matcher': 'Write|Edit',
        'hooks': [{'type': 'command', 'command': POST_CMD}],
    })

if added:
    target.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + '\n')
```

#### Recommend-Nudge (Tier-0, lines 225–243)
```bash
do_check_memory_hook() {
    # Opted out → silent forever.
    [ -f "$HOOK_OPTOUT" ] && return 0
    # Already registered → nothing to recommend; degrade silently to Tier-0.
    if memory_hook_registered; then return 0; fi
    
    # Already nudged today → silent.
    today="$(date +%Y-%m-%d)"
    last=""
    [ -f "$HOOK_PROMPTED_LAST" ] && last="$(cat "$HOOK_PROMPTED_LAST" 2>/dev/null || true)"
    [ "$last" = "$today" ] && return 0
    
    # Stamp first (so the line fires at most once/day even if the caller loops).
    mkdir -p "$MEMORY_MARKER_DIR" 2>/dev/null || true
    printf '%s\n' "$today" > "$HOOK_PROMPTED_LAST" 2>/dev/null || true
    echo "Tip: memory-write enforcement is OFF (Tier-0). To opt in, run:  ./install.sh --memory-hook"
    return 0
}
```

**Marker files (lines 192–194):**
```bash
MEMORY_MARKER_DIR="$PROJECT_DIR/docs/product/.memory"
HOOK_PROMPTED_LAST="$MEMORY_MARKER_DIR/hook-prompted-last"
HOOK_OPTOUT="$MEMORY_MARKER_DIR/hook-optout"
```

### Windows Equivalent (install.ps1)

**Pattern mirrors Bash exactly.** Key differences:
- Venv path: `.venv\Scripts\python.exe` instead of `.venv/bin/python3`
- JSON merge via Python (same logic, run via `Get-MergePython`)
- Settings path: `.claude\settings.local.json` (backslashes)

**Implementation snippet (install.ps1 lines 72–79):**
```powershell
function Get-MergePython {
    $venvPy = Join-Path $VenvDir "Scripts/python.exe"
    if (Test-Path $venvPy) { return $venvPy }
    foreach ($candidate in @("python", "python3", "py")) {
        if (Get-Command $candidate -ErrorAction SilentlyContinue) { return $candidate }
    }
    return $null
}
```

### **Spec-roast install pattern (MANDATORY)**

For `spec-roast/install.sh`:
1. **Reuse the venv:** `VENV_DIR="$SKILLS_DIR/.venv"` — same as product-spec. Do NOT create a new one.
2. **Add a NEW opt-in flag:** `--roast-hook` (mirrors `--memory-hook`).
3. **Register the hook** with a distinct script anchor, e.g. `roast_audit_hook.py`.
4. **Invoke the shared venv** for any shared dependencies (e.g., pyyaml is already there).
5. **Idempotency marker:** match on the basename `roast_audit_hook.py`, never a hard-coded path.

**Example flag block:**
```bash
ROAST_HOOK=0
for arg in "$@"; do
    case "$arg" in
        --dev) DEV=1 ;;
        --roast-hook) ROAST_HOOK=1 ;;  # NEW FLAG
        --roast-hook-shared) ROAST_HOOK=1; ROAST_HOOK_SHARED=1 ;;
        …
    esac
done
```

---

## 3. preferences.py: Closed-Enum Preferences API

**File:** `.claude/skills/product-spec/scripts/preferences.py` (lines 1–115+)

### Schema & Defaults (lines 43–56)

```python
# The single authoritative home for the preference defaults.
DEFAULTS: Dict[str, Any] = {
    "lang": "en",
    "detail_level": "standard",
    "prioritization": "moscow",
    "dismissed_reminders": [],
}

ENUMS: Dict[str, frozenset] = {
    "lang": frozenset({"en", "vi"}),
    "detail_level": frozenset({"concise", "standard", "verbose"}),
    "prioritization": frozenset({"moscow", "value-effort", "manual"}),
}
```

### Load Function (lines 63–93)

```python
def load(root) -> Dict[str, Any]:
    """Return the resolved preferences: every key present, defaults filled.
    
    A missing file, missing key, out-of-range enum, or unparseable YAML all
    degrade to defaults — this function never raises."""
    resolved = dict(DEFAULTS)
    path = _prefs_path(root)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError):
        return resolved
    if not isinstance(raw, dict):
        return resolved
    
    for key in DEFAULTS:
        if key not in raw:
            continue
        value = raw[key]
        if key in ENUMS:
            if value in ENUMS[key]:
                resolved[key] = value
            # else: leave the default
        elif key == "dismissed_reminders":
            if isinstance(value, list):
                resolved[key] = [str(v) for v in value]
        else:
            resolved[key] = value
    return resolved
```

### Save Function (lines 96–100+)

```python
def save(root, prefs: Dict[str, Any]) -> Path:
    """Validate + write preferences.yaml through the soft fence.
    
    Only known keys are persisted (unknown keys are dropped). A scalar key with a
    value outside its closed enum raises PreferenceError before any write."""
    # [implementation continues]
```

### Path Resolution (lines 59–60)

```python
def _prefs_path(root) -> Path:
    return Path(root) / "docs" / "product" / ".memory" / "preferences.yaml"
```

### **How to add a roast-specific preference**

1. **Add the key to DEFAULTS:**
   ```python
   DEFAULTS: Dict[str, Any] = {
       "lang": "en",
       …
       "roast_drift_threshold": 3,     # NEW: score threshold for flagging drift (1–5)
   }
   ```

2. **Add the enum (if closed):**
   ```python
   ENUMS: Dict[str, frozenset] = {
       …
       # roast_drift_threshold is NOT in ENUMS — it's a numeric scalar, so load() accepts any value
   }
   ```

3. **Load via:**
   ```python
   from preferences import load
   prefs = load(root)
   roast_threshold = prefs.get("roast_drift_threshold", 3)  # default fallback
   ```

4. **Write via:**
   ```python
   from preferences import save, PreferenceError
   try:
       save(root, {"roast_drift_threshold": 4})
   except PreferenceError as e:
       print(f"validation error: {e}")
   ```

---

## 4. spec_graph.py: Ancestry & Graph API

**File:** `.claude/skills/product-spec/scripts/spec_graph.py` (lines 1–259+)

### Top-Level Graph Build (lines 245–256)

```python
def build_graph(root: Path) -> Dict[str, Any]:
    """Top-level: parse, build, return graph JSON shape per visualization-spec.md.
    
    `root_path` is included so downstream checkers can inspect repo-level state
    without needing to be threaded a separate `root` argument."""
    product_dir = root / "docs" / "product"
    if not product_dir.exists():
        return _missing_dir_graph(root)
    artifacts = load_artifacts(product_dir)
    return _assemble_graph(artifacts, product_dir, root)
```

### Node Structure (lines 113–167)

Each node is a `Dict[str, Any]`:
```python
{
    "id": "PRD-AUTH",                    # str, or None if missing
    "type": "prd",                       # str: "product", "vision", "brd", "goal", "prd", "epic", "story"
    "body_hash": "a1b2c3d4",             # str: sha256(body)[:8], or None for goals (no standalone file)
    "title": "Authentication & Authorization",
    "status": "draft",                   # str: "draft" | "review" | "approved", or None
    "scope": "core-value",               # str: "in" | "out" | "core-value", or None
    "moscow": "must",                    # str: "must" | "should" | "could" | "wont", or None
    "horizon": "now",                    # str: "now" | "next" | "later", or None
    "size": "M",                         # str: "S" | "M" | "L", or None
    "personas": ["product-owner", "dev"],  # list
    "metrics": ["conversion_rate"],      # list
    "owner": "alice",                    # str or None
    "version": "1.0",                    # str or None
    "lang": "en",                        # str or None
    "file": "prds/auth.md",              # str: relative path under docs/product/
    "brd_goals": ["BRD-G1", "BRD-G2"],   # list of goal IDs (PRD only)
    "epic": "PRD-AUTH-E1",               # str: parent epic ID (story only)
    "prd": "PRD-AUTH",                   # str: parent PRD ID (epic only)
    "target_date": "2026-09-30",         # str ISO date or None
    "depends_on": ["PRD-X", "PRD-Y"],    # list of artifact IDs (PRD/epic only)
    "risks": [                           # list of dicts (or None if absent)
        {"id": "R1", "title": "…", "impact": "high", "likelihood": "med", "status": "open"}
    ],
    "competitive_parity": {              # dict ID → verdict (or None)
        "COMP-ACME": "behind",
        "COMP-RIVAL": "parity"
    },
}
```

### Graph JSON (complete shape)

```python
{
    "version": "1.0",
    "generated_at": "2026-06-02T12:34:56Z",  # ISO timestamp
    "product": { … },                        # metadata from PRODUCT.md frontmatter
    "nodes": [ … ],                          # list of node dicts (see above)
    "edges": [                               # list of parent-link dicts
        {"from": "PRD-AUTH-E1-S1", "to": "PRD-AUTH-E1", "kind": "epic"},
        {"from": "PRD-AUTH-E1", "to": "PRD-AUTH", "kind": "prd"},
        {"from": "PRD-AUTH", "to": "BRD-G1", "kind": "brd_goal"},
    ],
    "risks": [ … ],                          # aggregated risk entries from all artifacts
    "competitors": [                         # list from BRD.md competitors:
        {"id": "COMP-ACME", "name": "Acme Corp", "threat": "high"}
    ],
    "parse_errors": [                        # list of {file, error} for unparseable artifacts
        {"file": "prds/broken.md", "error": "invalid YAML in frontmatter"}
    ],
    "root_path": "/path/to/project",
}
```

### CLI Invocation

```bash
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/spec_graph.py \
  --root /path/to/project \
  [--snapshot]  # optional: also write JSON snapshot to docs/product/visuals/.snapshots/
```

### Ancestry Walking (lines 189–212)

The edges enable parent-link traversal. To get ancestors of a story:

```python
# Pseudo-code: walk backward via edges
story_id = "PRD-AUTH-E1-S1"
edges = graph["edges"]

# Find parent epic: edge with from=story_id, kind="epic"
epic_edge = next((e for e in edges if e["from"] == story_id and e["kind"] == "epic"), None)
epic_id = epic_edge["to"]  # "PRD-AUTH-E1"

# Find parent PRD: edge with from=epic_id, kind="prd"
prd_edge = next((e for e in edges if e["from"] == epic_id and e["kind"] == "prd"), None)
prd_id = prd_edge["to"]  # "PRD-AUTH"

# Find parent goal: edge with from=prd_id, kind="brd_goal"
goal_edges = [e for e in edges if e["from"] == prd_id and e["kind"] == "brd_goal"]
goal_ids = [e["to"] for e in goal_edges]  # ["BRD-G1", "BRD-G2"]
```

### **Spec-roast usage pattern**

For a roast scan, you need ancestry + node content hashing:
1. Call `build_graph(root)` to get the full graph.
2. Walk edges backward to collect ancestors.
3. Use `node["body_hash"]` (8-char sha256) as a cache key for "has this content drifted".
4. For nodes with body_hash == prior snapshot, skip re-analysis (optimization).

---

## 5. assemble_digest.py: Selection → Scope-Chain API

**File:** `.claude/skills/product-spec/scripts/assemble_digest.py` (lines 1–90+)

### Top-Level Function (implied from docstring lines 3–24)

**Purpose:** Turn `--export` selection (all | ID | list) into an ordered digest that **includes ancestors** (chain from story → epic → PRD → goal → vision).

### Layer Mapping (lines 38–46)

```python
LAYER_FOR_TYPE = {
    "vision": "vision",
    "brd": "brd",
    "goal": "brd",
    "prd": "prd",
    "epic": "epic",
    "story": "story",
}
ALL_LAYERS = ("vision", "brd", "prd", "epic", "story")

TYPE_RANK = {
    "_warning": -1,  # provenance notes lead
    "product": 0,    # context
    "vision": 1,
    "brd": 2,
    "goal": 3,
    "prd": 4,
    "epic": 5,
    "story": 6,
}
```

### Selection Model (lines 71–90, pseudo)

```python
def _resolve_selection(select: str, graph: Dict[str, Any]) -> Tuple[Set[str], Set[str], List[str]]:
    """Classify a `--export` selection into:
      • spec_targets   — goal/PRD/epic/story node IDs to walk (ancestors+descendants)
      • singleton_types — vision/brd/product requested as CONTEXT (not edge-walked)
      • unresolved     — requested IDs that match nothing (typos / wrong case)
    
    `all` selects every spec node and no explicit singletons. Splitting context
    artifacts (vision/brd/product) OUT of the target set is what stops `--export
    VISION` double-rendering vision (once as target, once as the prepended
    singleton); reporting `unresolved` is what lets the caller fail loudly instead
    of silently dropping typos.
    """
```

**Expected output shape (from docstring lines 13–23):**
```python
# Digest element
{
    "id": "PRD-AUTH-E1-S1",
    "type": "story",
    "role": "target",                    # "ancestor" | "target" | "descendant" | "warning"
    "verbosity": "full",                 # "full" | "struct" (context artifacts are struct/compacted)
    "title": "User Login via OAuth",
    "frontmatter": { … },                # YAML front matter as dict
    "body": "## User Login via OAuth — Story PRD-AUTH-E1-S1\n\n…",
    "ac": [ {"id": "S1", "text": "…"} ] # resolved acceptance criteria
}
# Emitted in canonical SORTED order (TYPE_RANK, then ID)
```

### **Spec-roast usage pattern**

Spec-roast can call `build_digest(selection, layers, depth, graph, artifacts)` to:
1. Get a single story WITH its full ancestry chain (story → epic → PRD → goal → vision).
2. Walk through the digest to collect all ancestors for a roast scope.
3. Example: `--roast PRD-AUTH` returns `[goal, vision, PRD, epic1, epic2, story1, story2, ...]` in order.

**Important caveat:** Per docstring, `ancestors()` cannot reach vision/product/BRD via edges — they are loaded and prepended as singletons. Spec-roast must either:
- Call `build_digest` and get singletons automatically, OR
- Load vision/product/BRD manually from artifacts if doing manual ancestry walking.

---

## 6. check_traceability.py: Findings JSON Schema

**File:** `.claude/skills/product-spec/scripts/check_traceability.py` (lines 1–80+)

### CLI Signature (lines 14–15)

```bash
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/check_traceability.py \
  --root <project-dir>
```

### Finding Types & Structure (lines 32–80, via spec_graph.make_finding)

From the docstring:
- `orphan_story` (error) — story with no epic reference
- `orphan_epic` (error) — epic with no PRD reference
- `orphan_prd` (error) — PRD with no BRD goals declared
- `dangling_link` (error) — frontmatter ID reference unresolved
- `unaddressed_parent` (warn) — parent with zero inbound child edges
- `orphan_brd_goal` (warn) — BRD goal with no PRD addressing it

**Finding shape (via `_f(type, severity, node, message, …)`)**:
```python
{
    "type": "orphan_story",                    # string: check id
    "severity": "error",                       # string: "error" | "warn"
    "affected_type": "story",                  # string: artifact type
    "affected_id": "PRD-AUTH-E1-S1",           # string: node id
    "affected_file": "stories/login.md",       # string: relative path
    "message": "Story has no epic reference.",
    "ref": "PRD-AUTH-E1",                      # optional: the referenced ID that is missing/wrong
    "expected_child": "epic",                  # optional: the child type expected for a parent
}
```

### Exit Code

Always exits **0** (advisory emitter). Output is JSON array of findings.

### **Spec-roast usage pattern**

Call this script and parse JSON findings:
```bash
python3 check_traceability.py --root "$ROOT" | jq '.[] | select(.severity == "error")'
```

Roast can use these as "structural blockers" before running semantic roast checks.

---

## 7. check_consistency.py: Enum Validation & Fields Check

**File:** `.claude/skills/product-spec/scripts/check_consistency.py` (lines 1–100+)

### CLI Signature (lines 14–15)

```bash
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/check_consistency.py \
  --root <project-dir>
```

### ENUMS Dictionary (lines 42–61)

The authoritative home for closed-enum validation:

```python
ENUMS = {
    "status": {"draft", "review", "approved"},
    "scope": {"in", "out", "core-value"},
    "moscow": {"must", "should", "could", "wont"},
    "horizon": {"now", "next", "later"},
    "size": {"S", "M", "L"},
    "lang": {"en", "vi"},
    "risk_impact": {"low", "med", "high"},
    "risk_likelihood": {"low", "med", "high"},
    "risk_status": {"open", "mitigated", "accepted"},
    "competitor_threat": {"low", "med", "high"},
    "competitive_parity": {"ahead", "parity", "behind", "none"},
}
```

### List-Typed Fields (lines 69–75)

Fields that MUST be lists; a bare scalar like `personas: "TBD"` triggers an error:

```python
LIST_FIELDS = (
    "personas",
    "metrics",
    "brd_goals",
    "risks",
    "acceptance_criteria",
)
```

### Finding Types

- `missing_ac` (error) — story without acceptance criteria
- `low_ac_count` (warn) — story with too few AC (soft cap)
- `invalid_id` (error) — ID does not match parent-scoped grammar
- `dup_id` (error) — two artifacts share the same ID
- `unknown_enum` (error) — closed-enum field with disallowed value
- `status_inconsistency` (warn) — child approved under draft parent
- `invalid_type` (error) — a LIST_FIELD contains a non-list value
- `risk_blindspot` (warn) — large epic with zero declared risks
- `risk_high_ratio` (warn) — too many "high" impact risks

### **Spec-roast usage pattern**

Use this to validate roasted artifacts before storing findings:
```bash
python3 check_consistency.py --root "$ROOT" | jq '.[] | select(.type == "unknown_enum")'
```

Reference `ENUMS` dict if roast wants to validate a custom field.

---

## 8. decision_register.py: DEC Record API

**File:** `.claude/skills/product-spec/scripts/decision_register.py` (lines 1–100+)

### CLI Signatures (lines 29–34)

```bash
# Allocate next ID
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/decision_register.py \
  --root <dir> --alloc-id
# Returns: JSON {id: "DEC-5"}

# Append a new decision
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/decision_register.py \
  --root <dir> --append \
  --id DEC-2 --title "Use OAuth instead of custom auth" \
  --rationale "Reduces maintenance burden and security risk." \
  [--affects PRD-AUTH] \
  [--supersedes DEC-1]

# List all decisions (active + superseded)
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/decision_register.py \
  --root <dir> --list
# Returns: JSON array of records
```

### Record Format (lines 18–22)

Storage file: `docs/product/decisions.md`

```markdown
---
id: DEC-2
status: active
date: 2026-06-02
affects: PRD-AUTH
supersedes: DEC-1
---

## DEC-2 — Use OAuth instead of custom auth

Reduces maintenance burden and security risk. The auth middleware cost (70h over 2 quarters) was unsustainable for a 1-person security team. OAuth has been battle-tested by millions of users; a custom system in a startup would require annual compliance audits and penetration testing at 5x cost.
```

### ID Grammar (lines 60)

```python
DECISION_ID_RE = re.compile(r"^DEC-\d+$")
```

Monotonic, globally unique. No reuse.

### Record Parsing (lines 78–100)

```python
def parse_decisions(root) -> List[Dict[str, Any]]:
    """Return every record (active AND superseded), in file order.
    
    Each record is a dict with at least `id`, `status`, `date`; plus `affects`,
    `supersedes`, and `title` when present. A missing file → empty list…"""
```

### **Spec-roast usage pattern**

For a roast finding that surfaces a prior decision:
```bash
# Allocate a new decision ID
python3 decision_register.py --root "$ROOT" --alloc-id  # → DEC-15

# Record the roast ruling
python3 decision_register.py --root "$ROOT" --append \
  --id DEC-15 \
  --title "Defer mobile-first redesign to Phase 2" \
  --rationale "Roast found implicit assumption that MVP targets mobile-first. Team consensus: web-first in Phase 1, mobile in Phase 2. Recorded to stop re-litigation." \
  --affects PRD-REDESIGN
```

---

## 9. judgment_cache.py: Verdict Cache Schema

**File:** `.claude/skills/product-spec/scripts/judgment_cache.py` (lines 1–100+)

### Storage (lines 29–32)

File: `docs/product/.memory/judgments.json`

```json
{
  "cache_version": "1",
  "model_id": "claude-opus-2024-08-06",
  "entries": {
    "invest_quality|PRD-AUTH|a1b2c3d4|en|": {
      "verdict": {"check": "invest_quality", "result": "pass", "notes": "…"},
      "stored_at": "2026-06-02T12:34:56Z"
    },
    "semantic_duplication|PRD-AUTH,PRD-PAY|a1b2c3d4,x9y8z7w6|en|": {
      "verdict": {"check": "semantic_duplication", "result": "flagged_dup", "pair": ["PRD-AUTH", "PRD-PAY"]},
      "po_ruling_ref": "DEC-8",
      "stored_at": "2026-06-02T12:35:00Z"
    },
    "core_value_drift|PRD-AUTH|a1b2c3d4|en|cv:xyz123": {
      "verdict": {"check": "core_value_drift", "result": "aligned"},
      "stored_at": "2026-06-02T12:35:10Z"
    }
  }
}
```

### Key Grammar (lines 17–26)

```
check | scope_key | hashes | lang | dep_hash

• Single-node check (invest_quality / vagueness / gold_plating / time_realism / competitive_drift / core_value_drift):
  scope_key = node_id
  hashes = body_hash

• Semantic duplication (pair check):
  scope_key = the two ids SORTED + joined
  hashes = the two body_hashes in SAME sorted order
  → (A,B) and (B,A) map to ONE key (unordered pair)

• core_value_drift additionally:
  dep_hash = cv:<hash(core_value)>
  → change to PRODUCT core_value invalidates every drift verdict
```

### CLI Signatures (lines 69–74)

```bash
# Check if a verdict is cached + fresh
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/judgment_cache.py \
  --root <dir> \
  --check --check-name invest_quality \
  --node-ids PRD-AUTH \
  --model-id claude-opus-2024-08-06 \
  [--no-cache]
# Returns: JSON {cached: true|false, verdict?: …, stored_at?: …}

# Store a single verdict
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/judgment_cache.py \
  --root <dir> \
  --store --key "invest_quality|PRD-AUTH|a1b2c3d4|en|" \
  --model-id claude-opus-2024-08-06 \
  --verdict '{"check": "invest_quality", "result": "pass"}' \
  [--po-ruling-ref DEC-n] \
  [--no-cache]

# Batch store (atomic)
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/judgment_cache.py \
  --root <dir> \
  --store-batch <file|-> \
  --model-id claude-opus-2024-08-06 \
  [--no-cache]
# <file> is a JSON array: [{key, verdict, po_ruling_ref?}, …]

# Garbage-collect deleted node IDs
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec/scripts/judgment_cache.py \
  --root <dir> \
  --gc
```

### Last-Validated Marker (lines 61, implied)

Written on `--validate` only:

```json
{
  "validated_at": "2026-06-02T12:34:56Z",
  "root_path": "/path/to/project",
  "content_fingerprint": "sha256:abc123…"
}
```

File: `docs/product/.memory/last_validated.json`

### **Spec-roast usage pattern**

Roast is a _new_ LLM check layer (not in product-spec's validate flow). To avoid re-judging identical artifacts:

1. After roast finishes, compute a cache key for each roasted node:
   ```python
   key = f"roast_contradiction|{node_id}|{body_hash}|{lang}|"
   ```

2. Store verdicts in a NEW cache file (e.g., `roast_verdicts.json`) with the same schema:
   ```bash
   python3 judgment_cache.py --root "$ROOT" \
     --store --key "roast_contradiction|PRD-AUTH|a1b2c3d4|en|" \
     --verdict '{"roast_check": "contradiction", "found": false}' \
     --model-id "$MODEL_ID"
   ```

3. On re-roast, check prior verdicts before re-calling the LLM for unchanged nodes.

---

## 10. fs_guard.py: Path-Assert Chokepoint

**File:** `.claude/skills/product-spec/scripts/fs_guard.py` (lines 1–75)

### Function Signature (lines 39–61)

```python
def assert_under_docs_product(path, root) -> Path:
    """Return the resolved `path` if it is contained under `<root>/docs/product/`,
    else raise `FenceError` with a friendly, actionable message. Raises BEFORE any
    write so a blocked target never touches disk.
    
    `path` may be relative to `root` or absolute; both are resolved. The boundary
    directory itself counts as in-fence (it is not an escape)."""
    root = Path(root).resolve()
    fence = (root / "docs" / "product").resolve()
    
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    # strict=False: the leaf (and intermediate dirs) may not exist yet
    resolved = target.resolve(strict=False)
    
    if resolved != fence and not _is_within(resolved, fence):
        raise FenceError(
            f"refusing to write outside the spec boundary: {resolved} is not "
            f"under {fence}. The skill only writes under docs/product/."
        )
    return resolved
```

### Exception Type (lines 35–36)

```python
class FenceError(Exception):
    """Raised when a script-driven write would land outside docs/product/."""
```

### Containment Check (lines 64–69)

```python
def _is_within(child: Path, parent: Path) -> bool:
    """True iff `child` is `parent` or a descendant of it. Uses path-segment
    containment (via is_relative_to) so a string prefix look-alike like
    `docs/product-extra` is correctly rejected — it shares the prefix string but
    not the path segments."""
    return child.is_relative_to(parent)
```

### **Spec-roast usage pattern**

For ANY script that writes roast findings or metadata to disk:

```python
from fs_guard import assert_under_docs_product, FenceError

try:
    target = assert_under_docs_product(
        "docs/product/roasts/critique-2026-06-02.json",
        root
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(findings))
except FenceError as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
```

All new writers (roast_scan, critique_storage) must pass through this before opening files.

---

## 11. eval/evals.json: Eval Scenario Structure

**File:** `.claude/skills/product-spec/eval/evals.json` (lines 1–50+)

### Top-Level Shape (lines 1–4)

```json
{
  "skill_name": "cleanmatic:product-spec",
  "evals": [
    { /* eval scenario 0 */ },
    { /* eval scenario 1 */ },
    …
  ]
}
```

### Scenario Schema (lines 5–26, example eval 0)

```json
{
  "id": 0,
  "prompt": "Initialize a brand new product spec for … Use the cleanmatic:product-spec skill. The PO answers are pre-baked in fixtures/init-answers.json. Produce a valid docs/product/PRODUCT.md and docs/product/vision.md.",
  "expected_output": "docs/product/PRODUCT.md and vision.md exist; both have schema-valid frontmatter; core_value is populated; personas list cap 2-4.",
  "files": ["fixtures/init-answers.json"],
  "assertions": [
    {"id": "files-created", "text": "Both docs/product/PRODUCT.md and docs/product/vision.md are created."},
    {"id": "frontmatter-valid", "text": "frontmatter_parser.py reports ok=true for both files."},
    {"id": "core-value-set", "text": "PRODUCT.md frontmatter has a non-empty core_value field."},
    {"id": "persona-cap", "text": "PRODUCT.md frontmatter personas list has between 2 and 4 entries."}
  ]
}
```

### Assertion Types (lines 42, optional field)

```json
{
  "_assertion_type": "llm_advisory",
  "_note": "A PRODUCT.md core-value change has no deterministic mapping…",
  "_gating": "llm_advisory" | "structural"
}
```

Values for `_gating`:
- `"structural"` — assertion can be verified by script/file inspection.
- `"llm_advisory"` — assertion requires LLM judgment (no automated check).

### **Spec-roast eval examples (TEMPLATE)**

```json
{
  "id": 0,
  "prompt": "Run --roast against the fixture spec at fixtures/sample-spec/. The spec contains a semantic contradiction (Feature A depends on Feature B, but PRD-A says 'independent') and implicit assumptions (story assumes mobile-first without stating it). Produce a roast report.",
  "expected_output": "Roast report identifies the contradiction and at least 2 implicit assumptions.",
  "files": ["fixtures/sample-spec"],
  "assertions": [
    {"id": "contradiction-detected", "text": "Report includes a contradiction finding between PRD-A and epic PRD-A-E1."},
    {"id": "implicit-assumptions", "_gating": "llm_advisory", "text": "Report surfaces at least 2 implicit assumptions (e.g., mobile-first, user signup assumed)."}
  ]
}
```

---

## 12. System Boundaries & Data Flow

### Script Invocation Chain (typical roast workflow)

```
roast_scan.py
  ├─ spec_graph.py --root (get full graph)
  ├─ check_traceability.py --root (structural blockers)
  ├─ check_consistency.py --root (enum validation)
  ├─ assemble_digest.py (get scope + ancestry)
  ├─ decision_register.py --list (check prior rulings)
  └─ judgment_cache.py --check (check prior verdicts)

roast_audit.py (LLM-driven; calls roast_scan outputs)
  ├─ Read prior findings (findings JSON)
  ├─ Read prior verdicts (judgment_cache)
  ├─ Call LLM for contradiction/drift/tone checks
  ├─ Store verdicts (judgment_cache.py --store-batch)
  ├─ Record rulings (decision_register.py --append)
  └─ Write critique (fs_guard → docs/product/roasts/)
```

### Key Immutable APIs

| Module | Function/CLI | Input | Output | Side Effect |
|--------|-------------|-------|--------|-------------|
| **spec_graph** | `build_graph(root)` | project root | graph JSON (nodes + edges) | None |
| **check_traceability** | CLI `--root` | project root | findings JSON (stdout) | None |
| **check_consistency** | CLI `--root` | project root | findings JSON (stdout) | None |
| **assemble_digest** | `build_digest(…, graph, artifacts)` | selection + graph | digest list (sorted) | None |
| **decision_register** | `--alloc-id` | project root | `{id: "DEC-5"}` | None |
| **decision_register** | `--append` | project root + record data | None | Writes to decisions.md |
| **decision_register** | `--list` | project root | decisions JSON | None |
| **judgment_cache** | `--check` | project root + key | `{cached: bool, verdict?: …}` | None |
| **judgment_cache** | `--store` | project root + key + verdict | None | Writes to judgments.json |
| **judgment_cache** | `--store-batch` | project root + file | None | Writes to judgments.json (atomic) |
| **fs_guard** | `assert_under_docs_product(path, root)` | path + root | resolved Path | Raises FenceError |
| **preferences** | `load(root)` | project root | prefs dict | None |
| **preferences** | `save(root, prefs)` | project root + prefs dict | Path | Writes to preferences.yaml |

---

## Unresolved Questions

1. **Artifact Enrichment:** When roast_scan loads artifacts via `spec_graph.build_graph_with_artifacts()`, does it also get the raw `parsed.body` field, or only the graph nodes? (Needed for full-text roasting.)

2. **Batch Atomicity in judgment_cache:** The `--store-batch` atomic write — is there a rollback mechanism if a single entry validation fails mid-batch, or does the entire batch reject?

3. **Soft Fence Symlinks:** The `fs_guard.resolve(strict=False)` follows existing symlinks. Does it follow symlinks on _non-existent_ targets (leaf is a dangling symlink)? Impact on security: can a roast output be symlinked out of bounds?

4. **Body Hash Stability:** When a story is copied/renamed (same content, different ID), is the body_hash preserved, or recomputed? This affects cache-key semantics for roast verdicts.

5. **Decision Record Mutation:** Can `--append` overwrite a prior decision, or is it purely append-only? The docstring says "append-only" but does a second `--append --id DEC-2` clobber or coexist?

6. **last_validated.json Path:** The spec_graph code does not emit a `last_validated.json`; that is written by status.py / judgment_cache.py on validate. Where does roast_scan write its "last_roasted" marker?

---

## Summary for Spec-Roast Implementation

### Immediate Dependencies

```
spec-roast/install.sh
  ├─ Reuse VENV_DIR="$SKILLS_DIR/.venv" (shared)
  ├─ Add --roast-hook flag (JSON merge into settings.local.json)
  └─ No new dependencies beyond pyyaml (already installed)

spec-roast/scripts/roast_scan.py
  ├─ Import spec_graph: build_graph(root) → graph
  ├─ Import check_traceability / check_consistency via subprocess
  ├─ Import decision_register: parse_decisions(root) → prior rulings
  ├─ Import judgment_cache: load cache, check stale verdicts
  └─ Import fs_guard: assert_under_docs_product() for output writes

spec-roast/scripts/roast_audit.py (LLM)
  ├─ Read roast_scan findings
  ├─ Call LLM for contradiction / drift / tone / assumption detection
  ├─ Call judgment_cache --store-batch to persist verdicts
  ├─ Call decision_register --append for recordable rulings
  └─ Write critique via fs_guard to docs/product/roasts/
```

### Required Files to Create

- `.claude/skills/spec-roast/install.sh` — mirror install.sh pattern
- `.claude/skills/spec-roast/install.ps1` — mirror install.ps1 pattern
- `.claude/skills/spec-roast/SKILL.md` — ~250 lines, lean skeleton
- `.claude/skills/spec-roast/scripts/roast_scan.py` — deterministic struct walk
- `.claude/skills/spec-roast/scripts/roast_audit.py` — LLM judgment layer
- `.claude/skills/spec-roast/scripts/requirements.txt` — (pyyaml only, reused)
- `.claude/skills/spec-roast/references/roast-checks-catalog.md` — check definitions
- `.claude/skills/spec-roast/references/roast-workflow.md` — orchestration flow
- `.claude/skills/spec-roast/eval/evals.json` — eval scenarios (3–4 cases)

### Key Architectural Decisions

1. **Script layer owns:** graph traversal, findings emission, cache management, fence validation.
2. **LLM layer owns:** contradiction/drift/tone/assumption detection, rationale prose, PO confirm.
3. **Memory:** Reuse product-spec's judgment_cache and decision_register (same `.memory/` structure).
4. **Isolation:** Roast verdicts keyed differently from product-spec verdicts (e.g., `roast_contradiction` vs `invest_quality`), so re-running product-spec `--validate` doesn't evict roast findings.
5. **Soft fence:** All roast output (critique files, metadata) must pass through `fs_guard` before write.
