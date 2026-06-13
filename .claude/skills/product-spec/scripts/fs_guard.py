#!/usr/bin/env python3
"""
fs_guard — the shared soft-fence path-assert for every SCRIPT-driven disk write.

The skill only ever writes under `<root>/docs/product/`. This module is the one
home for that invariant. The fence covers the SCRIPT writers whose target path is
caller-influenced (the HTML visual writer, the export writer, the template
instantiator, the change-log month-file writer, and the memory-store writers): each
resolves its target through `assert_under_docs_product` BEFORE opening the file.

Writers whose target carries no caller-influenced path component are intentionally
un-fenced: the graph snapshot writer and the traceability-matrix writer (a
deterministic hard-coded leaf under an already-resolved `<root>`), and the in-place
`migrate_*` migrators — every migrator target is either a hard-coded `docs/product/`
leaf or a result of globbing `docs/product/` itself, so the glob root IS the fence
and there is no caller-influenced component left to contain.

Why a dedicated module (not extending the widely-imported encoding_utils): the
fence is imported by several writers that should depend on a tiny, single-purpose
unit; keeping it separate keeps ownership clean and the import graph shallow.

Honesty caveat: this is a SCRIPT-path guard only. It cannot — and is not meant to
— stop a raw LLM `Write`, nor an LLM composing a body directly to disk (e.g. the
impact report). Those are governed by the prose boundary rule + the advisory
fence scan (`check_fence.py`), not by this assert.

The check is resolve-then-contain: the target is resolved (collapsing `..`
segments and following symlinks on existing path components), then tested for
containment under the resolved `<root>/docs/product/`. This defeats `..`
traversal, sibling directories, prefix look-alikes (`docs/product-extra`), and
symlinks that point outside the fence — none of which a naive string `startswith`
would catch.
"""

from pathlib import Path


class FenceError(Exception):
    """Raised when a script-driven write would land outside docs/product/."""


def assert_under_docs_product(path, root) -> Path:
    """Return the resolved `path` if it is contained under `<root>/docs/product/`,
    else raise `FenceError` with a friendly, actionable message. Raises BEFORE any
    write so a blocked target never touches disk.

    `path` may be relative to `root` or absolute; both are resolved. The boundary
    directory itself counts as in-fence (it is not an escape)."""
    root = Path(root).resolve()
    fence = (root / "docs" / "product").resolve()

    target = Path(path)
    if not target.is_absolute():
        target = root / target
    # strict=False: the leaf (and intermediate dirs) may not exist yet — we still
    # collapse `..` and follow any symlinks that DO exist along the way.
    resolved = target.resolve(strict=False)

    if resolved != fence and not _is_within(resolved, fence):
        raise FenceError(
            f"refusing to write outside the spec boundary: {resolved} is not "
            f"under {fence}. The skill only writes under docs/product/."
        )
    return resolved


def _is_within(child: Path, parent: Path) -> bool:
    """True iff `child` is `parent` or a descendant of it. Uses path-segment
    containment (via is_relative_to) so a string prefix look-alike like
    `docs/product-extra` is correctly rejected — it shares the prefix string but
    not the path segments."""
    return child.is_relative_to(parent)


# Private-named alias kept for callers that reference `_assert_under_docs_product`
# (the memory-store writers). Same callable, one implementation.
_assert_under_docs_product = assert_under_docs_product
