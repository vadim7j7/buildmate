---
name: review
description: Run a code review for React + Next.js projects using the frontend-reviewer agent
---

# /review

## What This Does

Identifies changed files, delegates a structured code review to the
`frontend-reviewer` agent, and reports findings categorized as blockers,
warnings, or suggestions. Specialized for React + Next.js with TypeScript.

## Usage

```
/review                        # Review all changed files vs base branch
/review src/components/Foo.tsx  # Review a specific file
/review --staged               # Review only staged changes
```

## How It Works

### 1. Identify Changed Files

```bash
# All changes vs base branch
git diff --name-only main...HEAD

# Staged only
git diff --cached --name-only

# Specific file: use the provided path
```

Filter to relevant files: `*.ts`, `*.tsx`, `*.css`, `*.json` (exclude
`node_modules`, `dist`, `.next`, lock files).

### 2. Gather Context

Read each changed file in full. Also read:

- `patterns/frontend-patterns.md` -- project code patterns
- `.agent-pipeline/implement.md` -- implementation notes (if exists)
- `.agent-pipeline/test.md` -- test results (if exists)
- Related feature file from `.claude/context/features/` (if linked)

### 3. Delegate to Frontend Reviewer

Use the Task tool to invoke the `frontend-reviewer` agent with:

- Full file contents of each changed file
- The git diff for each file
- Pipeline context (implementation notes, test results)
- Reference to the review checklist in the agent definition

### 4. Collect Review Results

The reviewer agent returns a structured review:

```markdown
## Code Review Results

**Verdict:** APPROVED | NEEDS_CHANGES | BLOCKED

### Blockers (must fix)
- [file:line] Description

### Warnings (should fix)
- [file:line] Description

### Suggestions (nice to have)
- [file:line] Description

### Checklist Results
| Category | Status |
|---|---|
| React Best Practices | PASS / ISSUES |
| Next.js Conventions | PASS / ISSUES |
| UI Library Usage | PASS / ISSUES |
| Accessibility | PASS / ISSUES |
| Performance | PASS / ISSUES |
| TypeScript | PASS / ISSUES |
| API Integration | PASS / ISSUES |
| Security | PASS / ISSUES |
| Testing Coverage | PASS / ISSUES |
```

### 5. Write Pipeline Artifact

If running as part of a pipeline, write results to `.agent-pipeline/review.md`.

## Reference Files

- `references/nextjs-patterns.md` -- Next.js code pattern references
- `references/react-security.md` -- React security checklist

## Review Focus Areas

| Area | What to Check |
|---|---|
| Server vs Client | `'use client'` only when needed |
| TypeScript | No `any`, `type` for props |
| UI Library | UI library components used per style guide |
| Accessibility | Labels, ARIA, keyboard nav |
| Performance | No unnecessary re-renders, proper memoization |
| Security | No XSS, no secrets in client code |
| Testing | Adequate test coverage for changes |

## Verdicts

| Verdict | Meaning |
|---|---|
| APPROVED | No blockers. Warnings and suggestions are advisory. |
| NEEDS_CHANGES | At least one blocker must be resolved before merge. |
| BLOCKED | Unresolvable architectural concern requiring user decision. |

## Error Handling

- If no changed files are found, report that there is nothing to review.
- If the diff is too large (> 100 files), suggest splitting into smaller PRs and
  review only the first 30 files.
