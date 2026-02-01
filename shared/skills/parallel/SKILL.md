---
name: parallel
description: Run multiple independent tasks in parallel using git worktrees
---

# /parallel

## What This Does

Creates isolated git worktrees for each task, spawns agent instances in
parallel across them, and collects results when all agents complete. This
enables concurrent work on independent tasks without branch conflicts.

## Usage

```
/parallel "Build login page" "Build signup page" "Build dashboard"
/parallel --max 3 "Task A" "Task B" "Task C" "Task D" "Task E"
```

## How It Works

1. **Validate prerequisites.** Ensure the current directory is a git
   repository with a clean working tree. Stash uncommitted changes if
   necessary.

2. **Parse tasks.** Extract individual tasks from the input. Each quoted
   string or comma-separated item becomes a separate task.

3. **Enforce concurrency limit.** Maximum of **5** concurrent worktrees. If
   more tasks are provided, queue them and run in batches.

4. **Create worktrees.** For each task, run `scripts/spawn-worktree.sh` to:
   - Create a new git worktree branching from the current HEAD
   - Branch naming convention: `agent-parallel/<timestamp>-<task-slug>`
   - Set up the worktree environment (copy `.claude/` config if needed)
   - Return the worktree path

5. **Spawn agents.** For each worktree, use the Task tool to delegate the
   task to an agent working in that worktree's directory. Each agent:
   - Receives the task description and any shared context
   - Works independently in its own worktree
   - Writes status updates to `.agent-status/progress.md` in its worktree
   - Writes final results to `.agent-status/result.md`

6. **Monitor progress.** Periodically check `.agent-status/progress.md` in
   each worktree to report overall progress.

7. **Collect results.** When all agents complete, run
   `scripts/collect-results.sh` to:
   - Read `.agent-status/result.md` from each worktree
   - Aggregate results into a unified report
   - Identify any failures

8. **Merge results.** For each successful worktree:
   - Merge the worktree's branch back into the original branch
   - Resolve conflicts if possible, or flag them for manual resolution

9. **Clean up.** Run `scripts/cleanup-worktrees.sh` to remove all temporary
   worktrees and branches.

10. **Report summary:**

    ```
    ## Parallel Execution Report

    **Tasks:** 3
    **Succeeded:** 3
    **Failed:** 0
    **Duration:** 45s

    ### Results
    | Task              | Status  | Branch                              |
    |-------------------|---------|-------------------------------------|
    | Build login page  | SUCCESS | agent-parallel/20260201-login-page  |
    | Build signup page | SUCCESS | agent-parallel/20260201-signup-page |
    | Build dashboard   | SUCCESS | agent-parallel/20260201-dashboard   |
    ```

## Configuration

| Setting        | Default | Description                               |
|----------------|---------|-------------------------------------------|
| Max worktrees  | 5       | Maximum concurrent worktrees              |
| Timeout        | 300s    | Per-task timeout before forced cleanup    |
| Auto-merge     | true    | Automatically merge successful branches   |
| Cleanup        | true    | Remove worktrees after collection         |

## Error Handling

- If a worktree creation fails, skip that task and report the error.
- If an agent fails in a worktree, mark that task as failed and continue
  with others.
- If a merge conflict occurs, leave the branch unmerged and report the
  conflict for manual resolution.
- If all tasks fail, report the aggregate failures.
- On any unrecoverable error, run cleanup to remove partial worktrees.
