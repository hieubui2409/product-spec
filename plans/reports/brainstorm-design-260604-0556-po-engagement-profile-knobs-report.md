# Brainstorm Design — PO Engagement Profile (learned-but-confirmed knobs) for product-spec*

- **Date:** 2026-06-04
- **Scope:** `cleanmatic:product-spec` + `cleanmatic:product-spec-critique`
- **Status:** design agreed (PO-confirmed), ready for `/ck:plan --tdd --redteam`
- **Decision posture:** v1 minimal, NO breaking changes, backward-compatible with current `preferences.yaml`.

---

## 1. Problem statement

PO wants product-spec* to adapt AI engagement to the PO's working style / experience / behavior:
- lazy PO → ask more thoroughly, suggest more next-actions
- argumentative / experienced PO → harder pushback, deeper edge-probing, more concise
- inexperienced PO → more explanation
- PO's recurring omissions / bad habits → AI compensates

Asked: which mechanism (hook / passive skill) captures this into a shared product-spec* memory applied across all workflows.

## 2. Key finding — ~half already exists

| PO example | Already covered? |
|---|---|
| inexperienced → detailed | `detail_level: verbose` (exists) |
| experienced → concise | `detail_level: concise` (exists) |
| argumentative → harsher (in **critique**) | `critique_level: 1..9` (exists) |
| lazy → more action suggestions | **missing** |
| deeper edge / pushback in **interview** (not critique) | **missing** |
| recurring mistakes → compensate | **missing** (3E tracks *skill* slips, not PO) |

Existing memory layer (per-project `docs/product/.memory/`, shared by both skills):
- `preferences.yaml` — PO-set closed-enum knobs (read by interview flow + `critique_scan`)
- `po-style.yaml` (3D) — PO voice/wording only
- `self-corrections.json` (3E) — the SKILL's own slips
- Passive-capture infra already present: `memory_gap.py` (deterministic signals) → Tier-0 forcing-functions → Tier-1 opt-in Stop hook → Tier-2 `--reflect` harvest (propose → PO-confirm → write).

