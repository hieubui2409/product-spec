# Convention Audit: cleanmatic:product-spec → cleanmatic:claude-pack

**Report**: Deep-dive structural audit of product-spec skill to extract AS-IS patterns for claude-pack replication.
**Date**: 2026-05-29
**Auditor**: researcher agent

---

## Q1: Product-Spec Skill Anatomy

### SKILL.md Frontmatter (required fields)
```yaml
---
name: cleanmatic:product-spec                    # fully-qualified namespace
description: "Interview-driven product spec ... [single sentence, ~200 chars]"
user-invocable: true                             # required for CLI invocation
when_to_use: "[narrative trigger context]"       # prose; not evaluated
category: product                                 # semantic routing
keywords: [prd, brd, epic, story, ...]           # CSV for search
argument-hint: "[--flag] [target]"                # CLI signature hint
metadata:
  author: cleanmatic                              # namespace author (not "ck:")
  version: "1.0.0"                                # semver
---
```

**Pattern**: `name: cleanmatic:<skill-name>` (not `ck:` prefix). Always include `user-invocable: true` and `when_to_use` prose. Frontmatter is parsed by skill-creator validation; avoid unknown fields.

**Citation**: `.claude/skills/product-spec/SKILL.md:1-12`

### Section Structure (SKILL.md body)
1. **Title & 1-line summary** (line 14–16)
2. **When to Use** — narrative bullets (18–24)
3. **Flags** — table of all command-line arguments (26–44)
4. **No-Flag Menu** — state detection + AskUserQuestion options (46–59)
5. **Output Contract** — directory structure diagram (61–78)
6. **Workflow Map** — flowchart (ASCII, Mermaid) (80–100)
7. **Loads `references/*` on Demand** — prose explaining each reference file (102–113)
8. **Resources** — one-liner per directory (`scripts/`, `assets/templates/`, `assets/vendor/`, `eval/`, `examples/`) (115–122)
9. **Operating Principles** — numbered bullets on philosophy (123–133)

**Pattern**: Total ~300 lines. Heavy use of tables, flowcharts, structured lists. LLM-friendly: repeating text minimized; cross-references to references for prose. No code in SKILL.md except examples (none in product-spec). 

**Citation**: `.claude/skills/product-spec/SKILL.md` (entire file, structure at lines listed above)

### Directory Layout (observed AS-IS)

```
product-spec/
├── SKILL.md                          (8.1 KB)
├── README.md                         (2.0 KB)
├── install.sh                        (3.4 KB)
├── scripts/                          (16 Python files, 2358 lines total)
│   ├── frontmatter_parser.py
│   ├── spec_graph.py
│   ├── generate_templates.py
│   ├── check_consistency.py          (13.4 KB alone — largest script)
│   ├── check_traceability.py
│   ├── visualize.py
│   ├── build_traceability_matrix.py
│   ├── render_ascii.py
│   ├── render_html.py
│   ├── render_mermaid.py
│   ├── i18n_labels.py
│   ├── strict_gate.py
│   ├── encoding_utils.py
│   ├── install-vendor-mermaid.sh
│   ├── requirements.txt              (pyyaml, pytest, pytest-cov)
│   └── tests/                        (pytest suite)
├── references/                       (12 markdown files, <300 lines each)
│   ├── frontmatter-and-id-spec.md
│   ├── document-model-and-hierarchy.md
│   ├── validation-rules-spec.md
│   ├── visualization-spec.md
│   ├── workflow-interview.md
│   ├── workflow-validate.md
│   ├── workflow-auto-and-update.md
│   ├── interview-vision.md
│   ├── interview-brd.md
│   ├── interview-prd.md
│   ├── interview-epic-story.md
│   └── interview-frameworks.md
├── assets/
│   ├── templates/                    (10 markdown templates)
│   │   ├── product.md, vision.md, brd.md, prd.md, epic.md, story.md
│   │   ├── change-log-entry.md, exec-summary.md, sign-off.md
│   │   └── visual-html-shell.html
│   └── vendor/                       (mermaid.min.js vendored)
├── eval/
│   ├── evals.json                    (5.0 KB, scenario-based assertions)
│   └── fixtures/                     (mock inputs for testing)
└── examples/
    ├── acme-shop/                    (worked example product spec)
    └── README.md
```

