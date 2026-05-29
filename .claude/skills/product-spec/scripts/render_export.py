#!/usr/bin/env python3
"""
render_export — F1 read-once Export. Assemble a spec slice (Phase-1 digest) into
ONE self-contained doc: deterministic markdown, or a linear print-ready HTML via
the Phase-2 body-render substrate.

CLI:
    render_export.py --root <dir> --export <all|ID|list>
        [--layers vision,brd,prd,epic,story] [--depth context|full|brief]
        [--compact-mode struct|llm] [--format md|html] [--lang en|vi]

Output: docs/product/exports/<stem>-<ts>-<hash8>.<md|html>. The doc body is
deterministic and the content HASH is stable (computed over the timestamp-free
body); the `<ts>` segment is the wall-clock stamp, so each invocation writes a
fresh file — re-exporting unchanged content accumulates one timestamped file per
run (the hash is the dedup key, not the filename). Script-vs-LLM split:
`--compact-mode llm` emits the full body wrapped in `<!-- COMPACT:<id> -->`
markers for the LLM to summarize — the script NEVER summarizes.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from encoding_utils import configure_utf8_console
from spec_graph import build_graph_with_artifacts, _now
from assemble_digest import build_digest, compact_fields
from i18n_labels import label
import render_html

configure_utf8_console()

SKILL_ROOT = Path(__file__).resolve().parent.parent
EXPORT_SHELL = SKILL_ROOT / "assets" / "templates" / "export-shell.html"


def _anchor(node_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(node_id).lower()).strip("-")


def _yaml_scalar(s: Any) -> str:
    """Emit a free-text value as a YAML double-quoted scalar. A raw `product: Acme:
    The Shop` is invalid YAML; `product: Acme #1` silently truncates at the `#`; a
    newline in the value injects a literal `\\n---\\n` that makes _strip_frontmatter
    cut early and eat real frontmatter into the HTML body. Quoting + escaping `\\` `"`
    and newlines neutralizes all three (double-quoted YAML supports the escapes)."""
    out = str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\r", "").replace("\n", "\\n")
    return f'"{out}"'


def _heading(entry: Dict[str, Any]) -> str:
    title = entry.get("title") or ""
    return f"{entry['id']} — {title}" if title else str(entry["id"])


def _ac_item(a: Any) -> str:
    """Render one acceptance-criteria item as a readable bullet. AC items are
    expected to be strings, but a PO may write a YAML mapping (`- {given: …,
    then: …}`); stringify that as `key: value` pairs rather than leaking a raw
    Python dict repr (`{'given': 'A'}`) into the doc."""
    if isinstance(a, dict):
        return " · ".join(f"{k}: {v}" for k, v in a.items())
    return str(a)


def _ac_block(entry: Dict[str, Any]) -> str:
    """The explicit acceptance-criteria bullet list for a story, or "" when none."""
    if entry["type"] == "story" and isinstance(entry.get("ac"), list) and entry["ac"]:
        return "**Acceptance criteria:**\n" + "\n".join(f"- {_ac_item(a)}" for a in entry["ac"])
    return ""


def _content_with_ac(entry: Dict[str, Any], ac: str) -> str:
    """The entry's raw body (or the struct skeleton when there is genuinely no body
    AND no AC), with the explicit AC list appended once. Body-FIRST so a bodyless
    story's struct skeleton — which already lists `acceptance_criteria: N item(s)` —
    never doubles the explicit AC list. Shared by the full and llm branches so the
    two cannot diverge (the llm branch previously fell back to the struct skeleton
    AND appended the explicit list, doubling the AC for a bodyless story)."""
    body = (entry.get("body") or "").strip()
    out = body if body else ("" if ac else _struct_lines(entry))
    if ac:
        out = (out + "\n\n" + ac) if out else ac
    return out


def _section_body(entry: Dict[str, Any], compact_mode: str) -> str:
    """Render one entry's content per its verbosity + compact-mode."""
    ac = _ac_block(entry)
    if entry["verbosity"] == "full":
        return _content_with_ac(entry, ac)
    # struct verbosity
    if compact_mode == "llm":
        # Full body (+ the story's AC inside the region so the step-2 LLM sees the
        # artifact's primary content) marked for in-place summarization. Defensive:
        # neutralize an inner '-->' with U+200B so it can't close the HTML-comment
        # COMPACT region for a comment-aware consumer (the documented LLM consumer
        # reads the named /COMPACT:<id> sentinel and is unaffected; --format html is
        # hard-rejected).
        inner = _content_with_ac(entry, ac).replace("-->", "--​>")
        return f"<!-- COMPACT:{entry['id']} -->\n{inner}\n<!-- /COMPACT:{entry['id']} -->"
    return _struct_lines(entry)


