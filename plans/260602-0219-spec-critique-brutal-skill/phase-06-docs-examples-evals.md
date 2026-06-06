---
phase: 6
title: "Docs examples evals"
status: completed
priority: P2
effort: "1d"
dependencies: [4]
---

# Phase 6: Docs examples evals

## Overview

The PO-facing docs surface (parity with product-spec): `README.md`, `GUIDE-VI.md`, `GUIDE-EN.md`, a worked `examples/` (sample critique output over the existing `product-spec/examples/acme-shop` — reused, not recreated), and `eval/evals.json`. The guides cover every flag, every use-case, and every lens as sample conversations (natural-language preferred + flag equivalent).

## Requirements

- **Functional:** README pitch + quickstart + flag table. GUIDE-VI/EN: per-flag, per-use-case, per-lens sample conversations through the acme-shop example, incl. an output sample per `--level`. examples/: 1–2 sample critique reports (default level 3 + a level-1 "ấm áp" for contrast) over acme-shop. eval/evals.json: 4–5 scenarios (basic critique, lens-select, repeat-offense/DEC bridge, **one `--lang en` parity scenario** so EN is not untested) with mechanical + LLM-advisory assertions.
- **Non-functional:** VI fully diacritic-correct, native phrasing; EN parity; sample outputs respect the voice contract (evidence+fix per line); examples reuse acme-shop (DRY).

## Architecture

- **`README.md`** (template = `product-spec/README.md`): one-paragraph pitch (what it critiques, how it differs from `--validate`), quickstart (`/spec-critique PRD-AUTH`), flag table, output location, "does NOT" list (no edit, no CI gate, no auto-memory).
- **`GUIDE-VI.md` / `GUIDE-EN.md`** (template = `product-spec/GUIDE-VI.md` structure — every UC as a sample dialogue):
  - Intro: what spec-critique is, how it differs from `--validate` (the §4 table), when to use, the personal-attack redline.
  - **By use-case:** critique whole spec · critique one branch (PRD/epic/story) — note ancestry is always pulled · pick lenses · `--interactive` · change voice level · offline `--no-web` · repeat-offense / read prior report · DEC bridge.
  - **By flag:** one in/out example each, incl. an output snippet per `--level` so the PO feels the tone.
  - **By lens:** product/tech/market/craft — what it critiques, which frameworks, 2–3 sample findings (evidence→mỉa→why→fix).
  - **Read the report:** severity, top-3, repeat-offense callout. **Boundaries:** no edit, no CI gate, level-5 warning.
- **`examples/`:** reuse `product-spec/examples/acme-shop` as input. Ship `examples/critique-acme-shop-all-level3.md` (+ optional `...-level1.md`) — also serves as eval golden material.
- **`eval/evals.json`** (schema from `product-spec/eval/evals.json`): scenarios mixing one MECHANICAL assertion + `_gating: "llm_advisory"` ones. Mechanical floor: "no finding line is byte-identical to a structural-finding `detail` string" + "every finding carries non-empty why_it_dies+fix" (checkable). Advisory: "report cites artifact IDs (`artifact_id:line`)", "market flags missing competitor grounding under --no-web", "tone matches requested --level". (Honest: the semantic 'adds value beyond validate' stays advisory.)

## Related Code Files

- Create: `.claude/skills/spec-critique/README.md`
- Create: `.claude/skills/spec-critique/GUIDE-VI.md`
- Create: `.claude/skills/spec-critique/GUIDE-EN.md`
- Create: `.claude/skills/spec-critique/examples/critique-acme-shop-all-level3.md`
- Create (optional): `.claude/skills/spec-critique/examples/critique-acme-shop-all-level1.md`
- Create: `.claude/skills/spec-critique/eval/evals.json`

## Implementation Steps

1. Read `product-spec/README.md`, `GUIDE-VI.md` (structure), `eval/evals.json` for templates.
2. Write README (pitch + quickstart + flags + does-NOT).
3. Write GUIDE-VI: per-flag + per-UC + per-lens sample dialogues through acme-shop, with per-level output snippets. Native-review VI phrasing.
4. Write GUIDE-EN parity.
5. Produce sample critique report(s) over acme-shop at level 3 (+ level 1) — hand-craft or run the real skill once it exists; must honor evidence+fix per line.
6. Write `eval/evals.json` (3–4 scenarios, LLM-advisory assertions).
7. Verify guides reference real flags/agents/paths (no drift vs Phase 4).

## Success Criteria

- [ ] README present: pitch, quickstart, flag table, output, does-NOT list.
- [ ] GUIDE-VI + GUIDE-EN cover every flag, every use-case, every lens with sample dialogues + per-level output snippets.
- [ ] examples/ ships ≥1 sample critique over acme-shop honoring the voice contract (evidence+fix), reusing acme-shop input (no new spec).
- [ ] eval/evals.json has 3–4 LLM-advisory scenarios.
- [ ] VI fully diacritic-correct, native phrasing; EN parity; no flag/path drift vs Phase 4.

## Risk Assessment

- **Doc drift vs implementation:** write docs AFTER Phase 4 (dependency set); final consistency sweep verifies flags/paths/agent names.
- **Sample output authenticity:** prefer running the real skill once (Phase 1–4 done) to generate the example rather than hand-faking, so it reflects true output.
- **VI quality:** native-review pass for natural sarcasm (the whole point); avoid translated-English stiffness.
