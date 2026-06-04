# cleanmatic:product-spec

User-invocable Claude skill for **non-technical product owners**: interview-driven product spec hierarchy (Vision → 1 BRD → many PRDs → Epics → Stories) with strict traceability, validation, and visualization. No code in prose, no engineering jargon.

## Install

```bash
./install.sh
```

One-shot setup (idempotent). Requires Python 3.11+ and curl/wget. The installer:

1. Creates the per-skill venv at `../.venv/` (next to this folder).
2. Installs `pyyaml` (runtime) from `scripts/requirements.txt`.
3. Vendors Mermaid JS + marked + DOMPurify locally for offline HTML (graph views + body rendering).

Add `--dev` (`./install.sh --dev`) to also install `pytest` + `pytest-cov` from `scripts/requirements-dev.txt` and run the script test suite as a smoke check. The default runtime install ships only `pyyaml` and skips the test gate.

Add `--memory-hook` (`./install.sh --memory-hook`) to opt in to the Tier-1 memory-write Stop-hook reminder (registered into `.claude/settings.local.json`; `--memory-hook-shared` targets the committed `settings.json`). It is **opt-in only and never auto-registered** — a plain `./install.sh` leaves your hooks untouched. See `references/memory-enforcement.md`.

## Quickstart

Invoke from Claude Code, then **talk in plain product language** — no command memorization needed:

```
/cleanmatic:product-spec
```

With no flag, the skill detects the state of `docs/product/` and shows a menu (init, new BRD/PRD, add stories, validate, visualize, approve, summary).

### The 6 things to know before you start

1. **It's a tree with traceability.** Vision → **one** BRD → **many** PRDs → Epics → Stories. Every layer links up to its parent by ID, so any story traces to the business goal it serves.
2. **One home per fact (DRY).** Personas live in `PRODUCT.md`, goals in the BRD, **acceptance criteria only in stories**, competitors declared once in the BRD. Facts are referenced by ID, never duplicated.
3. **Structure is data; your prose is yours.** The machine reads frontmatter (IDs, `status`, `scope`, `metrics`) as source-of-truth and **never overwrites your narrative** — on `--update` it flags affected nodes and asks.
4. **Nothing is approved or reversed silently.** `approved` needs an explicit owner + date; a contradiction with an approved doc always stops for **Keep / Change / Hybrid**.
5. **Preferences are asked once.** Language, detail level, and the **engagement profile** (`interview_rigor` + `action_prompting`) are seeded early and never re-asked — change them with `--lang` or `preferences.py --set`.
6. **Fully offline; bilingual EN/VI.** Everything runs locally after install; IDs and frontmatter keys stay English, prose localizes.

### Learning path (don't learn every flag at once)

- **Day 1 — the spine:** `init → BRD → one PRD → one epic → one story → --validate`. That one thin slice teaches the whole skill.
- **Week 1:** `--approve`, `--update`, `--status`, then `--viz` / `--summary` / `--export` to share. Set `--lang` + the engagement profile early.
- **As you grow:** the decision register (`--decision`), `--apply-critique`, the validate Memory pass, `--reflect`, the opt-in reminder hook.
- **Shortcut:** paste a brain-dump and let `--auto` decompose it (it still confirms every ambiguous split).

Full walkthroughs with sample conversations: **[`GUIDE-EN.md`](./GUIDE-EN.md) / [`GUIDE-VI.md`](./GUIDE-VI.md)**.

### Flags (shortcuts for the conversational asks above)

`--product`, `--brd`, `--prd <slug>`, `--epic`, `--story`, `--auto` (braindump → decompose), `--discover <path(s)>` (seed the interview from raw transcripts/notes), `--validate`, `--strict`, `--approve`, `--update`, `--decision`, `--apply-critique <report>` (turn a critique report into recorded decisions), `--status`, `--summary [--audience exec|release-notes]`, `--viz <view>` (incl. `audit`), `--format ascii|mermaid|html`, `--lang en|vi`, `--voice` (record PO voice), `--reflect` (retroactive memory harvest). Engagement knobs `interview_rigor` (light/standard/deep) + `action_prompting` (minimal/standard/proactive) tune interview challenge-depth and next-action density; set them deterministically via `preferences.py --set KEY=VALUE` (load→merge→save).

## Layout

- `SKILL.md` — lean skeleton (~300 lines), the canonical entry point Claude reads.
- `references/` — full prose for each flag (frontmatter+ID spec, document model, validation rules, visualization spec, interview banks, workflow guides).
- `scripts/` — Python (stdlib + pyyaml). Structural only; LLM owns judgment. Run via `../.venv/bin/python3 scripts/<name>.py --root <project-dir>`.
- `assets/templates/` — markdown templates with `{{token}}` substitution.
- `assets/vendor/` — vendored offline runtimes: `mermaid.min.js` (graph views) + `marked.min.js` + `purify.min.js` (body rendering).
- `eval/` — scenario evals.
- `examples/acme-shop/` — worked sample product spec.

## Further reading

- **[`GUIDE-VI.md`](./GUIDE-VI.md) / [`GUIDE-EN.md`](./GUIDE-EN.md)** — end-user guide for the non-technical PO: core concepts, a learning path, then every use case as a full sample conversation (natural-language way preferred + flag equivalent), with worked examples from `examples/acme-shop`.
- Top of `SKILL.md` — flags table + no-flag menu + output contract.
- `../../../CLAUDE.md` (repo-root) — operating principles loaded automatically by Claude Code.
- `references/frontmatter-and-id-spec.md` — canonical YAML schema and parent-scoped ID grammar (`BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1`, `PRD-AUTH-E1-S1`).
