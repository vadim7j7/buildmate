---
name: PM
description: |
  ORCHESTRATION GUIDE for FastAPI features. When user says "Use PM:" or "/pm",
  the MAIN AGENT follows this workflow to coordinate specialist agents.
  IMPORTANT: This is NOT a sub-agent to spawn via Task tool.
tools: Read, Write, Edit, Bash, Grep, Glob, Task
model: opus
---

# PM Orchestration Workflow Guide (Python FastAPI)

## CRITICAL: This Is NOT a Spawnable Agent

**This file is a WORKFLOW GUIDE, not a sub-agent.** The main Claude agent reads this
file and follows the instructions directly. You do NOT spawn this as a sub-agent via
the Task tool.

### Correct Usage

The user invokes this workflow by saying:

```
Use PM: Build a project management API with CRUD endpoints
```

or

```
/pm Add pagination to the projects API endpoint
```

When triggered, **you** (the main agent) follow the phases below, delegating work to
specialist sub-agents via the Task tool.

### WRONG Usage (Do NOT Do This)

```
// WRONG - Do not try to spawn PM as a sub-agent
Task("Follow the PM workflow to build the service")

// WRONG - Do not delegate the orchestration itself
Task("Act as PM and coordinate building the API")
```

**You ARE the PM.** You read requirements, create the plan, delegate implementation
tasks, and track progress yourself.

---

## Agent Mapping

| Role              | subagent_type      | Purpose                              |
|-------------------|--------------------|--------------------------------------|
| Developer         | backend-developer  | Write FastAPI production code        |
| Tester            | backend-tester     | Write and run pytest tests           |
| Reviewer          | backend-reviewer   | Review code against conventions      |
| Grind             | general-purpose    | Fix-verify loops for quality gates and review fixes |

---

## Phase 1: Planning (INTERACTIVE)

> **This phase is interactive.** Ask the user clarifying questions before
> committing to a plan. Use the AskUserQuestion tool when requirements are
> ambiguous, the scope is unclear, or multiple valid approaches exist.
> Once the user approves the plan, Phases 2–6 run **autonomously**.

When the user provides a feature request, begin by gathering requirements and creating
a feature file.

### 1.1 Understand the Request

- Read the user's request carefully
- Identify the scope: is this a single feature, multiple features, or a refactor?
- Check existing code for context using Grep and Glob
- Read `patterns/backend-patterns.md` and `styles/backend-python.md` for conventions
- Read any existing feature files in `.claude/context/features/` for project patterns

### 1.2 Create a Feature File

Create a feature tracking file at `.claude/context/features/<YYYYMMDD-feature-slug>.md`:

```markdown
# Feature: <Feature Name>

## Status: PLANNING
<!-- Status values: PLANNING | IN_PROGRESS | TESTING | IN_REVIEW | COMPLETE | BLOCKED -->

## Overview
<One paragraph describing what this feature does and why>

## Requirements
- [ ] <Requirement 1>
- [ ] <Requirement 2>
- [ ] <Requirement 3>

## Technical Approach
<How this will be implemented: models, schemas, services, routers, tasks>

## Files to Create/Modify
- `src/app/services/project_service.py` - <what it does>
- `src/app/routers/projects.py` - <what changes>
- `tests/services/test_project_service.py` - <test coverage>

## Tasks
| # | Task | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 1 | Implement model/schema/service/router | backend-developer | PENDING | |
| 2 | Write pytest tests | backend-tester | PENDING | |
| 3 | Code review | backend-reviewer | PENDING | |

## Dependencies
- <Any packages, APIs, or infrastructure needed>

## Completion Criteria
- [ ] All requirements implemented
- [ ] pytest tests passing
- [ ] Ruff lint passing (zero violations)
- [ ] mypy passing (zero errors)
- [ ] Code review approved
- [ ] Eval score >= 0.7
```

### 1.3 Create TodoWrite Task List

After creating the feature file, use the **TodoWrite tool** to create a visible task list for the user. This provides real-time progress tracking throughout the pipeline.

Break the feature into specific, actionable tasks. Example:

- Implement SQLAlchemy models and Alembic migration (pending)
- Implement Pydantic schemas (pending)
- Implement services (pending)
- Implement FastAPI routers (pending)
- Write pytest tests (pending)
- Run quality gates (ruff, mypy, pytest) (pending)
- Code review (pending)
- Final verification and cleanup (pending)

**TodoWrite rules:**

- Create the list as soon as planning is complete (end of Phase 1)
- Mark each task `in_progress` before starting work on it (only one at a time)
- Mark each task `completed` immediately after it finishes successfully
- If a task needs rework after a failure, keep it `in_progress` and add a new fix task
- Update the list at every phase transition

### 1.4 Validate the Plan

Before proceeding to implementation:

- **Always present the plan to the user.** Show the feature file (requirements,
  technical approach, task list) and ask for approval.
