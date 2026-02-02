---
name: PM
description: |
  ORCHESTRATION GUIDE for React Native mobile features. When user says "Use PM:" or "/pm",
  the MAIN AGENT follows this workflow to coordinate specialist mobile agents.
  IMPORTANT: This is NOT a sub-agent to spawn via Task tool.
tools: Read, Write, Edit, Bash, Grep, Glob, Task
model: opus
---

# PM Orchestration Workflow Guide -- React Native

## CRITICAL: This Is NOT a Spawnable Agent

**This file is a WORKFLOW GUIDE, not a sub-agent.** The main Claude agent reads this
file and follows the instructions directly. You do NOT spawn this as a sub-agent via
the Task tool.

### Correct Usage

The user invokes this workflow by saying:

```
Use PM: Build a transaction list screen with filtering and sorting
```

or

```
/pm Add offline sync for budget categories
```

When triggered, **you** (the main agent) follow the phases below, delegating work
to specialist sub-agents via the Task tool.

### WRONG Usage (Do NOT Do This)

```
// WRONG - Do not try to spawn PM as a sub-agent
Task("Follow the PM workflow to build transaction list")

// WRONG - Do not delegate the orchestration itself
Task("Act as PM and coordinate building the screen")
```

**You ARE the PM.** You read requirements, create the plan, delegate implementation
tasks, and track progress yourself.

---

## Sub-Agents

| Agent                  | Role                                     |
|------------------------|------------------------------------------|
| `mobile-developer`     | Writes production React Native code      |
| `mobile-tester`        | Writes and runs Jest + RNTL tests        |
| `mobile-code-reviewer` | Reviews code against RN conventions      |
| `grind` (general-purpose) | Fix-verify loops for quality gates and review fixes |

---

## Phase 1: Planning (INTERACTIVE)

> **This phase is interactive.** Ask the user clarifying questions before
> committing to a plan. Use the AskUserQuestion tool when requirements are
> ambiguous, the scope is unclear, or multiple valid approaches exist.
> Once the user approves the plan, Phases 2–5 run **autonomously**.

When the user provides a feature request, begin by gathering requirements and
creating a feature file.

### 1.1 Understand the Request

- Read the user's request carefully
- Identify the scope: new screen, new component, data layer, or cross-cutting feature
- Check existing code for context using Grep and Glob
- Read any existing feature files in `.claude/context/features/` for project patterns
- Determine which layers are involved: UI (screens/components), state (stores/queries),
  data (db/queries, services/api), or all

### 1.2 Create a Feature File

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
<High-level implementation plan including:>
- Screens to create/modify
- Components needed
- Zustand stores (UI state only)
- React Query hooks (data fetching)
- Drizzle queries (database operations)
- Navigation changes
- i18n keys needed

## Files to Create/Modify
- `app/(tabs)/feature.tsx` - <what changes>
- `components/ui/FeatureCard.tsx` - <what changes>
- `stores/useFeatureStore.ts` - <what changes>
- `queries/useFeature.ts` - <what changes>
- `db/queries/feature.ts` - <what changes>
- `locales/en.json` - <new translation keys>

## Tasks
| # | Task | Agent | Status | Notes |
|---|------|-------|--------|-------|
| 1 | <implementation task> | mobile-developer | PENDING | |
| 2 | <test task> | mobile-tester | PENDING | |
| 3 | <review task> | mobile-code-reviewer | PENDING | |

## Platform Considerations
- iOS: <any iOS-specific considerations>
- Android: <any Android-specific considerations>

## Dependencies
- <Any packages to install via npx expo install>

## Completion Criteria
- [ ] All requirements implemented
- [ ] All tests passing
- [ ] Code review passed
- [ ] No TypeScript errors
- [ ] No lint errors
- [ ] Works on both iOS and Android
```

### 1.3 Create TodoWrite Task List

After creating the feature file, use the **TodoWrite tool** to create a visible task list for the user. This provides real-time progress tracking throughout the pipeline.

Break the feature into specific, actionable tasks. Example:

- Implement Drizzle schema and DB queries (pending)
- Implement Zustand store (pending)
- Implement React Query hooks (pending)
- Implement screen and components (pending)
- Add i18n translation keys (pending)
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

## Phases 2–5: Autonomous Execution

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

Delegate implementation work to the `mobile-developer` agent via the Task tool.
Update the feature file status to `IN_PROGRESS`.

### 2.1 Agent Delegation

Use the Task tool to spawn the mobile-developer sub-agent. Always provide clear,
specific instructions including:

- What to build (screen, component, store, query, etc.)
- Which files to create or modify
- What patterns to follow (reference existing code and CLAUDE.md)
- State management rules (Zustand for UI only, React Query for data, Drizzle for DB)
- Acceptance criteria

**Delegation template:**

```
Task tool call with instructions:
"You are the mobile-developer agent. Your task:

1. <Specific implementation step>
2. <Specific implementation step>
3. <Specific implementation step>

Requirements:
- Follow existing code patterns in <reference file>
- Use Zustand ONLY for UI state (loading, modals, filters)
- Use React Query for all data fetching
- Use Drizzle queries from db/queries/ for database operations
- Use FlashList for any list with 20+ items
- Use StyleSheet.create with theme constants from @/constants
- All UI strings must use t('key') from i18next
- Support both iOS and Android

Files to create/modify:
- <file path>: <what to do>

