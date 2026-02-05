# Evaluation Rubrics

This document defines the quality dimensions, their weights, and the criteria
used to evaluate agent-produced code.

## Dimensions

### Correctness (30%)

Does the code work? Does it meet the stated requirements? Are edge cases
handled?

**Evaluate:**
- All acceptance criteria from the feature file are satisfied
- Core logic produces correct outputs for expected inputs
- Edge cases are identified and handled (null, empty, boundary values)
- Error states are handled gracefully with meaningful messages
- No regressions introduced to existing functionality
- Data transformations are accurate and complete

### Code Quality (15%)

Is the code clean, readable, and maintainable? Does it follow established
patterns?

**Evaluate:**
- Naming is clear, consistent, and descriptive (variables, functions, types)
- Functions have a single responsibility and are appropriately sized
- DRY principle is followed -- no unnecessary duplication
- SOLID principles are respected where applicable
- Code follows the project's existing patterns and conventions
- No dead code, commented-out blocks, or TODO hacks left behind
- Proper use of language features (destructuring, generics, pattern matching)
- Module organisation is logical and cohesive

### Security (25%)

Is the code free of vulnerabilities? Does it follow security best practices?

**Evaluate:**
- **Injection:** All user input is validated and sanitised before use in
  queries, commands, or templates (OWASP A03)
- **Authentication:** Auth checks are present and correct on protected routes
  and operations (OWASP A07)
- **Authorisation:** Users can only access resources they own or are permitted
  to access (OWASP A01)
- **Data exposure:** Sensitive data (passwords, tokens, PII) is never logged,
  returned in API responses, or stored in plain text (OWASP A02)
- **Configuration:** Secrets are loaded from environment variables, not
  hard-coded. Default configs are secure (OWASP A05)
- **Dependencies:** No known vulnerable dependencies are introduced
- **Cryptography:** Standard libraries are used; no custom crypto (OWASP A02)

### Performance (20%)

Is the code efficient? Will it scale under expected load?

**Evaluate:**
- Algorithm complexity is appropriate for the data size
- No N+1 queries in data fetching (database or API)
- Expensive operations are cached where appropriate
- Lazy loading is used for heavy resources (images, modules, data)
- No unnecessary re-renders in UI components
- Database queries use proper indexes
- Pagination is implemented for list endpoints
- Memory usage is bounded (no unbounded caches or collections)

### Test Coverage (10%)

Are the new code paths adequately tested?

**Evaluate:**
- Happy-path tests exist for all new functionality
- Error-case tests exist for failure modes
- Edge-case tests cover boundary conditions and unusual inputs
- Integration tests verify component interactions where appropriate
- Tests are deterministic (no flaky tests depending on timing or order)
- Test names clearly describe what is being tested
- Mocks are used appropriately -- not over-mocking

## Weighting

| Dimension      | Weight | Rationale                                    |
|----------------|--------|----------------------------------------------|
| Correctness    | 30%    | Code that does not work has zero value        |
| Security       | 25%    | Vulnerabilities are costly and hard to fix    |
| Performance    | 20%    | Perf issues compound under load               |
| Code Quality   | 15%    | Maintainability matters for long-term health  |
| Test Coverage  | 10%    | Tests guard against regressions               |

The overall score is computed as:

```
overall = (correctness * 0.30) + (security * 0.25) + (performance * 0.20)
        + (code_quality * 0.15) + (test_coverage * 0.10)
```