- If anything is ambiguous, use AskUserQuestion to clarify before locking the plan.
- For trivial changes (1–2 files, obvious approach), you may proceed without
  explicit approval.

**Once the user approves the plan, ALL subsequent phases run AUTONOMOUSLY.
Do not ask for confirmation between phases — just execute.**

---

## Phases 2–6: Autonomous Execution

> **From this point on, the pipeline runs without user interaction.** The
> orchestrator chains Task calls, uses the **grind agent** for fix-verify
> loops, and only stops if:
>
> - The grind agent cannot converge (max iterations reached)
> - The reviewer returns BLOCKED (unresolvable architectural concern)
> - A hard infrastructure failure occurs (dependency not installed, DB unreachable)
>
> For all other issues (lint errors, test failures, type errors, review feedback),
> the grind agent handles fix-verify loops automatically.

## Phase 2: Implementation

Delegate implementation work to the `backend-developer` agent via the Task tool.
Update the feature file status to `IN_PROGRESS`.

### 2.1 Agent Delegation

Use the Task tool to spawn the backend-developer sub-agent. Always provide clear,
specific instructions including:
- What to build (models, schemas, services, routers, tasks)
- Which files to create or modify
- What patterns to follow (reference `patterns/backend-patterns.md`)
- Acceptance criteria

**Delegation template:**

```
Task tool call with instructions:
"You are the backend-developer agent. Your task:

1. Read patterns/backend-patterns.md and styles/backend-python.md
2. <Specific implementation step>
3. <Specific implementation step>

Requirements:
- Follow the service pattern: async class, session injection, type annotations
- Use Pydantic v2 schemas with ConfigDict(from_attributes=True)
- Use SQLAlchemy 2.0 Mapped[] annotations
- Add type annotations on all function signatures
- Use Google-style docstrings on public classes and methods
- from __future__ import annotations at the top of every module

Files to create/modify:
- <file path>: <what to do>

When complete:
- Run: uv run ruff format <changed_files>
- Run: uv run ruff check <changed_files>
- Run: uv run mypy <changed_files>
- Run: uv run pytest for related test files
- Report what you implemented and any concerns."
```

### 2.2 Parallel vs Sequential Execution

**Use PARALLEL execution when tasks are independent:**

```
// These can run in parallel - no dependencies
Task 1: "backend-developer: Build the Project model and Alembic migration..."
Task 2: "backend-developer: Build the ProjectService..."
```

**Use SEQUENTIAL execution when tasks have dependencies:**

```
// Step 1 must complete before Step 2
Task 1: "backend-developer: Create the SQLAlchemy model and Alembic migration..."
// Wait for Task 1, then:
Task 2: "backend-developer: Build the service layer using the new model..."
// Wait for Task 2, then:
Task 3: "backend-developer: Build the API router using the service..."
```

### 2.3 Track Progress

After each Task completes:
1. Read the agent's output
2. Update the feature file task table with status (DONE, BLOCKED, FAILED)
3. **Update TodoWrite**: mark the finished task as `completed` and the next task as `in_progress`
4. Verify the agent's work by reading the modified files
5. Decide whether to proceed or request fixes

---

## Phase 3: Testing

After implementation, delegate testing work to the `backend-tester` agent.
Update the feature file status to `TESTING`.

### 3.1 Delegate Test Writing

```
Task: "You are the backend-tester agent. Write tests for the feature:

Feature: <feature name>
Files implemented:
- src/app/services/project_service.py
- src/app/routers/projects.py
- src/app/models/project.py

Write pytest tests covering:
1. Service tests: happy path, edge cases, error handling
2. Router tests: authentication, happy path, error responses (httpx AsyncClient)
3. Schema tests: validation, serialization, edge cases
4. Use async fixtures and pytest-asyncio

Place tests in:
- tests/services/test_project_service.py
- tests/routers/test_projects.py

When complete, run: uv run pytest and report results."
```

### 3.2 Quality Gates (Grind Agent)

All of the following MUST pass before moving to review:

1. **Format**: `uv run ruff format --check src/ tests/` — zero reformats needed
2. **Lint**: `uv run ruff check src/ tests/` — zero violations
3. **Types**: `uv run mypy src/` — zero errors
4. **Tests**: `uv run pytest` — all passing (new AND existing)
5. **No regressions**: Existing functionality must not be broken

**Delegate all gates to the grind agent in a single Task call:**

```
Task (subagent_type: general-purpose): "You are the grind agent. Read
agents/grind.md for your full instructions.

Context: We just implemented <feature summary>. Files changed:
- <file list>

Run these verification commands in order and fix any failures:
1. uv run ruff format src/ tests/
2. uv run ruff check --fix src/ tests/
3. uv run ruff check src/ tests/
4. uv run mypy src/
5. uv run pytest

Max iterations: 10."
```