def _struct_lines(entry: Dict[str, Any]) -> str:
    fields = compact_fields(entry)
    return "\n".join(f"- **{k}**: {v}" for k, v in fields) or "_(no structured fields)_"


def render_markdown_doc(
    digest: List[Dict[str, Any]],
    product_name: str,
    select: str,
    depth: str,
    layers_label: str,
    compact_mode: str,
    generated_at: str,
    lang: str = "en",
) -> str:
    warnings = [e for e in digest if e.get("role") == "warning"]
    sections = [e for e in digest if e.get("type") != "_warning"]

    lines: List[str] = []
    lines.append("---")
    # Free-text / user-controlled values are YAML-quoted so a ':' '#' or newline
    # cannot break or truncate the frontmatter (depth/compact_mode are enum choices
    # and generated_at is an ISO stamp, so they need no quoting).
    lines.append(f"product: {_yaml_scalar(product_name)}")
    lines.append(f"export: {_yaml_scalar(select)}")
    lines.append(f"depth: {depth}")
    lines.append(f"layers: {_yaml_scalar(layers_label)}")
    lines.append(f"compact_mode: {compact_mode}")
    if generated_at:
        lines.append(f"generated_at: {generated_at}")
    lines.append("---")
    lines.append("")
    # Body H1 localizes via the same i18n key as the HTML chrome title (so .md and
    # .html agree under --lang vi); CR/LF in the name collapse to a space so a
    # multi-line PRODUCT name can't garble the heading into a setext rule.
    heading_name = product_name.replace("\r", " ").replace("\n", " ")
    lines.append(f"# {label('export', lang)} — {heading_name}")
    lines.append("")
    lines.append(f"> Selection: `{select}` · Depth: `{depth}` · Layers: `{layers_label}`")
    lines.append("")
    for w in warnings:
        lines.append(f"> ⚠ {w.get('detail', 'layers excluded the selected root context')}")
        lines.append("")

    lines.append("## Contents")
    for e in sections:
        lines.append(f"- [{_heading(e)}](#{_anchor(e['id'])})")
    lines.append("")

    for e in sections:
        lines.append("---")
        lines.append("")
        lines.append(f'<a id="{_anchor(e["id"])}"></a>')
        lines.append(f"## {_heading(e)}")
        lines.append("")
        lines.append(_section_body(e, compact_mode))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _strip_frontmatter(md: str) -> str:
    """Drop a leading `---\\n … \\n---` YAML block. The provenance frontmatter is a
    .md affordance (the HTML shell already shows the same metadata in `.ps-meta`);
    `marked` does not strip it, so leaving it in renders a stray `<hr>` + a garbled
    setext `<h2>` at the top of every HTML export."""
    if md.startswith("---\n"):
        end = md.find("\n---\n", 4)
        if end != -1:
            return md[end + len("\n---\n"):].lstrip("\n")
    return md


