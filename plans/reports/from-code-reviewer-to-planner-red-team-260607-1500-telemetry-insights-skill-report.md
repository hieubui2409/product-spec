# Red-Team: telemetry-insights skill (cleanmatic:telemetry) + analyze_telemetry.py

Reviewer: code-reviewer (adversarial). Date: 2026-06-07.
Plan: `plans/260607-1500-telemetry-insights-skill/` (plan.md + 6 phases).
Posture: hostile, kill-or-shrink. Claims fact-checked against live repo, not plan text.

---

## VERDICT: **SHRINK** (hard) — drop to script-only ascii/md; cut the new skill, cut the HTML refactor, cut mermaid/html.

The plan is gold-plating a 1-line dataset. The single biggest defect is a **shipped-skill runtime breakage** (F1) that no phase and no gate catches. The "effectiveness" framing is a genuine mis-sell (F4). The data-volume problem is not a footnote — it's terminal for the headline feature (F2). Two of the three things the plan adds (new skill, HTML/mermaid render) fail YAGNI against a single local user. The packaging stance is *mostly* sound but rests on a fragile invariant the plan doesn't pin (F3).

What survives review: a ~60-LOC `analyze_telemetry.py --format ascii|md` that wraps the existing jq queries with a catalog cross-ref, output to the existing readback doc. Everything else is cut or deferred.

---

## FINDINGS

### F1 — [CRITICAL] Phase 1 ships a broken `render_html.py` (import to an un-bundled module). The guard that should catch it is blind to Python.

Phase 1 makes the **SHIPPED** `product-spec/scripts/render_html.py` `import` from `_shared/lib/html_render_helpers.py`. Verified facts:

- `render_html.py` is currently self-contained: sibling-dir imports only (`spec_graph`, `i18n_labels`, `fs_guard`), all live in `product-spec/scripts/` (verified). No `_shared` dependency today.
- `_shared/` is **NOT bundled**: manifest has `follow_shared: false` and empty `_include_shared`; `selection.py:37-44` only walks `_shared/<slug>` when `_include_shared` lists it (verified). So the tarball ships `render_html.py` but NOT `html_render_helpers.py`.
- The leak guard `safety_check.find_shared_refs()` greps **`SKILL.md` only**, with fenced code stripped, for the literal token `_shared/<name>` (verified `safety_check.py:58-78`). It does **not** scan `.py` source. A Python `import` from `render_html.py` is invisible to it. `--strict` would not fire. CI (`release-ci.yml`) runs `--dry-run` without `--strict` anyway.

**Result:** recipient unpacks the bundle, runs `--format html` in product-spec, gets `ModuleNotFoundError: html_render_helpers`. A shipped skill is broken by a refactor done for a never-shipped local tool. The blast radius is exactly backwards from the plan's "local-only, low risk" framing.

Phase 1's snapshot test only proves byte-identical HTML **on the dev machine where `_shared/` exists**. It cannot catch the missing-module-in-tarball failure because it never builds + unpacks + runs the tarball. The "behavior-preserving" success criterion is satisfied while the shipped artifact is broken — a textbook phantom-safety test.

**Fix:** Do NOT extract from shipped `render_html.py`. Two real options:
- (a) **Don't share.** `analyze_telemetry.py` reads the 3 vendored asset paths with a ~15-line local inliner (the plan's own "Option B fallback" in Phase 1 risk box). One tiny dup of a thin `escape`/`load`/`substitute` is cheaper than a cross-skill coupling that the bundler can't see. This is the YAGNI-correct call. (Best: just drop HTML — see F5.)
- (b) If sharing is truly wanted later, it must be paired with: add `html_render_helpers` to `_include_shared`, AND extend `find_shared_refs` to scan `.py`, AND add a real tarball-unpack-import test. That is a separate, larger plan — not a sub-task of a telemetry tool.

---

### F2 — [CRITICAL] The headline feature ("how are my skills doing") runs on a 1-line dataset. Adoption analytics are vacuous for one user.

