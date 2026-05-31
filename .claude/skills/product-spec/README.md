# cleanmatic:product-spec

User-invocable Claude skill for **non-technical product owners**: interview-driven product spec hierarchy (Vision → 1 BRD → many PRDs → Epics → Stories) with strict traceability, validation, and visualization. No code in prose, no engineering jargon.

## Install

```bash
./install.sh
```

One-shot setup (idempotent). Requires Python 3.11+ and curl/wget. The installer:

1. Creates the per-skill venv at `../.venv/` (next to this folder).
2. Installs `pyyaml` + `pytest` from `scripts/requirements.txt`.
3. Vendors Mermaid JS locally for offline HTML visualizations.
4. Runs the script test suite as a smoke check.

## Quickstart

Invoke from Claude Code:

```
/cleanmatic:product-spec
```

With no flag, the skill detects the state of `docs/product/` and presents a menu (init, new BRD, new PRD, validate, visualize, approve, summary). Common flags: `--product`, `--brd`, `--prd <slug>`, `--epic`, `--story`, `--auto` (braindump → decompose), `--validate`, `--strict`, `--approve`, `--update`, `--summary`, `--viz <view>`, `--format ascii|mermaid|html`, `--lang en|vi`.

## Layout

- `SKILL.md` — lean skeleton (~300 lines), the canonical entry point Claude reads.
- `references/` — full prose for each flag (frontmatter+ID spec, document model, validation rules, visualization spec, interview banks, workflow guides).
- `scripts/` — Python (stdlib + pyyaml). Structural only; LLM owns judgment. Run via `../.venv/bin/python3 scripts/<name>.py --root <project-dir>`.
- `assets/templates/` — markdown templates with `{{token}}` substitution.
- `assets/vendor/mermaid.min.js` — vendored Mermaid for offline HTML.
- `eval/` — scenario evals.
- `examples/acme-shop/` — worked sample product spec.

## Further reading

- **[`GUIDE-VI.md`](./GUIDE-VI.md) / [`GUIDE-EN.md`](./GUIDE-EN.md)** — end-user guide for the non-technical PO: every use case as a full sample conversation (natural-language way preferred + flag equivalent), with worked examples from `examples/acme-shop`.
- Top of `SKILL.md` — flags table + no-flag menu + output contract.
- `../../../CLAUDE.md` (repo-root) — operating principles loaded automatically by Claude Code.
- `references/frontmatter-and-id-spec.md` — canonical YAML schema and parent-scoped ID grammar (`BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1`, `PRD-AUTH-E1-S1`).
