---
name: eval
description: Run quality evaluation against scoring rubrics and produce a scored report
---

# /eval

## What This Does

Delegates to the eval-agent to score the current work against structured
quality rubrics. Reads rubric definitions from `references/`, evaluates the
code, and writes a scored report to `.agent-eval-results/`.

## Usage

```
/eval                     # Evaluate all changed files
/eval path/to/file.ts     # Evaluate a specific file
/eval --dimension security  # Evaluate only the security dimension
```

## How It Works

1. **Load rubrics.** Read the scoring rubrics from:
   - `references/eval-rubrics.md` -- dimension weights and descriptions
   - `references/eval-metrics.md` -- per-level scoring criteria (0.0-1.0)

2. **Identify scope.** Determine which files to evaluate:
   - All changed files vs the base branch (default)
   - A specific file if one was provided
   - A specific dimension if `--dimension` was passed

3. **Delegate to the eval-agent.** Use the Task tool to invoke the eval-agent
   with:
   - The full content of each file being evaluated
   - The rubric definitions
   - Any pipeline context from `.agent-pipeline/` (implementation notes, test
     results, review findings)

4. **Score each dimension.** The eval-agent scores each dimension on a 0.0-1.0
   scale according to the metric definitions:

   | Dimension      | Weight |
   |----------------|--------|
   | Correctness    | 30%    |
   | Code Quality   | 15%    |
   | Security       | 25%    |
   | Performance    | 20%    |
   | Test Coverage  | 10%    |

5. **Produce the report.** The eval-agent returns a structured report:

   ```
   ## Evaluation Report

   **Overall Score:** 0.82 / 1.00
   **Date:** 2026-02-01
   **Files Evaluated:** 5

   ### Dimension Scores

   | Dimension      | Score | Weight | Weighted |
   |----------------|-------|--------|----------|
   | Correctness    | 0.90  | 30%    | 0.270    |
   | Code Quality   | 0.85  | 15%    | 0.128    |
   | Security       | 0.75  | 25%    | 0.188    |
   | Performance    | 0.80  | 20%    | 0.160    |
   | Test Coverage  | 0.70  | 10%    | 0.070    |

   ### Findings
   - [Correctness] Edge case not handled in parseInput()
   - [Security] User input not sanitised before DB query
   - [Performance] N+1 query in getUserOrders()
   ```

6. **Write results.** Save the report to:
   - `.agent-eval-results/eval-<timestamp>.md` -- timestamped report
   - `.agent-eval-results/latest.md` -- symlink or copy of the latest report
   - `.agent-pipeline/eval.md` -- if running in a sequential pipeline

## Scoring Thresholds

| Threshold | Meaning                                      |
|-----------|----------------------------------------------|
| >= 0.90   | Excellent -- ready for production             |
| 0.75-0.89 | Good -- minor improvements recommended        |
| 0.60-0.74 | Acceptable -- notable issues to address       |
| < 0.60    | Below standard -- significant rework needed   |

## Error Handling

- If rubric files are missing, report the error and suggest running the
  template generator to restore them.
- If no files are in scope, report that there is nothing to evaluate.
- If the eval-agent cannot determine a score for a dimension, mark it as
  `N/A` and exclude it from the weighted total.
