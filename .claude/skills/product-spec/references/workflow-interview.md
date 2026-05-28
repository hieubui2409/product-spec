# Workflow — Interview & Generate

End-to-end workflow the LLM follows for the **product / brd / prd / epic / story** flags (and the no-flag init flow). Phased, resumable, adaptive, bilingual.

## Detect State (no-flag entry)

1. Look for `<root>/docs/product/PRODUCT.md`.
2. If missing → propose **Init product** via AskUserQuestion. On confirm, run *Init flow* below.
3. If present → present the No-Flag Menu (see SKILL.md). Each menu choice maps to one of the flag flows below.

## Init Flow (no PRODUCT.md yet)

1. Ensure `docs/product/` exists (create if not).
2. Run the **Vision** interview (`references/interview-vision.md`) — V1 through V8.
3. After V1–V8, write:
   - `PRODUCT.md` via `generate_templates.py --type product` with the labels from the answers.
   - `vision.md` via `generate_templates.py --type vision` with the narrative.
4. Append a change-log entry via `generate_templates.py --type change_log_entry --keep-optional detail`.
5. Offer next step: "Create the BRD now, or stop here?"

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

## Bilingual Handling

- `.session.md.lang` carries the active language (`en` or `vi`).
- `AskUserQuestion` text + options use the active language; IDs and frontmatter keys stay English.
- VI ships best-effort. If the PO writes mixed EN/VI, accept both, normalize whitespace, but keep the answer in whatever language the PO used.

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
2. Offer a quick `--validate` and `--viz tree` to summarize what was built.

## Examples (snippets the LLM emits)

> "I see PRODUCT.md exists. Want to (1) refine BRD, (2) add a new PRD, (3) add stories under an existing epic, (4) validate, (5) update, (6) visualize, (7) approve, (8) summary?"

> "Sounds like 'easy onboarding' — what does easy look like specifically? What does the user see or do in the first 60 seconds?" *(5-Why round 1)*

> "Out of 12 candidate requirements you've named, you've marked 10 as MUST. If any one of those delays launch by a month — is it still MUST?" *(MoSCoW gate)*
