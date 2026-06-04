# Workflow — Interview & Generate

End-to-end workflow the LLM follows for the **product / brd / prd / epic / story** flags (and the no-flag init flow). Phased, resumable, adaptive, bilingual.

## Detect State (no-flag entry)

1. Look for `<root>/docs/product/PRODUCT.md`.
2. If missing → propose **Init product** via AskUserQuestion. On confirm, run *Init flow* below.
3. If present → present the No-Flag Menu (see SKILL.md). Each menu choice maps to one of the flag flows below.

## Init Flow (no PRODUCT.md yet)

1. Ensure `docs/product/` exists (create if not).
2. Run the **Vision** interview (`references/interview-vision.md`) — V1 through V7.
3. After V1–V7, write:
   - `PRODUCT.md` via `generate_templates.py --type product` with the labels from the answers.
   - `vision.md` via `generate_templates.py --type vision` with the narrative.
4. Append a change-log entry via `generate_templates.py --type change_log_entry --keep-optional detail`.
5. Offer next step: "Create the BRD now, or stop here?"

## Detail-level preference (seed once, then consume every prose turn)

`detail_level` controls **how verbose the product-spec output is** — the vision narrative, PRD prose, story
descriptions, AC, and how many interview follow-ups to ask. It is a closed enum (`concise` / `standard` / `verbose`,
default `standard`) living in `preferences.yaml` (`scripts/preferences.py`). It is SEPARATE from `critique_detail_level`
(which sizes the `cleanmatic:product-spec-critique` report) — setting one never affects the other, so "verbose specs + concise
critiques" is a valid combo.

### Seed it (once, early)

On the **first** interview for a project (Init Flow), or whenever `preferences.yaml` has no `detail_level` set yet, ask
ONE `AskUserQuestion` near the start and persist the answer:

- **EN:** "How much detail should I put into the spec I write? **Concise** (short, to-the-point acceptance criteria and
  narrative, fewer follow-up questions), **Standard** (the balanced default), or **Verbose** (fuller narrative, more
  examples and rationale)?"
- **VI:** "Bạn muốn spec tôi viết chi tiết tới đâu? **Gọn** (tiêu chí nghiệm thu và mô tả ngắn gọn, đúng trọng tâm, hỏi
  ít hơn), **Tiêu chuẩn** (mức cân bằng mặc định), hay **Đầy đủ** (mô tả dày hơn, nhiều ví dụ và lý lẽ hơn)?"

Map: Concise/Gọn → `concise`, Standard/Tiêu chuẩn → `standard`, Verbose/Đầy đủ → `verbose`. Persist:

```bash
./.claude/skills/.venv/bin/python3 scripts/preferences.py --root <root>   # read current prefs first
# then write via the save() API (a thin caller), or hand-set in preferences.yaml
```

Per `GATE-NEVER-ASSUME`: this is a stylistic seed with a documented fallback, so if the PO skips it, default to
`standard` and say so. Never re-ask once set (read `.session.md` / `preferences.yaml`).

### Consume it (every prose-bearing turn)

Before composing prose — vision narrative, PRD body, story description, AC, or the size of an `AskUserQuestion` batch —
read `preferences.load(root)["detail_level"]` and size accordingly (LLM-side guidance, like `lang`, not a script knob):

| `detail_level` | product-spec prose |
|----------------|--------------------|
| `concise` | terse AC + narrative, minimal rationale, fewer interview follow-ups |
| `standard` (default) | the current balanced behaviour |
| `verbose` | fuller narrative, more worked examples, richer rationale |

This shapes prose LENGTH only; it never changes structure, frontmatter facts, or the DRY home of any fact.

## Engagement profile (interview rigor + action density)

Two closed-enum knobs in the same `preferences.yaml` (`scripts/preferences.py`) modulate **how the AI
engages** during the interview — distinct from `detail_level`'s output verbosity. Both default `standard`
and are read the same way (`preferences.load(root)[...]`).

- `interview_rigor` ∈ `light` / `standard` / `deep` (default `standard`) — how hard the interview
  **challenges claims and probes for gaps / edge cases / acceptance-criteria holes**.
- `action_prompting` ∈ `minimal` / `standard` / `proactive` (default `standard`) — the **density of
  suggested next-actions** the AI offers at turn boundaries.

**`interview_rigor` applies at ALL interview levels** — vision, BRD, PRD, epic, AND story — not just the
detailed story/epic flows.

