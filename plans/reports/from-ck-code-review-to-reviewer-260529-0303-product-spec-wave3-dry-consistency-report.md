# Product-Spec Wave-3 DRY / Consistency Review

Scope: SKILL.md ↔ references/*.md ↔ assets/templates/*.md ↔ scripts/*.py ↔ examples/ ↔ scripts/tests/fixtures/. Skill is DRY-driven; this audit hunts surfaces that disagree about the same fact.

## DRY / Consistency Findings (NEW only)

### CRITICAL — contradiction breaks the contract

**1. `type` enum is missing `exec_summary` — template emits a value the spec rejects.**

- Spec (authoritative): `references/frontmatter-and-id-spec.md:25` defines the `type` enum as `vision, product, brd, prd, epic, story, goal`.
- Template: `assets/templates/exec-summary.md:7` emits `type: exec_summary`, and the renderer wires `id: EXEC-SUMMARY`.
- Generator: `scripts/generate_templates.py:50,62,122` references `exec_summary` and synthesizes the ID.
- Script bypass: `check_consistency.py:40-47` ENUMS dict only covers `status/scope/moscow/horizon/size/lang` — `type` is never validated, so the contradiction silently lands as valid frontmatter that breaks the documented schema. Any tightening of `check_consistency` to validate `type` will reject every generated exec-summary.
- Authority: the spec (`frontmatter-and-id-spec.md:25`) is the source of truth; either add `exec_summary` to the enum OR drop the `type` field from the exec-summary template.

**2. BRD goal `owner` is documented as required but every authored goal omits it.**

- Spec: `references/frontmatter-and-id-spec.md:88` — "`owner: Jane Doe # required, accountable person`".
- Example: `examples/acme-shop/docs/product/brd.md:11-18` — both `BRD-G1` and `BRD-G2` have no `owner` key per goal (only document-level `owner` at line 6).
- Test fixture (valid-spec): `scripts/tests/fixtures/valid-spec/docs/product/brd.md:10-19` — both goals lack `owner` per goal.
- Test fixture (broken-spec): `scripts/tests/fixtures/broken-spec/docs/product/brd.md:11-19` — same omission.
- BRD template inline-comment: `assets/templates/brd.md:14-27` — the example block correctly shows the `owner` field per goal, so the template IS consistent; only the fixtures + example artifacts drift.
- Script gap: `spec_graph.py:105-115` (`_node_from_goal`) reads `owner` from each goal dict; if the spec is tightened to enforce required-field validation, all fixtures fail. Today no script flags the missing field, so the drift is invisible.
- Authority: spec is right; fix the example and both fixtures, OR loosen the spec to say "owner: optional".

**3. `visualize.py` delta flag name diverges from the spec's documented flag.**

- Spec (authoritative): `references/visualization-spec.md:25,104` — "`--viz delta [--snapshot <name>]`" / "`--viz delta --snapshot <name>     # explicit baseline`".
- Script: `scripts/visualize.py:101` exposes `--diff`, not `--snapshot`. The help string and inline docstring (`visualize.py:11`) say `--diff`.
- LLM workflow impact: a workflow that follows the spec literally and emits `--snapshot foo.json` will get argparse `unrecognized arguments` and the delta render never runs.
- Authority: pick one. Either rename the CLI to `--snapshot` (matches the spec) or update `visualization-spec.md` lines 25 and 104.

**4. CLAUDE.md lists `parent` as a frontmatter key, but `parent` is never written into any artifact frontmatter.**

- CLAUDE.md (repo-root, line 65): "Frontmatter keys stay English regardless of `lang`: `personas`, `metrics`, `moscow`, `scope`, `horizon`, `status`, `owner`, `parent`, `prd`, `epic`, `brd_goals`, …".
- Spec: `references/frontmatter-and-id-spec.md:43` — "BRD goals do not carry an explicit `parent` field"; the parent-link table at lines 37-41 uses only `epic`, `prd`, `brd_goals`.
- Script: `scripts/spec_graph.py:115` synthesizes `parent: "BRD"` IN-MEMORY on goal nodes only — never written to any artifact frontmatter.
- Authority: spec is right; remove `parent` from the CLAUDE.md frontmatter-key list. Otherwise an LLM following CLAUDE.md will try to write a `parent:` field that nothing reads.

### HIGH — silently confusing

**5. `validation-rules-spec.md` says "Scripts ALWAYS exit 0" but `strict_gate.py` exits 2.**

- Spec: `references/validation-rules-spec.md:50` — "Scripts ALWAYS exit 0. The LLM (orchestration layer) decides what to do with severities; `--strict` gating is the LLM's job, not the script's."
- Repo-root CLAUDE.md:96: "Scripts emit JSON to stdout. Scripts always exit 0. `--strict` gating is your job, not the script's."
- Script: `scripts/strict_gate.py:34-35,73` defines `EXIT_OK = 0` and `EXIT_BLOCKED = 2` and exits non-zero on any error finding. This is intentional for CI use — and `workflow-validate.md:17-22` correctly documents it.
- Contradiction: the always-zero invariant in `validation-rules-spec.md` and CLAUDE.md is broken by an intentional exception. Fix the spec to carve out `strict_gate.py` as the documented exception, OR rename the script so the rule "checkers exit 0" still holds.
- Authority: workflow-validate.md is the most recent operational doc; the structural-only invariant in validation-rules-spec.md needs an explicit "except strict_gate.py".

**6. Three implemented check IDs are not in the spec catalog.**

- Implemented (in `scripts/check_consistency.py`): `invalid_type` (line 111), `persona_cap_exceeded` (line 125), `session_md_gitignored` (line 176).
- Spec catalog (`references/validation-rules-spec.md` lines 18-37) — none of the three appear.
- Tests confirm these are emitted: `scripts/tests/test_scripts.py:212-258, 306-368`.
- Impact: an LLM consuming the findings JSON sees a `check` value it has no message template for. The auto-generated human report (`workflow-validate.md:36-46`) cannot describe what failed.
- Fix: extend the catalog rows in `validation-rules-spec.md` (with severity + message template).

**7. Documented `version_inconsistency` check is unimplemented.**

- Spec: `references/validation-rules-spec.md:31` defines `version_inconsistency` (warn) — "child `version` higher than parent (rare; flag only)".
- Implementation: no occurrence in any script (grep across `scripts/*.py` returns zero).
- Fix: either implement the check or strike the row from the catalog. Today the catalog over-promises.

**8. Vision template omits `horizon` deliberately, but SKILL.md + CLAUDE.md still advertise it as part of vision; example vision.md USES it.**

- Template (correct): `assets/templates/vision.md:17-22` — inline comment "vision.md intentionally omits `horizon`. The horizon enum (now/next/later) describes WHEN work happens; vision is timeless strategy." V6 in `interview-vision.md:64-67` confirms this.
- Repo-root CLAUDE.md:172: "`vision.md             (narrative vision + personas + north-star + horizon)`".
- SKILL.md:68: same text — "narrative vision + personas + north-star + horizon".
- Example artifact: `examples/acme-shop/docs/product/vision.md:10` has `horizon: now` in its frontmatter — exactly the value the template comment says to never collect.
- Impact: a fresh `--product` init via `generate_templates` correctly omits `horizon` from vision.md. But an LLM that reads CLAUDE.md/SKILL.md before regenerating the example writes the wrong shape back. The example artifact will fail an `unknown_enum`-style check IF `horizon` ever drifts off the closed enum (it doesn't fail today because `horizon: now` is a valid value).
- Authority: vision template's inline rationale is right. Fix CLAUDE.md:172, SKILL.md:68, and `examples/acme-shop/docs/product/vision.md:10` (drop horizon).

### MEDIUM — minor drift

**9. `sign-off.md` template carries `{{approval_notes}}` and `{{open_issues_at_approval}}` tokens not modeled in the approval block schema.**

- Spec: `references/frontmatter-and-id-spec.md:117-122` — approval block is exactly `approved_by`, `approved_at`, `approved_version`. No notes, no open_issues fields.
- Template: `assets/templates/sign-off.md:19,22-23` references `{{approval_notes}}` and `{{open_issues_at_approval}}` — these are body-level, not frontmatter. Token substitution at `generate_templates.render` (scripts/generate_templates.py:139-158) defaults missing tokens to `"TBD"`, so a vanilla `--approve` will emit `**Notes | Ghi chú:** TBD` and `> Open issues at approval time (warn-not-block): TBD`. Cosmetic but suggests the spec should explicitly document body-level approval tokens.
- Fix: add a body-token enumeration to the sign-off section of `frontmatter-and-id-spec.md` (or to a new "approval-output-tokens" reference), OR drop the two tokens from the template.

**10. `interview-brd.md` describes B3/B4 targets as frontmatter fields that don't exist.**

- `interview-brd.md:28-30` — "**target:** `brd.md → metrics`".
- `interview-brd.md:36` — "**target:** `brd.md → stakeholders`".
- `interview-brd.md:50` — "**target:** `brd.md → market`".
- BRD template (`assets/templates/brd.md` frontmatter, lines 6-29) has none of these as YAML keys — they are body sections only (`{{stakeholders}}`, `{{market_context}}`, `{{metrics_section}}`). Other interview banks use the same "target → frontmatter" convention precisely (`interview-prd.md:5,21,40`), so the inconsistency is surprising.
- Fix: change to "target: `brd.md → Stakeholders section`" (and same for market, metrics) to match the body-section convention, OR add the keys to the BRD frontmatter schema.

**11. BRD template frontmatter omits `personas` but spec lists `personas` as a domain field with no per-artifact restriction.**

- Spec: `references/frontmatter-and-id-spec.md:49-54` describes `personas` as a domain field; nothing restricts it to PRD/epic/story.
- BRD templates and examples never carry `personas` — but PRODUCT.md does, and the LLM is told to subset.
- Not necessarily wrong; the spec just doesn't say BRD opts out. Document that BRD has no `personas` field explicitly in the frontmatter table.

**12. `examples/acme-shop/docs/product/visuals/tree.md` is representative but stale title-rendering for PRD/epic/story.**

- Renderer (`render_mermaid.tree`, render_mermaid.py:66) uses `f"{n['id']}\\n{n.get('title') or ''}"`.
- Node title comes from `_node_from_artifact` (spec_graph.py:88): `fm.get("name") or fm.get("title") or ""`.
- PRD/epic/story templates have no `name` or `title` frontmatter key (they have a body `# Title — ID` heading instead) — so `title` is always empty for them. The example tree.md is consistent with this: lines 7-9 show `PRD-CHECKOUT\n` with empty after `\n`.
- Goals: `_node_from_goal` (spec_graph.py:107-115) sets `title` from the BRD goal dict's `title`, so BRD-G1/G2 show titles. Consistent with example.
- Verdict: example matches renderer output. No fix needed; flagged here only because tree.md depends on a 2-step inheritance that's easy to misread.

## Coverage holes

- `--filter-wont` flag implemented in `scripts/visualize.py:103` but NOT documented in `references/visualization-spec.md`, SKILL.md flag table, or CLAUDE.md. Affects ASCII tree/roadmap/persona and Mermaid tree/roadmap. (No-op for moscow/scope/heatmap/gap/risk/delta — but no doc says so.)
- `--snapshot` flag in spec (`visualization-spec.md:104`) not implemented in `visualize.py` — see CRITICAL #3.
- `version_inconsistency` documented in spec but no implementation — see HIGH #7.
- `invalid_type`, `persona_cap_exceeded`, `session_md_gitignored` implemented but not in spec catalog — see HIGH #6.
- `exec_summary` template/ID emitted by generator but the type enum doesn't include it — see CRITICAL #1.
- `parent` listed as a frontmatter key in CLAUDE.md but never appears in any artifact — see CRITICAL #4.
- `horizon` advertised on vision.md by CLAUDE.md + SKILL.md but template explicitly bans it — see HIGH #8.

## Verified-consistent surfaces

- Parent-scoped ID grammar: `frontmatter-and-id-spec.md:11-14`, CLAUDE.md:51-58, `check_consistency.ID_PATTERN_BY_TYPE` (check_consistency.py:33-38), and `generate_templates.PARENT_PATTERN_FOR_PRD/EPIC` (generate_templates.py:70-75) all agree on `BRD-G<n>`, `PRD-<SLUG>`, `PRD-<SLUG>-E<n>`, `PRD-<SLUG>-E<n>-S<n>` with slug ≤16 chars.
- Closed enums for `status`, `scope`, `moscow`, `horizon`, `size`, `lang`: `frontmatter-and-id-spec.md:26-27,57-68` matches `check_consistency.ENUMS` (check_consistency.py:40-47) exactly.
- The 9 viz views × 3 formats (`tree, heatmap, scope, roadmap, persona, gap, moscow, risk, delta` × `ascii, mermaid, html`) are all wired in `visualize.py` and dispatch through `render_ascii`/`render_mermaid`/`render_html`. ASCII-fallback views (`heatmap, persona, risk`) are intentional per spec.
- Status lifecycle (`draft → review → approved`) consistent across spec, template defaults, script (`STATUS_ORDER` in check_consistency.py:69), and the generate-templates safeguard refusing `approved` (generate_templates.py:216-221).
- Findings JSON shape (`schema_version`, `root`, `checked_at`, `findings`, `graph`) consistent across `check_traceability.py:109-115`, `check_consistency.py:263-269`, and the spec at `validation-rules-spec.md:84-101`.
- SKILL.md flag table (lines 28-44) ↔ workflow references mapping in CLAUDE.md:75-83 ↔ actual workflow file flag coverage — every flag has an owner workflow.
- BRD goals as list-of-dicts (`frontmatter-and-id-spec.md:79-94`) ↔ `spec_graph.build_nodes` goal expansion (`spec_graph.py:72-77`) — graph parses goals correctly into `type: goal` nodes.
- Bilingual rule "frontmatter keys stay English" enforced by templates: every template emits English keys. `i18n_labels.py` only localizes the seven `now/next/later/must/should/could/wont/product` strings, never frontmatter keys.
- Approval guard: `generate_templates.fill_defaults` (generate_templates.py:216-221) refuses caller-supplied `status: approved`, matching the spec rule that only `--approve` can flip status.
- Snapshot timestamp wired correctly: `spec_graph.write_snapshot` (spec_graph.py:207-222) derives filename from `generated_at` so file-name and `snapshot_at` agree.
- ID allocation regex tight on epic parent: `PRD_PARENT_LOOKS_LIKE_EPIC_OR_STORY` (generate_templates.py:75) prevents `PRD-AUTH-E1-S1-E1` nonsense.

## Unresolved questions

- Should `exec_summary` join the spec's `type` enum, or should the type field be dropped from the exec-summary template? Affects regeneration safety.
- Should the BRD goal `owner` be required (and fixtures fixed) or optional (and the spec relaxed)? The check_traceability/check_consistency code paths handle missing owner gracefully today, so the schema is the only enforcer.
- The `parent` frontmatter-key entry in CLAUDE.md:65 — is it a leftover from an earlier design where stories/epics carried a single `parent` field, since replaced by `epic`/`prd`/`brd_goals`? If so, just delete.
- For `--viz delta`, is renaming `--diff` to `--snapshot` acceptable, or would changing the spec be safer? The visualize.py error path (lines 78-81) provides good diagnostics on typos either way.
- Should `--filter-wont` propagate to gap/scope/heatmap/risk views or stay tree/roadmap/persona-only? Spec is silent.
