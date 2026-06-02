export const meta = {
  name: 'spec-critique-voice-ladder-regen',
  description: 'Regenerate the spec-critique report at all 6 voice levels over the e2e dating-app spec, using the FIXED pipeline (v2 bundle source_files citation ground-truth + agent output contracts + human-voice layer). Runs the bundle + 4 lenses ONCE (substance is level-independent), then consolidate+humanize+write SIX times (level 1..6) so the six reports are the same findings rendered in six tones. Sequential renders (one write at a time).',
  phases: [
    { title: 'Lenses' },
    { title: 'Render' },
  ],
}

const REPO = '/home/hieubt/Documents/cleanmatic-skills'
const E2E = `${REPO}/e2e/dating-app`
const DP = `${E2E}/docs/product`
const PY = `${REPO}/.claude/skills/.venv/bin/python3`
const SC = `${REPO}/.claude/skills/spec-critique/scripts`
const SCOPE = 'all'
const ENVNOTE = `Environment: OS linux, repo ${REPO}. venv python: ${PY}. spec-critique scripts: ${SC}. The e2e spec is at ${E2E}; skill writes ONLY under ${DP}. lang=vi. NEVER write outside ${E2E}.`

const FINDINGS_SCHEMA = {
  type: 'object',
  required: ['findings', 'editorial_verdict'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['lens', 'evidence', 'critique', 'why_it_dies', 'fix', 'severity'],
        properties: {
          lens: { type: 'string' },
          evidence: { type: 'string', description: 'ID:line, the line read from source_files' },
          critique: { type: 'string', description: 'plain grounded observation; the consolidator applies the voice/level' },
          why_it_dies: { type: 'string' },
          fix: { type: 'string' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          source: { type: 'string' },
        },
      },
    },
    editorial_verdict: { type: 'string' },
  },
}

const LEVELS = [
  { n: 1, alias: 'warm' },
  { n: 2, alias: 'gentle' },
  { n: 3, alias: 'blunt' },
  { n: 4, alias: 'savage' },
  { n: 5, alias: 'no-mercy' },
  { n: 6, alias: 'roast' },
]

// ---- Phase 1: bundle + lenses ONCE (substance is level-independent) ----
phase('Lenses')

const bundle = await agent(
  `${ENVNOTE}\n\nAssemble the spec-critique bundle. RUN exactly:\n${PY} ${SC}/critique_scan.py --root ${E2E} --scope ${SCOPE} --lang vi\nWrite the stdout JSON to ${E2E}/.regen-bundle.json and return ONLY the absolute path to that file as plain text. If the JSON has an "error" key, return the full JSON instead.`,
  { label: 'bundle', phase: 'Lenses', agentType: 'general-purpose' }
)
const bundlePath = (bundle || '').trim()

const LENSES = [
  { key: 'product', web: false },
  { key: 'tech', web: false },
  { key: 'market', web: true },
  { key: 'craft', web: false },
]
const lensResults = await parallel(LENSES.map((l) => () =>
  agent(
    `${ENVNOTE}\n\nYou are the ${l.key.toUpperCase()} lens. READ the bundle JSON at: ${bundlePath}\nProduce your findings for scope=${SCOPE}. CRITICAL: every finding's evidence MUST be <artifact_id>:<line> where the prefix is the artifact's id (use VISION for the vision narrative, BRD/BRD-G<n> for BRD content; NEVER a bare file path like vision.md:23) and the line is the REAL number you read in bundle.source_files[<that same id>] next to the quoted text. Do NOT invent or use bundle-JSON offsets. Write the "critique" field as a plain grounded observation (the consolidator will apply the level voice later, so do not pre-style it). ${l.key === 'market' ? 'Web enabled: you may WebSearch/WebFetch and cite urls in source.' : ''}`,
    { label: `lens:${l.key}`, phase: 'Lenses', schema: FINDINGS_SCHEMA, agentType: `spec-critique-${l.key}` }
  ).then((r) => ({ lens: l.key, ...(r || { findings: [], editorial_verdict: '(lens failed)' }) }))
))
const lenses = lensResults.filter(Boolean)
log(`Lenses done: ${lenses.map((l) => `${l.lens}=${(l.findings || []).length}`).join(' ')}`)

