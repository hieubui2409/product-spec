# Reasoning-judge brief — SKILL.md flag-table compaction (before vs after)

You are an independent routing judge (proof (b), best-of-3). Decide whether compacting the flag
tables in two SKILL.md files **preserved the router's ability to pick the right flag** from an
ambiguous PO ask that does NOT name the flag.

## What to read

- AFTER (compact, live): `.claude/skills/product-spec/SKILL.md` and
  `.claude/skills/product-spec-critique/SKILL.md` — the "Flags" tables + the "Loads references on
  Demand" section.
- BEFORE (verbose) purpose text for each compacted flag is reproduced below.

## BEFORE — verbose purpose text (the rows that were compacted)

**product-spec**
- `--discover`: "Discovery seed: ingest raw upstream text (transcripts / support dumps / competitor notes — files AND directories) → propose candidate personas / problems / JTBD to seed the Vision/BRD interview. Read-fenced to project root, .md/.txt only, dotfiles excluded, size-capped, bounded recursion. Never auto-commits — the interview confirms each."
- `--summary`: "Generate a 1-page audience brief FROM the spec. --audience exec (default) = exec one-pager. --audience release-notes = what changed since the last approved snapshot, from the governance audit trail. Same source-of-truth + render path, different audience — no new top-level flag."
- `--decision`: "Decision Register: view or record an explicit PO decision (DEC-<n>) in docs/product/decisions.md. A contradiction with an approved artifact auto-opens a decision; --decision lets the PO record one directly. Authoritative home for ruled drift (po_ruling_ref: DEC-<n>)."
- `--learn`: "Learn from reality (post-launch loop). Umbrella → asks outcomes or feedback. Outcomes: per BRD goal capture target/actual → record_outcome.py computes hit/partial/miss → OUT-<n>. A miss on an approved goal is surfaced (Keep/Change/DEC) — never auto-edited. Feedback: point at review/feedback files → ingest_raw_inputs.py → candidate problems/personas/risks → feeds --update. Never auto-commits."
- `--apply-critique`: "Consume a product-spec-critique report and walk each finding (Keep / Change+re-approve / Defer), recording one DEC-<n> per resolved finding. Findings from the structured lens-cache; report read-fenced to docs/product/critique/; a Change on an approved artifact goes through GATE-NO-SILENT-REVERSAL; prose never auto-rewritten. Resumable + injection-safe."
- `--status`: "Spec health nudge: report the last-validated state (errors/warns at the last --validate) and surface a soft fence reminder when the spec has drifted since. Read-only."
- `--viz`: "Render visualization. ASCII-default graph views: tree/heatmap/scope/roadmap/persona/gap/moscow/time/delta. HTML-native default: risk/competition/dashboard. Body viewers: board/explorer. Governance: audit. Learning views (--learn): scorecard/insight-gap/outcome-trend/learning-map/learning."
- `--format`: "Visualization format: ascii · mermaid · html. Default is per-view. ASCII downgraded, not removed."
- `--filter-wont`: "Hide deferred items (moscow: wont or scope: out) from tree/roadmap/time/persona/board/explorer. Default keeps them visible."
- `--export`: "read-once Export: assemble a spec slice into ONE self-contained doc under docs/product/exports/. Pairs with --layers, --depth, --compact-mode, --format md|html."
- `--layers`: "Filter which artifact types appear. --export uses buckets vision,brd,prd,epic,story; --viz board/explorer filter by TYPE goal,prd,epic,story. Unknown token rejected with non-zero exit, never silently dropped."
- `--compact-mode`: "--export compaction: struct (default, deterministic) · llm (emits <!-- COMPACT --> markers). llm requires --format md — rejected with --format html."
- `--lang`: "Interview/output language: en (default) · vi. IDs and frontmatter keys stay English; body-view facets/labels + in-view value labels + export headings localize. Page chrome stays English."
- `--voice`: "Record the PO's voice into .memory/po-style.yaml deterministically (--register/--vocabulary/--recurring-asks/--do/--dont, lang-keyed) instead of relying on the LLM noticing a wording correction."
- `preferences.py --set`: "Write a PO preference deterministically (repeatable). Persists engagement knobs interview_rigor (light/standard/deep) + action_prompting (minimal/standard/proactive), default standard. load→merge→save: preserves every other key; bad enum exits non-zero."
- `--reflect`: "Retroactive memory harvest: when inline forcing-functions were skipped, scan git + .memory/ (git-degrade-safe), spawn the read-only opus harvester, propose unrecorded rulings (DEC-<n>) / self-corrections / voice for PO confirm-then-persist."

**product-spec-critique**
- `[scope]`: "The artifact to critique by ID (PRD-AUTH, PRD-AUTH-E1, PRD-AUTH-E1-S1) or all (default). Full ancestry always pulled as context. all = whole tree, expensive."
- `--level 1..9`: "Voice intensity. Default = critique_level pref (5 no-mercy if unset). Aliases 1-6: warm/gentle/blunt/savage/no-mercy/roast; 7-9 no alias. 1-4 forbid personal attack; 5 lifts the redline (default baseline, ungated); 6-9 carry a danger gate (warning + AskUserQuestion ad-hoc, standing-pref reminder 6-8); 6 enforces a personal roast; 7 confrontational ông/tôi; 8 street mày/tao; 9 adds work profanity, re-confirms via AskUserQuestion EVERY run, downgrades to 8 on decline. Register at 7-9 reads critique_address_gender/dialect/profanity. Universal-harm floor at ALL levels: never violence threats, protected-characteristic slurs, self-harm, sexual, family-target profanity. Every level keeps evidence + fix."

## The routing scenarios (ambiguous asks — the flag is NOT named)

product-spec: route-viz, route-learn, route-set-pref, route-apply-critique, route-discover,
route-layers, route-format, route-reflect, route-summary, route-decision, route-voice,
route-compact, route-lang, route-export, route-filter-wont, route-status.
critique: route-level, route-scope.
(Full prompts live in each skill's `eval/evals.json` — read them there.)

## Rubric (per scenario, decide yes/no, then a verdict)

1. **BEFORE-routes:** would the verbose row route this ambiguous ask to the expected flag/mode?
2. **AFTER-routes:** does the compacted row (live SKILL.md) still route it to the same flag/mode?
3. **GATE-intact:** if the flag carries a safety GATE / danger-gate fact, is it still present in the compacted row? (e.g. `--decision`/`--learn`/`--apply-critique` keep GATE:NO-SILENT-REVERSAL; `--level` keeps the 6-9 danger gate, the level-9 re-confirm/downgrade, and the universal-harm floor.)
4. **Verdict:** `HELD` if (AFTER-routes ∧ GATE-intact); else `REGRESSED`, with the specific lost discriminator.

## Output format (return exactly this)

```
JUDGE VERDICT
- route-viz: HELD|REGRESSED — <one-line reason>
- ... (all 18) ...
SUMMARY: <n> HELD, <m> REGRESSED. Overall: HELD|REGRESSED.
```
Be skeptical: if a compacted row dropped the discriminator that separates it from a sibling flag
(e.g. --summary vs --export vs --viz; --decision vs --reflect; --lang vs --voice), mark REGRESSED.
