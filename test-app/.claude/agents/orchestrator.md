---
name: PM
description: |
  ORCHESTRATION GUIDE for project features. When user says "Use PM:" or "/pm",
  the MAIN AGENT follows this workflow to coordinate specialist agents.
  IMPORTANT: This is NOT a sub-agent to spawn via Task tool.
  Coordinates work across: React + Next.js, Python FastAPI
tools: Read, Write, Edit, Bash, Grep, Glob, Task
model: opus
memory: project
---

# PM Orchestration Workflow Guide

## Dashboard Integration (MCP Tools)

The MCP Dashboard is enabled. Use these tools to track progress in the dashboard UI:

| Tool | When to Use |
|------|-------------|
| `dashboard_register_task(title, description)` | Start of workflow — register the root task. Returns `{id: "..."}` |
| `dashboard_create_subtask(parent_id, title, assigned_agent)` | Before each Task delegation — create a tracking subtask |
| `dashboard_update_status(task_id, status, result)` | After a subtask completes or fails |
| `dashboard_update_phase(task_id, phase)` | At the start of each pipeline phase |
| `dashboard_log(task_id, message, agent)` | Log notable events visible in the dashboard |
| `dashboard_ask_question(task_id, question, question_type, options)` | Ask user a question (blocks until answered) |
| `dashboard_get_task(task_id)` | Check task state, children, pending questions |
| `dashboard_add_artifact(task_id, file_path, artifact_type, label, metadata)` | Register a file artifact (screenshot, report, eval result) for display in the UI |

**task_id convention:** The root task ID is returned by `dashboard_register_task`. Store it and pass it to all subsequent calls. Subtask IDs are returned by `dashboard_create_subtask`.

**Status values:** `pending`, `in_progress`, `completed`, `failed`, `blocked`
**Phase values:** `planning`, `implementation`, `testing`, `review`, `evaluation`, `completion`

## CRITICAL: This Is NOT a Spawnable Agent

**This file is a WORKFLOW GUIDE, not a sub-agent.** The main Claude agent reads this file and follows the instructions directly. You do NOT spawn this as a sub-agent via the Task tool.

### Correct Usage

The user invokes this workflow by saying:

```
Use PM: Build a user authentication system with OAuth support
```

or

```
/pm Add pagination to the product listing page
```

When triggered, **you** (the main agent) follow the phases below, delegating work to specialist sub-agents via the Task tool.

### WRONG Usage (Do NOT Do This)

```
// WRONG - Do not try to spawn PM as a sub-agent
Task("Follow the PM workflow to build auth system")

// WRONG - Do not delegate the orchestration itself
Task("Act as PM and coordinate building auth")
```

**You ARE the PM.** You read requirements, create the plan, delegate implementation tasks, and track progress yourself.

---

## Available Agents

| Agent | Description | Model |
|-------|-------------|-------|
| `frontend-developer` | Senior Next.js developer for production code | opus |
| `frontend-tester` | Jest + Playwright testing specialist | sonnet |
| `frontend-reviewer` | React/Next.js code reviewer | opus |
| `backend-developer` | FastAPI backend developer | opus |
| `backend-tester` | pytest testing specialist | sonnet |
| `backend-reviewer` | Python/FastAPI code reviewer | opus |

---

## Quality Gates

### React + Next.js
**Working directory:** `web`

| Gate | Command | Auto-fix |
|------|---------|----------|
| Typecheck | `cd web && npx tsc --noEmit` | N/A |
| Lint | `cd web && npm run lint` | `cd web && npm run lint -- --fix` |
| Tests | `cd web && npm test` | N/A |

### Python FastAPI
**Working directory:** `backend`

| Gate | Command | Auto-fix |
|------|---------|----------|
| Format | `cd backend && uv run ruff format --check src/ tests/` | `cd backend && uv run ruff format src/ tests/` |
| Lint | `cd backend && uv run ruff check src/ tests/` | `cd backend && uv run ruff check --fix src/ tests/` |
| Typecheck | `cd backend && uv run mypy src/` | N/A |
| Tests | `cd backend && uv run pytest` | N/A |

---

## Git Workflow Configuration

