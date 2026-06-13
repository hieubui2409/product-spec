export const meta = {
  name: 'harness-v240-code-audit',
  description: 'Width-3 multi-lens code audit of the product-spec harness v2.4.0 (4 skills, 11 clusters): audit -> adversarial refute -> per-skill completeness. Returns structured findings JSON.',
  phases: [
    { title: 'Audit' },
    { title: 'Refute' },
    { title: 'Completeness' },
  ],
}

// --- width-3 pool: at most 3 audit->refute chains in flight at once ---
async function poolMap(items, limit, fn) {
  const results = new Array(items.length)
  let next = 0
  async function worker() {
    while (next < items.length) {
      const idx = next++
      results[idx] = await fn(items[idx], idx)
    }
  }
  const n = Math.min(limit, items.length)
  await Promise.all(Array.from({ length: n }, () => worker()))
  return results
}

const SKILLS = '/home/hieubt15/Documents/vsf/product-spec/.claude/skills'
const CTX = '/home/hieubt15/Documents/vsf/product-spec/plans/260613-1739-harness-v240-audit/shared-context.md'

// 11 clusters. files are repo-relative to .claude/skills/<skill>/scripts/ unless noted.
const CLUSTERS = [
  { code: 'ps-a', skill: 'product-spec', title: 'Graph core & parsing',
    files: ['spec_graph.py','frontmatter_parser.py','encoding_utils.py','fs_guard.py','register_store.py','template_id_alloc.py','strict_gate.py','preferences.py','i18n_labels.py'] },
  { code: 'ps-b', skill: 'product-spec', title: 'Structural validators',
    files: ['check_consistency.py','check_consistency_product.py','check_consistency_schema.py','check_consistency_risk.py','check_consistency_time.py','check_consistency_competition.py','check_traceability.py','check_fence.py','build_traceability_matrix.py','memory_gap.py','open_questions.py'] },
  { code: 'ps-c', skill: 'product-spec', title: 'Judgment, anchors, decision register, staleness',
    files: ['judgment_cache.py','judgment_cache_keys.py','competitive_drift_anchors.py','time_realism_anchors.py','time_advisory.py','decision_register.py','decision_register_view.py','session_staleness.py'] },
  { code: 'ps-d', skill: 'product-spec', title: 'Migrators, templates, ingest, changelog, status',
    files: ['migrate_backfill_ids.py','migrate_metric_to_metrics.py','migrate_multidim_fields.py','generate_templates.py','ingest_raw_inputs.py','change_log_writer.py','status.py','status_vcs.py'] },
  { code: 'ps-e', skill: 'product-spec', title: 'Snapshot, audit-trail, outcomes, reflect, behavioral memory',
    files: ['snapshot.py','assemble_audit_trail.py','assemble_digest.py','record_outcome.py','outcome_verdict.py','load_outcomes.py','reflect_scan.py','behavioral_memory.py','behavioral_memory_po_style.py','behavioral_memory_self_corrections.py','visuals_retention.py'] },
  { code: 'ps-f1', skill: 'product-spec', title: 'Rendering core',
    files: ['visualize.py','render_ascii.py','render_mermaid.py','render_html.py','render_export.py','render_ascii_board.py','render_board.py','render_common.py','render_html_escape.py'] },
  { code: 'ps-f2', skill: 'product-spec', title: 'HTML sub-renderers, outcomes/explorer/learning render, critique parse/apply',
    files: ['render_html_assets.py','render_html_competition.py','render_html_governance.py','render_html_tooltip.py','render_html_risk_grid.py','render_html_count_grid.py','render_explorer.py','render_outcomes.py','render_learning.py','parse_critique_report.py','apply_critique_progress.py'] },
  { code: 'cr-g', skill: 'product-spec-critique', title: 'Critique scan/bundle/inherit/cache/language',
    files: ['critique_inherit.py','critique_provenance.py','check_report_language.py','critique_signals.py','critique_bundle.py','critique_scan.py','critique_cache.py','critique_common.py','critique_drift.py','critique_persist.py','critique_blob_cache.py','critique_cache_io.py'] },
  { code: 'rel-h1', skill: 'release', title: 'Pack pipeline, release, safety',
    files: ['release.py','release_check_guard.py','safety_check.py','safety_catalog.py','pack/cli.py','pack/args.py','pack/selection.py','pack/pipeline.py','pack/tarball.py','pack/manifest_io.py','pack/templates.py','pack/__init__.py','pack/__main__.py'] },
  { code: 'rel-h2', skill: 'release', title: 'Manifest family, upgrade planner/apply, version verify',
    files: ['upgrade_planner.py','upgrade_apply.py','manifest_loader.py','manifest_validator.py','build_manifest.py','build_manifest_writer.py','build_manifest_questions.py','build_manifest_discover.py','manifest_on_disk_checks.py','verify_skill_versions.py','manifest_path_guards.py','manifest_constants.py'] },
  { code: 'tel-i', skill: 'telemetry', title: 'Telemetry lenses, render, harvester, hooks, paths',
    files: ['telemetry_render.py','register_telemetry_hooks.py','telemetry_paths.py','analyze_telemetry.py','harvester.py','lens_memory_health.py','lens_usage_tokens.py','lens_workflow_chains.py','lens_forensics.py','catalog.py','lens_validate_proxy.py','lens_product_memory.py','formatters.py','lens_artifact_heat.py','lens_reliability.py','lens_health.py','lens_session_shape.py'] },
]

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          cluster: { type: 'string' },
          file: { type: 'string' },
          lens: { type: 'string', enum: ['correctness','contract','safety','dry-dead','test'] },
          severity: { type: 'string', enum: ['blocker','high','medium','low'] },
          evidence: { type: 'string' },
          title: { type: 'string' },
          why: { type: 'string' },
          fix: { type: 'string' },
          confidence: { type: 'string', enum: ['high','medium','low'] },
        },
        required: ['id','cluster','file','lens','severity','evidence','title','why','fix','confidence'],
        additionalProperties: false,
      },
    },
  },
  required: ['findings'],
  additionalProperties: false,
}

