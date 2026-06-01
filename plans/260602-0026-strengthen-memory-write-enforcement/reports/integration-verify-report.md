# Phase 12 — Integration Verify Report

Final gate for `260602-0026-strengthen-memory-write-enforcement`. Verification + remediation-within-ownership only.
Owned files: `.claude/skills/product-spec/eval/evals.json` (added 2 OUTCOME scenarios) + this report.

## Suite counts

| Suite | Result | Count | Baseline | Delta |
|-------|--------|-------|----------|-------|
| product-spec pytest (`scripts/tests/`) | **GREEN** | **527 passed** | 477 (pre-plan) | +50 new tests (P2/3/4/5/7/9) |
| claude-pack pytest (`scripts/tests/`) | **GREEN** | **130 passed** | — | docstring/manifest changes did not break it |

Both suites run via `./.claude/skills/.venv/bin/python3 -m pytest`. Re-ran product-spec after the `evals.json` edit: still 527 passed (no regression from the eval addition).

`full_suite_green = true` — both suites green, no regression.

## Per-check results

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | product-spec pytest green, ≥477 + new | **PASS** | 527 passed (477 baseline + 50 from P2/3/4/5/7/9). |
| 2 | claude-pack pytest green | **PASS** | 130 passed. |
| 3 | CLAUDE.md `cleanmatic:claude-pack` block byte-unchanged | **PASS** | awk-extract block (`<!-- BEGIN/END: cleanmatic:claude-pack operating guide -->`) HEAD vs working = 107 lines each, `diff -q` IDENTICAL. |
| 4 | `pack` lists harvester **and** hook; bundle deterministic | **PASS (local) / FAIL (CI clean checkout)** — see Routed regression | `selection.resolve_selection` includes `.claude/agents/memory-harvester.md` + `.claude/hooks/memory_gap_hook.py` (297 members, deterministic). Tarball SHA256 byte-identical across two builds. **BUT** the hook is gitignored → absent on a clean checkout (CI release). |
| 5 | check_fence clean — no unexpected writes outside docs/product/ | **PASS** | All 43 advisory `fence_breach` findings map 1:1 to the plan's file-ownership matrix (P2–P11 scripts/refs/docs/agent/hook/manifest/installer + this plan's own markdown). NO writes to forbidden paths: `git status` shows zero `.claude/rules/*` and zero `*.cjs` changes. |
| 6 | Cross-ref sweep — every new flag/script/agent/ref resolves | **PASS** | `memory_gap.py`, `reflect_scan.py`, `memory-enforcement.md`, `workflow-reflect.md`, `memory-harvester.md`, `memory_gap_hook.py` all exist on disk. CLAUDE.md product-spec ref-pointers (`memory-enforcement.md`, `guardrails-and-boundaries.md`) resolve; `error-catalog.md` resolves under claude-pack (full path). New artifacts referenced across CLAUDE.md / SKILL.md / GUIDE-EN / GUIDE-VI / README / references. |
| 7 | CLAUDE.md size delta = pointers-only | **PASS** | +12 lines (466→478): 2 workflow-table rows, 1 "Memory hygiene" bullet, 2 scripts-list entries, 1 hook note — every line points to `references/memory-enforcement.md` or is a terse scripts-list entry. No operative detail inlined (honors locked doc-placement). Entire diff sits above the marker block. |
| — | Leak sweep (rule §5: no phase/finding-code in shipped code/prose) | **PASS** | grep for `P<n>` / `phase-<n>` / `F<n>` / `red-team R<n>` / `§<n>` across CLAUDE.md, SKILL.md, the two new refs, both new scripts, the agent, and the hook → empty. |

## OUTCOME validation (added to `eval/evals.json`)

Two end-to-end scenarios were added (ids **17**, **18**) exercising the new mechanism. Each pairs a **deterministic structural anchor** (gradeable by a real script function) with an **llm_advisory** assertion for the part the plan flags as the honest ceiling (write-rate is LLM-behavioral).

