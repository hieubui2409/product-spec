#!/usr/bin/env python3
"""Build the Product Spec Harness docs site from a single source of truth.

Source of truth (hand-authored):
  partials/hub.html              — homepage (showcase / overview) content
  partials/guides-index.html     — the guides landing ("Welcome to the Guides")
  partials/<guide>.html          — one detailed guide per file
  partials/_footer.html          — shared footer (links are absolute GitHub URLs)
  assets/showcase.css, assets/showcase.js  — shared styles + behavior
  assets/lib/three.min.js        — vendored Three.js (r128, MIT) — the 3D hero
  artifacts/*                    — REAL captured stdout (never pasted into partials)

Outputs (generated — DO NOT hand-edit):
  index.html                     — homepage (slim header, no sidebar)
  guides/index.html              — guides landing (slim header + left sidebar)
  guides/<guide>.html            — one page per guide (slim header + left sidebar)
  product-spec-showcase.html     — ONE portable file (CSS+JS+three inlined, hash-router)

The homepage uses a plain shell; every guide uses a docs shell with a left sidebar
nav tree grouped by journey (see CATEGORIES) and a client-built right "On this page"
TOC. The portable file wraps every page in a [data-route] panel and the router in
showcase.js switches them on hashchange, showing the sidebar only on guide routes.
Emitted at showcase/ root (NOT dist/ or build/ — those are gitignored AND dropped by
the release safety filter). Stdlib only — run: python3 build.py
"""
import html
import pathlib
import shutil
import re

HERE = pathlib.Path(__file__).resolve().parent
PARTIALS = HERE / "partials"
ASSETS = HERE / "assets"
ARTDIR = HERE / "artifacts"

# Homepage (the showcase / overview) — not a guide; lives at index.html.
#   key, label(en), label(vi), partial, <title>, accent css-var
HOME = ("hub", "Overview", "Tổng quan", "hub.html",
        "Product Spec Harness — Interactive Showcase", "var(--spec)")

# The guides landing — lives at guides/index.html.
GUIDES_INDEX = ("guides", "All guides", "Mục lục", "guides-index.html",
                "Guides — Product Spec Harness", "var(--spec)")

# Guides — each gets the docs sidebar. Same fields as HOME.
# Order follows the sidebar reading order (also drives prev/next via SEQ).
GUIDES = [
    ("quickstart",        "Quick start",      "Bắt đầu",      "quickstart.html",        "Quick start — Product Spec Harness",        "var(--ok)"),
    ("install",           "Install",          "Cài đặt",      "install.html",           "Install — Product Spec Harness",            "var(--ok)"),
    ("journey",           "The loop",         "Vòng đời",     "journey.html",           "The loop — Product Spec Harness",           "var(--gold)"),
    ("product-spec",      "product-spec",     "product-spec", "product-spec.html",      "product-spec — Product Spec Harness",       "var(--spec)"),
    ("critique",          "critique",         "critique",     "critique.html",          "critique — Product Spec Harness",           "var(--crit)"),
    ("release",           "release",          "release",      "release.html",           "release — Product Spec Harness",            "var(--rel)"),
    ("telemetry",         "telemetry",        "telemetry",    "telemetry.html",         "telemetry — Product Spec Harness",          "var(--tel)"),
    ("spec-hierarchy",    "Spec hierarchy",   "Cây spec",     "spec-hierarchy.html",    "Spec hierarchy — Product Spec Harness",     "var(--spec)"),
    ("validation",        "Validation",       "Kiểm tra",     "validation.html",        "Validation — Product Spec Harness",         "var(--spec)"),
    ("decision-register", "Decision register","Sổ quyết định","decision-register.html", "Decision register — Product Spec Harness",  "var(--gold)"),
    ("voice-levels",      "Voice levels",     "Mức giọng",    "voice-levels.html",      "Voice levels — Product Spec Harness",       "var(--crit)"),
    ("determinism",       "Determinism",      "Tất định",     "determinism.html",       "Determinism — Product Spec Harness",        "var(--rel)"),
    ("cheatsheet",        "Cheatsheet",       "Tra cứu nhanh","cheatsheet.html",        "Cheatsheet — Product Spec Harness",         "var(--spec)"),
    ("glossary",          "Glossary",         "Thuật ngữ",    "glossary.html",          "Glossary — Product Spec Harness",           "var(--rel)"),
    ("finder",            "Skill finder",     "Chọn skill",   "finder.html",            "Skill finder — Product Spec Harness",       "var(--gold)"),
    ("the-rig",           "The rig",          "Bộ máy",       "the-rig.html",           "The rig — Product Spec Harness",            "var(--tel)"),
    ("vision",            "Vision",           "Tầm nhìn",     "vision.html",            "Vision — Product Spec Harness",             "var(--tel)"),
]

