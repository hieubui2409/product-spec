# workflow-pack

The interactive (no-flag) flow. Activated when the PO invokes `/cleanmatic:claude-pack` without a manifest path and without category-override flags. Walks them through manifest authoring via `AskUserQuestion`, previews the build, then packs.

**Hard rule:** Python scripts NEVER call `AskUserQuestion`. The LLM is the UI layer; the script is the structural layer. `build_manifest.py` has three modes: `--discover`, `--list-questions`, `--write`.

## When This Flow Runs

- No `.claude/pack.manifest.yaml` exists → run interactive build.
- `.claude/pack.manifest.yaml` exists → ask: **reuse / overwrite / cancel**. Overwrite goes through this flow with `--force`.
- User explicitly invokes `/cleanmatic:claude-pack --interactive` even with existing manifest.

## Question Bank (4 Batches)

Source-of-truth: `build_manifest.py --list-questions --root.` returns the JSON below at runtime. Schema is locked here.

### Batch 1: version-and-name (2 questions)

| ID | Header | Question | Type | Default | Validate |
|----|--------|----------|------|---------|----------|
| `version` | Version | Bundle version (SemVer 2.0.0, e.g. 1.0.0)? | text | `0.1.0` | semver |
| `bundle_name` | Bundle name | Bundle filename stem? | text | `claude-pack` | — (see note) |

> **Note:** `bundle_name` regex validation (`^[a-zA-Z0-9][a-zA-Z0-9._-]*$`) is enforced at `--write` time via `BUNDLE_NAME_RE` in `manifest_loader.validate` (→ `MANIFEST_E003`). The question bank JSON emitted by `--list-questions` does NOT carry a `validate` field for `bundle_name`.

### Batch 2: categories (4 questions)

| ID | Header | Question | Type | Options |
|----|--------|----------|------|---------|
| `skills` | Skills | Which skills to include? | multi-select | from `discover.available_skills` |
| `agents` | Agents | Which agents to include? | multi-select | from `discover.available_agents` |
| `hooks` | Hooks | Which hooks to include? | multi-select | from `discover.available_hooks` |
| `rules` | Rules | Which rules to include? | multi-select | from `discover.available_rules` |

### Batch 3: top-level (4 questions)

| ID | Header | Question | Type | Default |
|----|--------|----------|------|---------|
| `include_readme` | README | Include repo-root README.md? | bool | false |
| `include_claudemd` | CLAUDE.md | Include repo-root CLAUDE.md? | bool | false |
| `include_settings` | settings.json | Include.claude/settings.json? (opt-in only) | bool | false |
| `include_ck_config` |.ck.json | Include.claude/.ck.json? (opt-in only) | bool | false |

### Batch 4: extras-and-shared (2 questions)

| ID | Header | Question | Type | Default |
|----|--------|----------|------|---------|
| `extra` | Extra paths | Extra repo-relative paths (comma-separated). NO absolute, NO `..`. | text-list | `[]` |
| `follow_shared` | _shared/ | Auto-include _shared/<name> refs from packed skills? (default false = warn-only) | bool | false |

## LLM Orchestration Pattern

```
# 1. Discover state
bash: python -m build_manifest --discover --root. # → discovery JSON

# 2. Get question bank
bash: python -m build_manifest --list-questions --root. # → questions JSON

# 3. Walk batches via AskUserQuestion
answers = {}
for batch in questions.batches:
 for q in batch.questions:
 answers[q.id] = AskUserQuestion(q.question, q.options or q.default)

# 4. Show summary
echo: "Manifest: version={version}, skills={N}, agents={M}, rules={K}"

# 5. CONFIRM (locked prompt)
confirmed = AskUserQuestion(
 "Ready to write.claude/pack.manifest.yaml with {N} skills, {M} agents, {K} rules? [y/N]"
)

# 6. Write (only on confirmation)
if confirmed == "y":
 bash: echo $answers_json | python -m build_manifest --write --root.
```

## Validation Hook

Before invoking `--write`:

1. LLM MUST present a summary of all chosen values.
2. LLM MUST issue the **locked confirm prompt** (verbatim):

> **"Ready to write.claude/pack.manifest.yaml with {N} skills, {M} agents, {K} rules? [y/N]"**

3. Only on explicit `y` (or equivalent affirmative AskUserQuestion option) does the script invoke `--write`.
4. If `pack.manifest.yaml` already exists, `--write` exits 2 unless `--force` is passed. LLM must surface the collision and re-prompt before re-invoking.

## Resume Path

The interactive flow is stateless on disk (no `.session.md`). If the user aborts mid-interview:

- LLM's conversation context still holds prior answers.
- On resume, LLM can say: "I have your answers from batches 1-3; ready for batch 4?".
- If context is lost (compact, new session), LLM re-runs `--discover` and starts from batch 1.

Product-spec uses disk-backed `.session.md` because its interview is much larger (Vision/BRD/PRD/Epic/Story); claude-pack's 4-batch flow fits in-context.

## Edge Cases

- **Empty selection** (no skills, no agents, etc.): `--write` produces a manifest with empty lists; `pack` exits 5 (nothing to pack) when run later. LLM should warn during summary.
- **Invalid `extra` path** (absolute or `..`): `--write` validates via `manifest_loader.validate` → exits 1; no file written (`MANIFEST_E020` / `MANIFEST_E021`).
- **Bundle name collision** (e.g., `../etc/passwd`): caught by `BUNDLE_NAME_RE` → `MANIFEST_E003`.
- **Pre-existing manifest, no `--force`**: exit 2; LLM must re-prompt.

## Related References

- `manifest-spec.md` — full schema.
- `flag-reference.md` — CLI options at pack-time.
- `error-catalog.md` — `MANIFEST_E###` lookups.
