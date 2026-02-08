---
name: pm
description: Invoke the PM orchestration workflow to plan and delegate feature development. ALWAYS follows the full pipeline - no shortcuts.
---

# /pm — Project Manager Workflow

Invokes the PM orchestration workflow for feature development.

> **CRITICAL: When /pm is invoked, you MUST follow the full orchestrator workflow.**
>
> Do NOT skip steps or decide to "do it directly" because a task seems simple.
> The user explicitly requested the PM workflow — respect that request.
> Even simple tasks benefit from proper planning, delegation, and review.

## Usage

```
/pm Build a user authentication system with OAuth
/pm Add pagination to the product listing page
/pm Add seeds to generate fake data
```

Or use the alternative syntax:
```
Use PM: Build a user authentication system with OAuth
```

## What This Does

1. **Loads the orchestrator workflow** from `.claude/agents/orchestrator.md`
2. **Follows the 6-phase pipeline:**
   - Phase 1: Planning (interactive with user)
   - Phase 2: Implementation (delegates to developer agents)
   - Phase 2.5: Verification (verifiers test via HTTP/browser)
   - Phase 3: Testing (delegates to tester agents)
   - Phase 4: Review (delegates to reviewer agents)
   - Phase 5: Evaluation & Documentation
   - Phase 6: Completion (final report)

## MANDATORY Workflow

### Step 1: Load Orchestrator

**You MUST read the orchestrator first:**

```
Read .claude/agents/orchestrator.md
```

This file contains:
- Available agents and their roles
- Quality gates for each stack
- Delegation templates
- Phase-by-phase instructions

### Step 2: Follow ALL Phases

**You MUST execute each phase as instructed in the orchestrator:**

1. **Phase 1 (Planning):** Check previous context, understand requirements, create feature file, get user approval
2. **Phase 2 (Implementation):** Delegate to developer agents via Task tool
3. **Phase 3 (Testing):** Delegate to tester agents via Task tool
4. **Phase 4 (Review):** Delegate to reviewer agents via Task tool
5. **Phase 5 (Completion):** Update feature status, report to user

## CRITICAL Rules

1. **NEVER skip the orchestrator** — Always read `.claude/agents/orchestrator.md` first
2. **NEVER implement directly** — You are the PM, you delegate. Specialist agents do the work.
3. **NEVER decide a task is "too simple"** — If user invoked /pm, follow the full workflow
4. **ALWAYS use Task tool** — Spawn agents with `subagent_type: general-purpose`
5. **ALWAYS track progress** — Create feature file, use TodoWrite

## Why Delegation Matters

Even for "simple" tasks like adding seeds:
- **Developer agent** knows the framework patterns and conventions
- **Tester agent** ensures the seeds work correctly
- **Reviewer agent** catches issues you might miss
- **Feature file** tracks what was done for future reference

## Example: "Add seeds to generate fake data"

**WRONG approach (do NOT do this):**
```
"This is simple, let me just write the seeds directly..."
```

**CORRECT approach:**
```
1. Read .claude/agents/orchestrator.md
2. Create feature file: .claude/context/features/seed-data.md
3. Phase 2: Delegate to backend-developer:
   Task (subagent_type: general-purpose):
   "You are the backend-developer agent. Read .claude/agents/backend-developer.md.
   Your task: Add seed data for development..."
4. Phase 3: Delegate to backend-tester
5. Phase 4: Delegate to backend-reviewer
6. Phase 5: Report completion
```

## Delegation Template

```
Task (subagent_type: general-purpose):
"You are the backend-developer agent. Read .claude/agents/backend-developer.md for your role and instructions.

Your task: <specific implementation task>

Requirements:
<list requirements>

When complete, report what you implemented and any concerns."
```
