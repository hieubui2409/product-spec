# Showcase Guide Authoring Conventions

You are authoring ONE or more guide partials for the Product Spec Harness showcase
(`showcase/partials/<key>.html`). These are hand-written HTML fragments; a Python build
(`showcase/build.py`) wraps each in the page shell (header, left sidebar, right TOC, footer)
and emits multipage + portable builds. **Do NOT** write `<html>/<head>/<body>/<header>/<footer>/<aside>`
or `<script>/<style>` — only the page CONTENT. Output is plain HTML, no markdown.

## Read these first (concrete templates — match their structure & density)
- `../sdlc-harness/showcase/partials/quickstart.html` — start-here structure (steps, faq, cmdline+term)
- `../sdlc-harness/showcase/partials/glossary.html` — `.modetable.gloss` 4-col term table
- `../sdlc-harness/showcase/partials/cheatsheet.html` — flag tables + `.cs-more` disclosure
- `../sdlc-harness/showcase/partials/finder.html` — decision/tie-break list
- `../sdlc-harness/showcase/partials/vision.html` and `harness.html` — about-page structure
- `showcase/partials/product-spec.html` — THE voice + class usage for THIS repo (the gold reference)
- `showcase/partials/_footer.html`, `showcase/partials/hub.html` — house style

## Source of truth for FACTS (read, never invent)
- `README.md` — the pitch, the four skills, install commands, philosophy
- `.claude/skills/product-spec/SKILL.md` — product-spec flags, spec hierarchy, validate/approve, DEC
- `.claude/skills/product-spec-critique/SKILL.md` — 4 lenses, 9 voice levels, universal-harm floor
- `.claude/skills/release/SKILL.md` — pack/lifecycle flags, determinism, safety filter
- `.claude/skills/telemetry/SKILL.md` — lenses, formats, read-only honesty
- `CLAUDE.md` (project root) + `.claude/rules/*` — GATEs, Five Operating Principles, anti-rationalization
Never state a flag/term/number you did not verify in these files. If unsure, omit it.

## Bilingual rule (MANDATORY)
Every human-visible string is a pair of sibling spans:
`<span class="en">English</span><span class="vi">Tiếng Việt</span>`
CSS hides the inactive language. NEVER leave a visible string single-language. Vietnamese must be
natural product/PO language (not machine-translated word salad). Code/flags/IDs stay literal (not translated).

## Required page skeleton
Wrap content in `<section>` blocks, each with an inner `<div class="wrap reveal">`:

```
<section id="<key>-intro">
  <div class="wrap reveal">
    <div class="skill-head" style="--ac:<ACCENT>">
      <div class="badge">…inline SVG or emoji…</div>
      <div class="ttl">
        <div class="who"><span class="en">…tagline…</span><span class="vi">…</span></div>
        <h2 style="margin:0"><span class="en">…Page Title…</span><span class="vi">…</span></h2>
      </div>
    </div>
    <p class="lead"><span class="en">…1–2 sentence intro…</span><span class="vi">…</span></p>
  </div>
</section>

<section id="<key>-…">
  <div class="wrap reveal">
    <div class="eyebrow"><span class="en">SECTION KICKER</span><span class="vi">…</span></div>
    <h2 class="sectitle" id="<stable-kebab-id>"><span class="en">Section Heading</span><span class="vi">…</span></h2>
    …content…
  </div>
</section>
```

**TOC requirement:** every major section heading is `<h2 class="sectitle" id="…">…</h2>` with a UNIQUE,
stable, kebab-case `id`. The right-rail "On this page" TOC is built from `h2[id]`. Aim for 3–6 such
sections per guide. The first `.skill-head` h2 should NOT have an id (it is the page title, not a TOC entry).

## Cross-links (mode-agnostic) — use `@key`, never relative paths
Write in-content page links as `href="@<key>"` (optionally `href="@<key>#section-id"`). The build rewrites
them per output mode. Valid keys: `hub`, `guides`, and the guide keys:
`quickstart install journey product-spec critique release telemetry spec-hierarchy validation
decision-register voice-levels determinism cheatsheet glossary finder the-rig vision`.
External links (GitHub etc.) use full `https://` URLs with `target="_blank" rel="noopener"`.