# Sidebar grouping (5 categories). Each: key, EN label, VI label, EN intro, VI
# intro (shown on the guides landing as a per-category overview), guide keys.
CATEGORIES = [
    ("start",     "Start here",          "Bắt đầu",
     "Install in one command, then watch one product idea become a verified spec.",
     "Cài trong một lệnh, rồi xem một ý tưởng sản phẩm thành spec có kiểm chứng.",
     ["quickstart", "install", "journey"]),
    ("skills",    "The four skills",     "Bốn skill",
     "Define & validate, critique, release the bundle, and observe usage — one skill each.",
     "Định nghĩa & kiểm tra, phản biện, phát hành bộ, và quan sát mức dùng — mỗi việc một skill.",
     ["product-spec", "critique", "release", "telemetry"]),
    ("concepts",  "Concepts",            "Khái niệm",
     "The model underneath: the spec tree, the gates, the registers, the voice.",
     "Mô hình bên dưới: cây spec, các gate, các sổ, và giọng phản biện.",
     ["spec-hierarchy", "validation", "decision-register", "voice-levels", "determinism"]),
    ("reference", "Quick reference",     "Tra cứu nhanh",
     "Look things up fast: every flag, every term — and pick the right skill.",
     "Tra nhanh: mọi cờ, mọi thuật ngữ — và chọn đúng skill.",
     ["cheatsheet", "glossary", "finder"]),
    ("about",     "About",               "Giới thiệu",
     "Inside the machinery, and where the harness is headed.",
     "Bên trong bộ máy, và hướng đi của harness.",
     ["the-rig", "vision"]),
]

# Linear order for prev/next footer nav: homepage → guides landing → guides.
SEQ = ["hub", "guides"] + [g[0] for g in GUIDES]

DESC = ("An interactive, standalone tour of the Product Spec Harness: four Claude Code "
        "skills that define, validate, critique, ship and observe product specs.")
GEN_BANNER = "<!-- GENERATED by build.py — edit showcase/partials/ + assets/, never this file -->"
CHROME = ('<div class="glow g1"></div><div class="glow g2"></div><div class="glow g3"></div>\n'
          '<canvas id="net"></canvas>')


def read(p):
    fp = PARTIALS / p
    return fp.read_text(encoding="utf-8") if fp.exists() else f"<!-- missing partial: {p} -->"


def _art(name):
    return (ARTDIR / name).read_text(encoding="utf-8")


def _pre(name):
    """Real captured stdout, escaped, in a <pre> block."""
    return "<pre>" + html.escape(_art(name), quote=False) + "</pre>"


# placeholder token -> artifact file rendered as a <pre> terminal block
_PRE_TOKENS = {
    "<!--VIZ_TREE-->": "acme-viz-tree.txt",
    "<!--RELEASE_DRYRUN-->": "release-dryrun.txt",
    "<!--TEL_ASCII-->": "telemetry-usage.ascii.txt",
    "<!--TEL_MD-->": "telemetry-usage.md.txt",
    "<!--TEL_MERMAID-->": "telemetry-usage.mermaid.txt",
    "<!--TEL_JSON-->": "telemetry-usage.json.txt",
}


def inject(text, mode, art_rel):
    """Replace artifact placeholders in a partial with the real captured output.
    Artifacts are the single source of truth — never pasted into partials."""
    for tok, fn in _PRE_TOKENS.items():
        if tok in text:
            text = text.replace(tok, _pre(fn))
    if "<!--FINDING_DATA-->" in text:
        raw = _art("acme-critique-finding.json").replace("</", "<\\/")  # no script-breakout
        text = text.replace(
            "<!--FINDING_DATA-->",
            '<script type="application/json" id="finding-data">' + raw + "</script>")
    if "<!--BOARD_EMBED-->" in text:
        if mode == "single":   # truly standalone: inline the board via srcdoc
            sd = _art("acme-viz-board.html").replace("&", "&amp;").replace('"', "&quot;")
            embed = ('<iframe class="board-frame" loading="lazy" '
                     'title="Acme Shop — board view" srcdoc="' + sd + '"></iframe>')
        else:                  # multipage: reference the artifact file
            embed = ('<iframe class="board-frame" loading="lazy" title="Acme Shop — board view" '
                     'src="' + art_rel + 'artifacts/acme-viz-board.html"></iframe>')
        text = text.replace("<!--BOARD_EMBED-->", embed)
    return text


