# Brainstorm — N1 finding-level fingerprint (spec-span anchor)

**Skill:** `product-spec-critique` · **Backlog:** N1 (low/med, enhancement) · **Date:** 2026-06-06
**Decision:** Solution 3 + 3b (anchor fingerprint to cited spec-line text + severity)

---

## Problem statement

Repeat-offense + cross-critique inherit/rollup match by **NODE** (`critique_inherit._node_of` strips `:line`).
Line-shift resilient but coarse:
- **(a)** can't distinguish 2 different findings on same node (PRD w/ 4 blockers → "node has a repeat").
- **(b)** index key `<evidence_id>@<ts>` (`PRD-FUND:101@ts`) embeds line; same logical finding after line drift
  (`:103`) → new eid → `_index_rows` keeps both → `blocker_count` inflated 2× for one logical blocker.

Root cause: **no stable per-finding identity**. `evidence_id = node:line` — both parts unstable for identity
(line drifts; node too coarse).

### Grounded codebase facts
- Index `critique-findings-index.json` committed under `.memory/`; key `eid@ts`; row = `severity,why,fix,dec_worthy`;
  LOSSY (blocker + DEC-worthy only).
- 3 index consumers (`critique_inherit.py`): `_index_rows` (dedup per eid, latest ts) → `build_inherited_context`
  (parent→child) + `build_descendant_rollup` (child→parent, `blocker_count` per node). All collapse via `_node_of`.
- **Repeat-offense vs prior reports is LLM-side** (consolidator reads `prior_reports` text), NOT index-fed. N1 improves
  inherit/rollup dedup+count accuracy; does NOT change the LLM repeat mechanism.
- Evidence format = `node:line`, single int line (`PRD-AUTH:5`), no ranges. Voice contract mandates every finding cite
  a real `<id>:<line>` from the bundle.
- `spec_graph` nodes carry `file` → node→source resolvable at index-write time.

---

## Approaches evaluated

| # | Approach | Solves (a) | Solves (b) | Fragile? | Verdict |
|---|----------|:--:|:--:|:--:|---------|
| 1 | hash LLM `why` (backlog literal) | ✓ | ✓ | **Yes** — LLM rewording → new hash → misses repeat | ❌ reject (fragile) |
| 2 | node-only (strip line) | ✗ | half (can't tell drift vs 2 distinct) | No | ❌ reject (coarse, mis-fixes b) |
| **3** | **anchor to cited spec-line TEXT** | **✓** | **✓** | **No** — anchored to deterministic spec content | ✅ **chosen** |
| 3b | + `severity` in hash | ✓ | ✓ | No | ✅ **folded in** |

Approach 1 rejected per PO directive "no workaround, no fragile solution" — `why` is LLM-generated, paraphrase-unstable;
aggressive normalization trades fragility for collision risk. Approach 2 can't separate "same blocker drifted" from
"two distinct blockers" → under-counts.

---

## Chosen solution — Solution 3 + 3b

**Fingerprint anchored to the spec text the finding cites**, not LLM prose nor the volatile line number.

```
finding_fingerprint = sha256(node + "\0" + severity + "\0" + normalize(spec_line_text))[:N]
```

### Mechanics (write-time, `index_report_findings`)
1. Split `evidence_id` → `node` + `line`.
2. Resolve `node` → source file via `spec_graph` nodes[].file.
3. Read file, take text at `line` (1-indexed).
4. Normalize **lightly**: trim, collapse internal whitespace, lowercase, strip leading markdown bullet/heading markers.
   (Light only — spec text is deterministic; aggressive token-sort/stopword would add collision risk for no gain.)
5. `finding_fingerprint = sha256(node + "\0" + severity + "\0" + normalized_text)`.

### Why robust (non-fragile)
- Anchored to **deterministic spec content**, independent of how the LLM phrases `why`.
- **Line-drift immune:** inserting a paragraph above moves line 101→103 but the line's TEXT is unchanged → same
  fingerprint → correctly recognized as the same finding. (solves b at the root)
- **Per-finding granularity:** two findings citing different lines/spans of one node → different text → different
  fingerprint. (solves a)
- **Spec text genuinely edited → new fingerprint, which is CORRECT** — the criticized content changed, so it's a new
  finding semantically.
- **3b severity** disambiguates two findings on the same line at different severities; index is blocker+DEC-worthy-only
  (LOSSY) so severity-band volatility is narrow → low risk of false splits.

### Storage & back-compat (additive, no migration)
- Add `finding_fingerprint` field to the row; **keep key `eid@ts`** (additive, not key-replacing — avoids orphaning
  committed entries).
- Bump index `version: 1 → 2`.
- **Tolerant read:** old rows lacking `finding_fingerprint` → fall back to `evidence_id` (current behavior). No manual
  migration; committed `.memory/` index keeps working.

### Read-path changes (index-fed only)
- `_index_rows`: dedup by `finding_fingerprint` (fallback eid), keep latest ts.
- `build_descendant_rollup`: count distinct fingerprints per node for `blocker_count` (fixes 2× inflation).
- `build_inherited_context`: dedup candidates by fingerprint.
- `index_report_findings`: compute + write fingerprint.

### Graceful degradation (correct, not a workaround)
- Line out of range / file unreadable / node deleted → fall back to `evidence_id` keying. Source-absent is a real state;
  degrading to prior behavior is correct, not a hack.

---

## Scope

**IN:** `index_report_findings`, `_index_rows`, `build_descendant_rollup`, `build_inherited_context`,
`upsert_findings` (store the new field), tests.
**OUT (YAGNI):** LLM consolidator repeat-offense (`prior_reports` path) — separate mechanism, no change this round.

### Touchpoints
- `.claude/skills/product-spec-critique/scripts/critique_cache.py` (`upsert_findings`, `_INDEX_FIELDS`, version).
- `.claude/skills/product-spec-critique/scripts/critique_inherit.py` (`_index_rows`, `build_*`, `index_report_findings`,
  new spec-line resolver/normalizer helper).
- `.claude/skills/product-spec-critique/scripts/tests/test_critique_cache.py`, `test_critique_inherit.py`.
- Reads (no edit) `product-spec/scripts/spec_graph.py` for node→file.

---

## Acceptance criteria
1. Same logical blocker re-critiqued after a line shift (text unchanged, `:101`→`:103`) → **one** entry counted, not two.
2. Two distinct blockers on the same node → **two** distinct fingerprints (granularity preserved).
3. Editing the criticized spec line → new fingerprint (treated as new finding).
4. Old committed index (no `finding_fingerprint`) loads without error; falls back to eid behavior.
5. Source unreadable/line-out-of-range → no crash, falls back to eid keying.
6. Full existing suite green (anchor = collected passing-case count via `pytest --co -q`, no regression).

## Out of scope / non-goals
- No change to LLM repeat-offense detection.
- No fuzzy/semantic matching of `why` text.
- No index key-format change / migration tooling.

## Risks
- **Residual LLM citation dependency:** robustness assumes the LLM cites the same source line for the same issue across
  runs. Citing a concrete line is far more stable than free-form prose, and voice contract mandates the citation — but
  it can't be eliminated (findings are LLM-authored). Accepted, documented.
- **Same-line collision:** two genuinely different findings on the exact same line collapse — rare; severity (3b)
  mitigates partially.

## Success metrics
- `blocker_count` no longer inflates across re-critiques with line drift (criterion 1 test).
- Per-finding granularity retained (criterion 2 test).
- Zero regression in existing collected test count.

---

## Open questions
- Fingerprint hash truncation length `N` — pick at plan time (suggest 16 hex chars; collision-safe for this scale). Not
  blocking.