- **id 17 — surfaced contradiction → DEC recorded.** Fixture `impact-pass-spec` (approved `PRD-AUTH-E1` contradicted by the PRD's new passwordless scope).
  - structural: `memory_gap.collect()` emits an `approved_changed_no_dec` signal (closed enum) when the approved `body_hash` is stale with no matching DEC.
  - structural: `decision_register.py --alloc-id` returns the next monotonic `DEC-<n>` (`^DEC-\d+$`) and `--append` writes a valid append-only record. (Grounded: `--alloc-id` on `valid-spec` returns `DEC-1`.)
  - llm_advisory: the engine surfaces keep/change/hybrid and persists the ruling, NEVER silently flips `approved`→`draft` (GATE-NO-SILENT-REVERSAL).
- **id 18 — fence breach → 3E slip recorded; re-validate unchanged → 0 re-judges.** Fixture `valid-spec`.
  - structural: `memory_gap.collect()` emits a `fence_breach` signal (reusing `check_fence.scan`) for an out-of-boundary write.
  - structural: after a first `--validate` populates `judgments.json`, `judgment_cache --check` returns `fresh:true` for every node of the unchanged spec → no new verdict written (0 re-judges, the `body_hash`-key reuse path).
  - llm_advisory: the engine records a 3E self-correction to `.memory/self-corrections.json` rather than waving off the fence nudge.

`evals.json` validated as well-formed JSON: 19 scenarios total. No eval-harness test asserts a fixed scenario count, so the addition is regression-safe (product-spec suite re-ran green at 527).

## Dogfood checklist (HONEST framing)

> pytest validates the **mechanism** (the scripts emit the right signals deterministically). eval + dogfood validate the **outcome** (the writes actually land). **Write-rate is LLM-behavioral** — enforcement raises the consideration-rate, never the write-quality; the LLM can still rubber-stamp "none". This checklist is a manual run, not an automated gate.

Run product-spec against `.claude/skills/product-spec/examples/acme-shop` and confirm each forcing-function fires end-to-end:

- [ ] `--validate` → the **Memory pass** forcing-function runs and reports unrecorded signals (not skipped).
- [ ] Interview a prose turn → the **3D per-prose-turn** nudge fires (PO-style observation offered).
- [ ] Edit an `approved` artifact's body without a DEC → `memory_gap` surfaces `approved_changed_no_dec` → contradiction protocol → `DEC-<n>` lands in `docs/product/decisions.md` (no silent flip).
- [ ] Trigger a write outside `docs/product/` → `fence_breach` signal → 3E self-correction recorded.
- [ ] `--validate` twice with no edits → second pass reuses the judgment cache (0 re-judges).
- [ ] Opt in the Stop hook via `install.sh --memory-hook` → `settings.local.json` merge is idempotent; hook nudges once (`stop_hook_active`) for nudge-signals, persists for `fence_breach`.
- [ ] `--status` → surfaces `unrecorded_signals` + the soft `--reflect` suggestion.
- [ ] `--reflect` → `reflect_scan.py` produces git-degrade-safe anchors → read-only harvester agent proposes candidates → persist-after-PO-confirm.

## Routed regression (NOT patched — outside Phase 12 ownership)

**`.claude/hooks/memory_gap_hook.py` is gitignored → it will not be committed, and the CI release build (clean checkout) cannot bundle it.**

- Root cause: `.gitignore` line 76 `/.claude/*` ignores everything under `.claude/`; the re-includes cover `!/.claude/agents/**` (line 88) so `memory-harvester.md` commits, and `!/.claude/skills/product-spec/**`, but there is **NO** `!/.claude/hooks/**` re-include. `git check-ignore` confirms: `memory_gap_hook.py` → ignored (will NOT commit); `memory-harvester.md` → not ignored (will commit). `git ls-files .claude/hooks/` is empty (whole dir untracked).
- Impact: a fresh `git clone --depth 1` of this repo has no `.claude/hooks/` directory at all. The release workflow (`.github/workflows/claude-pack-release.yml`) uses `actions/checkout@v4` (git-tracked files only) then runs `python -m pack`, which resolves the hook via the manifest off the **filesystem** — on CI that file is absent, so the reproducible release bundle will miss the hook (or error). Local builds pass only because the file exists on disk here. This breaks plan success-criterion #4 under CI conditions.
- **Owning phase: P7** (created `memory_gap_hook.py` at the top-level `.claude/hooks/`) and/or **P8** (installer/registration wiring). The fix is a one-line `.gitignore` re-include — e.g. `!/.claude/hooks/` + `!/.claude/hooks/memory_gap_hook.py` (mirroring the existing agents re-include) so the skill-owned hook is tracked while the ck-managed `*.cjs` infra stays ignored if intended. `.gitignore` is in NO phase's ownership matrix, so this needs the lead to assign it (likely fold into P7/P8). Not patched here — out of Phase 12 ownership (`eval/evals.json` + this report only).

## Whole-plan consistency

- Locked decisions re-checked against shipped state: opt-in hook only (registered solely via `install.sh --memory-hook`, never auto), hook = Python/venv reusing `memory_gap.py`, harvester read-only at top-level `.claude/agents/`, cache never authoritative, CLAUDE.md = ref-only pointers, claude-pack marker byte-unchanged. All hold in the working tree.
- No forbidden-path edits: `.claude/rules/*` untouched, `*.cjs` hooks untouched, claude-pack marker block byte-identical.

## Unresolved questions

1. **`.gitignore` hook re-include (blocking for CI release, NOT for local/PR merge).** Needs lead to assign the one-line `.gitignore` fix to P7 or P8. Until then, the hook ships in local bundles but vanishes on a clean CI checkout. Everything else is fully green.
