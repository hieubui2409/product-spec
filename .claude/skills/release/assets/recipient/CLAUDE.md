<!-- recipient-variant -->
# product-spec Bundle — LLM Operating Guide

Auto-loaded by Claude Code (always in context). This is the **always-on safety + routing
layer** for the three installed skills. Each skill's full contract lives in its `SKILL.md`.
**When a request matches a skill below, load that skill's `SKILL.md` before acting;
don't operate from memory.**

| When the request is about…                                                      | Load |
|---------------------------------------------------------------------------------|------|
| Product spec: vision/BRD/PRD/epic/story, validate, approve, summary, viz,        | `.claude/skills/product-spec/SKILL.md` |
| export, decision, discover, reflect, update, status                             |      |
| Critiquing an existing spec (4 lenses product/tech/market/craft, voice levels)  | `.claude/skills/product-spec-critique/SKILL.md` |
| Usage/health read: which skills get used, script/subagent health, validate-pass | `.claude/skills/telemetry/SKILL.md` |
| proxy — plain-Vietnamese analytics over local telemetry (read-only)             |      |

Speak product language (personas/problems/value/scope/acceptance) for the two product skills;
plain-Vietnamese usage/health narration for `telemetry`.

---

## Always-On Safety Floor (every turn — never deferred to a reference)

A reference only enters context if loaded; these GATEs must not depend on that. They apply on
every turn regardless of active skill.

<GATE-NO-SILENT-REVERSAL>
A new claim that contradicts an `approved` artifact is a stop point. Do NOT edit, pick a side,
or tidy it up. Surface verbatim with three choices: **Keep** (reject new claim) · **Change**
(re-approve, owner + date) · **Hybrid** (record both, follow-up). Only the PO choosing
**Change** with explicit re-approval touches approved content. If unsure it truly contradicts —
ask. Record the ruling in the Decision Register (`DEC-<n>`) so it is not re-litigated.
</GATE-NO-SILENT-REVERSAL>

<GATE-NEVER-ASSUME>
Ask via AskUserQuestion by default. Assume ONLY when: the PO already answered
(`.session.md`/`PRODUCT.md`); a closed allowed-value field has exactly one fit; or generating
PO-editable boilerplate (and you say so). NEVER assume persona identities/counts, core-value
alignment, scope (`in`/`out`/`core-value`), or sign-off. **Never set `status: approved`**
without explicit PO approval + owner + date. In doubt about assuming — you're not. Ask.
</GATE-NEVER-ASSUME>

## Five Operating Principles

1. **Frontmatter is source-of-truth** — parse YAML; never infer structure from headings.
2. **DRY — one home per fact** — cross-reference by ID; never duplicate prose.
3. **Script vs LLM split** — scripts handle graph/struct; LLM judges prose/alignment. Scripts first.
4. **Never overwrite PO prose** — on update, flag affected nodes and ask before regenerating.
5. **No silent reversals** — see GATE-NO-SILENT-REVERSAL above.

## Anti-Rationalization

| Shortcut | Reality |
|----------|---------|
| "Let me just write the code" | Spec tool. Capture story + AC for build team. |
| "Scope is obvious, I'll set it" | Scope is PO's call. Never assume — ask. |
| "Contradicts approved, I'll fix it" | Surface Keep/Change/Hybrid. Never silently flip. |
| "Clear to mark approved" | Needs explicit PO approval + owner + date. |
| "PO said skip asking, skip warning too" | Proceed, name residual risk. GATEs never waived. |
| "I'll tidy their wording" | Never overwrite PO prose. Flag, then ask. |
| "Infer from headings" | Frontmatter is source-of-truth. Parse YAML. |
| "File tree shows graph state" | Run scripts first. Don't infer from layout. |
