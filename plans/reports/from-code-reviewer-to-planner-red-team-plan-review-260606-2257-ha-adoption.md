# Red-team Plan Review — HA Adoption (Observability + Audit + Eval/CI)

**To:** planner · **From:** code-reviewer · **Date:** 2026-06-06 22:57 · **Mode:** adversarial pre-impl
**Plan:** `plans/260606-2205-ha-adoption-observability-eval-audit/`
**Verdict:** **PROCEED-WITH-CHANGES** (2 CRITICAL gates must clear before Phase 01 & Phase 03 code)

Every finding cites a real file/section and proposes a concrete fix. Grammar sacrificed for concision.

---

## CRITICAL

### C1 — `PreToolUse:Skill` is a hook event that does not exist in Claude Code. A1's `invocations.jsonl` mechanism is built on a phantom matcher.
**Claim attacked:** phase-01 §Architecture L32, §Key insights L16 — "`PreToolUse:Skill → track-skill-invocation.cjs → invocations.jsonl`", "append new matchers". Blueprint Lens A L37 ports this verbatim from HA.
**Why wrong (evidence):** Claude Code's hook lifecycle (docs `code.claude.com/docs/en/hooks`) enumerates: `SessionStart, Setup, UserPromptSubmit, UserPromptExpansion, PreToolUse, PermissionRequest, … PostToolUse, … Stop, … SessionEnd`. PreToolUse matches on `tool_name` (`Bash`, `Edit|Write`, `mcp__.*`). **There is no `Skill` tool name**; skill invocation is surfaced via the separate **`UserPromptExpansion`** event ("when a user-typed command expands into a prompt… matcher filters on your skill/command names"). The plan ports HA's event names without verifying they exist in CM's runtime. CM's own `settings.json` (verified) never uses a `Skill` matcher anywhere. If `PreToolUse:Skill` is registered, the matcher simply never fires → `invocations.jsonl` stays empty forever → silent false-green (the worst kind: telemetry that looks installed, records nothing, and fail-open hides it).
**Concrete fix:** Before Phase 01 code, **spike the actual event**. Re-target skill-invocation tracking to `UserPromptExpansion` (matcher = skill/command names) OR confirm empirically that a `Skill` PreToolUse event fires in this Claude Code version by writing a one-line debug hook and invoking a skill. Update phase-01 §Architecture + the build-order note. Add an explicit "events verified against installed Claude Code version X.Y" line to the phase — HA's event vocabulary is NOT authoritative for CM.

### C2 — Phase 03 "deterministic-subset" is non-viable for claude-pack as written; the recommended option (i) collapses into the rejected option (ii); and it duplicates an existing taxonomy.
**Claim attacked:** phase-03 §Key insights L24 "claude-pack evals are **already mostly deterministic** … highest-value first target"; §Options (i) "add per-assertion tag `kind: deterministic|llm` … smallest reshape"; plan.md open-Q1.
**Why wrong (evidence):**
1. **claude-pack assertions are bare natural-language strings**, not `{script,args,extract,expected}`. Verified: `claude-pack/eval/evals.json` assertions are e.g. `"gzip header bytes [4:8] == 0x00000000"`, `"second run produces identical SHA256"`, `"no entry path contains '/.env'"` — free text with no checker mapping, no extract path, no expected value. A harness cannot "run the deterministic subset" without first PARSING those English sentences into executable checks. That parse + restructure **IS option (ii)** (rewrite into machine shape) — the option the plan explicitly rejected as "larger reshape". So the recommended (i) is internally inconsistent for the very skill the plan calls the easiest first target. (`grep -c '"_gating"' claude-pack/eval/evals.json` → 0; assertions have no structured fields.)
2. **Duplicate taxonomy (DRY violation — repo rule).** `product-spec/eval/evals.json` and `product-spec-critique/eval/evals.json` ALREADY tag every assertion with `_gating: "structural" | "llm_advisory"` (verified counts: product-spec 41 structural / 13 llm_advisory; critique 29 / 22). The plan proposes adding a NEW parallel field `kind: deterministic|llm`. Two fields meaning the same thing on the same objects = exactly the "parallel reimplementation of an existing pattern" anti-pattern. `CLAUDE.md` rule: "DRY — one home per fact."
**Concrete fix:** At the design gate, (a) **reuse `_gating`** (`structural`→runnable, `llm_advisory`→skip-manual) instead of inventing `kind`; (b) acknowledge claude-pack needs a real `check:`/`extract:` field added per assertion (this is reshape work, not tagging) — scope it honestly or **defer claude-pack to a second pass** and start the harness on product-spec's already-tagged `structural` subset; (c) re-estimate effort (see H4 — this is not "M", it's the largest phase). If the honest scope is "rewrite 3 eval schemas + harness + 3 CI wirings," strongly consider option (iii) defer for claude-pack and ship only the product-spec/critique `structural` slice now.

