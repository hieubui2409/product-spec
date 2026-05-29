"""conftest — shared pytest fixtures for cleanmatic:claude-pack tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


@pytest.fixture(autouse=True)
def _strip_source_date_epoch(monkeypatch):
    """Per-test: clear SOURCE_DATE_EPOCH to prevent leakage from host CI."""
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def sample_skill_src(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample-skill"


def _make_skill(skill_dir: Path, name: str = "sample-skill", version: str = "0.1.0") -> None:
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\n"
        f"name: cleanmatic:{name}\n"
        f"description: \"Synthetic skill for golden tests.\"\n"
        f"metadata:\n  version: \"{version}\"\n"
        f"---\n\n"
        f"# {name}\n\n"
        f"Synthetic minimal skill body.\n",
        encoding="utf-8",
    )
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "scripts" / "helper.py").write_text(
        "def hello() -> str:\n    return 'hi'\n", encoding="utf-8")
    (skill_dir / "references").mkdir(exist_ok=True)
    (skill_dir / "references" / "spec.md").write_text(
        "# spec\n\nReference doc.\n", encoding="utf-8")


@pytest.fixture
def tmp_root(tmp_path: Path) -> Path:
    """Fake repo with a minimal .claude/ + sample-skill."""
    claude = tmp_path / ".claude"
    (claude / "agents").mkdir(parents=True)
    (claude / "rules").mkdir(parents=True)
    (claude / "hooks").mkdir(parents=True)
    (claude / "skills").mkdir(parents=True)
    (claude / "agents" / "planner.md").write_text("# planner\n", encoding="utf-8")
    (claude / "rules" / "primary-workflow.md").write_text("# rules\n", encoding="utf-8")
    _make_skill(claude / "skills" / "sample-skill")
    return tmp_path


@pytest.fixture
def dirty_claude(tmp_path: Path) -> Path:
    """Repo with secrets + .git + caches for safety-filter tests."""
    claude = tmp_path / ".claude"
    (claude / "skills" / "demo").mkdir(parents=True)
    (claude / "skills" / "demo" / "SKILL.md").write_text("# demo\n", encoding="utf-8")
    (claude / ".env").write_text("SECRET=x\n", encoding="utf-8")
    (claude / "settings.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (claude / "skills" / "demo" / "__pycache__").mkdir()
    (claude / "skills" / "demo" / "__pycache__" / "x.pyc").write_text("x", encoding="utf-8")
    return tmp_path


@pytest.fixture
def skill_root() -> Path:
    """Resolve the actual claude-pack skill root (for asset templates)."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def assets_dir(skill_root: Path) -> Path:
    return skill_root / "assets" / "templates"
