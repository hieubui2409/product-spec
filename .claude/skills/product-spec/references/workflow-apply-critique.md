# workflow-apply-critique — the critique return-edge (`--apply-critique <report>`)

Loaded for `--apply-critique`. Consume a `product-spec-critique` report and walk each finding with
the PO, recording rulings in the Decision Register. Critique stays report-only; **product-spec owns
the spec and the rulings**. This closes the biggest structural gap in the pipeline.

> Script-vs-LLM split: `parse_critique_report.py` does the deterministic struct (read-fence,
> cache-JSON parse, fingerprint, freshness); `decision_register.py --append-alloc` does atomic DEC
> writes; `apply_critique_progress.py` does resume markers. The **LLM** owns the per-finding
> interview + the prose judgment. Always run the scripts first.

## Flow

### 0. Read-fence + parse (deterministic)
Run `parse_critique_report.py --root <root> --report <path>`. The script:
- **Read-fences** `<path>` under `<root>/docs/product/critique/` (traversal/symlink-escape → friendly
  refusal). Never read an arbitrary path.
- Resolves findings from the **structured lens-cache** (`lens_findings_hash` → `.memory/critique-lens-cache/<hash>.json`),
  NOT the humanized prose. Each finding gets a deterministic **fingerprint** = `sha8(lens + artifact_id + normalized_critique)`.
- Tags each finding's **freshness** (`fresh`/`stale`/`unknown`/`artifact-missing`).
- If `cache_present: false` → the cache is gone; fall back to a **manual prose walk** of the report
  with the PO (best-effort), and recommend re-running the critique with `--fresh`.

### 1. Resume check
Read prior progress: `apply_critique_progress.py --root <root> --lens-hash <h> --show`. **Skip any
finding whose fingerprint is already resolved** — an interrupted run never re-litigates or double-records.

### 2. Per-finding interview (LLM)
For each unresolved finding, present (bilingual per the report `lang`): the lens, the evidence
`ID:line`, the critique, why-it-dies, the proposed fix, **and the freshness tag**. If `freshness:
unknown`, tell the PO plainly: *"this report predates freshness tracking — re-critique or proceed
without a staleness check"* (never silently skip). Ask the PO to choose:

- **Keep** — reject the finding. Record a `DEC-<n>` capturing *why we keep it as-is* (the
  anti-re-litigation record).
- **Change + re-approve** — accept the finding. This is a spec change. **Never auto-rewrite prose** —
  run the `--update` impact pass (`workflow-update.md`): flag affected nodes, ask before regenerating.
  If the touched artifact is `approved`, this is **GATE-NO-SILENT-REVERSAL**: require a *fresh*
  re-approval (real `approved_by` + `approved_at >= the decision date`). The deterministic guard is
  `parse_critique_report.reapproval_ok(...)` — a placeholder owner or a stale approval **fails the gate**.
  If the Change overturns a prior **Keep** on the same fingerprint, pass `--supersedes <prior-DEC>` so
  exactly one active ruling remains.
- **Defer** — record a `DEC-<n>` noting the deferral + when to revisit.

### 3. Record the ruling (atomic)
Record each resolved finding with ONE atomic call:
```
decision_register.py --root <root> --append-alloc --title "<short>" \
  --rationale "<the PO's reasoning>" [--affects <artifact_id>] [--supersedes <DEC>]
```
- `--append-alloc` allocates the next id AND appends under a file lock in one process (no TOCTOU,
  no dup id across a PO-interaction gap).
- **Read the JSON `written` field.** On `written:false` (dup-id guard), abort/retry — never silently drop.
- The rationale is **injection-sanitized** by the register (a `---` fence or `## DEC-` heading in the
  text is neutralized) — phantom-DEC smuggling is impossible.
Then mark progress:
```
apply_critique_progress.py --root <root> --lens-hash <h> --record \
  --fingerprint <fp> --dec <DEC-n> --disposition keep|change|defer
```

### 4. Close out
Summarize: N findings, X kept / Y changed / Z deferred, the `DEC-<n>` ids, and any `stale`/`unknown`
findings the PO should re-critique. Multi-finding-per-artifact: present them together (disambiguated by
fingerprint) so the PO sees the full picture before confirming.

## GATEs (every turn)
- **GATE-NEVER-ASSUME**: never assume a disposition; the PO chooses each finding.
- **GATE-NO-SILENT-REVERSAL**: a Change on `approved` content needs a fresh, real re-approval — the
  deterministic guard cannot be forged by LLM honor alone.

## Residual
Cache-absent old reports take the weaker prose-fallback path — document it as best-effort and recommend
`--fresh` re-critique to regenerate the structured cache.