**Pattern**: ~16 Python scripts (structural + judgment split), 12 reference docs (~100-300 lines each), 10 markdown templates, vendored JS, eval fixtures. No duplication between SKILL.md and references.

**Citation**: Bash `ls -la` output from earlier execution; tree view at `.claude/skills/product-spec/` directory

---

## Q2: SKILL.md Frontmatter Conventions (Extracted)

### Comparison with skill-creator's Template

**skill-creator** (`SKILL.md:27-36`) specifies:
```yaml
---
name: kebab-case-name           # optional namespace: ck:kebab-case-name
description: Under 200 chars, specific triggers and use cases
license: Optional
version: Optional
---
```

**product-spec** actually uses:
```yaml
---
name: cleanmatic:product-spec
description: [~240 chars, pushy/trigger-heavy]
user-invocable: true
when_to_use: "Narrative context"
category: product
keywords: [list]
argument-hint: "[syntax]"
metadata:
  author: cleanmatic
  version: "1.0.0"
---
```

**Key Differences**:
1. **Namespace**: `cleanmatic:` not `ck:` (non-standard, but enforced for product-spec per plan decision)
2. **Extra fields**: `user-invocable`, `when_to_use`, `category`, `keywords`, `argument-hint`, `metadata` block
3. **No license field** (unlike skill-creator template)
4. **Description length**: ~240 chars (product-spec is pushy; stock template says "under 200 chars")

**Pattern for claude-pack**: Follow product-spec exactly (namespace, extra fields, metadata.author, metadata.version) since you're in the same family.

**Citation**: 
- skill-creator: `.claude/skills/skill-creator/references/skill-anatomy-and-requirements.md:27-36`
- product-spec: `.claude/skills/product-spec/SKILL.md:1-12`

---

## Q3: install.sh Template — Minimal Pattern for claude-pack

**product-spec install.sh** does:
1. Check Python 3.11+ on PATH
2. Create venv at `./.venv/` (sibling to skill folder, not `~/.claude/skills/.venv`)
3. `pip install --quiet` from `scripts/requirements.txt` (pyyaml, pytest, pytest-cov)
4. Vendor Mermaid JS via `install-vendor-mermaid.sh` (optional for visualization skills)
5. Run smoke-test: `python3 -m pytest scripts/tests/ -q`

**For claude-pack** (assuming: no visualization, no Mermaid):
- Steps 1–3 apply
- Step 4 (vendor mermaid) → **skip** (claude-pack has no viz)
- Step 5 (pytest) → **skip if no tests**, or run if you have `scripts/tests/`

**Minimal install.sh template** (≤30 lines):
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
VENV_DIR="$SKILLS_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/scripts/requirements.txt"

step() { echo ""; echo "▸ $*"; }
ok()   { echo "  ✓ $*"; }
fail() { echo "  ✗ $*" >&2; exit 1; }

step "Checking Python"
! command -v python3 >/dev/null 2>&1 && fail "python3 not found"
ok "python3 = $(python3 --version | cut -d' ' -f2)"

step "Setting up venv at $VENV_DIR"
[ -x "$VENV_DIR/bin/python3" ] && { ok "venv exists"; } || {
  python3 -m venv "$VENV_DIR"
  ok "venv created"
}

step "Installing dependencies"
"$VENV_DIR/bin/python3" -m pip install --upgrade pip --quiet
"$VENV_DIR/bin/python3" -m pip install --quiet -r "$REQUIREMENTS"
ok "pyyaml installed"

