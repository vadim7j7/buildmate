---
name: sync
description: Sync current branch with the base branch (main/master) using rebase or merge.
---

# /sync — Sync Branch with Base

Keeps your feature branch up to date with the base branch by rebasing or merging.

## Usage

```
/sync                    # Rebase on main/master (default)
/sync --merge            # Merge main/master into branch
/sync --base develop     # Sync with specific branch
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--merge` | Use merge instead of rebase | false (rebase) |
| `--base` | Base branch to sync with | main or master |
| `--repo` | Specific repo to sync (multi-repo only) | All repos |
| `--parallel` | Sync repos in parallel | false |

## Why Rebase vs Merge

| Strategy | Pros | Cons |
|----------|------|------|
| **Rebase** (default) | Clean linear history, easier to review | Rewrites history, can cause issues if branch is shared |
| **Merge** | Preserves history, safe for shared branches | Creates merge commits, messier history |

**Recommendation:**
- Use rebase for personal feature branches
- Use merge for shared branches or when history preservation matters

## Workflow

### Step 1: Check Current State

```bash
# Ensure we're on a feature branch
CURRENT_BRANCH=$(git branch --show-current)

# Check for uncommitted changes
git status --porcelain
```

If uncommitted changes exist:
- Stash them: `git stash push -m "Auto-stash before sync"`
- Restore after sync: `git stash pop`

### Step 2: Fetch Latest

```bash
git fetch origin
```

### Step 3: Determine Base Branch

```bash
# Use provided base or detect default
if [ -n "$BASE_ARG" ]; then
  BASE_BRANCH="$BASE_ARG"
else
  BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
  [ -z "$BASE_BRANCH" ] && BASE_BRANCH="main"
fi
```

### Step 4: Sync (Rebase or Merge)

#### Rebase (Default)

```bash
git rebase origin/$BASE_BRANCH
```

If conflicts occur:
1. List conflicting files: `git diff --name-only --diff-filter=U`
2. Show conflict details for each file
3. Help resolve conflicts or offer to abort

After successful rebase:
```bash
# Force push is needed after rebase
git push --force-with-lease origin $CURRENT_BRANCH
```

#### Merge

```bash
git merge origin/$BASE_BRANCH -m "Merge $BASE_BRANCH into $CURRENT_BRANCH"
```

If conflicts occur:
1. Same conflict resolution as rebase
2. After resolution: `git commit`

After successful merge:
```bash
git push origin $CURRENT_BRANCH
```

### Step 5: Restore Stashed Changes

```bash
git stash pop
```

If stash pop conflicts:
- Report which files conflict
- Help resolve or keep in stash

### Step 6: Report Result

```markdown
## Branch Synced

**Branch:** `feature/user-auth`
**Base:** `main`
**Strategy:** rebase

### Changes Incorporated
- abc1234 feat: add new API endpoint
- def5678 fix: resolve login issue

### Status
- Conflicts: None
- Push: Completed (force-with-lease)
```

## Conflict Resolution

When conflicts occur:

1. **Show the conflict:**
```bash
git diff --name-only --diff-filter=U
```

2. **For each conflicting file:**
- Show the conflict markers
- Suggest resolution based on context
- Apply fix with Edit tool

3. **After resolving:**
```bash
# For rebase
git add <resolved-files>
git rebase --continue

# For merge
git add <resolved-files>
git commit
```

4. **If unresolvable:**
```bash
git rebase --abort  # or git merge --abort
```
Report to user with details.

## Safety Features

### Force Push Protection

When rebasing requires force push:

```bash
# Use --force-with-lease to prevent overwriting others' work
git push --force-with-lease origin $CURRENT_BRANCH
```

If force-with-lease fails:
- Someone else pushed to the branch
- Abort and report the situation
- Suggest coordination with team

### Stash Protection

Always stash before sync to prevent losing work:

```bash
git stash push -m "Auto-stash before sync $(date +%Y%m%d-%H%M%S)"
```

List stashes if pop fails:
```bash
git stash list
```

## Error Handling

