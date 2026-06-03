# E2E run log — Backlog C/D/E flows on `/e2e/dating-app`

> Phase 9 (9a) of plan `260603-1817-backlog-cde-implementation`. Records the REAL run of every new
> surface against the committed dating-app spec, with named nodes + real script output. Driven in the
> main agent (ultracode), not the lens sub-agent fleet. Caches scrubbed (canonical timestamps, no
> web-cache). All commands via `.claude/skills/.venv/bin/python3`.

## Keep-vs-recreate audit
- **KEEP** (still valid): the whole spec (BRD→PRD→epic→story), the 18 `voice-ladder9-*` voice demos,
  the two existing lens-caches. `goal_without_metric` is **clean** — all 3 BRD goals carry metrics
  (`BRD-G1 [mau-monthly]`, `BRD-G2 [weekly-match-rate]`, `BRD-G3 [premium-conversion-rate, arpu]`), so
  the new C11 check does NOT invalidate the spec → no spec recreate needed.
- **RECREATE / ADD** (new features touch): DEC register + apply-critique progress markers; a scoped
  `PRD-CHAT` critique (for the inherit/rollup lifecycle); `release-notes.md`; scrubbed `.memory` caches.

## New product-spec flows (Part 1 — all real)

### `--apply-critique` (E1)
Consumed `docs/product/critique/voice-ladder9-en-lvl5.md` (lens-cache `22e9b7fd857a9d8e`, 19 findings).
Recorded two rulings atomically:
- finding `62cf6231` `[product] BRD-G2` → **Change+re-approve** → `DEC-1` (re-point BRD-G2 to a
  sustained-conversation north-star metric).
- finding `cfee3a85` `[product] PRD-EVENTS-E1-S3` → **Defer** → `DEC-2` (defer concert ticketing).
Resume markers written to `.memory/apply-critique/22e9b7fd857a9d8e.json` (re-run skips both).

### `--viz audit` (C9)
`visualize.py --view audit --format md` renders the chronological trail; the two new DECs join the
change-log rows (when · artifact · action · who · what-drifted · DEC). No `unreconciled` rows here
(every DEC corroborates an artifact). ASCII + md only.

### `--summary --audience release-notes` (E4)
`assemble_audit_trail.since_last_approved` → since=`None` (nothing approved) → all 5 events folded into
`docs/product/release-notes.md` via the `release_notes` template (frontmatter scalars rendered; the
multi-line "Since Last Approved" body composed from the C9 delta, same pattern as exec `brd_goals_summary`).

### `--discover` (E2)
`ingest_raw_inputs.py --path discovery-inputs --scaffold` over `discovery-inputs/interview-notes.md`:
accepted the `.md`, candidate buckets stay **empty by design** (GATE-NEVER-ASSUME — synthesis is the
interview's job). A `.env` placed alongside would be excluded; the read-fence resolves every walked
entry (symlink-escape closed).

### `goal_without_metric` (C11)
`strict_gate.py` → 0 errors · 6 warns; **no** `goal_without_metric` finding (all goals carry metrics).

## Critique lifecycle (Part 2 — real `critique_scan.py` output)

Prefs set: `critique_inherit: on` · `critique_rollup: on` · `critique_inherit_depth: nearest`.

Authored a real scoped critique **`critique/260603-prd-chat-lvl5.md`** (scope `PRD-CHAT`, level 5, 4
lenses, 2 blockers) registered through the real cache path: lens-cache `d4ec0301275ffe2f` +
findings-index (`PRD-CHAT:15`, `PRD-CHAT-E1-S4:18` blockers) + per-scope `critique-state`.

| Lifecycle leg | Command (scope) | Real result |
|---|---|---|
| **Inherit** (parent→child) | scan `PRD-CHAT-E1-S1` | `inherited_context` = 1 → `PRD-CHAT:15` blocker surfaced as the child's inherited risk |
| **Rollup** (child→parent) | scan epic `PRD-CHAT-E1` | `descendant_rollup` = "2/4 critiqued children carry blockers" (`PRD-CHAT-E1-S3`, `PRD-CHAT-E1-S4`) |
| **Cache HIT** | re-scan `PRD-CHAT` unchanged | `provenance.reuse = full` (report already current) |
| **Cache MISS** | `--fresh` `PRD-CHAT` | `provenance.reuse = none` (forced fresh run) |

## acme-shop lv5 showcase (Part 2)
Added `product-spec-critique/examples/critique-acme-shop-all-level5.md` — a real level-5 (no-mercy,
default) `all`-scope critique, citations grounded in `product-spec/examples/acme-shop` (PRD-MOBILE:13/28/37,
PRD-ANALYTICS:4/13, BRD-G5, PRD-MOBILE-E1-S1:18). The **lv7-9 harm-floor safety fixtures + their
grounding test are UNTOUCHED**.

## Commit hygiene
`.memory` caches scrubbed: `stored_at`/`last_ts` ISO values → canonical `2026-06-03T00:00:00+00:00`;
report-stem labels (e.g. `260603-prd-chat-lvl5`) left as-is (not timestamps); `web-cache/` absent
(third-party text never shipped). Desync-guard test ties this run to Phase-3's E1 freshness fixture.
