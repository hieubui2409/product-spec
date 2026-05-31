---
type: prior-decisions-baseline
date: 2026-05-29T03:03
purpose: Wave-4 cross-validation baseline — what's already been raised + fixed, deferred, or rejected across 3 prior review rounds
sources:
  - brainstorm-decisions-260528-0818-cleanmatic-product-spec-skill-report.md
  - from-cook-to-pm-260528-1747-product-spec-skill-implementation-report.md
  - code-review-260528-1945-product-spec-skill-hardcore-4-wave-report.md
  - from-fix-to-pm-260528-2011-product-spec-skill-crit-high-remediation-report.md
  - code-review-260528-2110-product-spec-skill-hardcore-4wave-rereview-report.md
  - from-fix-to-pm-260528-2141-product-spec-skill-all-findings-remediation-report.md
  - from-tester-to-pm-260528-2218-product-spec-skill-blind-subagent-full-coverage-report.md
  - from-fix-to-pm-260528-2229-product-spec-skill-deferred-items-remediation-report.md
  - from-ck-code-review-to-planner-260528-2241-cleanmatic-product-spec-skill-hardcore-review-report.md
  - from-ck-code-review-to-fixed-260528-2303-cleanmatic-product-spec-skill-fix-summary-report.md
---

# Wave 4 Baseline — Prior Decisions, Fixes, Deferrals

Status at HEAD: pytest 76/76, worked example clean, 17 review findings actioned across 3 rounds.

## Sticky Brainstorm Decisions (NEVER auto-reverse)

Citations: `brainstorm-decisions-260528-0818-*.md` §-numbers.

- **§1 Namespace:** `cleanmatic:product-spec`. Single user-facing skill. Lean SKILL.md + on-demand `references/`. Single product per workspace.
- **§1 Lang:** `lang: en|vi` per PRODUCT.md/artifact. Default EN. Localizes PROSE + interview only; frontmatter KEYS + IDs stay English.
- **§2 Hierarchy:** Vision → 1 BRD → many PRDs → Epics → Stories+AC. STRICT traceability. PRD owns narrative/scope/NFR/metrics; stories are decomposition.
- **§2 BRD count:** ONE BRD product-wide; MANY PRDs per feature.
- **§3 PRODUCT.md = thin labels-only** (DRY); depth lives in vision/BRD. Path: `docs/product/PRODUCT.md`.
- **§4 Script vs LLM split:** Scripts = structural/deterministic only (parse, graph, orphan/dangling, AC PRESENCE, ID integrity, matrix). LLM = INVEST quality, AC testability, off core-value, semantic duplicate, contradiction, judgment. NON-NEGOTIABLE.
- **§4 Severity:** Configurable, DEFAULT WARN. `--strict` blocks on hard errors (broken traceability / missing AC). Never block by default.
- **§5 Deps:** stdlib + pyyaml only. NO jinja2. Simple `{{token}}` substitution.
- **§5 Scripts emit JSON; never mutate docs; never auto-fix.**
- **§6 Interview:** AskUserQuestion batches ≤4 with defaults. Phased + resumable via `docs/product/.session.md` (committed).
- **§7 Output layout:** typed subfolders under `docs/product/`. Epics & stories = separate files each with full frontmatter.
- **§7 Delta update flow:** load existing, ask only what changed, regenerate affected artifacts, append change-log. NEVER overwrite manual prose silently.
- **§7 Status lifecycle:** `draft → review → approved`. Frontmatter = source of truth.
- **§8 Viz formats = 3** (ASCII + Mermaid + self-contained HTML). SVG/PNG DROPPED at validate-gate to avoid binary deps. NOT 4.
- **§8 Mermaid:** inline-vendored (offline self-contained). No runtime CDN.
- **§8 Viz library:** in-skill self-contained Python; single graph JSON source of truth.
- **§11 IDs:** parent-scoped `BRD-G<n>`, `PRD-<SLUG>`, `PRD-<SLUG>-E<n>`, `PRD-<SLUG>-E<n>-S<n>`. Slug ≤16 chars uppercase ASCII. Stored in frontmatter.
- **§12 No engineering handoff** (product-only, no ck:plan export).
- **§13 v1 = everything** (full surface; user explicitly rejected phased MVP).
- **§14 Templates carry REQUIRED vs OPTIONAL section markers.**
- **§16 `--approve`:** runs validation, WARNS not blocks, records owner+date, flips status. `.session.md` committed.
- **§17 Contradiction:** SURFACE + ASK (Keep/Change/Hybrid). NEVER auto-flip approved decisions.
- **§17 Duplicate features:** LLM flags; PO decides merge/keep-both/cross-link. Never auto-merge.
- **§18 Horizon vocab:** `now/next/later` (NOT dates).
- **§18 VI ships best-effort;** native-speaker review is a known open item (parked-pending-feedback, PO confirmed 2026-05-28T23:21).
- **AMENDMENT §15 (2026-05-28, post-review M-2):** Deferred items (`scope:out` / `moscow:wont`) SHOW BY DEFAULT with visual marker (`*` ASCII / `:::deferred` classDef Mermaid) on tree/roadmap/persona views. Opt-in `--filter-wont` hides them. Other views always show all.
- **AMENDMENT §18 (2026-05-28, post-review M-1):** `CLAUDE.md` lives at REPO ROOT only (dev-side, auto-loaded by Claude Code). NO in-skill `CLAUDE.md`. Operating-guide content absorbed by `SKILL.md` + `references/*.md`. Same for `README.md` at repo root.

