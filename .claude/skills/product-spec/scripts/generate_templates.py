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

ID allocation: parent-scoped. The CLI allocates ONE id per invocation (it passes
an empty `session_used`). `allocate_id(..., session_used=[...])` is the library
entry point for callers that mint MULTIPLE ids in one process: pass the ids
already handed out this session so siblings under the same parent don't collide
(exercised by the tests).

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
from typing import Any, Dict, List, Optional

from encoding_utils import configure_utf8_console
from spec_graph import build_graph, ID_PATTERN_BY_TYPE

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

# Strict parent-ID patterns — derived from spec_graph.ID_PATTERN_BY_TYPE (the
# single authoritative home) so a parent passed at generate time fast-fails the
# same way it would be flagged at validate time.
PARENT_PATTERN_FOR_PRD = ID_PATTERN_BY_TYPE["prd"]   # PRD-<SLUG>, slug ≤16 chars
PARENT_PATTERN_FOR_EPIC = ID_PATTERN_BY_TYPE["epic"]  # PRD-<SLUG>-E<n>
# A trailing -E<n> or -E<n>-S<n> means the ID is an epic or story shape — reject
# when a PRD ID is expected so callers can't accidentally pass an epic/story.
PRD_PARENT_LOOKS_LIKE_EPIC_OR_STORY = re.compile(r"-E\d+(-S\d+)?$")
# Bare PRD slug fast-fail (uppercase ASCII letter start, digits/hyphens, ≤16
# chars). Must match the slug section of PARENT_PATTERN_FOR_PRD so that
# `PRD-<SLUG>` produced below is itself a valid parent for an epic.
SLUG_PATTERN_FOR_PRD = re.compile(r"^[A-Z][A-Z0-9-]{0,15}$")

