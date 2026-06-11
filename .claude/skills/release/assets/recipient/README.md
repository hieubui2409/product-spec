<!-- recipient-variant -->
# product-spec — Claude Code Skills Bundle

This bundle installs three Claude Code skills into your project:

| Skill | Invoke with | What it does |
|-------|-------------|--------------|
| `product-spec` | `/product-spec` | Author and manage product specs (Vision → BRD → PRD → Epic → Story) |
| `product-spec-critique` | `/product-spec-critique` | Critique specs through 4 lenses: product, tech, market, craft |
| `telemetry` | `/telemetry` | Read usage and health analytics for the installed skills |

## Quick start

```bash
# 1. Extract the bundle
tar -xzf product-spec-*.tar.gz

# 2. Install into your repo
cd product-spec-*/
bash install.sh

# (Windows)
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

## Invoking skills

Open a Claude Code session in your repo, then type `/` to see available skills, or use them directly:

- `/product-spec:vision` — start a new product vision
- `/product-spec:validate` — validate your spec graph
- `/product-spec-critique` — critique an existing spec
- `/telemetry:proxy` — view skill usage analytics

## Upgrading

Re-run `bash install.sh` from a newer bundle. The installer is version-aware and will only overwrite
stale skills. Use `FORCE_OVERWRITE=1 bash install.sh` to unconditionally replace all files.

## Uninstalling

```bash
rm -rf .claude/skills/product-spec/ .claude/skills/product-spec-critique/ .claude/skills/telemetry/
```

Remove the related hooks from `.claude/settings.json` if you registered them.
