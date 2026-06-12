# Brainstorm → Plan handoff — remaining field-audit work → release 2.4.0

```yaml
type: brainstorm-to-plan
created: 2026-06-12
decision_owner: hieubt
source_plan: plans/260611-0050-po-field-audit-fix-waves/ (P1-P10a,P12,P13-draft landed)
target_plan_mode: /ck:plan --deep --tdd --validate
pipeline: brainstorm → plan → cook(--auto all) → code-review → consolidate/interview → release 2.4.0 + push
```

## Problem statement

Field-audit fix waves mostly landed (P1-P9, P10a, P12 committed; ledger 44/46). Remaining buildable
work = deferred PO-facing (P10b) + insight (P11) + validation-pack proposals (#9), all sitting unbuilt.
`CHANGELOG [Unreleased]` populated but `pack.manifest.yaml` still `2.3.0` → release uncut. Owner wants
one autonomous pipeline: build all remaining → plan/cook/review → interview on undecidables → cut+push 2.4.0.

## Decisions locked (AskUserQuestion 2026-06-12 — do NOT re-litigate)

| Q | Locked | Consequence |
|---|---|---|
| Scope | **P10b + P11 + #9 (all buildable)** | LIB-9 deferred — only resolvable on a real transcript session, not synthetic |
| #14 depth | **Full `--snapshot`/`--restore` engine + VCS-nudge** | not the nudge-only narrowing; engine independent of PO git |
| #9 depth | **All 3** (horizon↔PRD lint + persona-warn + id-backfill migrator) | id-backfill goes through GATE dry-run→confirm |
| Release/push | **Claude pushes tag + `gh release` directly** | after stage-5 interview sign-off; outward action authorized |
| Version | **2.4.0 (minor)** | new Added features present |
| Cadence | **Continuous; stop only at 3 gates** | gates = (a) /ck:plan --validate Qs, (b) post-review interview, (c) release-notes sign-off |

## Deliverable set (9 build-new units + release)

**#9 — validation pack (ask-PO-first cleared; all 3):**
- **#9a horizon↔PRD-table lint** (POX-F02, real PO defect): parse `PRODUCT.md` subsystem table by **ID**
  (not heading — brittle), compare vs each PRD frontmatter `horizon`; warn on mismatch. Rule in `check_consistency.py`.
- **#9b persona frontmatter↔body warn** (POX-F06): persona in VISION/BRD frontmatter but no body portrait → warn. Same rule-engine.
- **#9c `id: PRODUCT` template + id-backfill migrator**: separate migrate script, **P5 metric→metrics pattern**
  (dry-run 0-byte default; `--apply` requires `--confirmed-by`+`--date`; entry-scoped; idempotent). GATE re-approve.

**P10b — PO-facing (full):**
- **#6 visuals**: `*-latest.html` stable alias + banner "rendered at X, spec drifted N nodes" + content-hash
  reuse (no new file when hash matches) + `--viz --clean` (purge old, keep latest) + post-approve re-render nudge. `visualize.py`.
- **#13 decision index**: `--decision --list PRD-X` from `decision_register.py` data layer — filter affects/date/status,
  draw supersede chain, DEC dashboard row.
- **#14 snapshot/restore (full engine)**: `--snapshot` / `--restore <ts>` auto-before migration/large-update +
  README in snapshot dir; `--status`/validate warn when `docs/product` outside git or large uncommitted diff;
  Closing-the-Loop commit nudge post-approve. New snapshot module + `status.py` VCS-warn.

**P11 — insight (boundary A9 held — kit never self-evolves, only suggests):**
- **#8 artifact-events sink + heat lens**: reuse PostToolUse `Edit|Write|MultiEdit` matcher → record
  `{ts, artifact_path, op, session}` **path-only (no diff content)**; lens narrates VI "which PRD edited most".
- **#11 usage-summary export + harvester (report-only)**: `telemetry --export-summary` markdown aggregate
  (PO reviews then sends dev) + read-only harvester reads self-corrections + repeat-findings → **suggests**
  interview/template tweaks, never writes skill/template. Opt-in per run.
- **#15 change-log rotation + path-check**: monthly archive (`change-log/2026-06.md`) or cap+rollover;
  light "path mentioned in change-log exists" check; patch `assemble_audit_trail.py` read contract same-commit.

**Release 2.4.0:** bump each changed skill `metadata.version` + per-skill CHANGELOG; fill root
`[Unreleased]` with P10b/P11/#9 entries → `release.py --release 2.4.0 --apply` (locks → `[2.4.0]` + bumps
manifest together); commit; push tag `product-spec-v2.4.0`; `gh release create`.

