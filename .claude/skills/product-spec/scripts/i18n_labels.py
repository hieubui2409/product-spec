#!/usr/bin/env python3
"""
i18n_labels — minimal label map for visualization renderers (script layer only).

Scope is intentionally narrow: localize ONLY the 7-8 user-visible labels the
visualization-spec explicitly promises (`now/next/later` and MoSCoW). Prose
content (vision narrative, story descriptions, AC) is the LLM's job and uses
each artifact's `lang` frontmatter field, not this map.

Frontmatter keys and IDs always stay English regardless of `lang`.
"""

from typing import Dict


LABELS: Dict[str, Dict[str, str]] = {
    "en": {
        # horizon labels
        "now": "Now",
        "next": "Next",
        "later": "Later",
        # MoSCoW labels
        "must": "Must",
        "should": "Should",
        "could": "Could",
        "wont": "Won't",
        # tree label
        "product": "PRODUCT",
        # viewer UI chrome (board / explorer) — used by render_board / render_explorer
        "unassigned": "unassigned",
        "search": "Search…",
        "status": "Status",
        "moscow": "MoSCoW",
        "persona": "Persona",
        "layer": "Layer",
        "all": "All",
        "board": "Board",
        "explorer": "Explorer",
        "tree": "Tree",
        "tabs": "Flat tabs",
        "table": "Table",
        "no_results": "No matching artifacts",
        "ac_count": "AC",
        # artifact-type labels — viewer Layer facet + explorer Flat-tabs tab names
        "goal": "Goal",
        "prd": "PRD",
        "epic": "Epic",
        "story": "Story",
    },
    "vi": {
        "now": "Bây giờ",
        "next": "Tiếp",
        "later": "Sau",
        "must": "Bắt buộc",
        "should": "Nên",
        "could": "Có thể",
        "wont": "Không làm",
        "product": "SẢN PHẨM",
        "unassigned": "chưa gán",
        "search": "Tìm kiếm…",
        "status": "Trạng thái",
        "moscow": "MoSCoW",
        "persona": "Đối tượng",
        "layer": "Lớp",
        "all": "Tất cả",
        "board": "Bảng",
        "explorer": "Trình khám phá",
        "tree": "Cây",
        "tabs": "Thẻ phẳng",
        "table": "Bảng biểu",
        "no_results": "Không có hạng mục khớp",
        "ac_count": "Tiêu chí",
        "goal": "Mục tiêu",
        "prd": "PRD",
        "epic": "Epic",
        "story": "Story",
    },
}


def label(key: str, lang: str = "en") -> str:
    """Return the localized label for `key`. Falls back to English on miss."""
    table = LABELS.get(lang) or LABELS["en"]
    return table.get(key) or LABELS["en"].get(key) or key
