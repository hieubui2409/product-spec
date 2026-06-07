# workflow-critique — the executable orchestration

Load this whenever `/product-spec-critique` runs. It is the 6-step flow the main agent executes. The lens agents +
consolidator are READ-ONLY (they propose); only the main agent writes (the report, the snapshot, the optional DEC).

## 0. Early-exit guards (before spawning ANY agent)

- **No spec:** `docs/product/` absent OR the graph is empty → reply, in `--lang`, a friendly "chưa có spec để chửi, dùng `cleanmatic:product-spec` để viết spec trước đã" and STOP. Spawn no agents (no token/web cost on an empty repo).
- **Venv missing:** the shared interpreter is absent → AskUserQuestion to run an installer (see SKILL.md venv note),
  then retry. Never fall back to system Python.
- **critique_scan errors:** if `critique_scan.py` returns `{error,...}` (malformed spec, missing product-spec dir),
  surface the error to the PO and STOP, do not critique on a broken structure.

## 1. Parse flags (or `--interactive`)

- Resolve `scope` (default `all`), `lenses` (default all four), `lang` (default `vi`), `--no-web`.
- **Level resolution (1..9):** an explicit `--level`/alias flag wins; otherwise the default is the `critique_level`
  preference (`preferences.load(root)["critique_level"]`, itself defaulting to **5**, no-mercy). So a flagless run is
  level 5 (the last level before a mandated roast) plus the standing-consent reminder; a PO who wants a different
  standing voice sets `critique_level: 3` (gentler) or `: 6`/`7`/`8` (harsher) once. `critique_level: 9` is a
  VALID standing default too, but a RESOLVED level of 9 (from the preference OR a `--level 9` flag) always re-confirms
  per run, see the gate.
- `--interactive` → AskUserQuestion (three quick questions): which scope, which lenses, which level. Ground options in
  what exists (offer real artifact IDs from the graph).
- `--level` alias map: `--warm`=1, `--gentle`=2, `--blunt`=3, `--savage`=4, `--no-mercy`=5, `--roast`=6. **Levels 7, 8,
  9 have NO aliases** — invoke them only with `--level 7`, `--level 8`, `--level 9`.
- **Level 5 is the default baseline, NOT gated.** `critique_level` defaults to 5 (no-mercy), so a flagless run is level
  5. Level 5 lifts the personal-barb redline but it is the everyday voice now: it shows **no warning, no confirm, no
  standing reminder**, just run. (An ad-hoc `--no-mercy` / `--level 5` is likewise ungated.) The danger gate begins at
  6, where the attack turns into a mandated personal roast.
- **Danger gate (levels 6 through 9).** These carry a warning because they cross the professional line in a way the
  level-5 baseline does not. The escalation: 6 is a direct roast of effort/care; 7 attacks competence in the
  confrontational `ông/tôi` register; 8 attacks character in the street `mày/tao` register; 9 adds work-targeted
  profanity (`đm/vl`) and removes every internal restraint. How the gate resolves depends on the level AND where it
  came from:
  - **Levels 6, 7, 8 — from an ad-hoc flag (no standing preference):** show the level-appropriate warning and ask for
    an explicit AskUserQuestion confirmation BEFORE spawning any agent. Never infer consent from vague phrasing.
    On a "no", fall back one step: 8→7, 7→6, 6→5 (5 is the ungated baseline, so a fall-back to 5 just runs).
  - **Levels 6, 7, 8 — from the `critique_level` preference (standing consent):** the PO opted in deliberately by
    setting the preference, so do NOT re-ask every run. Print the one-line danger reminder each run (never run silently),
    in `--lang`: e.g. _"giọng mức 8 đang bật mặc định: critique sẽ chửi mày/tao, đánh vào năng lực lẫn tính cách; đừng
    chia sẻ ra ngoài; đổi bằng `critique_level` trong preferences hoặc `--level`."_ Then proceed.
  - **Level 9 — ALWAYS re-confirms, regardless of source.** Whether 9 comes from the `critique_level: 9` preference OR a
    `--level 9` flag, whenever the resolved level is 9 the workflow shows the STRONGEST warning + an AskUserQuestion
    confirm **every run** (never a silent standing reminder). The warning names exactly what level 9 removes (the polite
    pronoun, the no-profanity rule, the effort-only attack scope) AND what the floor still forbids (real violence
    threats / protected-characteristic slurs / self-harm / sexual / family-target profanity). **On decline, downgrade to
    8** (NOT to 6, NOT off). Vague phrasing is never consent. So 9 is settable and forceable, but it is never silent.
  - The **universal-harm floor** holds at EVERY level including 9, even with confirmation. The rule is the TARGET of the
    line, not its strength: profanity at the work is IN, anything aimed at who the author IS (body, family, region of
    origin, safety) is OUT. The authoritative spec is the IN/OUT adjudication table in
    `references/voice-and-tone.md` (the single home; agents reference it, never copy it). Every finding at every level
    still cites `ID:line` + ends in a fix; lv9 may interleave pure-scorn lines but each sits in a grounded finding block
    (scorn-count ≤ finding-count).

