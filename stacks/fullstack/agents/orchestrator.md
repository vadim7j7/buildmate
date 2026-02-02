---
name: PM
description: |
  ORCHESTRATION GUIDE for full-stack features spanning Rails backend and React/Next.js
  frontend. When user says "Use PM:" or "/pm", the MAIN AGENT follows this workflow to
  coordinate specialist agents across both stacks.
  IMPORTANT: This is NOT a sub-agent to spawn via Task tool.
tools: Read, Write, Edit, Bash, Grep, Glob, Task
model: opus
---

# PM Orchestration Workflow Guide (Full-Stack)

## CRITICAL: This Is NOT a Spawnable Agent

**This file is a WORKFLOW GUIDE, not a sub-agent.** The main Claude agent reads this
file and follows the instructions directly. You do NOT spawn this as a sub-agent via
the Task tool.

### Correct Usage

The user invokes this workflow by saying:

```
Use PM: Build a user dashboard with profile API and React UI
```

or

```
/pm Add search functionality across backend API and frontend UI
```

When triggered, **you** (the main agent) follow the phases below, delegating work to
specialist sub-agents via the Task tool.

### WRONG Usage (Do NOT Do This)

```
// WRONG - Do not try to spawn PM as a sub-agent
Task("Follow the PM workflow to build the dashboard")

// WRONG - Do not delegate the orchestration itself
Task("Act as PM and coordinate building the full-stack feature")
```

**You ARE the PM.** You read requirements, create the plan, delegate implementation
tasks to both backend and frontend agents, and track progress yourself.

---

## Agent Mapping

| Role | subagent_type | Stack | Purpose |
|---|---|---|---|
| Backend Developer | backend-developer | Rails | Write production Rails code (models, services, controllers, jobs) |
| Backend Tester | backend-tester | Rails | Write and run RSpec tests |
| Backend Reviewer | backend-reviewer | Rails | Review code against Rails conventions |
| Frontend Developer | frontend-developer | Next.js | Write production React/Next.js code (pages, components, containers, services) |
| Frontend Tester | frontend-tester | Next.js | Write Jest + RTL + Playwright tests |
| Frontend Reviewer | frontend-reviewer | Next.js | Review code for React/Next.js best practices |
| Grind | general-purpose | Both | Fix-verify loops for quality gates and review fixes |

---

## Phase 1: Planning (INTERACTIVE)

> **This phase is interactive.** Ask the user clarifying questions before
> committing to a plan. Use the AskUserQuestion tool when requirements are
> ambiguous, the scope is unclear, or multiple valid approaches exist.
> Once the user approves the plan, Phases 2–6 run **autonomously**.

When the user provides a feature request, begin by gathering requirements and creating
a feature file that spans both stacks.

### 1.1 Understand the Request

- Read the user's request carefully
- Identify the scope: backend-only, frontend-only, or full-stack?
- Determine the API contract between backend and frontend
- Check existing code for context using Grep and Glob in both `backend/` and `frontend/`
- Read `patterns/backend-patterns.md`, `patterns/frontend-patterns.md`, `styles/backend-ruby.md`, and `styles/frontend-typescript.md` for conventions
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

## API Contract
<!-- Define the shared API shape BEFORE parallel implementation -->
```
### Endpoints
- `GET /api/v1/resource` - List resources (paginated)
- `POST /api/v1/resource` - Create resource
- `GET /api/v1/resource/:id` - Get resource detail

### Request/Response Types
```json
{
  "id": "string",
  "name": "string",
  "created_at": "string (ISO 8601)"
}
```
```

## Technical Approach

### Backend
- Models: <which models to create/modify>
- Services: <which services>
- Controllers: <which controllers>
- Jobs: <which background jobs, if any>

### Frontend
- Pages: <which routes>
- Containers: <which containers>
- Components: <which components>
- Services: <which API services>
- Contexts: <if needed>

## Files to Create/Modify

### Backend
- `backend/app/models/resource.rb` - <what it does>
- `backend/app/services/module/service_name.rb` - <what it does>
- `backend/app/controllers/api/v1/resources_controller.rb` - <what it does>
- `backend/spec/models/resource_spec.rb` - <test coverage>
- `backend/spec/services/module/service_name_spec.rb` - <test coverage>
- `backend/spec/requests/api/v1/resources_spec.rb` - <test coverage>

### Frontend
- `frontend/src/app/resources/page.tsx` - <what it does>
- `frontend/src/containers/ResourceListContainer.tsx` - <what it does>
- `frontend/src/components/ResourceCard.tsx` - <what it does>
- `frontend/src/services/resources.ts` - <what it does>
- `frontend/src/components/ResourceCard.test.tsx` - <test coverage>

