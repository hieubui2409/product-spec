---
phase: 2
title: Fingerprint compute + storage (write path)
status: completed
priority: P2
effort: 2h
dependencies:
  - 1
---

# Phase 2: Fingerprint compute + storage (write path)

## Overview

Implement the fingerprint helper + line resolver, compute fingerprint at index-write time, and persist it as an
additive field with `version: 1 → 2`. Turns Phase-1 pure/resolver/write-path tests green. Read paths unchanged
this phase (still dedup by evidence_id) — that's Phase 3.

## Requirements
- Functional: `compute_finding_fingerprint`, `_resolve_line_text`; `index_report_findings` attaches
  `finding_fingerprint` (None when unresolvable); `upsert_findings` persists it; index `version == 2`.
- Non-functional: deterministic (no wall-clock in hash); one graph build per write; signature of
  `index_report_findings` unchanged (back-compat).

## Architecture

**Where compute lives:** `critique_inherit.py` (it owns `index_report_findings` + already imports `spec_graph`). Keep
helpers module-private; no new module (DRY/KISS — too small to extract).

```python
import hashlib, re

_BULLET_RE = re.compile(r'^[\s>#*\-+0-9.)]+')          # strip leading md bullet/heading/number markers

def _normalize_line(text: str) -> str:
    return re.sub(r'\s+', ' ', _BULLET_RE.sub('', text)).strip().lower()

def _resolve_line_text(root, graph, evidence_id):
    """Cited spec-line RAW text, or None when unresolvable (degrade → eid keying)."""
    if not evidence_id or ":" not in str(evidence_id):
        return None
    node, _, line_s = str(evidence_id).partition(":")
    try:
        line = int(line_s)
    except ValueError:
        return None
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    n = nodes.get(node)
    if not n or not n.get("file"):
        return None
    path = Path(root) / "docs" / "product" / n["file"]
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if line < 1 or line > len(lines):
        return None
    return lines[line - 1]

def _finding_fingerprint(root, graph, evidence_id, severity):
    """Fingerprint or None. None ⇒ caller keys by evidence_id (safe degrade).

    B1 fix: gate on the NORMALIZED text, not the raw line. An all-punctuation /
    structural line (`---`, a bare date, `1. 2.`) normalizes to "" → returning a
    hash of "" would COLLIDE distinct findings on the same node+severity (the very
    bug this feature removes). Empty-after-normalize ⇒ no usable anchor ⇒ None."""
    text = _resolve_line_text(root, graph, evidence_id)
    if text is None:
        return None
    norm = _normalize_line(text)
    if not norm:
        return None
    h = f"{_node_of(evidence_id)}\0{severity or ''}\0{norm}"
    return hashlib.sha256(h.encode("utf-8")).hexdigest()[:16]
```

**Write path (`index_report_findings`):** build graph once; per row compute fingerprint via `_finding_fingerprint`
(None when unresolvable OR normalized-empty). Attach `finding_fingerprint` to the row dict BEFORE `upsert_findings`.

```python
graph = _import_spec_graph().build_graph(Path(root))
...
for f in findings:
    eid = f.get("evidence_id") or f.get("evidence")
    ...
    rows.append({..., "finding_fingerprint": _finding_fingerprint(root, graph, eid, f.get("severity"))})
```

**B2 — BRD-goal nodes (corrected; "uniform for all node types" was WRONG).** `spec_graph._node_from_goal` sets a goal
node's `file = brd.md` and `body_hash = None` — the goal's content lives in BRD frontmatter `goals:`, not at a body
line. A goal evidence `BRD-G1:<line>` resolves to whatever brd.md line was cited; when that's a structural/empty line
(e.g. `---`) it normalizes to "" → `_finding_fingerprint` returns None → **eid fallback** (= today's behavior, no
regression). Goal findings that cite a real frontmatter content line still fingerprint normally. **Decision: accept
eid-fallback for goal nodes** — goals are few + ID-addressed; safe degrade, no new collision. (Surfaced as a known
limitation, not a blocker. PO may later opt to anchor goals to frontmatter goal-text if per-goal granularity is wanted
— deferred, YAGNI.)