# Caller-supplied `--id` override patterns — keyed from spec_graph.ID_PATTERN_BY_TYPE
# (the single authoritative home) so an --auto batch caller that pre-allocates IDs
# cannot smuggle an invalid one past the generator.
ID_PATTERN_OVERRIDE: Dict[str, re.Pattern] = {
    **ID_PATTERN_BY_TYPE,
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
        # A slug like AUTH-E1 mints PRD-AUTH-E1, which collides with the epic-1 ID
        # grammar under PRD-AUTH. Reject any slug whose resulting ID tail looks like
        # an epic (-E<n>) or story (-E<n>-S<n>) suffix.
        if PRD_PARENT_LOOKS_LIKE_EPIC_OR_STORY.search(normalised):
            raise ValueError(
                f"--slug {slug!r} produces an ID (PRD-{normalised}) that collides "
                f"with the epic/story ID grammar (suffix -{normalised.split('-E', 1)[-1]!r} "
                f"matches -E<n> or -E<n>-S<n>). Use a slug without a trailing -E<n> sequence."
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
    # A non-greedy match cannot consume a nested OPTIONAL block in one pass.
    # Any leftover <!-- OPTIONAL: ... --> or <!-- /OPTIONAL --> sentinels are
    # structural noise; strip them so they don't leak into the artifact.
    rendered = re.sub(r"<!--\s*/?OPTIONAL(?:\s*:.*?)?\s*-->", "", rendered)

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
    # BEFORE the residual-token check, so an illustrative {{example-token}} inside
    # the soon-to-be-discarded header comment can't spuriously trip the guard.
    rendered = re.sub(r"\A\s*<!--.*?-->\s*\n", "", rendered, count=1, flags=re.DOTALL)

    # TOKEN_RE only matches [a-zA-Z0-9_]+ tokens, so keys containing hyphens,
    # spaces, or dots (e.g. {{bad-key}}, {{ spaced }}) are left literally in
    # the output. Detect and reject them so a malformed template fails loudly
    # instead of writing literal {{...}} into the artifact.
    RESIDUAL_TOKEN_RE = re.compile(r"\{\{.*?\}\}")
    residual = RESIDUAL_TOKEN_RE.search(rendered)
    if residual:
        raise ValueError(
            f"unresolved template token {residual.group()!r} found after substitution; "
            f"token keys must match [a-zA-Z0-9_]+ — hyphens, spaces, and dots are not allowed"
        )

    return rendered


def _prd_slug_from_id(artifact_id: str) -> str:
    """Derive the lowercase slug from a PRD-<SLUG> id. The single home for this
    derivation; both output_path() and _run() call here so they never diverge."""
    return artifact_id[4:].lower()


def output_path(root: Path, target_type: str, artifact_id: str, slug: Optional[str]) -> Optional[Path]:
    """Return the output path for a type that has an OUTPUT_PATH_FOR_TYPE mapping,
    or None for content-only types (sign_off, change_log_entry) that have no file home
    in the standard layout."""
    template = OUTPUT_PATH_FOR_TYPE.get(target_type)
    if template is None:
        return None
    # PRD: ensure slug is never empty (would produce `prds/.md`).
    # _prd_slug_from_id is the single derivation home — no inline re-derivation.
    if target_type == "prd" and not slug and artifact_id.upper().startswith("PRD-"):
        slug = _prd_slug_from_id(artifact_id)
    out_rel = template.format(id=artifact_id, slug=(slug or "").lower())
    return root / "docs" / "product" / out_rel


def load_values(spec: Optional[str]) -> Dict[str, Any]:
    if not spec:
        return {}
    p = Path(spec)
    try:
        if p.exists():
            raw = json.loads(p.read_text(encoding="utf-8"))
        else:
            raw = json.loads(spec)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--values: invalid JSON ({exc})") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"--values: could not read file {spec!r} ({exc})") from exc
    if not isinstance(raw, dict):
        raise ValueError(
            f"--values: top-level JSON must be an object (mapping); "
            f"got {type(raw).__name__} — pass a JSON object like {{\"key\": \"value\"}}."
        )
    return raw


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
    # COMPETITION: the BRD's competitor-identity list. Same per-character-iteration
    # hazard as the other list fields, so default to [] (never the bare "TBD").
    "competitors",
)

# COMPETITION: a PRD's `competitive_parity` is an ID-keyed MAP, not a list, so it
# defaults to an empty mapping {} (token substitution emits valid YAML `{}`).
# Kept separate from LIST_FIELDS so the [] default doesn't mis-shape the map.
MAP_FIELDS = (
    "competitive_parity",
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
    for k in MAP_FIELDS:
        out[k] = {}
    out.update(values)
    # A caller may pass an explicit None for a structural field (e.g. {"personas":
    # null} from a --values payload), which would shadow the [] / {} default and
    # break downstream iteration (renderers do `for x in personas`). Restore the
    # empty default for any None'd list/map field.
    for k in LIST_FIELDS:
        if out.get(k) is None:
            out[k] = []
    for k in MAP_FIELDS:
        if out.get(k) is None:
            out[k] = {}
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

    try:
        return _run(args)
    except ValueError as exc:
        # Analytical script contract: any ValueError surfaces as a JSON finding
        # on stdout + exit 0 — never a bare traceback (validation-rules-spec.md:63).
        response = {
            "type": args.type,
            "id": args.id or "",
            "path": None,
            "written": False,
            "content": None,
            "error": "invalid_input",
            "message": str(exc),
        }
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return 0


def _run(args: argparse.Namespace) -> int:
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
        # For type=prd, --id is authoritative: the file is placed at prds/<slug>
        # where slug = id[4:].lower(). If --slug is also given it MUST agree,
        # otherwise the file path (based on --slug) diverges from the frontmatter id
        # (based on --id) → mislocated artifact that validate won't catch.
        if args.type == "prd" and args.slug:
            id_slug = args.id[4:].lower() if args.id.upper().startswith("PRD-") else ""
            if id_slug != args.slug.lower():
                raise ValueError(
                    f"--id {args.id!r} and --slug {args.slug!r} are inconsistent: "
                    f"the slug implied by --id is {id_slug!r}. "
                    f"Either omit --slug (let --id drive the path) or align them."
                )
        artifact_id = args.id
    else:
        artifact_id = allocate_id(graph, args.type, args.slug, args.parent, session_used=[])

    # For types with no OUTPUT_PATH mapping (sign_off, change_log_entry), the
    # artifact is content-only — no file path is assigned and --write is a no-op.
    has_path_mapping = args.type in OUTPUT_PATH_FOR_TYPE

    # Derive slug from --id for type=prd when --slug is omitted, so the output path
    # never collapses to `prds/.md`. _prd_slug_from_id is the single home used by
    # both this derivation and output_path() — no duplication.
    effective_slug = args.slug
    if args.type == "prd" and not effective_slug and artifact_id.upper().startswith("PRD-"):
        effective_slug = _prd_slug_from_id(artifact_id)

    # For epic/story: when --id given without --parent, derive the parent ID from
    # the artifact_id so token substitution doesn't leave the parent token as 'TBD'
    # (a downstream dangling-link error).
    effective_parent = args.parent
    if not effective_parent and args.id:
        if args.type == "story" and "-S" in args.id:
            effective_parent = args.id.rsplit("-S", 1)[0]
        elif args.type == "epic" and "-E" in args.id:
            effective_parent = args.id.rsplit("-E", 1)[0]

    values = fill_defaults(values, args.type, artifact_id, args.lang)
    if effective_parent:
        if args.type == "story":
            values.setdefault("epic", effective_parent)
        elif args.type == "epic":
            values.setdefault("prd", effective_parent)

    template_path = TEMPLATES_DIR / TYPE_TEMPLATE[args.type]
    template_text = template_path.read_text(encoding="utf-8")
    rendered = render(template_text, values, keep_optional)

    out_path = output_path(root, args.type, artifact_id, effective_slug) if has_path_mapping else None
    response: Dict[str, Any] = {
        "type": args.type,
        "id": artifact_id,
        "path": (
            str(out_path.relative_to(root)) if (out_path is not None and out_path.is_relative_to(root))
            else (str(out_path) if out_path is not None else None)
        ),
        "written": False,
        "content": rendered,
    }
    if args.write and out_path is not None:
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
        # Write with newline translation DISABLED so the generated file is
        # byte-identical across platforms (LF as authored), not os.linesep-
        # normalized — matches migrate_multidim_fields' write discipline.
        with open(out_path, "w", encoding="utf-8", newline="") as fh:
            fh.write(rendered)
        response["written"] = True

    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
