# Red-team triage (round 2) — telemetry usage-&-health port (Full scope)

**Date:** 2026-06-07 · **Plan:** `260607-1500-telemetry-insights-skill/` · **Input:** code-reviewer review `from-code-reviewer-to-cook-telemetry-port-full-scope-review-260607-1909.md` + cook implementation. Round-1 red-team ran on the PRE-port shape; this round challenges the EXPANDED ported scope.

## Verdict
Merge-ready. 6/6 acceptance criteria verified (tests + fault-injection + smoke). 0 CRITICAL/HIGH. 1 MEDIUM applied, 3 LOW conscious-accepts, scope upheld.

## Triage

| # | Sev | Finding | Decision | Action |
|---|-----|---------|----------|--------|
| M1 | MED | `never_used` = 85, dominated by ~82 vendored `ck:*` skills → misleading PO headline | **ACCEPT (fix, data-layer)** | Added `owned` flag to `catalog.py` (name `cleanmatic:*`); `lens_usage_tokens` now lists never-used for OWNED only + `never_used_external_count` informational. Renderers + narration-contract updated. Live: "4 owned never-used (+81 ext)". Tests added. |
| L2 | LOW | bash-timer command-hash key drops `ms` for back-to-back identical commands | **ACCEPT (no change)** | Documented conscious accept; `ms` degrades (drops), never mis-attributes. Single-user tool, `ms` is approx. |
| L3 | LOW | PreToolUse:Bash now spawns a python proc on every Bash | **ACCEPT (no change)** | Doubles an existing per-Bash cost (PostToolUse already does); fail-open, ~tens of ms, PO accepted overhead at validate. |
| L4 | LOW | `validate_proxy.last_status` stays "validated" after first validate (marker overwritten, never deleted) | **ACCEPT (no change)** | Honestly framed in docstring; pass-rate window carries the directional signal. |

## Scope challenge (Full 8 lenses for a 3-owned-skill repo)
**Upheld, not gold-plating.** PO chose Full twice after seeing cost (plan validation log). The low-volume gate keeps thin lenses honest ("chưa đủ dữ liệu" — confirmed live: reliability/workflow/session all gated on current thin data). Marginal LOC per extra lens is small given shared catalog/render/gate infra. M1 was the one place broad scope produced actively misleading output → fixed. Per-phase shrink points remain available if the PO later wants to trim.

## Invariants re-checked (held)
- `_shared` NOT bundled; telemetry skill + 2 hooks + sinks absent from real `python -m pack` tarball (2 independent test layers).
- No SHIPPED script imports a CM-local telemetry module (grep-assert test).
- Hooks fail-open + pytest-silent (direct-invocation + fault-injection verified).
- atexit/excepthook stays REJECTED (would ModuleNotFoundError on recipients).
- HTML stays dropped (D4); E3 stays `[defer]` (no silent reversal).
- Deterministic build sha (identical across two builds).
- `verify_skill_versions` made bundle-portable (skips a missing DEFAULT skill dir) so the SHIPPED checker no longer fails on a recipient bundle lacking the CM-local telemetry skill — a side-effect the plan's D8 had not anticipated; fixed without reversing D8's intent (telemetry still semver-checked locally).

## Live end-to-end smoke (both new Phase-2 sinks proven on real data)
- `ms` recorded in `hook-telemetry.jsonl` (Pre/Post:Bash pairing) — e.g. `register_telemetry_hooks.py … ms:77`.
- `subagent-outcomes.jsonl` gained a line from the code-reviewer subagent run: `{code-reviewer, unknown}` — honest default (never fabricates success).

## Unresolved questions
- None blocking. M1 fix locus was decided as data-layer (robust) per reviewer recommendation; owned = `cleanmatic:`-prefixed `name:`.
