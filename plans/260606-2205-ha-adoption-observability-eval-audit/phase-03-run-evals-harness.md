# Phase 03 — run_evals harness (A3)

**Item:** A3 · **Prio:** P1 · **Effort:** L · **Status:** pending · **Depends:** A1 (exit-handling pattern reuse)

## Context links
- Blueprint Lens D: `…ha-implementation-blueprint…` (§LENS D, run_evals.py)
- HA source: `human-analyzer/eval/run_evals.py`, `eval/evals.json`
- Current evals: `.claude/skills/{product-spec,product-spec-critique,claude-pack}/eval/evals.json`

## ⚠️ DESIGN GATE (revised after red-team — verified against real files)

**Reality (verified):**
- product-spec + critique evals ALREADY tag every assertion with **`_gating: "structural" | "llm_advisory"`** (product-spec 41 structural / 13 advisory; critique 51 tagged). → **reuse `_gating`; do NOT invent a `kind:` field (DRY violation).** `structural` → runnable in harness; `llm_advisory` → reported `skipped (manual)`.
- **claude-pack evals have 0 tags + bare-string assertions** (`"gzip header bytes [4:8] == 0x00000000"`, `"second run produces identical SHA256"`). No `script`/`extract`/`expected`. → there is nothing to "run as a subset"; making it runnable = **real reshape (= the rejected option ii)**, not tagging.

**Decision (PO-confirmed 2026-06-06):**
- **Build harness on product-spec + critique `structural` subset FIRST** (already tagged → smallest reshape; proves the harness).
- **THEN reshape claude-pack** (PO chose reshape-now, not defer): add `_gating` tags (DRY-consistent with the other 2) + a machine mapping (`check:`/`extract:`) to each bare-string assertion so it becomes runnable. All 3 skills wired into CI.
- **Effort: L** (harness + checker dispatch + structural checkers + **claude-pack full reshape** + 3 CI wirings + fixtures). claude-pack reshape is the heaviest sub-task — sequence it after ps/critique green so the harness contract is settled before reshaping bare strings against it.
- Reusing `_gating` (not `kind`) keeps one home for the structural/advisory fact across all 3 skills.

## Overview
Turn the decorative `evals.json` into a runnable gate: a harness that executes each skill's eval scenarios and asserts the deterministic subset, exit 0 iff all pass. Local + CI, no network/API key.

## Key insights
- **Order: product-spec + critique first** (already `_gating`-tagged → settle the harness contract), **then reshape claude-pack** (untagged bare strings → add `_gating` + machine mapping).
- `_gating: structural` assertions map to runnable checks; `llm_advisory` are reported skipped-manual (logged, never silently dropped).
- Reuse Phase-1 subprocess exit handling discipline.

## Requirements
**Functional**
- `run_evals.py --skill <name>` (and `--all`): load that skill's `evals.json`, run each scenario via `subprocess.run(..., timeout, capture)`, evaluate `_gating: structural` assertions, print PASS/FAIL table, exit 0 iff all structural pass.
- **Reuse existing `_gating`** field. `structural` assertions need a runnable mapping — add a `check:`/`extract:` sub-field ONLY where a structural assertion lacks a machine mapping (minimal, per-assertion, no new top-level taxonomy).
- `llm_advisory` → printed as `skipped (manual)`, counted + logged (no silent caps).
- No network, no API key.

**Non-functional**
- Per-skill (avoid cross-conftest races, like `cross-skill-bug-class.yml`).
- Timeout per scenario (HA uses 90s).
- Reject scenarios using `datetime.now()` / nondeterminism from the deterministic set.

## Architecture
```
run_evals.py
  load evals.json (skill)
  for scenario:
    subprocess.run(script/cli, args, cwd=tmp-fixture, timeout, capture)
    for assertion where kind==deterministic:
        check (file exists | frontmatter ok | path absent | bytes | sha | stdout-json extract==expected)
    llm-kind → skipped(manual)
  table → exit 0/1
```
- Assertion checkers: small dispatch by a `check:` field OR inferred from assertion text patterns (prefer explicit `check:` added during tagging).

