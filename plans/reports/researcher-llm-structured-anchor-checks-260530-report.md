# LLM Structured-Anchor Checks — Prompt Design Spec
**Date:** 2026-05-30 | **Skill:** cleanmatic:product-spec | **Phase:** TDD / eval design

---

## 0. Ground Truth From Existing Checks

Pattern established by `core_value_drift` / `invest_quality` / `vagueness`:
- Input = serialized frontmatter fields, never free prose alone
- Output = JSON finding or `no-finding` object (not a prose explanation)
- Condition = checked against explicit named fields in the input block
- Conservative default = `no-finding` when uncertain

The two new checks extend this same pattern. Key delta: they require **multi-field AND logic** and a `cited_data` block that names each anchor value consumed. Existing checks do not require `cited_data`; adding it here is the primary anti-hallucination lever.

---

## 1. Finding JSON Shape (shared contract for both checks)

Extended from the base findings schema in `validation-rules-spec.md`. The `context` field is now REQUIRED (not optional) for LLM checks.

```json
{
  "check": "time_realism" | "competitive_drift",
  "severity": "warn",
  "artifact_id": "<epic-or-PRD-id>",
  "file": "<path-relative-to-root>",
  "detail": "<short human message — EN or VI per lang field>",
  "context": {
    "cited_data": {
      /* All anchor values the LLM read to reach its decision.
         Must match the INPUT_BLOCK fields exactly.
         REQUIRED — a finding without cited_data is INVALID. */
    },
    "threshold_crossed": "<which rule fired, verbatim from prompt>"
  }
}
```

**No-finding object** (LLM must emit this, never silence):
```json
{ "check": "time_realism" | "competitive_drift", "finding": null, "reason": "below_threshold" | "missing_anchor" }
```

Rationale for explicit no-finding: forces the LLM to commit to a verdict; prevents silent pass-through that obscures missing-anchor cases.

---

## 2. Check 1 — `time_realism`

### 2.1 Input Block (serialized per-epic)

Script extracts these fields and passes them to the LLM as a structured block. All fields must be present; if any are absent, the block is marked `incomplete: true`.

```json
{
  "artifact_id": "PRD-AUTH-E2",
  "artifact_type": "epic",
  "lang": "en",
  "size": "L",
  "horizon": "now",
  "target_date": "2026-06-12",
  "today_date": "2026-05-30",
  "days_remaining": 13,
  "child_story_count": 7,
  "incomplete": false
}
```

Fields `days_remaining` and `child_story_count` are **pre-computed by the script** — the LLM does NOT do arithmetic. This eliminates a class of arithmetic hallucination.

### 2.2 Prompt Scaffold

```
You are a product-spec validator. Your job is to check one epic or story for time realism.

TASK: Determine if the deadline is unrealistic given the scope anchors below.

RULE — Only emit a warning if ALL THREE of the following are true simultaneously:
  1. size is "L"            (large scope)
  2. child_story_count >= 6 (many sub-deliverables)
  3. days_remaining < 21    (fewer than 3 weeks to target_date)

If ANY condition is NOT met → emit no-finding.
If ANY anchor field is missing or incomplete=true → emit no-finding, reason="missing_anchor".
If uncertain about any condition → emit no-finding.

INPUT:
<ANCHOR_BLOCK>
{
  "artifact_id": "...",
  "size": "...",
  "horizon": "...",
  "target_date": "...",
  "today_date": "...",
  "days_remaining": <integer>,
  "child_story_count": <integer>,
  "incomplete": <bool>
}
</ANCHOR_BLOCK>

OUTPUT CONTRACT — Return exactly one of these two JSON shapes, nothing else:

Shape A (finding):
{
  "check": "time_realism",
  "severity": "warn",
  "artifact_id": "<from input>",
  "detail": "<EN: 'Epic {id}: size=L with {N} stories, target_date {date} is {days} days away — may be unrealistic.' | VI: translated equivalent>",
  "context": {
    "cited_data": {
      "size": "<value from input>",
      "child_story_count": <value from input>,
      "days_remaining": <value from input>,
      "target_date": "<value from input>",
      "horizon": "<value from input>"
    },
    "threshold_crossed": "size=L AND child_story_count>=6 AND days_remaining<21"
  }
}

Shape B (no finding):
{
  "check": "time_realism",
  "finding": null,
  "reason": "below_threshold" | "missing_anchor"
}

Do not add prose. Do not speculate about team velocity. Do not flag based on the horizon value alone.
```

