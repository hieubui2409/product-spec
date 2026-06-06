---
title: N1 finding-level fingerprint (spec-span anchor)
description: >-
  Anchor critique findings-index identity to cited spec-line text (+severity) so
  repeat/inherit/rollup dedup is per-finding and line-drift-immune
status: completed
priority: P2
branch: master
tags:
  - product-spec-critique
  - cache
  - tdd
blockedBy: []
blocks: []
created: '2026-06-06T09:31:00.262Z'
createdBy: 'ck:plan'
source: skill
---

# N1 finding-level fingerprint (spec-span anchor)

## Overview

Give each critique finding a **stable per-finding identity** anchored to the spec text it cites, so the
findings-index dedup/count is precise per finding AND immune to line drift. Replaces the current NODE-level
collapse (`_node_of`) + line-embedded key (`<evidence_id>@<ts>`) that (a) can't tell two findings apart on one
node and (b) double-counts one logical blocker after a line shift.

**Chosen design (Solution 3 + 3b):**
```
finding_fingerprint = sha256(node + "\0" + severity + "\0" + normalize(cited_spec_line_text))[:16]
```
Anchored to deterministic spec content — NOT LLM `why` prose (paraphrase-fragile), NOT line number (drifts).

**Source of truth:** `plans/reports/brainstorm-260606-1627-n1-finding-fingerprint-spec-span-anchor-report.md`

### Key facts (grounded)
- Index `critique-findings-index.json` committed under `.memory/`; key `eid@ts`; row = `severity,why,fix,dec_worthy`;
  LOSSY (blocker + DEC-worthy only). `version: 1`.
- 3 consumers in `critique_inherit.py` all read through `_index_rows` (dedup per `evidence_id`, latest ts):
  `build_inherited_context`, `build_descendant_rollup`. Fix `_index_rows` dedup key → both inherit + rollup correct.
- `index_report_findings(root, ts, scope, findings)` — NO graph param; resolver builds graph from root via
  `spec_graph.build_graph(root)` (one parse per write, cheap). Keeps signature stable.
- `spec_graph` node carries `file` (relative to `docs/product/`); abs line file = `root/docs/product/<file>`.
  **Caveat (B2):** BRD-goal nodes have `file=brd.md` + `body_hash=None` — goal content lives in BRD frontmatter, NOT a
  body line. A goal evidence citing a structural line (`---`) normalizes to "" → eid fallback. Not uniform; goals accept
  eid-fallback (documented limitation).
- Repeat-offense **vs prior reports is LLM-side** (consolidator reads `prior_reports` text) — OUT of scope.
- Tests use `make_proj` (real `valid-spec` fixture w/ `docs/product/` source) → end-to-end line resolution testable.

### Non-negotiable constraints
- Run scripts/tests via `.claude/skills/.venv/bin/python3`.
- **No regression**: anchor = collected passing-case count via `pytest --co -q` (NOT a file count).
- Additive only: new field, keep key `eid@ts`, version 1→2, tolerant read of old rows. No migration tooling.
- Graceful degradation (source unreadable / node deleted / line out of range) → fall back to `evidence_id`; never crash.
- YAGNI/KISS/DRY. No fuzzy/semantic `why` matching. No change to LLM consolidator.

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | [Failing tests (TDD red)](./phase-01-failing-tests-tdd-red.md) | Completed |
| 2 | [Fingerprint compute + storage (write path)](./phase-02-fingerprint-compute-storage-write-path.md) | Completed |
| 3 | [Read-path dedup + regression green](./phase-03-read-path-dedup-regression-green.md) | Completed |

## Dependencies

- **`plans/260603-0028-spec-critique-lifecycle-cache-inherit`** — frontmatter `status: pending` but the code it
  describes (`critique_cache.py`, `critique_inherit.py`) is already shipped + committed (referenced as DONE by the
  backlog plan `260603-1817`). Treated as the **stale-pending ancestor** of this code, not a live conflict. N1 builds
  ON it. No `blockedBy` set. ⚠️ flag for user: that plan's status likely should be `completed`.

## Acceptance criteria (whole plan)
1. Same logical blocker re-critiqued after a **pure line shift with byte-identical cited text** (`:5`→`:7`) → ONE
   counted, not two. (M1: guarantee is scoped to unchanged text on the same cited line — LLM citing a different/nearby
   line, or markdown reflow re-wrapping the sentence, still breaks dedup. Residual, documented — not over-promised.)
2. Two distinct findings on the same node (different cited lines/text) → TWO distinct fingerprints.
3. Editing the cited spec line text → new fingerprint (new finding semantically).
4. Old committed index (no `finding_fingerprint`) loads + dedups without error (eid fallback). (Back-compat = the
   `... or eid` key, NOT the version field — M3.)
5. Source unreadable / line out of range / node absent / **normalized-empty cited line (B1)** / **BRD-goal structural
   line (B2)** → no crash, eid fallback; distinct findings do NOT collide.
6. Full existing suite green; collected passing-case count unchanged vs baseline.
