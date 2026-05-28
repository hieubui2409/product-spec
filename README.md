# cleanmatic:product-spec

A Claude Code skill for product owners. It runs an interview, captures your product spec as a strictly-traceable hierarchy (**Vision → 1 BRD → many PRDs → Epics → Stories with AC**), validates the spec, and visualizes it — all in plain language, no code required from you.

Bilingual: English and Vietnamese.

---

## What it does for you

| You want to… | Run |
|---|---|
| Start a new product spec from scratch | `/cleanmatic:product-spec` (no flag → menu) |
| Add a new feature area | `/cleanmatic:product-spec --prd <feature>` |
| Decompose a long brain-dump into a clean spec | `/cleanmatic:product-spec --auto` |
| Check the spec for orphans, missing AC, drift | `/cleanmatic:product-spec --validate` |
| Sign off a BRD/PRD/Epic/Story | `/cleanmatic:product-spec --approve` |
| Get a 1-page exec summary | `/cleanmatic:product-spec --summary` |
| Draw the spec tree / roadmap / coverage map | `/cleanmatic:product-spec --viz <view>` |
| Apply a change without losing prior decisions | `/cleanmatic:product-spec --update` |

Output lives in `docs/product/` inside your project — markdown files with rich YAML metadata.

---

## Install (one-time, ~3 minutes)

### Prerequisites