### 2.3 Threshold Rationale

| Condition | Value | Justification |
|-----------|-------|---------------|
| `size=L` | enum exact match | L = large; S/M cannot trigger |
| `child_story_count >= 6` | ≥6 | ≥6 stories is a meaningful decomposition; <6 could be incomplete, not risky |
| `days_remaining < 21` | <21 days | 3 weeks = common sprint ceiling for L work; conservative (not 3 weeks) |

All three must fire. Two of three is NOT flagged. This is the most important anti-hallucination lever — the LLM cannot make a judgment call about "close enough".

---

## 3. Check 2 — `competitive_drift`

### 3.1 `competitive_parity` Field (new PRD frontmatter field)

This field is not in the current spec. The design requires it. Schema:

```yaml
# in prds/<slug>.md frontmatter
competitive_parity:
  - competitor: "Shopify"
    parity: behind        # enum: ahead | parity | behind | none
  - competitor: "WooCommerce"
    parity: behind
  - competitor: "Wix"
    parity: parity
```

Enum `none` = this competitor is not relevant to this PRD (e.g., different market). Script validation: `unknown_enum` if a `parity` value is not in `{ahead, parity, behind, none}`.

### 3.2 Input Block (serialized per-PRD)

```json
{
  "artifact_id": "PRD-CHECKOUT",
  "artifact_type": "prd",
  "lang": "en",
  "scope": "core-value",
  "competitive_parity": [
    { "competitor": "Shopify",     "parity": "behind" },
    { "competitor": "WooCommerce", "parity": "behind" },
    { "competitor": "Wix",        "parity": "parity" }
  ],
  "competitors_with_data": 3,
  "incomplete": false
}
```

Script pre-computes `competitors_with_data` (count of entries where parity != "none"). If `competitors_with_data < 1`, set `incomplete: true`.

### 3.3 Prompt Scaffold

```
You are a product-spec validator. Your job is to check one PRD for competitive drift.

TASK: Determine if the feature is losing competitive advantage, using only the anchors below.

RULE — Only emit a warning if ALL THREE of the following are true simultaneously:
  1. scope is "core-value"   (feature is part of the core value proposition)
  2. competitors_with_data >= 2  (at least 2 relevant competitors with ratings)
  3. ALL entries where parity != "none" have parity == "behind"
     (not a single "ahead" or "parity" entry among relevant competitors)

If ANY condition is NOT met → emit no-finding.
If incomplete=true OR competitors_with_data < 2 → emit no-finding, reason="missing_anchor".
If uncertain about any condition → emit no-finding.

INPUT:
<ANCHOR_BLOCK>
{
  "artifact_id": "...",
  "scope": "...",
  "competitive_parity": [ { "competitor": "...", "parity": "..." }, ... ],
  "competitors_with_data": <integer>,
  "incomplete": <bool>
}
</ANCHOR_BLOCK>

OUTPUT CONTRACT — Return exactly one of these two JSON shapes, nothing else:

Shape A (finding):
{
  "check": "competitive_drift",
  "severity": "warn",
  "artifact_id": "<from input>",
  "detail": "<EN: 'PRD {id}: scope=core-value but behind all {N} competitors with data ({list}) — review competitive position.' | VI: translated equivalent>",
  "context": {
    "cited_data": {
      "scope": "<value from input>",
      "competitors_with_data": <value from input>,
      "all_behind_competitors": ["<competitor names where parity=behind>"]
    },
    "threshold_crossed": "scope=core-value AND competitors_with_data>=2 AND all_relevant_parity=behind"
  }
}

Shape B (no finding):
{
  "check": "competitive_drift",
  "finding": null,
  "reason": "below_threshold" | "missing_anchor"
}

Do not invent competitive context. Do not reason about market trends. Do not flag if any competitor has parity="ahead" or parity="parity".
```