---

## HIGH

### H1 — `## [Unreleased]` is the NORMAL top heading of all 3 changelogs, not an "edge case". The naive helper ships broken on day one.
**Claim attacked:** phase-04 §Implementation L46 "regex first `^## \[(\d+\.\d+\.\d+)\]`"; §Red-team L65 / §Risk L77 treat `## [Unreleased]` as an edge to "skip".
**Why wrong (evidence):** Verified all 3 CHANGELOGs:
- product-spec: L10 `## [Unreleased]`, L12 `## [2.2.0]` (SKILL.md metadata.version `2.2.0`)
- critique: L11 `## [Unreleased]`, L13 `## [1.2.0]` (metadata.version `1.2.0`)
- claude-pack: L14 `## [Unreleased]`, L16 `## [1.4.0]` — **but SKILL.md metadata.version is `0.2.0`** (E5 decoupling: bundle tag 1.4.0 ≠ skill version 0.2.0).
So the "edge case" is the default state of every file. The step-2 regex `^## \[(\d+\.\d+\.\d+)\]` would not match `[Unreleased]` (no digits) — OK by luck — but the plan's framing means the *first* test author may grab "the top heading" literally and fail. **More dangerous:** claude-pack's CHANGELOG top semver is `1.4.0` while its SKILL.md is `0.2.0`. The plan's check (`SKILL.md version == CHANGELOG top semver`) would compare `0.2.0` vs `1.4.0` → **FALSE DRIFT on a correct repo**. claude-pack's CHANGELOG tracks the *bundle* version, not the skill version — A4's core equality assumption is wrong for claude-pack specifically.
**Concrete fix:** (1) Make "skip `[Unreleased]`, take first `^## \[<semver>\]`" the PRIMARY spec, not an edge note. (2) **Resolve the claude-pack contradiction before coding A4**: confirm whether claude-pack's CHANGELOG is bundle-versioned (1.x) or skill-versioned (0.2.0). If bundle-versioned, A4's equality check must EXCLUDE claude-pack or compare against a different source — otherwise A4 is red on a clean tree. This is a GATE-NO-SILENT-REVERSAL-adjacent contradiction with the E5 decoupling the plan itself cites (open-Q2). Surface to PO.

### H2 — `PostToolUse:Bash` may not expose an exit code; A1's `{exit}` field + stderr-regex inference is unverified and likely fragile.
**Claim attacked:** phase-01 §Key insights L14 "Hook has no real exit code → infer from stderr regex `Traceback|Error|Exception` → exit=1 else 0. Coarse but enough." §Architecture hook-telemetry `{exit}`.
**Why wrong/risky (evidence):** The hooks doc was truncated at the PostToolUse schema, so **the plan is guessing at the tool_response shape** (the plan author admits "no real exit code"). If PostToolUse *does* provide `tool_response.exit_code` (plausible — there is also a distinct `PostToolUseFailure` event in the lifecycle list), the stderr-regex hack is unnecessary and inferior. If it does NOT, the regex is a known false-positive generator: any script that prints the word "Error" or "Exception" to stderr as benign log output (very common) gets recorded as `exit:1`. Either way the field is untrustworthy as designed. Note also the `PostToolUseFailure` event exists separately — failures may not even reach `PostToolUse`.
**Concrete fix:** Spike the real PostToolUse `tool_response` for Bash (one debug hook dump). If `exit_code` present, use it directly and delete the regex. If absent, consider listening to `PostToolUseFailure` for the failure signal instead of regex-sniffing stderr. Do not ship the regex inference on assumption.

