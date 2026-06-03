# Brainstorm: Backlog C/D/E — approaches, trade-offs, sequencing

> 2026-06-03 · Grounded by `plans/reports/research-260603-1758-backlog-cde-grounding-report.md`.
> Principles: YAGNI/KISS/DRY · modes-on-existing-skills > new skills · product-spec stays non-tech-PO + no runtime network.
> Locked: B6 low (internal) · E3 deferred · E5 standardize hybrid. PO calls this round: C10 → park (note) · E1 → present pros/cons · D11 → close + micro-util only.

---

## TL;DR sequencing (recommended build order)

| # | Item | Why this slot | Effort |
|---|---|---|---|
| 1 | **E5** | Cheapest, unblocks honest release identity, zero design risk. Warm-up. | S |
| 2 | **D12** | Safety net BEFORE adding features (E1/E2). 50 tests exist but ungated → regressions invisible. Build the gate first. | S–M |
| 3 | **E1** | Highest leverage (closes the critique return-edge). Infra mature. Needs the anchoring decision (below). | M |
| 4 | **C9** | Mostly assembly of existing parts; governance value; feeds future E3. | M |
| 5 | **E4** | Thin mode on existing assemblers; cheap polish. | S |
| 6 | **E2** | Genuinely additive but real scope-creep risk; do after the loop is closed. | M–L |
| 7 | **D11** | Close out: consolidate 2 micro-utils, drop the rest. | S |
| — | **C10** | **Parked** (PO note): pending "where does task mgmt live" decision; build sync skill + bridge infra later. | — |
| — | **E3** | Deferred (not in market). | — |

Rationale for order: **stabilize (E5, D12) → close the loop (E1) → governance/polish (C9, E4) → widen (E2) → cleanup (D11)**. Don't add features (E1/E2) on top of an ungated test suite.

---

## E5 — Per-skill release identity *(do first, S)*

