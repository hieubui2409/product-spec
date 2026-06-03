# Red-Team Review — Backlog C/D/E implementation plan

> 2026-06-03 · 4 hostile reviewers (Security Adversary, Failure Mode Analyst, Assumption Destroyer, Scope & Complexity Critic).
> 31 raw findings → deduped to 15. All carry `file:line` evidence (none rejected by evidence filter).
> Verdict: **plan needs substantial revision before cook** — D11 premise is factually refuted; E1 has 4 data-integrity/security defects.

## Severity tally: 5 Critical · 6 High · 4 Medium

| # | Sev | Phase | Finding | Disposition |
|---|-----|-------|---------|-------------|
| C1 | Critical | 7 D11 | `_now()` impls **not identical** — `spec_graph` uses `Z`-suffix, others `+00:00`; divergence is *documented as intentional*; `behavioral_memory._now` is a test monkeypatch seam. "Copy verbatim into one fn" is impossible + flips snapshot timestamp format → breaks determinism/diff silently. | **Accept** |
| C2 | Critical | 7 D11 | A `skills/common/` module is **not bundled** — manifest packs by skill-name allowlist, `follow_shared: false`; recipient install → `ModuleNotFoundError` (split-brain) across product-spec + critique. | **Accept** |
| C3 | Critical | 3 E1 | **DEC-register injection**: untrusted critique finding text → `--rationale` via naive `{{rationale}}` replace; `_RECORD_RE` splits on `^---`. Crafted finding smuggles a phantom `DEC-999` → suppresses a real future gate + corrupts `alloc_id`. | **Accept** |
| C4 | Critical | 3 E1 | **Non-atomic DEC alloc + no checkpoint/resume**: `--alloc-id`/`--append` are 2 subprocess calls, read-then-write no lock; per-finding loop → id collision (dup-id guard returns `written:false` on exit 0 → silently dropped ruling). Interrupt mid-walk → torn write; re-run re-walks all → duplicate DECs (breaks re-litigation contract). | **Accept** |
| C5 | Critical | 3 E1 | **GATE re-approval is LLM-honor-only** — no script writes/verifies `approved_by/at`; `approved_changed_no_dec` is warn-only + ack-silenceable. `--apply-critique` adds an automated loop driving approval transitions with no deterministic gate → forgeable owner+date audit trail. | **Accept** |
| H1 | High | 3 E1 | **Parse the structured lens-cache JSON, not humanized prose**: findings have no stable ID; report prose repeats each ID 2-3× (Top-3 + per-lens + DEC), bilingual + localized severity tokens. Resolve findings via `lens_findings_hash` → `.memory/critique-lens-cache/<hash>.json` (structured `{lens,evidence,critique,why_it_dies,fix,severity}`); emit a per-finding fingerprint. | **Accept** |
| H2 | High | 3 E1 | **Freshness untestable on shipped fixtures**: all 8 example reports have NO frontmatter (hand-authored); `body_hash` only exists on real generated reports + is per-node not per-finding. Must handle `body_hash:None` (tell PO "predates freshness — re-critique or proceed") + generate a real frontmatter fixture via the actual critique path. | **Accept** |
| H3 | High | 3+6 E1/E2 | **Missing read-side path fence** — `fs_guard` is write-only by design. `--apply-critique <report>` and `--discover <paths>` read PO-supplied paths raw → traversal / secret disclosure (`--discover /etc /…/.aws`) into committed `decisions.md`/`vision.md`. Add containment + extension/size filter + dotfile exclusion. | **Accept** |
| H4 | High | 7 D11 | **Site counts wrong**: `_now()` is 5-6 sites (not 4), `_hashable()` is 2 sites in `render_ascii.py`+`render_ascii_board.py` (NOT `spec_graph.py`/`critique_common.py` as listed) → moot if D11 deleted, else re-ground before build. | **Accept** |
| H5 | High | 2 D12 | **`bug_class` marker breaks `--strict-markers`**: claude-pack `pyproject.toml` sets `--strict-markers` + registers only `integration`; product-spec & critique have NO pytest config at all. Tagging tests → existing claude-pack CI goes red on collection error. Must register marker in all 3 (create 2 configs) before tagging. | **Accept** |
| H6 | High | 2 D12 | **venv/sys.path misdiagnosed**: imports resolve via each skill's `conftest.py` `sys.path.insert`, NOT claude-pack's `install.sh` `.pth`. CI must run pytest **scoped to each skill's tests dir** (not combined-root) or imports race / break. | **Accept** |
| H7 | High | 4 C9 | **Audit join has no source-disagreement rule**: 4 sources w/ no referential integrity; plan only handles sparse/empty, not *disagreement* (approval w/ no change-log entry). Must render an explicit **"unreconciled"** row (never drop) + fixture an orphaned approval. An audit view that hides inconsistency is worse than none. | **Accept** |
| H8 | High | all | **CLI surface bloat vs non-tech-PO**: plan adds `--apply-critique`+`--discover`+`--brief` (+`--viz audit`) onto a tool with 24 flags whose backlog already flags CLI-too-technical. Force a surface budget — prefer routing through no-flag menu / existing `--auto`/`--export`/`--update`/`--status`. | **Accept (surface budget)** |
| M1 | Med | 5 E4 | `--brief exec` duplicates `--summary` (same `exec_summary` path); and `generate_templates.render()` is token-substitution (errors on unresolved token), NOT an assembler — "reuse exec_summary inputs" needs the value-assembly path, not the template render. Cut exec flavor; keep only release-notes; reuse `--summary`'s flag. | **Accept** |
| M2 | Med | 1 E5 | Factual fixes: `version` is nested `metadata.version` (not top-level); "consistent in bundle" is undefined (skills 2.0.0/1.0.0/0.1.0 vs bundle 1.1.0 by design) → scope verifier to **semver shape + presence only**. **NOTE:** the "drop 2 CHANGELOGs (internal-only ceremony)" sub-finding contradicts the locked PO decision E5=standardize-hybrid → **surface to PO, do not auto-apply** (GATE-NO-SILENT-REVERSAL). | **Accept (factual) / Surface (CHANGELOG cut)** |