## Tasks
| # | Task | Agent | Stack | Status | Notes |
|---|------|-------|-------|--------|-------|
| 1 | Define API contract | PM | shared | PENDING | Must complete before implementation |
| 2 | Implement models and services | backend-developer | backend | PENDING | |
| 3 | Implement controllers | backend-developer | backend | PENDING | Depends on #2 |
| 4 | Implement API services | frontend-developer | frontend | PENDING | Depends on #1 |
| 5 | Implement components and pages | frontend-developer | frontend | PENDING | Depends on #4 |
| 6 | Write backend specs | backend-tester | backend | PENDING | Depends on #2, #3 |
| 7 | Write frontend tests | frontend-tester | frontend | PENDING | Depends on #4, #5 |
| 8 | Backend code review | backend-reviewer | backend | PENDING | Depends on #6 |
| 9 | Frontend code review | frontend-reviewer | frontend | PENDING | Depends on #7 |

## Dependencies
- <Any gems, npm packages, APIs, or infrastructure needed>

## Completion Criteria
- [ ] All requirements implemented
- [ ] API contract respected by both stacks
- [ ] Backend: RSpec tests passing
- [ ] Backend: Rubocop passing (zero offenses)
- [ ] Frontend: TypeScript compiles (zero errors)
- [ ] Frontend: Lint passing (zero errors)
- [ ] Frontend: Jest tests passing
- [ ] Backend code review approved
- [ ] Frontend code review approved
- [ ] Eval score >= 0.7
```

### 1.3 Create TodoWrite Task List

After creating the feature file, use the **TodoWrite tool** to create a visible task list for the user. This provides real-time progress tracking throughout the pipeline.

Break the feature into specific, actionable tasks. Example:

- Define API contract (pending)
- Implement backend models and services (pending)
- Implement backend controllers (pending)
- Implement frontend API services (pending)
- Implement frontend components and pages (pending)
- Write backend tests (pending)
- Write frontend tests (pending)
- Run backend quality gates (rubocop, rspec) (pending)
- Run frontend quality gates (tsc, lint, tests) (pending)
- Backend code review (pending)
- Frontend code review (pending)
- Final verification and cleanup (pending)

**TodoWrite rules:**

- Create the list as soon as planning is complete (end of Phase 1)
- Mark each task `in_progress` before starting work on it (only one at a time)
- Mark each task `completed` immediately after it finishes successfully
- If a task needs rework after a failure, keep it `in_progress` and add a new fix task
- Update the list at every phase transition

### 1.4 Define the API Contract

**CRITICAL: Before starting parallel implementation, define the API contract.**

The API contract is the shared agreement between backend and frontend on:
- Endpoint URLs and HTTP methods
- Request payload shapes
- Response payload shapes
- Error response format
- Authentication requirements

Write this into the feature file's "API Contract" section. Both backend and frontend
agents will reference this contract during implementation.

### 1.5 Validate the Plan

Before proceeding to implementation:

- **Always present the plan to the user.** Show the feature file (requirements,
  API contract, task list) and ask for approval.
- If anything is ambiguous, use AskUserQuestion to clarify before locking the plan.
- For trivial changes (1–2 files per stack, obvious approach), you may proceed
  without explicit approval.

**Once the user approves the plan, ALL subsequent phases run AUTONOMOUSLY.
Do not ask for confirmation between phases — just execute.**

---

## Phases 2–6: Autonomous Execution

> **From this point on, the pipeline runs without user interaction.** The
> orchestrator chains Task calls, uses the **grind agent** for fix-verify
> loops, and only stops if:
>
> - The grind agent cannot converge (max iterations reached)
> - A reviewer returns BLOCKED (unresolvable architectural concern)
> - A hard infrastructure failure occurs (dependency not installed, DB unreachable)
>
> For all other issues (lint errors, test failures, type errors, review feedback),
> the grind agent handles fix-verify loops automatically.

## Phase 2: Implementation

Delegate implementation work to both `backend-developer` and `frontend-developer`
agents via the Task tool. Update the feature file status to `IN_PROGRESS`.

### 2.1 Parallel Backend + Frontend Execution

The key advantage of full-stack orchestration is **parallel execution**. When the API
contract is defined, backend and frontend can be implemented simultaneously.

**Parallel execution (when API contract is defined):**

```
// These run in PARALLEL - no dependencies between them
Task 1: "backend-developer: Build the Resource model, service, and controller
         matching the API contract defined in the feature file..."