- **Python 3.11 or newer.** Check with `python3 --version`. Get it at [python.org/downloads](https://www.python.org/downloads/).
- **Claude Code** (the official CLI or VS Code extension).
- **A terminal** (Terminal on macOS, PowerShell or WSL on Windows, any shell on Linux).
- One of `curl` or `wget` (usually preinstalled).

### Steps

**1. Copy this folder into your project.**

After extracting the ZIP you received, you should have this layout at the root of your project:

```
your-project/
├── .claude/
│   └── skills/
│       └── product-spec/        ← the skill
├── CLAUDE.md                    ← LLM operating guide (auto-loaded)
└── README.md                    ← this file
```

If your project already has a `.claude/` folder, merge the contents — don't overwrite.

**2. Run the installer.**

From your project root, in a terminal:

```bash
bash .claude/skills/product-spec/install.sh
```

It creates a Python virtual environment, installs the two libraries the skill needs (`pyyaml`, `pytest`), and downloads the Mermaid diagram engine for offline visualizations. The script is **idempotent** — re-running it is safe.

You should see:

```
✓ python3 = 3.x
✓ venv created
✓ pyyaml + pytest installed
product-spec vendor: ... mermaid.min.js ... (sha256 OK)
43 passed
```

**3. Invoke the skill in Claude Code.**

Open Claude Code in your project folder and type:

```
/cleanmatic:product-spec
```

The skill detects whether `docs/product/PRODUCT.md` exists and either offers to initialize it (guided interview) or shows you a menu of actions.

That's it.

---

## What gets created in your project

After your first session:

```
docs/product/
├── PRODUCT.md            (one-line product facts: name, value, personas)
├── vision.md             (narrative: problem, north-star, principles)
├── brd.md                (single Business Requirements Doc + goals)
├── prds/<feature>.md     (one PRD per feature area)
├── epics/<id>.md         (epics under each PRD)
├── stories/<id>.md       (user stories with acceptance criteria)
├── exec-summary.md       (generated 1-page summary)
├── change-log.md         (dated record of every delta-update)
├── .session.md           (interview state — committed for resume)
└── visuals/              (generated visualizations)
    └── .snapshots/       (graph snapshots for delta/diff views)
```

You commit this folder to git like any other doc. The skill never writes outside `docs/product/`.

---

## Flag reference

| Flag | Purpose |
|------|---------|
| (no flag) | Detect state → present a menu of next actions. |
| `--product` | Init or refresh `PRODUCT.md` (the thin product-facts file). |
| `--brd` | Create or refine the single BRD. |
| `--prd [feature]` | Create or refine a PRD for one feature area. |
| `--epic [prd]` | Create or refine an epic under a PRD. |
| `--story [epic]` | Create or refine a story under an epic. |
| `--auto` | Paste a brain-dump → skill decomposes into BRD/PRD/Epic/Story. |
| `--validate` | Run structural checks + LLM judgment → human report. |
| `--strict` | (with `--validate`) errors block the action; warnings don't. |
| `--summary` | Generate a 1-page exec summary. |
| `--approve` | Sign-off: record owner + date, flip `status: approved`. |
| `--update` | Apply a change; flag affected downstream items for review. |
| `--viz <view>` | Render: `tree`, `heatmap`, `scope`, `roadmap`, `persona`, `gap`, `moscow`, `risk`, `delta`. |
| `--format <fmt>` | `ascii` (default) · `mermaid` · `html`. |
| `--lang <code>` | `en` (default) · `vi`. |

---

## Bilingual

- The interview asks questions in your chosen language (`--lang en` or `--lang vi`).
- LLM-generated prose (vision narrative, story descriptions, AC) is written in your chosen language.
- IDs (`BRD-G1`, `PRD-AUTH`, `PRD-AUTH-E1-S1`) and frontmatter keys (`personas`, `scope`, `moscow`, …) stay English so the structure is stable.
- Visualization labels (`Now/Next/Later`, `Must/Should/Could/Won't`) localize when you pass `--lang vi`.

Vietnamese ships best-effort in v1. If something reads awkwardly, the skill flags it for a native-speaker review.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python3: command not found` | Install Python 3.11+ from [python.org](https://www.python.org/downloads/). |
| `bash: install.sh: Permission denied` | `chmod +x .claude/skills/product-spec/install.sh` then re-run. |
| `pip install` hangs | Check your internet connection; the install needs one-time access to PyPI + the Mermaid CDN. After install, the skill runs offline. |
| HTML visualization shows a blank diagram | Re-run `bash .claude/skills/product-spec/install.sh` to re-vendor the Mermaid engine. |
| Claude Code doesn't see the skill | Make sure you opened Claude Code in your project folder (the one containing `.claude/`), then restart it. |
| `--validate` keeps flagging a parent you removed | The frontmatter `parent`/`epic`/`prd`/`brd_goals` field on a child still points to it. Edit the child to update its parent link, or delete the child. |
| Running scripts from a workspace under `/tmp/...` can't see the `.venv` binary | Some sub-agent / sandbox harnesses block `/tmp/...` reads from outside the workspace. Run the scripts from your project root (or any subdir inside the repo), or install `pyyaml` against the system `python3` and invoke that interpreter explicitly. |

---

## What this skill does NOT do

- It doesn't write production code. Output is product specs — your engineering team writes the code.
- It doesn't estimate in story points or hours — stories carry only `size: S | M | L`.
- It doesn't overwrite your manual edits. On `--update`, it flags affected items and asks before regenerating.
- It doesn't auto-flip a decision marked `approved`. If a new answer contradicts an approved fact, it surfaces the conflict for you to resolve.
- It doesn't need the internet at runtime. After install, everything runs from your machine.

---

## Privacy

Your spec lives in `docs/product/` inside your project. The skill makes no network calls at runtime. The one-time installer downloads `mermaid.min.js` from the public CDN (`cdn.jsdelivr.net`); the file is then stored locally and verified against a pinned SHA-256 hash.

---

## Versions

- Skill: `v1.0.0`
- Tested on: Python 3.11–3.14, macOS / Linux / Windows (WSL).
- Mermaid runtime: `11.4.1` (vendored, SHA-256 pinned).

---

## Need help?

The skill itself can answer most "how do I…" questions — invoke it and ask. For installer issues, re-run with `bash -x .claude/skills/product-spec/install.sh` to see each step.