## Approach rationale (vs alternatives)

- **Scope = maximal**: owner asked "all remaining problems". LIB-9 is the only true blocker (synthetic
  fixtures can't reproduce a 0-record live-hook channel) → deferred with reason, not dropped.
- **#14 full engine over nudge-only**: plan flagged YAGNI (PO has git) but owner chose engine — independent
  of PO's git habits, gives kit-native restore before risky migrations. Accepted scope cost.
- **#9 all 3 incl. id-backfill**: highest-signal lint (#9a) caught a real PO defect; id-backfill reuses the
  proven GATE-safe migrate pattern so artifact-id risk is contained.
- **One 2.4.0, not staged**: owner wants a single release at pipeline end; simpler changelog lifecycle.

## Implementation considerations & risks

- **Modularization budget (~250 exec-LOC)**: touched files already over — `check_consistency` 322 (#9a/#9b
  4th toucher → extract rule-engine), `visualize` 335 (#6 → split), `decision_register` 310 (#13 → split),
  `status` 249 (#14 nudges over → split or DEC). Default split; DEC only if split adds risk. Plan must phase this.
- **File-ownership serialize** (single-writer): `check_consistency` (#9a→#9b), `status` (#14 re-read after
  P6/P7/P10a), `assemble_audit_trail` (#15 re-read — P12 truncate already landed).
- **GATEs live during `--auto`**: id-backfill migrator is the one approved-artifact-touching unit → dry-run
  0-byte / `--apply` confirm-gated; any contradiction → stop, Keep/Change/Hybrid. Rest are build-new on
  synthetic fixtures ⇒ low GATE-trigger risk.
- **Privacy/boundary**: #8 path+op only (test asserts no diff content); #11 harvester read-only + opt-in
  (test asserts no write to skill/template). gitignore `.claude/telemetry/` already landed (P8).
- **Naming hygiene**: test/function/commit names describe behavior (CI lint blocks `test_(ps|lib|psc|pack)\d+`
  + commit-msg hook blocks finding-codes). Phase files may reference finding IDs as description only.

## Success / validation criteria

- 9/9 units RED→GREEN on synthetic in-repo fixtures; hard thresholds (byte/bool/count); each guard/migrate
  has a negative test (idempotent, no-over-fix, hook-HEAD-not-clobbered, fresh-install-not-broken).
- `CONTRIBUTING.md:69` suite (`telemetry .claude/hooks _shared`) + each touched skill suite green.
- POX-F02/F06/F04/F05(done)/F10/F11 ledger rows tick; build-new units record DECs + EVIDENCE before/after.
- `code-review` (coverage + adversarial correctness·cleanup·coverage·consistency·DRY) clean or
  consolidated→owner-decided.
- `release.py --release 2.4.0 --apply` green; manifest == `[2.4.0]`; per-skill version==skill-changelog-top
  (A4 gate); tag pushed; `gh release` live.

## Pipeline & gates

1. ✅ brainstorm (scope locked) → 2. `/ck:plan --deep --tdd --validate` (relay validate Qs) →
3. `/cook --auto` all phases → 4. `/code-review` (plan-coverage + adversarial 5-lens) →
5. **consolidate → interview owner** on undecidables + 2.4.0 release-notes sign-off →
6. cut 2.4.0 + push tag + `gh release`.

Stop-points: validate Qs · post-review interview · release-notes sign-off. Otherwise continuous.

## Unresolved (deferred, by decision)

- **LIB-9** — `UserPromptExpansion` 0-record: needs one real-transcript e2e session (matcher-fix vs
  `UserPromptSubmit` fallback vs remove). Out of this round; stays open in REVIEW.md + BACKLOG real-transcript bucket.