### H3 — "Hook clobber" risk is mis-modeled; the real risk (parallel-run + dedup semantics) is unaddressed.
**Claim attacked:** phase-01 §Risk L92 "Hook clobber (overwrite existing Stop/PostToolUse handler) → append-only, test existing hooks still fire."
**Why wrong (evidence):** Docs: "All matching hooks run **in parallel**, and identical handlers are deduplicated… by command string and args." So appending a Stop entry can NOT clobber the existing `session-state.cjs` Stop handler — they coexist and run in parallel. The plan spends a risk row + a red-team angle (L82 "Clobber") on a non-risk. The **actual** risks the plan misses: (a) parallel execution means no ordering guarantee between `emit-session-summary.cjs` and `session-state.cjs` — fine for append-only telemetry, but state any shared-file assumption; (b) the existing `Stop` array has ONE entry with NO matcher (settings.json L125-134) — appending a second hook object vs adding into the same `hooks:[]` array are different JSON shapes; pick one and test the registration parses.
**Concrete fix:** Drop the clobber framing. Replace with: "verify both Stop hooks run in parallel post-registration (docs: parallel+dedup); assert telemetry write is order-independent." Keep the JSON-shape registration test.

### H4 — Effort labels understate Phase 03; "M" should be "L", and the 7-phase split inflates a small scope.
**Claim attacked:** plan.md §Phases table — 03 = `M`; whole plan = 7 phases for a 3-skill repo.
**Why risky (evidence):** Given C2, Phase 03 = new harness + checker dispatch + add structured `check/extract` to 3 eval schemas (claude-pack from scratch) + 3 CI wirings + fixture tests + design-gate resolution. That is the heaviest item by far, not peer-"M" with the S phases. Meanwhile Phases 02 (doc-only ledger), 06 (doc-only STANDARDIZE, XS), 07 (red-team pass) are all light. Seven phase files for ~4 real code items (A1, A3, A4, P5-polish) + 2 docs is process overhead the repo's own KISS rule discourages.
**Concrete fix:** Re-label 03 `L`. Consider merging 02+06 (both doc-only) and folding 07's checklist into each phase's existing "Red-team angles" rather than a standalone phase — the inline red-team subsections already cover the invariants. If kept separate, that's defensible for the audit-trail demo, but flag it as a deliberate process choice not a scope necessity.

---

## MEDIUM

### M1 — Tarball-exclusion CI test verifies an invariant the whitelist manifest already guarantees; framed as "2 layers" but it's belt-on-belt, and the test as written is weak.
**Claim attacked:** phase-01 §Steps L60, §Risk L93 "gitignore + CI assert (2 layers)"; plan.md L68.
**Why (evidence):** Verified `pack.manifest.yaml` is **whitelist** (`schema_version, version, skills:[3], agents:[7], hooks:[2 .py], rules:[8], extra:[], top_level, follow_shared:false`). `.claude/telemetry/` is not in any list, and `apply_defaults`/`manifest_loader.py` only ever ADD whitelisted subtrees to `extra`. Telemetry cannot enter the tarball **by construction** — gitignore is irrelevant to packing (pack reads the manifest, not git). So the real guarantee is the whitelist (layer 1); the CI grep is a regression sentinel (layer 2); gitignore protects against *git commit*, a different threat, not tarball inclusion. The plan conflates these. Also `tar -tzf … | grep -q 'telemetry/' && fail` is a substring grep — a path like `skills/foo/telemetry/` (legit, hypothetical) would false-fail; and an empty/failed build would pass vacuously.
**Concrete fix:** Keep the CI sentinel (cheap, good), but re-frame: layer-1 = whitelist manifest (the actual guarantee), layer-2 = sentinel test. Make the assertion anchored (`grep -E '(^|/)\.claude/telemetry/'`) and assert the build produced a non-empty tarball FIRST (else vacuous pass). Drop "gitignore is a tarball layer" — it's a commit-hygiene layer.