echo ""
echo "─────────────────────────────────────────────────────"
echo "Install complete. Invoke skill:"
echo "    /cleanmatic:claude-pack"
echo "─────────────────────────────────────────────────────"
```

**Key differences from product-spec**:
- Removed vendor shim invocation (no mermaid for claude-pack)
- Removed pytest smoke test (assume no test suite initially)
- Simplified final message

**Citation**: `.claude/skills/product-spec/install.sh:1-92` (entire file); note lines 56–62 invoke vendor shim which claude-pack skips.

---

## Q4: AskUserQuestion Pattern — How to Invoke from LLM vs Scripts

**Finding**: product-spec scripts **never** call AskUserQuestion. The LLM layer calls it. Scripts are **structural-only** (parse YAML, build graph, compute IDs, render templates).

**Pattern** (from `workflow-interview.md:2-9`):
1. LLM **reads** the relevant `references/interview-*.md` file
2. LLM **composes** `AskUserQuestion` calls from question banks
3. LLM **appends** answers to `docs/product/.session.md`
4. LLM **removes** answered questions from pending list

**Product-spec references** (`interview-vision.md`, `interview-brd.md`, etc.) contain:
- Question ID + text (EN + VI)
- Expected answer type (string, enum, multiselect)
- Optional `target` field (which frontmatter key to populate)
- Skip logic (adaptive: "If V1='Marketplace', skip V2–V3")

**Example from interview-vision.md:1-30**:
```
The LLM composes `AskUserQuestion` calls from these records and skips questions 
already answered by an existing `PRODUCT.md`. Persona cap: soft 2–4.
```

**For claude-pack manifest builder**:
- **IF** you need interactive questions: write them in a `references/manifest-questions.md` file (question bank)
- **LLM layer** (the orchestration that uses claude-pack) will call `AskUserQuestion` with those questions
- Scripts **never** invoke `AskUserQuestion` directly

**Pattern is call-by-reference**: scripts emit JSON data; LLM decides on AskUserQuestion.

**Citation**: 
- `.claude/skills/product-spec/references/workflow-interview.md:1-40` (interview flow, AskUserQuestion batching)
- `.claude/skills/product-spec/SKILL.md:51` (no-flag menu mentions AskUserQuestion)

---

## Q5: Eval / Golden Test Convention

**product-spec evals.json structure**:
```json
{
  "skill_name": "cleanmatic:product-spec",
  "evals": [
    {
      "id": 0,
      "prompt": "Initialize a brand new product spec...",
      "expected_output": "docs/product/PRODUCT.md and vision.md exist...",
      "files": ["fixtures/init-answers.json"],
      "assertions": [
        {"id": "files-created", "text": "Both files are created."},
        {"id": "frontmatter-valid", "text": "frontmatter_parser reports ok=true"},
        ...
      ]
    },
    { "id": 1, ... },
    ...
  ]
}
```

**Pattern**:
- One JSON file `eval/evals.json` per skill
- Each eval is a scenario (prompt + expected outputs + assertions)
- Assertions are **semantic** (not regex): grader agent evaluates whether the output meets the text criterion
- Fixtures stored in `eval/fixtures/` (e.g., pre-baked `init-answers.json`)
- No `.expected` files or tarballs; comparisons are semantic + grader agent (no golden file diffs)

**For claude-pack**:
- Create `eval/evals.json` with 2–3 core scenarios:
  1. Initialize a manifest from scratch
  2. Validate an existing manifest
  3. Extend a manifest with new entries
- Each scenario includes fixtures (sample inputs) and assertions (grader checks)

**Citation**: `.claude/skills/product-spec/eval/evals.json:1-35` (shown earlier)

---

## Q6: skill-creator Scaffolding & Minimum Surface

**skill-creator** (`SKILL.md:39-46`) states the **minimum required** for a new skill:
```
.claude/skills/
└── skill-name/
    ├── SKILL.md              (required, <300 lines)
    ├── scripts/              (optional: executable code)
    ├── references/           (optional: docs loaded as-needed)
    ├── agents/               (optional: eval agent templates)
    └── assets/               (optional: output resources)
