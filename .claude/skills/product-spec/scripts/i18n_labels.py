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


# Programmatic native-review-pending caveat (bilingual convention). The VI
# locale ships best-effort; a native speaker has not yet reviewed phrasing.
# Renderers surface this once when --lang vi is active so the PO knows the VI
# labels are provisional — it is a *consumable* string here, not just an inline
# code comment, so the board/explorer/visualization headers can show it.
NATIVE_REVIEW_NOTE = (
    "VI labels ship best-effort — native-speaker review of phrasing is pending."
)


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
        "horizon": "Horizon",
        "board": "Board",
        "explorer": "Explorer",
        "export": "Spec Export",
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
        # TIME view (gantt title + ASCII header)
        "roadmap_deadlines": "Roadmap & Deadlines",
        "no_date": "no date",
        # COMPETITION view — parity-matrix cell verdicts + threat-heatmap tiers.
        # EN labels are the enum identity (the matrix renders the raw enum word);
        # VI translates. Keys are distinct from the risk tiers to avoid clashes.
        "competition": "Competition",
        "parity_ahead": "ahead",
        "parity_parity": "parity",
        "parity_behind": "behind",
        "parity_none": "none",
        "threat_low": "low",
        "threat_med": "med",
        "threat_high": "high",
        # Multi-dim impact view names (page titles / nav labels). Distinct from
        # the dimension enums above so each localizes independently.
        "time": "Time",
        "risk": "Risk",
        "dashboard": "Impact Dashboard",
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
        "horizon": "Mốc thời gian",
        "board": "Bảng",
        "explorer": "Trình khám phá",
        "export": "Xuất đặc tả",
        "tree": "Cây",
        "tabs": "Thẻ phẳng",
        "table": "Bảng biểu",
        "no_results": "Không có hạng mục khớp",
        "ac_count": "Tiêu chí",
        "goal": "Mục tiêu",
        "prd": "PRD",
        "epic": "Epic",
        "story": "Story",
        # TIME view — VI ships best-effort; native-speaker review of phrasing pending.
        "roadmap_deadlines": "Lộ trình & Hạn chót",
        "no_date": "chưa có hạn",
        # COMPETITION view — VI ships best-effort; native-speaker review pending.
        "competition": "Cạnh tranh",
        "parity_ahead": "dẫn trước",
        "parity_parity": "ngang bằng",
        "parity_behind": "thua kém",
        "parity_none": "không có",
        "threat_low": "thấp",
        "threat_med": "trung bình",
        "threat_high": "cao",
        # Multi-dim impact view names — VI ships best-effort; native review pending.
        "time": "Thời gian",
        "risk": "Rủi ro",
        "dashboard": "Bảng tổng quan tác động",
    },
}


def label(key: str, lang: str = "en") -> str:
    """Return the localized label for `key`. Falls back to English on miss."""
    table = LABELS.get(lang) or LABELS["en"]
    return table.get(key) or LABELS["en"].get(key) or key
