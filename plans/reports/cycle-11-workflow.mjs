export const meta = {
  name: 'hardcore-review-cycle-11',
  description: 'Cycle 11 FULL C7-style hardcore review of product-spec + claude-pack: file-partitioned finders (all 9 angles) -> dedup -> per-file 3-state verify -> sweep',
  phases: [
    { title: 'Find', detail: 'file-partitioned subsystem + cross-cutting angle + reference finders' },
    { title: 'Consolidate', detail: 'dedup by file:line + same-mechanism' },
    { title: 'Verify', detail: 'per-finding adversarial 3-state verdict' },
    { title: 'Sweep', detail: '2 whole-skill sweep finders for anything missed' },
  ],
}

const ROOT = '/home/hieubt/Documents/cleanmatic-skills'
const PS = '.claude/skills/product-spec'
const CP = '.claude/skills/claude-pack'

const CONTEXT = `
You are a finder in a HARDCORE max-recall code review (Cycle 11) of two Claude Code skills in repo ${ROOT}.
Skills: product-spec (PO-facing spec hierarchy + validation + visualization) and claude-pack (deterministic .claude/ tarball packager).

ENVIRONMENT:
- Root: ${ROOT}
- Python venv: ${ROOT}/.claude/skills/.venv/bin/python3
- Run product-spec tests: PYTHONPATH=${PS}/scripts ${ROOT}/.claude/skills/.venv/bin/python3 -m pytest ${PS}/scripts/tests -q
- Run claude-pack tests: PYTHONPATH=${CP}/scripts ${ROOT}/.claude/skills/.venv/bin/python3 -m pytest ${CP}/scripts/tests -q
- You MAY read any file and run read-only Bash (grep, python repro). Do NOT edit files.

THE 9 ANGLES (cover ALL of them on your assigned files):
  Correctness family:
   1. Crash-safety: unhandled exceptions on malformed/adversarial input (unhashable YAML keys, type-poison list/dict where scalar expected, UnicodeDecodeError, None where list/map expected, char-split on bare string).
   2. Logic correctness: wrong branch, off-by-one, boundary, mis-count, silent wrong output.
   3. Security/safety: path traversal (tar-slip, ../), XSS in self-contained HTML, secret/credential leak, safety-filter bypass (case, basename vs full path), URL OpSec.
   4. Determinism: same input -> byte-identical output; ordering, timestamps, set iteration, mtime/uid/gid.
  Cleanup family:
   5. DRY: duplicated logic that should be hoisted to a shared helper.
   6. Dead code: unreachable, unused, orphaned constants/imports.
   7. Stale callers / incomplete hoists: a prior fix hoisted/renamed something but a caller still uses the old inline path. THIS IS PRIMARY WATCH FOR C11 (see carry-forward).
  Altitude family:
   8. Contract/doc drift: SKILL.md / references/*.md / CLAUDE.md describes behavior the code no longer matches (or vice versa).
   9. Abstraction altitude: logic at the wrong layer, leaky abstraction, Script-vs-LLM split violation (scripts must be deterministic+structural-only; judgment belongs to the LLM).

PRIMARY WATCH (C11) = regressions introduced by the C10 fixes. Scrutinize for over/under-guarding + stale callers around:
  - Windows-safe path containment via Path.relative_to in manifest_loader (skills/agents/rules/hooks/_shared) + selection.py (replaced POSIX '/'-prefix test) + _check_path_safety extract. WATCH: relative_to on case-insensitive/symlink FS.
  - manifest_io userinfo scrub [^/]*@ (last-@, was [^/@]*@ first-@ which leaked passwords-with-@).
  - render_ascii.persona cell key str(p); assemble_digest._entry uses resolve_ac; spec_graph.index_artifacts keys by _scalar_id + ID_SENTINELS; check_consistency dup_id skips sentinels via _f; _status_inconsistency brd_goals guard; render_html.competition wires resolve_competition (dropped _DASHBOARD_HORIZONS); generate_templates load_values OSError/non-dict + _prd_slug_from_id + id/slug conflict raise; render_export._heading CR/LF collapse; diff_graphs str-persona; build_manifest --write non-dict-stdin guard; safety_check backslash-normalize + drive-letter predicate + walk OSError guard; cli --dry-run no FS side-effects + over_max_size:null + resolve_max_size extract; templates.render_template OSError->TemplateError; installers re-validate recipient $REL traversal + walk bundle root.
  WATCH especially: the persona str() key vs any OTHER raw-key renderer site that the C10 sweep may have missed.

LOCKED REFUTED — DO NOT re-flag unless you PROVE a NEW regression with a repro:
  - checked_at/today/root in *_anchors.py + time_advisory.py + competitive_drift output = INTENDED provenance (documented). NOT a determinism bug. G-A4 binds the payload, which build_anchors produces without it.
  - New v2 schema fields optional => v1 back-compat preserved. depends_on cycle detection = iterative 3-color DFS. ASCII = deterministic text-summary downgrade (NOT deleted). competitor url 'private:' prefix ignored (OpSec). Mermaid graph-views bundle Mermaid's OWN DOMPurify (exempt from the "no SKILL body-sanitizer" contract). generate_templates.session_used is a TESTED library mechanism — keep.
  - SEMVER_RE strict-2.0 rejecting leading-zero versions = INTENDED. exit-code divergence (build_manifest --write 2=collision vs pack 2=strict-gate) = intentional. broadened exception catches = safe. depends_on bare-scalar silently coerced = documented, kept (reverting would be risky multi-file).

OUTPUT: Return ONLY real, specific findings with concrete file:line and the exact mechanism. No vague "could be improved". Prefer precision over volume but do not miss real bugs. If a file is clean across all 9 angles, return an empty findings array.
`

