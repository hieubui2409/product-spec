#!/usr/bin/env python3
"""llm_eval — the *advisory* half of the eval gate.

``run_evals.py`` runs the deterministic (``_gating: structural``) assertions and
honestly reports the judgment ones as ``SKIP(manual)``. This harness closes that
gap for the parts that genuinely need an LLM: it judges each ``llm_advisory``
assertion against a **golden artifact fixture** (the produced report / spec, kept
under ``eval/golden/``) and returns PASS / FAIL / MISSING / ERROR.

It NEVER fabricates a verdict. The LLM is reached through an injectable client:

  * ``FakeLLMClient`` — deterministic, drives every test (no network, no key).
  * the real client (stdlib ``urllib`` against an Anthropic-compatible endpoint)
    is built *only* by ``make_client()`` when credentials are present. Generating
    or judging for real needs a key + human review — deliberately NOT run in CI.

A golden fixture that is absent is reported MISSING (loud, counted, non-gating by
default; gating under ``--strict-missing``) — a gap stays visible, never a silent
pass. An unparseable judge reply is ERROR (gating) — a broken judge is loud too.

Usage (real run needs ANTHROPIC_AUTH_TOKEN/-API_KEY + ANTHROPIC_BASE_URL):
  llm_eval.py --skill <name> [--root R] [--strict-missing]
  llm_eval.py --evals path/evals.json --skill-dir path/skill
  llm_eval.py --skill <name> --gen        # draft missing goldens for review
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

PASS, FAIL, MISSING, ERROR = "PASS", "FAIL", "MISSING", "ERROR"

_ARTIFACT_CAP = 24000  # chars of golden text fed to the judge (keeps the prompt bounded)


# --- LLM clients --------------------------------------------------------------

class FakeLLMClient:
    """Deterministic client for tests. ``responder`` is one of:
    a callable ``(system, user) -> str``; a list (popped in call order); a dict
    mapping a substring-of-the-user-prompt to the reply (first match wins)."""

    def __init__(self, responder):
        self._responder = responder
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        r = self._responder
        if callable(r):
            return r(system, user)
        if isinstance(r, list):
            return r.pop(0) if r else ""
        if isinstance(r, dict):
            for needle, reply in r.items():
                if needle in user:
                    return reply
            return r.get("_default", "")
        return str(r)


class UrllibAnthropicClient:
    """Minimal stdlib client for an Anthropic-compatible Messages endpoint.
    No SDK dependency; only built when credentials exist. Untested in CI by design."""

    def __init__(self, token: str, base_url: str, model: str):
        self._token = token
        self._base = base_url.rstrip("/")
        self._model = model

    def complete(self, system: str, user: str) -> str:
        import urllib.request

        body = json.dumps({
            "model": self._model,
            "max_tokens": 2048,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }).encode()
        req = urllib.request.Request(
            f"{self._base}/v1/messages",
            data=body,
            headers={
                "content-type": "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key": self._token,
                "authorization": f"Bearer {self._token}",
                # A real UA is required: gateways behind Cloudflare reject urllib's default
                # signature with HTTP 403 (CF error 1010, "banned browser signature").
                "user-agent": "anthropic-sdk-python/0.39.0",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 (explicit gen path)
            data = json.loads(resp.read())
        parts = data.get("content") or []
        return "".join(p.get("text", "") for p in parts if isinstance(p, dict))


def make_client():
    """Return a real LLM client, or raise with a clear message. This is the
    deferred path: it needs credentials and the result needs human review."""
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    model = os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL") or os.environ.get("ANTHROPIC_MODEL") or "claude-sonnet-4-6"
    if not token:
        raise RuntimeError(
            "llm_eval real run needs ANTHROPIC_AUTH_TOKEN or ANTHROPIC_API_KEY (deferred path: "
            "key + human review required). Tests inject FakeLLMClient and never reach here."
        )
    return UrllibAnthropicClient(token, base, model)


# --- judge --------------------------------------------------------------------

_JUDGE_SYSTEM = (
    "You are a strict, skeptical eval judge for a product-spec critique tool. You read ONE "
    "assertion and the produced artifact, then decide if the artifact satisfies the assertion. "
    "Default to FAIL when the evidence is absent or ambiguous — do not give benefit of the doubt. "
    "Do NOT explain your reasoning, do NOT think out loud, do NOT use a markdown code fence. "
    "Your ENTIRE response must be exactly one JSON object and nothing before or after it: "
    '{"verdict": "PASS" | "FAIL", "rationale": "<one short sentence citing the artifact>"}'
)


def build_judge_user(assertion: dict, scenario: dict, artifact: str) -> str:
    art = artifact if len(artifact) <= _ARTIFACT_CAP else artifact[:_ARTIFACT_CAP] + "\n…[truncated]"
    return (
        f"SCENARIO INTENT:\n{scenario.get('prompt', '').strip()}\n\n"
        f"EXPECTED OUTPUT:\n{scenario.get('expected_output', '').strip()}\n\n"
        f"ASSERTION TO JUDGE (id={assertion.get('id')}):\n{assertion.get('text', '').strip()}\n\n"
        f"PRODUCED ARTIFACT:\n{art}\n\n"
        'Now output ONLY the JSON verdict object {"verdict":...,"rationale":...} and nothing else.'
    )


def parse_verdict(raw: str) -> tuple[str, str]:
    """JSON-first, tolerant of surrounding prose. Unparseable → (ERROR, reason)."""
    m = re.search(r"\{.*\}", raw or "", re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            raw_v = obj.get("verdict")
            why = str(obj.get("rationale", "")).strip() or "(no rationale)"
            # Models phrase the verdict as a string ("PASS"), a bool (true), or yes/no.
            if isinstance(raw_v, bool):
                return (PASS if raw_v else FAIL), why
            v = str(raw_v).strip().upper()
            if v in (PASS, FAIL):
                return v, why
            if v in ("TRUE", "YES"):
                return PASS, why
            if v in ("FALSE", "NO"):
                return FAIL, why
        except (ValueError, TypeError):
            pass
    # Fallback: a bare leading PASS/FAIL token.
    head = (raw or "").strip().upper()
    if head.startswith(PASS):
        return PASS, "(bare verdict)"
    if head.startswith(FAIL):
        return FAIL, "(bare verdict)"
    return ERROR, f"unparseable judge reply: {(raw or '')[:80]!r}"


def judge_assertion(assertion: dict, scenario: dict, artifact: str, client) -> tuple[str, str]:
    try:
        raw = client.complete(_JUDGE_SYSTEM, build_judge_user(assertion, scenario, artifact))
    except Exception as e:  # noqa: BLE001
        return ERROR, f"judge call raised {type(e).__name__}: {e}"
    return parse_verdict(raw)


# --- golden fixtures ----------------------------------------------------------

def golden_path(skill_dir: Path, scenario: dict) -> Path:
    rel = scenario.get("golden") or f"eval/golden/{scenario.get('id')}.md"
    return (skill_dir / rel).resolve()


def load_golden(skill_dir: Path, scenario: dict) -> str | None:
    p = golden_path(skill_dir, scenario)
    return p.read_text(encoding="utf-8") if p.is_file() else None


def _scenarios(doc: dict) -> list[dict]:
    return doc.get("evals") or doc.get("scenarios") or []


def _advisory(scenario: dict) -> list[dict]:
    return [a for a in scenario.get("assertions", []) if isinstance(a, dict) and a.get("_gating") == "llm_advisory"]


def run_llm_evals(evals_path: Path, skill_dir: Path, client) -> tuple[list, dict]:
    doc = json.loads(evals_path.read_text(encoding="utf-8"))
    rows: list[tuple] = []
    tally = {PASS: 0, FAIL: 0, MISSING: 0, ERROR: 0}
    for sc in _scenarios(doc):
        advisory = _advisory(sc)
        if not advisory:
            continue
        artifact = load_golden(skill_dir, sc)
        for a in advisory:
            if artifact is None:
                verdict, detail = MISSING, f"no golden at {golden_path(skill_dir, sc)}"
            else:
                verdict, detail = judge_assertion(a, sc, artifact, client)
            tally[verdict] += 1
            rows.append((sc.get("id"), a.get("id"), verdict, detail))
    return rows, tally


# --- golden generation -------------------------------------------------------
# Two ways to source a golden, in order of fidelity:
#   1. BEST — a real artifact: map a committed example report via the scenario's
#      `golden` key (e.g. examples/critique-acme-shop-mobile-level7.md), or a
#      Claude subagent that actually RUNS the skill over the sample and reads the
#      real spec → a grounded report (cites real ID:line). Orchestrated by the
#      main agent (the Agent/Task tool), not this script.
#   2. BOOTSTRAP — `--gen` below: a single-shot draft from prompt text alone. It
#      has NO access to the real spec, so it cannot cite real evidence; it only
#      seeds a file for a human to replace/correct. DRAFT-marked, never trusted as-is.

_GEN_SYSTEM = (
    "You draft a ROUGH BOOTSTRAP golden for a product-spec critique eval scenario from the "
    "prompt text alone (you do NOT have the real spec, so do not invent specific evidence IDs). "
    "Produce the report shape the scenario describes. Output the artifact body only (markdown), "
    "no preamble. A human MUST review and ground it before it is trusted."
)


def generate_golden(scenario: dict, client) -> str:
    user = (
        f"SCENARIO PROMPT:\n{scenario.get('prompt', '').strip()}\n\n"
        f"EXPECTED OUTPUT:\n{scenario.get('expected_output', '').strip()}\n\n"
        f"ASSERTIONS THE ARTIFACT MUST SATISFY:\n"
        + "\n".join(f"- {a.get('text', '')}" for a in scenario.get("assertions", []) if isinstance(a, dict))
    )
    return client.complete(_GEN_SYSTEM, user)


def gen_missing_goldens(evals_path: Path, skill_dir: Path, client) -> list[Path]:
    doc = json.loads(evals_path.read_text(encoding="utf-8"))
    written: list[Path] = []
    for sc in _scenarios(doc):
        if not _advisory(sc):
            continue
        p = golden_path(skill_dir, sc)
        if p.is_file():  # never overwrite a reviewed golden
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        body = generate_golden(sc, client)
        p.write_text(f"<!-- DRAFT: LLM-generated golden, NEEDS HUMAN REVIEW before trust. scenario={sc.get('id')} -->\n\n{body}\n", encoding="utf-8")
        written.append(p)
    return written


# --- CLI ----------------------------------------------------------------------

def _resolve(args) -> tuple[Path, Path]:
    if args.evals:
        return args.evals, (args.skill_dir or args.evals.parent.parent)
    if not args.skill:
        raise SystemExit("either --skill or --evals is required")
    skill_dir = args.root / ".claude" / "skills" / args.skill
    return skill_dir / "eval" / "evals.json", skill_dir


def main(argv=None, client=None) -> int:
    ap = argparse.ArgumentParser(description="Judge a skill's llm_advisory eval assertions against golden fixtures.")
    ap.add_argument("--skill", help="skill name under .claude/skills/")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[4])
    ap.add_argument("--evals", type=Path, help="explicit evals.json (overrides --skill)")
    ap.add_argument("--skill-dir", type=Path, help="explicit skill dir (with --evals)")
    ap.add_argument("--gen", action="store_true", help="draft missing golden fixtures (needs creds; review before trust)")
    ap.add_argument("--strict-missing", action="store_true", help="MISSING golden → fail exit")
    args = ap.parse_args(argv)

    evals_path, skill_dir = _resolve(args)
    if not evals_path.is_file():
        print(f"[llm_eval] FATAL: evals.json not found at {evals_path}", file=sys.stderr)
        return 2
    if client is None:
        client = make_client()  # deferred real-LLM path; tests inject a Fake instead

    if args.gen:
        written = gen_missing_goldens(evals_path, skill_dir, client)
        for p in written:
            print(f"  [DRAFT]   {p}")
        print(f"\n{evals_path.parent.parent.name}: drafted {len(written)} golden(s) — REVIEW before trusting.")
        return 0

    rows, tally = run_llm_evals(evals_path, skill_dir, client)
    width = max((len(str(r[1])) for r in rows), default=8)
    for sid, aid, verdict, detail in rows:
        print(f"  [{verdict:<8}] {str(aid):<{width}}  {detail}")
    print(
        f"\n{evals_path.parent.parent.name}: "
        f"{tally[PASS]} pass · {tally[FAIL]} fail · {tally[MISSING]} missing · {tally[ERROR]} error"
    )
    failed = tally[FAIL] > 0 or tally[ERROR] > 0 or (args.strict_missing and tally[MISSING] > 0)
    if failed:
        print("LLM EVAL GATE: FAIL", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
