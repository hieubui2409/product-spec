"""templates — token substitution for INSTALL.md/install.sh/install.ps1 templates.

Unknown ``{{TOKEN}}`` references raise ``TemplateError`` (NOT silent). Token
format: ``{{UPPERCASE_NAME}}``.
"""

from __future__ import annotations

import re
from pathlib import Path

_TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]*)\}\}")


class TemplateError(Exception):
    """Raised when a template references an unknown token."""


def render(template_text: str, tokens: dict[str, str]) -> str:
    """Substitute every ``{{TOKEN}}`` in ``template_text`` with ``tokens[TOKEN]``.

    Unknown tokens raise ``TemplateError`` listing the missing names.
    """
    missing: set[str] = set()

    def _sub(m: re.Match) -> str:
        name = m.group(1)
        if name not in tokens:
            missing.add(name)
            return m.group(0)
        return str(tokens[name])

    result = _TOKEN_RE.sub(_sub, template_text)
    if missing:
        names = ", ".join(sorted(f"{{{{{n}}}}}" for n in missing))
        raise TemplateError(f"unknown template token(s): {names}")
    return result


def render_template(template_path: Path, tokens: dict[str, str]) -> bytes:
    """Read ``template_path`` and return rendered bytes (UTF-8 encoded).

    Raises ``TemplateError`` (not a bare ``OSError``) when the template file is
    missing or unreadable so callers only need to catch one exception type.
    """
    try:
        text = template_path.read_text(encoding="utf-8")
    except OSError as e:
        raise TemplateError(f"template not readable: {template_path}: {e}") from e
    return render(text, tokens).encode("utf-8")