Measured live (not estimated):
- `invocations.jsonl`: **1 line**
- `sessions.jsonl`: 13 lines
- `hook-telemetry.jsonl`: 52 lines

The plan's whole "adoption" pillar — per-skill invocation counts, `via` split, never-invoked → prune candidates, co-occurrence pairs — is computed from `invocations.jsonl`. With one record, "top skill", "never used", "prune candidate" are all noise. The research already flagged `Skill` tool_use ≈ 0.17% of records; the live sink confirms it's not 0.17% of a big number, it's literally one event. The narrated "ứng viên prune" recommendation, presented to a non-technical PO, will be confidently wrong (it will flag ~every skill as "never invoked").

The deferred per-skill duration/token work (D5) is deferred *for the right reason* (sparse). But the plan keeps the equally-sparse **adoption** layer in scope and builds a whole skill around narrating it. That's inconsistent: same sparsity, opposite decision.

**Fix:** Either (a) gate the narration on a minimum-volume threshold ("not enough data yet — N invocations recorded; check back after more usage") so it doesn't manufacture false prune advice, OR (b) drop the prune/adoption-ranking judgment entirely and keep only the two layers with non-trivial volume (session shape n=13, script error-rate n=52). The honest MVP is "session activity + script error hotspots", NOT "skill effectiveness".

---

### F3 — [HIGH] Bundle-exclusion holds *today* but the plan doesn't pin the invariant that keeps it true; and `analyze_telemetry.py` location undercuts the "skill not in manifest" guard.

D3/Phase 5 claim "omit from manifest whitelist = never shipped". For the **skill dir** (`skills/telemetry/`) that's correct and verified (selection walks only `manifest.skills`). But:

- The **script** lives in `_shared/scripts/analyze_telemetry.py`, not in `skills/telemetry/`. Phase 5's exclusion test asserts `skills/telemetry/` ∉ tarball — it says nothing about `_shared/scripts/analyze_telemetry.py`. Today `_shared` isn't bundled, so it's fine. But the moment anyone sets `follow_shared: true` or adds an `_include_shared` entry (plausible if F1's "share the helper properly" path is ever taken), `_shared/scripts/` gets walked and the telemetry script ships. The plan's exclusion test would stay green while the script leaks.
- gitignore (D4): the re-include lines are correct and `git check-ignore` confirms the new `skills/telemetry/` dir is currently ignored by `/.claude/skills/*` (verified — the force-add step is genuinely required, not hand-wavy). Good. But note `_shared/**` is *already* re-included (`.gitignore:171`, verified) so the new `analyze_telemetry.py` is auto-tracked there — the plan's D4 force-add ceremony applies only to the skill dir, which the plan does state. OK.

The A4 stance (add to `DEFAULT_SKILLS`, not `VERSION_SYNCED_SKILLS`) is **coherent** and matches the verified gate semantics (format check vs sync check). The dedicated "assert telemetry is exempt" test (Phase 5 step 3) is the right move to prevent the maintenance trap. No objection there.

**Fix:** Phase 5's tarball regression test must ALSO assert no `_shared/scripts/analyze_telemetry.py` (and no `_shared/lib/telemetry_*`) member, independent of manifest state. Pin the invariant against the file path, not just the manifest list. And add an assertion that `find_shared_refs` finds no telemetry ref leaking via SKILL.md.

---

### F4 — [HIGH] "How EFFECTIVE are my skills" is a bait-and-switch. The skill measures adoption + coarse error-rate; it cannot measure effectiveness, and the honesty gate is a band-aid on a mis-named product.

The skill is sold to the PO (plan.md line 19, Phase 4) as answering "hiệu quả ra sao?" / "how effective". E3 (true outcome) is explicitly OUT (correct — product not in market). So the skill ships promising a question it structurally cannot answer. The "honesty gate" (Phase 4) tells the PO *inside the output* "I can't actually measure effectiveness yet". That's not a save — it's an admission that the framing is wrong. You don't ship a feature named X whose first sentence is "this does not do X".

