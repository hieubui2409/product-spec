# workflow-discover — discovery seed (`--discover <path(s)>`)

Loaded for `--discover`. A pre-stage that ingests raw upstream inputs (interview transcripts,
support-ticket dumps, competitor notes) and proposes **candidate** personas / problems / JTBD to
**seed** the Vision/BRD interview instead of a cold start. **Never auto-commits** — the interview
confirms field-by-field.

> Distinct from `--auto`: `--auto` decomposes the PO's OWN finished brain-dump into the hierarchy;
> `--discover` synthesizes candidates from raw UPSTREAM material to seed the interview. Kept a
> separate flag for that reason.

## Flow

### 1. Read-fence + filter (deterministic — mandatory)
Run `ingest_raw_inputs.py --root <root> --path <p> [--path <p> …] [--scaffold]`. This is the broadest
read surface in the skill, so the script hard-fences it (`fs_guard` is write-only):
- **Project-root fence** — every path resolved + contained inside the project root; traversal /
  symlink-escape rejected.
- **Extension allow-list** — `.md` / `.txt` only.
- **Dotfile exclusion** — any `.`-prefixed component (`.env`, `.aws`, `.ssh`, `.git`, …) skipped even
  inside a walked directory.
- **Files AND directories** — a directory is walked with **bounded recursion** (depth + file-count
  cap); each discovered file still passes the fence/allow-list/dotfile/size filters.
- **Size cap** per file.

### 2. Echo the resolved list for PO confirm (the safety net)
Show the PO the `accepted` list (and the `rejected` list with reasons) **before reading content** for
synthesis. For directory inputs that fan out, this confirm step is the safety net. Only proceed on PO OK.

### 3. Synthesize candidates (LLM) — nothing committed
With `--scaffold`, the script reads the accepted files and returns raw text + **empty** candidate
buckets (`personas`/`problems`/`jtbd`). The LLM proposes candidates from the raw text. Keep scope
TIGHT: text in → candidate bullets out. **No entity-extraction / clustering gold-plating.**

### 4. Seed the Vision interview (confirm/edit/reject)
Present the candidates at interview start: *"found these — confirm / edit / reject"*, feeding V1/V2 of
`interview-vision.md`. **GATE-NEVER-ASSUME**: no persona is written to `PRODUCT.md` / `vision.md`
without the PO explicitly confirming each. The candidate buckets are empty by construction so the only
path to a committed persona is through the interview confirm.

## GATEs
- **GATE-NEVER-ASSUME** — never commit a candidate persona/problem without explicit PO confirm.
- No network — local files only.

## Residual
If the `--discover` vs `--auto` distinction proves thin in practice, folding this into `--auto --seed`
later is a clean follow-up (PO decision: kept separate for now).
