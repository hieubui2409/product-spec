# Issues & Deferred Decisions — Backlog C/D/E implementation

> Captured during `/ck:cook` ultracode run (2026-06-03). **Not interviewed during the run** per PO
> instruction ("run all, do not interview user … interview user when he asks about it later").
> When the PO asks about any row, interview then. Severity: 🔴 blocks correctness · 🟡 worth a ruling · 🟢 FYI.

## Run configuration (PO directives applied)
- **Workflow:** ultracode — implement directly in main agent, minimal subagent spawns.
- **Reviewer/validator reduction:** single consolidated `code-reviewer` pass at the end (not per-phase); fixers merged (one fix pass folding all findings) instead of one-subagent-per-finding.
- **e2e/example phases (9/10):** lean on committed caches/fixtures + fixture-replay for token economy; correctness/cleanup/consistency/plan-coverage/DRY bars still enforced by the final reviewer.
- **No interview:** all `AskUserQuestion`-worthy forks resolved by the plan's already-recorded PO rulings; anything genuinely undecided is logged below rather than asked.

## Environment notes
- 🟢 Test baseline required two global git settings to go green in this container:
  `commit.gpgsign=false` / `tag.gpgsign=false` (container enforces a signing server that returns 400)
  and `user.name`/`user.email`. Without them 31 git-dependent tests (check_fence, memory_gap, reflect_scan)
  error at `git commit`. These are env-only, not code issues.

## Baseline anchor (regression gate — plan.md:40)
- product-spec **552** · product-spec-critique **150** · claude-pack **134** = **836** collected+passing cases.
- Rule for every phase: collected-passing count must not drop below the per-skill baseline (additive only).

## Post-plan TODO (PO-requested 2026-06-03)
- [ ] **Update `BACKLOG.md`** after plan completes: mark the done C/D/E items (E5, D12, E1, C9, E4, E2, D11, C11) as shipped; note C10/E3 remain parked/deferred.

## Phase status (this run)
| Phase | Item | Status |
|-------|------|--------|
| 1 | E5 per-skill release identity | ✅ done (verifier + 2 CHANGELOGs + CI gate step) |
| 2 | D12 cross-skill CI gate | ✅ done (3 workflows, bug_class in 3 configs, offline guard) |
| 3 | E1 apply-critique loop | ✅ done (parse/progress scripts, atomic DEC, injection-safe, gate, workflow ref) |
| 4 | C9 audit-trail view | ✅ done (assembler, `--viz audit` ascii+md, unreconciled rows) |
| 5 | E4 stakeholder brief | ✅ done (`--summary --audience`, release-notes template, delta helper) |
| 6 | E2 discovery seed | ✅ done (`--discover` ingest, fence/filter/bounded-recursion, workflow ref) |
| 7 | D11 _hashable consolidation | ✅ done (`render_common.py`, output unchanged) |
| 8 | C11 assumption-rigor + goal_without_metric | ✅ done (lens prompts + check + fixtures + eval) |
| 9 | 9a E2E | ✅ **done** — D1 executed (see below); only the optional 4-agent live fleet re-run is unused |
| 10 | 9b docs sweep + changelog | ✅ **done** — D2 executed (GUIDEs EN+VI surgically extended, changelogs backfilled) |

## Code review (single consolidated pass, 2026-06-03)
- 🔴→✅ **CRITICAL — `--discover` directory-walk symlink escape (FIXED, commit 2b50e12).** `_walk_dir`
  passed un-resolved `iterdir()` entries to the lexical fence → a symlink inside a walked dir pointing
  outside root was read (verified exploit leaked `/tmp` content). Fixed by resolve-then-fence on every
  walked entry + 2 regression tests (walked symlinked file + dir). Exploit re-run → blocked, 0 leak.
- ✅ Other 6 invariants verified holding (read-fence, injection-sanitize, GATE reapproval, audit
  unreconciled, goal_without_metric precedence, viz md/audit gating). 2 LOW observations already
  resolved (audit dead-boolean simplified pre-commit; `except (DecisionError, Exception)` is
  pre-existing, out of scope).

## Open decisions / deferrals (interview later)

- ✅ **D1 — DONE 2026-06-03 (ultracode).** Drove every new surface on `/e2e/dating-app` for REAL (run log:
  `e2e/dating-app/RUN-LOG-backlog-cde-flows.md`):
  - `--apply-critique` → 2 atomic DECs (`DEC-1` change, `DEC-2` defer) + resume markers;
  - `--viz audit` (md), `--summary --audience release-notes` (→ `release-notes.md`), `--discover`
    (empty candidate buckets, GATE), `goal_without_metric` (clean — goals carry metrics);
  - **critique lifecycle from real `critique_scan` output**: authored scoped `critique/260603-prd-chat-lvl5.md`
    (lens-cache `d4ec0301`, registered in index+state); **inherit** (`PRD-CHAT:15`→child `PRD-CHAT-E1-S1`),
    **rollup** (epic `PRD-CHAT-E1` → "2/4 critiqued children carry blockers"), **cache HIT** (`reuse:full`) +
    **MISS** (`--fresh`→`reuse:none`);
  - **acme lv5 showcase** added (`critique-acme-shop-all-level5.md`, citations grounded), **lv7-9 safety
    fixtures + grounding test untouched + green**; caches scrubbed; suites green (product-spec 601).
  - The only thing NOT done (by the "reduce-agent/use-cache" directive): spawning the live 4-lens + opus
    consolidator + humanizer fleet to regenerate reports — the main agent acted as the lenses inline. Ask
    the PO if a full live-fleet regeneration is ever wanted; the lifecycle + contracts are already proven real.
- ✅ **D2 — DONE 2026-06-04.** GUIDEs **surgically extended** (not wholesale-rewritten — honors
  "never overwrite PO prose"; preserves existing quality): product-spec `GUIDE-EN.md` + `GUIDE-VI.md`
  gained sections for `--discover` (P1), `goal_without_metric` (P7), `--summary --audience` (P10),
  `--viz audit` (P11), and `--apply-critique` (P15) — VI written natively. Critique `GUIDE-EN.md` +
  `GUIDE-VI.md` gained the strengthened assumption-rigor (consequence-clause) note. product-spec
  `README.md` flag list + critique `README.md` worked-examples (incl. the lv5 showcase + dating-app
  run) updated. All **3 CHANGELOGs** backfilled by subject-scope + `--follow` (critique rename traced),
  no fabricated version numbers. Suites green (601/152/142), docs-only. NOTE: chose surgical-extend
  over the wholesale GUIDE rewrite the original deferral floated — if the PO wants a full narrative
  rewrite/restructure of the guides, that's a separate ask.
- 🟢 **D3 — `--format md` is audit-only.** Added `md` to `visualize.py` FORMATS but rejected for every
  non-audit view. If the PO later wants markdown for other views, that's a clean extension.
