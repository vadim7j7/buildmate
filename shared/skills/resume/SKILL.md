---
name: resume
description: Resume previous work by loading saved context, feature files, git state, and pipeline status. Use this at the start of a session to pick up where you left off.
---

# /resume — Resume Previous Work

Gathers all available context about work in progress and presents a clear
"here's where you left off" summary so you can continue without losing momentum.

## When to Use

- At the start of a new session
- After the session-load hook shows stale context
- When you want to review the full state of the project

## What It Checks

1. **Active work context** — `.claude/context/active-work.md` (auto-saved by session-save hook)
2. **In-progress features** — All feature files in `.claude/context/features/` with status `in-progress`
3. **Git state** — Current branch, uncommitted changes, recent commits
4. **Pipeline state** — `.agent-pipeline/pipeline.json` if an agent pipeline was running
5. **Eval results** — Latest eval report in `.agent-eval-results/` if any

## Workflow

### Step 1: Read Active Work File

```bash
cat .claude/context/active-work.md
```

If it exists, note when it was last saved and summarise the key points.

### Step 2: Scan Feature Files

Read all files in `.claude/context/features/`. For each file:
- Extract the title (first `#` heading)
- Extract the status line
- If status is `in-progress`, `testing`, or `review`, list the remaining unchecked tasks

### Step 3: Check Git State

Run these commands to understand the current code state:

```bash
git branch --show-current
git status --short
git log --oneline -10
git stash list
```

Note:
- What branch you're on
- Whether there are uncommitted changes
- What the recent commits were about
- Whether there are stashed changes

### Step 4: Check Pipeline State

If `.agent-pipeline/pipeline.json` exists:

```bash
cat .agent-pipeline/pipeline.json
```

Report which stages completed, which failed, and which are pending.

### Step 5: Check Latest Eval Results

Look for the most recent eval report:

```bash
ls -t .agent-eval-results/*.md 2>/dev/null | head -1
```

If found, read it and report the overall score and any NEEDS_FIXES items.

## Output Format

Present the findings as a structured summary:

```markdown
## Session Resume

### Last Session
- **Saved:** <timestamp from active-work.md>
- **Branch:** <branch name>

### In-Progress Features
1. **<Feature Title>** — <status>
   - Remaining: <count> tasks
   - Next task: <first unchecked item>

### Current Code State
- **Branch:** `<branch>`
- **Uncommitted changes:** <count> files modified, <count> untracked
- **Recent work:** <1-line summary of last 2-3 commits>

### Pipeline Status
- <stage>: <status> (or "No active pipeline")

### Suggested Next Steps
1. <most logical next action based on context>
2. <second action>
```

## Key Rules

1. **Read, don't guess.** Only report information from actual files and git state.
2. **Be concise.** The user wants to quickly orient themselves, not read an essay.
3. **Suggest next steps.** Based on the state, recommend what to do next.
4. **Don't modify anything.** This skill is read-only. It never writes files or runs commands that change state.