### Orthogonality with `detail_level` (do not conflate)

`detail_level` sizes **verbosity (how long the prose is)**; `interview_rigor` sizes **rigor (how deep the
challenge is)**. They are independent axes: **"concise but deep"** is a valid, expressible combo —
`detail_level: concise` + `interview_rigor: deep` means *terse output, but hard probing* (short AC, yet the
AI still pushes back on every unproven claim and hunts edge cases). Never read `deep` rigor as "write more".

### Consume the knobs

| `interview_rigor` | interview behaviour (all levels) |
|-------------------|----------------------------------|
| `light` | take claims largely at face value; minimal challenge; surface only blocking gaps |
| `standard` (default) | the current balanced challenge + gap/edge/AC probing |
| `deep` | challenge each unproven claim; actively hunt edge cases, missing AC, and contradictions |

| `action_prompting` | next-action density |
|--------------------|---------------------|
| `minimal` | answer the ask; offer a next step only when one is clearly required |
| `standard` (default) | the current balanced "here's the natural next step" closing |
| `proactive` | surface a short menu of relevant next steps at each turn boundary |

These are LLM-side guidance (like `lang` / `detail_level`), not script knobs — they never change structure,
frontmatter facts, or the DRY home of any fact.

### Seed the engagement profile (once, with `detail_level`)

On the **first** interview (Init Flow), or whenever `preferences.yaml` has these keys unset, offer the
posture as **ONE question folded into the existing `detail_level` Init-Flow `AskUserQuestion` batch**
(detail_level + this = 2 questions, well under the 4-per-batch cap); ask it as a separate batch only if some
other seed pushes the batch over 4.

It is a single **posture** choice that sets BOTH knobs together — deliberately *not* two separate questions —
because at the very first turn the PO has not seen the interview yet (asking them to fine-tune "rigor" vs
"prompting" in the abstract is a decision they lack context to make), and in practice the two correlate (a PO
who wants hard challenge usually also wants proactive guidance). The neutral default keeps it skippable
(GATE-NEVER-ASSUME). The rarer split case (e.g. terse-but-rigorous) is handled by per-knob `--set` below, so
the init batch stays short rather than front-loading three preference questions.

- **EN:** "Two quick things about *how* I run the interview — separate from how long the spec text is
  (`detail_level`). **Balanced** *(default)*: I challenge claims and suggest next steps at a normal level.
  **Push-hard**: I rigorously challenge every claim and actively hunt edge cases / missing acceptance
  criteria (`interview_rigor: deep`), AND proactively offer a short menu of next steps at each turn
  (`action_prompting: proactive`). Which do you want? *(Want them split — e.g. concise output but rigorous
  probing? Tell me, or set each one later.)*"
- **VI:** "Hai điều nhanh về *cách* tôi chạy phỏng vấn — tách biệt với độ dài chữ của spec (`detail_level`).
  **Cân bằng** *(mặc định)*: tôi chất vấn và gợi ý bước kế ở mức bình thường. **Đào sâu**: tôi vặn kỹ từng
  khẳng định, chủ động truy ca biên / tiêu chí nghiệm thu còn thiếu (`interview_rigor: deep`), VÀ bày sẵn
  menu bước kế mỗi lượt (`action_prompting: proactive`). Bạn muốn kiểu nào? *(Muốn tách riêng — vd chữ ngắn
  gọn nhưng vẫn vặn kỹ? Cứ nói, hoặc chỉnh từng cái sau.)*"

Map: **Balanced / Cân bằng** → leave both at `standard` (skip the write); **Push-hard / Đào sâu** → persist
both via the Phase-1 write-CLI:

```bash
./.claude/skills/.venv/bin/python3 scripts/preferences.py --root <root> \
  --set interview_rigor=deep --set action_prompting=proactive   # load→merge→save, preserves other keys
```

For the split case, set either knob alone — e.g. concise-but-rigorous is `--set interview_rigor=deep` only;
quieter next-step prompts is `--set action_prompting=minimal` only.

Per `GATE-NEVER-ASSUME`: defaults are neutral `standard`, so if the PO skips the question, default to
`standard` and **say so** — never silently assume a strict posture. Never re-ask once set (read
`.session.md` / `preferences.yaml`).

## Phased Interview Engine

The interview is **phased** (vision → brd → prd → epic → story) and **resumable** via `docs/product/.session.md` (committed). Session schema in `frontmatter-and-id-spec.md`.

### Resume Rules