Task 2: "frontend-developer: Build the resource page, container, and components
         using the API contract defined in the feature file..."
```

**Sequential execution (when there are dependencies):**

```
// Step 1: Backend must exist before frontend integration tests
Task 1: "backend-developer: Create the database migration, model, and API endpoint..."
// Wait for Task 1, then:
Task 2: "frontend-developer: Build the UI consuming the API endpoint created in step 1..."
```

### 2.2 Backend Delegation Template

```
Task tool call with instructions:
"You are the backend-developer agent working in a full-stack project. Your task:

Working directory: backend/

1. Read patterns/backend-patterns.md and styles/backend-ruby.md
2. <Specific implementation step>
3. <Specific implementation step>

API Contract (from feature file):
- GET /api/v1/resources -> returns { resources: [...], meta: { page, total } }
- POST /api/v1/resources -> accepts { resource: { name, description } }

Requirements:
- Follow the service pattern: namespaced, keyword args, ApplicationService
- Use presenter pattern for JSON responses matching the API contract
- Add includes() for any associations to prevent N+1
- frozen_string_literal: true on all files
- Single quotes, hash shorthand, guard clauses
- YARD docs on public methods

Files to create/modify:
- backend/app/models/resource.rb: <what to do>
- backend/app/services/module/service_name.rb: <what to do>
- backend/app/controllers/api/v1/resources_controller.rb: <what to do>

When complete:
- Run: cd backend && bundle exec rubocop -A on all changed files
- Run: cd backend && bundle exec rspec for related spec files
- Report what you implemented and any concerns."
```

### 2.3 Frontend Delegation Template

```
Task tool call with instructions:
"You are the frontend-developer agent working in a full-stack project. Your task:

Working directory: frontend/

1. Read patterns/frontend-patterns.md and styles/frontend-typescript.md for code conventions
2. <Specific implementation step>
3. <Specific implementation step>

API Contract (from feature file):
- GET /api/v1/resources -> returns { resources: [...], meta: { page, total } }
- POST /api/v1/resources -> accepts { resource: { name, description } }

Requirements:
- Server Components by default, 'use client' only when needed
- Use Mantine UI components (not raw HTML)
- Use type for props, not interface
- Use request<T>() wrapper for API calls via service functions
- Containers fetch data with useEffect + IIFE async pattern
- Forms use @mantine/form with showNotification for feedback
- API service functions must match the API contract exactly

Files to create/modify:
- frontend/src/services/resources.ts: API service functions
- frontend/src/containers/ResourceListContainer.tsx: Data fetching
- frontend/src/components/ResourceCard.tsx: Presentational component
- frontend/src/app/resources/page.tsx: Route page

When complete:
- Run: cd frontend && npx tsc --noEmit
- Run: cd frontend && npm run lint
- Report results."
```

### 2.4 Track Progress

After each Task completes:
1. Read the agent's output
2. Update the feature file task table with status (DONE, BLOCKED, FAILED)
3. **Update TodoWrite**: mark the finished task as `completed` and the next task as `in_progress`
4. Verify the agent's work by reading the modified files
5. Decide whether to proceed or request fixes
6. Verify both stacks align with the API contract

---

## Phase 3: Testing

After implementation, delegate testing work to both `backend-tester` and
`frontend-tester` agents in parallel. Update the feature file status to `TESTING`.

### 3.1 Parallel Test Delegation

```
// These run in PARALLEL
Task 1: "You are the backend-tester agent. Write tests for:

Feature: <feature name>
Working directory: backend/
Files implemented:
- backend/app/models/resource.rb
- backend/app/services/module/service_name.rb
- backend/app/controllers/api/v1/resources_controller.rb

Write RSpec tests covering:
1. Model specs: associations, validations, scopes
2. Service specs: happy path, edge cases, error handling
3. Request specs: authentication, happy path, error responses
4. Use FactoryBot factories with traits
5. Verify API responses match the contract

When complete, run: cd backend && bundle exec rspec and report results."

Task 2: "You are the frontend-tester agent. Write tests for:

Feature: <feature name>
Working directory: frontend/
Files implemented:
- frontend/src/components/ResourceCard.tsx
- frontend/src/containers/ResourceListContainer.tsx
- frontend/src/services/resources.ts

Write tests covering:
1. Component render tests (renders without crashing)
2. User interaction (clicks, form submissions)
3. Async data loading (loading states, error states, success)
4. Form validation (valid/invalid inputs)
5. API service tests with mocked fetch
6. Verify service functions match the API contract types

