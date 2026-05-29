---
phase: 2
title: "Vendor and HTML Body Render"
status: done
priority: P1
effort: "0.75d"
dependencies: []
---

# Phase 2: Vendor marked+DOMPurify + shared HTML body-render infra

## Overview

The shared HTML rendering substrate every body-bearing output (F1 html, board, explorer) reuses, plus a **prerequisite fix** to the token engine. **Re-founded after red-team C2/H3/L12/M7.** Independent of Phase 1.

## Requirements

- **C2 — single-pass token engine (PREREQUISITE, do first).** `render_html.assemble()` currently does `for k,v in values.items(): shell = shell.replace("{{"+k+"}}", v)` (`render_html.py:165-166`) — multi-pass, re-scans inserted content; `_escape()` does not escape `{`/`}`. Proven sink: a value of `"{{mermaid_js}}"` injects the 2.5 MB payload; a body containing `{{footer_note}}` bleeds the footer. Replace with **single-pass**: `re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), shell)` (inserted values never re-scanned). This also fixes a pre-existing latent bug for the 9 legacy views.
- **Vendor** — `scripts/install-vendor-markdown.sh` mirrors `install-vendor-mermaid.sh` (pin **marked 18.0.4** + **DOMPurify 3.4.7**, SHA256-verify, idempotent, offline after; escape `</script>`→`<\/script>` in the payload). **Libs are COMMITTED** to `assets/vendor/` — `.gitignore:118-120` un-ignores `assets/**` and `assets/vendor/mermaid.min.js` is already tracked; the two new libs (~62 KB total) ship the same way (red-team M7).
- **Body render** — `render_html._load_vendored_markdown_libs()` + a client chokepoint: `el.innerHTML = DOMPurify.sanitize(marked.parse(md))`. Bodies travel as an **embedded JSON** blob: `json.dumps(..., ensure_ascii=False)` then a literal `.replace("</", "<\\/")` post-step (json.dumps does NOT escape `/`). Never inject body HTML server-side.
- **L12 — fail closed, no CDN for the sanitizer.** If the vendored marked/DOMPurify are missing, body views render bodies as server-side `_escape()` plain text + a visible "run install.sh" banner — **never** load a sanitizer from CDN (offline + supply-chain guarantee; contradicts the earlier mermaid-mirror wording). Mermaid's CDN fallback for legacy graph views may remain (not a security control).
- **H3 — attribute-context sinks.** Board/explorer place free-text (group labels, persona names, titles) into HTML attributes (`data-status`, `aria-label`, `id`, anchor `href="#<ID>"`). Route every attribute value through `_escape()` (handles quotes); `href` through an allowlist (reject `javascript:`). The embedded-JSON body path + the attribute path are the two enumerated sinks.
- **H4 — symmetric payload gating.** Body views (export/board/explorer) omit the Mermaid payload; legacy graph views (`tree…delta`) omit the marked/DOMPurify payload (they render no bodies). State both rules; keep `mermaid_js` gate at `render_html.py:153`.
- **Design system** — partial (theme toggle sun/moon+localStorage, palette `--green/red/amber/sage/teal/plum`+`-dim`, typography, `.ve-card` `--elevated/--recessed/--hero`, `@media print`, stagger keyframes, `min-width:0` guard). **Single source for ALL product-spec HTML** (export/board/explorer + legacy shell retrofit in Phase 6).

## Architecture

Single client-side sanitize chokepoint. Server emits inert data via the **single-pass-substituted** shell + attribute-escaped values. One design-system partial (`render_html.py` constant or `assets/templates/_viewer-head.html`).

## Related Code Files

- Modify: `scripts/render_html.py` (single-pass `assemble()` fix ~L165; `_load_vendored_markdown_libs()` + body helper before `assemble()` ~L122; token expansion + attribute escaping in `assemble()` ~L155; fail-closed branch)
- Create: `scripts/install-vendor-markdown.sh`
- Create (produced by the script, **COMMITTED** like mermaid.min.js): `assets/vendor/marked.min.js`, `assets/vendor/purify.min.js`
- Modify: `install.sh` (add vendor step **after** the mermaid vendor call ~L80-84, after the closing `fi`)
- Create: `scripts/tests/test_html_sanitize.py`

## Implementation Steps

1. Replace `assemble()` substitution with single-pass `re.sub`; add a `{{token}}` round-trip test (a title/body containing `{{mermaid_js}}` + `{{footer_note}}` must survive verbatim, no injection/bleed).
2. Write `install-vendor-markdown.sh` (URLs `cdn.jsdelivr.net/npm/marked@18.0.4/lib/marked.umd.js`, `…/dompurify@3.4.7/dist/purify.min.js`; sha-pin; `</script>` escape); run it; commit the two libs.
3. Add render_html body helpers + embedded-JSON channel + fail-closed path + attribute escaping + design-system partial.
4. XSS tests: **body** payloads (`<script>`, `<img onerror>`, `[x](javascript:)`), **attribute** payloads (group/persona label = `"><script>…`), `</script>` in body JSON, fail-closed (libs absent → escaped text + banner, no CDN).
5. Run pytest (existing 92 stay green).

## Success Criteria

- [ ] Single-pass substitution: `{{token}}` in spec content round-trips verbatim; no payload injection / footer bleed.
- [ ] marked+DOMPurify vendored + SHA-verified + **committed** + inlined; works offline.
- [ ] Sanitize neutralizes body **and** attribute payloads; `href` allowlist blocks `javascript:`.
- [ ] Fail-closed when libs missing (escaped text + banner, never CDN sanitizer).
- [ ] Gating holds (body views: no Mermaid; legacy views: no marked/DOMPurify). 92 tests green.

## Risk Assessment

- **C2 latent bug** also affects the 9 legacy views → single-pass fix benefits them too; round-trip test locks it.
- **Order inversion** (purify before marked) → test locks `marked.parse`→`DOMPurify.sanitize`.
- **`</script>` in lib + JSON** → escape on vendoring + on JSON embed.
- **L12 CDN sanitizer** = security regression → fail closed, no CDN.
- **Committed +62 KB** → packed by claude-pack (sorted walk, deterministic) — acceptable; noted in Phase 7.