When complete:
1. Run npx tsc --noEmit and fix any TypeScript errors
2. Run npm run lint and fix any lint errors
3. Report what you implemented and any concerns."
```

### 2.2 Parallel vs Sequential Execution

**Use PARALLEL execution when tasks are independent:**

```
// These can run in parallel - different layers, no dependencies
Task 1: "mobile-developer: Create the Drizzle schema and DB queries..."
Task 2: "mobile-developer: Build the UI components (TransactionCard, FilterBar)..."
```

Parallel execution is appropriate when:
- Tasks modify different files
- Tasks don't depend on each other's output
- Tasks work on separate layers (e.g., DB queries vs UI components)

**Use SEQUENTIAL execution when tasks have dependencies:**

```
// Step 1 must complete before Step 2
Task 1: "mobile-developer: Create the Drizzle schema and DB queries..."
// Wait for Task 1 to complete, then:
Task 2: "mobile-developer: Build React Query hooks using the DB queries..."
// Wait for Task 2 to complete, then:
Task 3: "mobile-developer: Build the screen using the React Query hooks..."
```

Sequential execution is required when:
- A task depends on files created by a previous task
- DB schema must exist before query functions
- Query hooks must exist before screens can use them
- Store shape must be defined before components consume it

### 2.3 Track Progress

After each Task completes:
1. Read the agent's output
2. Update the feature file task table with status (DONE, BLOCKED, FAILED)
3. **Update TodoWrite**: mark the finished task as `completed` and the next task as `in_progress`
4. Verify the agent's work by reading the modified files
5. Decide whether to proceed or request fixes

---

## Phase 3: Testing

After implementation, delegate testing. Update the feature file status to `TESTING`.

**Testing and review can run in PARALLEL** since they are independent -- the tester
writes and runs tests while the reviewer reads the implementation.

### 3.1 Delegate Test Writing

```
Task: "You are the mobile-tester agent. Write tests for the feature:

Feature: <feature name>
Files implemented:
- <file 1>
- <file 2>

Write tests covering:
1. Component rendering and interactions (render, fireEvent, expect)
2. Screen data loading and navigation
3. Zustand store state transitions (reset before each test)
4. React Query hooks (fresh QueryClient per test)
5. Error states and loading states
6. Platform-specific behaviour if applicable

Place tests in __tests__/ following existing conventions.
When complete, run npm test and report results."
```

### 3.2 Quality Gates (Grind Agent)

All of the following MUST pass before marking the feature complete:

1. **TypeScript compilation**: `npx tsc --noEmit` with zero errors
2. **Linting**: `npm run lint` with zero errors
3. **Tests**: `npm test` with all new AND existing tests passing
4. **No regressions**: Existing functionality must not be broken

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

---

## Phase 4: Review

After implementation (can run in parallel with testing), delegate a code review.
Update the feature file status to `IN_REVIEW`.

### 4.1 Delegate Review

```
Task: "You are the mobile-code-reviewer agent. Review the following changes:

Feature: <feature name>
Files changed:
- <file 1>: <summary of changes>
- <file 2>: <summary of changes>

Review against React Native conventions in CLAUDE.md. Pay special attention to:
1. State management boundaries (Zustand for UI only, React Query for data)
2. FlashList usage for long lists
3. StyleSheet.create with theme constants
4. expo-router navigation patterns
5. Platform-specific handling (iOS vs Android)
6. i18n compliance (all strings use t())
7. TypeScript strictness
8. Performance (memoization, list virtualization)

Provide findings as BLOCKER, WARNING, or SUGGESTION.
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
  1. npx tsc --noEmit
  2. npm run lint
  3. npm test

  Max iterations: 10."
  ```

  After the grind agent converges, **re-run the review** (delegate to
  mobile-code-reviewer again). If it fails to converge after the second review
  cycle, stop and report to the user.

- **If BLOCKED:** Stop autonomous execution and surface the concerns to the
  user for a decision.
- **If review has only WARNINGs:** Proceed, noting the warnings for future improvement.

---

## Phase 5: Completion

Once all gates pass and review is approved, finalize the feature.

### 5.1 Final Checklist

- [ ] All requirements from the feature file are met
- [ ] All tasks in the feature file are DONE
- [ ] TypeScript compiles without errors (`npx tsc --noEmit`)
- [ ] Linter passes without errors (`npm run lint`)
- [ ] All tests pass (`npm test`)
- [ ] Code review approved
- [ ] Works on both iOS and Android
- [ ] No console.log / debug statements left behind
- [ ] All UI strings use i18n t() function
- [ ] No TODO comments without tracking issues

### 5.2 Update Feature File and TodoWrite

Update the feature file status to `COMPLETE` and check off all completed requirements.
Mark all remaining TodoWrite tasks as `completed`.

### 5.3 Report to User

```markdown
## Feature Complete: <Feature Name>

### What was built
- <Summary of what was implemented>

### Files changed
- `path/to/file.ext` - <what changed>

### Tests added
- `__tests__/path/to/test.ext` - <what's tested>

### Quality gates
- TypeScript: PASS
- Lint: PASS
- Tests: X/X passing
- Review: APPROVED

### Platform coverage
- iOS: <tested/verified>
- Android: <tested/verified>
```

---

## Communication Protocol

### Reading Requirements
- Always start by reading the user's full request
- Check `.claude/context/` for project-level context
- Check existing feature files to avoid conflicts

### Writing Feature Files
- Create feature files immediately during Planning
- Update status at each phase transition
- Track all tasks with agent assignments

### Status Updates
- After each phase, briefly update the user on progress
- If blocked, immediately surface the blocker to the user
- On completion, provide the full summary

### Error Recovery
- If an agent task fails, read the error output carefully
- Determine if it's a code error (delegate fix) or a requirements issue (ask user)
- Never skip a failing quality gate; fix it before proceeding
