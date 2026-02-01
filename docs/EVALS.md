# Evals

How to run quality evaluations, interpret results, and write custom eval cases.

---

## Table of Contents

- [Overview](#overview)
- [Scoring Formula](#scoring-formula)
- [Thresholds and Verdicts](#thresholds-and-verdicts)
- [Running Evals](#running-evals)
- [Eval Case Format](#eval-case-format)
- [Shared Eval Cases](#shared-eval-cases)
- [Writing Custom Eval Cases](#writing-custom-eval-cases)
- [Interpreting Results](#interpreting-results)
- [CI/CD Integration](#cicd-integration)

---

## Overview

The eval system provides objective quality scoring for code changes. It measures code across five dimensions using a weighted formula, producing a numerical score between 0.0 and 1.0. The system has three components:

1. **Eval Agent** -- The `eval-agent` sub-agent that reads code, applies rubrics, and scores each dimension
2. **Eval Skill** (`/eval`) -- The slash command that triggers evaluation from Claude Code
3. **Eval Infrastructure** -- Scripts in `evals/` for batch evaluation, scoring, and reporting

The eval system is used:
- As part of the sequential pipeline (after implementation and review)
- On demand via the `/eval` skill
- In CI/CD to gate merge quality

---

## Scoring Formula

The final score is a weighted sum of five dimension scores, each ranging from 0.0 to 1.0:

```
Final Score = (Correctness x 0.30)
            + (Code Quality x 0.15)
            + (Security x 0.25)
            + (Performance x 0.20)
            + (Test Coverage x 0.10)
```

### Dimension Weights

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| **Correctness** | 30% | Does the code do what it is supposed to do? Handles requirements, edge cases, error conditions, and logical correctness. |
| **Code Quality** | 15% | Is the code clean, readable, and maintainable? Covers naming, structure, duplication, conventions, and abstractions. |
| **Security** | 25% | Are there security vulnerabilities? Covers OWASP Top 10, injection, auth, secrets, input validation. |
| **Performance** | 20% | Will the code perform well? Covers N+1 queries, pagination, caching, unnecessary re-renders, algorithm efficiency. |
| **Test Coverage** | 10% | Are changes adequately tested? Covers happy path, error cases, edge cases, meaningful assertions. |

### Per-Dimension Scoring Scale

Each dimension is scored from 0.0 to 1.0:

| Score | Meaning |
|-------|---------|
| 1.0   | Exemplary. No issues found. Exceeds expectations. |
| 0.8   | Good. Minor improvements possible but not critical. |
| 0.6   | Acceptable. Notable issues that should be addressed. |
| 0.4   | Below standard. Significant problems requiring attention. |
| 0.2   | Poor. Major issues that would cause problems in production. |
| 0.0   | Failing. Fundamentally broken or dangerous. |

---

## Thresholds and Verdicts

The eval agent determines a grade based on the final weighted score:

| Score Range | Grade | Verdict | Action |
|-------------|-------|---------|--------|
| >= 0.90 | EXCELLENT | Ship it | No changes needed. Code is production-ready. |
| 0.70 - 0.89 | ACCEPTABLE | Approve with notes | Minor improvements recommended but not blocking. |
| < 0.70 | NEEDS_FIXES | Block | Must address issues before merging. Required fixes are listed in the report. |

The orchestrator pipeline uses a threshold of **>= 0.70** as the minimum passing score. If the eval score falls below 0.70, the pipeline halts and the developer agent is delegated fixes before re-evaluation.

---

## Running Evals

### Via the /eval Skill

The simplest way to run an evaluation is through the `/eval` slash command in Claude Code:

```
/eval                          # Evaluate all changed files
/eval path/to/file.ts          # Evaluate a specific file
/eval --dimension security     # Evaluate only the security dimension
```

The eval skill:
1. Loads rubrics from `references/eval-rubrics.md` and `references/eval-metrics.md`
2. Identifies files in scope (changed files or specific file)
3. Delegates to the eval-agent via the Task tool
4. The eval-agent scores each dimension and produces a report
5. Results are written to `.agent-eval-results/eval-<timestamp>.md`

### Via the Eval Scripts

The `evals/` directory contains scripts for batch evaluation and reporting. These are useful for CI/CD integration and systematic quality tracking.

#### runner.sh

The eval runner executes eval cases against the codebase:

```bash
./evals/runner.sh [options]
```

Options:
- `--cases <path>` -- Path to a JSONL file containing eval cases (default: `evals/shared-cases/`)
- `--output <path>` -- Directory for output files (default: `evals/reports/`)
- `--filter <pattern>` -- Run only cases matching the pattern
- `--timeout <seconds>` -- Per-case timeout (default: 300)

Example:

```bash
# Run all shared cases
./evals/runner.sh

# Run specific cases
./evals/runner.sh --cases evals/shared-cases/code-review.jsonl

# Run with a filter
./evals/runner.sh --filter "security*"
```

#### scorer.sh

The scorer processes runner output and computes scores:

```bash
./evals/scorer.sh [options]
```

Options:
- `--input <path>` -- Path to runner output (default: `evals/reports/`)
- `--rubrics <path>` -- Path to custom rubrics (default: built-in rubrics)
- `--format <json|markdown>` -- Output format (default: markdown)

Example:

```bash
# Score the latest run
./evals/scorer.sh

# Score with custom rubrics
./evals/scorer.sh --rubrics path/to/custom-rubrics.md

# Output as JSON for programmatic consumption
./evals/scorer.sh --format json
```

#### reporter.sh

The reporter generates human-readable summary reports:

```bash
./evals/reporter.sh [options]
```

Options:
- `--input <path>` -- Path to scorer output (default: `evals/reports/`)
- `--output <path>` -- Where to write the report (default: stdout)
- `--format <markdown|html>` -- Report format (default: markdown)
- `--compare <path>` -- Compare against a previous report to show trends

Example:

```bash
# Generate a summary report
./evals/reporter.sh

# Compare against the previous run
./evals/reporter.sh --compare evals/reports/previous-run/

# Write an HTML report
./evals/reporter.sh --format html --output evals/reports/report.html
```

---

## Eval Case Format

Eval cases are defined in JSONL (JSON Lines) format, where each line is a self-contained JSON object describing one evaluation scenario.

### Schema

```json
{
  "id": "unique-case-id",
  "name": "Human-readable case name",
  "description": "What this case evaluates",
  "category": "code-review | test-generation | documentation | security | performance",
  "difficulty": "basic | intermediate | advanced",
  "input": {
    "files": [
      {
        "path": "relative/path/to/file.ext",
        "content": "file content as string"
      }
    ],
    "context": "Additional context for the evaluation",
    "task": "The task description to evaluate against"
  },
  "expected": {
    "dimensions": {
      "correctness": { "min": 0.7, "max": 1.0 },
      "code_quality": { "min": 0.6, "max": 1.0 },
      "security": { "min": 0.8, "max": 1.0 },
      "performance": { "min": 0.6, "max": 1.0 },
      "test_coverage": { "min": 0.5, "max": 1.0 }
    },
    "must_flag": ["list", "of", "issues", "that", "must", "be", "detected"],
    "must_not_flag": ["things", "that", "should", "not", "be", "flagged"]
  },
  "tags": ["tag1", "tag2"]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the case |
| `name` | string | Yes | Human-readable name |
| `description` | string | Yes | What this case tests |
| `category` | string | Yes | Evaluation category |
| `difficulty` | string | Yes | Difficulty level |
| `input.files` | array | Yes | Files to evaluate (path + content) |
| `input.context` | string | No | Additional context |
| `input.task` | string | No | Task description |
| `expected.dimensions` | object | No | Expected score ranges per dimension |
| `expected.must_flag` | array | No | Issues the evaluator must detect |
| `expected.must_not_flag` | array | No | Things that should not be false positives |
| `tags` | array | No | Tags for filtering |

---

## Shared Eval Cases

The `evals/shared-cases/` directory contains built-in evaluation cases that apply across stacks:

### code-review

Cases that test the eval agent's ability to identify code quality issues:
- Naming and readability problems
- Duplication and abstraction issues
- Logic errors and off-by-one bugs
- Convention violations

### test-generation

Cases that test the eval agent's ability to assess test quality:
- Adequate coverage of happy paths
- Error case coverage
- Edge case coverage
- Meaningful assertions (not testing implementation details)

### documentation

Cases that test the eval agent's ability to assess documentation completeness:
- Missing inline documentation on public APIs
- Incorrect parameter descriptions
- Missing usage examples
- Stale documentation that no longer matches the code

---

## Writing Custom Eval Cases

### Step 1: Create a JSONL File

Create a new file in `evals/shared-cases/` or a custom directory:

```bash
touch evals/shared-cases/my-custom-cases.jsonl
```

### Step 2: Write Cases

Add one JSON object per line. Each case should test a specific quality concern:

```json
{"id": "sql-injection-basic", "name": "Detect basic SQL injection", "description": "The evaluator should flag string concatenation in SQL queries", "category": "security", "difficulty": "basic", "input": {"files": [{"path": "src/db/users.ts", "content": "export function getUser(id: string) {\n  return db.query(`SELECT * FROM users WHERE id = '${id}'`);\n}"}], "task": "Evaluate this database query function"}, "expected": {"dimensions": {"security": {"min": 0.0, "max": 0.4}}, "must_flag": ["SQL injection"]}, "tags": ["security", "injection"]}
```

### Step 3: Test Your Cases

Run the eval runner with your custom cases:

```bash
./evals/runner.sh --cases evals/shared-cases/my-custom-cases.jsonl
./evals/scorer.sh
./evals/reporter.sh
```

### Tips for Writing Good Cases

1. **One concern per case.** Each case should test a single quality dimension or issue type.
2. **Include both positive and negative cases.** Test that good code scores well and bad code scores poorly.
3. **Use realistic code.** Cases should resemble real-world code, not contrived examples.
4. **Set specific expectations.** Use `must_flag` for issues the evaluator should detect and dimension ranges for score bounds.
5. **Tag cases.** Use tags for filtering so you can run subsets of cases.
6. **Vary difficulty.** Include basic, intermediate, and advanced cases to test evaluator calibration.

---

## Interpreting Results

### Reading the Eval Report

The eval agent produces a markdown report with the following sections:

```markdown
# Quality Evaluation Report

**Date:** 2026-02-01
**Evaluator:** eval-agent
**Scope:** 5 files evaluated

## Summary

| Dimension      | Weight | Score | Weighted |
|----------------|--------|-------|----------|
| Correctness    | 30%    | 0.90  | 0.270    |
| Code Quality   | 15%    | 0.85  | 0.128    |
| Security       | 25%    | 0.75  | 0.188    |
| Performance    | 20%    | 0.80  | 0.160    |
| Test Coverage  | 10%    | 0.70  | 0.070    |
| **Final Score**|        |       | **0.82** |

## Grade: ACCEPTABLE

## Detailed Findings
...

## Required Fixes (if NEEDS_FIXES)
...

## Recommendations
...
```

### Understanding the Scores

- **Final Score** is the number that determines the grade. It is the weighted sum of all dimensions.
- **Individual dimension scores** show where the strengths and weaknesses are.
- **Weighted column** shows how much each dimension contributes to the final score.

### Common Score Patterns

| Pattern | Interpretation |
|---------|---------------|
| High correctness, low tests | Code works but lacks safety net. Prioritize test coverage. |
| High quality, low security | Clean code with security gaps. Run `/security` for detailed findings. |
| Low performance, high everything else | Functional and secure but may not scale. Check for N+1 queries, missing pagination, unnecessary computations. |
| Everything below 0.6 | Significant rework needed. Start with correctness, then security. |

### JSON Report Format

In addition to the markdown report, the eval agent writes a machine-readable JSON file:

```json
{
  "timestamp": "2026-02-01T12:00:00Z",
  "scope": "5 files evaluated",
  "scores": {
    "correctness": 0.9,
    "code_quality": 0.85,
    "security": 0.75,
    "performance": 0.8,
    "test_coverage": 0.7,
    "final": 0.82
  },
  "grade": "ACCEPTABLE",
  "files_evaluated": ["path/to/file1.ts", "path/to/file2.ts"],
  "required_fixes": [],
  "recommendations": ["Consider adding rate limiting to the API endpoint"]
}
```

---

## CI/CD Integration

### Basic Integration

Add eval scoring to your CI pipeline to gate merges on quality:

```yaml
# Example GitHub Actions workflow
name: Quality Gate
on: [pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run eval cases
        run: ./evals/runner.sh --cases evals/shared-cases/
      - name: Score results
        run: ./evals/scorer.sh --format json > eval-results.json
      - name: Check threshold
        run: |
          SCORE=$(jq '.scores.final' eval-results.json)
          if (( $(echo "$SCORE < 0.70" | bc -l) )); then
            echo "Quality gate failed: score $SCORE < 0.70"
            exit 1
          fi
```

### Tracking Trends

Store eval reports across runs to track quality trends:

```bash
# After each run, archive the report
cp evals/reports/latest.json "evals/reports/$(date +%Y%m%d-%H%M%S).json"

# Compare against previous run
./evals/reporter.sh --compare evals/reports/previous-run/
```

### Custom Thresholds Per Stack

Different stacks may warrant different thresholds:

| Stack | Suggested Minimum | Rationale |
|-------|------------------|-----------|
| Rails | 0.70 | Server-side code with security exposure needs higher baseline |
| React/Next.js | 0.70 | Client-facing code with performance and accessibility concerns |
| React Native | 0.70 | Mobile code with platform-specific correctness requirements |
| Fullstack | 0.70 | Combined stack inherits the strictest threshold |

### Tips for CI/CD

1. **Start with reporting, not blocking.** Run evals in CI and report scores before making them mandatory.
2. **Gradually raise thresholds.** Start at 0.60 and increase as the codebase improves.
3. **Focus on trends.** A score of 0.75 is fine if it is trending up from 0.65.
4. **Exclude prototype code.** Use `--filter` to skip eval cases for experimental or prototype code.
5. **Cache rubrics.** Rubric files rarely change -- cache them to speed up CI runs.

---

## Related Documentation

- [BOOTSTRAP.md](BOOTSTRAP.md) -- How to use bootstrap.sh
- [AGENTS.md](AGENTS.md) -- Agent roles and delegation patterns
- [SKILLS.md](SKILLS.md) -- Skill descriptions and usage
- [ADDING-A-STACK.md](ADDING-A-STACK.md) -- How to add a new stack template