## Class vocabulary (use these — they are all styled)
- Layout: `section`, `.wrap`, `.reveal` (fade-in), `.eyebrow` (kicker), `.lead`, `.muted`, `.faint`
- Headings: `.sectitle` (h2), `.skill-head`/`.badge`/`.ttl`/`.who`, `.divider`
- Cards: `.cards.grid-2` / `.cards.grid-3`, `.card` (h3 with `<span class="pin"></span>` bullet); `a.card` for clickable
- Callouts: `.callout` (with `.ci` icon span), `.honest` (with `.h` header + ul), `.floor` (dashed warning)
- Steps: `.steps` > `.step` (auto-numbered, h4 + p), `.cmdline` (with `<code>`), `.term`>`.tbar`(3 `<i>` dots)+`.tcmd`+`<pre>`
- Tables: `.modetable` (th/td); glossary uses `.modetable.gloss` (4 cols: Term | Definition | Forbidden wording | Backing); `.x` for forbidden, `.keepish`/`.outish` for in/out
- FAQ: `.faq` > `<details><summary>…</summary><div class="fa">…</div></details>` (native, no JS)
- Disclosure (cheatsheet extras): `<details class="cs-more"><summary>…</summary><table class="modetable">…</table></details>`
- Chips/flags: `.chipgroup`>`.chips`>`.chip` (use `<span class="x">` for the value part of `--flag x`)
- Tree (spec hierarchy): `.tree` > `.tnode.lvl-v|lvl-b|lvl-p|lvl-e|lvl-s` (`.tg` tag, `.tt` title, `.td` desc, `.cnt`), `.tconn` connectors
- Verdict triple (DEC): `.tri` > `span.keep` / `span.change` / `span.hybrid`; `.gate` box (`b` = gold)
- Lenses (critique): `.lenses` > `.lens.p|t|m|c` (`.lic` icon, h4, `.fw` frameworks)
- Voice dial readout chrome exists but the INTERACTIVE dial is only on the critique skill page — for voice-levels guide use a `.modetable` of levels + a `.floor` for the universal-harm floor instead
- Finder: `.tielist` (ol/ul) for tie-break rules; `.ttag.product|quality|ops` pills
- CTA: `.cta-row` > `a.btn-cta.primary` / `a.btn-cta.ghost`
- Stats: `.stats` > `.stat` (`.n` with `data-count="N"` animates, `.l` label)

## Accent per guide (set on `.skill-head style="--ac:…"` and key chips)
quickstart `var(--ok)` · install `var(--ok)` · journey `var(--gold)` · spec-hierarchy `var(--spec)` ·
validation `var(--spec)` · decision-register `var(--gold)` · voice-levels `var(--crit)` · determinism `var(--rel)` ·
cheatsheet `var(--spec)` · glossary `var(--rel)` · finder `var(--gold)` · the-rig `var(--tel)` · vision `var(--tel)`

## Artifact tokens (real captured stdout — use where genuinely relevant; do NOT paste fake terminal text)
Place the bare comment token on its own line inside a `.term` block; the build replaces it with the real `<pre>`:
`<!--VIZ_TREE-->` (acme-shop spec tree) · `<!--RELEASE_DRYRUN-->` (release pack dry-run) ·
`<!--TEL_ASCII--> / <!--TEL_MD--> / <!--TEL_MERMAID--> / <!--TEL_JSON-->` (telemetry usage lens).
If a guide needs a terminal block but no token fits, write a SHORT illustrative `<pre>` and DO NOT imply it
is captured output (no green "REAL" tag). Reuse, do not duplicate, the skill pages' deep examples — link to them with `@key`.

## Quality bar
- Match the density and polish of the sibling guides — substantial, not stubs. 4–7 sections each.
- Accurate to the source files. Concise. No marketing fluff that the facts don't support.
- Valid HTML (balanced tags, quoted attrs). No `<script>`/`<style>`/`<h1>` (h1 is the homepage's).
- End each guide naturally (the build appends prev/next nav automatically — do not add it yourself).