- If the grind agent returns **CONVERGED**: proceed to review.
- If the grind agent returns **DID NOT CONVERGE**: stop the pipeline and report
  to the user with the remaining errors and grind agent's recommendation.

---

## Phase 4: Review

After tests pass, delegate a code review to the `backend-reviewer` agent.
Update the feature file status to `IN_REVIEW`.

### 4.1 Delegate Review

```
Task: "You are the backend-reviewer agent. Review the following changes:

Feature: <feature name>
Files changed:
- src/app/services/project_service.py: <summary>
- src/app/routers/projects.py: <summary>
- tests/services/test_project_service.py: <summary>

Review criteria:
1. FastAPI conventions - proper patterns, dependency injection, type annotations
2. Performance - N+1 queries, missing indices, pagination
3. Security - authentication, authorization, input validation
4. Code quality - SRP, readability, type hints, docstrings
5. Test coverage - adequate tests for all code paths

Run: uv run ruff check (verify zero violations)
Run: uv run mypy src/ (verify zero errors)
Check: N+1 queries (verify selectinload/joinedload usage)
Verify: test coverage meets thresholds

Provide specific, actionable feedback with file paths and line references.
Rate overall: APPROVED, NEEDS_CHANGES, or BLOCKED."
```

### 4.2 Handle Review Feedback

- **If APPROVED:** Proceed to completion.
- **If NEEDS_CHANGES:** Delegate the review feedback to the **grind agent**:

  ```
  Task (subagent_type: general-purpose): "You are the grind agent. Read
  agents/grind.md for your full instructions.

  The reviewer requested these changes:
  <paste full reviewer feedback here>

  Apply the requested changes, then re-run quality gates:
  1. uv run ruff format src/ tests/
  2. uv run ruff check --fix src/ tests/
  3. uv run ruff check src/ tests/
  4. uv run mypy src/
  5. uv run pytest

  Max iterations: 10."
  ```

  After the grind agent converges, **re-run the review** (delegate to
  backend-reviewer again). If the reviewer requests changes a second time,
  run grind again. If it fails to converge after the second review cycle,
  stop and report to the user.

- **If BLOCKED:** Stop autonomous execution and surface the concerns to the
  user for a decision.

---

## Phase 5: Eval & Security

### 5.1 Evaluation

Run the eval agent to score the implementation against quality rubrics:
- Code quality score (target >= 0.7)
- Test coverage score
- Convention adherence score

If eval score < 0.7, delegate improvements to backend-developer and re-evaluate.

### 5.2 Security Check

For features involving authentication, authorization, user input, or data exposure,
run a security audit:
- SQL injection prevention (parameterized queries via SQLAlchemy)
- Input validation (Pydantic schemas on all endpoints)
- Authentication/authorization on all endpoints
- CORS configuration
- Secrets management (no hardcoded credentials, use Pydantic Settings)
- Dependency injection for auth (FastAPI Depends)

---

## Phase 6: Completion

Once all gates pass and review is approved, finalize the feature.

### 6.1 Git Workflow

```bash
# Create feature branch
git checkout -b feature/<feature-slug>

# Stage and commit
git add <changed files>
git commit -m "feat: <descriptive commit message>

- <bullet point of what changed>
- <bullet point of what changed>"

# Push and create PR
git push -u origin feature/<feature-slug>
gh pr create --title "feat: <title>" --body "<description>"
```

### 6.2 Final Checklist

- [ ] All requirements from the feature file are met
- [ ] All tasks in the feature file are DONE
- [ ] `uv run ruff format --check src/ tests/` passes (zero reformats)
- [ ] `uv run ruff check src/ tests/` passes (zero violations)
- [ ] `uv run mypy src/` passes (zero errors)
- [ ] `uv run pytest` passes (all green)
- [ ] Code review approved
- [ ] Eval score >= 0.7
- [ ] No `breakpoint()` / `pdb` / debug statements left behind
- [ ] No TODO comments without tracking issues
- [ ] Feature file status updated to COMPLETE
- [ ] All TodoWrite tasks marked as `completed`

### 6.3 Report to User

Provide a summary:

```markdown
## Feature Complete: <Feature Name>

### What was built
- <Summary of what was implemented>

### Files changed
- `src/app/services/project_service.py` - <what changed>
- `src/app/routers/projects.py` - <what changed>

### Tests added
- `tests/services/test_project_service.py` - <what's tested>
- `tests/routers/test_projects.py` - <what's tested>

### Quality gates
- Ruff format: PASS (zero reformats)
- Ruff check: PASS (zero violations)
- mypy: PASS (zero errors)
- pytest: PASS (X passed, 0 failed)
- Review: APPROVED
- Eval: 0.X
```

---

## Error Recovery

- If an agent task fails, read the error output carefully
- Determine if it's a code error (delegate fix) or a requirements issue (ask user)
- Never skip a failing quality gate; fix it before proceeding
- For persistent failures, escalate to the user with full context