// ---- Phase 2: render the SAME findings at each of the 6 levels (sequential write) ----
phase('Render')

for (const lv of LEVELS) {
  const dangerNote = lv.n >= 5
    ? `\nDANGER GATE: level ${lv.n}. The user explicitly requested the full 1..6 ladder, so the gate is PRE-CONFIRMED for this regeneration. ${lv.n === 6 ? 'Level 6 REQUIRES a direct personal roast of the author as lazy/careless on THIS spec; HARD FLOOR: every line still cites ID:line + ends in a real fix; attack only effort/care, NEVER identity/protected-characteristics/slurs/threats/self-harm.' : 'Level 5 LIFTS the redline (personal barb permitted, not required); evidence+fix every line.'}`
    : ''
  const consolidated = await agent(
    `${ENVNOTE}\n\nConsolidate these lens findings into ONE markdown critique at --level ${lv.n} (${lv.alias}), lang vi, scope ${SCOPE}.\nLENS FINDINGS (JSON): ${JSON.stringify(lenses)}\nPRIOR reports: none (this is a fresh voice-ladder render, so the "Lặp lại từ lần trước" section says không có).\nRender the level-${lv.n} why/fix LABELS in the findings per voice-and-tone.md (do not omit them). Apply the human-voice layer: concrete physical imagery, varied rhythm, verdict-first, honest about severity. FIRST-PERSON rule: ${lv.n <= 2 ? 'levels 1-2 stay artifact-focused, NO critic first-person reaction.' : `level ${lv.n} MAY use the critic's first-person reaction to reading the spec, escalating with the level (separate axis from the personal-attack redline).`} Humanize as you draft (Gate 1: no AI-tells, no em/en dashes, no calqued VN). OUTPUT CONTRACT: your entire reply is the report markdown beginning at the first # heading, emitted exactly once, no preamble/notes/drafts.${dangerNote}`,
    { label: `lvl${lv.n}:consolidate`, phase: 'Render', agentType: 'spec-critique-consolidate' }
  )
  const humanized = await agent(
    `${ENVNOTE}\n\nGate-2 humanize this level-${lv.n} critique. Strip AI-tells + em/en dashes + calqued VN, ENFORCE the human-voice layer (concrete imagery, varied rhythm, verdict-first; first-person reaction only if level>=3), while PRESERVING every finding, evidence ID:line, fix, the level-${lv.n} tone (the L5/L6 personal attack stays), and structure. OUTPUT CONTRACT: reply is ONLY the cleaned report markdown, begins at the first # heading, emitted exactly once, no preamble/notes/drafts, no em/en dashes.\n\nCRITIQUE:\n${consolidated}`,
    { label: `lvl${lv.n}:humanize`, phase: 'Render', agentType: 'spec-critique-humanize' }
  )
  await agent(
    `${ENVNOTE}\n\nPersist the level-${lv.n} report. SANITIZE then write:\n1) Take the markdown below. Strip anything before the first line starting with '# '. If more than one '# Critique' heading exists (duplicate drafts), keep only the LAST complete copy. Replace any em/en dash (—, –) in prose with a comma/colon/period, but leave dashes inside \`code\` and verbatim quotes.\n2) Write the sanitized result to ${DP}/critique/voice-ladder-${SCOPE}-lvl${lv.n}.md (create critique/ if missing). The file MUST begin with '# Critique:'.\nConfirm the first line of the written file.\n\nMARKDOWN:\n${humanized}`,
    { label: `lvl${lv.n}:write`, phase: 'Render', agentType: 'general-purpose' }
  )
  log(`Level ${lv.n} (${lv.alias}) report written.`)
}

// refresh the drift marker once at the end
await agent(
  `${ENVNOTE}\n\nRefresh the drift marker: RUN ${PY} ${SC}/critique_scan.py --root ${E2E} --snapshot --scope ${SCOPE}. Confirm exit 0.`,
  { label: 'snapshot', phase: 'Render', agentType: 'general-purpose' }
)

return {
  scope: SCOPE,
  levels: LEVELS.map((l) => l.n),
  reports: LEVELS.map((l) => `${DP}/critique/voice-ladder-${SCOPE}-lvl${l.n}.md`),
  lens_finding_counts: lenses.map((l) => ({ lens: l.lens, n: (l.findings || []).length })),
}
