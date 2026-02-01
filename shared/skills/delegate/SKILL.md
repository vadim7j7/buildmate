---
name: delegate
description: Smart delegation that analyses tasks and routes to parallel or sequential execution
---

# /delegate

## What This Does

Analyses a set of tasks to determine whether they should run in parallel or
sequentially, then routes to the appropriate execution mode. This is the
recommended way to hand off multi-step work when you are unsure which
execution strategy is best.

## Usage

```
/delegate Implement user auth, add rate limiting, write API docs
/delegate "Build login page" "Build signup page" "Build dashboard"
```

## How It Works

1. **Parse tasks.** Split the input into individual tasks. Tasks can be
   separated by commas, newlines, or quoted strings.

2. **Analyse dependencies.** For each pair of tasks, determine whether one
   depends on the output of another:
   - **Data dependency:** Task B needs files or data produced by Task A.
   - **Order dependency:** Task B logically follows Task A (e.g., "test"
     follows "implement").
   - **Resource dependency:** Both tasks modify the same files.

3. **Build a dependency graph.** Map tasks to a directed acyclic graph (DAG)
   where edges represent dependencies.

4. **Choose execution strategy:**

   | Condition                          | Strategy     |
   |------------------------------------|--------------|
   | No dependencies between any tasks  | `/parallel`  |
   | All tasks form a single chain      | `/sequential`|
   | Mix of independent and dependent   | Hybrid       |

   **Hybrid strategy:** Independent task groups run in parallel, while
   dependent chains within each group run sequentially.

5. **Route to the appropriate skill:**
   - If all parallel: invoke `/parallel` with all tasks
   - If all sequential: invoke `/sequential` with the ordered task list
   - If hybrid: invoke `/parallel` for each independent group, where each
     group internally runs `/sequential`

6. **Report the delegation plan.** Before execution, output the plan:

   ```
   ## Delegation Plan

   **Strategy:** Parallel (3 independent tasks)

   ### Worktree 1
   - Build login page

   ### Worktree 2
   - Build signup page

   ### Worktree 3
   - Build dashboard
   ```

   Or for sequential:

   ```
   ## Delegation Plan

   **Strategy:** Sequential (3 dependent stages)

   1. Implement user auth
   2. Write tests for auth
   3. Write API docs for auth endpoints
   ```

## Dependency Detection Heuristics

The delegate skill uses these heuristics to detect dependencies:

- Tasks mentioning "test" depend on "implement" tasks
- Tasks mentioning "docs" depend on the feature they document
- Tasks modifying the same module are resource-dependent
- Tasks with explicit ordering words ("then", "after", "once") are sequential
- Tasks for different features or modules are typically independent

## Error Handling

- If only one task is provided, run it directly without delegation overhead.
- If dependency analysis is ambiguous, default to sequential (safer).
- If a parallel group fails, report which worktree failed and what succeeded.
