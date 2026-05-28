#!/usr/bin/env python3
"""
generate_templates — instantiate one of the assets/templates/*.md templates
for a given artifact type, substitute {{tokens}}, drop optional sections the
caller did not request, allocate the next parent-scoped ID, and write the
output to the correct path under docs/product/.

Token substitution: simple {{name}} -> value replacement. Tokens not provided
become the literal string "TBD" (so the file is still valid; the PO fills in).

Optional sections: `<!-- OPTIONAL: name --> ... <!-- /OPTIONAL -->` blocks
are kept ONLY if `name` appears in --keep-optional (comma-separated). All
other optional blocks are dropped.

ID allocation: parent-scoped. For a single run, an in-memory counter ensures
unique IDs when multiple artifacts share a parent (used by --auto braindump).

CLI:
    generate_templates.py --root <project-dir> --type <type> [--slug <slug>] \\
        [--parent <id>] [--values <json-file-or-string>] \\
        [--keep-optional <name,name>] [--lang en|vi] [--write]

Examples:
    # Allocate a new story under PRD-AUTH-E1 from values.json
    generate_templates.py --root . --type story --parent PRD-AUTH-E1 \\
        --values values.json --keep-optional notes --write
"""

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from encoding_utils import configure_utf8_console
from spec_graph import build_graph

configure_utf8_console()


TYPE_TEMPLATE = {
    "product": "product.md",
    "vision": "vision.md",
    "brd": "brd.md",
    "prd": "prd.md",
    "epic": "epic.md",
    "story": "story.md",
    "exec_summary": "exec-summary.md",
    "sign_off": "sign-off.md",
    "change_log_entry": "change-log-entry.md",
}

OUTPUT_PATH_FOR_TYPE = {
    "product": "PRODUCT.md",
    "vision": "vision.md",
    "brd": "brd.md",
    "prd": "prds/{slug}.md",
    "epic": "epics/{id}.md",
    "story": "stories/{id}.md",
    "exec_summary": "exec-summary.md",
}

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"

OPTIONAL_RE = re.compile(
    r"<!--\s*OPTIONAL:\s*(?P<name>[a-z0-9_-]+)\s*-->(?P<body>.*?)<!--\s*/OPTIONAL\s*-->",
    re.DOTALL,
)

TOKEN_RE = re.compile(r"\{\{(?P<key>[a-zA-Z0-9_]+)\}\}")


def allocate_id(graph: Dict[str, Any], target_type: str, slug: Optional[str], parent: Optional[str], session_used: List[str]) -> str:
    existing_ids = {n["id"] for n in graph["nodes"]} | set(session_used)
    if target_type == "goal":
        return _next_with_prefix(existing_ids, "BRD-G")
    if target_type == "prd":
        if not slug:
            raise ValueError("--slug is required for type=prd")
        return f"PRD-{slug.upper()}"
    if target_type == "epic":
        if not parent or not parent.startswith("PRD-"):
            raise ValueError("--parent must be a PRD ID for type=epic")
        return _next_with_prefix(existing_ids, f"{parent}-E")
    if target_type == "story":
        if not parent or "-E" not in parent:
            raise ValueError("--parent must be an epic ID for type=story")
        return _next_with_prefix(existing_ids, f"{parent}-S")
    if target_type == "product":
        return "PRODUCT"
    if target_type == "vision":
        return "VISION"
    if target_type == "brd":
        return "BRD"
    if target_type == "exec_summary":
        return "EXEC-SUMMARY"
    return ""


def _next_with_prefix(existing: set, prefix: str) -> str:
    n = 1
    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    used = []
    for x in existing:
        m = pattern.match(x or "")
        if m:
            used.append(int(m.group(1)))
    n = (max(used) + 1) if used else 1
    return f"{prefix}{n}"


def render(template_text: str, values: Dict[str, Any], keep_optional: List[str]) -> str:
    keep_set = set(keep_optional or [])

    def opt_replace(m: re.Match) -> str:
        name = m.group("name")
        body = m.group("body")
        return body if name in keep_set else ""

    rendered = OPTIONAL_RE.sub(opt_replace, template_text)

    def tok(m: re.Match) -> str:
        k = m.group("key")
        v = values.get(k)
        if v is None:
            return "TBD"
        if isinstance(v, (list, dict)):
            return json.dumps(v, ensure_ascii=False)
        return str(v)

    rendered = TOKEN_RE.sub(tok, rendered)

    # Strip the leading template comment (everything between first '<!--' and '-->\n')
    rendered = re.sub(r"\A\s*<!--.*?-->\s*\n", "", rendered, count=1, flags=re.DOTALL)
    return rendered


def output_path(root: Path, target_type: str, artifact_id: str, slug: Optional[str]) -> Path:
    template = OUTPUT_PATH_FOR_TYPE.get(target_type)
    if template is None:
        raise ValueError(f"no output path mapping for type {target_type!r}")
    out_rel = template.format(id=artifact_id, slug=(slug or "").lower())
    return root / "docs" / "product" / out_rel


def load_values(spec: Optional[str]) -> Dict[str, Any]:
    if not spec:
        return {}
    p = Path(spec)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(spec)


def fill_defaults(values: Dict[str, Any], target_type: str, artifact_id: str, lang: str) -> Dict[str, Any]:
    today = dt.date.today().isoformat()
    out = {
        "id": artifact_id,
        "status": "draft",
        "lang": lang,
        "owner": "TBD",
        "version": "0.1.0",
        "created": today,
        "updated": today,
    }
    out.update(values)
    out["id"] = artifact_id
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--type", required=True, choices=sorted(TYPE_TEMPLATE.keys()))
    ap.add_argument("--slug", help="uppercase slug for PRD (e.g., AUTH)")
    ap.add_argument("--parent", help="parent ID for epic/story")
    ap.add_argument("--values", help="JSON file path OR JSON string of token values")
    ap.add_argument("--keep-optional", default="", help="comma-separated names of optional sections to keep")
    ap.add_argument("--lang", default="en", choices=["en", "vi"])
    ap.add_argument("--write", action="store_true", help="write the file (default: print only)")
    ap.add_argument("--id", default=None, help="override allocated ID (used by --auto batch)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph = build_graph(root)
    keep_optional = [s.strip() for s in args.keep_optional.split(",") if s.strip()]
    values = load_values(args.values)

    artifact_id = args.id or allocate_id(graph, args.type, args.slug, args.parent, session_used=[])
    values = fill_defaults(values, args.type, artifact_id, args.lang)
    if args.parent:
        if args.type == "story":
            values.setdefault("epic", args.parent)
        elif args.type == "epic":
            values.setdefault("prd", args.parent)

    template_path = TEMPLATES_DIR / TYPE_TEMPLATE[args.type]
    template_text = template_path.read_text(encoding="utf-8")
    rendered = render(template_text, values, keep_optional)

    out_path = output_path(root, args.type, artifact_id, args.slug)
    response = {
        "type": args.type,
        "id": artifact_id,
        "path": str(out_path.relative_to(root)) if out_path.is_relative_to(root) else str(out_path),
        "written": False,
        "content": rendered,
    }
    if args.write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        response["written"] = True

    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
