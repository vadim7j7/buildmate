# Git Workflow Patterns

Standard git workflow conventions for feature development.

## Branch Naming

```
<type>/<short-description>
```

| Type | Purpose | Example |
|------|---------|---------|
| `feature/` | New functionality | `feature/user-authentication` |
| `fix/` | Bug fixes | `fix/login-timeout` |
| `chore/` | Maintenance, deps | `chore/update-dependencies` |
| `hotfix/` | Urgent production fixes | `hotfix/security-patch` |
| `refactor/` | Code restructuring | `refactor/api-service` |
| `docs/` | Documentation only | `docs/api-reference` |
| `test/` | Test additions | `test/integration-suite` |

### Naming Rules

- Use lowercase
- Use hyphens for spaces
- Keep it short but descriptive
- Include issue number if applicable: `fix/123-login-timeout`

## Commit Messages

Use conventional commits format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature for the user |
| `fix` | Bug fix for the user |
| `chore` | Maintenance, no user impact |
| `refactor` | Code change, no behavior change |
| `docs` | Documentation only |
| `test` | Adding/updating tests |
| `style` | Formatting, no code change |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |

### Scope

Optional, indicates the area of change:

- `auth`, `api`, `ui`, `db`, `config`
- Component/module name: `navbar`, `user-service`

### Examples

```bash
# Feature
feat(auth): add OAuth2 login with Google

# Bug fix
fix(api): handle null response in user endpoint

# Chore
chore(deps): upgrade React to v18.2

# With body
feat(checkout): add PayPal payment option

Integrates PayPal SDK for payment processing.
Supports both one-time and subscription payments.

Closes #123
```

### Multi-line Commits

For complex changes, add a body:

```bash
git commit -m "$(cat <<'EOF'
feat(api): implement rate limiting

- Add sliding window rate limiter
- Configure per-endpoint limits
- Add Redis backend for distributed limiting

Breaking: API now returns 429 for rate-limited requests

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Pull Request Guidelines

### Title

Match the primary commit or summarize changes:

```
feat(auth): Add OAuth2 login with Google
fix: Resolve login timeout issue (#123)
```

### Description Template

```markdown
## Summary

Brief description of what this PR does.

## Changes

- Added X
- Modified Y
- Removed Z

## Test Plan

- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] Edge cases considered

## Screenshots

(if UI changes)

## Linked Issues

Closes #123
Related to #456
```

### Labels

| Label | Purpose |
|-------|---------|
| `bug` | Bug fix |
| `feature` | New feature |
| `breaking` | Breaking change |
| `documentation` | Docs update |
| `dependencies` | Dependency update |
| `needs-review` | Ready for review |
| `wip` | Work in progress |

## Workflow Strategies

### Feature Branch Workflow

```
main
  └── feature/user-auth (your work)
        ├── commit 1
        ├── commit 2
        └── commit 3 → PR → merge to main
```

1. Create branch from main: `/branch user-auth`
2. Make commits
3. Keep synced: `/sync`
4. Ship when ready: `/ship`

### Git Flow (for releases)

```
main (production)
  └── develop (integration)
        └── feature/user-auth
```

Use `--base develop` when creating branches:
```
/branch user-auth --base develop
```

### Trunk-Based Development

```
main
  └── short-lived feature branches (< 1 day)
```

Ship frequently, keep branches short:
```
/branch quick-fix
# ... minimal changes ...
/ship
```

## Keeping Branches Fresh

### Rebase (Preferred for Personal Branches)

```bash
git fetch origin
git rebase origin/main
git push --force-with-lease
```

Or use: `/sync`

### Merge (For Shared Branches)

```bash
git fetch origin
git merge origin/main
git push
```

Or use: `/sync --merge`

## Conflict Resolution

### Understanding Conflicts

```
<<<<<<< HEAD
your changes
=======
incoming changes
>>>>>>> origin/main
```

### Resolution Steps

1. Identify the conflict in context
2. Decide which changes to keep
3. Remove conflict markers
4. Test the resolved code
5. Stage and continue: `git add . && git rebase --continue`

### Common Scenarios

| Scenario | Resolution |
|----------|------------|
| Both modified same line | Combine or choose one |
| Both added to same location | Order appropriately |
| One deleted, one modified | Keep modification or accept deletion |
| Schema/config changes | Merge carefully, validate |

## Protected Branches

Never push directly to protected branches:

- `main` / `master`
- `production`
- `release/*`

Always use pull requests with required reviews.

## Automation with PM Workflow

Configure git automation in `.claude/settings.json`:

```json
{
  "pm": {
    "git_workflow": "full"
  }
}
```

Options:
- `"none"` — No git automation (manual control)
- `"branch"` — Auto-create branch after plan approval
- `"full"` — Auto-create branch + PR on completion

### Automated Flow

```
User: /pm Add user authentication

Phase 1: Planning
  → User approves plan
  → /branch feature/user-authentication (auto)

Phase 2-5: Implementation, Testing, Review

Phase 6: Completion
  → All gates pass
  → /ship (auto)
  → PR created and ready for review
```

---

## Multi-Repository Workflows

For workspaces with multiple git repositories (e.g., separate backend, frontend, mobile repos).

### Configuration

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

### How It Works

| Operation | Single Repo | Multi-Repo |
|-----------|-------------|------------|
| `/branch` | Creates one branch | Creates branches in all relevant repos |
| `/ship` | One commit, one PR | Commits + linked PRs across repos |
| `/sync` | Syncs one branch | Syncs all repos with same branch |

### Branch Naming Across Repos

All repos use the same branch name for coordination:

```
workspace/           → feature/user-auth
├── backend/         → feature/user-auth
├── web/             → feature/user-auth
└── mobile/          → feature/user-auth
```

### Linked Pull Requests

PRs are cross-linked for easy navigation:

```markdown
## Related PRs

| Repository | PR | Status |
|------------|-----|--------|
| backend | #42 | Open |
| web | #18 | Open |
| mobile | - | No changes |
```

### Stack-to-Repo Mapping

The `stack_repo_map` determines which repos are involved:

```
/pm Add user login --stacks rails,nextjs

→ Branches created in: backend, web
→ PRs created in: backend, web
→ Mobile skipped (not in stacks)
```

### Merge Order

For features spanning multiple repos with dependencies:

1. **Backend first** — API changes must be deployed before frontend
2. **Frontend second** — Consumes the new API
3. **Mobile last** — May need API deployed to production

### Workspace Repository

The workspace repo can track:
- Shared configuration
- Documentation
- Orchestration files
- Umbrella PRs that link sub-repo PRs

### Best Practices

1. **Consistent branch names** — Same name across all repos
2. **Atomic features** — Ship related changes together
3. **API contracts first** — Define interfaces before parallel work
4. **Cross-link PRs** — Easy navigation between related changes
5. **Merge order** — Respect dependencies between repos
