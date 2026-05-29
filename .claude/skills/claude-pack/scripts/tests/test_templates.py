"""test_templates — unknown {{TOKEN}} raises TemplateError."""

from __future__ import annotations

import pytest

from pack.templates import TemplateError, render


def test_render_known_token():
    out = render("hello {{NAME}}", {"NAME": "world"})
    assert out == "hello world"


def test_render_multiple_tokens():
    out = render("v{{VERSION}} built {{BUILT_AT}}",
                 {"VERSION": "1.0", "BUILT_AT": "2026-05-29"})
    assert out == "v1.0 built 2026-05-29"


def test_render_unknown_token_raises():
    """unknown token raises TemplateError."""
    with pytest.raises(TemplateError) as exc:
        render("hello {{UNKNOWN}}", {"VERSION": "1.0"})
    assert "UNKNOWN" in str(exc.value)


def test_render_lists_all_missing_tokens():
    with pytest.raises(TemplateError) as exc:
        render("{{A}} {{B}} {{C}}", {})
    msg = str(exc.value)
    for token in ("A", "B", "C"):
        assert token in msg


def test_render_idempotent_when_no_tokens():
    plain = "no tokens here at all"
    assert render(plain, {}) == plain