```

**Enforcement**:
- SKILL.md is **required** (frontmatter parsed by validation)
- scripts/, references/, assets/ are **optional** (depends on skill type)
- agents/ is **optional** (for eval grader/comparator/analyzer templates)

**skill-creator does NOT scaffold new skills automatically** (no `--create` flag in product-spec). The pattern is:
- Manually create `skill-name/` folder in `./.claude/skills/`
- Write SKILL.md by hand (or copy from template in skill-creator/references/)
- Add subdirs as needed
- Run `./install.sh` once

**For claude-pack**: 
- Minimum = SKILL.md + scripts/ + references/ (no agents/, no assets/ needed for manifest builder)
- No automatic scaffold; create directory structure manually
- Frontmatter must be valid YAML (skill-creator validates via `scripts/quick_validate.py`)

**Citation**: 
- skill-creator anatomy: `.claude/skills/skill-creator/references/skill-anatomy-and-requirements.md:1-78`
- product-spec scaffold: no `--create` flag used; manually built per plan phases 1–8

---

## Q7: Plan-Context Hook & Phase Breakdown

**product-spec plan** (`plans/260528-0912-cleanmatic-product-spec-skill/plan.md:25-36`) uses 8 phases:

| Phase | Name | Files Created |
|-------|------|---------------|
| 1 | Scaffold & Skeleton | SKILL.md, install.sh, README.md structure |
| 2 | Reference Specs | 5 reference files (frontmatter, validation, document model, etc.) |
| 3 | Bilingual Question Banks | interview-*.md (EN+VI; marked best-effort on VI) |
| 4 | Artifact Templates | 10 markdown templates with `{{token}}` placeholders |
| 5 | Core Scripts | spec_graph.py, check_*.py, generate_templates.py, render_*.py |
| 6 | Visualization Renderer | render_ascii/mermaid/html.py, vendoring |
| 7 | SKILL.md Orchestration | Final SKILL.md, workflow tie-ins to references |
| 8 | Eval Tests & Packaging | evals.json, fixtures, smoke tests |

**Standard phases for any skill**:
1. Scaffold (SKILL.md + install.sh)
2. References (documentation)
3. Scripts (if needed)
4. Templates/Assets (if needed)
5. Eval (if needed)

**For claude-pack plan** (recommend):
1. Scaffold: SKILL.md + install.sh + README
2. References: manifest-spec.md, cli-arguments.md
3. Scripts: manifest_builder.py, manifest_validator.py, manifest_registry.py
4. Templates: manifest-template.md (if needed)
5. Eval: evals.json with scenarios

**Citation**: `plans/260528-0912-cleanmatic-product-spec-skill/plan.md:25-36`

---

## Q8: Root CLAUDE.md Operating-Guide Integration

**Finding**: product-spec IS mentioned in root CLAUDE.md but **NOT as an operating guide**. Instead, it's cited for **script invocation path only**:

```
Run scripts via the per-skill venv created by `install.sh`:
    ./.claude/skills/.venv/bin/python3 \
      .claude/skills/product-spec/scripts/<script>.py --root <project-dir>
```

**The actual operating guide** for product-spec lives in:
1. `.claude/skills/product-spec/SKILL.md` (what the user reads)
2. `.claude/CLAUDE.md` (auto-loaded by Claude Code; separate product-spec section at root)

**Root CLAUDE.md structure** (from inspection):
```
# Product Spec — LLM Operating Guide

Auto-loaded by Claude Code in this project. Tells you (the LLM) how to operate 
the `cleanmatic:product-spec` skill...