**Recommended:** Changesets-lite, no new tooling.
1. Add `CHANGELOG.md` to product-spec + product-spec-critique (keepachangelog format, mirror claude-pack's).
2. Keep `version:` in each `SKILL.md` as the truth-of-record per skill.
3. Make `claude-pack-release.yml` **read + verify** SKILL.md versions match what's shipped (fail the build on drift) — it currently reads tag only.
4. Bundle tag stays the single release unit (no per-skill tags/release split — honors the decision).

**Alternatives:** (a) full Changesets/Lerna tooling → rejected, JS-ecosystem weight for a Python+md repo, YAGNI. (b) keep decorative versions → rejected, that's the status quo the decision overrides.

**Trade-off:** tiny ongoing discipline (update 3 changelogs per release) vs honest per-skill history. CI verify step is the only code.

---

## D12 — Cross-skill regression gate *(do second, S–M)*

**Recommended:** Two thin workflows + reuse existing tests.
1. `product-spec-ci.yml` + `product-spec-critique-ci.yml` (or one matrix workflow) running the **existing 31 + 10 pytest files** on PRs touching each skill's paths. Mirror `claude-pack-ci.yml` shape (3 OS × 3 Python is overkill for pure-Python md tooling → **1 OS × 2 Python** is enough; argue down the matrix).
2. A small **shared bug-class test module** asserting the cross-cutting invariants that held across all 11 red-team cycles: symlink escape (fs_guard + tarball), case-insensitive bypass (slug + safety_check), untracked-asset inclusion. Most already have a test — this just centralizes + runs them as one named gate.

**Alternatives:** (a) port the full 59-agent red-team into CI → rejected, non-deterministic + slow, that's a manual audit not a gate. (b) leave manual → rejected, the whole point is repeatability; D12 is the highest-leverage item in D.

**Trade-off:** CI minutes vs catching the regression classes that already bit 3× before features land. Cheap insurance.

---

## E1 — Apply-critique loop `--apply-critique <report>` *(do third, M — highest leverage)*

**Flow (agreed shape):** read critique report → per finding present **Keep / Change+re-approve / Defer** → record ruling in DEC register (`DEC-<n>`) → honor GATE-NO-SILENT-REVERSAL → never auto-edit prose (reuse `--update` impact-pass discipline).

**The core problem:** critique findings have **no stable ID** (transient, anchored by `evidence ID:line`). When the spec changes after the critique, `:line` drifts and a finding may be stale. Three anchoring strategies — **pros/cons as requested**:

### Option A — Anchor by artifact-id + freshness check *(my pick)*
Drop the line number for matching; anchor each finding to its **artifact ID** (`PRD-AUTH-E1-S1`). Compare the artifact's `body_hash` now vs at critique time; if changed, flag the finding **"⚠ may be stale — spec changed since critique"** before asking Keep/Change/Defer.
- **Pros:** survives line drift (the common case — edits shift lines, not identity); reuses `body_hash` that already exists in snapshots; degrades gracefully (warns, doesn't block); PO still in control.
- **Cons:** coarser than line-level (a finding about AC #2 won't auto-pinpoint if the story body moved); "stale" warning is heuristic, not proof the finding is wrong; multiple findings on one artifact need disambiguation by their `critique` text.

### Option B — Require freshest critique (hash-gate)
Only allow apply if the report's bundle/body_hash matches the current spec. Any drift → force re-run critique first.
- **Pros:** strongest correctness guarantee — every finding provably current; no stale-finding ambiguity; simplest matching logic once gate passes.
- **Cons:** rigid; punishes the normal workflow (PO fixes finding #1, which changes the file, now must re-critique before applying #2); re-running critique costs tokens + web; friction likely makes POs skip the loop entirely → defeats the feature.

### Option C — Manual per-finding PO confirmation
No auto-mapping; show each finding verbatim, PO eyeballs whether it still applies, then Keep/Change/Defer.
- **Pros:** simplest to build (no hash/anchor logic); PO judgment is the source of truth; zero false "stale" flags.
- **Cons:** all cognitive load on PO; doesn't scale past a handful of findings; no machine help exactly where the tool could add value; easy to mis-judge staleness manually.

**My recommendation: A as the default, with C as the fallback** when an artifact carries multiple findings (show them together, let PO pick). B's correctness is real but its friction kills adoption — reserve the hash-check as an *informational* signal (the "stale" warning in A), not a hard gate. Effort: M (the DEC-write + GATE plumbing already exists; new work is the report parser + the per-finding interaction loop).

**Open sub-question for you:** accept "A default + C fallback", or do you want the stricter B?

---

## C9 — Semantic audit-trail view *(do fourth, M)*

**Recommended:** A read-only **`--audit` view** (or `--viz audit`) that joins parts that already exist — no new capture machinery.
Render a chronological table from: `change-log.md` entries (action/author/date/dims/affected_set) + `approval:` frontmatter (approved_by/at/version) + `stale_approvals` from `status.py` + DEC register references. Output ASCII + md (+ html later if wanted), bilingual via session lang.
- Columns: *when · artifact · action · who-approved · what-drifted · DEC ref*.

**Alternatives:** (a) extend `--status` instead of a new view → viable, but `--status` is a health snapshot, not a timeline; mixing concerns. (b) new capture/event-log subsystem → rejected, YAGNI, the data is already captured, only unjoined.

**Trade-off:** small render module vs first governance-usable history. Sets up E3 later (outcome tracking reads the same trail). Keep it a **viewer** (read-only) per skill's "viewers never edit" rule.

---

## E4 — Stakeholder brief *(do fifth, S)*

**Recommended:** A thin `--brief` mode reusing the `--summary`/`--export` assemblers, with an audience preset (exec one-pager / release-notes). No new assembler.
- Reuse `generate_templates.py` exec_summary path + `assemble_digest.py`; add a release-notes template variant (what changed since last approved snapshot — pulls from C9's trail, so **sequence after C9** if release-notes flavor wanted; exec one-pager can ship before C9).
- Bilingual via session `lang` (matches current behavior).

**Alternatives:** dedicated new generator → rejected, DRY violation; the assemblers already do 90%.

**Trade-off:** near-free; mostly a template + flag. Lowest risk item.

---

## E2 — Discovery seed `--discover` *(do sixth, M–L)*

**Recommended (scoped tight):** ingest raw text inputs → propose **candidate** personas/problems/JTBD as a *draft seed* the Vision interview then confirms field-by-field. Never auto-commit personas (GATE-NEVER-ASSUME: persona identity/count is never assumed).
- Input: plain text/md files (transcripts, tickets, competitor notes) the PO points at.
- Output: a pre-filled draft for V2 (personas) / V1 (problem) that the interview presents as "found these — confirm/edit/reject".

**Scope-creep watch (brutal):** this is the easiest item to over-build (entity extraction, clustering, sentiment…). Keep it: text in → candidate bullets out → interview confirms. Distinct from `--auto` (which decomposes a *brain-dump you wrote* into the hierarchy; `--discover` synthesizes *upstream raw inputs* into interview seeds). If that distinction blurs in practice, **merge into `--auto` instead of two flags**.

**Alternatives:** fold into `--auto` from the start → possible, but their inputs/outputs differ enough to justify separate entry; revisit after E1 ships.

**Trade-off:** real PO value (no cold start) vs LLM-quality variance + scope discipline. Do it last of the features so the loop (E1) proves out first.

---

## D11 — Shared foundation *(close out, S)*

**Decided:** Close the "common base" ambition (research showed duplication ≈ 0 — critique + claude-pack generate no HTML, so no shared XSS/design-system surface exists).
**Recommended residue:** consolidate only the genuine micro-duplication — `_now()` (×4) and `_hashable()` (×3) — into one tiny shared util module the 3 skills import (note: must stay inside each skill's packable tree or the shared `common/`/`_shared/` that claude-pack already bundles; verify pack picks it up). Drop determinism/safety/design-system extraction entirely.

**Trade-off:** ~1 small module, removes 5 copy-paste sites. Marginal but real DRY win, and it's the only honest part of D11. Don't gold-plate it.

---

## C10 — Round-trip to issue tracker *(PARKED)*

**Status:** backlog open note per PO. Blocked on a prior decision: **where will task management live** (GitHub Issues / Jira / other). Once chosen, build it as a **separate outward-facing skill + bridge infra** reading product-spec's exported artifact (preserve `PRD-AUTH-E1-S1` IDs, one-way idempotent, back-ref the issue number into story frontmatter). Keeps product-spec's no-runtime-network + non-tech-PO promises intact. Not actioned this round.

---

## Risks / cross-cutting

- **Sequencing risk:** building E1/E2 before D12 means new features land with no automated gate → revert to manual red-team. Hence D12 second.
- **product-spec positioning drift:** every new flag (`--apply-critique`, `--discover`, `--audit`, `--brief`) adds CLI surface to a "non-technical PO" tool. Keep each one menu-discoverable (no-flag menu) and plain-language; don't let the CLI become the engineer-facing surface the backlog already flags as a con.
- **E1 `:line` drift** is the one genuine technical unknown — resolve the anchoring choice (A/B/C) before planning E1.

## Unresolved questions

1. **E1 anchoring:** accept "Option A default + C fallback", or require the stricter Option B hash-gate?
2. **C10:** which task tracker is the target (decides when C10 un-parks)?
3. **E2 vs --auto:** start E2 as a separate flag, or prototype inside `--auto` first and split only if needed?
4. **D12 matrix:** OK to drop to 1 OS × 2 Python for the 2 new workflows (vs claude-pack's 3×3)?