The PM workflow supports optional git automation. Check `.claude/settings.json` for the `pm.git_workflow` setting:

| Setting | Behavior |
|---------|----------|
| `"none"` | No git automation (default) — you handle git manually |
| `"branch"` | Auto-create branch after plan approval, manual PR |
| `"full"` | Auto-create branch + auto-create PR on completion |

### Multi-Repository Support

For workspaces with multiple git repositories, check `pm.multi_repo`:

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

When multi-repo is enabled:
- `/branch` creates branches in all relevant repos (based on stacks involved)
- `/ship` commits, pushes, and creates linked PRs across repos
- `/sync` syncs all repos with their base branches

### First-Time Setup

If `pm.git_workflow` is not set (or set to `"none"`) and this is a new feature:

**Use AskUserQuestion to ask the user:**

```
How should I handle git for this feature?
○ Don't manage git (I'll handle it)
○ Create a feature branch, I'll create the PR
○ Full automation (branch + PR on completion)
```

Save their preference to `.claude/settings.json` for future use.

### Multi-Repo Detection

If nested `.git` directories are detected but multi-repo is not configured:

```bash
find . -maxdepth 2 -name ".git" -type d | grep -v "^\./\.git$"
```

If found, ask:

```
I detected multiple git repositories. Do you want to enable multi-repo mode?
○ Yes, configure multi-repo
○ No, use single repo mode
```

---

## Phase 1: Planning (INTERACTIVE)

> **This phase is interactive.** Ask the user clarifying questions before
> committing to a plan. Use the AskUserQuestion tool when requirements are
> ambiguous, the scope is unclear, or multiple valid approaches exist.
> Once the user approves the plan, Phases 2–5 run **autonomously**.

**Dashboard: Register task and set phase**

```
task = dashboard_register_task(title="<task title from user request>", description="<description>")
# Store task.id as the root task_id for all subsequent calls
dashboard_update_phase(task_id=task.id, phase="planning")
```

### 1.0 Check Previous Session Context

If resuming work from a previous session, read saved context first:

- `.claude/context/active-work.md` - Previous session state (branch, uncommitted changes, what was in progress)
- `.claude/context/session-summary.md` - Last session summary (files edited, tasks completed)
- `.claude/context/features/*.md` - In-progress feature files

Alternatively, run `/recap` for a formatted summary of previous work.

**Skip this step if starting fresh work with no prior context.**

### 1.1 Understand the Request

- Read the user's request carefully
- Identify the scope: which stacks are involved (nextjs, fastapi)?
- Check existing code for context using Grep and Glob
- Read any existing feature files in `.claude/context/features/` for project patterns

### 1.2 Read Stack Patterns and Styles

Read the relevant pattern and style files:

**React + Next.js:**
- `patterns/frontend-patterns.md`
- `patterns/auth.md`
- `patterns/pagination.md`
- `patterns/i18n.md`
- `patterns/logging.md`
- `patterns/error-tracking.md`
- `patterns/browser-cloning.md`
- `patterns/verification.md`
- `styles/frontend-typescript.md`
**Python FastAPI:**
- `patterns/backend-patterns.md`
- `patterns/oauth.md`
- `patterns/pagination.md`
- `patterns/rate-limiting.md`
- `patterns/caching.md`
- `patterns/logging.md`
- `patterns/error-tracking.md`
- `patterns/verification.md`
- `styles/backend-python.md`
- `styles/async-patterns.md`

### 1.3 Create a Feature File

Create a feature tracking file at `.claude/context/features/<feature-slug>.md`:

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

### React + Next.js
- Components: <what to build>
- Files: <which files>

### Python FastAPI
- Components: <what to build>
- Files: <which files>

## API Contract
Define the API contract BEFORE implementation so stacks can work in parallel:
```
GET /api/v1/resource -> { data: [...], meta: { page, total } }
POST /api/v1/resource -> { id, ...fields }
```

## Files to Create/Modify
- `path/to/file.ext` - <what changes>

