---
phase: 4
title: "Orchestration references + voice floor"
status: completed
priority: P1
effort: "1d"
dependencies: [3]
---

# Phase 4: Orchestration references + voice floor

## Overview

Wire the P1–P3 scripts into the LLM flow by editing the markdown references (the orchestration contract). Teach `workflow-critique.md` the provenance branch, web-TTL gate, the consolidator's consumption of `inherited_context`/`descendant_rollup` (lens stays blind), the findings-index write at step 6, and humanized-output reuse. Add the IN/OUT-of-override table to `voice-and-tone.md` (Q3 invariant). No unit tests here — this is prose; P5 fixtures exercise it.

## Requirements

- **[PREREQUISITE — R6] Refactor the 4 lens prompts to be truly voice-neutral.** This MUST land before/with the consolidate_only wiring — the whole cache-across-levels thesis depends on it.
  - In each of `spec-critique-product.md` / `-tech.md` / `-market.md` / `-craft.md`: change the `critique` field spec from "the sarcastic but grounded observation, **in the active lang/level**" to a **neutral, grounded observation** (the WHAT, not the voiced barb); REMOVE the per-level voice instruction ("Follow voice-and-tone.md at the `--level`"), keep only lang. Resolve the internal contradiction (the line that already says "the consolidator renders the level voice/register downstream" becomes the single truth). The lens still emits `{lens, evidence, critique(neutral), why_it_dies, fix, severity, source?}` and still grounds every line + ends in a fix — only the VOICE moves out.
  - The **consolidator becomes the SOLE voice home** (it already renders at `--level` with full register logic, `spec-critique-consolidate.md:99-129`) — no consolidator change needed beyond confirming it does not assume pre-voiced lens text.
  - Why this is the premise: a cached lens finding must be level-INDEPENDENT for `consolidate_only` to re-render it at any level. A double-voiced lens makes the lens-cache reusable only at the same level (which the PO rejected). Cite this rationale in the lens contract.
- **`workflow-critique.md` edits:**
  - **Step 2/3 (build bundle):** after `critique_scan.py` emits the bundle, read `bundle["provenance"]["reuse"]`:
    - `full` → report already current; tell the PO, offer `--fresh` to force; stop or just point at the existing report.
    - `consolidate_only` → skip lens fan-out (Step 4); load the **full** prior lens-findings array from the **lens-cache** `critique-lens-cache/<lens_findings_hash>.json` (R1 — NOT the findings-index, which is lossy); jump to Step 5 (re-consolidate at the new level). Header notes "lens findings reused from `<report>@ts`". If the lens-cache file is missing, the script already downgraded the verdict to `relens` (P2) — do not attempt a partial reuse.
    - `relens` → **whole-scope re-lens by default** (the lens agents take a whole-scope bundle; there is no per-node lens entry point). `changed_ids` is advisory provenance shown in the header ("N node(s) changed since last critique"), not a per-node dispatch — partial per-node re-lens is explicitly OUT of scope (would need a reduced bundle + merge; YAGNI). Re-running the whole scope is correct, just not maximally frugal.
    - `none` → full fresh run.
    - `--fresh`/`--force` always forces `none`.
  - **Bootstrap note:** the findings-index + lens-cache start empty. Run 1 of any scope has nothing to reuse/inherit → `none` + empty `inherited_context`/`descendant_rollup` is correct-by-design, not a bug. Reuse/inherit/rollup begin working from run 2+ (and require the parent-before-child ordering for cross-critique context).
  - **Web-TTL gate (market lens):** before spawning the market lens, the agent uses the P1 web-cache (`get_cached`, 14-day TTL) for any URL it would fetch; `--refresh-web` forces re-fetch + `put_cached`. State that the cache is reuse-only, never fabricates, and `--no-web` still wins (no fetch, no cache read).
  - **Step 5 (consolidate) — NEW consumer paragraphs:** the consolidator (and ONLY the consolidator) reads `bundle["inherited_context"]` + `bundle["descendant_rollup"]`:
    - Inherited items render in a SEPARATE section "Kế thừa từ cha / Inherited from parent" with each item's `source` (`<parent-id>@<ts>`); **never added to the severity tally**.
    - Rollup renders a one-line verdict ("3/5 critiqued children carry blockers → delivery risk at this parent") in the parent's section.
    - Repeat-offense (evidence-ID == scope or descendant) keeps using the existing `prior_reports` plumbing — now fed precisely by the index.
  - **Step 6 (write) — NEW:** after writing the report: (1) `put_lens_findings` the full lens array to the lens-cache keyed by `lens_findings_hash` (R1 — this is what makes a FUTURE `consolidate_only` possible); (2) `index_report_findings` (P3) upserts this run's blockers+DEC to the findings-index; (3) write the report **frontmatter** (P2 `build_report_frontmatter`, carrying that same `lens_findings_hash`); (4) refresh `critique-state.json` (`last_ts`/`provenance_hash`/`blocker_count`). Humanized-output: before humanizing, check the P1 humanized-cache by `hash(consolidated)`; on hit reuse, on miss humanize then `put_humanized`.
  - **The "lens ignores inherited_context" rule** — copy the 5-reason rationale from the brainstorm (§"Vì sao lens BỎ QUA") into the Step-4 lens contract: anti-anchoring, scope discipline, consolidator's job (DRY), ×4 cost, double-surface. The market exception ("see parent's verdict, skip re-search") is handled by web/judgment cache reuse, NOT by feeding prose to the lens.
