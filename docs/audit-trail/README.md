# Audit trail

Dev-facing, durable, git-tracked record of **what was fixed** across review/red-team
cycles and **the proof** it worked. Two ledgers:

- **`EVIDENCE.md`** — one entry per landed fix: root cause + runnable before/after.
- **`REVIEW.md`** — per-cycle finding tracker (`[ ]` open · `[x]` fixed · `[~]` partial · `[N/A]`).

This is the artifact the `review-audit-self-decision.md` rule ("prove root cause
before fix") writes into. Not CI-driven; cadence = quarterly / post-major-feature.

## Conventions

- **ID grammar:** `(PS|PSC|PACK|LIB)-<n>` — skill-scoped (product-spec / -critique /
  the `release` skill, formerly `claude-pack` / shared lib). The `PACK` prefix token is
  retained so existing `PACK-<n>` IDs stay resolvable. Regex `^(PS|PSC|PACK|LIB)-\d+$`.
- **Category:** `CORRECTNESS · DRY · CONSISTENCY · CLEANUP · ENV · YAGNI`.
- **Severity:** `HIGH · MED · LOW`.
- **Evidence is runnable:** before/after blocks are copy-paste reproducible commands
  + their output — not prose. Scrub secrets/tokens before pasting.
- **No plan-artifact refs** inside (no `phase-0X`, finding codes, brainstorm section
  numbers) — per `review-audit-self-decision.md` (rule 5): explain the *why*, not the origin.
- **DEC tie-in:** when a fix resolves a ruled contradiction, cite the ruling
  `DEC-<n>` (Decision Register, `docs/product/decisions.md`). decisions.md = *what we
  decided*; EVIDENCE.md = *what changed + proof*.
- **Size caps:** `EVIDENCE.md` ≤200 lines, `REVIEW.md` ≤300 lines. Over cap → roll the
  oldest cycle into an `## Archive` section (keep the worked discipline, drop the bulk).

See `telemetry-readback.md` for A1 observability-sink `jq` queries.
