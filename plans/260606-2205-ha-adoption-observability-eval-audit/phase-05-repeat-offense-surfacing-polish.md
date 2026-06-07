# Phase 05 — Repeat-offense surfacing polish

**Item:** (PO-requested, derived from A9-safe-slice) · **Prio:** P1 · **Effort:** S · **Status:** pending · **Depends:** none (touches critique template/agents only)

## Context links
- Blueprint Lens B: `…ha-implementation-blueprint…` (§LENS B — "✅ Repeat-offense tracking" is the endorsed low-risk slice)
- N1 (shipped): `plans/260606-1627-n1-finding-fingerprint-spec-span-anchor/` — `finding_fingerprint` makes repeat-offense per-finding-accurate + line-drift-immune
- Repeat-offense lives in: `.claude/agents/critique-consolidator.md`, `.claude/agents/critique-humanizer.md`, `references/workflow-critique.md`, `references/humanizer-and-anti-ai-tells.md`
- Plumbing: `critique_inherit.py` (`index_report_findings`, `build_inherited_context`, `_finding_fingerprint`), `critique_cache.py` (`finding_fingerprint` in `_INDEX_FIELDS`)

## Overview
The critique already detects + reports repeat-offense findings (consolidator detects vs prior reports; report has a repeat-offense section). N1 made the match precise. This phase makes the **presentation louder** — at higher voice levels, the repeat-offense annotation scolds ("lần thứ N rồi, đọc lại đi") with the prior occurrences listed. **Presentation only.**

## ⛔ Litmus test (hard boundary — do not cross)
> If `findings-index` were deleted, the *set of flagged findings* MUST NOT change.
> Lenses judge the current spec **blind to repeat-counts**. The consolidator attaches the count **after** judgment as annotation. Count → presentation = OK. Count → lens/judgment input = A9 = FORBIDDEN this phase.

Mechanism guarantees:
- **Reproducible:** count is a pure script lookup over the committed `.memory/` findings-index (git-diffable). Same index + spec → same count. LLM does not "remember" between runs.
- **No echo chamber:** count never enters lens prompts; cannot manufacture a finding the fresh lens didn't independently flag.
- **No auto-decision:** louder wording is still a report sentence — no DEC auto-created, no spec edit, no resolved-marking. `--apply-critique` still requires PO ruling.

## Key insights
- This is a **template + voice change**, not new plumbing. The count/occurrence data already flows via `build_inherited_context` / repeat-offense detection.
- Wording must scale with voice level (1..9): neutral at ≤5 ("repeat: also seen in X, Y"), scolding at 7+ ("lần thứ N rồi — đọc lại đi"). Must stay inside the universal-harm floor (`voice-and-tone.md`).
- Humanizer must **preserve** the repeat-offense section + its occurrence IDs (it already lists repeat-offense in preserve-set — confirm it preserves the *louder* form too).

## Requirements
**Functional**
- Repeat-offense report section shows: finding fingerprint/symptom + **occurrence count** + **prior occurrence refs** (scope/ts) + (level-scaled) scolding line.
- Count + occurrences sourced from findings-index lookup (existing), never from lens guesswork.

**Non-functional**
- Litmus test holds (add/keep a test asserting lens prompts contain no repeat-count).
- Voice-level scaling respects existing IN/OUT table; level 9 still re-confirms.
- Determinism of which findings are flagged unchanged.

## Related code files
**Modify**
- `.claude/agents/critique-consolidator.md` — instruct: after dedup/severity, attach repeat-offense annotation with count + occurrence refs; emphasis scales with level. (Confirm exact current wording first.)
- `.claude/agents/critique-humanizer.md` — ensure preserve-set keeps the louder repeat-offense block + occurrence IDs verbatim.
- `references/workflow-critique.md` — document the louder surfacing + reaffirm litmus boundary.
- `references/humanizer-and-anti-ai-tells.md` — repeat-offense preserve note (if wording changes).

**Do NOT modify**
- The 4 lens agents' judgment prompts (must stay blind to repeat-count — the boundary).
- `critique_inherit.py` / `critique_cache.py` judgment logic (data already there; no scoring/feedback added).

## Implementation steps
1. Read current repeat-offense wording in consolidator + humanizer + workflow-critique to find exact insertion points.
2. Add level-scaled scolding template for the repeat-offense section (consolidator instruction).
3. Confirm humanizer preserves the louder block + occurrence refs.
4. Add/extend a `bug_class` (or unit) test asserting **no lens prompt** references repeat-count (litmus enforcement) — if testable via the bundle assembly path.
5. Document the boundary in workflow-critique.md.

## Todo
- [ ] locate exact repeat-offense wording (4 files)
- [ ] level-scaled scolding template (consolidator)
- [ ] humanizer preserve-set updated
- [ ] litmus test: lens prompts free of repeat-count
- [ ] workflow-critique.md boundary note
- [ ] no determinism change (verify flagged-set stable with/without index)

## TDD discipline (red → green → refactor)
**The enforceable boundary is INPUT-ISOLATION, not output-stability** (the critique is LLM/non-deterministic by charter — output cannot be diffed in CI).
- **RED first — the litmus test (the ONLY mechanical guard):** test over the **bundle-assembly path** asserting **assembled lens-input strings contain NO repeat-count / occurrence data** (grep the lens prompts built by `critique_bundle.py` / `build_inherited_context`). Write BEFORE touching templates; must pass before AND after this phase.
- **RED — presentation lookup test:** given a findings-index with a fingerprint in ≥2 prior reports, assert the **deterministic lookup** (`index_report_findings`/repeat path) returns `count` + occurrence refs. (This tests the data feed, which IS deterministic — NOT the rendered report.)
- **GREEN:** add level-scaled scolding template. **REFACTOR:** humanizer preserve-set tidy.
- **NOT a CI test:** "run critique twice, diff flagged set" — the consolidator is an LLM; two runs differ in wording regardless. → moved to a **manual red-team check in Phase 07**.

## Red-team angles
- **Boundary breach (CI-testable):** an edit injecting repeat-count into a lens prompt → litmus MUST go red. Verify by *temporarily* injecting → confirm red → revert.
- **Echo manufacture (MANUAL — Phase 07):** the consolidator is LLM; nothing deterministic proves the count didn't bleed into severity. Phase-07 manual review reads the consolidator prompt to confirm the count is *attached after* judgment, not fed into it.
- **Harm-floor at level 9:** louder scold must not cross the universal-harm floor; level 9 re-confirm gate intact.
- **Humanizer drop:** humanizer doesn't strip the louder block / occurrence IDs (preserve-set test).

## Success criteria
- A finding seen in ≥2 prior reports renders a louder, occurrence-listed scold at level ≥7.
- **Litmus (CI):** assembled lens prompts contain no repeat-count/occurrence data — test green; proven catchable via temporary-injection→red→revert.
- Deterministic lookup returns count + occurrence refs (data-feed test green).
- Humanizer keeps the scold + IDs intact; harm-floor respected.
- (Output-stability across runs is NOT asserted in CI — manual Phase-07 consolidator-prompt review instead.)

## Risk
- **Boundary creep** (someone later feeds count into lens) → litmus test guards it; document loudly.
- **Voice over-reach** at level 9 → existing re-confirm gate + harm-floor unchanged.

## Security
- No new data captured. Occurrence refs are internal scope/ts IDs already in `.memory/`.

## Next steps
- Mention in STANDARDIZE.md (Phase 6) as an HA-inspired pattern *kept on the safe side of the boundary* (HA's instinct-store crossed it; CM deliberately did not).
