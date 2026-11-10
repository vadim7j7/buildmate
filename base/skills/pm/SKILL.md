---
name: pm
description: Plan a feature and deliver it through the full agent pipeline (plan, implement, verify, test, review, evaluate). Use when the user runs /pm or says "Use PM:".
argument-hint: "<feature request> [--branch | --ship | --no-git]"
---

# /pm — Project Manager Workflow

Runs the PM pipeline for a feature: you plan it with the user, then delegate the
work to the specialist agents and track it to completion.

## Usage

```
/pm Build a user authentication system with OAuth
/pm Add pagination to the product listing page --branch
Use PM: Add seeds to generate fake data
```

| Flag | Behaviour |
|------|-----------|
| `--branch` | Create a feature branch after plan approval |
| `--ship` | Create a branch and run `/ship` (commit, push, PR) at the end |
| `--no-git` | No git automation, whatever `.claude/buildmate.json` says |

Without a flag, `pm.git_workflow` in `.claude/buildmate.json` decides (default `"none"`).

## Step 1: Read the workflow

Read `orchestrator.md` in this skill's folder (`.claude/skills/pm/orchestrator.md`).
It lists the agents, the quality gates for each stack, the delegation prompts and
the phase-by-phase instructions for this project.

## Step 2: Follow every phase

1. **Planning** — understand the request, write the feature file, get approval
2. **Implementation** — delegate to the developer agent(s), then verify
3. **Testing** — delegate to the tester agent(s), then the `grind` agent for quality gates
4. **Review** — delegate to the reviewer agent(s); at most 2 fix rounds
5. **Evaluation & documentation** — `eval-agent` and `documentation-specialist`
6. **Completion** — `/ship` if configured, then report to the user

## Rules

1. **Follow the full pipeline**, even for small tasks: the user asked for it.
2. **Delegate; don't implement.** You coordinate. Developer, tester and reviewer
   agents write and check the code.
3. **Name the agent:** `Agent(subagent_type: "<agent-name>", ...)`. That applies
   the agent's own model, tools and skills from `.claude/agents/<agent-name>.md`.
4. **Track progress** in the feature file (`.claude/context/features/<slug>.md`)
   and in your task list.

## Example

```
/pm Add seeds to generate fake data

1. Read .claude/skills/pm/orchestrator.md
2. Write .claude/context/features/seed-data.md and get the plan approved
3. Agent(subagent_type: "backend-developer", prompt: "Add seed data for ...")
4. Agent(subagent_type: "backend-tester", prompt: "Test the seeds ...")
5. Agent(subagent_type: "grind", prompt: "Run the quality gates ...")
6. Agent(subagent_type: "backend-reviewer", prompt: "Review ...")
7. Report to the user
```

## Related skills

- `/branch` — create a feature branch
- `/ship` — run the gates, commit, push and open a PR
- `/sync` — sync the branch with main/master
- `/recap` — load the saved context of earlier sessions