# In-content page links are written mode-agnostically as href="@<key>" and
# rewritten here per target — relative paths for the multipage build, #hash
# routes for the portable build — so the same partial works in both.
_LINK_RE = re.compile(r'href="@([a-z-]+)(#[a-z0-9-]+)?"')


def resolve_links(text, mode, here):
    def _sub(m):
        target, anchor = m.group(1), m.group(2) or ""
        if anchor and mode == "single":
            # one-file build: the section id lives in the same document
            return 'href="%s"' % anchor
        return 'href="%s%s"' % (_href(target, mode, here), anchor)
    return _LINK_RE.sub(_sub, text)


def _art_rel(mode, here):
    """Relative prefix from a rendered page to showcase/artifacts/."""
    if mode == "single":
        return ""            # board inlined via srcdoc; prefix unused
    return "" if here == "home" else "../"


def page_body(partial, mode, here):
    """Read a partial, inject real artifacts, and resolve @<key> page links."""
    return resolve_links(inject(read(partial), mode, _art_rel(mode, here)), mode, here)


def _guide_meta(k):
    return next(g for g in GUIDES if g[0] == k)


def _nav_label(k):
    """(en, vi) label for any nav target key."""
    if k == "hub":
        return (HOME[1], HOME[2])
    if k == "guides":
        return (GUIDES_INDEX[1], GUIDES_INDEX[2])
    g = _guide_meta(k)
    return (g[1], g[2])


def _href(target, mode, here):
    """Resolve a link to a target page key.

    target: 'home'/'hub' | 'guides' | <guide-key>
    mode:   'multi' (real page links) | 'single' (#hash route)
    here:   'home' (page at showcase root) | anything else (page inside guides/)
    """
    if mode == "single":
        if target in ("home", "hub"):
            return "#hub"
        if target == "guides":
            return "#guides"
        return "#" + target
    if here == "home":                       # linking out from index.html
        if target in ("home", "hub"):
            return "index.html"
        if target == "guides":
            return "guides/index.html"
        return "guides/" + target + ".html"
    # linking out from a page inside guides/
    if target in ("home", "hub"):
        return "../index.html"
    if target == "guides":
        return "index.html"
    return target + ".html"


def header_slim(mode, here):
    """Slim top bar: hamburger (mobile, docs only) · brand · Guides · EN/VI."""
    home = _href("home", mode, here)
    guides = _href("guides", mode, here)
    return (
        '<header class="app-header">\n  <div class="app-header-in">\n'
        '    <button class="side-toggle" data-side-toggle aria-label="Toggle guides menu" aria-expanded="false">'
        '<svg viewBox="0 0 24 24" fill="none"><path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round"/></svg></button>\n'
        f'    <a href="{home}" class="brand"><span class="dot"></span>'
        '<span>Product&nbsp;Spec&nbsp;Harness</span></a>\n'
        '    <div class="app-header-right">\n'
        f'      <a href="{guides}" class="btn-guides" data-nav="guides">'
        '<svg viewBox="0 0 24 24" fill="none"><path d="M5 4h9a3 3 0 0 1 3 3v14H7a2 2 0 0 1-2-2V4Z" '
        'stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
        '<path d="M9 9h5M9 13h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
        '<span class="en">Guides</span><span class="vi">Hướng dẫn</span></a>\n'
        '      <div class="langtoggle" role="group" aria-label="language">\n'
        '        <button id="btn-en" class="active" onclick="setLang(\'en\')">EN</button>\n'
        '        <button id="btn-vi" onclick="setLang(\'vi\')">VI</button>\n'
        '      </div>\n    </div>\n  </div>\n</header>'
    )