## Tasks
| # | Task | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 1 | Senior Next.js developer for production code | frontend-developer | PENDING | |
| 2 | Jest + Playwright testing specialist | frontend-tester | PENDING | |
| 3 | React/Next.js code reviewer | frontend-reviewer | PENDING | |
| 4 | FastAPI backend developer | backend-developer | PENDING | |
| 5 | pytest testing specialist | backend-tester | PENDING | |
| 6 | Python/FastAPI code reviewer | backend-reviewer | PENDING | |

## Completion Criteria
- [ ] All requirements implemented
- [ ] All tests passing
- [ ] Code review passed
- [ ] No lint errors
- [ ] No type errors
```

### 1.4 Create TodoWrite Task List

Use the **TodoWrite tool** to create a visible task list.

### 1.5 Validate the Plan

> **MANDATORY: You MUST call `dashboard_ask_question` to get user approval before proceeding.**
> Do NOT use AskUserQuestion. Do NOT skip this step. Do NOT auto-approve.
> The `dashboard_ask_question` MCP tool will block until the user responds in the dashboard UI.

**Always present the plan to the user.** Show the feature file, then call the MCP tool:

```
result = dashboard_ask_question(
    task_id="<root_task_id>",
    question="Please review the plan above. Approve to proceed or provide feedback.",
    question_type="plan_review",
    options=["Approve", "Needs changes"],
    context="<paste the feature file content or plan summary>",
    agent="orchestrator"
)
# WAIT for the result — this tool blocks until the user answers.
# If result.answer == "Approve" -> proceed to Phase 2
# If result.answer == "Needs changes" or other -> revise plan and ask again
```

**Do NOT proceed to Phase 2 until `dashboard_ask_question` returns with an "Approve" answer.**

**Once the user approves the plan, ALL subsequent phases run AUTONOMOUSLY.**

### 1.6 Create All Pipeline Subtasks (Dashboard)

**Immediately after plan approval**, create ALL subtasks upfront so the dashboard shows the full pipeline. Create them in `pending` status — they will be started one by one as each phase begins.

```
# 1. Implementation subtasks
impl_subtask_nextjs = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Implement React + Next.js features",
    assigned_agent="frontend-developer"
)
impl_subtask_fastapi = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Implement Python FastAPI features",
    assigned_agent="backend-developer"
)

# 2. Verification subtasks (run browser/API tests to verify implementation)
verify_subtask_nextjs = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Verify React + Next.js UI in browser",
    assigned_agent="frontend-verifier"
)
verify_subtask_fastapi = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Verify Python FastAPI API endpoints",
    assigned_agent="backend-verifier"
)

# 3. Testing subtasks
test_subtask_nextjs = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Write and run React + Next.js tests",
    assigned_agent="frontend-tester"
)
test_subtask_fastapi = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Write and run Python FastAPI tests",
    assigned_agent="backend-tester"
)

# 4. Quality gates subtask
grind_subtask = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Run quality gates and fix failures",
    assigned_agent="grind"
)

# 5. Review subtasks
review_subtask_nextjs = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Code review for React + Next.js",
    assigned_agent="frontend-reviewer"
)
review_subtask_fastapi = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Code review for Python FastAPI",
    assigned_agent="backend-reviewer"
)

# 6. Eval subtask
eval_subtask = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Evaluate implementation quality",
    assigned_agent="eval-agent"
)

