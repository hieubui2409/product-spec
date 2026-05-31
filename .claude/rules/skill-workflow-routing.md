# Skill Workflow Routing

When orchestrating multi-step tasks, consider these workflow sequences. Skills are listed in typical execution order.

## Core Development Workflow

```
/ck:plan → /ck:cook → /ck:test → /ck:code-review → /ck:ship → /ck:journal
```

| User Intent | Suggested Start |
|-------------|----------------|
| "implement feature X", "build X", "add X" | `/ck:plan` then `/ck:cook` |
| "execute this plan" | `/ck:cook <plan-path>` |
| "quick implementation" | `/ck:cook --fast` |

## Bugfix Workflow

```
/ck:scout → /ck:debug → /ck:fix → /ck:test → /ck:code-review
```

| User Intent | Suggested Start |
|-------------|----------------|
| "X is broken", "error in X", "bug in X" | `/ck:fix` (auto-scouts internally) |
| "CI is failing", "tests broken" | `/ck:fix --auto` |
| "investigate why X happens" | `/ck:scout` then `/ck:debug` |

## Investigation Workflow

```
/ck:scout → /ck:debug → /ck:brainstorm → /ck:plan
```

| User Intent | Suggested Start |
|-------------|----------------|
| "understand how X works" | `/ck:scout` |
| "why is X happening" | `/ck:debug` |
| "explore options for X" | `/ck:brainstorm` then `/ck:plan` |

## Post-Implementation Checklist

After completing implementation work, consider:
- `/ck:code-review` — review changes before merging
- `/ck:review-pr` — review a PR thoroughly (auto-flags AI-slop patterns); add `--fix` to auto-remediate, `--reply` to post the review to GitHub
- `/ck:ship` — run full shipping pipeline (tests, review, version, PR)
- `/ck:journal` — document decisions and lessons learned

## PR Review Workflow

```
/ck:review-pr <PR>           → review-only, prints to chat
/ck:review-pr <PR> --fix     → review + auto-remediate + commit/push, re-review loop
/ck:review-pr <PR> --reply   → review + post formal review to GitHub via gh
/ck:review-pr <PR> --fix --reply → fix loop, post final re-review when converged
```

| User Intent | Suggested Start |
|-------------|----------------|
| "review PR #123", "look at this PR" | `/ck:review-pr 123` |
| "fix the issues in PR 123" | `/ck:review-pr 123 --fix` |
| "review and comment on PR 123" | `/ck:review-pr 123 --reply` |

## Setup Skills

Before starting implementation in a shared codebase:
- `/ck:worktree` — create isolated worktree for the feature/fix
- `/ck:scout` — discover relevant files and code patterns
