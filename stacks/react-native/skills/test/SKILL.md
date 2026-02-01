---
name: test
description: Run Jest tests for React Native components, screens, stores, and queries
---

# /test -- React Native Test Runner

## What This Does

Runs the Jest test suite for a React Native + Expo project using React Native
Testing Library. Can run the full suite, a specific test file, or tests matching
a pattern.

## Usage

```
/test                           # Run the full test suite
/test TransactionCard           # Run tests matching "TransactionCard"
/test __tests__/stores/         # Run all store tests
/test --coverage                # Run with coverage reporting
/test --watch                   # Run in watch mode (interactive)
```

## How It Works

### 1. Detect Test Configuration

Check for test configuration in the project:
- `jest.config.js` or `jest.config.ts`
- `jest` field in `package.json`
- Presence of `__tests__/` directory

### 2. Delegate to mobile-tester Agent

Use the Task tool to invoke the `mobile-tester` sub-agent with:
- Which test framework was detected (Jest)
- Which files or patterns to test
- Whether coverage was requested
- Any previous pipeline context from `.agent-pipeline/implement.md`

### 3. Run Tests

Execute the appropriate test command:

```bash
# Full suite
npm test

# Specific file or pattern
npx jest <pattern>

# With coverage
npx jest --coverage

# Specific file
npx jest __tests__/components/TransactionCard.test.tsx
```

### 4. Report Results

Return a structured summary:

```markdown
## Test Results

**Status:** PASS | FAIL
**Total:** N tests
**Passed:** N
**Failed:** N
**Skipped:** N
**Duration:** Ns

### Test Suites
- PASS __tests__/components/TransactionCard.test.tsx (5 tests)
- PASS __tests__/stores/useTransactionStore.test.ts (4 tests)
- FAIL __tests__/screens/TransactionsScreen.test.tsx (2 passed, 1 failed)

### Failures (if any)
- `TransactionsScreen > shows error state`: Expected "Error" but received null
  at __tests__/screens/TransactionsScreen.test.tsx:45
```

### 5. Write Pipeline Artefact

If running as part of a sequential pipeline, write results to
`.agent-pipeline/test.md` for the next stage.

## Critical Test Requirements

When writing new tests or fixing failing tests, enforce these rules:

1. **Reset Zustand stores** before every test via `beforeEach`
2. **Fresh QueryClient** per test -- never share cached data
3. **Mock database queries** -- never hit the real database
4. **Mock expo-router** -- navigation must be mocked
5. **Mock i18next** -- use `t: (key) => key` for predictable output
6. **Use waitFor** for all async assertions

See `references/rn-jest-patterns.md` for complete code examples.

## Error Handling

- If no test configuration is found, report the error and suggest adding Jest config
- If tests fail, report failures clearly but do NOT attempt to fix production code
- If the test runner crashes, report the full error output
- If Zustand state leaks between tests, report it as a test infrastructure issue
