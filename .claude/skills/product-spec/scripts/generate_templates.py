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

# Strict parent-ID patterns. Kept in sync with check_consistency.ID_PATTERN_BY_TYPE
# so a parent passed at generate time fast-fails the same way it would be flagged
# at validate time. Slug section is 1+15=16 chars max (uppercase, digits, hyphens).
PARENT_PATTERN_FOR_PRD = re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}$")
PARENT_PATTERN_FOR_EPIC = re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+$")
# The slug regex above is permissive (hyphens allowed). A trailing -E<n> or
# -E<n>-S<n> means the ID is actually an epic or story shape — reject when a
# PRD ID is expected so callers can't accidentally pass an epic/story.
PRD_PARENT_LOOKS_LIKE_EPIC_OR_STORY = re.compile(r"-E\d+(-S\d+)?$")
# Bare PRD slug fast-fail (uppercase ASCII letter start, digits/hyphens, ≤16
# chars). Must match the slug section of PARENT_PATTERN_FOR_PRD so that
# `PRD-<SLUG>` produced below is itself a valid parent for an epic.
SLUG_PATTERN_FOR_PRD = re.compile(r"^[A-Z][A-Z0-9-]{0,15}$")

# Caller-supplied `--id` override patterns. Kept in sync with
# check_consistency.ID_PATTERN_BY_TYPE so an --auto batch caller that
# pre-allocates IDs cannot smuggle an invalid one past the generator.
ID_PATTERN_OVERRIDE = {
    "goal": re.compile(r"^BRD-G[0-9]+$"),
    "prd": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}$"),
    "epic": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+$"),
    "story": re.compile(r"^PRD-[A-Z][A-Z0-9-]{0,15}-E[0-9]+-S[0-9]+$"),
    "product": re.compile(r"^PRODUCT$"),
    "vision": re.compile(r"^VISION$"),
    "brd": re.compile(r"^BRD$"),
    "exec_summary": re.compile(r"^EXEC-SUMMARY$"),
    "sign_off": re.compile(r".+"),
    "change_log_entry": re.compile(r".+"),
}

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
        normalised = slug.upper()
        if not SLUG_PATTERN_FOR_PRD.match(normalised):
            raise ValueError(
                f"--slug must be uppercase ASCII (A-Z, 0-9, hyphen), start with "
                f"a letter, and be ≤16 chars (matches {SLUG_PATTERN_FOR_PRD.pattern}); "
                f"got {slug!r}"
            )
        return f"PRD-{normalised}"
    if target_type == "epic":
        # Parent must be a PRD ID exactly (PRD-<SLUG>, slug ≤16 chars). Reject
        # story/epic IDs (which would emit nonsense like PRD-AUTH-E1-S1-E1) and
        # oversized slugs (which would later trip invalid_id at validate time).
        if (
            not parent
            or not PARENT_PATTERN_FOR_PRD.match(parent)
            or PRD_PARENT_LOOKS_LIKE_EPIC_OR_STORY.search(parent)
        ):
            raise ValueError(
                f"--parent must be a valid PRD ID for type=epic "
                f"(PRD-<SLUG>, slug ≤16 chars, no -E<n>/-S<n> suffix); got {parent!r}"
            )
        return _next_with_prefix(existing_ids, f"{parent}-E")
    if target_type == "story":
        # Parent must be an epic ID exactly (PRD-<SLUG>-E<n>). Substring "-E"
        # would also match a story ID and allow PRD-AUTH-E1-S1-S1 nonsense.
        if not parent or not PARENT_PATTERN_FOR_EPIC.match(parent):
            raise ValueError(
                f"--parent must be a valid epic ID for type=story "
                f"(pattern {PARENT_PATTERN_FOR_EPIC.pattern}); got {parent!r}"
            )
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
        s = str(v)
        # Reject embedded newlines in scalar values: a caller-supplied
        # `--values '{"id":"foo\nstatus: approved"}'` would otherwise
        # inject a duplicate YAML key and bypass the approval guard
        # below. Multi-line content belongs in body sections, not in
        # single-line frontmatter substitution.
        if "\n" in s or "\r" in s:
            raise ValueError(
                f"value for token {{{{{k}}}}} contains a newline; "
                f"frontmatter tokens must be single-line scalars"
            )
        return s

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


# List-typed frontmatter fields. If the caller omits them, default to [] so
# token substitution emits a valid YAML list — never the bare string "TBD"
# (which downstream renderers iterate per-character: persona viz would render
# rows 'T', 'B', 'D' and traceability would flag phantom dangling_link errors
# for refs T/B/D). Closed list per references/frontmatter-and-id-spec.md.
LIST_FIELDS = (
    "personas",
    "metrics",
    "brd_goals",
    "risks",
    "acceptance_criteria",
)


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
    for k in LIST_FIELDS:
        out[k] = []
    out.update(values)
    out["id"] = artifact_id
    # Defense-in-depth: generate never mints `approved` artifacts. Approval is
    # a separate explicit promotion flow (records owner + date + version bump).
    # Caller-supplied `status: approved` is the most common silent-approval
    # vector; reject it here so the script layer cannot be tricked into it
    # even if a higher layer's safeguards regress.
    if out.get("status") == "approved":
        raise ValueError(
            f"generate_templates refuses to create {target_type}={artifact_id!r} "
            f"with status='approved'. New artifacts must start as 'draft'. "
            f"Use the explicit approval flow (--approve) to promote later."
        )
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
    ap.add_argument(
        "--force", action="store_true",
        help="with --write: overwrite an existing file. Without --force, "
             "an existing path causes the script to refuse rather than "
             "silently clobber manual PO edits.",
    )
    ap.add_argument("--id", default=None, help="override allocated ID (used by --auto batch)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    graph = build_graph(root)
    keep_optional = [s.strip() for s in args.keep_optional.split(",") if s.strip()]
    values = load_values(args.values)

    if args.id:
        # A pre-allocated `--id` from an --auto braindump still has to honour
        # the parent-scoped grammar; otherwise the LLM batch could quietly
        # mint a story like `PRD-AUTH-S99` (missing the epic segment) and
        # the validator would only catch it on the next pass.
        pattern = ID_PATTERN_OVERRIDE.get(args.type)
        if pattern and not pattern.match(args.id):
            raise ValueError(
                f"--id {args.id!r} does not match expected pattern "
                f"{pattern.pattern} for type={args.type}"
            )
        artifact_id = args.id
    else:
        artifact_id = allocate_id(graph, args.type, args.slug, args.parent, session_used=[])
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
        if out_path.exists() and not args.force:
            response["error"] = "exists"
            response["message"] = (
                f"refusing to overwrite existing file: "
                f"{out_path.relative_to(root) if out_path.is_relative_to(root) else out_path}. "
                f"Pass --force to overwrite."
            )
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return 0
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")
        response["written"] = True

    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