### M2 — Phase 05 litmus "delete index → flagged set unchanged" is NOT mechanically testable in CI; it's aspirational against an LLM consolidator.
**Claim attacked:** phase-05 §Litmus L14-22, §TDD L65 "write a test over the bundle-assembly path asserting lens prompts contain NO repeat-count"; §Red-team L72 "run critique twice, with/without index, diff flagged set → must be identical".
**Why risky (evidence):** Two different tests are conflated. (a) "Lens prompts contain no repeat-count" IS mechanically testable — grep the assembled lens input strings; this is the real, enforceable guard, keep it. (b) "Run critique twice, diff flagged set, must be identical" is NOT CI-testable: the lenses + consolidator are LLM, non-deterministic by the skill's own charter (CLAUDE.md product-spec-critique: "opinion + web + voice = non-deterministic… never gates CI"). Two real runs will differ in wording regardless of the index. The boundary the plan actually wants — count never *enters* judgment — is enforceable only via (a). The consolidator IS an LLM (`critique-consolidator.md` L55 "Repeat-offense. If a current finding matches…") and *attaches* the annotation; nothing stops a future prompt edit from letting the count bleed into severity, and no deterministic test can prove it didn't.
**Concrete fix:** Keep test (a) as the litmus (grep lens-input assembly for absence of count/occurrence data — verified the plumbing exists: `critique_inherit.build_inherited_context`). DROP the "diff flagged set across two runs" as a CI test (it can't be deterministic); restate it as a manual red-team check in Phase 07. State plainly: the boundary is enforced by *input isolation* (count absent from lens prompts), provable; it is NOT enforced by output-stability, unprovable.

### M3 — `_gating` reuse aside, A4 option (b) test-location path-resolution is real and under-tested.
**Claim attacked:** phase-04 §Modify L41-42, §Red-team L68 — single test in `claude-pack/scripts/tests/` reaching all 3 skills via `parents[N]`.
**Why (evidence):** `cross-skill-bug-class.yml` (verified) runs `working-directory: .claude/skills/claude-pack` + `pytest scripts/tests -m bug_class`. A test there must resolve repo-root via `Path(__file__).resolve().parents[N]` (verify_skill_versions.py uses `parents[4]` — confirmed L73). The plan flags this but doesn't pin N. Off-by-one in `parents[N]` from a tests/ subdir (one level deeper than verify_skill_versions.py) → `parents[5]`, easy to get wrong → test reads nonexistent paths → either false-pass (if it skips missing) or crash.
**Concrete fix:** Pin it: test lives at `claude-pack/scripts/tests/test_version_sync.py` → repo root = `parents[5]` (one deeper than the script). Add the "runs in CI working-dir, not just local CWD" assertion the plan already lists. Reuse `verify_skill_versions._frontmatter` (DRY) as the plan says — good.

### M4 — Injection/newline red-team angle (phase-01 L80) is correct to flag, but `JSON.stringify` already escapes newlines — risk is overstated; the real risk is unsanitized `session` IDs or non-string record values.
**Claim attacked:** phase-01 §Red-team L80 "skill name / script path containing newlines… assert JSONL stays one-line".
**Why (evidence):** `appendFileSync(JSON.stringify(record)+"\n")` — `JSON.stringify` escapes `\n`→`\\n` and `"`→`\"` natively, so a crafted skill name cannot break JSONL line-integrity through the standard path. The angle is worth a confirming test but is low-risk if the helper uses `JSON.stringify` (the plan's `appendEvent` does, L37). The under-covered case: a record value that is not JSON-serializable (undefined, BigInt, circular) → `JSON.stringify` throws → fail-open swallows → silent data loss (acceptable) BUT verify the throw is inside the try.
**Concrete fix:** Keep the test but downgrade severity; add a case asserting non-serializable record → swallowed, op unaffected. Confirm `JSON.stringify` is the only serialization path (no manual string concat of fields).

---

## LOW

- **L1 — Read-back script "or jq snippets" (phase-01 L61, Todo L69):** KISS-correct to prefer jq, but "or tiny scan script" leaves it undecided → scope creep risk. Decide now: jq snippets in a doc, no new script, unless a counts/never-used view is explicitly wanted. The blueprint's `scan-skill-usage` has token-attribution the plan correctly drops.
- **L2 — `_shared/lib/telemetry-paths.cjs` placement (phase-01 L42):** consistent with existing `_shared/lib/plan-table-parser.cjs` (verified, required cross-skill). Fine. But note `.claude/hooks/*.cjs` (the 3 new hooks) are NOT in manifest `hooks:[]` (which lists only `memory_gap_hook.py`, `product_spec_critique_nudge.py`) → new telemetry hooks won't ship in the bundle. That's correct (CM-local dev tooling) but state it explicitly so a later reviewer doesn't "fix" it by adding them to the manifest (which would then need the tarball-exclusion test to also catch hook leakage).
- **L3 — Phase 03 `_shared/lib/run_evals.py` (Python) next to `_shared/lib/*.cjs` (Node):** mixed-language shared dir. Minor; just confirm the per-skill CI legs invoke it with the venv python (`CLAUDE.md`: use `.claude/skills/.venv/bin/python3`), not bare `python`.
- **L4 — No-plan-refs-in-code rule (review-audit-self-decision.md §5):** plan correctly avoids it in phase text, but remind implementers: test names must be `TestVersionSync_*` / `test_telemetry_disabled`, NOT `_A1`/`_A4`; the litmus test must not be named `test_litmus_phase05`.

---

## What the plan got RIGHT (risk calibration, not praise-padding)

- **Litmus input-isolation instinct (Phase 05)** is the correct boundary mechanism — keeping repeat-count out of lens prompts is genuinely testable and is the right place to draw the A9 line. The plan correctly refused the instinct-store learning loop.
- **Fail-open telemetry** is the right default for an observ­ability sink; "never break the observed op" is sound.
- **Whitelist manifest = safe-by-default** is correctly identified (even if the layer-framing in M1 is loose).
- **E5 decoupling awareness** (open-Q2) — the plan *noticed* bundle-tag ≠ skill-version and refused to add a manifest↔CHANGELOG equality. It just didn't follow through to realize this breaks A4's equality for claude-pack itself (H1).
- **DRY reuse of `verify_skill_versions._frontmatter`** for A4 is the right call.
- **TDD red-first discipline** per phase is well-specified; the "confirm the test fails for the right reason" instruction is exactly right.
- **Dropping args from telemetry** (no flag-value leak) and dropping token attribution (3-skill YAGNI) are good filtering of HA's heavier design.

## Verdict

**PROCEED-WITH-CHANGES.** Two hard gates before any code:
1. **C1 gate (Phase 01):** empirically verify the skill-invocation hook event in *this* Claude Code version; re-target off `PreToolUse:Skill` if it's phantom. Same spike resolves H2 (PostToolUse Bash exit shape).
2. **C2 gate (Phase 03):** reuse `_gating`, not new `kind`; accept claude-pack needs real reshape (=option ii) or defer it; re-scope effort to `L`.
Plus resolve **H1** (claude-pack CHANGELOG = bundle-versioned 1.4.0 vs skill 0.2.0 → A4 false-drift) with PO before A4 code. M-items are fix-in-flight. The plan's logic is mostly sound; its **false confidence is concentrated in ported-from-HA assumptions** (hook event names, eval schema shape) that don't hold against CM's actual runtime and files.

## Unresolved questions for PO / planner

1. **C1:** Does this Claude Code version fire any hook on Skill invocation, and under which event (`UserPromptExpansion` vs a `Skill` tool)? Needs a 5-min empirical spike, not a doc guess.
2. **H1:** Is `claude-pack/CHANGELOG.md` intentionally bundle-versioned (top `1.4.0`) while `claude-pack/SKILL.md` is skill-versioned (`0.2.0`)? If yes, A4's per-skill equality check must exclude or special-case claude-pack — confirm the intended invariant.
3. **C2/H4:** Given claude-pack evals are bare strings (no structured fields), is the PO OK spending Phase-03 effort to restructure them now, or defer claude-pack and ship only product-spec/critique `structural` subset?
4. **H2:** Should script-failure telemetry listen to `PostToolUseFailure` (distinct event) rather than stderr-regex on `PostToolUse:Bash`?
5. **M2:** Confirm the Phase-05 litmus is enforced solely by lens-prompt input-isolation (testable) and that the "two-run flagged-set diff" is downgraded to a manual Phase-07 check (not a CI gate).
