# Agent System Overview

This project uses a multi-agent architecture powered by Claude Code. A single
main agent orchestrates work by delegating to specialised sub-agents through
the **Task** tool. Sub-agents never spawn their own sub-agents; only the main
agent delegates.

**Configured stacks:** React + Next.js, Python FastAPI

## Quick Start

Say **"Use PM: [task description]"** in any conversation to trigger the full
orchestration pipeline. The PM (project-manager) agent will break the task
down, create a feature file, and drive the pipeline to completion.

## Agent Pipeline

Every non-trivial task flows through the following stages:

```
Plan --> Implement --> Test --> Review --> (Eval --> Security --> Docs)
```

| Stage      | Agent                    | Purpose                                    |
|------------|--------------------------|-------------------------------------------|
| Plan       | PM (orchestrator)        | Break task into sub-tasks, create feature |
| Implement  | *-developer              | Write production code                     |
| Test       | *-tester                 | Write and run tests                       |
| Review     | *-reviewer               | Code review, find issues                  |
| Grind      | grind                    | Fix-verify loops until quality gates pass |
| Eval       | eval-agent               | Score against quality rubrics             |
| Security   | security-auditor         | OWASP scan, vulnerability check           |

Stages in parentheses are optional and run when explicitly requested.

## Available Agents

| Agent | Description | Model |
|-------|-------------|-------|
| `frontend-developer` | Senior Next.js developer for production code | opus |
| `frontend-tester` | Jest + Playwright testing specialist | sonnet |
| `frontend-reviewer` | React/Next.js code reviewer | opus |
| `backend-developer` | FastAPI backend developer | opus |
| `backend-tester` | pytest testing specialist | sonnet |
| `backend-reviewer` | Python/FastAPI code reviewer | opus |

## Quality Gates

Before the review stage, the following gates **must** pass:

### React + Next.js
**Working directory:** `web`

| Gate | Command | Requirement |
|------|---------|-------------|
| Typecheck | `cd web && npx tsc --noEmit` | Zero errors |
| Lint | `cd web && npm run lint` | Zero errors |
| Tests | `cd web && npm test` | Zero errors |

### Python FastAPI
**Working directory:** `backend`

| Gate | Command | Requirement |
|------|---------|-------------|
| Format | `cd backend && uv run ruff format --check src/ tests/` | Zero errors |
| Lint | `cd backend && uv run ruff check src/ tests/` | Zero errors |
| Typecheck | `cd backend && uv run mypy src/` | Zero errors |
| Tests | `cd backend && uv run pytest` | Zero errors |


If any gate fails, the **grind agent** runs fix-verify loops until all gates
pass or max iterations are reached.

## Available Slash Commands

### Core Commands

| Command | Description |
|---------|-------------|
| `/pm` | Run the full PM orchestration pipeline |
| `/delegate` | Smart task delegation (auto-picks parallel/sequential) |
| `/parallel` | Run multiple tasks in parallel via git worktrees |
| `/sequential` | Run tasks through the pipeline in order |
| `/recap` | Load saved context and show status summary |
| `/eval` | Run quality evaluation |
| `/security` | Run security audit |

### Git Workflow Commands

| Command | Description |
|---------|-------------|
| `/branch <name>` | Create a feature branch |
| `/ship` | Commit, push, and create PR |
| `/sync` | Sync branch with main/master |

Configure automation in `.claude/settings.json`:

```json
{
  "pm": {
    "git_workflow": "full"  // "none" | "branch" | "full"
  }
}
```

With `"full"`, PM auto-creates branches and ships PRs on completion.

### Stack Commands

#### React + Next.js

| Command | Description |
|---------|-------------|
| `/test` | Test |
| `/review` | Review |
| `/docs` | Docs |
| `/verify` | Verify |
| `/new-component` | New Component |
| `/new-page` | New Page |
| `/new-container` | New Container |
| `/new-context` | New Context |
| `/new-form` | New Form |
| `/new-api-service` | New Api Service |
| `/new-server-action` | New Server Action |
| `/new-hook` | New Hook |
| `/new-layout` | New Layout |
| `/clone-page` | Clone Page |
| `/analyze-site` | Analyze Site |

#### Python FastAPI

| Command | Description |
|---------|-------------|
| `/test` | Test |
| `/review` | Review |
| `/docs` | Docs |
| `/verify` | Verify |
| `/new-router` | New Router |
| `/new-schema` | New Schema |
| `/new-model` | New Model |
| `/new-service` | New Service |
| `/new-migration` | New Migration |
| `/db-migrate` | Db Migrate |
| `/new-test` | New Test |
| `/new-task` | New Task |
| `/new-middleware` | New Middleware |
| `/new-dependency` | New Dependency |

## Feature Tracking

Features are tracked as markdown files in `.claude/context/features/`.

```bash
# Convention: YYYYMMDD-short-slug.md
touch .claude/context/features/$(date +%Y%m%d)-my-feature.md
```

## Session Memory

The agent system includes automatic session persistence:

- **After each response:** Context is saved to `.claude/context/active-work.md`
- **On session start:** Previous context is loaded automatically
- **Use `/recap`:** For detailed status check at any time

## Delegation Rules

1. **Only the main agent delegates.** Sub-agents execute and return results.
2. **One responsibility per agent.** Each sub-agent owns a single concern.
3. **Context flows forward.** Each stage writes to `.agent-pipeline/<stage>.md`.
4. **Failures stop the pipeline.** The main agent reports actionable details.

---

*Generated by [Buildmate](https://github.com/vadim7j7/buildmate)*