### 3.4 Threshold Rationale

| Condition | Value | Justification |
|-----------|-------|---------------|
| `scope=core-value` | enum exact match | non-core PRDs losing ground is NOT drift by definition |
| `competitors_with_data >= 2` | ≥2 | single data point is insufficient signal; prevents single-competitor flags |
| `all relevant parity = behind` | unanimous | even one "parity" entry means the feature is at market level, not losing |

---

## 4. Anti-Hallucination Guardrails (cross-cutting)

### 4.1 Phrasing Patterns That Force Grounding

| Pattern | Purpose |
|---------|---------|
| `"Only emit a warning if ALL THREE of the following are true simultaneously"` | Prevents partial-match triggering |
| `"If ANY anchor field is missing or incomplete=true → emit no-finding"` | Prevents extrapolation from partial data |
| `"If uncertain about any condition → emit no-finding"` | Conservative default is explicit |
| `"Do not speculate about [team velocity / market trends]"` | Closes the "vibes" inference path |
| `"Return exactly one of these two JSON shapes, nothing else"` | Output format constraint prevents prose hallucination |
| Pre-computed arithmetic (`days_remaining`, `competitors_with_data`) | Removes numeric reasoning from LLM scope |
| `cited_data` required in finding | Makes grounding verifiable post-hoc; invalid if absent |

### 4.2 Anti-Patterns to Avoid

These prompt framings reliably produce false positives and must NOT appear:

| Anti-pattern | Why it fails |
|-------------|-------------|
| `"Does this deadline seem reasonable?"` | Vibes-based; model projects from training distribution, not from anchors |
| `"Consider the complexity of this epic"` | Invites inference beyond the provided fields |
| `"Is this company behind its competitors?"` | Scope too wide; imports outside-context knowledge |
| `"What is your confidence that this deadline is unrealistic?"` | Calibrated confidence ≠ structured threshold; produces numeric hallucinations |
| `"Flag if the horizon is 'now' AND the deadline seems close"` | "seems close" is subjective; no concrete threshold |
| Asking for explanation before JSON | Chain-of-thought before output biases toward finding when none exists; always output JSON first |
| `"List any concerns you have about this epic"` | Open-ended; model fills space with invented concerns |
| Missing-field tolerance (`"If a field is missing, infer from context"`) | Explicitly forbidden; must produce no-finding on missing anchor |