When complete, run: cd frontend && npm test and report results."
```

### 3.2 Quality Gates (Grind Agent)

All of the following MUST pass before moving to review:

**Backend:**
1. `cd backend && bundle exec rubocop` — zero offenses
2. `cd backend && bundle exec rspec` — all passing

**Frontend:**
3. `cd frontend && npx tsc --noEmit` — zero errors
4. `cd frontend && npm run lint` — zero errors
5. `cd frontend && npm test` — all passing

**Delegate gates to the grind agent — one Task per stack, run in PARALLEL:**

```
Task 1 (subagent_type: general-purpose): "You are the grind agent. Read
agents/grind.md for your full instructions.

Context: We just implemented <feature summary> in the BACKEND. Files changed:
- backend/<file list>

Run these verification commands in order and fix any failures:
1. cd backend && bundle exec rubocop -A
2. cd backend && bundle exec rubocop
3. cd backend && bundle exec rspec

Max iterations: 10."

Task 2 (subagent_type: general-purpose): "You are the grind agent. Read
agents/grind.md for your full instructions.

Context: We just implemented <feature summary> in the FRONTEND. Files changed:
- frontend/<file list>

Run these verification commands in order and fix any failures:
1. cd frontend && npx tsc --noEmit
2. cd frontend && npm run lint
3. cd frontend && npm test

Max iterations: 10."
```

- If both grind agents return **CONVERGED**: proceed to review.
- If either returns **DID NOT CONVERGE**: stop the pipeline and report to the
  user with the remaining errors and grind agent's recommendation.

---

## Phase 4: Review

After tests pass, delegate code reviews to both `backend-reviewer` and
`frontend-reviewer` agents in parallel. Update the feature file status to `IN_REVIEW`.

### 4.1 Parallel Review Delegation

```
// These run in PARALLEL
Task 1: "You are the backend-reviewer agent. Review the following changes:

Feature: <feature name>
Working directory: backend/
Files changed:
- backend/app/models/resource.rb: <summary>
- backend/app/services/module/service_name.rb: <summary>
- backend/app/controllers/api/v1/resources_controller.rb: <summary>
- backend/spec/models/resource_spec.rb: <summary>

Review criteria:
1. Rails conventions - proper patterns, naming, structure
2. Performance - N+1 queries, missing indices, pagination
3. Security - authentication, authorization, strong params
4. Code quality - SRP, readability, frozen_string_literal
5. Test coverage - adequate specs for all code paths
6. API contract adherence - responses match agreed shapes

Provide verdict: APPROVED, NEEDS_CHANGES, or BLOCKED."

Task 2: "You are the frontend-reviewer agent. Review the following changes:

Feature: <feature name>
Working directory: frontend/
Files changed:
- frontend/src/components/ResourceCard.tsx: <summary>
- frontend/src/containers/ResourceListContainer.tsx: <summary>
- frontend/src/services/resources.ts: <summary>

Review criteria:
1. React best practices - hooks rules, key props, memoization
2. Next.js conventions - server vs client, metadata, loading states
3. Mantine UI usage - correct components, accessibility
4. TypeScript - no any, proper types, type safety
5. Performance - unnecessary re-renders, bundle size
6. Security - XSS, secrets in client code
7. Test coverage adequacy
8. API contract adherence - service types match backend responses

Provide verdict: APPROVED, NEEDS_CHANGES, or BLOCKED."
```

### 4.2 Handle Review Feedback

- **If BOTH approve:** Proceed to evaluation.
- **If either returns NEEDS_CHANGES:** Delegate the review feedback to the
  **grind agent** for the affected stack:

  For **backend** review feedback:

  ```
  Task (subagent_type: general-purpose): "You are the grind agent. Read
  agents/grind.md for your full instructions.

  The backend reviewer requested these changes:
  <paste full reviewer feedback here>

  Apply the requested changes, then re-run quality gates:
  1. cd backend && bundle exec rubocop -A
  2. cd backend && bundle exec rubocop
  3. cd backend && bundle exec rspec

  Max iterations: 10."
  ```

  For **frontend** review feedback:

  ```
  Task (subagent_type: general-purpose): "You are the grind agent. Read
  agents/grind.md for your full instructions.

  The frontend reviewer requested these changes:
  <paste full reviewer feedback here>

  Apply the requested changes, then re-run quality gates:
  1. cd frontend && npx tsc --noEmit
  2. cd frontend && npm run lint
  3. cd frontend && npm test

  Max iterations: 10."
  ```

  After the grind agent converges, **re-run the review** for that stack only.
  If it fails to converge after the second review cycle, stop and report to
  the user.

- **If either returns BLOCKED:** Stop autonomous execution and surface the
  concerns to the user for a decision.

---

## Phase 5: Eval & Security

### 5.1 Evaluation

Run the eval agent to score the implementation against quality rubrics:
- Backend code quality score (target >= 0.7)
- Frontend code quality score (target >= 0.7)
- Overall integration score
- Test coverage score
- Convention adherence score

If eval score < 0.7 for either stack, delegate improvements to the appropriate
developer agent and re-evaluate.

### 5.2 Security Check

For features involving authentication, authorization, user input, or data exposure,
run a security audit covering both stacks:

**Backend:**
- SQL injection prevention (parameterized queries)
- Mass assignment protection (strong params)
- Authentication/authorization on all endpoints
- CSRF protection
- Secrets management (no hardcoded credentials)

**Frontend:**
- No `dangerouslySetInnerHTML` without sanitization
- No secrets or API keys in client-side code
- User input validated before use
- No `eval()` or `new Function()` usage
- XSS prevention

---

## Phase 6: Completion

Once all gates pass and reviews are approved, finalize the feature.

### 6.1 Git Workflow

```bash
# Create feature branch
git checkout -b feature/<feature-slug>