## Findings Raised → Fixed (do NOT re-flag)

Three review rounds; column "Round" = R1 (review 260528-1945), R2 (review 260528-2110), R3 (review 260528-2241).

| Round | Severity | Finding | File | Fix verified by |
|-------|----------|---------|------|-----------------|
| R1 | CRIT-1 | Repo venv `.claude/skills/.venv` missing | install.sh | `python3 -m venv` + 32/32 pytest (fix report 260528-2011) |
| R1 | CRIT-2 | Vendored Mermaid empty → offline broken | assets/vendor/mermaid.min.js | 2.57MB blob; sha256 `a43bc1af...` pinned; install-vendor-mermaid.sh shim; HTML zero CDN refs (R2 verified) |
| R1 | CRIT-3 | Eval fixtures absent in `eval/fixtures/` | eval/fixtures/* | 4 JSON + 1 TXT + 2 symlinks populated; all parse (fix report 260528-2011) |
| R1 | CRIT-4 | HTML render bug for ASCII-fallback views (heatmap/persona/risk wrapped as broken Mermaid) | visualize.py + render_html.py | Dispatch detects `<pre>` prefix, routes `view_format="pre"`; regression test (fix report 260528-2011); R2 verified |
| R1 | CRIT-5 | Skill-folder CLAUDE.md + README.md DEAD CODE | filesystem | `git mv` to repo root; SKILL.md:133 dead ref dropped; brainstorm §18 amended (fix report 260528-2011) |
| R1 | IMP-1 | install.sh does not vendor Mermaid | install.sh + install-vendor-mermaid.sh | Shim added; wired (fix report 260528-2011) |
| R1 | HIGH-2 / IMP-2 | `_escape` missing `"` and `'` | render_html.py:65-68 | Added `&quot;`, `&#39;` (fix report 260528-2011) |
| R1 | HIGH-3 / IMP-3 | Mermaid tree dup PRODUCT node | render_mermaid.py:32-34 | `if n.get("type") == "product": continue` (fix report 260528-2011) |
| R1 | HIGH-5 / IMP-5 | `generate_templates.py` story `--parent` weak | generate_templates.py:88-90 | Strict regex `^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+$` (fix report 260528-2011) |
| R1 | HIGH-6 | `frontmatter-and-id-spec.md` misstates allocator | references/frontmatter-and-id-spec.md | Rewrote line to match CLI `session_used=[]` + `--id` override (fix report 260528-2011) |
| R2 | NEW-1 IMP | `--format mermaid` returns HTML `<pre>` for heatmap/persona/risk | render_mermaid.py:55,98,136 | Plain ` ``` ` markdown fence (fix report 260528-2141) |
| R2 | NEW-2/8 IMP | Phantom `BRD` node in tree Mermaid (vestigial `goal→BRD` edge) | spec_graph.py:125-126 | Edge removed; regression test (fix report 260528-2141) |
| R2 | NEW-3 MIN | VISION disconnected with empty title | render_mermaid.py:tree | Skip `vision` node in loop (fix report 260528-2141) |
| R2 | NEW-4 IMP | Generate-time slug validation missing for epic/story parent | generate_templates.py | `PARENT_PATTERN_FOR_PRD/EPIC` + disambiguator; ValueError + 2 tests (fix report 260528-2141) |
| R2 | NEW-6 IMP | `--lang vi` silent no-op for ASCII/Mermaid | i18n_labels.py (NEW) + render_ascii/mermaid + visualize | Label map for 7 keys; plumbed `lang` arg through roadmap+moscow (fix report 260528-2141); tree prefix added in 260528-2229 |
| R2 | NEW-7 MIN | HTML for ASCII-fallback views embeds unused 2.5MB Mermaid JS | render_html.assemble | Conditional include: empty when `view_format != "mermaid"` (99.9% size reduction) (fix report 260528-2141) |
| R2 | NEW-9 IMP | Eval scenario 3 expected_downstream_set has no deterministic script function | eval/evals.json | Tagged `_assertion_type: "llm_advisory"`; per-assertion `_gating` tags (fix report 260528-2141) |
| R2 | NEW-10 OBS | Vendored Mermaid sha256 not pinned | install-vendor-mermaid.sh:24 | `EXPECTED_SHA256="a43bc1af..."` locked (fix report 260528-2141) |
| R2 | NEW-11 OBS | "No external network calls" wording too absolute | /CLAUDE.md L97 | Softened to "No runtime external network calls" (fix report 260528-2141) |
| R2 | NEW-13 OBS | install.sh dispatch may not survive fresh clone | .claude/skills/product-spec/install.sh (NEW) | PO-facing one-shot installer at skill root (fix report 260528-2141) |
| R2 | NEW-15 MIN | `_safe_label` doesn't escape Mermaid-special chars | render_mermaid._safe_label | Replaces `[]{}` and backticks (fix report 260528-2141) |
| Sub-Agent | SA-1A | Fresh `vision.md` ships with `horizon: TBD` (enum violation) | assets/templates/vision.md | Removed `horizon` token (timeless strategy) + regression test (fix report 260528-2141) |
| Sub-Agent | SA-1B | `frontmatter_parser.py` CLI TypeError on YAML dates | scripts/frontmatter_parser.py | Added `default=str` to `json.dumps` + regression test (fix report 260528-2141) |
| Sub-Agent | SA-1C | Vision template token mismatch (`personas_detail`, `north_star`, etc.) | assets/templates/vision.md | Tokens aligned to interview fixture; verified UC10 (deferred fix report 260528-2229) |
| Sub-Agent | SA-4A | `render_ascii.delta()` missed PRODUCT.core_value diff | render_ascii.delta | Added product-level diff; verified UC11 blind test |
| Sub-Agent | SA-7A | BRD `goals` template lacks shape hint | assets/templates/brd.md + frontmatter-and-id-spec.md | 13-line YAML comment block + new reference doc section (deferred fix report 260528-2229) |
| Sub-Agent | SA-11A | PRODUCT.md core_value duplicated frontmatter + body | assets/templates/product.md | Body replaced with reference-only stub (deferred fix report 260528-2229) |
| Deferred | NEW-12 | Script-level `--approve` gate (defense-in-depth) | generate_templates.fill_defaults | Now rejects `status: approved` with ValueError (deferred fix report 260528-2229) |
| Deferred | NEW-14 | `render_html._load_mermaid_js` mixed-responsibility | render_html.py | Split into `_load_vendored_mermaid_js` + `_cdn_fallback_snippet` (deferred fix report 260528-2229) |
| Deferred | O-3 | Tree view `--lang vi` localization | i18n_labels.py + render_ascii/mermaid tree | `product` key added (EN `PRODUCT`, VI `SẢN PHẨM`); lang routed through tree (deferred fix report 260528-2229) |
| Deferred | O-5 | README troubleshooting for `/tmp/` workspace `.venv` access | README.md | Added troubleshooting row (deferred fix report 260528-2229) |
| R3 | C-1 (W3-CRIT-1) | `personas: TBD` corrupts viz; list-typed defaults leak string | generate_templates.fill_defaults + check_consistency.shape_check | `LIST_FIELDS` defaults to `[]`; new `invalid_type` finding; 3 tests (fix report 260528-2303) |
| R3 | H-1 (W3-HIGH-1) | Mermaid tree inverted vs ASCII (PRODUCT at bottom) | render_mermaid.py:39-59 | `flowchart TB → BT`; test_w3_h1 (fix report 260528-2303) |
| R3 | H-2 (W3-HIGH-2) | install.sh swallows pytest exit code via `| tail -3` | install.sh:67 | Capture-then-tail; external sanity probe (fix report 260528-2303) |
| R3 | M-1 (W4-MED-1) | §18 silent reversal (CLAUDE.md location) | brainstorm + phase-01 | Amendment recorded; PO confirmed "keep current (repo root)" (fix report 260528-2303) |
| R3 | M-2 (W4-MED-2) | §15 viz filter not implemented | render_ascii/mermaid + visualize.py | Default show-all with marker + opt-in `--filter-wont`; 5 tests; §15 amended (fix report 260528-2303) |
| R3 | M-3 (W4-MED-3) | V6 vision-horizon orphan question | references/interview-vision.md | V6 deleted; V7→V6 (fix report 260528-2303) |
| R3 | M-4 (W4-MED-4) | Phase 2 SC4 "9 views × 4 formats" wrong | phase-02-reference-specs.md | Fixed to "3 formats" (fix report 260528-2303) |
| R3 | M-5 (W4-MED-5) | Phase 1 in-skill CLAUDE.md ref | phase-01-scaffold-skeleton.md | Updated with §18 amendment pointer (fix report 260528-2303) |
| R3 | M-6 (W3-MED-1) | `status_inconsistency` skips PRD↔BRD-goal | check_consistency._status_inconsistency | Iterates `brd_goals` for PRD type; test_w3_m6 (fix report 260528-2303) |
| R3 | M-7 (W3-MED-2) | `--viz delta` requires 2 snapshots, ignores live graph | visualize._load_baseline | 1-snap fallback; test_w3_m7 (fix report 260528-2303) |
| R3 | M-8 (W3-MED-4) | No CI-runnable `--strict` gate (LLM-layer only) | scripts/strict_gate.py (NEW) + workflow-validate.md | New shell-runnable strict gate script + 2 tests (fix report 260528-2303) |
| R3 | L-1 (W3-MED-3) | `--diff <bad-name>` silently degrades | visualize._load_baseline | Raises FileNotFoundError with available list; test_w3_l1 |
| R3 | L-2 (W4-LOW-1) | workflow-validate uses plain `python3` not venv | references/workflow-validate.md | Repo venv path (fix report 260528-2303) |
| R3 | L-3 (W4-LOW-2) | Example PRODUCT.md duplicates core_value (violates SA-11A) | examples/acme-shop/.../PRODUCT.md | Body stubbed (fix report 260528-2303) |
| R3 | L-4 (W3-LOW-1) | Gap-view counts any inbound edge (diverges from check_traceability) | render_ascii/mermaid.gap | Match by expected child type (DRY); test_w3_l4 |
| R3 | L-5 (W3-LOW-2) | snapshot filename/body clock skew | spec_graph.write_snapshot | Filename derived from generated_at; test_w3_l5 |
| R3 | L-7 | Unused BRD goal `parent` claim | spec_graph.PARENT_FIELD_BY_TYPE + spec doc | Goal removed; doc updated (fix report 260528-2303) |
| R3 | N-2 | Test coverage gaps (no list-default, orientation, install.sh exit, 1-snap delta, wont/out filter, round-trip tests) | scripts/tests/ | +19 new tests covering each fix path (fix report 260528-2303) |
| R3 | N-7 | Persona soft-cap not enforced | check_consistency.persona_cap_exceeded | New warn finding (soft cap 4) + 2 tests (fix report 260528-2303) |
| R3 | N-8 | `.session.md` gitignore guard missing | check_consistency._session_md_gitignore | New warn finding + 1 test (fix report 260528-2303) |

Blind sub-agent verification (tester report 260528-2218): 65/65 fixed assertions PASS + UC7 open-ended DONE across 11 agents in 4 rounds. All prior fixes verified in blind contexts (SA-1A, 1B, 1C, 2/8, 4A, 6). 0 NEW skill defects from blind testing.

## Findings Raised → DEFERRED (with reason)

| Round | Severity | Finding | Defer reason | Status now |
|-------|----------|---------|--------------|------------|
| R1 | IMP-4 | `--update` workflow integration test missing | LLM-driven harness gap; folds into CRIT-3 fixture work | Eval fixture populated; integration test path open (still LLM-layer) |
| R1 | IMP-6 | Bash hooks block reading `vendor/` despite `.ckignore` | Out of skill scope (repo tooling) | Tooling issue, not skill |
| R1 | MIN-1..MIN-8 | 8 observational items (graph schema edge, status spec, roadmap truncation, etc.) | Documented or out-of-scope | Each cited in R1 review §MIN |
| R2 | NEW-12 | Script-level `--approve` enforcement | YAGNI defer (LLM orchestration sufficient) | LATER FIXED in 260528-2229 (status="approved" guard added) |
| R2 | NEW-14 | CDN-fallback `</script>` injection refactor | Functional today; invasive refactor; CDN only hit when vendor missing | LATER FIXED in 260528-2229 (split into 2 helpers) |
| R3 | N-1 | Examples bloat (17 HTML files in visuals/) | **PO confirmed defer 2026-05-28T23:21** | Accepted-as-is; janitor pass later |
| Brainstorm | VI native review | Vietnamese phrasing quality review | **PO confirmed defer 2026-05-28T23:21** | Parked-pending-feedback; ships best-effort |

## Findings Raised → REJECTED (with reason)

| Round | Finding | Reject reason |
|-------|---------|---------------|
| R1 | "Accept CDN dependency, revise CLAUDE.md to match" (alt fix path for CRIT-2) | NOT recommended in original review — silently reverses confirmed PO decision §8 (inline-vendored). Rejected at audit time. |
| R3 | L-6 `_escape` quote-escape | NO ACTION — already documented as defensive; no real-world attack vector |
| R3 | N-3..N-6 observations | NOTED — no code action needed (positive signals / by-design) |

## Outstanding / Unresolved (real risks for Wave 4 to validate)

Items NOT closed by the 3 prior rounds. These are the only candidates for hardcore re-review:

1. **Skill discovery spike not independently re-verified.** Every review report (R1, R2) and remediation acknowledged the M1 spike "namespace `cleanmatic:product-spec` invocable" was claimed-passed but no reviewer reloaded Claude Code to re-confirm `/cleanmatic:product-spec` resolves post-distribution. Cited as unresolved Q5 (R1), Q7 (R2), and again in 260528-2141 Q5.
2. **Eval grader infrastructure does not exist.** `eval/evals.json` is scaffolded with fixtures + advisory tags but no runtime grader code (LLM-as-judge or assertion harness). Cited R1 Q4, R2 Q5. Treated as separate work item; out of skill scope but blocks Phase 8 verification claim.
3. **VI native-speaker review** parked-pending-feedback (PO accepted defer; ships best-effort).
4. **`render_ascii.delta()` node-only diff scope (post-SA-4A enhancement question)** — SA-4A added PRODUCT.core_value handling; the 260528-2141 Q3 asked whether to extend delta beyond node fields. PO did not lift it from defer.
5. **`.venv` sandbox blocking under `/tmp/...`** (tester report O-5 / IMP-6 family) — documented in README but root-cause is `.ckignore`/scout-block hook scope, not skill. Out-of-skill scope.
6. **Stale visuals/*.html in `examples/acme-shop`** — PO-deferred (N-1). Defer accepted but bloat persists in repo.
7. **install.sh tracking** — `.claude/skills/install.sh` was originally gitignored; the skill-local `install.sh` and `install-vendor-mermaid.sh` are tracked. Whether the repo-wide `install.sh` exception should be added was raised (260528-2011 Q2) and never explicitly resolved — current state: skill-local installers cover the case, but a fresh clone of the whole CK repo may still surprise the user.
8. **`--update` workflow does not have a script-integration test path** — LLM-layer prose exists in `workflow-auto-and-update.md`; eval fixtures populated; no automated round-trip subprocess test (R1 IMP-4, R2 NEW-9 backing).

## Confidence

- **Self-rate confidence in this baseline: ~92%.**
- Bases: read all 10 reports end-to-end; cross-referenced finding IDs across rounds (R1 CRIT-1..5 / IMP-1..6 / MIN-1..8 → R2 NEW-1..15 / SA-* → R3 C-1, H-1..2, M-1..8, L-1..7, N-1..8). Confirmed each fix has an evidence-cited closure or explicit defer/reject. Sticky decisions cross-checked against brainstorm §1-§18 + 2 amendments.
- **What I did NOT read or skim:**
  - The skill source itself (`.claude/skills/product-spec/scripts/*`, `references/*`, `assets/templates/*`) — baseline is paper-trail only.
  - The plan files (`plans/260528-0912-cleanmatic-product-spec-skill/plan.md` + 8 phase files) referenced as authority for Phase SC text.
  - The repo-root `CLAUDE.md` and `README.md` post-rewrite (only inferred from fix reports).
  - Test files (`scripts/tests/test_*.py`) — only count claims (32 → 41 → 45 → 57 → 76).
  - 4 researcher reports referenced in brainstorm frontmatter.
  - 4 eval fixtures (`init-answers.json`, `braindump.txt`, `auto-decisions.json`, `delta-change.json`) — only their existence/keys.
  - The vendored `mermaid.min.js` blob.
- **Implication for Wave 4:** assume facts in the fix reports are accurate but spot-check anything that smells. The outstanding-items list above is the safe re-validation surface.

## Unresolved Questions

None for this baseline — see "Outstanding / Unresolved" section for the items Wave 4 should validate.
