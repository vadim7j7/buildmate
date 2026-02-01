---
name: test
description: Run Jest unit tests and/or Playwright E2E tests for React + Next.js projects
---

# /test

## What This Does

Runs the project's frontend test suite using Jest (unit/integration) and
optionally Playwright (E2E). Detects which test runner is configured and
executes accordingly.

## Usage

```
/test                              # Run the full Jest test suite
/test path/to/Component.test.tsx   # Run a specific test file
/test --coverage                   # Run with coverage reporting
/test --e2e                        # Run Playwright E2E tests
/test --all                        # Run both Jest and Playwright
```

## How It Works

### 1. Detect Test Framework

Check for test runner configuration:

- `jest.config.ts` / `jest.config.js` / `jest` key in `package.json` --> Jest
- `playwright.config.ts` --> Playwright
- `vitest.config.ts` --> Vitest (alternative)

### 2. Run Unit/Integration Tests (Jest)

```bash
# Full suite
npm test

# Specific file
npx jest path/to/Component.test.tsx

# With coverage
npx jest --coverage

# Watch mode (for development)
npx jest --watch
```

### 3. Run E2E Tests (Playwright)

```bash
# Full E2E suite
npx playwright test

# Specific spec
npx playwright test e2e/projects.spec.ts

# With UI mode (for debugging)
npx playwright test --ui
```

### 4. Report Results

Provide a structured summary:

```
## Test Results

**Framework:** Jest / Playwright
**Status:** PASS | FAIL
**Total:** N tests
**Passed:** N
**Failed:** N
**Skipped:** N
**Duration:** Ns

### Failures (if any)
- `ComponentName.test.tsx` > `test name`: Error message

### Coverage (if requested)
| File | Statements | Branches | Functions | Lines |
|------|-----------|----------|-----------|-------|
| ... | ...% | ...% | ...% | ...% |
```

### 5. Write Pipeline Artifact

If running as part of a pipeline, write results to `.agent-pipeline/test.md`.

## Reference Files

- `references/jest-patterns.md` -- Jest + RTL testing patterns and examples
- `references/playwright-patterns.md` -- Playwright E2E testing patterns

## Error Handling

- If no test framework is detected, report the error and suggest installing Jest
  or Vitest.
- If tests fail, report failures clearly but do NOT attempt to fix them. Fixing
  is the developer agent's responsibility.
- If the test process itself crashes, report the full error output.