| Error | Action |
|-------|--------|
| Uncommitted changes | Auto-stash, restore after |
| Conflicts during rebase | Help resolve or abort |
| Conflicts during merge | Help resolve or abort |
| Force push rejected | Report, suggest coordination |
| Stash pop conflicts | Report, keep in stash |
| Not on feature branch | Warn, suggest creating branch |

## Examples

### Standard Sync
```
/sync
```
Rebases current branch on main, force-pushes.

### Merge Strategy
```
/sync --merge
```
Merges main into current branch, regular push.

### Sync with Specific Branch
```
/sync --base develop
```
Syncs with develop instead of main.

## Integration

This skill is automatically called by `/ship` when push fails due to upstream changes. Users can also invoke it manually to keep branches fresh during long-running work.

---

## Multi-Repository Support

For workspaces with multiple repositories, `/sync` coordinates syncing across all repos.

### Configuration

Uses the same configuration as `/branch` in `.claude/settings.json`:

```json
{
  "pm": {
    "multi_repo": {
      "enabled": true,
      "repositories": {
        "workspace": ".",
        "backend": "./backend",
        "web": "./web",
        "mobile": "./mobile"
      }
    }
  }
}
```

### Multi-Repo Workflow

#### Step 0: Identify Target Repos

1. If `--repo` specified, sync only that repo
2. Otherwise, sync all repos on the same branch

```bash
# Check which repos are on the feature branch
for repo in $REPOS; do
  BRANCH=$(cd $repo && git branch --show-current)
  if [ "$BRANCH" = "$FEATURE_BRANCH" ]; then
    echo "$repo: on $BRANCH"
  fi
done
```

#### Step 1-5: Per-Repository Sync

For each target repo, execute the standard sync workflow:

```bash
for repo in $REPOS; do
  (
    cd $repo
    git stash push -m "Auto-stash before sync"
    git fetch origin
    git rebase origin/$BASE_BRANCH  # or merge
    git push --force-with-lease origin $BRANCH
    git stash pop
  )
done
```

#### Parallel Sync (Optional)

With `--parallel`, sync repos concurrently:

```bash
# Sync in background
(cd backend && git fetch && git rebase origin/main) &
(cd web && git fetch && git rebase origin/main) &
(cd mobile && git fetch && git rebase origin/main) &
wait
```

**Note:** Parallel sync is faster but makes conflict resolution harder.

### Multi-Repo Output

```markdown
## Branches Synced

| Repository | Branch | Strategy | Status | Conflicts |
|------------|--------|----------|--------|-----------|
| backend | `feature/user-auth` | rebase | Synced | None |
| web | `feature/user-auth` | rebase | Synced | None |
| mobile | `feature/user-auth` | rebase | Synced | 1 file |

### Conflict Details (mobile)
- `src/api/auth.ts` - Manual resolution needed

### Changes Incorporated
**backend:**
- abc1234 feat: add user model

**web:**
- def5678 fix: update API client

### Next Steps
1. Resolve conflict in mobile/src/api/auth.ts
2. Run `/sync --repo mobile` to complete
```

### Conflict Handling

When conflicts occur in multi-repo sync:

1. **Stop at first conflict** (default)
   - Report which repo has conflicts
   - Help resolve, then continue with remaining repos

2. **Continue on conflict** (with flag)
   - Note conflicts but proceed with other repos
   - Report all conflicts at end

### Examples

#### Sync All Repos
```
/sync
```
Rebases all repos on their respective main branches.

#### Sync Specific Repo
```
/sync --repo backend
```
Only syncs the backend repo.

#### Parallel Sync
```
/sync --parallel
```
Syncs all repos concurrently (faster, but harder to debug).

#### Merge Strategy for All
```
/sync --merge
```
Uses merge instead of rebase in all repos.

### Error Handling

| Error | Action |
|-------|--------|
| Conflict in one repo | Stop, help resolve, offer to continue |
| Force push rejected | Report which repo, suggest coordination |
| Repo not on feature branch | Skip that repo, report |
| Stash pop conflicts | Keep in stash, report per repo |