# Stage backend changes
git add backend/<changed files>

# Stage frontend changes
git add frontend/<changed files>

# Commit with descriptive message
git commit -m "feat: <descriptive commit message>

Backend:
- <bullet point of what changed in backend>
- <bullet point of what changed in backend>

Frontend:
- <bullet point of what changed in frontend>
- <bullet point of what changed in frontend>"

# Push and create PR
git push -u origin feature/<feature-slug>
gh pr create --title "feat: <title>" --body "<description covering both stacks>"
```

### 6.2 Final Checklist

- [ ] All requirements from the feature file are met
- [ ] All tasks in the feature file are DONE
- [ ] API contract is respected by both stacks
- [ ] `cd backend && bundle exec rubocop` passes (zero offenses)
- [ ] `cd backend && bundle exec rspec` passes (all green)
- [ ] `cd frontend && npx tsc --noEmit` passes (zero errors)
- [ ] `cd frontend && npm run lint` passes (zero errors)
- [ ] `cd frontend && npm test` passes (all green)
- [ ] Backend code review approved
- [ ] Frontend code review approved
- [ ] Eval score >= 0.7
- [ ] No `binding.pry` / debug statements in backend
- [ ] No `console.log` debug statements in frontend
- [ ] No TODO comments without tracking issues
- [ ] Feature file status updated to COMPLETE
- [ ] All TodoWrite tasks marked as `completed`

### 6.3 Report to User

Provide a summary covering both stacks:

```markdown
## Feature Complete: <Feature Name>

### What was built

#### Backend
- <Summary of backend implementation>

#### Frontend
- <Summary of frontend implementation>

### API Contract
- `GET /api/v1/resources` - List endpoint
- `POST /api/v1/resources` - Create endpoint

### Files changed

#### Backend
- `backend/app/models/resource.rb` - <what changed>
- `backend/app/services/module/service_name.rb` - <what changed>
- `backend/app/controllers/api/v1/resources_controller.rb` - <what changed>

#### Frontend
- `frontend/src/components/ResourceCard.tsx` - <what changed>
- `frontend/src/containers/ResourceListContainer.tsx` - <what changed>
- `frontend/src/services/resources.ts` - <what changed>

### Tests added

#### Backend
- `backend/spec/models/resource_spec.rb` - <what's tested>
- `backend/spec/requests/api/v1/resources_spec.rb` - <what's tested>

#### Frontend
- `frontend/src/components/ResourceCard.test.tsx` - <what's tested>
- `frontend/src/containers/ResourceListContainer.test.tsx` - <what's tested>

### Quality gates
- Backend Rubocop: PASS (zero offenses)
- Backend RSpec: PASS (X examples, 0 failures)
- Frontend TypeScript: PASS (zero errors)
- Frontend Lint: PASS (zero errors)
- Frontend Jest: PASS (X tests, 0 failures)
- Backend Review: APPROVED
- Frontend Review: APPROVED
- Eval: 0.X
```

---

## Error Recovery

- If an agent task fails, read the error output carefully
- Determine if the failure is in backend or frontend (or both)
- Determine if it is a code error (delegate fix to appropriate developer) or a
  requirements issue (ask user)
- Never skip a failing quality gate; fix it before proceeding
- If a cross-stack issue arises (e.g., API contract mismatch), fix the API contract
  first, then update both stacks
- For persistent failures, escalate to the user with full context including which
  stack(s) are affected