This is worse for a non-technical PO than for an engineer: the PO asked the question precisely because they want effectiveness, and the tool's name validates the expectation before the caveat walks it back.

**Fix:** Rename the value prop honestly. It's a **usage/activity report**, not an effectiveness report: "skill nào tôi hay dùng, script nào hay lỗi, phiên làm việc của tôi trông thế nào". Drop "effectiveness/hiệu quả" from the name, description, and pitch until E3 (or the cheap validate-pass proxy) actually exists. If the PO specifically wants effectiveness, that's a signal to scope the proxy — not to mislabel an adoption report. Surface this to the PO as a Keep/Change decision; do not let the plan ship the effectiveness framing on the strength of a caveat.

---

### F5 — [HIGH] HTML + mermaid render is YAGNI for one local user. ascii/md already covers it; HTML is the most expensive format and the one that triggers F1.

Phase 3 builds md + mermaid + a 2.6MB-inlined self-contained HTML page. For a **single local user** reading their own telemetry:
- ascii prints in-terminal (zero deps). md drops into the existing `docs/audit-trail/` doc. Those two cover 100% of the realistic "let me look at my numbers" need.
- mermaid/html add the entire vendored-asset reuse problem (F1), the 2.6MB-bundle concern, the shell-template-reuse risk (Phase 3 risk box admits the shell "may not generalize"), and 3 extra snapshot test suites — to draw a pie chart of, currently, one invocation.

The plan even concedes the slippage: Phase 1 says "marked/purify loaders included only if a render actually needs them (defer if not)" — apply that same YAGNI one level up: **html/mermaid aren't needed at all this round.**

**Fix:** Cut Phase 3 entirely (or reduce to `--format md`). Ship ascii + md only. Revisit charts if/when (a) data volume justifies a chart and (b) a real shared-render path exists. This also dissolves F1 (no `_shared` HTML coupling needed).

---

### F6 — [MED] Steelman of "do almost nothing" — the plan never honestly competes against it.

Cheapest options, in order:
1. **Doc-only (zero code):** the existing `telemetry-readback.md` already has the 5 jq one-liners and already says "compare against the skills catalog manually". Add one more jq line for never-invoked (diff catalog vs `jq -r .skill`). Cost: 3 lines of doc. Delivers the same answer the script's "adoption" layer would, for one user.
2. **Script-only ascii/md (no skill):** `analyze_telemetry.py` ~60 LOC wrapping the jq logic + catalog diff, ascii/md out. The PO runs one command. No SKILL.md, no narration layer, no packaging dance, no A4 edits, no gitignore edits. ~1/4 the plan's surface.
3. **Full plan (6 phases):** new skill + new shared module + HTML/mermaid + packaging guards + refactor of shipped code.

