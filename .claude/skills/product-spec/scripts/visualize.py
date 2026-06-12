#!/usr/bin/env python3
"""
visualize — dispatcher for the 20 visualization views in up to 4 formats
(ASCII / Mermaid / inline-vendored HTML / md). Most graph views default to --format
ascii; the risk/competition/dashboard graph views and the 2 body-bearing viewers
(board, explorer) default to --format html. The body viewers have no Mermaid form
(a --format mermaid request falls back to their ASCII renderer).

Most views read the graph JSON from spec_graph; the `audit`, `--learn` outcome views
(scorecard/insight-gap/outcome-trend), and learning views (learning-map/learning) are
self-contained and dispatched in dedicated blocks (they read outcomes.md / the audit
trail, NOT graph nodes). `md` is valid only for `audit`.

CLI:
    visualize.py --view <name> --format <ascii|mermaid|html|md> --root <dir>
                 [--lang en|vi] [--group-by status|horizon|moscow]
                 [--layers goal,prd,epic,story] [--filter-wont]
                 [--snapshot <snapshot.json>]   # --diff is the legacy alias

Graph views:   tree | heatmap | scope | roadmap | persona | gap | moscow | risk | competition | time | delta | dashboard
Body viewers:  board | explorer
Governance:    audit
--learn views: scorecard | insight-gap | outcome-trend | learning-map | learning
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from encoding_utils import configure_utf8_console
from fs_guard import FenceError
from spec_graph import build_graph, build_graph_with_artifacts

import render_ascii
from render_ascii import _BOARD_CARD_TYPES
import render_mermaid
import render_html
import render_board
import render_explorer
import visuals_retention

configure_utf8_console()


VIEWS = ("tree", "heatmap", "scope", "roadmap", "persona", "gap", "moscow", "risk", "competition", "time", "delta", "dashboard", "board", "explorer", "audit", "scorecard", "insight-gap", "outcome-trend", "learning-map", "learning")
# --learn outcome views: read outcomes.md + brd goals via load_outcomes (NOT the
# spec graph), so they are dispatched in a self-contained block like `audit`.
# scorecard defaults to html (card-rich headline); gap/trend default to ascii.
OUTCOME_VIEWS = ("scorecard", "insight-gap", "outcome-trend")
# learning-map = outcome→goal→DEC flow (mermaid default, reusing the audit trail);
# learning = HTML-only dashboard stacking scorecard/gap/trend + a link to the map.
LEARNING_VIEWS = ("learning-map", "learning")
# `md` is accepted ONLY for the `audit` governance view (ASCII + markdown, no HTML this phase);
# requesting it for any other view is rejected with a friendly note.
FORMATS = ("ascii", "mermaid", "html", "md")
# Legal `--layers` tokens for the body viewers (artifact TYPE, matching the CLI
# help + card type badge). Distinct from the EXPORT doc-layer vocab (vision,brd,…).
# Single source: render_ascii._BOARD_CARD_TYPES owns this list; mirroring it here
# kept the two sets in sync only by convention — now derived directly.
VIEWER_LAYERS = tuple(_BOARD_CARD_TYPES)
# Body-bearing views render artifact bodies + own their html writer; they default
# to --format html (the 9 graph views default to ascii) and have NO Mermaid form
# (a --format mermaid request falls back to their ascii renderer with a note).
BODY_VIEWS = ("board", "explorer")
# PO decision — HTML-native is the default for the rich multi-dim/matrix
# views: the risk grid + competition matrix/heatmap (Mermaid can't express these
# cleanly) and the HTML-only `dashboard`. tree/roadmap/heatmap/scope/persona/gap/
# moscow/time/delta keep their ASCII default so the zero-dep terminal path loses
# nothing (the ASCII downgrade preserved a text-summary, not removed it).
HTML_DEFAULT_VIEWS = ("risk", "competition", "dashboard")
# `dashboard` is HTML-only (no ASCII/Mermaid form). A non-HTML request falls back
# to HTML with a stderr note rather than crashing (parity with the board/explorer
# mermaid fallback). It is a GRAPH view (not a body view): no card bodies, so no
# sanitizer payload — it stacks the already-escaped risk/competition fragments.
HTML_ONLY_VIEWS = ("dashboard",)


# Which kwargs each graph view's renderer accepts. ONE map drives both the ascii
# and mermaid dispatch so the "which view takes lang/filter_wont" knowledge lives
# in a single place instead of two lockstep if-ladders (delta is handled
# separately — it takes the baseline, not these graph-only kwargs). persona takes
# filter_wont on BOTH formats now, so the ascii/mermaid persona honor --filter-wont
# identically (previously mermaid/html silently ignored it).
_VIEW_KWARGS = {
    "tree": ("lang", "filter_wont"),
    "roadmap": ("lang", "filter_wont"),
    "time": ("lang", "filter_wont"),
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
    # Tiebreak by name so same-second snapshots produce a deterministic order.
    snaps = sorted(snap_dir.glob("*.json"), key=lambda p: (p.stat().st_mtime, p.name))
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
    (these views carry no Mermaid by design). `artifacts` is parsed
    once by the caller alongside `graph` (build_graph_with_artifacts) — do NOT
    re-load here (that re-parsed every file a second time)."""
    if fmt == "mermaid":
        print(f"note: '{view}' has no Mermaid form; showing ascii fallback.", file=sys.stderr)
        fmt = "ascii"

    # Compute selected nodes once: used for the empty-check guard below AND passed
    # into the HTML builders so they don't run select_cards a second time. The
    # ascii/mermaid-fallback branch does NOT use this variable — it runs its own
    # implicit scan inside render_ascii.board/explorer (cheap O(n) list walk).
    selected = render_ascii.select_cards(graph, layers, filter_wont)

    # Fail loud (Q1, parity with --export) when a non-empty --layers subset filters
    # every card out: a silently-empty board/explorer is the same silent failure the
    # export empty-after-filter guard closes. No --layers = nothing to fail on (the
    # allowed-empty case, mirroring `--export all` on a fresh spec).
    if layers and not selected:
        present = sorted({str(n.get("type")) for n in graph["nodes"] if n.get("type") in VIEWER_LAYERS})
        print(f"--layers {sorted(set(layers))} matched no cards for '{view}'"
              f"{' after --filter-wont' if filter_wont else ''}. "
              f"Card types present: {present or '(none)'}.", file=sys.stderr)
        return 2

    if view == "board":
        if fmt == "html":
            out = render_board.write(root, graph, artifacts, group_by=group_by, lang=lang,
                                     filter_wont=filter_wont, layers=layers,
                                     selected_nodes=selected)
            print(_written_json(out, root))
            return 0
        print(render_ascii.board(graph, group_by=group_by, lang=lang, filter_wont=filter_wont, layers=layers))
        return 0

    if view == "explorer":
        if fmt == "html":
            out = render_explorer.write(root, graph, artifacts, lang=lang,
                                        filter_wont=filter_wont, layers=layers,
                                        selected_nodes=selected)
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
             "tree/roadmap/time/persona/board/explorer. Default keeps them visible "
             "(a `*` marker on graph views; a card on board/explorer).",
    )
    ap.add_argument(
        "--clean", action="store_true",
        help="prune old timestamped renders for --view, keeping the most recent "
             f"{visuals_retention.RETENTION_KEEP} plus the -latest alias.",
    )
    args = ap.parse_args()

    # --clean: prune old timestamped renders for the requested view; -latest survives.
    if args.clean:
        root = Path(args.root).resolve()
        deleted = visuals_retention.clean_old_renders(root, args.view)
        if deleted:
            print(json.dumps({"cleaned": [str(p) for p in deleted]}, indent=2))
        else:
            print(json.dumps({"cleaned": []}, indent=2))
        return 0

    # Audit governance view: self-contained ASCII+md assembler (no graph dispatch,
    # no HTML emitter — keeps the view registry off the XSS watch this phase).
    if args.view == "audit":
        import assemble_audit_trail
        afmt = args.format or "ascii"
        if afmt == "mermaid":
            # An audit trail is a chronological table, not a graph — no Mermaid form.
            print("note: 'audit' has no Mermaid form (it is a chronological table); "
                  "rendering ascii.", file=sys.stderr)
            afmt = "ascii"
        root = Path(args.root).resolve()
        data = assemble_audit_trail.assemble(root)
        if afmt == "html":
            # HTML-native: render_html.audit escapes EVERY dynamic field server-side
            # (who_approved / DEC title / change-log text), then write a self-contained
            # page through the soft fence — same path as risk/competition.
            frag = render_html.audit(data, lang=args.lang)
            out = render_html.write(root, "audit", "html", frag, {}, lang=args.lang)
            print(_written_json(out, root))
        elif afmt == "md":
            print(assemble_audit_trail.render_markdown(data, args.lang))
        else:
            print(assemble_audit_trail.render_ascii(data, args.lang))
        return 0

    # --learn outcome views: self-contained (load_outcomes joins outcomes.md + brd
    # goals; no graph dispatch). Special-cased like `audit` so outcome data never has
    # to masquerade as graph nodes. HTML fragments are escaped server-side in
    # render_outcomes (the shared render_html._escape chokepoint).
    if args.view in OUTCOME_VIEWS:
        import load_outcomes
        import render_outcomes
        root = Path(args.root).resolve()
        data = load_outcomes.load_outcomes(root)
        ofmt = args.format or ("html" if args.view == "scorecard" else "ascii")
        if ofmt == "mermaid":
            print(f"note: '{args.view}' has no Mermaid form; rendering ascii.", file=sys.stderr)
            ofmt = "ascii"
        if ofmt == "md":
            print("--format md is only valid for --view audit.", file=sys.stderr)
            return 2
        ascii_fn = {"scorecard": render_outcomes.scorecard,
                    "insight-gap": render_outcomes.insight_gap,
                    "outcome-trend": render_outcomes.outcome_trend}[args.view]
        if ofmt == "html":
            html_fn = {"scorecard": render_outcomes.scorecard_html,
                       "insight-gap": render_outcomes.insight_gap_html,
                       "outcome-trend": render_outcomes.outcome_trend_html}[args.view]
            frag = html_fn(data, lang=args.lang)
            try:
                out = render_html.write(root, args.view, "html", frag, {}, lang=args.lang)
            except FenceError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            print(_written_json(out, root))
        else:
            print(ascii_fn(data, lang=args.lang))
        return 0

    # --learn learning views: learning-map (outcome→goal→DEC flow over the audit
    # trail; mermaid default, ascii downgrade, html via the shared mermaid wrapper) +
    # learning (HTML-only dashboard). Self-contained like the outcome block above.
    if args.view in LEARNING_VIEWS:
        import assemble_audit_trail
        import load_outcomes
        import render_learning
        root = Path(args.root).resolve()
        if args.view == "learning":
            if args.format and args.format != "html":
                print("note: 'learning' is HTML-only; rendering HTML.", file=sys.stderr)
            data = load_outcomes.load_outcomes(root)
            frag = render_learning.learning_dashboard_html(data, lang=args.lang)
            try:
                out = render_html.write(root, "learning", "html", frag, {}, lang=args.lang)
            except FenceError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            print(_written_json(out, root))
            return 0
        # learning-map
        if args.format == "md":
            print("--format md is only valid for --view audit.", file=sys.stderr)
            return 2
        audit = assemble_audit_trail.assemble(root)
        lfmt = args.format or "mermaid"
        if lfmt == "ascii":
            print(render_learning.learning_map_ascii(audit, lang=args.lang))
            return 0
        mermaid_text = render_learning.learning_map_mermaid(audit, lang=args.lang)
        if lfmt == "mermaid":
            print(mermaid_text)
            return 0
        try:  # html: reuse the generic mermaid→html page wrapper (runtime + <>escape)
            out = render_html.write(root, "learning-map", "mermaid", mermaid_text, {}, lang=args.lang)
        except FenceError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(_written_json(out, root))
        return 0

    # `md` is audit-only — reject it for every other view (keeps each surface's help honest).
    if args.format == "md":
        print("--format md is only valid for --view audit.", file=sys.stderr)
        return 2

    # Resolve the per-view default format: body viewers + the HTML-native
    # multi-dim/matrix views default to html; the other graph views to ascii.
    if args.format:
        fmt = args.format
    elif args.view in BODY_VIEWS or args.view in HTML_DEFAULT_VIEWS:
        fmt = "html"
    else:
        fmt = "ascii"

    # HTML-only views (dashboard) have no ascii/mermaid form: a non-html request
    # falls back to html with a stderr note (parity with board/explorer's mermaid
    # fallback) so the PO still gets the page instead of a crash/blank.
    if args.view in HTML_ONLY_VIEWS and fmt != "html":
        print(f"note: '{args.view}' is HTML-only; rendering HTML "
              f"(requested --format {fmt} has no {args.view} form).", file=sys.stderr)
        fmt = "html"
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
    try:
        baseline = _load_baseline(root, args.snapshot) if args.view == "delta" else None
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    # The HTML/body write paths route through the soft fence (render_html.write,
    # render_board, render_explorer). A blocked target raises FenceError BEFORE any
    # bytes land; surface it as the same stderr message + non-zero exit used for a
    # bad --root / baseline above, never a bare traceback.
    try:
        return _dispatch(args, fmt, root, graph, baseline,
                         artifacts if args.view in BODY_VIEWS else None, layers)
    except FenceError as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _dispatch(args, fmt, root, graph, baseline, artifacts, layers) -> int:
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
    # The risk view has no clean Mermaid form; instead of the
    # ASCII-in-<pre> fallback the other Mermaid-can't-express views use, it has a
    # dedicated HTML-native 3×3 grid whose cells drill down to description +
    # mitigation + status. Route it BEFORE the generic Mermaid path.
    if args.view == "risk":
        grid = render_html.risk(graph)
        out = render_html.write(root, "risk", "risk-grid", grid, graph, lang=args.lang)
        print(_written_json(out, root))
        return 0

    # The competition view is HTML-native too (parity matrix + threat heatmap;
    # NOT Mermaid). It reuses the SAME pre-rendered
    # native-fragment path as risk (view_format "html"): render_html.competition
    # escapes every spec-derived value server-side, so the fragment is injected
    # as-is. Route it BEFORE the generic Mermaid path so it never wraps in a
    # <div class="mermaid"> or an ASCII <pre> fallback.
    if args.view == "competition":
        frag = render_html.competition(graph, lang=args.lang)
        out = render_html.write(root, "competition", "html", frag, graph, lang=args.lang)
        print(_written_json(out, root))
        return 0

    # The dashboard is the HTML-only multi-dim view: one
    # page stacking the already-escaped roadmap + risk grid + competition fragments.
    # Like risk/competition it routes through the native "html" view_format (no
    # Mermaid wrapper, no sanitizer payload). HTML_ONLY_VIEWS guarantees fmt==html
    # here (a mermaid/ascii request was downgraded to html with a note above).
    if args.view == "dashboard":
        frag = render_html.dashboard(graph, lang=args.lang)
        out = render_html.write(root, "dashboard", "html", frag, graph, lang=args.lang)
        print(_written_json(out, root))
        return 0

    # heatmap (type×status) and persona (persona×PRD) are integer-count grids
    # Mermaid can't express; in HTML they used to fall back to an ASCII <pre> dump.
    # Render them HTML-native (real <table>s) like risk/competition. ASCII/mermaid
    # formats keep the existing render_ascii/_pre path (handled above / below).
    if args.view == "heatmap":
        frag = render_html.heatmap(graph, lang=args.lang)
        out = render_html.write(root, "heatmap", "html", frag, graph, lang=args.lang)
        print(_written_json(out, root))
        return 0

    if args.view == "persona":
        frag = render_html.persona(graph, lang=args.lang, filter_wont=args.filter_wont)
        out = render_html.write(root, "persona", "html", frag, graph, lang=args.lang)
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