const VERDICTS_SCHEMA = {
  type: 'object',
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          verdict: { type: 'string', enum: ['real','false_positive','needs_context','downgrade','upgrade'] },
          adjusted_severity: { type: 'string', enum: ['blocker','high','medium','low','none'] },
          reason: { type: 'string' },
        },
        required: ['id','verdict','adjusted_severity','reason'],
        additionalProperties: false,
      },
    },
  },
  required: ['verdicts'],
  additionalProperties: false,
}

const COMPLETENESS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          file: { type: 'string' },
          lens: { type: 'string', enum: ['contract','dry-dead','correctness','safety','test'] },
          severity: { type: 'string', enum: ['blocker','high','medium','low'] },
          evidence: { type: 'string' },
          title: { type: 'string' },
          why: { type: 'string' },
          fix: { type: 'string' },
          confidence: { type: 'string', enum: ['high','medium','low'] },
        },
        required: ['id','file','lens','severity','evidence','title','why','fix','confidence'],
        additionalProperties: false,
      },
    },
  },
  required: ['findings'],
  additionalProperties: false,
}

function auditPrompt(c) {
  const paths = c.files.map(f => `${SKILLS}/${c.skill}/scripts/${f}`).join('\n  ')
  return `You are a senior code auditor. FIRST read the shared context at ${CTX} (the full audit rubric, severity bar, citation rules, tone). Then read the skill contract ${SKILLS}/${c.skill}/SKILL.md.

Your cluster is "${c.code}" — ${c.title} (skill: ${c.skill}). Audit EXACTLY these files, reading each in full:
  ${paths}

Apply ALL FIVE lenses from the rubric (correctness, contract-fidelity vs SKILL.md, safety/integration, DRY/dead-code/incompleteness, test-quality). For test-quality, also glance at the matching tests under ${SKILLS}/${c.skill}/scripts/tests/ for the files you audit (e.g. time-dependent or assert-nothing tests).

Return ONLY real, defensible defects at the calibration bar in the rubric — concrete file + real line number + concrete failure mode + concrete fix. Do NOT pad with style nitpicks or speculative issues. A clean file yields zero findings. Set confidence honestly. Cluster code for every finding id prefix: "${c.code}".`
}

function refutePrompt(c, findingsJson) {
  return `You are an adversarial verifier. Your default stance is SKEPTICAL: assume each finding is wrong until the code proves it right. FIRST read the shared context at ${CTX} for the severity bar.

Below are findings another auditor reported for cluster "${c.code}" (${c.title}, skill ${c.skill}). For EACH finding, open the cited file at the cited line (under ${SKILLS}/${c.skill}/scripts/) and independently judge:
- Is it a REAL defect, or a false positive (misread code, intended behavior, handled elsewhere)?
- Is the severity right? (downgrade/upgrade with adjusted_severity)
- Does it need product/contract context to decide? (needs_context)

Be ruthless about false positives — a plausible-but-wrong finding that survives pollutes the report. But do NOT reject a real defect just because it's uncomfortable. Give a one-line reason citing what you saw in the code.

Findings JSON:
${findingsJson}

Return a verdict for every finding id.`
}

