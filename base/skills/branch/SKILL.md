---
name: branch
description: Create a new git branch for a feature, fix, or task. Optionally links to a GitHub issue.
---

# /branch — Create Feature Branch

Creates a new git branch with proper naming conventions for starting work on a feature, fix, or chore.

## Usage

```
/branch user-authentication              # Creates feature/user-authentication
/branch login-bug --type fix             # Creates fix/login-bug
/branch update-deps --type chore         # Creates chore/update-deps
/branch user-auth --issue 123            # Links to GitHub issue #123
/branch user-auth --base develop         # Branch from develop instead of main
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `name` | Branch name (will be slugified) | Required |
| `--type` | Branch type: feature, fix, chore, hotfix, refactor | feature |
| `--issue` | GitHub issue number to link | None |
| `--base` | Base branch to create from | main or master |

## Workflow

### Step 1: Validate Current State

```bash
# Check for uncommitted changes
git status --porcelain
```

If there are uncommitted changes:
- Warn the user
- Offer to stash changes: `git stash push -m "Auto-stash before branch switch"`
- Or abort and let user handle it

### Step 2: Determine Base Branch

```bash
# Find default branch
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'

# Fallback: check for main or master
git rev-parse --verify origin/main 2>/dev/null && echo "main" || echo "master"
```

If `--base` is provided, use that instead.

### Step 3: Update Base Branch

```bash
# Fetch latest
git fetch origin

# Ensure we're up to date
git checkout <base-branch>
git pull origin <base-branch>
```

### Step 4: Create Branch

```bash
# Slugify the name (lowercase, hyphens)
BRANCH_NAME="<type>/<slugified-name>"

# Create and switch to new branch
git checkout -b "$BRANCH_NAME"
```

Branch naming conventions:
- `feature/` - New functionality
- `fix/` - Bug fixes
- `chore/` - Maintenance, deps, configs
- `hotfix/` - Urgent production fixes
- `refactor/` - Code restructuring

### Step 5: Link Issue (Optional)

If `--issue` is provided:

1. Fetch issue details:
```bash
gh issue view <issue-number> --json title,body,labels
```

2. Create/update feature file with issue info:
```markdown
# Feature: <Issue Title>

## GitHub Issue
- **Issue:** #<number>
- **Link:** https://github.com/<owner>/<repo>/issues/<number>

## Description
<Issue body>
```

### Step 6: Push Branch (Optional)

```bash
# Set upstream and push
git push -u origin "$BRANCH_NAME"
```

Only push if explicitly requested or if project settings indicate auto-push.

## Output

Report the result:

```markdown
## Branch Created

**Branch:** `feature/user-authentication`
**Base:** `main`
**Issue:** #123 (if linked)

### Next Steps
1. Start implementing your changes
2. Use `/ship` when ready to create a PR
```

## Integration with PM Workflow

When used within the PM workflow:

1. PM reads `pm.git_workflow` from `.claude/settings.json`
2. If `"branch"` or `"full"`, PM calls `/branch` after plan approval
3. Branch name derived from feature file slug
4. Issue linked if mentioned in requirements

## Error Handling

| Error | Action |
|-------|--------|
| Uncommitted changes | Offer to stash or abort |
| Branch already exists | Ask to switch or create new name |
| Base branch not found | Fall back to main/master |
| Not a git repo | Error with helpful message |
| No remote configured | Create local branch only |

## Examples

### Basic Feature Branch
```
/branch add-dark-mode
```
Creates `feature/add-dark-mode` from main.

### Bug Fix with Issue
```
/branch login-timeout --type fix --issue 42
```
Creates `fix/login-timeout`, links to issue #42.

### Hotfix from Production
```
/branch security-patch --type hotfix --base production
```
Creates `hotfix/security-patch` from production branch.