## Related code files
**Create**
- `.claude/skills/_shared/lib/run_evals.py` (shared harness, imported/invoked per skill) OR per-skill `eval/run_evals.py` — decide in design gate (lean shared to avoid 3× dup).
- `tests/` entry to run harness on a known-green fixture.

**Modify**
- `.claude/skills/{product-spec,product-spec-critique}/eval/evals.json` — add `check:`/`extract:` ONLY to `structural` assertions lacking a machine mapping. Do NOT add `kind`; do NOT touch `_gating`; no assertion reword.
- `.claude/skills/claude-pack/eval/evals.json` — **reshape**: add `_gating` to every assertion + a `check:`/`extract:` machine mapping (the bare strings become runnable). Preserve assertion intent.
- `.github/workflows/product-spec-ci.yml` + `product-spec-critique-ci.yml` + `claude-pack-ci.yml` — add a harness step after pytest (all 3).

## Implementation steps
1. Build harness (shared lib): scenario runner + structural checkers + table + exit code (TDD against synthetic fixture first).
2. Audit product-spec + critique `structural` assertions; add `check:`/`extract:` where missing (minimal). Prove green locally (ps then critique).
3. Wire harness into `product-spec-ci.yml` + `product-spec-critique-ci.yml` (no-API-key, venv python).
4. **claude-pack reshape:** add `_gating` + `check:`/`extract:` to each bare-string assertion against the now-settled harness contract; prove green; wire into `claude-pack-ci.yml`.
5. Record any bug found → `docs/audit-trail/EVIDENCE.md` (Phase 2).

## Todo
- [ ] harness + structural checkers (TDD synthetic fixture first)
- [ ] ps + critique `structural` `check:`/`extract:` added (reuse `_gating`)
- [ ] green: product-spec then critique; wire 2 CI steps
- [ ] **claude-pack reshape:** `_gating` + machine mapping per assertion
- [ ] green claude-pack; wire `claude-pack-ci.yml` step
- [ ] py_compile / pytest green (no API key, venv python)

## TDD discipline (red → green → refactor)
- **RED first:** before the harness, write tests against a **tiny synthetic evals.json** fixture: (a) all-pass scenario → exit 0; (b) one deterministic assertion fails → exit 1 + names it; (c) `llm`-kind assertion → reported `skipped(manual)`, NOT counted as pass; (d) missing fixture → loud fail, not skip; (e) scenario timeout → fail with reason.
- **GREEN:** implement runner + checkers to satisfy. **REFACTOR:** extract checker dispatch.
- Only then run against real evals.json: product-spec → critique → (reshape) claude-pack.

## Red-team angles (tests MUST cover)
- **False green:** a scenario whose script exits 0 but produced nothing → assertion (file-exists) must still FAIL. Never infer pass from exit code alone.
- **Silent skip:** an assertion with no matching checker must FAIL loudly (unknown `check:`), not be silently treated as pass.
- **advisory-as-escape-hatch:** mis-tagging a `structural` assertion as `llm_advisory` to dodge it → red-team reviews `_gating` classification; count advisory skips in output (no silent caps).
- **Nondeterminism:** scenario using wall-clock/random in deterministic set → harness rejects.
- **Fixture path traversal / write outside tmp** → run in sandboxed tmp; assert no writes escape.

## Success criteria
- `run_evals.py --all` exits 0 on clean repo; flips to 1 if a deterministic assertion breaks.
- CI runs it with no API key.
- `llm`-kind assertions clearly reported as manual-skipped (not silently dropped — log them, per "no silent caps").

## Risk
- **Over-build** (trying to LLM-judge in CI) → explicitly out of scope; deterministic subset only.
- **Fixture drift** (evals reference fixtures that moved) → harness must fail loudly on missing fixture, not skip.

## Security
- Harness runs scripts in temp dirs; no network. claude-pack dirty-fixture scenario builds `.env` at runtime (already designed that way in evals.json).

## Next steps
- A6 (full e2e pipeline) builds on this harness pattern (P2, out of current scope).
