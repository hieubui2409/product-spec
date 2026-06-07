# Skill Packaging Contract: SKILL.md, A4 Gate, Bundle Selection & .gitignore

## Executive Summary

To keep `cleanmatic:telemetry` (local PO tooling) out of the bundle while keeping it tracked in git:

1. **Create** `.claude/skills/telemetry/SKILL.md` with required metadata (see Section 1)
2. **Exclude from A4 gate**: Add `telemetry` to the `DEFAULT_SKILLS` tuple in `verify_skill_versions.py` (skip the synced list)
3. **Exclude from bundle**: Do NOT list `telemetry` in `.claude/pack.manifest.yaml` `skills:` array
4. **Track in git**: Add `!/.claude/skills/telemetry/**` to `.gitignore` (see Section 4)
5. **Test exclusion**: Extend `test_bundle_excludes_telemetry.py` to verify the skill dir is never bundled (see Section 5)

---

## 1. SKILL.md Required Metadata Keys

**Source:** `.claude/skills/product-spec/SKILL.md:1–12`, `.claude/skills/product-spec-critique/SKILL.md:1–12`, `.claude/skills/release/SKILL.md:1–12`

All three skills follow the same frontmatter schema (YAML before first `---` boundary):

```yaml
---
name: cleanmatic:<slug>                    # REQUIRED. Format: cleanmatic:kebab-case (e.g., cleanmatic:telemetry)
description: "..."                         # REQUIRED. String (max ~200 chars). Purpose of the skill.
user-invocable: true                       # REQUIRED. Boolean. Whether end-users can invoke via /ck:slug
when_to_use: "..."                         # REQUIRED. String. When to invoke; UI context for /ck:find-skills
category: <category>                       # REQUIRED. One of: product | release | observability | (others)
keywords: [ ... ]                          # REQUIRED. Array of strings. Search tags.
argument-hint: "[--flag] [target]"         # OPTIONAL. Usage hint for --help output.
metadata:
  author: cleanmatic                       # REQUIRED. Fixed: "cleanmatic"
  version: "X.Y.Z"                         # REQUIRED. Semver. Verified by verify_skill_versions.py
---
```

**Key constraints:**
- `name:` MUST match the pattern `cleanmatic:<slug>` where `<slug>` is the directory name under `.claude/skills/`
- `metadata.version:` MUST be valid semver (`\d+\.\d+\.\d+`) with no pre-release or build metadata (regex: `^(\d+)\.(\d+)\.(\d+)$`)
- All fields are case-sensitive and YAML-parsed (not free-form strings)

**For telemetry:** Example frontmatter:
```yaml
---
name: cleanmatic:telemetry
description: "Local observability tooling: hook registry, eval harness, telemetry sinks. PO-only, not shipped."
user-invocable: true
when_to_use: "Invoke when instrumenting a skill or collecting evaluation metrics locally."
category: observability
keywords: [ observability, telemetry, hooks, evals, metrics, local ]
metadata:
  author: cleanmatic
  version: "1.0.0"
---
```

---

## 2. A4 Version-Sync Gate: Exact Assertions

**Source:** `.claude/skills/release/scripts/verify_skill_versions.py:21, 97` and `.claude/skills/release/scripts/tests/test_version_sync.py:27, 79–85`

### 2a. Two Skill Tuples

**verify_skill_versions.py line 21:**
```python
DEFAULT_SKILLS = ("product-spec", "product-spec-critique", "release")
```
Used in `verify()` (line 65–83) to scan each skill's `SKILL.md` for `metadata.version` presence + semver format **only**. No version equality check.

**test_version_sync.py line 27:**
```python
VERSION_SYNCED_SKILLS = ("product-spec", "product-spec-critique", "release")
```
Used in `test_skill_version_matches_changelog_top()` (line 79–85) to assert each skill's `SKILL.md metadata.version == top released heading in that skill's CHANGELOG.md`.

### 2b. Gate Assertions Verbatim

**Primary gate (PR/CI blocking):** `test_version_sync.py:79–85`
```python
@pytest.mark.bug_class
@pytest.mark.parametrize("skill", VERSION_SYNCED_SKILLS)
def test_skill_version_matches_changelog_top(skill):
    skill_version = _skill_version(skill)
    top = changelog_top_version(SKILLS_DIR / skill / "CHANGELOG.md")
    assert skill_version == top, (
        f"{skill}: SKILL.md metadata.version {skill_version!r} != CHANGELOG top {top!r} — "
        f"bump both together (version + a new `## [{skill_version}]` heading)."
    )
