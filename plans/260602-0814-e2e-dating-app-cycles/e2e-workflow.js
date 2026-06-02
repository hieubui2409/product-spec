export const meta = {
  name: 'spec-critique-e2e-dating-app',
  description: 'E2E dogfood: 10 sequential cycles of product-spec build/evolve -> LLM+structural validate -> spec-critique (4 real lens agents + consolidate + humanize) -> per-cycle AI semantic review, over a fictional nationwide VN dating app. Sequential cycles (no concurrent writes to the same e2e folder); only read-only lenses fan out.',
  phases: [
    { title: 'Cycles' },
    { title: 'Wrap-up' },
  ],
}

// ---------------------------------------------------------------------------
// Fixed paths (absolute, so workflow agents never depend on CWD)
// ---------------------------------------------------------------------------
const REPO = '/home/hieubt/Documents/cleanmatic-skills'
const E2E = `${REPO}/e2e/dating-app`
const DP = `${E2E}/docs/product`
const PY = `${REPO}/.claude/skills/.venv/bin/python3`
const PSP = `${REPO}/.claude/skills/product-spec/scripts`
const SC = `${REPO}/.claude/skills/spec-critique/scripts`
const ENVNOTE = `Environment: OS linux, repo ${REPO}. Run ALL python via the shared venv: ${PY}. product-spec scripts: ${PSP}/<name>.py --root ${E2E}. spec-critique scripts: ${SC}/<name>.py --root ${E2E}. The e2e product lives at ${E2E}; the skill writes ONLY under ${DP}. lang of this spec = vi. NEVER write outside ${E2E}.`

// ---------------------------------------------------------------------------
// Product brief (the "full info" that replaces the interactive interview)
// ---------------------------------------------------------------------------
const BRIEF = `
FICTIONAL PRODUCT (lang: vi): "Ghép Đôi Việt" — ứng dụng hẹn hò toàn quốc cho người Việt.
Bắc nguyên tắc product-spec: frontmatter là source-of-truth; ID parent-scoped (BRD-G<n>, PRD-<SLUG>, PRD-<SLUG>-E<n>, PRD-<SLUG>-E<n>-S<n>); story phải có AC.

NORTH-STAR: số cặp đôi duy trì nhắn tin qua lại >= 7 ngày trong tháng (kết nối thật, không chỉ match ảo).

PERSONAS (label ở PRODUCT.md, narrative ở vision.md):
- P-URBAN: người trẻ thành thị (25-32, HN/HCM), bận rộn, muốn mối quan hệ nghiêm túc.
- P-PROVINCE: người ở tỉnh lẻ, pool địa phương nhỏ, muốn mở rộng kết nối ra toàn quốc.
- P-RETURNEE: người Việt xa quê / du học, muốn tìm bạn cùng văn hoá.

BRD GOALS (brd.md):
- BRD-G1: đạt 100k MAU trong năm đầu. metric: MAU hàng tháng.
- BRD-G2: 20% người dùng hoạt động tạo >=1 match mỗi tuần. metric: weekly match rate.
- BRD-G3: doanh thu premium đủ hoà vốn vận hành vào năm 2. metric: tỉ lệ chuyển đổi premium + ARPU.
competitors (BRD frontmatter, dạng list {id,name,url,threat}): COMP-TINDER (Tinder), COMP-BUMBLE (Bumble), COMP-HEN (Hẹn, local), COMP-FIKA (Fika).

PRD ROADMAP (rải qua các cycle, KHÔNG dựng hết ở C1):
- PRD-MATCH: khám phá + quẹt + ghép đôi (core). [C1]
- PRD-SAFETY: xác minh danh tính + chống lừa đảo/catfish. [C2]
- PRD-CHAT: nhắn tin. [C3]
- PRD-EVENTS: sự kiện gặp mặt offline toàn quốc (CỐ Ý gold-plating, lệch north-star). [C4]
- PRD-PREMIUM: gói trả phí (xem ai thích mình, boost). [C5]
- PRD-AIREC: gợi ý ghép đôi bằng AI (me-too, để test market lens). [C8]

CỐ Ý CÀI LỖI (để critique có cái cắn — đây là điểm e2e semantic):
- C1: PRD-MATCH có 1 story với AC mơ hồ "ghép đôi nhanh và chính xác" (tính từ không đo được, không ngưỡng) -> craft + tech bait. KHÔNG sửa nó cho tới sau C6 (để test repeat-offense).
- C4: PRD-EVENTS lệch core-value (north-star là nhắn tin, không phải event offline), moscow:could nhưng mô tả như flagship -> product + market bait (gold-plating / solution-first).
- C8: PRD-AIREC competitive_parity behind cả đối thủ nhưng moscow:could -> market drift; chạy --no-web để test "thiếu căn cứ cạnh tranh".
`

