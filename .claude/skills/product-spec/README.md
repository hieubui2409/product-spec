# cleanmatic:product-spec

Product-Owner-facing Claude skill that builds and maintains a strictly-traceable product spec hierarchy — **Vision → 1 BRD → many PRDs → Epics → Stories (+AC)** — through a phased PO interview (bilingual EN/VI), persists artifacts as markdown under `docs/product/` in the user's project, validates structure deterministically with judgment via LLM, and visualizes the spec tree in ASCII / Mermaid / self-contained HTML.

## Status

v1.0.0 — first cut. Vietnamese interview banks ship best-effort with a pending-native-review note (open follow-up item).

## Quickstart

In Claude Code, invoke the skill from any project:

```text
/cleanmatic:product-spec
```

No flag → the skill inspects the project, presents a menu (init / new BRD / new PRD / add stories / validate / update / visualize / approve / summary). With a flag, it routes directly. See **Flag Reference** below.

## Flag Reference

| Flag | Purpose |
|------|---------|
| `--product` | Init/refresh `PRODUCT.md` (thin product-context labels). |
| `--brd` | Create/refine the single BRD. |
| `--prd [feature]` | Create/refine a PRD per feature-area. Multi-PRD supported. |
| `--epic [prd]` | Create/refine an epic under a PRD. |
| `--story [epic]` | Create/refine a story under an epic. |
| `--auto` | Brain-dump → decompose into BRD goals / PRDs / epics / stories. |
| `--validate [--strict]` | Run scripts + LLM judgment → human report. `--strict` blocks on errors. |
| `--summary` | 1-page exec summary (markdown / HTML). |
| `--approve` | Sign-off → record owner + date → flip `status: approved`. |
| `--update` | Delta — flag downstream nodes for PO review. Never auto-rewrites prose. |
| `--viz <view>` | Render: `tree`, `heatmap`, `scope`, `roadmap`, `persona`, `gap`, `moscow`, `risk`, `delta`. |
| `--format <fmt>` | `ascii` (default) · `mermaid` · `html`. |
| `--lang <en|vi>` | Interview/output language. IDs and frontmatter keys stay English. |

## Output Layout (in your project)

```
docs/product/
├── PRODUCT.md
├── vision.md
├── brd.md
├── prds/<slug>.md
├── epics/<id>.md
├── stories/<id>.md
├── exec-summary.md
├── .session.md
├── change-log.md
└── visuals/
    └── .snapshots/
```

## Namespace & Folder Decision

The skill is registered under the **`cleanmatic:`** namespace. `init_skill.py` (from `skill-creator`) accepts namespaced identifiers; the directory uses the slug-only form (`product-spec/`), and the frontmatter `name:` field carries the full identifier (`cleanmatic:product-spec`). This mirrors the existing `ckm:design` and `excalidraw` precedents in this repo.

Discovery was smoke-tested in Phase 1 (skeleton load → skill list shows the entry → invocation surfaces).

## Bilingual Note

Interview banks are authored in English and Vietnamese in parallel. The Vietnamese pass ships best-effort and is flagged for a native-speaker review (post-v1).

## Architecture Summary

- **Script vs LLM split** — scripts (Python, stdlib + pyyaml) do parse/graph/orphan/AC-count/ID-integrity; LLM does INVEST, vagueness, core-value drift, semantic dup, contradiction.
- **Frontmatter = source-of-truth** — YAML drives structure; prose carries narrative.
- **DRY** — one authoritative home per fact; cross-reference by ID.
- **Parent-scoped IDs** — `BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1`, `PRD-AUTH-E1-S1` (globally unique by construction).
- **No silent reversals** — contradictions with approved decisions are surfaced for PO choice.
- **HTML self-contained** — Mermaid JS vendored inline; no external CDN / binary required.

## Resources

- `SKILL.md` — entry point, flag table, workflow map.
- `CLAUDE.md` — LLM operating guide.
- `references/` — schemas, workflows, interview banks (loaded on demand).
- `scripts/` — Python scripts (run via repo venv `./.claude/skills/.venv/bin/python3`).
- `assets/templates/` — markdown templates with `{{token}}` substitution.
- `assets/vendor/` — vendored Mermaid JS.
- `eval/` — scenario evals.
- `examples/` — worked sample spec.

## Install

The skill ships with the rest of the `cleanmatic-skills` repository. Dependencies (`pyyaml`, `pytest`, `pytest-cov`) install via the repo bootstrap:

```bash
./.claude/skills/install.sh
```

Run scripts via the repo venv:

```bash
./.claude/skills/.venv/bin/python3 .claude/skills/product-spec/scripts/<script>.py --root <project-dir>
```

## License

Inherits from the parent repository.
