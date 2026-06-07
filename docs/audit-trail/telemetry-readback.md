# Telemetry read-back (A1)

The A1 hooks append JSONL to `.claude/telemetry/` (gitignored, local). Read them with
`jq` — no dashboard, no script (KISS, v1). Sinks:

| Sink | Written by | Shape |
|------|------------|-------|
| `invocations.jsonl` | `track-skill-invocation.cjs` | `{ts, skill, session, via}` |
| `hook-telemetry.jsonl` | `track-script-execution.cjs` | `{ts, source, script, exit}` |
| `sessions.jsonl` | `emit-session-summary.cjs` | `{ts, session, skills[], tools{}, files_modified, subagents, duration_s}` |
| `_spike.jsonl` | `telemetry-spike.cjs` (temporary) | event-shape probe for GATE C1/H2 |

## Queries

```bash
cd .claude/telemetry

# Skill adoption — invocation count per skill
jq -r .skill invocations.jsonl | sort | uniq -c | sort -rn

# Which real event carries a skill invocation (Spike 1 resolution)
jq -r .via invocations.jsonl | sort | uniq -c

# Script error rate per skill-script
jq -r 'select(.exit!=0) | .script' hook-telemetry.jsonl | sort | uniq -c | sort -rn

# Skills never invoked this window (compare against the skills catalog manually)
jq -r .skill invocations.jsonl | sort -u

# Session activity — files modified + duration trend
jq -r '[.ts, (.files_modified|tostring), (.duration_s|tostring)] | @tsv' sessions.jsonl
```

## Spike read-back (GATE C1/H2 — run after a session restart)

`telemetry-spike.cjs` is the empirical instrument for the two unverified events.
After restarting the session (so the harness loads the new hook registrations) and
invoking a skill + running a skill script:

```bash
# Spike 1 — which event(s) actually fired for a skill invocation?
jq -r '[.event, .tool, (.has_command|tostring)] | @tsv' .claude/telemetry/_spike.jsonl | sort -u

# Spike 2 — does any exit-code candidate appear non-null on a Bash PostToolUse?
jq -c 'select(.tool=="Bash") | .exit_candidates' .claude/telemetry/_spike.jsonl | sort -u
```

Once confirmed, re-target `track-skill-invocation` to the one real event and prune the
spike + the redundant registration:

```bash
node .claude/skills/_shared/scripts/register_telemetry_hooks.cjs --prune-spike
```
