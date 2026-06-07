# Telemetry read-back (A1)

The A1 hooks append JSONL to `.claude/telemetry/` (gitignored, local). Read them with
`jq` — no dashboard, no script (KISS, v1). Hooks are Python (`.claude/hooks/*.py`); the
sink helper is `.claude/skills/_shared/lib/telemetry_paths.py`. Sinks:

| Sink | Written by | Shape |
|------|------------|-------|
| `invocations.jsonl` | `track_skill_invocation.py` | `{ts, skill, session, via}` |
| `hook-telemetry.jsonl` | `track_script_execution.py` | `{ts, source, script, exit}` |
| `sessions.jsonl` | `emit_session_summary.py` | `{ts, session, skills[], tools{}, files_modified, subagents, duration_s}` |

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
```

## (Re)registering the hooks

The telemetry hooks are wired into the local (ck-managed, gitignored) `.claude/settings.json`
by an idempotent script — re-run it any time after a `settings.json` regen:

```bash
# add/repair the telemetry registrations (idempotent; venv python)
.claude/skills/.venv/bin/python3 .claude/skills/_shared/scripts/register_telemetry_hooks.py

# inspect / remove
.claude/skills/.venv/bin/python3 .claude/skills/_shared/scripts/register_telemetry_hooks.py --check
.claude/skills/.venv/bin/python3 .claude/skills/_shared/scripts/register_telemetry_hooks.py --remove
```