def sidebar(active, mode, here):
    """Left docs nav tree grouped by journey (CATEGORIES)."""
    out = ['<aside class="docs-side" aria-label="Guides navigation">']
    gi = _href("guides", mode, here)
    gcls = " active" if active == "guides" else ""
    out.append(f'  <a href="{gi}" class="side-link side-top{gcls}" data-nav="guides">'
               '<span class="en">All guides</span><span class="vi">Mục lục</span></a>')
    for _ck, cen, cvi, _ien, _ivi, keys in CATEGORIES:
        out.append(f'  <div class="side-cat"><span class="en">{cen}</span><span class="vi">{cvi}</span></div>')
        for k in keys:
            g = _guide_meta(k)
            href = _href(k, mode, here)
            cls = " active" if active == k else ""
            out.append(f'  <a href="{href}" class="side-link{cls}" data-nav="{k}">'
                       f'<span class="en">{g[1]}</span><span class="vi">{g[2]}</span></a>')
    out.append("</aside>")
    return "\n".join(out)


def crumb(key, mode, here):
    """Breadcrumb: Home › Guides › <current> (Guides hop omitted on the landing)."""
    home = _href("home", mode, here)
    gi = _href("guides", mode, here)
    en, vi = _nav_label(key)
    cur = f'<span class="cur"><span class="en">{en}</span><span class="vi">{vi}</span></span>'
    mid = ""
    if key != "guides":
        mid = (f'<a href="{gi}"><span class="en">Guides</span><span class="vi">Hướng dẫn</span></a> '
               '<span class="sep">›</span> ')
    return (f'<div class="crumb"><a href="{home}"><span class="en">Home</span>'
            f'<span class="vi">Trang chủ</span></a> <span class="sep">›</span> {mid}{cur}</div>')


def skill_nav(key, mode, here):
    """Generated prev · next footer nav. Order lives in SEQ (DRY)."""
    idx = SEQ.index(key)
    ac = "var(--spec)" if key in ("hub", "guides") else _guide_meta(key)[5]
    parts = [f'<div class="skill-nav" style="--ac:{ac}">']
    if idx > 0:
        pk = SEQ[idx - 1]
        pen, pvi = _nav_label(pk)
        parts.append(f'<a class="pv" href="{_href(pk, mode, here)}"><span class="k">← '
                     '<span class="en">Prev</span><span class="vi">Trước</span></span>'
                     f'<span class="v"><span class="en">{pen}</span><span class="vi">{pvi}</span></span></a>')
    else:
        parts.append('<span class="pv" style="flex:1"></span>')
    if idx + 1 < len(SEQ):
        nk = SEQ[idx + 1]
        nen, nvi = _nav_label(nk)
        parts.append(f'<a class="nx" href="{_href(nk, mode, here)}"><span class="k">'
                     '<span class="en">Next</span><span class="vi">Sau</span> →</span>'
                     f'<span class="v"><span class="en">{nen}</span><span class="vi">{nvi}</span></span></a>')
    else:
        parts.append('<span class="nx" style="flex:1"></span>')
    parts.append("</div>")
    return "".join(parts)