[Five Operating Principles]
[Parent-Scoped ID Grammar]
[Bilingual Conventions]
[Workflow Pointers]
[Script CLI Contract]
[Output Layout]
[Failure & Drift Handling]
[When to Ask vs Assume]
```

**Recommendation for claude-pack**:
- **Append a new section** to root `CLAUDE.md` (after product-spec section) titled "Claude Pack — LLM Operating Guide"
- Document the 5 key principles specific to manifest building (DRY, progressive disclosure, etc.)
- Reference the skill's SKILL.md + references/ for detail
- **Do NOT** create a standalone operating guide in the skill folder; use root CLAUDE.md for framework-wide guidance

**Rationale**: product-spec is PO-facing (non-technical); claude-pack is developer-facing (technical). Both need root-level guidance, but claude-pack's guidance is shorter (manifests are simpler than specs).

**Citation**: `/home/hieubt/Documents/cleanmatic-skills/CLAUDE.md:1-134` (entire "Product Spec — LLM Operating Guide" section); `.claude/skills/product-spec/SKILL.md:133` mentions "deeper LLM operating guidance lives in `references/` and in repo-root `CLAUDE.md`"

---

## Side-by-Side Directory Tree Comparison

**product-spec (AS-IS)** → **claude-pack (PROPOSED)**

```
product-spec/                      claude-pack/
├── SKILL.md (8.1 KB)             ├── SKILL.md (~4 KB, 250 lines)
├── README.md (2.0 KB)             ├── README.md (~1.5 KB)
├── install.sh (3.4 KB)            ├── install.sh (~2 KB, no vendor shim)
├── scripts/ (16 files)            ├── scripts/ (4 files)
│   ├── frontmatter_parser.py       │   ├── manifest_builder.py (~300 lines)
│   ├── spec_graph.py               │   ├── manifest_validator.py (~200 lines)
│   ├── generate_templates.py        │   ├── manifest_registry.py (~150 lines)
│   ├── check_consistency.py         │   └── requirements.txt
│   ├── check_traceability.py        │       (pyyaml only)
│   ├── ... (11 more)                │
│   ├── requirements.txt             │
│   │   (pyyaml, pytest, ...)        │
│   └── tests/ (pytest suite)        │
├── references/ (12 files)         ├── references/ (4 files)
│   ├── frontmatter-and-id-spec     │   ├── manifest-spec.md (~200 lines)
│   ├── document-model-hierarchy    │   ├── cli-arguments.md (~150 lines)
│   ├── validation-rules-spec       │   ├── validation-rules.md (~150 lines)
│   ├── visualization-spec          │   └── workflow-example.md (~100 lines)
│   ├── workflow-interview.md       │
│   ├── workflow-validate.md        │
│   ├── interview-*.md (5 files)    │
│   └── ...                         │
├── assets/                        ├── assets/
│   ├── templates/ (10 files)       │   └── templates/
│   │   (PRODUCT, Vision, BRD, ...)  │       └── manifest-template.md
│   └── vendor/                     │           (1 file; no vendor/)
│       └── mermaid.min.js          │
├── eval/                          ├── eval/
│   ├── evals.json (5.0 KB)         │   ├── evals.json (~2 KB, 3 scenarios)
│   └── fixtures/                   │   └── fixtures/
│       (mock inputs)                │       (sample manifests)
└── examples/                      └── examples/
    ├── acme-shop/                  └── sample-manifest/
    └── README.md                       └── README.md
