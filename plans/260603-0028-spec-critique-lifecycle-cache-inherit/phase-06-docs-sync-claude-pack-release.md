---
phase: 6
title: "Docs sync + claude-pack release"
status: completed
priority: P2
effort: "0.5d"
dependencies: [5]
---

# Phase 6: Docs sync + claude-pack release

## Overview

Land the user-facing documentation for the new lifecycle/cache/inheritance behavior in BOTH the root docs and the in-skill docs, then prepare the claude-pack release (version bump + CHANGELOG). No code; sync only. Last phase — runs after the behavior is proven (P5).

## Requirements

- **Root docs:**
  - `README.md` (spec-critique section): add the new flags + a one-line each on caching/inheritance/rollup; keep PO-friendly tone (it's a PO-facing section). Do not over-explain the cache internals.
  - `CLAUDE.md` (root, "Spec-Critique — LLM Operating Guide" block): extend the **Workflow pointers** table + add the new flags, the 3 new preferences, the new bundle keys (`provenance`/`inherited_context`/`descendant_rollup`), and the "lens ignores inherited_context" + "inherited not in tally" invariants. Cross-check that the existing `critique_detail_level` vs `detail_level` note stays correct (already present).
- **In-skill docs:**
  - `.claude/skills/spec-critique/README.md` (Flags table): add `--fresh`/`--force`, `--refresh-web`, `--no-inherit`, `--no-rollup`, `--inherit deep` (use the space form in all user-facing docs).
  - `.claude/skills/spec-critique/SKILL.md`: already touched in P4 for the flag surface/bundle contract — here just verify it's complete + consistent with README (no drift).
  - `.claude/skills/spec-critique/GUIDE-VI.md` + `GUIDE-EN.md`: add a sample conversation for each new use-case (natural-language way preferred + flag equivalent): "re-critique after editing one story" (relens), "make it harsher without re-running the analysis" (consolidate_only via level bump), "ignore the parent's prior findings" (`--no-inherit`), "force fresh" (`--fresh`), "refresh competitor research" (`--refresh-web`). Bilingual parity.
  - Confirm `install.sh`/`install.ps1` need NO change (caches are runtime `.memory/` files created on demand — research confirmed; just re-verify no new install-time dir/registration).
- **claude-pack release prep:**
  - `.claude/pack.manifest.yaml`: bump `version: 1.1.0` → `1.2.0` (minor: backward-compatible feature add, defaults preserve current behavior). Confirm NO file-list edit needed — skills are enumerated by name, new `critique_cache.py`/`critique_inherit.py` (+ any `critique_provenance.py`) ship automatically as part of the `spec-critique` skill dir. The PO's `docs/product/.memory/critique-*.json` are the consumer's project data, not skill files → never in the bundle regardless of git status. (Note: in THIS repo `.memory/` IS committed for e2e fixtures — that's repo git policy, distinct from what claude-pack ships. Do NOT repeat the earlier false "gitignored runtime data" phrasing.)
  - `.claude/skills/claude-pack/CHANGELOG.md`: add a `1.2.0` entry (keepachangelog, the bundle changelog covers both skills) under **Added** — list: lifecycle caching (findings-index, web-url+TTL, critique-state, humanized-output, **lens-findings cache**), provenance reuse + report frontmatter, cross-critique inheritance (parent→child) + descendant rollup (child→parent), new flags (`--fresh`/`--force`, `--refresh-web`, `--no-inherit`, `--no-rollup`, `--inherit deep`), IN/OUT-of-override table. **Also note the product-spec touch** (R2): 3 new critique preferences registered in `product-spec/preferences.py` — the entry spans both skills, not spec-critique-only.
  - **Do NOT build/tag/publish in this plan.** Per CLAUDE.md the release is tag-triggered CI: bump + CHANGELOG + commit + push `master` + push annotated tag `claude-pack-v1.2.0` is a SEPARATE, explicit human step. This phase only stages the version bump + CHANGELOG so the tag push is ready. Surface this clearly to the PO.
- **"Check if claude ship needs update" (the user's ask):** the answer the plan encodes — the `ship`/release flow itself does NOT change (tag-triggered CI, reproducible build, `softprops/action-gh-release`). The ONLY release-side deltas are the version bump + CHANGELOG entry; the workflow yml, installer, and manifest file-list are untouched. State this conclusion in the phase report.

## Architecture

Documentation + metadata only. The single sources of truth: flags live in argparse (P2/P3) + SKILL.md; the harm floor + override boundary live in voice-and-tone.md (P4). README/GUIDE/CLAUDE all *reference* those, never redefine. DRY: do not paste the IN/OUT-of-override table into multiple docs — link to voice-and-tone.md.

## Related Code Files

- Modify: `README.md` (root), `CLAUDE.md` (root)
- Modify: `.claude/skills/spec-critique/README.md`, `SKILL.md`, `GUIDE-VI.md`, `GUIDE-EN.md`
- Modify: `.claude/pack.manifest.yaml` (version bump only)
- Modify: `.claude/skills/claude-pack/CHANGELOG.md` (1.2.0 entry)
- Verify-no-change: `.claude/skills/spec-critique/install.sh`, `install.ps1`, manifest file lists
- Read for context: P2-P4 final flag/preference/bundle-key set, existing CHANGELOG format, existing GUIDE sample-conversation style

## Implementation Steps

1. Collect the final canonical flag/preference/bundle-key list from the shipped P2-P4 code (grep argparse + preferences keys) so docs match reality exactly.
2. Edit root `README.md` + `CLAUDE.md`; edit in-skill `README.md`, `SKILL.md` (verify), `GUIDE-VI.md`, `GUIDE-EN.md` with bilingual sample conversations.
3. Verify installer + manifest file-list need no edit; bump manifest version 1.1.0→1.2.0.
4. Add the `1.2.0` CHANGELOG entry (Added section, both-skills bundle).
5. Final cross-doc consistency pass: every flag appears identically in argparse ↔ SKILL.md ↔ README ↔ GUIDE; no ghost flags; harm-floor table not duplicated.

## Success Criteria

- [ ] Root `README.md` + `CLAUDE.md` document the new flags, preferences, bundle keys, and the lens-blind + no-tally invariants.
- [ ] In-skill `README.md`/`SKILL.md`/`GUIDE-VI.md`/`GUIDE-EN.md` updated with bilingual sample conversations for every new use-case; flag names consistent everywhere.
- [ ] `pack.manifest.yaml` bumped to `1.2.0`; confirmed no file-list edit needed; installer untouched.
- [ ] `CHANGELOG.md` has a complete `1.2.0` Added entry covering the 5 caches (incl. lens-findings cache) + inherit + rollup + flags + the lens voice-neutralization (R6) + the product-spec preferences touch (R2).
- [ ] Conclusion recorded: the release/ship flow is unchanged except version+CHANGELOG; tag push is a separate human step (NOT done in this plan).
- [ ] No DRY violation: harm-floor / override table linked, not copied.

## Risk Assessment

- **Risk: docs drift from the actual shipped flag names.** Mitigation: step 1 derives the list from code, not memory; step 5 cross-doc parity pass; the post-plan consistency sweep re-checks.
- **Risk: accidental release (tag) from this plan.** Mitigation: explicitly OUT of scope — this phase only stages bump+CHANGELOG; the human pushes the tag. Called out in success criteria.
- **Risk: version bump semantics.** Mitigation: minor (1.2.0) is correct — additive, backward-compatible, defaults preserve old behavior. Not a breaking change (no patch-only either, since it's a feature).
- **Risk: CHANGELOG covers both skills but this is spec-critique-only.** Mitigation: that's the established convention (bundle changelog); scope the entry to spec-critique items but keep it in the shared file.
