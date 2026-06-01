# Workflow — Auto-Decompose

End-to-end workflow for the **--auto** flag (brain-dump → spec hierarchy). The delta **--update** flow lives separately in `workflow-update.md`.

## `--auto` Flow (brain-dump decomposition)

The PO pastes (or refers to) a large free-form text dump. The skill chunks it, proposes a decomposition into BRD goals / PRDs / epics / stories, asks for confirmation on ambiguous splits, then writes the artifacts with full traceability.

### Step 1 — Capture the brain-dump

- Ask: "Paste the brain-dump, or give a path to a file."
- Load into memory as `dump_text`.
- Chunk if `len(dump_text) > 4000 chars`: split on blank lines or section headings, max ~3000 chars per chunk. Process chunks in order; the LLM keeps a running tally of identified candidates.

### Step 2 — First-pass extraction (LLM)

For each chunk, the LLM extracts candidates:

- **Goal candidates** — sentences expressing a business outcome ("Reach $1M ARR", "Achieve 80% repeat-purchase").
- **PRD candidates** — multi-sentence descriptions of a feature-area ("user authentication", "billing").
- **Epic candidates** — bounded chunks within a feature-area ("sign-in epic", "password recovery epic").
- **Story candidates** — single user-facing slices ("as a shopper, I want to reset my password").

Each candidate is recorded as: `{type, title, source_excerpt, suggested_parent}`.

### Step 3 — Propose decomposition

Present the proposed tree to the PO in one batch:

```
Proposed decomposition:
- BRD-G1 (new): "Reach $1M ARR in 12 months"
- BRD-G2 (new): "Achieve 80% repeat-purchase rate"
- PRD-AUTH (new): "User authentication"
  - PRD-AUTH-E1: "Sign-in flow"
    - PRD-AUTH-E1-S1: "Email + password sign-in"
    - PRD-AUTH-E1-S2: "OAuth Google sign-in"
  - PRD-AUTH-E2: "Password recovery"
    ...
- PRD-BILLING (new): "Billing & subscriptions"
  ...

Ambiguous items needing your call:
- "Allow user to upload an avatar" — looks like a story but no clear epic. Attach to PRD-AUTH or new PRD-PROFILE?
- "Send weekly newsletter" — likely a separate PRD-NOTIFICATIONS. Confirm?
```

### Step 4 — Confirm-batch on ambiguous items

For each ambiguous item, present an `AskUserQuestion` with 2–4 concrete options. **Do not silently classify** ambiguous items. Defer to PO.

**No silent reversal of PO-confirmed answers.** A brain-dump can restate something the PO already decided — a different scope boundary, a renamed persona, a changed threshold — recorded in the `.session.md` **Validation Log** (`workflow-interview.md → Validation Log`). If a candidate would **reverse** such a confirmed answer, do **not** fold it in silently: run the **No Silent Reversal** protocol (`workflow-update.md → No Silent Reversal`) — surface the verbatim original + reason + trade-off + Keep/Change/Hybrid — and apply nothing until the PO chooses. This holds even when the artifact carrying the original answer is still `draft`; a confirmed decision is protected by its confirmation, not by `approved` status.

### Step 5 — Write artifacts

Once decomposition is confirmed, generate the files in dependency order:

1. BRD (one file; multiple goals as `goals[]`).
2. PRDs.
3. Epics.
4. Stories.

Use a **single in-memory ID counter** so that batch-allocated parent-scoped IDs are unique even before any file is written. Pass `--id` explicitly to `generate_templates.py` so the counter is the source of truth.

Each file is generated with `keep-optional` set to the minimum that captures the PO's brain-dump content.

### Step 6 — Append change-log

One change-log entry per artifact created (action = `created_via_auto`, reason = "decomposed from brain-dump").