```

**Scale differences**:
- product-spec: ~16 scripts (2358 lines), 12 references, vendored deps
- claude-pack: ~4 scripts (~650 lines), 4 references, no vendoring

**Reusable pattern** from product-spec:
- SKILL.md structure (flags table, output contract, workflow map, load-on-demand references)
- install.sh pattern (venv setup, pip install, smoke test)
- references/ organization (split by domain)
- evals.json structure (scenario-based assertions)
- assets/templates/ with `{{token}}` substitution
- README.md linking to SKILL.md + examples

---

## Inconsistencies: Plan vs AS-IS

### C1: Venv Location
**Plan** (phase-01:C1): "use repo-local venv `./.claude/skills/.venv`"
**AS-IS**: install.sh creates venv at `$SKILLS_DIR/.venv` (one level up from skill folder)

→ Both are correct. "repo-local venv" = shared across ALL skills. Correct pattern: `./.claude/skills/.venv/bin/python3`

### C2: Parent-Scoped IDs
**Plan** (phase-01:C2): Confirmed. Implemented in `spec_graph.py` + `generate_templates.py`.
**AS-IS**: BRD-G1, PRD-AUTH, PRD-AUTH-E1, PRD-AUTH-E1-S1. Verified.

→ No inconsistency.

### C3: Script CWD
**Plan** (M5): Every script accepts `--root <project-dir>` (default CWD)
**AS-IS**: All core scripts have `--root` parameter. Verified in `spec_graph.py`, `frontmatter_parser.py`, `visualize.py`.

→ Pattern confirmed. claude-pack should replicate: all scripts take `--root` parameter.

### No Silent Reversals
**Plan** stated: contradictions surfaced, never auto-reversed
**AS-IS**: `workflow-validate.md:2` mentions "3 options to PO via AskUserQuestion: keep/change/hybrid"

→ Pattern confirmed. claude-pack validation must surface conflicts, not auto-fix.

---

## Unresolved Questions

1. **Claude-pack manifest registry persistence**: Should the manifest registry be a single JSON file (analogous to product-spec's `PRODUCT.md` singleton) or multiple files? Recommend: single `manifests-index.json` (analogous to BRD uniqueness).

2. **Bilingual support for claude-pack**: product-spec has EN+VI banks. Does claude-pack need EN+VI manifest descriptions? (Recommend: EN only for v1; bilingual is P3 if at all.)

3. **Eval grader agent templates**: product-spec references `agents/grader.md`, `agents/comparator.md`, `agents/analyzer.md` but these are not visible in the skill folder. Are they optional/external? (Recommend: optional; include only if your evals need multi-agent grading.)

4. **AskUserQuestion batching size**: product-spec cites "3–5 questions per batch" in `workflow-interview.md:58`. Does claude-pack follow the same?  (Recommend: yes, same UX standard.)

5. **Change-log format**: product-spec appends to `change-log.md` after every artifact creation. Should claude-pack track manifest edits in a similar log? (Recommend: yes, for audit trail.)

---

## Summary Table: Reusable Patterns for claude-pack

| Pattern | product-spec Example | claude-pack Recommendation |
|---------|----------------------|----------------------------|
| **Frontmatter** | `name: cleanmatic:product-spec`, metadata block | Copy exactly; use `cleanmatic:claude-pack` |
| **SKILL.md sections** | Flags table + no-flag menu + output contract + workflow map | Replicate structure; adapt text for manifests |
| **install.sh** | venv + pip install + smoke test (skip vendor shim) | Use template above; no mermaid vendor needed |
| **Scripts** | Python 3, stdlib + pyyaml, `--root` parameter, JSON output | Follow pattern; adapt for manifest operations |
| **References** | <300 lines each, one per domain, loaded on-demand | 4 files: spec, cli-args, validation, workflow |
| **Templates** | Markdown with `{{token}}`, `<!-- OPTIONAL: … -->` | 1–2 templates for manifest seed |
| **Eval** | evals.json with scenarios + assertions + fixtures | 3 core scenarios: init, validate, extend |
| **No vendor/** | product-spec vendors mermaid.min.js | claude-pack: **omit** vendor directory |
| **No AskUserQuestion in scripts** | Scripts are structural-only; LLM calls AskUserQuestion | Maintain strict script/LLM split |
| **Root CLAUDE.md** | product-spec has operating-guide section | Add claude-pack section (developer-facing, not PO-facing) |

---

**Report Complete.**
