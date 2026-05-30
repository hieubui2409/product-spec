#!/usr/bin/env python3
"""
visualize — dispatcher for the 11 visualization views in 3 formats
(ASCII / Mermaid / inline-vendored HTML). The 9 graph views default to --format
ascii; the 2 body-bearing viewers (board, explorer) default to --format html and
have no Mermaid form (a --format mermaid request falls back to their ASCII renderer).

Reads the graph JSON from spec_graph and routes the chosen view through the
matching renderer.

CLI:
    visualize.py --view <name> --format <ascii|mermaid|html> --root <dir>
                 [--lang en|vi] [--group-by status|horizon|moscow]
                 [--layers goal,prd,epic,story] [--filter-wont]
                 [--snapshot <snapshot.json>]   # --diff is the legacy alias

Graph views:  tree | heatmap | scope | roadmap | persona | gap | moscow | risk | delta
Body viewers: board | explorer
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from encoding_utils import configure_utf8_console
from spec_graph import build_graph, build_graph_with_artifacts

import render_ascii
import render_mermaid
import render_html
import render_board
import render_explorer

configure_utf8_console()


VIEWS = ("tree", "heatmap", "scope", "roadmap", "persona", "gap", "moscow", "risk", "delta", "board", "explorer")
FORMATS = ("ascii", "mermaid", "html")
# Legal `--layers` tokens for the body viewers (artifact TYPE, matching the CLI
# help + card type badge). Distinct from the EXPORT doc-layer vocab (vision,brd,…).
VIEWER_LAYERS = ("goal", "prd", "epic", "story")
# Body-bearing views render artifact bodies + own their html writer; they default
# to --format html (the 9 graph views default to ascii) and have NO Mermaid form
# (a --format mermaid request falls back to their ascii renderer with a note).
BODY_VIEWS = ("board", "explorer")


# Which kwargs each graph view's renderer accepts. ONE map drives both the ascii
# and mermaid dispatch so the "which view takes lang/filter_wont" knowledge lives
# in a single place instead of two lockstep if-ladders (delta is handled
# separately — it takes the baseline, not these graph-only kwargs). persona takes
# filter_wont on BOTH formats now, so the ascii/mermaid persona honor --filter-wont
# identically (previously mermaid/html silently ignored it).
_VIEW_KWARGS = {
    "tree": ("lang", "filter_wont"),
    "roadmap": ("lang", "filter_wont"),
    "persona": ("filter_wont",),
    "moscow": ("lang",),
}
_NO_BASELINE = "(no baseline yet — run --validate to create one)"


def _dispatch_view(module, view: str, graph: Dict[str, Any], baseline: Optional[Dict[str, Any]],
                   lang: str, filter_wont: bool, no_baseline_msg: str) -> str:
    if view == "delta":
        if not baseline:
            return no_baseline_msg
        return module.delta(graph, baseline)
    fn = getattr(module, view)
    kwargs = {k: (lang if k == "lang" else filter_wont) for k in _VIEW_KWARGS.get(view, ())}
    return fn(graph, **kwargs)


def _render_ascii(view: str, graph: Dict[str, Any], baseline: Optional[Dict[str, Any]], lang: str = "en", filter_wont: bool = False) -> str:
    return _dispatch_view(render_ascii, view, graph, baseline, lang, filter_wont, _NO_BASELINE)


def _render_mermaid(view: str, graph: Dict[str, Any], baseline: Optional[Dict[str, Any]], lang: str = "en", filter_wont: bool = False) -> str:
    return _dispatch_view(render_mermaid, view, graph, baseline, lang, filter_wont, f"```\n{_NO_BASELINE}\n```")


def _load_baseline(root: Path, override: Optional[str]) -> Optional[Dict[str, Any]]:
    snap_dir = root / "docs" / "product" / "visuals" / ".snapshots"

    def _read_snapshot(path: Path) -> Dict[str, Any]:
        # A corrupt snapshot file (truncated write, hand-edit, merge artefact)
        # would otherwise raise an uncaught JSONDecodeError and crash the
        # visualize pipeline. Surface a readable error and the offending
        # path so the PO can delete or repair it.
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"snapshot file is not valid JSON: {path} ({exc.msg} "
                f"at line {exc.lineno} col {exc.colno})"
            ) from exc

    if override:
        p = Path(override)
        if not p.is_absolute():
            p = snap_dir / override
        if not p.exists():
            # Originally returned None silently — the dispatcher then rendered
            # the generic "no baseline yet" message and a PO who typoed a
            # filename never learned why their --snapshot was ignored.
            available = sorted(snap_dir.glob("*.json")) if snap_dir.exists() else []
            available_names = [s.name for s in available]
            raise FileNotFoundError(
                f"--snapshot baseline not found: {p}. "
                f"Available snapshots in {snap_dir}: {available_names or '(none)'}"
            )
        return _read_snapshot(p)
    if not snap_dir.exists():
        return None
    # Order by mtime, not filename: snapshot names are <ts-to-second>-<hash>,
    # so same-second snapshots would otherwise sort by content hash (not time).
    snaps = sorted(snap_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not snaps:
        return None
    # With 1 snapshot, compare against the live graph (current). With 2+, use
    # the second-most-recent so the freshly-taken snapshot doesn't shadow the
    # change the PO is trying to see.
    target = snaps[-2] if len(snaps) >= 2 else snaps[-1]
    return _read_snapshot(target)


def _written_json(out: Path, root: Path) -> str:
    rel = str(out.relative_to(root)) if out.is_relative_to(root) else str(out)
    return json.dumps({"written": rel}, indent=2)


def _unfence(fenced: str) -> str:
    """Strip a leading/trailing plain ``` fence, returning the inner text. The
    Mermaid-can't-express views (heatmap/persona/risk/no-baseline delta) return
    their ASCII grid already wrapped in a plain ``` fence — unwrap and reuse it
    for the <pre> body instead of running the ASCII renderer a second time."""
    s = fenced.strip()
    if s.startswith("```"):
        s = s[3:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip("\n")


def _dispatch_body_view(view: str, fmt: str, root: Path, graph: Dict[str, Any],
                        artifacts, lang: str, filter_wont: bool, layers, group_by: str) -> int:
    """Render a body-bearing view (board / explorer). html → its own writer;
    ascii → its ascii renderer; mermaid → ascii fallback with a stderr note
    (these views carry no Mermaid by design — red-team M8). `artifacts` is parsed
    once by the caller alongside `graph` (build_graph_with_artifacts) — do NOT
    re-load here (that re-parsed every file a second time)."""
    if fmt == "mermaid":
        print(f"note: '{view}' has no Mermaid form; showing ascii fallback.", file=sys.stderr)
        fmt = "ascii"

    # Fail loud (Q1, parity with --export) when a non-empty --layers subset filters
    # every card out: a silently-empty board/explorer is the same silent failure the
    # export empty-after-filter guard closes. No --layers = nothing to fail on (the
    # allowed-empty case, mirroring `--export all` on a fresh spec).
    if layers and not render_ascii.select_cards(graph, layers, filter_wont):
        present = sorted({str(n.get("type")) for n in graph["nodes"] if n.get("type") in VIEWER_LAYERS})
        print(f"--layers {sorted(set(layers))} matched no cards for '{view}'"
              f"{' after --filter-wont' if filter_wont else ''}. "
              f"Card types present: {present or '(none)'}.", file=sys.stderr)
        return 2

    if view == "board":
        if fmt == "html":
            out = render_board.write(root, graph, artifacts, group_by=group_by, lang=lang,
                                     filter_wont=filter_wont, layers=layers)
            print(_written_json(out, root))
            return 0
        print(render_ascii.board(graph, group_by=group_by, lang=lang, filter_wont=filter_wont, layers=layers))
        return 0

    if view == "explorer":
        if fmt == "html":
            out = render_explorer.write(root, graph, artifacts, lang=lang,
                                        filter_wont=filter_wont, layers=layers)
            print(_written_json(out, root))
            return 0
        print(render_ascii.explorer(graph, lang=lang, filter_wont=filter_wont, layers=layers))
        return 0

    raise SystemExit(f"unknown body view: {view}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--view", required=True, choices=VIEWS)
    # default None → resolved per view: body views (board/explorer) → html, the
    # 9 graph views → ascii (preserves their long-standing default).
    ap.add_argument("--format", default=None, choices=FORMATS)
    ap.add_argument("--lang", default="en", choices=["en", "vi"])
    ap.add_argument("--group-by", dest="group_by", default="status",
                    choices=["status", "horizon", "moscow"],
                    help="board: column grouping field (default status).")
    ap.add_argument("--layers", default=None,
                    help="board/explorer: comma subset of goal,prd,epic,story to filter cards.")
    ap.add_argument(
        "--snapshot", default=None,
        help="path or filename of a baseline snapshot in .snapshots/ "
             "(used by --view delta). Alias --diff is kept for one cycle "
             "for transitional compatibility.",
    )
    ap.add_argument("--diff", dest="snapshot", default=None, help=argparse.SUPPRESS)
    ap.add_argument(
        "--filter-wont", action="store_true",
        help="hide deferred items (moscow=wont or scope=out) from "
             "tree/roadmap/persona/board/explorer. Default keeps them visible "
             "(a `*` marker on graph views; a card on board/explorer).",
    )
    args = ap.parse_args()

    # Resolve the per-view default format.
    fmt = args.format or ("html" if args.view in BODY_VIEWS else "ascii")
    layers = [s.strip() for s in args.layers.split(",") if s.strip()] if args.layers else None
    if layers:
        bad = [l for l in layers if l not in VIEWER_LAYERS]
        if bad:
            print(f"--layers: unknown value(s) {sorted(bad)}. Valid viewer layers: "
                  f"{list(VIEWER_LAYERS)}.", file=sys.stderr)
            return 2

    root = Path(args.root).resolve()
    # Body views need the parsed artifacts (bodies); parse docs/product/ ONCE via
    # build_graph_with_artifacts instead of build_graph + a second load_artifacts.
    if args.view in BODY_VIEWS:
        graph, artifacts = build_graph_with_artifacts(root)
    else:
        graph = build_graph(root)
    baseline = _load_baseline(root, args.snapshot) if args.view == "delta" else None

    # Body views own their html writer and have no Mermaid form — dispatch them
    # BEFORE the generic ascii/mermaid/<pre> branches so they never render as a
    # <pre> dump or AttributeError on getattr(render_mermaid, "board").
    if args.view in BODY_VIEWS:
        return _dispatch_body_view(args.view, fmt, root, graph, artifacts, args.lang, args.filter_wont, layers, args.group_by)

    if fmt == "ascii":
        body = _render_ascii(args.view, graph, baseline, lang=args.lang, filter_wont=args.filter_wont)
        print(body)
        return 0

    if fmt == "mermaid":
        body = _render_mermaid(args.view, graph, baseline, lang=args.lang, filter_wont=args.filter_wont)
        print(body)
        return 0

    # html
    # The risk view has no clean Mermaid form (design report Q44); instead of the
    # ASCII-in-<pre> fallback the other Mermaid-can't-express views use, it has a
    # dedicated HTML-native 3×3 grid whose cells drill down to description +
    # mitigation + status (G-C3 / G-G3). Route it BEFORE the generic Mermaid path.
    if args.view == "risk":
        grid = render_html.risk(graph)
        out = render_html.write(root, "risk", "risk-grid", grid, graph, lang=args.lang)
        print(_written_json(out, root))
        return 0

    mermaid_text = _render_mermaid(args.view, graph, baseline, lang=args.lang, filter_wont=args.filter_wont)
    # Mermaid renderers return either a ```mermaid fenced block (true Mermaid
    # DSL) or a plain ``` fenced block (ASCII fallback for views Mermaid can't
    # express: heatmap, persona, risk, no-baseline delta). Only the former
    # belongs in a <div class="mermaid"> wrapper; the latter must be HTML-
    # escaped inside a <pre> tag so the browser renders raw text and Mermaid
    # leaves it alone.
    if mermaid_text.startswith("```mermaid"):
        body_text = mermaid_text
        view_format = "mermaid"
    else:
        # Fallback views already embed the ASCII grid inside a plain ``` fence
        # (render_mermaid wraps the same render_ascii output); unwrap and reuse it
        # rather than re-running the ASCII renderer.
        body_text = _unfence(mermaid_text)
        view_format = "pre"
    out = render_html.write(root, args.view, view_format, body_text, graph, lang=args.lang)
    print(_written_json(out, root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
