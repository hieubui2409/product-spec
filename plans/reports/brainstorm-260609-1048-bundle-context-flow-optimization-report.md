# Brainstorm — Bundle context/flow optimization (measure-first, conservative)

- **Date:** 2026-06-09
- **Scope:** all 3 bundle skills — core `product-spec` + `product-spec-critique`; secondary `release` + `telemetry` (low value / low freq → light touch only)
- **Status:** PO-approved design → ready for `/ck:plan --hard --tdd`

---

## 1. Problem statement

Reframe (PO): this is **NOT byte-cutting** — it is auditing the **effectiveness of the operating
FLOW** of the two core skills (how they route + load context per turn) and trimming genuine waste.
**NON-NEGOTIABLE: no edit may reduce the reasoning effectiveness of any skill.**

### Footprint scout (lines ≈ token proxy)
- **Always-on (every turn):** root `CLAUDE.md` 60 + `.claude/rules/*` ~265 = ~325. **OUT of scope —
  the `rules/*` layer belongs to ClaudeKit, not this bundle.**
- **SKILL.md (per skill-activation):** product-spec 196 · critique 182 · release 197 — flag tables are
  verbose (each row a full paragraph).
- **References (on-demand per flag, already lazy):** product-spec 3427/23 files (heaviest
  `workflow-interview` 356, `frontmatter-and-id-spec` 343, `workflow-validate` 319,
  `validation-rules-spec` 229); critique 812 (`voice-and-tone` 310, `workflow-critique` 275);
  release 587.

### Honest read
Refs are already lazy-loaded → "split smaller" yields diminishing returns alone. Real levers:
**(1) SKILL.md flag-table verbosity** (paid every activation), **(2) prose that duplicates what a
script already enforces**, **(3) flow waste** — a flag pulling refs it doesn't need, GATE prose
duplicated across `CLAUDE.md`/`guardrails-and-boundaries`/workflow files.

---

## 2. Decisions (PO-confirmed)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Target levers | **prose-vs-script + SKILL.md verbosity + flow effectiveness** (NOT the ClaudeKit rules layer) |
| 2 | Scope | **all 3 skills**; release/telemetry = light dedup only (low value) |
| 3 | Acceptance | **token harness (before/after) + full eval/pytest green** |
| 4 | Scriptable depth | **Conservative** — keep grammar + mental-model scaffold; only drop script-owned enumerations |
| 5 | Build order | **Harness → flow-audit → (compact SKILL.md + scriptable)** |
| 6 | Critique voice | **dedup only** — `voice-and-tone.md` content UNTOUCHED (reasoning-critical: level/register/safety floor) |

**Guiding rule (the NON-NEGOTIABLE made operational):** every cut ships with two proofs — (a) harness
shows token-per-path dropped, (b) the eval scenarios for that path (incl. LLM-judged via `llm_eval.py`)
stay green = reasoning preserved. **No (b) → no cut (revert).**

---

## 3. Approaches considered

- **A. Aggressive scriptable (script = sole SoT, prose → bare pointer).** Biggest cut. **Rejected** —
  strips the reasoning scaffold the LLM needs to *author* specs; violates the NON-NEGOTIABLE.
- **B. Flow-only (fix ref-load triggers + dedup, no SKILL.md/ref content edits).** Lowest risk, lowest
  gain. Folded IN as block 2, but insufficient alone.
- **C. Measure-first conservative flow-refactor (CHOSEN).** Harness-gated, conservative content edits +
  flow audit, double-proof per change. Balances real savings with the reasoning guarantee.

---

## 4. Chosen solution — 5 blocks (in build order)

### Block 1 — Token-footprint harness (FIRST; baseline + gate)
- Script: for each skill, compute **tokens-per-flag-path** = SKILL.md + exactly the refs that flag's
  "Loads references on demand" row triggers. Emit before/after JSON.
- Doubles as a **flow-waste detector**: flags whose declared ref-load set exceeds what the flag
  actually needs.
- Deterministic, offline, CI-friendly (a token/line counter + the flag→ref map parsed from SKILL.md).

### Block 2 — Flow audit (the core of the reframe: product-spec ↔ critique)
- Build the real flag→ref dependency map; find: refs loaded "just in case", the `--apply-critique`
  handoff (consumes lens-cache JSON, not prose — verify no prose re-load), and **GATE/fact prose
  duplicated** across `CLAUDE.md` ↔ `guardrails-and-boundaries.md` ↔ `workflow-*`.
- Fix: ONE home per GATE/fact + pointer elsewhere (DRY); align each flag's ref-load to true need.

### Block 3 — SKILL.md flag-table compaction (conservative)
- Per flag: keep **one line = what + when + ref-pointer + the one GATE keyword** (enough for the router
  to choose correctly); move elaboration (edge cases, examples) into the ref that already loads when the
  flag fires. Routing crispness preserved.

### Block 4 — Prose-duplicates-script → scriptable (conservative)
- `frontmatter-and-id-spec.md` + `validation-rules-spec.md`: **keep** the grammar table + mental model
  (LLM needs them to generate); **replace** the exhaustive severity/check enumerations (already owned by
  `check_*`/`strict_gate`/`frontmatter_parser`) with "script X is the SoT — run it for the list".
- release/telemetry: light dedup only.

### Block 5 — Double-gate wiring + docs
- Wire the harness + eval into a repeatable check; record before/after deltas; update CHANGELOG +
  version. Each landed change cites its (a)+(b) proof.

**OUT scope:** editing `.claude/rules/*` (ClaudeKit), aggressive prose removal, `voice-and-tone.md`
content, runtime caching/hooks (Claude Code owns those).

---

## 5. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Compact SKILL.md → router picks wrong flag | Keep "when to use" + GATE keyword per flag; routing eval scenario before/after |
| Dropping prose → LLM loses reasoning context | Conservative: keep grammar + mental model; drop only script-owned enumerations; LLM-judged eval is the gate |
| "Reasoning degraded" is hard to measure | Use eval/golden LLM-judged runs as the reasoning proxy, pinned before/after each change |
| Flow audit churns critical refs | voice-and-tone untouched; GATE dedup keeps one authoritative home (never deletes a GATE) |
| release/telemetry over-investment | Explicitly light-touch (low value/freq) |

---

## 6. Success metrics / validation

- Harness reports a **measurable token-per-flag-path reduction** for product-spec + critique (release/
  telemetry incidental).
- **Full pytest (656) green** + **eval scenarios green** (structural + LLM-judged advisory) after every
  block — the reasoning-preservation proof.
- No GATE removed; every GATE has exactly one authoritative home + pointers (DRY check).
- `verify_skill_versions.py` + CHANGELOG consistent.

---

## 7. Next step

`/ck:plan --hard --tdd` — TDD because this refactors existing behavior with strong existing test
coverage to preserve (the 656-test suite + eval scenarios are the lock-in); `--hard` for red-team rigor
given the NON-NEGOTIABLE reasoning constraint.

## 8. Open questions

- Token-count method in the harness: exact tokenizer vs line/char proxy? *(Recommend a cheap
  char/word proxy first; exact tokenizer only if a target % needs it — PO chose harness+eval, no hard %.)*
- Whether the flow audit surfaces a GATE-dedup that touches an `approved`-artifact-governing rule →
  would route through the normal GATE-NO-SILENT-REVERSAL (record a DEC), not a silent edit.
