# Prior Art Research: `.claude` Skill Distribution & Packaging

**Researcher**: cleanmatic researcher agent  
**Date**: 2026-05-29  
**Scope**: Official Anthropic practices, community registries, adjacent ecosystems, existing skill overlap  
**Status**: COMPLETE

---

## Q1: Anthropic / Claude Code Official Distribution

### Official Structure
**Source:** [Extend Claude with skills — code.claude.com](https://code.claude.com/docs/en/skills)

- **Core format**: Directory + `SKILL.md` (YAML frontmatter + markdown instructions)
- **Official locations**:
  - Personal: `~/.claude/skills/<skill-name>/SKILL.md`
  - Project: `.claude/skills/<skill-name>/SKILL.md`
  - Plugin: `<plugin>/skills/<skill-name>/SKILL.md`
  - Enterprise: managed settings (organization-wide)

- **Directory structure (standardized)**:
  ```
  my-skill/
  ├── SKILL.md (required)
  ├── supporting-files/ (optional)
  ├── examples/ (optional)
  └── scripts/ (optional)
  ```

- **No official registry**: Anthropic does NOT maintain a centralized skill registry. Distribution is through: version control (commit to `.claude/`), plugins (package directory with `skills/` subdirectory), or managed settings deployments.

- **YAML frontmatter fields** (optional, but `description` recommended):
  - `name`, `description`, `when_to_use`, `argument-hint`
  - `disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`
  - `model`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell`

- **Plugins are the official distribution mechanism**:
  - Plugin skills use namespace: `plugin-name:skill-name`
  - Plugins packaged as directories with `SKILL.md` at root (for plugin command) or under `skills/` (for individual skills)
  - Plugins support: skills + commands + hooks + agents + rules

### No CLI for skill install/uninstall
**Source:** [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills)

Claude Code does NOT ship `claude code` subcommands for `skill install`, `skill uninstall`, or `skill list`. Skills are discovered via:
1. **File system discovery**: walking `.claude/skills/` directories at startup
2. **Live change detection**: edits to skill files take effect within current session
3. **Automatic discovery**: from parent directories and monorepo nested directories

**Implication**: Skill distribution is manual copy/git-clone/plugin-installation today.

---

## Q2: Community Registries & Distribution

Multiple community-driven registries exist; no single canonical source.

### Active Registries
**Sources:**
- [JSONbored/awesome-claude](https://github.com/JSONbored/awesome-claude)
- [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)
- [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills)
- [majiayu000/claude-skill-registry](https://github.com/majiayu000/claude-skill-registry)
- [ClaudSkills](https://claudskills.com/)

| Registry | Format | Install Method | Scale |
|----------|--------|-----------------|-------|
| HeyClaude (awesome-claude) | SKILL.md catalog | Browse + manual copy/git-clone | Curated |
| Antigravity Awesome Skills | GitHub library + installer CLI | `antigravity install --skill <name>` | 1,400+ skills |
| Claude Skill Registry | Web UI searchable index | Browse + manual | 73,000+ GitHub SKILL.md files |
| TravisVN/awesome-claude-skills | Curated GitHub list | Manual git-clone per entry | ~200 curated |

**Distribution pattern**: No `.tar.gz` standard yet. All registry entries link to GitHub repos or raw SKILL.md files. Users manually copy/clone.

---

## Q3: Adjacent Ecosystems

### oh-my-zsh
**Source:** [ohmyzsh/ohmyzsh GitHub](https://github.com/ohmyzsh/ohmyzsh)

- **Distribution**: Monorepo at GitHub, not tar-based. Users clone full monorepo or use plugins from `~/.oh-my-zsh/plugins/`.
- **Plugin structure**: Single `.zsh` file per plugin (e.g., `plugins/git/git.plugin.zsh`).
- **Install**: No native tar distribution. 3rd-party plugin managers (antigen, zplug) support tar, but oh-my-zsh itself uses git-clone.
- **Configuration**: No `.zcignore`; plugins auto-loaded from theme list in `.zshrc`.
- **No opt-in cherry-picking**: Full monorepo clone, then enable in config.

### VS Code VSIX Extensions
**Source:** [code.visualstudio.com/api/working-with-extensions/publishing-extension](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)

- **Format**: `.vsix` (ZIP archive + OPC standard structure)
- **Tool**: `vsce` CLI (`npm i -g @vscode/vsce`)
- **Packaging**: `vsce package` → `extension-name-version.vsix`
- **Versioning**: Semantic in `package.json`; vsce auto-generates `extension-name-version.vsix`
- **Distribution**: VS Code Marketplace (central) OR GitHub releases (.vsix file)
- **Install side-effects**: Managed by declarative `package.json` scripts (install, uninstall hooks)
- **Opt-in cherry-picking**: Each extension installed independently; no monorepo bundling.

### Vim Plugin Managers (vim-plug, dein.vim)
**Source:** [vim-plug tutorial](https://github.com/junegunn/vim-plug/wiki/tutorial), [dein.vim](https://github.com/Shougo/dein.vim)

- **Historical tar distribution**: Pre-plugin-manager era used tarballs (users extracted to `~/.vim`); now obsolete.
- **Modern pattern**: Plugin managers clone from GitHub (or local dir) into separate per-plugin directory (e.g., `~/.vim/plugged/plugin-name/`).
- **vim-plug structure**: Minimal; just requires plugin entry point file + optional `plugin/`, `autoload/` subdirs.
- **No tar bundling**: vim-plug and dein.vim both use git repos, not tar distributions.

### npm pack
**Source:** [npm docs](https://docs.npmjs.com/cli/v11/configuring-npm/package-json)

- **Tarball naming**: `package-name-version.tgz` (semantic versioning in package.json)
- **File control**: `.npmignore` (or `.gitignore` if .npmignore missing) + `files` field in package.json
- **Precedence**: `files` field overrides `.npmignore` (inclusions always win)
- **Root directory**: Unversioned. When extracted, tarball contains flat structure (no `package-name-version/` wrapper).
- **Checksums**: Optional `.sha256` sidecar file not standard; npm registry computes SHAs server-side.
- **Install side-effects**: Declarative `scripts` in package.json (preinstall, postinstall, install, postuninstall).

### Homebrew Formulas
**Source:** [Formula Cookbook — brew.sh](https://docs.brew.sh/Formula-Cookbook)

- **Tarball structure**: Versioned root directory expected: `package-version/` (auto-detected from URL if possible)
- **Version detection**: Auto-inferred from URL (e.g., `https://github.com/user/project/archive/v1.2.3.tar.gz` → version = `1.2.3`)
- **Formula revisions**: Separate concept from tarball version; recorded in Git history of formula repo, not in tarball.
- **Checksums**: SHA256 declared in formula metadata (manually computed, not auto-generated).
- **No ignore file**: Formulas control extracted contents via `install` function, not via `.homebrewignore`.

### Dotfiles (chezmoi)
**Source:** [chezmoi.io docs](https://www.chezmoi.io/)

- **Archive support**: `chezmoi archive --output=dotfiles.tar.gz` (default format is tar)
- **Root directory**: Not versioned; flat extract to `$HOME` (chezmoi manages path expansion via filename prefixes like `dot_` for `.`).
- **Installation**: Single-command curl (e.g., `sh -c "$(curl -fsLS get.chezmoi.io)"`) downloads binary, then user initializes repo.
- **Opt-in**: Users select which dotfiles to apply (not all-or-nothing); chezmoi applies selectively.
- **No ignore file**: chezmoi uses filename prefixes to encode behavior; no `.chezmoidenylist`.

---

## Q4: Tar.gz Bundle Conventions

### Directory Structure
- **Versioned root** (STANDARD): `package-name-version/` is expected by most installers (Homebrew, many release scripts)
- **Unversioned root** (ALTERNATIVE): Flat extract is used by npm; less common for general-purpose bundles
- **Recommendation**: Include `cleanmatic-skills-1.0.0/` or `skill-pack-260529/` to avoid conflicts on extract

### Checksums & Signatures
- **SHA256 sidecar** (NOT standard in tar): Some projects publish `.tar.gz.sha256` alongside tarball for verification
- **GPG signatures** (OPTIONAL, MATURE): `.tar.gz.asc` sidecar or detached `.asc` file; used by security-critical projects
- **No embedded checksum**: Tar header includes simple byte-sum checksum (auto-verified on extract), but not cryptographic SHA

### Recommendation for ClaudeMatic
```
cleanmatic-skills-1.0.0.tar.gz
cleanmatic-skills-1.0.0.tar.gz.sha256  (optional, for integrity check)
cleanmatic-skills-1.0.0.tar.gz.asc     (optional, for GPG verification)
```

Extract produces:
```
cleanmatic-skills-1.0.0/
├── .claude/
│   ├── skills/
│   ├── agents/
│   ├── rules/
│   └── hooks/
├── docs/
├── .ckignore
└── MANIFEST.md
```

---

## Q5: `.ckignore` Idiom (Local Inspection)

**File location**: `/home/hieubt/Documents/cleanmatic-skills/.claude/.ckignore`

### Contents
```
# SIZE-based blocking (fills LLM context)
node_modules, dist, build, .next, .nuxt
__pycache__, .venv, venv
vendor, target

# VCS & Coverage
.git, coverage

# Exceptions (allow-list prefixed with !)
!.claude/skills/product-spec/assets/vendor  (vendored Mermaid JS)
!.env, !.env.*
```

### Pattern
- **Syntax**: gitignore-spec (same as `.gitignore`)
- **Use case**: CONTEXT-aware, size-based blocking (not security or exclusion-based)
- **Scope**: Honoured by LLM tools (grep, read, glob) to avoid filling context with irrelevant large trees
- **Not tied to packaging**: `.ckignore` is for local development/interaction, NOT for tarball generation

### Implication
- `.ckignore` is **NOT** a precedent for skill package exclusion
- For packaging, a separate `.skillignore` or `.distignore` (or use `.npmignore` conventions) would be needed

---

## Q6: Existing Skill Overlap Analysis

### ship/SKILL.md
**Scope**: "Ship pipeline: merge main, test, review, commit, push, PR."
- **12-step pipeline**: pre-flight → link issues → merge → test → review → version → changelog → journal → docs → commit → push → PR
- **Outputs**: PR URL + journal + docs updates
- **Delegation**: test (subagent tester), review (subagent code-reviewer), docs (background /ck:docs update)
- **Does NOT handle packaging/distribution**: No tarball creation, no bundling, no checksum generation

### agentize/SKILL.md
**Scope**: "Convert existing code into AI-agent-friendly CLI and/or MCP server."
- **Output modes**: CLI (npm package) | MCP (stdio/SSE/HTTP) | Both (monorepo)
- **Steps**: Track → Scout → Analyze → Decide → Scaffold → Wrap → Harden → Package
- **"Package" step**: Handles npm packaging only (for CLI), not tar bundling of `.claude/` artifacts
- **Does NOT handle skill packaging**: Focuses on wrapping app code, not distributing `.claude/skills/` bundles

### bootstrap/SKILL.md
**Scope**: "Bootstrap new projects with research, tech stack, design, planning, and implementation."
- **Workflow**: Git init → Research → Tech stack → Design → Planning → Implementation → Test → Review → Docs → Onboard
- **Delegates to**: plan + cook skills; no packaging/distribution step
- **Does NOT handle skill packaging**

### skill-ship Gap
**None of the three existing skills handle**:
1. Creating a `.tar.gz` bundle of `.claude/` artifacts
2. Generating checksums or signatures
3. Publishing to a registry
4. Verifying bundle integrity on install
5. Testing bundle unpacking and skill discovery

**Conclusion**: skill-ship is **NOVEL** and does NOT duplicate existing capabilities.

---

## Summary & Recommendations

| Question | Finding | Citation |
|----------|---------|----------|
| Q1: Anthropic official | Directory + SKILL.md; no CLI; plugin model for distribution | [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) |
| Q2: Community | Multiple registries (awesome-claude, Claude Skill Registry); no `.tar.gz` standard yet | [awesome-claude](https://github.com/JSONbored/awesome-claude), [Claude Skill Registry](https://github.com/majiayu000/claude-skill-registry) |
| Q3: Adjacent | npm (semantic versioning, `.npmignore`); Homebrew (SHA256, versioned dirs); chezmoi (archive support); vim/zsh (git-based, no tar) | Multiple sources above |
| Q4: Tar conventions | Versioned root `package-version/`, optional SHA256/GPG sidecars | GNU tar, npm pack standards |
| Q5: `.ckignore` | Gitignore-spec, context-aware size blocking, NOT for packaging | Local file inspection |
| Q6: Existing skills | ship (PR pipeline), agentize (CLI/MCP), bootstrap (project init); none handle skill packaging | SKILL.md inspection |

### Suggested Design for skill-ship

1. **Bundle format**: `cleanmatic-skills-{date}-{version}.tar.gz` (versioned root)
2. **Checksum**: Optional `.sha256` sidecar for integrity check
3. **Manifest**: `MANIFEST.md` inside bundle listing included skills + versions
4. **Installation**: Simple tar extraction + auto-discovery (Claude Code's native mechanism)
5. **Exclusion**: Use `.skillignore` or `.npmignore` conventions (separate from `.ckignore`)
6. **No central registry**: Distribute via GitHub releases; users manually import or integrations via curl + tar

---

## Unresolved Questions

1. Should `.tar.gz` include git history or just working tree state?
2. Is `.skillignore` the right name, or should it reuse `.npmignore` for familiarity?
3. Should bundle include `CHANGELOG.md` for each skill or roll-up summary?
4. Should skill-ship auto-detect version from skill metadata (SKILL.md `version:` field) or require explicit argument?
5. Does Anthropic plan an official skill registry in 2026? (Unknown; no public roadmap signal.)

---

**Status**: RESEARCH COMPLETE — Findings ready for PM and implementation planning.