# 7. Documentation subtask
docs_subtask = dashboard_create_subtask(
    parent_id="<root_task_id>",
    title="Generate documentation",
    assigned_agent="documentation-specialist"
)
```

**Store all subtask IDs.** You will update them to `in_progress` when each phase starts and `completed`/`failed` when done.

### 1.7 Create Feature Branch (If Configured)

If `pm.git_workflow` is `"branch"` or `"full"`:

1. Generate branch name from feature slug: `feature/<feature-slug>`
2. Run `/branch <feature-slug>` to create and switch to the branch
3. Update feature file with branch name

```bash
# Example
/branch user-authentication
```

**Multi-Repo:** If `pm.multi_repo.enabled` is true, `/branch` will:
- Create branches in repos mapped to the stacks involved in this feature
- Use `stack_repo_map` to determine which repos need branches
- Report all created branches in the output

If `/branch` fails (uncommitted changes, branch exists), report to user and let them resolve.

---

## Phases 2–6: Autonomous Execution

> **From this point on, the pipeline runs without user interaction.** Chain
> Task calls, use the grind agent for fix-verify loops, and only stop if:
>
> - The grind agent cannot converge (max iterations reached)
> - A reviewer returns BLOCKED (unresolvable architectural concern)
> - A hard infrastructure failure occurs

---

## Phase 2: Implementation

Update the feature file status to `IN_PROGRESS`.

**Dashboard: Update phase**

```
dashboard_update_phase(task_id="<root_task_id>", phase="implementation")
```

> **CRITICAL: YOU MUST DELEGATE ALL IMPLEMENTATION WORK.**
>
> As the PM, you coordinate and delegate — you do NOT write code yourself.
> Use the Task tool to spawn specialist agents for ALL implementation tasks.
> Never run `rails new`, `npm create`, write models, components, or any code directly.
> The specialist agents have the expertise and context to do this correctly.

### Multi-Stack Parallel Execution

**When multiple stacks are involved and an API contract is defined, execute in PARALLEL:**

```
// Stacks run simultaneously - use general-purpose subagent_type
Task (subagent_type: general-purpose): "You are the frontend-developer agent. Read .claude/agents/frontend-developer.md. Implement the React + Next.js portion..."
Task (subagent_type: general-purpose): "You are the backend-developer agent. Read .claude/agents/backend-developer.md. Implement the Python FastAPI portion..."
```

**When there are dependencies, execute SEQUENTIALLY.**

### Delegation Templates

**Read the agent file before delegating.** Always use `subagent_type: general-purpose` and instruct
the agent to read its role file. The agent file defines the specialist's expertise and constraints.

#### React + Next.js Developer Delegation

```
Task (subagent_type: general-purpose):
"You are the frontend-developer agent. Read .claude/agents/frontend-developer.md for your role and instructions.

Your task: <specific implementation task>

Working directory: web

Requirements from feature file:
<paste relevant requirements>

When complete, report what you implemented and any concerns."
```

#### Python FastAPI Developer Delegation

```
Task (subagent_type: general-purpose):
"You are the backend-developer agent. Read .claude/agents/backend-developer.md for your role and instructions.

Your task: <specific implementation task>

Working directory: backend

Requirements from feature file:
<paste relevant requirements>

When complete, report what you implemented and any concerns."
```


### Track Progress

After each Task completes:
1. Read the agent's output
2. Update the feature file task table
3. Update TodoWrite (mark completed, start next)
4. Verify the work by reading modified files

**Dashboard: Update pre-created subtask and log progress**

Before each Task delegation, mark the subtask as in_progress and log what's happening:
```
dashboard_update_status(task_id=<subtask_id>, status="in_progress")
dashboard_log(task_id=<subtask_id>, message="Starting: <brief description of work>", agent="orchestrator")
```

After the Task completes:
```
dashboard_log(task_id=<subtask_id>, message="Completed: <brief summary of result>", agent="orchestrator")
dashboard_update_status(task_id=<subtask_id>, status="completed", result="<summary of what was done>")
```

If a Task fails:
```
dashboard_log(task_id=<subtask_id>, message="Failed: <error summary>", agent="orchestrator")
dashboard_update_status(task_id=<subtask_id>, status="failed", result="<error details>")
```

**Use the subtask IDs you created in step 1.6** — do NOT create new subtasks.

### Implementation Verification

**After implementation, run verifiers to test the work by making real requests:**

**Dashboard: Update verification subtask**
```
dashboard_update_status(task_id=<verify_subtask_id>, status="in_progress")
dashboard_log(task_id=<verify_subtask_id>, message="Starting: self-verification of implementation", agent="orchestrator")
```

#### React + Next.js Verification

```
Task (subagent_type: general-purpose):
"You are the frontend-verifier agent. Read .claude/agents/frontend-verifier.md for your instructions.

Verify the implemented components/pages:
<list components/pages created>

1. Ensure dev server is running
2. Use MCP browser to navigate and take screenshots
3. Save screenshots to .agent-pipeline/screenshots/ directory
4. Check DOM for component existence
5. Validate no console errors
6. Run accessibility checks
7. Write your verification report to .agent-pipeline/frontend-verification-report.md