**Honest ceiling (per repo's own `memory-enforcement.md`):** soft traits (lazy/argumentative) have NO deterministic signal → pure LLM judgment → must be PO-confirmed. "AI learning" here ≈ *preferences.yaml that proposes itself*, NOT a psychology engine. Do not over-sell.

## 3. Decisions (PO-confirmed this session)

1. **Build v1 minimal.** Defer global/multi-PO/auto-write/weakness-labels.
2. **Store = existing `preferences.yaml`** (NOT a new 3F file). Rationale: every knob is PO-confirmed before write → genuine preference, same privacy posture (committed) + same closed-enum nature as `detail_level`. Does not violate the 3D/3E split rationale (those split on user-facing-voice vs internal-conduct + privacy; these are prefs-like).
3. **Capture = both** explicit flag + hybrid infer→confirm harvest, **bidirectional** (tighten AND relax), always PO-confirmed.
4. **Privacy = neutral engagement-knobs only.** No personal labels ("lazy"); store behavioral consequence ("needs proactive action prompts", "always re-check metric on goals"). Committed.
5. **Default posture = strict-first** (`rigor=deep`, `action=proactive`), harvest relaxes over time. A default is a quality-first starting posture, NOT a judgment about the PO → does not trip GATE-NEVER-ASSUME.

## 4. Knob set (v1)

| Key | Enum | Default | Applies to |
|---|---|---|---|
| `interview_rigor` | `light` / `standard` / `deep` | **deep** | product-spec (interview) |
| `action_prompting` | `minimal` / `standard` / `proactive` | **proactive** | both skills |
| `standing_reminders` | `list[str]` | **`[]`** | both skills |
| `detail_level` *(existing)* | `concise` / `standard` / `verbose` | standard | product-spec — **referenced, never copied** |

`interview_rigor` MERGES the originally-proposed `interview_pushback` (challenge PO claims) + `edge_probing` (surface missing cases/AC) into one knob.

## 5. Overlap / ambiguity resolutions (the critical analysis)

| # | Collision | Resolution |
|---|---|---|
| A | `detail_level` ⟷ new depth knobs | Orthogonal axes: `detail_level` = prose/explanation **verbosity (length)**; `interview_rigor` = **risk-hunting rigor (depth)**. A PO can be "concise but deep". Document orthogonality. |
| B | `interview_rigor` ⟷ `critique_level` | Independent. Interview pushback = *constructive* (light/standard/deep, helps build). Critique = *adversarial/roast* (1..9). New knob never reaches roast register. No derivation between them. |
| C | `interview_pushback` ⟷ `edge_probing` | **Merged** into `interview_rigor` (edge-probing ⊂ challenge). KISS; removes the fuzzy "which one do I set" ambiguity. |
| D | `standing_reminders` ⟷ existing `dismissed_reminders` | Renamed new key to `standing_reminders` (avoid the name+opposite-semantics clash). Precedence: if a standing reminder is dismissed, `dismissed_reminders` WINS (PO can always silence). |

## 6. Non-breaking guarantee

- All-additive keys in `preferences.py` `DEFAULTS` + `ENUMS` (+ `standing_reminders` as a list, precedent: `dismissed_reminders`).
- `load()` already default-fills missing keys; `save()` drops unknown keys → old `preferences.yaml` files load unchanged. Covered by existing `test_preferences.py` degrade tests.
- Merging two **not-yet-shipped** keys into `interview_rigor` from day one = zero migration. (The breaking scenario would be ship-2-then-merge → `save()` silently drops the 2 → we explicitly avoid it.)

## 7. Capture mechanism (reuses existing infra, no new mechanism)

- **Flag (deterministic):** add a write-CLI to `preferences.py`, e.g. `preferences.py --root <r> --set interview_rigor=standard` → routes through `save()` (enum-validated, fenced). Additive to the current read-only `main()`.
- **Hybrid harvest (LLM, confirmed):**
  - Per-session forcing-function in `workflow-interview.md`: when AI observes a repeated pattern (e.g. goals omit a metric ×N; PO breezes past deep probing as noise), it asks ONCE → on PO yes, writes the knob/reminder. Bidirectional (may propose lowering `rigor`).
  - New `--reflect` harvest category `engagement-profile` (in `reflect_scan.py` + `workflow-reflect.md`): retroactively proposes knob changes from session/`.memory` state → PO confirm → write. Reuses `memory_gap` dedup so it never re-proposes an already-set value.
- All writes PO-confirmed → consistent with GATE-NEVER-ASSUME.

## 8. Injection points (read `preferences.load()` at trigger)

- **product-spec interview** (`workflow-interview.md`): at question-generation —
  - `interview_rigor` → depth of claim-challenge + gap/edge/AC probing
  - `action_prompting` → density of suggested next-actions
  - `standing_reminders` → injected as always-checks
- **product-spec prose**: `detail_level` (already wired) + `standing_reminders`.
- **product-spec-critique** (`critique_scan` / `workflow-critique.md`): **only** `action_prompting` (fix-suggestion density) + `standing_reminders`. **NOT** `interview_rigor` (critique harshness owned by `critique_level` — avoid ladder collision).

## 9. Deferred (YAGNI) + escape hatches

- **Global cross-project / multi-PO key:** when needed, split engagement knobs into a dedicated `po-profile.yaml` (3F) outside the flat prefs file (carries provenance: inferred-vs-PO-set, per-PO partition).
- **Split `interview_rigor` back into 2:** add optional `interview_pushback` / `edge_probing` that DEFAULT to `interview_rigor`'s value → non-breaking, no migration. Use only if the "deep-edges / light-pushback" power-user split materializes.
- **Auto-write without confirm, weakness/habit labels:** intentionally excluded (GATE + privacy).

## 10. Success criteria

- New keys load/save with enum validation; missing-key degrade preserved (extend `test_preferences.py`).
- Old `preferences.yaml` (no new keys) → unchanged resolved behavior.
- Interview flow visibly varies challenge-depth + action density by `interview_rigor` / `action_prompting`.
- `standing_reminders` injected in both skills; `dismissed_reminders` overrides it.
- critique receives only action+reminders; `critique_level` untouched.
- Harvest proposes a knob change and writes only after PO confirm (both directions).

## 11. Touchpoints (files)

- `.claude/skills/product-spec/scripts/preferences.py` (+ `tests/test_preferences.py`)
- `.claude/skills/product-spec/references/workflow-interview.md` (read + forcing-function)
- `.claude/skills/product-spec/references/workflow-reflect.md` + `scripts/reflect_scan.py` (harvest category)
- `.claude/skills/product-spec-critique/scripts/critique_scan.py` + `references/workflow-critique.md` (action+reminders read)
- Docs: `CLAUDE.md` preference table, `behavioral-memory.md` cross-ref, `SKILL.md` flag list.

## 12. Unresolved questions

1. `standing_reminders` — free-form strings, or a small closed vocabulary of check-types? (free-form = flexible but un-validatable; v1 leans free-form list like `dismissed_reminders`.)
2. Harvest forcing-function cadence — every prose turn (noisy) vs end-of-session only? (lean end-of-session + `--reflect`, mirror the 3D honesty caveat.)
3. Does `action_prompting=proactive` in critique risk turning report into a fix-list (scope creep vs critique's report-only contract)? Confirm bound before wiring.
