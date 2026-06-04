# Red Team — Consolidated Adjudication (PO Engagement Profile knobs)

- **Date:** 2026-06-04
- **Reviewers:** Assumption Destroyer (R1, 9) · Failure Mode Analyst (R2, 8) · Security/Privacy Adversary (R3, 7)
- **Raw:** 24 findings → **deduped: 19** → all pass evidence filter (every finding cited `file:line`).
- **Severity (deduped):** 4 Critical · 7 High · 8 Medium.

## Dedup map
- **Data-loss (save not load-merge):** R1-F9 = R2-F1 (Critical ×2)
- **`len(DEFAULTS)==13` test breaks:** R1-F1 = R2-F2 = R3-F5 (×3)
- **`dismissed_reminders` no consumer:** R1-F3 = R2-F5
- **YAML bool coercion mangles list items:** R2-F7 = R3-F6

## Adjudication

| # | Finding | Sev | Disp | Where |
|---|---------|-----|------|-------|
| A | `save()` is blind overwrite (not load-merge) → `--set` one key **clobbers entire `preferences.yaml`** (data loss; downgrades committed `critique_level`/dialect). `preferences.py:195-215` | Critical | **Accept** | P1 |
| B | Existing `test_defaults_has_exactly_thirteen_keys` (`assert len==13`) breaks on +3 keys; "no regression" self-contradicts. `test_preferences.py:41-45` | Critical | **Accept** | P1 |
| O | `standing_reminders` free-text **committed to git** echoes verbatim PO wording → privacy leak; violates posture. `behavioral-memory.md:177-183` | Critical | **Accept** | P1/schema |
| P | "PO-confirmed before write" is **doc-only, no script gate**; `--set` writes unconfirmed. `preferences.py:190-215` | Critical | **Accept (modified)** | P1/P4 |
| C | Phase 3 targets wrong file — bundle is built in `critique_bundle.py::emit_bundle`, not `critique_scan.py`. `critique_bundle.py:78-129` | High | **Accept** | P3 |
| F | `_existing_memory_index` returns `Dict[str,List[str]]` + `main()` fallback hardcodes 4 keys → adding `preference_knobs` breaks shape/degrade path. `reflect_scan.py:191,289-294` | High | **Accept** | P4 |
| G | `--reflect engagement-profile` has **no anchor signal** (reflect emits git-only) → manufactured candidate, violates "never manufacture". `reflect_scan.py:230-268`, `memory-harvester.md:78-88` | High | **Accept** | P4 |
| H | Dedup on **resolved** (default-filled) knob values → strict-first default looks "already set" → harvester **never proposes relaxing** → kills decision-5. `preferences.py:152-157` | High | **Accept** | P4 |
| Q | Default `rigor=deep`/`action=proactive` for unknown PO = inferred-trait posture; trips GATE-NEVER-ASSUME; breaks `detail_level=standard` neutral-default convention. `preferences.py:94` | High | **ESCALATE** (user decision) | design/P1 |
| R | `standing_reminders` free-text injected as "always-checks" into both skills = **prompt-injection / instruction-override** vector. P2/P3 | High | **Accept** (via O fix) | P2/P3 |
| E | Design §7 false: reflect dedup does **not** use `memory_gap` (uses `decision_register`+`behavioral_memory`). `reflect_scan.py:191-223` | High | **Accept** | design/P4 |
| D | `dismissed_reminders` is **never read for suppression** anywhere → Phase-2 precedence is phantom (doc-only, no consumer). grep `references/` | Medium | **Accept** | P2 |
| I | Critique provenance fast-path hashes **only spec body** → knob change on unchanged spec **reuses stale report** → knob silently inert. `critique_common.py:106-111`, `critique_provenance.py:150-155` | Medium | **Accept** | P3 |
| J | `--set standing_reminders=foo` → `save()` raises (list key) foot-gun; no steer to `--add-reminder`. `preferences.py:203-206` | Medium | **Accept** | P1 |
| K | Phase-2 cites wrong section ("§Bilingual/prose ~line 52"); `detail_level` read lives in "Detail-level preference" `workflow-interview.md:25-61`. | Medium | **Accept** | P2 |
| L | Phase-4 adds a **3rd** end-of-session nudge w/o sequencing → noise the design tried to avoid. `workflow-interview.md:236-242` | Medium | **Accept** | P4 |
| M | List branch `[str(v) for v in value]` turns YAML `[no]`→`["False"]`; proposed test checks wrong condition. `preferences.py:181-184` | Medium | **Accept** | P1 |
| N | Phase-4 multi-write session erases prior knobs unless A fixed (transitive). | Medium | **Accept** (subsumed by A) | P4 |
| S | Phase-3 ships design-unresolved Q3 (`proactive` vs report-only) as prose-only bound. design §12 Q3 | Medium | **Accept** | P3 |

**Rejected:** none (all evidence-backed).

## Corrections to the design doc (verified by R3, prevent over-correction)
- **claude-pack does NOT ship `preferences.yaml`** (`selection.py:30-36` walks `.claude/skills/...` only). The design's "pack leakage" worry is misdirected — the real exposure is **git commit** (finding O), not pack. Fix design framing.
- **`save()` IS path-fenced** (`preferences.py:210` → `fs_guard.py:39-61`). The "fenced" claim is accurate for path containment; the fence does NOT validate value *content* (that is O/R/M).

## How the accepted findings reshape the plan (themes)
1. **Phase 1 hardening:** `--set` must `load()→merge→save()` (A); update count test + DEFAULTS/ENUMS symmetry (B); reject `--set` for list keys → `--add-reminder` (J); bool→token guard for list items + round-trip test (M).
2. **Phase 3 retarget + scope:** edit `critique_bundle.py::emit_bundle` not `critique_scan.py` (C); fold knob values into provenance hash OR document fresh-only (I); **clamp critique to `action_prompting≤standard`** so `proactive` never reaches report-only (S).
3. **Phase 2 honesty:** reminder injection + dismissed-suppression is **net-new** (build read+filter), not "document existing precedence" (D); fix section ref (K).
4. **Phase 4 descope (KISS):** the `--reflect engagement-profile` harvest is **unfounded** (no signal G, false mechanism E, shape break F, dedup self-defeat H). **Recommend cutting it**; keep capture = explicit `--set` flag (PO typed = consent) + **end-of-session interview forcing-function** (live AskUserQuestion confirm = the real evidence) piggybacked on the existing Closing-the-Loop sequence (L). Dedup, if any, on **explicitly-set** raw values only (H).
5. **Privacy/injection (O,R,P):** make `standing_reminders` a **closed token vocab** (skill-authored phrasings) → no PO free-text committed, no injection surface, and "PO-confirmed" becomes: PO picks a token via AskUserQuestion → `--add-reminder <token>`. Alternative: keep free-text but ship the `.memory/` gitignore toggle NOW + inject as quoted data.

## Escalations needing PO ruling
- **Q (default posture)** — conflicts with the PO's earlier explicit choice "deep/proactive". Surface, do not silently flip.
- **standing_reminders shape** — closed vocab vs free-text+toggle vs drop.
- **Phase 4** — cut `--reflect` harvest vs build a real signal.

## Unresolved questions
1. Is `docs/product/.memory/` meant to be committed in consuming projects, or is the `behavioral-memory.md:180` gitignore toggle a prerequisite this plan must ship? (gates O/R severity)
2. Should harvest share the `--set` CLI or get a distinct staged-confirm path? (P)
