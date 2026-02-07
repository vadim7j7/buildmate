---
name: pm
description: Invoke the PM orchestration workflow to plan and delegate feature development. Use this for any non-trivial feature that requires planning, implementation, testing, and review.
---

# /pm — Project Manager Workflow

Invokes the PM orchestration workflow for feature development. The PM coordinates specialist agents to build features through a structured pipeline.

## Usage

```
/pm Build a user authentication system with OAuth
/pm Add pagination to the product listing page
/pm Refactor the payment processing module
```

Or use the alternative syntax:
```
Use PM: Build a user authentication system with OAuth
```

## What This Does

1. **Loads the orchestrator workflow** from `.claude/agents/orchestrator.md`
2. **Follows the 5-phase pipeline:**
   - Phase 1: Planning (interactive with user)
   - Phase 2: Implementation (delegates to developer agents)
   - Phase 3: Testing (delegates to tester agents)
   - Phase 4: Review (delegates to reviewer agents)
   - Phase 5: Completion (final report)

## Workflow

### Step 1: Load Orchestrator

Read the orchestrator workflow guide:

```
Read .claude/agents/orchestrator.md
```

This file contains:
- Available agents and their roles
- Quality gates for each stack
- Delegation templates
- Phase-by-phase instructions

### Step 2: Follow the Phases

After reading the orchestrator, execute each phase as instructed:

1. **Phase 1 (Planning):** Check previous context, understand requirements, create feature file, get user approval
2. **Phase 2 (Implementation):** Delegate to developer agents via Task tool
3. **Phase 3 (Testing):** Delegate to tester agents via Task tool
4. **Phase 4 (Review):** Delegate to reviewer agents via Task tool
5. **Phase 5 (Completion):** Update feature status, report to user

## Key Rules

1. **Always read the orchestrator first** — It contains the delegation templates and quality gates
2. **Delegate, don't implement** — The PM coordinates; specialist agents do the work
3. **Use Task tool for delegation** — Spawn agents with `subagent_type: general-purpose`
4. **Track progress** — Update feature files and TodoWrite as work progresses

## Example Delegation

```
Task (subagent_type: general-purpose):
"You are the backend-developer agent. Read .claude/agents/backend-developer.md for your role and instructions.

Your task: Implement user authentication with JWT tokens

Requirements:
- User model with email/password
- Login/logout endpoints
- JWT token generation and validation

When complete, report what you implemented and any concerns."
```
