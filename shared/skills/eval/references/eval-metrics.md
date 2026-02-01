# Evaluation Metrics

This document defines the specific scoring criteria for each quality dimension.
Scores range from 0.0 to 1.0 in increments of 0.1. Evaluators should pick the
level that best matches the observed state of the code.

---

## Correctness (Weight: 30%)

| Score | Level       | Criteria                                                          |
|-------|-------------|-------------------------------------------------------------------|
| 1.0   | Exemplary   | All requirements met. Edge cases handled. No bugs found.          |
| 0.9   | Excellent   | All requirements met. Most edge cases handled. Trivial gaps only. |
| 0.8   | Good        | Core requirements met. Some edge cases missing but no bugs.       |
| 0.7   | Adequate    | Core requirements met. Minor bugs in non-critical paths.          |
| 0.6   | Acceptable  | Most requirements met. One or two notable gaps.                   |
| 0.5   | Marginal    | Partial implementation. Several requirements missing.             |
| 0.4   | Poor        | Significant gaps. Core functionality partially broken.            |
| 0.3   | Very Poor   | Major bugs in core logic. Crashes on common inputs.               |
| 0.2   | Failing     | Fundamentally broken. Does not produce correct output.            |
| 0.1   | Absent      | Stub or placeholder code only. No real implementation.            |
| 0.0   | Missing     | No code written for this requirement.                             |

---

## Code Quality (Weight: 15%)

| Score | Level       | Criteria                                                          |
|-------|-------------|-------------------------------------------------------------------|
| 1.0   | Exemplary   | Clean, idiomatic, well-structured. Could serve as a reference.    |
| 0.9   | Excellent   | Very clean. Minor style nits only.                                |
| 0.8   | Good        | Clean with small inconsistencies. Follows project conventions.    |
| 0.7   | Adequate    | Readable but some functions are too long or names unclear.        |
| 0.6   | Acceptable  | Functional but noticeable duplication or poor organisation.       |
| 0.5   | Marginal    | Hard to follow in places. Multiple style violations.              |
| 0.4   | Poor        | Significant duplication. Inconsistent patterns.                   |
| 0.3   | Very Poor   | Difficult to read. Mixed paradigms. No clear structure.           |
| 0.2   | Failing     | Spaghetti code. No discernible architecture.                      |
| 0.1   | Absent      | Commented-out code, debug logs, and TODO hacks throughout.        |
| 0.0   | Missing     | No meaningful code structure.                                     |

---

## Security (Weight: 25%)

| Score | Level       | Criteria                                                          |
|-------|-------------|-------------------------------------------------------------------|
| 1.0   | Exemplary   | No vulnerabilities. Input validated. Secrets handled correctly.   |
| 0.9   | Excellent   | No vulnerabilities found. Minor hardening improvements possible.  |
| 0.8   | Good        | No high/critical vulnerabilities. One or two low-severity gaps.   |
| 0.7   | Adequate    | No critical vulns. Some medium-severity issues (e.g. missing CSRF). |
| 0.6   | Acceptable  | One medium-severity vulnerability. Basic validation present.      |
| 0.5   | Marginal    | Multiple medium-severity issues. Inconsistent input validation.   |
| 0.4   | Poor        | One high-severity vulnerability (e.g. SQL injection possible).    |
| 0.3   | Very Poor   | Multiple high-severity vulnerabilities.                           |
| 0.2   | Failing     | Critical vulnerability (e.g. auth bypass, RCE vector).            |
| 0.1   | Absent      | No security measures at all. Secrets hard-coded.                  |
| 0.0   | Missing     | Actively dangerous code (e.g. disables security middleware).      |

---

## Performance (Weight: 20%)

| Score | Level       | Criteria                                                          |
|-------|-------------|-------------------------------------------------------------------|
| 1.0   | Exemplary   | Optimal algorithms. Proper caching. Lazy loading. Paginated.      |
| 0.9   | Excellent   | Efficient code. Minor optimisation opportunities only.            |
| 0.8   | Good        | Generally efficient. One or two non-critical perf issues.         |
| 0.7   | Adequate    | Acceptable performance. Some unnecessary work (e.g. over-fetching). |
| 0.6   | Acceptable  | Noticeable inefficiencies. Missing pagination on a list endpoint. |
| 0.5   | Marginal    | N+1 query or equivalent pattern in one location.                  |
| 0.4   | Poor        | Multiple N+1 queries or O(n^2) where O(n) is possible.           |
| 0.3   | Very Poor   | Unbounded data fetching. No pagination. Memory leaks likely.      |
| 0.2   | Failing     | Will not scale. Blocks event loop or holds locks unnecessarily.   |
| 0.1   | Absent      | Synchronous blocking calls in async context. Crash under load.    |
| 0.0   | Missing     | No consideration for performance whatsoever.                      |

---

## Test Coverage (Weight: 10%)

| Score | Level       | Criteria                                                          |
|-------|-------------|-------------------------------------------------------------------|
| 1.0   | Exemplary   | Full coverage: happy, error, edge, integration. All deterministic.|
| 0.9   | Excellent   | Comprehensive tests. One or two minor gaps in edge cases.         |
| 0.8   | Good        | Happy path and error cases covered. Some edge cases missing.      |
| 0.7   | Adequate    | Happy path covered. Error cases partially tested.                 |
| 0.6   | Acceptable  | Happy path covered. No error case tests.                          |
| 0.5   | Marginal    | Some tests exist but major paths are untested.                    |
| 0.4   | Poor        | Minimal tests. Only one or two test cases total.                  |
| 0.3   | Very Poor   | Tests exist but are flaky or test implementation details.         |
| 0.2   | Failing     | Tests exist but do not assert meaningful behaviour.               |
| 0.1   | Absent      | Test file created but no test cases written.                      |
| 0.0   | Missing     | No tests at all for new code.                                    |

---

## Computing the Overall Score

```
overall = (correctness * 0.30)
        + (code_quality * 0.15)
        + (security * 0.25)
        + (performance * 0.20)
        + (test_coverage * 0.10)
```

If a dimension is marked `N/A` (cannot be evaluated), redistribute its weight
proportionally among the remaining dimensions.

### Interpretation

| Range       | Label            | Action                                      |
|-------------|------------------|---------------------------------------------|
| 0.90 - 1.00 | Excellent       | Ship it. No changes needed.                 |
| 0.75 - 0.89 | Good            | Ship with minor improvements recommended.   |
| 0.60 - 0.74 | Acceptable      | Address notable issues before merging.       |
| 0.40 - 0.59 | Below Standard  | Significant rework required.                |
| 0.00 - 0.39 | Unacceptable    | Reject. Fundamental problems to resolve.    |
