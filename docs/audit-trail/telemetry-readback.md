# Telemetry read-back (A1)

The A1 hooks append JSONL to `.claude/telemetry/` (gitignored, local). Read them with
`jq` — no dashboard, no script (KISS, v1). Hooks are Python (`.claude/hooks/*.py`); the
sink helper is `.claude/skills/telemetry/scripts/telemetry_paths.py`. Sinks:

| Sink | Written by | Shape |
|------|------------|-------|
| `invocations.jsonl` | `track_skill_invocation.py` | `{ts, skill, session, via}` |
| `hook-telemetry.jsonl` | `track_script_execution.py` (+ `mark_bash_start.py` for `ms`) | `{ts, source, script, exit, ms?}` |
| `sessions.jsonl` | `emit_session_summary.py` | `{ts, session, skills[], tools{}, files_modified, subagents, duration_s}` |
| `subagent-outcomes.jsonl` | `track_subagent_outcome.py` (SubagentStop) | `{ts, agent_type, outcome, session}` — outcome ∈ success/api_error/timeout/blocked/unknown |

`ms` (wall-clock script duration, approx) appears only when the PreToolUse:Bash
`mark_bash_start.py` paired with the PostToolUse:Bash `track_script_execution.py`;
records with no pair degrade gracefully (no `ms`).

### Crash-audit sink (not a usage sink)

Separate from the four usage sinks above, the shared `hook_runtime.log_hook_error`
appends a crash-audit line whenever a hook raises — so a fail-open hook still leaves a
trace instead of vanishing silently:

| Sink | Written by | Shape |
|------|------------|-------|
| `.claude/hooks/.logs/hook-crashes.log` | `hook_runtime.log_hook_error` (any hook crash) | `{ts, hook, type, msg, tb}` — exception **metadata only**, never the stdin payload (no PII); coarse-rotated at 256 KB → `.1` |

This is diagnostic, not telemetry — the lenses do not read it. `CK_HOOK_AUDIT_DISABLED`
(and any pytest run) silences it; `CK_HOOK_LOG_DIR` redirects it.

### Per-hook config gate

All seven Python hooks are gated by `.claude/hooks/product-spec-hooks.json` (a flat
stem→bool map — plus a `_README` note key that `hook_enabled` ignores — read once per
process via `hook_runtime.hook_enabled`, cached in `_load_config`):

- **Telemetry stems** (the 5 sink hooks): a missing/absent key ⇒ **ENABLED** by default;
  the global `CK_TELEMETRY_DISABLED` env forces all of them OFF.
- **Enforcement stems** (`memory_gap_hook`, `product_spec_critique_nudge`): a missing key
  ⇒ **DISABLED** (a blocking hook is never fallback-enabled); the installer's
  `--memory-hook` / `--critique-hook` flip the flag true. The telemetry kill-switch does
  not affect them.
- **Memory-hook MODE** (`memory_gap_mode`): the shipped config now AUTO-ENABLES
  `memory_gap_hook` in **advisory** mode — it warns on stderr at exit 0 (never blocks
  turn-end). The exit-2 block contract is OPT-IN only: set `memory_gap_mode: "blocking"`.
  Any non-`blocking` value (absent, typo) falls to the safe advisory default, so
  auto-enable can never silently impose blocking. The runtime rule above is unchanged —
  a *missing* `memory_gap_hook` key is still DISABLED; the bundle simply ships it `true`.
- **Upgrade safety**: the installer treats the two enforcement hooks as kit code. A
  pre-config-gate copy (one that never calls `hook_enabled`) is force-replaced with the
  gated bundle copy + a `.bak.<ts>`, so an old unconditional-blocking hook can't survive
  an upgrade. A gate-aware copy the PO locally edited is kept and flagged `[CONFLICT]`
  (never blind-overwritten; `FORCE_OVERWRITE=1` takes the bundle).

## Queries

```bash
cd .claude/telemetry

# Skill adoption — invocation count per skill
jq -r .skill invocations.jsonl | sort | uniq -c | sort -rn

# Which real event carries a skill invocation (ship-both: Skill-tool vs prompt-expansion)
jq -r .via invocations.jsonl | sort | uniq -c

# Script error rate per skill-script
jq -r 'select(.exit!=0) | .script' hook-telemetry.jsonl | sort | uniq -c | sort -rn

# Skills invoked this window (compare against the skills catalog manually)
jq -r .skill invocations.jsonl | sort -u

# Session activity — files modified + duration trend
jq -r '[.ts, (.files_modified|tostring), (.duration_s|tostring)] | @tsv' sessions.jsonl

# Subagent reliability — outcome mix per agent type
jq -r '[.agent_type, .outcome] | @tsv' subagent-outcomes.jsonl | sort | uniq -c | sort -rn

# Script duration (where paired) — slowest scripts
jq -r 'select(.ms!=null) | [.script, (.ms|tostring)] | @tsv' hook-telemetry.jsonl | sort -t$'\t' -k2 -rn | head
```

## Lenses + the `cleanmatic:telemetry` skill

Beyond raw `jq`, the **usage-&-health lenses** turn these sinks into narrated reports.
Deterministic gather (script) → narration (the `/cleanmatic:telemetry` skill, plain
Vietnamese). The lenses ship in the release bundle; the skill is read-only.

```bash
# overview dashboard-lite (ascii); --format md|mermaid|json; --lens usage|session|
# health|reliability|workflow|validate|memory|product_memory|forensics|all; --days N --top N
.claude/skills/.venv/bin/python3 .claude/skills/telemetry/scripts/analyze_telemetry.py \
  --lens all --format ascii
```

The PO normally invokes `/cleanmatic:telemetry` (VI narration + the mandatory
"Cái này KHÔNG đo được" honesty section); the `jq` queries above are the manual
fallback. The `validate` lens is an **internal-quality** proxy (did validate pass),
explicitly NOT market/user outcome (E3, deferred).

## (Re)registering the hooks

The telemetry hooks are wired into the local (ck-managed, gitignored) `.claude/settings.json`
by an idempotent script — re-run it any time after a `settings.json` regen:

```bash
# add/repair the telemetry registrations (idempotent; venv python)
.claude/skills/.venv/bin/python3 .claude/skills/telemetry/scripts/register_telemetry_hooks.py

# inspect / remove
.claude/skills/.venv/bin/python3 .claude/skills/telemetry/scripts/register_telemetry_hooks.py --check
.claude/skills/.venv/bin/python3 .claude/skills/telemetry/scripts/register_telemetry_hooks.py --remove
```
