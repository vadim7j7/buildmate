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

---

## Pipeline

Every feature flows through the following stages:

```
Plan --> Implement --> Test --> Review --> Eval
```

### Phase 1: Planning

1. **Understand the request.** Read the user's feature request. Identify scope.
2. **Check existing patterns.** Read `patterns/frontend-patterns.md` and scan
   existing components, containers, and services for project conventions.
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

4. **Validate.** For large features (>5 files), confirm the plan with the user.

### Phase 2: Implementation

Update feature status to `IN_PROGRESS`. Delegate to `frontend-developer`:

```
Task: "You are the frontend-developer agent. Your task:

1. Read patterns/frontend-patterns.md for code conventions
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

Provide verdict: APPROVE or REQUEST_CHANGES."
```

- **APPROVE**: Proceed to eval/completion
- **REQUEST_CHANGES**: Delegate fixes to `frontend-developer`, then re-review

### Phase 5: Evaluation (Optional)

If warranted, run the eval-agent for a scored quality assessment.

### Quality Gates

Before moving from Implementation to Testing, these MUST pass:

| Gate | Command | Requirement |
|---|---|---|
| TypeScript | `npx tsc --noEmit` | Zero errors |
| Lint | `npm run lint` | Zero errors |
| Tests | `npm test` | All passing |
| Eval score | eval-agent | >= 0.7 |

If any gate fails, delegate a fix to `frontend-developer` and re-run.

### Phase 6: Completion

Update feature status to `COMPLETE`. Report to user:

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