## 1b. Register seeding (first time a level-7-9 voice is used)

The level-7-9 register knobs (`critique_address_gender`, `critique_dialect`, `critique_profanity`) default to
`m`/`bac`/`strong`. The PO can hand-edit `preferences.yaml`, but they may not know the knobs exist. So the FIRST time a
run resolves to level ≥ 7 (whether by flag or the `critique_level` preference) AND the seed has not been offered before,
ask ONE `AskUserQuestion` batch (in `--lang`) to seed them, then persist via `preferences.save`:

- **Gender** (drives lv7 `ông/tôi` vs `bà/tôi`): "Xưng hô theo giới nào?" → `ông/tôi` (`m`) / `bà/tôi` (`f`).
- **Dialect** (drives lv8+ pronoun, the PO's OWN voice): "Giọng vùng nào của chính bạn?" → Bắc `mày/tao` (`bac`) /
  Trung `mi/tau` (`trung`) / Nam (`nam`).
- **Profanity strength** (lv9, work-targeted): "Mức chửi thề (nhắm vào spec)?" → tắt (`off`) / `đm/vl` (`abbrev`) /
  `đm/vl/vãi` (`strong`).

Ground the batch in the floor: state in one line that whatever they pick, the universal-harm floor holds (profanity
only at the work, never threats / protected-trait slurs / family-target / self-harm / sexual). Per `GATE-NEVER-ASSUME`,
these are stylistic seeds with documented defaults: if the PO skips, keep the defaults and say so. Persist the answers
AND append a `critique_register_seeded` marker to `dismissed_reminders` (via `preferences.save`) so the batch is asked
**once**, never re-offered. In `lang: en` the gender/dialect questions are no-ops (skip them; only ask profanity
strength, which still distinguishes EN level 7 from 8). An explicit `--level`-time register flag, if ever added, would
override; for now the batch is the only interactive seed.

## 2. Verdict ammo: NO forced `--validate` (refined D8)

`critique_scan.py` runs the structural checks FRESH (cheap) and reads cached LLM verdicts from `judgments.json`
(may be empty). The skill does **NOT** auto-run `--validate`, validate is reproducible/PO-facing and must not be
poisoned by a critique. If `cached_verdicts` is empty or the spec has drifted since the last validate, surface ONE
line, "chạy `--validate` trước để critique sắc hơn (có thêm phán quyết chất lượng làm đạn)", and proceed anyway.
The lens agents are the judgment layer; validate verdicts are supplementary ammo.

## 3. Build the bundle

```bash
./.claude/skills/.venv/bin/python3 \
  .claude/skills/product-spec-critique/scripts/critique_scan.py \
  --root <project> --scope <scope> --lang <lang> --level <N> \
  [--fresh] [--no-inherit] [--no-rollup] [--inherit deep]
```

Pass the resolved `--level` so the bundle's `provenance` verdict compares against the right level/register. Write the
bundle JSON to a SCRATCH path **outside** the fence, `$TMPDIR/product-spec-critique-bundle-<ts>.json` (it is scratch, not a spec
artifact; never under `docs/product/`). The bundle's top-level keys + the `digest` list shape are documented in
SKILL.md ("The bundle contract"); the new keys are `provenance`, `inherited_context`, `descendant_rollup`.

### 3a. Provenance branch — read `bundle["provenance"]["reuse"]` and act

This is the ECONOMIC gate (token savings), never a safety gate. `--fresh`/`--force` always forces `none`.

- **`full`** — drift=0 AND level/lang/register identical → the existing report is already current. Tell the PO (in
  `--lang`), point at `provenance.report`, offer `--fresh` to force a rebuild, and STOP (no lens fan-out, no consolidate).
- **`consolidate_only`** — drift=0 but level/lang/register differs → SKIP the lens fan-out (step 4). Load the FULL prior
  lens-findings array from the lens-cache `docs/product/.memory/critique-lens-cache/<lens_findings_hash>.json` (the
  `lens_findings_hash` is in the provenance result; this is the lens-findings store, NOT the lossy findings-index). Jump to step 5
  and re-consolidate those findings at the NEW level. The header notes "lens findings reused from `<report>@<ts>`". (If
  the lens-cache file is missing the script already downgraded the verdict to `relens` — you will never see a
  `consolidate_only` without its array.)
- **`relens`** — some node `body_hash` changed → **whole-scope re-lens** (full step 4). `changed_ids` is advisory
  provenance for the header ("N node(s) changed since last critique"), NOT a per-node dispatch; partial per-node re-lens
  is explicitly OUT of scope (YAGNI). Re-running the whole scope is correct, just not maximally frugal.
- **`none`** — full fresh run (steps 4→6).

**Bootstrap note:** the findings-index + lens-cache + critique-state start EMPTY. Run 1 of any scope has nothing to
reuse/inherit/rollup → `reuse: none` + empty `inherited_context`/`descendant_rollup` is correct-by-design, not a bug.
Reuse/inherit/rollup begin working from run 2+ (cross-critique context also needs the parent-before-child run order).

## 4. Fan out the lens agents (parallel, read-only)

Spawn the selected lenses concurrently via `Task`, each given: the bundle path, the active `--level`, `--lang`, and
(for market) the `--no-web` flag. Agent names: `product-critic`, `tech-critic`, `market-critic`,
`craft-critic`.

- **Scope-aware:** at a single-story scope the **market** lens is usually thin, spawn it but tell it the scope is
  narrow, or skip it and let the consolidator note the omission. At `--scope all` the market lens is most valuable.
- **Market grounding:** with no BRD `competitors:` AND `--no-web`, the market lens flags "thiếu căn cứ cạnh tranh"
  and never fabricates competitors. With web enabled it may research + cite (url in the finding's `source`).
- **Web-TTL gate (market lens).** Before the market lens fetches a URL, the main agent consults the web-cache
  (`critique_cache.get_cached(root, url, ttl_days=14)`): on a hit within TTL, pass the cached page text to the lens
  instead of re-fetching; on a miss/expiry, fetch then `critique_cache.put_cached(root, url, content)`. The cache is
  REUSE-ONLY — it never fabricates a page. `--refresh-web` forces a re-fetch + re-store (ignore the cache). `--no-web`
  still wins absolutely: no fetch AND no cache read.
- **Lens ignores `inherited_context` / `descendant_rollup` (anti-anchoring, 5 reasons).** The bundle carries these
  keys but the lens prompts are told to skip them, and you do NOT re-inject them into a lens spawn. Why the lens stays
  blind: (1) **anti-anchoring** — a fresh lens must judge THIS artifact on its own merits, not be primed by the parent's
  verdict; (2) **scope discipline** — the lens critiques `target_ids`, not the ancestry; (3) **consolidator's job (DRY)**
  — cross-critique context is rendered once, by the consolidator, not smeared across four lenses; (4) **×4 cost** —
  feeding context to every lens quadruples the prompt for no gain; (5) **double-surface** — an inherited item shown by
  both a lens AND the consolidator would double-count. The market exception ("see the parent's verdict, skip re-search")
  is handled by the web/judgment caches, NOT by feeding prose to the lens.
- Each agent returns a compact JSON findings array `{lens,evidence,critique,why_it_dies,fix,severity}` (+ `source`
  for market). The `critique` is NEUTRAL (voice is the consolidator's job). Collect whatever returns, **tolerate
  N<4** (a lens may return nothing/garbage).

## 5. Consolidate

**First, load the register + detail preferences and pass them in (do NOT skip).** Before spawning, the main agent
runs `preferences.load(root)` and extracts `critique_address_gender`, `critique_dialect`, `critique_profanity`,
`critique_detail_level`. These four values are INJECTED into the consolidate spawn prompt (and the humanize prompt in
5b). Without this the agents render the defaults (`m` / `bac` / `abbrev` / `standard`) regardless of the PO's config,
so a `gender: f` or `dialect: trung` preference would silently have no effect.

Spawn `critique-consolidator` (opus) with: the available lens findings arrays + the bundle's `prior_reports` +
the bundle's `inherited_context` + `descendant_rollup` (the consolidator is their ONLY consumer; render inherited
items in a SEPARATE "Kế thừa từ cha" section NOT in the tally, and the rollup `verdict_line` in the parent's section) +
`scope`/`lang`/`level` + the four register/detail prefs above. **On a `consolidate_only` provenance branch (step 3a),
the "lens findings arrays" you pass are the cached array loaded from the lens-cache, NOT a fresh fan-out** — same
consolidator, new level. It dedups cross-lens, enforces the mechanical
anti-overlap floor (drop byte-identical validate-echoes + findings missing why/fix), assigns final severity
(structural-backed ≥ major), picks the top-3, detects repeat-offense vs prior reports, flags DEC-worthy items, and
renders ONE markdown body in the voice.

> **Repeat-offense input-isolation boundary (A9).** Repeat-count is *presentation*, not *judgment*. The
> findings-index (`prior_reports` / `inherited_context` / `descendant_rollup`) reaches ONLY the consolidator, and the
> count + occurrence refs are attached AFTER each finding is already judged on its own merits — never fed back into the
> per-finding LENS inputs (`digest`, `structural_findings`). Litmus: *if the findings-index were deleted, would the set
> of flagged findings change? Must be NO.* A breach (repeat-count steering what gets flagged) would let a spec
> "age into" a worse verdict for no new defect. Guarded mechanically by
> `scripts/tests/test_repeat_offense_litmus.py` (the LLM body is non-deterministic and is not diffed; only the
> input-isolation is asserted).

The register knobs apply ONLY at their own threshold: at levels 7 to 9 it
renders the surface register from the prefs (`ông/tôi` vs `bà/tôi` by gender at 7; `mày/tao` vs `mi/tau` by dialect at
≥8; work-targeted profanity per `critique_profanity` at 9). **Levels 1 to 6 ignore the register knobs entirely** even
when passed, level 6 (roast) stays `bạn/tôi`; a `bà/tôi`/`mi/tau`/profanity leak at level ≤6 is a defect. It sizes the
report by `critique_detail_level` (concise = top-3 + one-line-per-lens, no extended pre-mortems; standard = current
full per-lens; verbose = full per-lens + extended why-it-dies + more sources). It writes through Gate 1 of the
humanizer (it consults `references/humanizer-and-anti-ai-tells.md` as it drafts) and reaffirms the universal-harm floor
+ grounding by reference to `voice-and-tone.md` (no copy). Its header NAMES any lens that did not complete. It returns
markdown TEXT, it does not write.

- **Render the level's labels in the findings, not just in your head.** The active level's why/fix label wording (the
  `voice-and-tone.md` table: e.g. L1 "Chỗ này đáng lưu tâm" / "Có thể thử", L3 "Toang ở đâu" / "Sửa") MUST actually
  appear on the rendered findings. A level-1 report whose findings carry no warm labels and read blunt is a level
  mismatch, the single most common voice defect.

## 5b. Humanize (Gate 2: the independent second eye)

**Humanized-output cache — check before spawning.** Compute a hash of the consolidator's markdown and consult the
humanized-cache (`critique_cache.get_humanized(root, hash)`): on a hit, REUSE the stored humanized text and skip the
spawn entirely; on a miss, spawn the humanizer (below), then store its result (`critique_cache.put_humanized(root, hash,
text)`). Identical consolidated input → identical humanized output, so this is a safe pure-token saving.

Spawn `critique-humanizer` (sonnet) with the consolidator's markdown + `--lang`/`--level` + the same
`critique_address_gender`/`critique_dialect`/`critique_profanity`/`critique_detail_level` values from step 5. It
rewrites the prose to strip AI-tells and Vietnamese word-for-word-translation tells per
`references/humanizer-and-anti-ai-tells.md`, while preserving the bite, the level's tone (the level 5/6 personal attack
stays; the level 7-9 harsher register AND the level-9 work-targeted profanity stay, do NOT soften `mày/tao` or strip
`đm/vl` as an "AI-tell"), every finding, every evidence `ID:line`, every fix, and the structure. The one exception is
the universal-harm floor: that clause is LEVEL-AGNOSTIC and OVERRIDES the preserve instruction, if preserving venom
would cross the floor (a real violence threat / protected-characteristic slur / self-harm / sexual / family-target
profanity), the humanizer DROPS the line, it does not soften-and-keep. It returns the cleaned markdown. This pass is
mandatory: the file written in step 6 is the humanized version, never the consolidator's raw draft. (Gate 1 =
consolidator self-applies the rules while writing; Gate 2 = this independent agent re-checks the finished draft.)

## 6. Write + snapshot + optional DEC bridge

Write the humanized markdown from step 5b (not the raw consolidator draft).

1. **Write** `docs/product/critique/<ts>-<scope>.md` with YAML frontmatter + the humanized markdown from step 5b
   (never the raw consolidator draft). Use the soft fence: the write target is under `docs/product/critique/`, confirm
   with `fs_guard.assert_under_docs_product` semantics (the main agent's own write; `critique_scan` owns the script-side
   fence for the snapshot). `<ts>` = compact UTC timestamp; `<scope>` = the scope id or `all`.
   - **Frontmatter (REQUIRED so the next run can decide reuse).** Compute the lens-findings hash of the FULL
     combined lens array (`critique_cache._lens_findings_hash(all_lens_findings)`), then build the block with
     `critique_provenance.build_report_frontmatter(root, scope, level, lang, register, lens_findings_hash)` (register =
     the prefs dict ONLY at level ≥ 7, else None) and PREPEND it above the `# Critique:` heading. The frontmatter carries
     `critique_scope`/`level`/`lang`/`register`/`body_hash`/`lens_findings_hash`/`bundle_version`. (On a
     `consolidate_only` rebuild, reuse the SAME `lens_findings_hash` you loaded the array from — the lens findings did
     not change, only the voice.)
   - **Sanitize the BODY first, THEN prepend frontmatter (ordering matters).** Even with the agent output contracts, an
     LLM occasionally leaks reasoning. Run the sanitize on the humanized markdown BEFORE adding the `---` block (the
     sanitize's "strip to first `#`" would otherwise eat the frontmatter):
     (a) **strip any preamble** — drop everything before the first line that starts with `# ` (the report heading);
     (b) **de-duplicate drafts** — if the text contains more than one `# Critique` heading (the agent emitted several
     draft copies), keep only the LAST complete copy;
     (c) **purge stray dashes** — replace any em/en dash (`—`, `–`) in the prose with a comma, colon, or period, but
     leave dashes inside `inline code`, fenced blocks, and verbatim spec quotes untouched.
     The sanitized body begins at `# Critique:` and contains the report exactly once, dash-clean; then prepend the
     frontmatter block so the file on disk is `---`…`---` + body.
2. **Lens-cache (this is what makes a FUTURE `consolidate_only` possible).** Persist the FULL combined lens
   array verbatim: `critique_cache.put_lens_findings(root, lens_findings_hash, all_lens_findings)` (same hash the
   frontmatter carries). On a `consolidate_only` rebuild the array already exists — re-`put` is a harmless idempotent
   write. Skip this only if there were no lens findings at all.
3. **Findings-index.** Feed this run's blockers + DEC-worthy to the index for the next critique's inherit /
   repeat-offense: `critique_inherit.index_report_findings(root, <ts>, scope, all_lens_findings)` (it filters to
   blockers + DEC-worthy itself).
4. **Snapshot**, refresh the drift marker:
   ```bash
   ./.claude/skills/.venv/bin/python3 \
     .claude/skills/product-spec-critique/scripts/critique_scan.py --root <project> --snapshot --scope <scope>
   ```
5. **Critique-state (the provenance fast-path source).** Record the per-scope marker so the NEXT run's fast-path
   can decide reuse without reading this report:
   `critique_provenance.record_critique_state(root, scope, level, lang, lens_findings_hash, blocker_count, register=<prefs-or-None>, report="docs/product/critique/<ts>-<scope>.md")`.
6. **DEC bridge (opt-in, GATEs apply):** for each DEC-worthy item the consolidator flagged, AskUserQuestion
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