# One-line description per guide, shown on the landing-page overview cards.
GUIDE_DESC = {
    "quickstart":        ("Install, then turn one idea into a validated spec tree.",
                          "Cài đặt, rồi biến một ý tưởng thành cây spec đã kiểm tra."),
    "install":           ("One command, shared venv, Python 3.11+ — POSIX or Windows.",
                          "Một lệnh, venv dùng chung, Python 3.11+ — POSIX hoặc Windows."),
    "journey":           ("Watch one product idea flow from vision to observed usage.",
                          "Xem một ý tưởng đi từ tầm nhìn đến mức dùng quan sát được."),
    "product-spec":      ("Define the Vision→BRD→PRD→Epic→Story tree; validate and approve.",
                          "Dựng cây Vision→BRD→PRD→Epic→Story; kiểm tra và duyệt."),
    "critique":          ("Four lenses, nine voice levels — sharp feedback, never silent edits.",
                          "Bốn lăng kính, chín mức giọng — góp ý sắc, không sửa lén."),
    "release":           ("Pack the bundle deterministically; the safety filter drops secrets.",
                          "Đóng gói bộ một cách tất định; bộ lọc an toàn loại bí mật."),
    "telemetry":         ("Read who used what, in plain Vietnamese, four output formats.",
                          "Đọc ai dùng gì, bằng tiếng Việt rõ, bốn định dạng."),
    "spec-hierarchy":    ("The five levels and their IDs — the spine of every spec.",
                          "Năm cấp và mã ID — xương sống của mọi spec."),
    "validation":        ("Scripts judge structure; the LLM judges prose; the PO approves.",
                          "Script soi cấu trúc; LLM soi văn; PO mới được duyệt."),
    "decision-register": ("DEC-n: how a contradiction becomes a recorded, settled ruling.",
                          "DEC-n: mâu thuẫn thành một phán quyết được ghi và chốt."),
    "voice-levels":      ("Levels 1–9 and the universal-harm floor under all of them.",
                          "Mức 1–9 và sàn cấm-gây-hại nằm dưới tất cả."),
    "determinism":       ("Same inputs, same bytes — why scripts do the structural work.",
                          "Cùng đầu vào, cùng byte — vì sao script làm phần cấu trúc."),
    "cheatsheet":        ("Every flag of every skill, in tables you can scan.",
                          "Mọi cờ của mọi skill, trong bảng tra nhanh."),
    "glossary":          ("The canonical terms — with the wording the harness forbids.",
                          "Thuật ngữ chuẩn — kèm cách nói mà harness cấm."),
    "finder":            ("Answer a few questions, get the exact skill to run.",
                          "Trả lời vài câu, ra đúng skill cần chạy."),
    "the-rig":           ("Skills, scripts, schemas, hooks, and the gates that say no.",
                          "Skill, script, schema, hook, và các gate biết nói không."),
    "vision":            ("Where the harness is going and the principles that steer it.",
                          "Harness đi về đâu và nguyên tắc dẫn lối."),
}


def category_overview(mode, here):
    """Per-category overview for the guides landing: intro + cards, from CATEGORIES."""
    out = []
    for _ck, cen, cvi, ien, ivi, keys in CATEGORIES:
        out.append('<section class="cat-ov reveal">')
        out.append(f'  <h2 class="sectitle"><span class="en">{cen}</span><span class="vi">{cvi}</span></h2>')
        out.append(f'  <p class="lead cat-intro"><span class="en">{ien}</span><span class="vi">{ivi}</span></p>')
        out.append('  <div class="cards grid-2">')
        for k in keys:
            g = _guide_meta(k)
            href = _href(k, mode, here)
            den, dvi = GUIDE_DESC.get(k, ("", ""))
            out.append(f'    <a class="card" href="{href}" style="--ac:{g[5]}"><h3><span class="pin"></span>'
                       f'<span class="en">{g[1]}</span><span class="vi">{g[2]}</span></h3>'
                       f'<p><span class="en">{den}</span><span class="vi">{dvi}</span></p></a>')
        out.append('  </div>')
        out.append('</section>')
    return "\n".join(out)


def gi_page_body(mode, here):
    """Guides landing body: hand-authored welcome + generated category overview."""
    body = page_body(GUIDES_INDEX[3], mode, here)
    return body.replace("<!--CATEGORY_OVERVIEW-->", category_overview(mode, here))


def head(title, head_inject):
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        '<meta charset="UTF-8" />\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
        # Declared before the stylesheet loads so the browser paints a dark canvas during
        # navigation — no white flash between pages.
        '<meta name="color-scheme" content="dark" />\n'
        '<meta name="theme-color" content="#070b16" />\n'
        f"<title>{title}</title>\n"
        f'<meta name="description" content="{DESC}" />\n'
        f"{head_inject}\n</head>\n"
    )


def shell(title, head_inject, view, header_html, sidebar_html, body_html,
          footer, script_inject, portable=False):
    """Assemble a page. view='home' → plain; view='guide' or portable → docs layout."""
    if portable or view == "guide":
        side = sidebar_html or ""
        # Right "On this page" TOC is built client-side (showcase.js) from the
        # active content's <h2 id> headings, so it works for both the multipage
        # guides and the portable router's active route.
        toc = '<nav class="toc" data-toc aria-label="On this page"></nav>'
        layout = ('<div class="scrim" data-scrim></div>\n'
                  '<div class="docs-layout">\n' + side + '\n'
                  '<main class="docs-main">\n' + body_html + '\n</main>\n'
                  + toc + '\n</div>')
    else:
        layout = body_html
    return (
        head(title, head_inject)
        + f'<body class="lang-en view-{view}">\n'
        # Restore the saved language before the content below paints — otherwise every
        # navigation flashes English first, then swaps to the stored Vietnamese.
        + '<script>try{if(localStorage.getItem(\'psh-lang\')===\'vi\')'
          'document.body.classList.replace(\'lang-en\',\'lang-vi\');}catch(e){}</script>\n'
        + GEN_BANNER + "\n"
        + CHROME + "\n"
        + header_html + "\n"
        + layout + "\n"
        + footer + "\n"
        + script_inject + "\n"
        + "</body>\n</html>\n"
    )


