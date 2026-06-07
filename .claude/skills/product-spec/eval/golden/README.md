# Golden artifacts — the `llm_advisory` judge fixtures

The shared harness `.claude/skills/_shared/lib/llm_eval.py` judges each scenario's
`llm_advisory` assertions against a **golden artifact** kept here as `<scenario-id>.md`
(or the path named by a scenario's `golden` key). The golden is the produced spec/report
artifact the scenario describes — the LLM judge reads it and decides PASS/FAIL per assertion.

## Convention

- One file per scenario that has advisory assertions: `eval/golden/<id>.md`.
- A missing golden is reported **MISSING** (loud, non-gating) — never a silent pass.
- Goldens are **LLM-generated, then human-reviewed** before they are trusted:
  ```
  .claude/skills/.venv/bin/python3 .claude/skills/_shared/lib/llm_eval.py \
      --skill product-spec --gen
  ```
  Each draft carries a `<!-- DRAFT: … NEEDS HUMAN REVIEW … -->` header. Review against the
  scenario's expected_output + assertions, then **remove the DRAFT marker** to bless it.
  `--gen` never overwrites an existing file.

## Why not in CI

The judge needs an API key and its verdicts are non-deterministic — local on-demand gate,
not a PR blocker. The deterministic half (`run_evals.py`) is what CI runs.