- On every invocation that triggers an interview, first read `.session.md`.
- If present and `phase != done`: ask "**Resume from saved state** (continue at `pending[0]`) or **Discard and restart**?"
- If `updated > 30 days ago` OR `answers` reference IDs no longer in the spec → mark as **stale**, default to "Discard" but still offer resume.

### Session Writes

- After every `AskUserQuestion` batch, append the answer to `.session.md.answers` and remove it from `pending`.
- On phase completion, set `phase` to the next stage; if all phases done, set `phase: done` and write the final artifacts.

## Adaptive Skipping

- Skip questions whose `target` is already filled in the live spec (e.g., persona cap interview if `PRODUCT.md.personas` is set).
- Skip optional questions (P7/P8/P9, E5, S5) unless the PO explicitly asks for them.
- Combine related questions into a single `AskUserQuestion` batch (e.g., size + persona for a story).

## 5-Why & MoSCoW Hooks

- After every PO answer, the LLM scans for vagueness triggers (`interview-frameworks.md → trigger phrases`). If found → run 5-Why up to 3 rounds, then propose a quantified rewrite.
- During the PRD interview's `P4` step, the MoSCoW gate is **mandatory**. If >60% of requirements end up as `must`, iterate the "delay by a month" test until at most ~60% remain MUST.

## Scope Challenge (always-on, once per PRD, BEFORE decomposition)

Before breaking a PRD into epics/stories, ask the PO **one coarse boundary question** and **lock the answer**. This sets the high-level intent for the whole feature-area so later additions are deliberate, not creep. It runs once per PRD — the first time that PRD is decomposed — and the lock is recorded so it is never re-asked.