def build():
    css = (ASSETS / "showcase.css").read_text(encoding="utf-8")
    js = (ASSETS / "showcase.js").read_text(encoding="utf-8")
    # Vendored Three.js (r128, MIT) — drives the 3D hero background. Multipage links
    # the local copy; the portable file inlines it so it stays self-contained + offline.
    lib = (ASSETS / "lib" / "three.min.js").read_text(encoding="utf-8")
    footer_tpl = read("_footer.html")
    written = []

    guides_dir = HERE / "guides"
    guides_dir.mkdir(exist_ok=True)
    old_skills = HERE / "skills"          # replaced by guides/
    if old_skills.exists():
        shutil.rmtree(old_skills)

    # ---------- multipage homepage (index.html) ----------
    link = '<link rel="stylesheet" href="assets/showcase.css" />'
    script = '<script src="assets/lib/three.min.js"></script>\n<script src="assets/showcase.js"></script>'
    home_body = (page_body("hub.html", "multi", "home")
                 + '\n<div class="wrap">' + skill_nav("hub", "multi", "home") + "</div>")
    out = shell(HOME[4], link, "home", header_slim("multi", "home"), None,
                home_body, footer_tpl, script)
    (HERE / "index.html").write_text(out, encoding="utf-8")
    written.append("index.html")

    # ---------- multipage guides (guides/*.html) ----------
    link_g = '<link rel="stylesheet" href="../assets/showcase.css" />'
    script_g = '<script src="../assets/lib/three.min.js"></script>\n<script src="../assets/showcase.js"></script>'

    gi_body = (crumb("guides", "multi", "guides") + "\n" + gi_page_body("multi", "guides")
               + '\n<div class="wrap">' + skill_nav("guides", "multi", "guides") + "</div>")
    out = shell(GUIDES_INDEX[4], link_g, "guide", header_slim("multi", "guides"),
                sidebar("guides", "multi", "guides"), gi_body, footer_tpl, script_g)
    (guides_dir / "index.html").write_text(out, encoding="utf-8")
    written.append("guides/index.html")

    for key, _en, _vi, pf, title, _ac in GUIDES:
        body = (crumb(key, "multi", key) + "\n" + page_body(pf, "multi", key)
                + '\n<div class="wrap">' + skill_nav(key, "multi", key) + "</div>")
        out = shell(title, link_g, "guide", header_slim("multi", key),
                    sidebar(key, "multi", key), body, footer_tpl, script_g)
        (guides_dir / (key + ".html")).write_text(out, encoding="utf-8")
        written.append(f"guides/{key}.html")

    # ---------- portable single file ----------
    style_inline = "<style>\n" + css + "\n</style>"
    script_inline = "<script>\n" + lib + "\n</script>\n<script>\n" + js + "\n</script>"
    panels = []
    for key in SEQ:
        if key == "hub":
            inner = page_body(HOME[3], "single", "")
        elif key == "guides":
            inner = gi_page_body("single", "")
        else:
            inner = page_body(_guide_meta(key)[3], "single", "")
        body = inner + '\n<div class="wrap">' + skill_nav(key, "single", "") + "</div>"
        panels.append(f'<div class="route" data-route="{key}">\n{body}\n</div>')
    main_single = "\n".join(panels)
    out = shell(HOME[4], style_inline, "home", header_slim("single", ""),
                sidebar("hub", "single", ""), main_single, footer_tpl,
                script_inline, portable=True)
    (HERE / "product-spec-showcase.html").write_text(out, encoding="utf-8")
    written.append("product-spec-showcase.html")

    return written


if __name__ == "__main__":
    for w in build():
        print("wrote", w)
