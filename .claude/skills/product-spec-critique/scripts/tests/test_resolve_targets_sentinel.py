"""Target resolution must not leak the absent/malformed-id sentinels into the bundle.

A node whose `id:` is missing or non-string is indexed under spec_graph's internal
`<missing-id>`/`<invalid-id>` sentinel. Those are not real, selectable artifact ids — they
must never appear in `target_ids` (and thus never in `source_files` or the PO-facing
bundle). Synthetic graph only.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from critique_common import _resolve_targets, _import_psp  # noqa: E402


def test_resolve_targets_all_scope_drops_id_sentinels():
    spec_graph = _import_psp()[0]
    graph = {
        "nodes": [{"id": "PRD-X"}, {"id": "<missing-id>"}, {"id": "<invalid-id>"}],
        "edges": [],
    }
    ids, err = _resolve_targets(spec_graph, graph, "all")
    assert err is None
    assert ids == ["PRD-X"], "sentinels must not appear as selectable targets"


def test_resolve_targets_sentinel_is_not_a_valid_scope():
    spec_graph = _import_psp()[0]
    graph = {"nodes": [{"id": "PRD-X"}, {"id": "<missing-id>"}], "edges": []}
    ids, err = _resolve_targets(spec_graph, graph, "<missing-id>")
    assert ids == [] and err, "the sentinel must not resolve as a real scope id"
