# Primary Workflow

Use this file when a task needs an implementation workflow beyond a direct answer.

## 1. Understand

- Read the request, relevant docs, and nearby code before planning.
- Clarify only decisions that cannot be discovered from the repo.
- For broad or risky work, create or update a plan in `plans/`.
- For ambiguous workflow sequence, load `.claude/skills/cook/references/workflow-routing.md`.

## 2. Implement

- Change existing files when that matches the design; create new files only for real boundaries.
- Keep behavior compatible unless the accepted scope says otherwise.
- Prefer local helpers, conventions, and test utilities over new abstractions.
- For bugs, prove the cause before changing behavior.

## 3. Verify

- Run focused tests for touched behavior.
- Broaden to lint, typecheck, build, or integration tests when shared contracts changed.
- Fix regressions instead of weakening tests.

## 4. Review and Explain

- Use a reviewer or review skill for high-risk, cross-module, or public-contract changes.
- Update docs only when user-facing behavior, workflows, commands, or architecture changed.
- Explain the result plainly; use `/ck:preview` only for complex workflows or architecture. For mode selection, load `.claude/skills/preview/references/visual-explanation-routing.md`.
