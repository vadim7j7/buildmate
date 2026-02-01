---
name: PM
description: |
  ORCHESTRATION GUIDE for Rails features. When user says "Use PM:" or "/pm",
  the MAIN AGENT follows this workflow to coordinate specialist agents.
  IMPORTANT: This is NOT a sub-agent to spawn via Task tool.
tools: Read, Write, Edit, Bash, Grep, Glob, Task
model: opus
---

# PM Orchestration Workflow Guide (Rails)

## CRITICAL: This Is NOT a Spawnable Agent

**This file is a WORKFLOW GUIDE, not a sub-agent.** The main Claude agent reads this
file and follows the instructions directly. You do NOT spawn this as a sub-agent via
the Task tool.

### Correct Usage

The user invokes this workflow by saying:

```
Use PM: Build a profile sync service with Airtable integration
```

or

```
/pm Add pagination to the candidates API endpoint
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

| Role              | subagent_type      | Purpose                          |
|-------------------|--------------------|----------------------------------|
| Developer         | backend-developer  | Write Rails production code      |
| Tester            | backend-tester     | Write and run RSpec tests        |
| Reviewer          | backend-reviewer   | Review code against conventions  |

---

## Phase 1: Planning

When the user provides a feature request, begin by gathering requirements and creating
a feature file.

### 1.1 Understand the Request

- Read the user's request carefully
- Identify the scope: is this a single feature, multiple features, or a refactor?
- Check existing code for context using Grep and Glob
- Read `patterns/backend-patterns.md` and `styles/backend-ruby.md` for conventions
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
<How this will be implemented: models, services, controllers, jobs>

## Files to Create/Modify
- `app/services/module/service_name.rb` - <what it does>
- `app/controllers/resource_controller.rb` - <what changes>
- `spec/services/module/service_name_spec.rb` - <test coverage>

## Tasks
| # | Task | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 1 | Implement service/model/controller | backend-developer | PENDING | |
| 2 | Write RSpec tests | backend-tester | PENDING | |
| 3 | Code review | backend-reviewer | PENDING | |

## Dependencies
- <Any gems, APIs, or infrastructure needed>

## Completion Criteria
- [ ] All requirements implemented
- [ ] RSpec tests passing
- [ ] Rubocop passing (zero offenses)
- [ ] Code review approved
- [ ] Eval score >= 0.7
```

### 1.3 Validate the Plan

Before proceeding to implementation:
- Confirm the plan with the user if the feature is large (>5 files changed)
- For small features, proceed directly unless the user asked for plan approval

---

## Phase 2: Implementation

Delegate implementation work to the `backend-developer` agent via the Task tool.
Update the feature file status to `IN_PROGRESS`.

### 2.1 Agent Delegation

Use the Task tool to spawn the backend-developer sub-agent. Always provide clear,
specific instructions including:
- What to build (models, services, controllers, jobs)
- Which files to create or modify
- What patterns to follow (reference `patterns/backend-patterns.md`)
- Acceptance criteria

**Delegation template:**

```
Task tool call with instructions:
"You are the backend-developer agent. Your task:

1. Read patterns/backend-patterns.md and styles/backend-ruby.md
2. <Specific implementation step>
3. <Specific implementation step>

Requirements:
- Follow the service pattern: namespaced, keyword args, ApplicationService
- Use presenter pattern for JSON responses
- Add includes() for any associations to prevent N+1
- frozen_string_literal: true on all files
- Single quotes, hash shorthand, guard clauses
- YARD docs on public methods

Files to create/modify:
- <file path>: <what to do>

When complete:
- Run: bundle exec rubocop -A on all changed files
- Run: bundle exec rspec for related spec files
- Report what you implemented and any concerns."
```

### 2.2 Parallel vs Sequential Execution

**Use PARALLEL execution when tasks are independent:**

```
// These can run in parallel - no dependencies
Task 1: "backend-developer: Build the Profile model and migration..."
Task 2: "backend-developer: Build the Sync::AirtableService..."
```

**Use SEQUENTIAL execution when tasks have dependencies:**

