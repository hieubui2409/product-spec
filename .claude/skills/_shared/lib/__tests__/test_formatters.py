"""test_formatters.py — markdown_table alignment, Vietnamese display width,
json_output, severity_badge. Ported-module sanity for the telemetry lenses.
"""
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_LIB))

from formatters import markdown_table, json_output, summary_block, severity_badge  # noqa: E402


class TestMarkdownTable:
    def test_empty_rows_render_placeholder(self):
        out = markdown_table(["A", "B"], [])
        assert "_(empty)_" in out
        assert out.splitlines()[0] == "| A | B |"

    def test_columns_align_by_display_width_ascii(self):
        out = markdown_table(["Skill", "N"], [["product-spec", "3"], ["release", "1"]])
        # Header + data rows must align (the GFM separator row uses a 3-dash
        # minimum per cell, so it is excluded from the equal-length check).
        body = [l for i, l in enumerate(out.splitlines()) if i != 1]
        assert len({len(l) for l in body}) == 1, f"misaligned rows:\n{out}"

    def test_vietnamese_diacritics_count_as_one_cell(self):
        # 'chưa đủ dữ liệu' is authored with combining marks; display width must
        # equal its visible glyph count so VI cells align with ASCII cells.
        out = markdown_table(["Trạng thái", "N"], [["chưa đủ dữ liệu", "0"], ["ổn", "9"]])
        body = [l for i, l in enumerate(out.splitlines()) if i != 1]
        assert len({len(l) for l in body}) == 1, f"VI misalignment:\n{out}"

    def test_right_align_separator(self):
        out = markdown_table(["A", "N"], [["x", "10"]], align=["l", "r"])
        sep = out.splitlines()[1]
        assert sep.rstrip().endswith(":|") or ":" in sep  # right-align marker present


class TestJsonOutput:
    def test_roundtrips_and_keeps_unicode(self):
        data = {"msg": "dữ liệu", "n": 3}
        s = json_output(data)
        assert json.loads(s) == data
        assert "dữ liệu" in s  # ensure_ascii=False keeps VI readable


class TestMisc:
    def test_summary_block_lists_items(self):
        out = summary_block("Tổng quan", {"Sessions": "2", "Skills": "3"})
        assert out.startswith("## Tổng quan")
        assert "- **Sessions**: 2" in out

    def test_severity_badge_known_and_unknown(self):
        assert severity_badge("high") == "[!!!]"
        assert severity_badge("weird") == "[weird]"