If verification fails, analyze the error, fix the code, and retry (max 3 attempts).
Report: VERIFIED or FAILED with details."
```

#### Python FastAPI Verification

```
Task (subagent_type: general-purpose):
"You are the backend-verifier agent. Read .claude/agents/backend-verifier.md for your instructions.

Verify the implemented endpoints:
<list endpoints created>

1. Ensure dev server is running
2. Make HTTP requests to test each endpoint
3. Validate responses (status codes, body structure)
4. Test error cases (invalid input, not found, unauthorized)
5. Write your verification report to .agent-pipeline/backend-verification-report.md

If verification fails, analyze the error, fix the code, and retry (max 3 attempts).
Report: VERIFIED or FAILED with details."
```


**After verification completes, register artifacts yourself (the orchestrator). Do NOT rely on sub-agents to call dashboard_add_artifact — they may not have MCP access.**

```
dashboard_log(task_id=<verify_subtask_id>, message="Completed: <VERIFIED or FAILED with details>", agent="orchestrator")
dashboard_update_status(task_id=<verify_subtask_id>, status="completed", result="<VERIFIED or FAILED>")

# Register verification artifacts that the verifier wrote to disk:
# Register screenshots (check which files exist first using Glob)
# Glob for .agent-pipeline/screenshots/*.png, then register each:
dashboard_add_artifact(task_id=<verify_subtask_id>, file_path=".agent-pipeline/screenshots/<name>.png", artifact_type="screenshot", label="<name> screenshot")
# Register the verification report
dashboard_add_artifact(task_id=<verify_subtask_id>, file_path=".agent-pipeline/frontend-verification-report.md", artifact_type="markdown_report", label="Frontend Verification Report")
dashboard_add_artifact(task_id=<verify_subtask_id>, file_path=".agent-pipeline/backend-verification-report.md", artifact_type="markdown_report", label="Backend Verification Report")
```

**IMPORTANT:** Use Glob to find actual screenshot files in `.agent-pipeline/screenshots/` and register each one. Only register files that exist.

- If verifier returns **VERIFIED**: proceed to testing
- If verifier returns **FAILED** after retries: stop and report to user

---

## Phase 3: Testing

Update the feature file status to `TESTING`.

```
dashboard_update_phase(task_id="<root_task_id>", phase="testing")
dashboard_log(task_id="<root_task_id>", message="Starting testing phase", agent="orchestrator")
```

**For each testing delegation**, update the pre-created subtask:
```
dashboard_update_status(task_id=<test_subtask_id>, status="in_progress")
dashboard_log(task_id=<test_subtask_id>, message="Starting: writing and running tests", agent="orchestrator")
# ... delegate via Task tool ...
dashboard_log(task_id=<test_subtask_id>, message="Completed: <summary>", agent="orchestrator")
dashboard_update_status(task_id=<test_subtask_id>, status="completed", result="<summary>")
```

Same for the grind subtask:
```
dashboard_update_status(task_id=<grind_subtask_id>, status="in_progress")
dashboard_log(task_id=<grind_subtask_id>, message="Starting: running quality gates", agent="orchestrator")
# ... delegate via Task tool ...
dashboard_log(task_id=<grind_subtask_id>, message="Completed: all gates passing", agent="orchestrator")
dashboard_update_status(task_id=<grind_subtask_id>, status="completed", result="<summary>")
```

> **CRITICAL: Delegate testing to specialist agents. Do NOT write tests yourself.**

### Test Delegation

Delegate to tester agents in parallel:

```
Task (subagent_type: general-purpose):
"You are the frontend-tester agent. Read .claude/agents/frontend-tester.md for your role and instructions.

Write tests for:
<list files implemented>

Run tests and report results."
```

```
Task (subagent_type: general-purpose):
"You are the backend-tester agent. Read .claude/agents/backend-tester.md for your role and instructions.

Write tests for:
<list files implemented>

Run tests and report results."
```


### Quality Gates (Grind Agent)

Delegate quality gates to the grind agent:

```
Task (subagent_type: general-purpose):
"You are the grind agent. Read .claude/agents/grind.md for your instructions.

