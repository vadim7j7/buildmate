---
name: PM
description: |
  ORCHESTRATION GUIDE for React + Next.js features. When user says "Use PM:" or "/pm",
  the MAIN AGENT follows this workflow to coordinate frontend specialist agents.
  IMPORTANT: This is NOT a sub-agent to spawn via Task tool.
tools: Read, Write, Edit, Bash, Grep, Glob, Task
model: opus
---

# PM Orchestration Workflow Guide (React + Next.js)

## CRITICAL: This Is NOT a Spawnable Agent

**This file is a WORKFLOW GUIDE, not a sub-agent.** The main Claude agent reads
this file and follows the instructions directly. You do NOT spawn this as a
sub-agent via the Task tool.

### Correct Usage

```
Use PM: Build a project dashboard with filtering and search
```

When triggered, **you** (the main agent) follow the phases below, delegating
work to specialist sub-agents via the Task tool.

---

## Specialist Agents

| Agent | Name | Responsibility |
|---|---|---|
| `frontend-developer` | Frontend Developer | Implements Next.js pages, components, containers, services |
| `frontend-tester` | Frontend Tester | Writes Jest + RTL unit tests and Playwright E2E tests |
| `frontend-reviewer` | Frontend Reviewer | Reviews code for quality, accessibility, performance, security |
| `grind` (general-purpose) | Grind | Fix-verify loops for quality gates and review fixes |

---

## Pipeline

Every feature flows through the following stages:

```
Plan --> Implement --> Test --> Review --> Eval
```

### Phase 1: Planning (INTERACTIVE)

> **This phase is interactive.** Ask the user clarifying questions before
> committing to a plan. Use the AskUserQuestion tool when requirements are
> ambiguous, the scope is unclear, or multiple valid approaches exist.
> Once the user approves the plan, Phases 2–6 run **autonomously**.

1. **Understand the request.** Read the user's feature request. Identify scope.
2. **Check existing patterns.** Read `patterns/frontend-patterns.md` and
   `styles/frontend-typescript.md`, then scan existing components, containers,
   and services for project conventions.
3. **Create a feature file** at `.claude/context/features/<slug>.md`:

```markdown
# Feature: <Feature Name>

## Status: PLANNING

## Overview
<What and why>

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Technical Approach
- Pages: <which routes>
- Containers: <which containers>
- Components: <which components>
- Services: <which API services>
- Contexts: <if needed>

## Files to Create/Modify
- `src/app/path/page.tsx` - New page
- `src/containers/FeatureContainer.tsx` - Data fetching
- `src/components/FeatureCard.tsx` - UI component
- `src/services/feature.ts` - API service

## Tasks
| # | Task | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 1 | Implement components and pages | frontend-developer | PENDING | |
| 2 | Write unit and integration tests | frontend-tester | PENDING | |
| 3 | Code review | frontend-reviewer | PENDING | |
```

4. **Create TodoWrite task list.** Use the **TodoWrite tool** to create a visible task
   list for the user. This provides real-time progress tracking throughout the pipeline.
   Break the feature into specific tasks:

   - Implement components (pending)
   - Implement containers (pending)
   - Implement API services (pending)
   - Implement pages (pending)
   - Write tests (pending)
   - Run quality gates (tsc, lint, tests) (pending)
   - Code review (pending)
   - Final verification and cleanup (pending)

   **TodoWrite rules:**
   - Create the list as soon as planning is complete (end of Phase 1)
   - Mark each task `in_progress` before starting work on it (only one at a time)
   - Mark each task `completed` immediately after it finishes successfully
   - If a task needs rework after a failure, keep it `in_progress` and add a new fix task
   - Update the list at every phase transition

5. **Validate the plan.**
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

### Phase 2: Implementation

Update feature status to `IN_PROGRESS`. Delegate to `frontend-developer`:

```
Task: "You are the frontend-developer agent. Your task:

1. Read patterns/frontend-patterns.md and styles/frontend-typescript.md for code conventions
2. <Specific implementation steps>

Requirements:
- Server Components by default, 'use client' only when needed
- Use Mantine UI components (not raw HTML)
- Use type for props, not interface
- Use request<T>() wrapper for API calls
- Containers fetch data with useEffect + IIFE async pattern
- Forms use @mantine/form with showNotification for feedback

Files to create/modify:
- <file list>

When complete, run:
  npx tsc --noEmit
  npm run lint
Report results."
```

For independent tasks (e.g., separate components that don't depend on each
other), delegate in parallel. For dependent tasks (e.g., service must exist
before container uses it), delegate sequentially.

After each Task completes:
1. Read the agent's output
2. Update the feature file task table with status (DONE, BLOCKED, FAILED)
3. **Update TodoWrite**: mark the finished task as `completed` and the next task as `in_progress`
4. Verify the agent's work by reading the modified files
5. Decide whether to proceed or request fixes

### Phase 3: Testing

Update feature status to `TESTING`. Delegate to `frontend-tester`:

```
Task: "You are the frontend-tester agent. Write tests for:

Feature: <name>
Files implemented:
- <file list>

Write tests covering:
1. Component render tests (renders without crashing)
2. User interaction (clicks, form submissions)
3. Async data loading (loading states, error states, success)
4. Form validation (valid/invalid inputs)
5. Accessibility (ARIA attributes, keyboard navigation)

Run: npm test
Report pass/fail summary."
```

### Phase 4: Review

Update feature status to `IN_REVIEW`. Delegate to `frontend-reviewer`:

```
Task: "You are the frontend-reviewer agent. Review changes for:

Feature: <name>
Files changed:
- <file list with summaries>

Review for:
1. React best practices (hooks rules, key props, memoization)
2. Next.js conventions (server vs client, metadata, loading states)
3. Mantine UI usage (correct components, accessibility)
4. TypeScript (no any, proper types, type safety)
5. Performance (unnecessary re-renders, bundle size)
6. Security (XSS, secrets in client code)
7. Test coverage adequacy

Provide verdict: APPROVED, NEEDS_CHANGES, or BLOCKED."
```

- **APPROVED**: Proceed to eval/completion.
- **NEEDS_CHANGES**: Delegate the review feedback to the **grind agent**:

  ```
  Task (subagent_type: general-purpose): "You are the grind agent. Read
  agents/grind.md for your full instructions.

  The reviewer requested these changes:
  <paste full reviewer feedback here>

  Apply the requested changes, then re-run quality gates:
  1. npx tsc --noEmit
  2. npm run lint
  3. npm test

  Max iterations: 10."
  ```

  After the grind agent converges, **re-run the review** (delegate to
  frontend-reviewer again). If it fails to converge after the second review
  cycle, stop and report to the user.

- **BLOCKED**: Stop autonomous execution and surface the concerns to the user
  for a decision.

### Quality Gates (Grind Agent)

Before moving to Review, these MUST pass:

| Gate | Command | Requirement |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | Zero errors |
| Lint | `npm run lint` | Zero errors |
| Tests | `npm test` | All passing |

**Delegate all gates to the grind agent in a single Task call:**

```
Task (subagent_type: general-purpose): "You are the grind agent. Read
agents/grind.md for your full instructions.

Context: We just implemented <feature summary>. Files changed:
- <file list>

Run these verification commands in order and fix any failures:
1. npx tsc --noEmit
2. npm run lint
3. npm test

Max iterations: 10."
```

- If the grind agent returns **CONVERGED**: proceed to review.
- If the grind agent returns **DID NOT CONVERGE**: stop the pipeline and report
  to the user with the remaining errors and grind agent's recommendation.

### Phase 5: Evaluation (Optional)

If warranted, run the eval-agent for a scored quality assessment.

### Phase 6: Completion

Update feature status to `COMPLETE`. Mark all TodoWrite tasks as `completed`. Report to user:

```markdown
## Feature Complete: <Name>

### What was built
- <summary>

### Files changed
- `src/...` - <what>

### Tests added
- `src/...test.tsx` - <what's tested>

### Quality gates
- TypeScript: PASS
- Lint: PASS
- Tests: X/X passing
- Review: APPROVED
```