- **`voice-and-tone.md` edit (Q3 invariant):**
  - Add the **IN/OUT-of-override table** under the universal-harm floor: what the PO CAN override (level 1-9, register gender/dialect, profanity-strength, scope, lenses, detail_level) vs CANNOT (harm floor: family/gender/region/slur/threat/self-harm/sexual targeting; collapsing subagents into the main agent). This is the single home; agents reference it.
- **`SKILL.md` + flag surface:** document the new flags (`--fresh`/`--force`, `--refresh-web`, `--no-inherit`, `--no-rollup`, `--inherit deep`) and the 3 new preferences (`critique_inherit`, `critique_rollup`, `critique_inherit_depth`). **Use the display form `--inherit deep`** (argparse `choices` idiom; the `=` form reads like a boolean) consistently across SKILL/README/GUIDE. State precedence: `--no-inherit` beats `--inherit deep`. Note the new bundle keys (`provenance`, `inherited_context`, `descendant_rollup`) in the bundle contract.
- **Agent prompt files** (`.claude/agents/spec-critique-*.md`): if the consolidate/humanize/lens agent prompts hard-code the bundle key list or "ignore X" rules, update the consolidate agent to consume the two new keys + render the separate section, and add the lens "ignore inherited_context/descendant_rollup" line. (Confirm during impl whether these live in `.claude/agents/` or are inline in `workflow-critique.md`.)

## Architecture

Pure documentation/contract changes. The data already exists (P1–P3); P4 tells the LLM agents how to consume it. DRY anchors: repeat-offense plumbing already referenced at `workflow-critique.md` Step 5 — inheritance is the SAME pass with a different label, not a parallel mechanism.

## Related Code Files

- Modify: `.claude/skills/spec-critique/references/workflow-critique.md` (Steps 2-6)
- Modify: `.claude/skills/spec-critique/references/voice-and-tone.md` (IN/OUT-of-override table under the floor)
- Modify: `.claude/skills/spec-critique/SKILL.md` (flags + preferences + bundle contract)
- Modify (R6 — confirmed these are the real homes): `.claude/agents/spec-critique-product.md` / `-tech.md` / `-market.md` / `-craft.md` (neutralize `critique` + drop per-level voice), `.claude/agents/spec-critique-consolidate.md` (consume inherited_context/rollup; confirm sole-voice-home), `spec-critique-humanize.md` (humanized-cache note)
- Read for context: P1-P3 phase reports + the brainstorm §"Vì sao lens BỎ QUA", §"Q3"

## Implementation Steps

1. Grep the 6 spec-critique agent files + `workflow-critique.md` for the current bundle-key list and the "ignore" instructions, to edit in place (no new files; update existing — per development-rules).
2. Edit `workflow-critique.md`: provenance branch (Step 2/3), web-TTL (Step 4 market), consolidator consumption + separate inherited section + no-tally rule (Step 5), index write + frontmatter + humanized-cache (Step 6).
3. Edit `voice-and-tone.md`: IN/OUT-of-override table (single home), reference it from SKILL.md gates.
4. Edit `SKILL.md`: flags, preferences, bundle keys.
5. Edit the consolidate agent prompt to render inherited_context/descendant_rollup; add the lens-ignore line to the 4 lens prompts.
6. Consistency: ensure every new flag named in SKILL.md matches an argparse flag added in P2/P3 (no doc-only ghost flags).

## Success Criteria

- [ ] **[R6] The 4 lens prompts are voice-neutral** — `critique` is a neutral grounded observation, the per-`--level` voice instruction removed, the internal contradiction resolved; consolidator confirmed as sole voice home. (Prereq for consolidate_only.)
- [ ] `workflow-critique.md` describes all 4 provenance branches, web-TTL gate, consolidator-only consumption, step-6 index write + frontmatter + humanized-cache.
- [ ] `voice-and-tone.md` has the IN/OUT-of-override table as the single home; SKILL.md references it, does not copy it.
- [ ] The 5-reason "lens ignores inherited_context" rationale is in the lens contract; the 4 lens prompts carry the ignore line; the consolidate prompt carries the consume + separate-section + no-tally rules.
- [ ] Every flag/preference documented matches a real argparse flag / preference key from P2/P3 (no ghosts).
- [ ] No prose duplication of the harm floor (DRY — single home in voice-and-tone.md).

## Risk Assessment

- **Risk: doc says a flag the script doesn't have (or vice-versa).** Mitigation: step 6 cross-check; the whole-plan consistency sweep (post-plan gate) re-verifies flag parity across SKILL.md ↔ argparse.
- **Risk: consolidator double-renders an inherited item that is ALSO a repeat-offense.** Mitigation: classification (P3) is mutually exclusive (ancestor=inherited vs ==/descendant=repeat); the consolidator contract states an item appears in exactly one section.
- **Risk: agents live inline vs in `.claude/agents/`.** Mitigation: step 1 greps first to find the real home before editing; do not assume.
- **Risk: register frontmatter / IN-OUT table contradicting the lv7-9 plan already shipped.** Mitigation: this only ADDS the override-boundary table; it must not restate or alter the existing register knob semantics (GATE-NO-SILENT-REVERSAL on approved voice spec).
