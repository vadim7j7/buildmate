# Agents

Agent roles, responsibilities, and delegation patterns used by the agent template system.

---

## Table of Contents

- [Overview](#overview)
- [Shared Agents](#shared-agents)
- [Rails Stack Agents](#rails-stack-agents)
- [React + Next.js Stack Agents](#react--nextjs-stack-agents)
- [React Native Stack Agents](#react-native-stack-agents)
- [Full-Stack Agents](#full-stack-agents)
- [Delegation Patterns](#delegation-patterns)
- [Agent Communication Protocol](#agent-communication-protocol)
- [Quality Gates](#quality-gates)
- [Customizing Agents](#customizing-agents)

---

## Overview

The agent system uses a multi-agent architecture where a single **main agent** coordinates work by delegating to **specialist sub-agents** through the Task tool. Sub-agents never spawn their own sub-agents -- only the main agent delegates.

Each agent is defined as a Markdown file with YAML frontmatter that specifies its name, description, available tools, and model. The body of the file contains the agent's instructions, workflows, and patterns.

---

## Shared Agents

These agents are included in every stack. They provide cross-cutting capabilities that are not specific to any technology.

| Agent | File | Role | Tools | When to Use |
|-------|------|------|-------|-------------|
| **PM (Orchestrator)** | `orchestrator.md` | Workflow guide that coordinates feature development through the full pipeline. Reads requirements, creates feature files, delegates to specialist agents, tracks progress, enforces quality gates. | Read, Write, Edit, Bash, Grep, Glob, Task | When building a complete feature end-to-end. Invoked with "Use PM: ..." or "/pm". |
| **Eval Agent** | `eval-agent.md` | Quality evaluation agent. Scores code changes across five dimensions (correctness, code quality, security, performance, test coverage) using a weighted formula. Produces structured evaluation reports with numerical scores. | Read, Bash, Grep, Glob | After implementation and testing, to get an objective quality score. Invoked with `/eval`. |
| **Security Auditor** | `security-auditor.md` | Security vulnerability scanner. Audits code for OWASP Top 10 vulnerabilities, injection attacks, authentication/authorization flaws, sensitive data exposure, and hardcoded secrets. Produces severity-classified findings. | Read, Grep, Glob, Bash | Before merging security-sensitive changes (auth, user input, API endpoints, data access). Invoked with `/security`. |
| **Regression Monitor** | `regression-monitor.md` | Pre-merge regression checker. Verifies existing tests pass, checks for breaking API changes, validates backwards compatibility, and ensures no public exports have been removed. | Read, Bash, Grep, Glob | Before merging changes that modify public interfaces, API endpoints, database schemas, or shared utilities. |
| **Documentation Specialist** | `documentation-specialist.md` | Documentation generator. Creates and updates inline code documentation (JSDoc, docstrings, YARD), API docs, component docs, and architecture overviews. | Read, Write, Edit, Grep, Glob, Bash | After features are implemented and reviewed, to ensure code is properly documented. Invoked with `/docs`. |

---

## Rails Stack Agents

These agents are specific to the Ruby on Rails stack. The orchestrator replaces the shared one with Rails-specific workflows and agent references.

| Agent | File | Role | Tools | When to Use |
|-------|------|------|-------|-------------|
| **PM (Orchestrator)** | `orchestrator.md` | Rails-specific orchestration guide. Coordinates backend-developer, backend-tester, and backend-reviewer agents. References Rails patterns, Rubocop, RSpec. | Read, Write, Edit, Bash, Grep, Glob, Task | Full feature development in a Rails project. |
| **Backend Developer** | `backend-developer.md` | Senior Rails developer. Writes production-quality services, controllers, models, presenters, jobs, and migrations following established project patterns. | Read, Write, Edit, Bash, Grep, Glob | Implementation of any Rails backend code. |
| **Backend Tester** | `backend-tester.md` | RSpec testing specialist. Writes comprehensive model, request, and service specs using FactoryBot, Shoulda Matchers, and project conventions. | Read, Write, Edit, Bash, Grep, Glob | Writing and running tests for Rails code. |
| **Backend Reviewer** | `backend-reviewer.md` | Rails code reviewer. Reviews code against Rails conventions, N+1 query prevention, security (strong params, auth), and quality standards. | Read, Grep, Glob, Bash | Code review before merging Rails changes. |

---

## React + Next.js Stack Agents

These agents are specific to the React + Next.js stack. The orchestrator replaces the shared one with frontend-specific workflows.

| Agent | File | Role | Tools | When to Use |
|-------|------|------|-------|-------------|
| **PM (Orchestrator)** | `orchestrator.md` | React/Next.js orchestration guide. Coordinates frontend-developer, frontend-tester, and frontend-reviewer agents. References Next.js App Router, Mantine UI, TypeScript. | Read, Write, Edit, Bash, Grep, Glob, Task | Full feature development in a React/Next.js project. |
| **Frontend Developer** | `frontend-developer.md` | Senior Next.js developer. Implements pages, components, containers, services, contexts, and forms using React 18+, Next.js 14+ App Router, TypeScript strict mode, and Mantine UI v7+. | Read, Write, Edit, Bash, Grep, Glob | Implementation of any frontend code. |
| **Frontend Tester** | `frontend-tester.md` | Frontend testing specialist. Writes Jest + React Testing Library unit tests and Playwright end-to-end tests. | Read, Write, Edit, Bash, Grep, Glob | Writing and running tests for React/Next.js code. |
| **Frontend Reviewer** | `frontend-reviewer.md` | Frontend code reviewer. Reviews code for React best practices, Next.js conventions, TypeScript correctness, Mantine UI usage, accessibility, and performance. | Read, Grep, Glob, Bash | Code review before merging frontend changes. |

---

## React Native Stack Agents

These agents are specific to the React Native + Expo stack.

| Agent | File | Role | Tools | When to Use |
|-------|------|------|-------|-------------|
| **PM (Orchestrator)** | `orchestrator.md` | React Native orchestration guide. Coordinates mobile-developer, mobile-tester, and mobile-code-reviewer agents. References Expo SDK 54, Zustand, React Query, Drizzle ORM. | Read, Write, Edit, Bash, Grep, Glob, Task | Full feature development in a React Native project. |
| **Mobile Developer** | `mobile-developer.md` | Expert React Native developer. Writes production-quality mobile code using Expo SDK 54, TypeScript strict mode, Zustand for UI state, React Query for server state, Drizzle ORM for database, FlashList for lists, and expo-router for navigation. | Read, Write, Edit, Bash, Grep, Glob | Implementation of any mobile code. |
| **Mobile Tester** | `mobile-tester.md` | React Native testing specialist. Writes and runs Jest + React Native Testing Library tests for components, screens, Zustand stores, React Query hooks, and Drizzle database queries. | Read, Write, Edit, Bash, Grep, Glob | Writing and running tests for mobile code. |
| **Mobile Code Reviewer** | `mobile-code-reviewer.md` | React Native code reviewer. Reviews code against mobile architecture conventions, state management boundaries (Zustand vs React Query vs Drizzle), performance patterns, and platform-specific correctness. | Read, Grep, Glob, Bash | Code review before merging mobile changes. |

---

## Full-Stack Agents

The fullstack stack combines agents from both Rails and React + Next.js. It uses the shared orchestrator (or a fullstack-specific override if provided) and includes agents from both the backend and frontend stacks.

Currently, the fullstack stack's `agents/` directory is empty, meaning it inherits all shared agents without overrides. When using the fullstack stack, you typically delegate backend work to rails-style agents and frontend work to react-style agents within the same orchestration pipeline.

---

## Delegation Patterns

### How the Orchestrator Works

The orchestrator (PM) is a **workflow guide, not a spawnable agent**. When triggered with "Use PM: ..." or "/pm", the main Claude agent reads the orchestrator file and follows its instructions directly. The main agent IS the PM -- it does not spawn itself as a sub-agent.

**Correct usage:**
```
Use PM: Build a user authentication system with OAuth support
```

**Incorrect usage (do NOT do this):**
```
Task("Follow the PM workflow to build auth")    // WRONG
Task("Act as PM and coordinate building auth")  // WRONG
```

The orchestrator drives the full feature lifecycle:

1. **Planning** -- Reads requirements, checks existing code, creates a feature file in `.claude/context/features/`
2. **Implementation** -- Delegates to the developer agent via Task tool
3. **Testing** -- Delegates to the tester agent via Task tool
4. **Review** -- Delegates to the reviewer agent via Task tool
5. **Evaluation** -- Optionally runs the eval-agent for quality scoring
6. **Completion** -- Updates the feature file, reports to the user

### Sequential Pipeline

The standard execution mode where each stage runs in order and feeds context to the next:

```
implement --> test --> review --> eval --> docs
     |          |        |         |        |
     v          v        v         v        v
  stage.md   stage.md  stage.md  stage.md  stage.md
```

Each stage writes its output to `.agent-pipeline/<stage>.md`, which the next stage reads as context. This ensures that:

- The tester knows what was implemented
- The reviewer knows what was implemented and tested
- The eval agent has full context from all previous stages

Use sequential execution when stages depend on each other. Invoke with `/sequential`:

```
/sequential implement test review
/sequential implement test review eval docs
/sequential --from test    # Resume from the test stage
```

### Parallel Worktrees

For independent tasks that do not share dependencies, use parallel execution via git worktrees:

```
main branch
  |-- worktree-1  (task A)
  |-- worktree-2  (task B)
  |-- worktree-3  (task C)
```

Each worktree gets its own isolated branch and agent instance. Results are collected and merged when all agents complete. Maximum 5 concurrent worktrees.

Invoke with `/parallel`:

```
/parallel "Build login page" "Build signup page" "Build dashboard"
```

Parallel execution is appropriate when:
- Tasks modify different files
- Tasks do not depend on each other's output
- Tasks work on separate features or layers

### Smart Delegation

If you are unsure whether tasks should run in parallel or sequentially, use `/delegate`. It analyzes the tasks for dependencies and routes to the correct execution mode:

```
/delegate Implement user auth, add rate limiting, write API docs
```

The delegate skill:
1. Parses tasks from the input
2. Analyzes dependencies between tasks (data, order, resource)
3. Builds a dependency graph
4. Routes to `/parallel`, `/sequential`, or a hybrid approach
5. Reports the delegation plan before executing

---

## Agent Communication Protocol

### Feature Files

Feature files in `.claude/context/features/` serve as the primary communication artifact between the orchestrator and the user. They track:

- Feature status (PLANNING, IN_PROGRESS, TESTING, IN_REVIEW, COMPLETE, BLOCKED)
- Requirements as a checklist
- Technical approach
- Task assignments with per-task status
- Completion criteria

### Pipeline Artifacts

When running the sequential pipeline, each stage writes its output to `.agent-pipeline/`:

| Artifact | Written By | Contents |
|----------|-----------|----------|
| `implement.md` | Developer agent | What was implemented, files changed, notes |
| `test.md` | Tester agent | Test results, pass/fail counts, failure details |
| `review.md` | Reviewer agent | Review findings (blockers, warnings, suggestions), verdict |
| `eval.md` | Eval agent | Quality scores across five dimensions, grade |
| `security.md` | Security auditor | Security findings by severity, OWASP checklist |
| `docs.md` | Documentation specialist | What was documented, files created/updated |
| `pipeline.json` | Pipeline runner | Stage status tracking (pending, in_progress, completed, failed) |

The `.agent-pipeline/` directory is gitignored -- it holds transient state for the current workflow.

### Agent Status (Parallel)

When running in parallel worktrees, each agent writes status to `.agent-status/` in its worktree:

| File | Purpose |
|------|---------|
| `progress.md` | Periodic progress updates |
| `result.md` | Final result when the agent completes |

---

## Quality Gates

Quality gates are enforced at the transition from implementation to review. The specific gates depend on the stack:

### Rails Quality Gates

| Gate | Command | Requirement |
|------|---------|-------------|
| Lint | `bundle exec rubocop` | Zero offenses |
| Tests | `bundle exec rspec` | All passing |
| Eval | Eval agent score | >= 0.7 |

### React + Next.js Quality Gates

| Gate | Command | Requirement |
|------|---------|-------------|
| TypeScript | `npx tsc --noEmit` | Zero errors |
| Lint | `npm run lint` | Zero errors |
| Tests | `npm test` | All passing |
| Eval | Eval agent score | >= 0.7 |

### React Native Quality Gates

| Gate | Command | Requirement |
|------|---------|-------------|
| TypeScript | `npx tsc --noEmit` | Zero errors |
| Lint | `npm run lint` | Zero errors |
| Tests | `npm test` | All passing |

If any gate fails, the implementing agent must fix the issues before the pipeline proceeds to review. The reviewer agent will reject work that has not passed all gates.

---

## Customizing Agents

### Modifying an Existing Agent

After bootstrap, agent files live in `<project>/.claude/agents/`. Edit them directly to customize for your project:

1. Open the agent file (e.g., `.claude/agents/backend-developer.md`)
2. Modify the instructions, patterns, or conventions
3. Keep the YAML frontmatter intact (name, description, tools, model)
4. Commit your changes

### Adding a New Agent

Create a new Markdown file in `.claude/agents/` following this format:

```markdown
---
name: my-custom-agent
description: Description of what this agent does
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
---

# My Custom Agent

Instructions for the agent go here. Include:

- What the agent's role is
- What tools it should use and how
- Patterns and conventions to follow
- Output format expectations
- Completion checklist
```

### Agent Design Principles

When creating or modifying agents, follow these principles:

1. **Single responsibility.** Each agent should own one concern (implementing, testing, reviewing, etc.).
2. **Clear instructions.** Agents should know exactly what to do without ambiguity.
3. **Reference patterns.** Point agents to pattern files and style guides rather than embedding all rules inline.
4. **Include examples.** Show agents what good output looks like with concrete code examples.
5. **Define completion criteria.** Specify what "done" means, including commands to run and checks to pass.
6. **Never self-delegate.** Sub-agents should never use the Task tool to spawn further sub-agents.

---

## Related Documentation

- [BOOTSTRAP.md](BOOTSTRAP.md) -- How to use bootstrap.sh
- [SKILLS.md](SKILLS.md) -- Skill descriptions and usage
- [EVALS.md](EVALS.md) -- How to run quality evaluations
- [ADDING-A-STACK.md](ADDING-A-STACK.md) -- How to add a new stack template