**M2 — write-time graph build is safe here.** Critique is **read-only** (never edits `docs/product`), so within one run
the spec is byte-stable between `critique_scan` and `index_report_findings`; resolving the anchor at index-write time
sees the same bytes that were critiqued. (Cross-run drift is the intended trigger for a NEW fingerprint, not a bug.) One
`build_graph(root)` per write call.

**Storage (`critique_cache.py`):** add `finding_fingerprint` to `_INDEX_FIELDS` so `upsert_findings` copies it.
`load_index` already returns the entries dict regardless of version (tolerant) — no read change. **M3: do NOT pretend
`version` gates anything** — no consumer reads it. Bump `version` 1→2 only as an inert schema marker; **do not assert a
consumer reads it** (the real back-compat is `entry.get("finding_fingerprint") or eid` in `_index_rows`). Optional —
may skip the bump entirely (YAGNI).

## Related Code Files
- Modify: `.claude/skills/product-spec-critique/scripts/critique_inherit.py` (helpers + `index_report_findings`;
  `from pathlib import Path` already imported)
- Modify: `.claude/skills/product-spec-critique/scripts/critique_cache.py` (`_INDEX_FIELDS`, version bump)
- Read: `.claude/skills/product-spec/scripts/spec_graph.py` (`build_graph`, node `file`)

## Implementation Steps
1. Add `_normalize_line`, `_resolve_line_text`, `_finding_fingerprint` to `critique_inherit.py`. The fingerprint gate is
   on the NORMALIZED text (B1): empty-after-normalize → None → eid fallback.
2. In `index_report_findings`: build graph once via `spec_graph.build_graph`; attach
   `finding_fingerprint = _finding_fingerprint(root, graph, eid, severity)` per row. Keep existing blocker+DEC-worthy
   filter and `evidence`/`evidence_id` acceptance.
3. In `critique_cache.upsert_findings`: append `"finding_fingerprint"` to `_INDEX_FIELDS`. Optionally bump `version`
   1→2 as an inert marker (no consumer reads it — M3); do NOT add a test asserting a consumer reads version.
4. Run Phase-1 pure + resolver + write-path + B1-empty-normalize + B2-goal tests → green. Read-path dedup tests stay
   red (Phase 3).
5. Sanity: `index_report_findings` signature unchanged; one graph build per call (not per finding).

## Success Criteria
- [ ] `_normalize_line` + `_resolve_line_text` + `_finding_fingerprint` implemented + unit tests green.
- [ ] `index_report_findings` attaches `finding_fingerprint`; unresolvable OR normalized-empty → None, no crash.
- [ ] All-punctuation/structural cited line (`---`, bare date) → None → eid fallback (B1 collision test green).
- [ ] BRD-goal finding citing a structural line → None → eid fallback (B2 test green); no goal-node crash.
- [ ] `upsert_findings` persists the new field; no phantom `version`-read assertion (M3).
- [ ] Write-path + pure + resolver Phase-1 tests green; no existing test regressed.

## Risk Assessment
- **Graph build cost at write time**: one `build_graph(root)` per critique write — acceptable (once per run). Safe re:
  staleness because critique is read-only (M2). If profiling flags it later, reuse `build_graph_with_artifacts`; not now.
- **B1 normalized-empty collision**: PRIMARY correctness risk — gate on normalized text (not raw); empty → eid fallback.
  Without this, all-punctuation lines silently merge distinct findings (worse than status quo).
- **B2 goal nodes**: `file=brd.md`, content in frontmatter → cited line often structural → eid fallback accepted (no
  granularity for goals, but no regression). Documented limitation.
- **`_node_of(eid)` vs resolver node**: both derive node from eid identically — keep single source (`_node_of`).