// ---------------------------------------------------------------------------
// 10-cycle plan: each evolves the spec (delta) + a varied critique config that
// covers a different skill use-case. expect = what the per-cycle judge checks.
// ---------------------------------------------------------------------------
const LENS_ALL = ['product', 'tech', 'market', 'craft']
const CYCLES = [
  {
    n: 1, scope: 'all', lenses: LENS_ALL, level: 3, web: true,
    evolve: 'BOOTSTRAP base spec. Create docs/product structure. Author vision.md (north-star + 3 personas narrative), PRODUCT.md (persona labels P-URBAN/P-PROVINCE/P-RETURNEE + horizon), brd.md (BRD-G1/G2/G3 + metrics + competitors list). Then PRD-MATCH (1 epic, 2 stories). One story MUST carry the vague AC "ghép đôi nhanh và chính xác" (no threshold). Use generate_templates.py for IDs. Ensure check_consistency + check_traceability return zero error findings.',
    expect: 'First run, no prior reports => repeat-offense must say "không có". Craft/tech must catch the vague "nhanh/chính xác" AC on the PRD-MATCH story (no measurable threshold). Level 3 default voice. Every finding cites ID:line + ends in a fix.',
  },
  {
    n: 2, scope: 'PRD-SAFETY', lenses: ['tech', 'craft'], level: 2, web: false,
    evolve: 'ADD PRD-SAFETY (xác minh danh tính qua selfie + giấy tờ, chống catfish/lừa đảo) with 1 epic + 2 stories with proper measurable AC. Keep PRD-MATCH untouched (the vague AC stays).',
    expect: 'Branch scope = PRD-SAFETY only; full ancestry pulled as context. Only tech+craft lenses ran. Level 2 dry voice (no personal attack).',
  },
  {
    n: 3, scope: 'all', lenses: LENS_ALL, level: 1, web: false,
    evolve: 'ADD PRD-CHAT (nhắn tin realtime, đã match mới chat được) with 1 epic + 2 stories with measurable AC.',
    expect: 'Level 1 warm labels (Chỗ này đáng lưu tâm / Có thể thử). --no-web: market lens leans on BRD competitors, must NOT fabricate. Tone gentle but findings still grounded.',
  },
  {
    n: 4, scope: 'PRD-EVENTS', lenses: ['product', 'market'], level: 4, web: true,
    evolve: 'ADD PRD-EVENTS (sự kiện gặp mặt offline toàn quốc) framed as a flagship feature but set moscow:could, horizon:later. This is DELIBERATELY off the messaging north-star (gold-plating / solution-first). 1 epic + 2 stories.',
    expect: 'Product lens must flag gold-plating / off core-value (events vs messaging north-star). Market lens questions the moat / cost vs core. Level 4 savage labels (Chết ở chỗ / Sửa ngay), still artifact-only (NO personal attack).',
  },
  {
    n: 5, scope: 'PRD-PREMIUM', lenses: ['market'], level: 3, web: true,
    evolve: 'ADD PRD-PREMIUM (gói trả phí: xem ai đã thích mình, boost hồ sơ, unlimited likes). Set competitive_parity to mostly at-par/behind vs COMP-TINDER/COMP-BUMBLE. 1 epic + 2 stories. This serves BRD-G3.',
    expect: 'Market lens only. Must judge revenue path / me-too monetization vs competitors (cite web or BRD competitors). Ties back to BRD-G3.',
  },
  {
    n: 6, scope: 'all', lenses: LENS_ALL, level: 3, web: true,
    evolve: 'NO new feature. Do a tiny unrelated edit (e.g. tighten one PRD-CHAT description sentence). CRITICALLY: leave the C1 vague "ghép đôi nhanh và chính xác" AC UNFIXED.',
    expect: 'REPEAT-OFFENSE must fire: the C1 vague-AC finding recurs and prior critique reports exist in docs/product/critique/ => consolidator must call it out ("đã nói ở lần trước, vẫn chưa sửa"). This is the key cross-report test.',
  },
  {
    n: 7, scope: 'PRD-CHAT', lenses: ['craft'], level: 2, web: false,
    evolve: 'ADD 2 stories to PRD-CHAT with DELIBERATELY vague AC: "trải nghiệm mượt mà" and "an toàn tuyệt đối" (unmeasurable adjectives).',
    expect: 'Craft lens must catch BOTH unmeasurable adjectives (mượt mà, an toàn tuyệt đối) and propose measurable rewrites. Level 2.',
  },
  {
    n: 8, scope: 'PRD-AIREC', lenses: ['market'], level: 3, web: false,
    evolve: 'ADD PRD-AIREC (gợi ý ghép đôi bằng AI) with competitive_parity = behind vs COMP-TINDER and COMP-BUMBLE, but moscow:could. 1 epic + 1 story.',
    expect: 'Market lens with --no-web: behind competitors + could priority is a drift (like acme-shop PRD-MOBILE). Must flag the parity-vs-priority contradiction WITHOUT fabricating competitor facts (web disabled). May tag DEC-worthy.',
  },
  {
    n: 9, scope: 'PRD-EVENTS', lenses: ['product', 'market', 'craft'], level: 5, web: true, dangerConfirmed: true,
    evolve: 'EXPAND PRD-EVENTS gold-plating further: add a story for "concert âm nhạc toàn quốc" inside the dating app. Even more off core-value.',
    expect: 'Level 5 (--no-mercy): redline LIFTED, a personal barb at the author is PERMITTED (not required). e2e harness pre-confirmed the danger gate (no interactive AskUserQuestion in a workflow). Floor still holds: every line cites ID:line + ends in a fix. Voice brutal/theatrical (Vì sao đi đời / Sửa cho đàng hoàng).',
  },
  {
    n: 10, scope: 'PRD-MATCH-E1-S1', lenses: ['craft', 'product'], level: 6, web: false, dangerConfirmed: true,
    evolve: 'NO new feature. Target the single worst story (the C1 vague-AC story, still unfixed). This is the level-6 roast target.',
    expect: 'Level 6 (--roast): personal attack REQUIRED, frames author as lazy/careless on THIS spec. e2e harness pre-confirmed the danger gate. HARD FLOOR: every line still cites ID:line + ends in a real fix; the roast attacks only effort/care on the spec, NEVER identity/protected-characteristics/slurs/threats/self-harm. NO genuine hate. Banh xác vì / Gõ lại giùm cái labels.',
  },
]

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const EVOLVE_SCHEMA = {
  type: 'object',
  required: ['changed_nodes', 'checks_clean', 'summary'],
  properties: {
    changed_nodes: { type: 'array', items: { type: 'string' }, description: 'artifact IDs added/modified this cycle' },
    files_written: { type: 'array', items: { type: 'string' } },
    checks_clean: { type: 'boolean', description: 'true if check_consistency + check_traceability had zero error-severity findings' },
    summary: { type: 'string' },
  },
}
const VALIDATE_SCHEMA = {
  type: 'object',
  required: ['structural_error_count', 'llm_verdicts', 'marker_written', 'summary'],
  properties: {
    structural_error_count: { type: 'integer' },
    structural_findings: { type: 'array', items: { type: 'object' } },
    llm_verdicts: { type: 'array', items: { type: 'object', properties: { node: { type: 'string' }, check: { type: 'string' }, verdict: { type: 'string' }, note: { type: 'string' } } } },
    marker_written: { type: 'boolean', description: 'true if .memory/last_validated.json was written via judgment_cache store path' },
    summary: { type: 'string' },
  },
}
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
          evidence: { type: 'string', description: 'ID:line' },
          critique: { type: 'string' },
          why_it_dies: { type: 'string' },
          fix: { type: 'string' },
          severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
          source: { type: 'string', description: 'market lens only: cited url' },
        },
      },
    },
    editorial_verdict: { type: 'string' },
  },
}
const JUDGE_SCHEMA = {
  type: 'object',
  required: ['cycle', 'score_0_100', 'verdict', 'every_finding_has_evidence', 'every_finding_has_fix', 'level_voice_match', 'planted_smells_caught', 'planted_smells_missed', 'fabrication_detected', 'validate_echo_detected', 'no_em_dash', 'notes'],
  properties: {
    cycle: { type: 'integer' },
    score_0_100: { type: 'integer' },
    verdict: { type: 'string', enum: ['pass', 'weak', 'fail'] },
    every_finding_has_evidence: { type: 'boolean' },
    every_finding_has_fix: { type: 'boolean' },
    level_voice_match: { type: 'boolean', description: 'does the rendered voice/labels match the requested level' },
    planted_smells_caught: { type: 'array', items: { type: 'string' } },
    planted_smells_missed: { type: 'array', items: { type: 'string' } },
    fabrication_detected: { type: 'boolean' },
    validate_echo_detected: { type: 'boolean', description: 'true if a finding merely restates a structural validate finding with no added why/fix' },
    repeat_offense_expected: { type: 'boolean' },
    repeat_offense_fired: { type: 'boolean' },
    danger_floor_ok: { type: ['boolean', 'null'], description: 'L5/L6 only: evidence+fix on every line AND no identity/slur/threat/self-harm; null if not applicable' },
    no_em_dash: { type: 'boolean', description: 'humanizer: report contains no em/en dashes' },
    notes: { type: 'string' },
  },
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function scopeSlug(scope) { return scope === 'all' ? 'all' : scope }
function reportName(c) { return `c${c.n}-${scopeSlug(c.scope)}-lvl${c.level}.md` }

// ---------------------------------------------------------------------------
// The cycle pipeline (SEQUENTIAL across cycles to avoid concurrent writes to
// the single e2e product folder; only the read-only lenses fan out in-cycle).
// ---------------------------------------------------------------------------
const scorecards = []

for (const c of CYCLES) {
  const ph = `c${c.n}`
  log(`Cycle ${c.n}/10 — scope=${c.scope} lenses=[${c.lenses.join(',')}] level=${c.level} web=${c.web}`)

  // --- A. EVOLVE (writes spec; sequential) ---
  const evolve = await agent(
    `${ENVNOTE}\n\nYou are operating the cleanmatic:product-spec skill (read its SKILL.md + references under ${REPO}/.claude/skills/product-spec/ as needed). This is e2e CYCLE ${c.n}. NO interactive interview is possible — use the brief below as the answered interview.\n\nPRODUCT BRIEF:\n${BRIEF}\n\nTHIS CYCLE'S EVOLVE TASK:\n${c.evolve}\n\nRULES: author/modify ONLY under ${DP}. Use ${PY} ${PSP}/generate_templates.py --root ${E2E} --type <t> [--slug/--parent] --lang vi --write to scaffold + allocate parent-scoped IDs, then fill frontmatter (English keys/IDs) + Vietnamese prose. Every story needs AC. After writing, RUN ${PY} ${PSP}/check_consistency.py --root ${E2E} and ${PY} ${PSP}/check_traceability.py --root ${E2E}; fix every error-severity finding and re-run until both are error-free (warnings are acceptable). Report what you changed.`,
    { label: `c${c.n}:evolve`, phase: ph, schema: EVOLVE_SCHEMA, agentType: 'general-purpose' }
  )

  // --- B. VALIDATE (LLM + structural; writes last_validated marker; sequential) ---
  const validate = await agent(
    `${ENVNOTE}\n\ne2e CYCLE ${c.n} VALIDATE step (this is the LLM-validate the user requires, not just scripts).\n1) STRUCTURAL: run ${PY} ${PSP}/check_consistency.py --root ${E2E} and ${PY} ${PSP}/check_traceability.py --root ${E2E}; collect findings; count error-severity ones.\n2) LLM JUDGMENT on the nodes changed this cycle (${(evolve && evolve.changed_nodes || []).join(', ') || 'see the spec'}): judge INVEST quality, vagueness, and core-value alignment (aligned/weak/off) by READING the prose. These are judgment calls scripts cannot make.\n3) PERSIST the validated marker: build a JSON list of {key, verdict} for your verdicts (key format check|scope|body_hash|lang|dep_hash — read ${PSP}/judgment_cache.py to get exact keying, or use --check to discover keys) and store via ${PY} ${PSP}/judgment_cache.py --root ${E2E} --store-batch <file> --model-id e2e-claude. Storing verdicts is what writes .memory/last_validated.json (judgment_cache.write_last_validated). Confirm the marker exists at ${DP}/.memory/last_validated.json.\nReport structural_error_count, your llm_verdicts, and whether the marker was written.`,
    { label: `c${c.n}:validate`, phase: ph, schema: VALIDATE_SCHEMA, agentType: 'general-purpose' }
  )

  // --- C. CRITIQUE BUNDLE (read-only assemble; sequential) ---
  const bundle = await agent(
    `${ENVNOTE}\n\ne2e CYCLE ${c.n}: assemble the spec-critique bundle. RUN exactly:\n${PY} ${SC}/critique_scan.py --root ${E2E} --scope ${c.scope} --lang vi\nThe script prints the bundle JSON to stdout. WRITE that exact stdout to a file ${E2E}/.critique-bundle-c${c.n}.json (so the lens agents can read it) and return the ABSOLUTE path to that file as plain text (just the path, nothing else). If the JSON has an "error" key, return the full JSON instead.`,
    { label: `c${c.n}:bundle`, phase: ph, agentType: 'general-purpose' }
  )
  const bundlePath = (bundle || '').trim()

  // --- D. LENSES (READ-ONLY, parallel — the only in-cycle fan-out) ---
  const webNote = c.web
    ? 'Web research ENABLED: you MAY use WebSearch/WebFetch to ground competitor/market claims; cite urls in source.'
    : 'Web research DISABLED (--no-web). Lean on the BRD competitors list in the bundle. If competitive grounding is absent, FLAG "thiếu căn cứ cạnh tranh" — do NOT fabricate competitor facts.'
  const lensResults = await parallel(c.lenses.map((lens) => () =>
    agent(
      `${ENVNOTE}\n\ne2e CYCLE ${c.n}. You are the ${lens.toUpperCase()} lens. READ the critique bundle JSON at: ${bundlePath}\nCritique at --level ${c.level}, lang vi, per voice-and-tone.md. ${lens === 'market' ? webNote : ''}\nReturn your findings (each: lens, evidence ID:line, critique, why_it_dies, fix, severity) + a one-line editorial_verdict. Ground every finding in the bundle; no fabrication; do not merely restate a structural validate finding.`,
      { label: `c${c.n}:lens:${lens}`, phase: ph, schema: FINDINGS_SCHEMA, agentType: `spec-critique-${lens}` }
    ).then((r) => ({ lens, ...(r || { findings: [], editorial_verdict: '(lens failed)' }) }))
  ))
  const lenses = lensResults.filter(Boolean)

  // --- E. CONSOLIDATE (real opus consolidator; sequential) ---
  const priorReports = CYCLES.slice(0, c.n - 1).map((p) => `${DP}/critique/${reportName(p)}`)
  const dangerNote = c.level >= 5
    ? `\nDANGER GATE: this is level ${c.level}. In normal use the main agent shows a warning + AskUserQuestion confirm before reaching you. In this e2e the harness has PRE-CONFIRMED the danger gate (dangerConfirmed=true), so render at level ${c.level} as specified. ${c.level === 6 ? 'Level 6 REQUIRES a direct personal roast of the author framed as lazy/careless on THIS spec; HARD FLOOR: every line still cites ID:line + ends in a real fix; attack only effort/care, NEVER identity/protected-characteristics/slurs/threats/self-harm.' : 'Level 5 LIFTS the redline (personal barb permitted, not required); evidence+fix on every line.'}`
    : ''
  const consolidated = await agent(
    `${ENVNOTE}\n\ne2e CYCLE ${c.n}: consolidate the lens findings into ONE markdown critique at --level ${c.level}, lang vi, scope ${c.scope}.\nLENS FINDINGS (JSON): ${JSON.stringify(lenses)}\nPRIOR critique reports (read them with Bash for repeat-offense detection): ${priorReports.length ? priorReports.join(', ') : '(none yet)'}\nApply level-scaled why/fix labels per voice-and-tone.md. Dedup cross-lens, assign final severity, pick Top-3, flag repeat-offenses and DEC-worthy items. Humanize as you draft (Gate 1: no AI-tells, NO em/en dashes, no calqued VN translations).${dangerNote}\nReturn the full markdown document as text.`,
    { label: `c${c.n}:consolidate`, phase: ph, agentType: 'spec-critique-consolidate' }
  )

  // --- F. HUMANIZE (Gate 2; sequential) ---
  const humanized = await agent(
    `${ENVNOTE}\n\ne2e CYCLE ${c.n}: you are the spec-critique-humanize Gate-2 agent. Re-check and rewrite the critique below to strip AI-tells while PRESERVING every finding, its evidence ID:line, its fix, the bite, the level-${c.level} voice, and the structure. Enforce: NO em/en dashes, no banned AI vocabulary, no word-for-word VN translation tells (làm tươi, đường gốc, một cách ...), varied sentence rhythm. Return ONLY the cleaned markdown.\n\nCRITIQUE TO HUMANIZE:\n${consolidated}`,
    { label: `c${c.n}:humanize`, phase: ph, agentType: 'spec-critique-humanize' }
  )

  // --- G. WRITE REPORT + refresh last_critique marker (sequential write) ---
  const fname = reportName(c)
  await agent(
    `${ENVNOTE}\n\ne2e CYCLE ${c.n}: persist the critique report.\n1) Write the markdown below to ${DP}/critique/${fname} (create the critique/ dir if missing). Write it VERBATIM.\n2) Refresh the critique drift marker: RUN ${PY} ${SC}/critique_scan.py --root ${E2E} --snapshot (writes ${DP}/.memory/last_critique.json).\nConfirm both succeeded.\n\nMARKDOWN:\n${humanized}`,
    { label: `c${c.n}:write`, phase: ph, agentType: 'general-purpose' }
  )

  // --- H. AI REVIEW (per-cycle semantic judge, opus) ---
  const card = await agent(
    `${ENVNOTE}\n\ne2e CYCLE ${c.n} AI SEMANTIC REVIEW. You are an independent judge scoring the QUALITY of the critique just written (this is the core of the e2e: is the critique semantically strong?). READ the report at ${DP}/critique/${fname} and the bundle at ${bundlePath}.\n\nCYCLE EXPECTATIONS:\n${c.expect}\n\nSCORE these dimensions honestly:\n- every_finding_has_evidence: does EVERY finding cite a real ID:line present in the spec?\n- every_finding_has_fix: does every finding end in a concrete, actionable fix?\n- level_voice_match: do the rendered why/fix labels + tone match level ${c.level} per voice-and-tone.md?\n- planted_smells_caught / missed: which of the cycle's intended smells did it catch vs miss?\n- fabrication_detected: any finding citing a non-existent ID/line or inventing facts (esp. market w/o web)?\n- validate_echo_detected: any finding that merely restates a structural validate finding with no added why/fix?\n- repeat_offense_expected (${c.n === 6 ? 'true' : 'false'}) vs repeat_offense_fired: did it correctly call out (or correctly stay silent on) repeat offenses?\n- danger_floor_ok: ${c.level >= 5 ? 'level ' + c.level + ' — verify evidence+fix on every line AND no identity/slur/threat/self-harm; for L6 verify a real personal roast is present but stays within the floor' : 'null (level < 5)'}.\n- no_em_dash: confirm the report has zero em/en dashes.\nReturn the scorecard. Be a harsh, fair judge; weak critique must score low.`,
    { label: `c${c.n}:judge`, phase: ph, schema: JUDGE_SCHEMA, agentType: 'general-purpose', model: 'opus' }
  )
  if (card) { scorecards.push(card); log(`Cycle ${c.n} judged: ${card.verdict} (${card.score_0_100}/100)`) }
}

// ---------------------------------------------------------------------------
// Wrap-up: hook smoke-test + aggregate report
// ---------------------------------------------------------------------------
phase('Wrap-up')

const hookTest = await agent(
  `${ENVNOTE}\n\nSMOKE-TEST the advisory Stop hook ${REPO}/.claude/hooks/spec_critique_nudge.py against the e2e product (hooks fire on the main agent's Stop, not inside subagents, so we exercise it directly).\nThe drift nudge fires only when last_validated.json is NEWER than last_critique.json (a validate happened since the last critique) AND drift >= threshold. After 10 cycles the last action was a critique (snapshot), so a fresh nudge should NOT fire. To prove BOTH branches:\n1) SILENT branch: with CLAUDE_PROJECT_DIR=${E2E}, pipe a Stop payload (echo '{"session_id":"e2e","cwd":"${E2E}","stop_hook_active":false}') into ${PY} ${REPO}/.claude/hooks/spec_critique_nudge.py and confirm it exits 0 with NO nudge (because last_critique is newest).\n2) NUDGE branch: touch ${DP}/.memory/last_validated.json so it is newer than last_critique.json, then run the same piped command and confirm it either emits a hookSpecificOutput nudge OR exits 0 silently if drift==0 (note which). Then RESTORE by running ${PY} ${SC}/critique_scan.py --root ${E2E} --snapshot so the markers end consistent.\nReport exactly what each branch printed + exit codes. Do NOT modify the hook source.`,
  { label: 'hook-smoke', phase: 'Wrap-up', agentType: 'general-purpose' }
)

const summary = {
  product: 'Ghép Đôi Việt (e2e dating app)',
  cycles_run: scorecards.length,
  scorecards,
  hook_smoke: hookTest,
  pass: scorecards.filter((s) => s && s.verdict === 'pass').length,
  weak: scorecards.filter((s) => s && s.verdict === 'weak').length,
  fail: scorecards.filter((s) => s && s.verdict === 'fail').length,
  avg_score: scorecards.length ? Math.round(scorecards.reduce((a, s) => a + (s.score_0_100 || 0), 0) / scorecards.length) : 0,
}
log(`E2E done: ${summary.pass} pass / ${summary.weak} weak / ${summary.fail} fail, avg ${summary.avg_score}/100`)
return summary