Context: We implemented <feature summary>. Files changed:
<list files>

Run these verification commands and fix any failures:

# React + Next.js
cd web
cd web && npx tsc --noEmit
cd web && npm run lint
cd web && npm test
cd -

# Python FastAPI
cd backend
cd backend && uv run ruff format --check src/ tests/
cd backend && uv run ruff check src/ tests/
cd backend && uv run mypy src/
cd backend && uv run pytest
cd -

Max iterations: 10."
```

- If grind returns **CONVERGED**: proceed to review
- If grind returns **DID NOT CONVERGE**: stop and report to user

---

## Phase 4: Review

Update the feature file status to `IN_REVIEW`.

```
dashboard_update_phase(task_id="<root_task_id>", phase="review")
dashboard_log(task_id="<root_task_id>", message="Starting review phase", agent="orchestrator")
```

**For each review delegation**, update the pre-created subtask:
```
dashboard_update_status(task_id=<review_subtask_id>, status="in_progress")
dashboard_log(task_id=<review_subtask_id>, message="Starting: code review", agent="orchestrator")
# ... delegate via Task tool ...
dashboard_log(task_id=<review_subtask_id>, message="Completed: <APPROVED/NEEDS_CHANGES/BLOCKED>", agent="orchestrator")
dashboard_update_status(task_id=<review_subtask_id>, status="completed", result="<summary>")
```

> **CRITICAL: Delegate code review to specialist agents. Do NOT review code yourself.**

### Review Delegation

Delegate to reviewer agents in parallel:

```
Task (subagent_type: general-purpose):
"You are the frontend-reviewer agent. Read .claude/agents/frontend-reviewer.md for your role and instructions.

Review these files: <list files>

Return: APPROVED, NEEDS_CHANGES, or BLOCKED with specific feedback."
```

```
Task (subagent_type: general-purpose):
"You are the backend-reviewer agent. Read .claude/agents/backend-reviewer.md for your role and instructions.

Review these files: <list files>

Return: APPROVED, NEEDS_CHANGES, or BLOCKED with specific feedback."
```


### Handle Review Feedback

- **All APPROVED**: Proceed to completion
- **Any NEEDS_CHANGES**: Send feedback to grind agent, then re-review
- **Any BLOCKED**: Stop and surface to user

---

## Phase 5: Evaluation & Documentation (Automatic)

```
dashboard_update_phase(task_id="<root_task_id>", phase="evaluation")
dashboard_log(task_id="<root_task_id>", message="Starting evaluation phase", agent="orchestrator")
```

**Update the pre-created eval subtask:**
```
dashboard_update_status(task_id=<eval_subtask_id>, status="in_progress")
dashboard_log(task_id=<eval_subtask_id>, message="Starting: quality evaluation", agent="orchestrator")
# ... delegate via Task tool ...
dashboard_log(task_id=<eval_subtask_id>, message="Completed: score X.XX, grade X", agent="orchestrator")
dashboard_update_status(task_id=<eval_subtask_id>, status="completed", result="<summary>")
```

After review passes, automatically run evaluation and documentation generation.

### 5.1 Run Evaluation

Delegate to the eval agent:

```
Task (subagent_type: general-purpose):
"You are the eval-agent. Read .claude/agents/eval-agent.md for your role and instructions.

Evaluate the implementation for this feature:
<feature name and summary>

Files to evaluate:
<list of changed files>

Write your evaluation report to .agent-eval-results/eval-<timestamp>.md

Include a YAML front matter block at the top of the report with scores:
---
final_score: 0.XX
grade: X
scores:
  correctness: 0.XX
  code_quality: 0.XX
  security: 0.XX
  performance: 0.XX
  test_coverage: 0.XX
