# Agent System Overview

This project uses a multi-agent architecture powered by Claude Code. A single
main agent orchestrates work by delegating to specialised sub-agents through
the **Task** tool. Sub-agents never spawn their own sub-agents; only the main
agent delegates.

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
|------------|--------------------------|--------------------------------------------|
| Plan       | project-manager          | Break task into sub-tasks, create feature file |
| Implement  | implementer              | Write production code                      |
| Test       | tester                   | Write and run tests                        |
| Review     | reviewer                 | Code review, find issues                   |
| Eval       | eval-agent               | Score against quality rubrics              |
| Security   | security-auditor         | OWASP scan, vulnerability check            |
| Docs       | documentation-specialist | Generate / update documentation            |

Stages in parentheses are optional and run when explicitly requested or when
the task warrants it.

## Delegation Rules

1. **Only the main agent delegates.** Sub-agents receive a task, execute it,
   and return results. They never call the Task tool themselves.
2. **One responsibility per agent.** Each sub-agent owns a single concern
   (testing, reviewing, etc.).
3. **Context flows forward.** Each stage writes its output to
   `.agent-pipeline/<stage>.md` so the next stage can read it.
4. **Failures stop the pipeline.** If a stage fails, the pipeline halts and
   the main agent reports the failure with actionable details.

## Feature Tracking

Features are tracked as markdown files in `.claude/context/features/`.

### Creating a Feature File

```bash
# Convention: YYYYMMDD-short-slug.md
touch .claude/context/features/20260201-user-auth.md
```

Each feature file should contain:

```markdown
# Feature: <title>

## Status
<!-- one of: planned | in-progress | testing | review | done -->
in-progress

## Description
<what this feature does and why>

## Tasks
- [ ] Task 1
- [ ] Task 2

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Notes
<any context, decisions, or trade-offs>
```

The PM agent creates and updates these files automatically when you use
`Use PM: ...`.

## Quality Gates

Before the review stage, the following gates **must** pass:

| Gate             | Command (stack-dependent)        | Requirement          |
|------------------|----------------------------------|----------------------|
| TypeScript check | `npx tsc --noEmit` (or equiv.)   | Zero errors          |
| Lint             | `npm run lint` (or equiv.)       | Zero errors          |
| Tests            | `npm test` (or equiv.)           | All passing          |

If any gate fails, the implementing agent must fix the issues before
proceeding. The reviewer agent will reject work that has not passed all gates.

## Available Slash Commands

| Command       | Description                                                |
|---------------|------------------------------------------------------------|
| `/test`       | Delegate to the stack's tester agent to run tests          |
| `/review`     | Delegate to the stack's reviewer agent for code review     |
| `/eval`       | Run quality evaluation against scoring rubrics             |
| `/security`   | Run a security audit (OWASP Top 10)                        |
| `/docs`       | Generate or update documentation for changed files         |
| `/delegate`   | Smart delegation - auto-picks parallel or sequential       |
| `/parallel`   | Run multiple tasks in parallel via git worktrees           |
| `/sequential` | Run tasks through the pipeline in order                    |
| `/resume`     | Load saved context and show a detailed status summary      |

## Parallel vs Sequential Execution

### Sequential (`/sequential`)

Tasks run one after another. Each stage's output feeds into the next as
context. Use this for the standard implement-test-review pipeline where each
stage depends on the previous one.

```
implement --> test --> review --> eval --> docs
     |          |        |         |        |
     v          v        v         v        v
  stage.md   stage.md  stage.md  stage.md  stage.md
```

All stage artefacts are written to `.agent-pipeline/` so the chain of context
is preserved.

### Parallel (`/parallel`)

Independent tasks run simultaneously in separate git worktrees. Use this when
tasks do not depend on each other (e.g., implementing unrelated features,
running security audit while docs are generated).

```
main branch
  |-- worktree-1  (task A)
  |-- worktree-2  (task B)
  |-- worktree-3  (task C)
```

- Maximum of **5** concurrent worktrees.
- Each worktree gets its own agent instance.
- Results are collected and merged when all agents complete.
- Worktrees are cleaned up automatically.

### Smart Delegation (`/delegate`)

If you are unsure whether tasks should be parallel or sequential, use
`/delegate`. It analyses the tasks, checks for dependencies, and routes to the
appropriate execution mode automatically.

## Session Memory

The agent system includes automatic session persistence so context survives
between Claude Code sessions.

### How It Works

- **After each response** (Stop event): The `session-save.sh` hook automatically
  captures the current git state (branch, recent commits, uncommitted changes),
  in-progress feature files, and pipeline state. Everything is written to
  `.claude/context/active-work.md`. This runs after every Claude response, so
  the saved context is always up to date even if the session ends unexpectedly.
- **On session start** (SessionStart event): The `session-load.sh` hook reads
  `active-work.md` and injects it into the conversation context so the agent
  immediately knows where you left off. If the file is older than 7 days, a
  staleness warning is shown instead.

### `/resume` Command

For a more detailed status check, use the `/resume` skill. It reads:

1. `active-work.md` — last session's saved context
2. Feature files in `.claude/context/features/` — in-progress features and
   remaining tasks
3. Git state — current branch, uncommitted changes, recent commits, stashes
4. Pipeline state — `.agent-pipeline/pipeline.json` if a pipeline was running
5. Eval results — latest report in `.agent-eval-results/`

`/resume` is **read-only** — it never modifies files or runs state-changing
commands. Use it at the start of a session or any time you want to orient
yourself.

### Files

| File | Purpose |
|------|---------|
| `.claude/context/active-work.md` | Auto-saved session context (git state, features, pipeline) |
| `.claude/hooks/session-save.sh` | Stop event hook — writes active-work.md |
| `.claude/hooks/session-load.sh` | SessionStart event hook — loads active-work.md into context |
| `.claude/skills/resume/SKILL.md` | `/resume` skill definition |