```

**Secondary gate (bundle-level):** `test_version_sync.py:89–101`
```python
@pytest.mark.bug_class
def test_bundle_changelog_top_matches_manifest_version():
    root_changelog = REPO_ROOT / "CHANGELOG.md"
    manifest = yaml.safe_load((REPO_ROOT / ".claude" / "pack.manifest.yaml").read_text())
    manifest_version = str(manifest["version"])
    top = changelog_top_version(root_changelog)
    assert manifest_version == top
```

### 2c. Release Skill Handling

**Key finding:** The `release` skill is **included** in `VERSION_SYNCED_SKILLS` (line 27). Test comment line 8 states: "The release skill is no longer special-cased — its skill changelog tracks the skill version like the other two."

Prior to v1.0.0, `release` was excluded from the synced list (implied by the comment). Now it's treated identically to the other two. Each has a `CHANGELOG.md` under `.claude/skills/<skill>/CHANGELOG.md` that must stay in sync with `SKILL.md metadata.version`.

### 2d. Recommendation for Telemetry

**Add `telemetry` to `DEFAULT_SKILLS` ONLY** (verify_skill_versions.py line 21):
```python
DEFAULT_SKILLS = ("product-spec", "product-spec-critique", "release", "telemetry")
```

This ensures the skill's `SKILL.md metadata.version` is present and valid semver at build-time (loose check).

**Do NOT add `telemetry` to `VERSION_SYNCED_SKILLS`** (test_version_sync.py line 27):
```python
VERSION_SYNCED_SKILLS = ("product-spec", "product-spec-critique", "release")  # telemetry omitted
```

This exempts telemetry from the PR gate that requires `SKILL.md version == CHANGELOG.md top`. For a local-only skill, version drift is acceptable (test_bundle_excludes_telemetry.py enforces bundling exclusion, not version sync).

**Rationale:** The A4 gate is an **identity** gate (proving each distributed skill is versioned), not a **completeness** gate. Local skills don't ship, so the version-sync invariant doesn't apply. If telemetry is ever shipped, move it to `VERSION_SYNCED_SKILLS`.

---

## 3. Bundle Selection Mechanism: Auto-Ship vs Explicit

**Source:** `.claude/pack.manifest.yaml:1–37`, `.claude/skills/release/scripts/pack/selection.py:19–138`

### 3a. Selection Is Explicit (Not Auto-Ship)

**pack.manifest.yaml lines 7–10:**
```yaml
skills:
- product-spec
- release
- product-spec-critique
```

Skills are bundled **only if listed** in the `skills:` array. The selection resolver (`selection.py:35–36`) iterates this array directly:
```python
for slug in manifest.get("skills", []):
    _walk_dir(claude_dir / "skills" / slug, f".claude/skills/{slug}")