Source grounding: structured prompting with explicit grounding requirements and conditional abstention reduces hallucination rates measurably per 2025 research on prompt-induced hallucination mitigation ([arxiv.org/pdf/2601.02739](https://arxiv.org/pdf/2601.02739), [datadoghq.com](https://www.datadoghq.com/blog/ai/llm-hallucination-detection/)).

---

## 5. Eval Scenarios (eval/evals.json additions)

Format follows existing eval schema. All scenarios include `_gating: "llm_judgment"`.

### 5.1 Check: `time_realism` (3 scenarios)

**Scenario TR-1 — True Positive (must flag)**
```json
{
  "id": "TR-1",
  "_check": "time_realism",
  "_gating": "llm_judgment",
  "input": {
    "artifact_id": "PRD-CHECKOUT-E3",
    "size": "L",
    "horizon": "now",
    "target_date": "2026-06-10",
    "today_date": "2026-05-30",
    "days_remaining": 11,
    "child_story_count": 8,
    "incomplete": false
  },
  "expected": "finding",
  "assertion": "Output must be Shape A with check=time_realism, cited_data.size=L, cited_data.child_story_count=8, cited_data.days_remaining=11"
}
```

**Scenario TR-2 — Borderline (must NOT flag)**

Epic is L with many stories but 25 days remaining — exceeds 21-day threshold. LLM must return no-finding.
```json
{
  "id": "TR-2",
  "_check": "time_realism",
  "_gating": "llm_judgment",
  "input": {
    "artifact_id": "PRD-AUTH-E1",
    "size": "L",
    "horizon": "now",
    "target_date": "2026-06-24",
    "today_date": "2026-05-30",
    "days_remaining": 25,
    "child_story_count": 7,
    "incomplete": false
  },
  "expected": "no-finding",
  "assertion": "Output must be Shape B (finding: null). days_remaining=25 does NOT satisfy <21. Must not flag because the third condition fails."
}
```

**Scenario TR-3 — Missing Anchor (must return no-finding with missing_anchor)**
```json
{
  "id": "TR-3",
  "_check": "time_realism",
  "_gating": "llm_judgment",
  "input": {
    "artifact_id": "PRD-ONBOARDING-E1",
    "size": "L",
    "horizon": "now",
    "target_date": null,
    "today_date": "2026-05-30",
    "days_remaining": null,
    "child_story_count": 9,
    "incomplete": true
  },
  "expected": "no-finding",
  "assertion": "Output must be Shape B with reason=missing_anchor. target_date is null; incomplete=true. Must not attempt to infer days remaining."
}
```

### 5.2 Check: `competitive_drift` (3 scenarios)

**Scenario CD-1 — True Positive (must flag)**
```json
{
  "id": "CD-1",
  "_check": "competitive_drift",
  "_gating": "llm_judgment",
  "input": {
    "artifact_id": "PRD-CHECKOUT",
    "scope": "core-value",
    "competitive_parity": [
      { "competitor": "Shopify",     "parity": "behind" },
      { "competitor": "WooCommerce", "parity": "behind" },
      { "competitor": "Wix",        "parity": "behind" }
    ],
    "competitors_with_data": 3,
    "incomplete": false
  },
  "expected": "finding",
  "assertion": "Output must be Shape A with check=competitive_drift, cited_data.scope=core-value, cited_data.all_behind_competitors=[Shopify,WooCommerce,Wix]"
}
```

**Scenario CD-2 — Borderline (must NOT flag)**

One competitor at parity — not all-behind. Must not flag.
```json
{
  "id": "CD-2",
  "_check": "competitive_drift",
  "_gating": "llm_judgment",
  "input": {
    "artifact_id": "PRD-CHECKOUT",
    "scope": "core-value",
    "competitive_parity": [
      { "competitor": "Shopify",     "parity": "behind" },
      { "competitor": "WooCommerce", "parity": "parity" },
      { "competitor": "Wix",        "parity": "behind" }
    ],
    "competitors_with_data": 3,
    "incomplete": false
  },
  "expected": "no-finding",
  "assertion": "Output must be Shape B. WooCommerce parity=parity means NOT all-behind. The third condition fails. Must not flag."
}
```

**Scenario CD-3 — Missing Anchor (must return no-finding with missing_anchor)**

`scope=in` (not core-value) AND only one competitor with data — two conditions fail.
```json
{
  "id": "CD-3",
  "_check": "competitive_drift",
  "_gating": "llm_judgment",
  "input": {
    "artifact_id": "PRD-AUTH",
    "scope": "in",
    "competitive_parity": [
      { "competitor": "Shopify", "parity": "behind" }
    ],
    "competitors_with_data": 1,
    "incomplete": false
  },
  "expected": "no-finding",
  "assertion": "Output must be Shape B. scope=in (not core-value) and competitors_with_data=1 (<2) — two independent conditions fail. If LLM flags, it has hallucinated."
}
```

---

## 6. Bilingual Label Contract

- All `detail` strings in findings must localize per the artifact's `lang` field.
- IDs, enum values, field names, competitor names stay English in both languages.
- `cited_data` keys stay English always.
- Example VI detail for `time_realism`: `"Epic {id}: size=L với {N} stories, target_date {date} còn {days} ngày — có thể không thực tế."`
- Example VI detail for `competitive_drift`: `"PRD {id}: scope=core-value nhưng đứng sau tất cả {N} đối thủ ({list}) — xem lại vị thế cạnh tranh."`

---

## 7. Integration Notes (no code changes — plan input only)

**Where these checks slot in** — `workflow-validate.md → Step 2` (LLM judgment layer), after structural scripts. Add two new passes:
- `time_realism` — per-epic that has `target_date` set
- `competitive_drift` — per-PRD that has `competitive_parity` in frontmatter

**Script responsibility** — extract + pre-compute the input block JSON; pass to LLM. LLM never reads the frontmatter file directly.

**`competitive_parity` field** — currently undocumented in `frontmatter-and-id-spec.md`. Needs a new entry in the PRD domain fields section before implementation. The field is optional (absence = `incomplete: true` → no-finding).

**`cited_data` validation** — the orchestrator must reject a finding that has `cited_data: null` or `cited_data: {}` as invalid output (same as rejecting a finding with no `artifact_id`).

---

## 8. Validation Rule Catalog Additions

Two rows to append to the check catalog table in `validation-rules-spec.md`:

| ID | Owner | Severity | Trigger | Message Template |
|----|-------|----------|---------|------------------|
| `time_realism` | LLM | warn | epic: size=L AND child_story_count≥6 AND days_remaining<21 | "Epic {id}: size=L with {N} stories, target_date {date} is {days} days away — may be unrealistic." |
| `competitive_drift` | LLM | warn | PRD: scope=core-value AND competitors_with_data≥2 AND all relevant parity=behind | "PRD {id}: scope=core-value but behind all {N} competitors ({list}) — review competitive position." |

---

## Unresolved Questions

1. **`competitive_parity` field not in current spec** — must be added to `frontmatter-and-id-spec.md` (PRD domain fields) and the PRD template before the LLM prompt can be activated. Is this in scope for the same TDD phase, or a prerequisite phase?

2. **`target_date` on epics** — the current frontmatter spec does not include `target_date` as a defined field for epics. Same question: add to spec first, or treat as optional-optional (presence gates the check)?

3. **Threshold calibration** — the thresholds (days<21, stories≥6) are reasonable defaults but project-specific. Should they be config in `pack.manifest.yaml` or hardcoded in the prompt? Hardcoded is KISS; configurable is more correct for teams with different sprint cadences.

4. **`competitive_drift` scope edge case** — PRDs with `scope=out` but `competitive_parity` data present: currently would not flag (scope≠core-value). Is that the intended behavior? (Answer: yes per design — only core-value loss is drift.)

5. **Eval fixture format** — the 6 new eval scenarios above use an `input` object that differs from existing evals (which reference fixture files). Is inline input acceptable in `evals.json`, or must all inputs be in `eval/fixtures/`?

---

**Status:** DONE
**Summary:** Produced plan-ready prompt scaffolds for `time_realism` and `competitive_drift` with structured input blocks, strict AND-logic thresholds, `cited_data`-required output contracts, anti-hallucination guardrails, and 6 eval scenarios (TP / borderline / missing-anchor per check). Two new frontmatter fields (`competitive_parity`, `target_date` on epics) are prerequisites not yet in the spec.

Sources:
- [Mitigating Prompt-Induced Hallucinations in LLMs via Structured Reasoning](https://arxiv.org/pdf/2601.02739)
- [Detecting hallucinations with LLM-as-a-judge: Prompt engineering and beyond (Datadog)](https://www.datadoghq.com/blog/ai/llm-hallucination-detection/)
- [7 Prompt Engineering Tricks to Mitigate Hallucinations — MachineLearningMastery](https://machinelearningmastery.com/7-prompt-engineering-tricks-to-mitigate-hallucinations-in-llms/)
