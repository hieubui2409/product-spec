# Golden artifacts — the `llm_advisory` judge fixtures

The shared harness `.claude/skills/_shared/lib/llm_eval.py` judges each scenario's
`llm_advisory` assertions against a **golden artifact** kept here as `<scenario-id>.md`
(or the path named by a scenario's `golden` key). The golden is the produced critique
report the scenario describes — the LLM judge reads it and decides PASS/FAIL per assertion.

## Convention

- One file per scenario that has advisory assertions: `eval/golden/<id>.md` (e.g. `0.md`).
- A missing golden is reported **MISSING** (loud, non-gating) — never a silent pass.
- Source a golden in this order of fidelity:
  1. **Map a real example report** (best, zero LLM) — point the scenario's `golden` key at a
     committed `examples/critique-acme-shop-*.md`. Several scenarios already do (2, 6, 7, 8, 9).
  2. **Subagent that runs the skill** (grounded) — spawn a Claude subagent that reads the real
     acme-shop spec + lens references and produces the report, writing it here. It cites *real*
     `ID:line` evidence because it read the actual files. This is the preferred way to fill a
     MISSING golden (proven: scenario 1's golden was generated this way and passes both advisory
     judgments). Orchestrated by the main agent, not the script.
  3. **`--gen` bootstrap** (rough, fallback) — a single-shot draft from prompt text only; it has
     NO access to the real spec so it cannot cite real evidence:
     ```
     .claude/skills/.venv/bin/python3 .claude/skills/_shared/lib/llm_eval.py \
         --skill product-spec-critique --gen
     ```
- Every generated golden carries a `<!-- DRAFT: … NEEDS HUMAN REVIEW … -->` header. Review it
  (does it honor the scenario's expected_output + assertions, and resolve its cited IDs?), then
  **remove the DRAFT marker** to bless it. Generation never overwrites an existing file.

## Judging (the real LLM gate)

```
.claude/skills/.venv/bin/python3 .claude/skills/_shared/lib/llm_eval.py --skill product-spec-critique
```
Reaches an Anthropic-compatible endpoint (`ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL`). A
gateway behind Cloudflare needs a real User-Agent (the client sends one) and may reject
assistant-prefill — the judge relies on prompt-strength JSON instead, so it is endpoint-portable.

## Why not in CI

The judge needs an API key and its verdicts are non-deterministic — so this is a local,
on-demand advisory gate, not a PR blocker. The deterministic half (`run_evals.py`) is what CI runs.
