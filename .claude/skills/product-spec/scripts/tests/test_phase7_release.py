"""Phase 7 — Docs & 2.0.0 release gates (TDD RED).

The final phase makes the v2 multi-dimensional schema authoritative everywhere
and bumps the skill to the major **2.0.0**. These are the *structural* pytest
cases the phase spec's "Tests First" table names:

  - test_version_consistency  (G-H2) — the skill version is 2.0.0 in SKILL.md
        frontmatter and NO skill doc still declares the old 1.1.0.
  - test_acme_shop_validate   (G-H4 / G-A1) — the worked example examples/acme-shop
        has been MIGRATED to v2 (carries real risk/time/competition data) AND
        still validates with 0 structural errors.
  - test_i18n_new_labels      (G-H1) — every new view/enum label localizes under
        --lang vi (VI is native-reviewed for natural wording).

Back-compat (G-A2, eval `backcompat-v1-spec`) is graded by the eval runner, not
here; the structural half — a v1 spec (no v2 fields) building + validating clean
— is already covered by the per-dimension "absence is clean" cases
(test_check_consistency.py / test_competition.py / test_risk_complete.py).

Assertion + fixture style mirrors test_competition.py / test_check_consistency.py:
sys.path-insert the scripts dir, import the real modules, assert the contract with
a failure message that names the missing v2 work (so RED fails for the intended
reason, never an import/crash).
"""

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import yaml  # noqa: E402  (ships with the skill venv, per CLAUDE.md)

from spec_graph import build_graph  # noqa: E402
from check_consistency import check as check_cons, _enrich_with_ac  # noqa: E402
from check_traceability import check as check_trace  # noqa: E402
import i18n_labels  # noqa: E402

SKILL_ROOT = SCRIPTS_DIR.parent                       # .../skills/product-spec
REPO_ROOT = SKILL_ROOT.parent.parent.parent           # repo root (cleanmatic-skills)
SKILL_MD = SKILL_ROOT / "SKILL.md"
REFERENCES_DIR = SKILL_ROOT / "references"
ACME_ROOT = SKILL_ROOT / "examples" / "acme-shop"

TARGET_VERSION = "2.1.0"
STALE_VERSION = "1.1.0"

# The five v2 frontmatter schema additions this major bump introduces. The
# migrated example must exercise them so the docs show v2 in action (Q42).
V2_NODE_FIELDS = ("risks", "target_date", "depends_on", "competitive_parity")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(path: Path) -> dict:
    """Parse the leading YAML frontmatter block of a markdown file."""
    text = _read(path)
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, f"{path} has no YAML frontmatter block"
    data = yaml.safe_load(m.group(1)) or {}
    assert isinstance(data, dict), f"{path} frontmatter is not a mapping"
    return data


# ---------------------------------------------------------------------------
# G-H2 — version 2.0.0 consistent across SKILL.md / CLAUDE.md / references.
# The authoritative skill version lives in SKILL.md frontmatter metadata.version;
# the test also guards that NO skill doc still carries the stale 1.1.0 string
# (example-artifact `version:` fields like 1.0.0/0.1.0 are NOT the skill version
# and are deliberately not matched).
# ---------------------------------------------------------------------------


def test_version_consistency():
    fm = _frontmatter(SKILL_MD)
    meta = fm.get("metadata") or {}
    declared = str(meta.get("version", "")).strip()
    assert declared == TARGET_VERSION, (
        f"SKILL.md metadata.version must be {TARGET_VERSION!r} for the major bump; "
        f"got {declared!r}"
    )

    # No skill doc may still advertise the old skill version.
    docs = [SKILL_MD, SKILL_ROOT / "README.md", SKILL_ROOT / "install.sh"]
    docs += sorted(REFERENCES_DIR.glob("*.md"))
    repo_claude = REPO_ROOT / "CLAUDE.md"
    if repo_claude.exists():
        docs.append(repo_claude)

    stale = []
    for d in docs:
        if not d.exists():
            continue
        for i, line in enumerate(_read(d).splitlines(), 1):
            if STALE_VERSION in line:
                stale.append(f"{d}:{i}: {line.strip()}")
    assert not stale, (
        f"stale skill version {STALE_VERSION!r} still present; bump to "
        f"{TARGET_VERSION!r}:\n" + "\n".join(stale)
    )


# ---------------------------------------------------------------------------
# G-H4 / G-A1 — examples/acme-shop migrated to v2 + green --validate.
# The example must (a) carry real v2 data across the new dimensions and
# (b) produce 0 structural errors from the consistency + traceability checks.
# ---------------------------------------------------------------------------


def _acme_graph():
    g = build_graph(ACME_ROOT)
    _enrich_with_ac(g, ACME_ROOT)
    return g


def test_acme_shop_validate():
    assert ACME_ROOT.is_dir(), f"missing worked example at {ACME_ROOT}"
    g = _acme_graph()

    # (a) migrated to v2: the example must exercise the new dimensions, not just
    #     remain a valid v1 spec. competitors live at the BRD (DRY home).
    competitors = g.get("competitors") or []
    assert competitors, (
        "acme-shop must declare competitors at the BRD (v2 COMPETITION dimension); "
        "graph['competitors'] is empty — example not migrated"
    )

    present = {
        field
        for n in g["nodes"]
        for field in V2_NODE_FIELDS
        if n.get(field)
    }
    missing = [f for f in V2_NODE_FIELDS if f not in present]
    assert not missing, (
        "acme-shop must carry these v2 node fields somewhere in the spec "
        f"(migrated example); missing: {missing}. present: {sorted(present)}"
    )

    # (b) still validates clean — 0 structural errors (G-A1 / G-H4).
    findings = check_cons(g) + check_trace(g)
    errors = [f for f in findings if f.get("severity") == "error"]
    assert errors == [], (
        "migrated acme-shop must validate with 0 structural errors; got:\n"
        + "\n".join(f"{f.get('check')} [{f.get('artifact_id')}]: {f.get('detail')}" for f in errors)
    )


# ---------------------------------------------------------------------------
# G-H1 — bilingual EN/VI labels for all new enums/views.
# Every new view name and dimension enum must localize under --lang vi.
# ---------------------------------------------------------------------------


def test_i18n_new_labels():
    # New view names introduced by the multi-dim work.
    new_views = ("time", "competition", "dashboard", "risk")
    # New dimension enum labels (competition parity + threat tiers).
    new_enums = (
        "parity_ahead", "parity_parity", "parity_behind", "parity_none",
        "threat_low", "threat_med", "threat_high",
    )

    # Every key must exist in BOTH locale tables (no silent EN fallback for a
    # new label under --lang vi).
    en_keys = set(i18n_labels.LABELS["en"])
    vi_keys = set(i18n_labels.LABELS["vi"])
    for key in new_views + new_enums:
        assert key in en_keys, f"i18n label key {key!r} missing from the EN table"
        assert key in vi_keys, f"i18n label key {key!r} missing from the VI table"

    # The VI rendering must differ from EN (i.e. actually be translated, not an
    # untranslated passthrough) for the new VIEW names.
    untranslated = [
        v for v in new_views
        if i18n_labels.label(v, "vi") == i18n_labels.label(v, "en")
    ]
    assert not untranslated, (
        "these new view labels are not localized under --lang vi (VI == EN "
        f"passthrough): {untranslated}"
    )
