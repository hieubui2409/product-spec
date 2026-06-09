# Changelog

All notable changes to **cleanmatic:product-spec-critique** are documented here. This is the human
changelog for the skill; it is NOT the source of the bundle's GitHub Release notes (those stay
auto-generated from commits by `claude-pack-release.yml`). The skill's release identity is its
frontmatter `metadata.version` in `SKILL.md`, verified at release time by
`claude-pack/scripts/verify_skill_versions.py`.

Format: [keepachangelog.com](https://keepachangelog.com/en/1.1.0/). Versioning: [semver](https://semver.org/).

## [Unreleased]

## [1.2.1] — 2026-06-09

### Changed
- **SKILL.md flag-table compaction (per-turn context flow).** Compacted the `--level 1..9` (the
  biggest row) and `[scope]` rows to one crisp `what · when · see <ref>` line each, relocating the
  elaboration into `references/voice-and-tone.md` (which already homes the nine levels, the danger
  gate, the register config, and the universal-harm floor). SKILL.md token proxy **3820 → 3677
  (−3.7%)**. Every safety-critical fact kept inline: the 6-9 danger gate, level-9
  re-confirm-every-run + downgrade-to-8, and the universal-harm floor at all levels. Routing
  preserved (best-of-3 sub-agent judge: `route-level` + `route-scope` HELD).

### Added
- **Routing-selection eval scenarios** (`eval/evals.json`, `route-level` + `route-scope`) —
  ambiguous-ask probes gating flag/scope-selection reasoning; sub-agent-judged (advisory), never
  the deterministic gate.

## [1.2.0] — 2026-06-06

### Changed
- **Finding-level fingerprint (N1).** The findings-index now carries a per-finding
  `finding_fingerprint` = `sha256(node + severity + normalize(cited spec-line text))`,
  anchored to the deterministic spec text a finding cites (not the LLM `why` prose, not the
  line number). Inherit + descendant-rollup dedup by fingerprint (falling back to
  `evidence_id`), so a logical blocker re-critiqued after a line shift is counted once
  instead of inflating the rollup. Additive + back-compatible: legacy rows without the field
  degrade to `evidence_id` keying; a structural/unresolvable cited line (`---`, BRD-goal
  frontmatter fence) yields a null fingerprint → `evidence_id` fallback, never a false merge.
  Leading list numbers are kept as content so numbered siblings (`3. X` vs `7. X`) stay
  distinct. LLM consolidator repeat-offense (prior-reports) is unchanged.

## [1.1.0] — 2026-06-04

### Changed
- **Renamed the skill `spec-critique` → `product-spec-critique`** (the `agent-naming-conventions` work).
  Invoke it as `cleanmatic:product-spec-critique` / `/product-spec-critique` now. The skill directory,
  `SKILL.md`, the `pack.manifest.yaml` entry, and the bundle changelog references were all updated.
- **Renamed the 6 lens/consolidator sub-agents to an actor-noun convention:**
  `spec-critique-product` → **`product-critic`**, `spec-critique-tech` → **`tech-critic`**,
  `spec-critique-market` → **`market-critic`**, `spec-critique-craft` → **`craft-critic`**,
  `spec-critique-consolidate` → **`critique-consolidator`**, `spec-critique-humanize` →
  **`critique-humanizer`** (in `.claude/agents/`; all cross-references updated).
- **Renamed the Stop-hook** `spec_critique_nudge.py` → **`product_spec_critique_nudge.py`**.
- **Assumption-rigor in existing lenses** — the product **Riskiest-assumption** and tech
  **Hidden-dependencies / assume-success** lens prompts now require an explicit
  "unproven belief X → if wrong, Y happens" consequence clause (name the assumption AND its failure),
  not just that an assumption exists. Prompt/reference edit only — no new lens, agent, or flag; the
  consolidator's N<4 tolerance and the lens flag set are unchanged.

## [1.0.0]

Prior shipped baseline. History below reconstructed from `feat(spec-critique)`/`fix(spec-critique)`
commit subjects traced through the `spec-critique` → `product-spec-critique` rename (`git log --follow`),
not a raw path log.

### Added
- 4-lens critique (product/tech/market/craft) via read-only sub-agents + an opus consolidator + a
  humanizer pass; one markdown report per run; never edits the spec, never gates CI.
- **Voice ladder, levels 1..9** with the universal harm-floor; register knobs (gender/dialect/profanity)
  hard-gated to levels 7-9; split `detail_level` preferences.
- **Lifecycle caching + provenance reuse** (`none`/`full`/`consolidate_only`/`relens`) + cross-critique
  inheritance (parent→child `inherited_context`) and descendant rollup (child→parent).
- Voice-neutral lenses + orchestration wiring.
- Advisory en-language-purity check for reports.

### Changed
- Bilingual-output hardening: render `lang: en` reports fully in English (Vietnamese-leak fix); a
  concrete "sustained profanity" floor so the English level-9 outscales level 8.
- Recorded the lens-per-language design decision in `voice-and-tone`.
