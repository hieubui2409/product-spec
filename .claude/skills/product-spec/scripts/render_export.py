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
deterministic; the content hash is computed over the timestamp-free body so
identical content yields a stable filename (collision-free snapshot pattern).
Script-vs-LLM split: `--compact-mode llm` emits the full body wrapped in
`<!-- COMPACT:<id> -->` markers for the LLM to summarize — the script NEVER
summarizes.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from encoding_utils import configure_utf8_console
from spec_graph import build_graph_with_artifacts, _now
from assemble_digest import build_digest, compact_fields
import render_html

configure_utf8_console()

SKILL_ROOT = Path(__file__).resolve().parent.parent
EXPORT_SHELL = SKILL_ROOT / "assets" / "templates" / "export-shell.html"


def _anchor(node_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(node_id).lower()).strip("-")


def _heading(entry: Dict[str, Any]) -> str:
    title = entry.get("title") or ""
    return f"{entry['id']} — {title}" if title else str(entry["id"])


def _body_or_struct(entry: Dict[str, Any]) -> str:
    """The entry's narrative body, or a struct-field skeleton when it has none."""
    return (entry.get("body") or "").strip() or _struct_lines(entry)


def _section_body(entry: Dict[str, Any], compact_mode: str) -> str:
    """Render one entry's content per its verbosity + compact-mode."""
    if entry["verbosity"] == "full":
        out = _body_or_struct(entry)
        if entry["type"] == "story" and isinstance(entry.get("ac"), list) and entry["ac"]:
            out += "\n\n**Acceptance criteria:**\n" + "\n".join(f"- {a}" for a in entry["ac"])
        return out
    # struct verbosity
    if compact_mode == "llm":
        # Emit the full body but mark it for the LLM to summarize in-place.
        return f"<!-- COMPACT:{entry['id']} -->\n{_body_or_struct(entry)}\n<!-- /COMPACT:{entry['id']} -->"
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
) -> str:
    warnings = [e for e in digest if e.get("role") == "warning"]
    sections = [e for e in digest if e.get("type") != "_warning"]

    lines: List[str] = []
    lines.append("---")
    lines.append(f"product: {product_name}")
    lines.append(f"export: {select}")
    lines.append(f"depth: {depth}")
    lines.append(f"layers: {layers_label}")
    lines.append(f"compact_mode: {compact_mode}")
    if generated_at:
        lines.append(f"generated_at: {generated_at}")
    lines.append("---")
    lines.append("")
    lines.append(f"# Product Spec Export — {product_name}")
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


def render_html_doc(markdown_doc: str, product_name: str, generated_at: str, lang: str = "en") -> str:
    shell = EXPORT_SHELL.read_text(encoding="utf-8")
    values = render_html.body_render_values({"doc": markdown_doc})
    values.update({
        "lang_attr": lang,
        "title": render_html._escape(f"Spec Export — {product_name}"),
        "product_name": render_html._escape(product_name),
        "generated_at": generated_at,
    })
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
    md_doc = render_markdown_doc(digest, product_name, select, depth, layers_label, compact_mode, generated_at)
    stable = md_doc.replace(f"generated_at: {generated_at}\n", "", 1)
    content_hash = hashlib.sha256(stable.encode("utf-8")).hexdigest()[:8]

    out_dir = root / "docs" / "product" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ext = "html" if fmt == "html" else "md"
    target = out_dir / f"{_stem(select)}-{ts}-{content_hash}.{ext}"
    payload = render_html_doc(md_doc, product_name, generated_at, lang) if fmt == "html" else md_doc
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