const FINDINGS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['file', 'line', 'severity', 'angle', 'mechanism', 'title', 'detail', 'suggested_fix'],
        properties: {
          file: { type: 'string', description: 'repo-relative path' },
          line: { type: 'string', description: 'line number or range, e.g. "412" or "412-430"' },
          severity: { type: 'string', enum: ['CRIT', 'HIGH', 'MED', 'LOW'] },
          angle: { type: 'integer', minimum: 1, maximum: 9 },
          mechanism: { type: 'string', description: 'short mechanism tag for dedup, e.g. "unhashable-key-crash" or "stale-caller-resolve_ac"' },
          title: { type: 'string' },
          detail: { type: 'string', description: 'what + why it is a bug/issue; include repro if you ran one' },
          suggested_fix: { type: 'string' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['state', 'severity', 'reasoning', 'is_locked_decision', 'fix_risk'],
  properties: {
    state: { type: 'string', enum: ['confirmed', 'refuted', 'uncertain'] },
    severity: { type: 'string', enum: ['CRIT', 'HIGH', 'MED', 'LOW'] },
    reasoning: { type: 'string', description: 'adversarial: try to refute; cite file:line you read' },
    is_locked_decision: { type: 'boolean', description: 'true if this touches a GOAL.md locked design decision or the REFUTED list' },
    fix_risk: { type: 'string', enum: ['safe', 'risky'], description: 'safe=mechanical local fix; risky=multi-file/behavior-change/ambiguous' },
  },
}

// ---- Finder partitions ----
const SUBSYSTEM_FINDERS = [
  { label: 'ps:graph-core', files: `${PS}/scripts/spec_graph.py, ${PS}/scripts/frontmatter_parser.py, ${PS}/scripts/encoding_utils.py` },
  { label: 'ps:validation', files: `${PS}/scripts/check_consistency.py, ${PS}/scripts/check_traceability.py, ${PS}/scripts/strict_gate.py` },
  { label: 'ps:render-html', files: `${PS}/scripts/render_html.py` },
  { label: 'ps:render-graph', files: `${PS}/scripts/render_ascii.py, ${PS}/scripts/render_mermaid.py` },
  { label: 'ps:body-viewers', files: `${PS}/scripts/render_board.py, ${PS}/scripts/render_explorer.py, ${PS}/scripts/render_export.py, ${PS}/scripts/assemble_digest.py` },
  { label: 'ps:generate-migrate', files: `${PS}/scripts/generate_templates.py, ${PS}/scripts/migrate_multidim_fields.py, ${PS}/scripts/i18n_labels.py` },
  { label: 'ps:dispatch-matrix', files: `${PS}/scripts/visualize.py, ${PS}/scripts/build_traceability_matrix.py` },
  { label: 'ps:anchors-advisory', files: `${PS}/scripts/time_advisory.py, ${PS}/scripts/time_realism_anchors.py, ${PS}/scripts/competitive_drift_anchors.py` },
  { label: 'cp:manifest-safety', files: `${CP}/scripts/manifest_loader.py, ${CP}/scripts/build_manifest.py, ${CP}/scripts/safety_check.py` },
  { label: 'cp:pack-core', files: `${CP}/scripts/pack/selection.py, ${CP}/scripts/pack/tarball.py, ${CP}/scripts/pack/manifest_io.py, ${CP}/scripts/pack/cli.py, ${CP}/scripts/pack/pipeline.py, ${CP}/scripts/pack/args.py, ${CP}/scripts/pack/templates.py, ${CP}/scripts/pack/__main__.py` },
]

const ANGLE_FINDERS = [
  { label: 'x:crash-security', focus: 'angles 1-3 (crash-safety, logic correctness, security/safety) ACROSS BOTH skills. Hunt adversarial inputs that crash or leak. Trace every place a YAML value is used as a dict key, indexed, char-iterated, or path-joined.' },
  { label: 'x:determinism-dry', focus: 'angles 4-6 (determinism, DRY, dead code) ACROSS BOTH skills. Find non-deterministic ordering/timestamps, duplicated logic that should be a shared helper, and dead/unreachable code.' },
  { label: 'x:stale-callers', focus: 'angle 7 (stale callers / incomplete hoists) ACROSS BOTH skills — THE PRIMARY C11 WATCH. For every shared helper introduced in C8/C9/C10 (resolve_ac, _scalar_id/_scalar_link, ID_SENTINELS, resolve_competition, make_finding, HORIZON_ORDER, moscow_story_counts, competitor_id_to_name, match_hooks, _as_id_list, _check_path_safety/relative_to containment), grep ALL call sites and confirm none still uses the old inline path or a divergent copy.' },
  { label: 'x:altitude-drift', focus: 'angles 8-9 (contract/doc drift, abstraction altitude) ACROSS BOTH skills. Compare code behavior against the claims in both SKILL.md, CLAUDE.md (repo root), and references. Flag Script-vs-LLM split violations.' },
]

const REFERENCE_FINDERS = [
  { label: 'ref:product-spec', files: `all of ${PS}/references/*.md and ${PS}/SKILL.md, compared against ${PS}/scripts/*.py behavior` , focus: 'doc-drift: every claim in the references/SKILL.md that the code contradicts, and every code behavior the docs fail to document. Focus on the v2 multidim feature (risk/time/competition), the visualization output contract, and the script CLI contract.' },
  { label: 'ref:claude-pack', files: `all of ${CP}/references/*.md and ${CP}/SKILL.md and the repo-root CLAUDE.md claude-pack section, compared against ${CP}/scripts behavior`, focus: 'doc-drift: error-catalog codes vs raised codes, flag-reference vs cli.py/args.py, safety-rules vs safety_check.py, manifest-spec vs manifest_loader.py, exit codes.' },
]

// ---------------- FIND ----------------
phase('Find')
log(`Cycle 11: launching ${SUBSYSTEM_FINDERS.length} subsystem + ${ANGLE_FINDERS.length} cross-cutting + ${REFERENCE_FINDERS.length} reference finders`)

const finderThunks = [
  ...SUBSYSTEM_FINDERS.map(f => () =>
    agent(`${CONTEXT}\n\nYOUR ASSIGNMENT (subsystem finder): review these files across ALL 9 angles:\n${f.files}\n\nRead each file fully. Run repros where a crash is plausible. Return findings.`,
      { label: f.label, phase: 'Find', schema: FINDINGS_SCHEMA })),
  ...ANGLE_FINDERS.map(f => () =>
    agent(`${CONTEXT}\n\nYOUR ASSIGNMENT (cross-cutting angle finder): ${f.focus}\nSweep the relevant files in both ${PS}/scripts and ${CP}/scripts. Return findings.`,
      { label: f.label, phase: 'Find', schema: FINDINGS_SCHEMA })),
  ...REFERENCE_FINDERS.map(f => () =>
    agent(`${CONTEXT}\n\nYOUR ASSIGNMENT (reference/doc-drift finder): ${f.focus}\nFiles: ${f.files}\nReturn findings (use angle 8 for doc-drift, angle 9 for altitude).`,
      { label: f.label, phase: 'Find', schema: FINDINGS_SCHEMA })),
]

const rawResults = (await parallel(finderThunks)).filter(Boolean)
const rawFindings = rawResults.flatMap(r => r.findings || [])
log(`Find complete: ${rawFindings.length} raw findings from ${rawResults.length} finders`)

// ---------------- CONSOLIDATE ----------------
phase('Consolidate')
let deduped = rawFindings
if (rawFindings.length > 0) {
  const consolidation = await agent(
    `You are the consolidation step of a code review. Below are ${rawFindings.length} raw findings (JSON) from parallel finders that had OVERLAPPING file ownership.\n\n` +
    `Dedup by (file + nearby line + same mechanism): merge findings that describe the SAME underlying issue even if titles differ. Keep the clearest title/detail and the HIGHEST severity among merged. Preserve distinct issues. Do NOT drop a finding just because it seems minor.\n\n` +
    `Raw findings:\n${JSON.stringify(rawFindings, null, 1)}\n\nReturn the deduped findings array.`,
    { label: 'consolidate', phase: 'Consolidate', schema: FINDINGS_SCHEMA })
  deduped = consolidation.findings || rawFindings
}
log(`Consolidated: ${rawFindings.length} -> ${deduped.length} distinct findings`)

// ---------------- VERIFY (3-state, adversarial, per finding) ----------------
phase('Verify')
const verified = (await parallel(deduped.map((f, i) => () =>
  agent(`${CONTEXT}\n\nYOU ARE AN ADVERSARIAL VERIFIER. A finder claims the following. Try HARD to REFUTE it by reading the actual code at the cited location and tracing the real control/data flow. Default to 'refuted' if you cannot prove the bad outcome is reachable. Mark 'uncertain' only if genuinely undecidable without the owner.\n\nCLAIM:\n${JSON.stringify(f, null, 1)}\n\nRead ${f.file} around line ${f.line} (and callers if needed). Return your verdict. Set is_locked_decision=true if it collides with any GOAL.md locked decision or the REFUTED list. Set fix_risk per how mechanical the fix is.`,
    { label: `verify:${f.file.split('/').pop()}:${f.line}`, phase: 'Verify', schema: VERDICT_SCHEMA })
    .then(v => ({ ...f, verdict: v }))
))).filter(Boolean)

const confirmed = verified.filter(f => f.verdict && f.verdict.state === 'confirmed')
const uncertain = verified.filter(f => f.verdict && f.verdict.state === 'uncertain')
const refuted = verified.filter(f => f.verdict && f.verdict.state === 'refuted')
log(`Verify: ${confirmed.length} confirmed, ${uncertain.length} uncertain, ${refuted.length} refuted`)

// ---------------- SWEEP ----------------
phase('Sweep')
const confirmedSummary = confirmed.map(f => `${f.severity} ${f.file}:${f.line} ${f.mechanism} — ${f.title}`).join('\n') || '(none yet)'
const sweepThunks = [
  () => agent(`${CONTEXT}\n\nFINAL SWEEP (product-spec). The review already CONFIRMED these:\n${confirmedSummary}\n\nLook for what the partitioned finders MISSED in ${PS}/scripts and ${PS}/references: cross-file interactions, a modality not run, a contract claim unverified. Especially re-check the C10 PRIMARY WATCH surface for any second raw-key renderer site or stale caller missed. Return only NEW findings not already listed.`,
    { label: 'sweep:product-spec', phase: 'Sweep', schema: FINDINGS_SCHEMA }),
  () => agent(`${CONTEXT}\n\nFINAL SWEEP (claude-pack). The review already CONFIRMED these:\n${confirmedSummary}\n\nLook for what the partitioned finders MISSED in ${CP}/scripts and ${CP}/references: tarball determinism edge cases, safety-filter bypass, installer recipient-side traversal, exit-code drift. Return only NEW findings not already listed.`,
    { label: 'sweep:claude-pack', phase: 'Sweep', schema: FINDINGS_SCHEMA }),
]
const sweepRaw = (await parallel(sweepThunks)).filter(Boolean).flatMap(r => r.findings || [])
log(`Sweep raw: ${sweepRaw.length} candidate new findings`)

// verify sweep findings too
const sweepVerified = (await parallel(sweepRaw.map(f => () =>
  agent(`${CONTEXT}\n\nADVERSARIAL VERIFIER (sweep finding). Try to refute. Read the code.\n\nCLAIM:\n${JSON.stringify(f, null, 1)}\n\nReturn verdict.`,
    { label: `sweep-verify:${f.file.split('/').pop()}:${f.line}`, phase: 'Sweep', schema: VERDICT_SCHEMA })
    .then(v => ({ ...f, verdict: v }))
))).filter(Boolean)
const sweepConfirmed = sweepVerified.filter(f => f.verdict && f.verdict.state === 'confirmed')
const sweepUncertain = sweepVerified.filter(f => f.verdict && f.verdict.state === 'uncertain')
log(`Sweep confirmed: ${sweepConfirmed.length} new, ${sweepUncertain.length} uncertain`)

return {
  cycle: 11,
  counts: {
    raw: rawFindings.length,
    deduped: deduped.length,
    confirmed: confirmed.length + sweepConfirmed.length,
    uncertain: uncertain.length + sweepUncertain.length,
    refuted: refuted.length,
  },
  confirmed: [...confirmed, ...sweepConfirmed],
  uncertain: [...uncertain, ...sweepUncertain],
  refuted,
}