This is the **coarse** boundary lock. It is NOT the per-requirement MoSCoW gate (that runs later, at `P4`, and assigns each requirement Must/Should/Could/Won't). Division of labour:

- **Scope Challenge** owns the *boundary*: how much of this feature-area are we building this round — the trimmed core, the whole thing, or just enough to test the idea? Answered once, locked.
- **MoSCoW gate** then *operationalizes* that boundary per requirement, and must stay **consistent** with it. The MUST set must not exceed the locked scope.

**Never re-ask "what's the MVP"** — the Scope Challenge owns the boundary; MoSCoW derives the per-requirement detail from it. Asking both would double-ask the PO (no double-ask).

### Ask (EN | VI)

- **EN:** "Before we break '{PRD title}' into pieces — how much of it are we building this round? **MVP** (the trimmed must-have core), **Full** (the complete feature as you picture it), or **Strip** (a bare slice just to test whether anyone wants it)?"
- **VI:** "Trước khi chia '{tên PRD}' thành các phần — đợt này ta làm tới đâu? **MVP** (phần lõi bắt buộc, tối giản), **Full** (toàn bộ tính năng như bạn hình dung), hay **Strip** (lát mỏng nhất để thử xem có ai cần không)?"

Present this as a 3-option `AskUserQuestion` (MVP / Full / Strip). Keep it terse — one question, one answer.

### Complexity-smell follow-up

If the PRD already looks heavy (the PO has named many sub-features, or the brain-dump for this area is large), add one sentence after the choice: *"This looks like a lot for one round — anything here you'd be comfortable pushing to a later round?"* Record any deferral; do not push the PO.

### Lock + record

- Record the choice on the PRD as `scope_intent: mvp | full | strip` (frontmatter is the source-of-truth). Once set, the Scope Challenge does **not** re-ask on later edits of that PRD.
- A PO who explicitly says "skip the scope question, just decompose" may bypass it — record `scope_intent` as unset and note the bypass in the session log; do not nag.

### Surface out-of-mode additions (never silently add)

After the lock, if the PO (or the brain-dump) adds something clearly **beyond** the locked intent — e.g. a gold-plated extra under a `strip` or `mvp` lock — do not silently fold it in. Surface it: *"You locked '{PRD}' as {scope_intent} this round, but '{addition}' looks like it goes past that. Add it anyway (and widen the lock), defer it to a later round, or drop it?"* The PO decides. The MoSCoW gate also flags when the MUST set exceeds the locked scope (consistency check), so the two gates reinforce — they never duplicate the question.

## Scout-First, Ask-Second

Before interrupting the PO with a question, **resolve it from the existing spec first** — the PO has often already answered it in a prior artifact, in `PRODUCT.md`, or in `.session.md`.

1. **Scout the live spec first.** For anything answerable from existing artifacts (a persona label, a core-value sentence, a parent ID, a prior MoSCoW call, a locked `scope_intent`), read the artifact and use the answer — **cite it by ID** so the PO sees where it came from ("PRODUCT.md lists the shopper + store-admin personas; reusing those").
2. **Ask the PO only when the spec is genuinely silent**, or when:
   - two **approved** artifacts conflict (surface both — never pick one silently; see the contradiction protocol in `validation-rules-spec.md`),
   - it is a **business judgement** the spec cannot answer (pricing, timing, scope boundary, a brand-new persona identity),
   - the answer would **reverse a PO-confirmed decision** (see no-silent-reversal in `workflow-update.md`).
3. Never ask the PO for something a quick read of the spec already answers. A wrong cited assumption is cheap for the PO to correct; an unnecessary question is friction.

This mirrors DRY (one authoritative home per fact) and the Script-vs-LLM split: structure comes from the artifacts; only genuine judgement goes to the PO.

## Validation Log (record every PO decision verbatim)

Every batch of PO answers that resolves an open question — a Scope Challenge lock, a MoSCoW call, a 5-Why quantified rewrite, an ambiguous-split decision — is recorded **verbatim** so the decision trail survives across sessions and the no-silent-reversal protections (`workflow-update.md`) have something to protect.

Append to a `## Validation Log` section in the session notes body of `docs/product/.session.md` (the `.session.md` frontmatter schema itself lives in `frontmatter-and-id-spec.md`; this is a prose section in its body). Schema:

```markdown
## Validation Log

### Session {N} — {YYYY-MM-DD}
**Trigger:** {what prompted this batch — e.g. "PRD-AUTH Scope Challenge", "MoSCoW gate on PRD-BILLING"}

1. **[{Category — Scope | Assumptions | Tradeoffs | Risks | Architecture}]** {full question text, verbatim — not a summary}
   - Options: {every option presented, verbatim} | Other
   - **Answer:** {the PO's choice, verbatim}
   - **Custom input:** {verbatim "Other" free-text if the PO typed one; omit if none}
   - **Rationale:** {one line — why this decision matters / what it locks}

#### Confirmed Decisions
- {decision}: {choice} — {brief why}
```

Recording rules:

- **Full question text** — the exact question, never a paraphrase.
- **All options** — every option presented, including the automatic "Other".
- **Verbatim custom input** — record any "Other" free-text exactly as the PO typed it.
- **Session numbering** — increment from the last `### Session N` in the log.
- **Rationale** — state what the decision locks (e.g. "locks PRD-AUTH at MVP this round").

The Validation Log is the verbatim source the no-silent-reversal protocol reads back to the PO before any regeneration — see `workflow-update.md → No Silent Reversal`.

## Bilingual Handling

- `.session.md.lang` carries the active language (`en` or `vi`).
- `AskUserQuestion` text + options use the active language; IDs and frontmatter keys stay English.
- VI ships best-effort. If the PO writes mixed EN/VI, accept both, normalize whitespace, but keep the answer in whatever language the PO used.

### PO-style read (behavioral memory 3D)

Before composing any prose for the PO — the vision narrative, a story description, or the text/options of an
`AskUserQuestion` — read the PO's voice store for the **active session lang** and let it shape the wording:

```bash
./.claude/skills/.venv/bin/python3 scripts/behavioral_memory.py --root <root> --lang <en|vi> --dump po-style
```

Use the returned `vocabulary` (the PO's own terms — prefer these over synonyms), `register` (tone), `recurring_asks`,
and `do`/`dont` to tune *how* the prose reads. It is lang-partitioned: a `vi` read never returns `en` voice. This shapes
PHRASING only — it never re-homes a structural fact (DRY). Full spec + the DRY guard (incl. the LLM-side persona-label
check) in `references/behavioral-memory.md`.

#### Per-prose-turn forcing-function (3D write)

On **every prose-bearing turn**, before moving on, run one deterministic consideration: **did the PO correct my wording
this turn?** (e.g. "call them shoppers, not customers", "drop the jargon", "always lead with a one-line summary"). If
yes, record it back so the same correction is not needed twice:

```bash
# explicit / PO-stated voice — the deterministic entry point
./.claude/skills/.venv/bin/python3 scripts/behavioral_memory.py --root <root> --lang <en|vi> --voice \
  [--vocabulary <a,b>] [--do <...>] [--dont <...>] [--recurring-asks <...>] [--register <s>]
```

`--voice` is a thin CLI over `record_po_style` (the LLM may also call `record_po_style` directly when it merely
*observes* the voice mid-composition) — same shape-validate, lang-key, union-merge, and DRY guard; no second writer
home. This is the portable Tier-0 forcing-function for 3D; it raises the consideration-rate, **not** the write-quality —
3D stays nudge-only because a wording correction is conversational, with no structural signal to key on (honest ceiling
+ the full enforcement model in `references/memory-enforcement.md`; 3D write-trigger detail in
`references/behavioral-memory.md`).

## Generation Flow — `--brd`, `--prd`, `--epic`, `--story`

For each flag:

1. Read the relevant interview bank for the phase.
2. Compose `AskUserQuestion` batches sized 3–5 questions; never overwhelm.
3. Once enough fields are filled, call:
   - `generate_templates.py --root <root> --type <type> --parent <parent_id> --slug <SLUG> --values <json> --keep-optional <list> --lang <lang> --write`
4. Inspect the script's response (`id`, `path`, `written`). Confirm to PO that the file was created.
5. Append a change-log entry (`change_log_entry`, action = `created` / `refined`).
6. Update `.session.md` (mark phase complete or proceed to the next artifact).

## Multi-PRD Targeting (`--prd <feature>`)

- If `--prd` is given an explicit slug → use it.
- Else: list existing PRDs (from `spec_graph.py`) and present an `AskUserQuestion` menu: "Refine which PRD, or create a new one (give a SLUG)?"

## Multi-Story / Multi-Epic Loops

After writing a story, ask:

- "Another story under {epic_id}?"
- "Move to the next epic?"
- "Stop here?"

Loop with a clear termination question — never go more than ~6 stories without offering an explicit stop.

## Closing the Loop

When the PO ends the session:

1. Save `.session.md` with `phase: done` and the last `updated` timestamp.
2. **End-of-interview validate nudge (forcing-function).** If the session changed N items since the spec was last
   validated, nudge before closing: *"you changed N items since your last `--validate` — run it now to re-gate them?"*
   This is the portable Tier-0 reminder that pairs with the per-turn 3D forcing-function above; the same drift is what
   `--status` surfaces read-only later (`workflow-status.md`), and `--validate` is where the required **Memory pass**
   records any unrecorded ruling/slip (`workflow-validate.md`; full model in `references/memory-enforcement.md`). It is
   a nudge, never a block — the PO may decline.
3. **Engagement-knob forcing-function (OPTIONAL — only when live evidence exists).** If THIS session
   produced real conversational evidence about engagement fit — e.g. goals omitted a metric ×N times, or
   the PO repeatedly waved off deep probing as noise, or kept asking "what's next?" — fold ONE tighten-or-
   relax proposal into the SAME close-out `AskUserQuestion` batch above (do **not** raise a separate
   interrupt). Ask once whether to adjust a knob, **bidirectionally**: propose *raising* `interview_rigor`
   to `deep` (or `action_prompting` to `proactive`) when the PO wanted more push, OR *lowering* it to
   `light` / `minimal` when they found it noisy. On an explicit PO confirm, persist via the Phase-1
   write-CLI (load→merge→save, preserves every other key):

   ```bash
   ./.claude/skills/.venv/bin/python3 scripts/preferences.py --root <root> --set interview_rigor=light
   ```

   **No auto-write.** The write happens ONLY after the PO confirms in that batch — markdown cannot
   *enforce* the confirm gate, but there is no auto path to abuse: the only writers are `--set` (PO-typed)
   and this forcing-function (PO-confirmed). Honesty caveat (consistent with `memory-enforcement.md`): this
   raises the *consideration rate* of an engagement adjustment, it does not guarantee capture — "reduced
   recurrence", never "the store fills itself". Skip the item entirely when no live evidence exists.
4. Offer a quick `--validate` and `--viz tree` to summarize what was built.

## Examples (snippets the LLM emits)

> "I see PRODUCT.md exists. Want to (1) refine BRD, (2) add a new PRD, (3) add stories under an existing epic, (4) validate, (5) update, (6) visualize, (7) approve, (8) summary?"

> "Sounds like 'easy onboarding' — what does easy look like specifically? What does the user see or do in the first 60 seconds?" *(5-Why round 1)*

> "Out of 12 candidate requirements you've named, you've marked 10 as MUST. If any one of those delays launch by a month — is it still MUST?" *(MoSCoW gate)*