## Also noted (folded, not separate rows)
- C9 reroute to `--status --audit` instead of a 15th XSS-watched `--viz` view (Scope F6) — fold into H8 surface-budget.
- D12 offline enforcement via `pytest-socket`/socket-block conftest (Security F7) — fold into H5/H6 CI hardening.
- C9/E4 HTML escape discipline must be a bound test gate if HTML ever added (Security F5) — fold into H7.
- "50 tests" anchor imprecise (files≠cases; 31/9→30/10) — re-baseline to `pytest --co -q` case count.
- Phase frontmatter `dependencies:[2]/[3]/[4]` contradicts plan.md "soft ordering" prose — reconcile (split phase 5 into 5a-exec/5b-release-notes).
- Minor citation drift (guardrails `:102` heading vs `:105-108`; frontmatter `:171` vs `:176`).

## Bottom line per phase
- **D11 (7):** DELETE / close as no-op. Premise refuted (C1, C2, H4). Duplication is intentional + trivial + un-bundlable.
- **E1 (3):** Keep (genuine gap) but **major hardening required** — parse cache-JSON not prose (H1), atomic+resumable DEC writes (C4), injection sanitize (C3), read-fence (H3), deterministic re-approval gate test (C5), freshness `None`-handling (H2).
- **D12 (2):** Keep but fix marker-registration (H5) + per-skill-dir scoping (H6) + offline enforcement.
- **C9 (4):** Keep but reroute to `--status` + add unreconciled-row rule (H7).
- **E4 (5):** Shrink to release-notes-only, no `--brief exec`; fix assembler reuse (M1).
- **E5 (1):** Fix `metadata.version` + shape-only verifier (M2); CHANGELOG-cut needs PO ruling.
- **E2 (6):** Prototype inside `--auto`, add read-fence (H3, H8).

## Unresolved (for PO)
1. E5 CHANGELOG cut contradicts locked decision (standardize-hybrid) — keep CHANGELOGs or trim to verifier-only given internal-only?
2. E1 atomic DEC: add a single alloc+append subprocess mode?
3. D11: confirm delete vs keep `_hashable`-only (2 same-skill sites)?
