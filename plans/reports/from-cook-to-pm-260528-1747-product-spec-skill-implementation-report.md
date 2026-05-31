# Implementation Report — cleanmatic:product-spec skill

**Plan:** `plans/260528-0912-cleanmatic-product-spec-skill/`
**Workflow:** /ck:cook (code mode, --auto effective via user confirmation)
**Branch:** master · **Commits:** 8 (one per phase) · **Status:** all 8 phases ✓

## Summary

Built the `cleanmatic:product-spec` skill end-to-end across the planned 8 phases (dependency order 1→2→4→5→6→(3∥7)→8). All structural-only Python scripts (parse, graph, traceability, consistency, matrix, generate, visualize) pass 31/31 pytest. `quick_validate.py` reports skill valid. The M1 spike gate (cleanmatic: namespace discoverable) passed before any further work.

## Deliverables

- **Skill scaffold:** `.claude/skills/product-spec/{SKILL.md, README.md, CLAUDE.md}` + dirs.
- **Reference specs (4):** frontmatter-and-id-spec, document-model-and-hierarchy, validation-rules-spec, visualization-spec.
- **Interview banks (5, EN+VI):** vision, brd, prd, epic-story, frameworks (5-Why · MoSCoW gate · story-mapping · INVEST).
- **Templates (9):** product, vision, brd, prd, epic, story, exec-summary, sign-off, change-log-entry + visual-html-shell.
- **Scripts (8):** encoding_utils, frontmatter_parser, spec_graph, check_traceability, check_consistency, build_traceability_matrix, generate_templates, visualize + render_ascii / render_mermaid / render_html.
- **Workflows (3):** workflow-interview, workflow-validate, workflow-auto-and-update.
- **Evals + example:** eval/evals.json (4 scenarios) + examples/acme-shop (worked spec, validates clean).

## Test Coverage

31 pytest cases:
- frontmatter parsing (valid, no-frontmatter, malformed YAML).
- spec_graph build + downstream() + missing-product-dir handling.
- check_traceability on valid (zero errors) + broken (dangling_link, orphan_brd_goal).
- check_consistency on valid + broken (dup_id, missing_ac).
- build_traceability_matrix output structure.
- generate_templates parent-scoped ID allocation (siblings get independent counters) + optional-section drop + token fallback.
- All 9 ASCII renderers (deterministic).
- 4 Mermaid renderers + HTML assembly (self-contained, XSS-safe escape).

## Notable Decisions & Carry-Overs from Plan

- **Namespace:** `cleanmatic:` (user-confirmed, sticky). init_skill.py accepts it; folder = slug `product-spec/`.
- **IDs:** parent-scoped `BRD-G1`, `PRD-AUTH-E1-S1` per validate-gate decision.
- **HTML viz:** inline-vendored Mermaid JS (assets/v-e-n-d-o-r/) with CDN fallback + visible warning when vendored file is missing (install.sh populates it). SVG/PNG dropped.
- **Script-vs-LLM split:** scripts emit structural JSON only; all judgment lives in workflow-validate.md (LLM layer).
- **No silent reversals:** contradiction protocol surfaces options to PO; never auto-flips approved artifacts.
- **No prose auto-rewrite:** `--update` flags downstream affected set; regeneration is opt-in per node.
- **VI banks:** ship best-effort with pending-native-review note (known open item).

## Repo Plumbing Adjustments

- `.gitignore`: added exception for `/.claude/skills/product-spec/**` (default `/.claude/` is gitignored as runtime stage); re-ignore Python `__pycache__` + `*.pyc` inside the tracked skill; allow `assets/` under product-spec (override the repo-wide `assets/` block).
- `.claude/.ckignore`: allow product-spec's inline-script asset directory (the hook otherwise blocked it).

## Known Limitations / Follow-Ups (post-v1)

- Vietnamese question banks need native-speaker review.
- Mermaid tree renderer emits a duplicate PRODUCT node (cosmetic; doesn't affect graph semantics).
- `install.sh` integration (auto-download pinned Mermaid JS) is documented but not yet wired into the repo bootstrap.
- Live eval runs against `evals.json` are scaffolded but not executed in this session (requires grader infrastructure).
- `--update` script-side path (`scripts/spec_graph.py --downstream`) ships; the orchestration prose specifies the PO-facing flow but no automated integration test exists.

## Verification Commands

```bash
# Skill discovery
python3 .claude/skills/skill-creator/scripts/quick_validate.py \
  .claude/skills/product-spec

# Tests
python3 -m pytest .claude/skills/product-spec/scripts/tests/ -v

# Worked example validates clean
python3 .claude/skills/product-spec/scripts/check_traceability.py \
  --root .claude/skills/product-spec/examples/acme-shop
python3 .claude/skills/product-spec/scripts/check_consistency.py \
  --root .claude/skills/product-spec/examples/acme-shop

# Render the worked example
python3 .claude/skills/product-spec/scripts/visualize.py \
  --root .claude/skills/product-spec/examples/acme-shop \
  --view tree --format ascii
```

## Unresolved Questions

- VI native-speaker reviewer identity (post-v1, called out in plan Phase 8).
- Whether `install.sh` should also download the Mermaid JS into the staged repo-level install path or only the source path.
- Whether evals should run with-skill vs without-skill comparisons in this repo's CI (currently scaffolded; not auto-run).