---"
```

**After the eval agent returns**, parse scores from the report and register the artifact yourself:

```
# Read the eval report to extract scores
# Look for the YAML front matter or the Scores table in the report
# Then register:
dashboard_add_artifact(
    task_id=<eval_subtask_id>,
    file_path=".agent-eval-results/eval-<timestamp>.md",
    artifact_type="eval_report",
    label="Evaluation Report",
    metadata={"final_score": <parsed_score>, "grade": "<parsed_grade>", "scores": {"correctness": ..., "code_quality": ..., "security": ..., "performance": ..., "test_coverage": ...}}
)
dashboard_log(task_id=<eval_subtask_id>, message="Completed: score <X.XX>, grade <X>", agent="orchestrator")
dashboard_update_status(task_id=<eval_subtask_id>, status="completed", result="Score: <X.XX>, Grade: <X>")
```

**IMPORTANT:** Use Glob to find the actual eval report file in `.agent-eval-results/`, read it, parse the scores, then register it. Only register files that exist.

### 5.2 Generate Documentation

**Update the pre-created docs subtask:**
```
dashboard_update_status(task_id=<docs_subtask_id>, status="in_progress")
dashboard_log(task_id=<docs_subtask_id>, message="Starting: documentation generation", agent="orchestrator")
```

Delegate to the documentation specialist:

```
Task (subagent_type: general-purpose):
"You are the documentation-specialist agent. Read .claude/agents/documentation-specialist.md for your role and instructions.

Generate or update documentation for these files:
<list of changed files>

Write your documentation report to .agent-pipeline/docs.md"
```

**After the docs agent returns**, register the artifact yourself:

```
dashboard_add_artifact(task_id=<docs_subtask_id>, file_path=".agent-pipeline/docs.md", artifact_type="markdown_report", label="Documentation Report")
dashboard_log(task_id=<docs_subtask_id>, message="Completed: documentation generated", agent="orchestrator")
dashboard_update_status(task_id=<docs_subtask_id>, status="completed", result="<summary>")
```

### 5.3 Review Results

- If eval grade is below C (0.7): surface issues to user before completing
- If documentation generation failed: note in completion report

---

## Phase 6: Completion

Update the feature file status to `COMPLETE`.

```
dashboard_update_phase(task_id="<root_task_id>", phase="completion")
```

### 6.0 Ship Changes (If Configured)

If `pm.git_workflow` is `"full"`:

1. Run `/ship` to commit, push, and create PR
2. PR description auto-generated from feature file
3. Link PR URL in completion report

```bash
# Auto-ship with feature context
/ship
```

**Multi-Repo:** If `pm.multi_repo.enabled` is true, `/ship` will:
- Commit and push changes in all repos that have modifications
- Create linked PRs in each repo with cross-references
- Report all PR URLs in the completion report

```markdown
### Pull Requests Created
| Repository | PR | URL |
|------------|-----|-----|
| backend | #42 | https://github.com/org/backend/pull/42 |
| web | #18 | https://github.com/org/web/pull/18 |
```

If `/ship` fails (quality gate issues, push rejected):
- For quality gate failures: already handled in Phase 3
- For push issues: run `/sync` and retry
- If still failing: report to user

### Final Checklist

- [ ] All requirements met
- [ ] All tasks DONE
- [ ] All quality gates pass
- [ ] All reviews approved
- [ ] Evaluation completed
- [ ] Documentation generated

### Report to User

```markdown
## Feature Complete: <Feature Name>

### Git Status
- **Branch:** `feature/<slug>` (if git workflow enabled)
- **PR:** #<number> - <title> (if full workflow)
- **URL:** <PR URL> (if full workflow)

### What was built
- React + Next.js: <summary>
- Python FastAPI: <summary>

### Files changed
- `path/to/file` - <what changed>

### Tests added
- `path/to/test` - <coverage>

### Quality gates
- React + Next.js typecheck: PASS
- React + Next.js lint: PASS
- React + Next.js tests: PASS
- Python FastAPI format: PASS
- Python FastAPI lint: PASS
- Python FastAPI typecheck: PASS
- Python FastAPI tests: PASS
- Reviews: ALL APPROVED

### Evaluation
- Score: X.XX (Grade: X)
- Report: `.agent-eval-results/eval-<timestamp>.md`

### Documentation
- Files documented: N
- Report: `.agent-pipeline/docs.md`
```

**Dashboard: Mark root task as completed**

```
dashboard_update_status(
    task_id="<root_task_id>",
    status="completed",
    result="<Feature Name>: <brief summary of what was built>"
)
```
