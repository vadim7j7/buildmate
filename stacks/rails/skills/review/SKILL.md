---
name: review
description: Delegate to the backend-reviewer agent for Rails code review
---

# /review

## What This Does

Identifies changed files in the current branch, delegates a comprehensive code review
to the `backend-reviewer` agent, and reports findings categorized by severity (BLOCKER,
WARNING, SUGGESTION).

## Usage

```
/review                       # Review all changed files vs base branch
/review app/services/         # Review only files in a specific directory
/review --staged              # Review only staged changes
/review app/models/profile.rb # Review a specific file
```

## How It Works

1. **Identify changed files.** Run `git diff --name-only` against the base branch
   (typically `main` or `master`) to build the list of files to review. If `--staged`
   is passed, use `git diff --cached --name-only`. If a specific path is provided,
   review only matching files.

2. **Gather context.** Read each changed file in full. Also read:
   - `patterns/backend-patterns.md` for expected code patterns
   - `styles/backend-ruby.md` for style conventions
   - `skills/review/references/rails-patterns.md` for pattern reference
   - `skills/review/references/rails-security.md` for security checklist
   - `.agent-pipeline/implement.md` if it exists (implementation notes)
   - `.agent-pipeline/test.md` if it exists (test results)
   - The relevant feature file from `.claude/context/features/` if linked

3. **Delegate to backend-reviewer.** Use the Task tool to invoke the
   `backend-reviewer` sub-agent with:
   - The list of changed files and their full contents
   - The diff for each file (`git diff` output)
   - Reference patterns and security checklist
   - Any gathered pipeline context

4. **Run automated checks.** The backend-reviewer executes:

   ```bash
   # Lint check
   bundle exec rubocop <changed_files>

   # Check for N+1 indicators
   grep -rn 'has_many\|belongs_to' <changed_model_files>
   grep -rn 'includes\|preload\|eager_load' <changed_controller_files>
   ```

5. **Collect review results.** The reviewer returns findings in this format:

   ```markdown
   ## Code Review: <Feature Name>

   ### Verdict: APPROVED | NEEDS CHANGES | BLOCKED

   ### Blockers (must fix)
   - [file:line] Description of the issue

   ### Warnings (should fix)
   - [file:line] Description of the concern

   ### Suggestions (nice to have)
   - [file:line] Description of the improvement
   ```

6. **Write pipeline artifact.** If running as part of a sequential pipeline, write
   results to `.agent-pipeline/review.md` for the next stage.

## Review Criteria

The backend-reviewer checks for:

- **Rails Conventions**: Service/presenter/controller/model patterns
- **Performance**: N+1 queries, missing indices, pagination, batch processing
- **Security**: Authentication, authorization, strong params, SQL injection
- **Code Quality**: SRP, readability, YARD docs, guard clauses, frozen_string_literal
- **Testing**: Adequate spec coverage for all new code paths

## Verdicts

| Verdict       | Meaning                                                    |
|---------------|------------------------------------------------------------|
| APPROVED      | No blockers. Warnings and suggestions are advisory.        |
| NEEDS CHANGES | At least one warning-level issue should be resolved.       |
| BLOCKED       | At least one blocker must be resolved before merge.        |

## Error Handling

- If no changed files are found, report that there is nothing to review.
- If rubocop is not available, note it in the review but continue with manual checks.
- If the diff is very large (>50 files), suggest splitting into smaller PRs and
  review only the most critical files first.
