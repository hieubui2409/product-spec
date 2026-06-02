# lens-frameworks — the 4 critique framework banks (single home)

The single DRY home for each lens's frameworks. Agents carry a compact checklist and reference THIS for the full bank.
Each row: framework → the diagnostic question to ask the spec → the failure signature to flag.

---

## Product lens (opus): "is this worth building?"

| Framework | Diagnostic question | Failure signature |
|-----------|---------------------|-------------------|
| **JTBD** | What job is a real persona hiring this to do? | Story with a hollow/circular "so that…"; feature in search of a user. |
| **Value Prop Canvas** | Which stated pain does it relieve / gain does it create (per vision/BRD)? | Feature mapped to no pain or gain anywhere upstream. |
| **Kano** | Must-be, performance, or delighter? | Gold-plating a delighter while a must-be is missing. |
| **RICE-integrity** | Do reach/impact claims square with the persona set + BRD goals? | A `must` story serving a persona the BRD never names as a buyer. |
| **Riskiest-assumption** | What single unproven belief, if wrong, kills this? | No assumption named; the spec assumes success. |
| **Opportunity-solution-tree** | Problem-first or solution-first? | AC describes a UI mechanism with no problem behind it. |

Headline catches: **feature nobody needs · fake persona vs BRD buyer · gold-plating · solution-first**.

---

## Tech / feasibility lens (sonnet): "is this buildable & testable?"

| Framework | Diagnostic question | Failure signature |
|-----------|---------------------|-------------------|
| **INVEST** | Independent, Negotiable, Valuable, Estimable, Small, Testable? | A story bundling three features; one no engineer could size. |
| **Given-When-Then testability** | Can each AC become a deterministic test? | AC with no observable outcome ("works well", "is fast"). |
| **Hidden dependencies** | Does it silently assume another story/system exists? | AC referencing data/flows defined nowhere upstream; empty `depends_on` but needs a prerequisite. |
| **Complexity-vs-value** | Build effort vs the value in ancestry? | A `could`/delighter demanding the hardest integration. |
| **NFR gaps** | Are perf/security/scale/error-paths present where they matter? | An auth/payment story with only happy-path AC. |

Headline catches: **untestable AC · non-INVEST story · assume-success (no error/edge paths)**.
Rule: a fix is a SPEC change (rewrite the AC, split the story, add the NFR), never implementation code.

---

## Market lens (sonnet + web): "will anyone pay, and why this?"

| Framework | Diagnostic question | Failure signature |
|-----------|---------------------|-------------------|
| **Lean Canvas** | Coherent problem → solution → unfair-advantage → revenue line? | No revenue path back to the BRD goal. |
| **Porter (light)** | What stops a competitor copying this next quarter? | Zero switching cost / no defensibility. |
| **Blue Ocean** | Real differentiator or me-too in a red ocean? | Parity-only features matching competitors with nothing new. |
| **Unit-economics** | Does value created exceed cost-to-serve at BRD scale? | A giveaway with no monetization in sight. |
| **JTBD-competition** | What is the user firing to hire this (incl. "do nothing")? | Ignores the real alternative the user already uses. |

Headline catches: **me-too · no revenue path · no moat**.
Grounding rule: prefer BRD `competitors:`; may cite web (put the url in `source`). With neither + `--no-web`, flag
"thiếu căn cứ cạnh tranh", NEVER fabricate a competitor or a market fact.

---

## Craft / editorial lens (haiku): "is it written well?" (validate never checks this)

| Framework | Diagnostic question | Failure signature |
|-----------|---------------------|-------------------|
| **Plain-language** | Would a non-technical PO understand it on first read? | Jargon, nested clauses, passive fog. |
| **CSI-4Cs** | Clear, Concise, Consistent, Correct? | A 200-word AC saying one thing; a typo; an internal contradiction. |
| **Unmeasurable-adjective audit** | Any "fast/easy/intuitive/seamless/robust" with no number? | An adjective masquerading as a requirement. |
| **Terminology consistency** | Same term for a thing as the ancestry uses? | "user" here, "shopper" upstream, "member" two lines later. |
| **Show-don't-tell** | Concrete examples, or only abstract claims? | A story that asserts value but shows no example interaction. |

Headline catches: **typos · vague adjectives · term drift · wall-of-text · no examples**.
Severity discipline: a typo is `minor`; reserve `major`/`blocker` for ambiguity that genuinely changes what gets built.

---

## Anti-overlap (all lenses)

Do not restate a `structural_findings`/`cached_verdicts` label verbatim. The mechanical floor (consolidator-enforced):
a finding line must NOT be byte-identical to a structural-finding `detail`, AND must carry non-empty `why_it_dies` +
`fix`. Your value is precisely what `--validate` cannot say, the consequence, the market, the craft, the cross-lens.
