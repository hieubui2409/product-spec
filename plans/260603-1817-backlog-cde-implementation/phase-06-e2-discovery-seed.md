---
phase: 6
title: "E2 discovery seed (--discover)"
status: pending
priority: P2
effort: "1.5d"
dependencies: [3]
---

# Phase 6: E2 discovery seed (`product-spec --discover`)
<!-- Updated: Validation Session 1 - accept files + directories (bounded recursion), fences retained -->

> **Kept as a separate flag after red-team (2026-06-03)** — `--discover` (ingest upstream raw text →
> candidate seeds) is semantically distinct from `--auto` (decompose a finished brain-dump into the
> hierarchy), so it stays its own flag (H8 / PO). Adds a hard read-side fence (Security F3).

## Overview
A pre-stage that ingests raw inputs (interview transcripts, support-ticket dumps, competitor notes) and
proposes **candidate** personas / problems / JTBD to SEED the Vision/BRD interview instead of a cold
start. Never auto-commits — the interview confirms field-by-field.

## Requirements
- Functional: `--discover <path(s)>` reads local raw text → proposes candidate personas/problems/JTBD as a DRAFT the Vision interview then confirms field-by-field.
- Non-functional: NEVER auto-commit personas (GATE-NEVER-ASSUME); no network; **read-fenced + filtered** local files only; scope TIGHT (text in → candidate bullets out).

## Key facts (from research + red-team)
- No `--discover` today; `--auto` (`workflow-auto.md:11`) already ingests a file path/paste + enforces No-Silent-Reversal — but its job is "decompose MY brain-dump", not "synthesize upstream raw inputs". Distinct enough to keep separate.
- Vision interview V1–V7 asks personas as an OPEN question (assumes known) → seeding is additive.
- Personas live in `PRODUCT.md`; narrative in `vision.md`.
- **Security F3:** `fs_guard` is **write-only**. `--discover` reading PO-pointed paths raw is the broadest exposure surface (e.g. `--discover /etc ~/.aws`) → secret fragments could land in committed `vision.md`.

## Architecture
- Input: local files the PO names (no network). LLM synthesizes CANDIDATE personas/problems/JTBD; script handles file read + draft assembly.
- **Read fence + filter (Security F3 — mandatory):**
  - Resolve each input path; **reject traversal/symlink-escape outside the project root** (reuse `_is_within`).
  - **Extension allow-list**: `.md`, `.txt` only (reject everything else).
  - **Exclude dotfiles** (never read `.env`/`.aws`/`.ssh`/etc.).
  - **Files AND directories accepted** (PO validation 2026-06-03, rolled back to allow dirs) — a directory is walked with **bounded recursion** (depth + file-count cap), each discovered file still passing the fence/allow-list/dotfile/size filters below.
  - **Size cap** per file + bounded recursion for directory inputs; **echo the resolved file list back to the PO for confirm before reading** (the confirm step is the safety net for dir inputs that fan out).
- Output: a draft seed presented at interview start ("found these — confirm/edit/reject") feeding V1/V2. PO confirms each before anything is written. GATE-NEVER-ASSUME: no persona written without explicit confirm.

## Related Code Files
- Modify: SKILL.md (flag + menu), CLAUDE.md pointer table
- Create: `.claude/skills/product-spec/references/workflow-discover.md` (ingest → fence/filter → candidate-synthesis → seed-handoff contract)
- Reuse: `interview-vision.md` (seed feeds V1/V2), `workflow-interview.md` scout-first, GATE-NEVER-ASSUME, `fs_guard._is_within`
- Create: `scripts/ingest_raw_inputs.py` (deterministic read-fence + extension/dotfile/size filter + draft scaffold; synthesis stays LLM)

## Implementation Steps
> **TDD:** write step 5 tests FIRST (incl. the fence/secret tests + the no-auto-commit gate test), confirm fail, implement to green, re-run full suite.
1. `ingest_raw_inputs.py`: path resolve + `_is_within` fence + `.md/.txt` allow-list + dotfile exclusion + size cap + **bounded directory recursion (depth + file-count cap)**; echo resolved list for PO confirm; emit a draft scaffold.
2. `workflow-discover.md`: candidate-synthesis rules, confirm/edit/reject handoff into Vision, GATE-NEVER-ASSUME enforcement.
3. Register flag + menu + plain-language description.
4. Update E1 coupling note (none — independent of apply-critique except both ingest; this phase depends on [3] only for shared fence patterns if reused).
5. Tests: traversal/symlink rejected; **directory input walked with bounded recursion (depth/count cap enforced)**; dotfile (`.env`) skipped even inside a dir; non-`.md/.txt` rejected; oversize rejected; ingest fixture transcripts → candidate draft; **gate test: NO persona committed without a confirm step**.

## Success Criteria
- [ ] `--discover <files>` reads only `_is_within` + `.md/.txt` + non-dotfile + size-capped inputs; resolved list echoed for confirm.
- [ ] Traversal/symlink/dotfile/oversize/wrong-ext rejected (tested); **directory inputs walked with bounded recursion (depth/count cap)**, each file still fenced — no secret disclosure path.
- [ ] Candidate seeds the Vision interview; nothing written to PRODUCT.md/vision.md without confirmation (gate test).
- [ ] Scope stays tight (no entity-extraction/clustering gold-plating); no network. Tests pass; full suite green.

## Risk Assessment
- Highest scope-creep + highest exposure surface → the fence/filter is mandatory, not optional.
- Risk: overlap with `--auto` → kept separate by PO decision; if the distinction proves thin in practice, folding into `--auto --seed` later is a clean follow-up.
- `dependencies: [3]` only to reuse E1's read-fence pattern; otherwise independent.