```

**No auto-discovery via rglob:** A new skill directory `.claude/skills/telemetry/` is **not** automatically discovered or included. It must be explicitly added to the manifest.

### 3b. What Keeps a Skill Out

A skill not listed in `manifest.get("skills", [])` is never walked and never bundled. This is the **primary** exclusion mechanism (verified by test_bundle_excludes_telemetry.py line 46–51, "by construction").

No manifest entry = no tarball member. The skill can exist and be tracked in git; the pack simply ignores it.

### 3c. Action for Telemetry

**Do not add `telemetry` to `.claude/pack.manifest.yaml` `skills:` array.**

Verify the omission by running:
```bash
grep -A 5 "^skills:" /home/hieubt/Documents/cleanmatic-skills/.claude/pack.manifest.yaml
```

Should list only `product-spec`, `release`, and `product-spec-critique`. If telemetry appears, it will be bundled.

---

## 4. .gitignore Selective Re-Include Idiom

**Source:** `.gitignore:73–109`

### 4a. Current Pattern for Tracked Skills

```gitignore
# line 76–85: Ignore all .claude/skills/ except the three shipped ones
/.claude/*
!/.claude/rules/
!/.claude/skills/
/.claude/skills/*
!/.claude/skills/product-spec/
!/.claude/skills/product-spec/**
!/.claude/skills/release/
!/.claude/skills/release/**
!/.claude/skills/product-spec-critique/
!/.claude/skills/product-spec-critique/**
```

**Pattern:** 
1. `/.claude/*` blocks all top-level items under `.claude/`
2. `!/.claude/skills/` re-includes the `skills/` directory itself (not its contents yet)
3. `/.claude/skills/*` re-blocks all skill directories
4. `!/.claude/skills/<skill>/` + `!/.claude/skills/<skill>/**` re-includes specific skills and all files within

This pattern is case-sensitive and file-granular. A new skill `.claude/skills/telemetry/` is caught by the `/.claude/skills/*` rule and must be explicitly re-included.

### 4b. Required Addition for Telemetry

Add after line 85 (after product-spec-critique) or at the end of the skill block:
```gitignore
!/.claude/skills/telemetry/
!/.claude/skills/telemetry/**
```

**Exact lines to add (maintaining the block structure):**
```gitignore
!/.claude/skills/telemetry/
!/.claude/skills/telemetry/**
```

**Verification:** After adding, run:
```bash
cd /home/hieubt/Documents/cleanmatic-skills
git check-ignore -v .claude/skills/telemetry/SKILL.md
# Should output nothing (file is NOT ignored)
git status --porcelain .claude/skills/telemetry/
# Should list new files with status "??" (untracked, not ignored)
```

### 4c. Why Two Lines

- `!/.claude/skills/telemetry/` : Re-includes the directory itself (allows walking into it)
- `!/.claude/skills/telemetry/**` : Re-includes all files recursively within it (allows individual files to be staged)

Git's ignore semantics require both: the directory re-include is a gate; the `/**` glob is the actual file catch-all.

### 4d. The Gotcha: File Creation After .gitignore Edit

The comment at line 74 states: "keep them ignored" (referring to `.claude/hooks/*.cjs`). Below it:
```gitignore
!/.claude/hooks/
/.claude/hooks/*
!/.claude/hooks/*.py
```

**Gotcha documented in repo**: If `/.claude/skills/telemetry/` directory exists and matches the old rule `/.claude/skills/*`, **creating a new file inside does not automatically become tracked** even after the re-include is added. Git caches the "this dir is ignored" decision. Work around by:
```bash
git add -f .claude/skills/telemetry/SKILL.md
# or
git add -A .claude/skills/telemetry/
```

Force-add the first file, then subsequent files in the directory will be tracked normally.

---

## 5. Bundle Exclusion Test Pattern

**Source:** `.claude/skills/release/scripts/tests/test_bundle_excludes_telemetry.py:1–75`

### 5a. Current Test Structure

The test has two independent assertions:

**Layer 1 (by construction, deterministic):** Line 46–51
```python
@pytest.mark.bug_class
def test_selection_excludes_telemetry_by_construction():
    arcs = _arcs()  # resolve_selection(manifest, root)
    leaks = [a for a in arcs if "/.claude/telemetry/" in f"/{a}" or a.startswith(".claude/telemetry/")]
    assert not leaks, f"telemetry sink path leaked into bundle file set: {leaks}"
    hook_leaks = [a for a in arcs if Path(a).name in TELEMETRY_HOOK_BASENAMES]
    assert not hook_leaks, f"CM-local telemetry hook leaked into bundle file set: {hook_leaks}"
```

Calls `resolve_selection()` directly on the manifest, verifies no `.claude/telemetry/` or telemetry hooks appear.

**Layer 2 (regression sentinel, real tarball):** Line 55–74
```python
@pytest.mark.bug_class
def test_real_tarball_excludes_telemetry(tmp_path):
    # Run `python -m pack` (real build)
    # Extract tarball, scan members for "/.claude/telemetry/" or hook names
    # Assert none found and tarball is non-empty (vacuous-pass guard)
```

### 5b. To Test Telemetry Skill Exclusion

**Option A: Extend existing test** (minimal change):

Modify `test_selection_excludes_telemetry_by_construction()` to also check that the **skill directory itself** is not bundled:

```python
@pytest.mark.bug_class
def test_selection_excludes_telemetry_by_construction():
    arcs = _arcs()
    leaks = [a for a in arcs if "/.claude/telemetry/" in f"/{a}" or a.startswith(".claude/telemetry/")]
    assert not leaks, f"telemetry sink path leaked into bundle file set: {leaks}"
    hook_leaks = [a for a in arcs if Path(a).name in TELEMETRY_HOOK_BASENAMES]
    assert not hook_leaks, f"CM-local telemetry hook leaked into bundle file set: {hook_leaks}"
    # NEW: Verify the telemetry skill directory is not in manifest.skills
    skill_leaks = [a for a in arcs if a.startswith(".claude/skills/telemetry/")]
    assert not skill_leaks, f"telemetry skill directory leaked into bundle: {skill_leaks}"
```

**Option B: Standalone test** (clearer intent):

```python
@pytest.mark.bug_class
def test_telemetry_skill_not_in_manifest():
    """Verify cleanmatic:telemetry is intentionally omitted from pack.manifest.yaml skills: list."""
    manifest = manifest_loader.load(MANIFEST)
    bundled_skills = manifest.get("skills", [])
    assert "telemetry" not in bundled_skills, (
        f"telemetry skill should NOT be in manifest.skills (local-only tooling). "
        f"Found: {bundled_skills}"
    )
```

**Recommendation:** Use Option B. It's explicit, fast (no resolve_selection call), and documents the intent ("local-only, intentionally omitted").

---

## 6. Summary: Configuration Checklist

| Component | Action | File | Status |
|-----------|--------|------|--------|
| **SKILL.md** | Create with required metadata | `.claude/skills/telemetry/SKILL.md` | New |
| **Metadata version** | Valid semver in `metadata.version:` | `.claude/skills/telemetry/SKILL.md` | New |
| **CHANGELOG.md** | Create `.claude/skills/telemetry/CHANGELOG.md` | `.claude/skills/telemetry/CHANGELOG.md` | New (optional but recommended) |
| **A4 gate (verify)** | Add `telemetry` to `DEFAULT_SKILLS` tuple | `.claude/skills/release/scripts/verify_skill_versions.py:21` | Edit (add "telemetry" to tuple) |
| **A4 gate (synced)** | **Do NOT add** to `VERSION_SYNCED_SKILLS` tuple | `.claude/skills/release/scripts/tests/test_version_sync.py:27` | Leave as-is |
| **Bundle manifest** | **Do NOT add** `telemetry` to `skills:` array | `.claude/pack.manifest.yaml:7–10` | Leave as-is |
| **.gitignore** | Add re-include rules for the skill | `.gitignore:86+` | Edit (add 2 lines) |
| **Bundle test** | Add or extend test to verify skill exclusion | `.claude/skills/release/scripts/tests/test_bundle_excludes_telemetry.py` | Edit (add 1 assertion or new test) |

---

## 7. File Paths & Line Citations

| Reference | File | Lines |
|-----------|------|-------|
| SKILL.md schema (product-spec example) | `.claude/skills/product-spec/SKILL.md` | 1–12 |
| SKILL.md schema (release example) | `.claude/skills/release/SKILL.md` | 1–12 |
| Verify script: DEFAULT_SKILLS | `.claude/skills/release/scripts/verify_skill_versions.py` | 21 |
| Verify script: verify() function | `.claude/skills/release/scripts/verify_skill_versions.py` | 65–83 |
| Test: VERSION_SYNCED_SKILLS | `.claude/skills/release/scripts/tests/test_version_sync.py` | 27 |
| Test: version-sync assertion | `.claude/skills/release/scripts/tests/test_version_sync.py` | 79–85 |
| Test: bundle-level assertion | `.claude/skills/release/scripts/tests/test_version_sync.py` | 89–101 |
| Bundle manifest | `.claude/pack.manifest.yaml` | 1–37 |
| Selection resolver: skills loop | `.claude/skills/release/scripts/pack/selection.py` | 35–36 |
| Selection resolver: full function | `.claude/skills/release/scripts/pack/selection.py` | 19–138 |
| .gitignore: skill block | `.gitignore` | 73–85 |
| .gitignore: telemetry sinks | `.gitignore` | 159 |
| .gitignore: _shared re-include | `.gitignore` | 170–175 |
| Bundle exclusion test: construction | `.claude/skills/release/scripts/tests/test_bundle_excludes_telemetry.py` | 46–51 |
| Bundle exclusion test: real tarball | `.claude/skills/release/scripts/tests/test_bundle_excludes_telemetry.py` | 55–74 |

---

## Unresolved Questions

1. Should `.claude/skills/telemetry/CHANGELOG.md` be created and kept in sync with `metadata.version:`, even though the skill is never shipped? (Recommendation: yes, for consistency; no, to avoid maintenance overhead. Ask PO.)
2. Should telemetry hooks be co-located under `.claude/skills/telemetry/` or remain in `.claude/hooks/`? Current layout puts telemetry hooks in `.claude/hooks/` and they're individually re-included by the `!/.claude/hooks/*.py` rule. Consolidating might improve organization.
3. Should `_include_shared` in the manifest be used to include telemetry-related shared libs (`.claude/skills/_shared/lib/telemetry_paths.py`, etc.) when needed during development, or do they stay external to the bundle?