def render_html_doc(markdown_doc: str, graph: Dict[str, Any], generated_at: str, lang: str = "en") -> str:
    shell = EXPORT_SHELL.read_text(encoding="utf-8")
    pname = render_html.product_name(graph)
    # Body channel: strip the .md frontmatter (HTML shows it in .ps-meta instead).
    values = render_html.body_render_values({"doc": _strip_frontmatter(markdown_doc)})
    # Reuse the shared chrome preamble; override only generated_at with the
    # hash-stable stamp (chrome_values would call a fresh _now()). Localize the
    # chrome heading via i18n (board/explorer localize their view-name too).
    values.update(render_html.chrome_values(graph, lang, f"{label('export', lang)} — {pname}"))
    values["generated_at"] = generated_at
    return render_html.substitute(shell, values)


def _sanitize_id(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(s)).strip("_") or "export"


def _stem(select: str) -> str:
    if select == "all":
        return "all"
    ids = [s.strip() for s in select.split(",") if s.strip()]
    if len(ids) == 1:
        return _sanitize_id(ids[0])
    joined = "_".join(sorted(_sanitize_id(i) for i in ids))
    if len(joined) <= 48:
        return joined
    tail = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:8]
    return f"{joined[:40]}-{tail}"


def write_export(root: Path, select: str, layers, depth: str, compact_mode: str, fmt: str, lang: str) -> Path:
    # `--compact-mode llm` is a markdown-only contract: it emits <!-- COMPACT -->
    # markers for a step-2 LLM rewrite of the .md on disk. In html those markers
    # are stripped by DOMPurify and no .md is written, so the combo is meaningless
    # — reject it rather than emit a silently-degraded file (CLAUDE.md: no silent
    # failure). The two valid pairings are md+llm and html+struct.
    if compact_mode == "llm" and fmt == "html":
        raise ValueError(
            "--compact-mode llm is incompatible with --format html: DOMPurify strips "
            "the <!-- COMPACT --> markers and no .md artifact is written for the "
            "step-2 LLM rewrite. Use '--format md --compact-mode llm', or "
            "'--format html --compact-mode struct'."
        )

    graph, artifacts = build_graph_with_artifacts(root)
    digest = build_digest(graph, artifacts, select=select, layers=layers, depth=depth)
    product_name = render_html.product_name(graph)
    layers_label = ",".join(layers) if layers else "all"

    # Render the markdown doc ONCE with the real timestamp, then hash over the
    # doc with the volatile generated_at line stripped → identical content yields
    # a stable, collision-free filename regardless of when it was generated.
    generated_at = _now()
    md_doc = render_markdown_doc(digest, product_name, select, depth, layers_label, compact_mode, generated_at, lang)
    stable = md_doc.replace(f"generated_at: {generated_at}\n", "", 1)
    content_hash = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:8]

    out_dir = root / "docs" / "product" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    ext = "html" if fmt == "html" else "md"
    target = out_dir / f"{_stem(select)}-{render_html.file_timestamp()}-{content_hash}.{ext}"
    payload = render_html_doc(md_doc, graph, generated_at, lang) if fmt == "html" else md_doc
    target.write_text(payload, encoding="utf-8")
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--export", dest="select", required=True, help="all | <ID> | comma-list")
    ap.add_argument("--layers", default=None, help="comma list subset of vision,brd,prd,epic,story")
    ap.add_argument("--depth", default="context", choices=["context", "full", "brief"])
    ap.add_argument("--compact-mode", dest="compact_mode", default="struct", choices=["struct", "llm"])
    ap.add_argument("--format", default="md", choices=["md", "html"])
    ap.add_argument("--lang", default="en", choices=["en", "vi"])
    args = ap.parse_args()

    layers = [s.strip() for s in args.layers.split(",") if s.strip()] if args.layers else None
    root = Path(args.root).resolve()
    try:
        out = write_export(root, args.select, layers, args.depth, args.compact_mode, args.format, args.lang)
    except ValueError as exc:
        # Unresolved/empty selection or an incompatible flag combo. Surface the
        # message to stderr and exit non-zero instead of writing a degraded doc.
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps({"written": str(out.relative_to(root)) if out.is_relative_to(root) else str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
