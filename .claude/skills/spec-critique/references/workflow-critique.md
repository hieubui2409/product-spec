# workflow-critique — the executable orchestration

Load this whenever `/spec-critique` runs. It is the 6-step flow the main agent executes. The lens agents +
consolidator are READ-ONLY (they propose); only the main agent writes (the report, the snapshot, the optional DEC).

## 0. Early-exit guards (before spawning ANY agent)

- **No spec:** `docs/product/` absent OR the graph is empty → reply, in `--lang`, a friendly "chưa có spec để chửi, dùng `cleanmatic:product-spec` để viết spec trước đã" and STOP. Spawn no agents (no token/web cost on an empty repo).
- **Venv missing:** the shared interpreter is absent → AskUserQuestion to run an installer (see SKILL.md venv note),
  then retry. Never fall back to system Python.
- **critique_scan errors:** if `critique_scan.py` returns `{error,...}` (malformed spec, missing product-spec dir),
  surface the error to the PO and STOP, do not critique on a broken structure.

## 1. Parse flags (or `--interactive`)

- Resolve `scope` (default `all`), `lenses` (default all four), `lang` (default `vi`), `--no-web`.
- **Level resolution:** an explicit `--level`/alias flag wins; otherwise the default is the `critique_level` preference
  (`preferences.load(root)["critique_level"]`, itself defaulting to 3). So a PO who wants a standing harsh voice sets
  `critique_level: 6` once and every flagless run roasts.
- `--interactive` → AskUserQuestion (three quick questions): which scope, which lenses, which level. Ground options in
  what exists (offer real artifact IDs from the graph).
- `--level` alias map: `--warm`=1, `--gentle`=2, `--blunt`=3, `--savage`=4, `--no-mercy`=5, `--roast`=6.
- **Levels 5 and 6 danger gate.** These two carry a warning because they break the professional line (5 may jab the
  author; 6 is a direct roast that has no place in a shared report). How the gate resolves depends on WHERE the level
  came from:
  - **From an ad-hoc `--level 5/6` / `--no-mercy` / `--roast` flag (no standing preference):** show the warning and ask
    for an explicit AskUserQuestion confirmation BEFORE spawning any agent. Never infer consent from vague phrasing. On
    a no: level 5 falls back to 4, level 6 falls back to 5.
  - **From the `critique_level` preference being 5 or 6 (standing consent):** the PO already opted in deliberately by
    setting the preference, so do NOT re-ask every run. Still print the one-line danger reminder each run (never run it
    silently), in `--lang`: e.g. _"giọng mức 6 (roast) đang bật mặc định: bài critique sẽ chửi thẳng người viết, đừng
    chia sẻ ra ngoài; đổi bằng `critique_level` trong preferences hoặc `--level`."_ Then proceed.
  - The hard floor still holds at every level incl. 6: each line cites `ID:line` + ends in a fix; the roast attacks the
    work's sloppiness, never identity, protected characteristics, slurs, threats, or self-harm.

## 2. Verdict ammo: NO forced `--validate` (refined D8)

`critique_scan.py` runs the structural checks FRESH (cheap) and reads cached LLM verdicts from `judgments.json`
(may be empty). The skill does **NOT** auto-run `--validate`, validate is reproducible/PO-facing and must not be
poisoned by a critique. If `cached_verdicts` is empty or the spec has drifted since the last validate, surface ONE
line, "chạy `--validate` trước để critique sắc hơn (có thêm phán quyết chất lượng làm đạn)", and proceed anyway.
The lens agents are the judgment layer; validate verdicts are supplementary ammo.

## 3. Build the bundle

```bash
./.claude/skills/.venv/bin/python3 \
  .claude/skills/spec-critique/scripts/critique_scan.py \
  --root <project> --scope <scope> --lang <lang>
```

Write the bundle JSON to a SCRATCH path **outside** the fence, `$TMPDIR/spec-critique-bundle-<ts>.json` (it is
scratch, not a spec artifact; never under `docs/product/`). Pass that path to each lens agent. The bundle's top-level
keys + the `digest` list shape are documented in SKILL.md ("The bundle contract").

## 4. Fan out the lens agents (parallel, read-only)

Spawn the selected lenses concurrently via `Task`, each given: the bundle path, the active `--level`, `--lang`, and
(for market) the `--no-web` flag. Agent names: `spec-critique-product`, `spec-critique-tech`, `spec-critique-market`,
`spec-critique-craft`.

- **Scope-aware:** at a single-story scope the **market** lens is usually thin, spawn it but tell it the scope is
  narrow, or skip it and let the consolidator note the omission. At `--scope all` the market lens is most valuable.