```
// Step 1 must complete before Step 2
Task 1: "backend-developer: Create the database migration and model..."
// Wait for Task 1, then:
Task 2: "backend-developer: Build the service layer using the new model..."
// Wait for Task 2, then:
Task 3: "backend-developer: Build the API controller using the service..."
```

### 2.3 Track Progress

After each Task completes:
1. Read the agent's output
2. Update the feature file task table with status (DONE, BLOCKED, FAILED)
3. Verify the agent's work by reading the modified files
4. Decide whether to proceed or request fixes

---

## Phase 3: Testing

After implementation, delegate testing work to the `backend-tester` agent.
Update the feature file status to `TESTING`.

### 3.1 Delegate Test Writing

```
Task: "You are the backend-tester agent. Write tests for the feature:

Feature: <feature name>
Files implemented:
- app/services/module/service_name.rb
- app/controllers/resource_controller.rb
- app/models/resource.rb

Write RSpec tests covering:
1. Model specs: associations, validations, scopes
2. Service specs: happy path, edge cases, error handling
3. Request specs: authentication, happy path, error responses
4. Use FactoryBot factories with traits

Place tests in:
- spec/models/resource_spec.rb
- spec/services/module/service_name_spec.rb
- spec/requests/resource_spec.rb

When complete, run: bundle exec rspec and report results."
```

### 3.2 Quality Gates

All of the following MUST pass before moving to review:

1. **Lint**: `bundle exec rubocop` - zero offenses
2. **Tests**: `bundle exec rspec` - all passing (new AND existing)
3. **No regressions**: Existing functionality must not be broken

If any gate fails:
- Identify the failure
- Delegate a fix to the backend-developer agent
- Re-run the gate
- Repeat until all gates pass

---

## Phase 4: Review

After tests pass, delegate a code review to the `backend-reviewer` agent.
Update the feature file status to `IN_REVIEW`.

### 4.1 Delegate Review

```
Task: "You are the backend-reviewer agent. Review the following changes:

Feature: <feature name>
Files changed:
- app/services/module/service_name.rb: <summary>
- app/controllers/resource_controller.rb: <summary>
- spec/models/resource_spec.rb: <summary>

Review criteria:
1. Rails conventions - proper patterns, naming, structure
2. Performance - N+1 queries, missing indices, pagination
3. Security - authentication, authorization, strong params
4. Code quality - SRP, readability, frozen_string_literal
5. Test coverage - adequate specs for all code paths

Run: bundle exec rubocop (verify zero offenses)
Check: N+1 queries (verify includes() usage)
Verify: test coverage meets thresholds

Provide specific, actionable feedback with file paths and line references.
Rate overall: APPROVED, NEEDS_CHANGES, or BLOCKED."
```

### 4.2 Handle Review Feedback

- If APPROVED: Proceed to completion
- If NEEDS_CHANGES: Delegate fixes to backend-developer, then re-review
- If BLOCKED: Surface the concerns to the user for decision

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
- SQL injection prevention (parameterized queries)
- Mass assignment protection (strong params)
- Authentication/authorization on all endpoints
- CSRF protection
- Secrets management (no hardcoded credentials)

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
- [ ] `bundle exec rubocop` passes (zero offenses)
- [ ] `bundle exec rspec` passes (all green)
- [ ] Code review approved
- [ ] Eval score >= 0.7
- [ ] No `binding.pry` / debug statements left behind
- [ ] No TODO comments without tracking issues
- [ ] Feature file status updated to COMPLETE

### 6.3 Report to User

Provide a summary:

```markdown
## Feature Complete: <Feature Name>

### What was built
- <Summary of what was implemented>

### Files changed
- `app/services/module/service_name.rb` - <what changed>
- `app/controllers/resource_controller.rb` - <what changed>

### Tests added
- `spec/services/module/service_name_spec.rb` - <what's tested>
- `spec/requests/resource_spec.rb` - <what's tested>

### Quality gates
- Rubocop: PASS (zero offenses)
- RSpec: PASS (X examples, 0 failures)
- Review: APPROVED
- Eval: 0.X
```

---

## Error Recovery

- If an agent task fails, read the error output carefully
- Determine if it's a code error (delegate fix) or a requirements issue (ask user)
- Never skip a failing quality gate; fix it before proceeding
- For persistent failures, escalate to the user with full context
