# Shared Context — Code Audit of the product-spec Harness v2.4.0

**You are auditing the ACTUAL CODE of a Claude-Code skill bundle** (the "harness"), not a product spec.
The harness is 4 PO-facing skills written in Python (scripts) + Markdown (SKILL.md contracts). Your job:
find **real defects** in the code assigned to you — bugs, contract violations, safety holes, dead/duplicated
code, incompleteness, and fragile tests. Read the actual files. Cite real line numbers.

Skills root: `/home/hieubt15/Documents/vsf/product-spec/.claude/skills/`

---

## 1. What the harness is (so you judge intent correctly)

Four skills, each `scripts/*.py` + `SKILL.md` (the human/LLM contract) + `scripts/tests/`:

- **product-spec** (67 scripts, ~14.9k LOC): the core PO toolkit. Builds a spec graph
  (VISION→BRD→PRD→epic→story), validates it (structural + LLM-judgment), renders visuals,
  manages a Decision Register, snapshots/audit-trail/outcomes, migrators, behavioral memory.
- **product-spec-critique** (12 scripts, ~1.8k LOC): read-only multi-lens critique of a spec
  (product/tech/market/craft lenses + consolidator + humanizer). Builds a `critique_scan` bundle
  the lens subagents read.
- **release** (25 scripts, ~3.3k LOC): packs/releases the bundle, writes MANIFEST + CHANGELOG,
  CI safety checks, upgrade planner/apply, skill-version verification.
- **telemetry** (17 scripts, ~2.7k LOC): read-only usage/health lenses over local telemetry logs;
  plain-Vietnamese analytics proxy.

**Source-of-truth principles the code MUST honor** (violations are findings):
- Frontmatter (YAML) is source-of-truth; structure is never inferred from headings.
- DRY: one home per fact; cross-reference by ID, never duplicate prose.
- Script-vs-LLM split: scripts handle graph/struct deterministically; LLM judges prose.
- Never overwrite PO prose silently; never silently reverse an `approved` artifact.
- `fs_guard.py` gates filesystem writes; scripts must not write outside allowed roots.

## 2. The audit rubric — five lenses (apply ALL to your assigned files)

For every file you're given, hunt for:

1. **Correctness / logic bugs** — wrong results, off-by-one, bad edge-case handling, mutable-default
   args, unhandled `None`/empty, incorrect regex, wrong comparison/ordering, swallowed exceptions,
   resource leaks, encoding bugs, **time-coupling** (using real `datetime.now()` in a way that makes
   behavior or tests date-dependent), unicode/Vietnamese-diacritic handling, YAML edge cases.
2. **Contract fidelity (SKILL.md ↔ code)** — read the skill's `SKILL.md`. Does a flag/command/output
   the contract promises actually exist and behave as described? Does code do something the contract
   forbids (e.g. assume scope, auto-approve, overwrite prose)? Are GATE behaviors (no-silent-reversal,
   never-assume) actually enforced in code where the contract says they are?
3. **Safety / integration** — `fs_guard` bypasses, path traversal, writing outside allowed roots,
   `subprocess`/`shell=True` risks, unsafe `eval`/`exec`/`pickle`, unvalidated external input,
   cross-script import coupling that breaks if run standalone, hard-coded absolute paths, missing
   error handling on file/JSON/YAML reads.
4. **DRY / dead-code / incompleteness** — duplicated logic that drifts (e.g. same check implemented
   twice), dead/unreachable code, unused functions/params, half-wired features (a writer with no
   reader, a flag parsed but ignored), missing migrator for a known schema-drift check, TODO/stub
   left in a shipped path.
5. **Test quality / coverage** — tests that are time-dependent / order-dependent / non-deterministic,
   tests asserting nothing meaningful, fixtures with hard-coded absolute dates that rot, critical
   logic with no test, tests that would pass even if the code were broken.

## 3. Calibration — one CONFIRMED defect already found (don't re-find, match its bar)

`telemetry/scripts/lens_artifact_heat.py` `gather(days=N)` computes
`cutoff = datetime.now(timezone.utc) - timedelta(days=days)`, but its test
`tests/test_lens_artifact_heat.py::...::test_heat_lens_respects_days_window` hard-codes the "recent"
event at `2026-06-12T10:00:00+00:00` and asserts it's inside a `days=1` window. Once wall-clock passes
~2026-06-13 10:00 the event falls outside the window and the test FAILS. **Class: time-dependent test +
hard-coded absolute dates in fixtures.** This is exactly the severity/precision bar: a concrete file,
a concrete line, a concrete failure mode, a concrete fix. Look for *this caliber* of real issue.

## 4. Severity definitions

- **blocker** — produces wrong output a PO would trust, corrupts/loses data, bypasses a safety GATE,
  or breaks a documented command for everyone.
- **high** — real bug or contract violation that bites in common usage; fragile test that fails on a
  normal calendar day; safety hole reachable with normal inputs.
- **medium** — edge-case bug, DRY/drift smell that will cause divergence, incompleteness that blocks a
  promised workflow, test that doesn't test what it claims.
- **low** — cosmetic, dead code, minor inconsistency, defensive-coding nicety.

Do NOT pad. A clean file with no real issues should return zero findings for that file. Inventing weak
findings wastes the audit. Quality over count.

## 5. How to report each finding (MANDATORY structured format)

Each finding:
- `id`: short slug, prefix with your cluster code (e.g. `ps-c-judgment-stale-key-1`)
- `cluster`: your cluster code (given in your task)
- `file`: repo-relative path (e.g. `.claude/skills/product-spec/scripts/judgment_cache.py`)
- `lens`: correctness | contract | safety | dry-dead | test
- `severity`: blocker | high | medium | low
- `evidence`: `<file>:<line>` — you MUST open the file and use a REAL line number. Never guess.
- `title`: one plain line (Vietnamese)
- `why`: the concrete consequence if left as-is (Vietnamese, plain language — explain the harm, not
  the framework name)
- `fix`: a specific, actionable fix (Vietnamese, plain language)
- `confidence`: high | medium | low (your honest confidence it's a real defect)

## 6. Tone

Audience is the harness maintainer (a PO who is not a deep engineer). Write `title`/`why`/`fix` in
**plain Vietnamese, low jargon**. Technical terms are OK when unavoidable (it's code) but always tie the
finding to a concrete consequence. Be direct about severity. No sarcasm. Every finding earns its place
with evidence + why + fix. If a file is genuinely clean, say nothing about it.