- **Market grounding:** with no BRD `competitors:` AND `--no-web`, the market lens flags "thiếu căn cứ cạnh tranh"
  and never fabricates competitors. With web enabled it may research + cite (url in the finding's `source`).
- Each agent returns a compact JSON findings array `{lens,evidence,critique,why_it_dies,fix,severity}` (+ `source`
  for market). Collect whatever returns, **tolerate N<4** (a lens may return nothing/garbage).

## 5. Consolidate

Spawn `spec-critique-consolidate` (opus) with: the available lens findings arrays + the bundle's `prior_reports` +
`scope`/`lang`/`level`. It dedups cross-lens, enforces the mechanical anti-overlap floor (drop byte-identical
validate-echoes + findings missing why/fix), assigns final severity (structural-backed ≥ major), picks the top-3,
detects repeat-offense vs prior reports, flags DEC-worthy items, and renders ONE markdown body in the voice. It writes
through Gate 1 of the humanizer (it consults `references/humanizer-and-anti-ai-tells.md` as it drafts). Its header NAMES
any lens that did not complete. It returns markdown TEXT, it does not write.

- **Render the level's labels in the findings, not just in your head.** The active level's why/fix label wording (the
  `voice-and-tone.md` table: e.g. L1 "Chỗ này đáng lưu tâm" / "Có thể thử", L3 "Toang ở đâu" / "Sửa") MUST actually
  appear on the rendered findings. A level-1 report whose findings carry no warm labels and read blunt is a level
  mismatch, the single most common voice defect.

## 5b. Humanize (Gate 2: the independent second eye)

Spawn `spec-critique-humanize` (sonnet) with the consolidator's markdown + `--lang`/`--level`. It rewrites the prose to
strip AI-tells and Vietnamese word-for-word-translation tells per `references/humanizer-and-anti-ai-tells.md`, while
preserving the bite, the level's tone (the level 5/6 personal attack stays), every finding, every evidence `ID:line`,
every fix, and the structure. It returns the cleaned markdown. This pass is mandatory: the file written in step 6 is
the humanized version, never the consolidator's raw draft. (Gate 1 = consolidator self-applies the rules while writing;
Gate 2 = this independent agent re-checks the finished draft. Two passes, matching the humanizer's own draft → find
tells → final-rewrite process.)

## 6. Write + snapshot + optional DEC bridge

Write the humanized markdown from step 5b (not the raw consolidator draft).

1. **Write** `docs/product/critique/<ts>-<scope>.md` with the humanized markdown from step 5b (never the raw
   consolidator draft). Use the soft fence: the write target is under `docs/product/critique/`, confirm with
   `fs_guard.assert_under_docs_product` semantics
   (the main agent's own write; `critique_scan` owns the script-side fence for the snapshot). `<ts>` = compact UTC
   timestamp; `<scope>` = the scope id or `all`.
   - **Sanitize before writing (mechanical safety net, do NOT trust the agents to be clean).** Even with the agent
     output contracts, an LLM occasionally leaks reasoning. Before writing, the main agent MUST:
     (a) **strip any preamble** — drop everything before the first line that starts with `# ` (the report heading);
     (b) **de-duplicate drafts** — if the text contains more than one `# Critique` heading (the agent emitted several
     draft copies), keep only the LAST complete copy;
     (c) **purge stray dashes** — replace any em/en dash (`—`, `–`) in the prose with a comma, colon, or period, but
     leave dashes inside `inline code`, fenced blocks, and verbatim spec quotes untouched.
     The file handed to the PO begins at `# Critique:` and contains the report exactly once, dash-clean.
2. **Snapshot**, refresh the drift marker:
   ```bash
   ./.claude/skills/.venv/bin/python3 \
     .claude/skills/spec-critique/scripts/critique_scan.py --root <project> --snapshot --scope <scope>
   ```
3. **DEC bridge (opt-in, GATEs apply):** for each DEC-worthy item the consolidator flagged, AskUserQuestion
   (Keep / Change / Hybrid, or simply "record this as a decision?"). On PO confirm only:
   ```bash
   ./.claude/skills/.venv/bin/python3 \
     .claude/skills/product-spec/scripts/decision_register.py --root <project> --append \
     --title "<ruling>" --rationale "[nguồn: critique] <why>" --affects "<ids>"
   ```
   - The `decision_register.py` CLI has no `--source` flag and the DEC record schema has no provenance field (do NOT
     invent one, it would change the product-spec schema). Encode the provenance in the `--rationale` prose with a
     leading `[nguồn: critique]` / `[source: critique]` marker so the ruling is still distinguishable from a
     validate-contradiction DEC, without touching product-spec.
   - **GATE-NEVER-ASSUME:** never record a DEC without explicit confirm.
   - **GATE-NO-SILENT-REVERSAL:** if the item contradicts an `approved` artifact, present Keep / Change+re-approve /
     Hybrid; only `Change` (with owner+date re-approval, done via product-spec) touches approved content.

## Scope-aware lens applicability

| scope | product | tech | market | craft |
|-------|---------|------|--------|-------|
| `all` / PRD | full | full | full | full |
| epic | full | full | thin | full |
| story | full | full | **thin/skip** (note it) | full |

## Cost note

`--scope all` with all four lenses spawns opus×2 (product + consolidate) + sonnet×2 + haiku, plus web for market.
It is opt-in and scope-aware; for a quick read use a single lens (`--craft`) or a narrow scope. `--no-web` trims the
market round. State the cost expectation when the PO runs `--scope all`.
