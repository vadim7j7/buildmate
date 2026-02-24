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
| `--repo` | Specific repo to ship (multi-repo only) | All with changes |
| `--link-prs` | Cross-link PRs in descriptions | true |

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

---

## Multi-Repository Support

For workspaces with multiple repositories, `/ship` coordinates commits, pushes, and PRs across all repos.

### Configuration

Uses the same configuration as `/branch` in `.claude/settings.json`:

```json
{
  "pm": {
    "git_workflow": "full",
    "multi_repo": {
      "enabled": true,
      "repositories": {
        "workspace": ".",
        "backend": "./backend",
        "web": "./web",
        "mobile": "./mobile"
      },
      "stack_repo_map": {
        "rails": "backend",
        "fastapi": "backend",
        "nextjs": "web",
        "react-native": "mobile"
      }
    }
  }
}
```

### Multi-Repo Workflow

#### Step 0: Identify Repos with Changes

```bash
# Check each configured repo for uncommitted changes or unpushed commits
for repo in $REPOS; do
  (cd $repo && git status --porcelain && git log origin/main..HEAD --oneline)
done
```

Only process repos that have changes.

#### Step 1: Quality Gates Per Repo

Run quality gates in each repo based on its stack:

```bash
# Backend (Rails/FastAPI)
(cd backend && bundle exec rubocop && bundle exec rspec)

# Web (Next.js)
(cd web && npm run lint && npm test && npx tsc --noEmit)

# Mobile (React Native)
(cd mobile && npm run lint && npm test)
```

#### Step 2: Commit in Each Repo

For each repo with changes:

```bash
(cd $repo && git add -A && git commit -m "$MESSAGE")
```

Use the same commit message format, or customize per repo based on changes.

#### Step 3: Push All Repos

```bash
for repo in $REPOS; do
  (cd $repo && git push -u origin "$BRANCH_NAME")
done
```

#### Step 4: Create Linked PRs

Create PRs in sequence, then update descriptions with cross-links:

```bash
# Create PRs and collect URLs
BACKEND_PR=$(cd backend && gh pr create --title "$TITLE" --body "$BODY" | tail -1)
WEB_PR=$(cd web && gh pr create --title "$TITLE" --body "$BODY" | tail -1)

# Update PR descriptions with cross-links
gh pr edit $BACKEND_PR --body "... Related: $WEB_PR"
gh pr edit $WEB_PR --body "... Related: $BACKEND_PR"
```

### Cross-Linked PR Description

```markdown
## Summary

<Feature summary from feature file>

## Changes in This Repo

<Repo-specific changes>

## Related PRs

| Repository | PR | Status |
|------------|-----|--------|
| backend | #42 | Open |
| web | #18 | Open |
| mobile | - | No changes |

## Test Plan

- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] Integration tested

---
Generated with [Claude Code](https://claude.ai/code)
```

### Multi-Repo Output

```markdown
## Shipped!

### Pull Requests Created

| Repository | PR | URL | Changes |
|------------|-----|-----|---------|
| backend | #42 | https://github.com/org/backend/pull/42 | +350/-45 |
| web | #18 | https://github.com/org/web/pull/18 | +280/-30 |
| mobile | - | - | No changes |

### Summary
- 3 repos processed
- 2 PRs created
- All PRs cross-linked

### Quality Gates
| Repo | Lint | Tests | Types |
|------|------|-------|-------|
| backend | PASS | PASS | N/A |
| web | PASS | PASS | PASS |

### Next Steps
1. Wait for CI in all repos
2. Review PRs together
3. Merge in order: backend → web (if dependencies)
```

### Examples

#### Ship All Repos
```
/ship
```
Commits, pushes, and creates PRs in all repos with changes.

#### Ship Specific Repo
```
/ship --repo backend
```
Only ships the backend repo.

#### Draft PRs for All
```
/ship --draft
```
Creates draft PRs in all repos.

#### Ship Without Cross-Linking
```
/ship --link-prs=false
```
Creates independent PRs without cross-references.

### Workspace PR (Optional)

If the workspace itself has changes (e.g., shared configs, documentation):

```bash
# Create workspace PR that references all sub-PRs
(cd . && gh pr create --title "feat: user authentication" --body "
## Umbrella PR

This PR coordinates changes across repositories:

- Backend: #42
- Web: #18

Merge sub-PRs first, then merge this.
")
```

### Error Handling

| Error | Action |
|-------|--------|
| Quality gate fails in one repo | Report which repo failed, offer to skip or fix |
| Push fails in one repo | Sync that repo, retry |
| PR creation fails | Report error, continue with other repos |
| Cross-linking fails | Create PRs without links, report issue |
