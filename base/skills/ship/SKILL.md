---
name: ship
description: Complete work by running quality gates, committing changes, pushing to remote, and creating a pull request.
---

# /ship — Ship Your Work

Completes your work by running all quality gates, committing uncommitted changes, pushing to remote, and creating a pull request with auto-generated description.

## Usage

```
/ship                          # Full flow: commit, push, create PR
/ship --draft                  # Create as draft PR
/ship --no-push                # Commit only, don't push or create PR
/ship --no-pr                  # Commit and push, but don't create PR
/ship --message "Custom msg"   # Use custom commit message
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--draft` | Create PR as draft | false |
| `--no-push` | Skip push and PR creation | false |
| `--no-pr` | Push but skip PR creation | false |
| `--message` | Custom commit message | Auto-generated |
| `--reviewer` | Add reviewer to PR | None |
| `--label` | Add label to PR | None |

## Workflow

### Step 1: Run Quality Gates

Before shipping, ensure all quality gates pass:

```bash
# Read quality gates from stack config or run standard checks
npm run lint 2>/dev/null || bundle exec rubocop 2>/dev/null || ruff check . 2>/dev/null
npm test 2>/dev/null || bundle exec rspec 2>/dev/null || pytest 2>/dev/null
npx tsc --noEmit 2>/dev/null || true
```

If any gate fails:
- Report the failure
- Offer to run fix commands (lint --fix, rubocop -A, etc.)
- Retry after fixes
- Abort if still failing

### Step 2: Check Current State

```bash
# Ensure we're on a feature branch, not main/master
CURRENT_BRANCH=$(git branch --show-current)

# Get base branch
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
```

If on main/master:
- Error: "Cannot ship from main/master. Create a feature branch first with /branch"

### Step 3: Stage and Commit Changes

```bash
# Check for uncommitted changes
git status --porcelain
```

If there are changes:

1. Show what will be committed:
```bash
git status --short
git diff --stat
```

2. Generate commit message (or use provided --message):
```bash
# Analyze changes to generate message
git diff --cached --stat
git log --oneline $BASE_BRANCH..HEAD  # Previous commits for context
```

Smart commit message generation:
- Look at files changed (models, controllers, components, tests)
- Look at feature file if exists
- Summarize the changes in conventional commit format

3. Commit:
```bash
git add -A  # Or specific files if preferred
git commit -m "$(cat <<'EOF'
<type>(<scope>): <description>

<body if needed>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Step 4: Push to Remote

```bash
# Push with upstream tracking
git push -u origin "$CURRENT_BRANCH"
```

If push fails due to upstream changes:
```bash
# Offer to sync first
git fetch origin
git rebase origin/$BASE_BRANCH
# Or merge if user prefers
git push -u origin "$CURRENT_BRANCH"
```

### Step 5: Create Pull Request

```bash
# Get PR description from feature file or generate from commits
FEATURE_FILE=$(find .claude/context/features -name "*.md" -newer .git/refs/heads/$BASE_BRANCH 2>/dev/null | head -1)
```

Generate PR body:

```markdown
## Summary

<From feature file overview or commit messages>

## Changes

<List of key changes from commits>

## Test Plan

- [ ] <From feature file or auto-generated>

## Linked Issues

<If issue was linked via /branch>
Closes #<issue-number>

---
Generated with [Claude Code](https://claude.ai/code)
```

Create PR:

```bash
gh pr create \
  --title "<PR title from branch name or feature>" \
  --body "$(cat <<'EOF'
<generated body>
EOF
)" \
  --base "$BASE_BRANCH" \
  $([ "$DRAFT" = true ] && echo "--draft") \
  $([ -n "$REVIEWER" ] && echo "--reviewer $REVIEWER") \
  $([ -n "$LABEL" ] && echo "--label $LABEL")
```

### Step 6: Report Result

```markdown
## Shipped!

**Branch:** `feature/user-authentication`
**PR:** #42 - Add user authentication
**URL:** https://github.com/owner/repo/pull/42

### Summary
- 5 commits
- 12 files changed
- +450 / -23 lines

### Quality Gates
- Lint: PASS
- Tests: PASS
- TypeScript: PASS

### Next Steps
- Wait for CI to complete
- Request review if not auto-assigned
- Address any review feedback
```

## Integration with PM Workflow

When PM workflow has `git_workflow: "full"`:

1. After Phase 5 (Completion), PM calls `/ship`
2. PR description includes full feature summary
3. All quality gates already passed in Phase 3
4. PR linked to any issues from planning

## Error Handling

| Error | Action |
|-------|--------|
| Quality gates fail | Offer to fix, retry, or abort |
| On main/master | Error with /branch suggestion |
| No changes to commit | Skip commit, proceed to PR |
| Push rejected | Offer to sync with /sync |
| PR already exists | Update existing PR or error |
| gh CLI not installed | Error with install instructions |
| Not authenticated | Run `gh auth login` |

## Commit Message Format

Uses conventional commits:

```
<type>(<scope>): <short description>

<body - what and why>

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `chore` - Maintenance
- `refactor` - Code restructuring
- `docs` - Documentation
- `test` - Test additions
- `style` - Formatting

## Examples

### Standard Ship
```
/ship
```
Commits all changes, pushes, creates PR.

### Draft PR for Early Feedback
```
/ship --draft
```
Creates draft PR for work-in-progress review.

### Commit Without PR
```
/ship --no-pr
```
Useful for pushing work without PR (e.g., updating branch).

### Custom Message
```
/ship --message "feat(auth): add OAuth2 login flow"
```
Uses provided commit message instead of auto-generating.