function completenessPrompt(skill, inventory, confirmedJson) {
  return `You are a completeness & contract-fidelity auditor for ONE skill. FIRST read the shared context at ${CTX}, then read the full contract ${SKILLS}/${skill}/SKILL.md.

Skill: ${skill}. Its script inventory (name — LOC):
${inventory}

Findings already CONFIRMED real in the per-file audit (so you don't repeat them):
${confirmedJson}

Your distinct job — find what the per-file pass structurally cannot see:
1. CONTRACT GAPS: a flag / sub-command / output / GATE behavior that SKILL.md PROMISES but no script implements (or implements differently). Grep the scripts dir to confirm absence before claiming it.
2. WIRING GAPS: a writer with no reader, a produced artifact nothing consumes, a check with no migrator/fix path, a feature half-wired across scripts.
3. CROSS-SCRIPT DRY: the same logic implemented in 2+ scripts that can drift apart.
4. MISSING SAFETY ENFORCEMENT: a GATE the contract says is enforced, but no code path actually enforces (e.g. approved-reversal, never-assume, fs_guard coverage).

Use Glob/Grep across ${SKILLS}/${skill}/scripts/ to verify presence/absence — never claim "missing" without grepping. Return only defensible, concrete gaps with evidence (file:line, or "absent: <grep term> not found in scripts/"). Id prefix: "comp-${skill}".`
}

// ---------------- run ----------------
phase('Audit')
log(`Auditing ${CLUSTERS.length} clusters at width-3 (audit -> refute per cluster)...`)

const perCluster = await poolMap(CLUSTERS, 3, async (c) => {
  const audit = await agent(auditPrompt(c), { label: `audit:${c.code}`, phase: 'Audit', schema: FINDINGS_SCHEMA, agentType: 'Explore' })
  const findings = (audit && audit.findings) || []
  if (findings.length === 0) {
    return { cluster: c.code, skill: c.skill, findings: [], verdicts: [] }
  }
  const refute = await agent(refutePrompt(c, JSON.stringify(findings)), { label: `refute:${c.code}`, phase: 'Refute', schema: VERDICTS_SCHEMA, agentType: 'Explore' })
  return { cluster: c.code, skill: c.skill, findings, verdicts: (refute && refute.verdicts) || [] }
})

// merge verdicts into findings -> confirmed set per skill
const VERDICT_DROP = new Set(['false_positive'])
function applyVerdicts(entry) {
  const vmap = new Map((entry.verdicts || []).map(v => [v.id, v]))
  const kept = []
  for (const f of entry.findings) {
    const v = vmap.get(f.id)
    if (!v) { kept.push({ ...f, verdict: 'real', verdict_reason: '(no verdict returned)' }); continue }
    if (VERDICT_DROP.has(v.verdict)) continue
    let sev = f.severity
    if ((v.verdict === 'downgrade' || v.verdict === 'upgrade') && v.adjusted_severity && v.adjusted_severity !== 'none') sev = v.adjusted_severity
    kept.push({ ...f, severity: sev, verdict: v.verdict, verdict_reason: v.reason })
  }
  return kept
}

const confirmedAll = perCluster.flatMap(applyVerdicts)
log(`Audit+refute done. ${confirmedAll.length} findings survived refute across ${CLUSTERS.length} clusters.`)

// group confirmed by skill for completeness prompts
const bySkill = {}
for (const f of confirmedAll) {
  const sk = (CLUSTERS.find(c => c.code === f.cluster) || {}).skill || 'product-spec'
  ;(bySkill[sk] = bySkill[sk] || []).push(f)
}

const INVENTORIES = {
  'product-spec': CLUSTERS.filter(c => c.skill === 'product-spec').flatMap(c => c.files).map(f => `  ${f}`).join('\n'),
  'product-spec-critique': CLUSTERS.filter(c => c.skill === 'product-spec-critique').flatMap(c => c.files).map(f => `  ${f}`).join('\n'),
  'release': CLUSTERS.filter(c => c.skill === 'release').flatMap(c => c.files).map(f => `  ${f}`).join('\n'),
  'telemetry': CLUSTERS.filter(c => c.skill === 'telemetry').flatMap(c => c.files).map(f => `  ${f}`).join('\n'),
}

phase('Completeness')
const skillList = ['product-spec','product-spec-critique','release','telemetry']
const completeness = await poolMap(skillList, 3, async (sk) => {
  const confirmedJson = JSON.stringify((bySkill[sk] || []).map(f => ({ id: f.id, file: f.file, title: f.title })))
  const r = await agent(completenessPrompt(sk, INVENTORIES[sk], confirmedJson), { label: `complete:${sk}`, phase: 'Completeness', schema: COMPLETENESS_SCHEMA, agentType: 'Explore' })
  return { skill: sk, findings: (r && r.findings) || [] }
})

return {
  perClusterConfirmed: perCluster.map(e => ({ cluster: e.cluster, skill: e.skill, confirmed: applyVerdicts(e), rawCount: e.findings.length })),
  confirmedAll,
  completeness,
}
