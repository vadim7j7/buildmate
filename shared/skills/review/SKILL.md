---
name: review
description: Delegate to the stack-specific reviewer agent for code review
---

# /review

## What This Does

Identifies changed files in the current branch, delegates a code review to the
stack's reviewer agent, and reports findings categorised as blockers, warnings,
or suggestions.

## Usage

```
/review                   # Review all changed files vs base branch
/review path/to/file.ts   # Review a specific file
/review --staged          # Review only staged changes
```

## How It Works

1. **Identify changed files.** Run `git diff --name-only` against the base
   branch (typically `main` or `master`) to build the list of files to review.
   If `--staged` is passed, use `git diff --cached --name-only` instead. If a
   specific file is provided, review only that file.

2. **Gather context.** Read each changed file in full. Also read:
   - `.agent-pipeline/implement.md` if it exists (implementation notes)
   - `.agent-pipeline/test.md` if it exists (test results)
   - The relevant feature file from `.claude/context/features/` if one is
     linked in the pipeline context.

3. **Delegate to the stack's reviewer agent.** Use the Task tool to invoke
   the reviewer sub-agent with:
   - The list of changed files and their full contents
   - The diff for each file (`git diff` output)
   - Any gathered pipeline context
   - The project's linting and type-checking configuration

4. **Collect review results.** The reviewer agent analyses each file and
   returns findings in the following structure:

   ```
   ## Code Review Results

   **Verdict:** APPROVE | REQUEST_CHANGES

   ### Blockers (must fix)
   - [file:line] Description of the issue

   ### Warnings (should fix)
   - [file:line] Description of the concern

   ### Suggestions (nice to have)
   - [file:line] Description of the improvement
   ```

5. **Write pipeline artefact.** If running as part of a sequential pipeline,
   write results to `.agent-pipeline/review.md`.

## Review Criteria

The reviewer agent checks for:

- **Correctness:** Logic errors, off-by-one bugs, unhandled edge cases
- **Security:** Injection vulnerabilities, data exposure, auth gaps
- **Performance:** Unnecessary re-renders, N+1 queries, missing indexes
- **Code quality:** Naming, duplication, single-responsibility violations
- **Type safety:** Any/unknown usage, missing type guards
- **Test coverage:** Whether new code paths have corresponding tests
- **API design:** Breaking changes, inconsistent naming, missing validation

## Verdicts

| Verdict          | Meaning                                              |
|------------------|------------------------------------------------------|
| APPROVE          | No blockers. Warnings and suggestions are advisory.  |
| REQUEST_CHANGES  | At least one blocker must be resolved before merge.  |

## Error Handling

- If no changed files are found, report that there is nothing to review.
- If the diff is too large (> 200 files), suggest splitting the work into
  smaller PRs and review only the first 50 files.
