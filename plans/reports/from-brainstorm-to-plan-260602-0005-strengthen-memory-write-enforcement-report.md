# Brainstorm — Strengthen reminder / memory-write reliability (product-spec)

**Date:** 2026-06-02 · **Branch:** feat/product-spec-guardrails-and-memory-layer
**Mode requested next:** `/ck:plan --hard --tdd` — construct phases suitable for **ultracode (multi-agent Workflow)
execution**: file-ownership matrix (each file = one owning phase) + dependency DAG + execution waves (parallel within a
wave), with **red-team + validate** gates after the plan. Tier-0 → Tier-1 → Tier-2 ordering.
**Status:** design AGREED, all unresolved RESOLVED (§8), packaging RESOLVED (§9). Ready to plan.

---

## 1. Problem statement

product-spec's memory layer (decision register, judgment cache, 3D PO-style, 3E self-corrections) is **entirely
LLM-discretionary**: a write only happens if the LLM remembers to run a writer command/function at a workflow hook
point. The references themselves admit it is *soft* ("reduced recurrence, not a hard invariant", "the store does not
fill itself"; `check_fence.py` is advisory, never blocks). Risk: stores stay empty → memory provides little value
(no read-back signal because nothing was written).

**Goal:** make the *trigger* more reliable (deterministic where possible) WITHOUT a false hard-guarantee.

**Hard constraint (the irreducible tension):** WHAT to write needs judgment → a script can never guarantee a *correct*
write. WHEN to consider writing (the trigger) CAN be made deterministic. So: strengthen the trigger, keep the write as
LLM judgment, and never over-claim enforcement.

**Locked-decision reversal (surfaced, user-approved):** the original plan locked "soft fence F1+F3+F2, **NO hook**".
This design reopens that to allow an **opt-in** Claude Code hook. Documented as a deliberate reversal, not silent.

---

## 2. Evaluated approaches

| # | Approach | Mechanism | Deterministic trigger | Covers 3D? | Script-vs-LLM | Reverses no-hook | Effort |
|---|----------|-----------|-----------------------|------------|----------------|------------------|--------|
| A | Soft reminder++ | end-of-flow checklist in references + CLAUDE.md always-on line | ❌ | ✅ (soft) | ✅ | ❌ | very low |
| B | Detect-then-nudge | script detectors emit `memory_gap` findings; `--status` surfaces | ✅ | ❌ | ✅ | ❌ | medium |
| C | Hook enforcement | `Stop` hook reads transcript, blocks to force a write | ✅ enforce | ❌ | ⚠️ (if it parses prose) | ✅ | high |
| D | Forcing-function | `--validate` report MUST carry a "Memory pass" section (even if "none") | ✅ (consideration) | ✅ | ✅ | ❌ | low-medium |

Key finding: **only D covers 3D** (PO voice corrections are conversational, no structural signal). **C/B cover only the
structurally-detectable subset** (fence breach, validate-without-write, approved-body-changed-without-DEC). A real
fence-breach is the only signal worth a hard block.

---

## 3. Recommended solution — tiered Hybrid

### Tier 0 — portable core (no hook, ships to every PO project, no locked-decision reversal)

1. **`memory_gap.py`** — single deterministic detector module (DRY home). Emits structured signals:
   - `fence_breach` (file written outside `docs/product/` — reuses `check_fence` logic)
   - `validate_no_marker` (validate ran but `.memory/last_validated.json` unchanged)
   - `approved_changed_no_dec` (an `approved` artifact's `body_hash` changed but no new `DEC-<n>`)
   - `judged_not_stored` (stale set > 0 but `judgments.json` did not grow) — kept (belt-and-suspenders for the cache)
   Imported by `status.py`, the validate forcing-function, and the Tier-1 hook → one home, no drift.
2. **Validate forcing-function** — `--validate` report MUST include a **"Memory pass"** section: contradiction→DEC?
   slip→3E? + the `memory_gap` candidate list. Required section, even if the answer is "none".
3. **judgment-cache batch-write** — collapse N per-verdict `--store` calls into **one** structured-output→one script
   write at the end of Step 2 (removes the per-verdict "forgetting surface"). Stays validate-gated.
4. **Interview forcing-function** — at each prose-generating interview turn: consider `record_po_style` (3D). At
   interview end: nudge "you changed N items since last validate — run `--validate`?".
5. **`--status` `unrecorded_signals`** — surfaces `memory_gap` output + drift-since-validate (read-only).
6. **CLAUDE.md always-on line** — "Memory hygiene: after resolving a contradiction / a PO wording-correction / a caught
   slip, persist it."

### Tier 1 — opt-in `Stop` hook (recommend-and-ask, never silent-force, degrades cleanly)

7. **`Stop` hook** (`scripts/memory_gap_hook.*`): no-op guard → run `memory_gap.py --json` → apply **per-signal
   persistence policy**:

   | Signal | Policy | Rationale |
   |--------|--------|-----------|
   | `fence_breach` | **persist** (re-block while gap remains, capped at 8) | a write outside `docs/product/` violates the contract; must be fixed |
   | `validate_no_marker` | **nudge-once** | may be a legit incomplete validate |
   | `approved_changed_no_dec` | **nudge-once** | high false-positive (approved artifact can change legitimately) |

   **block-once mechanic (resolves false-positives):** hook returns `{"ok":false,"reason":"re-judge X; if a DEC/entry
   is warranted, write it; if not, say why and stop"}`. The LLM continues, re-judges ONCE, then on the next stop attempt
   the hook sees `stop_hook_active: true` and **exits 0** → LLM proceeds whether or not it wrote. A false positive costs
   exactly one re-judgment, never a loop. `fence_breach` deliberately ignores `stop_hook_active` (persist) up to the
   8-block cap.
8. **No-op guard (hook fires globally per project):** a `PostToolUse` on `Write|Edit` sets a per-session
   "touched docs/product" flag; the `Stop` hook runs the detector only if the flag is set AND `docs/product/` exists →
   otherwise exits 0 immediately (cheap on non-product-spec turns).
9. **Recommend-and-ask install:** on first run (`SessionStart` notice or skill self-check), if the hook is not
   registered → recommend `install.sh --memory-hook` ONCE; record an optout/prompted marker so it never nags again.
10. **Install merge:** `install.sh --memory-hook` does an **idempotent JSON merge** into `.claude/settings.local.json`
    (gitignored, per-user) by default; shared `.claude/settings.json` only on explicit opt-in. Decline → graceful
    degrade to Tier-0 (skill fully functional, one-line "enforcement off" notice).

### Tier 2 — `--reflect` retroactive harvest (opt-in command; added per follow-up brainstorm)

Complement to the inline layer: forcing-functions catch *at-the-moment*; `--reflect` catches what was missed, from
**structurally-readable sources only**. Home = product-spec `docs/product/.memory/` (NOT Claude Code's `MEMORY.md`).

11. **`reflect_scan.py`** (script half, deterministic) — emit anchors only: commits touching `docs/product/` since last
    reflect/validate, files changed, revert/fix commit markers, existing-memory index (dedup vs `.memory/` +
    `decisions.md`). No judgment. Reuses `memory_gap` dedup where possible.
12. **Context-isolated harvester sub-agent** (LLM half) — a shipped agent def `agents/memory-harvester.md`
    (`model: opus`, `tools: Glob, Grep, Read, Bash` = read-only; NO Write/Edit/Task → cannot write memory at the tool
    layer). Reads anchors + diffs → **candidate report** (proposed DECs / self-corrections / po-style observations).
    **Read-only: it NEVER writes memory** (write path stays single-homed in main agent + scripts). Legit
    context-isolation win (heavy read → compact report). Cannot see the live conversation (forcing-function's job).
13. **Main agent** reads the report → **interviews the PO** per candidate (accept / edit / reject) → persists accepted
    ones via existing writers (`decision_register --append`, `behavioral_memory.record_*`, through `fs_guard`).
    **"Silently add" = no extra ceremony AFTER the PO approved in the interview** — never an unconfirmed decision/voice
    write (`GATE-NEVER-ASSUME`).

Boundaries: opt-in explicit command (never automatic); harvests git+file sources only; candidates are proposals
(PO confirms). Sub-agent token cost is paid **only when the PO chooses to run `--reflect`** — acceptable; auto-spawn is
rejected.

### Agent / hook architecture decisions (follow-up brainstorm — evidence-grounded)

- **claude-pack: NO sub-agent, NO hook** (for claude-pack ITSELF). Non-interactive work (manifest / safety / tarball)
  is already pure scripts — nothing LLM-heavy to isolate; build is an explicit one-shot CLI + tag-CI, never "forgotten
  mid-flow". Both = over-engineering. **BUT claude-pack is NOT zero-change** — it must bundle the new harvester agent:
  manifest `agents:` += `memory-harvester.md` + a 1-line `INSTALL.md.template` note for the opt-in `--memory-hook` step
  (see §9 Packaging).
- **product-spec sub-agent: ONLY the `--reflect` harvester.** Core flows (`--validate`/`--auto`) need whole-graph +
  cross-node context (semantic-dup pairwise, contradiction vs decisions) → splitting loses context + judgment-cache
  already makes re-validate cheap. Sub-agent's only clear win = the heavy read-once harvest (Tier 2).
- **Evidence:** `product-spec/agents/` is empty (`.gitkeep`); neither skill spawns sub-agents at runtime today
  (grep = 0); a sub-agent cannot see the main agent's conversation (orchestration-protocol.md) → the
  "scan-conversation-via-sub-agent" idea is infeasible, so conversational capture stays with the main-agent
  forcing-functions and only git/file harvest is delegated.
- **PO cost caveat:** product-spec serves non-technical POs; a sub-agent spawn costs tokens invisibly to them →
  acceptable ONLY because `--reflect` is opt-in/explicit.

### Per-store outcome (honest scope)

| Store | Strongest lever | Hook? |
|-------|-----------------|-------|
| decision register | Tier-0 forcing + hook `nudge-once` (`approved_changed_no_dec`) | yes (nudge-once) |
| 3E self-corrections | Tier-0 forcing + hook `persist` (`fence_breach`) | yes (persist) |
| judgment-cache | **batch structured-write** (N→1); NO chat-time write, NO hook | no |
| 3D PO-style | forcing-function each prose-turn (+ optional `--voice` flag) | **impossible** (judgment limit) |

### "PO never invokes --validate" — nudge, not enforce
Routed to `--status` + interview-end "run `--validate`?" nudge. Cannot/should-not force the PO to validate (hostile).

### judgment-cache chat-time write — explicitly NOT enforced
Content changed in chat is **self-healing** (body_hash/dep_hash key → miss → re-judge next validate; stale entry GC'd —
cache is optimization, never authoritative). A PO dismissing a flag in chat is a **ruling → Decision Register**
(`--decision`/`po_ruling_ref`), not a cache write. Seeding the cache from chat would corrupt the "never authoritative"
invariant = YAGNI + risk.

---

## 4. Honest ceiling (do NOT over-claim)

- decision + 3E + fence-breach: materially stronger (deterministic consideration + hook nudge/block).
- 3D: nudge-only (irreducibly conversational); accepted.
- judgment-cache: batch-write removes the forgetting surface; no enforcement needed.
- **Enforcement raises the *consideration rate*, never the *write quality*** — the LLM can still rubber-stamp "none" or
  write a junk entry. There is no way around the judgment limit.

---

## 5. Touching files (for the plan)

**New:**
- `scripts/memory_gap.py` — deterministic detector (single home).
- `scripts/memory_gap_hook.py` — `Stop` hook (Python/venv): guard → detect → per-signal policy → block/exit.
- `scripts/reflect_scan.py` — Tier-2 `--reflect` anchors: git-since-last + revert/fix markers + existing-memory dedup index (git-degrade safe).
- `references/workflow-reflect.md` — Tier-2 flow: spawn harvester agent → candidate report → PO interview → persist.
- `.claude/agents/memory-harvester.md` — harvester agent def (TOP-LEVEL; `model: opus`, read-only `tools: Glob, Grep, Read, Bash`); bundled via manifest `agents:`.
- `scripts/tests/test_memory_gap.py`, `test_reflect_scan.py` (+ hook test, + batch-write test, + `--voice` test).
- *(maybe)* `references/memory-enforcement.md` — DRY home for the forcing-function + hook spec.

**Modified:**
- `scripts/status.py` — add `unrecorded_signals` (import `memory_gap`) + soft `--reflect` suggestion when drift high.
- `scripts/judgment_cache.py` — batch store path (one write for N verdicts).
- `scripts/behavioral_memory.py` — add `--voice` CLI write path (3D explicit PO entry, via `record_po_style`).
- `references/workflow-validate.md` — "Memory pass" forcing-function + batch-store wiring + `memory_gap` candidates.
- `references/workflow-interview.md` — 3D per-prose-turn forcing-function + interview-end validate nudge.
- `references/workflow-status.md` — document `unrecorded_signals`.
- `references/behavioral-memory.md` — update 3D/3E write-trigger to reference forcing-function + hook.
- `CLAUDE.md` — always-on memory-hygiene line + `memory_gap.py` in scripts list + document the opt-in hook + revise any
  "no runtime hook" claim (reversal) + the no-silent-force-register consent rule.
- `SKILL.md` — install note for `--memory-hook`; optional `--voice` flag row if adopted.
- `install.sh` / `install.ps1` (product-spec) — `--memory-hook` idempotent settings.local.json merge.
- `.claude/pack.manifest.yaml` (claude-pack) — `agents:` += `memory-harvester.md` (bundle the harvester); version bump on release.
- `.claude/skills/claude-pack/assets/templates/INSTALL.md.template` — 1-line note for the opt-in `--memory-hook` step.
  *(install.sh.template / install.ps1.template need NO logic change — per-skill hooks + `.claude/agents/` files are handled generically.)*

---

## 6. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Reverses locked "no hook" decision; hook fires globally | hook is **opt-in**; cheap no-op guard; documented reversal |
| Hook can't enforce 3D / chat-formed verdicts | accepted (judgment limit); 3D stays forcing-function only |
| Auto-modifying settings.json = trust violation | **recommend-and-ask only**; settings.local.json default; never silent-force / never "required" |
| `Stop` hook reads transcript every turn → perf | `PostToolUse` touched-flag guard; exit 0 fast when no `docs/product/` |
| Block loop | `stop_hook_active` honored for nudge-once signals; 8-block cap for persist |
| Exotic hook-event names unverified | use only `SessionStart`/`Stop`/`PostToolUse` (canonical); verify against installed CC version in phase 1 |
| Enforcement read as a guarantee | docs state "consideration-rate, not write-quality" explicitly |

---

## 7. Success metrics / validation

- Eval scenarios: a surfaced contradiction → `DEC-<n>` recorded; a `fence_breach` → 3E recorded; a re-validate of an
  unchanged spec → 0 re-judges (batch-write intact).
- Existing 477 tests pass; new tests for `memory_gap` (each signal), batch-write, hook policy (block-once vs persist,
  `stop_hook_active` escape).
- Hook no-op cost negligible on a non-product-spec turn (guard short-circuits).
- Decline path verified: no hook → Tier-0 fully functional, one-line notice, no nag.

---

## 8. Resolved decisions (from interview — authoritative for the plan)

1. **Hook script language = Python via the shared venv** (`.claude/skills/.venv/bin/python3`). One source; reuses
   `memory_gap.py` directly. (venv always exists post-install in a project that installed product-spec.)
2. **`--reflect` harvester = ship an agent def at top-level `.claude/agents/memory-harvester.md`** (NOT a skill-subdir —
   agents are spawnable only from `.claude/agents/`; bundled via manifest `agents:` so the recipient gets it in-place
   with no copy hack). Frontmatter: **`model: opus`**, **`tools: Glob, Grep, Read, Bash`** (read-only — NO
   Write/Edit/NotebookEdit/Task → cannot write memory at the tool layer). `description` names that it serves product-spec
   `--reflect`. *Cost note: opus harvester → higher token cost per `--reflect`; accepted because `--reflect` is
   opt-in/explicit.*
3. **Recommend-nudge cadence = passive one-line, ≤1/day, with an explicit "never".** Markers:
   `hook-prompted-last:<date>` (1-day cooldown) + `hook-optout` (set only on an explicit user "stop asking"). Not a
   blocking dialog; never vanishes after a single accidental skip.
4. **Keep BOTH optional add-ons:** the PO-facing **`--voice`** flag (explicit 3D voice entry point, writes via
   `record_po_style`) AND the **`judged_not_stored`** `memory_gap` signal (belt-and-suspenders for the cache).
5. **`--reflect` UX = on-demand + a soft `--status` suggestion** when drift-since-last-validate is high. Never automatic.
6. **Doc-placement principle (hard constraint):**

   | File | Role | For new `--reflect`/`--memory-hook`/"Memory pass" |
   |------|------|---------------------------------------------------|
   | `CLAUDE.md` | ref-only, token-optimized (loads every turn) | ONE Workflow-Pointers row + ONE scripts-list line; NO long prose |
   | `references/*.md` | operative detail | full flow (`workflow-reflect.md`, memory-enforcement) |
   | `GUIDE-EN.md` / `GUIDE-VI.md` | full use-cases | add UC for `--reflect`, `--memory-hook`, "Memory pass" |
   | `README.md` | overview / install | 1–2 lines (flag + install note) |

7. **No-hook reversal is re-ratified** and recorded in the plan's "locked decisions" block (Tier-1 hook = opt-in;
   reversal documented, not silent).
8. **`--reflect` git-degrade (requirement, not a question):** if the project / `docs/product/` is not a git repo,
   `reflect_scan.py` harvests from `.memory/`/`decisions.md` diff state only, skips commit-derived candidates, never
   crashes.
9. **Phase-1 build task (not a decision):** verify on the target CC version — `SessionStart`/`Stop`/`PostToolUse`,
   `stop_hook_active`, and the 8-block cap env (`CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`) — before building the hook.

---

## 9. Packaging / distribution (claude-pack bundle) — evidence-grounded

**Manifest today:** `skills: [product-spec, claude-pack]` (both default ✓), `agents: []`, `hooks: []`,
`top_level.include_settings: false`. Bundled installer (`install.sh.template`) extracts `.claude/...` paths and runs
per-skill `install.sh` ONLY under `RUN_HOOKS=1` (opt-in); it never touches settings.

| Component | How it ships | Change? |
|-----------|--------------|---------|
| product-spec + claude-pack skills | already default-bundled | none |
| new scripts (`memory_gap.py`, `memory_gap_hook.py`, `reflect_scan.py`) + references | auto-ship via skill slug rglob | none |
| **harvester agent** | place at top-level `.claude/agents/memory-harvester.md` + add to manifest `agents:` → lands in recipient's `.claude/agents/`, spawnable, no copy hack | **manifest** |
| **hook** | ship the SCRIPT (auto via skill) + the `--memory-hook` installer flag (capability). **Do NOT auto-register** — settings stay out of the bundle (`include_settings: false`; `settings.local.json` safety-dropped). Recipient opts in post-install | no settings bundling |

**install.sh / template changes:**
- **product-spec `install.sh` / `.ps1`:** ADD `--memory-hook` (idempotent merge into `settings.local.json`).
- **claude-pack's own `install.sh`:** NO change (sets up claude-pack's venv only).
- **bundled-installer templates (`install.sh.template` / `.ps1.template`):** NO logic change — per-skill hooks
  (`RUN_HOOKS=1`) + agent files (`.claude/agents/...`) handled generically.
- **`INSTALL.md.template`:** ADD one line — optional post-install `bash .claude/skills/product-spec/install.sh
  --memory-hook` to enable the opt-in memory hook.
- **`pack.manifest.yaml`:** `agents:` += `memory-harvester.md`; bump `version` on release (tag-CI owns the build).

**Posture:** "default include the hook" = ship the *capability* (script + agent + `--memory-hook` flag), NOT an
auto-registered settings entry — auto-modifying the recipient's settings = trust violation (the same reason the
recommend-and-ask / never-silent-force decision stands). NO sub-agent and NO hook for claude-pack ITSELF.
