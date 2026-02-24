# Claude Code Agent System

This project is configured with Claude Code agents for **React + Next.js + Python FastAPI**.

## Quick Start

Say **"Use PM: [task description]"** to run the full orchestration pipeline.

```
Use PM: Add user authentication with JWT tokens
```

Or use slash commands for specific tasks:

```
/test          Run tests
/review        Code review
/eval          Quality evaluation
/security      Security audit
```

## Available Agents

| Agent | Role | Model |
|-------|------|-------|
| `frontend-developer` | Senior Next.js developer for production code | opus |
| `frontend-tester` | Jest + Playwright testing specialist | sonnet |
| `frontend-reviewer` | React/Next.js code reviewer | opus |
| `backend-developer` | FastAPI backend developer | opus |
| `backend-tester` | pytest testing specialist | sonnet |
| `backend-reviewer` | Python/FastAPI code reviewer | opus |

## Slash Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `/pm` | Run full orchestration pipeline |
| `/delegate` | Smart task delegation |
| `/parallel` | Run tasks in parallel worktrees |
| `/sequential` | Run pipeline stages in sequence |
| `/recap` | Load session context and show status |
| `/eval` | Run quality evaluation |
| `/security` | Run security audit |

### Git Workflow Commands

| Command | Description |
|---------|-------------|
| `/branch <name>` | Create a feature branch |
| `/ship` | Commit, push, and create PR |
| `/sync` | Sync branch with main |

### Stack Commands

#### React + Next.js

| Command | Description |
|---------|-------------|
| `/test` | Test |
| `/review` | Review |
| `/docs` | Docs |
| `/verify` | Verify |
| `/new-component` | Create Component |
| `/new-page` | Create Page |
| `/new-container` | Create Container |
| `/new-context` | Create Context |
| `/new-form` | Create Form |
| `/new-api-service` | Create Api Service |
| `/new-server-action` | Create Server Action |
| `/new-hook` | Create Hook |
| `/new-layout` | Create Layout |
| `/clone-page` | Clone Page |
| `/analyze-site` | Analyze Site |

#### Python FastAPI

| Command | Description |
|---------|-------------|
| `/test` | Test |
| `/review` | Review |
| `/docs` | Docs |
| `/verify` | Verify |
| `/new-router` | Create Router |
| `/new-schema` | Create Schema |
| `/new-model` | Create Model |
| `/new-service` | Create Service |
| `/new-migration` | Create Migration |
| `/db-migrate` | Db Migrate |
| `/new-test` | Create Test |
| `/new-task` | Create Task |
| `/new-middleware` | Create Middleware |
| `/new-dependency` | Create Dependency |

## Quality Gates

Before code review, these checks must pass:

### React + Next.js
**Working directory:** `web`

| Gate | Command |
|------|---------|
| Typecheck | `cd web && npx tsc --noEmit` |
| Lint | `cd web && npm run lint` |
| Tests | `cd web && npm test` |

### Python FastAPI
**Working directory:** `backend`

| Gate | Command |
|------|---------|
| Format | `cd backend && uv run ruff format --check src/ tests/` |
| Lint | `cd backend && uv run ruff check src/ tests/` |
| Typecheck | `cd backend && uv run mypy src/` |
| Tests | `cd backend && uv run pytest` |


## Project Structure

```
.claude/
├── agents/          # Agent definitions
├── skills/          # Slash command implementations
├── hooks/           # Event hooks (session save/load)
├── context/
│   └── features/    # Feature tracking files
├── patterns/        # Code pattern references
├── styles/          # Style guides
├── settings.json    # Shared settings
└── README.md        # This file
```

## Feature Tracking

Track features in `.claude/context/features/`:

```bash
# Create a new feature file
touch .claude/context/features/$(date +%Y%m%d)-my-feature.md
```

Feature files track:
- Status (PLANNING, IN_PROGRESS, TESTING, IN_REVIEW, COMPLETE)
- Requirements checklist
- Technical approach
- Task assignments

## Session Memory

Your session context is automatically saved to `.claude/context/active-work.md` after each response.

Use `/recap` to restore context in a new session and see:
- Current branch and git status
- In-progress features
- Recent commits
- Pipeline state

## Configuration

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Shared settings (committed) |
| `.claude/settings.local.json` | Personal overrides (gitignored) |

### Git Workflow Automation

Configure automatic branch creation and PR submission in `settings.json`:

```json
{
  "pm": {
    "git_workflow": "full"
  }
}
```

| Setting | Behavior |
|---------|----------|
| `"none"` | No git automation (default) |
| `"branch"` | Auto-create branch after plan approval |
| `"full"` | Auto-create branch + PR on completion |

**PM flags to override per-task:**

```
/pm Add feature --branch    # Create branch only
/pm Add feature --ship      # Full automation
/pm Add feature --no-git    # Disable automation
```

## Patterns and Styles

Reference these when writing code:

- **frontend-patterns.md** - Code patterns and examples
- **auth.md** - Code patterns and examples
- **pagination.md** - Code patterns and examples
- **i18n.md** - Code patterns and examples
- **logging.md** - Code patterns and examples
- **error-tracking.md** - Code patterns and examples
- **browser-cloning.md** - Code patterns and examples
- **verification.md** - Code patterns and examples
- **zustand.md** - Code patterns and examples
- **backend-patterns.md** - Code patterns and examples
- **oauth.md** - Code patterns and examples
- **rate-limiting.md** - Code patterns and examples
- **caching.md** - Code patterns and examples
- **frontend-typescript.md** - Style conventions
- **tailwind.md** - Style conventions
- **backend-python.md** - Style conventions
- **async-patterns.md** - Style conventions

---

*Generated by [Buildmate](https://github.com/vadim7j7/buildmate) for nextjs, fastapi*