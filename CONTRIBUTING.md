# Contributing

Thanks for your interest in the **Product Spec Harness Eco-system**. This document covers how to
work on the project and — importantly — the terms your contributions are made under.

## License & commercial use (read first)

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** — see
[`LICENSE`](LICENSE). Copyright (c) 2026 Hieu Bui.

What that means in practice:

- You may use, study, modify, and share it. **If you run a modified version to provide a service over
  a network, or you distribute it, you must release your complete corresponding source under
  AGPL-3.0 as well** (this closes the "SaaS loophole" of ordinary GPL).
- You **may not** take this code into a closed-source / proprietary commercial product. Doing so
  requires a **separate commercial license** — contact the copyright holder to arrange one.
- AGPL-3.0 does not forbid commercial use outright; it forbids *proprietary* appropriation. If you
  want to build on this commercially without open-sourcing your derivative, you need that separate
  license.

### Inbound = outbound

By submitting a contribution (pull request, patch, or any change), **you agree your contribution is
licensed under AGPL-3.0**, the same terms as the project (the standard "inbound = outbound" rule),
and that you have the right to submit it under those terms.

### Sign-off (DCO)

Add a `Signed-off-by` line to each commit to certify the [Developer Certificate of
Origin](https://developercertificate.org/):

```bash
git commit -s -m "feat: ..."
```

## Project layout

This is a bundle of Claude Code skills under `.claude/`:

- `.claude/skills/<skill>/` — the four self-contained skills (`product-spec`, `product-spec-critique`,
  `release`, `telemetry`). Each owns its `scripts/`, `references/`, guides, and `CHANGELOG.md`.
- `.claude/skills/_shared/lib/` — genuinely cross-skill code only (the eval-gate `run_evals.py` /
  `llm_eval.py`). Skill-specific code lives in that skill's own `scripts/`.
- `.claude/agents/`, `.claude/hooks/`, `.claude/rules/` — sub-agents, hooks, and orchestration rules
  that ship with the bundle.

## Development setup

Requires **Python 3.11+**. Create the shared virtual environment via any skill installer:

```bash
bash .claude/skills/product-spec/install.sh        # add --dev for pytest deps
```

Run all scripts with the shared interpreter:

```bash
.claude/skills/.venv/bin/python3 .claude/skills/<skill>/scripts/<script>.py
```

## Running tests

```bash
# A skill's suite
.claude/skills/.venv/bin/python3 -m pytest .claude/skills/<skill> -q

# Telemetry + hooks + shared eval-gate
.claude/skills/.venv/bin/python3 -m pytest .claude/skills/telemetry .claude/hooks .claude/skills/_shared -q

# Release skill suite (run from its scripts dir)
cd .claude/skills/release/scripts && ../../.venv/bin/python3 -m pytest tests -q
```

All tests must pass before a PR is merged. Do not skip or fake tests to go green.

## Commit & PR conventions

- **Conventional commits**: `feat:`, `fix:`, `refactor:`, `test:`, `release:`. For changes under
  `.claude/`, do **not** use the `chore:` or `docs:` types.
- No AI-tool references in commit messages.
- Keep commits focused; one logical change per commit where practical.
- If you change a skill's behaviour, bump that skill's `SKILL.md` `metadata.version` **and** add a
  matching `## [X.Y.Z]` entry to that skill's `CHANGELOG.md` (the A4 PR-gate enforces version ==
  changelog top).

## Releases

Releases are **tag-triggered via CI** — never build and upload by hand.

1. Fill the root [`CHANGELOG.md`](CHANGELOG.md) `## [Unreleased]` section.
2. Bump each changed skill's version + skill `CHANGELOG.md`.
3. `release.py --release X.Y.Z --apply` (locks `[Unreleased]`, bumps `pack.manifest.yaml`).
4. Commit, push `master`, then push the annotated tag `product-spec-vX.Y.Z`. CI builds the
   reproducible tarball, verifies its SHA256, and publishes the GitHub Release.

## Questions

Open an issue, or read a skill's `GUIDE-*.md` / `SKILL.md` for how it works.