The plan jumps to (3). The value delta between (2) and (3) for ONE non-technical user is: Vietnamese narration. That is real (the PO is non-technical) — but it argues for a thin *prompt/reference*, not a whole packaged skill with CHANGELOG, version, A4 wiring, and bundle-exclusion tests. The narration can be a markdown reference the PO's agent reads after running the script. Most of Phase 4/5's ceremony is justified only by the decision to make this a first-class *shipped-contract* skill — which it explicitly is NOT (it's never shipped).

**Fix:** Default to option (2)+thin-narration-doc. The "skill" overhead (versioning, A4 `DEFAULT_SKILLS`, bundle-exclusion test, gitignore force-add) is pure cost for a never-shipped local tool. If the PO insists on `/cleanmatic:telemetry` ergonomics, a minimal SKILL.md is fine — but drop the version-sync/CHANGELOG ceremony (the plan already exempts it from `VERSION_SYNCED_SKILLS`, which is a tell that the skill-shaped packaging is a poor fit).

---

### F7 — [MED] Hidden phase coupling: Phases 2-4 all depend on F2's data being meaningful; success criteria are mostly untestable as written.

- Phase 4 SC "narration reads naturally for a non-tech PO in Vietnamese" and "recommendations are sane" are **not testable** — they're LLM-prose judgments with no oracle. Phase 4 step 3 ("dry-run manually, does it read correctly?") is the only check, and it runs against the 1-line sink (F2), so "sane recommendations" will be tested against vacuous data.
- Phase 6 depends on Phase 5 which depends on 4→3→2→1. The whole chain is serial; F1 (Phase 1) or a SHRINK verdict invalidates 2-6. The plan's Phase 6 step 1 literally lists "is the skill justified vs jq scope-creep?" as a finding to triage AFTER building phases 1-5. That's backwards — the scope-creep question is a gate, not a closeout item. Running `--hard` at Phase 6 is too late; the verdict (this report) should land before Phase 1.

**Fix:** Move the scope decision (this report) to a pre-Phase-0 gate. Make Phase 4 narration SC concrete: assert the output *contains* the honesty caveat string and a volume-warning when n < threshold (testable), drop "reads naturally" as a CI criterion (it's a review-time human check, not a gate).

---

### F8 — [LOW] Missing NFRs.

- No statement on what happens when `telemetry_dir()` is empty/absent on a fresh machine (fail-soft is claimed for *corrupt lines* but the all-empty case → narration of zeros → "all skills are prune candidates"). Tie to F2's volume gate.
- No cap on output size / no `--since` default — on a long-lived machine `sessions.jsonl` grows unbounded; ascii table of all-time could be large. Minor for now (13 lines) but unspecified.
- `_spike.jsonl` (203 lines) exists in the telemetry dir but isn't in the documented 3-sink contract — the aggregator must ignore unknown sinks explicitly or it'll trip on it. Not mentioned in any phase.

---

## TOP-3 MUST-FIX (in order)

1. **F1 (CRITICAL):** Do not refactor shipped `render_html.py` to import from un-bundled `_shared/`. The bundler's leak guard can't see Python imports — you'd ship a broken skill. Drop the shared-HTML extraction; if HTML survives at all, use a local inliner.
2. **F2 (CRITICAL):** Don't narrate adoption/prune judgments off a 1-line sink. Add a volume gate or cut the adoption-ranking layer. Keep only session-shape + error-rate (the layers with real n).
3. **F4 (HIGH):** Stop calling it "effectiveness". Rename to a usage/activity report and surface the framing change to the PO as a Keep/Change decision. A caveat inside the output does not fix a mis-named product.

## RECOMMENDED RESHAPE (if proceeding)

- Phase 1: cut HTML extraction → 15-line local inliner OR drop HTML.
- Phase 2: keep (aggregation + ascii) — but add empty/low-volume handling and ignore unknown sinks.
- Phase 3: cut (no mermaid/html) or reduce to `--format md`.
- Phase 4: downgrade "skill" to a thin narration reference invoked after the script; drop effectiveness framing; concrete testable SCs only.
- Phase 5: keep the A4 `DEFAULT_SKILLS` + bundle-exclusion tests ONLY if a real SKILL.md ships; add the `_shared/scripts/analyze_telemetry.py`-path exclusion assertion (F3).
- Phase 6: move the scope/`--hard` gate to BEFORE Phase 1; keep deferred-decision recording.

Net: ~2 phases of real work, not 6.

---

## UNRESOLVED QUESTIONS

1. Does the PO actually want charts (mermaid/html), or is that Claude-proposed gold-plating? If PO never asked for visual charts, F5's cut is safe; if they did, confirm before keeping HTML (and accept F1's cost).
2. Is `/cleanmatic:telemetry` ergonomics (a slash-invocable skill) a hard PO requirement, or would "run this one script + read the narration doc" suffice? Determines whether F6's skill-overhead is justified.
3. Will telemetry data volume ever realistically grow for this single local user, or is adoption analytics permanently vacuous here? If permanently low-volume, the entire adoption pillar should be cut, not just gated.
4. Was the "effectiveness" framing the PO's word or the plan author's? If the PO literally asked "how effective", that's a real unmet need pointing at the validate-pass proxy — escalate as a separate slice rather than mislabeling this one.
